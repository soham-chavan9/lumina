"""Shared fixtures for API unit tests (no live OpenAI required)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Force a deterministic non-prod boot for tests before app import.
os.environ.setdefault("LUMINA_ENV", "development")
os.environ.setdefault("LUMINA_SEED_SAMPLE_DOCS", "false")
os.environ.setdefault("LUMINA_RATE_LIMIT_PER_MINUTE", "10000")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")


@pytest.fixture(scope="session")
def client() -> TestClient:
    from backend.config import get_settings
    from backend.main import app

    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
