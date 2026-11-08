"""Rate-limit middleware trust and budget tests."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.middleware import RateLimitMiddleware


def _app(trust_proxy: bool, llm_limit: int = 2, general_limit: int = 50):
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        limit_per_minute=general_limit,
        llm_limit_per_minute=llm_limit,
        trust_proxy=trust_proxy,
    )

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.post("/api/ask")
    def ask():
        return {"ok": True}

    @app.get("/api/documents")
    def docs():
        return {"ok": True}

    return app


def test_xff_ignored_when_proxy_untrusted():
    client = TestClient(_app(trust_proxy=False, llm_limit=2))
    for i in range(2):
        r = client.post("/api/ask", headers={"X-Forwarded-For": f"203.0.113.{i}"})
        assert r.status_code == 200
    # third call from same peer IP should 429 even with rotating XFF
    r = client.post("/api/ask", headers={"X-Forwarded-For": "203.0.113.99"})
    assert r.status_code == 429


def test_llm_budget_stricter_than_general():
    client = TestClient(_app(trust_proxy=False, llm_limit=1, general_limit=20))
    assert client.post("/api/ask").status_code == 200
    assert client.post("/api/ask").status_code == 429
    assert client.get("/api/documents").status_code == 200


def test_health_exempt():
    client = TestClient(_app(trust_proxy=False, llm_limit=1))
    assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 200
