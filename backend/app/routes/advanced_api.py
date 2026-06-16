import logging
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from bson import ObjectId
from app.database import get_database
from app.services.vector_store_service import VectorStoreService
from app.services.advanced_ai_service import AdvancedAIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/lecture/{lecture_id}", tags=["advanced-ai"])

# --- Request / Response Pydantic Schemas ---

class ChatRequest(BaseModel):
    query: str = Field(..., description="The student's chat message to the lecture bot.")

class TranslateRequest(BaseModel):
    target_language: str = Field(..., description="Target language identifier (e.g. 'Spanish', 'French').")

# --- Routes ---

@router.post("/chat")
async def chat_with_lecture_vectors(lecture_id: str, payload: ChatRequest):
    """
    RAG Chatbot endpoint. Queries ChromaDB for local transcript context chunks
    and prompts Phi-3 to answer the student's question.
    """
    db = get_database()
    lecture = await db.lectures.find_one({"_id": ObjectId(lecture_id)})
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    try:
        response = await VectorStoreService.chat_with_lecture(lecture_id, payload.query)
        return {
            "query": payload.query,
            "response": response
        }
    except Exception as e:
        logger.error(f"Error in chat route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chatbot processing failed."
        )


@router.get("/search")
async def semantic_search_transcript(lecture_id: str, query: str):
    """
    Performs vector similarity search on the lecture's indexed transcript collection.
    """
    db = get_database()
    lecture = await db.lectures.find_one({"_id": ObjectId(lecture_id)})
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    try:
        results = VectorStoreService.semantic_search(lecture_id, query, k=3)
        return {
            "query": query,
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in search route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Semantic search failed."
        )


@router.post("/chapters")
async def segment_lecture_chapters(lecture_id: str):
    """
    Performs topic segmentation on the transcript segments to output logical chapters.
    """
    db = get_database()
    lecture = await db.lectures.find_one({"_id": ObjectId(lecture_id)})
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    transcript = lecture.get("transcript", [])
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript is empty. Please transcribe lecture first.")

    try:
        chapters = await AdvancedAIService.generate_chapters(transcript)
        await db.lectures.update_one(
            {"_id": ObjectId(lecture_id)},
            {"$set": {"chapters": chapters}}
        )
        return {
            "lecture_id": lecture_id,
            "chapters": chapters
        }
    except Exception as e:
        logger.error(f"Error in chapters route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chapter generation failed."
        )


@router.post("/translate")
async def translate_lecture_content(lecture_id: str, payload: TranslateRequest):
    """
    Translates the lecture transcript segments into the target language.
    """
    db = get_database()
    lecture = await db.lectures.find_one({"_id": ObjectId(lecture_id)})
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    transcript = lecture.get("transcript", [])
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript is empty.")

    try:
        translated = await AdvancedAIService.translate_transcript(transcript, payload.target_language)
        return {
            "lecture_id": lecture_id,
            "target_language": payload.target_language,
            "translated_transcript": translated
        }
    except Exception as e:
        logger.error(f"Error in translate route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Translation failed."
        )
