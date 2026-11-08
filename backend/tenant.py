"""Per-request tenant isolation for the vector corpus.

Wired via Depends on API routers; get_embed_store() reads the context var.
User asked to bridge gap C2 (shared FAISS bleed).
"""

from __future__ import annotations

import re
from contextvars import ContextVar

from fastapi import Header

_tenant_ctx: ContextVar[str] = ContextVar("lumina_tenant", default="default")


def sanitize_tenant_id(raw: str | None) -> str:
    value = (raw or "default").strip().lower() or "default"
    cleaned = re.sub(r"[^a-z0-9_-]", "", value)[:64]
    return cleaned or "default"


def get_current_tenant() -> str:
    return _tenant_ctx.get()


def bind_tenant(
    x_tenant_id: str | None = Header(default="default", alias="X-Tenant-Id"),
) -> str:
    tenant = sanitize_tenant_id(x_tenant_id)
    _tenant_ctx.set(tenant)
    return tenant
