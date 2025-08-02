"""
Refactored analysis client with better separation of concerns and error handling.
Addresses the complex function and magic number issues identified in meeting_analyzer.py.
"""
import logging
import os
from typing import Optional, List, Dict, Any
from src.transcription.exceptions import AnalysisError
from src.interfaces import TranscriptionService, TextAnalysisModelInterface
from src.models.model_factory import ModelProviderFactory

logger = logging.getLogger(__name__)

# Configuration constants to replace magic numbers
MAX_CONTENT_LENGTH = 15000
MAX_ANALYSIS_LENGTH = 100
FALLBACK_MODEL = "gpt-3.5-turbo"

# Model type classification
CHAT_MODELS = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4-1106-preview"]


class AnalysisClientConfig:
    """Configuration object for analysis client to reduce parameter lists."""
    
    def __init__(self, provider_name: str = "openai", api_key: Optional[str] = None,
                 model_id: str = "gpt-3.5-turbo", max_content_length: int = MAX_CONTENT_LENGTH):
        self.provider_name = provider_name
        self.api_key = api_key
        self.model_id = model_id
        self.max_content_length = max_content_length


class MessageProcessor:
    """Handles message preprocessing and validation."""
    
    @staticmethod
    def validate_and_truncate_messages(messages: List[Dict[str, str]], 
                                      max_length: int = MAX_CONTENT_LENGTH) -> List[Dict[str, str]]:
        """
        Validate and truncate messages to prevent API errors.
        
        Args:
            messages: List of messages to process
            max_length: Maximum allowed content length
            
        Returns:
            Processed messages list
        """
        processed_messages = []
        
        for i, message in enumerate(messages):
            if "content" not in message:
                logger.warning(f"Message {i} missing 'content' field, skipping")
                continue
                
            content = message["content"]
            if len(content) > max_length:
                logger.warning(
                    f"Message {i} too long ({len(content)} chars). "
                    f"Truncating to {max_length} chars."
                )
                processed_message = message.copy()
                processed_message["content"] = content[:max_length]
                processed_messages.append(processed_message)
            else:
                processed_messages.append(message)
        
        return processed_messages


class ModelTypeClassifier:
    """Classifies models into chat or completion types."""
    
    @staticmethod
    def is_chat_model(model_id: str) -> bool:
        """Determine if model is a chat model based on its ID."""
        return any(chat_name in model_id for chat_name in CHAT_MODELS)


class OpenAIAnalysisHandler:
    """Handles OpenAI-specific analysis operations."""
    
    def __init__(self, config: AnalysisClientConfig):
        self.config = config
        self._setup_environment()
    
    def _setup_environment(self) -> None:
        """Set up environment variables for OpenAI."""
        if self.config.api_key:
            os.environ["OPENAI_API_KEY"] = self.config.api_key
    
    def analyze(self, messages: List[Dict[str, str]], model_id: Optional[str] = None, 
                **kwargs) -> str:
        """
        Analyze text using OpenAI API with appropriate model type handling.
        
        Args:
            messages: Messages to analyze
            model_id: Model ID to use (optional)
            **kwargs: Additional model parameters
            
        Returns:
            Analysis result
        """
        model_to_use = model_id or self.config.model_id
        
        if ModelTypeClassifier.is_chat_model(model_to_use):
            return self._analyze_with_chat_model(messages, model_to_use, **kwargs)
        else:
            return self._analyze_with_completion_fallback(messages, model_to_use, **kwargs)
    
    def _analyze_with_chat_model(self, messages: List[Dict[str, str]], 
                                model_id: str, **kwargs) -> str:
        """Analyze using chat completion API."""
        import openai
        
        try:
            response = openai.ChatCompletion.create(
                model=model_id,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Chat model analysis failed: {e}")
            raise AnalysisError(f"Failed to analyze with chat model {model_id}: {e}") from e
    
    def _analyze_with_completion_fallback(self, messages: List[Dict[str, str]], 
                                         model_id: str, **kwargs) -> str:
        """Try completion model with fallback to chat model."""
        try:
            return self._analyze_with_completion_model(messages, model_id, **kwargs)
        except Exception as completion_error:
            logger.warning(
                f"Completion model {model_id} failed: {completion_error}. "
                f"Using {FALLBACK_MODEL} as fallback."
            )
            return self._analyze_with_chat_model(messages, FALLBACK_MODEL, **kwargs)
    
    def _analyze_with_completion_model(self, messages: List[Dict[str, str]], 
                                      model_id: str, **kwargs) -> str:
        """Analyze using text completion API."""
        import openai
        
        # Convert messages to prompt text for completion models
        prompt = "\n".join([msg.get("content", "") for msg in messages])
        
        try:
            response = openai.Completion.create(
                model=model_id,
                prompt=prompt,
                max_tokens=kwargs.get("max_tokens", MAX_ANALYSIS_LENGTH),
                **{k: v for k, v in kwargs.items() if k != "max_tokens"}
            )
            return response.choices[0].text.strip()
        except Exception as e:
            logger.error(f"Completion model analysis failed: {e}")
            raise AnalysisError(f"Failed to analyze with completion model {model_id}: {e}") from e


class RefactoredAnalysisClient:
    """
    Modern analysis client with improved architecture and error handling.
    Replaces the deprecated AnalysisClient with better separation of concerns.
    """
    
    def __init__(self, config: AnalysisClientConfig, 
                 provider: Optional[TextAnalysisModelInterface] = None):
        """
        Initialize the analysis client.
        
        Args:
            config: Configuration object
            provider: Pre-configured model provider (optional)
        """
        self.config = config
        self.provider = provider or self._create_provider()
        self.message_processor = MessageProcessor()
        
        # Initialize provider-specific handlers
        if config.provider_name.lower() == "openai":
            self.openai_handler = OpenAIAnalysisHandler(config)
    
    def _create_provider(self) -> TextAnalysisModelInterface:
        """Create model provider using factory."""
        return ModelProviderFactory.get_analysis_model(
            self.config.provider_name, 
            api_key=self.config.api_key
        )
    
    def analyze(self, messages: List[Dict[str, str]], model_id: Optional[str] = None, 
                **kwargs) -> str:
        """
        Analyze text using the configured provider.
        
        Args:
            messages: Messages to analyze
            model_id: Model ID to use (optional)
            **kwargs: Additional model parameters
            
        Returns:
            Analysis result
            
        Raises:
            AnalysisError: If analysis fails
        """
        try:
            # Preprocess messages
            processed_messages = self.message_processor.validate_and_truncate_messages(
                messages, self.config.max_content_length
            )
            
            if not processed_messages:
                raise AnalysisError("No valid messages to analyze")
            
            # Route to appropriate handler
            if self.config.provider_name.lower() == "openai":
                return self.openai_handler.analyze(processed_messages, model_id, **kwargs)
            else:
                return self._analyze_with_provider(processed_messages, model_id, **kwargs)
        
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise AnalysisError(f"Failed to analyze text: {e}") from e
    
    def _analyze_with_provider(self, messages: List[Dict[str, str]], 
                              model_id: Optional[str] = None, **kwargs) -> str:
        """Analyze using the configured provider."""
        model_to_use = model_id or self.config.model_id
        return self.provider.analyze(messages, model_to_use, **kwargs)