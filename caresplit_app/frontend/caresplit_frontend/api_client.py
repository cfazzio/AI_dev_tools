"""HTTP-backed CareSplitService: calls the real FastAPI backend
(backend/caresplit_backend/api/) over the wire instead of running
in-process. Implements the same protocol as MockCareSplitService — see
caresplit_backend/services/base.py — so no page needs to know which one
it's talking to; only caresplit_frontend.services.get_service() decides.

Converts between the wire format (camelCase, decimals as strings — see
openapi.yaml) and the domain dataclasses every page already works with.

get_category/get_expense aren't real endpoints (openapi.yaml deliberately
omits them — no page calls them, see its info.description), so they're
implemented here by fetching the list and filtering client-side, purely to
keep this class a complete, drop-in CareSplitService.
"""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from typing import Optional

import httpx

from caresplit_backend.domain import (
    Category,
    CategoryBreakdown,
    DashboardTotals,
    Expense,
    MonthBreakdown,
    Totals,
    YearlyReport,
)
from caresplit_backend.services.errors import CareSplitError

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_USERNAME = "cindy"
DEFAULT_PASSWORD = "caresplit-demo"


class ApiError(CareSplitError):
    """Any non-2xx response from the API, carrying its message verbatim."""


def _category_from_json(data: dict) -> Category:
    return Category(
        id=data["id"], name=data["name"], pct_me=Decimal(data["pctMe"]), notes=data["notes"]
    )


def _expense_from_json(data: dict) -> Expense:
    return Expense(
        id=data["id"],
        date=date.fromisoformat(data["date"]),
        category_id=data["categoryId"],
        category_name=data["categoryName"],
        amount=Decimal(data["amount"]),
        pct_me=Decimal(data["pctMe"]),
        description=data["description"],
        note=data["note"],
        receipt_filename=data["receiptFilename"],
    )


def _totals_from_json(data: dict) -> Totals:
    return Totals(
        total=Decimal(data["total"]), me=Decimal(data["me"]), insurance=Decimal(data["insurance"])
    )


def _dashboard_from_json(data: dict) -> DashboardTotals:
    return DashboardTotals(
        month=_totals_from_json(data["month"]),
        year=_totals_from_json(data["year"]),
        recent=[_expense_from_json(e) for e in data["recent"]],
    )


def _yearly_report_from_json(data: dict) -> YearlyReport:
    return YearlyReport(
        year=data["year"],
        totals=_totals_from_json(data["totals"]),
        by_category=[
            CategoryBreakdown(
                category_name=row["categoryName"], totals=_totals_from_json(row["totals"])
            )
            for row in data["byCategory"]
        ],
        by_month=[
            MonthBreakdown(month=row["month"], totals=_totals_from_json(row["totals"]))
            for row in data["byMonth"]
        ],
    )


