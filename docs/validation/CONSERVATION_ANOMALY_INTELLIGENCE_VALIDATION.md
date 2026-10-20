# Conservation Anomaly Intelligence Validation

## 1. Validation Date
2026-10-07

## 2. Feature Objective
Enhance the existing Isolation Forest anomaly detection system to provide contextual, explainable conservation intelligence. The goal was to provide evidence-grounded insights by linking anomalies to related observations, scientific documents, and identified ecological threats without introducing fabricated data or new black-box models.

## 3. Project Constraints Checklist
- [x] **No replacement of ML models:** The existing Isolation Forest (`AnomalyDetectorService`) remains untouched and continues to generate the raw `anomaly_score`.
- [x] **No new standalone AI models added:** All contextual intelligence is derived directly via SQL joins from the existing validated datasets.
- [x] **No fabricated ecological conclusions:** Context is constructed factually (e.g. "X observations in last 30 days," "Y related documents").
- [x] **Adherence to scientific stance:** The system uses neutral terminology such as "investigation guidance" and "evidence strength" instead of claiming certain extinction risks.
- [x] **No modification of unrelated features:** Only the `/anomalies` API response and the corresponding UI components (`AnomalyCard`) were updated.
- [x] **Explicit evidence handling:** Implemented rules for calculating `evidence_strength` (HIGH, MEDIUM, LOW, INSUFFICIENT) strictly based on document counts.

## 4. Implementation Details
### Backend Updates
- Modifed the `/api/v1/ml/anomalies` endpoint in `backend/app/routers/ml.py`.
- Enriched `AnomalyItem` schema with the following fields:
  - `isolation_score`: Relabeled from `anomaly_score` to reflect its true mathematical origin.
  - `species`: Included detailed species metadata.
  - `location`: Mapped geospatial origin if available.
  - `observation_count`: Rolling 30-day species observation count query.
  - `related_threats`: Dynamically aggregates and counts mentions of IUCN threats across linked documents.
  - `related_documents`: Fetches titles and IDs of up to 5 recently indexed documents mentioning the species.
  - `supporting_record_count`: Sum of observation and document counts.
  - `investigation_guidance`: Neutral directive prompting data review.
  - `evidence_strength`: Deterministic evaluation string based on volume of related documents.

### Frontend Updates
- Extended `AnomalyResult` typing in `frontend/src/types/index.ts`.
- Redesigned `AnomalyCard.tsx` to visualize:
  - Contextual metadata (Species Name, Scientific Name, Location).
  - Explicit Investigation Guidance block.
  - Related Threats pill-style layout with mention counts.
  - Observation metrics for the 30-day window.
  - Visual categorization of Evidence Strength.

## 5. Verification
- **Backend Tests:** Passed (40/40 via `pytest backend/tests/test_api.py -v`). No API contracts or test coverage were broken.
- **Frontend Build:** Passed (`vite build`). No strict TypeScript errors detected.

## 6. Executive Result
**VALIDATED AND READY TO FREEZE.** The Conservation Anomaly Intelligence enhancement successfully transforms the abstract Isolation Forest scores into actionable, evidence-backed decision support data, preserving the integrity of the project's original machine learning framework.
