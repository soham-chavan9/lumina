"""Local-model fallback when OpenAI is missing or rejects the key."""

import pytest
from langchain_community.chat_models import ChatOllama
from langchain_core.runnables import RunnableWithFallbacks

from backend import llm_workflow as lw
from backend.utils import embed_store as es
from backend.utils.local_embeddings import LocalHashEmbeddings


@pytest.fixture
def fallback_on(monkeypatch):
    monkeypatch.setenv("LUMINA_LOCAL_FALLBACK", "true")
    monkeypatch.setattr(lw, "_probe_cache", None)


class _ProbeEmbeddings:
    """Stand-in for OpenAIEmbeddings: records probes, accepts or rejects the key."""

    calls: list[str] = []
    accept = True

    def __init__(self, **kwargs):
        pass

    def embed_query(self, text):
        _ProbeEmbeddings.calls.append(text)
        if not _ProbeEmbeddings.accept:
            raise RuntimeError("401 invalid_api_key")
        return [0.0]


def _probe(monkeypatch, accept: bool):
    _ProbeEmbeddings.calls = []
    _ProbeEmbeddings.accept = accept
    monkeypatch.setattr(lw, "OpenAIEmbeddings", _ProbeEmbeddings)


def test_no_key_uses_local_model(fallback_on, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    model = lw.get_lumina_model()
    assert isinstance(model, ChatOllama)
    assert model.model == "llama3.1:8b"
    assert lw.active_model_label() == "llama3.1:8b (local)"


def test_json_mode_forces_json_from_local_model(fallback_on, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert lw.get_lumina_model(json_mode=True).format == "json"
    assert lw.get_lumina_model().format is None


def test_rejected_key_uses_local_model_and_probes_once(fallback_on, monkeypatch):
    _probe(monkeypatch, accept=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-invalid")
    assert isinstance(lw.get_lumina_model(), ChatOllama)
    assert isinstance(lw.get_lumina_model(), ChatOllama)
    assert len(_ProbeEmbeddings.calls) == 1


def test_working_key_uses_openai_with_local_backup(fallback_on, monkeypatch):
    _probe(monkeypatch, accept=True)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-valid")
    model = lw.get_lumina_model()
    assert isinstance(model, RunnableWithFallbacks)
    assert isinstance(model.fallbacks[0], ChatOllama)
    assert lw.active_model_label() == "gpt-4o-mini"


def test_fallback_disabled_without_key_raises(monkeypatch):
    monkeypatch.setenv("LUMINA_LOCAL_FALLBACK", "false")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        lw.get_lumina_model()


def test_unusable_openai_switches_to_local_store(monkeypatch, tmp_path):
    monkeypatch.setenv("LUMINA_EMBEDDINGS", "auto")
    monkeypatch.setattr(es, "openai_usable", lambda: False)
    monkeypatch.setattr(es, "DEFAULT_PERSIST", tmp_path)
    monkeypatch.setattr(es, "_store_instances", {})

    store = es.get_embed_store("acme")
    assert store.persist_path == tmp_path / "local" / "tenants" / "acme"
    assert isinstance(store.embedding_model, LocalHashEmbeddings)
    assert store.default_max_distance == es.LOCAL_MAX_DISTANCE
    assert store.honor_caller_distance is False


def test_local_embeddings_retrieve_the_matching_policy(tmp_path):
    store = es.PersistentEmbedStore(
        persist_path=str(tmp_path),
        embedding_model=LocalHashEmbeddings(),
        max_distance=es.LOCAL_MAX_DISTANCE,
        honor_caller_distance=False,
    )
    store.add_document(
        "Breach notification: notify affected individuals without unreasonable delay and "
        "no later than 60 days after discovery of a breach of unsecured PHI.",
        "breach.pdf",
    )
    store.add_document(
        "Business associates must sign a BAA before receiving protected health information "
        "from the covered entity.",
        "baa.pdf",
    )

    hits = store.query("How many days do we have to notify individuals after a breach?")
    assert [h["source"] for h in hits] == ["breach.pdf"]
    # Callers pass OpenAI-tuned thresholds; the local store must not apply them.
    assert [h["source"] for h in store.query("breach notification timeline", max_distance=1.2)] == ["breach.pdf"]


def test_local_embeddings_are_deterministic_and_normalised():
    emb = LocalHashEmbeddings()
    a = emb.embed_query("Minimum necessary standard for workforce access")
    assert a == emb.embed_query("Minimum necessary standard for workforce access")
    assert abs(sum(x * x for x in a) - 1.0) < 1e-5


@pytest.mark.parametrize(
    "reply",
    [
        '{"likely_reportable": true}',
        '```json\n{"likely_reportable": true}\n```',
        'Here is the assessment:\n```json\n{"likely_reportable": true}\n```\nLet me know!',
        'Sure! {"likely_reportable": true} Hope that helps.',
    ],
)
def test_extract_json_handles_local_model_replies(reply):
    assert lw.extract_json(reply) == {"likely_reportable": True}


def test_extract_json_finds_arrays_and_rejects_prose():
    assert lw.extract_json('Questions:\n[{"question": "q1", "category": "breach"}]') == [
        {"question": "q1", "category": "breach"}
    ]
    with pytest.raises(ValueError):
        lw.extract_json("I could not find anything relevant.")
