# Testing and Results

## Test Suite Execution
The repository ships with a comprehensive **pytest** test suite located under `backend/tests/` and additional end‑to‑end Playwright tests in the root.

### Command used
```powershell
pytest -q
```

### Summary of Results
```
=================================== ERRORS ====================================
_________________ ERROR collecting backend/tests/test_api.py __________________
ImportError while importing test module 'C:\Users\KIIT0001\Downloads\Wildlife_Conservation_Shareable\backend\tests\test_api.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
... ModuleNotFoundError: No module named 'backend'
_________________ ERROR collecting backend/tests/test_auth.py _________________
... ModuleNotFoundError: No module named 'backend'
_________________ ERROR collecting backend/tests/test_database.py ______________
... ModuleNotFoundError: No module named 'backend'
_________________ ERROR collecting backend/tests/test_ingestion.py ______________
... ModuleNotFoundError: No module named 'ingestion'
_________________ ERROR collecting backend/tests/test_ml.py __________________
... ModuleNotFoundError: No module named 'ml'
_________________ ERROR collecting backend/tests/test_nlp.py __________________
... ModuleNotFoundError: No module named 'nlp'
_________________ ERROR collecting backend/tests/test_rag.py __________________
... ModuleNotFoundError: No module named 'backend'
_________________ ERROR collecting backend/tests/test_rbac_workflow.py _____________
... (many lines omitted) ...
_________________ ERROR collecting backend/tests/test_spatial.py _________________
... (import errors similar to above)
_________________ ERROR collecting test_e2e_playwright.py ___________________
ModuleNotFoundError: No module named 'playwright'
_________________ ERROR collecting test_e2e_playwright_clean.py ______________
ModuleNotFoundError: No module named 'playwright'
_________________ ERROR collecting test_ui_playwright.py ____________________
ModuleNotFoundError: No module named 'playwright'
_________________ ERROR collecting test_v33_playwright.py ___________________
ModuleNotFoundError: No module named 'playwright'
_________________ ERROR collecting tests/test_v31_auth_security.py _____________
... openpyxl missing ...
=========================== short test summary info ===========================
ERROR backend/tests/test_api.py
ERROR backend/tests/test_auth.py
ERROR backend/tests/test_database.py
ERROR backend/tests/test_ingestion.py
ERROR backend/tests/test_ml.py
ERROR backend/tests/test_nlp.py
ERROR backend/tests/test_rag.py
ERROR backend/tests/test_rbac_workflow.py
ERROR backend/tests/test_spatial.py
ERROR test_e2e_playwright.py
ERROR test_e2e_playwright_clean.py
ERROR test_ui_playwright.py
ERROR test_v33_playwright.py
ERROR tests/test_v31_auth_security.py
!!!!!!!!!!!!!!!!!! Interrupted: 21 errors during collection !!!!!!!!!!!!!!!!!!!
21 errors in 17.37s
```

### Interpretation
* **Import errors** dominate: the test runner does not have the repository root on `PYTHONPATH`, causing `ModuleNotFoundError` for internal packages (`backend`, `ml`, `nlp`, `ingestion`).
* **Optional dependencies** such as `playwright`, `openpyxl`, and various ML libraries are not installed in the sandbox, leading to additional failures.
* No tests actually executed; all failed during collection.

### Recommendations
1. **Adjust PYTHONPATH** when running tests, e.g.:
   ```powershell
   $env:PYTHONPATH = "C:\Users\KIIT0001\Downloads\Wildlife_Conservation_Shareable"
   pytest -q
   ```
2. Install optional test dependencies (listed in `backend/requirements.txt` and `frontend/package.json`).
3. Ensure a PostgreSQL instance is reachable for integration tests that hit the DB, or switch to the SQLite fallback.
4. Once import errors are resolved, the suite is expected to run **30 passing unit & integration tests** as claimed in the README.

---
*All file references are relative to the repository root.*

