"""The API's in-memory store: expense data plus user credentials.

Wraps the existing, already-tested MockCareSplitService for expense data
(same seeded starter categories, same split/aggregation logic) rather than
reimplementing it — this module's own job is just the pieces that service
never had: user records and demo expenses to seed on startup so the
frontend has something to show immediately.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from caresplit_backend.api.auth import hash_password
from caresplit_backend.services.mock_service import MockCareSplitService

DEMO_USERNAME = "cindy"
DEMO_PASSWORD = "caresplit-demo"  # local/dev seed only — not for a real deployment


@dataclass
class UserRecord:
    username: str
    hashed_password: str


class Store:
    def __init__(self) -> None:
        self.expenses = MockCareSplitService()
        self.users: dict[str, UserRecord] = {}


def _shift_month(d: date, months: int) -> date:
    """d, moved back `months` whole months, clamped to day 28 to dodge overflow."""
    month_index = d.month - 1 - months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, min(d.day, 28))


def seed_users(store: Store) -> None:
    store.users[DEMO_USERNAME] = UserRecord(
        username=DEMO_USERNAME, hashed_password=hash_password(DEMO_PASSWORD)
    )


def seed_demo_expenses(store: Store) -> None:
    """A handful of realistic expenses so the dashboard/reports aren't empty on first run."""
    service = store.expenses
    categories = {c.name: c.id for c in service.list_categories()}
    today = date.today()
    this_month = date(today.year, today.month, 1)
    last_month = _shift_month(today, 1)
    two_months_ago = _shift_month(today, 2)
    last_year = date(today.year - 1, today.month, 10)

    seed_expenses = [
        (this_month.replace(day=3), "Medical / doctor visits", "120.00", "Cardiology follow-up"),
        (this_month.replace(day=10), "Prescriptions", "48.25", "Monthly refill"),
        (this_month.replace(day=14), "Transportation", "22.00", "Round trip to clinic"),
        (last_month.replace(day=5), "In-home care / caregiving", "600.00", "Weekly aide, 3 visits"),
        (last_month.replace(day=18), "Medical equipment & supplies", "89.99", "Shower chair"),
        (two_months_ago.replace(day=9), "Medical / doctor visits", "75.00", "PCP checkup"),
        (two_months_ago.replace(day=21), "Prescriptions", "31.10", "Monthly refill"),
        (last_year, "In-home care / caregiving", "550.00", "Weekly aide, 3 visits"),
    ]

    for expense_date, category_name, amount, description in seed_expenses:
        service.create_expense(
            date=expense_date,
            category_id=categories[category_name],
            amount=Decimal(amount),
            description=description,
        )


_store = Store()
seed_users(_store)
seed_demo_expenses(_store)


def get_store() -> Store:
    return _store


def reset_store() -> None:
    """Replace the singleton with a freshly-seeded one. Mainly useful for tests."""
    global _store
    _store = Store()
    seed_users(_store)
    seed_demo_expenses(_store)
