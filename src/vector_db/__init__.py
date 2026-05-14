"""
Vector database module.

Provides:
    - TfidfEmbeddings : LangChain-compatible embeddings using TF-IDF
    - VectorStore    : Chroma-backed vector database with cosine search
"""

from .embeddings import TfidfEmbeddings, get_embeddings
from .vector_store import VectorStore

__all__ = ["TfidfEmbeddings", "get_embeddings", "VectorStore"]
