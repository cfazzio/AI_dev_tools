from fastapi.testclient import TestClient

from caresplit_backend.api.store import DEMO_PASSWORD, DEMO_USERNAME


def test_login_with_correct_credentials_returns_a_token(client: TestClient) -> None:
    response = client.post(
        "/auth/token", json={"username": DEMO_USERNAME, "password": DEMO_PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tokenType"] == "bearer"
    assert isinstance(body["accessToken"], str) and len(body["accessToken"]) > 20
    assert "expiresAt" in body


def test_login_with_wrong_password_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/auth/token", json={"username": DEMO_USERNAME, "password": "not-the-password"}
    )
    assert response.status_code == 401
    assert "message" in response.json()


def test_login_with_unknown_username_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/auth/token", json={"username": "nobody", "password": DEMO_PASSWORD}
    )
    assert response.status_code == 401


def test_password_is_not_stored_in_plain_text() -> None:
    from caresplit_backend.api.store import get_store

    user = get_store().users[DEMO_USERNAME]
    assert DEMO_PASSWORD not in user.hashed_password
    assert "$" in user.hashed_password  # salt$digest


def test_protected_endpoint_without_a_token_is_rejected(client: TestClient) -> None:
    response = client.get("/categories")
    assert response.status_code == 401
    assert response.json() == {"message": "Not authenticated"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_protected_endpoint_with_a_garbage_token_is_rejected(client: TestClient) -> None:
    response = client.get("/categories", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_protected_endpoint_with_a_valid_token_succeeds(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/categories", headers=auth_headers)
    assert response.status_code == 200


def test_expired_token_is_rejected(client: TestClient, auth_headers: dict[str, str]) -> None:
    from datetime import datetime, timedelta, timezone

    from caresplit_backend.api.auth import get_token_store

    token_store = get_token_store()
    token = auth_headers["Authorization"].removeprefix("Bearer ")
    # Force the just-issued token into the past instead of waiting 24h.
    token_store._tokens[token].expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    response = client.get("/categories", headers=auth_headers)
    assert response.status_code == 401
