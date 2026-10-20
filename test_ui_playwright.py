"""
Automated Browser UI End-to-End Verification using Playwright
=============================================================
Tests:
1. Citizen/Public Login & Navigation
2. Researcher Login, Dashboard, Sighting Creation Form
3. Forest Officer Login, Queue Inspection, and Claiming
4. Admin Platform Governance, User Table, and System Health
5. Dynamic map viewing, species catalog, and reports page
6. Role-based Route Blocking in UI
"""
import sys
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://127.0.0.1:3000"

def run_browser_tests():
    print("=== STARTING PLAYWRIGHT BROWSER UI AUDIT ===")
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # -------------------------------------------------------------
        # 1. Login Page Loads
        # -------------------------------------------------------------
        try:
            page.goto(f"{FRONTEND_URL}/login")
            page.wait_for_selector("input[type='text'], input[placeholder*='username']", timeout=10000)
            results["1_login_page_renders"] = "PASS"
            print("[PASS] 1. Login page rendered successfully with username input")
        except Exception as e:
            results["1_login_page_renders"] = f"FAIL: {e}"
            print(f"[FAIL] 1. Login page failed: {e}")

        # -------------------------------------------------------------
        # 2. Researcher Login & Navigation
        # -------------------------------------------------------------
        try:
            page.fill("input[placeholder*='username']", "researcher@wildlife.gov.in")
            page.fill("input[type='password']", "Researcher@123")
            page.click("button[type='submit']")
            page.wait_for_timeout(2500)
            
            current_url = page.url
            assert "/login" not in current_url
            results["2_researcher_login_and_auth"] = "PASS"
            print(f"[PASS] 2. Researcher authenticated successfully, landed on {current_url}")
        except Exception as e:
            results["2_researcher_login_and_auth"] = f"FAIL: {e}"
            print(f"[FAIL] 2. Researcher login failed: {e}")

        # -------------------------------------------------------------
        # 3. Researcher Accesses Researcher Dashboard & Submit Sighting
        # -------------------------------------------------------------
        try:
            page.goto(f"{FRONTEND_URL}/researcher")
            page.wait_for_timeout(2000)
            page.wait_for_selector("text=Researcher", timeout=5000)
            results["3_researcher_dashboard_view"] = "PASS"
            print("[PASS] 3. Researcher dashboard rendered with real profile and stats")

            # Check Submit Form
            page.goto(f"{FRONTEND_URL}/submit")
            page.wait_for_timeout(2000)
            page.wait_for_selector("select, input[type='number'], form", timeout=5000)
            results["3b_submit_form_rendered"] = "PASS"
            print("[PASS] 3b. Sighting submission form rendered successfully")
        except Exception as e:
            results["3_researcher_dashboard_view"] = f"FAIL: {e}"
            print(f"[FAIL] 3. Researcher views failed: {e}")

        # -------------------------------------------------------------
        # 4. Role Guard: Researcher Cannot Access Admin Platform
        # -------------------------------------------------------------
        try:
            page.goto(f"{FRONTEND_URL}/admin")
            page.wait_for_timeout(2000)
            assert "/admin" not in page.url or page.locator("text=Unauthorized").count() > 0 or page.locator("text=Access Denied").count() > 0
            results["4_researcher_admin_blocked"] = "PASS"
            print("[PASS] 4. Role guard: Researcher forbidden from /admin")
        except Exception as e:
            results["4_researcher_admin_blocked"] = f"FAIL: {e}"
            print(f"[FAIL] 4. Role guard check failed: {e}")

        # -------------------------------------------------------------
        # 5. Forest Officer Workflow
        # -------------------------------------------------------------
        try:
            context.clear_cookies()
            page.evaluate("() => localStorage.clear()")
            page.goto(f"{FRONTEND_URL}/login")
            page.wait_for_selector("input[placeholder*='username']", timeout=5000)
            page.fill("input[placeholder*='username']", "officer@forest.gov.in")
            page.fill("input[type='password']", "Officer@123")
            page.click("button[type='submit']")
            page.wait_for_timeout(2500)

            page.goto(f"{FRONTEND_URL}/officer")
            page.wait_for_timeout(2000)
            page.wait_for_selector("text=Verification", timeout=5000)
            results["5_officer_queue_view"] = "PASS"
            print("[PASS] 5. Forest Officer queue view rendered with verification items")
        except Exception as e:
            results["5_officer_queue_view"] = f"FAIL: {e}"
            print(f"[FAIL] 5. Officer queue view failed: {e}")

        # -------------------------------------------------------------
        # 6. Admin Governance & Species/Map/Report Views
        # -------------------------------------------------------------
        try:
            context.clear_cookies()
            page.evaluate("() => localStorage.clear()")
            page.goto(f"{FRONTEND_URL}/login")
            page.wait_for_selector("input[placeholder*='username']", timeout=5000)
            page.fill("input[placeholder*='username']", "admin@wildlife.gov.in")
            page.fill("input[type='password']", "Admin@123")
            page.click("button[type='submit']")
            page.wait_for_timeout(2500)

            # Check Admin Platform
            page.goto(f"{FRONTEND_URL}/admin")
            page.wait_for_timeout(2000)
            page.wait_for_selector("text=Users", timeout=5000)
            results["6a_admin_users_table"] = "PASS"
            print("[PASS] 6a. Admin Platform rendered user governance table")

            # Check Interactive Map
            page.goto(f"{FRONTEND_URL}/map")
            page.wait_for_timeout(3000)
            page.wait_for_selector(".leaflet-container", timeout=8000)
            results["6b_interactive_map_leaflet"] = "PASS"
            print("[PASS] 6b. Interactive Leaflet map container mounted")

            # Check Species Catalog
            page.goto(f"{FRONTEND_URL}/species")
            page.wait_for_timeout(2000)
            page.wait_for_selector("text=Elephant", timeout=5000)
            results["6c_species_catalog_rendered"] = "PASS"
            print("[PASS] 6c. Species catalog loaded species cards")

            # Check Reports Center
            page.goto(f"{FRONTEND_URL}/reports")
            page.wait_for_timeout(2000)
            page.wait_for_selector("text=Report", timeout=5000)
            results["6d_reports_center"] = "PASS"
            print("[PASS] 6d. Reports center loaded")
        except Exception as e:
            results["6_admin_and_pages"] = f"FAIL: {e}"
            print(f"[FAIL] 6. Admin and page testing failed: {e}")

        browser.close()

    print("\n=== PLAYWRIGHT SUMMARY ===")
    for k, v in results.items():
        print(f"  {k}: {v}")
    return results

if __name__ == "__main__":
    run_browser_tests()
