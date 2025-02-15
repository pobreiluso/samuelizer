import sys
import logging
import glob
import click
import os
import json
from typing import Optional
from src.transcription.meeting_minutes import (
    AudioTranscriptionService,
    MeetingAnalyzer, 
    DocumentManager,
    VideoDownloader
)
from src.slack.download_slack_channel import SlackDownloader, SlackConfig
from src.transcription.exceptions import MeetingMinutesError
from src.utils.audio_extractor import AudioExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cli_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@click.group()
def cli():
    """CLI agent for summarizing videos, audios, and Slack conversations."""
    pass

@cli.group()
def transcribe():
    """Commands related to audio/video transcription."""
    pass

@transcribe.command('video')
@click.argument('api_key')
@click.argument('file_path')
@click.option('--drive_url', required=False, help='Google Drive URL to download video.')
def transcribe_video(api_key, file_path, drive_url):
    """
    Transcribe and analyze a video file.

    API_KEY: OpenAI API key
    FILE_PATH: Path to video file
    """
    try:
        if drive_url:
            video_file = VideoDownloader.download_from_google_drive(drive_url)
            file_path = video_file

        service = AudioTranscriptionService()
        transcription = service.transcribe(file_path)
        
        analyzer = MeetingAnalyzer(transcription)
        meeting_info = {
            'abstract_summary': analyzer.summarize(),
            'key_points': analyzer.extract_key_points(),
            'action_items': analyzer.extract_action_items(),
            'sentiment': analyzer.analyze_sentiment()
        }

        DocumentManager.save_to_docx(meeting_info, 'video_summary.docx')
        logger.info("Document saved: video_summary.docx")

    except MeetingMinutesError as e:
        logger.error(f"Error transcribing video: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

@cli.group()
def summarize():
    """Commands related to text summarization."""
    pass

@summarize.command('text')
@click.argument('text')
@click.option('--api_key', prompt=True, hide_input=True, help='OpenAI API key.')
def summarize_text_command(text, api_key):
    """
    Summarize a provided text.

    TEXT: Text to summarize.
    """
    try:
        analyzer = MeetingAnalyzer(text)
        summary = analyzer.summarize()
        click.echo(f"Summary: {summary}")
    except MeetingMinutesError as e:
        logger.error(f"Error summarizing text: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
        sys.exit(0)
    except openai.AuthenticationError as e:
        logger.error(f"OpenAI Authentication Error: {e}")
        sys.exit(1)
    except openai.APIError as e:
        logger.error(f"OpenAI API Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

@cli.group()
def slack():
    """Commands related to Slack operations."""
    pass

@slack.command('download')
@click.argument('channel_id')
@click.option('--start-date', type=click.DateTime(formats=["%Y-%m-%d"]), help='Start date in YYYY-MM-DD format')
@click.option('--end-date', type=click.DateTime(formats=["%Y-%m-%d"]), help='End date in YYYY-MM-DD format')
@click.option('--output-dir', default='slack_exports', help='Directory to save messages')
@click.option('--token', help='Slack token. Can also use SLACK_TOKEN env var')
def download_slack_messages(channel_id, start_date, end_date, output_dir, token):
    """
    Download and summarize messages from a Slack channel.

    CHANNEL_ID: Slack channel ID (e.g., C01234567)
    """
    try:
        slack_config = SlackConfig(
            token=token,
            channel_id=channel_id,
            start_date=start_date,
            end_date=end_date,
            output_dir=output_dir
        )
        downloader = SlackDownloader(slack_config)
        messages = downloader.fetch_messages()
        output_file = downloader.save_messages(messages)
        
        json_files = glob.glob(os.path.join(output_dir, f"slack_messages_{channel_id}*.json"))
        if not json_files:
            logging.error("No JSON message files found.")
            sys.exit(1)
        
        latest_file = max(json_files, key=os.path.getctime)
        logging.info(f"Latest message file: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        messages = data.get('messages', [])
        if not messages:
            logging.info("No messages to summarize.")
            sys.exit(0)
        
        transcription_text = "\n".join([msg.get('text', '') for msg in messages])
        
        analyzer = MeetingAnalyzer(transcription_text)
        meeting_info = {
            'abstract_summary': analyzer.summarize(),
            'key_points': analyzer.extract_key_points(),
            'action_items': analyzer.extract_action_items(),
            'sentiment': analyzer.analyze_sentiment()
        }
        
        DocumentManager.save_to_docx(meeting_info, 'slack_summary.docx')
        logging.info("Summary document saved: slack_summary.docx")
    
    except MeetingMinutesError as e:
        logging.error(f"Error processing Slack messages: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Process interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unexpected error while summarizing Slack messages: {e}")
        sys.exit(1)

@cli.command()
def version():
    """Displays the CLI agent version."""
    click.echo("samuelizer version 0.1.0")

if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error in CLI: {e}")
        sys.exit(1)
