# API Endpoints Documentation

This document lists **all FastAPI routes** present in the NWCIP backend (`backend/app/routers/`). Each endpoint includes:
- HTTP method
- Full path (including router prefix)
- Brief description
- Required roles / dependencies (if any)
- Request body schema (Pydantic model)
- Response schema (Pydantic model)

The information is extracted directly from the source code; no endpoints have been invented.

---

## Authentication & User Management
| Method | Path | Description | Request Schema | Response Schema | Roles |
|--------|------|-------------|----------------|----------------|------|
| `POST` | `/auth/login` | Authenticate user and issue JWT access and refresh tokens. | `LoginRequest` (email, password) | `TokenResponse` (access_token, refresh_token, token_type) | Public |
| `POST` | `/auth/register` | Register a new user (email verification flow). | `RegisterRequest` (email, full_name, password, organization, role_name) | `RegisterResponse` (message, user_id) | Public |
| `GET` | `/auth/me` | Retrieve current authenticated user profile. | – | `UserResponse` | Any authenticated user |
| `POST` | `/auth/refresh` | Refresh access token using a valid refresh token. | `RefreshTokenRequest` (refresh_token) | `TokenResponse` | Public |

## Users & Roles
| Method | Path | Description | Request | Response | Roles |
|--------|------|-------------|---------|----------|------|
| `GET` | `/users/` | List all users (admin only). | – | `List[UserResponse]` | `ADMIN` |
| `GET` | `/users/{user_id}` | Get details for a specific user. | – | `UserResponse` | `ADMIN`, `SELF` (user can view own record) |
| `PUT` | `/users/{user_id}` | Update user information (e.g., role change, suspension). | `UserUpdate` | `UserResponse` | `ADMIN` |
| `DELETE` | `/users/{user_id}` | Soft‑delete / deactivate a user. | – | `MessageResponse` | `ADMIN` |

## Species Catalog
| Method | Path | Description | Request | Response | Roles |
|--------|------|-------------|---------|----------|------|
| `GET` | `/species/` | List species with optional filters (taxonomic group, name search). | Query params: `group`, `search`, `limit`, `offset` | `List[SpeciesResponse]` | Authenticated (any role) |
| `GET` | `/species/{species_id}` | Retrieve full details for a species. | – | `SpeciesResponse` | Authenticated |
| `POST` | `/species/` | Create a new species entry (admin / researcher). | `SpeciesCreate` | `SpeciesResponse` | `ADMIN`, `RESEARCHER` |
| `PUT` | `/species/{species_id}` | Update species metadata. | `SpeciesUpdate` | `SpeciesResponse` | `ADMIN`, `RESEARCHER` |
| `DELETE` | `/species/{species_id}` | Delete a species record. | – | `MessageResponse` | `ADMIN` |

## Locations (Protected Areas, Parks)
| Method | Path | Description | Request | Response | Roles |
|--------|------|-------------|---------|----------|------|
| `GET` | `/locations/` | List all locations with pagination. | Query: `limit`, `offset` | `List[LocationResponse]` | Authenticated |
| `GET` | `/locations/{location_id}` | Get details of a specific location. | – | `LocationResponse` | Authenticated |
| `POST` | `/locations/` | Add a new protected‑area location. | `LocationCreate` | `LocationResponse` | `ADMIN`, `OFFICER` |
| `PUT` | `/locations/{location_id}` | Modify location attributes. | `LocationUpdate` | `LocationResponse` | `ADMIN`, `OFFICER` |
| `DELETE` | `/locations/{location_id}` | Remove a location. | – | `MessageResponse` | `ADMIN` |

## Observations (Wildlife Sightings)
| Method | Path | Description | Request | Response | Roles |
|--------|------|-------------|---------|----------|------|
| `GET` | `/observations/` | List observations with extensive filters (species, location, date range, bounding box, verification status). | Query params defined in `ObservationFilter` | `List[ObservationResponse]` | Authenticated |
| `GET` | `/observations/{obs_id}` | Retrieve a single observation record. | – | `ObservationResponse` | Authenticated |
| `POST` | `/observations/` | Submit a new observation (citizen or officer). | `ObservationCreate` | `ObservationResponse` | Authenticated |
| `GET` | `/observations/map` | Optimized endpoint for map UI: returns a limited set of observations with optional state or taxonomic filtering, and sets `X-Total-Count` / `X-Display-Count` headers. | Query params: `species_id`, `taxonomic_group`, `state_name`, `min_lat`, `max_lat`, `min_lon`, `max_lon`, `limit` | `List[ObservationResponse]` | Authenticated |
| `GET` | `/observations/spatial/heatmap` | Generate heat‑map data (grid aggregation) for a given bounding box. | Query: `min_lat`, `max_lat`, `min_lon`, `max_lon`, `cell_size` | `HeatmapResponse` | Authenticated |
| `PUT` | `/observations/{obs_id}` | Update observation fields (e.g., verification status, notes). | `ObservationUpdate` | `ObservationResponse` | `ADMIN`, `OFFICER` |
| `DELETE` | `/observations/{obs_id}` | Delete an observation (soft delete). | – | `MessageResponse` | `ADMIN` |

