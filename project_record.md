---
title: WILDLIFE CONSERVATION INTELLIGENCE PLATFORM
author:
  - Aashita Dash — 2305266
  - Anurag Mukherjee — 2305283
  - Kiran Mohapatra — 2305299
  - Bhavya Shrivastava — 23052071
  - Anwesha Panda — 23053376
---
<div class="cover-page">
    <br><br><br>
    <h1>WILDLIFE CONSERVATION INTELLIGENCE PLATFORM</h1>
    <h2>AI-Assisted Wildlife Conservation Intelligence and Decision-Support Platform</h2>
    <br><br>
    <p><strong>A Final Year Project Report</strong></p>
    <p>Submitted in partial fulfillment of the requirements for the degree of</p>
    <p><strong>Bachelor of Technology in Computer Science & Engineering</strong></p>
    <br><br>
    <p>By:</p>
    <p><strong>Aashita Dash — 2305266</strong><br>
    <strong>Anurag Mukherjee — 2305283</strong><br>
    <strong>Kiran Mohapatra — 2305299</strong><br>
    <strong>Bhavya Shrivastava — 23052071</strong><br>
    <strong>Anwesha Panda — 23053376</strong></p>
    <br><br>
    <p>Project Guide: <strong>Mr. Sovan Kumar Sahoo</strong></p>
    <p>7th Semester</p>
    <br>
    <p><strong>KIIT Deemed University</strong></p>
</div>

<div class="page-break"></div>

## CERTIFICATE

This is to certify that the project report entitled **"WILDLIFE CONSERVATION INTELLIGENCE PLATFORM"** is a bona fide record of work carried out by **Aashita Dash, Anurag Mukherjee, Kiran Mohapatra, Bhavya Shrivastava, and Anwesha Panda** under my supervision and guidance, in partial fulfillment of the requirements for the award of the Degree of Bachelor of Technology in Computer Science & Engineering at KIIT Deemed University.

<br><br><br><br>
__________________________<br>
**Mr. Sovan Kumar Sahoo**<br>
Project Guide<br>
KIIT Deemed University

<div class="page-break"></div>

## DECLARATION

We hereby declare that the project report entitled **"WILDLIFE CONSERVATION INTELLIGENCE PLATFORM"** submitted for the degree of Bachelor of Technology in Computer Science & Engineering is our original work and the project has not formed the basis for the award of any degree, diploma, associate-ship, fellowship or similar other titles.

<br><br><br>
__________________________<br>
Aashita Dash — 2305266<br><br>
__________________________<br>
Anurag Mukherjee — 2305283<br><br>
__________________________<br>
Kiran Mohapatra — 2305299<br><br>
__________________________<br>
Bhavya Shrivastava — 23052071<br><br>
__________________________<br>
Anwesha Panda — 23053376<br>

<div class="page-break"></div>

## ACKNOWLEDGEMENT

We would like to express our profound gratitude to our project guide, Mr. Sovan Kumar Sahoo, for his continuous support, encouragement, and invaluable guidance throughout the course of this project. His expertise and constructive feedback have been instrumental in the successful completion of this work.

We extend our sincere thanks to the Department of Computer Science & Engineering, KIIT Deemed University, for providing us with the resources and facilities necessary for our research and development. 

Finally, we would like to thank our families and friends for their unwavering moral support.

<div class="page-break"></div>

## ABSTRACT

Biodiversity loss is one of the most pressing environmental challenges of our time. Traditional wildlife conservation efforts often rely on fragmented data sources, making it difficult for researchers and policymakers to gain a comprehensive and actionable view of species health and distribution. To address this, we developed the **Wildlife Conservation Intelligence Platform**, an AI-assisted decision-support system designed to integrate disparate biodiversity data streams into a unified, intelligent interface.

The platform aggregates 39,066 real-world biodiversity observations across 313 species native to the Indian subcontinent, drawing from prominent sources such as GBIF, iNaturalist, eBird, and government reports. Data is ingested, cleaned, and deduplicated using an automated pipeline, enriched with conservation status indicators from the IUCN Red List, and stored in a robust PostgreSQL database. 

A natural language processing (NLP) module, powered by SentenceTransformer embeddings (all-MiniLM-L6-v2) and rule-based extraction, enables semantic search and automated threat detection from unstructured conservation documents. Furthermore, a Random Forest machine learning model generates decision-support risk indicators based on geographic spread, observation trends, and threat frequencies, supplemented by an Isolation Forest for anomaly detection.

The system is delivered via a modern, role-based web application (React, TypeScript, Vite) interacting with a highly optimized Python FastAPI backend. By providing geospatial mapping, predictive risk analysis, and comprehensive species registries, the Wildlife Conservation Intelligence Platform empowers conservationists with data-driven insights necessary for proactive environmental stewardship.

<div class="page-break"></div>

## TABLE OF CONTENTS

1. **CHAPTER 1 — INTRODUCTION**
2. **CHAPTER 2 — EXISTING SYSTEM AND LITERATURE / DOMAIN STUDY**
3. **CHAPTER 3 — REQUIREMENT ANALYSIS**
4. **CHAPTER 4 — SYSTEM ANALYSIS AND DESIGN**
5. **CHAPTER 5 — DATA SOURCES AND DATA INGESTION**
6. **CHAPTER 6 — DATABASE DESIGN**
7. **CHAPTER 7 — NATURAL LANGUAGE PROCESSING**
8. **CHAPTER 8 — MACHINE LEARNING**
9. **CHAPTER 9 — GEOSPATIAL INTELLIGENCE**
10. **CHAPTER 10 — BACKEND IMPLEMENTATION**
11. **CHAPTER 11 — AUTHENTICATION AND RBAC**
12. **CHAPTER 12 — FRONTEND IMPLEMENTATION**
13. **CHAPTER 13 — IMPLEMENTATION DETAILS**
14. **CHAPTER 14 — TESTING AND VALIDATION**
15. **CHAPTER 15 — RESULTS AND DISCUSSION**
16. **CHAPTER 16 — LIMITATIONS**
17. **CHAPTER 17 — FUTURE SCOPE**
18. **CHAPTER 18 — CONCLUSION**

