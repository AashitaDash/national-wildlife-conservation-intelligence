import io
import pytest
from fastapi.testclient import TestClient


def _make_text_pdf(text: str) -> bytes:
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=11)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def _make_empty_pdf() -> bytes:
    import fitz
    doc = fitz.open()
    doc.new_page()
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


CONSERVATION_TEXT = (
    "Poaching pressure has significantly increased around tiger habitats in "
    "Similipal National Park, Odisha. WWF India reports mining encroachment "
    "along the Mahanadi river basin threatens Bengal Tiger corridors in 2024."
)


@pytest.fixture(scope="module")
def client():
    from backend.app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def valid_pdf_bytes():
    return _make_text_pdf(CONSERVATION_TEXT)


@pytest.fixture(scope="module")
def empty_pdf_bytes():
    return _make_empty_pdf()


# 1 — Valid PDF upload returns 201 with NLP result
def test_valid_pdf_upload_returns_201(client, valid_pdf_bytes):
    r = client.post(
        "/api/v1/documents/upload-pdf",
        files={"file": ("test.pdf", valid_pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert "id" in data
    assert data["source_type"] == "PDF_UPLOAD"
    assert data.get("summary") is not None


# 2 — PDF text extraction helper returns non-empty string
def test_pdf_text_extraction(valid_pdf_bytes):
    from backend.app.routers.documents import _extract_pdf_text
    extracted = _extract_pdf_text(valid_pdf_bytes)
    assert isinstance(extracted, str)
    assert len(extracted.strip()) > 20


# 3 — NLP results key present after PDF upload
def test_pdf_nlp_results_present(client, valid_pdf_bytes):
    r = client.post(
        "/api/v1/documents/upload-pdf",
        files={"file": ("report.pdf", valid_pdf_bytes, "application/pdf")},
        params={"title": "Tiger Corridor Report"},
    )
    assert r.status_code == 201
    assert "nlp_results" in r.json()


# 4 — Invalid file extension rejected with 415
def test_invalid_extension_rejected(client, valid_pdf_bytes):
    r = client.post(
        "/api/v1/documents/upload-pdf",
        files={"file": ("document.docx", valid_pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 415


# 5 — Invalid MIME type rejected with 415
def test_invalid_mime_type_rejected(client, valid_pdf_bytes):
    r = client.post(
        "/api/v1/documents/upload-pdf",
        files={"file": ("document.pdf", valid_pdf_bytes, "image/png")},
    )
    assert r.status_code == 415


# 6 — Oversized file rejected with 413
def test_oversized_pdf_rejected(client):
    from backend.app.routers.documents import MAX_PDF_UPLOAD_BYTES
    fake_big = b"%PDF" + b"0" * (MAX_PDF_UPLOAD_BYTES + 1)
    r = client.post(
        "/api/v1/documents/upload-pdf",
        files={"file": ("big.pdf", fake_big, "application/pdf")},
    )
    assert r.status_code == 413


# 7 — Image-only (empty-text) PDF rejected with 422
def test_empty_text_pdf_rejected(client, empty_pdf_bytes):
    r = client.post(
        "/api/v1/documents/upload-pdf",
        files={"file": ("scanned.pdf", empty_pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 422
    detail = r.json()["detail"].lower()
    assert "extractable" in detail or "text" in detail or "ocr" in detail


# 8 — Non-%PDF magic bytes rejected with 422
def test_fake_pdf_magic_rejected(client):
    fake = b"PK\x03\x04" + b"\x00" * 200
    r = client.post(
        "/api/v1/documents/upload-pdf",
        files={"file": ("mal.pdf", fake, "application/pdf")},
    )
    assert r.status_code == 422
    detail = r.json()["detail"].lower()
    assert "pdf" in detail


# 9 — Unauthenticated request accepted (get_optional_user allows anonymous)
def test_unauthenticated_upload_accepted(client, valid_pdf_bytes):
    r = client.post(
        "/api/v1/documents/upload-pdf",
        files={"file": ("anon.pdf", valid_pdf_bytes, "application/pdf")},
    )
    # Should succeed without authentication token
    assert r.status_code == 201


# 10 — Existing text NLP endpoint regression test
def test_existing_text_nlp_still_works(client):
    r = client.post(
        "/api/v1/documents",
        json={
            "title": "Regression Test",
            "source_type": "INCIDENT_LOG",
            "raw_text": "Asian elephant sighted near Similipal corridor during morning patrol.",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["source_type"] == "INCIDENT_LOG"
