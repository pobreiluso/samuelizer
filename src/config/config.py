import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Global system configuration management.
    
    This class centralizes all configurations and environment variables
    needed for the application to function.
    
    Attributes:
        SLACK_TOKEN (str): Authentication token for Slack API
        OPENAI_API_KEY (str): API key for OpenAI services
        GOOGLE_CLIENT_ID (str): Client ID for Google authentication
        GOOGLE_CLIENT_SECRET (str): Client secret for Google authentication
        SLACK_RATE_LIMIT_DELAY (float): Delay between Slack API requests (in seconds)
        SLACK_BATCH_SIZE (int): Number of messages per Slack API request
        OUTPUT_DIR (str): Directory for output files
        LOG_FILE (str): Path to log file
    """
    
    # Credenciales de APIs
    SLACK_TOKEN = os.getenv("SLACK_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    
    # Configuración de Slack
    SLACK_RATE_LIMIT_DELAY = float(os.getenv("SLACK_RATE_LIMIT_DELAY", "1.0"))
    SLACK_BATCH_SIZE = int(os.getenv("SLACK_BATCH_SIZE", "1000"))
    
    # Rutas de archivos y directorios
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "slack_exports")
    LOG_FILE = os.getenv("LOG_FILE", "slack_download.log")