<div class="page-break"></div>

## CHAPTER 1 — INTRODUCTION

### 1.1 Background
The rapid decline of global biodiversity demands urgent and effective conservation strategies. With countless species facing the threat of extinction due to habitat loss, climate change, and human-wildlife conflict, data-driven decision-making has never been more critical. The Indian subcontinent, renowned for its rich and diverse ecosystems, serves as a crucial region for wildlife conservation. 

### 1.2 Wildlife Conservation Context
Effective conservation requires a thorough understanding of species distribution, population trends, and environmental threats. Conservationists rely on observation data, environmental reports, and academic research. However, this data is often siloed, making real-time analysis difficult.

### 1.3 Problem Statement
Currently, biodiversity data is fragmented across various platforms such as GBIF, iNaturalist, and eBird, alongside unstructured PDF reports from government and NGOs. There is a lack of a unified platform that not only aggregates this data but also applies artificial intelligence to extract meaningful insights, detect anomalies, and provide actionable risk assessments.

### 1.4 Motivation
The motivation for this project stems from the need to bridge the gap between raw biodiversity data and actionable conservation intelligence. By leveraging modern software architecture, Machine Learning (ML), and Natural Language Processing (NLP), we can significantly reduce the cognitive load on researchers and policymakers.

### 1.5 Need for the System
A comprehensive intelligence platform is needed to provide a single source of truth for species observations, automatically identify emerging threats from text, and flag species that are exhibiting anomalous observation patterns indicative of ecological distress.

### 1.6 Proposed Solution
We propose the **Wildlife Conservation Intelligence Platform**, an integrated decision-support system that ingests observations from multiple sources, processes unstructured text to find threats, visualizes data geographically, and uses ML to assess conservation risks.

### 1.7 Objectives
1. To develop a reliable data ingestion pipeline for real-world biodiversity data.
2. To implement a secure, scalable backend and an intuitive frontend dashboard.
3. To apply NLP for extracting threats and enabling semantic search across documents.
4. To utilize ML for calculating decision-support risk scores and detecting data anomalies.
5. To provide role-based access control (RBAC) ensuring data security and integrity.

### 1.8 Scope
The current scope is focused on 313 key species within the Indian context, encompassing Aves, Mammalia, Reptilia, and Amphibia. It includes 39,066 verified observation records. The platform provides decision-support metrics, not definitive extinction predictions.

### 1.9 Key Contributions
- Aggregation of 39,066 deduplicated observation records across 313 species.
- A functional NLP pipeline using SentenceTransformer embeddings for semantic search.
- An ML-driven risk assessment model utilizing Random Forest and Isolation Forest.
- A fully realized, interactive web application tailored for diverse conservation stakeholders.

<div class="page-break"></div>

## CHAPTER 2 — EXISTING SYSTEM AND LITERATURE / DOMAIN STUDY

### 2.1 Existing Wildlife Data Platforms
Platforms like GBIF (Global Biodiversity Information Facility) and iNaturalist serve as excellent repositories for occurrence data. However, they are primarily data hosts rather than intelligence platforms. They do not natively integrate automated text analysis of conservation reports or predictive risk modeling.

### 2.2 Biodiversity Observation Sources
Data is collected globally via citizen science (eBird, iNaturalist) and professional scientific surveys (GBIF, government data). The volume is immense, requiring careful deduplication and standardization.

### 2.3 Limitations of Fragmented Biodiversity Data
Researchers currently must manually cross-reference IUCN Red List status with GBIF occurrences and unstructured government PDFs. This manual process is slow, prone to error, and limits proactive conservation.

### 2.4 Existing Approaches to Conservation Intelligence
While some specialized tools exist for specific tasks (e.g., spatial mapping via ArcGIS), there is a distinct lack of open-source or easily accessible platforms that combine geospatial mapping, NLP, and ML into a single, cohesive user experience.

### 2.5 Need for Integrated Intelligence
An integrated system ensures that an observation of a rare species in a specific location can be immediately cross-referenced against known threats extracted from recent documents, resulting in a dynamic risk score.

### 2.6 Comparative Analysis
Unlike raw data portals, our platform provides *synthesized intelligence*. It goes beyond displaying points on a map by offering a calculated ML Risk Score and highlighting NLP-extracted threats.

### 2.7 Research / Technical Gap
There is a clear technical gap in applying lightweight, efficient NLP (like SentenceTransformers) and traditional ML (Random Forests) directly to aggregated local biodiversity pipelines to create a real-time decision-support dashboard for Indian wildlife.

<div class="page-break"></div>

## CHAPTER 3 — REQUIREMENT ANALYSIS

### 3.1 Functional Requirements
- The system must ingest and deduplicate data from GBIF, iNaturalist, and eBird.
- The system must display a species registry and individual species profiles.
- The system must render a spatial map of species occurrences.
- The system must process text documents to extract threats and enable semantic search.
- The system must calculate a risk score for species with sufficient observation data.

### 3.2 Non-Functional Requirements
- **Performance:** The API should respond within acceptable timeframes (<500ms for standard queries).
- **Scalability:** The database must handle tens of thousands of observation records efficiently.
- **Usability:** The frontend must be responsive and intuitive.
- **Security:** Passwords must be hashed; API endpoints must be protected by JWT.

### 3.3 User Roles
- **Admin:** Full system access.
- **Forest Officer:** Can view all intelligence and sensitive anomalies.
- **Researcher:** Can access data, NLP, and ML insights.
- **Citizen / Viewer:** Read-only access to public observations.

### 3.4 Hardware Requirements
- Server: Multi-core CPU, minimum 8GB RAM for running Python backend and vector operations.
- Client: Modern web browser (Chrome, Firefox, Safari).

