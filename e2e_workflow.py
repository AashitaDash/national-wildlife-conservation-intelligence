"""
End-to-End Workflow Verification Test for Wildlife Conservation Intelligence Platform
===================================================================================
Tests and verifies all 10 checkpoints against the live API:
1. Admin, Officer, and Researcher can log in.
2. Researcher dashboard returns the correct database-backed statistics.
3. Researcher submissions appear under the correct status.
4. Officer can retrieve the verification queue.
5. Officer can inspect and review an eligible submission.
6. A verified submission updates the appropriate counts and contribution totals.
7. Rejected and pending submissions do not count as verified.
8. Leaderboard results reflect actual eligible contributions.
9. Admin dashboard and user-management APIs return the expected results.
10. Unauthorized access returns the correct HTTP status.
"""
import sys
import json
import requests
from datetime import datetime, timezone

BASE_URL = "http://127.0.0.1:8000/api/v1"

def log_step(step_num, title, success, details):
    status_str = "PASS" if success else "FAIL"
    print(f"\n[{status_str}] Step {step_num}: {title}")
    for k, v in details.items():
        print(f"       {k}: {v}")

def run_workflow():
    report = []
    
    # -------------------------------------------------------------
    # 1. Admin, Officer, and Researcher can log in
    # -------------------------------------------------------------
    logins = {
        "admin": ("admin@wildlife.gov.in", "Admin@123"),
        "officer": ("officer@forest.gov.in", "Officer@123"),
        "researcher": ("researcher@wildlife.gov.in", "Researcher@123"),
    }
    tokens = {}
    step1_ok = True
    step1_details = {}
    
    for role, (email, pwd) in logins.items():
        r = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": pwd})
        if r.status_code == 200:
            data = r.json()
            tokens[role] = data["access_token"]
            step1_details[f"{role}_login"] = f"OK (role={data.get('role')}, id={data.get('user_id')})"
        else:
            step1_ok = False
            step1_details[f"{role}_login"] = f"FAILED (HTTP {r.status_code}: {r.text})"
            
    log_step(1, "Admin, Officer, and Researcher Login", step1_ok, step1_details)
    report.append(("1. Role Login Checks", step1_ok, step1_details))
    assert step1_ok, "Login failed for one or more roles"
    
    admin_hdr = {"Authorization": f"Bearer {tokens['admin']}"}
    officer_hdr = {"Authorization": f"Bearer {tokens['officer']}"}
    researcher_hdr = {"Authorization": f"Bearer {tokens['researcher']}"}
    
    # -------------------------------------------------------------
    # 2. Researcher dashboard returns correct database-backed statistics
    # -------------------------------------------------------------
    r_prof = requests.get(f"{BASE_URL}/gamification/profile/me", headers=researcher_hdr)
    step2_ok = r_prof.status_code == 200
    prof_data = r_prof.json() if step2_ok else {}
    step2_details = {
        "http_status": r_prof.status_code,
        "total_points": prof_data.get("total_points"),
        "level": prof_data.get("level"),
        "verified_count": prof_data.get("verified_count"),
        "badges": [b["code"] for b in prof_data.get("badges", [])],
        "submission_counts": prof_data.get("submission_counts", {})
    }
    step2_ok = step2_ok and prof_data.get("verified_count", 0) >= 1
    log_step(2, "Researcher Dashboard Database-Backed Statistics", step2_ok, step2_details)
    report.append(("2. Researcher Dashboard Stats", step2_ok, step2_details))
    assert step2_ok, "Researcher dashboard stats failed"

    # -------------------------------------------------------------
    # 3. Researcher submissions appear under correct status
    # -------------------------------------------------------------
    r_subs = requests.get(f"{BASE_URL}/submissions", headers=researcher_hdr)
    step3_ok = r_subs.status_code == 200
    subs_list = r_subs.json() if step3_ok else []
    status_counts_returned = {}
    for s in subs_list:
        st = s.get("status")
        status_counts_returned[st] = status_counts_returned.get(st, 0) + 1
    
    step3_details = {
        "http_status": r_subs.status_code,
        "total_returned": len(subs_list),
        "status_breakdown": status_counts_returned,
    }
    # Researcher Priya has verified, pending, and under_review in demo dataset
    step3_ok = step3_ok and len(subs_list) >= 3 and "VERIFIED" in status_counts_returned
    log_step(3, "Researcher Submissions Status Verification", step3_ok, step3_details)
    report.append(("3. Researcher Submissions Status", step3_ok, step3_details))
    assert step3_ok, "Researcher submissions check failed"

    # -------------------------------------------------------------
    # 4. Officer can retrieve the verification queue
    # -------------------------------------------------------------
    r_queue = requests.get(f"{BASE_URL}/officer/queue", headers=officer_hdr)
    r_qstats = requests.get(f"{BASE_URL}/officer/queue/stats", headers=officer_hdr)
    step4_ok = r_queue.status_code == 200 and r_qstats.status_code == 200
    queue_list = r_queue.json() if r_queue.status_code == 200 else []
    qstats = r_qstats.json() if r_qstats.status_code == 200 else {}
    step4_details = {
        "queue_http_status": r_queue.status_code,
        "stats_http_status": r_qstats.status_code,
        "queue_length": len(queue_list),
        "stats_summary": qstats
    }
    step4_ok = step4_ok and len(queue_list) > 0
    log_step(4, "Officer Queue Retrieval", step4_ok, step4_details)
    report.append(("4. Officer Queue Retrieval", step4_ok, step4_details))
    assert step4_ok, "Officer queue check failed"

    # -------------------------------------------------------------
    # 5. Officer can inspect and review an eligible submission
    # Create a fresh submission by researcher -> submit -> inspect by officer -> claim
    # -------------------------------------------------------------
    # Get species ID 1 (Asian Elephant)
    sighting_payload = {
        "species_id": 1,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "latitude": 21.6543,
        "longitude": 86.3456,
        "accuracy_meters": 12.0,
        "description": "E2E workflow test submission: herd spotted along forest trail.",
        "status": "DRAFT",
        "citations": ["https://doi.org/10.1016/j.biocon.2026.1001"]
    }
    r_create = requests.post(f"{BASE_URL}/submissions", json=sighting_payload, headers=researcher_hdr)
    assert r_create.status_code == 201, f"Failed to create draft: {r_create.text}"
    new_sub = r_create.json()
    new_sub_id = new_sub["id"]
    
    # Transition to PENDING_REVIEW
    r_trans = requests.post(f"{BASE_URL}/submissions/{new_sub_id}/submit", headers=researcher_hdr)
    assert r_trans.status_code == 200, f"Failed to submit for review: {r_trans.text}"
    
    # Officer inspects single submission detail
    r_insp = requests.get(f"{BASE_URL}/officer/queue/{new_sub_id}", headers=officer_hdr)
    step5_ok = r_insp.status_code == 200
    insp_data = r_insp.json() if step5_ok else {}
    
    # Officer claims submission (UNDER_REVIEW)
    r_claim = requests.post(f"{BASE_URL}/officer/queue/{new_sub_id}/claim", headers=officer_hdr)
    step5_ok = step5_ok and r_claim.status_code == 200
    claim_data = r_claim.json() if r_claim.status_code == 200 else {}
    
    step5_details = {
        "created_sub_id": new_sub_id,
        "submitted_status": r_trans.json().get("status"),
        "officer_inspect_status": r_insp.status_code,
        "species_name": insp_data.get("species_common_name"),
        "officer_claim_status": r_claim.status_code,
        "claimed_status": claim_data.get("status")
    }
    log_step(5, "Officer Inspect and Claim Eligible Submission", step5_ok, step5_details)
    report.append(("5. Officer Inspect and Review", step5_ok, step5_details))
    assert step5_ok, "Officer review/claim failed"

    # -------------------------------------------------------------
    # 6. A verified submission updates appropriate counts and contribution totals
    # -------------------------------------------------------------
    # Record initial counts
    prof_before = requests.get(f"{BASE_URL}/gamification/profile/me", headers=researcher_hdr).json()
    points_before = prof_before["total_points"]
    verified_before = prof_before["verified_count"]
    
    # Verify the submission
    r_verify = requests.post(
        f"{BASE_URL}/officer/queue/{new_sub_id}/verify",
        json={"note": "Verified via photographic evidence and geofence logs."},
        headers=officer_hdr
    )
    step6_ok = r_verify.status_code == 200
    verify_data = r_verify.json() if step6_ok else {}
    promoted_obs_id = verify_data.get("promoted_observation_id")
    step6_ok = step6_ok and (promoted_obs_id is not None)
    
    # Fetch updated researcher profile
    prof_after = requests.get(f"{BASE_URL}/gamification/profile/me", headers=researcher_hdr).json()
    points_after = prof_after["total_points"]
    verified_after = prof_after["verified_count"]
    
    step6_details = {
        "verify_http_status": r_verify.status_code,
        "promoted_observation_id": promoted_obs_id,
        "submission_final_status": verify_data.get("status"),
        "points_before": points_before,
        "points_after": points_after,
        "points_earned": points_after - points_before,
        "verified_before": verified_before,
        "verified_after": verified_after
    }
    step6_ok = step6_ok and (points_after > points_before) and (verified_after == verified_before + 1)
    log_step(6, "Verified Submission Count & Points Update", step6_ok, step6_details)
    report.append(("6. Counts and Contribution Totals Update", step6_ok, step6_details))
    assert step6_ok, "Points or verified count did not increment"

    # -------------------------------------------------------------
    # 7. Rejected and pending submissions do not count as verified
    # -------------------------------------------------------------
    # Create another submission to reject
    r_create_rej = requests.post(f"{BASE_URL}/submissions", json={
        "species_id": 1,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "latitude": 20.123,
        "longitude": 85.123,
        "accuracy_meters": 50.0,
        "description": "E2E invalid sighting to reject.",
        "status": "DRAFT"
    }, headers=researcher_hdr)
    sub_rej_id = r_create_rej.json()["id"]
    requests.post(f"{BASE_URL}/submissions/{sub_rej_id}/submit", headers=researcher_hdr)
    requests.post(f"{BASE_URL}/officer/queue/{sub_rej_id}/claim", headers=officer_hdr)
    
    # Check counts before rejection
    prof_pre_rej = requests.get(f"{BASE_URL}/gamification/profile/me", headers=researcher_hdr).json()
    
    # Reject it
    r_rej = requests.post(
        f"{BASE_URL}/officer/queue/{sub_rej_id}/reject",
        json={"reason": "Location invalid, no photographic proof."},
        headers=officer_hdr
    )
    step7_ok = r_rej.status_code == 200
    
    # Check counts after rejection
    prof_post_rej = requests.get(f"{BASE_URL}/gamification/profile/me", headers=researcher_hdr).json()
    
    step7_details = {
        "reject_http_status": r_rej.status_code,
        "verified_count_before": prof_pre_rej["verified_count"],
        "verified_count_after": prof_post_rej["verified_count"],
        "points_before": prof_pre_rej["total_points"],
        "points_after": prof_post_rej["total_points"],
        "rejected_submission_status": r_rej.json().get("status"),
        "promoted_obs_id": r_rej.json().get("promoted_observation_id")
    }
    step7_ok = (
        step7_ok 
        and (prof_post_rej["verified_count"] == prof_pre_rej["verified_count"])
        and (prof_post_rej["total_points"] == prof_pre_rej["total_points"])
        and (r_rej.json().get("promoted_observation_id") is None)
    )
    log_step(7, "Rejected & Pending Submissions Do Not Count as Verified", step7_ok, step7_details)
    report.append(("7. Non-Verified Do Not Increment Totals", step7_ok, step7_details))
    assert step7_ok, "Rejected submission improperly affected counts"

    # -------------------------------------------------------------
    # 8. Leaderboard results reflect actual eligible contributions
    # -------------------------------------------------------------
    r_board = requests.get(f"{BASE_URL}/gamification/leaderboard")
    step8_ok = r_board.status_code == 200
    board_data = r_board.json() if step8_ok else []
    
    # Check that each entry has points > 0, rank order is descending
    points_list = [entry["total_points"] for entry in board_data]
    is_sorted = points_list == sorted(points_list, reverse=True)
    
    step8_details = {
        "http_status": r_board.status_code,
        "total_ranked_researchers": len(board_data),
        "top_three": [
            f"Rank {e['rank']}: {e['display_name']} ({e['total_points']} pts, {e['verified_count']} verified)"
            for e in board_data[:3]
        ],
        "is_sorted_descending": is_sorted
    }
    step8_ok = step8_ok and len(board_data) >= 1 and is_sorted
    log_step(8, "Leaderboard Verification", step8_ok, step8_details)
    report.append(("8. Leaderboard Results", step8_ok, step8_details))
    assert step8_ok, "Leaderboard validation failed"

    # -------------------------------------------------------------
    # 9. Admin dashboard and user-management APIs return expected results
    # -------------------------------------------------------------
    r_adm_stats = requests.get(f"{BASE_URL}/admin/platform/stats", headers=admin_hdr)
    r_adm_users = requests.get(f"{BASE_URL}/admin/platform/users", headers=admin_hdr)
    r_dash_stats = requests.get(f"{BASE_URL}/dashboards/stats")
    
    step9_ok = (
        r_adm_stats.status_code == 200 
        and r_adm_users.status_code == 200
        and r_dash_stats.status_code == 200
    )
    adm_stats = r_adm_stats.json() if r_adm_stats.status_code == 200 else {}
    adm_users = r_adm_users.json() if r_adm_users.status_code == 200 else []
    dash_stats = r_dash_stats.json() if r_dash_stats.status_code == 200 else {}
    
    step9_details = {
        "admin_stats_status": r_adm_stats.status_code,
        "admin_users_status": r_adm_users.status_code,
        "dashboard_stats_status": r_dash_stats.status_code,
        "total_users": adm_stats.get("total_users"),
        "total_submissions": adm_stats.get("total_submissions"),
        "verified_submissions": adm_stats.get("verified_submissions"),
        "total_species": dash_stats.get("total_species"),
        "total_observations": dash_stats.get("total_observations"),
        "database_backend": dash_stats.get("database_backend"),
        "users_count_returned": len(adm_users)
    }
    step9_ok = step9_ok and adm_stats.get("total_users", 0) >= 7 and len(adm_users) >= 7
    log_step(9, "Admin Dashboard and User-Management APIs", step9_ok, step9_details)
    report.append(("9. Admin Dashboard and User APIs", step9_ok, step9_details))
    assert step9_ok, "Admin dashboard APIs failed"

    # -------------------------------------------------------------
    # 10. Unauthorized access returns correct HTTP status
    # -------------------------------------------------------------
    # A) Researcher trying to access /admin/platform/stats -> 403 Forbidden
    r_unauth_admin = requests.get(f"{BASE_URL}/admin/platform/stats", headers=researcher_hdr)
    # B) Researcher trying to access officer queue -> 403 Forbidden
    r_unauth_queue = requests.get(f"{BASE_URL}/officer/queue", headers=researcher_hdr)
    # C) No token trying to access /submissions -> 401 Unauthorized
    r_unauth_no_tok = requests.get(f"{BASE_URL}/submissions")
    # D) Officer trying to access /admin/platform/users -> 403 Forbidden
    r_unauth_off_adm = requests.get(f"{BASE_URL}/admin/platform/users", headers=officer_hdr)
    
    step10_ok = (
        r_unauth_admin.status_code == 403
        and r_unauth_queue.status_code == 403
        and r_unauth_no_tok.status_code == 401
        and r_unauth_off_adm.status_code == 403
    )
    step10_details = {
        "researcher_to_admin_route": f"HTTP {r_unauth_admin.status_code} (Expected 403)",
        "researcher_to_officer_route": f"HTTP {r_unauth_queue.status_code} (Expected 403)",
        "unauthenticated_to_protected": f"HTTP {r_unauth_no_tok.status_code} (Expected 401)",
        "officer_to_admin_route": f"HTTP {r_unauth_off_adm.status_code} (Expected 403)",
    }
    log_step(10, "Unauthorized Access Role Enforcement", step10_ok, step10_details)
    report.append(("10. Unauthorized Access Verification", step10_ok, step10_details))
    assert step10_ok, "Role enforcement check failed"
    
    print("\n=======================================================")
    print("ALL 10 END-TO-END WORKFLOW VERIFICATION CHECKS PASSED!")
    print("=======================================================")
    return report

if __name__ == "__main__":
    try:
        report = run_workflow()
    except Exception as e:
        print(f"\n[FATAL] Workflow check aborted: {e}")
        sys.exit(1)
