import os
import pytest
import tempfile
import shutil
from pathlib import Path
from src.transcription.cache import FileCache, TranscriptionCacheService

@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def file_cache(temp_cache_dir):
    """Create a FileCache instance with a temporary directory"""
    return FileCache(temp_cache_dir)

@pytest.fixture
def cache_service(file_cache):
    """Create a TranscriptionCacheService with the file cache"""
    return TranscriptionCacheService(file_cache)

@pytest.fixture
def sample_audio_file():
    """Create a temporary audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        temp_file.write(b'dummy audio content')
        temp_path = temp_file.name
    
    yield temp_path
    os.unlink(temp_path)

def test_file_cache_set_get(file_cache):
    """Test setting and getting values from the file cache"""
    # Set a value in the cache
    file_cache.set("test_key", "test_value")
    
    # Get the value from the cache
    value = file_cache.get("test_key")
    
    assert value == "test_value"

def test_file_cache_has(file_cache):
    """Test checking if a key exists in the cache"""
    # Key should not exist initially
    assert not file_cache.has("test_key")
    
    # Set a value
    file_cache.set("test_key", "test_value")
    
    # Now the key should exist
    assert file_cache.has("test_key")

def test_file_cache_invalidate(file_cache):
    """Test invalidating a cache entry"""
    # Set a value
    file_cache.set("test_key", "test_value")
    
    # Invalidate the entry
    file_cache.invalidate("test_key")
    
    # Key should no longer exist
    assert not file_cache.has("test_key")

def test_cache_service_workflow(cache_service, sample_audio_file):
    """Test the complete workflow of the cache service"""
    options = {"diarization": False, "model": "whisper-1"}
    transcription = "This is a test transcription."
    
    # Initially, there should be no cached transcription
    assert not cache_service.has_cached_transcription(sample_audio_file, options)
    
    # Cache a transcription
    cache_service.cache_transcription(sample_audio_file, transcription, options)
    
    # Now there should be a cached transcription
    assert cache_service.has_cached_transcription(sample_audio_file, options)
    
    # Get the cached transcription
    cached = cache_service.get_cached_transcription(sample_audio_file, options)
    assert cached == transcription
    
    # Invalidate the cached transcription
    cache_service.invalidate_transcription(sample_audio_file, options)
    
    # Now there should be no cached transcription again
    assert not cache_service.has_cached_transcription(sample_audio_file, options)

def test_cache_key_generation(cache_service, sample_audio_file):
    """Test that different options generate different cache keys"""
    options1 = {"diarization": False, "model": "whisper-1"}
    options2 = {"diarization": True, "model": "whisper-1"}
    
    # Cache with different options
    cache_service.cache_transcription(sample_audio_file, "Transcription 1", options1)
    cache_service.cache_transcription(sample_audio_file, "Transcription 2", options2)
    
    # Both should be cached
    assert cache_service.has_cached_transcription(sample_audio_file, options1)
    assert cache_service.has_cached_transcription(sample_audio_file, options2)
    
    # And they should have different values
    assert cache_service.get_cached_transcription(sample_audio_file, options1) == "Transcription 1"
    assert cache_service.get_cached_transcription(sample_audio_file, options2) == "Transcription 2"
