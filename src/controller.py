import os
import logging
import openai
from src.utils.audio_extractor import AudioExtractor
from src.transcription.meeting_transcription import AudioTranscriptionService, OpenAITranscriptionClient
from src.transcription.meeting_analyzer import MeetingAnalyzer, DocumentManager
from src.slack.download_slack_channel import SlackDownloader, SlackConfig
from src.slack.http_client import RequestsClient
from src.exporters.json_exporter import JSONExporter
from src.config.config import Config
from src.transcription.cache import FileCache, TranscriptionCacheService

logger = logging.getLogger(__name__)

def run_transcription(api_key: str, file_path: str, diarization: bool, use_cache: bool = True) -> str:
    os.environ["OPENAI_API_KEY"] = api_key
    openai.api_key = api_key

    # If file is not MP3, extract audio from video
    if not file_path.lower().endswith('.mp3'):
        audio_file = AudioExtractor.extract_audio(file_path)
    else:
        audio_file = file_path

    # Import dependencies for audio processing
    from src.transcription.audio_processor import AudioFileHandler, TranscriptionFileWriter, SpeakerDiarization
    
    # Set up cache service if enabled
    cache_service = None
    if use_cache:
        file_cache = FileCache()
        cache_service = TranscriptionCacheService(file_cache)

    transcription_service = AudioTranscriptionService(
        transcription_client=OpenAITranscriptionClient(),
        diarization_service=SpeakerDiarization(),
        file_handler=AudioFileHandler(),
        file_writer=TranscriptionFileWriter(),
        model="whisper-1",
        cache_service=cache_service
    )
    transcription = transcription_service.transcribe(audio_file, diarization=diarization, use_cache=use_cache)
    logger.info("Transcription completed.")
    return transcription

def run_analysis(transcription: str) -> dict:
    analyzer = MeetingAnalyzer(transcription)
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
