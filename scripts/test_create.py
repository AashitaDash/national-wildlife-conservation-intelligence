with open("scripts/run_ingestion.py") as f:
    if "def create_species_from_record" in f.read():
        print("YES")
    else:
        print("NO")
