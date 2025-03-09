import os
import openai
import logging
from tqdm import tqdm
from src.interfaces import TranscriptionService
from src.transcription.audio_processor import AudioFileHandler, TranscriptionFileWriter, SpeakerDiarization

logger = logging.getLogger(__name__)

class AudioFileHandler:
    """
    Responsible for handling audio file operations such as obtaining duration and extracting segments.
    """
    @staticmethod
    def get_audio_duration(audio_file_path):
        try:
            import subprocess
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                 '-of', 'default=noprint_wrappers=1:nokey=1', audio_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return float(result.stdout.strip())
        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")
            return 300.0

    @staticmethod
    def extract_segment(audio_file_path, start_time, end_time):
        import tempfile
        import subprocess
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
        subprocess.run([
            'ffmpeg', '-y', '-i', audio_file_path,
            '-ss', str(start_time), '-to', str(end_time),
            '-c:a', 'copy', temp_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return temp_path

class TranscriptionFileWriter:
    """
    Handles writing transcription results to text files.
    """
    @staticmethod
    def save_transcription(transcription, audio_file_path):
        output_txt = os.path.splitext(audio_file_path)[0] + "_transcription.txt"
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write(transcription)
        logger.info(f"Transcription saved to: {output_txt}")
        return output_txt

class OpenAITranscriptionClient:
    """
    OpenAI transcription client implementation.
    """
    def __init__(self, client=None):
        self.client = client or openai

    def transcribe(self, audio_file, model, response_format="text"):
        return self.client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            response_format=response_format
        )

class AudioTranscriptionService(TranscriptionService):
    """
    Service for transcribing audio files. This module is focused solely on the transcription process.
    """
    def __init__(self, model="whisper-1", transcription_client=None):
        self.model = model
        self.transcription_client = transcription_client or OpenAITranscriptionClient()
        self.file_handler = AudioFileHandler()
        self.file_writer = TranscriptionFileWriter()

    def transcribe(self, audio_file_path, diarization: bool = False) -> str:
        try:
            logger.info("Starting transcription...")
            with open(audio_file_path, 'rb') as audio_file:
                transcription = self.transcription_client.transcribe(audio_file, model=self.model)
            self.file_writer.save_transcription(transcription, audio_file_path)
            return transcription
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise Exception(f"Transcription failed: {e}")
