import os
import shutil
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel, Field
from bson import ObjectId
from app.database import get_database
from app.config import settings
from app.services.transcription import transcribe_audio
from app.services.ai_generation import generate_notes, generate_flashcards, generate_quiz

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["lecture-voice-to-notes"])

# --- Request / Response Pydantic Schemas ---

class LectureIdRequest(BaseModel):
    lecture_id: str = Field(..., description="The unique ID of the lecture document.")

class TranscriptSegmentSchema(BaseModel):
    start: float
    end: float
    text: str

class FlashcardSchema(BaseModel):
    question: str
    answer: str

class QuizItemSchema(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = ""

class LectureDetailResponse(BaseModel):
    id: str
    title: str
    file_name: str
    file_size: int
    status: str
    created_at: datetime
    transcript: Optional[List[TranscriptSegmentSchema]] = []
    summary: Optional[str] = ""
    bullet_notes: Optional[List[str]] = []
    flashcards: Optional[List[FlashcardSchema]] = []
    quizzes: Optional[List[QuizItemSchema]] = []

    class Config:
        json_encoders = {
            ObjectId: str
        }

# --- Helper Functions ---

async def get_lecture_or_404(lecture_id: str, db) -> dict:
    """
    Utility helper to fetch a lecture by ID from MongoDB, raising a 404 error if not found.
    """
    if not ObjectId.is_valid(lecture_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid lecture ID format"
        )
    lecture = await db.lectures.find_one({"_id": ObjectId(lecture_id)})
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture not found"
        )
    # Convert MongoDB _id object to string for serialization compatibility
    lecture["id"] = str(lecture["_id"])
    return lecture


