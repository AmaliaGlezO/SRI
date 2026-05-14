class ExtractDataError(Exception):
	"""Base exception for data extraction components."""


class SpiderConfigurationError(ExtractDataError):
	"""Raised when a spider class is missing required configuration."""


class MissingSpiderNameError(SpiderConfigurationError):
	"""Raised when a spider does not define a name."""


class MissingSpiderSourceError(SpiderConfigurationError):
	"""Raised when a spider does not define a source."""
