"""
Provider configuration helper to reduce code duplication in CLI commands.
"""
import os
import openai
import logging
from typing import Optional, Dict, Any
from src.exceptions import ProviderConfigurationError, FileFormatError

logger = logging.getLogger(__name__)


class ProviderConfigHelper:
    """Helper class to configure AI providers and handle common setup tasks."""
    
    @staticmethod
    def configure_provider(
        provider: str,
        api_key: Optional[str] = None,
        local: bool = False,
        whisper_size: str = 'base',
        text_model: str = 'facebook/bart-large-cnn'
    ) -> Dict[str, Any]:
        """
        Configure AI provider settings based on user preferences.
        
        Args:
            provider: Provider name (openai, local)
            api_key: API key for the provider
            local: Whether to use local models
            whisper_size: Whisper model size for local mode
            text_model: Text model for local mode
            
        Returns:
            Dict containing configured provider settings
        """
        config = {
            'provider': provider,
            'api_key': api_key,
            'model_id': None
        }
        
        if local:
            config['provider'] = 'local'
            config['model_id'] = whisper_size
            config['text_model'] = text_model
            config['api_key'] = None
            logger.info("Using local models for offline processing")
            return config
        
        if provider.lower() == 'openai':
            if not api_key:
                raise ProviderConfigurationError("OpenAI API key is required for OpenAI provider")
            
            ProviderConfigHelper._setup_openai_api(api_key)
            config['api_key'] = api_key
            config['model_id'] = 'whisper-1'
        
        return config
    
    @staticmethod
    def _setup_openai_api(api_key: str) -> None:
        """Setup OpenAI API configuration."""
        os.environ["OPENAI_API_KEY"] = api_key
        if hasattr(openai, 'api_key'):
            openai.api_key = api_key
    
    @staticmethod
    def validate_supported_format(file_path: str, supported_formats: list) -> bool:
        """
        Validate if file format is supported.
        
        Args:
            file_path: Path to the file
            supported_formats: List of supported file extensions
            
        Returns:
            bool: True if format is supported
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in supported_formats
    
    @staticmethod
    def get_or_prompt_api_key(
        provided_key: Optional[str],
        provider: str,
        env_var: str = 'OPENAI_API_KEY'
    ) -> Optional[str]:
        """
        Get API key from parameter, environment, or prompt user.
        
        Args:
            provided_key: API key provided by user
            provider: Provider name for prompting
            env_var: Environment variable name
            
        Returns:
            str: API key or None if not needed
        """
        if provided_key:
            return provided_key
        
        env_key = os.environ.get(env_var)
        if env_key:
            return env_key
        
        # For now, return None - the CLI will handle prompting
        # This allows for better separation of concerns
        return None