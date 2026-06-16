from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str

class Flashcard(BaseModel):
    question: str
    answer: str

class QuizItem(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = ""

class LectureBase(BaseModel):
    title: str

class LectureCreate(LectureBase):
    pass

class LectureResponse(LectureBase):
    id: str
    user_id: str
    file_name: str
    file_size: int
    duration: Optional[float] = None
    status: str  # pending, transcribing, generating, completed, failed
    error_message: Optional[str] = None
    created_at: datetime
    
    # We might choose not to include heavy fields in the list view, but we'll put them as optional
    transcript: Optional[List[TranscriptSegment]] = None
    summary: Optional[str] = None
    bullet_notes: Optional[List[str]] = None
    flashcards: Optional[List[Flashcard]] = None
    quizzes: Optional[List[QuizItem]] = None

    class Config:
        from_attributes = True
