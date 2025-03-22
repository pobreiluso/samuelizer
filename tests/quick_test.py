#!/usr/bin/env python
"""
Simplified test script that only tests the most basic functionality
without external dependencies.
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class BasicTests(unittest.TestCase):
    def test_version_command(self):
        """Test that the version command works"""
        from src.cli import version
        from click.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(version)
        
        self.assertEqual(0, result.exit_code)
        self.assertIn("samuelizer version", result.output)
    
    def test_basic_text_analysis(self):
        """Test basic text analysis with mocks"""
        from src.transcription.meeting_analyzer import AnalysisClient
        
        # Create a mock provider
        mock_provider = MagicMock()
        mock_provider.analyze.return_value = "Test analysis"
        
        # Create client with mock provider
        client = AnalysisClient(provider=mock_provider)
        
        # Test analysis
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Analyze this text"}
        ]
        
        # Patch the provider_name to ensure we use our mock
        with patch.object(client, 'provider_name', 'mock'):
            # Use the mock provider
            result = client.analyze(messages)
            
            # Verify the mock provider was used
            self.assertEqual(result, "Test analysis")
            mock_provider.analyze.assert_called_once()

if __name__ == '__main__':
    unittest.main()
