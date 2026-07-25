import os
import logging
from datetime import datetime
from rich.logging import RichHandler

# A custom log formatter for files
FILE_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - [%(filename)s:%(lineno)d] - %(message)s"

def setup_logger(name: str = "SuryaNet", log_dir: str = "data_pipeline/logs") -> logging.Logger:
    """Sets up a logger with Rich console handler and daily log file rotation."""
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if logger is already initialized
    if not logger.handlers:
        # 1. Rich Console Handler
        console_handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=True
        )
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        
        # 2. Daily Log File Handler
        today_str = datetime.today().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"{today_str}.log")
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(FILE_FORMAT)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

# Module-level default logger
logger = setup_logger()
