"""
End-to-End Tests for Role-Based Wildlife Management:
1. Researcher creates field observation submission
2. Submits for peer review (state transition DRAFT -> PENDING_REVIEW)
3. Forest Officer inspects and claims (PENDING_REVIEW -> UNDER_REVIEW)
4. Forest Officer verifies submission, promoting it into official observations
5. Researcher profile awarded points & badge
6. System Admin inspects platform stats and user accounts
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.user import User, Role
from backend.app.models.species import Species
from backend.app.services.auth_service import AuthService

client = TestClient(app)


@pytest.fixture
def test_setup():
    db = SessionLocal()
    try:
        # 1. Ensure required roles exist
        for r_name in ["ADMIN", "FOREST_OFFICER", "RESEARCHER", "VIEWER"]:
            role = db.query(Role).filter(Role.name == r_name).first()
            if not role:
                role = Role(name=r_name, description=f"{r_name} role")
                db.add(role)
        db.commit()

        # 2. Get or create test Researcher
        researcher = db.query(User).filter(User.email == "researcher_test@wildlife.gov.in").first()
        res_role = db.query(Role).filter(Role.name == "RESEARCHER").first()
        if not researcher:
            researcher = User(
                email="researcher_test@wildlife.gov.in",
                hashed_password=AuthService.hash_password("Pass123!"),
                full_name="Dr. Salim Researcher",
                role_id=res_role.id,
                is_active=True,
                is_suspended=False
            )
            db.add(researcher)
        else:
            researcher.role_id = res_role.id
            researcher.is_suspended = False
        db.commit()

        # 3. Get or create test Officer
        officer = db.query(User).filter(User.email == "officer_test@wildlife.gov.in").first()
        off_role = db.query(Role).filter(Role.name == "FOREST_OFFICER").first()
        if not officer:
            officer = User(
                email="officer_test@wildlife.gov.in",
                hashed_password=AuthService.hash_password("Pass123!"),
                full_name="Ranger Sharma",
                role_id=off_role.id,
                is_active=True,
                is_suspended=False
            )
            db.add(officer)
        else:
            officer.role_id = off_role.id
            officer.is_suspended = False
        db.commit()

        # 4. Get a valid species
        species = db.query(Species).first()

        # Generate tokens
        res_token = AuthService.create_access_token({"sub": researcher.email, "role": "RESEARCHER", "user_id": researcher.id})
        off_token = AuthService.create_access_token({"sub": officer.email, "role": "FOREST_OFFICER", "user_id": officer.id})

        return {
            "researcher_token": res_token,
            "officer_token": off_token,
            "species_id": species.id,
            "researcher_id": researcher.id,
            "officer_id": officer.id,
        }
    finally:
        db.close()


def test_rbac_sighting_and_verification_workflow(test_setup):
    res_headers = {"Authorization": f"Bearer {test_setup['researcher_token']}"}
    off_headers = {"Authorization": f"Bearer {test_setup['officer_token']}"}

    # Step 1: Researcher creates a draft sighting
    create_payload = {
        "species_id": test_setup["species_id"],
        "observed_at": "2026-05-10T08:30:00Z",
        "latitude": 21.654,
        "longitude": 88.123,
        "accuracy_meters": 10.0,
        "description": "Adult individual basking along tidal creek.",
        "status": "DRAFT",
    }
    res = client.post("/api/v1/submissions", json=create_payload, headers=res_headers)
    assert res.status_code == 201, res.text
    sub_data = res.json()
    sub_id = sub_data["id"]
    assert sub_data["status"] == "DRAFT"

    # Step 2: Researcher transitions to PENDING_REVIEW
    res_submit = client.post(f"/api/v1/submissions/{sub_id}/submit", headers=res_headers)
    assert res_submit.status_code == 200
    assert res_submit.json()["status"] == "PENDING_REVIEW"

    # Step 3: Forest Officer views queue and claims submission
    queue_res = client.get("/api/v1/officer/queue?status=PENDING_REVIEW", headers=off_headers)
    assert queue_res.status_code == 200
    queue_ids = [item["id"] for item in queue_res.json()]
    assert sub_id in queue_ids

    claim_res = client.post(f"/api/v1/officer/queue/{sub_id}/claim", headers=off_headers)
    assert claim_res.status_code == 200
    assert claim_res.json()["status"] == "UNDER_REVIEW"

    # Step 4: Forest Officer verifies submission
    verify_res = client.post(
        f"/api/v1/officer/queue/{sub_id}/verify",
        json={"note": "Photographic and spatiotemporal evidence verified for inclusion in registry."},
        headers=off_headers,
    )
    assert verify_res.status_code == 200
    sub_verified = verify_res.json()
    assert sub_verified["status"] == "VERIFIED"
    assert sub_verified["promoted_observation_id"] is not None

    # Step 5: Researcher checks profile gamification points
    profile_res = client.get("/api/v1/gamification/profile/me", headers=res_headers)
    assert profile_res.status_code == 200
    profile_data = profile_res.json()
    assert profile_data["total_points"] >= 50
    assert profile_data["verified_count"] >= 1


def test_demo_accounts_authentication():
    """Verify all 3 documented demo roles authenticate successfully."""
    for email, pwd, expected_role in [
        ("admin@wildlife.gov.in", "Admin@123", "ADMIN"),
        ("officer@forest.gov.in", "Officer@123", "FOREST_OFFICER"),
        ("researcher@wildlife.com", "Researcher@123", "RESEARCHER"),
    ]:
        res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        assert res.status_code == 200, f"Login failed for {email}: {res.text}"
        data = res.json()
        assert "access_token" in data
        assert data.get("role") == expected_role


def test_rbac_security_boundaries_and_forbidden_access(test_setup):
    """Enforce strict 401 Unauthorized and 403 Forbidden across roles."""
    res_headers = {"Authorization": f"Bearer {test_setup['researcher_token']}"}
    off_headers = {"Authorization": f"Bearer {test_setup['officer_token']}"}

    # 1. Unauthenticated requests must receive 401
    assert client.get("/api/v1/officer/queue").status_code == 401
    assert client.get("/api/v1/admin/platform/stats").status_code == 401
    assert client.get("/api/v1/submissions/mine").status_code == 401

    # 2. Researcher cannot access Forest Officer queue (403)
    assert client.get("/api/v1/officer/queue", headers=res_headers).status_code == 403

    # 3. Researcher cannot access Admin endpoints (403)
    assert client.get("/api/v1/admin/platform/stats", headers=res_headers).status_code == 403
    assert client.get("/api/v1/admin/platform/users", headers=res_headers).status_code == 403

    # 4. Officer cannot access Admin endpoints (403)
    assert client.get("/api/v1/admin/platform/stats", headers=off_headers).status_code == 403


def test_invalid_submission_transitions_and_payloads(test_setup):
    """Verify validation on bad payloads and illegal state transitions."""
    res_headers = {"Authorization": f"Bearer {test_setup['researcher_token']}"}

    # Invalid species ID
    bad_payload = {
        "species_id": 999999,
        "observed_at": "2026-05-10T08:30:00Z",
        "latitude": 21.654,
        "longitude": 88.123,
        "description": "Invalid species test"
    }
    assert client.post("/api/v1/submissions", json=bad_payload, headers=res_headers).status_code == 400

    # Nonexistent submission submit transition
    assert client.post("/api/v1/submissions/999999/submit", headers=res_headers).status_code == 404

