"""Where Lumina writes runtime data (vector index, performance logs)."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent


def data_dir() -> Path:
    """Writable data root.

    LUMINA_DATA_DIR wins when set. On Vercel the deployed bundle is read-only and
    only /tmp is writable (per instance, not persistent), so default there.
    Everywhere else (local, Docker volumes) keep backend/data.
    """
    override = os.getenv("LUMINA_DATA_DIR", "").strip()
    if override:
        return Path(override)
    if os.getenv("VERCEL"):
        return Path("/tmp/lumina")
    return BACKEND_DIR / "data"
