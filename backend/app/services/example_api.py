import os
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any

# Import the transcription service module
from app.services.transcription_service import LectureTranscriptionService

router = APIRouter(prefix="/example", tags=["transcription-example"])

# Instantiate the service. You can toggle use_gpu=True/False
transcriber = LectureTranscriptionService(model_id="openai/whisper-small", use_gpu=True)

class TranscriptionResponseSchema(BaseModel):
    full_transcript: str
    detected_language: str
    segments_count: int
    timestamps: List[Dict[str, Any]]

@router.post("/transcribe-media", response_model=TranscriptionResponseSchema)
async def transcribe_media_file(file: UploadFile = File(...)):
    """
    Example API endpoint demonstrating how to consume the LectureTranscriptionService.
    Accepts media file uploads (audio/video), performs local Whisper-small transcription,
    and returns a structured JSON payload detailing transcript, detected language, and segment timestamps.
    """
    
    # 1. Validate file format extensions
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".webm", ".mov"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported media format. Supports MP3, WAV, M4A, MP4, WebM, and MOV."
        )

    # 2. Write upload stream to a secure temporary location on disk
    # This prevents storing huge video files in RAM buffer during processing.
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"upload_{file.filename}")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write uploaded file to disk: {str(e)}"
        )

    # 3. Invoke transcription service
    try:
        # batch_size=4 is recommended for whisper-small to avoid VRAM overload
        result = transcriber.transcribe_lecture(temp_file_path, batch_size=4)
        
        # 4. Map outputs to response schema
        return {
            "full_transcript": result["full_transcript"],
            "detected_language": result["detected_language"],
            "segments_count": len(result["timestamps"]),
            "timestamps": result["timestamps"]
        }
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
    finally:
        # 5. Always clean up temporary file from workspace
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
