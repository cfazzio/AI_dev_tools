"""The one place every page asks for a CareSplitService implementation.

Chooses the real API client by default; set CARESPLIT_BACKEND=mock to run
against the in-process mock instead — e.g. for tests (see
frontend/tests/conftest.py, which forces this), or local UI development
without the FastAPI server running.
"""

from __future__ import annotations

import os
from typing import Optional

from caresplit_backend.services.base import CareSplitService
from caresplit_backend.services.mock_service import MockCareSplitService

from caresplit_frontend.api_client import ApiCareSplitService

_service: Optional[CareSplitService] = None


def _build_service() -> CareSplitService:
    if os.environ.get("CARESPLIT_BACKEND", "api").lower() == "mock":
        return MockCareSplitService()
    return ApiCareSplitService()


def get_service() -> CareSplitService:
    global _service
    if _service is None:
        _service = _build_service()
    return _service


def reset_service() -> None:
    """Replace the singleton with a fresh one. Mainly useful for tests."""
    global _service
    _service = _build_service()