### 3.5 Software Requirements
- Backend: Python 3.10+, FastAPI, SQLAlchemy.
- Frontend: Node.js, React, Vite, TypeScript.
- Database: PostgreSQL (with PostGIS and pgvector extensions available, though core implementation utilizes standard relational capabilities).

### 3.6 Technology Stack
- **Frontend:** React, Tailwind CSS, TypeScript
- **Backend:** FastAPI (Python), Pydantic
- **Database:** PostgreSQL
- **ML/NLP:** Scikit-learn, SentenceTransformers (all-MiniLM-L6-v2), NLTK

### 3.7 API/Data Source Requirements
- External APIs: GBIF API, iNaturalist API, eBird API, IUCN Red List API.

### 3.8 Security Requirements
- Implementation of OAuth2 with Password Flow and JWT tokens.
- Role-Based Access Control (RBAC) middleware for FastAPI.

<div class="page-break"></div>

## CHAPTER 4 — SYSTEM ANALYSIS AND DESIGN

### 4.1 High-Level Architecture
The system follows a modern client-server architecture. The React frontend communicates via RESTful APIs with the FastAPI backend, which handles business logic, ML inference, and NLP processing, backed by a PostgreSQL database.

### 4.2 System Components
1. **Data Ingestion Engine:** Scripts to fetch, clean, and store data.
2. **Core API:** FastAPI application routing requests.
3. **ML Service:** Generates risk scores and anomalies.
4. **NLP Service:** Processes text and handles semantic search.
5. **Web Client:** The React-based user interface.

### 4.3 End-to-End Data Flow
External APIs -> Ingestion Script -> Normalization/Deduplication -> PostgreSQL -> FastAPI -> React UI.

### 4.4 Data Ingestion Architecture
The ingestion architecture utilizes Python scripts that query external APIs based on scientific names. It normalizes responses into a common `Observation` schema, creates a unique fingerprint (species, coordinates, date) for deduplication, and performs bulk inserts.

### 4.5 NLP Architecture
The NLP pipeline utilizes `all-MiniLM-L6-v2` for generating 384-dimensional sentence embeddings. The embeddings are stored in JSON arrays in PostgreSQL, and semantic search is performed via NumPy cosine similarity at runtime (providing a deterministic, fallback mechanism). Rule-based regex and gazetteers handle entity and threat extraction.

### 4.6 Machine Learning Architecture
A Scikit-learn `RandomForestRegressor` is trained on heuristically generated labels based on core features (recent observation trends, threat frequency, geographic spread). An `IsolationForest` identifies statistical anomalies in the observation data.

### 4.7 Search Architecture
A hybrid approach: keyword search for species names using SQL `ILIKE`, and semantic search for document contents using embedding cosine similarity.

### 4.8 Geospatial Architecture
Coordinates (latitude/longitude) are stored in standard float columns in PostgreSQL. The backend filters observations within bounding boxes passed from the frontend map viewport.

### 4.9 Authentication Architecture
Standard JWT (JSON Web Token) implementation. Passwords are hashed using bcrypt.

### 4.10 Role-Based Access Control
FastAPI dependencies check the user's role stored in the JWT payload before granting access to protected endpoints.

### 4.11 Frontend Architecture
A Single Page Application (SPA) built with React. State is managed via React hooks. Routing is handled by React Router. Components are styled using vanilla CSS/Tailwind principles.

### 4.12 Backend Architecture
Follows a modular pattern: `routers/` for API endpoints, `services/` for business logic, `models/` for SQLAlchemy ORM definitions, and `schemas/` for Pydantic validation.

<div class="page-break"></div>

## CHAPTER 5 — DATA SOURCES AND DATA INGESTION

### 5.1 GBIF
The Global Biodiversity Information Facility (GBIF) provides the bulk of historical and global occurrence observations.

### 5.2 iNaturalist
Provides highly verified, community-driven observations and serves as a primary source for enriching the database with species photographs.

### 5.3 eBird
Specifically targeted for avian species, providing high-fidelity bird watching records.

### 5.4 IUCN Red List
Used strictly for conservation-status enrichment (e.g., classifying a species as Vulnerable, Endangered). It does not supply observation coordinate data.

### 5.5 Government / Conservation Records
Simulated or imported unstructured reports that are processed by the NLP engine.

### 5.6 API Integration
Python clients utilizing the `requests` library interact with the respective REST APIs.

### 5.7 Data Fetching
Data is fetched in batches using pagination to respect API rate limits.

### 5.8 Validation
Coordinates are validated to ensure they fall within acceptable ranges (e.g., within the Indian subcontinent bounding box).

### 5.9 Normalization
Varying API response formats are mapped to a unified internal dictionary before database insertion.

### 5.10 Species Matching
Incoming records are strictly matched against the 313 predefined species in the catalog using exact scientific name matching.

### 5.11 Deduplication
To prevent inflated observation counts, a robust deduplication mechanism was implemented. In addition to tracking unique source IDs, the system checks a fingerprint of `(species_id, latitude, longitude, observed_at)`. The final cleanup resulted in exactly 40 duplicate source-ID rows removed, leaving 39,066 distinct observations.

### 5.12 Image Enrichment
The `enrich_species_images.py` script queries the iNaturalist API to retrieve representative, high-quality photos for species. 311 out of 313 species have successfully been enriched with verified photos.

### 5.13 Observation Storage
Data is persisted to the `observations` table using SQLAlchemy bulk insert operations for efficiency.

### 5.14 Provenance / Source Tracking
Every observation retains its original source (e.g., GBIF) and its external source ID in a JSON `raw_metadata` column to ensure traceability.

### 5.15 Error Handling and Fallbacks
The ingestion scripts implement retry logic and graceful fallbacks for missing data fields (e.g., missing observation dates default to the ingestion date with a flag).

