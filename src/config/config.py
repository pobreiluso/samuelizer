import os
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()

class Config:
    """
    Gestión global de configuración del sistema.
    
    Esta clase centraliza todas las configuraciones y variables de entorno necesarias
    para el funcionamiento de la aplicación.
    
    Atributos:
        SLACK_TOKEN (str): Token de autenticación para la API de Slack
        OPENAI_API_KEY (str): Clave de API para servicios de OpenAI
        GOOGLE_CLIENT_ID (str): ID de cliente para autenticación con Google
        GOOGLE_CLIENT_SECRET (str): Secreto de cliente para autenticación con Google
        SLACK_RATE_LIMIT_DELAY (float): Delay entre peticiones a la API de Slack (en segundos)
        SLACK_BATCH_SIZE (int): Número de mensajes por petición a la API de Slack
        OUTPUT_DIR (str): Directorio para archivos de salida
        LOG_FILE (str): Ruta del archivo de logs
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
