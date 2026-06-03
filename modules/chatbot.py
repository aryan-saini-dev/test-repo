"""
Chatbot Module for the AI-Powered Student Query Assistant.

Handles message generation using Gemini API (preferred) and OpenAI API (fallback).
Provides a fallback to offline mock responses if no API credentials are provided.
"""

import os
import json
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError
from openai import OpenAI
from typing import List, Dict, Any, Optional
from modules.logger import logger

# Configuration and defaults
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048

# Track Prompt Definitions
TRACK_PROMPTS = {
    "Programming": (
        "You are an expert programming tutor. Your goal is to help students learn programming concepts, "
        "understand syntax, debug code, and write efficient, clean, and PEP 8-compliant programs. "
        "When a student shares code with bugs, explain *why* it fails and guide them to the solution instead of "
        "just giving the answer. Always use markdown formatting, syntax highlighting for code blocks, and "
        "provide clear explanations. Keep your tone encouraging and educational."
    ),
    "AI/ML": (
        "You are a Senior AI/ML research scientist and educator. Help the student understand machine learning "
        "algorithms, deep learning concepts, mathematical foundations (linear algebra, probability, calculus), "
        "and frameworks like PyTorch, TensorFlow, and Scikit-Learn. "
        "Break down complex math or concepts (e.g., Backpropagation, Attention mechanism, Gradient Descent) into "
        "intuitive, bite-sized explanations with practical analogies. Use clear headings, bullet points, "
        "and markdown formatting."
    ),
    "Career Guidance": (
        "You are an experienced career counselor in the tech industry. Provide guidance on different job roles "
        "(Software Developer, Data Scientist, Product Manager, DevOps, etc.), required skill sets, project ideas, "
        "portfolio reviews, resume tips, and industry trends. "
        "Help students map out learning paths, advise them on how to gain practical experience, and guide them on "
        "where to search for internships. Be inspiring, realistic, and highly structured in your advice."
    ),
    "Interview Preparation": (
        "You are a technical interviewer at a top tech company. Help the student prepare for coding assessments "
        "(Data Structures and Algorithms), system design questions, and behavioral interview questions (using the STAR method: "
        "Situation, Task, Action, Result). "
        "Provide mock interview questions, explain optimal time and space complexities (Big O), and give constructive "
        "feedback. Be rigorous but supportive."
    )
}

GENERAL_SYSTEM_PROMPT = (
    "You are a helpful and knowledgeable academic assistant. Answer the student's question "
    "clearly, accurately, and with an encouraging, professional tone. Use Markdown formatting "
    "for readability."
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK_RESPONSES_FILE = os.path.join(BASE_DIR, "test_data", "sample_responses.json")

# Generic simple fallback responses for conversational/filler words
SIMPLE_FALLBACKS = {
    "hello": "Hello! How can I help you with your studies today?",
    "hi": "Hi there! What track are we focusing on today?",
    "hey": "Hey! Ready to learn? Ask me anything about programming, AI/ML, careers, or interviews.",
    "ok": "Got it! Let me know when you have a question or code to discuss.",
    "oh": "No problem! Let me know if you want to explore any concept further.",
    "thanks": "You're very welcome! Let me know if you need anything else.",
    "thank you": "You're very welcome! I'm here to help you succeed.",
}

def _get_mock_response(query: str) -> Optional[str]:
    """Retrieves a mock response from sample_responses.json if matching."""
    if not os.path.exists(MOCK_RESPONSES_FILE):
        return None
    try:
        with open(MOCK_RESPONSES_FILE, "r") as f:
            mock_data = json.load(f)
        query_clean = query.strip().lower()
        # Look for exact or substring match
        for key, val in mock_data.items():
            if key in query_clean or query_clean in key:
                return val
    except Exception as e:
        logger.error(f"Error reading mock responses: {e}")
    return None

def generate_response(
    query: str,
    track: str,
    chat_history: List[Dict[str, str]],
    gemini_key: Optional[str] = None,
    openai_key: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = DEFAULT_TEMPERATURE
) -> str:
    """
    Generates a response from Gemini, falling back to OpenAI, and then to offline mock data.
    """
    if not query.strip():
        return "I cannot generate a response for an empty query. Please enter a valid question!"

    system_prompt = TRACK_PROMPTS.get(track, GENERAL_SYSTEM_PROMPT)

    # 1. Attempt Gemini Generation
    if gemini_key:
        logger.info("Attempting response generation via Gemini API...")
        client = genai.Client(api_key=gemini_key)
        
        # Format history for the new google-genai SDK
        gemini_history = []
        for msg in chat_history:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )
            
        max_retries = 3
        backoff_factor = 2.0
        delay = 1.0
        
        for attempt in range(max_retries):
            try:
                chat = client.chats.create(
                    model=DEFAULT_GEMINI_MODEL,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=temperature,
                        max_output_tokens=DEFAULT_MAX_TOKENS,
                    ),
                    history=gemini_history
                )
                response = chat.send_message(query)
                if response.text:
                    logger.info("Response generated successfully using Gemini API.")
                    return response.text
                else:
                    logger.warning("Empty response from Gemini API.")
                    break # Success but empty response, do not retry
            except APIError as e:
                # Retry on rate limit (429) or server errors (500, 503, 504)
                is_transient = e.code in [429, 500, 503, 504] or "503" in str(e) or "unavailable" in str(e).lower() or "demand" in str(e).lower()
                if is_transient and attempt < max_retries - 1:
                    logger.warning(f"Gemini API transient error {e.code or 503}: {e.message}. Retrying in {delay}s (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(delay)
                    delay *= backoff_factor
                else:
                    logger.error(f"Gemini API Error after attempt {attempt+1}: {e}. Attempting fallback...")
                    break
            except Exception as e:
                logger.error(f"Unexpected Gemini error: {e}. Attempting fallback...")
                break
            
    # 2. Attempt OpenAI Fallback
    if openai_key:
        try:
            logger.info("Attempting response generation via OpenAI API...")
            client = OpenAI(api_key=openai_key)
            
            # Format history for OpenAI
            openai_messages = [{"role": "system", "content": system_prompt}]
            for msg in chat_history:
                role = "user" if msg["role"] == "user" else "assistant"
                openai_messages.append({"role": role, "content": msg["content"]})
            openai_messages.append({"role": "user", "content": query})
            
            completion = client.chat.completions.create(
                model=DEFAULT_OPENAI_MODEL,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=DEFAULT_MAX_TOKENS
            )
            
            res_text = completion.choices[0].message.content
            if res_text:
                logger.info("Response generated successfully using OpenAI API.")
                return f"🤖 *[OpenAI Fallback]*\n\n{res_text}"
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}. Attempting offline mock match...")

    # 3. Offline Mock Match
    mock_res = _get_mock_response(query)
    if mock_res:
        logger.info("Offline match found. Returning mock response.")
        return f"💡 *[Offline Mock Mode]*\n\n{mock_res}"

    # 4. Simple conversational offline fallback for small expressions
    query_clean = query.strip().lower().strip("?.!,")
    if query_clean in SIMPLE_FALLBACKS:
        logger.info(f"Returning simple offline fallback for conversational query '{query_clean}'")
        return f"💡 *[Offline Helper]*\n\n{SIMPLE_FALLBACKS[query_clean]}"

    # 5. Error Message if all options fail
    if not gemini_key and not openai_key:
        return "❌ **API Keys Missing:** Please supply a valid Gemini or OpenAI API Key in the sidebar to start chat."
    
    return "⚠️ **Connection Error:** Failed to generate a response from both Gemini and OpenAI API. Please check your internet connection, API keys, or try again later."
