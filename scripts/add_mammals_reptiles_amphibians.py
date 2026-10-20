"""
add_mammals_reptiles_amphibians.py
====================================
Adds IUCN-listed Indian mammals, reptiles, and amphibians to the species catalog.
- NEVER modifies existing species
- NEVER deletes observations
- Checks for duplicates before inserting
- Fetches verified iNaturalist photos for each species
"""
import sys
import time
import requests

sys.path.append('.')
from backend.app.database import SessionLocal
from backend.app.models.species import Species

# ─────────────────────────────────────────────────────────────────────────────
# SPECIES CATALOG TO ADD
# Format: (scientific_name, common_name, class_name, order_name, family, genus, iucn_category, description)
# ─────────────────────────────────────────────────────────────────────────────
NEW_SPECIES = [
    # ══════════════════ MAMMALIA ══════════════════
    ("Panthera leo persica",     "Asiatic Lion",               "Mammalia", "Carnivora",    "Felidae",       "Panthera",         "EN", "Critically endangered population of lions restricted to Gir Forest, Gujarat. Last wild population in Asia."),
    ("Cuon alpinus",             "Dhole",                      "Mammalia", "Carnivora",    "Canidae",        "Cuon",             "EN", "Endangered wild dog found in forested regions. Highly social pack hunter; plays critical role in ecosystem regulation."),
    ("Melursus ursinus",         "Sloth Bear",                 "Mammalia", "Carnivora",    "Ursidae",        "Melursus",         "VU", "Vulnerable bear species endemic to the Indian subcontinent. Primarily insectivorous; iconic wildlife of central India."),
    ("Prionailurus viverrinus",  "Fishing Cat",                "Mammalia", "Carnivora",    "Felidae",        "Prionailurus",     "VU", "Vulnerable wetland felid with partially webbed feet. Found in mangroves and freshwater wetlands across South Asia."),
    ("Macaca silenus",           "Lion-tailed Macaque",        "Mammalia", "Primates",     "Cercopithecidae","Macaca",           "EN", "Endangered endemic primate of the Western Ghats. Characterized by its distinctive silver mane. Highly habitat-sensitive."),
    ("Trachypithecus johnii",    "Nilgiri Langur",             "Mammalia", "Primates",     "Cercopithecidae","Trachypithecus",   "VU", "Vulnerable Old World monkey restricted to the Nilgiri Hills and Western Ghats. Black-coated leaf-eating primate."),
    ("Hoolock hoolock",          "Western Hoolock Gibbon",     "Mammalia", "Primates",     "Hylobatidae",    "Hoolock",          "EN", "Only ape species found in India. Endangered due to forest fragmentation in Northeast India. Monogamous and territorial."),
    ("Platanista gangetica",     "Gangetic River Dolphin",     "Mammalia", "Artiodactyla", "Platanistidae",  "Platanista",       "EN", "Endangered freshwater dolphin nearly blind due to murky river habitat. National aquatic animal of India; found in Ganges-Brahmaputra basin."),
    ("Porcula salvania",         "Pygmy Hog",                  "Mammalia", "Artiodactyla", "Suidae",         "Porcula",          "CR", "Critically Endangered and world's smallest wild pig. Restricted to tall grasslands of Assam. Subject of intensive conservation breeding programs."),
    ("Ailurus fulgens",          "Red Panda",                  "Mammalia", "Carnivora",    "Ailuridae",      "Ailurus",          "EN", "Endangered arboreal mammal of the Himalayas. Feeds primarily on bamboo. Iconic flagship species of Eastern Himalayan biodiversity."),
    ("Neofelis nebulosa",        "Clouded Leopard",            "Mammalia", "Carnivora",    "Felidae",        "Neofelis",         "VU", "Vulnerable medium-sized wild cat with distinctive cloud-pattern coat. Found in Himalayan foothills and Northeast India."),
    ("Rucervus duvaucelii",      "Barasingha",                 "Mammalia", "Artiodactyla", "Cervidae",       "Rucervus",         "VU", "Vulnerable swamp deer endemic to the Indian subcontinent. Named for its distinctive large branching antlers. Key species of terai grasslands."),
    ("Tetracerus quadricornis",  "Four-horned Antelope",       "Mammalia", "Artiodactyla", "Bovidae",        "Tetracerus",       "VU", "Vulnerable and unique antelope; only wild bovid in the world to have four horns. Endemic to the Indian subcontinent."),
    ("Lutrogale perspicillata",  "Smooth-coated Otter",        "Mammalia", "Carnivora",    "Mustelidae",     "Lutrogale",        "VU", "Vulnerable semi-aquatic mammal found in rivers, lakes, and coastal areas. Largest otter species in Asia; indicator of water quality."),
    ("Helarctos malayanus",      "Sun Bear",                   "Mammalia", "Carnivora",    "Ursidae",        "Helarctos",        "VU", "Vulnerable smallest bear species in the world. Found in dense tropical forests of Northeast India. Distinctive chest patch markings."),
    ("Viverra civettina",        "Malabar Large-spotted Civet","Mammalia", "Carnivora",    "Viverridae",     "Viverra",          "CR", "Critically Endangered large civet endemic to the Western Ghats. One of the rarest mammals in India; rarely photographed in the wild."),
    ("Caprolagus hispidus",      "Hispid Hare",                "Mammalia", "Lagomorpha",   "Leporidae",      "Caprolagus",       "EN", "Endangered rabbit-like mammal with coarse bristly fur. Restricted to tall terai grasslands of the sub-Himalayan region."),
    ("Trachypithecus geei",      "Golden Langur",              "Mammalia", "Primates",     "Cercopithecidae","Trachypithecus",   "EN", "Endangered primate with striking golden fur found only in Assam and Bhutan. One of the world's most endangered primates."),
    ("Bos gaurus",               "Gaur",                       "Mammalia", "Artiodactyla", "Bovidae",        "Bos",              "VU", "Vulnerable largest extant bovine. Massive, powerful wild cattle found in forests across South and Southeast Asia."),
    ("Prionailurus rubiginosus", "Rusty-spotted Cat",          "Mammalia", "Carnivora",    "Felidae",        "Prionailurus",     "NT", "Near Threatened world's smallest wild cat; some individuals weigh under 1 kg. Endemic to India and Sri Lanka."),
    ("Hyaena hyaena",            "Striped Hyena",              "Mammalia", "Carnivora",    "Hyaenidae",      "Hyaena",           "NT", "Near Threatened large carnivore found in arid and semi-arid regions. Important scavenger contributing to nutrient cycling."),
    ("Rusa unicolor",            "Sambar",                     "Mammalia", "Artiodactyla", "Cervidae",        "Rusa",             "VU", "Vulnerable large deer species widespread across South and Southeast Asia. Primary prey of tigers and leopards in many ecosystems."),
    ("Orcaella brevirostris",    "Irrawaddy Dolphin",          "Mammalia", "Artiodactyla", "Delphinidae",    "Orcaella",         "EN", "Endangered dolphin found in coastal and riverine habitats. Known for cooperative fishing with humans in Myanmar."),
    ("Equus hemionus khur",      "Indian Wild Ass",            "Mammalia", "Perissodactyla","Equidae",       "Equus",            "NT", "Near Threatened wild ass restricted to the Little Rann of Kutch in Gujarat. Symbol of the dry scrubland ecosystem."),
    ("Pardofelis marmorata",     "Marbled Cat",                "Mammalia", "Carnivora",    "Felidae",        "Pardofelis",       "NT", "Near Threatened small wild cat with distinctive marbled coat pattern. Found in forested hills of the Himalayas and Northeast India."),
    ("Aonyx cinereus",           "Asian Small-clawed Otter",   "Mammalia", "Carnivora",    "Mustelidae",     "Aonyx",            "VU", "Vulnerable smallest otter species. Uses forepaws to catch prey rather than mouth. Highly social and found in freshwater habitats."),
    ("Antilope cervicapra",      "Blackbuck",                  "Mammalia", "Artiodactyla", "Bovidae",        "Antilope",         "LC", "Endemic antelope of the Indian subcontinent. Only living species of genus Antilope. Males have distinctive spiraling horns."),
    ("Boselaphus tragocamelus",  "Nilgai",                     "Mammalia", "Artiodactyla", "Bovidae",        "Boselaphus",       "LC", "Asia's largest antelope, endemic to the Indian subcontinent. Also called Blue Bull; males have distinctive bluish-grey coat."),

    # ══════════════════ REPTILIA ══════════════════
    ("Ophiophagus hannah",       "King Cobra",                 "Reptilia", "Squamata",     "Elapidae",       "Ophiophagus",      "VU", "Vulnerable world's longest venomous snake. Found in forests across South and Southeast Asia. Uniquely builds a nest for its eggs."),
    ("Crocodylus palustris",     "Mugger Crocodile",           "Reptilia", "Crocodilia",   "Crocodylidae",   "Crocodylus",       "VU", "Vulnerable freshwater crocodile endemic to the Indian subcontinent. Found in rivers, lakes, and man-made reservoirs."),
    ("Crocodylus porosus",       "Saltwater Crocodile",        "Reptilia", "Crocodilia",   "Crocodylidae",   "Crocodylus",       "LC", "World's largest living reptile. Found in mangroves and coastal waterways. Apex predator of estuarine ecosystems."),
    ("Python molurus",           "Indian Rock Python",         "Reptilia", "Squamata",     "Pythonidae",     "Python",           "VU", "Vulnerable large constrictor snake; one of the six largest snakes in the world. Found across South Asia in varied habitats."),
    ("Varanus bengalensis",      "Bengal Monitor",             "Reptilia", "Squamata",     "Varanidae",      "Varanus",          "LC", "Large monitor lizard widespread across South and Southeast Asia. Important scavenger; plays key role in maintaining ecosystem health."),
    ("Varanus flavescens",       "Yellow Monitor",             "Reptilia", "Squamata",     "Varanidae",      "Varanus",          "VU", "Vulnerable monitor lizard restricted to the Indo-Gangetic plains. Listed under CITES Appendix I due to illegal skin trade."),
    ("Geochelone elegans",       "Indian Star Tortoise",       "Reptilia", "Testudines",   "Testudinidae",   "Geochelone",       "VU", "Vulnerable tortoise with striking star-patterned shell. Endemic to India and Sri Lanka. Heavily impacted by illegal pet trade."),
    ("Indotestudo travancorica", "Travancore Tortoise",        "Reptilia", "Testudines",   "Testudinidae",   "Indotestudo",      "CR", "Critically Endangered tortoise restricted to the Western Ghats. Among the most threatened tortoise species in Asia."),
    ("Batagur kachuga",          "Red-crowned Roofed Turtle",  "Reptilia", "Testudines",   "Geoemydidae",    "Batagur",          "CR", "Critically Endangered large river turtle of the Ganges basin. Males develop brilliant red-orange head coloration during breeding season."),
    ("Dermochelys coriacea",     "Leatherback Sea Turtle",     "Reptilia", "Testudines",   "Dermochelyidae", "Dermochelys",      "VU", "Vulnerable world's largest sea turtle and heaviest living reptile. Migrates thousands of kilometres; nests on Indian coastlines."),
    ("Chelonia mydas",           "Green Sea Turtle",           "Reptilia", "Testudines",   "Cheloniidae",    "Chelonia",         "EN", "Endangered large sea turtle named for the green fat beneath its shell. Nests on beaches of India's Andaman and Nicobar Islands."),
    ("Eretmochelys imbricata",   "Hawksbill Sea Turtle",       "Reptilia", "Testudines",   "Cheloniidae",    "Eretmochelys",     "CR", "Critically Endangered sea turtle with distinctive narrow pointed beak. Plays crucial ecological role in coral reef ecosystems."),
    ("Nilssonia gangetica",      "Indian Softshell Turtle",    "Reptilia", "Testudines",   "Trionychidae",   "Nilssonia",        "CR", "Critically Endangered large river turtle of the Ganges-Indus river system. One of the fastest-declining turtle species in the world."),
    ("Chamaeleo zeylanicus",     "Indian Chameleon",           "Reptilia", "Squamata",     "Chamaeleonidae", "Chamaeleo",        "LC", "Only chameleon species native to India. Found in scrub forests and agricultural areas of peninsular India. Known for colour change."),

    # ══════════════════ AMPHIBIA ══════════════════
    ("Nasikabatrachus sahyadrensis","Purple Frog",             "Amphibia", "Anura",        "Nasikabatrachidae","Nasikabatrachus","EN", "Endangered ancient frog species discovered in 2003. Spends most of year underground; surfaces only for 2 weeks to breed. Endemic to Western Ghats."),
    ("Rhacophorus malabaricus",  "Malabar Gliding Frog",       "Amphibia", "Anura",        "Rhacophoridae",  "Rhacophorus",      "LC", "Large arboreal frog with huge webbed feet that enable gliding between trees. Endemic to the Western Ghats of India."),
    ("Nyctibatrachus major",     "Large Wrinkled Frog",        "Amphibia", "Anura",        "Nyctibatrachidae","Nyctibatrachus",  "EN", "Endangered stream frog endemic to the Western Ghats. Found near fast-flowing forest streams. Highly sensitive to habitat disturbance."),
    ("Raorchestes annandalii",   "Annandale's Bush Frog",      "Amphibia", "Anura",        "Rhacophoridae",  "Raorchestes",      "EN", "Endangered miniature frog endemic to the high-altitude Nilgiri Hills. Part of a recently described group of bush frogs."),
    ("Clinotarsus curtipes",     "Bicolored Frog",             "Amphibia", "Anura",        "Ranidae",        "Clinotarsus",      "NT", "Near Threatened medium-sized frog endemic to the Western Ghats. Characterized by striking two-toned coloration."),
    ("Indirana beddomii",        "Beddome's Indian Frog",      "Amphibia", "Anura",        "Ranixalidae",    "Indirana",         "EN", "Endangered frog endemic to the southern Western Ghats. Part of an ancient lineage found only in India."),
    ("Micrixalus fuscus",        "Dusky Torrent Frog",         "Amphibia", "Anura",        "Micrixalidae",   "Micrixalus",       "EN", "Endangered tiny frog that breeds in fast-flowing rocky streams of the Western Ghats. Males perform elaborate foot-flagging displays."),
]