<div class="page-break"></div>

## CHAPTER 6 — DATABASE DESIGN

### 6.1 Database Selection
PostgreSQL was selected for its robustness, ACID compliance, and excellent support for JSON data types.

### 6.2 PostgreSQL
The core relational engine handles complex joins between species, observations, and NLP documents.

### 6.3 PostGIS & 6.4 pgvector
While PostgreSQL is configured in the environment, the current architecture relies on standard relational structures. Latitude and longitude are stored as floats. Embeddings are stored in JSON and processed in application memory. Native pgvector and PostGIS implementations are designated as future scope.

### 6.5 Database Schema
The schema is highly normalized. 

### 6.6 Entity Relationships
- A `Species` has many `Observations`.
- A `Species` has many `Documents`.
- A `Species` has one `MLRiskScore`.
- A `User` has one `Role`.

### 6.7 Species Table
Stores taxonomic information: `id`, `common_name`, `scientific_name`, `class_name`, `iucn_category`, `image_url`.

### 6.8 Observation Table
Stores spatial data: `id`, `species_id`, `latitude`, `longitude`, `observed_at`, `source_id`, `raw_metadata`.

### 6.9 User and Role Tables
Manage RBAC. `User` contains hashed passwords and links to a `Role`.

### 6.10 Document/NLP Tables
`Document` stores textual reports. `DocumentEmbedding` stores the 384-dimensional vector as a JSON array.

### 6.11 ML/Risk Tables
`MLRiskScore` caches the output of the Random Forest model to prevent real-time re-computation delays.

### 6.12 Alerts
The `Alert` table stores anomalies generated by the Isolation Forest.

### 6.13 Indexing
B-Tree indexes are applied to `scientific_name`, `species_id`, and `observed_at` to optimize query performance.

### 6.14 Data Integrity
Foreign keys enforce referential integrity. Deleting a species cascades to its observations.

### 6.15 Relationships and Constraints
Constraints ensure non-null critical fields and valid geographic coordinate ranges. The final integrity audit confirmed 0 NULL species_ids and 0 broken species references.

<div class="page-break"></div>

## CHAPTER 7 — NATURAL LANGUAGE PROCESSING

### 7.1 NLP Motivation
Conservation literature is vast and unstructured. NLP allows for the automated extraction of threats and rapid semantic searching.

### 7.2 Document Processing
Documents are ingested as raw text and segmented into paragraphs or sentences for granular processing.

### 7.3 Text Preprocessing
Standard tokenization, lowercasing, and stop-word removal using NLTK.

### 7.4 Species Entity Recognition
A gazetteer-based approach matches exact scientific and common names from our 313-species catalog against the text.

### 7.5 Location / Entity Recognition
Rule-based matching against a predefined dictionary of Indian states and protected areas.

### 7.6 Threat Detection
A regex/rule-based engine scans for keywords related to poaching, habitat loss, climate change, and human-wildlife conflict.

### 7.7 Topic Classification
Weighted keyword scoring categorizes paragraphs into topics like "Policy", "Ecological Study", or "Incident Report".

### 7.8 Extractive Summarization
Key sentences containing the highest density of entities and threat keywords are extracted to form a summary.

### 7.9 Sentence Embeddings
We utilize the `SentenceTransformer` library with the `all-MiniLM-L6-v2` model to generate 384-dimensional embeddings of document segments.

### 7.10 Semantic Search
When a user searches (e.g., "water contamination affecting birds"), the query is embedded, and NumPy is used to calculate the cosine similarity between the query vector and all stored document vectors, returning the top results.

### 7.11 Hybrid Search
The API supports combining keyword filtering (e.g., only documents linked to a specific species ID) with semantic similarity scoring.

### 7.12 NLP Output
The frontend displays the extracted threats, summary, and matched species beautifully on the NLP Documents page.

### 7.13 Performance Optimization
The NLP model is loaded lazily and cached in memory upon FastAPI startup to prevent cold-start delays during API requests.

<div class="page-break"></div>

## CHAPTER 8 — MACHINE LEARNING

### 8.1 ML Motivation
Raw observation data is informative but not predictive. ML helps synthesize various factors into a single, understandable risk indicator.

### 8.2 Feature Engineering
The actual features extracted per species include:
- `observation_count_total`
- `recent_observation_count`
- `threat_frequency` (from NLP)
- `iucn_status_weight`
- `hwc_incident_count`
- `geographic_spread_km`
- `trend_slope`

### 8.3 Risk Assessment
The system computes these features and passes them to the ML model.

### 8.4 Random Forest
A `RandomForestRegressor` was chosen for its robustness to overfitting and ability to handle non-linear relationships in the feature set. It is trained on synthetic/heuristic labels tailored to flag concerning trends.

### 8.5 Risk Categories
Outputs are mapped to categories:
- LOW (0-33)
- MEDIUM (34-66)
- HIGH (67-89)
- CRITICAL (90-100)

### 8.6 Risk Score
A 0–100 scale indicating the platform's calculated concern level. **IMPORTANT: This is a decision-support indicator, not an official IUCN status or a scientific extinction probability.**

### 8.7 Isolation Forest
Used in parallel with the Random Forest to detect multivariate statistical anomalies in the observation data patterns.

### 8.8 Anomaly Detection
Identifies species where the observation pattern (e.g., a sudden, massive drop in recent observations combined with high geographic shrinkage) is highly unusual.

### 8.9 Alert Generation
Anomalies trigger automated entries in the `Alert` table, visible on the dashboard.

### 8.10 Model Artifacts
Trained models and scalers are serialized using `joblib` and loaded into the FastAPI dependency injection system.

### 8.11 ML Workflow
Data extraction -> Feature computation -> Scaling -> Inference -> Database caching.

