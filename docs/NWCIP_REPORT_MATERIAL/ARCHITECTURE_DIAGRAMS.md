# Architecture Diagrams

The platform’s high‑level architecture is already documented in the README as a Mermaid flowchart. Below is the same diagram reproduced for the report.

```mermaid
flowchart TD
    subgraph Data_Sources ["Telemetry & Document Ingestion"]
        S1["GBIF Telemetry"]
        S2["iNaturalist / eBird"]
        S3["Field Ranger Submissions"]
        S4["Unstructured Incident Reports & News"]
    end

    subgraph Ingestion_Layer ["Ingestion & Preprocessing Engine"]
        CLN["Spatial Sanitizer (BBox & Deduplication)"]
        NER["spaCy NER & IUCN Threat Ontologies"]
        EMB["SentenceTransformer ('all-MiniLM-L6-v2')"]
    end

    subgraph Storage_Engine ["Relational & Vector Storage"]
        DB[("PostgreSQL / PostGIS\nSQLite Fallback (Dev/Offline)" )]
        VEC["384-dim Embedding JSON / FAISS Indexes"]
    end

    subgraph Intelligence_Core ["Analytical & ML Decision Engine"]
        RF["Random Forest Risk Classifier\n(Composite Score 0–100)"]
        IF["Isolation Forest Anomaly Engine\n(Spatial/Temporal Deviation)"]
        HYB["Hybrid Search Engine\n(BM25 + Dense Cosine Fusion)"]
    end

    subgraph Presentation_Layer ["React 18 + Tailwind GIS Frontend"]
        DASH["Executive KPI Dashboard & Threat Charts"]
        MAP["Geospatial Leaflet GIS Map"]
        CAT["Species Catalog & Radar Risk Profiles"]
        DOC["NLP Ingestion Workbench"]
        SRC["Hybrid Semantic Search UI"]
        ANM["ML Anomaly & Retraining Console"]
        ADM["Admin RBAC Governance & System Health"]
    end

    S1 & S2 & S3 --> CLN --> DB
    S4 --> NER --> EMB --> DB & VEC
    DB & VEC --> RF & IF & HYB
    RF & IF & HYB --> DASH & MAP & CAT & DOC & SRC & ANM & ADM
```

The diagram illustrates the flow from data sources through ingestion, storage, intelligence, and finally to the user‑facing web application.

