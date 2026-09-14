from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from nicegui import ui

from caresplit_backend.domain import Category
from caresplit_backend.services import get_service
from caresplit_backend.services.errors import CareSplitError
from caresplit_frontend.components import format_pct
from caresplit_frontend.layout import page_layout


@ui.page("/categories")
def categories_page() -> None:
    service = get_service()

    with page_layout("/categories"):
        ui.label("Categories").classes("text-xl font-bold")
        ui.label(
            "Each category sets the default split applied when you log an expense "
            "in it. You can still override the split on an individual expense."
        ).classes("text-sm text-gray-500")

        list_container = ui.column().classes("w-full gap-2")

        def refresh() -> None:
            list_container.clear()
            categories = service.list_categories()
            with list_container:
                if not categories:
                    with ui.card().classes("w-full"):
                        ui.label("No categories yet.").classes(
                            "text-gray-500 text-center py-6"
                        )
                for category in categories:
                    with ui.card().classes("w-full cursor-pointer hover:bg-gray-50").on(
                        "click", lambda _, category=category: open_form(category)
                    ).mark(f"category-row-{category.id}"):
                        with ui.row().classes("w-full justify-between items-center"):
                            ui.label(category.name).classes("font-semibold")
                            ui.label(
                                f"{format_pct(category.pct_me)}% me / "
                                f"{format_pct(category.pct_insurance)}% insurance"
                            ).classes("text-sm text-gray-600")

        def open_form(category: Optional[Category] = None) -> None:
            with ui.dialog() as dialog, ui.card().classes("w-full max-w-md gap-2"):
                ui.label("Edit category" if category else "Add category").classes(
                    "text-lg font-bold"
                )
                name_input = ui.input(
                    "Name", value=category.name if category else ""
                ).classes("w-full").mark("category-name")
                pct_input = ui.number(
                    "My share (%)",
                    value=float(category.pct_me) if category else 100,
                    min=0,
                    max=100,
                ).classes("w-full").mark("category-pct")
                notes_input = ui.textarea(
                    "Notes", value=category.notes if category else ""
                ).classes("w-full")
                error_label = ui.label("").classes("text-red-600 text-sm")

                def save() -> None:
                    if not name_input.value or not name_input.value.strip():
                        error_label.text = "Enter a name."
                        return
                    if pct_input.value is None:
                        error_label.text = "Enter a share percentage."
                        return
                    try:
                        pct_me = Decimal(str(pct_input.value))
                    except InvalidOperation:
                        error_label.text = "Share must be a number."
                        return
                    try:
                        if category:
                            service.update_category(
                                category.id,
                                name=name_input.value,
                                pct_me=pct_me,
                                notes=notes_input.value or "",
                            )
                        else:
                            service.create_category(
                                name_input.value, pct_me, notes_input.value or ""
                            )
                    except CareSplitError as exc:
                        error_label.text = str(exc)
                        return
                    dialog.close()
                    refresh()

                def delete() -> None:
                    try:
                        service.delete_category(category.id)
                    except CareSplitError as exc:
                        error_label.text = str(exc)
                        return
                    dialog.close()
                    refresh()

                with ui.row().classes("w-full justify-end gap-2 mt-2"):
                    if category:
                        ui.button("Delete", on_click=delete).props("flat color=red").mark(
                            "category-delete"
                        )
                    ui.button("Cancel", on_click=dialog.close).props("flat")
                    ui.button("Save", on_click=save).mark("category-save")

            dialog.open()

        ui.button("Add category", icon="add", on_click=lambda: open_form(None)).mark(
            "category-add"
        )
        refresh()
