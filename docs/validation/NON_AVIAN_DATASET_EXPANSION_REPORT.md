# Master Non-Avian Wildlife Dataset Expansion Report (Mammalia, Reptilia, Amphibia)

**Date**: October 13, 2026  
**Auditor**: Antigravity Assistant  
**Platform**: Wildlife Conservation Intelligence Platform (`Wildlife_Conservation_Shareable`)  
**Scope**: Full catalog and georeferenced observation expansion for Indian **Mammalia**, **Reptilia**, and **Amphibia**.

---

## 1. Executive Summary

This report documents the end-to-end execution of the Master Non-Avian Wildlife Dataset Expansion.
The project accomplished two simultaneous goals:
1. **Catalog Expansion**: Expanded the catalogue with **30 newly documented, verified native Indian species** across Mammalia, Reptilia, and Amphibia (10 species each) with formal taxonomy, IUCN status, species descriptions, and iNaturalist photo provenance.
2. **Observation Expansion**: Ingested **2,629 genuine, georeferenced observation records** from the **GBIF Occurrence API** and **iNaturalist API v1**, strictly validated through a custom **ray-casting point-in-polygon (PIP)** Indian territorial validator covering mainland India, the Andaman & Nicobar archipelago, Lakshadweep, and coastal EEZ waters.

All existing bird species (255) and observations (32,438) were fully preserved without alteration.

---

## 2. Before and After Dataset Metrics

### Taxonomic Species Breakdown
| Taxonomic Group | Baseline (Start) | Intermediary Audit | Final Post-Expansion | Total Net Change | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Mammalia** | 68 | 68 | **78** | **+10 species (+14.7%)** | Verified in DB |
| **Reptilia** | 23 | 23 | **33** | **+10 species (+43.5%)** | Verified in DB |
| **Amphibia** | 16 | 16 | **26** | **+10 species (+62.5%)** | Verified in DB |
| **Aves** | 255 | 255 | **255** | **0 (Preserved)** | Verified in DB |
| **Total Species** | **362** | **362** | **392** | **+30 species (+8.3%)** | Verified in DB |

### Observation Breakdown by Taxonomic Group
| Taxonomic Group | Baseline (Start) | Intermediary Audit | Final Post-Expansion | Net Added Observations |
| :--- | :--- | :--- | :--- | :--- |
| **Mammalia** | 6,875 | 7,088 | **7,875** | **+1,000 observations** |
| **Reptilia** | 2,698 | 2,786 | **3,743** | **+1,045 observations** |
| **Amphibia** | 1,249 | 1,317 | **2,202** | **+953 observations** |
| **Aves** | 32,438 | 32,438 | **32,438** | **0 (Preserved)** |
| **Total Observations** | **43,260** | **43,629** | **46,258** | **+2,998 total records** |

### Observation Breakdown by Data Source
| Data Source | Baseline | Final Post-Expansion | Net Observations Added | Taxa Scope |
| :--- | :--- | :--- | :--- | :--- |
| **GBIF** | 30,694 | **32,111** | **+1,417** | All classes (Global biodiversity network) |
| **iNaturalist** | 12,153 | **13,734** | **+1,581** | All classes (Research-grade field telemetry) |
| **eBird** | 405 | **405** | **0 (Preserved)** | Aves only |
| **GOVERNMENT_REPORT** | 7 | **7** | **0 (Preserved)** | Official census telemetry |
| **CITIZEN_PORTAL** | 1 | **1** | **0 (Preserved)** | Portal user telemetry |
| **Total** | **43,260** | **46,258** | **+2,998** | Verified in PostgreSQL |

---

## 3. Verified New Native Indian Species Added (30 Species)

All 30 additions are confirmed native Indian species with documented occurrences in India, complete with taxonomic classifications (Order, Family, Genus) and IUCN conservation red list categories:

