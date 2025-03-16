from src.transcription.exceptions import DownloadError

class SlackAPIError(DownloadError):
    """Error en la API de Slack."""
    pass

class SlackRateLimitError(SlackAPIError):
    """Error por límite de tasa en la API de Slack."""
    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after
        message = f"Límite de tasa excedido. Reintentar después de {retry_after} segundos."
        super().__init__(message)

class SlackAuthenticationError(SlackAPIError):
    """Error de autenticación en la API de Slack."""
    pass

class SlackResourceNotFoundError(SlackAPIError):
    """Recurso no encontrado en Slack (canal, usuario, etc.)."""
    pass
