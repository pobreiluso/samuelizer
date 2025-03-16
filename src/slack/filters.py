from datetime import datetime
from typing import Dict, List, Callable, Optional

class SlackMessageFilter:
    """
    Filtros avanzados para mensajes de Slack.
    """
    
    @staticmethod
    def by_date_range(messages: List[Dict], start_date: Optional[datetime] = None, 
                     end_date: Optional[datetime] = None) -> List[Dict]:
        """Filtra mensajes por rango de fechas."""
        if not start_date and not end_date:
            return messages
            
        filtered_messages = []
        for message in messages:
            ts = float(message.get('ts', 0))
            message_date = datetime.fromtimestamp(ts)
            
            if start_date and message_date < start_date:
                continue
                
            if end_date and message_date > end_date:
                continue
                
            filtered_messages.append(message)
            
        return filtered_messages
    
    @staticmethod
    def by_user(messages: List[Dict], user_id: str) -> List[Dict]:
        """Filtra mensajes por usuario."""
        return [msg for msg in messages if msg.get('user') == user_id]
    
    @staticmethod
    def by_has_replies(messages: List[Dict]) -> List[Dict]:
        """Filtra mensajes que tienen respuestas en hilos."""
        return [msg for msg in messages if msg.get('reply_count', 0) > 0]
    
    @staticmethod
    def by_has_reactions(messages: List[Dict]) -> List[Dict]:
        """Filtra mensajes que tienen reacciones."""
        return [msg for msg in messages if 'reactions' in msg]
    
    @staticmethod
    def by_custom_filter(messages: List[Dict], filter_func: Callable[[Dict], bool]) -> List[Dict]:
        """Aplica un filtro personalizado."""
        return [msg for msg in messages if filter_func(msg)]
