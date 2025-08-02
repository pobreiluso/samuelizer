"""
Audio file management utilities to handle file optimization and user interactions.
Extracted from controller.py to reduce complexity and improve maintainability.
"""
import os
import time
import logging
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioFileManager:
    """Manages audio file operations including optimization and user interactions."""
    
    def __init__(self):
        self.optimized_cache = {}
    
    def prepare_audio_file(self, file_path: str, interactive: bool = True) -> str:
        """
        Prepare audio file for transcription, handling optimization as needed.
        
        Args:
            file_path: Path to the input file
            interactive: Whether to prompt user for decisions
            
        Returns:
            Path to the prepared audio file
        """
        if not file_path.lower().endswith('.mp3'):
            return self._extract_audio_from_video(file_path)
        else:
            return self._handle_mp3_optimization(file_path, interactive)
    
    def _extract_audio_from_video(self, file_path: str) -> str:
        """Extract audio from video file."""
        from src.utils.audio_extractor import AudioExtractor
        logger.info(f"Extracting audio from video file: {file_path}")
        return AudioExtractor.extract_audio(file_path)
    
    def _handle_mp3_optimization(self, file_path: str, interactive: bool) -> str:
        """Handle MP3 file optimization with user interaction."""
        from src.utils.audio_optimizer import AudioOptimizer
        
        # Check for existing optimized versions
        optimized_path = self._find_existing_optimized_file(file_path)
        
        if optimized_path and interactive:
            if self._prompt_use_existing_optimized(optimized_path):
                logger.info(f"Using existing optimized audio file: {optimized_path}")
                return optimized_path
        elif optimized_path and not interactive:
            # In non-interactive mode, use existing optimized file
            logger.info(f"Using existing optimized audio file: {optimized_path}")
            return optimized_path
        
        # Create new optimized version if needed
        if AudioOptimizer.needs_optimization(file_path):
            return self._create_optimized_file(file_path)
        else:
            return file_path
    
    def _find_existing_optimized_file(self, file_path: str) -> Optional[str]:
        """Find existing optimized version of the audio file."""
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        dir_path = os.path.dirname(file_path) or "."
        
        try:
            optimized_files = [
                f for f in os.listdir(dir_path) 
                if f.startswith(base_name) and '_optimized_' in f and f.endswith('.mp3')
            ]
            
            if optimized_files:
                # Sort by modification time (most recent first)
                optimized_files.sort(
                    key=lambda f: os.path.getmtime(os.path.join(dir_path, f)), 
                    reverse=True
                )
                return os.path.join(dir_path, optimized_files[0])
        except OSError as e:
            logger.warning(f"Error accessing directory {dir_path}: {e}")
        
        return None
    
    def _prompt_use_existing_optimized(self, optimized_path: str) -> bool:
        """Prompt user whether to use existing optimized file."""
        file_name = os.path.basename(optimized_path)
        response = input(
            f"Found an optimized audio version ({file_name}). Use it? (yes/no): "
        ).lower().strip()
        return response in ['y', 'yes', 's', 'si', 'sí']
    
    def _create_optimized_file(self, file_path: str) -> str:
        """Create a new optimized version of the audio file."""
        from src.utils.audio_optimizer import AudioOptimizer
        
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = os.path.dirname(file_path) or "recordings"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = int(time.time())
        output_audio = os.path.join(output_dir, f"{base_name}_optimized_{timestamp}.mp3")
        
        logger.info(f"Creating optimized audio file: {output_audio}")
        return AudioOptimizer.optimize_audio(file_path, output_audio)


class TranscriptionCacheManager:
    """Manages transcription caching logic and user interactions."""
    
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        self.cache_service = None
        
        if use_cache:
            from src.transcription.cache import FileCache, TranscriptionCacheService
            file_cache = FileCache()
            self.cache_service = TranscriptionCacheService(file_cache)
    
    def check_and_handle_cache(
        self, 
        audio_file: str, 
        transcription_options: dict, 
        interactive: bool = True
    ) -> Tuple[Optional[str], bool]:
        """
        Check for cached transcription and handle user interaction.
        
        Args:
            audio_file: Path to audio file
            transcription_options: Transcription configuration
            interactive: Whether to prompt user for decisions
            
        Returns:
            Tuple of (cached_transcription, should_use_cache)
        """
        if not self.cache_service:
            return None, False
        
        if not self.cache_service.has_cached_transcription(audio_file, transcription_options):
            return None, self.use_cache
        
        if interactive:
            if self._prompt_use_cached_transcription():
                cached_transcription = self.cache_service.get_cached_transcription(
                    audio_file, transcription_options
                )
                if cached_transcription:
                    logger.info("Using cached transcription...")
                    return cached_transcription, True
                else:
                    logger.warning("Could not retrieve cached transcription. Proceeding with new transcription.")
                    return None, self.use_cache
            else:
                logger.info("User chose not to use cached transcription. Proceeding with new transcription.")
                return None, False
        else:
            # In non-interactive mode, use cache if available
            cached_transcription = self.cache_service.get_cached_transcription(
                audio_file, transcription_options
            )
            if cached_transcription:
                logger.info("Using cached transcription (non-interactive mode)...")
                return cached_transcription, True
        
        return None, self.use_cache
    
    def _prompt_use_cached_transcription(self) -> bool:
        """Prompt user whether to use cached transcription."""
        response = input("Found a cached transcription. Use it? (yes/no): ").lower().strip()
        return response in ['y', 'yes', 's', 'si', 'sí']