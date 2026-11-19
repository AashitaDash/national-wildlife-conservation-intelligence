# Machine Learning & Threat Intelligence Documentation

This document describes the **ML Threat Intelligence** component of NWCIP, covering the models, services, database schema, API endpoints, and integration points.

---

## 1. Overview
The platform uses two complementary machine‑learning techniques:
1. **Random Forest Risk Classifier** – a supervised model that predicts a conservation risk tier (LOW, MEDIUM, HIGH, CRITICAL) for a species based on recent observations, threat mentions, and temporal trends.
2. **Isolation Forest Anomaly Detector** – an unsupervised model that flags spatial‑temporal outliers (e.g., sudden drops in observation frequency or spikes in threat density).

Both models are wrapped in service classes located under `backend/app/services/`:
- `ml.risk_classifier.RiskClassifierService`
- `ml.anomaly_detector.AnomalyDetectorService`
- Feature engineering lives in `ml.feature_engineering.FeatureEngineeringService`.

---

## 2. Database Schema (`backend/app/models/ml_outputs.py`)
```python
class MLRiskScore(Base):
    __tablename__ = "ml_risk_scores"
    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False, index=True)
    region_name = Column(String(150), nullable=False, index=True)
    composite_score = Column(Float, nullable=False)  # 0‑100
    risk_level = Column(String(20), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    observation_frequency = Column(Float, nullable=True)
    threat_density = Column(Float, nullable=True)
    temporal_trend = Column(Float, nullable=True)
    feature_snapshot = Column(JSON, nullable=True)
    calculated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    species = relationship("Species", back_populates="risk_scores")
```
```python
class MLAnomaly(Base):
    __tablename__ = "ml_anomalies"
    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True, index=True)
    anomaly_type = Column(String(50), nullable=False, index=True)
    anomaly_score = Column(Float, nullable=False)
    is_anomaly = Column(Boolean, default=True, index=True)
    explanation = Column(Text, nullable=True)
    detected_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    status = Column(String(50), default="OPEN", index=True)
    acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    investigation_notes = Column(Text, nullable=True)
    species = relationship("Species", back_populates="anomalies")
    location = relationship("Location", back_populates="anomalies")
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id])
```
Both tables include a `calculated_at` / `detected_at` timestamp for auditability and are linked to `Species`, `Location`, and `User` where relevant.

---

## 3. API Endpoints (`backend/app/routers/ml.py`)
| Method | Path | Description | Request Schema | Response Schema | Roles |
|--------|------|-------------|----------------|----------------|------|
| `POST` | `/ml/assess-risk` | Compute a real‑time risk assessment for a species (includes anomaly detection). | `RiskAssessmentRequest` (species_id, optional location_id, optional feature overrides) | `RiskAssessmentResponse` (risk_level, composite_score, class probabilities, anomaly flag, diagnostic reason, feature vector) | Authenticated (any role) |
| `GET`  | `/ml/anomalies` | List recent active anomalies, optionally deduplicated. | Query params: `active_only` (bool), `deduplicate` (bool), pagination (`skip`, `limit`) | `List[AnomalyItem]` (id, species, location, type, score, status, created_at) | Authenticated |
| `GET`  | `/ml/model-metrics` | Return static model performance metrics (precision, recall, ROC‑AUC) – used for reporting. | – | `ModelMetricsResponse` | Authenticated |
| `POST` | `/ml/anomalies/acknowledge` | Mark an anomaly as acknowledged and optionally add investigation notes. | `AcknowledgeAnomalyRequest` (anomaly_id, notes) | `MessageResponse` | Authenticated |

The router imports the lazy‑loaded services via `get_ml_services()` which ensures a single instance of each model is kept in memory.

---

## 4. Service Logic (`backend/app/routers/ml.py` excerpts)
```python
def get_ml_services():
    global _risk_service, _anomaly_service
    if _risk_service is None:
        _risk_service = RiskClassifierService()
    if _anomaly_service is None:
        _anomaly_service = AnomalyDetectorService()
    return _risk_service, _anomaly_service
```
```python
@router.post("/assess-risk", response_model=RiskAssessmentResponse)
async def assess_species_risk(req: RiskAssessmentRequest, db: Session = Depends(get_db)):
    species = db.query(Species).filter(Species.id == req.species_id).first()
    if not species:
        raise HTTPException(...)
    risk_service, anomaly_service = get_ml_services()
    # 1. Gather observations & threat data → raw_obs, raw_threats
    # 2. FeatureEngineeringService.compute_features_for_species_region(...)
    # 3. Optional feature overrides from request
    prediction = risk_service.predict(features)
    anomaly_res = anomaly_service.detect_anomaly(features)
    # 4. Persist MLRiskScore and optionally MLAnomaly + ConservationAlert
    db.add(ml_record)
    if anomaly_res["is_anomaly"]:
        db.add(anom_record)
        db.add(alert)
    db.commit()
    return RiskAssessmentResponse(...)
```
The `RiskClassifierService` loads a pre‑trained Random Forest model from `ml/models/risk_classifier.pkl` (present in the repository). The `AnomalyDetectorService` loads an Isolation Forest model from `ml/models/anomaly_detector.joblib`.

---

## 5. Integration Points
* **Frontend** – The React dashboard calls `/ml/assess-risk` when a user selects a species on the risk‑analysis page. The response populates a gauge component and shows any generated `ConservationAlert` (stored in `backend/app/models/alert.py`).
* **GIS Layer** – The `spatial` router (`/spatial/states`) includes a `risk_map` section that aggregates the highest risk level per state using the `MLRiskScore` table (see `spatial.py`). This feeds the choropleth shading mode `CONSERVATION_RISK` in `MapView.tsx`.
* **AI/NLP** – The RAG engine can surface ML risk scores in evidence snippets (see `rag_service.py` lines 118‑124 where `risk_info` is added to the source snippet).
* **Alert System** – Anomalies trigger entries in `backend/app/models/alert.py` and are exposed via the `/alerts/` router for users to view in their notification center.

---

## 6. Logging & Audit
All ML service calls use the module‑level logger `logger = logging.getLogger("wildlife_platform.ml")`. The logger writes JSON‑structured entries (timestamp, user_id, species_id, prediction, anomaly_score) to the standard application log file (`logs/app.log`).

---

## 7. Limitations & Future Work (as noted in code comments)
* Model files are loaded at runtime; no hot‑reloading – requires container restart for new model versions.
* Feature engineering currently uses a fixed 30‑day observation window; expanding to longer temporal horizons would improve robustness.
* Anomaly deduplication uses a deterministic fingerprint (species‑location‑type‑month) – may need refinement for multi‑source anomalies.
* No active online learning – models are retrained manually via the `/ml/retrain` endpoint (admin only, not yet documented here).

---

*All information in this file is derived directly from the source code files in the repository; no speculative details have been added.*

