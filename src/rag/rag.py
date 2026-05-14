from __future__ import annotations

from typing import Any, List, Dict
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import LlamaCpp
from langchain_classic.retrievers import EnsembleRetriever

from src.retrieval.lm_retriever import LMRetriever
from src.retrieval.query_processor import QueryProcessor
from src.retrieval.langchain_retriever import LangChainLMRetriever
from src.vector_db.vector_store import VectorStore


class RAGPipeline:
    """
    Complete RAG pipeline using LangChain LCEL.
    """

    def __init__(
        self,
        retriever_lm: LMRetriever,
        vector_store: VectorStore,
        model_path: str = "models/TinyLlama-1.1B-Chat-v1.0-Q4_K_M.gguf",
    ) -> None:
        #  Initialize LLM
        self.llm = LlamaCpp(
            model_path=model_path,
            temperature=0.3,
            max_tokens=2048,
            n_ctx=2048,
            verbose=False,
        )

        #  Initialize Retrievers
        self.lm_retriever = LangChainLMRetriever(retriever=retriever_lm, k=5)
        self.vector_retriever = vector_store.as_retriever(search_kwargs={"k": 5})

        #  Create Ensemble Retriever (Hybrid Search)
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.lm_retriever, self.vector_retriever],
            weights=[0.5, 0.5]
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
            {"context": self.ensemble_retriever | self._format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def _format_docs(self, docs: List[Any]) -> str:
        formatted = []
        for i, doc in enumerate(docs, 1):
            title = doc.metadata.get("title", "Sin titulo")
            formatted.append(f"Documento {i}:\nTitulo: {title}\nContenido: {doc.page_content}")
        return "\n\n".join(formatted)

    def answer(self, query: str) -> Dict[str, Any]:
        """
        Answer a query using the full LangChain RAG pipeline.
        """
        print(f"[RAGPipeline] Generating answer for: {query}")
        
        # Get retrieved docs for metadata reporting
        docs = self.ensemble_retriever.get_relevant_documents(query)
        
        answer_text = self.chain.invoke(query)
        
        sources = []
        for doc in docs:
            source_info = {
                "title": doc.metadata.get("title", "Unknown"),
                "url": doc.metadata.get("url", ""),
            }
            if source_info not in sources:
                sources.append(source_info)

        return {
            "query": query,
            "answer": answer_text.strip(),
            "sources": sources,
            "retrieved_documents": [
                {"title": d.metadata.get("title"), "score": d.metadata.get("score", 0)} 
                for d in docs
            ],
        }

