# Samuelizer

**Description:**
Samuelizer is an AI-powered agent designed to summarize Slack channels, threads, meetings, and supported audio/video files. It automates the process of downloading, transcribing, and summarizing conversations, providing concise summaries, key points, action items, and sentiment analysis.

## Features

- **Download Slack Conversations:**
  - Download messages from any Slack channel or thread
  - Support for specifying date ranges
  - Message formatting and user mention resolution
  
- **Transcribe Audio/Video Files:**
  - Extract audio from video files
  - Transcribe audio using OpenAI's Whisper model
  - Support for multiple audio/video formats
  - Automatic audio optimization
  
- **Summarize Conversations:**
  - Generate abstract summaries
  - Extract key points and action items
  - Perform sentiment analysis
  - Multiple analysis templates

- **Document Management:**
  - Save summaries and analyses to Word documents
  - Structured output format
  - Support for custom templates

## Installation

### Prerequisites

1. **Python 3.12+**
   ```bash
   python --version  # Should be 3.12 or higher
   ```

2. **Poetry**
   ```bash
   # macOS / Linux
   curl -sSL https://install.python-poetry.org | python3 -
   
   # Windows PowerShell
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
   ```

### Project Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/samuelizer.git
   cd samuelizer
   ```

2. **Install Dependencies**
   ```bash
   poetry install
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

## Usage

### CLI Commands

1. **Analyze Media Files**
   ```bash
   # Basic usage
   samuelize media path/to/file.mp4
   
   # With options
   samuelize media video.mp4 --api_key YOUR_KEY --optimize 64k --template executive
   ```

2. **Analyze Slack Channel**
   ```bash
   # Basic usage
   samuelize slack CHANNEL_ID
   
   # With date range
   samuelize slack C01234567 --start-date 2024-01-01 --end-date 2024-02-01
   ```

3. **Analyze Text**
   ```bash
   samuelize text "Your text here" --template quick
   ```

4. **Record and Analyze System Audio**
   ```bash
   # Record for specific duration
   samuelize listen --duration 300
   
   # Record until interrupted
   samuelize listen
   ```

### Available Templates

1. **summary**
   - Concise abstract paragraph
   - Main context and purpose
   - Important points and conclusions

2. **executive**
   - Structured executive summary
   - Objectives and key points
   - Decisions and next steps
   - Expected impact

3. **quick**
   - Ultra-concise summary
   - Main idea in one sentence
   - Maximum 3 critical points
   - Key conclusion

4. **action_items**
   - Concrete tasks
   - Responsible parties
   - Deadlines
   - Task format

5. **sentiment**
   - General tone analysis
   - Sentiment changes
   - Topic reactions
   - Agreement levels

6. **slack_brief**
   - TL;DR summary
   - Final decisions only
   - Pending tasks
   - Minimal context

7. **slack_detailed**
   - Full context
   - Main discussions
   - Decisions with rationale
   - Action plan
   - Attention points

## Environment Variables

```env
OPENAI_API_KEY=your_openai_api_key
SLACK_TOKEN=your_slack_bot_token
SLACK_RATE_LIMIT_DELAY=1.0
SLACK_BATCH_SIZE=1000
OUTPUT_DIR=slack_exports
LOG_FILE=slack_download.log
```

## Supported Formats

### Audio/Video
- Video: mp4, avi, mkv, mov, wmv, flv, webm
- Audio: mp3, wav, m4a, aac, ogg

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

