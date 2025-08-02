"""
Text analysis service.
Extracted from cli.py to improve maintainability and reduce complexity.
"""
import logging
from typing import Dict, Any

from src.config.command_configs import TextAnalysisConfig
from src.config.provider_manager import ProviderConfigurationManager
from src.utils.error_handlers import ErrorContext
from src.transcription.meeting_analyzer import MeetingAnalyzer
from src.transcription.meeting_minutes import DocumentManager

logger = logging.getLogger(__name__)


class TextAnalysisService:
    """Service for handling text analysis operations."""
    
    def __init__(self, config: TextAnalysisConfig):
        """
        Initialize the text analysis service.
        
        Args:
            config: Configuration for text analysis
        """
        self.config = config
        self.provider_manager = ProviderConfigurationManager()
    
    def analyze_text(self, provider_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze text using the specified configuration.
        
        Args:
            provider_config: Provider configuration from ProviderConfigurationManager
            
        Returns:
            Dict containing analysis results
        """
        with ErrorContext("text analysis"):
            # Parse template parameters
            template_params = self.config.get_template_params()
            
            # Create analysis client
            analysis_client = self.provider_manager.create_analysis_client(
                provider_config['provider'],
                provider_config['api_key'],
                provider_config['model_id']
            )
            
            # Create analyzer
            analyzer = MeetingAnalyzer(
                transcription=self.config.text,
                analysis_client=analysis_client
            )
            
            # Perform analysis
            results = self._perform_analysis(analyzer, template_params)
            
            # Save results if requested
            if self.config.output:
                DocumentManager.save_to_docx(results, str(self.config.output))
                logger.info(f"Document saved: {self.config.output}")
            
            return results
    
    def _perform_analysis(self, analyzer: MeetingAnalyzer, template_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform the actual text analysis based on template configuration.
        
        Args:
            analyzer: MeetingAnalyzer instance
            template_params: Additional parameters for template processing
            
        Returns:
            Dict containing analysis results
        """
        if self.config.template == 'all':
            return {
                'abstract_summary': analyzer.summarize(**template_params),
                'key_points': analyzer.extract_key_points(**template_params),
                'action_items': analyzer.extract_action_items(**template_params),
                'sentiment': analyzer.analyze_sentiment(**template_params)
            }
        else:
            result = analyzer.analyze(self.config.template, **template_params)
            return {self.config.template: result}