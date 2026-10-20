import pytest
import datetime
from ingestion.cleaner import DataCleaner
from ingestion.document_parser import DocumentParser
from ingestion.gbif_client import GBIFClient
from ingestion.inat_client import INaturalistClient
from ingestion.ebird_client import EBirdClient


def test_coordinate_validation():
    # Valid coordinates inside Indian envelope (Similipal)
    valid, msg = DataCleaner.validate_coordinates(21.6667, 86.3333)
    assert valid is True
    assert msg == "Valid"

    # Out of latitude range
    invalid_lat, msg = DataCleaner.validate_coordinates(95.0, 86.0)
    assert invalid_lat is False
    assert "Latitude" in msg

    # Coordinates outside Indian envelope (e.g., North America)
    out_of_region, msg = DataCleaner.validate_coordinates(40.7128, -74.0060)
    assert out_of_region is False
    assert "outside the Indian geographic envelope" in msg


def test_observation_deduplication():
    now = datetime.datetime.now(datetime.timezone.utc)
    raw_obs = [
        {
            "scientific_name": "Elephas maximus",
            "latitude": 21.66671,
            "longitude": 86.33331,
            "observed_at": now,
            "notes": "Observation A"
        },
        # Duplicate in same ~110m cell on same day
        {
            "scientific_name": "Elephas maximus",
            "latitude": 21.66674,
            "longitude": 86.33329,
            "observed_at": now,
            "notes": "Duplicate of A"
        },
        # Distinct observation further away
        {
            "scientific_name": "Elephas maximus",
            "latitude": 21.7500,
            "longitude": 86.4200,
            "observed_at": now,
            "notes": "Observation B"
        }
    ]

    deduped = DataCleaner.deduplicate_observations(raw_obs)
    assert len(deduped) == 2
    assert deduped[0]["notes"] == "Observation A"
    assert deduped[1]["notes"] == "Observation B"


def test_species_name_canonicalization():
    assert DataCleaner.canonicalize_species_name("elephas maximus subsp. indicus") == "Elephas maximus"
    assert DataCleaner.canonicalize_species_name("Panthera tigris tigris") == "Panthera tigris"
    assert DataCleaner.canonicalize_species_name("  panthera pardus  ") == "Panthera pardus"


def test_document_parser():
    raw_text = """
    Recent   elephant   sightings have increased around Similipal\x00.
    
    
    Multiple corridors have been fragmented by railway tracks.
    """
    parsed = DocumentParser.parse_document(
        title="Corridor Assessment",
        raw_text=raw_text,
        source_type="GOVERNMENT_REPORT",
        author="Forest Department"
    )

    assert parsed["title"] == "Corridor Assessment"
    assert parsed["source_type"] == "GOVERNMENT_REPORT"
    assert "\x00" not in parsed["cleaned_text"]
    assert "Recent elephant sightings" in parsed["cleaned_text"]
    assert parsed["word_count"] > 10


def test_gbif_client_fallback_structure():
    client = GBIFClient()
    records = client.get_fallback_data("Elephas maximus")
    assert len(records) > 0
    first = records[0]
    assert first["source"] == "GBIF"
    assert first["scientific_name"] == "Elephas maximus"
    assert "latitude" in first and "longitude" in first
    assert first["verification_status"] == "VERIFIED"


def test_inaturalist_client_fallback_structure():
    client = INaturalistClient()
    records = client.get_fallback_data("Panthera pardus")
    assert len(records) > 0
    first = records[0]
    assert first["source"] == "iNaturalist"
    assert first["scientific_name"] == "Panthera pardus"
    assert "verification_status" in first


def test_ebird_client_fallback_structure():
    client = EBirdClient(api_key="mock_key")
    records = client.fetch_records("Ardeotis nigriceps")
    assert len(records) > 0
    first = records[0]
    assert first["source"] == "eBird"
    assert first["scientific_name"] == "Ardeotis nigriceps"


def test_non_avian_coordinate_envelope_validation():
    # Strict boundary checks for Indian subcontinent
    assert DataCleaner.validate_coordinates(28.6139, 77.2090)[0] is True   # Delhi
    assert DataCleaner.validate_coordinates(11.9416, 79.8083)[0] is True   # Puducherry
    assert DataCleaner.validate_coordinates(34.0837, 74.7973)[0] is True   # Srinagar
    assert DataCleaner.validate_coordinates(1.3521, 103.8198)[0] is False  # Singapore (outside envelope)
    assert DataCleaner.validate_coordinates(-33.8688, 151.2093)[0] is False # Sydney (outside envelope)
    assert DataCleaner.validate_coordinates(51.5074, -0.1278)[0] is False  # London (outside envelope)


def test_source_specific_fingerprinting_deduplication():
    from scripts.expand_sparse_non_avian import is_valid_india_coord
    
    assert is_valid_india_coord(22.5, 88.3) is True
    assert is_valid_india_coord(55.0, 37.0) is False
    assert is_valid_india_coord(None, 88.0) is False
    assert is_valid_india_coord(22.0, None) is False


def test_api_session_retries_and_headers():
    from scripts.expand_sparse_non_avian import create_resilient_session
    session = create_resilient_session()
    assert "User-Agent" in session.headers
    assert "WildlifeConservation" in session.headers["User-Agent"]
    assert "https://" in session.adapters
    adapter = session.adapters["https://"]
    assert adapter.max_retries.total == 4

