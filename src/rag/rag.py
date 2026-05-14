from __future__ import annotations

from typing import Any, List, Dict
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import LlamaCpp
from langchain_classic.retrievers import EnsembleRetriever

from src.errors.internet_search_error import WebSearchExecutionError
from src.errors.rag_errors import (
    RAGAnswerGenerationError,
    RAGPipelineInitializationError,
    RAGRetrievalError,
)
from src.retrieval.lm_retriever import LMRetriever
from src.retrieval.query_processor import QueryProcessor
from src.retrieval.langchain_retriever import LangChainLMRetriever
from src.vector_db.vector_store import VectorStore
from src.vector_db.langchain_retriever import LangChainVectorRetriever
from src.search_internet.searcher import WebSearcher


class RAGPipeline:
    """
    Complete RAG pipeline using LangChain LCEL.
    """

    def __init__(
        self,
        retriever_lm: LMRetriever,
        vector_store: VectorStore,
        model_path: str = "models/TinyLlama-1.1B-Chat-v1.0-Q4_K_M.gguf",
        relevance_threshold: float = 0.4,
    ) -> None:
        try:
            # Initialize LLM
            self.vector_store = vector_store
            self.relevance_threshold = relevance_threshold
            self.web_searcher = WebSearcher()
            self.llm = LlamaCpp(
                model_path=model_path,
                temperature=0.3,
                max_tokens=2048,
                n_ctx=2048,
                verbose=False,
            )

            #  Initialize Retrievers
            self.lm_retriever = LangChainLMRetriever(retriever=retriever_lm, k=5)
            self.vector_retriever = LangChainVectorRetriever(
                vectorstore=vector_store._vectorstore, k=5
            )

            # Create Ensemble Retriever (Hybrid Search)
            self.ensemble_retriever = EnsembleRetriever(
                retrievers=[self.lm_retriever, self.vector_retriever],
                weights=[0.5, 0.5],
            )

            # Define Prompt
            template = """Basandote unicamente en la siguiente informacion, responde la pregunta del usuario de manera clara y concisa.

Contexto:
{context}

Pregunta del usuario: {question}

Responde en espanol usando solo la informacion proporcionada en el contexto. Si la informacion no esta disponible, indica que no hay suficiente informacion. y DETENTE

Respuesta:"""
            self.prompt = ChatPromptTemplate.from_template(template)

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
        formatted = []
        for i, doc in enumerate(docs, 1):
            title = doc.metadata.get("title", "Sin titulo")
            formatted.append(
                f"Documento {i}:\nTitulo: {title}\nContenido: {doc.page_content}"
            )
        return "\n\n".join(formatted)

    def answer(self, query: str) -> Dict[str, Any]:
        """
        Answer a query using the full LangChain RAG pipeline.
        If local results are not relevant, search the internet.
        """
        print(f"[RAGPipeline] Generating answer for: {query}")

        # Get local retrieved docs
        try:
            local_docs = self.ensemble_retriever.get_relevant_documents(query)
        except Exception as exc:
            raise RAGRetrievalError("Failed to retrieve local documents.") from exc

        vector_results = self.vector_retriever.get_relevant_documents(query)
        max_relevance = 0.0
        if vector_results:

            pass

        top_score = 0.0
        for doc in local_docs:
            score = doc.metadata.get("score", 0)

            if isinstance(score, float) and 0 <= score <= 1:
                top_score = max(top_score, score)

        docs = local_docs
        search_performed = False

        if top_score < self.relevance_threshold:
            print(
                f"[RAGPipeline] Local relevance ({top_score:.2f}) below threshold ({self.relevance_threshold}). Searching internet..."
            )
            try:
                internet_docs = self.web_searcher.search(query)
            except WebSearchExecutionError as exc:
                print(f"[RAGPipeline] Internet search failed: {exc}")
                internet_docs = []
            if internet_docs:
                # Persist new internet docs to the vector store
                print(
                    f"[RAGPipeline] Persisting {len(internet_docs)} internet documents to local DB..."
                )
                self.vector_store.add_documents(internet_docs)
                docs = internet_docs + local_docs
                search_performed = True

        context = self._format_docs(docs)

        try:
            if search_performed:
                chain_input = {"context": context, "question": query}
                answer_text = (self.prompt | self.llm | StrOutputParser()).invoke(
                    chain_input
                )
            else:
                answer_text = self.chain.invoke(query)
        except Exception as exc:
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
                    "title": d.metadata.get("title"),
                    "score": d.metadata.get("score", 0),
                    "source": d.metadata.get("source", "Local DB"),
                }
                for d in docs
            ],
        }