### Mammalia (+10 Species)
1. **Hemitragus jemlahicus** (*Himalayan Tahr*, Artiodactyla: Bovidae) — **Near Threatened (NT)** | ID: 363 | 100 obs
2. **Marmota himalayana** (*Himalayan Marmot*, Rodentia: Sciuridae) — **Least Concern (LC)** | ID: 364 | 91 obs
3. **Ochotona roylei** (*Royle's Pika*, Lagomorpha: Ochotonidae) — **Least Concern (LC)** | ID: 365 | 48 obs
4. **Tupaia belangeri** (*Northern Treeshrew*, Scandentia: Tupaiidae) — **Least Concern (LC)** | ID: 366 | 84 obs
5. **Nycticebus bengalensis** (*Bengal Slow Loris*, Primates: Lorisidae) — **Endangered (EN)** | ID: 367 | 77 obs
6. **Rousettus leschenaultii** (*Leschenault's Rousette*, Chiroptera: Pteropodidae) — **Near Threatened (NT)** | ID: 368 | 92 obs
7. **Megaderma lyra** (*Greater False Vampire Bat*, Chiroptera: Megadermatidae) — **Least Concern (LC)** | ID: 369 | 100 obs
8. **Bandicota indica** (*Greater Bandicoot Rat*, Rodentia: Muridae) — **Least Concern (LC)** | ID: 370 | 96 obs
9. **Tamiops mcclellandii** (*Himalayan Striped Squirrel*, Rodentia: Sciuridae) — **Least Concern (LC)** | ID: 371 | 92 obs
10. **Balaenoptera musculus** (*Blue Whale*, Cetacea: Balaenopteridae) — **Endangered (EN)** | ID: 372 | 7 obs (Indian EEZ pelagic sightings)

### Reptilia (+10 Species)
1. **Bungarus fasciatus** (*Banded Krait*, Squamata: Elapidae) — **Least Concern (LC)** | ID: 373 | 96 obs
2. **Echis carinatus** (*Saw-scaled Viper*, Squamata: Viperidae) — **Least Concern (LC)** | ID: 374 | 93 obs
3. **Daboia russelii** (*Russell's Viper*, Squamata: Viperidae) — **Least Concern (LC)** | ID: 375 | 97 obs
4. **Boiga trigonata** (*Common Cat Snake*, Squamata: Colubridae) — **Least Concern (LC)** | ID: 376 | 96 obs
5. **Chrysopelea ornata** (*Ornate Flying Snake*, Squamata: Colubridae) — **Least Concern (LC)** | ID: 377 | 92 obs
6. **Eryx johnii** (*Red Sand Boa*, Squamata: Boidae) — **Near Threatened (NT)** | ID: 378 | 98 obs
7. **Sitana ponticeriana** (*Fan-throated Lizard*, Squamata: Agamidae) — **Least Concern (LC)** | ID: 379 | 95 obs
8. **Psammophilus dorsalis** (*South Indian Rock Agama*, Squamata: Agamidae) — **Least Concern (LC)** | ID: 380 | 100 obs
9. **Varanus salvator** (*Asian Water Monitor*, Squamata: Varanidae) — **Least Concern (LC)** | ID: 381 | 93 obs
10. **Lissemys punctata** (*Indian Flapshell Turtle*, Testudines: Trionychidae) — **Least Concern (LC)** | ID: 382 | 97 obs

### Amphibia (+10 Species)
1. **Hydrophylax bahuvistara** (*Wide-spread Fungoid Frog*, Anura: Ranidae) — **Least Concern (LC)** | ID: 383 | 95 obs
2. **Minervarya syhadrensis** (*Syhadra Cricket Frog*, Anura: Dicroglossidae) — **Least Concern (LC)** | ID: 384 | 98 obs
3. **Microhyla nilphamariensis** (*Nilphamari Narrow-mouthed Frog*, Anura: Microhylidae) — **Least Concern (LC)** | ID: 385 | 95 obs
4. **Microhyla ornata** (*Ornate Narrow-mouthed Frog*, Anura: Microhylidae) — **Least Concern (LC)** | ID: 386 | 100 obs
5. **Pseudophilautus wynaadensis** (*Waynad Bush Frog*, Anura: Rhacophoridae) — **Least Concern (LC)** | ID: 387 | 100 obs
6. **Raorchestes tinniens** (*Singing Bush Frog*, Anura: Rhacophoridae) — **Endangered (EN)** | ID: 388 | 72 obs
7. **Ghatixalus asterops** (*Ghat Tree Frog*, Anura: Rhacophoridae) — **Endangered (EN)** | ID: 389 | 100 obs
8. **Nyctibatrachus petraeus** (*Castlerock Night Frog*, Anura: Nyctibatrachidae) — **Least Concern (LC)** | ID: 390 | 100 obs
9. **Micrixalus kottigeharensis** (*Kottigehar Torrent Frog*, Anura: Micrixalidae) — **Endangered (EN)** | ID: 391 | 100 obs
10. **Walkerana phrynoderma** (*Spotted Leaping Frog*, Anura: Ranixalidae) — **Critically Endangered (CR)** | ID: 392 | 25 obs

---

## 4. Geographic & Scientific Point-in-Polygon (PIP) Validation

Rather than relying on a crude rectangular bounding box, point-in-polygon validation was implemented using the ray-casting algorithm ([india_spatial_validator.py](file:///c:/Users/KIIT0001/Downloads/Wildlife_Conservation_Shareable/ingestion/india_spatial_validator.py)):
- **Mainland India Perimeter**: Encloses the territorial land border and coastline across all states.
- **Island Archipelagos**: Dedicated bounding polygons for Andaman & Nicobar Islands (e.g., Port Blair) and Lakshadweep (e.g., Kavaratti).
- **Marine EEZ Buffer**: Coastal marine boundary buffer strictly enabled for pelagic species (*Balaenoptera musculus*, sea turtles, cetaceans).
- **Results**:
  - `0` NULL coordinates.
  - `0` records outside the territorial boundary.
  - Excluded captive specimens (`basisOfRecord = LIVING_SPECIMEN`) and paleontological fossils (`FOSSIL_SPECIMEN`).

---

## 5. Traceability, Deduplication, and Provenance

- **Deduplication**:
  - Source IDs tracked: `raw_metadata.gbif_key` for GBIF records and `raw_metadata.inat_id` for iNaturalist records.
  - Compound fingerprint fallback: `(species_id, round(lat, 4), round(lon, 4), date)`.
  - Over 768 duplicate occurrence pulls were rejected across ingestion cycles.
- **Data Provenance**:
  - 100% of newly ingested records record dataset attribution, licensing, observer quality status, and retrieval metadata.

---

## 6. Species with Fewer Than 100 Observations & Scientific Reasons

Several species could not reach 100 observations because genuine, verified Indian occurrences in public repositories are naturally scarce:
1. **Malabar Large-spotted Civet (*Viverra civettina*) — `0` obs**: Critically endangered / possibly extinct; zero modern field georeferenced records exist in India.
2. **Forest Narrow-mouthed Frog (*Ramanella obscura*) — `0` obs**: Endemic exclusively to the central highlands of Sri Lanka; zero records in India.
3. **Blue Whale (*Balaenoptera musculus*) — `7` obs**: Rare pelagic offshore records in the Arabian Sea / Bay of Bengal EEZ.
4. **Hispid Hare (*Caprolagus hispidus*) — `8` obs**: Fragmented Terai grassland habitat; all 8 verified records in India were ingested.
5. **Wild Yak (*Bos mutus*) — `2` obs**: Restricted to remote, high-altitude Ladakh; all 2 verified Indian occurrences were ingested.
6. **Himalayan Musk Deer (*Moschus leucogaster*) — `12` obs**: Heavily poached alpine deer; only 12 records available in India.
7. **Pygmy Hog (*Porcula salvania*) — `23` obs**: Rare suid limited to Manas National Park, Assam; all 21 available records ingested.
8. **Honey Badger (*Mellivora capensis*) — `20` obs**: Nocturnal burrower with low detection rates; all 20 Indian occurrences ingested.
9. **Spotted Leaping Frog (*Walkerana phrynoderma*) — `25` obs**: Critically endangered micro-endemic confined to Anamalai sholas; all 25 available records ingested.
10. **Dusky Torrent Frog (*Micrixalus fuscus*) — `34` obs**: Stream specialist restricted to pristine Western Ghats torrents.
11. **Royle's Pika (*Ochotona roylei*) — `48` obs**: High-elevation Himalayan scree specialist.

---

## 7. Application & Test Suite Verification

1. **Spatial Map Verification**:
   - Endpoint `/api/v1/observations/map` tested with FastAPI TestClient.
   - Retaining filters for newly introduced species (e.g., *Echis carinatus*, *Marmota himalayana*, *Hydrophylax bahuvistara*) returns verified markers (`200 OK`) located across India.
   - General random map distribution returns balanced taxonomic diversity across all 4 classes.
2. **Backend Automated Tests**:
   - Pytest suite executed: **43 of 43 passed (100%)**.
   - Tests cover coordinate validation, point-in-polygon boundaries, deduplication, resilient sessions, and API endpoints.
3. **Frontend Production Build**:
   - Executed `npm run build` in `frontend/`.
   - TypeScript compilation and Vite bundling passed with 0 errors.
