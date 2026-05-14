from src.indexing.indexer import TextNormalizer, InvertedIndex
from src.indexing.storage import DocumentStore
from src.retrieval.lm_retriever import LMRetriever
from src.retrieval.query_processor import QueryProcessor
import os
import numpy as np
from src.errors.indexing_errors import IndexingError
from src.errors.llm_errors import LLMError
from src.errors.rag_errors import RAGError
from src.errors.retrieval_errors import RetrievalError
from src.errors.vector_db_errors import VectorDBError
from src.rag.rag import RAGPipeline
from src.vector_db.embeddings import get_embeddings
from src.vector_db.vector_store import VectorStore


def get_or_create_system(normaliser, force=False):
    """Load or create the hybrid retrieval system."""
    #  LMRetriever 
    if not force and os.path.exists("data/index/lm"):
        lm = LMRetriever.load("data/index/lm")
    else:
        docs = DocumentStore().load_all()
        d = docs.all()
        indexer = InvertedIndex(normalizer=normaliser)
        indexer.build(d)
        indexer.save("data/index")
        lm = LMRetriever.from_inverted_index(indexer)
        lm.save("data/index/lm")

    #  Embeddings & Vector Store 
    embeddings = get_embeddings()
    vector_store = VectorStore(embeddings=embeddings)

    if force or vector_store.stats()["num_documents"] == 0:
        docs = DocumentStore().load_all()
        doc_ids = []
        texts = []
        metadatas = []
        for doc in docs:
            doc_id = str(doc.get("id") or doc.get("url", ""))
            doc_ids.append(doc_id)
            texts.append(f"{doc.get('title', '')} {doc.get('content', '')}")
            metadatas.append(doc)

        vector_store.setup(doc_ids, texts, metadatas, reset=True)

    return lm, vector_store


def main():
    try:
        normalizer = TextNormalizer()

        # Initialize both retrieval systems
        lm_retriever, vector_store = get_or_create_system(normalizer, force=True)

        # Initialize LangChain RAG Pipeline
        rag = RAGPipeline(
            retriever_lm=lm_retriever,
            vector_store=vector_store,
            model_path="models/TinyLlama-1.1B-Chat-v1.0-Q4_K_M.gguf",
        )

        query = "dame una lista de Modelos de celulares de la marca samsung 2026"

        res = rag.answer(query=query)

        print("\n--- RESPUESTA GENERADA ---")
        print(res["answer"])
        print("\n--- FUENTES ---")
        for src in res["sources"]:
            print(f"- {src['title']} ({src['url']})")
    except (IndexingError, RetrievalError, VectorDBError, LLMError, RAGError) as exc:
        print(f"[SRI Error] {exc}")


if __name__ == "__main__":
    main()
