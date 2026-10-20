"""
Rich Demo Data Seeder
=====================
Populates the Wildlife Conservation Intelligence Platform with realistic
Indian biodiversity data: species, locations, observations, documents,
threats, ML risk scores, anomalies, and alerts.

Run from project root:
    python scripts/seed_demo_data.py
"""

import sys, os, datetime, random
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.database import SessionLocal, init_db
from backend.app.models.species import Species
from backend.app.models.observation import Observation, DataSource
from backend.app.models.location import Location
from backend.app.models.document import Document, DocumentThreat, DocumentSpecies, NLPAnalysisResult
from backend.app.models.threat import Threat
from backend.app.models.ml_outputs import MLRiskScore, MLAnomaly
from backend.app.models.alert import ConservationAlert
from nlp.embeddings import VectorEmbedder

init_db()
db = SessionLocal()
embedder = VectorEmbedder()

rng = random.Random(42)

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def now():
    return datetime.datetime.now(datetime.timezone.utc)

def days_ago(n):
    return now() - datetime.timedelta(days=n)

def existing(model, **kwargs):
    return db.query(model).filter_by(**kwargs).first()

# ─── 1. THREATS ───────────────────────────────────────────────────────────────
THREAT_DEFS = [
    ("Poaching & Illegal Wildlife Trade", "5.1.1", 2.5),
    ("Habitat Loss & Deforestation", "7.1",   2.0),
    ("Human-Wildlife Conflict",       "6.1",   1.8),
    ("Linear Infrastructure (Roads & Rails)", "4.1", 1.6),
    ("Invasive Species Pressure",     "8.1",   1.4),
    ("Pesticide & Chemical Pollution", "9.2",  1.3),
    ("Climate Induced Range Shift",   "11.2",  1.5),
    ("Mining & Resource Extraction",  "3.2",   1.7),
    ("Forest Fire & Arson",           "7.3",   1.6),
    ("Overfishing & Bycatch",         "5.4",   1.4),
]
threats = []
for cat, code, weight in THREAT_DEFS:
    t = existing(Threat, category_name=cat)
    if not t:
        t = Threat(category_name=cat, iucn_threat_code=code, severity_weight=weight)
        db.add(t)
    threats.append(t)
db.flush()
print(f"  Threats: {len(threats)}")

# ─── 2. LOCATIONS ─────────────────────────────────────────────────────────────
LOCATIONS = [
    ("Corbett Tiger Reserve",         "National Park",       "Uttarakhand",    29.53,  78.77),
    ("Kanha National Park",           "National Park",       "Madhya Pradesh", 22.33,  80.61),
    ("Kaziranga National Park",       "National Park",       "Assam",          26.67,  93.37),
    ("Sundarbans Tiger Reserve",      "Tiger Reserve",       "West Bengal",    21.94,  89.18),
    ("Bandipur National Park",        "National Park",       "Karnataka",      11.67,  76.63),
    ("Gir National Park",             "Wildlife Sanctuary",  "Gujarat",        21.12,  70.80),
    ("Chilika Lake",                  "Wetland Sanctuary",   "Odisha",         19.73,  85.32),
    ("Silent Valley National Park",   "National Park",       "Kerala",         11.07,  76.44),
    ("Great Indian Bustard Sanctuary","Wildlife Sanctuary",  "Rajasthan",      26.86,  71.65),
    ("Rann of Kutch",                 "Biosphere Reserve",   "Gujarat",        23.85,  70.25),
    ("Dibru-Saikhowa NP",             "National Park",       "Assam",          27.69,  95.19),
    ("Nagarhole National Park",       "Tiger Reserve",       "Karnataka",      12.05,  76.00),
]
locations = []
for name, ptype, state, lat, lon in LOCATIONS:
    loc = existing(Location, name=name)
    if not loc:
        loc = Location(name=name, protected_area_type=ptype, state=state, latitude=lat, longitude=lon)
        db.add(loc)
    locations.append(loc)
db.flush()
print(f"  Locations: {len(locations)}")