### 8.12 Interpretation and Limitations
An anomaly does not definitively mean population decline; it may indicate a lack of reporting. The ML pipeline is an assistant, not an autonomous decision-maker. Furthermore, species with 0 observations dynamically bypass the ML risk calculation and display an "Insufficient observation data" state on the frontend to prevent misleading scores.

<div class="page-break"></div>

## CHAPTER 9 — GEOSPATIAL INTELLIGENCE

### 9.1 Spatial Data
Observations are fundamentally spatial, tied to specific latitude and longitude coordinates.

### 9.2 Observation Coordinates
Validated to ensure they fall within realistic global boundaries, with a specific focus on the Indian subcontinent.

### 9.3 Spatial Map
The React frontend utilizes mapping libraries (like Leaflet or custom SVG bounds) to render observation points over a geographic layout.

### 9.4 Species Filtering
Users can filter the map to view the distribution of a single species.

### 9.5 Viewport Filtering
The backend supports bounding box parameters `(min_lat, max_lat, min_lon, max_lon)` to only return observations visible on the user's screen.

### 9.6 Map API
`GET /api/observations/map` returns a lightweight GeoJSON or optimized coordinate array.

### 9.7 Observation Markers
Rendered dynamically. For dense clusters, frontend rendering limits or sampling is applied.

### 9.8 Species-specific Map
Displayed on the Species Profile page to show exact recorded habitats.

### 9.9 All-species Map
Displayed on the main Spatial Map hub. It relies on a representative sample to maintain browser performance, rather than rendering all 39,066 points simultaneously.

### 9.10 India Boundary Visualization
The map emphasizes the Indian region, aligning with the project's scope.

### 9.11 Map Limitations
The map reflects *recorded observations*, not complete biological habitats. Absence of points indicates a lack of data, not necessarily the absence of the species.

<div class="page-break"></div>

## CHAPTER 10 — BACKEND IMPLEMENTATION

### 10.1 FastAPI
Chosen for its asynchronous capabilities, extremely fast execution, and automatic OpenAPI (Swagger) documentation generation.

### 10.2 Project Structure
`backend/app/`
- `main.py`
- `api/`
- `core/`
- `models/`
- `schemas/`
- `services/`

### 10.3 Routers
Endpoints are grouped logically (e.g., `routers/species.py`, `routers/observations.py`).

### 10.4 Schemas
Pydantic is used for request/response validation, ensuring data integrity before it reaches the database.

### 10.5 Dependencies
FastAPI's dependency injection provides database sessions (`get_db`) and current user context (`get_current_user`).

### 10.6 Services
Business logic, such as aggregating the total observation count efficiently, is abstracted into service functions rather than cluttered inside routers.

### 10.7 Authentication
Implemented using the `OAuth2PasswordBearer` dependency.

### 10.8 Database Access
SQLAlchemy ORM provides Pythonic access to PostgreSQL. Efficient aggregated SQL queries (e.g., `func.count()`) are used to calculate the `total_observations` displayed on registry cards.

### 10.9 NLP Services
Wrapper classes interact with the loaded `SentenceTransformer` models safely.

### 10.10 ML Services
Handles the extraction of features from SQLAlchemy models and runs inference via `joblib`-loaded Scikit-learn models.

### 10.11 Search
The `GET /api/species/search` endpoint utilizes Postgres `ILIKE` for rapid keyword matching.

### 10.12 Error Handling
Global exception handlers return standardized HTTP 400/404/500 JSON responses.

### 10.13 API Endpoints
Core endpoints include `/species`, `/observations`, `/documents/search`, and `/ml/risk`.

<div class="page-break"></div>

## CHAPTER 11 — AUTHENTICATION AND RBAC

### 11.1 Authentication
Users must log in to access the Intelligence Hub. The frontend sends credentials; the backend verifies them and issues a JWT.

### 11.2 Password Security
Passwords are never stored in plaintext; they are hashed using the `bcrypt` algorithm.

### 11.3 JWT
The JSON Web Token contains the user's ID and role, signed with a secure secret key.

### 11.4 Authorization
Every protected API route verifies the JWT signature before proceeding.

### 11.5 Role-Based Access Control
RBAC ensures that sensitive data (like precise locations of endangered species) is only accessible to authorized personnel.

### 11.6 Protected Routes
Routes are decorated with `RequiresRole` dependencies.

### 11.7 Backend Enforcement
If a Viewer attempts to access an Admin-only endpoint, FastAPI immediately returns an HTTP 403 Forbidden error.

### 11.8 User Roles
- **Admin**: System management.
- **Forest Officer**: High-level clearance for sensitive anomalies.
- **Researcher**: Access to ML and NLP tooling.
- **Citizen / Viewer**: Read-only public data.

<div class="page-break"></div>

## CHAPTER 12 — FRONTEND IMPLEMENTATION

### 12.1 React Architecture
The user interface is built as a modular React application, favoring functional components and hooks.

### 12.2 TypeScript
Provides static typing, reducing runtime errors and ensuring the frontend interfaces perfectly match the backend Pydantic schemas.

### 12.3 Vite
Used as the build tool, offering incredibly fast Hot Module Replacement (HMR) during development and highly optimized production builds.

### 12.4 Routing
`react-router-dom` enables seamless client-side navigation without page reloads.

### 12.5 API Integration
Axios or native `fetch` wrappers handle communication with the FastAPI backend, including appending the JWT Authorization header to requests.

### 12.6 Login / Registration
Secure forms that manage authentication state and redirect the user to the Intelligence Hub upon success.

### 12.7 Intelligence Hub
The main dashboard providing high-level metrics, recent alerts, and quick navigation.

### 12.8 Species Registry
A paginated, visually rich catalog of all 313 species. Cards dynamically display the species photo, scientific name, IUCN status, and the accurately aggregated Total Observations count.

### 12.9 Species Profile
A detailed view showing the species photo, observation map, and ML Risk Score. Conditional logic gracefully handles species with zero observations.

### 12.10 Spatial Map
A dedicated page for visualizing geographic data across the region.

