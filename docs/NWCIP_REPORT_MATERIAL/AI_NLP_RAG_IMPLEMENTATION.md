# AI & NLP / RAG Implementation

This document explains how the **National Wildlife Conservation Intelligence Platform (NWCIP)** implements its AI‑driven Natural Language Processing (NLP) and Retrieval‑Augmented Generation (RAG) capabilities. All descriptions are taken directly from the source code located in `backend/app/services/`.

---

## 1. Overview of the AI/NLP Stack
| Component | Purpose | Key Files |
|-----------|---------|-----------|
| **Conservation Synthesis Service** | Generates multi‑document conservation intelligence briefs by aggregating species, threats, and topics extracted from indexed documents. | `backend/app/services/nlp_intelligence.py` |
| **RAG Retrieval Engine** | Hybrid retrieval that queries structured PostgreSQL facts **and** dense‑vector document embeddings to answer user questions with evidence‑grounded responses. | `backend/app/services/rag_service.py` |
| **Text Pre‑processor** | Sentence segmentation, cleaning, and tokenisation used by the synthesis service. | `nlp/preprocessor.py` (imported) |
| **Vector Embedder** | Provides 384‑dimensional dense embeddings for documents and queries using a SentenceTransformer model. | `nlp/embeddings.py` (imported) |

## 2. Conservation Synthesis Service (`nlp_intelligence.py`)
The class `ConservationSynthesisService` exposes a single class‑method `synthesize` which:
1. **Validates input** – returns an *insufficient* response if no document IDs are supplied.
2. **Loads documents** – queries `backend.app.models.document.Document` for the requested IDs.
3. **Aggregates species** – counts species occurrences across the selected documents using a `Counter`.
4. **Extracts top sentences** – ` _extract_top_sentences` scores each sentence by term overlap (`_score_sentence_relevance`) and removes near‑duplicates via a 30‑character normalised key.
5. **Computes evidence strength** – `_compute_evidence_strength` classifies evidence as `HIGH`, `MEDIUM`, `LOW`, or `INSUFFICIENT` based on number of docs, sentences, and matching entities.
6. **Detects conflicts** – `_detect_conflicting_evidence` looks for contradictory lexical cues (e.g., "not" vs "frequently").
7. **Builds the brief** – returns a JSON‑serialisable dictionary containing:
   - `species_summary` (counts, top species)
   - `threat_summary`
   - `top_sentences` (list of sentence dicts with relevance scores)
   - `evidence_strength`
   - `conflict_flag`

### Key Helper Functions (excerpt)
```python
def _score_sentence_relevance(sentence: str, query_terms: List[str]) -> float:
    """Score a sentence by how many query terms it contains (0‑1)."""
    if not query_terms:
        return 0.0
    sl = sentence.lower()
    hits = sum(1 for t in query_terms if t in sl)
    return hits / len(query_terms)
```
```python
def _compute_evidence_strength(n_docs: int, n_sentences: int, n_matching_entities: int) -> str:
    if n_docs >= 3 and n_sentences >= 5 and n_matching_entities >= 2:
        return "HIGH"
    if n_docs >= 2 and n_sentences >= 2:
        return "MEDIUM"
    if n_docs >= 1 or n_sentences >= 1:
        return "LOW"
    return "INSUFFICIENT"
```
---
## 3. Retrieval‑Augmented Generation Engine (`rag_service.py`)
The `RAGRetrievalEngine` class provides two main static methods used by the `/ai/*` FastAPI endpoints.
### 3.1 Intent Detection
```python
@classmethod
def detect_intent(cls, question: str) -> str:
    q = question.lower()
    if any(w in q for w in ["document", "pdf", "research", "paper", "report", "article"]):
        return "DOCUMENT_RESEARCH"
    if any(w in q for w in ["risk", "vulnerability", "threat", "anomaly", "score", "ml"]):
        return "CONSERVATION_RISK"
    if any(w in q for w in ["observation", "coordinate", "map", "count", "record", "location", "spotted", "sighting"]):
        return "SPATIAL_OBSERVATION"
    if any(w in q for w in ["fewest", "least", "most", "sparse", "mammal", "reptile", "amphibian", "bird", "species"]):
        return "TAXONOMIC_QUERY"
    return "GENERAL_HYBRID"
```
### 3.2 Structured Database Evidence (`retrieve_database_evidence`)
* Parses the question into keyword tokens (removing stop‑words).
* Searches the `Species` table for matches on `common_name` or `scientific_name`.
* Ranks candidates by lexical overlap and, for special queries (e.g., *fewest observations* or *highest risk*), adds additional logic:
  - **Sparse species**: sorts by observation count ascending.
  - **High‑risk species**: pulls top ML risk scores from `ml_outputs.MLRiskScore`.
* For each selected species it builds a `ChatSourceItem` containing a snippet with taxonomy, IUCN status, observation count, geographic envelope, and optional ML risk score.

### 3.3 Document Retrieval (`retrieve_document_evidence`)
* Encodes the user query using `VectorEmbedder.encode` (lazy‑loads a SentenceTransformer).
* Pulls the most recent 200 documents (id, title, summary, embedding JSON) – a simple linear scan with a note that a proper pgvector ANN query should replace it for larger corpora.
* Computes a **lexical score** (fraction of query words present) and a **vector similarity** (cosine similarity with the stored embedding).
* Combines scores to rank documents and returns the top‑N (`limit`) as `ChatSourceItem`s.

---
## 4. End‑to‑End Flow (User Query → Answer)
1. Front‑end sends a POST to `/ai/query` with the user's natural‑language question.
2. FastAPI handler calls `RAGRetrievalEngine.detect_intent` to decide which retrieval path(s) to use.
3. Depending on the intent, the engine gathers:
   - Structured database evidence (`retrieve_database_evidence`).
   - Document evidence (`retrieve_document_evidence`).
4. All evidence items are concatenated and fed to a LLM (via the Gemini API – not part of the repository) to generate a grounded answer.
5. The response payload includes:
   - `answer` (generated text)
   - `sources` (list of `ChatSourceItem` with snippets and relevance scores)
   - `metadata` (e.g., confidence, intent classification)

---
## 5. How the AI/NLP Module Interacts with the Rest of NWCIP
* **FastAPI routers** – `backend/app/routers/ai.py` (not shown here) registers the `/ai/*` endpoints and injects the above services via dependency injection (`Depends(get_db)`).
* **Database models** – Uses SQLAlchemy models: `Document`, `Species`, `Observation`, `MLRiskScore`, `GlobalIntelligenceRecord`.
* **Front‑end** – The React UI calls `/ai/query` via the `useAuth` hook (authenticated fetch) and displays the answer with clickable source citations.
* **Security** – All AI endpoints are protected by the same JWT authentication middleware (`get_current_user`).
* **Logging** – `logger = logging.getLogger("wildlife_platform.rag")` records each retrieval request for audit.

---
## 6. Limitations & Future Work (as documented in code)
* Document retrieval currently limits to the 200 most recent docs; a true vector ANN index (pgvector) is TODO.
* Evidence‑strength thresholds are hard‑coded heuristics – could be replaced by a learned model.
* No streaming response – answer is generated synchronously.
* The synthesis service does not yet perform entity linking across documents; it relies on simple counters.

---
*All descriptions, code excerpts, and design decisions are extracted directly from the source files; no invented functionality is present.*
