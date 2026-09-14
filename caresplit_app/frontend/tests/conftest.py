"""Shared fixtures for frontend tests.

Two independent things get reset before every test in this directory:

- the frontend's own service singleton, forced to the in-process mock (so
  UI tests never need a live backend process — set before import so
  caresplit_frontend.services._build_service() picks it up the first time
  anything calls get_service())
- the backend API's in-memory store + issued tokens, for
  test_api_client.py's integration tests against the real FastAPI app
  (in-process via ASGI, still no server process) — a harmless no-op for
  test_ui.py, which never touches it
"""

from __future__ import annotations

import os

os.environ["CARESPLIT_BACKEND"] = "mock"

import pytest

from caresplit_backend.api.auth import get_token_store
from caresplit_backend.api.store import reset_store
from caresplit_frontend.services import reset_service


@pytest.fixture(autouse=True)
def _reset_frontend_service():
    reset_service()
    yield


@pytest.fixture(autouse=True)
def _reset_backend_api_state():
    reset_store()
    get_token_store().reset()
    yield
