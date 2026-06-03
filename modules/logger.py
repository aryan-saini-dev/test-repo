"""
Logging Module for the AI-Powered Student Query Assistant.

Configures file-based rotating logging in the root logs/ directory.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

# Define the log directory at root level
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Ensure the logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Set up logging configuration
logger = logging.getLogger("StudentQueryAssistant")
logger.setLevel(logging.INFO)

# Avoid adding handlers multiple times if the module is re-imported
if not logger.handlers:
    # Use RotatingFileHandler to prevent the log file from growing infinitely
    # Max size: 5MB, keeps up to 5 backup log files
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    
    # Standard format for logs
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    
    # Console handler for terminal output during debugging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

logger.info("Logging module initialized successfully.")
