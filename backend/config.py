# backend/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):

    # Groq
    GROQ_API_KEY: str
    GROQ_LLM_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_WHISPER_MODEL: str = "whisper-large-v3-turbo"

    # Cartesia
    CARTESIA_API_KEY: str
    CARTESIA_VOICE_ID: str = "694f9389-aac1-45b6-b726-9d9369183238"
    CARTESIA_MODEL_ID: str = "sonic-3.5"
    CARTESIA_VOICES: dict = {
        "Skyler": "db6b0ed5-d5d3-463d-ae85-518a07d3c2b4",
        "Gemma": "62ae83ad-4f6a-430b-af41-a9bede9286ca",
        "Daniel": "47c38ca4-5f35-497b-b1a3-415245fb35e1",
        "Ronald": "5ee9feff-1265-424a-9d7f-8e4d431a12c7",
        "Archie": "ef191366-f52f-447a-a398-ed8c0f2943a1",
    }

    # Tavily
    TAVILY_API_KEY: str
    # SERPAPI
    SERPAPI_API_KEY: str

    # App
    MAX_MEMORY_MESSAGES: int = 10

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()