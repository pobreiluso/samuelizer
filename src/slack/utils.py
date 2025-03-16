import re
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def parse_slack_link(link: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extrae el ID del canal y el timestamp del mensaje de un enlace de Slack.
    
    Args:
        link: Enlace de Slack (https://workspace.slack.com/archives/CXXXXXXXX/pXXXXXXXXXXXXXXXX)
        
    Returns:
        Tuple[Optional[str], Optional[str]]: (channel_id, message_ts) o (None, None) si no es válido
    """
    # Patrón para extraer el ID del canal y el timestamp del mensaje
    pattern = r'archives/([A-Z0-9]+)(?:/p([0-9]+))?'
    match = re.search(pattern, link)
    
    if not match:
        logger.warning(f"No se pudo extraer información del enlace de Slack: {link}")
        return None, None
    
    channel_id = match.group(1)
    logger.info(f"ID de canal extraído: {channel_id}")
    
    # El timestamp puede no estar presente (si es un enlace a un canal)
    message_ts = match.group(2) if match.group(2) else None
    
    # Convertir el formato del timestamp si es necesario
    if message_ts:
        # Slack usa un formato especial para los timestamps en los enlaces
        # Necesitamos convertirlo al formato que usa la API (segundos.microsegundos)
        message_ts = f"{message_ts[:-6]}.{message_ts[-6:]}"
        logger.info(f"Timestamp extraído y convertido: {message_ts}")
    
    return channel_id, message_ts
