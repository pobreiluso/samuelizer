import requests
import json
import logging
import click
from datetime import datetime, timezone
import time
from typing import Dict, List, Optional
import os
from dataclasses import dataclass
import argparse
import sys
import re
from src.config.config import Config
from src.interfaces import SlackServiceInterface
from src.slack.http_client import HttpClientInterface, RequestsClient
from src.exporters.json_exporter import JSONExporter

# Custom exceptions
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

class MessageProcessor:
    """
    Processes Slack messages to replace user mentions and other formatting
    """
    def __init__(self, slack_service: SlackServiceInterface):
        self.slack_service = slack_service
        
    def replace_user_mentions(self, text: str) -> str:
        """
        Replaces user mentions in the text with user names
        
        Args:
            text: Text containing user mentions in the format <@USER_ID>
            
        Returns:
            str: Text with user mentions replaced by @username
        """
        if not text:
            return text
            
        def replace_mention(match):
            user_id = match.group(1)
            return f"@{self.slack_service.get_user_info(user_id)}"
            
        return re.sub(r'<@([A-Z0-9]+)>', replace_mention, text)
        
    def process_message(self, message: Dict) -> Dict:
        """
        Process a Slack message to replace mentions and format text
        
        Args:
            message: Slack message dictionary
            
        Returns:
            Dict: Processed message
        """
        if "text" in message:
            message["text"] = self.replace_user_mentions(message["text"])
        return message

class SlackDownloader(SlackServiceInterface):
    """
    Service for downloading and processing Slack messages.
    
    This class handles:
    - Authentication with Slack API
    - Message downloading with pagination
    - User information caching
    """
    
    def __init__(self, config: SlackConfig, http_client: HttpClientInterface = None):
        """
        Initialize the downloader with configuration.
        
        Args:
            config: Configuration object with API credentials and settings
            http_client: HTTP client for making requests (defaults to RequestsClient)
        """
        self.config = config
        self.http_client = http_client or RequestsClient()
        self.base_url = "https://slack.com/api"
        self.headers = {"Authorization": f"Bearer {self.config.token}"}
        self.users_cache = {}
        
        # Create message processor
        self.message_processor = MessageProcessor(self)
        
        # Ensure output directory exists
        if not os.path.exists(config.output_dir):
            os.makedirs(config.output_dir)

    def get_user_info(self, user_id: str) -> str:
        """
        Get Slack username from user ID with retry logic.
        
        Args:
            user_id: Slack user ID to look up
            
        Returns:
            str: User's display name or real name, falls back to user_id if not found
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

    def get_channel_info(self) -> Dict:
        """
        Get information about a Slack channel
        
        Returns:
            Dict: Channel information
            
        Raises:
            SlackAPIError: If there's an error in the Slack API
            RequestError: If there's an error in the HTTP request
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
        """Convert a datetime object to a Slack timestamp"""
        return str(int(date.timestamp()))

    def fetch_messages(self) -> List[Dict]:
        """
        Download all messages from the channel using pagination and date filters
        
        Returns:
            List[Dict]: List of message dictionaries
            
        Raises:
            RequestError: If there's an error in the HTTP request
            SlackAPIError: If there's an error in the Slack API
        """
        url = f"{self.base_url}/conversations.history"
        params = {
            "channel": self.config.channel_id,
            "limit": self.config.batch_size,
        }

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
                    error_msg = data.get("error", "Unknown error")
                    raise SlackAPIError(f"Error en la API de Slack: {error_msg}")

                messages = data["messages"]
                processed_messages = [self.message_processor.process_message(msg) for msg in messages]
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
                raise RequestError(f"Failed to connect to Slack API: {str(e)}")

        return all_messages
        
    def fetch_thread_messages(self, thread_ts: str) -> List[Dict]:
        """
        Download all messages from a specific thread
        
        Args:
            thread_ts: Thread timestamp to fetch replies from
            
        Returns:
            List[Dict]: List of message dictionaries
            
        Raises:
            RequestError: If there's an error in the HTTP request
            SlackAPIError: If there's an error in the Slack API
        """
        url = f"{self.base_url}/conversations.replies"
        params = {
            "channel": self.config.channel_id,
            "ts": thread_ts,
            "limit": self.config.batch_size,
        }

        all_messages = []
        page = 1

        while True:
            try:
                logging.info(f"Downloading thread page {page}...")
                response = self.http_client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()

                if not data.get("ok"):
                    error_msg = data.get("error", "Unknown error")
                    raise SlackAPIError(f"Error en la API de Slack: {error_msg}")

                messages = data["messages"]
                processed_messages = [self.message_processor.process_message(msg) for msg in messages]
                all_messages.extend(processed_messages)
                logging.info(f"Downloaded {len(messages)} thread messages")

                if "next_cursor" in data.get("response_metadata", {}):
                    params["cursor"] = data["response_metadata"]["next_cursor"]
                    page += 1
                    time.sleep(self.config.rate_limit_delay)
                else:
                    break

            except requests.exceptions.RequestException as e:
                logging.error(f"Request error: {str(e)}")
                raise RequestError(f"Failed to connect to Slack API: {str(e)}")

        return all_messages

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
        argparse.Namespace: Parsed command line arguments
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
    6. Saves messages to JSON file using JSONExporter
    
    Exits:
        0: Successful execution
        1: Error occurred during execution
    """
    args = parse_arguments()
    
    if not args.token:
        args.token = click.prompt('Slack Token', hide_input=True)

    try:
        # Create configuration
        config = SlackConfig(
            token=args.token,
            channel_id=args.channel_id,
            start_date=args.start_date,
            end_date=args.end_date,
            output_dir=args.output_dir
        )
        
        # Create services with dependency injection
        http_client = RequestsClient()
        downloader = SlackDownloader(config, http_client)
        exporter = JSONExporter()
        
        # Get channel information
        channel_info = downloader.get_channel_info()
        channel_name = channel_info.get('channel', {}).get('name', 'unknown_channel')
        channel_type = channel_info.get('channel', {}).get('is_private', False)
        channel_type_str = "privado" if channel_type else "público"
        
        logging.info(f"Canal encontrado: {channel_name} (tipo: {channel_type_str})")
        
        # Show date range if specified
        if config.start_date:
            logging.info(f"Fecha inicio: {config.start_date.strftime('%Y-%m-%d')}")
        if config.end_date:
            logging.info(f"Fecha fin: {config.end_date.strftime('%Y-%m-%d')}")
        
        # Download messages
        messages = downloader.fetch_messages()
        
        # Save messages using the exporter
        output_file = exporter.export_messages(
            messages,
            config.channel_id,
            config.output_dir,
            start_date=config.start_date,
            end_date=config.end_date
        )
        
        logging.info(f"Se han descargado {len(messages)} mensajes")
        logging.info(f"Archivo guardado en: {output_file}")

    except Exception as e:
        logging.error(f"Error durante la ejecución: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
