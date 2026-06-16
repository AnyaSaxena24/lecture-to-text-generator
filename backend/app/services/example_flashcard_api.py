from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List
from app.services.flashcard_service import FlashcardGenerationService

router = APIRouter(prefix="/example-flashcards", tags=["flashcards-generation-example"])

# Instantiate the service
flashcard_service = FlashcardGenerationService()

class GenerateFlashcardsRequest(BaseModel):
    transcript_text: str = Field(..., min_length=10, description="The raw transcript text to generate flashcards from.")

class FlashcardResponseSchema(BaseModel):
    question: str = Field(..., description="The query representing core concepts.")
    answer: str = Field(..., description="Concise answer details.")
    difficulty: str = Field(..., description="The difficulty level assigned: Easy, Medium, or Hard.")
    tag: str = Field(..., description="Category tag associated with this concept.")

@router.post("/generate", response_model=List[FlashcardResponseSchema])
async def generate_study_flashcards(payload: GenerateFlashcardsRequest):
    """
    Example API endpoint demonstrating how to consume the FlashcardGenerationService.
    Accepts raw text transcript payloads, invokes local Phi-3-mini pipelines,
    applies local deduplication, and returns a JSON list of flashcards.
    """
    try:
        cards = await flashcard_service.generate_flashcards(payload.transcript_text)
        return cards
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Flashcard compilation failed: {str(e)}"
        )
