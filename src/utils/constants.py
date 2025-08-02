"""
Application constants to replace magic numbers and improve maintainability.
"""

# Audio processing constants
DEFAULT_AUDIO_BITRATE = "128k"
DEFAULT_MAX_FILE_SIZE_MB = 100

# Transcription constants
DEFAULT_WHISPER_MODEL_SIZE = "base"
DEFAULT_TRANSCRIPTION_MODEL = "whisper-1"
DEFAULT_ANALYSIS_MODEL = "gpt-4"

# Content length limits
MAX_CONTENT_LENGTH = 15000
MAX_ANALYSIS_OUTPUT_LENGTH = 100

# Cache settings
DEFAULT_CACHE_ENABLED = True

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.aac', '.ogg']
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']

# Model classifications
OPENAI_CHAT_MODELS = [
    "gpt-3.5-turbo", 
    "gpt-4", 
    "gpt-4-turbo", 
    "gpt-4-1106-preview",
    "gpt-4-32k"
]

OPENAI_COMPLETION_MODELS = [
    "text-davinci-003",
    "text-davinci-002", 
    "text-curie-001",
    "text-babbage-001",
    "text-ada-001"
]

# Default providers
DEFAULT_TRANSCRIPTION_PROVIDER = "openai"
DEFAULT_ANALYSIS_PROVIDER = "openai"

# Progress tracking
PROGRESS_UPDATE_INTERVAL = 1  # seconds

# Error handling
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2

# File naming patterns
OPTIMIZED_FILE_SUFFIX = "_optimized"
TRANSCRIPTION_FILE_SUFFIX = "_transcription.txt"
ANALYSIS_FILE_SUFFIX = "_analysis.docx"