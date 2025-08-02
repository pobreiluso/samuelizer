"""
Unified analysis client to replace duplicate implementations.
This consolidates the AnalysisClient classes from meeting_analyzer.py and meeting_minutes.py.
"""
import os
import logging
from typing import Optional, List, Dict, Any

from src.interfaces import TextAnalysisModelInterface
from src.models.model_factory import ModelProviderFactory

logger = logging.getLogger(__name__)


class AnalysisClient:
    """
    Unified analysis client that handles different AI model providers.
    Supports both chat and completion models with proper error handling.
    """
    
    def __init__(
        self, 
        provider: Optional[TextAnalysisModelInterface] = None, 
        provider_name: str = "openai", 
        api_key: Optional[str] = None,
        model_id: str = "gpt-3.5-turbo"
    ):
        """
        Initialize the analysis client.
        
        Args:
            provider: Pre-configured model provider (optional)
            provider_name: Name of the provider to use if none provided
            api_key: API key for the provider (optional)
            model_id: Model identifier to use (optional)
        """
        self.provider = provider
        if not self.provider:
            self.provider = ModelProviderFactory.get_analysis_model(
                provider_name, api_key=api_key
            )
        self.provider_name = provider_name
        self.model_id = model_id
        
        # Configure OpenAI API key if provided
        if api_key and provider_name.lower() == "openai":
            os.environ["OPENAI_API_KEY"] = api_key

    def analyze(
        self, 
        messages: List[Dict[str, str]], 
        model_id: Optional[str] = None, 
        temperature: float = 0.0,
        **kwargs
    ) -> str:
        """
        Analyze text using the configured provider.
        
        Args:
            messages: List of messages in model-compatible format
            model_id: Model identifier to use (optional, uses self.model_id if not provided)
            temperature: Temperature parameter for generation
            **kwargs: Additional parameters for the model
            
        Returns:
            str: Analysis result
            
        Raises:
            Exception: If analysis fails
        """
        model_to_use = model_id or self.model_id
        
        # Limit message content length to avoid token limit errors
        max_content_length = 15000
        for i, message in enumerate(messages):
            if "content" in message and len(message["content"]) > max_content_length:
                logger.warning(
                    f"Message too long ({len(message['content'])} characters). "
                    f"Truncating to {max_content_length} characters."
                )
                messages[i]["content"] = message["content"][:max_content_length]
        
        # Handle OpenAI direct API calls
        if self.provider_name.lower() == "openai":
            return self._analyze_with_openai(messages, model_to_use, temperature, **kwargs)
        
        # Use configured provider
        return self.provider.analyze(messages, model_to_use, temperature=temperature, **kwargs)
        
    def _analyze_with_openai(
        self, 
        messages: List[Dict[str, str]], 
        model_id: str, 
        temperature: float = 0.0,
        **kwargs
    ) -> str:
        """
        Analyze text using OpenAI API directly, handling different model types.
        
        Args:
            messages: List of messages in model-compatible format
            model_id: Model identifier to use
            temperature: Temperature parameter for generation
            **kwargs: Additional parameters for the model
            
        Returns:
            str: Analysis result
        """
        try:
            import openai
            
            # Chat models use the chat completions API
            chat_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4-1106-preview"]
            
            if any(model in model_id for model in chat_models):
                response = openai.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    temperature=temperature,
                    **kwargs
                )
                return response.choices[0].message.content
            else:
                # Legacy completion models
                prompt = messages[0]["content"] if messages else ""
                response = openai.completions.create(
                    model=model_id,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=1000,
                    **kwargs
                )
                return response.choices[0].text.strip()
                
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            raise


class LegacyAnalysisClient:
    """
    Legacy analysis client for backward compatibility.
    This provides the simple interface from meeting_minutes.py.
    """
    
    def __init__(self, client=None):
        """Initialize with optional OpenAI client."""
        if client:
            self.client = client
        else:
            import openai
            self.client = openai
    
    def analyze(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4-1106-preview", 
        temperature: float = 0.0
    ) -> str:
        """
        Analyze text using OpenAI (legacy interface).
        
        Args:
            messages: Messages to send to the model
            model: OpenAI model to use
            temperature: Temperature parameter for generation
            
        Returns:
            str: Analysis result
        """
        response = self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=messages
        )
        return response.choices[0].message.content