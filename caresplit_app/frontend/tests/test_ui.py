"""End-to-end UI tests using NiceGUI's headless user simulation.

These exercise the pages against the mock service (no real backend
involved) to catch template/wiring mistakes that unit tests of the
service layer alone wouldn't.
"""

from nicegui.testing import User


async def test_dashboard_shows_empty_state(user: User) -> None:
    await user.open("/")
    await user.should_see("Dad's care expenses")
    await user.should_see("No expenses yet")


async def test_nav_links_to_every_page(user: User) -> None:
    await user.open("/")
    for label in ["Home", "Expenses", "Categories", "Reports"]:
        await user.should_see(label)


async def test_categories_page_lists_starter_categories(user: User) -> None:
    await user.open("/categories")
    await user.should_see("Medical / doctor visits")
    await user.should_see("In-home care / caregiving")


async def test_add_category_via_ui(user: User) -> None:
    await user.open("/categories")
    user.find(marker="category-add").click()
    user.find(marker="category-name").type("Dental")
    user.find(marker="category-pct").clear().type("60")
    user.find(marker="category-save").click()
    await user.should_see("Dental")
    await user.should_see("60% me")


async def test_add_category_rejects_duplicate_name(user: User) -> None:
    await user.open("/categories")
    user.find(marker="category-add").click()
    user.find(marker="category-name").type("Medical / doctor visits")
    user.find(marker="category-pct").clear().type("50")
    user.find(marker="category-save").click()
    await user.should_see("already exists")


async def test_expenses_page_empty_state(user: User) -> None:
    await user.open("/expenses")
    await user.should_see("No expenses match this filter")


async def test_add_expense_dialog_opens_with_fields(user: User) -> None:
    await user.open("/expenses")
    user.find(marker="expense-add").click()
    await user.should_see("Add expense")
    user.find(marker="expense-amount")
    user.find(marker="expense-category")
    user.find(marker="expense-date")


async def test_reports_page_handles_no_data(user: User) -> None:
    await user.open("/reports")
    await user.should_see("No expenses recorded yet")


async def test_category_delete_blocked_when_in_use(user: User) -> None:
    from datetime import date
    from decimal import Decimal

    from caresplit_backend.services import get_service

    service = get_service()
    category = service.list_categories()[0]
    service.create_expense(date=date(2026, 1, 1), category_id=category.id, amount=Decimal("10"))

    await user.open("/categories")
    user.find(marker=f"category-row-{category.id}").click()
    user.find(marker="category-delete").click()
    await user.should_see("still has")
