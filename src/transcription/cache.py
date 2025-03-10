import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from src.interfaces import CacheInterface

logger = logging.getLogger(__name__)

class FileCache(CacheInterface):
    """
    File-based implementation of the cache interface.
    Stores transcriptions in files for persistence between runs.
    """
    
    def __init__(self, cache_dir: str = ".cache/transcriptions"):
        """
        Initialize the file cache
        
        Args:
            cache_dir: Directory where cache files will be stored
        """
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """Create the cache directory if it doesn't exist"""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """
        Get the file path for a cache key
        
        Args:
            key: Cache key
            
        Returns:
            Path: Path to the cache file
        """
        # Create a hash of the key to use as filename
        hashed_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hashed_key}.json"
    
    def get(self, key: str) -> Optional[str]:
        """
        Retrieve a cached transcription
        
        Args:
            key: Unique identifier for the cached item
            
        Returns:
            Optional[str]: The cached transcription or None if not found
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                logger.info(f"Cache hit for key: {key[:8]}...")
                return cache_data.get('transcription')
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read cache file: {e}")
            return None
    
    def set(self, key: str, value: str) -> None:
        """
        Store a transcription in the cache
        
        Args:
            key: Unique identifier for the cached item
            value: The transcription to cache
        """
        cache_path = self._get_cache_path(key)
        
        try:
            cache_data = {
                'transcription': value,
                'timestamp': os.path.getmtime(cache_path) if cache_path.exists() else None
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Cached transcription for key: {key[:8]}...")
        except IOError as e:
            logger.error(f"Failed to write to cache: {e}")
    
    def has(self, key: str) -> bool:
        """
        Check if a transcription exists in the cache
        
        Args:
            key: Unique identifier for the cached item
            
        Returns:
            bool: True if the item exists in cache, False otherwise
        """
        cache_path = self._get_cache_path(key)
        return cache_path.exists()
    
    def invalidate(self, key: str) -> None:
        """
        Remove a transcription from the cache
        
        Args:
            key: Unique identifier for the cached item
        """
        cache_path = self._get_cache_path(key)
        
        if cache_path.exists():
            try:
                os.remove(cache_path)
                logger.info(f"Invalidated cache for key: {key[:8]}...")
            except IOError as e:
                logger.error(f"Failed to invalidate cache: {e}")

class TranscriptionCacheService:
    """
    Service that manages transcription caching.
    Provides a higher-level API on top of the cache implementation.
    """
    
    def __init__(self, cache: CacheInterface):
        """
        Initialize the transcription cache service
        
        Args:
            cache: Cache implementation to use
        """
        self.cache = cache
    
    def get_cached_transcription(self, audio_file_path: str, options: Dict[str, Any] = None) -> Optional[str]:
        """
        Get a cached transcription if available
        
        Args:
            audio_file_path: Path to the audio file
            options: Dictionary of transcription options
            
        Returns:
            Optional[str]: Cached transcription or None if not found
        """
        key = self._generate_cache_key(audio_file_path, options)
        return self.cache.get(key)
    
    def cache_transcription(self, audio_file_path: str, transcription: str, options: Dict[str, Any] = None) -> None:
        """
        Cache a transcription result
        
        Args:
            audio_file_path: Path to the audio file
            transcription: Transcription text to cache
            options: Dictionary of transcription options
        """
        key = self._generate_cache_key(audio_file_path, options)
        self.cache.set(key, transcription)
    
    def has_cached_transcription(self, audio_file_path: str, options: Dict[str, Any] = None) -> bool:
        """
        Check if a transcription is cached
        
        Args:
            audio_file_path: Path to the audio file
            options: Dictionary of transcription options
            
        Returns:
            bool: True if cached, False otherwise
        """
        key = self._generate_cache_key(audio_file_path, options)
        return self.cache.has(key)
    
    def invalidate_transcription(self, audio_file_path: str, options: Dict[str, Any] = None) -> None:
        """
        Invalidate a cached transcription
        
        Args:
            audio_file_path: Path to the audio file
            options: Dictionary of transcription options
        """
        key = self._generate_cache_key(audio_file_path, options)
        self.cache.invalidate(key)
    
    def _generate_cache_key(self, file_path: str, options: Dict[str, Any] = None) -> str:
        """
        Generate a unique cache key based on file path and options
        
        Args:
            file_path: Path to the audio file
            options: Dictionary of transcription options
            
        Returns:
            str: Unique cache key
        """
        if options is None:
            options = {}
        
        # Get file metadata
        file_stat = os.stat(file_path)
        file_info = {
            'path': os.path.abspath(file_path),
            'size': file_stat.st_size,
            'mtime': file_stat.st_mtime,
            'options': options
        }
        
        # Create a string representation and hash it
        key_str = json.dumps(file_info, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
