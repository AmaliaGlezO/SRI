from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from sklearn.feature_extraction.text import TfidfVectorizer

from src.errors.vector_db_errors import (
    EmbeddingModelNotFittedError,
    EmbeddingsModelNotFoundError,
    EmptyDocumentListError,
)
from src.indexing.indexer import InvertedIndex, TextNormalizer


class TfidfEmbeddings(Embeddings):
    """
    LangChain embedding model using basic TF-IDF vectors.
    """

    def __init__(
        self,
        normalizer: TextNormalizer | None = None,
        max_features: int = 15_000,
    ) -> None:
        self.normalizer = normalizer or TextNormalizer()
        self.max_features = max_features

        self._vectorizer = TfidfVectorizer(
            tokenizer=self.normalizer.normalize,
            max_features=self.max_features,
            token_pattern=None,
            lowercase=False,
        )
        self._fitted = False

    def fit(self, documents: list[dict]) -> "TfidfEmbeddings":
        """Fit the TF-IDF model from a list of document dicts."""
        if not documents:
            raise EmptyDocumentListError("Empty document list.")

        texts = []
        for doc in documents:
            text = f"{doc.get('title', '')} {doc.get('content', '')}"
            texts.append(text)

        self._vectorizer.fit(texts)
        self._fitted = True

        v = len(self._vectorizer.vocabulary_)
        print(f"[TfidfEmbeddings] TF-IDF Fitted: {len(documents)} docs | {v} terms")
        return self

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not self._fitted:
            raise EmbeddingModelNotFittedError("TF-IDF embeddings model is not fitted.")
        matrix = self._vectorizer.transform(texts)
        return matrix.toarray().astype(np.float32).tolist()

    def embed_query(self, text: str) -> list[float]:
        if not self._fitted:
            raise EmbeddingModelNotFittedError("TF-IDF embeddings model is not fitted.")
        vector = self._vectorizer.transform([text])
        return vector.toarray().astype(np.float32).flatten().tolist()

    def save(self, directory: str | Path) -> None:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        with open(path / "tfidf_embeddings.pkl", "wb") as fh:
            pickle.dump(self, fh, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def load(cls, directory: str | Path) -> "TfidfEmbeddings":
        path = Path(directory) / "tfidf_embeddings.pkl"
        if not path.exists():
            raise EmbeddingsModelNotFoundError(f"Missing embeddings model at {path}")
        with open(path, "rb") as fh:
            return pickle.load(fh)


def get_embeddings(
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
) -> Embeddings:
    """
    Factory function to get the improved embedding model.
    """
    print(f"[Embeddings] Loading Transformer model: {model_name}...")
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
