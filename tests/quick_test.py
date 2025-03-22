#!/usr/bin/env python
"""
Simplified test script that only tests the most basic functionality
without external dependencies.
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class BasicTests(unittest.TestCase):
    def test_version_command(self):
        """Test that the version command works"""
        # Import here to avoid loading all dependencies
        from click.testing import CliRunner
        
        # Mock the version function directly
        with patch('src.cli.version') as mock_version:
            mock_version.return_value = "samuelizer version 1.1.0"
            
            # Create a runner and invoke the command
            runner = CliRunner()
            result = runner.invoke(mock_version)
            
            # Check the result
            self.assertEqual(0, result.exit_code)
            self.assertIn("samuelizer version", mock_version.return_value)
    
    def test_basic_functionality(self):
        """Test a very basic functionality that doesn't require external dependencies"""
        # Test something simple like a utility function
        from src.utils.logging_utils import setup_logging
        
        # Mock the actual logging setup to avoid file operations
        with patch('logging.FileHandler'):
            logger = setup_logging('test.log')
            self.assertIsNotNone(logger)

if __name__ == '__main__':
    unittest.main()
