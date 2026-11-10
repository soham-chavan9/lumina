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



def test_cors_preflight_allows_auth_and_tenant_headers(client):
    res = client.options(
        "/api/documents",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "x-api-key,x-tenant-id",
        },
    )
    assert res.status_code == 200
