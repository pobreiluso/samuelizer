import os
import openai
import logging
from tqdm import tqdm
from typing import Dict, Any, Optional
from src.interfaces import TranscriptionService, CacheInterface
from src.transcription.audio_processor import AudioFileHandler, TranscriptionFileWriter, SpeakerDiarization
from src.transcription.cache import FileCache, TranscriptionCacheService

logger = logging.getLogger(__name__)

# Eliminamos la duplicación de AudioFileHandler y TranscriptionFileWriter, 
# ya que se importan de audio_processor.py

class TranscriptionClient:
    """
    Cliente de transcripción que utiliza el proveedor de modelos configurado.
    """
    def __init__(self, provider=None, provider_name="openai", api_key=None):
        """
        Inicializa el cliente de transcripción
        
        Args:
            provider: Proveedor de modelos preconfigurado (opcional)
            provider_name: Nombre del proveedor a utilizar si no se proporciona uno
            api_key: Clave API para el proveedor (opcional)
        """
        from src.models.model_factory import ModelProviderFactory
        
        self.provider = provider
        if not self.provider:
            self.provider = ModelProviderFactory.get_transcription_model(
                provider_name, api_key=api_key
            )
        self.provider_name = provider_name

    def transcribe(self, audio_file, model_id, **kwargs):
        """
        Transcribe un archivo de audio utilizando el proveedor configurado
        
        Args:
            audio_file: Archivo de audio abierto en modo binario
            model_id: Identificador del modelo a utilizar
            **kwargs: Parámetros adicionales para el modelo
            
        Returns:
            str: Texto transcrito
        """
        try:
            return self.provider.transcribe(audio_file, model_id, **kwargs)
        except Exception as e:
            logger.error(f"Error en la transcripción con {self.provider_name}: {e}")
            raise

class AudioTranscriptionService(TranscriptionService):
    """
    Service for transcribing audio files.
    Dependencies are injected to follow the Dependency Inversion Principle.
    """
    def __init__(self, transcription_client=None, diarization_service=None, file_handler=None, 
                 audio_file_handler=None, file_writer=None, model_id="whisper-1", provider_name="openai", 
                 api_key=None, cache_service=None):
        self.model_id = model_id
        self.provider_name = provider_name
        
        # Inicializar el cliente de transcripción si no se proporciona
        if transcription_client is None:
            self.transcription_client = TranscriptionClient(
                provider_name=provider_name, 
                api_key=api_key
            )
        else:
            self.transcription_client = transcription_client
            
        self.diarization_service = diarization_service
        # Permitir ambos nombres de parámetros para compatibilidad
        self.file_handler = file_handler if file_handler is not None else audio_file_handler
        self.file_writer = file_writer
        
        # Initialize cache service if not provided
        if cache_service is None:
            file_cache = FileCache()
            self.cache_service = TranscriptionCacheService(file_cache)
        else:
            self.cache_service = cache_service

    def _transcribe_segment(self, audio_file_path, start_time, end_time):
        # Try to extract a segment with the injected file_handler.
        try:
            if self.file_handler:
                segment_path = self.file_handler.extract_segment(audio_file_path, start_time, end_time)
            else:
                # Fallback to the AudioFileHandler class if file_handler is not provided
                from src.transcription.audio_processor import AudioFileHandler
                segment_path = AudioFileHandler.extract_segment(audio_file_path, start_time, end_time)
        except Exception as extraction_error:
            logger.error(f"Segment extraction failed: {extraction_error}. Falling back to whole file transcription.")
            with open(audio_file_path, 'rb') as audio_file:
                return self.transcription_client.transcribe(audio_file, model_id=self.model_id)
        try:
            with open(segment_path, 'rb') as segment_file:
                segment_transcription = self.transcription_client.transcribe(
                    segment_file, 
                    model_id=self.model_id
                )
        finally:
            os.unlink(segment_path)
        return segment_transcription

    def transcribe_whole(self, audio_file_path):
        return self.transcribe(audio_file_path, diarization=False)

    def transcribe_with_diarization(self, audio_file_path):
        return self.transcribe(audio_file_path, diarization=True)

    def transcribe(self, audio_file_path, diarization: bool = False, use_cache: bool = True) -> str:
        try:
            # Check if we have a cache service and if the transcription is cached
            if use_cache and self.cache_service:
                transcription_options = {
                    'diarization': diarization, 
                    'model_id': self.model_id,
                    'provider': self.provider_name
                }
                
                if self.cache_service.has_cached_transcription(audio_file_path, transcription_options):
                    logger.info("Using cached transcription...")
                    cached_transcription = self.cache_service.get_cached_transcription(
                        audio_file_path, transcription_options)
                    if cached_transcription:
                        return cached_transcription
            
            logger.info(f"Starting transcription with provider: {self.provider_name}, model: {self.model_id}...")
            if diarization:
                logger.info("Diarization enabled. Processing audio segments...")
                segments = self.diarization_service.detect_speakers(audio_file_path)
                full_transcript = ""
                for seg in segments:
                    seg_text = self._transcribe_segment(audio_file_path, start_time=seg['start'], end_time=seg['end'])
                    full_transcript += f"[{seg['speaker']}]: {seg_text}\n"
                self.file_writer.save_transcription(full_transcript, audio_file_path)
                
                # Cache the result if we have a cache service and caching is enabled
                if use_cache and self.cache_service:
                    transcription_options = {
                        'diarization': diarization, 
                        'model_id': self.model_id,
                        'provider': self.provider_name
                    }
                    self.cache_service.cache_transcription(
                        audio_file_path, full_transcript, transcription_options)
                
                return full_transcript
            else:
                with open(audio_file_path, 'rb') as audio_file:
                    transcription = self.transcription_client.transcribe(
                        audio_file, 
                        model_id=self.model_id,
                        response_format="text"
                    )
                self.file_writer.save_transcription(transcription, audio_file_path)
                
                # Cache the result if we have a cache service and caching is enabled
                if use_cache and self.cache_service:
                    transcription_options = {
                        'diarization': diarization, 
                        'model_id': self.model_id,
                        'provider': self.provider_name
                    }
                    self.cache_service.cache_transcription(
                        audio_file_path, transcription, transcription_options)
                
                return transcription
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise Exception(f"Transcription failed: {e}")
import os
import logging
from src.transcription.exceptions import TranscriptionError

logger = logging.getLogger(__name__)

class SegmentTranscriber:
    def __init__(self, transcription_client, file_handler, model):
        self.transcription_client = transcription_client
        self.file_handler = file_handler
        self.model = model

    def transcribe_segment(self, audio_file_path, start_time, end_time):
        try:
            segment_path = self.file_handler.extract_segment(audio_file_path, start_time, end_time)
            with open(segment_path, 'rb') as f:
                transcription = self.transcription_client.transcribe(f, model=self.model)
            os.unlink(segment_path)
            return transcription
        except Exception as e:
            logger.error(f"Error transcribing segment from {start_time} to {end_time}: {e}")
            raise TranscriptionError(f"Segment transcription failed: {e}") from e
