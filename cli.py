import sys
import logging
import click
from transcription.meeting_minutes import main as transcribe_meeting
from slack.download_slack_channel import main as download_slack
from transcription.exceptions import MeetingMinutesError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cli_agent.log'),
        logging.StreamHandler()
    ]
)

@click.group()
def cli():
    """Agent CLI para sumarizar videos, audios y conversaciones de Slack."""
    pass

@cli.command()
@click.argument('api_key')
@click.argument('file_path')
@click.option('--drive_url', required=False, help='URL de Google Drive para descargar el video.')
def transcribe_meeting_command(api_key, file_path, drive_url):
    """
    Transcribe y analiza un archivo de video o audio.
    
    API_KEY: Clave de API de OpenAI.
    FILE_PATH: Ruta al archivo de video o audio.
    """
    try:
        if drive_url:
            from transcription.meeting_minutes import VideoDownloader
            video_file = VideoDownloader.download_from_google_drive(drive_url)
            file_path = video_file

        transcribe_meeting(api_key, file_path)
    except MeetingMinutesError as e:
        logging.error(f"Error en transcribir y analizar la reunión: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Proceso interrumpido por el usuario.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        sys.exit(1)

@cli.command()
@click.argument('channel_id')
@click.option('--start-date', help='Fecha de inicio en formato YYYY-MM-DD')
@click.option('--end-date', help='Fecha final en formato YYYY-MM-DD')
@click.option('--output-dir', default='slack_exports', help='Directorio para guardar los mensajes.')
@click.option('--token', help='Token de Slack. También puede usar la variable de entorno SLACK_TOKEN.')
def download_slack_command(channel_id, start_date, end_date, output_dir, token):
    """
    Descargar y sumarizar mensajes de un canal de Slack.
    
    CHANNEL_ID: ID del canal de Slack (ej: C01234567)
    """
    try:
        download_slack(channel_id=channel_id, start_date=start_date, end_date=end_date, output_dir=output_dir, token=token)
        
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
        transcribe_meeting(api_key, file_path)
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
