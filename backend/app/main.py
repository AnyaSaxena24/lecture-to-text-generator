from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import get_database, close_database
from app.routes import lectures, lecture_api, advanced_api
from app.services import example_api, example_notes_api, example_flashcard_api, example_quiz_api
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

app = FastAPI(
    title="Lecture Voice-to-Notes AI API",
    description="Backend service for transcribing lectures and generating summary notes, flashcards, and quizzes.",
    version="1.0.0"
)

# CORS Middleware config
# Set to support local Next.js client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(lectures.router)
app.include_router(lecture_api.router)
app.include_router(advanced_api.router)
app.include_router(example_api.router)
app.include_router(example_notes_api.router)
app.include_router(example_flashcard_api.router)
app.include_router(example_quiz_api.router)

@app.on_event("startup")
async def startup_event():
    # Trigger database connection
    get_database()

@app.on_event("shutdown")
async def shutdown_event():
    close_database()

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "app": "Lecture Voice-to-Notes AI API",
        "llm_provider": settings.LLM_PROVIDER,
        "whisper_model": settings.WHISPER_MODEL
    }