class ApiCareSplitService:
    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self._username = username or os.environ.get("CARESPLIT_API_USERNAME", DEFAULT_USERNAME)
        self._password = password or os.environ.get("CARESPLIT_API_PASSWORD", DEFAULT_PASSWORD)
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=base_url or os.environ.get("CARESPLIT_API_URL", DEFAULT_BASE_URL),
            timeout=10.0,
        )
        self._token: Optional[str] = None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        try:
            return response.json().get("message", response.text)
        except ValueError:
            return response.text or f"HTTP {response.status_code}"

    def _login(self) -> None:
        response = self._client.post(
            "/auth/token", json={"username": self._username, "password": self._password}
        )
        if response.status_code != 200:
            raise ApiError(
                f"Could not log in to the CareSplit API: {self._error_message(response)}"
            )
        self._token = response.json()["accessToken"]

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        if self._token is None:
            self._login()
        headers = {"Authorization": f"Bearer {self._token}"}
        response = self._client.request(method, path, headers=headers, **kwargs)
        if response.status_code == 401:
            # Token expired (or was somehow never valid) — log in once more and retry.
            self._login()
            headers["Authorization"] = f"Bearer {self._token}"
            response = self._client.request(method, path, headers=headers, **kwargs)
        if response.status_code >= 400:
            raise ApiError(self._error_message(response))
        return response

    # -- categories ---------------------------------------------------

    def list_categories(self) -> list[Category]:
        response = self._request("GET", "/categories")
        return [_category_from_json(c) for c in response.json()]

    def get_category(self, category_id: int) -> Category:
        for category in self.list_categories():
            if category.id == category_id:
                return category
        raise ApiError(f"Category {category_id} not found")

    def create_category(self, name: str, pct_me: Decimal, notes: str = "") -> Category:
        response = self._request(
            "POST", "/categories", json={"name": name, "pctMe": str(pct_me), "notes": notes}
        )
        return _category_from_json(response.json())

    def update_category(
        self,
        category_id: int,
        *,
        name: Optional[str] = None,
        pct_me: Optional[Decimal] = None,
        notes: Optional[str] = None,
    ) -> Category:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if pct_me is not None:
            body["pctMe"] = str(pct_me)
        if notes is not None:
            body["notes"] = notes
        response = self._request("PATCH", f"/categories/{category_id}", json=body)
        return _category_from_json(response.json())

    def delete_category(self, category_id: int) -> None:
        self._request("DELETE", f"/categories/{category_id}")

    # -- expenses -------------------------------------------------------

    def list_expenses(self, category_id: Optional[int] = None) -> list[Expense]:
        params = {"categoryId": category_id} if category_id is not None else None
        response = self._request("GET", "/expenses", params=params)
        return [_expense_from_json(e) for e in response.json()]

    def get_expense(self, expense_id: int) -> Expense:
        for expense in self.list_expenses():
            if expense.id == expense_id:
                return expense
        raise ApiError(f"Expense {expense_id} not found")

    def create_expense(
        self,
        *,
        date: date,
        category_id: int,
        amount: Decimal,
        description: str = "",
        pct_me: Optional[Decimal] = None,
        note: str = "",
        receipt_filename: Optional[str] = None,
    ) -> Expense:
        body: dict = {
            "date": date.isoformat(),
            "categoryId": category_id,
            "amount": str(amount),
            "description": description,
            "note": note,
            "receiptFilename": receipt_filename,
        }
        if pct_me is not None:
            body["pctMe"] = str(pct_me)
        response = self._request("POST", "/expenses", json=body)
        return _expense_from_json(response.json())

    def update_expense(
        self,
        expense_id: int,
        *,
        date: Optional[date] = None,
        category_id: Optional[int] = None,
        amount: Optional[Decimal] = None,
        description: Optional[str] = None,
        pct_me: Optional[Decimal] = None,
        note: Optional[str] = None,
        receipt_filename: Optional[str] = None,
    ) -> Expense:
        body: dict = {}
        if date is not None:
            body["date"] = date.isoformat()
        if category_id is not None:
            body["categoryId"] = category_id
        if amount is not None:
            body["amount"] = str(amount)
        if description is not None:
            body["description"] = description
        if pct_me is not None:
            body["pctMe"] = str(pct_me)
        if note is not None:
            body["note"] = note
        if receipt_filename is not None:
            body["receiptFilename"] = receipt_filename
        response = self._request("PATCH", f"/expenses/{expense_id}", json=body)
        return _expense_from_json(response.json())

    def delete_expense(self, expense_id: int) -> None:
        self._request("DELETE", f"/expenses/{expense_id}")

    # -- aggregates -------------------------------------------------------

    def dashboard_totals(self, today: date) -> DashboardTotals:
        response = self._request("GET", "/dashboard", params={"today": today.isoformat()})
        return _dashboard_from_json(response.json())

    def available_years(self) -> list[int]:
        response = self._request("GET", "/reports/years")
        return response.json()

    def yearly_report(self, year: int) -> YearlyReport:
        response = self._request("GET", f"/reports/{year}")
        return _yearly_report_from_json(response.json())
