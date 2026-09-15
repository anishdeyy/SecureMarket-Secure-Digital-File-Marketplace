from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
import os

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    APP_NAME: str = "SecureMarket"
    SECRET_KEY: str = "dev-secret-key-change-in-production-abc123xyz"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://securemarket:securemarket@localhost:5432/securemarket"

    # JWT
    JWT_SECRET: str = "jwt-secret-key-change-in-production-xyz789"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: Optional[str] = None
    AWS_KMS_KEY_ID: Optional[str] = None

    # Storage
    STORAGE_MODE: str = "local"  # local | s3
    LOCAL_STORAGE_PATH: str = "./storage"
    S3_SIGNED_URL_EXPIRATION: int = 300  # seconds

    # Payment
    PAYMENT_MODE: str = "mock"  # mock | razorpay
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None

    # AI
    AI_MODE: str = "gemini"  # gemini | ollama | mock
    GEMINI_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"

    # Malware
    MALWARE_SCAN_MODE: str = "mock"  # mock | clamav
    CLAMAV_HOST: str = "localhost"
    CLAMAV_PORT: int = 3310

    # Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379"

    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: list = [
        "pdf", "docx", "doc", "txt", "zip", "rar", "7z",
        "xlsx", "xls", "csv", "pptx", "ppt",
        "png", "jpg", "jpeg", "gif", "svg", "webp",
        "mp3", "mp4", "mov", "avi",
        "py", "js", "ts", "html", "css", "json",
        "md", "epub"
    ]

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:3000"

    # Download limits
    DEFAULT_DOWNLOAD_LIMIT: int = 5

    class Config:
        env_file = str(_ENV_FILE)
        extra = "ignore"

settings = Settings()
