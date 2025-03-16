import logging
import time
from typing import Dict, List, Callable, Any

logger = logging.getLogger(__name__)

class SlackPaginator:
    """
    Maneja la paginación de resultados de la API de Slack.
    """
    
    def __init__(self, client_method: Callable, method_args: Dict[str, Any] = None, 
                 rate_limit_delay: float = 1.0, max_retries: int = 3):
        self.client_method = client_method
        self.method_args = method_args or {}
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        
    def fetch_all(self) -> List[Dict]:
        """Obtiene todos los resultados paginados."""
        all_results = []
        next_cursor = None
        
        while True:
            # Añadir cursor si existe
            if next_cursor:
                self.method_args['cursor'] = next_cursor
                
            # Realizar la llamada a la API con reintentos
            response = self._make_api_call()
            
            # Extraer resultados y añadirlos
            if 'messages' in response:
                all_results.extend(response['messages'])
            
            # Verificar si hay más páginas
            metadata = response.get('response_metadata', {})
            next_cursor = metadata.get('next_cursor', '')
            
            if not next_cursor:
                break
                
        return all_results
    
    def _make_api_call(self) -> Dict:
        """Realiza la llamada a la API con reintentos."""
        for attempt in range(self.max_retries):
            try:
                response = self.client_method(**self.method_args)
                time.sleep(self.rate_limit_delay)
                return response
            except Exception as e:
                logger.error(f"Error en intento {attempt+1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.rate_limit_delay * 2)
        
        return {"ok": False, "error": "Max retries exceeded"}