# ─── 3. SPECIES ───────────────────────────────────────────────────────────────
SPECIES_DATA = [
    ("Panthera tigris tigris",       "Bengal Tiger",         "Felidae",       "EN",  "Carnivora",  "Mammalia",  "Forests & grasslands of central and north India. Flagship species for Project Tiger."),
    ("Elephas maximus",              "Asian Elephant",        "Elephantidae",  "EN",  "Proboscidea","Mammalia",  "Megaherbivore ranging across Indian forest corridors. Keystone seed disperser."),
    ("Rhinoceros unicornis",         "Indian One-Horned Rhino","Rhinocerotidae","VU",  "Perissodactyla","Mammalia","Restricted to Terai floodplains; greatest population in Kaziranga."),
    ("Panthera pardus fusca",        "Indian Leopard",        "Felidae",       "VU",  "Carnivora",  "Mammalia",  "Adaptable predator facing intense habitat pressure outside PAs."),
    ("Pavo cristatus",               "Indian Peafowl",        "Phasianidae",   "LC",  "Galliformes","Aves",      "National bird; abundant but threatened by pesticide use."),
    ("Gavialis gangeticus",          "Gharial",               "Gavialidae",    "CR",  "Crocodilia","Reptilia",  "Critically endangered fish-eating crocodilian; fewer than 300 adults remain."),
    ("Pteropus giganteus",           "Indian Flying Fox",     "Pteropodidae",  "LC",  "Chiroptera", "Mammalia",  "Keystone pollinator; faces threats from electrocution and hunting."),
    ("Balearica regulorum",          "Grey Crowned Crane",    "Gruidae",       "EN",  "Gruiformes", "Aves",      "Wetland specialist threatened by drainage and agriculture."),
    ("Ardeotis nigriceps",           "Great Indian Bustard",  "Otididae",      "CR",  "Otidiformes","Aves",      "Flagship grassland species; fewer than 150 individuals remain."),
    ("Lutra lutra",                  "European Otter",        "Mustelidae",    "NT",  "Carnivora",  "Mammalia",  "Freshwater specialist sensitive to river pollution and fishing nets."),
    ("Axis axis",                    "Chital / Spotted Deer", "Cervidae",      "LC",  "Artiodactyla","Mammalia", "Abundant prey species; indicator of forest ecosystem health."),
    ("Manis crassicaudata",          "Indian Pangolin",       "Manidae",       "EN",  "Pholidota",  "Mammalia",  "Most trafficked mammal globally; scales used in traditional medicine."),
    ("Crocodylus palustris",         "Mugger Crocodile",      "Crocodylidae",  "VU",  "Crocodilia", "Reptilia",  "Freshwater crocodile facing habitat loss and hunting pressure."),
    ("Bibos gaurus",                 "Indian Gaur (Bison)",   "Bovidae",       "VU",  "Artiodactyla","Mammalia", "Largest wild cattle; threatened by disease from livestock."),
    ("Semnopithecus entellus",       "Hanuman Langur",        "Cercopithecidae","LC", "Primates",   "Mammalia",  "Common monkey; declining in urban fringes due to deforestation."),
]
species_list = []
for sci, common, family, iucn, order_, class_, desc in SPECIES_DATA:
    sp = existing(Species, scientific_name=sci)
    if not sp:
        sp = Species(
            scientific_name=sci, common_name=common, family=family,
            iucn_category=iucn,
            order_name=order_, class_name=class_, kingdom="Animalia", phylum="Chordata",
            description=desc
        )
        db.add(sp)
    species_list.append(sp)
db.flush()
print(f"  Species: {len(species_list)}")

# ─── 4. DATA SOURCES ──────────────────────────────────────────────────────────
SOURCES = [
    ("GBIF India",        "https://gbif.org"),
    ("iNaturalist India", "https://inaturalist.org"),
    ("eBird India",       "https://ebird.org"),
    ("WII Field Rangers", "https://wii.gov.in"),
    ("WWF India",         "https://wwfindia.org"),
    ("Citizen Science Portal", None),
]
srcs = []
for name, url in SOURCES:
    s = existing(DataSource, name=name)
    if not s:
        s = DataSource(name=name, url=url, description=f"{name} biodiversity telemetry ingest")
        db.add(s)
    srcs.append(s)
db.flush()

