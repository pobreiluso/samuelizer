import logging
from typing import Dict, Type, Optional
from src.interfaces import AIModelProviderInterface, TranscriptionModelInterface, TextAnalysisModelInterface

logger = logging.getLogger(__name__)

class ModelProviderFactory:
    """
    Fábrica para crear instancias de proveedores de modelos
    """
    _providers = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class) -> None:
        """
        Registra un nuevo proveedor de modelos
        
        Args:
            name: Nombre del proveedor
            provider_class: Clase del proveedor que implementa las interfaces necesarias
        """
        cls._providers[name.lower()] = provider_class
        logger.info(f"Proveedor de modelos registrado: {name}")
    
    @classmethod
    def get_provider(cls, provider_name: str, **kwargs) -> AIModelProviderInterface:
        """
        Obtiene una instancia de un proveedor de modelos
        
        Args:
            provider_name: Nombre del proveedor
            **kwargs: Argumentos para inicializar el proveedor
            
        Returns:
            AIModelProviderInterface: Instancia del proveedor
            
        Raises:
            ValueError: Si el proveedor no está registrado
        """
        # Importar el adaptador de OpenAI si no hay proveedores registrados
        if not cls._providers:
            from src.models.openai_adapter import OpenAIProvider
            from src.models.local_adapter import LocalProvider
            cls.register_provider("openai", OpenAIProvider)
            cls.register_provider("local", LocalProvider)
        
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            available = ", ".join(cls._providers.keys())
            raise ValueError(f"Proveedor '{provider_name}' no registrado. Proveedores disponibles: {available}")
        
        return provider_class(**kwargs)
    
    @classmethod
    def get_transcription_model(cls, provider_name: str, **kwargs) -> TranscriptionModelInterface:
        """
        Obtiene un modelo de transcripción de un proveedor específico
        
        Args:
            provider_name: Nombre del proveedor
            **kwargs: Argumentos para inicializar el proveedor
            
        Returns:
            TranscriptionModelInterface: Modelo de transcripción
            
        Raises:
            ValueError: Si el proveedor no implementa la interfaz de transcripción
        """
        provider = cls.get_provider(provider_name, **kwargs)
        if not isinstance(provider, TranscriptionModelInterface):
            raise ValueError(f"El proveedor '{provider_name}' no implementa la interfaz de transcripción")
        
        return provider
    
    @classmethod
    def get_analysis_model(cls, provider_name: str, **kwargs) -> TextAnalysisModelInterface:
        """
        Obtiene un modelo de análisis de texto de un proveedor específico
        
        Args:
            provider_name: Nombre del proveedor
            **kwargs: Argumentos para inicializar el proveedor
            
        Returns:
            TextAnalysisModelInterface: Modelo de análisis de texto
            
        Raises:
            ValueError: Si el proveedor no implementa la interfaz de análisis de texto
        """
        provider = cls.get_provider(provider_name, **kwargs)
        if not isinstance(provider, TextAnalysisModelInterface):
            raise ValueError(f"El proveedor '{provider_name}' no implementa la interfaz de análisis de texto")
        
        return provider
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, Type]:
        """
        Obtiene la lista de proveedores disponibles
        
        Returns:
            Dict[str, Type]: Diccionario de proveedores registrados
        """
        # Importar los adaptadores si no hay proveedores registrados
        if not cls._providers:
            from src.models.openai_adapter import OpenAIProvider
            from src.models.local_adapter import LocalProvider
            cls.register_provider("openai", OpenAIProvider)
            cls.register_provider("local", LocalProvider)
            
        return cls._providers.copy()
