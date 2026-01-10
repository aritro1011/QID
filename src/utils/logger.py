"""
QID - Query Images by Description
Logging Configuration
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logging(log_file: str = None, level: str = "INFO", console: bool = True):
    """Configure application logging."""
    
    # Remove default handler
    logger.remove()
    
    # Console logging
    if console:
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level=level,
            colorize=True
        )
    
    # File logging
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            level=level,
            rotation="10 MB",
            retention="1 week",
            compression="zip"
        )


def get_logger(name: str = None):
    """Get logger instance."""
    return logger