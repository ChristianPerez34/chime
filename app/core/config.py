from typing import List
from dotenv import load_dotenv
from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "chime"
    API_PATH: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    DATABASE_URL: PostgresDsn = os.getenv("DATABASE_URL")
    PORT: int = os.getenv("PORT", 8000)


load_dotenv()
settings = Settings()
