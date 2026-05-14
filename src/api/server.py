#!/usr/bin/env python3
"""Entry point for starting the SRI RAG API server."""

import logging
import sys
from pathlib import Path

from src.config import API_HOST, API_PORT, MODEL_PATH

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def initialize_system(model_path):
    """Initialize the SRI system components."""
    from src.indexing.indexer import TextNormalizer, InvertedIndex
    from src.indexing.storage import DocumentStore
    from src.retrieval.lm_retriever import LMRetriever
    from src.vector_db.embeddings import get_embeddings
    from src.vector_db.vector_store import VectorStore
    from src.rag.rag import RAGPipeline

    logger.info("Initializing SRI system...")

    indexes_dir = Path("indexes")

    try:
        normalizer = TextNormalizer()

        def get_or_create_system(force=False):
            """Load or create the hybrid retrieval system."""
            lm_path = indexes_dir / "lm"
            index_path = indexes_dir / "index"
            
            # LMRetriever
            if not force and lm_path.exists():
                logger.info("Loading existing LM retriever...")
                lm = LMRetriever.load(lm_path)
            else:
                logger.info("Building new LM retriever...")
                docs = DocumentStore("data").load_all()
                d = docs.all()
                if not d:
                    logger.warning("No documents found in data/")
                    return None, None
                indexer = InvertedIndex(normalizer=normalizer)
                indexer.build(d)
                indexer.save(index_path)
                lm = LMRetriever.from_inverted_index(indexer)
                lm.save(lm_path)

            # Embeddings & Vector Store
            logger.info("Initializing embeddings and vector store...")
            embeddings = get_embeddings()
            vector_store = VectorStore(embeddings=embeddings)

            if force or vector_store.stats()["num_documents"] == 0:
                logger.info("Populating vector store...")
                docs = DocumentStore("data").load_all()
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

        # Initialize both retrieval systems
        logger.info("Creating retrieval systems...")
        lm_retriever, vector_store = get_or_create_system(force=False)

        # Initialize LangChain RAG Pipeline
        logger.info("Initializing RAG pipeline...")
        rag = RAGPipeline(
            retriever_lm=lm_retriever,
            vector_store=vector_store,
            model_path=model_path,
        )

        logger.info("✓ SRI system initialized successfully")
        return rag, get_or_create_system, lm_retriever, vector_store

    except Exception as exc:
        logger.error(f"Failed to initialize system: {exc}", exc_info=True)
        raise


def create_status_checker(lm_retriever, vector_store):
    """Create a status checker function."""

    def check_status():
        """Check the status of all components."""
        try:
            lm_stats = lm_retriever.stats() if lm_retriever else None
            vector_stats = vector_store.stats() if vector_store else None

            return {
                "status": "healthy",
                "lm_retriever_available": lm_retriever is not None,
                "vector_store_available": vector_store is not None,
                "lm_stats": lm_stats,
                "vector_stats": vector_stats,
                "message": "All systems operational",
            }
        except Exception as exc:
            logger.error(f"Error checking status: {exc}")
            return {
                "status": "degraded",
                "lm_retriever_available": False,
                "vector_store_available": False,
                "message": f"Error: {exc}",
            }

    return check_status


def main(model_path):
    """Main entry point."""
    try:
        # Initialize system
        rag, get_or_create_system, lm_retriever, vector_store = initialize_system(model_path)

        # Initialize API
        from src.api.app import app, init_api

        status_checker = create_status_checker(lm_retriever, vector_store)
        init_api(rag, get_or_create_system, status_checker)

        logger.info("✓ API initialized successfully")
        logger.info("Starting FastAPI server...")
        logger.info("API available at: http://localhost:8000")
        logger.info("Docs available at: http://localhost:8000/docs")

        import uvicorn

        uvicorn.run(
            app,
            host=API_HOST,
            port=API_PORT,
            log_level="info",
        )

    except Exception as exc:
        logger.error(f"Fatal error: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main(model_path=MODEL_PATH)
