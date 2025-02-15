import requests
import json
import logging
import click
from datetime import datetime, timezone

class SlackAPIError(Exception):
    """Raised when Slack API returns an error response"""
    pass

class RequestError(Exception):
    """Raised when there is an error making HTTP requests"""
    pass
import time
from typing import Dict, List, Optional
import os
from dataclasses import dataclass
import argparse
import sys
from src.config.config import Config

# Initialize configuration
config = Config()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class SlackConfig:
    """Configuration for Slack API interactions"""
    token: str
    channel_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    output_dir: str = Config.OUTPUT_DIR
    rate_limit_delay: float = Config.SLACK_RATE_LIMIT_DELAY
    batch_size: int = Config.SLACK_BATCH_SIZE

class SlackDownloader:
    def __init__(self, config: SlackConfig):
        self.config = config
        self.base_url = "https://slack.com/api"
        self.headers = {"Authorization": f"Bearer {self.config.token}"}
        
        if not os.path.exists(config.output_dir):
            os.makedirs(config.output_dir)

    def get_channel_info(self) -> Dict:
        """
        Obtiene información del canal de Slack
        
        Returns:
            Dict: Información del canal
            
        Raises:
            SlackAPIError: Si hay un error en la API de Slack
            RequestError: Si hay un error en la solicitud HTTP
            JSONDecodeError: Si la respuesta no es JSON válido
        """
        url = f"{self.base_url}/conversations.info"
        params = {"channel": self.config.channel_id}
        
        try:
            with requests.Session() as session:
                response = session.get(url, headers=self.headers, params=params, verify=True)
                response.raise_for_status()
                data = response.json()
                
                if not data.get("ok"):
                    error_msg = data.get("error", "Unknown error")
                    logger.error(f"Error from Slack API: {error_msg}")
                    raise SlackAPIError(f"Slack API error: {error_msg}")
                
                return data
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise RequestError(f"Failed to connect to Slack API: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {str(e)}")
            raise

    def convert_date_to_ts(self, date: datetime) -> str:
        """Convierte un objeto datetime a timestamp de Slack"""
        return str(int(date.timestamp()))

    def fetch_messages(self) -> List[Dict]:
        """Descarga todos los mensajes del canal usando paginación y filtros de fecha"""
        url = f"{self.base_url}/conversations.history"
        params = {
            "channel": self.config.channel_id,
            "limit": self.config.batch_size,
        }

        # Añadir filtros de fecha si están especificados
        if self.config.start_date:
            params["oldest"] = self.convert_date_to_ts(self.config.start_date)
        if self.config.end_date:
            params["latest"] = self.convert_date_to_ts(self.config.end_date)

        all_messages = []
        page = 1

        while True:
            try:
                logging.info(f"Descargando página {page}...")
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()

                if not data.get("ok"):
                    raise Exception(f"Error en la API de Slack: {data.get('error')}")

                messages = data["messages"]
                all_messages.extend(messages)
                logging.info(f"Descargados {len(messages)} mensajes")

                if "next_cursor" in data.get("response_metadata", {}):
                    params["cursor"] = data["response_metadata"]["next_cursor"]
                    page += 1
                    time.sleep(self.config.rate_limit_delay)
                else:
                    break

            except requests.exceptions.RequestException as e:
                logging.error(f"Error en la request: {str(e)}")
                raise

        return all_messages

    def save_messages(self, messages: List[Dict]) -> str:
        """Guarda los mensajes en un archivo JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        date_range = ""
        if self.config.start_date:
            date_range += f"_from_{self.config.start_date.strftime('%Y%m%d')}"
        if self.config.end_date:
            date_range += f"_to_{self.config.end_date.strftime('%Y%m%d')}"
        
        filename = os.path.join(
            self.config.output_dir,
            f"slack_messages_{self.config.channel_id}{date_range}_{timestamp}.json"
        )
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "channel_id": self.config.channel_id,
                "download_date": timestamp,
                "start_date": self.config.start_date.isoformat() if self.config.start_date else None,
                "end_date": self.config.end_date.isoformat() if self.config.end_date else None,
                "message_count": len(messages),
                "messages": messages
            }, f, indent=2, ensure_ascii=False)
        
        return filename

def parse_date(date_str: str) -> datetime:
    """Convierte una cadena de fecha en formato YYYY-MM-DD a datetime"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Formato de fecha inválido: {str(e)}")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Descarga mensajes de un canal de Slack')
    
    parser.add_argument(
        'channel_id',
        help='ID del canal de Slack (ej: C01234567)'
    )
    
    parser.add_argument(
        '--start-date',
        type=parse_date,
        help='Fecha de inicio en formato YYYY-MM-DD'
    )
    
    parser.add_argument(
        '--end-date',
        type=parse_date,
        help='Fecha final en formato YYYY-MM-DD'
    )
    
    parser.add_argument(
        '--output-dir',
        default='slack_exports',
        help='Directorio donde se guardarán los archivos'
    )
    
    parser.add_argument(
        '--token',
        default=os.getenv("SLACK_TOKEN"),
        help='Token de Slack (también puede usar la variable de entorno SLACK_TOKEN)'
    )

    return parser.parse_args()

def main():
    args = parse_arguments()
    
    if not args.token:
        args.token = click.prompt('Slack Token', hide_input=True)

    try:
        config = SlackConfig(
            token=args.token,
            channel_id=args.channel_id,
            start_date=args.start_date,
            end_date=args.end_date,
            output_dir=args.output_dir
        )
        
        downloader = SlackDownloader(config)
        
        # Obtener información del canal
        channel_info = downloader.get_channel_info()
        channel_name = channel_info.get('channel', {}).get('name', 'unknown_channel')
        channel_type = channel_info.get('channel', {}).get('is_private', False)
        channel_type_str = "privado" if channel_type else "público"
        
        logging.info(f"Canal encontrado: {channel_name} (tipo: {channel_type_str})")
        
        # Mostrar rango de fechas si está especificado
        if config.start_date:
            logging.info(f"Fecha inicio: {config.start_date.strftime('%Y-%m-%d')}")
        if config.end_date:
            logging.info(f"Fecha fin: {config.end_date.strftime('%Y-%m-%d')}")
        
        # Descargar mensajes
        messages = downloader.fetch_messages()
        
        # Guardar mensajes
        output_file = downloader.save_messages(messages)
        logging.info(f"Se han descargado {len(messages)} mensajes")
        logging.info(f"Archivo guardado en: {output_file}")

    except Exception as e:
        logging.error(f"Error durante la ejecución: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
