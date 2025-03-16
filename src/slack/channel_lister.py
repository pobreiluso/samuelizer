import logging
from typing import Dict, List, Optional, Tuple
import requests
import time
from src.slack.http_client import HttpClientInterface, RequestsClient
from src.slack.exceptions import SlackAPIError, SlackRateLimitError

logger = logging.getLogger(__name__)

class SlackChannelLister:
    """
    Lista los canales de Slack a los que tiene acceso un token.
    """
    
    def __init__(self, token: str, http_client: HttpClientInterface = None):
        """
        Inicializa el listador de canales.
        
        Args:
            token: Token de autenticación de Slack
            http_client: Cliente HTTP para hacer las peticiones
        """
        self.token = token
        self.http_client = http_client or RequestsClient()
        self.base_url = "https://slack.com/api"
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def list_channels(self, include_private: bool = True, 
                     include_archived: bool = False) -> List[Dict]:
        """
        Lista todos los canales a los que tiene acceso el token.
        
        Args:
            include_private: Si se deben incluir canales privados
            include_archived: Si se deben incluir canales archivados
            
        Returns:
            List[Dict]: Lista de información de canales
            
        Raises:
            SlackAPIError: Si hay un error en la API de Slack
        """
        all_channels = []
        
        # Primero obtener canales públicos
        public_channels = self._get_channels("conversations.list", {
            "types": "public_channel",
            "exclude_archived": not include_archived,
            "limit": 1000
        })
        all_channels.extend(public_channels)
        logger.info(f"Encontrados {len(public_channels)} canales públicos")
        
        # Luego obtener canales privados si se solicitan
        if include_private:
            private_channels = self._get_channels("conversations.list", {
                "types": "private_channel",
                "exclude_archived": not include_archived,
                "limit": 1000
            })
            all_channels.extend(private_channels)
            logger.info(f"Encontrados {len(private_channels)} canales privados")
            
            # También obtener mensajes directos (DMs)
            dms = self._get_channels("conversations.list", {
                "types": "im",
                "limit": 1000
            })
            all_channels.extend(dms)
            logger.info(f"Encontrados {len(dms)} mensajes directos")
            
            # Y grupos de mensajes directos (MPDMs)
            mpdms = self._get_channels("conversations.list", {
                "types": "mpim",
                "limit": 1000
            })
            all_channels.extend(mpdms)
            logger.info(f"Encontrados {len(mpdms)} grupos de mensajes directos")
        
        return all_channels
    
    def _get_channels(self, method: str, params: Dict) -> List[Dict]:
        """
        Obtiene canales de la API de Slack con paginación.
        
        Args:
            method: Método de la API a llamar
            params: Parámetros para la llamada
            
        Returns:
            List[Dict]: Lista de canales
            
        Raises:
            SlackAPIError: Si hay un error en la API de Slack
        """
        url = f"{self.base_url}/{method}"
        channels = []
        
        while True:
            try:
                response = self.http_client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                if not data.get("ok"):
                    error_msg = data.get("error", "Unknown error")
                    if error_msg == "ratelimited":
                        retry_after = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limit alcanzado. Esperando {retry_after} segundos...")
                        time.sleep(retry_after)
                        continue
                    raise SlackAPIError(f"Error en la API de Slack: {error_msg}")
                
                channels.extend(data.get("channels", []))
                
                # Verificar si hay más páginas
                if "response_metadata" in data and "next_cursor" in data["response_metadata"]:
                    next_cursor = data["response_metadata"]["next_cursor"]
                    if next_cursor:
                        params["cursor"] = next_cursor
                        time.sleep(0.5)  # Pequeña pausa para evitar rate limits
                        continue
                
                break
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error de conexión: {str(e)}")
                raise SlackAPIError(f"Error de conexión: {str(e)}")
        
        return channels
    
    def get_channel_details(self, channels: List[Dict]) -> List[Dict]:
        """
        Enriquece la información de los canales con detalles adicionales.
        
        Args:
            channels: Lista de información básica de canales
            
        Returns:
            List[Dict]: Lista de información detallada de canales
        """
        enriched_channels = []
        
        for channel in channels:
            channel_type = self._determine_channel_type(channel)
            
            # Obtener nombre para mostrar
            display_name = self._get_display_name(channel, channel_type)
            
            # Crear objeto enriquecido
            enriched_channel = {
                "id": channel.get("id"),
                "name": display_name,
                "type": channel_type,
                "is_archived": channel.get("is_archived", False),
                "created": channel.get("created"),
                "creator": channel.get("creator"),
                "member_count": channel.get("num_members", 0),
                "purpose": channel.get("purpose", {}).get("value", ""),
                "topic": channel.get("topic", {}).get("value", ""),
                "is_member": channel.get("is_member", False),
                "is_private": channel.get("is_private", False),
                "is_shared": channel.get("is_shared", False),
                "is_org_shared": channel.get("is_org_shared", False),
                "raw_data": channel  # Mantener los datos originales por si acaso
            }
            
            enriched_channels.append(enriched_channel)
        
        return enriched_channels
    
    def _determine_channel_type(self, channel: Dict) -> str:
        """
        Determina el tipo de canal basado en sus propiedades.
        
        Args:
            channel: Información del canal
            
        Returns:
            str: Tipo de canal (public_channel, private_channel, im, mpim)
        """
        if channel.get("is_im", False):
            return "im"
        elif channel.get("is_mpim", False):
            return "mpim"
        elif channel.get("is_private", False):
            return "private_channel"
        else:
            return "public_channel"
    
    def _get_display_name(self, channel: Dict, channel_type: str) -> str:
        """
        Obtiene un nombre para mostrar para el canal.
        
        Args:
            channel: Información del canal
            channel_type: Tipo de canal
            
        Returns:
            str: Nombre para mostrar
        """
        if channel_type == "im":
            # Para DMs, mostrar el nombre del usuario
            user_id = channel.get("user")
            if user_id:
                return f"DM con <@{user_id}>"
            return "Mensaje directo"
        elif channel_type == "mpim":
            # Para MPDMs, mostrar los nombres de los usuarios
            return channel.get("name", "Grupo de mensajes directos")
        else:
            # Para canales regulares, mostrar el nombre del canal
            return f"#{channel.get('name', 'canal-sin-nombre')}"
    
    def format_channels_for_display(self, channels: List[Dict]) -> str:
        """
        Formatea la lista de canales para mostrarla de forma legible.
        
        Args:
            channels: Lista de información de canales
            
        Returns:
            str: Texto formateado con la información de los canales
        """
        if not channels:
            return "No se encontraron canales accesibles con este token."
        
        # Agrupar por tipo
        public_channels = []
        private_channels = []
        dms = []
        mpdms = []
        
        for channel in channels:
            if channel["type"] == "public_channel":
                public_channels.append(channel)
            elif channel["type"] == "private_channel":
                private_channels.append(channel)
            elif channel["type"] == "im":
                dms.append(channel)
            elif channel["type"] == "mpim":
                mpdms.append(channel)
        
        # Ordenar cada grupo por nombre
        public_channels.sort(key=lambda x: x["name"])
        private_channels.sort(key=lambda x: x["name"])
        dms.sort(key=lambda x: x["name"])
        mpdms.sort(key=lambda x: x["name"])
        
        # Construir el texto
        result = []
        
        result.append(f"Total de canales accesibles: {len(channels)}\n")
        
        if public_channels:
            result.append(f"\n== Canales públicos ({len(public_channels)}) ==")
            for channel in public_channels:
                archived = " [ARCHIVADO]" if channel["is_archived"] else ""
                member = " [MIEMBRO]" if channel["is_member"] else ""
                result.append(f"- {channel['name']}{archived}{member} (ID: {channel['id']})")
        
        if private_channels:
            result.append(f"\n== Canales privados ({len(private_channels)}) ==")
            for channel in private_channels:
                archived = " [ARCHIVADO]" if channel["is_archived"] else ""
                member = " [MIEMBRO]" if channel["is_member"] else ""
                result.append(f"- {channel['name']}{archived}{member} (ID: {channel['id']})")
        
        if dms:
            result.append(f"\n== Mensajes directos ({len(dms)}) ==")
            for channel in dms:
                result.append(f"- {channel['name']} (ID: {channel['id']})")
        
        if mpdms:
            result.append(f"\n== Grupos de mensajes directos ({len(mpdms)}) ==")
            for channel in mpdms:
                result.append(f"- {channel['name']} (ID: {channel['id']})")
        
        return "\n".join(result)
