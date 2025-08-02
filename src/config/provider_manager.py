"""
Centralized provider configuration management to reduce code duplication.
"""
import os
import logging
from typing import Dict, Any, Optional
import click
from src.utils.provider_helper import ProviderConfigHelper
from src.exceptions import ProviderConfigurationError

logger = logging.getLogger(__name__)


class ProviderConfigurationManager:
    """Manages AI provider configuration for all commands."""
    
    @staticmethod
    def configure_provider(
        ctx: click.Context,
        provider: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Configure provider settings from context and parameters.
        Centralizes provider configuration logic across all CLI commands.
        
        Args:
            ctx: Click context with global options
            provider: Provider name (e.g., 'openai', 'local')
            api_key: API key for the provider
            model: Model ID to use
            
        Returns:
            Dict containing provider configuration
            
        Raises:
            ProviderConfigurationError: If configuration fails
        """
        local = ctx.obj.get('local', False)
        whisper_size = ctx.obj.get('whisper_size', 'base')
        text_model = ctx.obj.get('text_model', 'facebook/bart-large-cnn')
        
        try:
            config = ProviderConfigHelper.configure_provider(
                provider=provider,
                api_key=api_key,
                local=local,
                whisper_size=whisper_size,
                text_model=text_model
            )
            
            # Override model if specifically provided
            if model and not local:
                config['model_id'] = model
                
            return config
        except ProviderConfigurationError as e:
            if 'API key is required' in str(e) and provider == 'openai':
                api_key = click.prompt('OpenAI API key', hide_input=True)
                return ProviderConfigurationManager.configure_provider(
                    ctx, provider, api_key, model
                )
            raise
    
    @staticmethod
    def setup_environment(provider: str, api_key: Optional[str]) -> None:
        """
        Set up environment variables for the specified provider.
        
        Args:
            provider: Provider name
            api_key: API key to set in environment
        """
        if provider.lower() == "openai" and api_key:
            os.environ["OPENAI_API_KEY"] = api_key
    
    @staticmethod
    def create_analysis_client(provider: str, api_key: str, model_id: Optional[str] = None):
        """
        Create an analysis client with the specified configuration.
        
        Args:
            provider: Provider name
            api_key: API key
            model_id: Model ID to use
            
        Returns:
            Analysis client instance
        """
        from src.transcription.meeting_analyzer import AnalysisClient
        
        return AnalysisClient(
            provider_name=provider,
            api_key=api_key,
            model_id=model_id
        )
    
    @staticmethod
    def create_transcription_client(provider: str, api_key: str):
        """
        Create a transcription client with the specified configuration.
        
        Args:
            provider: Provider name
            api_key: API key
            
        Returns:
            Transcription client instance
        """
        from src.transcription.meeting_transcription import TranscriptionClient
        
        return TranscriptionClient(
            provider_name=provider,
            api_key=api_key
        )