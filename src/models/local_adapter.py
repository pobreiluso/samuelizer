import os
import logging
from typing import List, Dict, BinaryIO, Optional, Any
import torch
from transformers import pipeline  # Para análisis de texto local
from src.interfaces import AIModelProviderInterface, TranscriptionModelInterface, TextAnalysisModelInterface

# Importar whisper con manejo de errores
try:
    import whisper
except ImportError:
    logging.error("No se pudo importar el módulo 'whisper'. Asegúrate de instalar openai-whisper correctamente.")
    logging.error("Ejecuta: poetry add --no-interaction openai-whisper")
    whisper = None

logger = logging.getLogger(__name__)

class LocalProvider(AIModelProviderInterface, TranscriptionModelInterface, TextAnalysisModelInterface):
    """
    Adaptador para modelos locales (Whisper y Transformers)
    """
    def __init__(self, api_key: Optional[str] = None, client=None, 
                 whisper_model_size: str = "base", 
                 text_model_id: str = "facebook/bart-large-cnn"):
        """
        Inicializa el proveedor de modelos locales
        
        Args:
            api_key: No se utiliza, incluido para compatibilidad con la interfaz
            client: No se utiliza, incluido para compatibilidad con la interfaz
            whisper_model_size: Tamaño del modelo Whisper a utilizar
            text_model_id: ID del modelo de Hugging Face para análisis de texto
        """
        self.whisper_model_size = whisper_model_size
        self.text_model_id = text_model_id
        self.whisper_model = None
        self.text_model = None
        
        # Verificar disponibilidad de GPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"LocalProvider inicializado. Usando dispositivo: {self.device}")
        
    def get_name(self) -> str:
        """
        Obtiene el nombre del proveedor
        
        Returns:
            str: Nombre del proveedor
        """
        return "local"
        
    def get_available_models(self) -> List[str]:
        """
        Obtiene los modelos disponibles
        
        Returns:
            List[str]: Lista de modelos disponibles
        """
        whisper_models = ["tiny", "base", "small", "medium", "large"]
        text_models = ["facebook/bart-large-cnn", "google/flan-t5-base", "google/flan-t5-large"]
        return whisper_models + text_models
        
    def _load_whisper_model(self):
        """
        Carga el modelo Whisper bajo demanda
        """
        if whisper is None:
            raise ImportError("El módulo 'whisper' no está disponible. Instala openai-whisper con 'poetry add openai-whisper'")
            
        if self.whisper_model is None:
            logger.info(f"Cargando modelo Whisper '{self.whisper_model_size}'...")
            self.whisper_model = whisper.load_model(self.whisper_model_size, device=self.device)
            logger.info(f"Modelo Whisper cargado correctamente")
            
    def _load_text_model(self):
        """
        Carga el modelo de análisis de texto bajo demanda
        """
        if self.text_model is None:
            logger.info(f"Cargando modelo de análisis '{self.text_model_id}'...")
            self.text_model = pipeline(
                "summarization", 
                model=self.text_model_id,
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info(f"Modelo de análisis cargado correctamente")
            
    def transcribe(self, audio_file: BinaryIO, model_id: str = "base", **kwargs) -> str:
        """
        Transcribe audio usando Whisper localmente
        
        Args:
            audio_file: Archivo de audio abierto en modo binario
            model_id: Tamaño del modelo Whisper a utilizar
            **kwargs: Argumentos adicionales
            
        Returns:
            str: Texto transcrito
        """
        self.whisper_model_size = model_id
        self._load_whisper_model()
        
        # Guardar el archivo temporalmente
        temp_path = "temp_audio.mp3"
        with open(temp_path, "wb") as f:
            f.write(audio_file.read())
            
        try:
            # Transcribir con Whisper
            logger.info(f"Transcribiendo audio con Whisper {model_id}...")
            result = self.whisper_model.transcribe(temp_path)
            logger.info(f"Transcripción completada. Longitud: {len(result['text'])} caracteres")
            return result["text"]
        except Exception as e:
            logger.error(f"Error durante la transcripción local: {e}")
            raise
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    def analyze(self, messages: List[Dict[str, str]], model_id: str = "facebook/bart-large-cnn", **kwargs) -> str:
        """
        Analizar texto usando modelos de Hugging Face localmente
        
        Args:
            messages: Lista de mensajes a analizar
            model_id: ID del modelo de Hugging Face a utilizar
            **kwargs: Argumentos adicionales
            
        Returns:
            str: Resultado del análisis
        """
        self.text_model_id = model_id
        self._load_text_model()
        
        # Preparar el texto para análisis
        text = ""
        for msg in messages:
            if isinstance(msg, dict):
                content = msg.get("content", "")
                if not content and "text" in msg:
                    content = msg.get("text", "")
                text += content + "\n"
            elif isinstance(msg, str):
                text += msg + "\n"
        
        # Dividir en chunks si es necesario (para manejar textos largos)
        max_length = 1024
        chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        
        results = []
        logger.info(f"Analizando texto con modelo {model_id}...")
        for i, chunk in enumerate(chunks):
            logger.info(f"Procesando chunk {i+1}/{len(chunks)}...")
            summary = self.text_model(chunk, max_length=150, min_length=30, do_sample=False)
            results.append(summary[0]['summary_text'])
            
        final_result = " ".join(results)
        logger.info(f"Análisis completado. Longitud: {len(final_result)} caracteres")
        return final_result
