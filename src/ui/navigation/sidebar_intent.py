from __future__ import annotations

from dataclasses import dataclass


DEFAULT_EXPAND_THRESHOLD = 700

_EXPANDED_MODE = "EXPAND"
_OVERLAY_MODE = "MENU"
_COLLAPSED_MODES = frozenset({"COMPACT", "MINIMAL"})


def normalize_display_mode_name(display_mode) -> str:
    return str(getattr(display_mode, "name", display_mode) or "").upper()


@dataclass
class SidebarIntentController:
    """Владелец намерения пользователя «сайдбар развёрнут».

    qfluentwidgets меняет displayMode и по действиям пользователя, и сам —
    responsive-сворачивание при сужении окна ниже minimumExpandWidth и
    MENU-оверлей на узких окнах. Персистится только намерение пользователя,
    поэтому события классифицируются по ширине окна на момент сигнала:
    ниже порога закреплённый EXPAND недоступен, значит смена режима там
    не может быть осознанным выбором «свернуть навсегда».
    """

    intent: bool
    last_saved: bool | None = None
    applying: bool = False

    def classify_display_mode_change(
        self,
        display_mode,
        *,
        window_width: int,
        threshold: int = DEFAULT_EXPAND_THRESHOLD,
    ) -> bool | None:
        """Возвращает новое намерение для сохранения или None (игнорировать)."""
        if self.applying:
            return None

        mode = normalize_display_mode_name(display_mode)
        wide = int(window_width) >= int(threshold)

        if mode == _EXPANDED_MODE and wide:
            new_intent = True
        elif mode in _COLLAPSED_MODES and wide:
            new_intent = False
        else:
            # MENU-оверлей и любые переходы на узком окне — responsive-механика.
            return None

        if new_intent == self.intent:
            return None

        self.intent = new_intent
        return new_intent

    def should_reapply_expand(
        self,
        *,
        window_width: int,
        is_collapsed: bool,
        threshold: int = DEFAULT_EXPAND_THRESHOLD,
    ) -> bool:
        """Нужно ли развернуть сайдбар обратно после расширения окна."""
        if self.applying:
            return False
        return bool(self.intent) and bool(is_collapsed) and int(window_width) >= int(threshold)

    def mark_saved(self, value: bool) -> None:
        self.last_saved = bool(value)

    def pending_flush(self) -> bool | None:
        """Намерение, которое ещё не записано на диск (для flush при выходе)."""
        if self.last_saved is None or bool(self.last_saved) != bool(self.intent):
            return bool(self.intent)
        return None


__all__ = [
    "DEFAULT_EXPAND_THRESHOLD",
    "SidebarIntentController",
    "normalize_display_mode_name",
]
