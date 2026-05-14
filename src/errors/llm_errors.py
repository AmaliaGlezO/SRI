class LLMError(Exception):
	"""Base exception for local LLM operations."""


class LLMDependencyError(LLMError):
	"""Raised when required LLM dependencies are missing."""


class LLMModelNotFoundError(LLMError):
	"""Raised when the configured model file or directory cannot be found."""


class LLMGenerationError(LLMError):
	"""Raised when text generation or chat completion fails."""
