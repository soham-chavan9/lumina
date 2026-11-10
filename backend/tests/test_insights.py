"""Suggested-question behaviour for /api/suggestions."""

from backend.routes import insights_route


class _EmptyStore:
    def is_ready(self) -> bool:
        return False


def test_suggestions_empty_without_corpus(client, monkeypatch):
    monkeypatch.setattr(insights_route, "get_embed_store", lambda: _EmptyStore())
    res = client.get("/api/suggestions")
    assert res.status_code == 200
    assert res.json()["suggestions"] == []
