import pytest

from caresplit_backend.services import reset_service

pytest_plugins = ["nicegui.testing.user_plugin"]


@pytest.fixture(autouse=True)
def fresh_mock_service():
    """Every test starts from a clean, freshly-seeded mock service."""
    reset_service()
    yield
    reset_service()
