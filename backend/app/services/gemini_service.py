"""
Gemini API integration service for audio transcription and AI content generation.
Uses the free-tier google-generativeai SDK with gemini-2.0-flash model.
"""
import os
import json
import logging
import asyncio
import mimetypes
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Lazy-loaded Gemini client
_gemini_model = None


def _get_gemini_model():
    """Lazy-load the Gemini generative model."""
    global _gemini_model
    if _gemini_model is None:
        import google.generativeai as genai
        from app.config import settings

        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set. Please add it to your environment variables.")

        genai.configure(api_key=settings.GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        logger.info("Gemini 2.0 Flash model initialized successfully.")
    return _gemini_model


async def transcribe_audio_with_gemini(file_path: str) -> List[Dict[str, Any]]:
    """
    Transcribes an audio/video file using Gemini's multimodal capabilities.
    Returns a list of transcript segments with start, end, and text.
    """
    import google.generativeai as genai

    model = _get_gemini_model()

    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".mp4": "video/mp4",
            ".ogg": "audio/ogg",
            ".webm": "audio/webm",
            ".mpeg": "video/mpeg",
        }
        mime_type = mime_map.get(ext, "audio/mpeg")

    logger.info(f"Uploading file to Gemini for transcription: {file_path} ({mime_type})")

    loop = asyncio.get_running_loop()

    def _upload_and_transcribe():
        # Upload file to Gemini
        uploaded_file = genai.upload_file(file_path, mime_type=mime_type)
        logger.info(f"File uploaded to Gemini: {uploaded_file.name}")

        prompt = (
            "You are a precise audio transcription assistant. "
            "Transcribe the audio in this file word-for-word. "
            "Break the transcription into logical segments (roughly every 1-3 sentences). "
            "Return ONLY a valid JSON array with no extra text, where each element has:\n"
            '- "start": approximate start time in seconds (float)\n'
            '- "end": approximate end time in seconds (float)\n'
            '- "text": the transcribed text for that segment\n\n'
            "Example format:\n"
            '[{"start": 0.0, "end": 8.5, "text": "Hello and welcome..."}, '
            '{"start": 8.5, "end": 15.0, "text": "Today we will..."}]\n\n'
            "If you cannot hear clear speech, still transcribe whatever is audible. "
            "Return ONLY the JSON array, no markdown formatting or code blocks."
        )

        response = model.generate_content([uploaded_file, prompt])

        # Clean up uploaded file
        try:
            genai.delete_file(uploaded_file.name)
        except Exception:
            pass

        return response.text

    try:
        raw_response = await loop.run_in_executor(None, _upload_and_transcribe)

        # Parse JSON from response - strip markdown code blocks if present
        text = raw_response.strip()
        if text.startswith("```"):
            # Remove opening ```json or ``` and closing ```
            lines = text.split("\n")
            lines = lines[1:]  # remove opening ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]  # remove closing ```
            text = "\n".join(lines)

        segments = json.loads(text)
        if isinstance(segments, list) and len(segments) > 0:
            logger.info(f"Gemini transcription returned {len(segments)} segments.")
            return segments

        raise ValueError("Empty or invalid transcription result")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini transcription JSON: {e}")
        logger.error(f"Raw response: {raw_response[:500]}")
        # Try to extract text as a single segment
        return [{"start": 0.0, "end": 60.0, "text": raw_response.strip()}]
    except Exception as e:
        logger.error(f"Gemini transcription failed: {e}")
        raise


async def generate_with_gemini(prompt: str) -> str:
    """
    Sends a text prompt to Gemini and returns the response text.
    """
    model = _get_gemini_model()
    loop = asyncio.get_running_loop()

    def _generate():
        response = model.generate_content(prompt)
        return response.text

    return await loop.run_in_executor(None, _generate)


async def generate_notes_with_gemini(transcript_text: str) -> Dict[str, Any]:
    """
    Generate lecture summary and bullet notes from transcript text.
    """
    prompt = (
        "You are an expert academic AI teaching assistant. "
        "Analyze the following lecture transcript and generate:\n"
        "1. A comprehensive summary paragraph (3-5 sentences)\n"
        "2. A list of 5-8 key bullet point notes\n\n"
        "Return ONLY a valid JSON object with no extra text:\n"
        '{"summary": "...", "bullet_notes": ["...", "..."]}\n\n'
        "No markdown formatting or code blocks.\n\n"
        f"Transcript:\n{transcript_text[:8000]}"
    )

    try:
        response = await generate_with_gemini(prompt)
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        data = json.loads(text)
        return {
            "summary": data.get("summary", ""),
            "bullet_notes": data.get("bullet_notes", [])
        }
    except Exception as e:
        logger.error(f"Gemini notes generation failed: {e}")
        raise


async def generate_flashcards_with_gemini(transcript_text: str) -> List[Dict[str, str]]:
    """
    Generate study flashcards from transcript text.
    """
    prompt = (
        "You are an expert academic AI teaching assistant. "
        "Create 5-8 study flashcards from this lecture transcript. "
        "Each flashcard should test a key concept or definition.\n\n"
        "Return ONLY a valid JSON array with no extra text:\n"
        '[{"question": "...", "answer": "..."}, ...]\n\n'
        "No markdown formatting or code blocks.\n\n"
        f"Transcript:\n{transcript_text[:8000]}"
    )

    try:
        response = await generate_with_gemini(prompt)
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        data = json.loads(text)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "flashcards" in data:
            return data["flashcards"]
        return data
    except Exception as e:
        logger.error(f"Gemini flashcards generation failed: {e}")
        raise


async def generate_quiz_with_gemini(transcript_text: str) -> List[Dict[str, Any]]:
    """
    Generate multiple-choice quiz questions from transcript text.
    """
    prompt = (
        "You are an expert academic AI teaching assistant. "
        "Create 4-6 multiple-choice quiz questions from this lecture transcript. "
        "Each question should have exactly 4 options with one correct answer.\n\n"
        "Return ONLY a valid JSON array with no extra text:\n"
        '[{"question": "...", "options": ["A", "B", "C", "D"], '
        '"correct_answer": "A", "explanation": "..."}, ...]\n\n'
        "No markdown formatting or code blocks.\n\n"
        f"Transcript:\n{transcript_text[:8000]}"
    )

    try:
        response = await generate_with_gemini(prompt)
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        data = json.loads(text)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "quizzes" in data:
            return data["quizzes"]
        return data
    except Exception as e:
        logger.error(f"Gemini quiz generation failed: {e}")
        raise
