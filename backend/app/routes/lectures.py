import os
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from app.database import get_database
from app.config import settings
from app.models.lecture import LectureResponse
from app.services.transcription import transcribe_audio
from app.services.ai_generation import generate_lecture_notes
from app.services.pdf_service import generate_notes_pdf
from bson import ObjectId
from datetime import datetime
import shutil
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lectures", tags=["lectures"])

# Define a static default student ID to replace user scopes
DEFAULT_STUDENT_ID = "default_student"

async def process_lecture_pipeline(lecture_id: str, file_path: str):
    db = get_database()
    try:
        # 1. Update status to transcribing
        await db.lectures.update_one(
            {"_id": ObjectId(lecture_id)},
            {"$set": {"status": "transcribing"}}
        )
        logger.info(f"Starting transcription for lecture {lecture_id}")
        
        # 2. Transcribe
        segments = await transcribe_audio(file_path)
        
        # 3. Update status to generating
        await db.lectures.update_one(
            {"_id": ObjectId(lecture_id)},
            {
                "$set": {
                    "status": "generating",
                    "transcript": segments
                }
            }
        )
        logger.info(f"Starting AI generation for lecture {lecture_id}")
        
        # Build prompt string from transcript
        transcript_text = " ".join([seg["text"] for seg in segments])
        
        # 4. Generate AI content
        summary, bullet_notes, flashcards, quizzes = await generate_lecture_notes(transcript_text)
        
        # 5. Save and finalize status
        await db.lectures.update_one(
            {"_id": ObjectId(lecture_id)},
            {
                "$set": {
                    "status": "completed",
                    "summary": summary,
                    "bullet_notes": bullet_notes,
                    "flashcards": flashcards,
                    "quizzes": quizzes
                }
            }
        )
        logger.info(f"Successfully processed lecture {lecture_id}")
    except Exception as e:
        logger.exception(f"Failed to process lecture {lecture_id}")
        await db.lectures.update_one(
            {"_id": ObjectId(lecture_id)},
            {
                "$set": {
                    "status": "failed",
                    "error_message": str(e)
                }
            }
        )

@router.post("/upload", response_model=LectureResponse, status_code=status.HTTP_201_CREATED)
async def upload_lecture(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # Validate file format
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".ogg", ".webm"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload audio or video files."
        )

    db = get_database()
    
    # Save file to upload directory
    file_id = str(ObjectId())
    file_name = f"{file_id}{ext}"
    dest_path = os.path.join(settings.UPLOAD_DIR, file_name)
    
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save uploaded file."
        )
        
    file_size = os.path.getsize(dest_path)
    
    # Create lecture entry in database mapped to static DEFAULT_STUDENT_ID
    lecture_dict = {
        "user_id": DEFAULT_STUDENT_ID,
        "title": file.filename.rsplit(".", 1)[0],
        "file_name": file.filename,
        "file_path": dest_path,
        "file_size": file_size,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "transcript": [],
        "summary": "",
        "bullet_notes": [],
        "flashcards": [],
        "quizzes": []
    }
    
    result = await db.lectures.insert_one(lecture_dict)
    lecture_dict["id"] = str(result.inserted_id)
    
    # Launch background processing pipeline
    background_tasks.add_task(process_lecture_pipeline, lecture_dict["id"], dest_path)
    
    return lecture_dict

@router.get("", response_model=list[LectureResponse])
async def list_lectures():
    db = get_database()
    cursor = db.lectures.find({"user_id": DEFAULT_STUDENT_ID}).sort("created_at", -1)
    lectures = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        lectures.append(doc)
    return lectures

@router.get("/{lecture_id}", response_model=LectureResponse)
async def get_lecture(lecture_id: str):
    db = get_database()
    lecture = await db.lectures.find_one({"_id": ObjectId(lecture_id), "user_id": DEFAULT_STUDENT_ID})
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture not found"
        )
    lecture["id"] = str(lecture["_id"])
    return lecture

@router.delete("/{lecture_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lecture(lecture_id: str):
    db = get_database()
    lecture = await db.lectures.find_one({"_id": ObjectId(lecture_id), "user_id": DEFAULT_STUDENT_ID})
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture not found"
        )
        
    # Remove physical file if it exists
    file_path = lecture.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {e}")
            
    await db.lectures.delete_one({"_id": ObjectId(lecture_id)})
    return None

@router.get("/{lecture_id}/pdf")
async def download_lecture_pdf(lecture_id: str):
    db = get_database()
    lecture = await db.lectures.find_one({"_id": ObjectId(lecture_id), "user_id": DEFAULT_STUDENT_ID})
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture not found"
        )
        
    if lecture.get("status") != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lecture processing is not completed yet."
        )
        
    created_at = lecture.get("created_at")
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            try:
                created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                created_at = datetime.utcnow()
    elif not created_at:
        created_at = datetime.utcnow()

    date_str = created_at.strftime("%Y-%m-%d")
    
    pdf_buffer = generate_notes_pdf(
        lecture_title=lecture.get("title", "Lecture"),
        date_str=date_str,
        summary=lecture.get("summary", ""),
        bullet_notes=lecture.get("bullet_notes", []),
        flashcards=lecture.get("flashcards", []),
        quizzes=lecture.get("quizzes", []),
        transcript=lecture.get("transcript", [])
    )
    
    safe_title = "".join([c if c.isalnum() else "_" for c in lecture.get("title", "notes")])
    headers = {
        "Content-Disposition": f"attachment; filename={safe_title}_notes.pdf"
    }
    
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)
