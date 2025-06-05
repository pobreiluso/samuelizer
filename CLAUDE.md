# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Samuelizer is an AI-powered tool for summarizing Slack conversations, meetings, and audio/video transcriptions. It supports both online (OpenAI API) and offline (local models) processing modes.

## Development Commands

### Setup and Dependencies
```bash
poetry install                    # Install dependencies
poetry install --extras local_models  # Install with local model support
```

### Testing
```bash
make test                        # Run tests with pytest
make test-cov                    # Run tests with coverage report
poetry run pytest               # Direct pytest execution
./tests/run_tests.sh            # Full test suite with environment checks
```

### Code Quality
```bash
make lint                        # Run flake8 linting
make format                      # Format code with black and isort
make type-check                  # Run mypy type checking
```

### Application Execution
```bash
poetry run samuelize            # Run CLI tool
make run                        # Alternative run command
```

### Maintenance
```bash
make clean                      # Remove temporary files and caches
poetry run samuelize clear-cache # Clear transcription cache
```

## Core Architecture

### Entry Point
- `src/cli.py` - Main CLI interface using Click framework with global flags for offline/local mode

### Processing Pipeline
1. **Audio Processing**: `src/utils/audio_extractor.py` and `src/utils/audio_optimizer.py` handle media file conversion and optimization
2. **Transcription**: `src/transcription/` module handles speech-to-text conversion with caching
3. **Analysis**: `src/transcription/meeting_analyzer.py` performs AI-powered content analysis
4. **Export**: `src/exporters/` handles output formatting (JSON, DOCX)

### Key Modules
- **Slack Integration** (`src/slack/`): Complete Slack API integration with rate limiting, pagination, and filtering
- **Transcription** (`src/transcription/`): Modular transcription system supporting multiple providers (OpenAI, local models)
- **AI Models** (`src/models/`): Factory pattern for different AI provider adapters
- **Configuration** (`src/config/`): Centralized configuration management

### Provider Architecture
The system uses a factory pattern for AI providers:
- `src/models/model_factory.py` - Creates appropriate model adapters
- `src/models/openai_adapter.py` - OpenAI API integration
- `src/models/local_adapter.py` - Local model support (Whisper, transformers)

### Caching System
- `src/transcription/cache.py` - File-based caching for transcriptions to avoid redundant API calls
- Cache keys based on file hash, model parameters, and provider settings

## CLI Commands

### Media Analysis
```bash
poetry run samuelize media FILE_PATH [options]
# Options: --api_key, --template, --provider, --model, --output, --optimize
```

### Text Analysis
```bash
poetry run samuelize text "TEXT" [options]
```

### Slack Analysis
```bash
poetry run samuelize slack CHANNEL_ID_OR_LINK [options]
poetry run samuelize slack --list-channels    # List all channels
poetry run samuelize slack --summary          # Global workspace summary
```

### Audio Recording
```bash
poetry run samuelize listen [--duration SECONDS]
```

### Offline Mode
All commands support `--local` or `--offline` flags for completely local processing without API calls.

## Testing Strategy

- Unit tests in `tests/` directory
- Integration tests with mock API responses
- Sample media files in `tests/samples/`
- Environment-aware testing (checks for API keys, handles offline mode)
- Use `tests/run_tests.sh` for comprehensive testing including environment setup

## Configuration

- Environment variables via `.env` file
- Provider-specific configuration in `src/config/providers.py`
- Template system in `src/transcription/templates.py` for different analysis types

## Development Notes

- Use `poetry` for dependency management
- Follow Black code formatting (88 character line length)
- Type hints required (mypy enforcement)
- Comprehensive error handling with custom exceptions in each module
- Logging configured per module via `src/utils/logging_utils.py`