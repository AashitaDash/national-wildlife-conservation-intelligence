# Project Overview

**National Wildlife Conservation Intelligence Platform (NWCIP)**

- **Purpose**: An AI‑assisted decision‑support system that integrates biodiversity telemetry, unstructured conservation documents, machine‑learning risk scoring, and interactive GIS to help wildlife authorities and NGOs monitor and protect Indian wildlife.
- **Scope**: Multi‑source ingestion (GBIF, iNaturalist, eBird, field submissions), NLP extraction, hybrid search, risk & anomaly ML models, and a role‑based React/Leaflet front‑end.
- **Academic Context**: Final‑year B.Tech Computer Science capstone project.
- **Key Functional Modules** (see README `## 🚀 Key Functional Modules`):
  1. **Geospatial Telemetry & Sighting Ingestion**
  2. **NLP Conservation Intelligence**
  3. **Machine‑Learning Risk & Anomaly Engine**
  4. **Role‑Based Access Control (RBAC)**
  5. **Interactive GIS Front‑end**
- **Technology Stack** (excerpt from README `## 🛠️ Technology Stack`):
  - Front‑end: React 18, Vite, Tailwind CSS, Leaflet, Recharts.
  - Back‑end: FastAPI, Python 3.12+, SQLAlchemy 2.0, PostgreSQL + PostGIS (fallback SQLite).
  - NLP: spaCy, Sentence‑Transformers (`all‑MiniLM‑L6‑v2`), Sumy LSA.
  - ML: scikit‑learn (RandomForestRegressor, IsolationForest).
- **Demo Personas & Credentials** are listed in the README under `## 🔑 Demo Personas & Seed Credentials`.

---

*All information above is directly extracted from the repository files (`README.md`, source code in `backend/app/routers`, `backend/app/models`, `frontend/src/App.tsx`).*

