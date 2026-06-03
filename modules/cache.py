"""
Caching Module for the AI-Powered Student Query Assistant.

Provides memory-based query-response caching using functools.lru_cache.
"""

from functools import lru_cache
from typing import List, Dict, Tuple, Optional
from modules.chatbot import generate_response
from modules.logger import logger

@lru_cache(maxsize=128)
def _generate_cached_impl(
    query: str,
    track: str,
    history_tuple: Tuple[Tuple[str, str], ...],
    gemini_key: Optional[str],
    openai_key: Optional[str],
    model_name: Optional[str],
    temperature: float
) -> str:
    """Internal cached implementation containing the actual API call."""
    logger.info(f"Cache MISS for query: '{query[:30]}...' in track '{track}'")
    # Convert history tuple back to list of dicts
    chat_history = [{"role": role, "content": content} for role, content in history_tuple]
    return generate_response(
        query=query,
        track=track,
        chat_history=chat_history,
        gemini_key=gemini_key,
        openai_key=openai_key,
        model_name=model_name,
        temperature=temperature
    )

def get_cached_response(
    query: str,
    track: str,
    chat_history: List[Dict[str, str]],
    gemini_key: Optional[str] = None,
    openai_key: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.7,
    bypass_cache: bool = False
) -> Tuple[str, bool]:
    """
    Checks cache first, then calls generation if cache miss or bypass_cache is True.
    
    Returns:
        (response_text, is_cache_hit)
    """
    if bypass_cache:
        logger.info(f"Bypassing cache for query: '{query[:30]}...'")
        res = generate_response(
            query=query,
            track=track,
            chat_history=chat_history,
            gemini_key=gemini_key,
            openai_key=openai_key,
            model_name=model_name,
            temperature=temperature
        )
        return res, False

    # Convert list of dicts to hashable tuple of tuples
    history_tuple = tuple((msg["role"], msg["content"]) for msg in chat_history)
    
    before_info = _generate_cached_impl.cache_info()
    res = _generate_cached_impl(
        query.strip(),
        track.strip(),
        history_tuple,
        gemini_key,
        openai_key,
        model_name,
        temperature
    )
    after_info = _generate_cached_impl.cache_info()
    
    is_hit = after_info.hits > before_info.hits
    if is_hit:
        logger.info(f"Cache HIT for query: '{query[:30]}...' in track '{track}'")
        
    return res, is_hit

def clear_response_cache() -> None:
    """Wipes the global memory cache."""
    _generate_cached_impl.cache_clear()
    logger.info("Response LRU cache cleared successfully.")
