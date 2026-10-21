import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.config import settings

logger = logging.getLogger("wildlife_platform.database")
logging.basicConfig(level=logging.INFO)

Base = declarative_base()

# Attempt to connect to primary PostgreSQL engine
engine = None
SessionLocal = None
IS_POSTGRES = False

try:
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)

    pg_engine = create_engine(
        db_url,
        # Keep pool small — Render free tier allows max 25 connections total
        # across all services. With a single-worker uvicorn process, 3 is plenty.
        pool_size=3,
        max_overflow=2,        # Allow up to 5 total concurrent connections
        pool_timeout=30,       # Wait up to 30s for an available connection
        pool_recycle=1800,     # Recycle connections every 30 min (prevents stale TCP)
        pool_pre_ping=True,    # Verify connection liveness before use
        connect_args={
            "connect_timeout": 10,
        } if "psycopg" in db_url else {}
    )
    # Validate connectivity at startup
    with pg_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    engine = pg_engine
    IS_POSTGRES = True
    logger.info("Successfully connected to primary PostgreSQL database.")
except Exception as e:
    logger.warning(
        f"PostgreSQL connection failed ({type(e).__name__}: {e}). "
        f"Falling back to local SQLite database: {settings.FALLBACK_SQLITE_URL}."
    )
    engine = create_engine(
        settings.FALLBACK_SQLITE_URL,
        connect_args={"check_same_thread": False}
    )
    IS_POSTGRES = False

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """
    FastAPI dependency that provides a transactional database session per request.
    Closes the session automatically upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_extensions_and_tables():
    """
    Initializes database schema.
    For PostgreSQL, activates PostGIS and pgvector extensions if available.
    Creates all declarative tables registered under Base metadata.
    """
    if IS_POSTGRES:
        with engine.connect() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                conn.commit()
                logger.info("PostGIS extension verified.")
            except Exception as ex:
                logger.warning(f"Could not enable PostGIS extension: {ex}")

            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                logger.info("pgvector extension verified.")
            except Exception as ex:
                logger.warning(f"Could not enable pgvector extension: {ex}")

    # Create all tables defined in models
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")


# Alias for application startup lifecycle
init_db = setup_extensions_and_tables
