from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPixmap

from ui.theme import get_cached_qta_pixmap


_INITIALS_PREFIX = "profile-initials:"


def profile_icon_pixmap(icon_name: str, *, color: str, size: int, theme_name: str = "") -> QPixmap:
    name = str(icon_name or "").strip()
    if name.startswith(_INITIALS_PREFIX):
        return _initials_pixmap(
            name.removeprefix(_INITIALS_PREFIX).strip() or "P",
            color=str(color or "#3B82F6"),
            size=size,
        )
    return get_cached_qta_pixmap(name, color=color, size=size, theme_name=theme_name)


def _initials_pixmap(initials: str, *, color: str, size: int) -> QPixmap:
    safe_size = max(12, int(size or 18))
    canvas = QPixmap(safe_size, safe_size)
    canvas.fill(Qt.GlobalColor.transparent)

    bg = QColor(str(color or "#3B82F6"))
    if not bg.isValid():
        bg = QColor("#3B82F6")

    painter = QPainter(canvas)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(0, 0, safe_size, safe_size, max(4, safe_size // 4), max(4, safe_size // 4))

        font = QFont()
        font.setBold(True)
        font.setPixelSize(max(8, int(safe_size * 0.48)))
        painter.setFont(font)
        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.drawText(canvas.rect(), Qt.AlignmentFlag.AlignCenter, str(initials or "P")[:2].upper())
    finally:
        painter.end()
    return canvas


__all__ = ["profile_icon_pixmap"]
