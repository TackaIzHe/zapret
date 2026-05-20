"""Общий workflow действий для страницы пользовательских preset-ов."""

from __future__ import annotations

from qfluentwidgets import FluentIcon


def _tr_key(tr_prefix: str, suffix: str) -> str:
    return f"{tr_prefix}.{suffix}"


def show_inline_action_create(
    *,
    dialog_cls,
    parent_window,
    language: str,
    actions_api,
    runtime_service,
    log_fn,
    info_bar_cls,
    tr_fn,
    tr_prefix: str,
) -> None:
    dlg = dialog_cls([], parent_window, language=language)
    if not dlg.exec():
        return

    name = dlg.nameEdit.text().strip()
    from_current = getattr(dlg, "_source", "current") == "current"

    try:
        result = actions_api.create_preset(name=name, from_current=from_current)
        if result.structure_changed:
            runtime_service.mark_presets_structure_changed()
        log_fn(result.log_message, result.log_level)
    except Exception as exc:
        log_fn(f"Ошибка создания пресета: {exc}", "ERROR")
        info_bar_cls.error(
            title=tr_fn("common.error.title", "Ошибка"),
            content=tr_fn(_tr_key(tr_prefix, "error.generic"), "Ошибка: {error}", error=exc),
            parent=parent_window,
        )


def show_inline_action_rename(
    *,
    current_name: str,
    resolve_display_name_fn,
    is_builtin_preset_file_fn,
    dialog_cls,
    parent_window,
    language: str,
    actions_api,
    runtime_service,
    log_fn,
    info_bar_cls,
    tr_fn,
    tr_prefix: str,
) -> None:
    display_name = resolve_display_name_fn(current_name)
    if is_builtin_preset_file_fn(current_name):
        info_bar_cls.warning(
            title=tr_fn("common.error.title", "Ошибка"),
            content="Встроенный пресет нельзя переименовать. Можно создать копию и работать уже с ней.",
            parent=parent_window,
        )
        return

    dlg = dialog_cls(display_name, [], parent_window, language=language)
    if not dlg.exec():
        return

    new_name = dlg.nameEdit.text().strip()
    if not new_name or new_name == display_name:
        return

    try:
        result = actions_api.rename_preset(current_name=current_name, new_name=new_name)
        if result.structure_changed:
            runtime_service.mark_presets_structure_changed()
        log_fn(result.log_message, result.log_level)
    except Exception as exc:
        log_fn(f"Ошибка переименования пресета: {exc}", "ERROR")
        info_bar_cls.error(
            title=tr_fn("common.error.title", "Ошибка"),
            content=tr_fn(_tr_key(tr_prefix, "error.generic"), "Ошибка: {error}", error=exc),
            parent=parent_window,
        )


def import_preset_action(
    *,
    file_dialog_cls,
    parent,
    parent_window,
    tr_fn,
    actions_api,
    runtime_service,
    log_fn,
    info_bar_cls,
    tr_prefix: str,
) -> None:
    file_path, _ = file_dialog_cls.getOpenFileName(
        parent,
        tr_fn(_tr_key(tr_prefix, "file_dialog.import_title"), "Импортировать пресет"),
        "",
        "Файлы пресетов (*.txt);;Все файлы (*.*)",
    )
    if not file_path:
        return

    try:
        result = actions_api.import_preset_from_file(file_path=file_path)
        if result.structure_changed:
            runtime_service.mark_presets_structure_changed()
        log_fn(result.log_message, result.log_level)
        if result.infobar_level == "warning":
            info_bar_cls.warning(
                title=result.infobar_title,
                content=result.infobar_content,
                parent=parent_window,
            )
        else:
            info_bar_cls.success(
                title=result.infobar_title,
                content=result.infobar_content,
                parent=parent_window,
            )
    except Exception as exc:
        log_fn(f"Ошибка импорта пресета: {exc}", "ERROR")
        info_bar_cls.error(
            title=tr_fn("common.error.title", "Ошибка"),
            content=tr_fn(
                _tr_key(tr_prefix, "error.import_exception"),
                "Не удалось импортировать пресет: {error}",
                error=exc,
            ),
            parent=parent_window,
        )


def run_reset_all_presets_action(
    *,
    dialog_cls,
    parent_window,
    language: str,
    actions_api,
    runtime_service,
    log_fn,
    info_bar_cls,
    tr_fn,
    show_result_fn,
    is_visible: bool,
    refresh_view_fn,
    set_bulk_reset_running_fn,
    tr_prefix: str,
) -> None:
    dlg = dialog_cls(parent_window, language=language)
    if not dlg.exec():
        return

    set_bulk_reset_running_fn(True)
    try:
        result = actions_api.reset_all_presets()
        if result.structure_changed:
            runtime_service.mark_presets_structure_changed()
        log_fn(result.log_message, result.log_level)
        show_result_fn(result.success_count, result.total_count, result.failed_count)
    except Exception as exc:
        log_fn(f"Ошибка массового восстановления пресетов: {exc}", "ERROR")
        info_bar_cls.error(
            title=tr_fn("common.error.title", "Ошибка"),
            content=tr_fn(
                _tr_key(tr_prefix, "error.reset_all_exception"),
                "Ошибка восстановления пресетов: {error}",
                error=exc,
            ),
            parent=parent_window,
        )
    finally:
        set_bulk_reset_running_fn(False)
        if runtime_service.is_ui_dirty() and is_visible:
            refresh_view_fn()


def show_reset_all_result(
    *,
    cleanup_in_progress: bool,
    success_count: int,
    total_count: int,
    failed_count: int = 0,
    reset_all_btn,
    single_shot_fn,
    restore_label_fn,
) -> None:
    if cleanup_in_progress:
        return
    _ = total_count
    ok = int(success_count or 0)
    failed = int(failed_count or 0)
    try:
        if failed > 0:
            reset_all_btn.setText(f"Ошибки: {failed}")
            icon = FluentIcon.INFO
        elif ok > 0:
            reset_all_btn.setText(f"Сброшено: {ok}")
            icon = FluentIcon.ACCEPT
        else:
            reset_all_btn.setText("Нечего менять")
            icon = FluentIcon.ACCEPT
        reset_all_btn.setIcon(icon)
    except Exception:
        pass
    single_shot_fn(3000, restore_label_fn)


def restore_reset_all_button_label(
    *,
    cleanup_in_progress: bool,
    reset_all_btn,
    tr_fn,
    tr_prefix: str,
) -> None:
    if cleanup_in_progress:
        return
    try:
        reset_all_btn.setText(
            tr_fn(_tr_key(tr_prefix, "button.reset_all"), "Вернуть встроенные")
        )
        reset_all_btn.setIcon(FluentIcon.RETURN)
    except Exception:
        pass
