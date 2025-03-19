import os
import logging
from src.utils.audio_extractor import AudioExtractor
from src.transcription.meeting_transcription import AudioTranscriptionService, TranscriptionClient
from src.transcription.meeting_analyzer import MeetingAnalyzer, DocumentManager, AnalysisClient
from src.slack.download_slack_channel import SlackDownloader, SlackConfig
from src.slack.http_client import RequestsClient
from src.slack.pagination import SlackPaginator
from src.slack.user_cache import SlackUserCache
from src.slack.filters import SlackMessageFilter
from src.slack.exceptions import SlackAPIError, SlackRateLimitError
from src.slack.utils import parse_slack_link
from src.exporters.json_exporter import JSONExporter
from src.config.config import Config
from src.transcription.cache import FileCache, TranscriptionCacheService
from src.models.model_factory import ModelProviderFactory

logger = logging.getLogger(__name__)

def run_transcription(api_key: str, file_path: str, diarization: bool, use_cache: bool = True,
                     provider_name: str = "openai", model_id: str = "whisper-1") -> str:
    # Configurar la clave API para el proveedor seleccionado
    if provider_name.lower() == "openai":
        os.environ["OPENAI_API_KEY"] = api_key

    # If file is not MP3, extract audio from video
    if not file_path.lower().endswith('.mp3'):
        from src.utils.audio_optimizer import AudioOptimizer
        audio_file = AudioExtractor.extract_audio(file_path)
    else:
        # Check if MP3 needs optimization
        from src.utils.audio_optimizer import AudioOptimizer
        if AudioOptimizer.needs_optimization(file_path):
            output_dir = os.path.dirname(file_path) or "recordings"
            os.makedirs(output_dir, exist_ok=True)
            output_audio = os.path.join(output_dir, os.path.splitext(os.path.basename(file_path))[0] + '_optimized.mp3')
            audio_file = AudioOptimizer.optimize_audio(file_path, output_audio)
        else:
            audio_file = file_path

    # Import dependencies for audio processing
    from src.transcription.audio_processor import AudioFileHandler, TranscriptionFileWriter, SpeakerDiarization
    
    # Set up cache service if enabled
    cache_service = None
    if use_cache:
        file_cache = FileCache()
        cache_service = TranscriptionCacheService(file_cache)

    # Crear el cliente de transcripción con el proveedor seleccionado
    transcription_client = TranscriptionClient(
        provider_name=provider_name,
        api_key=api_key
    )

    transcription_service = AudioTranscriptionService(
        transcription_client=transcription_client,
        diarization_service=SpeakerDiarization(),
        audio_file_handler=AudioFileHandler(),
        file_writer=TranscriptionFileWriter(),
        model_id=model_id,
        provider_name=provider_name,
        api_key=api_key,
        cache_service=cache_service
    )
    transcription = transcription_service.transcribe(audio_file, diarization=diarization, use_cache=use_cache)
    logger.info("Transcription completed.")
    return transcription

def run_analysis(transcription: str, provider_name: str = "openai", 
                model_id: str = "gpt-3.5-turbo", api_key: str = None) -> dict:
    # Configurar la clave API para el proveedor seleccionado
    if provider_name.lower() == "openai" and api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        
    # Crear el cliente de análisis con el proveedor seleccionado
    analysis_client = AnalysisClient(
        provider_name=provider_name,
        api_key=api_key,
        model_id=model_id
    )
    
    analyzer = MeetingAnalyzer(
        transcription=transcription,
        analysis_client=analysis_client
    )
    
    meeting_info = {
        'abstract_summary': analyzer.summarize(),
        'key_points': analyzer.extract_key_points(),
        'action_items': analyzer.extract_action_items(),
        'sentiment': analyzer.analyze_sentiment()
    }
    logger.info("Analysis completed.")
    return meeting_info

def save_meeting_info(meeting_info: dict, output_path: str) -> str:
    return DocumentManager.save_to_docx(meeting_info, output_path)
