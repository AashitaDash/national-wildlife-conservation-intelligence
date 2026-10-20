from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import init_db
from nlp.embeddings import VectorEmbedder

# Import Routers
from backend.app.routers import (
    auth,
    species,
    observations,
    documents,
    search,
    ml,
    dashboards,
    admin,
    chat
)
from backend.app.routers import submissions, officer, admin_platform, gamification, spatial, reports

app = FastAPI(
    title="Wildlife Conservation Intelligence Platform",
    description=(
        "Production-grade, AI-assisted conservation intelligence API integrating multi-source biodiversity "
        "telemetry (GBIF, iNaturalist, eBird), unstructured incident report NLP parsing, "
        "dense vector semantic search, Random Forest extinction vulnerability classification, "
        "and Isolation Forest spatial-temporal ecological anomaly detection."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware for React Vite / Web Frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits localhost:5173, localhost:3000 in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(species.router, prefix=settings.API_V1_PREFIX)
app.include_router(observations.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(search.router, prefix=settings.API_V1_PREFIX)
app.include_router(ml.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboards.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
# New RBAC workflow routers
app.include_router(submissions.router, prefix=settings.API_V1_PREFIX)
app.include_router(officer.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_platform.router, prefix=settings.API_V1_PREFIX)
app.include_router(gamification.router, prefix=settings.API_V1_PREFIX)
app.include_router(spatial.router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def on_startup():
    """Initialize database tables and seed reference data on application launch."""
    init_db()

    # Seed roles and badge catalog (idempotent)
    from backend.app.database import SessionLocal
    from backend.app.services.gamification_service import seed_badges, seed_roles
    import os
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with SessionLocal() as _db:
        seed_roles(_db)
        seed_badges(_db)

    # Preload the ML embedding model at startup so the first request doesn't block
    VectorEmbedder.preload_model()


@app.get("/", tags=["System Information"])
def root():
    return {
        "platform": "Wildlife Conservation Intelligence Platform",
        "version": "1.0.0",
        "api_documentation": "/docs",
        "status": "OPERATIONAL"
    }


@app.get("/health", tags=["System Information"])
def health_check():
    return {
        "status": "HEALTHY",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
