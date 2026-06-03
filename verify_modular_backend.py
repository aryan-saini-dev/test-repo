"""
Verification script to test the modular backend components of the AI Student Query Assistant.

Tests database-free JSON authentication, caching, query validation, and conversation logging.
"""

import os
import sys
import shutil

# Ensure active directory is on path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.logger import logger
import modules.auth as auth
import modules.cache as cache
import modules.utils as utils
import modules.chatbot as chatbot

def run_tests():
    logger.info("Starting verification tests for modular JSON-based backend modules...")
    print("=== Verification Starting ===")
    
    # Setup test environment directories
    # Backup existing files if they exist to prevent losing developer's real files
    backup_users = False
    backup_logs = False
    
    if os.path.exists(auth.USERS_FILE):
        shutil.copy2(auth.USERS_FILE, auth.USERS_FILE + ".bak")
        backup_users = True
    if os.path.exists(utils.LOGS_FILE):
        shutil.copy2(utils.LOGS_FILE, utils.LOGS_FILE + ".bak")
        backup_logs = True

    try:
        # Clean slate for testing
        os.makedirs(auth.DATA_DIR, exist_ok=True)
        with open(auth.USERS_FILE, 'w') as f:
            f.write("{}")
        with open(utils.LOGS_FILE, 'w') as f:
            f.write("[]")

        # 1. Test Hashed Password Authentication
        print("1. Testing User Authentication (Signup & Login)...")
        test_user = "test_student"
        test_pass = "securepassword123"
        
        # Test signup
        signup_ok = auth.register_user(test_user, test_pass)
        assert signup_ok is True, "Failed to register test user"
        
        # Test duplicate signup
        dup_signup = auth.register_user(test_user, "anotherpassword")
        assert dup_signup is False, "Duplicate user signup should fail"
        
        # Test login success
        login_ok = auth.verify_user(test_user, test_pass)
        assert login_ok is True, "Verify user failed with correct password"
        
        # Test login failure
        bad_login = auth.verify_user(test_user, "wrongpassword")
        assert bad_login is False, "Verify user succeeded with incorrect password"
        
        # Test non-existent user login
        no_user_login = auth.verify_user("nonexistent_user", "password")
        assert no_user_login is False, "Login should fail for non-existent user"
        print("   [PASSED] User registration and authentication verified.")

        # 2. Test Input Query Validation
        print("2. Testing Input Query Validation...")
        valid, msg = utils.validate_query("How do I learn Machine Learning?")
        assert valid is True, f"Valid query marked invalid: {msg}"
        
        empty, msg = utils.validate_query("")
        assert empty is False, "Empty query should be invalid"
        
        spaces, msg = utils.validate_query("    ")
        assert spaces is False, "Spaces-only query should be invalid"
        
        special, msg = utils.validate_query("???!!!@@#$")
        assert special is False, "Special-character-only query should be invalid"
        
        timestamp, msg = utils.validate_query("00:00")
        assert timestamp is False, "Timestamp-only query should be invalid"
        
        numeric, msg = utils.validate_query("12345")
        assert numeric is False, "Numeric-only query should be invalid"
        
        print("   [PASSED] Query validation rules verified.")

        # 3. Test Conversation Logs
        print("3. Testing JSON Conversation Logs...")
        test_query = "Explain Python decorators."
        test_track = "Programming"
        test_response = "A decorator is a function..."
        
        log_ok = utils.log_conversation(
            username=test_user,
            track=test_track,
            query=test_query,
            response=test_response
        )
        assert log_ok is True, "Failed to log conversation details to JSON"
        
        history = utils.get_conversation_history(test_user, limit=5)
        assert len(history) >= 1, "Log history should return at least 1 record"
        assert history[0]["user"] == test_query, "Log record query did not match input query"
        assert history[0]["assistant"] == test_response, "Log record response did not match input response"
        assert history[0]["username"] == test_user.lower(), "Log record username did not match"
        
        # Test clearing history
        clear_ok = utils.clear_conversation_history(test_user)
        assert clear_ok is True, "Failed to clear conversation history"
        history_cleared = utils.get_conversation_history(test_user, limit=5)
        assert len(history_cleared) == 0, "Log history should be empty after clearing"
        print("   [PASSED] Conversation logging to JSON verified.")

        # 4. Test Caching (LRU Cache)
        print("4. Testing Memory Response Caching (lru_cache)...")
        cache.clear_response_cache()
        
        # Test offline query generation - should match mock response in sample_responses.json
        q = "explain python decorators."
        res, is_hit = cache.get_cached_response(
            query=q,
            track=test_track,
            chat_history=[],
            gemini_key=None,
            openai_key=None,
            bypass_cache=False
        )
        assert "decorator" in res.lower(), "Should return mock response for decorators"
        assert is_hit is False, "First query should be a cache miss"
        
        # Second call - should be a hit
        res2, is_hit2 = cache.get_cached_response(
            query=q,
            track=test_track,
            chat_history=[],
            gemini_key=None,
            openai_key=None,
            bypass_cache=False
        )
        assert res2 == res, "Second query response should match first"
        assert is_hit2 is True, "Second query should be a cache hit"
        
        # Bypass cache call
        res3, is_hit3 = cache.get_cached_response(
            query=q,
            track=test_track,
            chat_history=[],
            gemini_key=None,
            openai_key=None,
            bypass_cache=True
        )
        assert is_hit3 is False, "Bypass cache call should report miss"
        
        # After clear cache call
        cache.clear_response_cache()
        res4, is_hit4 = cache.get_cached_response(
            query=q,
            track=test_track,
            chat_history=[],
            gemini_key=None,
            openai_key=None,
            bypass_cache=False
        )
        assert is_hit4 is False, "Call after cache wipe should be a miss"
        print("   [PASSED] Memory-based response caching verified.")

        # 5. Test Chatbot Fallback / Mock Offline Mode
        print("5. Testing Offline Mock Fallback...")
        # Query that is not in mock responses
        unknown_q = "What is the capital of France?"
        unknown_res = chatbot.generate_response(
            query=unknown_q,
            track="Programming",
            chat_history=[],
            gemini_key=None,
            openai_key=None
        )
        assert "API Keys Missing" in unknown_res, "Should warn about missing keys for unknown queries"
        print("   [PASSED] Chatbot offline fallback verified.")
        
        # 6. Test Voice Transcription Format Checks
        print("6. Testing Voice Transcription and Format Handling...")
        import modules.voice as voice
        
        # Test empty audio bytes
        try:
            voice.transcribe_audio_bytes(b"")
            assert False, "Empty audio bytes should raise ValueError"
        except ValueError as ve:
            assert "empty" in str(ve).lower()
            
        # Test WebM/OGG format with no API keys (should raise RuntimeError with user advice)
        try:
            fake_webm_bytes = b"fake webm header and metadata content"
            voice.transcribe_audio_bytes(fake_webm_bytes, mime_type="audio/webm", gemini_key=None, openai_key=None)
            assert False, "Local recognition on fake WebM should fail"
        except RuntimeError as re:
            assert "recorded audio in a format" in str(re), f"Expected format warning, got: {re}"
            
        print("   [PASSED] Voice transcription format handling verified.")
        
        print("\n=== All Tests Passed Successfully! ===")
        logger.info("Verification tests completed. All modules verified.")

    finally:
        # Restore backups if they were created to preserve original state
        if backup_users:
            shutil.copy2(auth.USERS_FILE + ".bak", auth.USERS_FILE)
            os.remove(auth.USERS_FILE + ".bak")
        else:
            if os.path.exists(auth.USERS_FILE):
                os.remove(auth.USERS_FILE)
                
        if backup_logs:
            shutil.copy2(utils.LOGS_FILE + ".bak", utils.LOGS_FILE)
            os.remove(utils.LOGS_FILE + ".bak")
        else:
            if os.path.exists(utils.LOGS_FILE):
                os.remove(utils.LOGS_FILE)

if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as e:
        print(f"\n❌ [FAILED] Assertion Error: {e}")
        logger.error(f"Backend verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ [FAILED] Unexpected Error: {e}")
        logger.error(f"Backend verification encountered an unexpected error: {e}")
        sys.exit(1)
