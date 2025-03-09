import os
import pytest
from src.transcription.meeting_transcription import AudioTranscriptionService
from src.transcription.audio_processor import AudioFileHandler, TranscriptionFileWriter, SpeakerDiarization

class DummyTranscriptionClient:
    def transcribe(self, audio_file, model, response_format="text"):
        return "dummy transcription"

class DummyDiarizationService:
    def detect_speakers(self, audio_file_path):
        return [{'speaker': 'Test', 'start': 0, 'end': 1}]

class DummyFileWriter:
    def save_transcription(self, transcription, file_path):
        return "saved"

@pytest.fixture
def service(tmp_path):
    # Create a dummy audio file
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"dummy audio data")
    service_instance = AudioTranscriptionService(
        transcription_client=DummyTranscriptionClient(),
        diarization_service=DummyDiarizationService(),
        file_handler=AudioFileHandler(),
        file_writer=DummyFileWriter(),
        model="dummy-model"
    )
    return service_instance, str(audio_file)

def test_transcribe_whole(service):
    srv, audio_path = service
    result = srv.transcribe_whole(audio_path)
    assert result == "dummy transcription"

def test_transcribe_with_diarization(service):
    srv, audio_path = service
    result = srv.transcribe_with_diarization(audio_path)
    assert "Test" in result
