"""
Media transcription and analysis service.
Extracted from cli.py to reduce complexity and improve maintainability.
"""
import os
import logging
from typing import Dict, Any, Optional
from tqdm import tqdm

from src.config.command_configs import MediaTranscriptionConfig
from src.config.provider_manager import ProviderConfigurationManager
from src.utils.audio_extractor import AudioExtractor
from src.utils.error_handlers import ErrorContext
from src.transcription.meeting_minutes import (
    AudioTranscriptionService,
    MeetingAnalyzer,
    DocumentManager,
    VideoDownloader
)
from src.transcription.meeting_transcription import TranscriptionClient
from src.transcription.audio_processor import (
    AudioFileHandler, 
    TranscriptionFileWriter, 
    SpeakerDiarization
)

logger = logging.getLogger(__name__)


class MediaTranscriptionService:
    """Service for handling media file transcription and analysis."""
    
    def __init__(self, config: MediaTranscriptionConfig):
        """
        Initialize the media transcription service.
        
        Args:
            config: Configuration for media transcription
        """
        self.config = config
        self.provider_manager = ProviderConfigurationManager()
    
    def process_media_file(self, provider_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a media file through transcription and analysis.
        
        Args:
            provider_config: Provider configuration from ProviderConfigurationManager
            
        Returns:
            Dict containing analysis results
            
        Raises:
            FileNotFoundError: If the media file doesn't exist
            ValueError: If the file format is not supported
        """
        with ErrorContext("media file processing", log_traceback=True):
            # Validate file existence and format
            self._validate_file()
            
            # Handle Google Drive downloads if needed
            file_path = self._handle_drive_download()
            
            # Extract and optimize audio
            audio_file = self._prepare_audio_file(file_path)
            
            # Transcribe audio
            transcription = self._transcribe_audio(audio_file, provider_config)
            
            # Analyze transcription
            analysis_results = self._analyze_transcription(transcription, provider_config)
            
            # Save results if requested
            if self.config.output:
                DocumentManager.save_to_docx(analysis_results, str(self.config.output))
                logger.info(f"Document saved: {self.config.output}")
            
            return analysis_results
    
    def _validate_file(self) -> None:
        """Validate the input file exists and has supported format."""
        if not os.path.exists(self.config.file_path):
            raise FileNotFoundError(f"File does not exist: {self.config.file_path}")
        
        supported_formats = AudioExtractor.get_supported_formats()
        file_ext = os.path.splitext(self.config.file_path)[1].lower()
        
        if file_ext not in supported_formats:
            raise ValueError(
                f"Unsupported file format. Supported formats: {', '.join(supported_formats)}"
            )
    
    def _handle_drive_download(self) -> str:
        """Handle Google Drive file download if needed."""
        if self.config.drive_url:
            logger.info("Downloading file from Google Drive...")
            return VideoDownloader.download_from_google_drive(self.config.drive_url)
        return self.config.file_path
    
    def _prepare_audio_file(self, file_path: str) -> str:
        """Extract and optimize audio from the media file."""
        if file_path.lower().endswith('.mp3'):
            return file_path
        
        logger.info("Extracting audio from media file...")
        return AudioExtractor.extract_audio(
            file_path,
            target_bitrate=self.config.optimize,
            remove_silences=not self.config.keep_silence,
            max_size_mb=self.config.max_size
        )
    
    def _transcribe_audio(self, audio_file: str, provider_config: Dict[str, Any]) -> str:
        """Transcribe the audio file to text."""
        logger.info(f"Starting transcription: {audio_file}")
        
        # Create transcription client
        transcription_client = self.provider_manager.create_transcription_client(
            provider_config['provider'],
            provider_config['api_key']
        )
        
        # Set up transcription service
        service = AudioTranscriptionService(
            transcription_client=transcription_client,
            diarization_service=SpeakerDiarization(),
            audio_file_handler=AudioFileHandler(),
            file_writer=TranscriptionFileWriter(),
            model_id=provider_config['model_id'],
            provider_name=provider_config['provider'],
            api_key=provider_config['api_key']
        )
        
        # Perform transcription
        use_cache = not self.config.no_cache
        transcription = service.transcribe(
            audio_file,
            diarization=self.config.diarization,
            use_cache=use_cache
        )
        
        logger.info(f"Transcription completed. Length: {len(transcription)} characters")
        
        # Save transcription file
        self._save_transcription_file(audio_file, transcription)
        
        return transcription
    
    def _save_transcription_file(self, audio_file: str, transcription: str) -> None:
        """Save transcription to a text file."""
        output_txt = os.path.splitext(audio_file)[0] + "_transcription.txt"
        if not os.path.exists(output_txt):
            with open(output_txt, 'w', encoding='utf-8') as f:
                f.write(transcription)
            logger.info(f"Transcription saved to: {output_txt}")
    
    def _analyze_transcription(
        self, 
        transcription: str, 
        provider_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the transcription to extract insights."""
        logger.info("Starting content analysis...")
        
        # Create analysis client
        analysis_client = self.provider_manager.create_analysis_client(
            provider_config['provider'],
            provider_config['api_key'],
            provider_config['model_id']
        )
        
        # Create analyzer
        analyzer = MeetingAnalyzer(
            transcription=transcription,
            analysis_client=analysis_client
        )
        
        # Perform analysis based on template
        if self.config.template == 'all':
            return self._perform_comprehensive_analysis(analyzer)
        else:
            result = analyzer.analyze(self.config.template)
            return {self.config.template: result}
    
    def _perform_comprehensive_analysis(self, analyzer: MeetingAnalyzer) -> Dict[str, Any]:
        """Perform comprehensive analysis with progress tracking."""
        meeting_info = {}
        
        with tqdm(total=4, desc="Analyzing content", unit="task") as pbar:
            meeting_info['abstract_summary'] = analyzer.summarize()
            pbar.update(1)
            
            meeting_info['key_points'] = analyzer.extract_key_points()
            pbar.update(1)
            
            meeting_info['action_items'] = analyzer.extract_action_items()
            pbar.update(1)
            
            meeting_info['sentiment'] = analyzer.analyze_sentiment()
            pbar.update(1)
        
        return meeting_info