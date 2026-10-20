echo "=== 1. TEST SUITE ==="
pytest backend/app/tests
echo "=== 2. INITIAL AUDIT ==="
python scripts/audit_db.py
echo "=== 3. GBIF INGESTION 1 ==="
python scripts/run_ingestion.py --source gbif
echo "=== 4. INATURALIST INGESTION 1 ==="
python scripts/run_ingestion.py --source inaturalist
echo "=== 5. AUDIT 2 ==="
python scripts/audit_db.py
echo "=== 6. GBIF INGESTION 2 ==="
python scripts/run_ingestion.py --source gbif
echo "=== 7. INATURALIST INGESTION 2 ==="
python scripts/run_ingestion.py --source inaturalist
echo "=== 8. FINAL AUDIT ==="
python scripts/audit_db.py
