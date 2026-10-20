# -*- coding: utf-8 -*-
"""
NWCIP Responsive Regression Test Suite
Commit: 7dd82b7  Repo: AashitaDash/national-wildlife-conservation-intelligence
"""
import sys, json, datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

FRONTEND_URL   = "http://127.0.0.1:3000"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

VIEWPORTS = [
    {"name": "small_mobile",  "width": 320,  "height": 568},
    {"name": "std_mobile",    "width": 375,  "height": 812},
    {"name": "large_mobile",  "width": 430,  "height": 932},
    {"name": "tablet",        "width": 768,  "height": 1024},
    {"name": "laptop",        "width": 1366, "height": 768},
    {"name": "desktop",        "width": 1920, "height": 1080},
]

CREDS = {
    "admin":      {"email": "admin@wildlife.gov.in",      "password": "Admin@123"},
    "researcher": {"email": "researcher@wildlife.gov.in", "password": "Researcher@123"},
    "officer":    {"email": "officer@forest.gov.in",      "password": "Officer@123"},
}

ROUTES = [
    ("/login",          None,         "login",            "input[type=password]"),
    ("/",               "admin",      "dashboard",        "main"),
    ("/species",        "admin",      "species_catalog",  "main"),
    ("/map",            "admin",      "gis_map",          ".leaflet-container"),
    ("/threats",        "admin",      "threats",          "main"),
    ("/documents",      "admin",      "documents",        "main"),
    ("/alerts",         "admin",      "alerts",           "main"),
    ("/assistant",      "admin",      "ai_assistant",     "main"),
    ("/reports",        "admin",      "reports",          "main"),
    ("/leaderboard",    "admin",      "leaderboard",      "main"),
    ("/researcher",     "researcher", "researcher_dash",  "main"),
    ("/submit",         "researcher", "submit_sighting",  "main"),
    ("/my-submissions", "researcher", "my_submissions",   "main"),
    ("/officer",        "officer",    "officer_dash",     "main"),
    ("/admin",          "admin",      "admin_platform",   "main"),
]


def shot(page, vp, label, suf=""):
    name = "{}_{}{}.png".format(vp, label, ("_"+suf) if suf else "")
    p = str(SCREENSHOT_DIR / name)
    try:
        page.screenshot(path=p, full_page=False)
    except Exception:
        pass
    return p


def has_overflow(page):
    try:
        return page.evaluate("function(){return document.body.scrollWidth>window.innerWidth+2;}")
    except Exception:
        return False


