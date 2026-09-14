from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

from nicegui import events, ui

from caresplit_backend.domain import Expense
from caresplit_backend.services import get_service
from caresplit_backend.services.errors import CareSplitError
from caresplit_frontend.components import split_pill
from caresplit_frontend.layout import page_layout
from caresplit_frontend.receipts import save_receipt


@ui.page("/expenses")
def expenses_page() -> None:
    service = get_service()
    state: dict = {"category_filter": None}

    with page_layout("/expenses"):
        ui.label("Expenses").classes("text-xl font-bold")

        categories = service.list_categories()
        category_options = {c.id: c.name for c in categories}

        totals_row = ui.row().classes("w-full gap-3")
        list_container = ui.column().classes("w-full gap-2")

        def refresh() -> None:
            expenses = service.list_expenses(state["category_filter"])

            totals_row.clear()
            with totals_row:
                total = sum((e.amount for e in expenses), Decimal("0.00"))
                me = sum((e.amount_me for e in expenses), Decimal("0.00"))
                with ui.card().classes("flex-1 p-3"):
                    ui.label("TOTAL").classes("text-xs text-gray-500")
                    ui.label(f"${total:,.2f}").classes("text-xl font-bold")
                with ui.card().classes("flex-1 p-3"):
                    ui.label("MY SHARE").classes("text-xs text-gray-500")
                    ui.label(f"${me:,.2f}").classes("text-xl font-bold text-emerald-700")
                with ui.card().classes("flex-1 p-3"):
                    ui.label("INSURANCE").classes("text-xs text-gray-500")
                    ui.label(f"${total - me:,.2f}").classes("text-xl font-bold text-blue-700")

            list_container.clear()
            with list_container:
                if not expenses:
                    with ui.card().classes("w-full"):
                        ui.label("No expenses match this filter.").classes(
                            "text-gray-500 text-center py-6"
                        )
                for expense in expenses:
                    with ui.card().classes("w-full cursor-pointer hover:bg-gray-50").on(
                        "click", lambda _, expense=expense: open_form(expense)
                    ).mark(f"expense-row-{expense.id}"):
                        with ui.row().classes("w-full justify-between items-center"):
                            with ui.column().classes("gap-0"):
                                ui.label(expense.description or expense.category_name).classes(
                                    "font-semibold"
                                )
                                label = f"{expense.date} · {expense.category_name}"
                                if expense.receipt_filename:
                                    label += " · 📎"
                                ui.label(label).classes("text-xs text-gray-500")
                                split_pill(expense.pct_me, expense.pct_insurance)
                            ui.label(f"${expense.amount:,.2f}").classes("font-bold")

        def open_form(expense: Optional[Expense] = None) -> None:
            receipt_state = {"filename": expense.receipt_filename if expense else None}

            with ui.dialog() as dialog, ui.card().classes("w-full max-w-md gap-2"):
                ui.label("Edit expense" if expense else "Add expense").classes(
                    "text-lg font-bold"
                )
                date_input = ui.input(
                    "Date", value=str(expense.date if expense else date.today())
                ).props("type=date").classes("w-full").mark("expense-date")
                category_select = ui.select(
                    category_options,
                    label="Category",
                    value=expense.category_id if expense else (
                        categories[0].id if categories else None
                    ),
                ).classes("w-full").mark("expense-category")
                amount_input = ui.number(
                    "Amount ($)",
                    value=float(expense.amount) if expense else None,
                    format="%.2f",
                    min=0,
                ).classes("w-full").mark("expense-amount")
                description_input = ui.input(
                    "Description", value=expense.description if expense else ""
                ).classes("w-full").mark("expense-description")
                pct_input = ui.number(
                    "My share % (blank = category default)",
                    value=float(expense.pct_me) if expense else None,
                    min=0,
                    max=100,
                ).classes("w-full").mark("expense-pct")
                note_input = ui.textarea(
                    "Note", value=expense.note if expense else ""
                ).classes("w-full").mark("expense-note")

                receipt_label = ui.label(
                    f"Current receipt: {receipt_state['filename']}"
                    if receipt_state["filename"]
                    else ""
                ).classes("text-xs text-gray-500")

                async def on_upload(e: events.UploadEventArguments) -> None:
                    filename = await save_receipt(e.file)
                    receipt_state["filename"] = filename
                    receipt_label.text = f"Attached: {e.file.name}"
                    ui.notify("Receipt attached", type="positive")

                ui.upload(
                    label="Attach receipt (optional)", on_upload=on_upload, auto_upload=True
                ).props('accept=".jpg,.jpeg,.png,.pdf"').classes("w-full")

                error_label = ui.label("").classes("text-red-600 text-sm")

                def save() -> None:
                    if not category_select.value:
                        error_label.text = "Choose a category."
                        return
                    try:
                        expense_date = date.fromisoformat(date_input.value)
                    except (TypeError, ValueError):
                        error_label.text = "Enter a valid date."
                        return
                    if amount_input.value is None:
                        error_label.text = "Enter an amount."
                        return
                    try:
                        amount = Decimal(str(amount_input.value))
                        pct_me = (
                            Decimal(str(pct_input.value))
                            if pct_input.value is not None
                            else None
                        )
                    except InvalidOperation:
                        error_label.text = "Amount and split must be numbers."
                        return

                    try:
                        kwargs = dict(
                            date=expense_date,
                            category_id=category_select.value,
                            amount=amount,
                            description=description_input.value or "",
                            pct_me=pct_me,
                            note=note_input.value or "",
                            receipt_filename=receipt_state["filename"],
                        )
                        if expense:
                            service.update_expense(expense.id, **kwargs)
                        else:
                            service.create_expense(**kwargs)
                    except CareSplitError as exc:
                        error_label.text = str(exc)
                        return

                    dialog.close()
                    refresh()

                def delete() -> None:
                    service.delete_expense(expense.id)
                    dialog.close()
                    refresh()

                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    if expense:
                        ui.button("Delete", on_click=delete).props("flat color=red").mark(
                            "expense-delete"
                        )
                    ui.button("Cancel", on_click=dialog.close).props("flat")
                    ui.button("Save", on_click=save).mark("expense-save")

            dialog.open()

        with ui.row().classes("w-full items-center gap-2"):
            def on_filter_change(e: events.ValueChangeEventArguments) -> None:
                state["category_filter"] = e.value
                refresh()

            ui.select(
                {None: "All categories", **category_options},
                value=None,
                on_change=on_filter_change,
            ).classes("flex-1").mark("expense-filter")
            ui.button("Add expense", icon="add", on_click=lambda: open_form(None)).mark(
                "expense-add"
            )

        refresh()
