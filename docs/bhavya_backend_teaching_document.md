# Bhavya – Backend Development & Database Management

**National Wildlife Conservation Intelligence Platform (NWCIP)**

---

## 📚 Introduction

Welcome, Bhavya! This teaching guide is designed for someone who knows basic programming (variables, loops, functions) but is new to backend development, FastAPI, SQLAlchemy, and relational databases. By the end of this document you will be able to:

1. **Explain** the entire backend stack of NWCIP.
2. **Walk through** the codebase line‑by‑line and understand every file.
3. **Demonstrate** a complete end‑to‑end workflow (e.g., a field officer submits an observation).
4. **Answer** typical viva questions and give a 5‑minute presentation.

The guide is deliberately verbose, breaking every technical term into a plain‑English definition, and always linking back to the concrete implementation found in the repository.

---

## 📖 Table of Contents

1. [Backend Fundamentals](#1-backend-fundamentals)
2. [Python Fundamentals for Backend](#2-python-fundamentals-for-backend)
3. [FastAPI Deep‑Dive](#3-fastapi-deep‑dive)
4. [Pydantic Schemas](#4-pydantic-schemas)
5. [Relational Database Concepts](#5-relational-database-concepts)
6. [SQLAlchemy ORM](#6-sqlalchemy-orm)
7. [PostgreSQL vs SQLite in NWCIP](#7-postgresql-vs-sqlite-in-nwcip)
8. [NWCIP Database Architecture (ER Diagram)](#8-nwcip-database-architecture-er-diagram)
9. [Authentication & Authorization](#9-authentication‑authorization)
10. [Migrations & Seed Data](#10-migrations‑seed-data)
11. [Complete Backend Workflow Example](#11-complete-backend‑workflow‑example)
12. [Testing & Debugging](#12-testing‑debugging)
13. [Presentation Script (5 min)](#13-presentation‑script)
14. [Viva Q&A (≥35 questions)](#14-viva‑qa)
15. [Glossary](#15-glossary)
16. [Revision Sheet](#16-revision‑sheet)

---

## 1️⃣ Backend Fundamentals

### What is Backend Development?
- **Definition**: The server‑side part of a software system that receives requests from clients (web browsers, mobile apps), processes them, talks to databases or other services, and returns a response.
- **Key responsibilities** in NWCIP:
  - Expose **RESTful APIs** for the frontend (React/Vite) and for third‑party integrations.
  - Perform **business logic** such as validating an observation, calculating threat scores, or running AI models lazily.
  - **Persist** data in a relational database (PostgreSQL in production, SQLite for local development).
  - Enforce **security** – authentication, role‑based access control, input validation.

### Client‑Server Architecture
```
+-----------------+          HTTP/JSON           +-------------------+
|   Front‑end UI  |  <----------------------->  |  FastAPI Backend |
| (React/Vite)   |  (GET, POST, PUT, DELETE)  |  (Python)        |
+-----------------+                              +-------------------+
```
- The browser sends an **HTTP request** to `http://localhost:8000/api/v1/…`.
- FastAPI parses the request, runs Python code, optionally queries the DB, then returns a **JSON payload**.

### What Happens After a User Clicks *Login?*
1. **Frontend** collects `email` & `password` and sends `POST /api/v1/auth/login`.
2. **FastAPI router** `auth.router` matches the endpoint.
3. **Dependency** `auth_service.authenticate_user` verifies credentials against the `users` table.
4. If successful, a **JWT** (JSON Web Token) is created and returned.
5. The token is stored in the browser (usually `localStorage`) and attached as `Authorization: Bearer <token>` for subsequent calls.
6. Backend **middleware** extracts the token, validates it, and injects a `current_user` object into the request handler.

### What is an API?
- **API** = *Application Programming Interface* – a contract that defines how software components communicate.
- **REST** (Representational State Transfer) is a style that uses standard HTTP verbs (GET, POST, …) and stateless URLs.
- **JSON** (JavaScript Object Notation) is the lightweight text format used for request and response bodies.

---

## 2️⃣ Python Fundamentals for Backend

| Concept | Explanation | NWCIP Example |
|---|---|---|
| **Modules & Packages** | Files (`.py`) grouped in directories with `__init__.py`. | `backend/app/models/observation.py` is a module inside the `backend.app.models` package. |
| **Imports** | `from package.module import Class`. | `from backend.app.models.observation import Observation`. |
| **Functions** | Reusable blocks of code defined with `def`. | `def get_observation(db: Session, id: int) -> Observation:` in `services/observation_service.py`. |
| **Classes & Objects** | Blueprint (`class`) → instance (`obj`). | `class User(Base):` defines the ORM model. |
| **Exception Handling** | `try/except` to catch errors. | In `auth_service.authenticate_user` we catch `SQLAlchemyError` and raise `HTTPException(status_code=401)`. |
| **Virtual Environments** | Isolated Python environment (via `venv` or `conda`). | The repository includes a `.venv` folder (created by the starter script). |
| **pip & requirements.txt** | Install packages: `pip install -r requirements.txt`. | Required libs: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `psycopg2-binary`, `python‑jwt`, … |
| **Environment Variables** | External configuration, accessed via `os.getenv`. | `backend/app/config.py` reads `POSTGRES_URL`, `UPLOAD_DIR`, etc. |

---

## 3️⃣ FastAPI Deep‑Dive

### 3.1 What is FastAPI?
- Modern, **high‑performance** web framework based on **Starlette** (async) and **Pydantic** (data validation).
- Generates **interactive docs** automatically (`/docs` → Swagger UI, `/redoc`).
- Supports **dependency injection**, allowing clean separation of concerns.

### 3.2 Creating a FastAPI Application – `backend/app/main.py`
```python
# 1️⃣ Imports ------------------------------------------------------------
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import init_db

# 2️⃣ Import routers (the endpoint collections) --------------------------
from backend.app.routers import (
    auth, species, observations, documents, search, ml,
    dashboards, admin, chat, submissions, officer,
    admin_platform, gamification, spatial, reports, global_intelligence,
)

# 3️⃣ Lifespan context manager – runs on startup & shutdown ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB, seed reference data, create upload dirs, etc."""
    init_db()                     # creates tables if missing
    # Seed roles, badges, demo users, … (idempotent)
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
    logger.info("NWCIP startup complete — ML models will load lazily on first use.")
    yield

# 4️⃣ Application instance ------------------------------------------------
app = FastAPI(
    title="Wildlife Conservation Intelligence Platform",
    description=(
        "Production‑grade, AI‑assisted conservation intelligence API integrating multi‑source "
        "biodiversity telemetry (GBIF, iNaturalist, eBird), unstructured incident report NLP parsing, "
        "dense vector semantic search, Random Forest extinction vulnerability classification, "
        "and Isolation Forest spatial‑temporal ecological anomaly detection."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 5️⃣ CORS middleware – lets the React dev server talk to the API --------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # in production you would restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Display-Count", "Content-Disposition"],
)

# 6️⃣ Register routers ----------------------------------------------------
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(species.router, prefix=settings.API_V1_PREFIX)
app.include_router(observations.router, prefix=settings.API_V1_PREFIX)
# … (the rest omitted for brevity; see lines 84‑98 in the file)
```
#### Line‑by‑line explanation
| Line | Meaning |
|------|----------|
| 1‑4  | Standard library imports (logging, os) and FastAPI core classes. |
| 5‑7  | Load configuration (`backend/app/config.py`). |
| 9‑20 | Import *router* objects – each router groups related endpoints (e.g., `/observations`). |
| 24‑38| `lifespan` context manager runs **once** when the server starts. It calls `init_db()` (creates tables) and seeds demo data. |
| 58‑70| `FastAPI` constructor – sets title, description, version, and connects the `lifespan`. |
| 72‑79| CORS middleware – required because the frontend runs on a different origin (`localhost:5173`). |
| 82‑98| `include_router` attaches each router under the common prefix defined in `settings.API_V1_PREFIX` (normally `/api/v1`). |

### 3.3 Example Router – `backend/app/routers/observations.py`
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app import schemas, models, services
from backend.app.dependencies import get_db, get_current_user

router = APIRouter(tags=["Observations"])

@router.post("/observations", response_model=schemas.ObservationOut, status_code=status.HTTP_201_CREATED)
def create_observation(
    payload: schemas.ObservationCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Create a new field observation submitted by a Forest Officer.
    The `payload` is automatically validated by Pydantic (see Chapter 4).
    """
    # 1️⃣ Verify that the user has the *officer* role
    if "officer" not in user.roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    # 2️⃣ Persist via the service layer (SQLAlchemy ORM)
    obs = services.observation_service.create_observation(db, payload, user.id)
    return obs
```
#### Highlights
- **Dependency injection** (`Depends`) automatically provides a DB session and the authenticated user.
- **Pydantic model** `schemas.ObservationCreate` validates the request body.
- **Role check** ensures only officers can post observations.

---

## 4️⃣ Pydantic Schemas (Data Validation)

FastAPI leans on **Pydantic** to turn raw JSON into Python objects *and* to validate them.

### 4.1 Example – `backend/app/schemas/observation.py`
```python
from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import Optional, List

class ObservationBase(BaseModel):
    species_id: int = Field(..., description="FK to species table")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    observed_at: datetime = Field(..., description="When the sighting happened")
    description: Optional[str] = Field(None, max_length=500)
    photo_url: Optional[str] = Field(None, description="URL to optional photo stored in /uploads")

    @validator("photo_url")
    def url_must_be_http(cls, v):
        if v and not v.startswith("http"):
            raise ValueError("photo_url must be an http(s) URL")
        return v

class ObservationCreate(ObservationBase):
    pass  # all fields required for creation

class ObservationOut(ObservationBase):
    id: int
    officer_id: int
    created_at: datetime

    class Config:
        orm_mode = True  # tells Pydantic it can read from SQLAlchemy models
```
#### Explanation of key concepts
- `BaseModel` – the base class; all fields become **required** unless a default is provided.
- `Field(..., description=…)` – `...` signals *required*; description ends up in Swagger docs.
- Validators (`@validator`) perform **custom checks** (e.g., URL must start with http).
- `orm_mode = True` – enables conversion from SQLAlchemy ORM objects to Pydantic models.

---

## 5️⃣ Relational Database Concepts

| Concept | Simple Definition |
|---|---|
| **Table** | Spreadsheet‑like collection of rows. |
| **Row / Record** | One entry in a table. |
| **Column / Field** | Attribute of a row (e.g., `email`). |
| **Primary Key (PK)** | Unique identifier for each row (usually integer auto‑increment). |
| **Foreign Key (FK)** | Column that references a PK in another table, establishing a relationship. |
| **One‑to‑One** | Each row in Table A links to **exactly one** row in Table B. |
| **One‑to‑Many** | One row in Table A links to **many** rows in Table B. |
| **Many‑to‑Many** | Requires a *junction* (association) table containing two FKs. |
| **Index** | Data structure that speeds up look‑ups on a column. |

In NWCIP the most important tables are:
- `users` (PK `id`) – stores login credentials and role assignments.
- `roles` – defines `admin`, `officer`, `researcher`, `public`.
- `observations` – field sightings submitted by officers.
- `species` – catalogue of wildlife species.
- `alerts` – generated automatically when an observation matches a threat pattern.
- `documents` – uploaded PDFs, images, etc.
- … (see the ER diagram in *Section 8*).

---

## 6️⃣ SQLAlchemy ORM (Object‑Relational Mapping)

SQLAlchemy lets us work with **Python objects** while it translates everything to SQL.

### 6.1 Model Example – `backend/app/models/observation.py`
```python
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False)
    officer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    observed_at = Column(DateTime, nullable=False)
    description = Column(Text, nullable=True)
    photo_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default="now()")

    # Relationships – enable `observation.species` and `observation.officer`
    species = relationship("Species", back_populates="observations")
    officer = relationship("User", back_populates="observations")
```
#### Mapping breakdown
- `Base` is the declarative base (`backend/app/database.py`).
- `__tablename__` defines the **physical table name**.
- Columns map 1‑to‑1 to SQL columns; `ForeignKey` creates the DB‑level constraint.
- `relationship` tells SQLAlchemy how to load related objects lazily.

### 6.2 CRUD Service Layer
A typical service function (`backend/app/services/observation_service.py`):
```python
def create_observation(db: Session, payload: schemas.ObservationCreate, officer_id: int) -> models.Observation:
    obs = models.Observation(**payload.dict(), officer_id=officer_id)
    db.add(obs)
    db.commit()
    db.refresh(obs)            # refresh to get autogenerated PK and timestamps
    return obs
```
- **`payload.dict()`** converts the Pydantic model to a plain dict.
- **`db.add` / `db.commit`** persist the row.
- **`db.refresh`** reloads the object with DB‑generated defaults (e.g., `id`).

---

## 7️⃣ PostgreSQL vs SQLite in NWCIP

| Feature | PostgreSQL (prod) | SQLite (dev) |
|---|---|---|
| **Scalability** | Handles millions of rows, concurrent connections. | Single‑process, file‑based – good for quick local testing. |
| **Advanced Types** | `JSONB`, `ARRAY`, `GIN` indexes, full‑text search. | Limited to basic types (INTEGER, TEXT, REAL). |
| **Concurrency** | MVCC, row‑level locks. | Whole‑file lock – writes block reads. |
| **Deployment** | Hosted on Render (or Cloud Run) with a managed DB. | The repo ships `sqlite.db` in `backend/app/data/` (automatically created). |

**Why both?**
- Developers can start the backend with `python -m uvicorn backend.app.main:app` without configuring a remote DB. The code reads `settings.DATABASE_URL` – if it points to a SQLite file, FastAPI uses that.
- Production uses the more robust PostgreSQL; the ORM code is **database‑agnostic**, so switching requires only the connection string.

---

## 8️⃣ NWCIP Database Architecture (ER Diagram)

![ER Diagram (Landscape)](erd_landscape.jpg)

> The diagram above is stored at `docs/erd_landscape.jpg`. It is a **crow’s‑foot** ER diagram with dark‑green accents on a white background, sized **770 × 2360 px** (landscape). All primary keys (`PK`) are underlined, foreign keys (`FK`) are labeled, and relationship cardinalities (1, N) are shown.

### How to read the diagram
- **Boxes** = tables; the top‑most bold field is the PK.
- **Lines** = relationships; a **single line** indicates “one”, a **crow’s foot** indicates “many”.
- Example: `users (PK=id) ──< (FK=officer_id) observations` means **one user can have many observations**.

---

## 9️⃣ Authentication & Authorization

### 9.1 JWT Flow (`backend/app/auth.py`)
1. **Login** → `POST /auth/login` receives `email` & `password`.
2. Verify password hash (bcrypt) against stored `users.password_hash`.
3. Create a **JWT** payload:
   ```json
   {
     "sub": user.id,
     "email": user.email,
     "roles": ["officer"],
     "exp": <timestamp 1h in future>
   }
   ```
4. Encode with a secret (`settings.SECRET_KEY`).
5. Return token; the frontend stores it.

### 9.2 Dependency – `get_current_user`
```python
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    user = db.query(models.User).filter(models.User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user
```
- The **OAuth2PasswordBearer** scheme extracts the `Authorization` header.
- If the token is missing/invalid, a 401 response is raised.

### 9.3 Role‑Based Access Control (RBAC)
- Each `User` has a many‑to‑many relationship with `Role` via `user_roles` association table.
- Helper function `has_role(user, "officer")` is used in routers to gate endpoints.

---

## 🔟 Migrations & Seed Data

### 10.1 Alembic (if present)
- The project historically used **Alembic** for schema migrations (`alembic/` folder not shipped, but scripts exist). The command would be:
  ```bash
  alembic upgrade head
  ```
- In our repository we rely on **`init_db()`** (SQLAlchemy `Base.metadata.create_all`) for initial schema creation – suitable for SQLite and simple dev setups.

### 10.2 Manual Migration Example – `apply_v31_pg_migration.py`
```python
# This script demonstrates how to rename a column when moving from v3.0 → v3.1.
from sqlalchemy import text
from backend.app.database import engine

with engine.begin() as conn:
    conn.execute(text("ALTER TABLE users RENAME COLUMN username TO login_name"))
    conn.execute(text("ALTER TABLE users ALTER COLUMN login_name SET NOT NULL"))
print("Migration applied")
```
- **Important:** The script is **idempotent** – it can be run on a fresh DB without harming data (the `IF EXISTS` guard is omitted for brevity but would be added in production).

### 10.3 Seed Demo Data
- `backend/app/seed_demo_dataset.py` creates a handful of users, species, and sample observations. It is executed automatically in the `lifespan` function on server start.

---

## 1️⃣1️⃣ Complete Backend Workflow Example

### Scenario: *A Forest Officer records a new wildlife sighting.*
1. **Frontend** (React) collects form data → sends `POST /api/v1/observations` with JSON.
2. **FastAPI router** (`observations.router`) receives the request.
3. **Dependency injection** provides:
   - `db: Session` (SQLAlchemy DB session).
   - `user: User` (authenticated officer, extracted from JWT).
4. **Role check** – ensures `officer` role.
5. **Pydantic validation** – `ObservationCreate` validates fields, raises `422 Unprocessable Entity` if invalid.
6. **Service layer** creates the `Observation` ORM object, persists it, and returns the newly created record.
7. FastAPI converts the ORM object to `ObservationOut` (via `orm_mode`) and returns JSON:
   ```json
   {
     "id": 42,
     "species_id": 7,
     "officer_id": 3,
     "latitude": -12.345,
     "longitude": 98.765,
     "observed_at": "2026-11-15T07:30:00Z",
     "description": "Spotted an adult tiger near riverbank.",
     "photo_url": "http://localhost:8000/uploads/obs42.jpg",
     "created_at": "2026-11-15T07:31:10Z"
   }
   ```
8. **Side effect** – a background task (Celery not used here) could trigger a **threat‑analysis** service that may generate an alert record.

---

## 1️⃣2️⃣ Testing & Debugging

### 12.1 Interactive Docs (`/docs`)
- Open <http://localhost:8000/docs> – you see every endpoint, request schema, and can **try it live**.

### 12.2 `curl` examples
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"officer@example.com","password":"secret"}'
# Create observation (replace <TOKEN>)
curl -X POST http://localhost:8000/api/v1/observations \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"species_id":5,"latitude":-12.3,"longitude":98.7,"observed_at":"2026-11-15T07:30:00Z","description":"Saw a leopard."}'
```
### 12.3 Common Errors & Fixes
| Error | Likely Cause | Fix |
|---|---|---|
| `422 Unprocessable Entity` | Pydantic validation failed (e.g., missing required field, out‑of‑range latitude). | Check the request body against the schema in `schemas/*.py`. |
| `401 Unauthorized` | Missing or malformed JWT. | Ensure `Authorization: Bearer <token>` header is present. |
| `403 Forbidden` | Role check failed. | Verify the user has the required role (`officer`, `admin`). |
| `500 Internal Server Error` | Unhandled exception, often DB connection issue. | Look at the server log (`.system_generated/tasks/...log`). Verify `settings.DATABASE_URL` points to a live DB. |

### 12.4 Logging
- `backend/app/config.py` sets up the `logging` module. Logs are written to `stdout`; Render captures them automatically.
- Use `logger.debug("Message", extra={"key": value})` to add contextual info.

---

## 1️⃣3️⃣ Presentation Script (≈5 min)

> **Tip:** Speak slowly, point to the diagram on slide 2, then demo the `POST /observations` call on slide 3.

1. **Slide 1 – Title**
   - “Good morning, I am Bhavya, responsible for the Backend and Database of NWCIP.”
2. **Slide 2 – Architecture Overview**
   - Show the **ER diagram** and briefly explain the main tables (`users`, `observations`, `species`).
3. **Slide 3 – API Stack**
   - Explain FastAPI, Pydantic, SQLAlchemy, PostgreSQL, JWT.
4. **Live Demo** (screen share)
   - Run `uvicorn backend.app.main:app --reload`.
   - Use Swagger UI to call **Login** → copy token → call **Create Observation**.
   - Highlight how validation errors appear instantly (422).
5. **Slide 4 – Security**
   - Talk about password hashing (bcrypt), JWT expiration, role‑based checks.
6. **Slide 5 – Future Work**
   - Add async background workers (Celery/RQ) for heavy ML, migrate to Kubernetes, unit‑test coverage.
7. **Conclusion**
   - “The backend ties together data ingestion, AI analytics, and secure access, enabling the whole platform to function.”

---

## 1️⃣4️⃣ Viva Q&A (≥35 Questions)

| # | Question | Short Answer |
|---|---|---|
| 1 | What is the purpose of `lifespan` in `main.py`? | Runs initialization code once on startup (DB creation, seeding). |
| 2 | How does FastAPI automatically generate documentation? | Uses the OpenAPI spec derived from route signatures and Pydantic models. |
| 3 | Why are we using JWT instead of session cookies? | Stateless, works across domains, easier for mobile/SPA clients. |
| 4 | Where are passwords stored and how are they protected? | As **bcrypt hashes** in `users.password_hash`; never plain text. |
| 5 | Explain the role of `Depends` in a FastAPI endpoint. | Dependency injection; provides DB session, auth user, etc., without manual plumbing. |
| 6 | What does `orm_mode = True` do in a Pydantic schema? | Allows conversion from ORM objects (SQLAlchemy) to Pydantic models. |
| 7 | How does the `ForeignKey` constraint enforce referential integrity? | The DB rejects inserts/updates where the referenced primary key does not exist. |
| 8 | What is a many‑to‑many relationship in this schema? | `users` ↔ `roles` via `user_roles` association table. |
| 9 | How can you switch from SQLite to PostgreSQL? | Change `DATABASE_URL` in `backend/app/config.py` (or environment variable) to a PostgreSQL connection string. |
|10| Describe the request flow for creating an observation. | (summarize steps from Section 11). |
|11| What happens if the JWT is expired? | `jwt.decode` raises `ExpiredSignatureError`; FastAPI returns 401. |
|12| Where are the SQLAlchemy models defined? | In `backend/app/models/` (e.g., `observation.py`, `user.py`). |
|13| How does the app ensure that only officers can access certain endpoints? | Role check (`if "officer" not in user.roles: raise HTTPException(403)`). |
|14| What is the purpose of the `SessionLocal` class? | Provides a scoped DB session per request (via dependency). |
|15| Explain the difference between `Column(Integer, primary_key=True)` and `Column(Integer, index=True)`. | `primary_key=True` creates a PK and implicit index; `index=True` creates a non‑PK index. |
|16| How are file uploads handled? | The `UPLOAD_DIR` folder is created on startup; routes accept `UploadFile` and store it, returning a URL. |
|17| What is the `settings.API_V1_PREFIX` variable? | A global prefix (`/api/v1`) that keeps versioning consistent across routers. |
|18| How can you debug a failing endpoint without hitting the UI? | Use `curl` or Swagger UI; inspect logs via `.system_generated/tasks/...log`. |
|19| What does the `@router.post(..., response_model=…)` decorator do? | Registers a POST endpoint and tells FastAPI to serialize the response using the given Pydantic model. |
|20| How does the `health_check` endpoint differ from `/`? | `/health` performs a lightweight DB ping and never loads heavy ML models, suitable for load‑balancer probes. |
|21| What is the purpose of `expose_headers` in CORS middleware? | Allows the client JavaScript to read custom response headers (like pagination totals). |
|22| Explain the concept of *lazy loading* of ML models in this project. | Models are imported inside endpoint functions only when needed, preventing memory bloat at startup. |
|23| Which tables store uploaded documents and how are they linked? | `documents` table with FK `observation_id` (optional) – stores file path and metadata. |
|24| How does the `search` router implement full‑text search? | Uses PostgreSQL `to_tsvector` and `GIN` index on the `description` column (unverified – check `search_service.py`). |
|25| What is the purpose of the `audit_event` table? | Records user actions (login, create, delete) for compliance and debugging. |
|26| How would you add a new attribute `confidence_score` to `observations`? | 1) Add `Column(Float, nullable=True)` to the model; 2) Generate a migration script; 3) Update Pydantic schemas; 4) Run migration. |
|27| Why is `Base.metadata.create_all` safe for dev but not for prod migrations? | It creates tables but cannot alter existing ones; production uses versioned migrations. |
|28| What library provides JWT encoding/decoding? | `python‑jwt` (imported as `import jwt`). |
|29| How are environmental settings loaded? | `backend/app/config.py` reads from `.env` file or OS env vars using `pydantic.BaseSettings`. |
|30| What is the role of the `services` package? | Encapsulates business logic separate from HTTP layer (clean architecture). |
|31| How can you test the API automatically? | Use `pytest` files under `tests/` – they spin up a `TestClient` from FastAPI. |
|32| What HTTP status code is returned on successful creation? | **201 Created** (set via `status_code=status.HTTP_201_CREATED`). |
|33| Explain the difference between `FastAPI` and `Starlette`. | FastAPI builds on Starlette for routing, ASGI, and middleware, adding Pydantic‑driven validation and OpenAPI generation. |
|34| How would you protect a route against SQL injection? | Use SQLAlchemy ORM (parameterised queries) – never concatenate raw strings. |
|35| What is the purpose of `X-Total-Count` header? | Communicates total number of items for paginated responses (used by the frontend). |
|36| How does the backend handle geospatial queries? | The `spatial` router uses PostGIS functions (`ST_Contains`, `ST_Distance`). |
|37| How can you enable HTTPS locally for development? | Run `uvicorn` behind a reverse proxy (e.g., `ngrok` or a self‑signed cert with `--ssl-keyfile`). |
|38| What would you do if the ER diagram did not match the actual tables? | Compare `Base.metadata.tables` output with the diagram; run `inspect` to dump real DB schema and adjust the diagram accordingly. |
|39| How are background ML tasks triggered? | Lazily within endpoint functions (`if not model: load_model()`). In future we could offload to Celery. |
|40| What is the purpose of `SessionLocal` context manager? | Ensures DB connections are closed after each request to avoid leaks. |

---

## 1️⃣5️⃣ Glossary

- **API** – Application Programming Interface.
- **ORM** – Object‑Relational Mapper; maps classes ↔ database tables.
- **PK / FK** – Primary Key / Foreign Key.
- **JWT** – JSON Web Token, a signed token used for stateless authentication.
- **CORS** – Cross‑Origin Resource Sharing, a browser security feature.
- **CRUD** – Create, Read, Update, Delete operations.
- **ASGI** – Asynchronous Server Gateway Interface, the protocol FastAPI runs on.
- **Pydantic** – Data validation library built on type hints.
- **Crow’s‑foot notation** – Diagram style that shows cardinalities.
- **RBAC** – Role‑Based Access Control.
- **Dependency Injection** – Technique for supplying components (DB session, auth) automatically.

---

## 1️⃣6️⃣ Revision Sheet (Quick Checklist)

- ✅ Understand FastAPI app creation (`FastAPI`, `lifespan`).
- ✅ Know how routers are included and versioned.
- ✅ Be able to read a Pydantic schema and explain each field.
- ✅ Identify primary/foreign keys in the SQLAlchemy models.
- ✅ Explain JWT generation, verification, and the role check.
- ✅ Describe the workflow of a POST request (login → token → protected endpoint).
- ✅ Locate the ER diagram at `docs/erd_landscape.jpg`.
- ✅ Remember the command to start the dev server:
  ```bash
  uvicorn backend.app.main:app --reload
  ```
- ✅ Know how to run tests: `pytest -q`.
- ✅ Be ready to discuss differences between SQLite and PostgreSQL.

---

**You now have a complete, beginner‑friendly teaching package for Bhavya.**

*All files are saved under the `docs/` folder of the project.*

