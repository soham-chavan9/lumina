# ==============================================================
# ✅ Lumina Backend API Live Server Tests
# Requires FastAPI backend running on port 8000
# ==============================================================

import pytest
import requests
from pathlib import Path

# ==============================================================
# Configuration
# ==============================================================
LIVE_URL = "http://127.0.0.1:8000"  # FastAPI live server address
BASE_DIR = Path(__file__).resolve().parent.parent  # points to /backend
TEST_PDF_DIR = BASE_DIR / "data" / "testing_pdfs"  # /backend/data/testing_pdfs
SAMPLE_PDF = TEST_PDF_DIR / "GDPR_Sample_Compliance.pdf"  # expected test PDF file


# ==============================================================
# Fixtures
# ==============================================================
@pytest.fixture(scope="session")
def sample_pdf():
    """✅ Ensure a sample test PDF exists in /backend/data/testing_pdfs"""
    TEST_PDF_DIR.mkdir(parents=True, exist_ok=True)

    if not SAMPLE_PDF.exists():
        print("⚙️ Creating a fake PDF for testing at:", SAMPLE_PDF)
        pdf_content = b"%PDF-1.4\n%Fake PDF for testing\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        SAMPLE_PDF.write_bytes(pdf_content)

    return SAMPLE_PDF


# ==============================================================
# Tests
# ==============================================================
def test_health_check():
    """✅ Verify FastAPI server health check route works"""
    print("\n🩺 Testing /health endpoint ...")
    response = requests.get(f"{LIVE_URL}/health", timeout=5)
    assert response.status_code == 200, f"❌ /health failed: {response.text}"
    assert response.json() == {"status": "ok"}
    print("✅ /health check passed!")


def test_file_upload(sample_pdf):
    """✅ Test uploading a sample PDF file from /data/testing_pdfs"""
    print("\n📤 Testing /upload endpoint ...")
    with open(sample_pdf, "rb") as f:
        files = {"file": (sample_pdf.name, f, "application/pdf")}
        response = requests.post(f"{LIVE_URL}/upload", files=files, timeout=10)

    assert response.status_code in [200, 201], f"❌ Upload failed: {response.text}"
    json_resp = response.json()
    assert any(k in json_resp for k in ["message", "success", "file_id", "detail"]), \
        f"❌ Unexpected upload response: {json_resp}"
    print(f"✅ File upload successful: {sample_pdf.name}")


def test_query_route():
    """✅ Test query endpoint on live server"""
    print("\n💬 Testing /query endpoint ...")
    payload = {"query": "Summarize the uploaded document"}
    response = requests.post(f"{LIVE_URL}/query", json=payload, timeout=10)

    assert response.status_code in [200, 201], f"❌ Query failed: {response.text}"
    json_resp = response.json()
    assert isinstance(json_resp, dict), "❌ Query response is not JSON"
    assert len(json_resp) > 0, "❌ Query returned empty response"
    print("✅ Query endpoint working correctly!")


# ==============================================================
# Entry Point for Direct Run
# ==============================================================
if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", __file__]))