INAT_API = "https://api.inaturalist.org/v1/observations"

def fetch_inat_photo(scientific_name: str):
    """Fetch a verified research-grade photo from iNaturalist."""
    try:
        params = {
            "taxon_name": scientific_name,
            "has[]": "photos",
            "quality_grade": "research",
            "per_page": 5,
            "order_by": "votes",
        }
        r = requests.get(INAT_API, params=params, timeout=12)
        if r.status_code != 200:
            return None, None, None
        results = r.json().get("results", [])
        for obs in results:
            taxon = obs.get("taxon", {})
            # Require genus-level match at minimum
            obs_sci = taxon.get("name", "")
            genus = scientific_name.split()[0]
            if not obs_sci.startswith(genus):
                continue
            photos = obs.get("photos", [])
            if not photos:
                continue
            photo = photos[0]
            raw_url = photo.get("url", "")
            if not raw_url:
                continue
            photo_url = raw_url.replace("/square.", "/original.")
            license_code = photo.get("license_code") or "all-rights-reserved"
            attribution = photo.get("attribution", "")
            # Verify URL is live
            head = requests.head(photo_url, timeout=8)
            if head.status_code == 200:
                return photo_url, license_code, attribution
    except Exception as e:
        print(f"    iNat error for {scientific_name}: {e}")
    return None, None, None


