import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Global configuration management"""
    SLACK_TOKEN = os.getenv("SLACK_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    
    # Slack configuration
    SLACK_RATE_LIMIT_DELAY = float(os.getenv("SLACK_RATE_LIMIT_DELAY", "1.0"))
    SLACK_BATCH_SIZE = int(os.getenv("SLACK_BATCH_SIZE", "1000"))
    
    # File paths and directories
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "slack_exports")
    LOG_FILE = os.getenv("LOG_FILE", "slack_download.log")
