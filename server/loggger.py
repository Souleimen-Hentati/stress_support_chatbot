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
   
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] --- [%(message)s]")
    ch.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(ch)

    return logger


logger = setup_logger("PFA_Medical_Assistant")
