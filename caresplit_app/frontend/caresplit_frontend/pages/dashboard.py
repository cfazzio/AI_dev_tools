from __future__ import annotations

from datetime import date

from nicegui import ui

from caresplit_frontend.services import get_service
from caresplit_frontend.components import split_pill, stat_card
from caresplit_frontend.layout import page_layout


@ui.page("/")
def dashboard_page() -> None:
    service = get_service()
    today = date.today()
    data = service.dashboard_totals(today)

    with page_layout("/"):
        ui.label("Dad's care expenses").classes("text-xl font-bold")

        ui.label(f"This month ({today:%B %Y})").classes(
            "text-xs uppercase text-gray-500 tracking-wide mt-2"
        )
        with ui.row().classes("w-full gap-3"):
            stat_card("Total", data.month.total)
            stat_card("My share", data.month.me, "text-emerald-700")
            stat_card("Insurance share", data.month.insurance, "text-blue-700")

        ui.label(f"Year to date ({today.year})").classes(
            "text-xs uppercase text-gray-500 tracking-wide mt-2"
        )
        with ui.row().classes("w-full gap-3"):
            stat_card("Total", data.year.total)
            stat_card("My share", data.year.me, "text-emerald-700")
            stat_card("Insurance share", data.year.insurance, "text-blue-700")

        ui.label("Recent expenses").classes(
            "text-xs uppercase text-gray-500 tracking-wide mt-2"
        )
        with ui.card().classes("w-full"):
            if data.recent:
                for expense in data.recent:
                    with ui.row().classes(
                        "w-full justify-between items-center border-b py-2 last:border-b-0"
                    ):
                        with ui.column().classes("gap-0"):
                            ui.label(expense.description or expense.category_name).classes(
                                "font-semibold"
                            )
                            ui.label(f"{expense.date} · {expense.category_name}").classes(
                                "text-xs text-gray-500"
                            )
                            split_pill(expense.pct_me, expense.pct_insurance)
                        ui.label(f"${expense.amount:,.2f}").classes("font-bold")
            else:
                ui.label("No expenses yet — tap Add expense to log the first one.").classes(
                    "text-gray-500 text-center py-6"
                )

        ui.button(
            "Add expense", icon="add", on_click=lambda: ui.navigate.to("/expenses")
        ).classes("mt-2")
