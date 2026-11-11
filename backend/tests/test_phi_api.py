"""PHI scan endpoint and the upload check that keeps patient records out of the library."""

from backend.routes import upload_route
from backend.scripts.eval_phi_detector import DEFAULT_DIR


def _pdf(name: str) -> bytes:
    return (DEFAULT_DIR / name).read_bytes()


def _scan(client, name: str):
    return client.post("/api/phi-scan", files={"file": (name, _pdf(name), "application/pdf")})


def test_phi_scan_reports_categories_with_masked_values(client):
    res = _scan(client, "01_patient_intake_form.pdf")
    assert res.status_code == 200
    body = res.json()
    assert body["verdict"] == "phi_found"
    assert body["likely_patient_record"] is True
    assert {"ssn", "mrn", "name", "dob", "email", "ip"} <= {c["category"] for c in body["categories"]}
    # Values come back partially masked, never in full.
    assert "941-38-3286" not in res.text
    assert "Maria Delgado" not in res.text


def test_phi_scan_control_is_clean(client):
    body = _scan(client, "06_deidentified_control.pdf").json()
    assert body["verdict"] == "no_phi_found"
    assert body["identifier_count"] == 0
    assert body["categories"] == []


def test_phi_scan_rejects_non_pdf(client):
    res = client.post("/api/phi-scan", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert res.status_code == 400


class _FakeStore:
    def __init__(self):
        self.added: list[str] = []

    def add_document(self, text, source):
        self.added.append(source)
        return 3


def test_upload_refuses_patient_records_but_files_clean_documents(client, monkeypatch):
    store = _FakeStore()
    monkeypatch.setattr(upload_route, "get_embed_store", lambda: store)
    res = client.post(
        "/api/upload",
        files=[
            ("files", ("intake.pdf", _pdf("01_patient_intake_form.pdf"), "application/pdf")),
            ("files", ("control.pdf", _pdf("06_deidentified_control.pdf"), "application/pdf")),
        ],
    )
    statuses = {r["filename"]: r["status"] for r in res.json()["results"]}
    assert statuses["intake.pdf"].startswith("Not filed: this looks like a patient record")
    assert statuses["control.pdf"] == "Embedded successfully."
    assert store.added == ["control.pdf"]
