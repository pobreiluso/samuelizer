"""
Refactored controller with improved separation of concerns and reduced complexity.
This version addresses the code smells identified in the original controller.py.
"""
import os
import logging
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
from src.models.model_factory import ModelProviderFactory
from src.config.provider_manager import ProviderConfigurationManager
from src.utils.audio_file_manager import AudioFileManager, TranscriptionCacheManager

logger = logging.getLogger(__name__)


def run_transcription(api_key: str, file_path: str, diarization: bool, use_cache: bool = True,
                     provider_name: str = "openai", model_id: str = "whisper-1", 
                     force_new_transcription: bool = False, interactive: bool = True) -> str:
    """
    Run transcription with improved separation of concerns and error handling.
    
    Args:
        api_key: API key for the provider
        file_path: Path to the media file
        diarization: Enable speaker diarization
        use_cache: Enable transcription caching
        provider_name: AI provider to use
        model_id: Model ID for transcription
        force_new_transcription: Force new transcription even if cached
        interactive: Enable user prompts for decisions
        
    Returns:
        Transcribed text
    """
    # Configure provider using centralized manager
    ProviderConfigurationManager.setup_environment(provider_name, api_key)

    # Handle audio file preparation
    audio_manager = AudioFileManager()
    audio_file = audio_manager.prepare_audio_file(file_path, interactive)
    
    # Handle transcription caching
    cache_manager = TranscriptionCacheManager(use_cache and not force_new_transcription)
    transcription_options = {
        'diarization': diarization, 
        'model_id': model_id,
        'provider': provider_name
    }
    
    cached_transcription, should_use_cache = cache_manager.check_and_handle_cache(
        audio_file, transcription_options, interactive
    )
    
    if cached_transcription:
        return cached_transcription
    
    # Create transcription service and perform transcription
    return _perform_transcription(
        audio_file, diarization, provider_name, model_id, api_key, 
        cache_manager.cache_service if should_use_cache else None
    )


def _perform_transcription(audio_file: str, diarization: bool, provider_name: str, 
                          model_id: str, api_key: str, cache_service) -> str:
    """Perform the actual transcription with the given parameters."""
    from src.transcription.audio_processor import AudioFileHandler, TranscriptionFileWriter, SpeakerDiarization
    
    # Create transcription client using centralized manager
    transcription_client = ProviderConfigurationManager.create_transcription_client(
        provider_name, api_key
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
    
    transcription = transcription_service.transcribe(
        audio_file, diarization=diarization, use_cache=cache_service is not None
    )
    logger.info("Transcription completed.")
    return transcription


def run_analysis(transcription: str, provider_name: str = "openai", 
                model_id: str = "gpt-3.5-turbo", api_key: str = None) -> dict:
    """
    Run analysis on transcribed text using centralized provider management.
    
    Args:
        transcription: Text to analyze
        provider_name: AI provider to use
        model_id: Model ID for analysis
        api_key: API key for the provider
        
    Returns:
        Dictionary containing analysis results
    """
    # Configure provider using centralized manager
    ProviderConfigurationManager.setup_environment(provider_name, api_key)
        
    # Create analysis client using centralized manager
    analysis_client = ProviderConfigurationManager.create_analysis_client(
        provider_name, api_key, model_id
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
    """Save meeting information to a document file."""
    return DocumentManager.save_to_docx(meeting_info, output_path)