# GIS Implementation

## Overview
The GIS module visualises state‑wise wildlife intelligence on an interactive map using **Leaflet** (React‑Leaflet) in the frontend and **PostGIS** spatial queries in the FastAPI backend.

## Backend – Spatial Router (`backend/app/routers/spatial.py`)
```python
# File: backend/app/routers/spatial.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text, func

router = APIRouter(prefix="/spatial", tags=["Spatial Wildlife Intelligence & State Choropleths"])

# Sensitive categories that trigger coordinate fuzzing
SENSITIVE_IUCN_CATEGORIES = {"CR", "EN"}
AUTHORIZED_ROLES = {"ADMIN", "FOREST_OFFICER", "RESEARCHER"}

def _is_authorized_for_precise_locations(user: Optional[User]) -> bool:
    if not user or not user.is_active:
        return False
    user_role = user.role.name.upper() if user.role else ""
    return user_role in AUTHORIZED_ROLES

def _fuzz_coordinate(val: float) -> float:
    # Round to 1 decimal place (~11 km grid) to hide exact locations of CR/EN species
    return round(val, 1)
```

### Key Queries
* **State‑wise aggregation** – joins `observations` with `state_boundaries` using `ST_Contains`.
* **Taxonomic breakdown**, **top species**, **data provenance**, and **risk scores** are all assembled in a single request.
* When a user lacks the required role, coordinates of endangered species are fuzzed via `_fuzz_coordinate` before being returned.

## Frontend – Map View (`frontend/src/components/MapView.tsx`)
```tsx
// File: frontend/src/components/MapView.tsx
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';

// Custom marker with optional fuzzy‑style dash
const createCustomIcon = (color = '#10b981', selected = false, isFuzzy = false) => {
  const size = selected ? 18 : 12;
  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `<div style="
      background-color: ${color};
      width: ${size}px;
      height: ${size}px;
      border-radius: 50%;
      border: 2px solid #ffffff;
      box-shadow: 0 0 ${selected ? 12 : 6}px ${color};
      ${isFuzzy ? 'border-style: dashed; opacity: 0.85;' : ''}
      transition: all 0.15s ease;`>
      </div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};
```

### Choropleth colour scaling
```tsx
export function getChoroplethColor(
  stateName: string,
  stateMetrics: Record<string, StateMetricSummary> | undefined,
  shadingMode: ChoroplethShading,
): string {
  if (!stateMetrics) return '#e5e2da';
  const metric = stateMetrics[stateName];
  if (!metric) return '#f4f2ec';
  if (shadingMode === 'CONSERVATION_RISK') {
    const risk = (metric.highest_risk_level || 'LOW').toUpperCase();
    if (risk === 'CRITICAL') return '#991b1b';
    if (risk === 'HIGH') return '#ea580c';
    if (risk === 'MEDIUM') return '#eab308';
    return '#10b981';
  }
  // numeric metrics omitted for brevity …
}
```

## Data Flow
1. **API call** → `GET /spatial/states` returns a JSON payload containing aggregated metrics per state.
2. Frontend fetches `india-states.geojson` (static vector file) and overlays the metrics using the choropleth colour function.
3. When a user clicks a state, `GET /spatial/states/{state_name}` supplies detailed observations; the map renders markers with `createCustomIcon`, applying fuzzy styling for sensitive species if the user is not authorized.

## Security & Privacy
* Coordinate fuzzing (`_fuzz_coordinate`) is enforced server‑side; the frontend only receives the already‑obfuscated values.
* Role‑based access is checked via `_is_authorized_for_precise_locations`.
* No raw latitude/longitude of **CR** or **EN** species is ever exposed to public/viewer accounts.

---
*All file references are relative to the repository root.*

