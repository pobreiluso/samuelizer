import os
import json
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SlackUserCache:
    """
    Caché para información de usuarios de Slack.
    """
    
    def __init__(self, cache_dir: str = ".cache/slack_users"):
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_dir()
        self.memory_cache = {}
        
    def _ensure_cache_dir(self) -> None:
        """Asegura que el directorio de caché exista."""
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def get(self, user_id: str) -> Optional[Dict]:
        """Obtiene información de usuario desde la caché."""
        # Primero buscar en memoria
        if user_id in self.memory_cache:
            return self.memory_cache[user_id]
            
        # Luego buscar en disco
        cache_file = self.cache_dir / f"{user_id}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    user_info = json.load(f)
                    self.memory_cache[user_id] = user_info
                    return user_info
            except Exception as e:
                logger.error(f"Error al leer caché de usuario {user_id}: {str(e)}")
                
        return None
        
    def set(self, user_id: str, user_info: Dict) -> None:
        """Guarda información de usuario en la caché."""
        # Guardar en memoria
        self.memory_cache[user_id] = user_info
        
        # Guardar en disco
        cache_file = self.cache_dir / f"{user_id}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(user_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error al guardar caché de usuario {user_id}: {str(e)}")
