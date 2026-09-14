from __future__ import annotations

import calendar
from datetime import date

from nicegui import events, ui

from caresplit_backend.services import get_service
from caresplit_frontend.layout import page_layout


@ui.page("/reports")
def reports_page() -> None:
    service = get_service()

    with page_layout("/reports"):
        ui.label("Reports").classes("text-xl font-bold")

        years = service.available_years()
        state = {"year": years[0] if years else date.today().year}

        content = ui.column().classes("w-full gap-3")

        def render() -> None:
            content.clear()
            report = service.yearly_report(state["year"])
            with content:
                with ui.row().classes("w-full gap-3"):
                    with ui.card().classes("flex-1 p-3"):
                        ui.label(f"{state['year']} TOTAL").classes("text-xs text-gray-500")
                        ui.label(f"${report.totals.total:,.2f}").classes("text-xl font-bold")
                    with ui.card().classes("flex-1 p-3"):
                        ui.label("MY SHARE").classes("text-xs text-gray-500")
                        ui.label(f"${report.totals.me:,.2f}").classes(
                            "text-xl font-bold text-emerald-700"
                        )
                    with ui.card().classes("flex-1 p-3"):
                        ui.label("INSURANCE").classes("text-xs text-gray-500")
                        ui.label(f"${report.totals.insurance:,.2f}").classes(
                            "text-xl font-bold text-blue-700"
                        )

                ui.label("By category").classes(
                    "text-xs uppercase text-gray-500 tracking-wide mt-2"
                )
                with ui.card().classes("w-full"):
                    if report.by_category:
                        columns = [
                            {"name": "name", "label": "Category", "field": "name", "align": "left"},
                            {"name": "total", "label": "Total", "field": "total", "align": "right"},
                            {"name": "me", "label": "Me", "field": "me", "align": "right"},
                            {
                                "name": "insurance",
                                "label": "Insurance",
                                "field": "insurance",
                                "align": "right",
                            },
                        ]
                        rows = [
                            {
                                "name": row.category_name,
                                "total": f"${row.totals.total:,.2f}",
                                "me": f"${row.totals.me:,.2f}",
                                "insurance": f"${row.totals.insurance:,.2f}",
                            }
                            for row in report.by_category
                        ]
                        ui.table(columns=columns, rows=rows, row_key="name").classes("w-full")
                    else:
                        ui.label(f"No expenses recorded for {state['year']}.").classes(
                            "text-gray-500 text-center py-6"
                        )

                ui.label("By month").classes(
                    "text-xs uppercase text-gray-500 tracking-wide mt-2"
                )
                with ui.card().classes("w-full"):
                    if report.by_month:
                        columns = [
                            {"name": "month", "label": "Month", "field": "month", "align": "left"},
                            {"name": "total", "label": "Total", "field": "total", "align": "right"},
                            {"name": "me", "label": "Me", "field": "me", "align": "right"},
                            {
                                "name": "insurance",
                                "label": "Insurance",
                                "field": "insurance",
                                "align": "right",
                            },
                        ]
                        rows = [
                            {
                                "month": calendar.month_name[row.month],
                                "total": f"${row.totals.total:,.2f}",
                                "me": f"${row.totals.me:,.2f}",
                                "insurance": f"${row.totals.insurance:,.2f}",
                            }
                            for row in report.by_month
                        ]
                        ui.table(columns=columns, rows=rows, row_key="month").classes("w-full")
                    else:
                        ui.label(f"No expenses recorded for {state['year']}.").classes(
                            "text-gray-500 text-center py-6"
                        )

        if years:

            def on_year_change(e: events.ValueChangeEventArguments) -> None:
                state["year"] = e.value
                render()

            ui.select(years, value=state["year"], on_change=on_year_change).classes("w-32")
        else:
            ui.label("No expenses recorded yet.").classes("text-gray-500")

        render()
