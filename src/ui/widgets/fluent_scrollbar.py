from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractScrollArea
from qfluentwidgets import ScrollBar, ScrollBarHandleDisplayMode


@dataclass(frozen=True)
class FluentScrollBars:
    vertical: ScrollBar | None = None
    horizontal: ScrollBar | None = None


def install_fluent_scrollbars(
    widget: QAbstractScrollArea,
    *,
    vertical: bool = True,
    horizontal: bool = False,
    handle_mode: ScrollBarHandleDisplayMode = ScrollBarHandleDisplayMode.ALWAYS,
) -> FluentScrollBars:
    """Ставит библиотечный scrollbar qfluentwidgets на обычный Qt-список."""

    current = getattr(widget, "_zapret_fluent_scrollbars", None)
    if isinstance(current, FluentScrollBars):
        return current

    vertical_bar = None
    horizontal_bar = None
    if vertical:
        vertical_bar = ScrollBar(Qt.Orientation.Vertical, widget)
        vertical_bar.setHandleDisplayMode(handle_mode)
    if horizontal:
        horizontal_bar = ScrollBar(Qt.Orientation.Horizontal, widget)
        horizontal_bar.setHandleDisplayMode(handle_mode)

    bars = FluentScrollBars(vertical=vertical_bar, horizontal=horizontal_bar)
    setattr(widget, "_zapret_fluent_scrollbars", bars)
    return bars


__all__ = ["FluentScrollBars", "install_fluent_scrollbars"]
