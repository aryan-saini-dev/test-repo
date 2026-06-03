"""
Voice Recognition Module for the AI-Powered Student Query Assistant.

Pipeline:
  1. mic_recorder captures audio as WebM bytes in the browser
  2. ffmpeg (via imageio-ffmpeg) converts WebM → WAV directly via subprocess
  3. SpeechRecognition's recognize_google performs actual STT
  4. The transcribed text is returned for Gemini chat processing
"""

import io
import os
import subprocess
import tempfile
import speech_recognition as sr
from typing import Optional
from modules.logger import logger

# --- Locate the bundled ffmpeg binary from imageio-ffmpeg ---
_ffmpeg_path = None
try:
    import imageio_ffmpeg
    _ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    if not os.path.isfile(_ffmpeg_path):
        logger.error(f"imageio-ffmpeg binary not found at: {_ffmpeg_path}")
        _ffmpeg_path = None
    else:
        logger.info(f"ffmpeg binary located: {_ffmpeg_path}")
except ImportError:
    logger.warning("imageio-ffmpeg not installed. Run: pip install imageio-ffmpeg")


def _convert_webm_to_wav(audio_bytes: bytes, source_ext: str = "webm") -> bytes:
    """
    Convert audio bytes (WebM/OGG/MP3/etc.) to 16kHz mono WAV
    by calling ffmpeg directly via subprocess.

    No pydub, no ffprobe — just a single ffmpeg call.
    """
    if _ffmpeg_path is None:
        raise RuntimeError(
            "ffmpeg binary not found. Install imageio-ffmpeg: pip install imageio-ffmpeg"
        )

    # Create temp files for input and output
    input_tmp = None
    output_tmp = None
    try:
        # Write input audio to a temp file
        input_tmp = tempfile.NamedTemporaryFile(
            suffix=f".{source_ext}", delete=False
        )
        input_tmp.write(audio_bytes)
        input_tmp.close()

        # Prepare output temp file path
        output_tmp = tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
        )
        output_tmp.close()

        # Run ffmpeg: convert to 16kHz, mono, 16-bit PCM WAV
        cmd = [
            _ffmpeg_path,
            "-y",                    # overwrite output
            "-i", input_tmp.name,    # input file
            "-ar", "16000",          # sample rate 16kHz
            "-ac", "1",              # mono
            "-sample_fmt", "s16",    # 16-bit signed PCM
            "-f", "wav",             # output format
            output_tmp.name,         # output file
            "-loglevel", "error"     # suppress noisy output
        ]

        logger.info(f"Running ffmpeg conversion: {source_ext} → WAV")
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=30  # 30 second timeout
        )

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            logger.error(f"ffmpeg conversion failed (exit {result.returncode}): {stderr}")
            raise RuntimeError(f"ffmpeg conversion failed: {stderr}")

        # Read the converted WAV bytes
        with open(output_tmp.name, "rb") as f:
            wav_bytes = f.read()

        if len(wav_bytes) < 100:
            raise RuntimeError("ffmpeg produced an empty or invalid WAV file.")

        logger.info(
            f"Audio converted: {source_ext} ({len(audio_bytes)} bytes) → "
            f"WAV ({len(wav_bytes)} bytes)"
        )
        return wav_bytes

    finally:
        # Clean up temp files
        if input_tmp and os.path.exists(input_tmp.name):
            try:
                os.unlink(input_tmp.name)
            except OSError:
                pass
        if output_tmp and os.path.exists(output_tmp.name):
            try:
                os.unlink(output_tmp.name)
            except OSError:
                pass


def transcribe_audio_bytes(
    audio_bytes: bytes,
    mime_type: str = "audio/wav",
    gemini_key: Optional[str] = None,
    openai_key: Optional[str] = None
) -> str:
    """
    Transcribes audio bytes into plain text using SpeechRecognition.

    Workflow:
      1. If audio is not WAV, convert it to WAV via ffmpeg subprocess
      2. Run SpeechRecognition's recognize_google (free, no API key needed)
      3. Return the transcribed text

    Args:
        audio_bytes: Raw audio bytes from mic_recorder.
        mime_type: MIME type of audio (e.g. 'audio/webm', 'audio/wav').
        gemini_key: Not used for STT (kept for API compatibility).
        openai_key: Not used for STT (kept for API compatibility).

    Returns:
        The transcribed text string.

    Raises:
        ValueError: If speech cannot be understood or audio is empty.
        RuntimeError: If conversion or transcription fails.
    """
    if not audio_bytes:
        logger.warning("Voice transcription called with empty audio bytes.")
        raise ValueError("Audio data is empty.")

    if len(audio_bytes) < 1000:
        logger.warning(f"Audio too short ({len(audio_bytes)} bytes).")
        raise ValueError("Recording too short. Please speak for at least 1 second.")

    # --- Step 1: Convert to WAV if not already WAV ---
    wav_bytes = audio_bytes
    is_wav = mime_type in ("audio/wav", "audio/x-wav", "audio/wave")

    if not is_wav:
        # Map MIME type to file extension for ffmpeg
        ext_map = {
            "audio/webm": "webm",
            "audio/ogg": "ogg",
            "audio/opus": "ogg",
            "audio/mpeg": "mp3",
            "audio/mp3": "mp3",
            "audio/mp4": "mp4",
            "audio/x-m4a": "m4a",
            "audio/flac": "flac",
        }
        source_ext = ext_map.get(mime_type, "webm")
        logger.info(f"Converting {mime_type} → WAV via ffmpeg...")

        try:
            wav_bytes = _convert_webm_to_wav(audio_bytes, source_ext=source_ext)
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            raise RuntimeError(f"Could not convert audio to WAV: {e}")

    # --- Step 2: Transcribe WAV with SpeechRecognition ---
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    try:
        audio_io = io.BytesIO(wav_bytes)
        with sr.AudioFile(audio_io) as source:
            audio_data = recognizer.record(source)

        logger.info("Running Google Web Speech API recognition...")
        text = recognizer.recognize_google(audio_data)
        text = text.strip()

        if not text:
            raise ValueError("No speech detected in the audio.")

        logger.info(f"STT result: \"{text[:80]}{'...' if len(text) > 80 else ''}\"")
        return text

    except sr.UnknownValueError:
        logger.warning("Speech recognition could not understand the audio.")
        raise ValueError(
            "Could not understand the audio. Please speak clearly and try again."
        )
    except sr.RequestError as e:
        logger.error(f"Speech recognition service error: {e}")
        raise RuntimeError(
            "Speech recognition service unavailable. Check your internet connection."
        )
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Unexpected transcription error: {e}")
        raise RuntimeError(f"Transcription failed: {e}")


# Backward-compatible alias
stream_audio_data = transcribe_audio_bytes
