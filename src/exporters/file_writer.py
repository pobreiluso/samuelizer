import os
import json
from typing import Any
from src.interfaces import FileWriterInterface

class FileWriter(FileWriterInterface):
    """
    Handles file writing operations
    """
    def ensure_directory_exists(self, path: str) -> None:
        """
        Ensure the directory for a file path exists
        
        Args:
            path: File path
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
    
    def write_json(self, data: Any, output_path: str) -> str:
        """
        Write data to a JSON file
        
        Args:
            data: Data to write
            output_path: Path where to save the file
            
        Returns:
            str: Path to the written file
        """
        self.ensure_directory_exists(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return output_path
