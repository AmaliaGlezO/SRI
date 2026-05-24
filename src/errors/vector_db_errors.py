class VectorDBError(Exception):
	"""Base exception for vector database components."""


class EmptyDocumentListError(VectorDBError):
	"""Raised when an embeddings fit operation receives no documents."""


class EmbeddingModelNotFittedError(VectorDBError):
	"""Raised when embeddings are used before fitting."""


class EmbeddingsModelNotFoundError(VectorDBError):
	"""Raised when a persisted embeddings model file is missing."""


class VectorStoreOperationError(VectorDBError):
	"""Raised when vector store setup, insert or search operations fail."""
	
class TimeoutError(Exception):
    pass
