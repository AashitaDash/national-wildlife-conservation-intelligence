# Implementation Plan - Downloadable Conservation Reports Feature

Integrate a complete, institutional-grade Downloadable Conservation Reports module into the existing Wildlife Conservation Intelligence Platform.

## 1. Verified Live Database Entities & Sources
Audited against live PostgreSQL database:
- **Species**: 392 records across 4 classes (Aves: 255, Mammalia: 78, Reptilia: 33, Amphibia: 26) with verified IUCN categories (`CR`: 9, `EN`: 29, `VU`: 25, `NT`: 9, `LC`: 320).
- **Observations**: 46,273 records with coordinates, dates, and provenance across 6 data sources (GBIF: 32,111, iNaturalist: 13,734, eBird: 405, Researcher Submission: 15, Government Report: 7, Citizen Portal: 1).
- **Threats & NLP Intelligence**: 125 documents, 10 standardized threat categories, 176 document-threat associations (Poaching: 90, Habitat Fragmentation: 26, Linear Infrastructure: 21, Mining: 19, etc.).
- **ML Risk Indicators**: 81 assessed species with Random Forest vulnerability scores (CRITICAL: 3, HIGH: 13, MEDIUM: 29, LOW: 36) and 80 Isolation Forest spatial-temporal anomalies.
- **Locations**: 10 primary national parks / tiger reserves (Similipal, Corbett, Kaziranga, Sundarbans, etc.).

## 2. Report Types Implemented
1. **Conservation Overview Report**: Platform-wide metrics, taxonomic breakdown, conservation status distribution, observation provenance, and scientific caveats.
2. **Species Conservation Report**: Target species taxonomic profile, IUCN status & source, observation counts & temporal range, geographic extent, associated threats, and platform-generated ML risk score.
3. **Geographic Intelligence Report**: Filtered by location/protected area or bounding coordinates, observation density, species inventory, and spatial limitations.
4. **Threat & Risk Assessment Report**: Documented threat incidence, affected species, ML vulnerability levels, and methodological distinctions between verified field threats and ML model risk indicators.
5. **Research & Document Intelligence Report**: Corpus of parsed conservation documents, NLP-extracted threats/entities, citations, and metadata.

## 3. Supported Export Formats
- **PDF**: Generated dynamically via `reportlab` with institutional header, summary cards, breakdown tables, metadata, and scientific interpretation caveats.
- **CSV**: Filtered tabular data with formula-injection mitigation (`=`, `+`, `-`, `@` escaping on string fields).
- **XLSX**: Formatted multi-tab Excel workbooks via `openpyxl` with styled headers and clear sheets (Overview, Data, Methodology).

## 4. Architecture & Proposed API Contract
- Router: `backend/app/routers/reports.py` (registered under `/api/v1/reports`)
- Service: `backend/app/services/report_service.py`
- Schemas: `backend/app/schemas/report.py`
- Endpoints:
  - `GET /api/v1/reports/types` — Available report types and their supported filters.
  - `POST /api/v1/reports/preview` — Scoped record count and summary metadata before generation.
  - `POST /api/v1/reports/generate` — Dynamic report compilation returning streamed file (PDF, CSV, XLSX) with `Content-Disposition: attachment; filename=...`.

## 5. Security & RBAC
- Authenticated via JWT (`get_current_active_user`).
- Role-based accessibility: Available to all authenticated platform roles (`ADMIN`, `FOREST_OFFICER`, `RESEARCHER`, `VIEWER`).
- In-memory streaming using `io.BytesIO` — zero unmanaged temporary files on disk.
- Safe query limits and parameterization.

## 6. Frontend Integration
- Route: `/reports` in `App.tsx` within ProtectedRoute.
- Sidebar: "REPORTS & EXPORTS" entry in `Sidebar.tsx`.
- Component: `frontend/src/pages/ReportsPage.tsx` using the institutional ivory/dark-forest design language.
