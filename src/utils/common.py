"""
Common utility functions to reduce code duplication across modules.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path to ensure exists
        
    Returns:
        Path object of the directory
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def safe_json_load(file_path: Union[str, Path], default: Any = None) -> Any:
    """
    Safely load JSON from a file with error handling.
    
    Args:
        file_path: Path to JSON file
        default: Default value to return if loading fails
        
    Returns:
        Loaded JSON data or default value
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load JSON from {file_path}: {e}")
        return default


def safe_json_save(data: Any, file_path: Union[str, Path]) -> bool:
    """
    Safely save data to JSON file with error handling.
    
    Args:
        data: Data to save
        file_path: Path to save JSON file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_directory_exists(Path(file_path).parent)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")
        return False


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_file_hash(file_path: Union[str, Path]) -> Optional[str]:
    """
    Get SHA-256 hash of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        SHA-256 hash string or None if error
    """
    try:
        import hashlib
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash file {file_path}: {e}")
        return None


def validate_api_key(api_key: Optional[str], provider: str = "openai") -> bool:
    """
    Basic validation for API keys.
    
    Args:
        api_key: API key to validate
        provider: Provider name for validation rules
        
    Returns:
        True if key appears valid, False otherwise
    """
    if not api_key:
        return False
    
    # Basic format validation
    if provider.lower() == "openai":
        return api_key.startswith("sk-") and len(api_key) > 10
    
    # For other providers, just check it's not empty
    return len(api_key.strip()) > 0


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries, with later ones taking precedence.
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def normalize_text(text: str) -> str:
    """
    Normalize text by removing extra whitespace and newlines.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    import re
    text = re.sub(r'\s+', ' ', text.strip())
    return text


def format_timestamp(timestamp: float, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format Unix timestamp to human-readable string.
    
    Args:
        timestamp: Unix timestamp
        format_str: Format string for strftime
        
    Returns:
        Formatted timestamp string
    """
    import time
    try:
        return time.strftime(format_str, time.localtime(timestamp))
    except (ValueError, OSError):
        return "Invalid timestamp"


def get_env_var(key: str, default: Any = None, required: bool = False) -> Any:
    """
    Get environment variable with optional default and required validation.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        required: Whether the variable is required
        
    Returns:
        Environment variable value or default
        
    Raises:
        ValueError: If required variable is not found
    """
    value = os.environ.get(key, default)
    
    if required and not value:
        raise ValueError(f"Required environment variable '{key}' not found")
    
    return value