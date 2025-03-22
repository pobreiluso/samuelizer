import logging
import os
import atexit
import weakref

# Dictionary to keep track of loggers and their handlers
_loggers = {}

def setup_logging(log_file_name):
    """
    Set up logging with proper file handler management
    
    Args:
        log_file_name: Name of the log file
        
    Returns:
        logging.Logger: Configured logger
    """
    # Check if we already have a logger for this file
    if log_file_name in _loggers:
        return _loggers[log_file_name]
    
    # Create logger with a unique name based on the file path
    logger_name = f"logger_{os.path.basename(log_file_name)}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
    
    # Add stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(stream_handler)
    
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file_name)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Add file handler
    file_handler = logging.FileHandler(log_file_name)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    # Store weak references to handlers for cleanup
    handlers = weakref.WeakSet([stream_handler, file_handler])
    
    # Register cleanup function
    def cleanup():
        for handler in handlers:
            try:
                handler.close()
                logger.removeHandler(handler)
            except:
                pass
    
    atexit.register(cleanup)
    
    # Store the logger in our dictionary
    _loggers[log_file_name] = logger
    
    # Also set the root logger level to avoid duplicate messages
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(logging.INFO)
    
    return logger