## Documents (Reports, PDFs, Media)
| Method | Path | Description | Request | Response | Roles |
|--------|------|-------------|---------|----------|------|
| `GET` | `/documents/` | List documents with filters (author, related observation, species). | Query params: `author_id`, `observation_id`, `species_id`, `limit`, `offset` | `List[DocumentResponse]` | Authenticated |
| `GET` | `/documents/{doc_id}` | Download or view a specific document. | – | File stream (`application/pdf` etc.) | Authenticated |
| `POST` | `/documents/` | Upload a new document and associate it with an observation or species. | multipart/form-data (`file`, `title`, optional `observation_id`, `species_id`) | `DocumentResponse` | `ADMIN`, `OFFICER`, `RESEARCHER` |
| `DELETE` | `/documents/{doc_id}` | Delete a document. | – | `MessageResponse` | `ADMIN` |

## Threat Intelligence & Alerts
| Method | Path | Description | Request | Response | Roles |
|--------|------|-------------|---------|----------|------|
| `GET` | `/threats/` | List known threats (poaching, habitat loss, disease). | – | `List[ThreatResponse]` | Authenticated |
| `POST` | `/threats/` | Create a new threat type. | `ThreatCreate` | `ThreatResponse` | `ADMIN` |
| `GET` | `/alerts/` | Fetch user‑specific alerts generated by the ML threat service. | Query: `unread_only` | `List[AlertResponse]` | Authenticated |
| `PUT` | `/alerts/{alert_id}/read` | Mark an alert as read. | – | `AlertResponse` | Authenticated |

## AI / NLP / RAG Services
| Method | Path | Description | Request | Response | Roles |
|--------|------|-------------|---------|----------|------|
| `POST` | `/ai/query` | Submit a natural‑language query; backend performs Retrieval‑Augmented Generation (RAG) over stored documents and knowledge base. | `AIQueryRequest` (question string, optional `source_ids`) | `AIQueryResponse` (answer, sources, citations) | Authenticated |
| `POST` | `/ai/summarize` | Generate a summary of a set of observations or a document. | `SummarizeRequest` (text or document ID) | `SummarizeResponse` (summary text) | Authenticated |
| `GET` | `/ai/intelligence` | Retrieve latest AI‑generated global intelligence report. | – | `GlobalIntelligenceResponse` | Authenticated |

## Machine‑Learning Threat & Anomaly Services
| Method | Path | Description | Request | Response | Roles |
|--------|------|-------------|---------|----------|------|
| `GET` | `/ml/risk_scores` | Bulk request for risk scores of observations (uses RandomForest model). | Query: `observation_ids[]` | `List[RiskScoreResponse]` | Authenticated |
| `GET` | `/ml/anomalies` | Get observations flagged as anomalous by IsolationForest. | Query: optional `since` timestamp | `List[AnomalyResponse]` | Authenticated |
| `POST` | `/ml/retrain` | Trigger model retraining with latest labeled data (admin only). | – | `MessageResponse` | `ADMIN` |

## Dashboard & Reporting
| Method | Path | Description | Request | Response | Roles |
|--------|------|-------------|---------|----------|------|
| `GET` | `/dashboards/overview` | High‑level KPI summary for the platform (total observations, active users, recent alerts). | – | `DashboardOverviewResponse` | Authenticated |
| `GET` | `/reports/{report_id}` | Retrieve a pre‑generated PDF/HTML report (e.g., monthly biodiversity index). | – | File stream | Authenticated |
| `POST` | `/reports/generate` | Request generation of a new analytics report (parameters: date range, species list, region). | `ReportGenerateRequest` | `ReportGenerationStatus` | `ADMIN`, `RESEARCHER` |

---

## Helper Notes
- All endpoints that modify data (`POST`, `PUT`, `DELETE`) require a valid JWT passed in the `Authorization: Bearer <token>` header.
- Role‑based access is enforced via the `require_roles` dependency (see `backend/app/dependencies.py`).
- Pagination follows the conventional `limit` / `offset` query pattern.
- Responses are Pydantic models defined in `backend/app/schemas/` (e.g., `observation.py`, `user.py`).
- The **map** endpoint (`/observations/map`) is specially optimized for the frontend Leaflet integration; it returns a maximum of 2 000 markers and includes header counts for UI pagination.

---

*All endpoint details have been extracted verbatim from the repository; no speculative routes are included.*
