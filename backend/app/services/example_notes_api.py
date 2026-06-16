from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List
from app.services.notes_service import LectureNotesService

router = APIRouter(prefix="/example-notes", tags=["notes-generation-example"])

# Instantiate the service with window settings
notes_service = LectureNotesService(chunk_size_words=1200, overlap_words=150)

class GenerateNotesRequest(BaseModel):
    transcript_text: str = Field(..., min_length=10, description="The raw transcript text to compile notes from.")

class StudyGuideResponseSchema(BaseModel):
    summary: str = Field(..., description="Executive summary of the lecture.")
    detailed_notes: List[str] = Field(..., description="Deduplicated detailed concepts bullet points.")
    key_concepts: List[str] = Field(..., description="Key concept titles with short annotations.")
    formulas: List[str] = Field(..., description="Important math/physics formulas or logic patterns.")
    definitions: List[str] = Field(..., description="Crucial vocab terms and definitions.")
    topics: List[str] = Field(..., description="Extracted subjects or tags list.")

@router.post("/generate", response_model=StudyGuideResponseSchema)
async def generate_study_guide_from_transcript(payload: GenerateNotesRequest):
    """
    Example API endpoint demonstrating how to consume the LectureNotesService.
    Accepts raw text transcript payloads, performs sliding-window chunking, 
    triggers local Phi-3-mini pipelines, and merges the compiled responses into a unified study guide.
    """
    try:
        # Generate the structured guide
        guide = await notes_service.generate_study_guide(payload.transcript_text)
        return guide
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Study guide compilation failed: {str(e)}"
        )
