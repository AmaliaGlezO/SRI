class IndexingError(Exception):
	"""Base exception for indexing and document storage components."""


class NltkResourceError(IndexingError):
	"""Raised when required NLTK resources cannot be loaded."""


class InvalidDocumentError(IndexingError):
	"""Raised when an input document is invalid for indexing."""


class IndexPersistenceError(IndexingError):
	"""Raised when persisting an index fails."""


class IndexLoadError(IndexingError):
	"""Raised when loading an index from disk fails."""


class DocumentStoreError(IndexingError):
	"""Raised for document store loading and parsing issues."""


class DocumentParseError(DocumentStoreError):
	"""Raised when a JSON/JSONL document cannot be parsed."""


class SnapshotLoadError(DocumentStoreError):
	"""Raised when a document snapshot cannot be reconstructed."""
