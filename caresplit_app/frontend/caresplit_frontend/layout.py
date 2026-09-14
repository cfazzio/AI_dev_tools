"""Shared header/nav wrapper used by every page."""

from __future__ import annotations

from contextlib import contextmanager

from nicegui import ui

NAV_ITEMS = [
    ("Home", "/"),
    ("Expenses", "/expenses"),
    ("Categories", "/categories"),
    ("Reports", "/reports"),
]


@contextmanager
def page_layout(active_path: str):
    """Render the sticky header + nav, then yield a content column to fill in."""
    with ui.header().classes("items-center justify-between py-2 bg-emerald-700 text-white"):
        ui.label("CareSplit").classes("text-lg font-bold")

    with ui.row().classes("w-full gap-0 bg-emerald-800 no-wrap overflow-x-auto"):
        for label, path in NAV_ITEMS:
            classes = "text-white px-4 py-2 no-underline text-center flex-1"
            if path == active_path:
                classes += " font-bold border-b-2 border-white"
            ui.link(label, path).classes(classes)

    with ui.column().classes("w-full max-w-2xl mx-auto p-4 gap-3") as content:
        yield content
