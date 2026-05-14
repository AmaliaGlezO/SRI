class RAGError(Exception):
	"""Base exception for RAG pipeline operations."""


class RAGPipelineInitializationError(RAGError):
	"""Raised when the RAG pipeline cannot be initialized."""


class RAGRetrievalError(RAGError):
	"""Raised when document retrieval in the RAG pipeline fails."""


class RAGAnswerGenerationError(RAGError):
	"""Raised when answer generation in the RAG pipeline fails."""
