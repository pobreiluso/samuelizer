# Samuelizer API Documentation

This document provides detailed information about the Samuelizer API, including interfaces, classes, and usage examples.

## Core Interfaces

### TranscriptionService

Interface for audio transcription services.

```python
class TranscriptionService(ABC):
    @abstractmethod
    def transcribe(self, audio_file_path, diarization: bool = False):
        """
        Transcribe audio to text
        
        Args:
            audio_file_path: Path to the audio file
            diarization: Whether to identify different speakers
            
        Returns:
            str: Transcribed text
        """
        pass
```

### AIModelProviderInterface

Base interface for AI model providers.

```python
class AIModelProviderInterface(ABC):
    @abstractmethod
    def get_name(self) -> str:
        """
        Get the provider name
        """
        pass
        
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get available models
        """
        pass
```

### TranscriptionModelInterface

Interface for transcription models.

```python
class TranscriptionModelInterface(ABC):
    @abstractmethod
    def transcribe(self, audio_file: BinaryIO, model_id: str, **kwargs) -> str:
        """
        Transcribe an audio file
        """
        pass
```

### TextAnalysisModelInterface

Interface for text analysis models.

```python
class TextAnalysisModelInterface(ABC):
    @abstractmethod
    def analyze(self, messages: List[Dict[str, str]], model_id: str, **kwargs) -> str:
        """
        Analyze text
        """
        pass
```

### CacheInterface

Interface for caching services.

```python
class CacheInterface(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Retrieve a cached item"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: str) -> None:
        """Store an item in the cache"""
        pass
    
    @abstractmethod
    def has(self, key: str) -> bool:
        """Check if an item exists in the cache"""
        pass
    
    @abstractmethod
    def invalidate(self, key: str) -> None:
        """Remove an item from the cache"""
        pass
```

## Key Classes

### AudioTranscriptionService

Service for transcribing audio files.

```python
class AudioTranscriptionService(TranscriptionService):
    def __init__(self, transcription_client=None, diarization_service=None, 
                 audio_file_handler=None, file_writer=None, model_id="whisper-1", 
                 provider_name="openai", api_key=None, cache_service=None):
        # Initialize service
        
    def transcribe(self, audio_file_path, diarization: bool = False, use_cache: bool = True) -> str:
        """
        Transcribe an audio file
        """
```

### MeetingAnalyzer

Analyzes meeting transcriptions.

```python
class MeetingAnalyzer:
    def __init__(self, transcription: str, analysis_client=None, prompt_templates=None, 
                model_id: str = "gpt-4", provider_name: str = "openai", api_key: str = None):
        # Initialize analyzer
        
    def analyze(self, template_name: str = "auto", **kwargs) -> str:
        """
        Analyze text using a specific template
        """
        
    def summarize(self, **kwargs):
        """
        Summarize the transcription
        """
        
    def extract_key_points(self, **kwargs):
        """
        Extract key points from the transcription
        """
        
    def extract_action_items(self, **kwargs):
        """
        Extract action items from the transcription
        """
        
    def analyze_sentiment(self, **kwargs):
        """
        Analyze sentiment in the transcription
        """
```

### SlackDownloader

Service for downloading and processing Slack messages.

```python
class SlackDownloader(SlackServiceInterface):
    def __init__(self, config: SlackConfig, http_client: HttpClientInterface = None):
        # Initialize downloader
        
    def fetch_messages(self) -> List[Dict]:
        """
        Download all messages from the channel
        """
```

### ModelProviderFactory

Factory for creating AI model provider instances.

```python
class ModelProviderFactory:
    @classmethod
    def register_provider(cls, name: str, provider_class) -> None:
        """
        Register a new model provider
        """
        
    @classmethod
    def get_provider(cls, provider_name: str, **kwargs) -> AIModelProviderInterface:
        """
        Get a provider instance
        """
        
    @classmethod
    def get_transcription_model(cls, provider_name: str, **kwargs) -> TranscriptionModelInterface:
        """
        Get a transcription model
        """
        
    @classmethod
    def get_analysis_model(cls, provider_name: str, **kwargs) -> TextAnalysisModelInterface:
        """
        Get an analysis model
        """
```

## Usage Examples

### Transcribing Audio

```python
from src.transcription.meeting_transcription import AudioTranscriptionService, TranscriptionClient
from src.transcription.audio_processor import AudioFileHandler, TranscriptionFileWriter, SpeakerDiarization

# Create dependencies
transcription_client = TranscriptionClient(provider_name="openai", api_key="your-api-key")
diarization_service = SpeakerDiarization()
file_handler = AudioFileHandler()
file_writer = TranscriptionFileWriter()

# Create service
service = AudioTranscriptionService(
    transcription_client=transcription_client,
    diarization_service=diarization_service,
    audio_file_handler=file_handler,
    file_writer=file_writer,
    model_id="whisper-1"
)

# Transcribe audio
transcription = service.transcribe("path/to/audio.mp3", diarization=False)
print(transcription)
```

### Analyzing Text

```python
from src.transcription.meeting_analyzer import MeetingAnalyzer, AnalysisClient

# Create analyzer
analyzer = MeetingAnalyzer(
    transcription="Your text to analyze",
    provider_name="openai",
    api_key="your-api-key",
    model_id="gpt-4"
)

# Analyze with different templates
summary = analyzer.summarize()
key_points = analyzer.extract_key_points()
action_items = analyzer.extract_action_items()
sentiment = analyzer.analyze_sentiment()

# Use a specific template
executive_summary = analyzer.analyze(template_name="executive")
```

### Downloading Slack Messages

```python
from src.slack.download_slack_channel import SlackDownloader, SlackConfig
from src.slack.http_client import RequestsClient

# Create configuration
config = SlackConfig(
    token="your-slack-token",
    channel_id="C01234567",
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 1, 31),
    output_dir="slack_exports"
)

# Create downloader
http_client = RequestsClient()
downloader = SlackDownloader(config, http_client)

# Fetch messages
messages = downloader.fetch_messages()
```

## Error Handling

Samuelizer uses custom exceptions for different error scenarios:

- `MeetingMinutesError`: Base exception for all errors
- `TranscriptionError`: Errors during transcription
- `AnalysisError`: Errors during content analysis
- `DownloadError`: Errors during video download
- `AudioExtractionError`: Errors during audio extraction
- `SlackAPIError`: Errors from the Slack API
- `RequestError`: HTTP request errors

Example error handling:

```python
from src.transcription.exceptions import TranscriptionError, AnalysisError

try:
    transcription = service.transcribe("path/to/audio.mp3")
    analysis = analyzer.analyze(transcription)
except TranscriptionError as e:
    print(f"Transcription failed: {e}")
except AnalysisError as e:
    print(f"Analysis failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```
