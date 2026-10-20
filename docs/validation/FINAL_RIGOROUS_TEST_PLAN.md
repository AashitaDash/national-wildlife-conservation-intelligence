# Final Rigorous Test Plan

## 1. Baseline verification
- Purpose: Establish current project state.
- Expected result: Document species count, observation count, python version, node version, etc.

## 2. Backend regression tests
- Purpose: Ensure all existing backend tests pass.
- Preconditions: pytest installed and configured.
- Expected result: 0 failures, 0 unexpected errors.

## 3. Database integrity
- Purpose: Ensure database constraints and valid data.
- Expected result: No broken foreign keys, no duplicates.

## 4. Observation deduplication
- Purpose: Verify idempotent ingestion.
- Expected result: Duplicate records are rejected or deduplicated.

## 5. Real-data ingestion robustness
- Purpose: Verify graceful failure on malformed APIs.
- Expected result: Application does not crash.

## 6. Species matching
- Purpose: Test taxonomic resolution.
- Expected result: Correct mapping without silent failures.

## 7. PDF upload validation
- Purpose: Validate file upload constraints.
- Expected result: Reject oversized, empty, and fake PDFs.

## 8. PDF extraction & 9. PDF NLP processing
- Purpose: Ensure pipeline stability on documents.
- Expected result: No crashes on malformed text.

## 10. NLP adversarial testing & 11. NLP performance
- Purpose: Test resilience to XSS/SQLi in NLP, evaluate speed.

## 12. ML risk assessment & 13. Anomaly detection
- Purpose: Test predictive modeling.
- Expected result: Predict valid categorical states.

## 14. Spatial map & 15. Species Registry
- Purpose: Test UI and API for large datasets.

## 16. Authentication & 17. RBAC & 18. API security
- Purpose: Verify protection of endpoints.

## 19. Frontend failure handling & 20. Concurrent requests
- Purpose: Test resilience and state management.

## 21. Database failure recovery & 22. Repeated startup & 23. Data preservation
- Purpose: Ensure fault tolerance and idempotency.

## 24. UI terminology & 25. Visual QA & 26. Final regression
- Purpose: Polish and finalize platform.
