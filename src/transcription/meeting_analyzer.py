from docx import Document
import openai
import logging
import os
from src.transcription.exceptions import AnalysisError
from src.interfaces import TranscriptionService
from .templates import PromptTemplates

logger = logging.getLogger(__name__)

from src.transcription.text_preprocessor import TextPreprocessor

class OpenAIAnalysisClient:
    """
    OpenAI implementation of an analysis client.
    """
    def __init__(self, client=None):
        self.client = client or openai

    def analyze(self, messages, model="gpt-4-1106-preview", temperature=0):
        response = self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=messages
        )
        return response.choices[0].message.content

class TemplateSelector:
    """
    Selects the appropriate template for analysis.
    """
    def __init__(self, prompt_templates, analysis_client):
        self.prompt_templates = prompt_templates
        self.analysis_client = analysis_client

    def select_template(self, text, **kwargs):
        template = self.prompt_templates.get_template("auto")
        try:
            messages = [
                {"role": "system", "content": template["system"]},
                {"role": "user", "content": template["template"].format(text=text)}
            ]
            analysis = self.analysis_client.analyze(messages)
            first_line = analysis.split('\n')[0].strip()
            recommended_template = first_line.split(':')[-1].strip().lower().replace('**', '').replace('*', '')
            logger.info(f"Auto-selected template: {recommended_template}")
            logger.info(f"Selection reasoning: {analysis}")
            return self.prompt_templates.get_template(recommended_template, **kwargs)
        except Exception as e:
            logger.warning(f"Error in auto-template selection: {e}. Falling back to 'summary' template.")
            return self.prompt_templates.get_template("summary", **kwargs)

class MeetingAnalyzer:
    """
    Analyzes meeting transcriptions.
    """
    def __init__(self, transcription: str, analysis_client=None, prompt_templates=None):
        self.text_preprocessor = TextPreprocessor()
        self.transcription = self.text_preprocessor.prepare_text(transcription)
        self.analysis_client = analysis_client or OpenAIAnalysisClient()
        self.prompt_templates = prompt_templates or PromptTemplates()
        self.template_selector = TemplateSelector(self.prompt_templates, self.analysis_client)

    def analyze(self, template_name: str = "auto", **kwargs) -> str:
        try:
            if template_name == "auto":
                template = self.template_selector.select_template(self.transcription, **kwargs)
            else:
                template = self.prompt_templates.get_template(template_name, **kwargs)
            messages = [
                {"role": "system", "content": template["system"]},
                {"role": "user", "content": template["template"].format(text=self.transcription)}
            ]
            return self.analysis_client.analyze(messages)
        except openai.AuthenticationError as e:
            logger.error(f"Error with template '{template_name}': {e}")
            raise AnalysisError(f"Authentication failed: {e}") from e
        except openai.APIError as e:
            logger.error(f"API Error: {e}")
            raise AnalysisError(f"API Error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during analysis: {e}")
            raise AnalysisError(f"Unexpected error: {e}") from e

    def summarize(self, **kwargs):
        return self.analyze("summary", **kwargs)

    def extract_key_points(self, **kwargs):
        return self.analyze("key_points", **kwargs)

    def extract_action_items(self, **kwargs):
        return self.analyze("action_items", **kwargs)

    def analyze_sentiment(self, **kwargs):
        return self.analyze("sentiment", **kwargs)

class DocumentManager:
    """
    Manages document creation and saving.
    """
    @staticmethod
    def create_document(content):
        doc = Document()
        for key, value in content.items():
            heading = key.replace('_', ' ').title()
            doc.add_heading(heading, level=1)
            doc.add_paragraph(value)
            doc.add_paragraph()
        return doc

    @staticmethod
    def save_to_docx(content, filename):
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        doc = DocumentManager.create_document(content)
        doc.save(filename)
        return filename
