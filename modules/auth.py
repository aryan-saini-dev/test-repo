"""
Authentication Module for the AI-Powered Student Query Assistant.

Handles local user profiles in JSON format, utilizing PBKDF2 hashing.
"""

import os
import json
import hashlib
import secrets
from datetime import datetime
from typing import Dict, Tuple, Any
from modules.logger import logger

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
SAMPLE_USERS_FILE = os.path.join(BASE_DIR, "test_data", "sample_users.json")

def hash_password(password: str, salt: bytes = None) -> Tuple[str, str]:
    """
    Hashes a password using PBKDF2 HMAC SHA-256.
    If salt is not provided, a random 16-byte salt is generated.
    Returns (hex_hash, hex_salt).
    """
    if salt is None:
        salt = secrets.token_bytes(16)
    
    iterations = 100000
    pwd_bytes = password.encode('utf-8')
    dk = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt, iterations)
    return dk.hex(), salt.hex()

def _ensure_data_files() -> None:
    """Ensures data directory and users file exist, seeding if needed."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        if os.path.exists(SAMPLE_USERS_FILE):
            try:
                with open(SAMPLE_USERS_FILE, 'r') as sf:
                    data = json.load(sf)
                with open(USERS_FILE, 'w') as uf:
                    json.dump(data, uf, indent=2)
                logger.info(f"Seeded users database from {SAMPLE_USERS_FILE}")
            except Exception as e:
                logger.error(f"Failed to seed users file: {e}")
                # Create empty file
                with open(USERS_FILE, 'w') as uf:
                    json.dump({}, uf)
        else:
            with open(USERS_FILE, 'w') as uf:
                json.dump({}, uf)

def load_users() -> Dict[str, Dict[str, Any]]:
    """Loads all users from data/users.json."""
    _ensure_data_files()
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Corrupted users JSON: {e}")
        return {}
    except Exception as e:
        logger.error(f"Failed to load users: {e}")
        return {}

def save_users(users: Dict[str, Dict[str, Any]]) -> bool:
    """Saves the user registry to data/users.json."""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save users: {e}")
        return False

def register_user(username: str, password: str) -> bool:
    """
    Registers a new student user profile.
    Returns True if successful, False if username exists or registration fails.
    """
    username = username.strip().lower()
    if not username or not password:
        logger.warning("Registration failed: empty username or password.")
        return False
        
    users = load_users()
    if username in users:
        logger.warning(f"Registration failed: username '{username}' already exists.")
        return False
        
    password_hash, salt = hash_password(password)
    users[username] = {
        "password_hash": password_hash,
        "salt": salt,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if save_users(users):
        logger.info(f"User '{username}' registered successfully.")
        return True
    return False

def verify_user(username: str, password: str) -> bool:
    """
    Verifies user login credentials.
    Returns True if valid, False otherwise.
    """
    username = username.strip().lower()
    if not username or not password:
        return False
        
    users = load_users()
    user_info = users.get(username)
    if not user_info:
        logger.warning(f"Login failed: user '{username}' not found.")
        return False
        
    stored_hash = user_info.get("password_hash")
    stored_salt_hex = user_info.get("salt")
    if not stored_hash or not stored_salt_hex:
        logger.error(f"User database record for '{username}' is corrupted.")
        return False
        
    salt = bytes.fromhex(stored_salt_hex)
    computed_hash, _ = hash_password(password, salt)
    
    if secrets.compare_digest(stored_hash, computed_hash):
        logger.info(f"User '{username}' verified successfully.")
        return True
    
    logger.warning(f"Login failed: incorrect password for user '{username}'.")
    return False
