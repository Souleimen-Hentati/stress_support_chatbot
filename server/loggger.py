"""
Logging configuration module.
Sets up a logger for the Medical Assistant application.
Handles logging of debug messages, errors, and important events throughout the app.
"""

import logging

def setup_logger(name: str):
    """
    Creates and configures a logger instance with console output.
    
    Parameters:
    - name: Name identifier for the logger (useful when multiple loggers exist)
    
    Returns:
    - Configured logger instance that can be used for logging
    
    Features:
    1. Sets logging level to DEBUG (catches all messages: debug, info, warning, error, critical)
    2. Streams output to console (StreamHandler)
    3. Formats messages with timestamp, level, and content
    4. Prevents duplicate handlers if called multiple times
    
    Usage:
    - logger.debug("Debug message")
    - logger.info("Info message")
    - logger.warning("Warning message")
    - logger.error("Error message")
    - logger.exception("Error with traceback")
    """
    # CREATE LOGGER INSTANCE
    # Get or create logger with given name
    logger = logging.getLogger(name)
    
    # SET LOGGING LEVEL
    # DEBUG level captures all messages (most verbose)
    logger.setLevel(logging.DEBUG)

    # CREATE CONSOLE HANDLER
    # StreamHandler outputs log messages to console (stdout)
    ch = logging.StreamHandler()
    # Set handler to DEBUG level (same as logger)
    ch.setLevel(logging.DEBUG)

    # CREATE FORMATTER
    # Defines how log messages are formatted
    # Format: [TIMESTAMP] [LEVEL] --- [MESSAGE]
    # Example: [2026-02-17 17:28:07,123] [DEBUG] --- Running chain for input: What is diabetes?
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] --- [%(message)s]")
    # Apply formatter to console handler
    ch.setFormatter(formatter)

    # ADD HANDLER TO LOGGER
    # Prevent duplicate handlers if setup_logger is called multiple times
    if not logger.hasHandlers():
        # Add console handler to logger
        logger.addHandler(ch)

    return logger

# ===========================
# CREATE GLOBAL LOGGER
# ===========================
# Create logger instance that will be imported throughout the application
# When other modules do: from loggger import logger
# They get this configured logger instance
logger = setup_logger("PFA_Medical_Assistant")

# Usage throughout app:
# from loggger import logger
# logger.info("Database connected")
# logger.error("Failed to embed documents")
# logger.exception("Unhandled exception occurred")
