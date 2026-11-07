"""DEPRECATED — duplicate /ask path removed from main.

Use backend.routes.ask_route exclusively. Kept only so old notebooks
that import this module do not crash on import.
"""

from fastapi import APIRouter

router = APIRouter()
