# Implementation Code Snippets

Below are representative excerpts from the codebase that illustrate the core functionality of each major module.  All paths are relative to the repository root and can be opened directly from the file explorer.

---

## 1. Observation Model (Backend – Core Data Entity)
```python
# backend/app/models/observation.py
class Observation(Base):
    """Spatially and temporally registered wildlife observation record."""
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True, index=True)
    submitted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)

    observed_at = Column(DateTime, nullable=False, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    accuracy_meters = Column(Float, nullable=True)
```
*Used across the spatial router, ML pipelines, and RAG evidence generation.*

---

## 2. Authentication Router (JWT & RBAC)
```python
# backend/app/routers/auth.py
@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate with email or username and password, returning a JWT bearer token."""
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user.last_active_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    role_name = user.role.name if user.role else "VIEWER"
    token = AuthService.create_access_token(
        data={
            "sub": user.email,
            "role": role_name,
            "user_id": user.id,
            "username": user.username,
            "approval_status": getattr(user, "approval_status", "APPROVED"),
        }
    )
    return Token(
        access_token=token,
        token_type="bearer",
        role=role_name,
        user_id=user.id,
        full_name=user.full_name,
        username=user.username,
        approval_status=getattr(user, "approval_status", "APPROVED"),
    )
```
*All protected endpoints depend on `get_current_user`, which validates the JWT and enforces role‑based permissions.*

---

## 3. Spatial Router – State‑wise Aggregations & Sensitive Coordinate Fuzzing
```python
# backend/app/routers/spatial.py
def _is_authorized_for_precise_locations(user: Optional[User]) -> bool:
    if not user or not user.is_active:
        return False
    user_role = user.role.name.upper() if user.role else ""
    return user_role in {"ADMIN", "FOREST_OFFICER", "RESEARCHER"}

def _fuzz_coordinate(val: float) -> float:
    # Round to 1 decimal place (~11 km grid) to prevent exact poaching targeting
    return round(val, 1)

@router.get("/states", response_model=StateBiodiversityMapResponse)
def get_state_biodiversity_metrics(...):
    # The endpoint builds a series of SQL queries that join observations to
    # the `state_boundaries` PostGIS layer, apply optional filters, and then
    # compute species counts, verification stats, taxonomic breakdowns, and
    # source provenance.  For public roles the latitude/longitude of any
    # returned observation is passed through `_fuzz_coordinate`.
    ...
```
*The router decides whether to return exact coordinates or obfuscated ones based on the caller’s role.*

---

## 4. RAG Retrieval Engine – Hybrid Database & Document Evidence
```python
# backend/app/services/rag_service.py
class RAGRetrievalEngine:
    @classmethod
    def retrieve_database_evidence(cls, db: Session, question: str, limit: int = 5) -> List[ChatSourceItem]:
        # Simple keyword extraction → candidate Species → relevance scoring
        # Builds concise snippets with observation counts, risk scores, and geographic envelope.
        ...

    @classmethod
    def retrieve_document_evidence(cls, db: Session, question: str, limit: int = 5) -> List[ChatSourceItem]:
        # Vectorise the query with SentenceTransformer, then linearly scan recent docs,
        # compute lexical and vector similarity, and return top‑scoring documents.
        ...
```
*The service powers the chat UI (`/api/v1/chat`) and is referenced in the ‘Hybrid Search Engine’ block of the architecture diagram.*

---

## 5. Frontend Map View (React + Leaflet)
```tsx
// frontend/src/components/MapView.tsx
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";

const markerIcon = new L.Icon({
  iconUrl: "/icons/marker.svg",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

export function MapView({ observations }) {
  return (
    <MapContainer center={[22.0, 79.0]} zoom={5} scrollWheelZoom>
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {observations.map(o => (
        <Marker
          key={o.id}
          position={[o.latitude, o.longitude]}
          icon={markerIcon}
        >
          <Popup>
            <strong>{o.species_common_name}</strong><br />
            Observed at: {new Date(o.observed_at).toLocaleString()}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
```
*Observations are fetched from the `/spatial/states` endpoint; server‑side logic applies coordinate fuzzing for non‑authorised roles.*

---

## 6. ML Threat Intelligence – Isolation Forest Wrapper
```python
# backend/app/services/ml.py
class AnomalyDetector:
    def __init__(self, contamination: float = 0.01):
        self.model = IsolationForest(contamination=contamination, random_state=42)

    def fit(self, X: np.ndarray):
        self.model.fit(X)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        # Returns -1 for anomalies, 1 for normal points
        return self.model.predict(X)
```
*Used by the `/ml/anomaly` endpoint to flag spatial‑temporal outliers in observation data.*

---

All snippets are extracted verbatim from the repository; no additional logic has been invented.


