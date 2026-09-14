from datetime import date

from fastapi.testclient import TestClient


def test_dashboard_requires_the_today_param(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/dashboard", headers=auth_headers)
    assert response.status_code == 422


def test_dashboard_totals_reflect_seeded_data(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    today = date.today().isoformat()
    response = client.get("/dashboard", params={"today": today}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"month", "year", "recent"}
    assert float(body["year"]["total"]) > 0
    assert float(body["month"]["total"]) > 0
    assert len(body["recent"]) > 0
    assert len(body["recent"]) <= 8


def test_dashboard_totals_split_adds_up(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    today = date.today().isoformat()
    body = client.get("/dashboard", params={"today": today}, headers=auth_headers).json()
    year = body["year"]
    assert round(float(year["me"]) + float(year["insurance"]), 2) == round(
        float(year["total"]), 2
    )


def test_available_years_includes_seeded_years(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/reports/years", headers=auth_headers)
    assert response.status_code == 200
    years = response.json()
    assert date.today().year in years
    assert years == sorted(years, reverse=True)


def test_yearly_report_structure_for_a_seeded_year(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    year = date.today().year
    response = client.get(f"/reports/{year}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["year"] == year
    assert len(body["byCategory"]) > 0
    assert len(body["byMonth"]) > 0
    assert float(body["totals"]["total"]) > 0


def test_yearly_report_for_a_year_with_no_data_is_empty_not_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/reports/1999", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["year"] == 1999
    assert body["byCategory"] == []
    assert body["byMonth"] == []
    assert body["totals"]["total"] == "0.00"


def test_reports_years_route_is_not_shadowed_by_the_year_path_param(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    # /reports/years must resolve to listAvailableYears, not getYearlyReport(year="years").
    response = client.get("/reports/years", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
