import requests
import json
import logging
import click
from datetime import datetime, timezone

class SlackAPIError(Exception):
    """
    Custom exception for Slack API errors.
    
    Raised when:
    - API returns an error response
    - Authentication fails
    - Rate limits are exceeded
    - Invalid parameters are provided
    """
    pass

class RequestError(Exception):
    """
    Custom exception for HTTP request errors.
    
    Raised when:
    - Network connection fails
    - DNS resolution fails
    - Timeout occurs
    - SSL/TLS errors occur
    """
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
    """
    Configuration dataclass for Slack API interactions.
    
    Attributes:
        token (str): Slack API authentication token
        channel_id (str): ID of the Slack channel to process
        start_date (Optional[datetime]): Start date for message filtering
        end_date (Optional[datetime]): End date for message filtering
        output_dir (str): Directory where exported files will be saved
        rate_limit_delay (float): Delay between API requests to avoid rate limiting
        batch_size (int): Number of messages to fetch per API request
    """
    token: str
    channel_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    output_dir: str = Config.OUTPUT_DIR
    rate_limit_delay: float = Config.SLACK_RATE_LIMIT_DELAY
    batch_size: int = Config.SLACK_BATCH_SIZE

class SlackDownloader:
    """
    Main class for downloading and processing Slack messages.
    
    This class handles:
    - Authentication with Slack API
    - Message downloading with pagination
    - User information caching
    - Message processing and formatting
    - Export to JSON files
    """
    
    def __init__(self, config: SlackConfig, http_client=None):
        """
        Initialize the downloader with configuration.
        
        Args:
            config (SlackConfig): Configuration object with API credentials and settings
            http_client: Optional HTTP client to allow dependency injection (defaults to requests)
            
        Creates:
            - Output directory if it doesn't exist
            - Authorization headers for API requests
            - Empty user information cache
        """
        self.config = config
        self.http_client = http_client or requests
        self.base_url = "https://slack.com/api"
        self.headers = {"Authorization": f"Bearer {self.config.token}"}
        self.users_cache = {}
        
        if not os.path.exists(config.output_dir):
            os.makedirs(config.output_dir)

    def get_user_info(self, user_id: str) -> str:
        """
        Get Slack username from user ID with retry logic.
        
        Args:
            user_id (str): Slack user ID to look up
            
        Returns:
            str: User's display name or real name, falls back to unknown_user if not found
            
        Note:
            Results are cached to minimize API calls
            Implements retry logic for API failures
        """
        if not user_id:
            logger.warning("Empty user_id provided")
            return "unknown_user"
            
        if user_id in self.users_cache:
            return self.users_cache[user_id]
            
        max_retries = 3
        retry_delay = 1
            
        try:
            url = f"{self.base_url}/users.info"
            params = {"user": user_id}
            
            response = self.http_client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("ok"):
                logger.warning(f"No se pudo obtener info del usuario {user_id}")
                return user_id
                
            user = data["user"]
            display_name = user.get("profile", {}).get("display_name") or user.get("real_name") or user_id
            self.users_cache[user_id] = display_name
            return display_name
            
        except Exception as e:
            logger.warning(f"Error obteniendo info del usuario {user_id}: {e}")
            return user_id

    def replace_user_mentions(self, text: str) -> str:
        """Replaces user mentions in the text"""
        import re
        
        def replace_mention(match):
            user_id = match.group(1)
            return f"@{self.get_user_info(user_id)}"
            
        return re.sub(r'<@([A-Z0-9]+)>', replace_mention, text)

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
            response = self.http_client.get(url, headers=self.headers, params=params, verify=True)
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
        
        # Process user mentions in messages
        def process_message(message):
            if "text" in message:
                message["text"] = self.replace_user_mentions(message["text"])
            return message

        # Add date filters if specified
        if self.config.start_date:
            params["oldest"] = self.convert_date_to_ts(self.config.start_date)
        if self.config.end_date:
            params["latest"] = self.convert_date_to_ts(self.config.end_date)

        all_messages = []
        page = 1

        while True:
            try:
                logging.info(f"Downloading page {page}...")
                response = self.http_client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()

                if not data.get("ok"):
                    raise Exception(f"Error en la API de Slack: {data.get('error')}")

                messages = data["messages"]
                processed_messages = [process_message(msg) for msg in messages]
                all_messages.extend(processed_messages)
                logging.info(f"Downloaded {len(messages)} messages")

                if "next_cursor" in data.get("response_metadata", {}):
                    params["cursor"] = data["response_metadata"]["next_cursor"]
                    page += 1
                    time.sleep(self.config.rate_limit_delay)
                else:
                    break

            except requests.exceptions.RequestException as e:
                logging.error(f"Request error: {str(e)}")
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
    """
    Convert a date string to datetime object.
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        datetime: Parsed date with UTC timezone
        
    Raises:
        ArgumentTypeError: If date format is invalid
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Formato de fecha inválido: {str(e)}")

def parse_arguments():
    """
    Parse command line arguments for the script.
    
    Returns:
        argparse.Namespace: Parsed command line arguments containing:
            - channel_id: Slack channel identifier
            - start_date: Optional start date for filtering
            - end_date: Optional end date for filtering
            - output_dir: Directory for saving exports
            - token: Slack API token
            
    Note:
        The token can also be provided via SLACK_TOKEN environment variable
    """
    parser = argparse.ArgumentParser(description='Download messages from a Slack channel')
    
    parser.add_argument(
        'channel_id',
        help='Slack channel ID (e.g., C01234567)'
    )
    
    parser.add_argument(
        '--start-date',
        type=parse_date,
        help='Start date in YYYY-MM-DD format'
    )
    
    parser.add_argument(
        '--end-date',
        type=parse_date,
        help='End date in YYYY-MM-DD format'
    )
    
    parser.add_argument(
        '--output-dir',
        default='slack_exports',
        help='Directory where files will be saved'
    )
    
    parser.add_argument(
        '--token',
        default=os.getenv("SLACK_TOKEN"),
        help='Slack token (can also use SLACK_TOKEN environment variable)'
    )

    return parser.parse_args()

def main():
    """
    Main entry point for the Slack message downloader.
    
    This function:
    1. Parses command line arguments
    2. Prompts for Slack token if not provided
    3. Creates SlackDownloader instance
    4. Downloads channel information
    5. Fetches messages with optional date filtering
    6. Saves messages to JSON file
    
    Exits:
        0: Successful execution
        1: Error occurred during execution
    """
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
