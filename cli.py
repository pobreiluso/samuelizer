import sys
import logging
import glob
import click
from typing import Optional
from transcription.meeting_minutes import (
    AudioTranscriptionService,
    MeetingAnalyzer, 
    DocumentManager,
    VideoDownloader
)
from slack.download_slack_channel import SlackDownloader, SlackConfig
from transcription.exceptions import MeetingMinutesError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cli_agent.log'),
        logging.StreamHandler()
    ]
)

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
    """CLI agent for summarizing videos, audios and Slack conversations."""
    pass

@cli.group()
def transcribe():
    """Commands related to audio/video transcription."""
    pass

@cli.group()
def slack():
    """Commands related to Slack operations."""
    pass

@cli.group()
def summarize():
    """Commands related to text summarization."""
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

@slack.command('download')
@click.argument('channel_id')
@click.option('--start-date', help='Start date in YYYY-MM-DD format')
@click.option('--end-date', help='End date in YYYY-MM-DD format')
@click.option('--output-dir', default='slack_exports', help='Directory to save messages')
@click.option('--token', help='Slack token. Can also use SLACK_TOKEN env var')
def download_slack_messages(channel_id, start_date, end_date, output_dir, token):
    """
    Descargar y sumarizar mensajes de un canal de Slack.
    
    CHANNEL_ID: ID del canal de Slack (ej: C01234567)
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
        
        import glob
        import os
        import json
        from transcription.meeting_minutes import MeetingAnalyzer, DocumentManager

        json_files = glob.glob(os.path.join(output_dir, f"slack_messages_{channel_id}*.json"))
        if not json_files:
            logging.error("No se encontraron archivos JSON de mensajes descargados.")
            sys.exit(1)
        
        latest_file = max(json_files, key=os.path.getctime)
        logging.info(f"Archivo de mensajes más reciente: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        messages = data.get('messages', [])
        if not messages:
            logging.info("No hay mensajes para sumarizar.")
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
        logging.info("Documento de suma guardado: slack_summary.docx")
    
    except Exception as e:
        logging.error(f"Error al procesar mensajes de Slack: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Proceso interrumpido por el usuario.")
        sys.exit(0)

@cli.command()
@click.argument('file_path')
@click.option('--api_key', prompt=True, hide_input=True, help='Clave de API de OpenAI.')
def summarize_file_command(file_path, api_key):
    """
    Sumariza un archivo de audio o video directamente.
    
    FILE_PATH: Ruta al archivo de audio o video.
    """
    try:
        service = AudioTranscriptionService()
        transcription = service.transcribe(file_path)
        
        analyzer = MeetingAnalyzer(transcription)
        meeting_info = {
            'abstract_summary': analyzer.summarize(),
            'key_points': analyzer.extract_key_points(),
            'action_items': analyzer.extract_action_items(),
            'sentiment': analyzer.analyze_sentiment()
        }

        DocumentManager.save_to_docx(meeting_info, 'summary.docx')
        logger.info("Document saved: summary.docx")
    except MeetingMinutesError as e:
        logging.error(f"Error en sumarizar el archivo: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Proceso interrumpido por el usuario.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        logging.info("Proceso interrumpido por el usuario.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error inesperado en la CLI: {e}")
        sys.exit(1)
