"""Small reusable UI pieces shared across pages."""

from __future__ import annotations

from decimal import Decimal

from nicegui import ui


def stat_card(label: str, value: Decimal, color: str = "") -> None:
    with ui.card().classes("flex-1 min-w-[9rem] p-3"):
        ui.label(label.upper()).classes("text-xs text-gray-500 tracking-wide")
        ui.label(f"${value:,.2f}").classes(f"text-2xl font-bold {color}")


def format_pct(value: Decimal) -> str:
    """Render a percentage without spurious trailing zeros (60.0 -> "60").

    Decimal's ``g`` format keeps whatever decimal places the value happens
    to carry (e.g. a value round-tripped through a float input often ends
    up as Decimal("60.0")), and Decimal.normalize() turns whole numbers
    like 100 into exponential form ("1E+2"). Formatting to a fixed
    precision and trimming trailing zeros as a string avoids both.
    """
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text or "0"


def split_pill(pct_me: Decimal, pct_insurance: Decimal) -> None:
    ui.badge(f"{format_pct(pct_me)}% me / {format_pct(pct_insurance)}% insurance").classes(
        "bg-gray-100 text-gray-700 normal-case"
    )
