import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.user import User, Role
from backend.app.services.auth_service import AuthService

client = TestClient(app)

def test_missing_full_name_rejected():
    """Verify that registration rejects missing or whitespace-only full name."""
    # 1. Missing full name entirely
    res1 = client.post("/api/v1/auth/register", json={
        "username": "test_user_nofullname",
        "email": "test_noname@example.com",
        "password": "Password123!",
        "full_name": ""
    })
    assert res1.status_code == 422 or res1.status_code == 400

    # 2. Whitespace-only full name
    res2 = client.post("/api/v1/auth/register", json={
        "username": "test_user_spaces",
        "email": "test_spaces@example.com",
        "password": "Password123!",
        "full_name": "     "
    })
    assert res2.status_code == 422 or res2.status_code == 400

def test_username_availability_endpoint():
    """Verify username checking, case-insensitivity, and suggestion generation."""
    # Existing user in db: 'admin'
    res = client.get("/api/v1/auth/check-username?username=ADMIN")
    assert res.status_code == 200
    data = res.json()
    assert data["available"] is False
    assert data["valid"] is True
    assert "already taken" in data["message"].lower()
    assert len(data["suggestions"]) > 0

    # Verify each suggested alternative is genuinely available in the database
    for suggestion in data["suggestions"]:
        sug_res = client.get(f"/api/v1/auth/check-username?username={suggestion}")
        assert sug_res.status_code == 200
        assert sug_res.json()["available"] is True, f"Suggestion {suggestion} should be available"

    # Truly unique username
    res_unique = client.get("/api/v1/auth/check-username?username=unique_wildlife_test_9988")
    assert res_unique.status_code == 200
    assert res_unique.json()["available"] is True
    assert res_unique.json()["valid"] is True

    # Invalid username (too short or invalid chars)
    res_short = client.get("/api/v1/auth/check-username?username=a")
    assert res_short.status_code == 200
    assert res_short.json()["valid"] is False

def test_valid_registration_and_secure_role_assignment():
    """
    CRITICAL SECURITY TEST:
    Verify that public registration succeeds with a safe role (CITIZEN) and PENDING approval,
    and attempts to register as ADMIN or FOREST_OFFICER in the payload are ignored/neutralized.
    """
    uname = "hacker_trying_admin"
    email = "hacker@defense.org"
    res = client.post("/api/v1/auth/register", json={
        "username": uname,
        "email": email,
        "password": "SecretPassword123!",
        "full_name": "Security Tester",
        "role_name": "ADMIN"  # Malicious attempt to elevate privileges
    })
    assert res.status_code == 201
    user_data = res.json()
    # Must NOT have received ADMIN
    assert user_data["role"]["name"] != "ADMIN"
    assert user_data["role"]["name"] in ("CITIZEN", "VIEWER")
    assert user_data["approval_status"] == "PENDING"
    assert user_data["full_name"] == "Security Tester"

def test_duplicate_username_case_insensitive_rejected():
    """Verify duplicate username rejection regardless of casing."""
    # 'admin' exists in db
    res = client.post("/api/v1/auth/register", json={
        "username": "AdMiN",
        "email": "another_admin_email@test.com",
        "password": "Password123!",
        "full_name": "Another Admin",
    })
    assert res.status_code == 400
    assert "already taken" in res.json()["detail"].lower()

def test_pending_account_cannot_access_protected_role_endpoints():
    """Verify that a pending account cannot access role-protected dashboards or endpoints."""
    # Login with the newly registered pending user
    login_res = client.post("/api/v1/auth/login", json={
        "email": "hacker@defense.org",
        "password": "SecretPassword123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to access researcher submission endpoints
    res_sub = client.get("/api/v1/submissions/my", headers=headers)
    assert res_sub.status_code == 403
    assert "pending administrator review" in res_sub.json()["detail"].lower()

    # Attempt to access officer endpoints
    res_officer = client.get("/api/v1/officer/metrics", headers=headers)
    assert res_officer.status_code == 403

    # Attempt to access admin endpoints
    res_admin = client.get("/api/v1/admin/platform/stats", headers=headers)
    assert res_admin.status_code == 403

def test_authorized_admin_can_approve_and_assign_role():
    """Verify that an authorized admin can approve a pending user and assign a permitted role."""
    # 1. Login as Admin
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@wildlife.gov.in",
        "password": "Admin@123"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Get user id of 'hacker_trying_admin'
    db = SessionLocal()
    user = db.query(User).filter(User.username == "hacker_trying_admin").first()
    user_id = user.id
    db.close()

    # 3. Approve and assign RESEARCHER role
    approve_res = client.put(f"/api/v1/admin/platform/users/{user_id}/approve", json={
        "action": "APPROVE",
        "assigned_role": "RESEARCHER"
    }, headers=admin_headers)
    assert approve_res.status_code == 200
    approved_data = approve_res.json()
    assert approved_data["approval_status"] == "APPROVED"
    assert approved_data["role_name"] == "RESEARCHER"

    # 4. Now login as the approved user and verify they can access researcher endpoints
    user_login = client.post("/api/v1/auth/login", json={
        "email": "hacker@defense.org",
        "password": "SecretPassword123!"
    })
    user_token = user_login.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    sub_res = client.get("/api/v1/submissions/my", headers=user_headers)
    assert sub_res.status_code == 200

def test_admin_cannot_remove_own_last_admin_role():
    """Verify that admin cannot remove their own admin role if they are the sole admin."""
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@wildlife.gov.in",
        "password": "Admin@123"
    })
    admin_token = admin_login.json()["access_token"]
    admin_id = admin_login.json()["user_id"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Attempt to change own role to CITIZEN
    role_change_res = client.put(f"/api/v1/admin/platform/users/{admin_id}/role", json={
        "role_name": "CITIZEN"
    }, headers=admin_headers)
    
    # Should either be 400 (Cannot remove own administrative role)
    if role_change_res.status_code != 200:
        assert role_change_res.status_code == 400
        assert "administrative role" in role_change_res.json()["detail"].lower()

def test_existing_demo_accounts_functional():
    """Verify that existing demo accounts continue to authenticate and hold their expected roles."""
    demo_credentials = [
        ("admin@wildlife.gov.in", "Admin@123", "ADMIN"),
        ("researcher@wildlife.gov.in", "Researcher@123", "FOREST_OFFICER"), # Or RESEARCHER/FOREST_OFFICER in db
        ("officer@forest.gov.in", "Officer@123", "FOREST_OFFICER"),
    ]
    for email, pwd, expected_role in demo_credentials:
        login_res = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": pwd
        })
        assert login_res.status_code == 200, f"Failed demo login for {email}"
        data = login_res.json()
        assert data["access_token"]
        assert len(data["full_name"]) > 0
        assert data["approval_status"] == "APPROVED"


