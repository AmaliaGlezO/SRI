#!/usr/bin/env python3

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


def initialize_system(model_path, force=False):
    """Initialize the SRI system components."""
    from src.indexing.indexer import TextNormalizer, InvertedIndex
    from src.indexing.storage import DocumentStore
    from src.retrieval.lm_retriever import LMRetriever
    from src.vector_db.embeddings import get_embeddings, TfidfEmbeddings
    from src.vector_db.vector_store import VectorStore
    from src.rag.rag import RAGPipeline
    from src.generator.answer_generator import AnswerGenerator
    from src.indexing.chunker import DocumentChunker
    from langchain_community.llms import LlamaCpp
    from src.config import MODEL_MAX_TOKENS, MODEL_N_CTX, MODEL_TEMPERATURE, MODEL_VERBOSE
    
    logger.info("Initializing SRI system...")

    indexes_dir = Path("indexes")

    try:
        normalizer = TextNormalizer()
        chuker = DocumentChunker()
        def get_or_create_system(force=force):
            """Load or create the hybrid retrieval system."""
            lm_path = indexes_dir / "lm"
            index_path = indexes_dir / "index"

            shared_chunked_docs = None

            def get_chunked_docs():
                nonlocal shared_chunked_docs
                docs = DocumentStore("data").load_all()
                d = docs.all()
                if shared_chunked_docs is None:
                    docs = DocumentStore("data").load_all()
                    d = docs.all()
                    if not d:
                        shared_chunked_docs = []
                    else:
                        logger.info(f"Chunking {len(d)} documents...")
                        shared_chunked_docs = chuker.chunk_corpus(d)
                        logger.info(f"Created {len(shared_chunked_docs)} chunks")
                return shared_chunked_docs

            # LMRetriever
            if not force and lm_path.exists():
                logger.info("Loading existing LM retriever...")
                lm = LMRetriever.load(lm_path)
            else:
                logger.info("Building new LM retriever...")
                chunked_docs = get_chunked_docs()
                if not chunked_docs:
                    logger.warning("No documents found in data/")
                    return None, None
                
                indexer = InvertedIndex(normalizer=normalizer, chunker=None)
                indexer.build(chunked_docs)
                indexer.save(index_path)
                lm = LMRetriever.from_inverted_index(indexer)
                lm.save(lm_path)

            # Embeddings & Vector Store
            logger.info("Initializing embeddings and vector store...")
            embeddings_path = indexes_dir / "vector_store"
            
            
            #embeddings = get_embeddings()
            
            if 'embeddings' not in locals():
                if (embeddings_path / "tfidf_embeddings.pkl").exists():
                    logger.info("Loading existing TF-IDF embeddings model...")
                    embeddings = TfidfEmbeddings.load(embeddings_path)
                else:
                    logger.info("Initializing new TF-IDF embeddings model...")
                    embeddings = TfidfEmbeddings(normalizer=normalizer)
                
            vector_store = VectorStore(embeddings=embeddings)

            if force or vector_store.stats()["num_documents"] == 0:
                logger.info("Populating vector store with chunks...")
                chunked_docs = get_chunked_docs()
                
                if chunked_docs:
                    doc_ids = []
                    texts = []
                    metadatas = []
                    for chunk in chunked_docs:
                        chunk_id = chunk.get("chunk_id", str(chunk.get("id", "")))
                        doc_ids.append(chunk_id)
                        texts.append(" ".join(normalizer.normalize(chunk.get("content", ""))))
                        metadatas.append(chunk)

                    if isinstance(embeddings, TfidfEmbeddings):
                        embeddings.fit(metadatas)
                        embeddings.save(embeddings_path)
                    
                    vector_store.setup(doc_ids, texts, metadatas, reset=True)
                    logger.info(f"Vector store populated with {len(doc_ids)} chunks")
                else:
                    logger.warning("No chunks available to populate the vector store.")

            return lm, vector_store

        logger.info("Creating retrieval systems...")
        lm_retriever, vector_store = get_or_create_system(force=force)

        # Initialize LangChain RAG Pipeline 
        logger.info("Initializing RAG pipeline (retrieval)...")
        from src.search_internet.searcher import WebSearcher
        from src.retrieval.query_processor import QueryProcessor
        from src.positioning.ranker import ResultRanker
        from src.utils.model_downloader import ModelDownloader
        web_searcher = WebSearcher(normalizer=normalizer)
        query_processor = QueryProcessor(lm_retriever.normalizer)
        ranker = ResultRanker(
            relevance_weight=0.5,
            popularity_weight=0.15,
            freshness_weight=0.2,
            completeness_weight=0.1,
            source_quality_weight=0.05,
        )
        
        rag = RAGPipeline(
            retriever_lm=lm_retriever,
            vector_store=vector_store,
            web_searcher=web_searcher,
            query_processor=query_processor,
            ranker=ranker,
        )
        
        # Initialize standalone Answer Generator (generation only)
        logger.info("Initializing Answer Generator...")
        
        # Find or download model
        model_path_resolved = str(ModelDownloader.ensure_model_exists(model_path))
        logger.info(f"Using model: {model_path_resolved}")
        
        from langchain_community.llms import LlamaCpp
        llm = LlamaCpp(
            model_path=model_path_resolved,
            temperature=MODEL_TEMPERATURE,
            max_tokens=MODEL_MAX_TOKENS,
            n_ctx=MODEL_N_CTX,
            verbose=MODEL_VERBOSE,
        )
        generator = AnswerGenerator(llm=llm)
        
        logger.info("✓ SRI system initialized successfully")
        return rag, get_or_create_system, lm_retriever, vector_store, generator

    except Exception as exc:
        logger.error(f"Failed to initialize system: {exc}", exc_info=True)
        raise


def create_status_checker(rag, lm_retriever, vector_store):
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
                "model_info": rag.llm.model_path if hasattr(rag, 'llm') and hasattr(rag.llm, 'model_path') else "Llama 1.1B",
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
        rag, get_or_create_system, lm_retriever, vector_store, generator = initialize_system(
            model_path, force=False
        )

        # Initialize API
        from src.api.app import app, init_api

        status_checker = create_status_checker(rag, lm_retriever, vector_store)
        init_api(rag, get_or_create_system, status_checker, generator)

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
