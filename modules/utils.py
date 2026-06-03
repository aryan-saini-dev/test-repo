"""
Utility Module for the AI-Powered Student Query Assistant.

Handles validation of query inputs and JSON-based conversation logging.
"""

import os
import json
import re
from datetime import datetime
from typing import List, Dict, Tuple, Any
from modules.logger import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_FILE = os.path.join(DATA_DIR, "conversation_logs.json")
SAMPLE_LOGS_FILE = os.path.join(BASE_DIR, "test_data", "sample_conversation_logs.json")

def _ensure_logs_file() -> None:
    """Ensures log file exists, seeding from test_data if empty."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(LOGS_FILE):
        if os.path.exists(SAMPLE_LOGS_FILE):
            try:
                with open(SAMPLE_LOGS_FILE, 'r') as sf:
                    data = json.load(sf)
                with open(LOGS_FILE, 'w') as lf:
                    json.dump(data, lf, indent=2)
                logger.info(f"Seeded conversation logs from {SAMPLE_LOGS_FILE}")
            except Exception as e:
                logger.error(f"Failed to seed conversation logs: {e}")
                with open(LOGS_FILE, 'w') as lf:
                    json.dump([], lf)
        else:
            with open(LOGS_FILE, 'w') as lf:
                json.dump([], lf)

def validate_query(query: str) -> Tuple[bool, str]:
    """
    Validates a student query to prevent empty, special-character-only,
    or digit/timestamp-only (e.g. '00:00') submissions.
    
    Returns:
        (is_valid, error_message)
    """
    if not query or not query.strip():
        return False, "Your question cannot be empty! Please type or speak something."
        
    query_clean = query.strip()
    
    # Check if the query is just a timestamp or duration placeholder (like 00:00)
    if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', query_clean):
        return False, "We detected silence or a timestamp format. Please speak clearly into the microphone."
    
    # Remove all symbols, punctuation, and whitespaces
    clean = re.sub(r'[^\w\s]', '', query_clean).strip()
    if not clean:
        return False, "Your question cannot contain only special characters! Please ask a real question."
        
    # Check if it has any alphabetic characters (at least one letter)
    # This prevents purely numeric / placeholder queries
    if not any(c.isalpha() for c in clean):
        return False, "Your question must contain at least some letters or words! Please ask a real academic question."
        
    return True, ""

def log_conversation(username: str, track: str, query: str, response: str) -> bool:
    """
    Appends a new conversation entry to the JSON logs.
    """
    _ensure_logs_file()
    try:
        with open(LOGS_FILE, 'r') as f:
            logs = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read conversation logs before writing: {e}")
        logs = []

    new_log = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "username": username.strip().lower(),
        "track": track,
        "user": query.strip(),
        "assistant": response.strip()
    }
    logs.append(new_log)

    try:
        with open(LOGS_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
        logger.info(f"Logged conversation details for '{username}' to JSON logs.")
        return True
    except Exception as e:
        logger.error(f"Failed to save log entry: {e}")
        return False

def get_conversation_history(username: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves logged conversations for a specific user, sorted from newest to oldest.
    """
    _ensure_logs_file()
    username_clean = username.strip().lower()
    try:
        with open(LOGS_FILE, 'r') as f:
            logs = json.load(f)
        
        user_logs = [log for log in logs if log.get("username") == username_clean]
        
        # Sort descending by timestamp
        user_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return user_logs[:limit]
    except Exception as e:
        logger.error(f"Failed to retrieve conversation logs: {e}")
        return []

def clear_conversation_history(username: str) -> bool:
    """
    Clears all logged conversations for a specific user while preserving others.
    """
    _ensure_logs_file()
    username_clean = username.strip().lower()
    try:
        with open(LOGS_FILE, 'r') as f:
            logs = json.load(f)
            
        filtered_logs = [log for log in logs if log.get("username") != username_clean]
        
        with open(LOGS_FILE, 'w') as f:
            json.dump(filtered_logs, f, indent=2)
        logger.info(f"Cleared conversation logs for user '{username}'.")
        return True
    except Exception as e:
        logger.error(f"Failed to clear conversation history for user '{username}': {e}")
        return False
