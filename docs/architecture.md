# Samuelizer Architecture

This document outlines the architecture and design principles of the Samuelizer project.

## Overview

Samuelizer is built following SOLID principles and clean architecture patterns to ensure maintainability, testability, and extensibility. The system is designed with clear separation of concerns and dependency inversion to allow for easy adaptation to different AI providers and use cases.

## Core Principles

### 1. Dependency Inversion

All components depend on abstractions (interfaces) rather than concrete implementations. This allows for:

- Easy swapping of implementations (e.g., different AI providers)
- Simplified testing through mocking
- Loose coupling between components

Example:
```python
# Interface
class TranscriptionService(ABC):
    @abstractmethod
    def transcribe(self, audio_file_path, diarization: bool = False):
        pass

# Implementation
class AudioTranscriptionService(TranscriptionService):
    def __init__(self, transcription_client, diarization_service, audio_file_handler, file_writer):
        self.transcription_client = transcription_client
        self.diarization_service = diarization_service
        self.file_handler = audio_file_handler
        self.file_writer = file_writer
```

### 2. Single Responsibility Principle

Each class has a single responsibility and reason to change:

- `AudioFileHandler`: Handles audio file operations
- `TranscriptionClient`: Manages communication with AI providers
- `MeetingAnalyzer`: Analyzes transcribed content
- `DocumentManager`: Manages document creation and saving

### 3. Open/Closed Principle

The system is open for extension but closed for modification:

- New AI providers can be added without changing existing code
- New analysis templates can be added without modifying the analyzer
- New export formats can be supported by implementing new exporters

### 4. Interface Segregation

Interfaces are client-specific rather than general-purpose:

- `TranscriptionModelInterface`: Specifically for transcription operations
- `TextAnalysisModelInterface`: Specifically for text analysis
- `MessageExporterInterface`: Specifically for exporting messages

### 5. Liskov Substitution Principle

Subtypes are substitutable for their base types:

- Any implementation of `TranscriptionService` can be used where the interface is expected
- Different AI providers implement the same interfaces and can be used interchangeably

## Component Architecture

### Core Components

1. **CLI Layer** (`src/cli.py`)
   - Handles command-line interface and user interaction
   - Parses arguments and options
   - Delegates to appropriate services

2. **Controller Layer** (`src/controller.py`)
   - Orchestrates the flow between different services
   - Manages the high-level application logic

3. **Service Layer**
   - `AudioTranscriptionService`: Handles audio transcription
   - `MeetingAnalyzer`: Analyzes transcribed content
   - `SlackDownloader`: Downloads and processes Slack messages

4. **Provider Layer**
   - `OpenAIProvider`: Implements OpenAI-specific functionality
   - `ModelProviderFactory`: Creates appropriate provider instances

5. **Utility Layer**
   - `AudioExtractor`: Handles audio extraction and optimization
   - `AudioFileHandler`: Manages audio file operations
   - `DocumentManager`: Creates and saves documents

### Data Flow

1. User input via CLI
2. CLI parses commands and options
3. Controller orchestrates the appropriate services
4. Services use providers to interact with AI models
5. Results are processed and returned to the user

## Extension Points

### Adding New AI Providers

1. Create a new provider class implementing the required interfaces
2. Register the provider with `ModelProviderFactory`
3. Update provider configuration in `src/config/providers.py`

### Adding New Analysis Templates

1. Add the template definition to `PromptTemplates.DEFAULT_TEMPLATES`
2. The template will be automatically available through the existing API

### Adding New Export Formats

1. Create a new exporter implementing the `ExporterInterface`
2. Inject the new exporter where needed

## Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: Test complete workflows from CLI to output

## Dependency Management

Dependencies are managed using Poetry, with clear separation between:

- Core dependencies required for runtime
- Development dependencies for testing and code quality

## Future Considerations

- Support for additional AI providers
- Pluggable architecture for custom extensions
- Web interface for non-CLI usage
- Distributed processing for large media files
