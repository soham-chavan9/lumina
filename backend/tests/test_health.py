"""Health/ready/root smoke tests for backend.main — no prior unit tests in backend/tests/."""

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "model" in body
    assert "vector_store_ready" in body
    assert "X-Request-ID" in res.headers
    assert "X-Content-Type-Options" in res.headers


def test_ready(client):
    res = client.get("/ready")
    assert res.status_code == 200
    body = res.json()
    assert body["ready"] is True
    assert "version" in body


def test_root(client):
    res = client.get("/")
    assert res.status_code == 200
    body = res.json()
    assert body["service"] == "lumina"
    assert body["industry"] == "healthcare-hipaa"
    assert "endpoints" in body

