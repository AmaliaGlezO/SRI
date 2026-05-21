"""
Indexing module

Provides:
    - InvertedIndex   : builds, queries and persists an inverted index
    - DocumentStore   : JSON-backed document store used by the index
    - TextNormalizer  : tokenisation, cleanup and stop-word removal
    - DocumentChunker: splits documents into smaller chunks
    - MetadataEnricher: enriches documents with computed metadata
"""

from .indexer import InvertedIndex, TextNormalizer
from .storage import DocumentStore
from .chunker import DocumentChunker

__all__ = [
    "InvertedIndex", 
    "TextNormalizer", 
    "DocumentStore",
    "DocumentChunker",

]
