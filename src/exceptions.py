"""
Custom exceptions for better error handling throughout the application.
"""


class SamuelizerError(Exception):
    """Base exception for all Samuelizer-related errors."""
    pass


class ProviderConfigurationError(SamuelizerError):
    """Raised when there's an issue configuring an AI provider."""
    pass


class TranscriptionError(SamuelizerError):
    """Base exception for transcription-related errors."""
    pass


class AudioProcessingError(TranscriptionError):
    """Raised when audio processing fails."""
    pass


class ModelNotAvailableError(TranscriptionError):
    """Raised when a requested model is not available."""
    pass


class APIQuotaExceededError(SamuelizerError):
    """Raised when API quota is exceeded."""
    pass


class APIRateLimitError(SamuelizerError):
    """Raised when API rate limit is hit."""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class FileFormatError(SamuelizerError):
    """Raised when file format is not supported."""
    pass


class CacheError(SamuelizerError):
    """Raised when cache operations fail."""
    pass


class ConfigurationError(SamuelizerError):
    """Raised when configuration is invalid or missing."""
    pass