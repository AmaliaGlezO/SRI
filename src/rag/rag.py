from __future__ import annotations

from typing import Any, List, Dict, Optional
from src.generator.answer_generator import AnswerGenerator
from src.positioning.ranker import ResultRanker
from src.utils.logger import rag_logger as logger
from src.config import (
    RAG_ENABLE_PRF,
    RAG_LM_RETRIEVER_WEIGHT,
    RAG_MAX_DOC_CHARS,
    RAG_PRF_K,
    RAG_PRF_TERMS,
    RAG_RELEVANCE_THRESHOLD,
    RAG_RETRIEVER_K,
    RAG_VECTOR_RETRIEVER_WEIGHT,
)
from langchain_core.documents import Document
from src.errors.internet_search_error import WebSearchExecutionError
from src.errors.rag_errors import (
    RAGPipelineInitializationError,
    RAGRetrievalError,
)
from src.errors.retrieval_errors import QueryProcessingError
from src.retrieval.lm_retriever import LMRetriever
from src.retrieval.query_processor import QueryProcessor
from src.retrieval.langchain_retriever import LangChainLMRetriever
from src.vector_db.vector_store import VectorStore
from src.vector_db.langchain_retriever import LangChainVectorRetriever
from src.search_internet.searcher import WebSearcher
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

class EnsembleRetriever(BaseRetriever):
    """Simple ensemble retriever combining LM and vector retrievers."""
    retrievers: List[Any]
    weights: List[float]
    k:int=60

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Any]:
        """Combine results from multiple retrievers with weighted scoring."""
        all_docs = {}  # {content_hash: (doc, weighted_score)}
        
        for retriever, weight in zip(self.retrievers, self.weights):
            try:
                docs = retriever.invoke(query)
                for i, doc in enumerate(docs,start=1):
                    score = weight/(self.k+i) # Rank-WRRF
                    doc_hash = hash(doc.page_content)
                    
                    if doc_hash in all_docs:
                        all_docs[doc_hash] = (doc, all_docs[doc_hash][1] + score)
                    else:
                        all_docs[doc_hash] = (doc, score)
            except Exception:
                pass
        
        sorted_docs = sorted(all_docs.values(), key=lambda x: x[1], reverse=True)
        return [doc for doc, score in sorted_docs]


