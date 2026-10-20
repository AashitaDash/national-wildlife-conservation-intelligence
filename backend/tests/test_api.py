"""
FastAPI REST API integration tests.
Tests endpoints across Auth, Species, Observations, Documents (NLP), Search, ML, and Dashboards.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_and_health():
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "OPERATIONAL"

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "HEALTHY"


def test_auth_login_and_me():
    # Login with seeded admin
    login_payload = {
        "email": "admin@wildlife.gov.in",
        "password": "Admin@123"
    }
    res = client.post("/api/v1/auth/login", json=login_payload)
    assert res.status_code == 200, f"Login failed: {res.text}"
    token_data = res.json()
    assert "access_token" in token_data
    assert token_data["role"] == "ADMIN"
    
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check /auth/me
    res_me = client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "admin@wildlife.gov.in"


def test_species_endpoints():
    res = client.get("/api/v1/species")
    assert res.status_code == 200
    species_list = res.json()["items"]
    assert len(species_list) > 0
    first_id = species_list[0]["id"]

    # Detail
    res_detail = client.get(f"/api/v1/species/{first_id}")
    assert res_detail.status_code == 200
    data = res_detail.json()
    assert "total_observations" in data
    assert "recent_risk_level" in data


def test_observations_endpoints():
    res = client.get("/api/v1/observations?limit=10")
    assert res.status_code == 200
    obs_list = res.json()
    assert len(obs_list) > 0
    assert "latitude" in obs_list[0]
    assert "longitude" in obs_list[0]


def test_document_ingestion_and_nlp_pipeline():
    # Submit text report mentioning tiger and poaching in Bandipur
    payload = {
        "title": "Incident Log: Tiger Monitoring in Bandipur",
        "source_type": "INCIDENT_LOG",
        "raw_text": "Rangers observed an adult Bengal Tiger near the southern border of Bandipur National Park. Evidence of illegal wire snares and poaching was recorded."
    }
    res = client.post("/api/v1/documents", json=payload)
    assert res.status_code == 201, f"Document submission failed: {res.text}"
    data = res.json()
    assert data["title"] == payload["title"]
    assert data["summary"] is not None
    # Check that Bengal Tiger was linked
    species_names = [s["common_name"] for s in data["species_mentions"]]
    assert any("Tiger" in name for name in species_names)


def test_hybrid_search_endpoint():
    res = client.get("/api/v1/search?q=tiger&alpha=0.5")
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert len(data["results"]) > 0


def test_ml_risk_assessment_endpoint():
    # Species ID 1: Bengal Tiger or Asian Elephant
    payload = {
        "species_id": 1,
        "override_features": {
            "threat_mention_count_30d": 5.0,
            "hwc_incident_ratio": 0.4
        }
    }
    res = client.post("/api/v1/ml/assess-risk", json=payload)
    assert res.status_code == 200, f"ML assessment failed: {res.text}"
    data = res.json()
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert 0 <= data["composite_score"] <= 100
    assert "diagnostic_reason" in data


def test_dashboard_stats_endpoint():
    res = client.get("/api/v1/dashboards/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_species"] >= 10
    assert stats["total_observations"] >= 20
    assert stats["total_documents"] >= 4