# ─── 5. OBSERVATIONS (rich geo scatter across India) ──────────────────────────
OBS_COORDS = {
    "Bengal Tiger":           [(29.5, 78.8), (22.3, 80.6), (21.9, 89.2), (23.9, 93.5), (25.1, 82.3), (12.0, 76.0)],
    "Asian Elephant":         [(11.6, 76.6), (11.0, 76.4), (12.0, 76.0), (26.6, 93.4), (27.7, 95.2), (29.5, 78.8)],
    "Indian One-Horned Rhino":[(26.7, 93.4), (26.5, 93.2), (26.8, 93.6), (27.0, 93.8), (26.6, 93.1)],
    "Indian Leopard":         [(29.5, 78.8), (22.3, 80.6), (11.6, 76.6), (21.1, 70.8), (26.9, 71.7), (19.7, 85.3)],
    "Great Indian Bustard":   [(26.9, 71.7), (26.7, 71.5), (27.1, 71.9), (26.5, 71.2), (23.8, 70.2)],
    "Gharial":                [(26.3, 79.1), (26.1, 78.9), (26.5, 79.3), (25.8, 78.5), (26.0, 79.0)],
    "Indian Pangolin":        [(22.5, 80.4), (11.1, 76.5), (25.3, 82.1), (19.7, 85.3), (21.9, 89.1)],
    "Mugger Crocodile":       [(22.6, 80.5), (21.1, 70.8), (19.7, 85.3), (26.6, 93.3), (11.6, 76.6)],
    "Indian Gaur (Bison)":    [(11.7, 76.7), (12.1, 76.1), (22.4, 80.7), (11.1, 76.4), (29.5, 78.7)],
    "Hanuman Langur":         [(29.6, 78.9), (22.4, 80.7), (11.7, 76.7), (21.1, 70.8), (26.8, 71.6)],
    "Chital / Spotted Deer":  [(22.4, 80.7), (11.7, 76.7), (12.1, 76.1), (26.8, 93.5), (29.5, 78.8)],
    "Indian Peafowl":         [(22.4, 80.7), (21.1, 70.8), (26.9, 71.7), (29.5, 78.8), (19.7, 85.3)],
    "European Otter":         [(19.7, 85.3), (26.7, 93.4), (27.7, 95.2), (11.1, 76.4)],
    "Indian Flying Fox":      [(11.0, 76.4), (11.7, 76.7), (19.7, 85.3), (22.3, 80.6), (29.5, 78.7)],
    "Grey Crowned Crane":     [(19.7, 85.3), (23.9, 93.5), (26.7, 93.3)],
}
RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
obs_count = 0
for sp in species_list:
    base_coords = OBS_COORDS.get(sp.common_name, [(20.5, 79.0)])
    n_obs = rng.randint(5, 12)
    for i in range(n_obs):
        base = base_coords[i % len(base_coords)]
        lat = round(base[0] + rng.uniform(-0.35, 0.35), 4)
        lon = round(base[1] + rng.uniform(-0.35, 0.35), 4)
        src = rng.choice(srcs)
        loc = rng.choice(locations)
        obs_date = days_ago(rng.randint(1, 365))
        r_level = rng.choice(RISK_LEVELS)
        r_score = round(rng.uniform(15, 95), 1)
        obs = Observation(
            species_id=sp.id,
            location_id=loc.id,
            source_id=src.id,
            observed_at=obs_date,
            latitude=lat,
            longitude=lon,
            accuracy_meters=rng.choice([10.0, 25.0, 50.0, 100.0]),
            verification_status=rng.choice(["VERIFIED", "VERIFIED", "VERIFIED", "CITIZEN_PENDING"]),
            notes=f"Telemetry sighting recorded at {loc.name} via {src.name}",
            raw_metadata={"risk_level": r_level, "risk_score": r_score}
        )
        db.add(obs)
        obs_count += 1
db.flush()
print(f"  Observations: {obs_count}")

