# RAG-Based Wildlife Conservation Assistant — Setup & Verification Guide

This document describes the Retrieval-Augmented Generation (RAG) AI Assistant integrated into the Wildlife Conservation Intelligence Platform.

---

## 1. Architecture Overview

The assistant implements an end-to-end grounded query pipeline:

```
User Query
  │
  ▼
[Query Preprocessing & Intent Detection]
  │ (TAXONOMIC_QUERY | CONSERVATION_RISK | SPATIAL_OBSERVATION | DOCUMENT_RESEARCH)
  ▼
[Hybrid Multi-Source Retrieval]
  ├─ 1. PostgreSQL Database Telemetry (SQLAlchemy)
  │     • Species registry & taxonomy
  │     • Official IUCN conservation status
  │     • Documented observation counts & lat/lon bounding envelopes
  │     • ML Extinction Risk Classification & Isolation Forest anomalies
  ├─ 2. Research Document Corpus
  │     • 384-dimensional dense vectors (`all-MiniLM-L6-v2` via `nlp.embeddings.VectorEmbedder`)
  │     • Lexical BM25 keyword matching
  │     • FastText-style deterministic hash vector fallback
  └─ 3. Authoritative External Data (Optional)
        • Live GBIF / iNaturalist references where supported
  │
  ▼
[Context Assembly & Prompt Guardrails]
  • Untrusted external snippet isolation
  • Defense against prompt injection
  ▼
[Configurable LLM Generation Engine]
  • Primary: Local Ollama model / Cloud LLM via backend service
  • Fallback: High-fidelity deterministic extractive synthesis (zero hallucination, offline capable)
  ▼
[Citation Validation & Structured Response]
  • Inline citations ([S1], [S2]) mapped directly to retrieved evidence items
```

---

## 2. Configuration & Environment Variables

All settings are configured via environment variables and loaded into `backend/app/config.py`:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `CHAT_LLM_PROVIDER` | `"auto"` | Provider to use: `"ollama"`, `"cloud"`, or `"auto"` (falls back to extractive synthesizer) |
| `CHAT_LLM_MODEL` | `"llama3.2:latest"` | Model identifier for Ollama or Cloud API |
| `CHAT_LLM_API_KEY` | `""` | Optional API key for cloud LLM services |
| `OLLAMA_BASE_URL` | `"http://localhost:11434"` | Base URL for local Ollama server |
| `CHAT_LLM_TIMEOUT_SECONDS` | `15` | Request timeout before falling back to extractive synthesis |
| `CHAT_LLM_MAX_TOKENS` | `1024` | Maximum tokens for generation |

> **Graceful Failure Guarantee:** If `CHAT_LLM_API_KEY` is absent or the Ollama daemon is offline, application startup is **never blocked**. The system transparently falls back to the deterministic, cited extractive synthesis engine.

---

## 3. Grounding & Anti-Hallucination Guardrails

1. **Strict Evidence Grounding:** The assistant will not invent scientific names, IUCN statuses, observation counts, or coordinates.
2. **Predictive Model Demarcation:** Platform-generated ML risk scores are explicitly marked as predictive indicators, never conflated with official IUCN extinction determinations.
3. **Refusal on Insufficient Evidence:** If retrieval matches no records, the system responds:
   > *"The available platform data does not contain sufficient verified evidence to answer this question. Please refine your query or check available species in the registry."*
4. **Prompt Injection Defense:** Retrieved document snippets are sanitized and treated as untrusted data in the generation engine to ignore adversarial instructions.
5. **Inline Citations:** Answers provide inline source tags `[S1]`, `[S2]` with expandable drawer metadata (record type, relevance score, title, and link).

---

## 4. API Specification

### Endpoint: `POST /api/v1/chat/ask`
- **Authentication:** Mandatory (`Bearer <jwt_token>`). Unauthenticated calls return `401 Unauthorized`.
- **Validation:** Bounded question length (1 to 2000 characters). Empty queries return `422 Unprocessable Entity`.

#### Sample Request:
```json
{
  "question": "Which mammals have the fewest observation records?",
  "conversation_id": "conv-101",
  "conversation_history": []
}
```

#### Sample Response:
```json
{
  "answer": "Based on retrieved platform records and research intelligence, here is the verified evidence regarding your inquiry:\n\n**Verified Database Records:**\n- **Kashmir Stag (Cervus hanglu)** [S1]: Taxon: Cervus hanglu (Kashmir Stag), Class: Mammalia, Family: Cervidae. Official IUCN Status: CR. Documented Observations in DB: 2 [Lat: 34.15-34.18, Lon: 74.92-74.98].\n...",
  "sources": [
    {
      "id": "S1",
      "source_type": "DATABASE",
      "title": "Kashmir Stag (Cervus hanglu)",
      "reference": "/species/42",
      "snippet": "Taxon: Cervus hanglu (Kashmir Stag), Class: Mammalia...",
      "relevance_score": 0.95,
      "metadata": {
        "species_id": 42,
        "class_name": "Mammalia",
        "iucn_category": "CR",
        "observation_count": 2
      }
    }
  ],
  "retrieval_metadata": {
    "intent": "TAXONOMIC_QUERY",
    "db_species_retrieved": 4,
    "db_observations_retrieved": 12,
    "documents_retrieved": 0,
    "external_records_retrieved": 0,
    "llm_provider": "extractive_synthesizer",
    "llm_model": "nlp-vector-hybrid",
    "retrieval_time_ms": 32.5,
    "generation_time_ms": 0.2
  },
  "conversation_id": "conv-101"
}
```

---

## 5. Frontend Integration

1. **Dedicated AI Assistant Page:**
   - Route: `/assistant`
   - Access: Sidebar item **AI ASSISTANT** with `Bot` icon.
   - Features: Full conversation panel, suggested queries, expandable citation drawers, institutional styling matching `#131210` / `#faf8f4` palette.
2. **Floating Chat Widget:**
   - Visible across all application pages (automatically hidden on `/assistant` to prevent duplicate instances).
   - Bottom-right launcher button (`#11682f` / emerald hover) opening a compact chat panel with a maximize button navigating to the full page.

---

## 6. How to Run Locally

### Start Backend:
```bash
.venv\Scripts\activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Frontend:
```bash
cd frontend
npm run dev
```

### Run Automated Tests:
```bash
# Run RAG unit tests
.venv\Scripts\python.exe -m pytest backend/tests/test_rag.py -v

# Run full backend test suite
.venv\Scripts\python.exe -m pytest -q

# Build frontend bundle
cd frontend
npm run build
```
