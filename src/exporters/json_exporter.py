import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from src.interfaces import MessageExporterInterface

class JSONExporter(MessageExporterInterface):
    def export(self, data: Any, output_path: str) -> str:
        """
        Export any data to a JSON file
        
        Args:
            data: Data to export
            output_path: Path where to save the JSON file
            
        Returns:
            str: Path to the exported file
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        return output_path
        
    def export_messages(self, 
                       messages: List[Dict], 
                       channel_id: str, 
                       output_dir: str,
                       start_date: Optional[datetime] = None, 
                       end_date: Optional[datetime] = None) -> str:
        """
        Export Slack messages to a JSON file
        
        Args:
            messages: List of message dictionaries
            channel_id: ID of the Slack channel
            output_dir: Directory where to save the exported file
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            str: Path to the exported file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_range = ""
        if start_date:
            date_range += f"_from_{start_date.strftime('%Y%m%d')}"
        if end_date:
            date_range += f"_to_{end_date.strftime('%Y%m%d')}"
            
        filename = os.path.join(
            output_dir,
            f"slack_messages_{channel_id}{date_range}_{timestamp}.json"
        )
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        data = {
            "channel_id": channel_id,
            "download_date": timestamp,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "message_count": len(messages),
            "messages": messages
        }
        
        return self.export(data, filename)
