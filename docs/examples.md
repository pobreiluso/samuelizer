# Samuelizer Usage Examples

This document provides practical examples of using Samuelizer for various scenarios.

## Basic Examples

### Transcribing a Video File

```bash
# Transcribe a video file and analyze the content
poetry run samuelize media path/to/video.mp4 --api_key YOUR_OPENAI_API_KEY
```

### Analyzing Text

```bash
# Analyze a text file
poetry run samuelize text "$(cat path/to/text_file.txt)" --api_key YOUR_OPENAI_API_KEY

# Analyze text directly
poetry run samuelize text "This is a sample text to analyze. It contains important information about the project timeline and next steps." --api_key YOUR_OPENAI_API_KEY
```

### Analyzing a Slack Channel

```bash
# Download and analyze a Slack channel
poetry run samuelize slack C01234567 --token YOUR_SLACK_TOKEN --api_key YOUR_OPENAI_API_KEY --output slack_analysis.docx
```

### Recording and Transcribing Audio

```bash
# Start recording system audio (press Ctrl+C to stop)
poetry run samuelize listen --api_key YOUR_OPENAI_API_KEY --output meeting_notes.docx
```

## Advanced Examples

### Using Different Templates

```bash
# Use the executive template for a formal summary
poetry run samuelize media path/to/video.mp4 --template executive

# Use the quick template for a very concise summary
poetry run samuelize text "Your text" --template quick

# Use the brainstorming template for idea organization
poetry run samuelize media path/to/brainstorming_session.mp3 --template brainstorming

# Use the one_to_one template for 1:1 meeting analysis
poetry run samuelize media path/to/one_to_one.mp3 --template one_to_one
```

### Enabling Speaker Diarization

```bash
# Transcribe with speaker identification
poetry run samuelize media path/to/meeting.mp4 --diarization
```

### Using Date Filters for Slack

```bash
# Download Slack messages from a specific date range
poetry run samuelize slack C01234567 --start-date 2023-01-01 --end-date 2023-01-31
```

### Disabling Transcription Cache

```bash
# Force fresh transcription without using cache
poetry run samuelize media path/to/video.mp4 --no-cache
```

### Using Different AI Providers and Models

```bash
# Specify a different provider and model
poetry run samuelize media path/to/audio.mp3 --provider openai --model whisper-1
```

## Practical Use Cases

### Meeting Summarization

```bash
# Record and summarize a meeting
poetry run samuelize listen --output meeting_summary.docx --template executive
```

### Podcast Analysis

```bash
# Analyze a podcast episode
poetry run samuelize media path/to/podcast.mp3 --template default
```

### Interview Transcription

```bash
# Transcribe an interview with speaker identification
poetry run samuelize media path/to/interview.mp4 --diarization --output interview_transcript.docx
```

### Slack Channel Weekly Summary

```bash
# Generate a weekly summary of a Slack channel
poetry run samuelize slack C01234567 --start-date 2023-01-01 --end-date 2023-01-07 --template slack_detailed --output weekly_slack_summary.docx
```

### Press Conference Analysis

```bash
# Analyze a press conference
poetry run samuelize media path/to/press_conference.mp4 --template press_conference --output press_analysis.docx
```

### Team Sync Meeting

```bash
# Summarize a team sync meeting
poetry run samuelize media path/to/team_sync.mp3 --template weekly_sync --output team_sync_summary.docx
```

## Programmatic Usage

You can also use Samuelizer programmatically in your Python code:

```python
from src.controller import run_transcription, run_analysis, save_meeting_info

# Transcribe an audio file
transcription = run_transcription(
    api_key="YOUR_OPENAI_API_KEY",
    file_path="path/to/audio.mp3",
    diarization=False,
    provider_name="openai",
    model_id="whisper-1"
)

# Analyze the transcription
meeting_info = run_analysis(
    transcription=transcription,
    provider_name="openai",
    model_id="gpt-4",
    api_key="YOUR_OPENAI_API_KEY"
)

# Save the results
save_meeting_info(meeting_info, "output.docx")
```

## Environment Variables

You can set environment variables to avoid passing API keys in the command line:

```bash
# Set environment variables
export OPENAI_API_KEY=your_openai_api_key
export SLACK_TOKEN=your_slack_token

# Run commands without specifying API keys
poetry run samuelize media path/to/video.mp4
poetry run samuelize slack C01234567
```
