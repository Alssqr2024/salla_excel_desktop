import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    BASE_DIR: Path = BASE_DIR
    STORAGE_DIR: Path = BASE_DIR / "storage"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    STATIC_DIR: Path = BASE_DIR / "static"

    OPENSERP_URL: str = "http://127.0.0.1:7000"
    SERPER_API_KEY: str = ""

    AI_VISION_API_KEY: str = ""
    AI_VISION_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    AI_VISION_MODEL: str = "gemini-2.5-flash"

    IMAGE_FINDER_TIMEOUT: int = 30
    IMAGE_FINDER_MAX_CANDIDATES: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
