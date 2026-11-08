"""Upload validation tests for backend.routes.upload_route. Scripts under backend/scripts are live-only; this is the unit suite."""

def test_upload_rejects_non_pdf(client):
    res = client.post(
        "/api/upload",
        files={"files": ("notes.txt", b"not a pdf", "text/plain")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["results"][0]["status"].startswith("Skipped")