class RAGPipeline:
    """
    Complete RAG pipeline using LangChain LCEL.
    """

    def __init__(
        self,
        retriever_lm: LMRetriever,
        vector_store: VectorStore,
        web_searcher: Optional[WebSearcher] = None,
        query_processor: Optional[QueryProcessor] = None,
        ranker: Optional[ResultRanker] = None,
        relevance_threshold: float | None = None,
        enable_prf: bool | None = None,
        prf_k: int | None = None,
        prf_terms: int | None = None,
    ) -> None:
        """Initialize RAG pipeline with dependency injection."""
        try:
            self.vector_store = vector_store
            
            # Dependency injection
            self.web_searcher = web_searcher or WebSearcher()
            self.query_processor = query_processor or QueryProcessor(retriever_lm.normalizer)
            self.ranker = ranker or ResultRanker(
                relevance_weight=0.5,
                popularity_weight=0.15,
                freshness_weight=0.2,
                completeness_weight=0.1,
                source_quality_weight=0.05,
            )
            
            self.relevance_threshold = (
                relevance_threshold
                if relevance_threshold is not None
                else RAG_RELEVANCE_THRESHOLD
            )
            self.enable_prf = enable_prf if enable_prf is not None else RAG_ENABLE_PRF
            self.prf_k = prf_k if prf_k is not None else RAG_PRF_K
            self.prf_terms = prf_terms if prf_terms is not None else RAG_PRF_TERMS
            self.max_doc_chars = RAG_MAX_DOC_CHARS

            self.raw_lm_retriever = retriever_lm

            #  Initialize Retrievers
            self.lm_retriever = LangChainLMRetriever(
                retriever=retriever_lm, k=RAG_RETRIEVER_K
            )
            self.vector_retriever = LangChainVectorRetriever(
                vectorstore=vector_store._vectorstore, k=RAG_RETRIEVER_K
            )

            # Create Ensemble Retriever (Hybrid Search)
            self.ensemble_retriever = EnsembleRetriever(
                retrievers=[self.lm_retriever, self.vector_retriever],
                weights=[RAG_LM_RETRIEVER_WEIGHT, RAG_VECTOR_RETRIEVER_WEIGHT],
            )
    

        except Exception as exc:
            raise RAGPipelineInitializationError(
                "Failed to initialize RAG pipeline."
            ) from exc

    async def retrieve(
            self,
            query: str,
            top_k: int | None = None,
            use_prf: bool = True,
            relevance_threshold: float | None = None,
            max_doc_chars: int | None = None,
            use_internet_search: bool = True,
        ) -> Dict[str, Any]:
            """
            Retrieve documents using the RAG pipeline.
            
            - returns context and documents for external generation.
            
            Parameters
            ----------
            query : str
                User query in Spanish
            top_k : int, optional
                Number of documents to retrieve
            use_prf : bool
                Whether to apply Pseudo-Relevance Feedback for query expansion
            relevance_threshold : float, optional
                RAG relevance threshold for web search fallback
            max_doc_chars : int, optional
                Max characters per document
            use_internet_search : bool
                Whether to allow internet fallback search
                
            Returns
            -------
            dict
                Contains: query, context, documents, sources, search_performed, top_local_score
            """
            effective_threshold = (
                relevance_threshold if relevance_threshold is not None 
                else RAG_RELEVANCE_THRESHOLD
            )
            effective_top_k = top_k if top_k is not None else RAG_RETRIEVER_K
            self.max_doc_chars = max_doc_chars if max_doc_chars is not None else RAG_MAX_DOC_CHARS
            logger.info(f"RAG: Processing query: {query}")

            # Process query: normalize, extract filters, optional PRF
            try:
                processed_query = self.query_processor.process(query)
                logger.info(f"Normalized query: {processed_query.text}")
                if processed_query.filters:
                    logger.info(f"Detected filters: {processed_query.filters}")
            except QueryProcessingError as exc:
                raise RAGRetrievalError(f"Query processing failed: {exc}") from exc

            # Get initial query weights from processed query
            q_weights = processed_query.to_weights()

            # Apply Pseudo-Relevance Feedback if enabled
            if  self.enable_prf and use_prf:
                logger.info("Applying PRF for query expansion...")
                
                try:
                    q_weights_expanded = self.query_processor.apply_prf(
                        q_weights,
                        self.raw_lm_retriever,
                        prf_k=self.prf_k,
                        prf_terms=self.prf_terms,
                    )
                    q_weights = q_weights_expanded
                    logger.info("Query expanded via PRF")
                    logger.info(f"Expanded query: {processed_query.text}")
                except Exception as exc:
                    logger.info(f"PRF expansion skipped: {exc}")


            try:
                if hasattr(self.lm_retriever, 'k'):
                    self.lm_retriever.k = effective_top_k
                if hasattr(self.vector_retriever, 'k'):
                    self.vector_retriever.k = effective_top_k

                local_docs = self.ensemble_retriever.invoke(processed_query.text)
                print(f"total_doc_retrieval: {len(local_docs)}")
                local_docs = local_docs[:effective_top_k]
                logger.info(f"Retrieved {len(local_docs)} docs from ensemble")
                
            except Exception as exc:
                raise RAGRetrievalError("Failed to retrieve local documents.") from exc

            
            docs = local_docs
            

            top_score = 0.0
            for doc in docs:
                score = doc.metadata.get("score", 0)
                if isinstance(score, float):
                    top_score = max(top_score, score)

            search_performed = False
            internet_docs = []

            if use_internet_search and top_score < effective_threshold:
                logger.info(
                    f"Local relevance ({top_score:.2f}) below threshold ({effective_threshold}). Searching internet..."
                )
                
                try:
                    internet_docs = self.web_searcher.search(processed_query.text)
                except WebSearchExecutionError as exc:
                    logger.info(f"Internet search failed: {exc}")
                    internet_docs = []

            # Combine local and internet documents
            all_docs = local_docs + internet_docs
            
            # Apply ranking with positioning module
            logger.info(f"Ranking {len(all_docs)} documents...")
            ranked_docs = self.ranker.rank(all_docs, processed_query.text)
            
            # Get top K from ranked results
            docs = ranked_docs[:effective_top_k]
            for doc in docs:
               if doc.page_content:
                  doc.page_content = doc.page_content[:self.max_doc_chars]
         
            logger.info(f"Using top {len(docs)} ranked documents")
            
            if internet_docs:
                logger.info(f"save {len(internet_docs)} web docs in ChromaDB")
                await self.vector_store.add_documents(internet_docs)
               
                search_performed = True

            context, token_count, exceeds_context = AnswerGenerator._format_docs(docs)
            self._last_char_truncated = 0
            self._last_context_truncated = 1 if exceeds_context else 0
            

            logger.info(f"Retrieved {len(docs)} documents for context")
            print(docs)
            sources = []
            for doc in docs:
                source_info = {
                    "title": doc.metadata.get("title", "Unknown"),
                    "url": doc.metadata.get("url", ""),
                    "source": doc.metadata.get("source", "Local DB"),
                }
                if source_info not in sources:
                    sources.append(source_info)

            return {
                "query": query,
                "context": context,  # Formatted context for LLM
                "documents": docs,     # Raw documents for external processing
                "sources": sources,
                "search_performed": search_performed,
                "exceeds_context": exceeds_context,
                "context_token_count": token_count,
                "top_local_score": top_score,
                "retrieved_documents": [
                    {
                        "title": d.metadata.get("title") or "Sin título",
                        "url": d.metadata.get("url") or "",
                        "score": d.metadata.get("score", 0),
                        "source": d.metadata.get("source", "Local DB"),
                        "tags": d.metadata.get("tags", []) if d.metadata else [],
                        "category": d.metadata.get("category", "") if d.metadata else "",
                    }
                    for d in docs
                ],
                "status": ["Retrieval complete", f"Found {len(docs)} documents"],
            }