### 12.11 Threats & ML Risk
Dashboards aggregating the outputs of the Random Forest models.

### 12.12 NLP Documents
An interface for executing semantic searches against the ingested conservation reports.

### 12.13 Alerts & Anomalies
Displays the output of the Isolation Forest, flagging highly unusual data patterns.

### 12.14 Responsive / Desktop UI
The layout is optimized for desktop analysis, utilizing standard CSS for grid and flexbox layouts to create a premium, modern aesthetic utilizing Charcoal, Forest Green, Warm Ivory, and Muted Gold.

### 12.15 Visual Design System
Consistent typography, color palettes, and micro-animations ensure the platform feels like a professional, state-of-the-art decision-support tool.

<div class="page-break"></div>

## CHAPTER 13 — IMPLEMENTATION DETAILS

### 13.1 Authentication Flow
The client posts to `/api/auth/login`. The server verifies bcrypt hashes, signs a JWT, and returns it. The client stores this in memory/localStorage.

### 13.2 Species Retrieval
The registry uses `GET /api/species?skip=0&limit=20`. The backend uses an optimized SQLAlchemy query with `func.count(Observation.id)` to attach observation counts without triggering N+1 query problems.

### 13.3 Observation Retrieval
Observations are fetched lazily. The map requests coordinates only, reducing payload size.

### 13.4 Ingestion Pipeline
The `scripts/ingest_new_species_observations.py` uses multi-threading and API pagination. It constructs a unique fingerprint to prevent duplication and performs `session.bulk_save_objects()`.

### 13.5 NLP Pipeline
```python
# Representative snippet
embeddings = model.encode(sentences)
similarity = cosine_similarity(query_embedding, embeddings)
```
The application uses local NumPy arrays to compute similarities quickly for the current document volume.

### 13.6 Risk Assessment
The backend checks if `total_observations == 0`. If true, it returns a specific "Insufficient Data" flag to the frontend. Otherwise, it scales the features and calls `model.predict()`.

### 13.7 Anomaly Detection
The Isolation Forest returns -1 for anomalies. These are filtered and saved as `Alert` objects.

### 13.8 Semantic Search
A hybrid function that first filters documents by species metadata, then ranks them by embedding similarity.

### 13.9 Map Endpoint
Constructs a GeoJSON-like structure iterating over SQLAlchemy results, stripping unnecessary metadata to optimize rendering.

### 13.10 Photo Enrichment
The script queries the iNaturalist taxa endpoint, extracts the `default_photo.medium_url`, and updates the PostgreSQL `Species` record.

### 13.11 Observation Count Aggregation
A critical UI fix was implementing a SQL `GROUP BY` strategy in the backend router to attach observation counts directly to the `SpeciesResponse` schema, rather than fetching them individually.

<div class="page-break"></div>

## CHAPTER 14 — TESTING AND VALIDATION

### 14.1 Testing Strategy
The project employs strict automated testing for the backend and build verification for the frontend.

### 14.2 Backend Unit/Integration Testing
Implemented using `pytest`. The test suite covers database connectivity, model schemas, and API routing.

### 14.3 API Testing
FastAPI's `TestClient` is used to simulate HTTP requests and assert expected JSON responses.

### 14.4 Database Integrity Testing
A custom Python audit script was executed to verify database state.
- **Species:** 313
- **NULL species_id:** 0
- **Broken species references:** 0

### 14.5 Data Ingestion Validation
Ingestion scripts log successes and failures. The most recent major ingestion successfully added 1,703 new records.

### 14.6 Deduplication Validation
An exhaustive deduplication script identified and safely removed exactly 40 duplicate source-ID rows (6 GBIF, 34 iNaturalist), ensuring the final 39,066 count is highly accurate. 1,427 coordinate/date matches were properly retained as they lacked source-ID duplication evidence.

### 14.7 NLP Performance Testing
The NLP module was tested for startup performance, successfully loading the SentenceTransformer model into memory.

### 14.8 Semantic Search Testing
Verified that cosine similarity correctly ranks relevant documents above irrelevant ones.

### 14.9 Map Testing
Verified that the API correctly handles missing coordinates gracefully.

### 14.10 Frontend Build Testing
The command `npm run build` utilizes `tsc` (TypeScript compiler) to ensure strict type safety before generating the Vite production bundle.

### 14.11 Final Test Results
- **Backend tests:** 30 passed, 0 failures.
- **Frontend production build:** PASS (Zero TypeScript errors).

<div class="page-break"></div>

## CHAPTER 15 — RESULTS AND DISCUSSION

### 15.1 Final Dataset
The final database represents a robust cut of Indian wildlife biodiversity data.
- **Total Species:** 313
- **Total Observations:** 39,066

### 15.2 Species Distribution
- Aves (Birds): 255
- Mammalia: 35
- Reptilia: 16
- Amphibia: 7

### 15.3 Observation Distribution
The vast majority of records originate from GBIF (28,694) and iNaturalist (9,999), reflecting the power of global biodiversity databases and citizen science.

### 15.4 Photo Coverage
311 out of 313 species possess verified, high-quality photographs, vastly improving the usability of the Species Registry.

### 15.5 NLP Results
The rule-based and gazetteer systems successfully extract entities from sample conservation reports, highlighting the utility of automated text processing.

### 15.6 Semantic Search
The `all-MiniLM-L6-v2` embeddings provide fast and accurate semantic matching, bypassing the limitations of strict keyword searches.

### 15.7 ML Risk Results
The Random Forest model successfully categorizes species into LOW, MEDIUM, HIGH, and CRITICAL risk tiers based on their data profiles. The UI gracefully handles edge cases (e.g., zero observations) by displaying "Insufficient observation data" instead of a misleading score.

### 15.8 Anomaly Results
The Isolation Forest successfully flags statistical outliers, directing researcher attention to species that require immediate data verification.

