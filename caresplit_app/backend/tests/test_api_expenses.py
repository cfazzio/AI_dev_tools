from fastapi.testclient import TestClient


def _first_category(client: TestClient, auth_headers: dict[str, str], name: str) -> dict:
    categories = client.get("/categories", headers=auth_headers).json()
    return next(c for c in categories if c["name"] == name)


def test_list_expenses_returns_the_seeded_demo_data(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/expenses", headers=auth_headers)
    assert response.status_code == 200
    expenses = response.json()
    assert len(expenses) == 8


def test_expense_response_uses_camel_case_decimal_strings(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    expense = client.get("/expenses", headers=auth_headers).json()[0]
    assert set(expense.keys()) == {
        "id",
        "date",
        "categoryId",
        "categoryName",
        "amount",
        "pctMe",
        "pctInsurance",
        "amountMe",
        "amountInsurance",
        "description",
        "note",
        "receiptFilename",
    }
    assert isinstance(expense["amount"], str)
    assert isinstance(expense["amountMe"], str)


def test_list_expenses_filters_by_category(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    medical = _first_category(client, auth_headers, "Medical / doctor visits")

    response = client.get(
        "/expenses", headers=auth_headers, params={"categoryId": medical["id"]}
    )
    assert response.status_code == 200
    expenses = response.json()
    assert len(expenses) > 0
    assert all(e["categoryId"] == medical["id"] for e in expenses)


def test_create_expense_inherits_category_split_by_default(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    medical = _first_category(client, auth_headers, "Medical / doctor visits")  # 20% me

    response = client.post(
        "/expenses",
        headers=auth_headers,
        json={"date": "2026-01-01", "categoryId": medical["id"], "amount": "100.00"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["pctMe"] == "20"
    assert body["amountMe"] == "20.00"
    assert body["amountInsurance"] == "80.00"
    assert body["categoryName"] == "Medical / doctor visits"


def test_create_expense_can_override_split(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    medical = _first_category(client, auth_headers, "Medical / doctor visits")  # 20% me

    response = client.post(
        "/expenses",
        headers=auth_headers,
        json={
            "date": "2026-01-01",
            "categoryId": medical["id"],
            "amount": "100.00",
            "pctMe": "100",
        },
    )
    assert response.status_code == 201
    assert response.json()["amountMe"] == "100.00"


def test_create_expense_for_missing_category_is_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/expenses",
        headers=auth_headers,
        json={"date": "2026-01-01", "categoryId": 999999, "amount": "10.00"},
    )
    assert response.status_code == 404


def test_update_expense(client: TestClient, auth_headers: dict[str, str]) -> None:
    medical = _first_category(client, auth_headers, "Medical / doctor visits")
    created = client.post(
        "/expenses",
        headers=auth_headers,
        json={"date": "2026-01-01", "categoryId": medical["id"], "amount": "10.00"},
    ).json()

    response = client.patch(
        f"/expenses/{created['id']}",
        headers=auth_headers,
        json={"amount": "55.00", "description": "updated"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["amount"] == "55.00"
    assert body["description"] == "updated"
    assert body["categoryId"] == medical["id"]  # untouched


def test_update_missing_expense_is_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.patch(
        "/expenses/999999", headers=auth_headers, json={"amount": "10.00"}
    )
    assert response.status_code == 404


def test_delete_expense(client: TestClient, auth_headers: dict[str, str]) -> None:
    medical = _first_category(client, auth_headers, "Medical / doctor visits")
    created = client.post(
        "/expenses",
        headers=auth_headers,
        json={"date": "2026-01-01", "categoryId": medical["id"], "amount": "10.00"},
    ).json()

    response = client.delete(f"/expenses/{created['id']}", headers=auth_headers)
    assert response.status_code == 204

    follow_up = client.get("/expenses", headers=auth_headers)
    assert created["id"] not in {e["id"] for e in follow_up.json()}
