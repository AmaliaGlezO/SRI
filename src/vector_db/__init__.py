"""
Vector database module.

Provides:
    - BasicEmbeddings : LangChain-compatible embeddings using basic TF-IDF
    - VectorStore   : Chroma-backed vector database with cosine search
"""

from .embeddings import BasicEmbeddings
from .vector_store import VectorStore

__all__ = ["BasicEmbeddings", "VectorStore"]
