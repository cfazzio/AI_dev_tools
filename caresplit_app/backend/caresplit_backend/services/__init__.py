"""The one place UI code asks for a CareSplitService implementation.

Everything the UI needs from "the backend" goes through
:class:`caresplit_backend.services.base.CareSplitService`. Right now only a mock,
in-memory implementation exists, so this always returns that — but it is the
single seam where a real implementation would be wired in later without any
UI code changing.
"""

from __future__ import annotations

from .base import CareSplitService
from .mock_service import MockCareSplitService

_service: CareSplitService | None = None


def get_service() -> CareSplitService:
    global _service
    if _service is None:
        _service = MockCareSplitService()
    return _service


def reset_service() -> None:
    """Replace the singleton with a fresh mock. Mainly useful for tests."""
    global _service
    _service = MockCareSplitService()


__all__ = ["CareSplitService", "MockCareSplitService", "get_service", "reset_service"]