# --- API Routes ---

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_lecture_file(file: UploadFile = File(...)):
    """
    API endpoint to upload and save video/audio lecture files.
    Triggers internal file validation and directory checking before storing.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    # Support major audio and video media extensions
    if ext not in [".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".ogg", ".webm"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported media format. Please upload standard audio/video files."
        )

    db = get_database()
    lecture_id = str(ObjectId())
    stored_filename = f"{lecture_id}{ext}"
    dest_path = os.path.join(settings.UPLOAD_DIR, stored_filename)

    try:
        logger.info(f"Saving uploaded file to {dest_path}")
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to write uploaded file to disk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save file on server."
        )

    file_size = os.path.getsize(dest_path)

    # Insert initial lecture status log in MongoDB
    lecture_doc = {
        "_id": ObjectId(lecture_id),
        "title": file.filename.rsplit(".", 1)[0],
        "file_name": file.filename,
        "file_path": dest_path,
        "file_size": file_size,
        "status": "uploaded",
        "created_at": datetime.utcnow(),
        "transcript": [],
        "summary": "",
        "bullet_notes": [],
        "flashcards": [],
        "quizzes": []
    }

    await db.lectures.insert_one(lecture_doc)
    logger.info(f"Created lecture document for {lecture_id}")

    return {
        "lecture_id": lecture_id,
        "title": lecture_doc["title"],
        "status": "uploaded",
        "message": "File uploaded and saved successfully."
    }


@router.post("/transcribe")
async def transcribe_lecture(request_body: LectureIdRequest):
    """
    API endpoint to transcribe a lecture file.
    Runs the audio extraction (if video) and calls local whisper-small pipeline.
    """
    db = get_database()
    lecture = await get_lecture_or_404(request_body.lecture_id, db)
    
    file_path = lecture["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture media file not found on disk."
        )

    try:
        logger.info(f"Triggering transcription pipeline for lecture {request_body.lecture_id}")
        await db.lectures.update_one(
            {"_id": ObjectId(request_body.lecture_id)},
            {"$set": {"status": "transcribing"}}
        )

        segments = await transcribe_audio(file_path)

        await db.lectures.update_one(
            {"_id": ObjectId(request_body.lecture_id)},
            {
                "$set": {
                    "status": "transcribed",
                    "transcript": segments
                }
            }
        )
        logger.info(f"Completed transcription for lecture {request_body.lecture_id}")
        return {
            "lecture_id": request_body.lecture_id,
            "status": "transcribed",
            "segments_count": len(segments)
        }
    except Exception as e:
        logger.error(f"Error during transcribe route processing: {e}")
        await db.lectures.update_one(
            {"_id": ObjectId(request_body.lecture_id)},
            {"$set": {"status": "failed", "error_message": str(e)}}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )


@router.post("/generate-notes")
async def generate_lecture_summary_notes(request_body: LectureIdRequest):
    """
    API endpoint to generate summary paragraphs and bullet notes.
    Leverages microsoft/Phi-3-mini local text-generation pipeline.
    """
    db = get_database()
    lecture = await get_lecture_or_404(request_body.lecture_id, db)
    
    transcript = lecture.get("transcript", [])
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lecture must be transcribed before generating notes."
        )

    transcript_text = " ".join([seg["text"] for seg in transcript])

    try:
        logger.info(f"Generating notes for lecture {request_body.lecture_id}")
        notes_data = await generate_notes(transcript_text)

        await db.lectures.update_one(
            {"_id": ObjectId(request_body.lecture_id)},
            {
                "$set": {
                    "summary": notes_data["summary"],
                    "bullet_notes": notes_data["bullet_notes"]
                }
            }
        )
        return {
            "lecture_id": request_body.lecture_id,
            "status": "notes_generated",
            "summary_preview": notes_data["summary"][:100] + "..."
        }
    except Exception as e:
        logger.error(f"Error generating notes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Notes generation failed: {str(e)}"
        )


@router.post("/generate-flashcards")
async def generate_lecture_flashcards(request_body: LectureIdRequest):
    """
    API endpoint to generate concept flashcards.
    Leverages microsoft/Phi-3-mini local text-generation pipeline.
    """
    db = get_database()
    lecture = await get_lecture_or_404(request_body.lecture_id, db)
    
    transcript = lecture.get("transcript", [])
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lecture must be transcribed before generating flashcards."
        )

    transcript_text = " ".join([seg["text"] for seg in transcript])

    try:
        logger.info(f"Generating flashcards for lecture {request_body.lecture_id}")
        flashcards = await generate_flashcards(transcript_text)

        await db.lectures.update_one(
            {"_id": ObjectId(request_body.lecture_id)},
            {"$set": {"flashcards": flashcards}}
        )
        return {
            "lecture_id": request_body.lecture_id,
            "status": "flashcards_generated",
            "flashcards_count": len(flashcards)
        }
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Flashcards generation failed: {str(e)}"
        )


@router.post("/generate-quiz")
async def generate_lecture_quiz(request_body: LectureIdRequest):
    """
    API endpoint to generate multiple-choice quizzes.
    Leverages microsoft/Phi-3-mini local text-generation pipeline.
    """
    db = get_database()
    lecture = await get_lecture_or_404(request_body.lecture_id, db)
    
    transcript = lecture.get("transcript", [])
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lecture must be transcribed before generating quizzes."
        )

    transcript_text = " ".join([seg["text"] for seg in transcript])

    try:
        logger.info(f"Generating quiz items for lecture {request_body.lecture_id}")
        quiz_items = await generate_quiz(transcript_text)

        await db.lectures.update_one(
            {"_id": ObjectId(request_body.lecture_id)},
            {"$set": {"quizzes": quiz_items}}
        )
        return {
            "lecture_id": request_body.lecture_id,
            "status": "quiz_generated",
            "questions_count": len(quiz_items)
        }
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation failed: {str(e)}"
        )


@router.get("/lecture/{id}", response_model=LectureDetailResponse)
async def get_lecture_details(id: str):
    """
    API endpoint to retrieve the full content details of a specific lecture.
    """
    db = get_database()
    lecture = await get_lecture_or_404(id, db)
    return lecture
