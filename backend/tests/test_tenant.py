"""Tenant isolation for FAISS stores."""

from backend.tenant import get_current_tenant, sanitize_tenant_id
from backend.utils import embed_store as es


def test_sanitize_tenant():
    assert sanitize_tenant_id("../Evil!!") == "evil"
    assert sanitize_tenant_id("") == "default"
    assert sanitize_tenant_id("Acme_Health-1") == "acme_health-1"


def test_stores_are_isolated_by_tenant(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-used")
    es._store_instances.clear()
    from backend.tenant import _tenant_ctx

    token_a = _tenant_ctx.set("alpha")
    store_a = es.get_embed_store()
    _tenant_ctx.reset(token_a)

    token_b = _tenant_ctx.set("beta")
    store_b = es.get_embed_store()
    _tenant_ctx.reset(token_b)

    assert store_a is not store_b
    assert "alpha" in str(store_a.persist_path)
    assert "beta" in str(store_b.persist_path)
    assert get_current_tenant() in {"default", "beta", "alpha"}