# ─── 6. DOCUMENTS ─────────────────────────────────────────────────────────────
DOCUMENTS = [
    ("Tiger Poaching Nexus in Madhya Pradesh – Intelligence Briefing 2025",
     "INCIDENT_LOG", "DFO Madhya Pradesh",
     """Forest department intelligence unit has identified an active poaching syndicate operating across 
     the Kanha-Pench corridor. Preliminary investigations reveal organized tiger bone and skin smuggling 
     routes linked to international wildlife trafficking networks. Three suspects were apprehended near 
     the Balaghat district boundary carrying tiger claws and 4.2 kg of bones. Analysis of digital 
     communication intercepts reveals coordination with buyers in Southeast Asia. The syndicate uses 
     local guides to evade patrol schedules. Immediate intensification of anti-poaching operations is 
     recommended, including increased tiger-specific camera trap networks and night patrol augmentation. 
     Coordination with INTERPOL Wildlife Crime unit has been initiated. Forest guard mortality risks 
     are considered HIGH in the operational zone.""",
     ["Bengal Tiger", "Indian Leopard"],
     ["Poaching & Illegal Wildlife Trade", "Forest Fire & Arson"]),

    ("GBIF Quarterly Observation Report – Northeast India Q1 2025",
     "RESEARCH_PAPER", "GBIF India Node",
     """Analysis of 14,328 verified species observations submitted to the GBIF India node during 
     January-March 2025 reveals significant population-level trends. Indian rhinoceros sightings in 
     Kaziranga have declined by 12% compared to the same period in 2024, potentially indicating 
     temporary corridor disruption due to ongoing NH-715B construction. Asian elephant observations 
     show unusual eastern clustering beyond traditional range boundaries, consistent with habitat 
     compression hypothesis. Gharial nesting sites on the Chambal River have increased by 3 locations, 
     representing the first positive trend in a decade. Birdwatch India reported 1,247 new species 
     location records from citizen scientists across the Northeast biodiversity hotspot region. 
     Data quality flags were applied to 8.4% of submitted records requiring coordinate verification.""",
     ["Indian One-Horned Rhino", "Asian Elephant", "Gharial"],
     ["Linear Infrastructure (Roads & Rails)", "Habitat Loss & Deforestation"]),

    ("Human-Elephant Conflict Crisis – Assam Community Impact Assessment",
     "GOVT_REPORT", "WWF India Northeast",
     """The expanding tea estate periphery in Assam's Nagaon and Sonitpur districts has triggered 
     an unprecedented human-elephant conflict wave. Between December 2024 and February 2025, 47 crop 
     raids were recorded affecting 312 farming families, with estimated losses of ₹18.7 lakhs. 
     Three human fatalities occurred during nighttime elephant intrusions near Jakhalabandha. 
     The primary driver is documented fragmentation of the Kaziranga-Karbi Anglong corridor by 
     agricultural expansion and unplanned settlements. Mitigation measures deployed include 
     community SMS alert networks covering 23 villages and installation of 4.2 km of solar-powered 
     electric fencing. However, elephant retaliation attacks on fencing have rendered 60% of 
     installed segments non-functional. Urgent corridor restoration via land-use negotiation 
     with tea estates is recommended as the long-term solution.""",
     ["Asian Elephant"],
     ["Human-Wildlife Conflict", "Habitat Loss & Deforestation"]),

    ("Great Indian Bustard Emergency Conservation Action Plan",
     "GOVT_REPORT", "Wildlife Institute of India",
     """The Great Indian Bustard (Ardeotis nigriceps) population has declined to an estimated 
     150 ± 30 individuals, classified as Critically Endangered under IUCN Red List 3.1 criteria. 
     The primary proximate threat is powerline collision mortality, which the WII estimates causes 
     15-18 deaths annually in the Desert National Park landscape. The Supreme Court of India 
     directed underground cabling across 15,000 sq km of critical GIB habitat in March 2021, 
     but implementation progress is less than 12% as of Q4 2024. Secondary threats include 
     free-range dog predation on nests, mechanical harvesting of agriculture eliminating chick 
     habitat, and overgrazing. This action plan recommends: (1) expedited underground cable 
     deployment, (2) head-start captive breeding program at Jaisalmer facility, (3) dog control 
     in buffer zones, and (4) Pavagi grass restoration in degraded grasslands.""",
     ["Great Indian Bustard"],
     ["Linear Infrastructure (Roads & Rails)", "Habitat Loss & Deforestation"]),

    ("Pangolin Trafficking Interception – Wildlife Crime Control Bureau Report",
     "INCIDENT_LOG", "WCCB India",
     """The Wildlife Crime Control Bureau (WCCB) intercepted a major pangolin trafficking shipment 
     at Chennai International Airport. Customs officers seized 32 kg of pangolin scales hidden 
     within consignments of dried fish powder destined for Malaysia. DNA analysis confirmed the 
     scales are from Indian Pangolin (Manis crassicaudata), a Schedule I species under the 
     Wildlife Protection Act 1972. The shipment value is estimated at ₹64 lakhs in domestic markets 
     and USD 180,000 internationally. Intelligence indicates the trafficking ring has operated 
     for at least 18 months across Tamil Nadu, Andhra Pradesh, and Odisha. Local poachers use 
     trained dogs and manual excavation to extract pangolins from burrows. The species faces 
     extinction-level pressure with an estimated 80% global population decline in the last decade 
     primarily driven by demand for scales in traditional Chinese medicine.""",
     ["Indian Pangolin"],
     ["Poaching & Illegal Wildlife Trade"]),

    ("Gharial Population Survey – Chambal River System 2024",
     "RESEARCH_PAPER", "Madhya Pradesh Forest Department",
     """A systematic census of gharial (Gavialis gangeticus) populations across the 635 km National 
     Chambal Sanctuary was conducted using boat-based visual counts and photographic identification. 
     Total population estimate: 287 individuals (95% CI: 264-312), representing a 6.3% increase 
     over the 2022 survey. Juvenile recruitment has improved following the 2023 riverine habitat 
     restoration. However, 14 gharial mortalities attributed to fishing net entanglement were 
     documented during the survey period. Illegal sand mining activity was recorded at 23 locations 
     within the sanctuary boundary, with estimated 40% nest site destruction. The species remains 
     Critically Endangered; population viability analysis indicates at least 500 breeding adults 
     are required for long-term persistence. Immediate net removal operations and sand mining 
     enforcement are critical conservation priorities.""",
     ["Gharial", "Mugger Crocodile"],
     ["Mining & Resource Extraction", "Overfishing & Bycatch"]),

    ("Chilika Lake Ecosystem Health Assessment – Fisherfolk Conflict Analysis",
     "ARTICLE", "Chilika Development Authority",
     """Chilika Lake, Asia's largest coastal wetland and a Ramsar Convention site, is experiencing 
     accelerating ecological stress from multiple anthropogenic pressures. Fishery stock collapse 
     in the outer channel has displaced 9,000 registered fishing families, triggering disputes 
     with mechanized trawler operators entering the protected zone. Irrawaddy dolphin (Orcaella 
     brevirostris) sightings declined by 22% compared to the 2023 baseline, correlating with 
     increased boat traffic and net entanglement incidents. Invasive water hyacinth now covers 
     approximately 18,000 hectares of the lake's central sector, disrupting nesting of migratory 
     bar-headed geese and flamingos. Water quality parameters show declining dissolved oxygen in 
     the southern sector linked to aquaculture effluent discharge. Integrated management action 
     is required addressing fishing community livelihoods, invasive species removal, and 
     aquaculture regulation.""",
     ["European Otter", "Grey Crowned Crane"],
     ["Overfishing & Bycatch", "Invasive Species Pressure", "Pesticide & Chemical Pollution"]),

    ("Climate Vulnerability Assessment – Western Ghats Biodiversity Hotspot",
     "RESEARCH_PAPER", "IISER Pune & Nature Conservation Foundation",
     """Species distribution modeling using MaxEnt and ensemble approaches was applied to 43 endemic 
     Western Ghats vertebrate species under three CMIP6 climate scenarios (SSP2-4.5, SSP3-7.0, 
     SSP5-8.5). Results indicate 67% of modeled species face range contractions exceeding 30% by 
     2050 under the high-emission scenario. Nilgiri tahr, lion-tailed macaque, and Malabar giant 
     squirrel face the highest vulnerability indices. Riverine species in the Periyar and Chaliyar 
     watersheds face complete range loss from projected temperature increases exceeding their 
     physiological thermal tolerance by 2.8°C. The analysis identifies 12 high-priority microrefugia 
     corridors connecting climate-stable patches across the Shola grassland mosaic. Immediate 
     land-use planning integration of climate vulnerability data into Protected Area management 
     plans is recommended, including northward corridor establishment.""",
     ["Indian Gaur (Bison)", "Hanuman Langur"],
     ["Climate Induced Range Shift", "Habitat Loss & Deforestation"]),
]

