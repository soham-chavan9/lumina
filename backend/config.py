"""Central configuration — validated once at process start."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache

logger = logging.getLogger("lumina.config")


def _split_origins(raw: str | None, fallback: str) -> list[str]:
    source = raw if raw and raw.strip() else fallback
    return [o.strip() for o in source.split(",") if o.strip()]


@dataclass(frozen=True)
class Settings:
    env: str = "development"
    openai_api_key: str = ""
    api_key: str = ""
    model: str = "gpt-4o-mini"
    embed_model: str = "text-embedding-3-small"
    max_distance: float = 1.2
    cors_origins: list[str] = field(default_factory=list)
    seed_sample_docs: bool = False
    rate_limit_per_minute: int = 120
    llm_rate_limit_per_minute: int = 20
    trust_proxy: bool = False
    max_upload_mb: int = 15
    max_upload_files: int = 10
    version: str = "2.3.0"

    @property
    def is_prod(self) -> bool:
        return self.env in {"production", "prod"}

    def validate_for_boot(self) -> None:
        if not self.is_prod:
            return
        if not self.openai_api_key:
            logger.warning(
                "LUMINA_ENV=production but OPENAI_API_KEY is empty — RAG/upload will fail"
            )
        if not self.api_key:
            raise RuntimeError(
                "Production requires LUMINA_API_KEY — unauthenticated API access is not allowed."
            )
        if not os.getenv("CORS_ORIGINS"):
            raise RuntimeError(
                "Production requires CORS_ORIGINS to be set explicitly "
                "(do not rely on localhost defaults)."
            )
        if any("localhost" in o or "127.0.0.1" in o for o in self.cors_origins):
            logger.warning(
                "Production CORS_ORIGINS still includes localhost — confirm this is intentional"
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    env = os.getenv("LUMINA_ENV", "development").lower().strip()
    default_origins = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:3001,http://127.0.0.1:3001"
    )
    settings = Settings(
        env=env,
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        api_key=os.getenv("LUMINA_API_KEY", "").strip(),
        model=os.getenv("LUMINA_MODEL", "gpt-4o-mini").strip(),
        embed_model=os.getenv("LUMINA_EMBED_MODEL", "text-embedding-3-small").strip(),
        max_distance=float(os.getenv("LUMINA_MAX_DISTANCE", "1.2")),
        cors_origins=_split_origins(os.getenv("CORS_ORIGINS"), default_origins),
        seed_sample_docs=os.getenv("LUMINA_SEED_SAMPLE_DOCS", "false").lower()
        in {"1", "true", "yes"},
        rate_limit_per_minute=int(os.getenv("LUMINA_RATE_LIMIT_PER_MINUTE", "120")),
        llm_rate_limit_per_minute=int(os.getenv("LUMINA_LLM_RATE_LIMIT_PER_MINUTE", "20")),
        trust_proxy=os.getenv("LUMINA_TRUST_PROXY", "false").lower() in {"1", "true", "yes"},
        max_upload_mb=int(os.getenv("LUMINA_MAX_UPLOAD_MB", "15")),
        max_upload_files=int(os.getenv("LUMINA_MAX_UPLOAD_FILES", "10")),
        version=os.getenv("LUMINA_VERSION", "2.3.0"),
    )
    return settings
