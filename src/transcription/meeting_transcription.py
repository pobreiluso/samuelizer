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
    Service for transcribing audio files.
    Dependencies are injected to follow the Dependency Inversion Principle.
    """
    def __init__(self, transcription_client, diarization_service, file_handler, file_writer, model="whisper-1"):
        self.model = model
        self.transcription_client = transcription_client
        self.diarization_service = diarization_service
        self.file_handler = file_handler
        self.file_writer = file_writer

    def _transcribe_segment(self, audio_file_path, start_time, end_time):
        # Extract segment using the injected file_handler (AudioFileHandler)
        segment_path = self.file_handler.extract_segment(audio_file_path, start_time, end_time)
        with open(segment_path, 'rb') as segment_file:
            segment_transcription = self.transcription_client.transcribe(segment_file, model=self.model)
        os.unlink(segment_path)
        return segment_transcription

    def transcribe(self, audio_file_path, diarization: bool = False) -> str:
        try:
            logger.info("Starting transcription...")
            if diarization:
                logger.info("Diarization enabled. Processing audio segments...")
                segments = self.diarization_service.detect_speakers(audio_file_path)
                full_transcript = ""
                for seg in segments:
                    seg_text = self._transcribe_segment(audio_file_path, start_time=seg['start'], end_time=seg['end'])
                    full_transcript += f"[{seg['speaker']}]: {seg_text}\n"
                self.file_writer.save_transcription(full_transcript, audio_file_path)
                return full_transcript
            else:
                with open(audio_file_path, 'rb') as audio_file:
                    transcription = self.transcription_client.transcribe(audio_file, model=self.model)
                self.file_writer.save_transcription(transcription, audio_file_path)
                return transcription
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise Exception(f"Transcription failed: {e}")
