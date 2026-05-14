class RetrievalError(Exception):
	"""Base exception for retrieval components."""


class RetrieverNotInitializedError(RetrievalError):
	"""Raised when a retriever is used before being initialized."""


class RetrieverModelNotFoundError(RetrievalError):
	"""Raised when a persisted retriever model file cannot be found."""


class QueryFormatError(RetrievalError):
	"""Raised when an input query format is invalid."""


class QueryProcessingError(RetrievalError):
	"""Raised when query preprocessing or PRF expansion fails."""
