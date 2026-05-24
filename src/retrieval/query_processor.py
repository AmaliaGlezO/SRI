from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from src.errors.retrieval_errors import QueryFormatError, QueryProcessingError
from src.indexing.indexer import InvertedIndex, TextNormalizer
from src.utils.logger import query_expansion_logger as logger


@dataclass
class ProcessedQuery:
    """Holds a processed query ready to be sent to a retriever."""

    original: str
    text: str  # text stripped of syntax
    tokens: list[str] = field(default_factory=list)
    expanded: bool = False

    def to_weights(self) -> dict[str, float]:
        """Convert the processed text into normalized query weights P(w|q)."""
        w: dict[str, float] = {}
        for q in self.tokens:
            w[q] = w.get(q, 0.0) + 1.0
        tot = sum(w.values())
        if tot > 0:
            for k in w:
                w[k] /= tot
        return w


class QueryProcessor:
    """
    Pre-processes user queries for the information retrieval system (SRI).

    Parameters
    ----------
    normalizer : TextNormalizer | None
        Shared normalizer used by the index and retriever.
    """

    def __init__(self, normalizer: TextNormalizer | None = None) -> None:
        self.normalizer = normalizer 
        self._cooccurrence_cache: dict[
            tuple[int, int, int, int], dict[str, Counter[str]]
        ] = {}

    def process(self, raw_query: str) -> ProcessedQuery:
        """
        Process *raw_query* and return a ProcessedQuery.

        Steps
        -----
        1. Normalise whitespace and casing
        2. Detect explicit filters (``source:xataka``)
        """
      
        query = self._clean(str(raw_query))
        if not query:
            raise QueryFormatError("Query must not be empty.")

        try:
            tokens = self.normalizer.normalize_query(query)
            text = " ".join(tokens)
        except QueryFormatError:
            raise
        except Exception as exc:
            raise QueryProcessingError("Failed to process query.") from exc

        return ProcessedQuery(
            original=raw_query,
            text=text,
            tokens=tokens,
        )

    def precompute_cooccurrence_matrix(
        self,
        index: InvertedIndex | None,
        window_size: int = 1,
    ) -> dict[str, int]:
        """Build and cache the co-occurrence matrix before serving queries."""
        if index is None:
            return {"terms": 0, "pairs": 0, "window": max(1, window_size)}

        matrix = self._get_cooccurrence_matrix(index, window_size)
        return {
            "terms": len(matrix),
            "pairs": sum(len(row) for row in matrix.values()) // 2,
            "window": max(1, window_size),
        }

    def apply_cooccurrence_expansion(
        self,
        orig_q_weights: dict[str, float],
        query_text: str,
        expansion_terms: int = 5,
        alpha: float = 0.65,
        window_size: int = 1,
        index: InvertedIndex | None = None,
    ) -> dict[str, float]:
        """
        Expand a query using an indexed-term co-occurrence matrix.

        Steps:
        1. Build a symmetric sparse co-occurrence matrix from indexed tokens.
        2. Read the rows for the original query terms.
        3. Select the terms with the highest co-occurrence counts.
        4. Interpolate original and expansion term probabilities.
        """
        try:
            logger.info(f"Applying co-occurrence expansion to query: '{query_text}'")
            query_terms = list(orig_q_weights) or self.normalizer.normalize_query(
                query_text
            )
            if not query_terms or index is None:
                return orig_q_weights

            cooccurrence_matrix = self._get_cooccurrence_matrix(index, window_size)
            if not cooccurrence_matrix:
                return orig_q_weights

            original_terms = set(query_terms)
            candidate_scores: Counter[str] = Counter()
            fallback_weight = 1.0 / len(query_terms)

            for term in query_terms:
                row = cooccurrence_matrix.get(term)
                if not row:
                    continue

                query_weight = orig_q_weights.get(term, fallback_weight)
                for candidate, count in row.items():
                    if candidate in original_terms or len(candidate) <= 1:
                        continue
                    candidate_scores[candidate] += query_weight * count

            if not candidate_scores:
                return orig_q_weights

            top_n = min(max(expansion_terms, 0), len(candidate_scores))
            if top_n <= 0:
                return orig_q_weights

            selected_terms = candidate_scores.most_common(top_n)
            total_score = sum(score for _, score in selected_terms)
            if total_score <= 0:
                return orig_q_weights

            logger.info(f"Selected {len(selected_terms)} expansion terms.")
            expansion_probs = {
                term: float(score / total_score)
                for term, score in selected_terms
            }

            final_probs = {
                term: alpha * weight for term, weight in orig_q_weights.items()
            }
            for term, weight in expansion_probs.items():
                final_probs[term] = final_probs.get(term, 0.0) + (
                    (1.0 - alpha) * weight
                )

            result: dict[str, float] = {}
            total = sum(final_probs.values())
            if total > 0:
                for term, weight in final_probs.items():
                    result[term] = weight / total

            return result
        except QueryProcessingError:
            raise
        except Exception as exc:
            raise QueryProcessingError(
                "Failed to apply co-occurrence expansion."
            ) from exc

    def weights_to_query_text(
        self,
        weights: dict[str, float],
        fallback: str,
        max_repeats: int = 4,
    ) -> str:
        """Approximate weighted terms as text for vector and string retrievers."""
        if not weights:
            return fallback

        max_weight = max(weights.values())
        if max_weight <= 0:
            return fallback

        terms: list[str] = []
        for term, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            repeats = max(1, round((weight / max_weight) * max_repeats))
            terms.extend([term] * repeats)

        return " ".join(terms) if terms else fallback

    def _get_cooccurrence_matrix(
        self,
        index: InvertedIndex,
        window_size: int,
    ) -> dict[str, Counter[str]]:
        """Return a cached sparse symmetric term co-occurrence matrix."""
        normalized_window = max(1, window_size)
        cache_key = (
            id(index),
            getattr(index, "_N", 0),
            len(getattr(index, "_vocab", set())),
            normalized_window,
        )
        cached = self._cooccurrence_cache.get(cache_key)
        if cached is not None:
            return cached

        matrix: defaultdict[str, Counter[str]] = defaultdict(Counter)
        vocabulary = getattr(index, "_vocab", set())

        for doc_info in getattr(index, "_doc_info", {}).values():
            token_text = doc_info.get("content_preview", "")
            if not token_text:
                continue

            tokens = [
                token
                for token in token_text.split()
                if token in vocabulary and len(token) > 1
            ]

            for pos, term in enumerate(tokens):
                end = min(len(tokens), pos + normalized_window + 1)
                for neighbor in tokens[pos + 1 : end]:
                    if neighbor == term:
                        continue

                    matrix[term][neighbor] += 1
                    matrix[neighbor][term] += 1

        result = {term: Counter(row) for term, row in matrix.items()}
        self._cooccurrence_cache[cache_key] = result
        logger.info(
            "Built co-occurrence matrix with "
            f"{len(result)} terms and window={normalized_window}"
        )
        return result

    @staticmethod
    def _clean(text: str) -> str:
        """Strip excess whitespace and lower-case."""
        return re.sub(r"\s+", " ", text.strip().lower())
    

    def __str__(self) -> str:
        return f"QueryProcessor()"