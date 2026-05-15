from __future__ import annotations

from typing import Any, List, Dict
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import LlamaCpp

from src.config import (
    MODEL_MAX_TOKENS,
    MODEL_N_CTX,
    MODEL_TEMPERATURE,
    MODEL_VERBOSE,
    RAG_ENABLE_PRF,
    RAG_LM_RETRIEVER_WEIGHT,
    RAG_MAX_DOC_CHARS,
    RAG_PRF_K,
    RAG_PRF_TERMS,
    RAG_RELEVANCE_THRESHOLD,
    RAG_RETRIEVER_K,
    RAG_VECTOR_RETRIEVER_WEIGHT,
)
from src.errors.internet_search_error import WebSearchExecutionError
from src.errors.rag_errors import (
    RAGAnswerGenerationError,
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
                for i, doc in enumerate(docs):
                    # Assign score based on retriever rank and weight
                    score = (1.0 / (i + 1)) * weight  # Rank-based scoring
                    doc_hash = hash(doc.page_content)
                    
                    if doc_hash in all_docs:
                        # Accumulate scores for duplicate documents
                        all_docs[doc_hash] = (doc, all_docs[doc_hash][1] + score)
                    else:
                        all_docs[doc_hash] = (doc, score)
            except Exception:
                pass
        
        # Sort by weighted score and return documents
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
        model_path: str | None = None,
        relevance_threshold: float | None = None,
        enable_prf: bool | None = None,
        prf_k: int | None = None,
        prf_terms: int | None = None,
    ) -> None:
        try:
            # Initialize LLM
            self.vector_store = vector_store
            self.relevance_threshold = (
                relevance_threshold
                if relevance_threshold is not None
                else RAG_RELEVANCE_THRESHOLD
            )
            self.web_searcher = WebSearcher()
            self.enable_prf = enable_prf if enable_prf is not None else RAG_ENABLE_PRF
            self.prf_k = prf_k if prf_k is not None else RAG_PRF_K
            self.prf_terms = prf_terms if prf_terms is not None else RAG_PRF_TERMS
            # Use default model path if not provided
            if not model_path:
                from src.utils.model_downloader import ModelDownloader

                model_path = str(ModelDownloader.ensure_model_exists())

            self.llm = LlamaCpp(
                model_path=model_path,
                temperature=MODEL_TEMPERATURE,
                max_tokens=MODEL_MAX_TOKENS,
                n_ctx=MODEL_N_CTX,
                verbose=MODEL_VERBOSE,
            )

            # Initialize Query Processor for advanced query handling
            self.query_processor = QueryProcessor(retriever_lm.normalizer)
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

            # Define Prompt
            template = """Basandote unicamente en la siguiente informacion, responde la pregunta del usuario de manera clara y concisa.

Contexto:
{context}

Pregunta del usuario: {question}

Responde en espanol usando solo la informacion proporcionada en el contexto. Si la informacion no esta disponible, indica que no hay suficiente informacion. y DETENTE

Respuesta:"""
            self.prompt = PromptTemplate.from_template(template)

            #  Build Chain
            self.chain = (
                {
                    "context": self.ensemble_retriever | self._format_docs,
                    "question": RunnablePassthrough(),
                }
                | self.prompt
                | self.llm
                | StrOutputParser()
            )
        except Exception as exc:
            raise RAGPipelineInitializationError(
                "Failed to initialize RAG pipeline."
            ) from exc

    def _format_docs(self, docs: List[Any]) -> str:
        # Estimate available context window in characters
        # Llama 2/3 context is n_ctx tokens. We leave 400 for instructions/query.
        # Conservative estimate: 3 characters per token.
        max_total_chars = (MODEL_N_CTX - 400) * 3
        
        # Calculate total characters if we don't truncate
        total_untruncated_chars = sum(len(doc.page_content) for doc in docs)
        
        # Determine if we need to truncate
        should_truncate = total_untruncated_chars > max_total_chars
        
        formatted = []
        for i, doc in enumerate(docs, 1):
            title = doc.metadata.get("title", "Sin titulo")
            
            if should_truncate:
                # Use environment variable limit per document
                limit = RAG_MAX_DOC_CHARS
                content = (
                    doc.page_content[:limit] + "..."
                    if len(doc.page_content) > limit
                    else doc.page_content
                )
            else:
                content = doc.page_content
                
            formatted.append(f"Documento {i}:\nTitulo: {title}\nContenido: {content}")
        return "\n\n".join(formatted)

    def answer(self, query: str, use_prf: bool = True) -> Dict[str, Any]:
        """
        Answer a query using the full LangChain RAG pipeline.
        If local results are not relevant, search the internet.

        Parameters
        ----------
        query : str
            User query in Spanish
        use_prf : bool
            Whether to apply Pseudo-Relevance Feedback for query expansion
        """
        print(f"[RAGPipeline] Processing query: {query}")

        # Process query: normalize, extract filters, optional PRF
        try:
            processed_query = self.query_processor.process(query)
            print(f"[RAGPipeline] Normalized query: {processed_query.text}")
            if processed_query.filters:
                print(f"[RAGPipeline] Detected filters: {processed_query.filters}")
        except QueryProcessingError as exc:
            raise RAGRetrievalError(f"Query processing failed: {exc}") from exc

        # Get initial query weights from processed query
        q_weights = processed_query.to_weights()

        # Apply Pseudo-Relevance Feedback if enabled
        if self.enable_prf and use_prf:
            print(f"[RAGPipeline] Applying PRF for query expansion...")
            try:
                q_weights_expanded = self.query_processor.apply_prf(
                    q_weights,
                    self.raw_lm_retriever,
                    prf_k=self.prf_k,
                    prf_terms=self.prf_terms,
                )
                q_weights = q_weights_expanded
                print(f"[RAGPipeline] Query expanded via PRF")
            except Exception as exc:
                print(f"[RAGPipeline] PRF expansion skipped: {exc}")

        # Retrieve documents using LM retriever with processed query weights
        try:
            lm_results = self.raw_lm_retriever.retrieve(
                q_weights,
                top_k=RAG_RETRIEVER_K,
                filters=processed_query.filters if processed_query.filters else None,
            )
            print(f"[RAGPipeline] Retrieved {len(lm_results)} docs from LM retriever")
        except Exception as exc:
            print(f"[RAGPipeline] LM retriever fallback to ensemble")
            lm_results = None

        # Get ensemble results as fallback or complement
        try:
            local_docs = self.ensemble_retriever.invoke(query)
            print(f"[RAGPipeline] Retrieved {len(local_docs)} docs from ensemble")
        except Exception as exc:
            raise RAGRetrievalError("Failed to retrieve local documents.") from exc

        # Use LM results if available, otherwise use ensemble results
        if lm_results and len(lm_results) > 0:
            # Convert LM results to LangChain Document-like objects for formatting
            docs = local_docs
        else:
            docs = local_docs

        top_score = 0.0
        for doc in docs:
            score = doc.metadata.get("score", 0)
            if isinstance(score, float) and 0 <= score <= 1:
                top_score = max(top_score, score)

        search_performed = False

        if top_score < self.relevance_threshold:
            print(
                f"[RAGPipeline] Local relevance ({top_score:.2f}) below threshold ({self.relevance_threshold}). Searching internet..."
            )
            try:
                internet_docs = self.web_searcher.search(processed_query.text)
            except WebSearchExecutionError as exc:
                print(f"[RAGPipeline] Internet search failed: {exc}")
                internet_docs = []
            if internet_docs:
                print(
                    f"[RAGPipeline] Persisting {len(internet_docs)} internet documents to local DB..."
                )
                self.vector_store.add_documents(internet_docs)
                docs = internet_docs + local_docs
                search_performed = True

        print(f"[RAGPipeline] Formatting {len(docs)} documents for context...")
        context = self._format_docs(docs)

        try:
            if search_performed:
                print(f"[RAGPipeline] Generating answer with internet search context...")
                chain_input = {"context": context, "question": query}
                answer_text = (self.prompt | self.llm | StrOutputParser()).invoke(
                    chain_input
                )
            else:
                print(f"[RAGPipeline] Generating answer with local ensemble context...")
                answer_text = self.chain.invoke(query)
            print(f"[RAGPipeline] Answer generated successfully")
        except Exception as exc:
            print(f"[RAGPipeline] Answer generation failed: {exc}")
            raise RAGAnswerGenerationError("Failed to generate final answer.") from exc

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
            "answer": answer_text.strip(),
            "sources": sources,
            "search_performed": search_performed,
            "top_local_score": top_score,
            "retrieved_documents": [
                {
                    "title": d.metadata.get("title") or "Sin título",
                    "url": d.metadata.get("url") or "",
                    "score": d.metadata.get("score", 0),
                    "source": d.metadata.get("source", "Local DB"),
                }
                for d in docs
            ],
        }
