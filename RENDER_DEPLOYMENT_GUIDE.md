# Render Deployment Guide: National Wildlife Conservation Intelligence Platform (NWCIP)

This guide provides step-by-step instructions for deploying the **National Wildlife Conservation Intelligence Platform** on [Render](https://render.com).

---

## 🏗️ Architecture on Render

```mermaid
flowchart LR
    User[Client Browser] -->|HTTPS| Frontend[Render Static Site\nReact + Vite + Leaflet]
    Frontend -->|API calls\n/api/v1/*| Backend[Render Web Service\nFastAPI + Uvicorn + ML]
    Backend -->|SQLAlchemy + Psycopg| DB[(Render PostgreSQL 16\nPostGIS + pgvector)]
```

---

## 🚀 Option 1: Automatic Deployment via Blueprint (`render.yaml`)

The repository includes a ready-to-use [`render.yaml`](./render.yaml) Blueprint that defines all 3 services automatically:
1. `nwcip-postgres`: Managed PostgreSQL 16 database.
2. `nwcip-backend`: FastAPI Web Service with automated PostGIS initialization, health-check `/health`, and Sentence-Transformers / spaCy models.
3. `nwcip-frontend`: React Vite Static Site with SPA routing rules.

### Steps to Deploy:
1. Push this project to your GitHub or GitLab repository.
2. Log in to [dashboard.render.com](https://dashboard.render.com).
3. Click **New +** in the top navigation bar and select **Blueprint**.
4. Connect your Git repository containing the project.
5. Render will automatically detect [`render.yaml`](./render.yaml) and prompt you to create:
   - PostgreSQL Database: `nwcip-postgres`
   - Web Service: `nwcip-backend`
   - Static Site: `nwcip-frontend`
6. Click **Apply**.

---

## 🛠️ Option 2: Step-by-Step Manual Deployment

If you prefer to configure each service individually on Render, follow these steps:

### Step 1: Create the PostgreSQL Database
1. In Render Dashboard, click **New +** $\rightarrow$ **PostgreSQL**.
2. **Name:** `nwcip-postgres`
3. **Database:** `wildlife_db`
4. **User:** `wildlife_user`
5. **Region:** Choose Oregon (or Frankfurt) — ensure all services use the same region.
6. **Plan:** Starter (or standard).
7. Click **Create Database**.
8. Once created, click on the database and copy the **Internal Database URL** (e.g., `postgresql://wildlife_user:...@dpg-...-a:5432/wildlife_db`).
9. Under the database **Connect** $\rightarrow$ open `psql` (or use the Render web shell) and confirm extensions:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

---

### Step 2: Deploy the FastAPI Backend (Web Service)
1. Click **New +** $\rightarrow$ **Web Service**.
2. Connect your Git repository.
3. Configure the service:
   - **Name:** `nwcip-backend`
   - **Region:** Same as your database (e.g., Oregon).
   - **Environment:** `Python`
   - **Branch:** `main`
   - **Build Command:**
     ```bash
     pip install -r backend/requirements.txt && python -m spacy download en_core_web_sm
     ```
   - **Start Command:**
     ```bash
     uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Health Check Path:** `/health`
4. In the **Environment Variables** section, configure:
   | Key | Value / Source |
   |---|---|
   | `PYTHON_VERSION` | `3.11.9` |
   | `ENVIRONMENT` | `production` |
   | `DATABASE_URL` | Paste your Render **Internal Database URL** (replace `postgresql://` with `postgresql+psycopg://` if needed) |
   | `JWT_SECRET` | Click *Generate* (or enter a 32+ character random string) |
   | `JWT_ALGORITHM` | `HS256` |
   | `JWT_EXPIRE_MINUTES` | `1440` |
   | `EMBEDDING_MODEL_NAME`| `all-MiniLM-L6-v2` |
   | `EMBEDDING_DIMENSION` | `384` |
   | `CHAT_LLM_PROVIDER` | `extractive` |
5. Click **Deploy Web Service**.
6. When deployment finishes, copy your live backend URL (e.g., `https://nwcip-backend.onrender.com`).

---

### Step 3: Deploy the React / Vite Frontend (Static Site)
1. Click **New +** $\rightarrow$ **Static Site**.
2. Connect your Git repository.
3. Configure the static site:
   - **Name:** `nwcip-frontend`
   - **Region:** Same as backend.
   - **Branch:** `main`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`
4. In **Redirects / Rewrites**, add an SPA fallback route:
   - **Type:** `Rewrite`
   - **Source:** `/*`
   - **Destination:** `/index.html`
5. In **Environment Variables**, add:
   | Key | Value |
   |---|---|
   | `VITE_API_BASE_URL` | `https://your-backend-name.onrender.com/api/v1` |
6. Click **Create Static Site**.

---

## 🔒 Post-Deployment Verification Checklist

Once both services are active:
- [ ] Visit `https://your-backend.onrender.com/health` $\rightarrow$ should return `{"status":"HEALTHY","environment":"production"}`.
- [ ] Visit `https://your-backend.onrender.com/docs` $\rightarrow$ Swagger UI loads and lists all 30+ endpoints.
- [ ] Open the frontend URL $\rightarrow$ map tiles render, species catalog displays, and login works using seed credentials:
  - **Admin:** `admin@wildlife.gov.in` / `Admin@123`
  - **Officer:** `officer@forest.gov.in` / `Officer@123`
  - **Researcher:** `researcher@wildlife.gov.in` / `Researcher@123`
