import logging
import os
from datetime import datetime
from rich.logging import RichHandler

def setup_logger(log_dir="data_pipeline/logs"):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_filename = datetime.now().strftime("%Y-%m-%d.log")
    log_path = os.path.join(log_dir, log_filename)

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(rich_tracebacks=True),
            logging.FileHandler(log_path)
        ]
    )
    return logging.getLogger("suryanet_pipeline")

def log_journal(operation, status, details="", journal_path="data_pipeline/logs/journal.log"):
    """Write-Ahead Log (WAL) for crash recovery."""
    timestamp = datetime.now().isoformat()
    entry = f"{timestamp} | {operation} | {status} | {details}\n"
    with open(journal_path, "a") as f:
        f.write(entry)

logger = setup_logger()
