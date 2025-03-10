from typing import Any

class TextPreprocessor:
    """
    Handles text preprocessing for analysis.
    """
    def __init__(self, max_chunk_size: int = 4000) -> None:
        self.max_chunk_size = max_chunk_size

    def prepare_text(self, text: str) -> str:
        if len(text) > self.max_chunk_size:
            chunks = [text[i:i+self.max_chunk_size] for i in range(0, len(text), self.max_chunk_size)]
            return "\n\n".join(chunks)
        return text