docs = []
for title, stype, author, content, sp_names, th_names in DOCUMENTS:
    doc = existing(Document, title=title)
    if not doc:
        # Precompute embedding vector for hybrid search
        emb_vec = embedder.embed_text(title + " " + content[:400])
        doc = Document(
            title=title,
            raw_text=content,
            cleaned_text=content.lower(),
            source_type=stype,
            author=author,
            summary=content[:250].strip() + "…",
            topics=rng.sample(["Poaching", "Habitat Loss", "Human-Wildlife Conflict", "Climate Change",
                                "Wetlands", "Policy", "Biodiversity", "Conservation"], k=3),
            embedding_json=emb_vec,
            publication_date=days_ago(rng.randint(10, 200))
        )
        db.add(doc)
        db.flush()

        # Link DocumentSpecies
        for sp_name in sp_names:
            target_sp = next((s for s in species_list if s.common_name == sp_name), None)
            if target_sp:
                db.add(DocumentSpecies(
                    document_id=doc.id,
                    species_id=target_sp.id,
                    mention_count=rng.randint(2, 6)
                ))

        # Link DocumentThreat
        for th_name in th_names:
            target_th = next((t for t in threats if t.category_name == th_name), None)
            if target_th:
                db.add(DocumentThreat(
                    document_id=doc.id,
                    threat_id=target_th.id,
                    confidence_score=round(rng.uniform(0.72, 0.98), 3)
                ))

        # Create NLPAnalysisResult
        nlp = NLPAnalysisResult(
            document_id=doc.id,
            topics=doc.topics,
            raw_meta={
                "sentiment_score": round(rng.uniform(-0.6, 0.1), 3),
                "urgency": rng.choice(["HIGH", "HIGH", "MEDIUM", "LOW"]),
                "processing_time_ms": rng.randint(340, 1200),
                "entity_count": rng.randint(5, 25),
                "sentence_count": rng.randint(8, 40),
            }
        )
        db.add(nlp)

    docs.append(doc)
