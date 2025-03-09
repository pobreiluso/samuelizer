from abc import ABC, abstractmethod

class TranscriptionService(ABC):
    @abstractmethod
    def transcribe(self, audio_file_path, diarization: bool = False):
        pass