### 15.9 Map Results
The spatial map accurately visualizes the geographic spread of observations, providing crucial context for the calculated Risk Scores.

### 15.10 User Interface Results
The resulting React application is fast, responsive, and visually cohesive, proving the viability of the architecture.

### 15.11 System Performance
The FastApi backend handles the 39,066 records effortlessly, and the frontend Vite build is highly optimized for production deployment.

### 15.12 Discussion
The Wildlife Conservation Intelligence Platform successfully achieves its objective of unifying fragmented data. By combining raw observations with NLP insights and ML risk modeling, it demonstrates how modern AI/software engineering can directly support ecological conservation efforts.

<div class="page-break"></div>

## CHAPTER 16 — LIMITATIONS

While robust, the platform operates under several realistic technical and domain limitations:

1. **Uneven Dataset Coverage:** Public biodiversity datasets suffer from spatial and taxonomic bias. Common species often have thousands of records, while rare or elusive species may have few or zero records.
2. **Not Unique Animal Counts:** The 39,066 records are *biodiversity observation records*, not a census of 39,066 unique animals. A single tiger might be photographed and uploaded 10 times by different tourists.
3. **NLP Constraints:** The current NLP implementation relies heavily on rule-based and gazetteer-based entity extraction, which can miss nuanced context compared to fine-tuned Large Language Models.
4. **ML Decision Support Only:** The ML Risk Score is a decision-support heuristic. It is not an official IUCN risk prediction, nor is it a scientifically validated extinction or population prediction model. It relies on synthetic/heuristic training labels.
5. **No Autonomous Decision-Making:** The platform advises and highlights anomalies; it does not make autonomous conservation decisions.
6. **Geographic Scope:** While optimized for the Indian subcontinent, it does not guarantee complete or exhaustive India-wide biodiversity coverage.
7. **Vector Search:** Currently, semantic search uses in-memory NumPy cosine similarity rather than native pgvector operators, which limits massive horizontal scaling.

<div class="page-break"></div>

## CHAPTER 17 — FUTURE SCOPE

The architecture was designed to be extensible, allowing for several future enhancements:

1. **Native pgvector Integration:** Migrating the NumPy-based cosine similarity search directly into PostgreSQL using the `pgvector` extension for immense scalability.
2. **PostGIS Geometry:** Migrating from standard float coordinates to native PostGIS geometries to enable advanced spatial queries (e.g., intersecting observations with precise National Park boundary polygons).
3. **Advanced Transformer NER:** Replacing gazetteer-based entity extraction with a fine-tuned BERT/spaCy model for highly accurate, context-aware Ecological Named Entity Recognition.
4. **OCR and PDF Ingestion:** Implementing optical character recognition to automatically ingest and process scanned, historical government PDFs.
5. **Automated Scheduled Ingestion:** Deploying background cron jobs or Celery workers to continuously ingest new data from GBIF and iNaturalist daily.
6. **Temporal Forecasting:** Implementing Time Series ML models (like ARIMA or Prophet) to forecast future observation trends.
7. **Mobile Application:** Developing a React Native field application allowing forest officers to submit observations directly to the platform offline.

<div class="page-break"></div>

## CHAPTER 18 — CONCLUSION

The **Wildlife Conservation Intelligence Platform** successfully demonstrates the powerful intersection of modern software engineering, artificial intelligence, and environmental science. By addressing the critical problem of fragmented biodiversity data, the platform provides a unified, highly optimized decision-support system.

The ingestion and rigorous deduplication of 39,066 real-world observation records across 313 Indian species provides a solid data foundation. Upon this foundation, the application of Natural Language Processing (via SentenceTransformers) transforms unstructured text into searchable, actionable intelligence. Simultaneously, the application of Machine Learning (Random Forests and Isolation Forests) translates raw spatial and temporal data into intuitive risk and anomaly indicators.

Delivered through a secure, role-based React frontend and powered by a highly performant FastAPI backend, the system meets all established academic and functional requirements. While acknowledging the inherent limitations of public datasets and heuristic models, the platform serves as a highly effective, scalable prototype. It empowers researchers, citizens, and policymakers alike, proving that integrated AI-assisted intelligence is a vital tool in the ongoing effort to protect and preserve global biodiversity.

<div class="page-break"></div>

## FINAL DATA SUMMARY

| Metric | Value |
|--------|-------|
| **Total Species** | 313 |
| **Aves (Birds)** | 255 |
| **Mammalia** | 35 |
| **Reptilia** | 16 |
| **Amphibia** | 7 |
| **Total Observation Records** | 39,066 |
| **Species with verified photos** | 311 / 313 |
| **Backend Tests** | 30 passed |
| **Frontend Production Build** | PASS |
| **Database Integrity (NULL/Broken Refs)** | 0 |


## CHAPTER 13 — IMPLEMENTATION DETAILS

### 13.1 Authentication Flow
The security of the Wildlife Conservation Intelligence Platform is paramount. The system utilizes OAuth2 with Password Flow (Bearer Tokens). When a user attempts to log in, they provide their username (or email) and password. The FastAPI backend hashes the provided password and compares it against the stored bcrypt hash. If valid, the system generates a JSON Web Token (JWT) signed with a secret key.

```python
# Backend Authentication Dependency snippet
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
```

### 13.2 Species Retrieval
Fetching species for the registry requires attaching the total observation count. To avoid N+1 query performance issues, we utilize SQLAlchemy's `func.count()` grouped by the species ID.

```python
# Efficient Observation Count Aggregation
species_with_counts = db.query(
    Species,
    func.count(Observation.id).label("total_observations")
).outerjoin(Observation, Species.id == Observation.species_id) \
 .group_by(Species.id) \
 .order_by(Species.scientific_name) \
 .offset(skip).limit(limit).all()
```

### 13.3 Data Ingestion Pipeline
The ingestion pipeline is designed for robustness. It pulls data from GBIF and iNaturalist APIs, normalizes the data into standard Python dictionaries, and bulk inserts them into PostgreSQL.

