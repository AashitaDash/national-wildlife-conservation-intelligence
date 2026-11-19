# Backend Architecture

NWCIP’s backend is a **FastAPI** application written in Python 3.12+. It follows a modular layout under `backend/app/`.

## Core Packages
- **`main.py`** – creates the FastAPI instance, includes routers, and registers middleware (CORS, authentication). 
- **`dependencies.py`** – helper functions for DB session (`get_db`), user retrieval (`get_current_user`), and RBAC (`require_roles`).
- **`config.py`** – loads environment variables via `pydantic.BaseSettings` (DB URL, JWT secret, model paths, etc.).
- **`database.py`** – SQLAlchemy `engine` and `Base` declarative base; supports PostgreSQL + PostGIS (production) and SQLite fallback.

## Routers (API Groups)
| Router file | Prefix | Purpose |
|------------|--------|----------|
| `auth.py` | `/auth` | Registration, login, JWT issuance, email verification. |
| `admin.py` | `/admin` | User management, role changes, system‑health diagnostics. |
| `spatial.py` | `/spatial` | State‑wise biodiversity metrics, choropleth data, fuzzy coordinate handling. |
| `observations.py` | `/observations` | CRUD for wildlife sighting records. |
| `species.py` | `/species` | Species catalogue, taxonomy lookup. |
| `documents.py` | `/documents` | Upload & retrieve unstructured NLP documents. |
| `ml.py` | `/ml` | ML risk‑score and anomaly endpoints. |
| `search.py` | `/search` | Hybrid lexical‑semantic search service. |
| `global_intelligence.py` | `/global_intelligence` | Aggregated threat intelligence dashboards. |
| `admin_platform.py` | `/admin_platform` | Admin UI specific helpers (audit logs, badges). |
| `officer.py`, `reports.py`, `dashboards.py`, `chat.py`, `gamification.py` – auxiliary functional areas.

All routers are imported in `main.py` with:
```python
app.include_router(auth.router)
app.include_router(admin.router)
# …etc.
```

## Services Layer
Business logic lives in `backend/app/services/` (e.g., `auth_service.py`, `nlp_intelligence.py`, `rag_service.py`, `ml_outputs`, `search_service.py`). Each service is called from the corresponding router, keeping endpoint functions thin.

## Example Service Call (RAG)
```python
from backend.app.services.rag_service import RAGService

@router.post("/rag/query", response_model=RAGResponse)
def rag_query(req: RAGRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return RAGService.answer_query(db, req.question, user.id)
```

The service handles retrieval, context construction, and LLM inference (model abstracted behind a function).

## Error Handling & Logging
- Centralised `logger = logging.getLogger(__name__)` used across modules.
- HTTPExceptions with appropriate status codes (`401`, `403`, `404`, `400`).
- Audit logs recorded via `AuditService.log` for privileged actions.

All file names and paths referenced above exist under `backend/app/`.

---
*Information is drawn directly from source files (`main.py`, `dependencies.py`, router modules, and service implementations). No code was altered.*
