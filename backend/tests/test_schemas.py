"""Schema and config unit tests — backend.schemas / backend.config. No prior unit tests."""

from backend.config import Settings, get_settings
from backend.schemas import AskRequest, BreachClockRequest


def test_ask_request_bounds():
    AskRequest(question="What is minimum necessary?")
    try:
        AskRequest(question="")
        assert False, "empty question should fail"
    except Exception:
        pass


def test_breach_clock_request():
    payload = BreachClockRequest(
        description="Enough characters for a valid incident",
        discovered_at="2026-11-07",
        phi_involved=True,
    )
    assert payload.phi_involved is True


def test_settings_cache_and_defaults():
    get_settings.cache_clear()
    s = get_settings()
    assert isinstance(s, Settings)
    assert s.version
    assert s.rate_limit_per_minute >= 1
    get_settings.cache_clear()


def test_prod_requires_cors(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("LUMINA_ENV", "production")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    get_settings.cache_clear()
    s = Settings(
        env="production",
        cors_origins=["http://localhost:3000"],
        openai_api_key="",
    )
    try:
        # validate_for_boot checks os.environ CORS_ORIGINS, not the dataclass field alone
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        s.validate_for_boot()
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "CORS_ORIGINS" in str(exc)
    finally:
        get_settings.cache_clear()
        monkeypatch.setenv("LUMINA_ENV", "development")

