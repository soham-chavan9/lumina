"""Runtime data directory selection (local vs Vercel vs explicit override)."""

from pathlib import Path

from backend.storage import BACKEND_DIR, data_dir


def test_defaults_to_backend_data(monkeypatch):
    monkeypatch.delenv("LUMINA_DATA_DIR", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    assert data_dir() == BACKEND_DIR / "data"


def test_uses_tmp_on_vercel(monkeypatch):
    monkeypatch.delenv("LUMINA_DATA_DIR", raising=False)
    monkeypatch.setenv("VERCEL", "1")
    assert data_dir() == Path("/tmp/lumina")


def test_explicit_override_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("LUMINA_DATA_DIR", str(tmp_path))
    assert data_dir() == tmp_path