def main():
    db = SessionLocal()

    existing = {sp.scientific_name for sp in db.query(Species.scientific_name).all()}
    print(f"Existing species in DB: {len(existing)}")

    added = 0
    skipped = 0
    no_photo = 0

    for i, row in enumerate(NEW_SPECIES):
        sci_name, common_name, cls, order, family, genus, iucn, desc = row
        prefix = f"[{i+1}/{len(NEW_SPECIES)}] {sci_name}"

        if sci_name in existing:
            print(f"{prefix} -> SKIP (already exists)")
            skipped += 1
            continue

        # Fetch photo
        photo_url, license_code, attribution = fetch_inat_photo(sci_name)
        if photo_url:
            img_src = "iNaturalist"
        else:
            img_src = None
            no_photo += 1
            print(f"{prefix} -> NO PHOTO")

        sp = Species(
            scientific_name=sci_name,
            common_name=common_name,
            class_name=cls,
            order_name=order,
            family=family,
            genus=genus,
            iucn_category=iucn,
            description=desc,
            image_url=photo_url,
            image_source=img_src,
            image_license=license_code,
            image_attribution=attribution,
        )
        db.add(sp)
        db.commit()
        db.refresh(sp)
        added += 1
        print(f"{prefix} -> ADDED [id={sp.id}] {'[PHOTO OK]' if photo_url else '[NO PHOTO]'}")

        # Polite rate limit
        time.sleep(0.8)

    print()
    print("=" * 50)
    print("SPECIES ADDITION REPORT")
    print("=" * 50)
    final_count = db.query(Species).count()
    print(f"Added:       {added}")
    print(f"Skipped:     {skipped} (already existed)")
    print(f"No photo:    {no_photo}")
    print(f"Total now:   {final_count}")
    print("=" * 50)
    db.close()


if __name__ == "__main__":
    main()
