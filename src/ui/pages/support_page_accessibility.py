"""Accessibility helpers for the Support page."""

from __future__ import annotations

from ui.accessibility import set_control_accessibility


def _set_card_and_button_accessibility(card, *, name: str, description: str) -> None:
    set_control_accessibility(card, name=name, description=description)
    button = getattr(card, "button", None)
    if button is not None:
        set_control_accessibility(button, name=name, description=description)


def apply_support_page_accessibility(page) -> None:
    """Задаёт понятные имена карточкам страницы «Поддержка»."""

    tr_fn = page._tr
    if page._support_card is not None:
        _set_card_and_button_accessibility(
            page._support_card,
            name=tr_fn("page.support.discussions.accessible_name", "Открыть GitHub Discussions"),
            description=tr_fn(
                "page.support.discussions.description",
                "Основной канал поддержки. Здесь можно задать вопрос, описать проблему и приложить нужные материалы вручную.",
            ),
        )
    if page._tg_card is not None:
        _set_card_and_button_accessibility(
            page._tg_card,
            name=tr_fn("page.support.channel.telegram.accessible_name", "Открыть Telegram"),
            description=tr_fn("page.support.channel.telegram.desc", "Быстрые вопросы и общение с сообществом"),
        )
    if page._dc_card is not None:
        _set_card_and_button_accessibility(
            page._dc_card,
            name=tr_fn("page.support.channel.discord.accessible_name", "Открыть Discord"),
            description=tr_fn("page.support.channel.discord.desc", "Обсуждение и живое общение"),
        )


__all__ = ["apply_support_page_accessibility"]
