"""
Centralized error handling utilities to reduce code duplication.
"""
import sys
import logging
from functools import wraps
from typing import Callable, Any
import openai
from src.transcription.exceptions import MeetingMinutesError
from src.slack.exceptions import SlackAPIError, SlackRateLimitError

logger = logging.getLogger(__name__)


def handle_common_cli_errors(func: Callable) -> Callable:
    """
    Decorator to handle common CLI errors with consistent error reporting.
    
    Args:
        func: Function to wrap with error handling
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except MeetingMinutesError as e:
            logger.error(f"Meeting processing error: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info("Process interrupted by user.")
            sys.exit(0)
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI Authentication Error: {e}")
            sys.exit(1)
        except openai.APIError as e:
            logger.error(f"OpenAI API Error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)
    return wrapper


def handle_slack_errors(func: Callable) -> Callable:
    """
    Decorator to handle Slack-specific errors.
    
    Args:
        func: Function to wrap with Slack error handling
        
    Returns:
        Wrapped function with Slack error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except SlackRateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            if hasattr(e, 'retry_after') and e.retry_after:
                logger.info(f"Waiting {e.retry_after} seconds before retrying...")
                import time
                time.sleep(e.retry_after)
                # Retry once
                try:
                    return func(*args, **kwargs)
                except Exception as retry_e:
                    logger.error(f"Retry failed: {retry_e}")
                    sys.exit(1)
            sys.exit(1)
        except SlackAPIError as e:
            error_str = str(e)
            if "invalid_auth" in error_str:
                logger.error("Slack authentication error. Please verify your token.")
            elif "not_in_channel" in error_str:
                logger.error("Cannot access channel. Bot is not a member.")
            else:
                logger.error(f"Slack API error: {e}")
            sys.exit(1)
    return wrapper


class ErrorContext:
    """Context manager for handling errors with additional context."""
    
    def __init__(self, operation_name: str, log_traceback: bool = False):
        """
        Initialize error context.
        
        Args:
            operation_name: Name of the operation for error reporting
            log_traceback: Whether to log full traceback on errors
        """
        self.operation_name = operation_name
        self.log_traceback = log_traceback
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.log_traceback:
                import traceback
                logger.error(f"Error in {self.operation_name}: {traceback.format_exc()}")
            else:
                logger.error(f"Error in {self.operation_name}: {exc_val}")
            return False  # Re-raise the exception