db.flush()
print(f"  Documents: {len(docs)}")

# ─── 7. ML RISK SCORES ────────────────────────────────────────────────────────
REGIONS = ["Central India", "Western Ghats", "Eastern Himalayas", "Sundarbans", "Terai Arc", "Thar Desert"]
RISK_MAP = {
    "CR": (75, 96, "CRITICAL"),
    "EN": (55, 80, "HIGH"),
    "VU": (35, 60, "MEDIUM"),
    "NT": (20, 40, "LOW"),
    "LC": (5, 25, "LOW"),
}
rs_count = 0
for sp in species_list:
    low, high, risk = RISK_MAP.get(sp.iucn_category, (30, 70, "MEDIUM"))
    score = round(rng.uniform(low, high), 2)
    existing_rs = db.query(MLRiskScore).filter_by(species_id=sp.id).first()
    if not existing_rs:
        db.add(MLRiskScore(
            species_id=sp.id,
            region_name=rng.choice(REGIONS),
            composite_score=score,
            risk_level=risk,
            observation_frequency=round(rng.uniform(0.1, 1.0), 3),
            threat_density=round(rng.uniform(0.2, 0.95), 3),
            temporal_trend=round(rng.uniform(-0.8, 0.3), 3),
            calculated_at=days_ago(rng.randint(0, 30))
        ))
        rs_count += 1
db.flush()
print(f"  ML Risk Scores: {rs_count}")

