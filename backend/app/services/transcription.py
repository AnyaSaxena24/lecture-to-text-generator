import os
import subprocess
import logging
import asyncio
from app.config import settings

logger = logging.getLogger(__name__)

# Global variable to hold the Hugging Face Whisper pipeline
whisper_pipeline_instance = None

def get_whisper_pipeline():
    """
    Lazy loads the local Hugging Face Whisper-small pipeline.
    This avoids slow startup times for the FastAPI server.
    """
    global whisper_pipeline_instance
    if settings.WHISPER_MODEL == "mock":
        return None

    if whisper_pipeline_instance is None:
        try:
            import torch
            from transformers import pipeline
            
            logger.info("Initializing Hugging Face whisper-small pipeline...")
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            
            whisper_pipeline_instance = pipeline(
                "automatic-speech-recognition",
                model="openai/whisper-small",
                device=device,
                torch_dtype=torch_dtype,
                chunk_length_s=30,
                return_timestamps=True
            )
            logger.info("Hugging Face whisper-small pipeline loaded successfully.")
        except Exception as e:
            logger.exception(f"Failed to load local Whisper pipeline: {e}. Falling back to mock transcription.")
            settings.WHISPER_MODEL = "mock"
            
    return whisper_pipeline_instance

def extract_audio_from_video(video_path: str, output_audio_path: str) -> bool:
    """
    Extracts audio from video file using FFmpeg subprocess execution.
    Converts audio into 16kHz mono WAV, which is ideal for Whisper.
    """
    try:
        logger.info(f"Extracting audio from {video_path} to {output_audio_path} using FFmpeg...")
        # -y overwrites existing file, -i is input, -vn disables video, -ac 1 mono, -ar 16000 16kHz sample rate
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            output_audio_path
        ]
        
        # Run subprocess
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False
            
        logger.info("FFmpeg audio extraction completed successfully.")
        return True
    except Exception as e:
        logger.exception(f"Exception during FFmpeg execution: {e}")
        return False

async def transcribe_audio(file_path: str) -> list:
    """
    Transcribes audio file and returns a list of segments with start, end, and text keys.
    Runs in a threadpool to avoid blocking the async loop during heavy neural network tasks.
    """
    # Check if this is a video file and extract audio if necessary
    ext = os.path.splitext(file_path)[1].lower()
    work_file = file_path
    
    if ext in [".mp4", ".mpeg", ".webm", ".avi", ".mov"]:
        audio_out = f"{os.path.splitext(file_path)[0]}_temp.wav"
        # Run blocking FFmpeg inside thread pool
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(None, extract_audio_from_video, file_path, audio_out)
        if success and os.path.exists(audio_out):
            work_file = audio_out
            
    if settings.WHISPER_MODEL == "gemini":
        logger.info("Using Gemini API for transcription...")
        try:
            from app.services.gemini_service import transcribe_audio_with_gemini
            segments = await transcribe_audio_with_gemini(work_file)
            # Clean up temporary audio file if created
            if work_file != file_path and os.path.exists(work_file):
                os.remove(work_file)
            return segments
        except Exception as e:
            logger.error(f"Gemini transcription failed: {e}")
            # Clean up temporary audio file if created
            if work_file != file_path and os.path.exists(work_file):
                os.remove(work_file)
            raise

    if settings.WHISPER_MODEL == "mock":
        await asyncio.sleep(2)
        # Clean up temporary audio file if created
        if work_file != file_path and os.path.exists(work_file):
            os.remove(work_file)
            
        return [
            {"start": 0.0, "end": 8.0, "text": "Hello and welcome to this lecture on full stack AI application development."},
            {"start": 8.0, "end": 20.0, "text": "Today we will learn how to build modular APIs using FastAPI, MongoDB, and local Hugging Face pipelines."},
            {"start": 20.0, "end": 35.0, "text": "Local models like whisper-small and Phi-3 can run directly on consumer hardware without calling external cloud services."}
        ]

    loop = asyncio.get_running_loop()
    try:
        pipe = get_whisper_pipeline()
        if pipe is None:
            raise ValueError("Whisper pipeline is not initialized")

        def _transcribe():
            logger.info(f"Running Whisper inference on {work_file}...")
            # We pass return_timestamps=True to get segment offsets
            result = pipe(work_file, return_timestamps=True)
            segments = []
            
            chunks = result.get("chunks", [])
            for chunk in chunks:
                timestamp = chunk.get("timestamp", (0.0, 0.0))
                # Ensure values are floats and handle cases where they might be None
                start = float(timestamp[0]) if timestamp[0] is not None else 0.0
                end = float(timestamp[1]) if timestamp[1] is not None else start + 5.0
                
                segments.append({
                    "start": start,
                    "end": end,
                    "text": chunk.get("text", "").strip()
                })
            return segments

        transcription_result = await loop.run_in_executor(None, _transcribe)
        
        # Clean up temporary audio file
        if work_file != file_path and os.path.exists(work_file):
            try:
                os.remove(work_file)
            except Exception as e:
                logger.error(f"Error deleting temp audio file: {e}")
                
        return transcription_result
    except Exception as e:
        logger.error(f"Error during Whisper pipeline transcription: {e}")
        # Clean up temporary audio file
        if work_file != file_path and os.path.exists(work_file):
            try:
                os.remove(work_file)
            except Exception:
                pass
        # Graceful fallback mock data
        return [
            {"start": 0.0, "end": 5.0, "text": "Whisper execution failed."},
            {"start": 5.0, "end": 10.0, "text": "Using mock text segment due to local engine initialization failure."}
        ]
