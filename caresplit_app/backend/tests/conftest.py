import pytest
from fastapi.testclient import TestClient

from caresplit_backend.api.auth import get_token_store
from caresplit_backend.api.main import app
from caresplit_backend.api.store import DEMO_PASSWORD, DEMO_USERNAME, reset_store


@pytest.fixture(autouse=True)
def _reset_api_state():
    """Every API test starts from a freshly-seeded store and no issued tokens."""
    reset_store()
    get_token_store().reset()
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/token", json={"username": DEMO_USERNAME, "password": DEMO_PASSWORD}
    )
    token = response.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}