A crucial aspect is the deduplication logic. A composite fingerprint combining `species_id`, `latitude`, `longitude`, and `observed_at` is generated. Furthermore, `source_record_id` is tracked.

### 13.4 NLP Pipeline Execution
When the server starts, the `SentenceTransformer` model is loaded into memory. Upon receiving a search query, it generates an embedding and performs a fast, NumPy-based cosine similarity search.

```python
# Semantic Search Snippet
query_embedding = model.encode(search_query)
similarities = []
for doc in documents:
    doc_embedding = np.array(doc.embedding)
    sim = cosine_similarity(query_embedding.reshape(1, -1), doc_embedding.reshape(1, -1))[0][0]
    similarities.append((doc, sim))
    
similarities.sort(key=lambda x: x[1], reverse=True)
return similarities[:top_k]
```

<div class="page-break"></div>

## CHAPTER 14 — TESTING AND VALIDATION

### 14.1 Testing Strategy
A multi-layered testing strategy was implemented. Backend API endpoints are tested using `pytest` and `FastAPI.TestClient`. The database integrity is verified through dedicated audit scripts, and the frontend is validated via the Vite/TypeScript build process.

### 14.2 Final Test Results

| Test Category | Status | Details |
|---------------|--------|---------|
| **Backend Unit Tests** | PASS | 30 tests passed, 0 failures |
| **API Integration** | PASS | Simulated client interactions successful |
| **Database Integrity** | PASS | 0 NULL species_id, 0 Broken references |
| **Frontend Build** | PASS | TypeScript compiler found 0 errors |

### 14.3 Database Deduplication Audit
Following the final data ingestion run, a comprehensive deduplication audit was performed. The platform correctly identified duplicate source IDs resulting from overlapping ingestion windows. Exactly 40 duplicate records were safely removed, preserving 39,066 distinct observations while retaining 1,427 coordinate-date fingerprint matches that lacked source-ID evidence, thereby respecting the complexity of legitimate coincident observations.

<div class="page-break"></div>

## CHAPTER 15 — RESULTS AND DISCUSSION

### 15.1 Final Dataset Overview
The final dataset is a robust compilation of Indian wildlife occurrences.

**Table 11: Final Dataset Summary**
| Metric | Value |
|--------|-------|
| Total Species | 313 |
| Aves | 255 |
| Mammalia | 35 |
| Reptilia | 16 |
| Amphibia | 7 |
| Observation records | 39,066 |
| Species with photos | 311 / 313 |

### 15.2 ML Risk Assessment Outcomes
The Random Forest model effectively synthesizes the extracted features into actionable risk indicators. The UI appropriately handles edge cases, such as the Malabar Large-spotted Civet (Viverra civettina), which has 0 observations, by displaying "Insufficient observation data" rather than a misleading mathematical score.

### 15.3 Geospatial Mapping
The map successfully plots the geographic distribution. By dynamically querying the database with bounding boxes, the system ensures browser performance remains optimal even when interacting with tens of thousands of potential data points.

### 15.4 NLP Efficacy
The integration of `all-MiniLM-L6-v2` has dramatically improved the discoverability of critical information within conservation reports. The semantic search can understand context (e.g., matching "water pollution" with "toxic effluent"), surpassing traditional SQL `LIKE` limitations.

<div class="page-break"></div>

## CHAPTER 16 — LIMITATIONS

1. **Dataset Bias:** Public databases like GBIF and iNaturalist are biased towards accessible areas and charismatic species (e.g., birds and large mammals).
2. **Not Unique Counts:** 39,066 observations do not represent 39,066 unique animals.
3. **ML Heuristics:** The Risk Score is a decision-support heuristic, not a scientifically validated extinction model.
4. **NLP Processing:** Entity extraction relies on predefined gazetteers, missing undocumented local names.
5. **No Native pgvector Search:** Embeddings are stored as JSON arrays and compared via NumPy, which works for current loads but will bottleneck at extreme scale.

<div class="page-break"></div>

## CHAPTER 17 — FUTURE SCOPE

1. **Native pgvector Migration:** Transitioning the JSON arrays to native `vector` types in PostgreSQL to enable highly scalable, indexed nearest-neighbor searches.
2. **PostGIS Geometries:** Upgrading latitude/longitude float columns to PostGIS `geometry` types for complex polygon intersections (e.g., matching observations against National Park boundaries).
3. **Transformer-based NER:** Replacing gazetteers with a fine-tuned Transformer model for Ecological Named Entity Recognition.
4. **Automated Scheduled Ingestion:** Implementing a Celery task queue to fetch daily updates from GBIF.
5. **OCR Integration:** Automatically processing scanned historical government PDFs using Tesseract.

<div class="page-break"></div>

## CHAPTER 18 — CONCLUSION

The **Wildlife Conservation Intelligence Platform** successfully demonstrates the powerful intersection of modern software engineering, artificial intelligence, and environmental science. By addressing the critical problem of fragmented biodiversity data, the platform provides a unified, highly optimized decision-support system.

The ingestion and rigorous deduplication of 39,066 real-world observation records across 313 Indian species provides a solid data foundation. Upon this foundation, the application of Natural Language Processing (via SentenceTransformers) transforms unstructured text into searchable, actionable intelligence. Simultaneously, the application of Machine Learning (Random Forests and Isolation Forests) translates raw spatial and temporal data into intuitive risk and anomaly indicators.

Delivered through a secure, role-based React frontend and powered by a highly performant FastAPI backend, the system meets all established academic and functional requirements. While acknowledging the inherent limitations of public datasets and heuristic models, the platform serves as a highly effective, scalable prototype. It empowers researchers, citizens, and policymakers alike, proving that integrated AI-assisted intelligence is a vital tool in the ongoing effort to protect and preserve global biodiversity.


