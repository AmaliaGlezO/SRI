"""Centralized logging configuration for SRI."""

import logging
import sys
from pathlib import Path

# Create logs directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "sri.log"),
        logging.StreamHandler(sys.stdout)
    ]
)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)


rag_logger = get_logger("RAG")
indexing_logger = get_logger("Indexing")
vector_logger = get_logger("VectorDB")
search_logger = get_logger("Search")
api_logger = get_logger("API")
query_expansion_logger = get_logger("QueryExpansion")