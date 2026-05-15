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
            self.max_doc_chars = RAG_MAX_DOC_CHARS
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
            template = """Eres un asistente de tecnologia especializado en tecnologia, moviles, PCs y comparaciones de productos.

Basandote unicamente en la siguiente informacion, responde la pregunta del usuario.

Contexto:
{context}

Pregunta del usuario: {question}

Instrucciones:
- Responde en ESPAÑOL
- Usa FORMATO MARKDOWN para facilitar el parseo
- Para comparaciones usa TABLAS en formato markdown:
  | Caracteristica | Producto 1 | Producto 2 | ....  | Prdocuto N |
  |----------------|------------|------------| ....  |------------|
  | Valor 1        | Dato 1     | Dato 2     | ....  | Dato N     |
- Para listas usabullet points con guiones (-)
- Incluye CITACIONES usando el formato [n] donde n es el numero del documento
- Si la pregunta es sobre ranking o "mejor", haz una lista numerada con los top 3-5
- Si la pregunta requiere comparacion, haz una tabla comparativa
- Si no tienes suficiente informacion, indica que no puedes responder
- NUNCA inventes informacion que no este en el contexto

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
    
        max_total_chars = (MODEL_N_CTX - 400) * 3
        limit = self.max_doc_chars if self.max_doc_chars is not None else max_total_chars
        
        # Calculate total characters if we don't truncate
        total_untruncated_chars = sum(len(doc.page_content) for doc in docs)
        
        # Determine if we need to truncate
        should_truncate = total_untruncated_chars > max_total_chars
        
        formatted = []
        for i, doc in enumerate(docs, 1):
            title = doc.metadata.get("title", "Sin titulo")
            
            if should_truncate:
                content = (
                    doc.page_content[:limit] + "..."
                    if len(doc.page_content) > limit
                    else doc.page_content
                )
            else:
                content = doc.page_content
                
            formatted.append(f"Documento {i}:\nTitulo: {title}\nContenido: {content}")
        return "\n\n".join(formatted)

    def answer(
        self,
        query: str,
        use_rag: bool = True,
        top_k: int | None = None,
        use_prf: bool = True,
        temperature: float | None = None,
        relevance_threshold: float | None = None,
        max_doc_chars: int | None = None,
        use_internet_search: bool = True,
    ) -> Dict[str, Any]:
        """
        Answer a query using the full LangChain RAG pipeline.
        If local results are not relevant, search the internet.

        Parameters
        ----------
        query : str
            User query in Spanish
        use_rag : bool
            Whether to use the RAG pipeline (if False, use LLM directly without context)
        top_k : int, optional
            Number of documents to retrieve
        use_prf : bool
            Whether to apply Pseudo-Relevance Feedback for query expansion
        temperature : float, optional
            LLM temperature
        relevance_threshold : float, optional
            RAG relevance threshold
        max_doc_chars : int, optional
            Max characters per document
        use_internet_search : bool
            Whether to allow internet fallback search
        """
        # Handle temperature override
        original_temperature = None
        if temperature is not None and hasattr(self.llm, 'temperature'):
            original_temperature = self.llm.temperature
            self.llm.temperature = temperature

        # Mode without RAG: use LLM directly without context
        if not use_rag:
            print(f"[RAGPipeline] RAG disabled - using LLM directly without context")
            try:
                # Simple prompt for direct LLM response
                simple_template = """Pregunta: {question}

Responde en español de manera clara y concisa. Si no tienes información suficiente, indica que no puedes responder la pregunta.

Respuesta:"""
                simple_prompt = PromptTemplate.from_template(simple_template)
                answer_text = (simple_prompt | self.llm | StrOutputParser()).invoke(
                    {"question": query}
                )
                print(f"[RAGPipeline] Direct LLM answer generated")
            except Exception as exc:
                print(f"[RAGPipeline] Direct LLM generation failed: {exc}")
                raise RAGAnswerGenerationError("Failed to generate answer without RAG.") from exc
            finally:
                # Restore original temperature
                if original_temperature is not None:
                    self.llm.temperature = original_temperature

            return {
                "query": query,
                "answer": answer_text.strip(),
                "sources": [],
                "search_performed": False,
                "top_local_score": 0.0,
                "retrieved_documents": [],
                "status": ["Procesando consulta", "Generando respuesta con LLM directo"],
            }

        # RAG mode enabled
        effective_threshold = (
            relevance_threshold if relevance_threshold is not None else RAG_RELEVANCE_THRESHOLD
        )
        effective_top_k = top_k if top_k is not None else RAG_RETRIEVER_K
        self.max_doc_chars = max_doc_chars if max_doc_chars is not None else RAG_MAX_DOC_CHARS

        status_steps = []
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
        if use_rag and self.enable_prf and use_prf:
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
                print(f"[RAGPipeline] Expanded query: {processed_query.text}")
            except Exception as exc:
                print(f"[RAGPipeline] PRF expansion skipped: {exc}")

        # Retrieve documents using LM retriever with processed query weights
        
        try:
            lm_results = self.raw_lm_retriever.retrieve(
                q_weights,
                top_k=effective_top_k,
                filters=processed_query.filters if processed_query.filters else None,
            )
            print(f"[RAGPipeline] Retrieved {len(lm_results)} docs from LM retriever")
        except Exception as exc:
            print(f"[RAGPipeline] LM retriever fallback to ensemble")
            lm_results = None

        # Get ensemble results as fallback or complement
        try:
            local_docs = self.ensemble_retriever.invoke(query)
            local_docs = local_docs[:effective_top_k]
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

        if use_rag and use_internet_search and top_score < effective_threshold:
            print(
                f"[RAGPipeline] Local relevance ({top_score:.2f}) below threshold ({effective_threshold}). Searching internet..."
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
                
                all_docs = local_docs + internet_docs
                
                all_docs_with_scores = []
                for doc in all_docs:
                    score = doc.metadata.get("score", 0.5)
                    all_docs_with_scores.append((score, doc))
                
                all_docs_with_scores.sort(key=lambda x: x[0], reverse=True)
                
                docs = [doc for score, doc in all_docs_with_scores[:effective_top_k]]
                
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
            "status": status_steps,
        }
