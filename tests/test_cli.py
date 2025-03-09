import os
import sys
import tempfile
import json
import pytest
from click.testing import CliRunner
from src.cli import cli

def test_version_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['version'])
    assert result.exit_code == 0
    assert "samuelizer version" in result.output.lower()

def test_summarize_text_command(monkeypatch):
    runner = CliRunner()
    # Dummy the analysis in MeetingAnalyzer to avoid real API calls
    monkeypatch.setattr("src.transcription.meeting_analyzer.MeetingAnalyzer.analyze", lambda self, template, **kwargs: "Summary Dummy")
    result = runner.invoke(cli, ['text', 'Texto de prueba para analizar', '--api_key', 'dummy_key'])
    assert result.exit_code == 0
    # Either the dummy summary or the default CLI header is acceptable.
    assert "summary dummy" in result.output.lower() or "samuelization summary" in result.output.lower()

def test_media_command_file_not_found(tmp_path):
    runner = CliRunner()
    fake_file = tmp_path / "non_existent.mp3"
    result = runner.invoke(cli, ['media', str(fake_file), '--api_key', 'dummy_key'])
    # Expecting a non-zero exit code because the file does not exist.
    assert result.exit_code != 0
    assert "file does not exist" in result.output.lower()

def test_slack_command_basic(monkeypatch, tmp_path):
    runner = CliRunner()
    from src.slack.download_slack_channel import SlackDownloader
    # Monkeypatch fetch_messages to return dummy messages
    monkeypatch.setattr(SlackDownloader, "fetch_messages", lambda self: [{'text': 'Mensaje de prueba', 'user': 'U12345'}])
    result = runner.invoke(cli, ['slack', 'C12345678', '--start-date', '2023-01-01', '--end-date', '2023-01-02', '--token', 'dummy_token'])
    assert result.exit_code == 0
    # Validate that expected Spanish keywords appear in the output.
    assert ("mensaje" in result.output.lower() or "descargado" in result.output.lower() or "archivo" in result.output.lower())

def test_listen_command_simulation(monkeypatch):
    runner = CliRunner()
    from src.audio_capture.system_audio import SystemAudioCapture

    # Monkeypatch start_recording and stop_recording for simulation
    monkeypatch.setattr(SystemAudioCapture, "start_recording", lambda self, output_dir="recordings": None)
    monkeyatch_stop = lambda self: "dummy_recording.mp3"
    monkeypatch.setattr(SystemAudioCapture, "stop_recording", monkeyatch_stop)
    
    # Simulate KeyboardInterrupt during time.sleep to trigger end of recording
    def dummy_sleep(*args, **kwargs):
        raise KeyboardInterrupt()
    monkeypatch.setattr("time.sleep", dummy_sleep)
    
    result = runner.invoke(cli, ['listen', '--duration', '1', '--api_key', 'dummy_key'])
    assert result.exit_code == 0
    assert ("transcribing recorded audio" in result.output.lower() or "audio saved to:" in result.output.lower())

def test_media_command_valid_file(monkeypatch, tmp_path):
    runner = CliRunner()
    # Create a dummy mp3 file with dummy audio content to simulate valid file input
    dummy_audio = tmp_path / "dummy.mp3"
    dummy_audio.write_bytes(b"dummy audio contents")
    # Monkeypatch AudioTranscriptionService.transcribe to bypass actual transcription and return dummy text
    from src.transcription.meeting_transcription import AudioTranscriptionService
    monkeypatch.setattr(AudioTranscriptionService, "transcribe", lambda self, file_path, diarization=False: "dummy transcription")
    result = runner.invoke(cli, ['media', str(dummy_audio), '--api_key', 'dummy_key'])
    assert result.exit_code == 0
    assert "dummy transcription" in result.output.lower()
