"""API-key authentication for mutating / PHI-adjacent routes.

Called from route Depends(...) in ask/upload/library/insights/healthcare.
No prior auth module existed. User: plan commits ... start bridging the gaps.
"""

from __future__ import annotations

import hmac

from fastapi import Header, HTTPException

from backend.config import get_settings


def _extract_key(authorization: str | None, x_api_key: str | None) -> str | None:
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def require_api_key(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    settings = get_settings()
    expected = settings.api_key

    # Dev convenience: open access only when no key configured and not production.
    if not expected:
        if settings.is_prod:
            raise HTTPException(
                status_code=503,
                detail="Server misconfigured: LUMINA_API_KEY is required in production.",
            )
        return

    provided = _extract_key(authorization, x_api_key)
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