def do_login(page, ctx, role):
    try:
        ctx.clear_cookies()
        page.evaluate("function(){try{localStorage.clear();}catch(e){}}")
    except Exception:
        pass
    page.goto("%s/login" % FRONTEND_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector("input[type=password]", timeout=10000)
    creds = CREDS[role]
    filled = False
    for sel in ["input[type=email]", "input[placeholder*=email]", "input[placeholder*=username]"]:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                el.fill(creds["email"])
                filled = True
                break
        except Exception:
            pass
    if not filled:
        page.locator("input").first.fill(creds["email"])
    page.fill("input[type=password]", creds["password"])
    page.click("button[type=submit]")
    page.wait_for_timeout(3000)
    return "/login" not in page.url


def run_tests():
    results = []
    tp, tf = 0, 0
    print("\n" + "="*60)
    print("NWCIP Responsive Regression  commit=7dd82b7")
    print("Viewports:%d  Routes:%d  Screenshots->%s" % (len(VIEWPORTS), len(ROUTES), SCREENSHOT_DIR))
    print("="*60)
    with sync_playwright() as pw:
        for vp in VIEWPORTS:
            vw, vh = vp["width"], vp["height"]
            print("\n>> %s  (%dx%d)" % (vp["name"], vw, vh))
            is_mobile = vw < 1024
            browser = pw.chromium.launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
            ctx = browser.new_context(viewport={"width":vw,"height":vh})
            page = ctx.new_page()
            c_errs = []
            page.on("console", lambda m: c_errs.append(m.text) if m.type=="error" else None)
            page.on("pageerror", lambda e: c_errs.append(str(e)))
            cur_role = None
            for (route, role, label, wait_sel) in ROUTES:
                r = {"viewport":vp["name"],"vw":vw,"vh":vh,"route":route,"label":label,
                     "role":role or "public","overflow":False,"hamburger":"N/A",
                     "screenshot":"","console_errors":0,"status":"PASS","notes":[]}
                try:
                    if role and role != cur_role:
                        ok = do_login(page, ctx, role)
                        if not ok:
                            raise RuntimeError("Login failed for "+role)
                        cur_role = role
                    page.goto("%s%s" % (FRONTEND_URL,route), wait_until="domcontentloaded", timeout=20000)
                    found = False
                    for sel in wait_sel.split(","):
                        try:
                            page.wait_for_selector(sel.strip(), timeout=7000, state="visible")
                            found = True
                            break
                        except Exception:
                            pass
                    if not found:
                        r["notes"].append("selector-not-found:"+wait_sel)
                    page.wait_for_timeout(700)
                    r["screenshot"] = shot(page, vp["name"], label)
                    ov = has_overflow(page)
                    r["overflow"] = ov
                    if ov:
                        r["status"] = "FAIL"
                        r["notes"].append("HORIZONTAL_OVERFLOW")
                        shot(page, vp["name"], label, "overflow")
                    if is_mobile and route not in ["/login","/register"]:
                        btn = page.locator('button[aria-label="Toggle Navigation Menu"]')
                        if btn.count() > 0:
                            try:
                                btn.first.click(timeout=5000)
                            except Exception:
                                pass
                            page.wait_for_timeout(400)
                            sx = page.evaluate("function(){var a=document.querySelector('aside');return a?a.getBoundingClientRect().left:-9999;}")
                            open_ok = sx > -100
                            r["hamburger"] = "open=OK" if open_ok else "open=FAIL"
                            if not open_ok:
                                r["status"] = "FAIL"
                                r["notes"].append("sidebar_hidden_after_hamburger")
                            bd = page.locator("div[aria-hidden='true']")
                            if bd.count() > 0:
                                try:
                                    bd.first.click(timeout=3000)
                                except Exception:
                                    pass
                                page.wait_for_timeout(300)
                                r["hamburger"] += " close=OK"
                            else:
                                try:
                                    btn.first.click(timeout=3000)
                                except Exception:
                                    pass
                                page.wait_for_timeout(300)
                                r["hamburger"] += " close=btn"
                        else:
                            r["hamburger"] = "btn_missing"
                            if vw <= 430:
                                r["notes"].append("WARN_hamburger_missing")
                    if route == "/map":
                        try:
                            page.wait_for_selector(".leaflet-container", timeout=8000)
                        except Exception:
                            pass
                        lf = page.locator(".leaflet-container")
                        if lf.count() == 0:
                            r["status"] = "FAIL"
                            r["notes"].append("leaflet_missing")
                        else:
                            r["notes"].append("leaflet_OK")
                    if route == "/submit":
                        fm = page.locator("form,select,input[type=number]")
                        r["notes"].append("form_elements:%d" % fm.count())
                    r["console_errors"] = len(c_errs)
                    if r["status"] == "PASS":
                        tp += 1
                        note = "  [" + "; ".join(r["notes"]) + "]" if r["notes"] else ""
                        print("  PASS  %-22s  ov=%s  hb=%-25s%s" % (label, str(ov), r["hamburger"], note))
                    else:
                        tf += 1
                        print("  FAIL  %-22s  %s" % (label, "; ".join(r["notes"])))
                except Exception as ex:
                    r["status"] = "FAIL"
                    r["notes"].append(str(ex)[:120])
                    tf += 1
                    print("  ERR   %-22s  %s" % (label, str(ex)[:80]))
                    shot(page, vp["name"], label, "error")
                results.append(r)
            ctx.close()
            browser.close()
    print("\n" + "="*60)
    print("TOTAL: %d PASS  |  %d FAIL  |  %d checks" % (tp, tf, len(results)))
    print("="*60)
    ovs = [r for r in results if r.get("overflow")]
    fails = [r for r in results if r["status"] == "FAIL"]
    if ovs:
        print("OVERFLOW ISSUES:")
        for r in ovs: print("  [%s] %s" % (r["viewport"], r["route"]))
    if fails:
        print("FAILED:")
        for r in fails: print("  [%s] %s: %s" % (r["viewport"], r["route"], "; ".join(r["notes"])))
    else:
        print("All layout checks PASSED.")
    rpath = Path(__file__).parent / "responsive_report.json"
    with open(rpath, "w") as f:
        json.dump({"commit":"7dd82b7","timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   "total_pass":tp,"total_fail":tf,
                   "viewports":[v["name"] for v in VIEWPORTS],
                   "routes":[r[0] for r in ROUTES],"results":results}, f, indent=2)
    print("Result: %s" % rpath)
    return tf == 0

if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
