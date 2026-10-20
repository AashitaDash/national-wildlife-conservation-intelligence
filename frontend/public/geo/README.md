# /geo — Static Geographic Assets

## india-boundary.geojson

**Source:** Esri India / Survey of India — India Administrative Boundaries 2024
**Service URL:** https://livingatlas.esri.in/server/rest/services/IAB2024/India_Administrative_Boundaries_2024/MapServer/0
**Accessed:** 2026-10-07

### Usage
This file is served as a static public asset (`/geo/india-boundary.geojson`) and loaded by the React Leaflet `MapView` component as the national boundary reference layer.

### Attribution
Map data © Esri India / Survey of India, India Administrative Boundaries 2024. Simplified version for display purposes only.

---

## india-states.geojson

**Source:** Survey of India / Bharat Administrative Boundaries (Census of India, Survey of India, Open Government Data Platform India / DataMeet open geospatial mapping project under Open Database License / Creative Commons Attribution-ShareAlike 4.0).
**Coverage:** 37 States and Union Territories of the Republic of India including Jammu & Kashmir, Ladakh, and Telangana.
**Geometry Format:** WGS84 (EPSG:4326) GeoJSON FeatureCollection.
**Standardized Properties:**
- `st_nm`: Canonical State / UT name.
- `state_name`: Canonical State / UT name.
- `name`: Canonical State / UT name.

### Usage
1. **Frontend**: Bundled in `frontend/public/geo/india-states.geojson` for client-side React Leaflet GeoJSON choropleth layers with instant render performance.
2. **Backend**: Stored in `backend/app/data/india-states.geojson` and imported into PostgreSQL/PostGIS spatial polygon tables (`state_boundaries`) for deterministic, spatial joins (`ST_Contains(geom, ST_SetSRID(ST_Point(lon, lat), 4326))`).
