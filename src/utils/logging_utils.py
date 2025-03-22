import logging
import os

def setup_logging(log_file_name):
    """
    Set up logging with proper file handler management
    
    Args:
        log_file_name: Name of the log file
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
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
    
    return logger
