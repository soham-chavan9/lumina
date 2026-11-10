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


class _RecordingStore:
    """Stand-in store that records which persist path the route selected."""

    created: list[str] = []

    def __init__(self, persist_path=None):
        self.persist_path = persist_path
        _RecordingStore.created.append(str(persist_path))

    def list_documents(self):
        return []

    def chunk_count(self):
        return 0


def test_tenant_header_selects_store_over_http(client, monkeypatch):
    _RecordingStore.created = []
    monkeypatch.setattr(es, "PersistentEmbedStore", _RecordingStore)
    monkeypatch.setattr(es, "_store_instances", {})

    assert client.get("/api/documents", headers={"X-Tenant-Id": "alpha"}).status_code == 200
    assert _RecordingStore.created[-1].endswith("tenants/alpha")

    assert client.get("/api/documents").status_code == 200
    assert _RecordingStore.created[-1].endswith("tenants/default")


def test_legacy_corpus_migrates_into_default_tenant(tmp_path, monkeypatch):
    for name in es.LEGACY_INDEX_FILES:
        (tmp_path / name).write_bytes(b"legacy-" + name.encode())
    monkeypatch.setattr(es, "DEFAULT_PERSIST", tmp_path)
    monkeypatch.setattr(es, "PersistentEmbedStore", _RecordingStore)
    monkeypatch.setattr(es, "_store_instances", {})

    es.get_embed_store("alpha")
    assert not (tmp_path / "tenants" / "alpha" / "index.faiss").exists()

    es.get_embed_store("default")
    target = tmp_path / "tenants" / "default"
    for name in es.LEGACY_INDEX_FILES:
        assert (target / name).read_bytes() == b"legacy-" + name.encode()
        assert (tmp_path / name).exists()  # copied, not moved


def test_legacy_migration_skips_when_default_tenant_has_index(tmp_path, monkeypatch):
    for name in es.LEGACY_INDEX_FILES:
        (tmp_path / name).write_bytes(b"legacy")
    target = tmp_path / "tenants" / "default"
    target.mkdir(parents=True)
    (target / "index.faiss").write_bytes(b"current")
    monkeypatch.setattr(es, "DEFAULT_PERSIST", tmp_path)
    monkeypatch.setattr(es, "PersistentEmbedStore", _RecordingStore)
    monkeypatch.setattr(es, "_store_instances", {})

    es.get_embed_store("default")
    assert (target / "index.faiss").read_bytes() == b"current"
    assert not (target / "index.pkl").exists()
