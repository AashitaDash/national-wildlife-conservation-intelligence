# Dependencies & Technology Stack

Both the backend and frontend stacks are fully listed in the repository.

## Backend (Python 3.12+)

| Dependency | Version (pinned) | Purpose |
|------------|------------------|---------|
| `fastapi` | >=0.111.0 | Web API framework |
| `uvicorn[standard]` | >=0.30.0 | ASGI server |
| `pydantic` | >=2.7.0 | Data validation |
| `sqlalchemy` | >=2.0.30 | ORM |
| `geoalchemy2` | >=0.14.0 | PostGIS support |
| `psycopg[binary]` | >=3.1.18 | PostgreSQL driver |
| `python‑jose[cryptography]` | >=3.3.0 | JWT handling |
| `passlib[bcrypt]` / `bcrypt` | >=1.7.4 / 4.1.0 | Password hashing |
| `scikit‑learn` | >=1.4.0 | ML models (RandomForest, IsolationForest) |
| `sentence‑transformers` | >=3.0.0 | 384‑dim embeddings |
| `torch` | >=2.2.0 | Underpinning for sentence‑transformers |
| `transformers` | >=4.41.0 | Optional language model utilities |
| `spacy` | >=3.7.0,<4.0.0 | NLP tokenisation & NER |
| `pandas`, `numpy`, `scipy` | >=2.2.0, 1.26.0, 1.13.0 | Data manipulation |
| `requests` | >=2.32.0 | HTTP client for external APIs |
| `python‑multipart` | >=0.0.9 | File upload handling |
| `pymupdf` | >=1.24.0 | PDF processing |
| `openpyxl` | >=3.1.2 | Excel import/export |
| `reportlab` | >=4.1.0 | PDF generation |
| `pytest` | >=8.2.0 | Test runner |

*All backend dependencies are declared in* `backend/requirements.txt`.

## Frontend (React 18, Vite)

```json
{
  "dependencies": {
    "axios": "^1.7.9",
    "leaflet": "^1.9.4",
    "lucide-react": "^0.469.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-leaflet": "^4.2.1",
    "react-router-dom": "^6.28.1",
    "recharts": "^2.15.0"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4.3.3",
    "@types/leaflet": "^1.9.14",
    "@types/node": "^22.10.2",
    "@types/react": "^18.3.18",
    "@types/react-dom": "^18.3.5",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.6.1",
    "postcss": "^8.5.28",
    "tailwindcss": "^3.4.19",
    "typescript": "^5.7.2",
    "vite": "^6.0.5"
  }
}
```

*All frontend dependencies live in* `frontend/package.json`.

## Database

- **PostgreSQL + PostGIS** (production) – spatial queries & geometry handling.
- **SQLite** (fallback for local development).

## Overall Stack Summary (as presented in the README)

| Layer | Technologies |
|-------|--------------|
| **Frontend** | React 18, Vite, Tailwind CSS, Leaflet |
| **Backend API** | FastAPI, SQLAlchemy, PostgreSQL/PostGIS |
| **NLP & Search** | spaCy, Sentence‑Transformers (`all‑MiniLM‑L6‑v2`), BM25 lexical fallback |
| **Machine Learning** | Scikit‑learn (RandomForestRegressor, IsolationForest) |
| **Auth & Security** | JWT, Passlib + bcrypt, role‑based RBAC |
| **Testing** | Pytest (unit & integration), Playwright (E2E) |
| **Containerisation / Deployment** | Docker (not part of the source but used in deployment scripts) |

---

All versions are taken directly from `backend/requirements.txt` and `frontend/package.json`; no versions have been inferred or fabricated.

