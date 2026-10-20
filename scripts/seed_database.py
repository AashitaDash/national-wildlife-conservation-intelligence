import sys
import os
import datetime
import bcrypt

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal, setup_extensions_and_tables
from backend.app.models import (
    Role, User, Species, Location, DataSource, Observation,
    Threat, Document, DocumentSpecies, DocumentThreat,
    MLRiskScore, MLAnomaly, ConservationAlert, UserAlert
)


def get_password_hash(password: str) -> str:
    pwd_bytes = password[:72].encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def seed():
    print("=" * 70)
    print(" WILDLIFE CONSERVATION INTELLIGENCE PLATFORM - SEED ENGINE")
    print(" [Notice: All seeded numbers & reports represent academic sample data]")
    print("=" * 70)

    setup_extensions_and_tables()
    db = SessionLocal()

    try:
        now = datetime.datetime.now(datetime.timezone.utc)

        # ----------------------------------------------------------------------
        # 1. ROLES
        # ----------------------------------------------------------------------
        print("\n[1/9] Seeding Role-Based Access Control Groups...")
        roles_data = [
            ("RESEARCHER", "Academic and field conservation researcher with advanced analytical and export access"),
            ("FOREST_OFFICER", "Field enforcement and protected area range officer with tactical threat alerts"),
            ("NGO", "Non-governmental organization coordinator focused on conservation trends and community advocacy"),
            ("CITIZEN", "Public contributor with search access and citizen observation submission permissions"),
            ("ADMIN", "System administrator overseeing models, users, ingestion health, and audit logs")
        ]
        roles_map = {}
        for name, desc in roles_data:
            role = db.query(Role).filter_by(name=name).first()
            if not role:
                role = Role(name=name, description=desc)
                db.add(role)
                db.flush()
            roles_map[name] = role
        print(f"  [OK] {len(roles_map)} roles verified.")

        # ----------------------------------------------------------------------
        # 2. USERS
        # ----------------------------------------------------------------------
        print("\n[2/9] Seeding Verified Demo Users across all roles...")
        users_data = [
            ("researcher@wildlife.gov.in", "Researcher@123", "Dr. Ananya Roy", "Wildlife Institute of India", "RESEARCHER"),
            ("officer@forest.gov.in", "Officer@123", "Rameshwar Sen", "Odisha Forest Department", "FOREST_OFFICER"),
            ("ngo@wwfindia.org", "Ngo@123", "Pooja Banerjee", "WWF India Conservation Cell", "NGO"),
            ("citizen@gmail.com", "Citizen@123", "Vikram Das", "Citizen Science Network", "CITIZEN"),
            ("admin@wildlife.gov.in", "Admin@123", "System Administrator", "National Biodiversity Authority", "ADMIN")
        ]
        users_map = {}
        for email, pwd, name, org, role_name in users_data:
            u = db.query(User).filter_by(email=email).first()
            if not u:
                u = User(
                    email=email,
                    hashed_password=get_password_hash(pwd),
                    full_name=name,
                    organization=org,
                    role_id=roles_map[role_name].id,
                    is_active=True
                )
                db.add(u)
                db.flush()
            users_map[role_name] = u
        print(f"  [OK] {len(users_map)} system users verified.")

        # ----------------------------------------------------------------------
        # 3. DATA SOURCES
        # ----------------------------------------------------------------------
        print("\n[3/9] Seeding Data Sources & Provenance Registry...")
        sources_data = [
            ("GBIF", "https://api.gbif.org", "Global Biodiversity Information Facility"),
            ("iNaturalist", "https://api.inaturalist.org", "iNaturalist Citizen Science Network"),
            ("eBird", "https://api.ebird.org", "Cornell Lab of Ornithology eBird Platform"),
            ("IUCN Red List", "https://www.iucnredlist.org", "IUCN Global Species Programme"),
            ("GOVERNMENT_REPORT", "https://forest.odisha.gov.in", "Official Forest Department Field Dispatches"),
            ("CITIZEN_PORTAL", "https://wildlife-intel.ac.in", "Direct Platform Public Submissions")
        ]
        sources_map = {}
        for name, url, desc in sources_data:
            s = db.query(DataSource).filter_by(name=name).first()
            if not s:
                s = DataSource(name=name, url=url, description=desc)
                db.add(s)
                db.flush()
            sources_map[name] = s
        print(f"  [OK] {len(sources_map)} data sources configured.")

        # ----------------------------------------------------------------------
        # 4. SPECIES (Authentic Indian Taxa with IUCN Status)
        # ----------------------------------------------------------------------
        print("\n[4/9] Seeding Master Species Catalog...")
        species_catalog = [
            {
                "sci": "Elephas maximus",
                "common": "Asian Elephant",
                "class_name": "Mammalia",
                "order_name": "Proboscidea",
                "family": "Elephantidae",
                "iucn": "EN",
                "desc": "Endangered megaherbivore native to the Indian subcontinent. Highly vulnerable to linear infrastructure, habitat fragmentation, and human-elephant conflict.",
                "img": "https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?w=600"
            },
            {
                "sci": "Panthera tigris",
                "common": "Bengal Tiger",
                "class_name": "Mammalia",
                "order_name": "Carnivora",
                "family": "Felidae",
                "iucn": "EN",
                "desc": "Apex predator of Indian forests. Relies on contiguous canopy corridors, prey density, and strictly protected core reserves.",
                "img": "https://images.unsplash.com/photo-1561731216-c3a4d99437d5?w=600"
            },
            {
                "sci": "Panthera pardus",
                "common": "Indian Leopard",
                "class_name": "Mammalia",
                "order_name": "Carnivora",
                "family": "Felidae",
                "iucn": "VU",
                "desc": "Adaptable big cat frequenting forest buffers and agricultural edges. Significant human-wildlife conflict interface.",
                "img": "https://images.unsplash.com/photo-1456926631375-92c8ce872def?w=600"
            },
            {
                "sci": "Rhinoceros unicornis",
                "common": "Greater One-horned Rhinoceros",
                "class_name": "Mammalia",
                "order_name": "Perissodactyla",
                "family": "Rhinocerotidae",
                "iucn": "VU",
                "desc": "Herbivore inhabiting alluvial grasslands in Assam and North Bengal. Target of organized horn poaching syndicates.",
                "img": "https://images.unsplash.com/photo-1534177616072-ef7dc120449d?w=600"
            },
            {
                "sci": "Panthera uncia",
                "common": "Snow Leopard",
                "class_name": "Mammalia",
                "order_name": "Carnivora",
                "family": "Felidae",
                "iucn": "VU",
                "desc": "High-altitude apex predator of the Trans-Himalayan ranges. Threatened by retaliatory pastoralist conflict and climate retreat.",
                "img": "https://images.unsplash.com/photo-1615963244664-5b845b202bfe?w=600"
            },
            {
                "sci": "Ardeotis nigriceps",
                "common": "Great Indian Bustard",
                "class_name": "Aves",
                "order_name": "Otidiformes",
                "family": "Otididae",
                "iucn": "CR",
                "desc": "Critically Endangered grassland bird with fewer than 150 wild individuals remaining. Severely impacted by high-voltage overhead power lines.",
                "img": "https://images.unsplash.com/photo-1544943910-4c1dc44a0447?w=600"
            },
            {
                "sci": "Gavialis gangeticus",
                "common": "Gharial",
                "class_name": "Reptilia",
                "order_name": "Crocodilia",
                "family": "Gavialidae",
                "iucn": "CR",
                "desc": "Fish-eating crocodilian endemic to deep fast-flowing river systems in northern and eastern India. River sand mining degrades nesting sandbanks.",
                "img": "https://images.unsplash.com/photo-1596707328905-236b2f7358d7?w=600"
            },
            {
                "sci": "Lepidochelys olivacea",
                "common": "Olive Ridley Sea Turtle",
                "class_name": "Reptilia",
                "order_name": "Testudines",
                "family": "Cheloniidae",
                "iucn": "VU",
                "desc": "Marine turtle known for mass nesting (Arribada) along the Odisha coastline. Highly susceptible to mechanized trawl net entanglements.",
                "img": "https://images.unsplash.com/photo-1437622368342-7a3d73a34c8f?w=600"
            },
            {
                "sci": "Nilgiritragus hylocrius",
                "common": "Nilgiri Tahr",
                "class_name": "Mammalia",
                "order_name": "Artiodactyla",
                "family": "Bovidae",
                "iucn": "EN",
                "desc": "Ungulate endemic to montane shola-grassland ecosystems of the Western Ghats. Threatened by invasive wattle/pine and habitat loss.",
                "img": "https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=600"
            },
            {
                "sci": "Manis crassicaudata",
                "common": "Indian Pangolin",
                "class_name": "Mammalia",
                "order_name": "Pholidota",
                "family": "Manidae",
                "iucn": "EN",
                "desc": "Scaly insectivore subject to intensive illicit international trafficking for scales and meat.",
                "img": "https://images.unsplash.com/photo-1574063413132-355dbfd83e25?w=600"
            }
        ]
        species_map = {}
        for sp in species_catalog:
            rec = db.query(Species).filter_by(scientific_name=sp["sci"]).first()
            if not rec:
                rec = Species(
                    scientific_name=sp["sci"],
                    common_name=sp["common"],
                    class_name=sp["class_name"],
                    order_name=sp["order_name"],
                    family=sp["family"],
                    iucn_category=sp["iucn"],
                    description=sp["desc"],
                    image_url=sp["img"]
                )
                db.add(rec)
                db.flush()
            species_map[sp["sci"]] = rec
        print(f"  [OK] {len(species_map)} master species verified.")

        # ----------------------------------------------------------------------
        # 5. LOCATIONS & PROTECTED SANCTUARIES
        # ----------------------------------------------------------------------
        print("\n[5/9] Seeding Protected Areas and Spatial Centroids...")
        locations_data = [
            ("Similipal Tiger Reserve", "Odisha", "Mayurbhanj", "Tiger Reserve", 21.6667, 86.3333, 2750.0),
            ("Kaziranga National Park", "Assam", "Golaghat", "National Park", 26.6667, 93.3500, 858.0),
            ("Jim Corbett National Park", "Uttarakhand", "Nainital", "National Park", 29.5300, 78.7747, 1318.0),
            ("Sundarbans National Park", "West Bengal", "South 24 Parganas", "National Park", 21.9497, 88.8999, 1330.0),
            ("Bandipur National Park", "Karnataka", "Chamarajanagar", "National Park", 11.6667, 76.6333, 874.0),
            ("Gir National Park", "Gujarat", "Junagadh", "National Park", 21.1243, 70.8242, 1412.0),
            ("Desert National Park", "Rajasthan", "Jaisalmer", "National Park", 26.8500, 70.5200, 3162.0),
            ("Satkosia Gorge Sanctuary", "Odisha", "Angul", "Wildlife Sanctuary", 20.5833, 84.8333, 795.0),
            ("Hemis National Park", "Ladakh", "Leh", "National Park", 33.9167, 77.4167, 4400.0),
            ("Eravikulam National Park", "Kerala", "Idukki", "National Park", 10.2000, 77.0667, 97.0)
        ]
        locations_map = {}
        for name, st, dist, ptype, lat, lon, area in locations_data:
            loc = db.query(Location).filter_by(name=name).first()
            if not loc:
                loc = Location(
                    name=name,
                    state=st,
                    district=dist,
                    protected_area_type=ptype,
                    latitude=lat,
                    longitude=lon,
                    area_sq_km=area,
                    geometry_geojson=f'{{"type":"Point","coordinates":[{lon},{lat}]}}'
                )
                db.add(loc)
                db.flush()
            locations_map[name] = loc
        print(f"  [OK] {len(locations_map)} protected sanctuaries verified.")

        # ----------------------------------------------------------------------
        # 6. THREAT TAXONOMY (IUCN Aligned)
        # ----------------------------------------------------------------------
        print("\n[6/9] Seeding IUCN Conservation Threat Categories...")
        threats_data = [
            ("Poaching & Snaring", "5.1.1", 2.5, "Intentional illegal hunting, trapping, or wire-snaring of wildlife."),
            ("Habitat Fragmentation & Encroachment", "4.1", 2.3, "Severing of wildlife migration corridors through settlements and clearance."),
            ("Human-Wildlife Conflict", "1.1", 2.0, "Crop raiding, livestock depredation, and retaliatory incidents."),
            ("Linear Infrastructure & Collisions", "4.1.2", 2.4, "Highways, railway tracks, and fences causing mortality and movement barriers."),
            ("Transmission Line Electrocution", "4.2.1", 2.5, "Uninsulated overhead electrical distribution grids causing fatal shocks."),
            ("Forest Fire & Canopy Burning", "7.1.1", 1.8, "Anthropogenic or climate-induced fires destroying undergrowth and fauna."),
            ("Agricultural Expansion & Deforestation", "2.1.1", 2.1, "Conversion of natural deciduous and evergreen forest canopy to monocultures."),
            ("Invasive Alien Flora", "8.1.1", 1.5, "Proliferation of Lantana camara, Prosopis juliflora, and Senna spectabilis."),
            ("Mining & Quarrying Disturbance", "3.2", 2.4, "Open-cast iron ore, bauxite, and river sand extraction disrupting riverbeds and forests."),
            ("Water Scarcity & Prolonged Drought", "11.2", 1.6, "Climate-induced dry seasons forcing wildlife into human habitations.")
        ]
        threats_map = {}
        for cat_name, code, weight, desc in threats_data:
            th = db.query(Threat).filter_by(category_name=cat_name).first()
            if not th:
                th = Threat(category_name=cat_name, iucn_threat_code=code, severity_weight=weight, description=desc)
                db.add(th)
                db.flush()
            threats_map[cat_name] = th
        print(f"  [OK] {len(threats_map)} threat categories configured.")

        # ----------------------------------------------------------------------
        # 7. OBSERVATIONS (Realistic Spatio-Temporal Distribution)
        # ----------------------------------------------------------------------
        print("\n[7/9] Seeding Realistic Temporal Wildlife Observations (past 180 days)...")
        # Ensure we have observation data across species and locations
        sample_observations = [
            # Similipal Asian Elephants (Temporal decline demonstration)
            ("Elephas maximus", "Similipal Tiger Reserve", "GBIF", 21.684, 86.321, 3, "VERIFIED", "Maternal elephant herd (6 adults, 2 calves) crossing south corridor."),
            ("Elephas maximus", "Similipal Tiger Reserve", "iNaturalist", 21.650, 86.340, 8, "VERIFIED", "Lone tusker sighted near agricultural perimeter of Pithabata range."),
            ("Elephas maximus", "Similipal Tiger Reserve", "GBIF", 21.620, 86.290, 14, "VERIFIED", "Sub-adult elephant group feeding on bamboo clumps."),
            ("Elephas maximus", "Similipal Tiger Reserve", "CITIZEN_PORTAL", 21.580, 86.380, 22, "CITIZEN_PENDING", "Citizen report: Elephant herd entered paddy field near village border."),
            ("Elephas maximus", "Similipal Tiger Reserve", "GOVERNMENT_REPORT", 21.710, 86.310, 35, "VERIFIED", "Forest patrol GPS fix: 12 individuals moving towards Hadgarh sanctuary corridor."),
            ("Elephas maximus", "Similipal Tiger Reserve", "GBIF", 21.640, 86.350, 52, "VERIFIED", "Camera trap photo capture: Elephant family unit."),
            ("Elephas maximus", "Similipal Tiger Reserve", "GBIF", 21.690, 86.300, 75, "VERIFIED", "Winter survey point: 18 elephants logged along river bed."),
            ("Elephas maximus", "Similipal Tiger Reserve", "GBIF", 21.730, 86.330, 110, "VERIFIED", "Historical patrol GPS waypoint."),
            ("Elephas maximus", "Similipal Tiger Reserve", "GBIF", 21.600, 86.370, 145, "VERIFIED", "Baseline monsoon census waypoint."),

            # Bengal Tigers in Similipal (Pseudomelanistic tigers)
            ("Panthera tigris", "Similipal Tiger Reserve", "GOVERNMENT_REPORT", 21.720, 86.360, 5, "VERIFIED", "Camera trap: Verified pseudomelanistic tiger female with clear striping pattern."),
            ("Panthera tigris", "Similipal Tiger Reserve", "GBIF", 21.750, 86.320, 19, "VERIFIED", "Pugmark trail confirmed along stream bank in core zone."),
            ("Panthera tigris", "Similipal Tiger Reserve", "GBIF", 21.690, 86.380, 48, "VERIFIED", "Adult male tiger camera trap photo."),
            ("Panthera tigris", "Similipal Tiger Reserve", "GBIF", 21.710, 86.340, 88, "VERIFIED", "Radio-collar satellite fix (ID: T-12)."),

            # Asian Elephants in Kaziranga & Satkosia
            ("Elephas maximus", "Kaziranga National Park", "GBIF", 26.650, 93.350, 10, "VERIFIED", "Elephant herd migrating southward toward Karbi Anglong hills."),
            ("Elephas maximus", "Satkosia Gorge Sanctuary", "GBIF", 20.583, 84.833, 12, "VERIFIED", "Lone bull elephant sighted foraging near Mahanadi gorge."),

            # Rhinos in Kaziranga
            ("Rhinoceros unicornis", "Kaziranga National Park", "GOVERNMENT_REPORT", 26.680, 93.310, 2, "VERIFIED", "Central range anti-poaching patrol recorded mother with calf."),
            ("Rhinoceros unicornis", "Kaziranga National Park", "GBIF", 26.620, 93.380, 16, "VERIFIED", "Adult male rhino grazing in Bagori grassland sector."),
            ("Rhinoceros unicornis", "Kaziranga National Park", "iNaturalist", 26.640, 93.280, 41, "VERIFIED", "Tourist vehicle safari visual record."),

            # Bengal Tigers in Corbett & Sundarbans
            ("Panthera tigris", "Jim Corbett National Park", "GBIF", 29.530, 78.770, 7, "VERIFIED", "Dhikala grassland morning patrol encounter with adult male tiger."),
            ("Panthera tigris", "Sundarbans National Park", "GOVERNMENT_REPORT", 21.940, 88.910, 15, "VERIFIED", "Pugmark trail tracked along high tide mudflat."),

            # Great Indian Bustard in Desert NP
            ("Ardeotis nigriceps", "Desert National Park", "eBird", 26.850, 70.520, 4, "VERIFIED", "eBird notable: 2 adult Great Indian Bustards foraging in fenced enclosure."),
            ("Ardeotis nigriceps", "Desert National Park", "GOVERNMENT_REPORT", 26.810, 70.480, 25, "VERIFIED", "Breeding display observed by forest guard post."),

            # Gharial in Satkosia
            ("Gavialis gangeticus", "Satkosia Gorge Sanctuary", "GOVERNMENT_REPORT", 20.570, 84.820, 9, "VERIFIED", "Mahanadi river monitoring: 3 sub-adult gharials basking on sand spit."),

            # Olive Ridley Sea Turtle in Odisha coastal margin
            ("Lepidochelys olivacea", "Similipal Tiger Reserve", "GOVERNMENT_REPORT", 20.800, 86.900, 18, "VERIFIED", "Coastal surveillance: Offshore congregation preceding mass nesting."),

            # Snow Leopard in Hemis
            ("Panthera uncia", "Hemis National Park", "GBIF", 33.920, 77.420, 11, "VERIFIED", "Rumbak valley camera trap: Adult snow leopard traversing ridge."),

            # Indian Leopard in Bandipur
            ("Panthera pardus", "Bandipur National Park", "iNaturalist", 11.670, 76.640, 6, "VERIFIED", "Research-grade sighting: Leopard descending tree at dusk.")
        ]

        obs_count = 0
        for sci, loc_name, src_name, lat, lon, days_ago, status, note in sample_observations:
            sp = species_map.get(sci)
            loc = locations_map.get(loc_name)
            src = sources_map.get(src_name)
            if not sp or not loc or not src:
                continue

            obs_date = now - datetime.timedelta(days=days_ago)
            # Check if matching observation exists
            exists = db.query(Observation).filter(
                Observation.species_id == sp.id,
                Observation.location_id == loc.id,
                Observation.latitude == lat,
                Observation.longitude == lon
            ).first()

            if not exists:
                new_obs = Observation(
                    species_id=sp.id,
                    location_id=loc.id,
                    source_id=src.id,
                    submitted_by_user_id=users_map["RESEARCHER"].id if src_name == "GBIF" else users_map["CITIZEN"].id,
                    observed_at=obs_date,
                    latitude=lat,
                    longitude=lon,
                    accuracy_meters=20.0,
                    verification_status=status,
                    notes=f"SAMPLE_DATA: {note}",
                    raw_metadata={"sample": True, "curated_academic_dataset": True}
                )
                db.add(new_obs)
                obs_count += 1

        db.flush()
        print(f"  [OK] {obs_count} new temporal wildlife observations inserted.")

        # ----------------------------------------------------------------------
        # 8. CONSERVATION DOCUMENTS & NLP BENCHMARK TEXTS
        # ----------------------------------------------------------------------
        print("\n[8/9] Seeding Authentic Conservation Documents & Field Incident Reports...")
        doc_samples = [
            {
                "title": "Similipal Elephant Corridor Assessment: Habitat Fragmentation and Railway Corridors in Northern Odisha",
                "source_type": "GOVERNMENT_REPORT",
                "author": "Odisha State Forest Department & Wildlife Trust of India",
                "pub_days_ago": 12,
                "url": "https://forest.odisha.gov.in/reports/similipal-elephant-corridor-2026.pdf",
                "species": ["Elephas maximus"],
                "threats": [
                    "Habitat Fragmentation & Encroachment",
                    "Linear Infrastructure & Collisions",
                    "Human-Wildlife Conflict"
                ],
                "topics": ["Habitat Loss", "Linear Infrastructure", "Human-Wildlife Conflict"],
                "summary": "Recent elephant sightings have increased around Similipal due to habitat fragmentation and agricultural expansion. Railway lines and state highways traversing Mayurbhanj district pose severe collision risks. Intensifying human-elephant conflict requires immediate restoration of the Kuldiha-Hadgarh corridor and dedicated underpasses.",
                "raw_text": (
                    "Recent elephant sightings have increased around Similipal due to habitat fragmentation and "
                    "agricultural expansion. In Mayurbhanj district, traditional migratory routes connecting Similipal "
                    "with Kuldiha Wildlife Sanctuary have been severed by new road widening and railway expansion. "
                    "As herds are forced into fringe agricultural zones, human-elephant conflict incidents, including "
                    "crop raiding and retaliatory measures, have surged over the past eighteen months. "
                    "Uninsulated low-hanging electrical transmission lines and high-speed freight trains represent "
                    "critical mortality drivers for Asian elephants in northern Odisha. Key recommendations include "
                    "the construction of dedicated eco-ducts, solar fencing around vulnerable villages, and satellite "
                    "tracking of high-risk herd movements."
                )
            },
            {
                "title": "Mayurbhanj Forest Incident Dispatch: Crop Depredation and Electrocution Hazards",
                "source_type": "INCIDENT_LOG",
                "author": "Regional Range Officer, Baripada Forest Division",
                "pub_days_ago": 5,
                "url": "https://forest.odisha.gov.in/dispatches/mayurbhanj-incident-44.pdf",
                "species": ["Elephas maximus"],
                "threats": [
                    "Human-Wildlife Conflict",
                    "Transmission Line Electrocution",
                    "Poaching & Snaring"
                ],
                "topics": ["Conflict Incident", "Poaching & Snaring"],
                "summary": "Urgent dispatch reporting elephant herd movement into village farm plots near Betnoti. Low-hanging agricultural transmission lines pose immediate electrocution hazard.",
                "raw_text": (
                    "Field rangers intercepted a herd of seven Asian elephants in Mayurbhanj buffer farmland near Betnoti. "
                    "Local farmers reported extensive paddy destruction. Forest patrol discovered illegal wire snares placed along "
                    "boundary trenches and notified anti-poaching teams. Low-hanging 11kV agricultural power cables create an imminent "
                    "electrocution danger for passing tuskers. Solar illumination torches and rapid response squads deployed."
                )
            },
            {
                "title": "Kaziranga National Park Annual Anti-Poaching and Flood Inundation Report",
                "source_type": "RESEARCH_PAPER",
                "author": "Assam Forest Department & Centre for Wildlife Studies",
                "pub_days_ago": 45,
                "url": "https://kaziranga.assam.gov.in/research/rhino-anti-poaching-annual-2025.pdf",
                "species": ["Rhinoceros unicornis", "Panthera tigris", "Elephas maximus"],
                "threats": [
                    "Poaching & Snaring",
                    "Linear Infrastructure & Collisions",
                    "Water Scarcity & Prolonged Drought"
                ],
                "topics": ["Poaching & Illegal Trade", "Population Survey"],
                "summary": "Annual review of Greater One-horned Rhinoceros protection measures in Kaziranga. Highlights anti-poaching camera surveillance and high-ground animal crossings along National Highway 715.",
                "raw_text": (
                    "Intensive thermal drone patrols and electronic surveillance grids have significantly reduced rhino horn poaching "
                    "across Kaziranga National Park. However, annual Brahmaputra monsoon inundation forces wildlife, including rhinos, "
                    "elephants, and tigers, to cross National Highway 715 towards the Karbi Anglong highlands, exposing them to high-speed vehicular "
                    "collisions. Elevated wildlife corridors and automated speed-enforcement cameras have proven essential to minimizing casualties."
                )
            },
            {
                "title": "Desert National Park Mitigation Strategy: Mitigating Powerline Mortalities for Great Indian Bustard",
                "source_type": "CONSERVATION_ARTICLE",
                "author": "Bombay Natural History Society (BNHS)",
                "pub_days_ago": 30,
                "url": "https://bnhs.org/articles/gib-powerline-mitigation.html",
                "species": ["Ardeotis nigriceps"],
                "threats": [
                    "Transmission Line Electrocution",
                    "Linear Infrastructure & Collisions",
                    "Habitat Fragmentation & Encroachment"
                ],
                "topics": ["Policy & Protection", "Habitat Loss"],
                "summary": "Analysis of collision risks for Great Indian Bustard in the Thar desert. Urges underground cabling of transmission wires to prevent species extinction.",
                "raw_text": (
                    "The Great Indian Bustard (Ardeotis nigriceps) faces imminent extinction in Rajasthan's Thar desert. Due to limited frontal "
                    "vision, bustards cannot detect overhead transmission cables in time to adjust flight paths, leading to fatal impacts. "
                    "Bird flight diverters provide partial protection, but comprehensive underground routing of power cables in priority habitats "
                    "remains the only scientifically robust intervention to preserve the remaining wild population."
                )
            }
        ]

        doc_count = 0
        for d in doc_samples:
            doc = db.query(Document).filter_by(title=d["title"]).first()
            if not doc:
                pub_date = now - datetime.timedelta(days=d["pub_days_ago"])
                # Generate a mock normalized 384-dimensional vector embedding
                mock_vector = [0.05 * (i % 7 - 3) for i in range(384)]
                # Normalize vector to unit length
                norm = sum(x**2 for x in mock_vector)**0.5
                mock_vector = [round(x / norm, 5) for x in mock_vector]

                doc = Document(
                    title=d["title"],
                    source_type=d["source_type"],
                    author=d["author"],
                    publication_date=pub_date,
                    url=d["url"],
                    raw_text=d["raw_text"],
                    cleaned_text=d["raw_text"].strip(),
                    summary=d["summary"],
                    topics=d["topics"],
                    embedding_json=mock_vector,
                    author_user_id=users_map["RESEARCHER"].id
                )
                db.add(doc)
                db.flush()

                # Link species
                for s_sci in d["species"]:
                    sp_obj = species_map.get(s_sci)
                    if sp_obj:
                        db.add(DocumentSpecies(document_id=doc.id, species_id=sp_obj.id, mention_count=4))

                # Link threats
                for t_name in d["threats"]:
                    th_obj = threats_map.get(t_name)
                    if th_obj:
                        db.add(DocumentThreat(document_id=doc.id, threat_id=th_obj.id, confidence_score=0.92))

                doc_count += 1

        db.flush()
        print(f"  [OK] {doc_count} conservation reports ingested and entity-linked.")

        # ----------------------------------------------------------------------
        # 9. ML RISK SCORES, ANOMALIES & SYSTEM ALERTS
        # ----------------------------------------------------------------------
        print("\n[9/9] Seeding Initial Machine Learning Decisions & Tactical Alerts...")
        
        # Risk Score: Asian Elephant in Odisha
        elephant = species_map["Elephas maximus"]
        similipal = locations_map["Similipal Tiger Reserve"]

        existing_risk = db.query(MLRiskScore).filter_by(species_id=elephant.id, region_name="Odisha").first()
        if not existing_risk:
            risk_score = MLRiskScore(
                species_id=elephant.id,
                region_name="Odisha",
                composite_score=78.0,
                risk_level="HIGH",
                observation_frequency=14.0,
                threat_density=5.2,
                temporal_trend=-0.28,  # Negative indicating observed decline
                feature_snapshot={
                    "recent_14d_obs": 3,
                    "baseline_90d_obs": 9,
                    "threat_mentions_30d": 8,
                    "hwc_frequency": 6,
                    "corridor_severance_score": 0.82
                }
            )
            db.add(risk_score)

        # Risk Score: Great Indian Bustard in Rajasthan
        gib = species_map["Ardeotis nigriceps"]
        existing_gib_risk = db.query(MLRiskScore).filter_by(species_id=gib.id, region_name="Rajasthan").first()
        if not existing_gib_risk:
            gib_risk = MLRiskScore(
                species_id=gib.id,
                region_name="Rajasthan",
                composite_score=94.5,
                risk_level="CRITICAL",
                observation_frequency=2.0,
                threat_density=7.8,
                temporal_trend=-0.50,
                feature_snapshot={
                    "recent_14d_obs": 1,
                    "baseline_90d_obs": 2,
                    "threat_mentions_30d": 12,
                    "powerline_density_km2": 4.1
                }
            )
            db.add(gib_risk)

        # ML Anomaly: Spatial-temporal spike in snaring encounters
        existing_anomaly = db.query(MLAnomaly).filter_by(species_id=elephant.id, location_id=similipal.id).first()
        if not existing_anomaly:
            anomaly = MLAnomaly(
                species_id=elephant.id,
                location_id=similipal.id,
                anomaly_type="INCIDENT_SURGE",
                anomaly_score=-0.435,  # Isolation forest negative decision boundary
                is_anomaly=True,
                explanation="Unusual surge in snaring and crop-depredation dispatches flagged in Mayurbhanj southern buffer zone."
            )
            db.add(anomaly)

        # Tactical Alert for Forest Officers
        existing_alert = db.query(ConservationAlert).filter_by(species_id=elephant.id, location_id=similipal.id).first()
        if not existing_alert:
            alert = ConservationAlert(
                title="HIGH RISK ALERT: Asian Elephant Corridor Severance in Similipal",
                severity="HIGH",
                alert_type="RISK_THRESHOLD",
                message="AI Risk Score calculated at 78.0/100 (HIGH). Rapid encroachment and snaring incidents detected along Mayurbhanj corridor.",
                species_id=elephant.id,
                location_id=similipal.id,
                is_resolved=False
            )
            db.add(alert)
            db.flush()

            # Map alert to Officer and Researcher
            db.add(UserAlert(alert_id=alert.id, user_id=users_map["FOREST_OFFICER"].id, is_read=False))
            db.add(UserAlert(alert_id=alert.id, user_id=users_map["RESEARCHER"].id, is_read=False))

        db.commit()
        print("  [OK] ML risk profiles, Isolation Forest outliers, and officer alerts persisted.")
        print("-" * 70)
        print("SEEDING COMPLETE: Database populated with rich, authentic conservation intelligence.")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
