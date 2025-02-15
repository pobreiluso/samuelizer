import os
import requests
import sys
from docx import Document
from src.utils.audio_extractor import AudioExtractor
import openai
import webbrowser
import logging
from src.transcription.exceptions import (
    TranscriptionError,
    AnalysisError,
    DownloadError,
    AudioExtractionError,
    MeetingMinutesError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('meeting_minutes.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class AudioTranscriptionService:
    def __init__(self, model="whisper-1"):
        self.model = model

    def transcribe(self, audio_file_path):
        try:
            with open(audio_file_path, 'rb') as audio_file:
                transcription = openai.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file
                )
            return transcription.text
        except openai.error.OpenAIError as e:
            logger.error(f"Transcription failed: {e}")
            raise TranscriptionError(f"Transcription failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during transcription: {e}")
            raise TranscriptionError(f"Unexpected error during transcription: {e}") from e


class MeetingAnalyzer:
    def __init__(self, transcription):
        self.transcription = transcription

    def summarize(self):
        return self._get_openai_response("summarize into a concise abstract paragraph")

    def extract_key_points(self):
        return self._get_openai_response("identify and list the main points")

    def extract_action_items(self):
        return self._get_openai_response("extract action items")

    def analyze_sentiment(self):
        return self._get_openai_response("analyze the sentiment of the following text", message_key='message')

    def _get_openai_response(self, task_description, message_key='message.content'):
        try:
            response = openai.chat.completions.create(
                model="gpt-4-1106-preview",
                temperature=0,
                messages=[
                    {"role": "system", "content": f"You are an AI {task_description}."},
                    {"role": "user", "content": self.transcription}
                ]
            )
            return response.choices[0].message.content
        except openai.error.OpenAIError as e:
            logger.error(f"Analysis failed: {e}")
            raise AnalysisError(f"Analysis failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during analysis: {e}")
            raise AnalysisError(f"Unexpected error during analysis: {e}") from e


class DocumentManager:
    @staticmethod
    def save_to_docx(content, filename):
        doc = Document()
        for key, value in content.items():
            heading = key.replace('_', ' ').title()
            doc.add_heading(heading, level=1)
            doc.add_paragraph(value)
            doc.add_paragraph()
        doc.save(filename)


class VideoDownloader:
    @staticmethod
    def download_from_google_drive(drive_url):
        file_id = drive_url.split('/')[-2]
        direct_download_url = f'https://drive.google.com/uc?id={file_id}&export=download'
        local_filename = 'downloaded_video.mp4'
        with requests.get(direct_download_url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename




def login_with_google():
    webbrowser.open('https://accounts.google.com/o/oauth2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&scope=https://www.googleapis.com/auth/drive.readonly&response_type=code', new=2)


def main(api_key, file_path):
    try:
        logger.info("Beginning video transcription process...")

        # login_with_google()
        audio_file = AudioExtractor.extract_audio(file_path)
        logger.info("Audio extracted, starting transcription...")

        transcription_text = AudioTranscriptionService().transcribe(audio_file)
        logger.info("Transcription completed.")

        logger.info("Analyzing transcription...")
        analyzer = MeetingAnalyzer(transcription_text)
        meeting_info = {
            'abstract_summary': analyzer.summarize(),
            'key_points': analyzer.extract_key_points(),
            'action_items': analyzer.extract_action_items(),
            'sentiment': analyzer.analyze_sentiment()
        }
        logger.info("Analysis completed.")

        logger.info("Saving analyzed information to document...")
        DocumentManager.save_to_docx(meeting_info, 'meeting_minutes.docx')
        logger.info("Document saved: meeting_minutes.docx")

        logger.info("\nMeeting Information:")
        for section, content in meeting_info.items():
            logger.info(f"{section.title().replace('_', ' ')}:\n{content}\n")

    except MeetingMinutesError as e:
        logger.error(f"MeetingMinutesError occurred: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        logger.error("Usage: python transcribe_video.py api_key file_path")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
