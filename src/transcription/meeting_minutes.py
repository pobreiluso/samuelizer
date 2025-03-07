import os
import requests
import sys
from docx import Document
from src.utils.audio_extractor import AudioExtractor
import openai
import webbrowser
import logging
from tqdm import tqdm
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
            file_size = os.path.getsize(audio_file_path) / (1024 * 1024)  # Tamaño en MB
            logger.info(f"Processing audio file of {file_size:.2f} MB")
            
            with tqdm(total=100, desc="Transcribing audio", unit="%", colour='green') as pbar:
                # Update progress: Preparation
                pbar.update(10)
                logger.info("Preparing file for transcription...")
                
                # Update progress: Opening file
                with open(audio_file_path, 'rb') as audio_file:
                    pbar.update(20)
                    logger.info("Sending file to OpenAI...")
                    
                    # Update progress: Sending to OpenAI
                    pbar.update(20)
                    
                    # Perform transcription
                    transcription = openai.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        response_format="text"
                    )
                    
                    # Update progress: Transcription completed
                    pbar.update(40)
                    logger.info("Transcription completed successfully")
                    
                    # Show result information
                    if transcription:
                        char_count = len(transcription)
                        word_count = len(transcription.split())
                        logger.info(f"Transcription generated: {word_count} words, {char_count} characters")
                    
            return transcription
        except openai.AuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            raise TranscriptionError(f"Authentication failed: {e}") from e
        except openai.APIError as e:
            logger.error(f"API Error: {e}")
            raise TranscriptionError(f"API Error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during transcription: {e}")
            raise TranscriptionError(f"Unexpected error during transcription: {e}") from e


from .templates import PromptTemplates

class MeetingAnalyzer:
    def __init__(self, transcription: str):
        # Split long transcriptions into manageable chunks
        self.max_chunk_size = 4000  # OpenAI's token limit consideration
        self.transcription = self._prepare_transcription(transcription)
        self.prompt_templates = PromptTemplates()
        
    def _prepare_transcription(self, text: str) -> str:
        """Prepare transcription for analysis by cleaning and chunking if needed"""
        if len(text) > self.max_chunk_size:
            # Split into semantic chunks (at paragraph or sentence boundaries)
            chunks = [text[i:i+self.max_chunk_size] for i in range(0, len(text), self.max_chunk_size)]
            return "\n\n".join(chunks)
        return text

    def analyze(self, template_name: str = "auto", **kwargs) -> str:
        """
        Analyze text using a specific template or auto-select the best template.
        
        Args:
            template_name (str): Name of the template to use, defaults to "auto"
            **kwargs: Additional parameters to customize the template
            
        Returns:
            str: Analysis result based on the template
            
        Raises:
            AnalysisError: If analysis fails
            ValueError: If template doesn't exist
        """
        if template_name == "auto":
            # First, analyze the content to determine the best template
            template = self.prompt_templates.get_template("auto")
            try:
                response = openai.chat.completions.create(
                    model="gpt-4-1106-preview",
                    temperature=0,
                    messages=[
                        {"role": "system", "content": template["system"]},
                        {"role": "user", "content": template["template"].format(text=self.transcription)}
                    ]
                )
                
                # Parse the response to get the recommended template
                analysis = response.choices[0].message.content
                # Extract template name from the first line, removing any markdown or extra text
                first_line = analysis.split('\n')[0].strip()
                recommended_template = first_line.split(':')[-1].strip().lower()
                recommended_template = recommended_template.replace('**', '').replace('*', '')
                
                # Log the template selection reasoning
                logger.info(f"Auto-selected template: {recommended_template}")
                logger.info(f"Selection reasoning: {analysis}")
                
                # Get and use the recommended template
                template = self.prompt_templates.get_template(recommended_template, **kwargs)
            except Exception as e:
                logger.warning(f"Error in auto-template selection: {e}. Falling back to 'summary' template.")
                template = self.prompt_templates.get_template("summary", **kwargs)
        else:
            template = self.prompt_templates.get_template(template_name, **kwargs)
            
        messages = [
            {"role": "system", "content": template["system"]},
            {"role": "user", "content": template["template"].format(text=self.transcription)}
        ]

        try:
            response = openai.chat.completions.create(
                model="gpt-4-1106-preview",
                temperature=0,
                messages=messages
            )
            return response.choices[0].message.content
        except openai.AuthenticationError as e:
            logger.error(f"Error en el análisis con template '{template_name}': {e}")
            raise AnalysisError(f"Authentication failed: {e}") from e
        except openai.APIError as e:
            logger.error(f"OpenAI API Error: {e}")
            raise AnalysisError(f"API Error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during analysis: {e}")
            raise AnalysisError(f"Unexpected error during analysis: {e}") from e

    def summarize(self, **kwargs):
        return self.analyze("summary", **kwargs)

    def extract_key_points(self, **kwargs):
        return self.analyze("key_points", **kwargs)

    def extract_action_items(self, **kwargs):
        return self.analyze("action_items", **kwargs)

    def analyze_sentiment(self, **kwargs):
        return self.analyze("sentiment", **kwargs)


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
