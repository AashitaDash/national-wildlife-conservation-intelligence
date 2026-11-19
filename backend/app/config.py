import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables or .env file.
    Defines database connectivity, JWT security, external endpoints, and ML parameters.
    """
    # Environment
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/wildlife_db"
    FALLBACK_SQLITE_URL: str = "sqlite:///./wildlife_dev.db"

    # Authentication & Security
    JWT_SECRET: str = "dev-only-insecure-secret-change-before-deployment"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours

    # External APIs
    GBIF_API_URL: str = "https://api.gbif.org/v1"
    INATURALIST_API_URL: str = "https://api.inaturalist.org/v1"
    EBIRD_API_URL: str = "https://api.ebird.org/v2"
    IUCN_API_URL: str = "https://api.iucnredlist.org/api/v4"
    EBIRD_API_KEY: Optional[str] = None
    IUCN_API_KEY: Optional[str] = None
    IUCN_API_TOKEN: Optional[str] = None
    PROTECTED_PLANET_API_KEY: Optional[str] = None
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = None

    # NLP & Machine Learning Settings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    ML_MODEL_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ml", "models")

    # LLM & RAG Chatbot Settings
    CHAT_LLM_PROVIDER: str = "auto"  # 'auto', 'ollama', 'gemini', 'openai', 'extractive'
    CHAT_LLM_MODEL: str = "llama3:latest"
    CHAT_LLM_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    CHAT_LLM_TIMEOUT_SECONDS: int = 25
    CHAT_LLM_MAX_TOKENS: int = 1024

    # File uploads
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    MAX_UPLOAD_SIZE_MB: int = 10

    # Gamification point values (configurable)
    POINTS_VERIFIED_OBSERVATION: int = 50
    POINTS_CITATION_BONUS: int = 15
    POINTS_RECORD_CORRECTION: int = 10
    POINTS_RARE_SPECIES_BONUS: int = 25
    # IUCN categories considered "rare" for bonus eligibility
    RARE_SPECIES_IUCN: str = "CR,EN,VU"
    # Active user window in hours
    ACTIVE_USER_WINDOW_HOURS: int = 24

    # Email / SMTP Configuration (Optional, falls back to safe mock delivery)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    EMAIL_FROM: str = "noreply@wildlife.gov.in"
    EMAIL_VERIFICATION_EXPIRY_MINUTES: int = 15
    EMAIL_RESEND_COOLDOWN_SECONDS: int = 60
    MAX_RESEND_ATTEMPTS: int = 5
    MAX_VERIFY_ATTEMPTS: int = 5

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

