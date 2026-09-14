from fastapi.testclient import TestClient


def test_list_categories_returns_the_seeded_starter_set(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/categories", headers=auth_headers)
    assert response.status_code == 200
    names = {c["name"] for c in response.json()}
    assert "Medical / doctor visits" in names
    assert "In-home care / caregiving" in names


def test_category_response_uses_camel_case_decimal_strings(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/categories", headers=auth_headers)
    category = response.json()[0]
    assert set(category.keys()) == {"id", "name", "pctMe", "pctInsurance", "notes"}
    assert isinstance(category["pctMe"], str)
    assert isinstance(category["pctInsurance"], str)


def test_create_category(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/categories",
        headers=auth_headers,
        json={"name": "Dental", "pctMe": "60", "notes": "test note"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Dental"
    assert body["pctMe"] == "60"
    assert body["pctInsurance"] == "40"
    assert body["notes"] == "test note"


def test_create_category_defaults_notes_to_empty_string(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/categories", headers=auth_headers, json={"name": "Dental", "pctMe": "60"}
    )
    assert response.status_code == 201
    assert response.json()["notes"] == ""


def test_create_duplicate_category_name_is_rejected(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/categories",
        headers=auth_headers,
        json={"name": "Medical / doctor visits", "pctMe": "50"},
    )
    assert response.status_code == 409
    assert "message" in response.json()


def test_update_category(client: TestClient, auth_headers: dict[str, str]) -> None:
    categories = client.get("/categories", headers=auth_headers).json()
    category_id = categories[0]["id"]

    response = client.patch(
        f"/categories/{category_id}", headers=auth_headers, json={"pctMe": "77"}
    )
    assert response.status_code == 200
    assert response.json()["pctMe"] == "77"
    assert response.json()["name"] == categories[0]["name"]  # untouched


def test_update_missing_category_is_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.patch(
        "/categories/999999", headers=auth_headers, json={"pctMe": "50"}
    )
    assert response.status_code == 404


def test_delete_unused_category(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post(
        "/categories", headers=auth_headers, json={"name": "Dental", "pctMe": "60"}
    ).json()

    response = client.delete(f"/categories/{created['id']}", headers=auth_headers)
    assert response.status_code == 204

    follow_up = client.get("/categories", headers=auth_headers)
    assert created["id"] not in {c["id"] for c in follow_up.json()}


def test_delete_category_in_use_is_409(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    categories = client.get("/categories", headers=auth_headers).json()
    category_id = categories[0]["id"]
    client.post(
        "/expenses",
        headers=auth_headers,
        json={"date": "2026-01-01", "categoryId": category_id, "amount": "10.00"},
    )

    response = client.delete(f"/categories/{category_id}", headers=auth_headers)
    assert response.status_code == 409
