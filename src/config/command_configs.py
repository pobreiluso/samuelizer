"""
Configuration classes for CLI commands to reduce parameter complexity.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from pathlib import Path


@dataclass
class BaseCommandConfig:
    """Base configuration for all commands."""
    api_key: Optional[str] = None
    provider: str = "openai"
    model: Optional[str] = None
    output: Optional[Path] = None
    template: str = "summary"


@dataclass
class MediaTranscriptionConfig(BaseCommandConfig):
    """Configuration for media transcription commands."""
    file_path: str = ""
    drive_url: Optional[str] = None
    optimize: str = "128k"
    diarization: bool = False
    no_cache: bool = False
    keep_silence: bool = False
    max_size: int = 100
    output_audio: Optional[Path] = None
    
    def __post_init__(self):
        """Validate and process configuration after initialization."""
        if self.file_path:
            self.file_path = str(Path(self.file_path).expanduser().resolve())


@dataclass
class TextAnalysisConfig(BaseCommandConfig):
    """Configuration for text analysis commands."""
    text: str = ""
    params: Optional[str] = None
    
    def get_template_params(self) -> dict:
        """Parse and return template parameters."""
        if self.params:
            import json
            return json.loads(self.params)
        return {}


@dataclass
class SlackAnalysisConfig(BaseCommandConfig):
    """Configuration for Slack analysis commands."""
    channel_id_or_link: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    output_dir: str = "slack_exports"
    token: Optional[str] = None
    thread_ts: Optional[str] = None
    user_id: Optional[str] = None
    only_threads: bool = False
    with_reactions: bool = False
    summary: bool = False
    list_channels: bool = False
    include_private: bool = True
    include_archived: bool = False
    max_channels: int = 10
    min_messages: int = 5
    workers: int = 0
    auto_join: bool = False


@dataclass
class AudioCaptureConfig(BaseCommandConfig):
    """Configuration for audio capture commands."""
    duration: int = 0
    output_dir: str = "recordings"
    no_cache: bool = False
    keep_silence: bool = False
    optimize: str = "128k"
    max_size: int = 100