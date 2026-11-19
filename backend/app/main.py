import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import init_db

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
from backend.app.routers import submissions, officer, admin_platform, gamification, spatial, reports, global_intelligence

logger = logging.getLogger("wildlife_platform.main")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize database schema and seed reference data.

    Memory discipline:
    - Heavy ML models (SentenceTransformer, sklearn) are NOT loaded here.
      They initialize lazily on first feature request.
    - Seeding is idempotent and exits immediately when data already exists.
    - No background warmup threads: on Render's 512 MB free tier, loading
      SentenceTransformer immediately after PyTorch/spaCy/seed have been
      imported pushes resident memory past the OOM threshold.
    """
    init_db()

    # Idempotent data seeding — exits instantly when data already exists
    from backend.app.database import SessionLocal
    from backend.app.services.gamification_service import seed_badges, seed_roles
    from backend.app.seed_demo_dataset import seed_demo_users, seed_demo_submissions
    from backend.app.services.seed_service import seed_biodiversity_dataset

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with SessionLocal() as _db:
        seed_roles(_db)
        seed_badges(_db)
        users = seed_demo_users(_db)
        seed_biodiversity_dataset(_db)
        seed_demo_submissions(_db, users)

    # ---------- Scheduler registration ----------
    from backend.app.services.sync.sync_manager import SyncScheduler
    scheduler = SyncScheduler(app)
    # Store on app.state so other components could access if needed
    app.state.sync_scheduler = scheduler
    # Start background sync tasks (non‑blocking)
    await scheduler.start()

    logger.info("NWCIP startup complete — ML models will load lazily on first use.")
    yield
    # On shutdown: gracefully stop the scheduler
    await app.state.sync_scheduler.shutdown()

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
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware for React Vite / Web Frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Display-Count", "Content-Disposition"],
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
app.include_router(submissions.router, prefix=settings.API_V1_PREFIX)
app.include_router(officer.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_platform.router, prefix=settings.API_V1_PREFIX)
app.include_router(gamification.router, prefix=settings.API_V1_PREFIX)
try:
    from backend.app.routers import spatial
    from backend.app.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("SELECT PostGIS_Full_Version();"))
    app.include_router(spatial.router, prefix=settings.API_V1_PREFIX)
except Exception as e:
    logger.warning(f"PostGIS not available ({e}), using fallback spatial router")
    from backend.app.routers.spatial_fallback import router as spatial_fallback_router
    app.include_router(spatial_fallback_router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)
app.include_router(global_intelligence.router, prefix=settings.API_V1_PREFIX)




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
    """
    Lightweight liveness probe used by Render health checks.
    Does NOT load ML models or run database queries — returns instantly
    so Render does not time out while models are being initialized.
    """
    from backend.app.database import engine
    db_ok = False
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        logger.warning(f"Health check: database ping failed: {exc}")

    return {
        "status": "HEALTHY" if db_ok else "DEGRADED",
        "database": "connected" if db_ok else "unavailable",
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

