import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "lecture_notes_db"
    JWT_SECRET: str = "supersecretjwtkeychangeinproduction1234567890"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    UPLOAD_DIR: str = "uploads"
    
    # AI models & settings
    LLM_PROVIDER: str = "mock"  # "ollama" | "gemini" | "openai" | "mock"
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    WHISPER_MODEL: str = "mock"  # "tiny" | "base" | "gemini" | "mock"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Make sure upload dir exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
