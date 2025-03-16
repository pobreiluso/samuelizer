# Samuelizer

**Samuelizer** is an AI-powered tool designed to automatically summarize Slack conversations, meetings, audio/video transcriptions, and other related content. It leverages cutting-edge technologies (such as OpenAI's models) to transform large amounts of information into clear, concise, and visually appealing summaries—facilitating decision-making and rapid analysis.

---

## Table of Contents

- [Main Features](#main-features)
- [Installation and Requirements](#installation-and-requirements)
- [Usage and Examples](#usage-and-examples)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Maintenance and Roadmap](#maintenance-and-roadmap)
- [License](#license)
- [Authors and Contact](#authors-and-contact)

---

## Main Features

- **Slack Analysis:**  
  - Download and process Slack messages (from channels or threads).  
  - Intelligent replacement of user mentions for improved readability.  
  - Advanced filtering options (by date range, user, threads, reactions).
  - Robust pagination and rate limit handling.
  - User information caching for improved performance.

- **Audio/Video Transcription:**  
  - Extract and optimize audio from various media formats (MP4, AVI, MKV, MP3, WAV, etc.).  
  - Automatically transcribe audio using OpenAI’s Whisper model.

- **Summary Generation:**  
  - Generate executive summaries, sentiment analysis, key points, and action items.
  - **Automatic Template Selection:** The AI analyzes the content and automatically selects the best template based on context.
  - Customize analysis templates (e.g., summary, executive, quick).
  - Process and segment long texts to meet token limitations.

- **Automated Documentation:**  
  - Export summaries and analyses to DOCX files.
  - Use Markdown formatting for enhanced clarity.

- **Command Line Interface (CLI):**  
  - Clear commands for multiple modes: media analysis, text summarization, Slack message analysis, real-time recording, etc.
  - The `version` command displays the current version of the tool.

- **Integration & Automation:**  
  - Managed with Poetry for dependency and environment management.
  - A Makefile with targets for setup, testing, linting, formatting, documentation generation, and running the application.

---

## Installation and Requirements

### Prerequisites

- **Operating System:**  
  - Compatible with Windows, macOS, and Linux.
- **Python:**  
  - Version 3.12 or higher.
- **Poetry:**  
  - For environment and dependency management.
  
  You can install Poetry by running:
  ```bash
  # macOS / Linux
  curl -sSL https://install.python-poetry.org | python3 -
  
  # Windows PowerShell
  (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
  ```

### Installation Steps

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/tu_usuario/samuelizer.git
   cd samuelizer
   ```

2. **Install Dependencies:**
   ```bash
   poetry install
   ```

3. **Configure the Environment:**
   - Rename the `.env.example` file to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit the `.env` file to set your credentials and configurations, for example:
     ```env
     OPENAI_API_KEY=your_openai_api_key
     SLACK_TOKEN=your_slack_token
     SLACK_RATE_LIMIT_DELAY=1.0
     SLACK_BATCH_SIZE=1000
     OUTPUT_DIR=slack_exports
     LOG_FILE=slack_download.log
     ```

4. **Verify Installation:**
   - Run:
     ```bash
     poetry run samuelize version
     ```
   - This should display the current version of the tool.

---

## Usage and Examples

The application offers several CLI commands to access its features. Here are some examples:

### Media Analysis (Audio/Video)
```bash
poetry run samuelize media path/to/file.mp4 --api_key your_openai_api_key --optimize 32k --template executive
```

### Text Summarization
```bash
poetry run samuelize text "Text to analyze" --template quick
```

### Slack Message Analysis
```bash
# Análisis básico de canal usando ID
poetry run samuelize slack CHANNEL_ID --start-date 2024-01-01 --end-date 2024-02-01

# Análisis usando un enlace de Slack a un canal
poetry run samuelize slack https://workspace.slack.com/archives/C01234567

# Análisis usando un enlace de Slack a un mensaje específico o hilo
poetry run samuelize slack https://workspace.slack.com/archives/C01234567/p1234567890123456

# Análisis de un hilo específico usando --thread-ts
poetry run samuelize slack CHANNEL_ID --thread-ts 1234567890.123456

# Filtrar por usuario
poetry run samuelize slack CHANNEL_ID --user-id U01234ABC

# Only messages with thread replies
poetry run samuelize slack CHANNEL_ID --only-threads

# Only messages with reactions
poetry run samuelize slack CHANNEL_ID --with-reactions
```

### Real-Time Recording and Analysis
```bash
poetry run samuelize listen --duration 300
```
*Note:* If no duration is specified, recording will continue until manually interrupted (Ctrl+C).

### Check Version
```bash
poetry run samuelize version
```

### Offline Mode (100% Local Processing)
```bash
# Process any command completely offline without any external API calls
poetry run samuelize --offline media path/to/file.mp4 --whisper-size base --text-model facebook/bart-large-cnn

# Process text analysis offline
poetry run samuelize --local text "Text to analyze" --template quick

# Process Slack messages offline
poetry run samuelize --local slack CHANNEL_ID --start-date 2024-01-01

# Record and analyze audio offline
poetry run samuelize --local listen --duration 300
```

### Using Local Models with Specific Whisper Size
```bash
# Specify the size of the Whisper model to use (tiny, base, small, medium, large)
poetry run samuelize --local --whisper-size medium media path/to/file.mp4
```

---

## Project Structure

The repository is organized as follows:

- **src/**: Contains the source code.
  - **cli.py**: Entry point for the CLI application.
  - **transcription/**: Module for transcription and summary generation, including templates and exception handling.
  - **slack/**: Integration with the Slack API for downloading and processing messages.
  - **audio_capture/**: Code for capturing and processing system audio.
  - **config/**: Global configuration and environment variable management.
  - **utils/**: Various utilities (audio extraction, helper functions, etc.).

- **Makefile**: Automates common tasks (setup, test, lint, docs, etc.).
- **pyproject.toml**: Project configuration and dependency management via Poetry.
- **.env**: Environment configuration file for credentials and sensitive parameters.
- **README.md**: This file, detailing the project's usage and features.

---

## Contributing

Contributions are welcome! To contribute:

1. **Fork the Repository:**  
   Create a fork and develop your feature or fix in a new branch.
2. **Submit a Pull Request:**  
   Provide a clear description of your changes.
3. **Issues and Feedback:**  
   Open an issue for bug reports, improvement proposals, or feature discussions.

Please follow the [Contributing Guidelines](CONTRIBUTING.md) and adhere to the code style standards.

---

## Maintenance and Roadmap

### Future Plans

- **Template Optimization:**  
  Implement a templating engine (e.g., Jinja2) for greater flexibility and reusability.
- **Enhanced Audio Processing:**  
  Improve error handling and optimize audio extraction.
- **Continuous Integration:**  
  Set up CI/CD pipelines for automated testing, style checks, and deployments.
- **Web Interface:**  
  Explore a graphical web interface for easier use by non-expert users.
- **Multilanguage Support:**  
  Expand the template system to support multiple languages and contexts.

---

## License

This project is licensed under the [MIT License](LICENSE). The MIT License was chosen for its simplicity and flexibility, allowing developers to freely use, modify, and distribute the code.

---

## Authors and Contact

- **ajerez** –  
  Email: [pobreiluso@gmail.com](mailto:pobreiluso@gmail.com)  
  [GitHub](https://github.com/ajerez) | [LinkedIn](https://www.linkedin.com/in/ajerez/)

If you have any questions, suggestions, or would like to contribute further, please feel free to get in touch.

---

This README is designed to serve both developers and end users by providing clear guidance on how to install and use the project, regardless of experience level. Welcome to Samuelizer!

