"""
Logging configuration for B2 Sync Local application
"""

import logging
import logging.handlers
from pathlib import Path
import appdirs

def setup_logger(name: str = None, level: str = "INFO") -> logging.Logger:
    """Setup application logger with file and console handlers"""
    
    # Get logger
    logger_name = name or "b2sync"
    logger = logging.getLogger(logger_name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create logs directory
    app_name = "B2SyncLocal"
    app_author = "B2Sync"
    log_dir = Path(appdirs.user_log_dir(app_name, app_author))
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # File handler with rotation
    log_file = log_dir / "b2sync.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """Get existing logger or create new one"""
    logger_name = name or "b2sync"
    return logging.getLogger(logger_name)