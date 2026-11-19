# External Data Sources

## Overview
The platform seeds biodiversity telemetry from a curated set of **public and governmental APIs**. The seeder lives in `backend/app/services/seed_service.py` and is executed on first‑run (idempotent).

## Listed Sources
| # | Data Provider | URL |
|---|---------------|-----|
| 1 | GBIF India | https://gbif.org |
| 2 | iNaturalist India | https://inaturalist.org |
| 3 | eBird India | https://ebird.org |
| 4 | WII Field Rangers | https://wii.gov.in |
| 5 | WWF India | https://wwfindia.org |
| 6 | Citizen Science Portal | (no public URL – internal UI) |
| 7 | Researcher Submission | (manual upload) |

The list is defined in the seeder as:
```python
SOURCES = [
    ("GBIF India", "https://gbif.org"),
    ("iNaturalist India", "https://inaturalist.org"),
    ("eBird India", "https://ebird.org"),
    ("WII Field Rangers", "https://wii.gov.in"),
    ("WWF India", "https://wwfindia.org"),
    ("Citizen Science Portal", None),
    ("Researcher Submission", None),
]
```

### How they are used
* **Ingestion pipelines** read raw telemetry from these endpoints (via `requests` or specialised clients) – the code lives in the same `seed_service.py` under the heading *"Populates the Wildlife Conservation Intelligence Platform with realistic, consistent Indian biodiversity data"*.
* Each source becomes a row in the `data_sources` table (`backend/app/models/observation.py` → `DataSource` model) and is referenced by every `Observation` record (`source_id` foreign key).
* The frontend displays the provenance of observations in the state‑detail view (`backend/app/routers/spatial.py` → `sources_query`).

---
*All file references are relative to the repository root.*