# ─── 8. ANOMALIES ────────────────────────────────────────────────────────────
ANOMALY_TYPES = ["SPATIAL_TEMPORAL_DEVIATION", "POPULATION_CRASH", "RANGE_SHIFT", "UNUSUAL_CLUSTERING"]
anom_descs = [
    "Isolation Forest detected statistically unusual geographic dispersal beyond sanctuary boundaries.",
    "Observation frequency anomaly detected — 3σ deviation from historical baseline for this species.",
    "Temporal clustering of sightings in an atypical season suggests range displacement or human pressure.",
    "Unusually low observation count compared to prior 6-month moving average, flagging potential population stress.",
    "Multiple sightings concentrated in a single grid cell, potentially indicating a cornered or injured individual.",
]
an_count = 0
for sp in species_list[:10]:
    score = round(rng.uniform(-0.9, -0.2), 4)
    loc = rng.choice(locations)
    existing_an = db.query(MLAnomaly).filter_by(species_id=sp.id).first()
    if not existing_an:
        db.add(MLAnomaly(
            species_id=sp.id,
            location_id=loc.id,
            anomaly_score=score,
            is_anomaly=True,
            anomaly_type=rng.choice(ANOMALY_TYPES),
            explanation=rng.choice(anom_descs),
            detected_at=days_ago(rng.randint(0, 60))
        ))
        an_count += 1
db.flush()
print(f"  Anomalies: {an_count}")

# ─── 9. CONSERVATION ALERTS ──────────────────────────────────────────────────
ALERT_DEFS = [
    ("CRITICAL ALERT: Tiger Corridor Breach Detected", "CRITICAL", "ANOMALY_DETECTED",
     "ML anomaly engine detected statistically significant absence of Bengal Tiger observations in the Pench-Kanha corridor segment for 47 consecutive days. Satellite imagery cross-reference suggests illegal settlement encroachment near buffer zone. Immediate ranger verification patrol recommended."),
    ("HIGH ALERT: Great Indian Bustard Population Below Minimum Viable Threshold", "HIGH", "RISK_THRESHOLD",
     "Species population count (≤150 individuals) has fallen below the Minimum Viable Population threshold modelled by WII. Extinction probability exceeds 40% within 25 years under current threat trajectory. Emergency conservation intervention required."),
    ("HIGH ALERT: Gharial Nest Destruction — Chambal Sand Mining", "HIGH", "ANOMALY_DETECTED",
     "Remote sensing analysis confirms active mechanized sand mining within 200m of mapped gharial nesting sites on the Chambal River. Estimated 6-8 active nests at risk. District administration notified. Immediate enforcement action pending."),
    ("MEDIUM ALERT: Anomalous Elephant Movement — NH-715B Corridor", "MEDIUM", "ANOMALY_DETECTED",
     "Unusual elephant movement patterns detected east of the known range boundary, consistent with habitat compression from highway construction activity. Community alert network activated in adjacent villages."),
    ("MEDIUM ALERT: Pangolin Trafficking Spike Detected", "MEDIUM", "RISK_THRESHOLD",
     "WCCB intelligence data cross-referenced with forest officer reports indicates a 340% increase in pangolin seizure attempts in Tamil Nadu-Andhra Pradesh border region over the last 90 days."),
    ("LOW ALERT: Chilika Lake Irrawaddy Dolphin Sightings Declined", "LOW", "CITIZEN_SUBMISSION",
     "Citizen science data aggregation shows 22% reduction in Irrawaddy dolphin sighting frequency in Chilika Lake outer channel. Potential causes: increased vessel traffic, net entanglement, or seasonal displacement."),
]
al_count = 0
for i, (title, sev, atype, msg) in enumerate(ALERT_DEFS):
    existing_al = db.query(ConservationAlert).filter_by(title=title).first()
    if not existing_al:
        sp = species_list[i % len(species_list)]
        loc = rng.choice(locations)
        db.add(ConservationAlert(
            title=title,
            alert_type=atype,
            message=msg,
            severity=sev,
            species_id=sp.id,
            location_id=loc.id,
            is_resolved=False,
            created_at=days_ago(rng.randint(0, 14))
        ))
        al_count += 1
db.flush()
print(f"  Conservation Alerts: {al_count}")

# ─── COMMIT ──────────────────────────────────────────────────────────────────
db.commit()
db.close()

print()
print("=" * 55)
print("  [SUCCESS] Demo data seeded successfully with rich Indian biodiversity records!")
print("=" * 55)
