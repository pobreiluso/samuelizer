import sys
import logging
import glob
import click
import os
import json
import openai
from typing import Optional
from tqdm import tqdm
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
    """Samuelizer - AI-powered summarization tool."""
    pass

@cli.command('media')
@click.argument('file_path')
@click.option('--api_key', help='OpenAI API key.', default=lambda: os.environ.get('OPENAI_API_KEY', None))
@click.option('--drive_url', required=False, help='Google Drive URL to download media file.')
@click.option('--optimize', default='32k', help='Target bitrate for audio optimization (e.g. 32k, 64k)')
@click.option('--output', help='Save results to a DOCX file', required=False, type=click.Path())
def transcribe_media(file_path, api_key, drive_url, optimize, output):
    if not api_key:
        api_key = click.prompt('OpenAI API key', hide_input=True)
    
    # Expandir la ruta del usuario
    file_path = os.path.expanduser(file_path)
    
    # Verificar que el archivo existe
    if not os.path.exists(file_path):
        logger.error(f"El archivo no existe: {file_path}")
        sys.exit(1)
    """
    Summarize and analyze any media file (video or audio).

    FILE_PATH: Path to media file
    Supported formats: mp4, avi, mkv, mov, wmv, flv, webm, mp3, wav, m4a, aac, ogg
    
    The file will be:
    1. Optimized for processing (if needed)
    2. Transcribed to text
    3. Analyzed to extract:
       - Abstract summary
       - Key points
       - Action items
       - Sentiment analysis
    """
    supported_formats = AudioExtractor.get_supported_formats()
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext not in supported_formats:
        logger.error(f"Formato de archivo no soportado. Formatos soportados: {', '.join(supported_formats)}")
        sys.exit(1)
    try:
        if not api_key:
            logger.error("No se ha proporcionado la API key de OpenAI")
            sys.exit(1)
            
        # Configurar OpenAI
        os.environ["OPENAI_API_KEY"] = api_key
        openai.api_key = api_key
            
        if drive_url:
            video_file = VideoDownloader.download_from_google_drive(drive_url)
            file_path = video_file

        # Check if file is already MP3
        if file_path.lower().endswith('.mp3'):
            audio_file = file_path
        else:
            # Extract audio from video
            audio_file = AudioExtractor.extract_audio(file_path, target_bitrate=optimize)
        
        # Transcribe audio
        logger.info(f"Iniciando transcripción del archivo: {audio_file}")
        service = AudioTranscriptionService()
        try:
            transcription = service.transcribe(audio_file)
            logger.info(f"Transcripción completada. Longitud del texto: {len(transcription)} caracteres")
        except Exception as e:
            logger.error(f"Error durante la transcripción: {str(e)}")
            raise
        
        analyzer = MeetingAnalyzer(transcription)
        meeting_info = {}
        
        with tqdm(total=4, desc="Analizando contenido", unit="tarea") as pbar:
            meeting_info['abstract_summary'] = analyzer.summarize()
            pbar.update(1)
            meeting_info['key_points'] = analyzer.extract_key_points()
            pbar.update(1)
            meeting_info['action_items'] = analyzer.extract_action_items()
            pbar.update(1)
            meeting_info['sentiment'] = analyzer.analyze_sentiment()
            pbar.update(1)

        # Mostrar resultados en CLI
        click.echo("\n=== Resumen de la Samuelización ===")
        for key, value in meeting_info.items():
            click.echo(f"\n{key.replace('_', ' ').title()}:")
            click.echo("-" * 40)
            click.echo(value)
            click.echo()

        # Guardar en docx si se solicita
        if output:
            DocumentManager.save_to_docx(meeting_info, output)
            logger.info(f"Document saved: {output}")

    except MeetingMinutesError as e:
        logger.error(f"Error transcribing video: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

@cli.command('text')
@click.argument('text')
@click.option('--api_key', help='OpenAI API key.', default=lambda: os.environ.get('OPENAI_API_KEY', None))
@click.option('--output', help='Save results to a DOCX file', required=False, type=click.Path())
def summarize_text_command(text, api_key, output):
    if not api_key:
        api_key = click.prompt('OpenAI API key', hide_input=True)
    """
    Analyze and summarize a text.

    TEXT: Text to analyze
    
    The text will be analyzed to extract:
    - Abstract summary
    - Key points
    - Action items
    - Sentiment analysis
    """
    try:
        openai.api_key = api_key
        analyzer = MeetingAnalyzer(text)
        meeting_info = {
            'abstract_summary': analyzer.summarize(),
            'key_points': analyzer.extract_key_points(),
            'action_items': analyzer.extract_action_items(),
            'sentiment': analyzer.analyze_sentiment()
        }

        # Mostrar resultados en CLI
        click.echo("\n=== Resumen del Texto ===")
        for key, value in meeting_info.items():
            click.echo(f"\n{key.replace('_', ' ').title()}:")
            click.echo("-" * 40)
            click.echo(value)
            click.echo()

        # Guardar en docx si se solicita
        if output:
            DocumentManager.save_to_docx(meeting_info, output)
            logger.info(f"Document saved: {output}")
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

@cli.command('slack')
@click.argument('channel_id')
@click.option('--start-date', type=click.DateTime(formats=["%Y-%m-%d"]), help='Start date in YYYY-MM-DD format')
@click.option('--end-date', type=click.DateTime(formats=["%Y-%m-%d"]), help='End date in YYYY-MM-DD format')
@click.option('--output-dir', default='slack_exports', help='Directory to save messages')
@click.option('--token', help='Slack token. Can also use SLACK_TOKEN env var', default=lambda: os.environ.get('SLACK_TOKEN', None))
@click.option('--api_key', help='OpenAI API key.', default=lambda: os.environ.get('OPENAI_API_KEY', None))
@click.option('--output', help='Save results to a DOCX file', required=False, type=click.Path())
def analyze_slack_messages(channel_id, start_date, end_date, output_dir, token, api_key, output):
    """
    Analyze and summarize a Slack channel.

    CHANNEL_ID: Slack channel ID (e.g., C01234567)
    
    You can find the channel ID by:
    1. Right-clicking on the channel in Slack
    2. Select 'Copy link'
    3. The ID is the last part of the URL
    
    The channel messages will be:
    1. Downloaded and saved as JSON
    2. Analyzed to extract:
       - Abstract summary
       - Key points
       - Action items
       - Sentiment analysis
    3. Results saved as DOCX
    
    Required:
    - SLACK_TOKEN or --token: Slack Bot User OAuth Token
    - OPENAI_API_KEY or --api_key: OpenAI API key
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
        
        # Mostrar resultados en CLI
        click.echo("\n=== Resumen del Canal de Slack ===")
        for key, value in meeting_info.items():
            click.echo(f"\n{key.replace('_', ' ').title()}:")
            click.echo("-" * 40)
            click.echo(value)
            click.echo()

        # Guardar en docx si se solicita
        if output_file:
            DocumentManager.save_to_docx(meeting_info, output_file)
            logger.info(f"Document saved: {output_file}")
    
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
    click.echo("samuelizer version 1.0.0")

if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error in CLI: {e}")
        sys.exit(1)
