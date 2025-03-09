import json
import os
from datetime import datetime

class JSONExporter:
    @staticmethod
    def export_messages(messages, channel_id, output_dir, start_date=None, end_date=None):
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
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "channel_id": channel_id,
                "download_date": timestamp,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "message_count": len(messages),
                "messages": messages
            }, f, indent=2, ensure_ascii=False)
        return filename
