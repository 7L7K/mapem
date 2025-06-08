# backend/utils/logger.py
import logging
import sys 
import os

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

def _add_color(level, text):
    colors = {
        "DEBUG": "\033[90m",   # Grey
        "INFO":  "\033[37m",   # White
        "WARNING": "\033[33m", # Yellow
        "ERROR": "\033[31m",   # Red
        "CRITICAL": "\033[41m" # Red background
    }
    reset = "\033[0m"
    return f"{colors.get(level, '')}{text}{reset}"

class ColorFormatter(logging.Formatter):
    def format(self, record):
        levelname = record.levelname
        record.levelname = _add_color(levelname, levelname)
        return super().format(record)


def configure_logging(level: int = logging.DEBUG) -> None:
    """Configure the root logger once."""
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter(_LOG_FORMAT))
    root.addHandler(handler)


def get_logger(name: str = "mapem", level: int = logging.DEBUG) -> logging.Logger:
    """Return a logger that uses the central configuration."""
    configure_logging(level)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


def get_file_logger(module_name: str):
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    file_path = os.path.join(log_dir, f"{module_name}.log")
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)
    # Prevent duplicate handlers
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == file_path for h in logger.handlers):
        fh = logging.FileHandler(file_path, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger
