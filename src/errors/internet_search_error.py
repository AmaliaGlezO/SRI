class InternetSearchError(Exception):
	"""Base exception for internet search operations."""


class WebSearchExecutionError(InternetSearchError):
	"""Raised when an internet search provider call fails."""
