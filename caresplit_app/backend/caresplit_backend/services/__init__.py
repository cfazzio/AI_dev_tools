"""Re-exports of this package's public API.

The in-process service-singleton pattern that used to live here
(get_service/reset_service) moved to caresplit_frontend.services — that
was always a frontend concern (which implementation the UI talks to), not
a backend one. The backend's own consumer of MockCareSplitService is
caresplit_backend/api/store.py, which instantiates it directly.
"""

from __future__ import annotations

from .base import CareSplitService
from .mock_service import MockCareSplitService

__all__ = ["CareSplitService", "MockCareSplitService"]
