from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Union, BinaryIO
from datetime import datetime
from pathlib import Path

class AIModelProviderInterface(ABC):
    """
    Interfaz base para proveedores de modelos de IA
    """
    @abstractmethod
    def get_name(self) -> str:
        """
        Obtiene el nombre del proveedor
        
        Returns:
            str: Nombre del proveedor
        """
        pass
        
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Obtiene la lista de modelos disponibles
        
        Returns:
            List[str]: Lista de identificadores de modelos disponibles
        """
        pass

class TranscriptionModelInterface(ABC):
    """
    Interfaz para modelos de transcripción de audio a texto
    """
    @abstractmethod
    def transcribe(self, audio_file: BinaryIO, model_id: str, **kwargs) -> str:
        """
        Transcribe un archivo de audio a texto
        
        Args:
            audio_file: Archivo de audio abierto en modo binario
            model_id: Identificador del modelo a utilizar
            **kwargs: Parámetros adicionales específicos del modelo
            
        Returns:
            str: Texto transcrito
        """
        pass

class TextAnalysisModelInterface(ABC):
    """
    Interfaz para modelos de análisis de texto
    """
    @abstractmethod
    def analyze(self, messages: List[Dict[str, str]], model_id: str, **kwargs) -> str:
        """
        Analiza un texto utilizando un modelo específico
        
        Args:
            messages: Lista de mensajes en formato compatible con el modelo
            model_id: Identificador del modelo a utilizar
            **kwargs: Parámetros adicionales específicos del modelo
            
        Returns:
            str: Resultado del análisis
        """
        pass

class TranscriptionService(ABC):
    @abstractmethod
    def transcribe(self, audio_file_path, diarization: bool = False):
        """
        Transcribe audio to text
        
        Args:
            audio_file_path: Path to the audio file
            diarization: Whether to identify different speakers
            
        Returns:
            str: Transcribed text
        """
        pass

class AIModelProviderInterface(ABC):
    """
    Interfaz base para proveedores de modelos de IA
    """
    @abstractmethod
    def get_name(self) -> str:
        """
        Obtiene el nombre del proveedor
        
        Returns:
            str: Nombre del proveedor
        """
        pass
        
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Obtiene la lista de modelos disponibles
        
        Returns:
            List[str]: Lista de identificadores de modelos disponibles
        """
        pass

class TranscriptionModelInterface(ABC):
    """
    Interfaz para modelos de transcripción de audio a texto
    """
    @abstractmethod
    def transcribe(self, audio_file: BinaryIO, model_id: str, **kwargs) -> str:
        """
        Transcribe un archivo de audio a texto
        
        Args:
            audio_file: Archivo de audio abierto en modo binario
            model_id: Identificador del modelo a utilizar
            **kwargs: Parámetros adicionales específicos del modelo
            
        Returns:
            str: Texto transcrito
        """
        pass

class TextAnalysisModelInterface(ABC):
    """
    Interfaz para modelos de análisis de texto
    """
    @abstractmethod
    def analyze(self, messages: List[Dict[str, str]], model_id: str, **kwargs) -> str:
        """
        Analiza un texto utilizando un modelo específico
        
        Args:
            messages: Lista de mensajes en formato compatible con el modelo
            model_id: Identificador del modelo a utilizar
            **kwargs: Parámetros adicionales específicos del modelo
            
        Returns:
            str: Resultado del análisis
        """
        pass

class CacheInterface(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """
        Retrieve a cached transcription
        
        Args:
            key: Unique identifier for the cached item
            
        Returns:
            Optional[str]: The cached transcription or None if not found
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: str) -> None:
        """
        Store a transcription in the cache
        
        Args:
            key: Unique identifier for the cached item
            value: The transcription to cache
        """
        pass
    
    @abstractmethod
    def has(self, key: str) -> bool:
        """
        Check if a transcription exists in the cache
        
        Args:
            key: Unique identifier for the cached item
            
        Returns:
            bool: True if the item exists in cache, False otherwise
        """
        pass
    
    @abstractmethod
    def invalidate(self, key: str) -> None:
        """
        Remove a transcription from the cache
        
        Args:
            key: Unique identifier for the cached item
        """
        pass

class ExporterInterface(ABC):
    @abstractmethod
    def export(self, data, output_path: str) -> str:
        """
        Export data to a file
        
        Args:
            data: The data to export
            output_path: Path where to save the exported file
            
        Returns:
            str: Path to the exported file
        """
        pass
        
class MessageExporterInterface(ExporterInterface):
    @abstractmethod
    def export_messages(self, 
                        messages: List[Dict], 
                        channel_id: str, 
                        output_dir: str,
                        start_date: Optional[datetime] = None, 
                        end_date: Optional[datetime] = None) -> str:
        """
        Export messages to a file
        
        Args:
            messages: List of message dictionaries
            channel_id: ID of the channel
            output_dir: Directory where to save the exported file
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            str: Path to the exported file
        """
        pass

class SlackServiceInterface(ABC):
    @abstractmethod
    def get_channel_info(self) -> Dict:
        """
        Get information about a Slack channel
        
        Returns:
            Dict: Channel information
        """
        pass
        
    @abstractmethod
    def fetch_messages(self) -> List[Dict]:
        """
        Fetch messages from a Slack channel
        
        Returns:
            List[Dict]: List of message dictionaries
        """
        pass
        
    @abstractmethod
    def get_user_info(self, user_id: str) -> str:
        """
        Get user information from Slack
        
        Args:
            user_id: ID of the user
            
        Returns:
            str: User display name or ID if not found
        """
        pass
