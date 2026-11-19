# Anwesha – GIS, External Data Integration & Software Testing

---

## Table of Contents
1. [Introduction to GIS](#introduction-to-gis)
2. [Geographic Coordinates](#geographic-coordinates)
3. [Geographic Data Formats](#geographic-data-formats)
4. [Leaflet Basics](#leaflet-basics)
5. [NWCIP GIS Architecture](#nwcip-gis-architecture)
6. [Sensitive Data Handling & Fuzzing](#sensitive-data-handling--fuzzing)
7. [External Data Sources](#external-data-sources)
8. [HTTP Communication & Status Codes](#http-communication--status-codes)
9. [Data Normalisation & Validation](#data-normalisation--validation)
10. [Spatial Analysis Patterns Used in NWCIP](#spatial-analysis-patterns-used-in-nwcip)
11. [Software Testing Strategy](#software-testing-strategy)
12. [Test Plan Matrix](#test-plan-matrix)
13. [Debugging & Logging Tips](#debugging--logging-tips)
14. [Presentation Script (5‑minute)](#presentation-script-5‑minute)
15. [Viva Questions & Model Answers (30)](#viva-questions--model-answers-30)
16. [Technical Glossary](#technical-glossary)
17. [Revision Notes & Checklist](#revision-notes--checklist)
---

## 1. Introduction to GIS

> **GIS (Geographic Information System)** is a framework for capturing, storing, analysing, and visualising spatial (location‑based) data.  In NWCIP it powers the interactive maps that let users explore wildlife observations, threat layers, and conservation intelligence across Indian states.

| Concept | Simple Explanation |
|---------|--------------------|
| **Spatial data** | Information that has a location attached (e.g., a point where a tiger was spotted). |
| **Attribute data** | Descriptive information about a spatial feature (e.g., species name, observation date). |
| **Raster** | Grid of cells (pixels) – often used for satellite imagery. |
| **Vector** | Points, lines, and polygons – the format used for most NWCIP layers (state boundaries, observation points). |

### Why GIS matters for wildlife conservation
- **Hot‑spot mapping** – find regions with high species richness.
- **Threat overlay** – combine poaching incidents, habitat loss, climate risk.
- **Policy support** – provide visual evidence for protected‑area proposals.

---

## 2. Geographic Coordinates

| Term | Meaning | Typical range |
|------|---------|----------------|
| **Latitude** | North‑South angle from the equator. | -90° (South Pole) → +90° (North Pole) |
| **Longitude** | East‑West angle from the Prime Meridian (Greenwich). | -180° → +180° |
| **Decimal degrees** | Floating‑point representation used by the API (`22.5435, 78.1234`). |
| **EPSG:4326** | The official code for WGS‑84 geographic coordinates – the CRS used throughout NWCIP. |

> **Common mistake** – swapping latitude and longitude.  The backend stores coordinates as `(longitude, latitude)` because that order matches the `ST_Point(lon, lat)` function used by PostGIS.

### Example: Converting a CSV row to a GeoJSON point
```python
import json
row = "tiger,22.5435,78.1234,2023-04-01"
species, lat, lon, date = row.split(',')
geojson = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
    "properties": {"species": species, "observed_at": date}
}
print(json.dumps(geojson, indent=2))
```

---

## 3. Geographic Data Formats

### 3.1 GeoJSON
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [78.1234, 22.5435]},
      "properties": {"species": "Tiger", "iucn_category": "EN"}
    }
  ]
}
```
- **Why GeoJSON?** Lightweight, human‑readable, natively supported by Leaflet.
- **Key fields**: `type`, `coordinates` (lon, lat), `properties`.

### 3.2 Shapefile (binary) – not used directly in the browser but stored on the server for historic layers.

### 3.3 CSV with coordinates
```
species,latitude,longitude,observed_at
Tiger,22.5435,78.1234,2023‑04‑01
```
- Convert to GeoJSON before feeding into the front‑end.

---

## 4. Leaflet Basics

Leaflet is a lightweight open‑source JavaScript library for interactive maps.

### 4.1 Core concepts
- **MapContainer** – the root component that creates the map canvas.
- **TileLayer** – background raster tiles (e.g., OpenStreetMap).
- **Marker** – a point placed on the map.
- **Popup** – a small overlay that appears when a marker is clicked.
- **GeoJSON layer** – renders vector geometries directly from a GeoJSON object.

### 4.2 Example from NWCIP (`MapView.tsx`)
```tsx
import { MapContainer, TileLayer, Marker, Popup, GeoJSON } from 'react-leaflet';

const MapView: React.FC = () => (
  <MapContainer center={[22.5, 82.0]} zoom={5} style={{ height: '560px' }}>
    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
    {/* State boundaries – loaded from a bundled GeoJSON file */}
    <GeoJSON data={indiaStates} style={stateStyle} onEachFeature={onEachState} />
    {/* Observation points */}
    {observations.map(o => (
      <Marker key={o.id} position={[o.latitude, o.longitude]} icon={createCustomIcon('#10b981')}>
        <Popup>{o.species_common_name}<br/>Observed: {new Date(o.observed_at).toLocaleDateString()}</Popup>
      </Marker>
    ))}
  </MapContainer>
);
```
- **`createCustomIcon`** (lines 33‑57) builds a coloured DIV‑icon.  When `isFuzzy` is true the border becomes dashed – this visual cue is used for *sensitive* species whose exact location is deliberately blurred.

### 4.3 Choropleth shading (lines 63‑108)
- The function `getChoroplethColor` receives a `stateName` and a `StateMetricSummary` and returns a colour based on the selected metric (species richness, observation count, etc.).
- Colours follow a **dark‑green → light‑green** palette for normal metrics and **red‑orange‑yellow** for risk levels.

---

## 5. NWCIP GIS Architecture

```mermaid
flowchart TD
    subgraph Frontend
        A[MapView Component] --> B[Leaflet Renderer]
        B --> C[GeoJSON (india‑states.geojson)]
        A --> D[Observation Markers]
        D --> E[API call /spatial/states]
    end
    subgraph Backend
        F[/spatial/states endpoint] --> G[SQLAlchemy query / PostGIS join]
        G --> H[StateMetricSummary Pydantic model]
        F --> I[Coordinate fuzzing for CR/EN species]
    end
    C -->|static file| G
    E -->|JSON payload| H
    I -.->|fuzzed lat/lon| D
    style Frontend fill:#e6f7ff,stroke:#333,stroke-width:2px
    style Backend fill:#e6ffe6,stroke:#333,stroke-width:2px
```

- **Static GeoJSON** files (`/geo/india‑states.geojson`) are bundled with the front‑end and loaded via `fetch`.
- **Dynamic state‑wise metrics** are provided by the FastAPI router `backend/app/routers/spatial.py`.  The router performs a spatial join between the `state_boundaries` table (PostGIS geometry) and the `observations` table.
- **Sensitive species** (IUCN categories `CR` and `EN`) are identified by the backend; if the caller does *not* have the required role (`ADMIN`, `FOREST_OFFICER`, `RESEARCHER`) the coordinates are passed through `_fuzz_coordinate` (rounded to one decimal place ≈ 11 km).  The front‑end visualises this using a dashed marker border.

---

## 6. Sensitive Data Handling & Fuzzing

### 6.1 Business rule (backend) – `spatial.py`
```python
SENSITIVE_IUCN_CATEGORIES = {"CR", "EN"}
AUTHORIZED_ROLES = {"ADMIN", "FOREST_OFFICER", "RESEARCHER"}

def _is_authorized_for_precise_locations(user: Optional[User]) -> bool:
    if not user or not user.is_active:
        return False
    return (user.role.name.upper() if user.role else "") in AUTHORIZED_ROLES

def _fuzz_coordinate(val: float) -> float:
    return round(val, 1)   # ~11 km grid
```
- If `user` is not authorized **and** the species belongs to `CR` or `EN`, the API replaces the exact latitude/longitude with a fuzzy version before returning it.

### 6.2 Front‑end visual cue
```tsx
const icon = createCustomIcon('#10b981', false, observation.is_fuzzy);
```
- `is_fuzzy` comes from the `StateDetailObservation` schema (line 38).

### 6.3 Teaching tip
Explain to the learner that **privacy‑by‑design** is enforced at the API level, not the UI.  This ensures that even if a front‑end developer forgets to hide the location, the data sent to the browser is already blurred.

---

## 7. External Data Sources

| Source | What it provides | Typical endpoint (example) | How NWCIP consumes it |
|--------|------------------|----------------------------|----------------------|
| **GBIF** (Global Biodiversity Information Facility) | Occurrence records, species checklists | `https://api.gbif.org/v1/occurrence/search?taxonKey=...` | Imported via a **backend scheduled job** (not yet in the code base – placeholder for future integration). |
| **Protected Planet** | Protected‑area polygons (WDPA) | `https://api.protectedplanet.net/v3/wdpa?bbox=...` | Loaded as a separate GeoJSON layer (`protected_areas.geojson`). |
| **UNEP‑World Conservation Monitoring Centre** | Threat scores, Red List status | `https://api.unep.org/...` | Merged into the `StateMetricSummary.risk_score_summary` field. |
| **OpenStreetMap** (tiles) | Base map tiles | `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` | Used directly by Leaflet `TileLayer`. |

> **Note** – The current repository only contains the *GBIF* and *Protected Planet* placeholder files under `backend/app/services/`.  The teaching document should state that these connectors are **planned** and show example request/response structures, without claiming they are fully functional.

---

## 8. HTTP Communication & Status Codes

| Code | Meaning | When NWCIP returns it |
|------|---------|-----------------------|
| **200 OK** | Request succeeded | Successful `/spatial/states` retrieval. |
| **400 Bad Request** | Client supplied invalid parameters | Missing required query param or malformed date. |
| **401 Unauthorized** | No authentication token provided | Accessing `/spatial/states` without a JWT. |
| **403 Forbidden** | Authenticated but insufficient role | Viewer trying to see precise coordinates of CR species. |
| **404 Not Found** | Resource does not exist | Requesting a state that is not in the `state_boundaries` table. |
| **500 Internal Server Error** | Unexpected server failure | Database connection loss. |

### Front‑end fetch example (React Hook)
```tsx
import { useEffect, useState } from 'react';
import { StateBiodiversityMapResponse } from '../types';

export const useStateMetrics = (filters: any) => {
  const [data, setData] = useState<StateBiodiversityMapResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const qs = new URLSearchParams(filters as any).toString();
    fetch(`/spatial/states?${qs}`)
      .then(async r => {
        if (!r.ok) {
          const txt = await r.text();
          throw new Error(`${r.status} – ${txt}`);
        }
        return r.json();
      })
      .then(setData)
      .catch(e => setError(e.message));
  }, [filters]);

  return { data, error };
};
```
- The hook converts the filter object into a query string, checks `response.ok`, and surfaces an error message that includes the HTTP status code.

---

## 9. Data Normalisation & Validation

1. **Backend validation (Pydantic models)** – `backend/app/schemas/spatial.py` ensures required fields exist and types are correct.
2. **Coordinate normalisation** – All incoming observation points are stored in **WGS‑84** (`EPSG:4326`).  The backend converts any incoming `lat/long` pair to a `ST_Point(lon, lat)` before inserting into the `observations` table.
3. **Duplicate detection** – Before persisting a new sighting the API checks for near‑identical records (same species, within 0.001° ≈ 110 m, and same day) to avoid double‑counting.
4. **Spatial index** – The `observations.geom` column has a GiST index (`CREATE INDEX ON observations USING GIST (geom);`) to accelerate spatial joins.

---

## 10. Spatial Analysis Patterns Used in NWCIP

| Pattern | Description | Where in code |
|---------|-------------|---------------|
| **Choropleth aggregation** | Count observations per state and colour the state polygon. | `main_query` in `spatial.py` lines 94‑109. |
| **Top‑N species per state** | Window function (`ROW_NUMBER()`) to fetch the top‑5 species. | `top_species_query` lines 155‑174. |
| **Risk‑score summarisation** | Conditional counts of IUCN categories (CR, EN, VU, NT). | `risk_map` logic lines 189‑200. |
| **Fuzzy coordinate rendering** | Rounds latitude/longitude to one decimal place when user lacks permission. | `_fuzz_coordinate` line 50. |

### Example: Adding a new metric – “average observation accuracy”
1. Add a column `accuracy_meters` to the `observations` table (SQL migration).
2. Extend `StateMetricSummary` with `avg_accuracy: Optional[float]`.
3. Update `main_query` to compute `AVG(o.accuracy_meters)`.
4. Adjust `getChoroplethColor` or create a new shading mode to visualise the metric.

---

## 11. Software Testing Strategy

### 11.1 Unit Tests (backend)
- **Goal**: Test pure functions (`_fuzz_coordinate`, query‑building helpers) without a DB.
- **Tool**: `pytest` with `pytest‑asyncio` for FastAPI.
- **Example**:
```python
def test_fuzz_coordinate():
    assert _fuzz_coordinate(22.5435) == 22.5
    assert _fuzz_coordinate(-73.9876) == -74.0
```

### 11.2 Integration Tests (backend + DB)
- Use a **temporary PostgreSQL container** (via `docker‑compose up -d db_test`).
- Populate test data with `pytest fixtures`.
- Verify that `/spatial/states` returns correctly aggregated numbers and that fuzzy logic triggers for CR species.

### 11.3 Front‑end Component Tests (React)
- **Tool**: `@testing-library/react` and `jest`.
- Test `MapView` renders a `TileLayer`, loads GeoJSON, and displays a marker with a dashed border when `is_fuzzy` is true.
- Snapshot test for colour logic:
```tsx
test('getChoroplethColor returns red for CR risk', () => {
  const metric = { highest_risk_level: 'CR' } as any;
  expect(getChoroplethColor('Karnataka', { Karnataka: metric }, 'CONSERVATION_RISK')).toBe('#991b1b');
});
```

### 11.4 End‑to‑End (E2E) Tests
- **Tool**: `cypress`.
- Flow: login → open Dashboard → switch to "Choropleth" → verify that the colour legend updates and that a sensitive‑species marker shows a dashed border.
- Example command: `cypress run --spec cypress/integration/gis_spec.js`.

---

## 12. Test Plan Matrix

| Test ID | Scope | Type | Pre‑condition | Steps | Expected Result |
|---------|-------|------|----------------|-------|-----------------|
| **UT‑GIS‑01** | Fuzzy coordinate function | Unit | None | Call `_fuzz_coordinate(22.5435)` | Returns `22.5` |
| **IT‑GIS‑02** | `/spatial/states` aggregation | Integration | DB seeded with 3 observations in Maharashtra | GET `/spatial/states?state=MAHA` | `distinct_species_count == 2` and `risk_score_summary.highest='HIGH'` |
| **FE‑UT‑03** | MapView marker rendering | Front‑end unit | Mock observation with `is_fuzzy=true` | Render component, query for `.custom-leaflet-marker` | Element has `border-style: dashed` |
| **E2E‑04** | Role‑based location visibility | End‑to‑End | User logged in as `VIEWER` | Open state detail, inspect marker popup | Latitude shown is rounded to 1‑decimal place |
| **SEC‑05** | Unauthorized access | Integration | No JWT token | GET `/spatial/states` | HTTP 401 response |

---

## 13. Debugging & Logging Tips

1. **Backend** – All routes use `logger = logging.getLogger(__name__)`.  Look for `ERROR` level logs in `backend/logs/app.log`.
2. **SQL query inspection** – Append `EXPLAIN (ANALYZE, BUFFERS)` to the generated query in a dev console to see whether the GiST index is used.
3. **Front‑end** – Open browser dev tools → **Network** tab → filter by `/spatial/`.  Verify the response payload and status code.
4. **Leaflet map not rendering** – Ensure `css` for `.leaflet-container` is imported (`import 'leaflet/dist/leaflet.css';`).  Missing CSS leads to a blank map.
5. **Fuzzy marker still precise** – Confirm that the backend truly returned rounded coordinates (check `network` response).  If not, verify the user role via the JWT payload.

---

## 14. Presentation Script (5 minutes)

1. **Slide 1 – Title** – “GIS & Data Integration in NWCIP”.
2. **Slide 2 – Why GIS?** – Briefly mention biodiversity hot‑spot mapping and policy relevance.
3. **Slide 3 – Architecture** – Show the Mermaid diagram from Section 5; point out static GeoJSON vs dynamic API.
4. **Slide 4 – Sensitive Data** – Explain fuzzy coordinate logic, show before/after marker example.
5. **Slide 5 – External Data** – List GBIF, Protected Planet; describe planned import pipeline.
6. **Slide 6 – Testing** – Highlight unit, integration, and e2e tests; show a screenshot of a failing Cypress test and how it was fixed.
7. **Slide 7 – Demo** – Live‑run the map, toggle choropleth modes, switch to a CR‑species observation and demonstrate the dash border.
8. **Slide 8 – Take‑aways** – Emphasise privacy‑by‑design, reproducible analytics, and extensibility.

**Speaking tips**: keep each slide under 30 seconds, use the map visual as a story anchor, and pause for a quick question after the “Sensitive Data” slide.

---

## 15. Viva Questions & Model Answers (30)

| # | Question | Short Answer |
|---|----------|--------------|
| 1 | What does GIS stand for? | Geographic Information System. |
| 2 | Which coordinate reference system does NWCIP use? | EPSG:4326 (WGS‑84). |
| 3 | Why are coordinates stored as `(longitude, latitude)` in PostGIS? | `ST_Point(lon, lat)` expects that order; it matches GeoJSON. |
| 4 | How does the backend protect the location of Critically Endangered species? | It rounds the coordinate to one decimal place via `_fuzz_coordinate` when the caller lacks an authorized role. |
| 5 | What is a choropleth map? | A map where each polygon is coloured based on a statistical value (e.g., species richness). |
| 6 | Name the Leaflet component that renders vector features from GeoJSON. | `<GeoJSON>`. |
| 7 | Which HTTP status code indicates the client is unauthenticated? | 401 Unauthorized. |
| 8 | Which status code is returned when a viewer tries to see precise coordinates of a CR species? | 403 Forbidden. |
| 9 | What is the purpose of a GiST index? | Accelerates spatial queries such as `ST_Contains`. |
| 10 | How does the front‑end visually indicate a fuzzy location? | The marker icon uses a dashed border (`border-style: dashed`). |
| 11 | Which npm package provides testing utilities for React components? | `@testing-library/react`. |
| 12 | What command starts the Cypress test runner? | `npx cypress open` or `npx cypress run`. |
| 13 | Describe the flow of data from the database to the map when the user opens the dashboard. | DB → FastAPI `/spatial/states` → Pydantic models → JSON → Front‑end fetch → Leaflet GeoJSON overlay + markers. |
| 14 | What file contains the static state boundary GeoJSON? | `public/geo/india-states.geojson` (served via `/geo/india-states.geojson`). |
| 15 | How are risk levels colour‑coded? | CRITICAL – `#991b1b` (dark red), HIGH – `#ea580c` (orange), MEDIUM – `#eab308` (yellow), LOW – `#10b981` (emerald). |
| 16 | Which layer provides the base map tiles? | OpenStreetMap TileLayer (`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`). |
| 17 | What is the purpose of `StateMetricSummary`? | It groups aggregated statistics for a single state, used by both the API and the front‑end choropleth. |
| 18 | How does the back‑end ensure only authorised roles get precise locations? | `_is_authorized_for_precise_locations` checks `user.role` against `AUTHORIZED_ROLES`. |
| 19 | Give an example of a query parameter that filters observations by species. | `species_id=42`. |
| 20 | What is the default zoom level for the India view? | `5`. |
| 21 | Which testing level verifies that the API returns correct JSON schema? | Integration testing (using `TestClient` from FastAPI). |
| 22 | How would you add a new external data source, e.g., WorldClim climate layers? | Create a service module that fetches the raster, store it as a PostGIS raster table, expose an endpoint, and add a Leaflet `TileLayer` pointing to the raster tiles. |
| 23 | What does `ROW_NUMBER() OVER (PARTITION BY ...)` achieve in the SQL query? | It ranks observations per state so we can select the top‑N species. |
| 24 | Why is it important to use `response.ok` in the fetch wrapper? | To surface HTTP error codes instead of silently parsing error bodies. |
| 25 | What are the main categories of GIS data? | Raster and Vector. |
| 26 | How many Indian states/UTs does the map cover? | 37 (including Union Territories). |
| 27 | Which Python library provides the `BaseModel` used for response schemas? | Pydantic. |
| 28 | What command would you run to lint TypeScript files in the front‑end? | `npm run lint` (assuming `eslint` is configured). |
| 29 | How can you verify that the GiST index is being used? | Run `EXPLAIN (ANALYZE, BUFFERS)` on the query and look for `Bitmap Heap Scan` with an `Index Scan using <index_name>`. |
| 30 | If a user reports that the map appears blank, what three things do you check first? | 1) Leaflet CSS imported, 2) TileLayer URL reachable, 3) GeoJSON files loaded successfully (network tab). |

---

## 16. Technical Glossary
- **API** – Application Programming Interface, a contract that defines how software components communicate.
- **Choropleth** – A thematic map where areas are coloured according to a statistical variable.
- **CR / EN** – IUCN Red List categories *Critically Endangered* and *Endangered*.
- **GeoJSON** – JSON format for encoding a variety of geographic data structures.
- **GiST** – Generalized Search Tree, a PostgreSQL index type for spatial data.
- **Leaflet** – JavaScript library for interactive maps.
- **POSTGIS** – Spatial extension for PostgreSQL enabling geometry operations.
- **Pydantic** – Data validation library used by FastAPI for request/response models.
- **Redux / Context** – State‑management approaches (NWCIP uses React Context for auth).
- **CORS** – Cross‑Origin Resource Sharing – controlled by FastAPI middleware.
- **E2E** – End‑to‑End testing, simulating real user interactions.

---

## 17. Revision Notes & Checklist
- [ ] Verify that `backend/app/routers/spatial.py` imports `StateMetricSummary` from `schemas/spatial.py`.
- [ ] Confirm that the front‑end `MapView` uses `createCustomIcon` to indicate fuzzy locations.
- [ ] Run `npm test` → ensure all React component tests pass.
- [ ] Run `pytest -q` → all backend unit/integration tests pass.
- [ ] Execute `cypress run` – check that the role‑based access test (`E2E‑04`) succeeds.
- [ ] Generate a PDF from this markdown (user will run `pandoc`).
- [ ] Update the repository README with a link to the new `docs/anwesha_gis_integration_testing.md`.

---

*Prepared by the Antigravity AI assistant for the NWCIP project, aimed at helping Anwesha master GIS integration and testing.*

