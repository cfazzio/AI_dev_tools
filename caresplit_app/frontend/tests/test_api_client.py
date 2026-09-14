"""Integration tests for ApiCareSplitService against the real FastAPI app.

httpx's ASGITransport only supports its *async* client, but
ApiCareSplitService is deliberately synchronous (it's called directly from
sync NiceGUI page functions, same as the mock) — so instead of ASGITransport,
this runs the real app on a real (ephemeral, localhost, in-process)
uvicorn server for the module, via plain synchronous HTTP, exactly like
production. Each test still gets a fresh, freshly-seeded backend store:
the autouse `_reset_backend_api_state` fixture in conftest.py resets the
app's singletons before every test regardless of how long the server
thread has been running.
"""

from __future__ import annotations

import threading
import time
from datetime import date
from decimal import Decimal

import pytest
import uvicorn

from caresplit_backend.api.main import app
from caresplit_backend.api.store import DEMO_PASSWORD, DEMO_USERNAME
from caresplit_backend.services.errors import CareSplitError

from caresplit_frontend.api_client import ApiCareSplitService


class _ThreadedServer(uvicorn.Server):
    def install_signal_handlers(self) -> None:
        pass  # only valid in the main thread; we're not running in it


@pytest.fixture(scope="module")
def live_server_url():
    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning")
    server = _ThreadedServer(config=config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.01)
    port = server.servers[0].sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture
def service(live_server_url: str):
    svc = ApiCareSplitService(
        base_url=live_server_url, username=DEMO_USERNAME, password=DEMO_PASSWORD
    )
    yield svc
    svc.close()


def test_list_categories_returns_the_seeded_starter_set(service: ApiCareSplitService) -> None:
    names = {c.name for c in service.list_categories()}
    assert "Medical / doctor visits" in names
    assert "In-home care / caregiving" in names


def test_create_expense_round_trips_amount_and_date_through_the_wire(
    service: ApiCareSplitService,
) -> None:
    category = service.list_categories()[0]
    created = service.create_expense(
        date=date(2026, 3, 7), category_id=category.id, amount=Decimal("42.50")
    )
    assert created.amount == Decimal("42.50")
    assert created.date == date(2026, 3, 7)
    assert created.category_id == category.id

    fetched = next(e for e in service.list_expenses() if e.id == created.id)
    assert fetched.amount == Decimal("42.50")
    assert fetched.date == date(2026, 3, 7)


def test_expense_split_defaults_from_category(service: ApiCareSplitService) -> None:
    medical = next(c for c in service.list_categories() if c.name == "Medical / doctor visits")
    expense = service.create_expense(
        date=date(2026, 1, 1), category_id=medical.id, amount=Decimal("100.00")
    )
    assert expense.pct_me == medical.pct_me
    assert expense.amount_me == Decimal("20.00")


def test_update_and_delete_expense(service: ApiCareSplitService) -> None:
    category = service.list_categories()[0]
    expense = service.create_expense(
        date=date(2026, 1, 1), category_id=category.id, amount=Decimal("10.00")
    )

    updated = service.update_expense(expense.id, amount=Decimal("25.00"))
    assert updated.amount == Decimal("25.00")

    service.delete_expense(expense.id)
    assert expense.id not in {e.id for e in service.list_expenses()}


def test_create_duplicate_category_raises_care_split_error(
    service: ApiCareSplitService,
) -> None:
    existing = service.list_categories()[0]
    with pytest.raises(CareSplitError):
        service.create_category(existing.name, Decimal("50"))


def test_delete_category_in_use_raises_care_split_error(service: ApiCareSplitService) -> None:
    category = service.list_categories()[0]
    service.create_expense(date=date(2026, 1, 1), category_id=category.id, amount=Decimal("10"))
    with pytest.raises(CareSplitError):
        service.delete_category(category.id)


def test_get_category_and_get_expense_are_synthesized_client_side(
    service: ApiCareSplitService,
) -> None:
    # There's no GET /categories/{id} or /expenses/{id} in the API (no
    # frontend page ever needed them) — the client fakes both from the
    # list endpoints so it's still a complete CareSplitService.
    category = service.list_categories()[0]
    assert service.get_category(category.id).id == category.id

    expense = service.create_expense(
        date=date(2026, 1, 1), category_id=category.id, amount=Decimal("5.00")
    )
    assert service.get_expense(expense.id).id == expense.id

    with pytest.raises(CareSplitError):
        service.get_category(999999)


def test_dashboard_and_yearly_report_round_trip(service: ApiCareSplitService) -> None:
    today = date.today()
    totals = service.dashboard_totals(today)
    assert totals.year.total >= Decimal("0.00")

    years = service.available_years()
    assert years  # store.py seeds demo expenses, so this should be non-empty
    report = service.yearly_report(years[0])
    assert report.totals.total >= Decimal("0.00")


def test_wrong_password_raises_care_split_error(live_server_url: str) -> None:
    service = ApiCareSplitService(
        base_url=live_server_url, username=DEMO_USERNAME, password="wrong-password"
    )
    with pytest.raises(CareSplitError):
        service.list_categories()
    service.close()


def test_expired_token_triggers_an_automatic_relogin(service: ApiCareSplitService) -> None:
    from datetime import datetime, timedelta, timezone

    from caresplit_backend.api.auth import get_token_store

    service.list_categories()  # force the initial login
    token_store = get_token_store()
    token_store._tokens[service._token].expires_at = datetime.now(timezone.utc) - timedelta(
        seconds=1
    )

    # Should transparently log in again and succeed, not raise.
    categories = service.list_categories()
    assert categories
