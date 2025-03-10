import openai
import logging
from typing import List, Dict, Any, BinaryIO, Optional
from src.interfaces import AIModelProviderInterface, TranscriptionModelInterface, TextAnalysisModelInterface

logger = logging.getLogger(__name__)

class OpenAIProvider(AIModelProviderInterface, TranscriptionModelInterface, TextAnalysisModelInterface):
    """
    Adaptador para los servicios de OpenAI
    """
    def __init__(self, api_key: Optional[str] = None, client=None):
        """
        Inicializa el adaptador de OpenAI
        
        Args:
            api_key: Clave API de OpenAI (opcional si ya está configurada en el entorno)
            client: Cliente de OpenAI preconfigurado (opcional)
        """
        self.client = client or openai
        if api_key:
            self.client.api_key = api_key
    
    def get_name(self) -> str:
        """
        Obtiene el nombre del proveedor
        
        Returns:
            str: Nombre del proveedor
        """
        return "OpenAI"
    
    def get_available_models(self) -> List[str]:
        """
        Obtiene la lista de modelos disponibles
        
        Returns:
            List[str]: Lista de identificadores de modelos disponibles
        """
        # Lista de modelos comunes de OpenAI
        return [
            "whisper-1",  # Para transcripción
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-1106-preview"
        ]
    
    def transcribe(self, audio_file: BinaryIO, model_id: str = "whisper-1", **kwargs) -> str:
        """
        Transcribe un archivo de audio a texto usando OpenAI
        
        Args:
            audio_file: Archivo de audio abierto en modo binario
            model_id: Identificador del modelo a utilizar (por defecto whisper-1)
            **kwargs: Parámetros adicionales para la API de OpenAI
            
        Returns:
            str: Texto transcrito
        """
        try:
            response_format = kwargs.get('response_format', 'text')
            response = self.client.audio.transcriptions.create(
                model=model_id,
                file=audio_file,
                response_format=response_format
            )
            return response
        except Exception as e:
            logger.error(f"Error en la transcripción con OpenAI: {e}")
            raise
    
    def analyze(self, messages: List[Dict[str, str]], model_id: str = "gpt-4", **kwargs) -> str:
        """
        Analiza un texto utilizando un modelo de OpenAI
        
        Args:
            messages: Lista de mensajes en formato compatible con OpenAI
            model_id: Identificador del modelo a utilizar
            **kwargs: Parámetros adicionales para la API de OpenAI
            
        Returns:
            str: Resultado del análisis
        """
        try:
            temperature = kwargs.get('temperature', 0)
            response = self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error en el análisis con OpenAI: {e}")
            raise
