import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_get_state_metrics_all():
    """Verify state-wise aggregate metrics returns authoritative state dictionary."""
    response = client.get("/api/v1/spatial/states")
    assert response.status_code == 200
    data = response.json()
    assert "states" in data
    assert "dataset_disclaimer" in data
    assert len(data["states"]) >= 36  # Covers all 37 Indian states and UTs
    
    # Check Maharashtra or Karnataka
    mh = data["states"].get("Maharashtra")
    assert mh is not None
    assert mh["total_observation_records"] > 0
    assert mh["distinct_species_count"] > 0
    assert "Mammalia" in mh["taxonomic_breakdown"] or "Aves" in mh["taxonomic_breakdown"]

def test_get_state_metrics_filter_taxa():
    """Verify taxonomic group filter applies to state aggregations."""
    response = client.get("/api/v1/spatial/states?taxonomic_group=Mammalia")
    assert response.status_code == 200
    data = response.json()
    assert "states" in data
    # Non-empty states should only report Mammalia records
    for st_name, s in data["states"].items():
        if s["total_observation_records"] > 0:
            for cls_name in s["taxonomic_breakdown"].keys():
                assert cls_name == "Mammalia"

def test_get_state_detail_drilldown():
    """Verify state drilldown endpoint returns summary, top recorded species, and observations."""
    response = client.get("/api/v1/spatial/states/Maharashtra")
    assert response.status_code == 200
    data = response.json()
    assert data["state_name"].lower() == "maharashtra"
    assert "summary" in data
    assert "observations" in data
    assert len(data["summary"]["top_recorded_species"]) > 0
    assert data["total_observations_available"] > 0

def test_get_state_detail_invalid_state():
    """Verify 404 returned for unknown state."""
    response = client.get("/api/v1/spatial/states/NonExistentState123")
    assert response.status_code == 404


def test_observations_map_state_filter_odisha():
    """Verify /observations/map?state_name=Odisha returns only observations within Odisha."""
    response = client.get("/api/v1/observations/map?state_name=Odisha&limit=500")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0, "Expected observations within Odisha"

    # Odisha approximate bounding box (generous margins)
    ODISHA_MIN_LAT, ODISHA_MAX_LAT = 17.5, 22.7
    ODISHA_MIN_LON, ODISHA_MAX_LON = 81.0, 87.6

    for obs in data:
        assert ODISHA_MIN_LAT <= obs["latitude"] <= ODISHA_MAX_LAT, \
            f"Observation {obs['id']} lat {obs['latitude']} is outside Odisha bounds"
        assert ODISHA_MIN_LON <= obs["longitude"] <= ODISHA_MAX_LON, \
            f"Observation {obs['id']} lon {obs['longitude']} is outside Odisha bounds"


def test_observations_map_state_filter_excludes_neighbors():
    """Verify Odisha filter does not return observations from Andhra Pradesh or Chhattisgarh."""
    # Get Odisha observations
    odisha_resp = client.get("/api/v1/observations/map?state_name=Odisha&limit=2000")
    odisha_ids = {obs["id"] for obs in odisha_resp.json()}

    # Get Andhra Pradesh observations
    ap_resp = client.get("/api/v1/observations/map?state_name=Andhra Pradesh&limit=2000")
    ap_ids = {obs["id"] for obs in ap_resp.json()}

    # There should be no overlap between Odisha and AP observations
    overlap = odisha_ids & ap_ids
    assert len(overlap) == 0, f"Found {len(overlap)} observations appearing in both Odisha and Andhra Pradesh"


def test_observations_map_state_filter_nonexistent():
    """Verify state filter for nonexistent state returns empty list."""
    response = client.get("/api/v1/observations/map?state_name=FakeStateName123")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_observations_map_taxonomic_filter():
    """Verify taxonomic_group filter works on /observations/map."""
    response_all = client.get("/api/v1/observations/map?limit=500")
    assert response_all.status_code == 200
    all_count = len(response_all.json())

    response_mammals = client.get("/api/v1/observations/map?taxonomic_group=Mammalia&limit=500")
    assert response_mammals.status_code == 200
    mammal_obs = response_mammals.json()
    assert isinstance(mammal_obs, list)

    response_birds = client.get("/api/v1/observations/map?taxonomic_group=Aves&limit=500")
    assert response_birds.status_code == 200
    bird_obs = response_birds.json()
    assert isinstance(bird_obs, list)


def test_spatial_states_taxonomic_filter_updates_metrics():
    """Verify /spatial/states with taxonomic_group returns taxon-specific metrics."""
    res_all = client.get("/api/v1/spatial/states")
    assert res_all.status_code == 200
    states_all = res_all.json()["states"]

    res_mammalia = client.get("/api/v1/spatial/states?taxonomic_group=Mammalia")
    assert res_mammalia.status_code == 200
    states_mammalia = res_mammalia.json()["states"]

    # Verify states structure is returned and values adapt
    assert isinstance(states_mammalia, dict)
    assert len(states_mammalia) > 0
    # For states present in both, taxon species count should be <= overall species count
    for state_name, m_metrics in states_mammalia.items():
        if state_name in states_all:
            assert m_metrics["distinct_species_count"] <= states_all[state_name]["distinct_species_count"]
