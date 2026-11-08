"""API key auth tests for backend.auth / protected routes."""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def locked_client(monkeypatch):
    monkeypatch.setenv("LUMINA_API_KEY", "secret-test-key")
    monkeypatch.setenv("LUMINA_ENV", "development")
    monkeypatch.setenv("LUMINA_SEED_SAMPLE_DOCS", "false")
    monkeypatch.setenv("LUMINA_RATE_LIMIT_PER_MINUTE", "10000")
    monkeypatch.setenv("LUMINA_LLM_RATE_LIMIT_PER_MINUTE", "10000")
    from backend.config import get_settings
    from backend.main import app

    get_settings.cache_clear()
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()
    monkeypatch.delenv("LUMINA_API_KEY", raising=False)


def test_ask_rejects_missing_key(locked_client):
    res = locked_client.post("/api/ask", json={"question": "What is minimum necessary?"})
    assert res.status_code == 401


def test_ask_accepts_valid_key(locked_client):
    res = locked_client.post(
        "/api/ask",
        json={"question": "What is minimum necessary?"},
        headers={"X-API-Key": "secret-test-key"},
    )
    assert res.status_code == 200


def test_health_stays_open(locked_client):
    assert locked_client.get("/health").status_code == 200
