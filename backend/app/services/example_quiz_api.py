from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.quiz_service import QuizGenerationService

router = APIRouter(prefix="/example-quiz", tags=["quiz-generation-example"])

# Instantiate the service
quiz_service = QuizGenerationService()

class GenerateQuizRequest(BaseModel):
    transcript_text: str = Field(..., min_length=10, description="The raw transcript text to compile quizzes from.")

class QuizItemResponseSchema(BaseModel):
    question: str = Field(..., description="The query string representing quiz prompt.")
    options: List[str] = Field(..., description="List of options. Empty for short answer type, exactly 2 for true/false, exactly 4 for mcq.")
    correct_answer: str = Field(..., description="The answer key details.")
    difficulty: str = Field(..., description="The difficulty rating: Easy, Medium, or Hard.")
    type: str = Field(..., description="The question format: mcq, true_false, or short_answer.")

@router.post("/generate", response_model=List[QuizItemResponseSchema])
async def generate_lecture_quiz(payload: GenerateQuizRequest):
    """
    Example API endpoint demonstrating how to consume the QuizGenerationService.
    Accepts raw text transcript payloads, invokes local Phi-3-mini pipelines,
    applies local deduplication, and returns a JSON list of quiz items (MCQs, True/False, Short Answer).
    """
    try:
        quiz = await quiz_service.generate_quiz(payload.transcript_text)
        return quiz
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz compilation failed: {str(e)}"
        )
