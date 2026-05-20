"""Workflow чтения и сохранения пользовательских list-файлов."""

from __future__ import annotations


def normalize_editor_kind(kind: str) -> str:
    normalized = str(kind or "").strip().lower().replace("-", "_")
    if normalized in {"domains", "domain", "hostlist"}:
        return "domains"
    if normalized in {"ipset", "ips", "ipset_all"}:
        return "ipset"
    if normalized in {"netrogat", "exclusions"}:
        return "netrogat"
    if normalized in {"ipru", "ipset_ru"}:
        return "ipru"
    raise ValueError(f"Unknown list editor kind: {kind}")


def load_editor_text(lists_feature, kind: str):
    """Загружает текст пользовательского list-файла через feature."""
    normalized = normalize_editor_kind(kind)
    if normalized == "domains":
        return lists_feature.load_custom_domains_text()
    if normalized == "ipset":
        return lists_feature.load_custom_ipset_text()
    if normalized == "netrogat":
        return lists_feature.load_custom_netrogat_text()
    return lists_feature.load_custom_ipru_text()


def save_editor_text(lists_feature, kind: str, text: str):
    """Сохраняет текст пользовательского list-файла через feature."""
    normalized = normalize_editor_kind(kind)
    if normalized == "domains":
        return lists_feature.save_custom_domains_text(text)
    if normalized == "ipset":
        return lists_feature.save_custom_ipset_text(text)
    if normalized == "netrogat":
        return lists_feature.save_custom_netrogat_text(text)
    return lists_feature.save_custom_ipru_text(text)


def open_editor_user_file(lists_feature, kind: str) -> None:
    """Открывает пользовательский list-файл."""
    normalized = normalize_editor_kind(kind)
    if normalized == "domains":
        lists_feature.open_domains_user_file()
        return
    if normalized == "ipset":
        lists_feature.open_ipset_all_user_file()
        return
    if normalized == "netrogat":
        lists_feature.open_netrogat_user_file()
        return
    lists_feature.open_ipset_ru_user_file()


def open_editor_user_file_action(lists_feature, kind: str):
    """Открывает пользовательский list-файл и возвращает UI action result."""
    normalized = normalize_editor_kind(kind)
    if normalized == "domains":
        return lists_feature.open_domains_user_file_action()
    if normalized == "ipset":
        return lists_feature.open_ipset_all_user_file_action()
    if normalized == "netrogat":
        return lists_feature.open_netrogat_user_file_action()
    return lists_feature.open_ipset_ru_user_file_action()


def open_editor_final_file_action(lists_feature, kind: str):
    """Открывает итоговый list-файл и возвращает UI action result."""
    normalized = normalize_editor_kind(kind)
    if normalized == "netrogat":
        return lists_feature.open_netrogat_final_file_action()
    if normalized == "ipru":
        return lists_feature.open_ipset_ru_final_file_action()
    raise ValueError(f"Final file is not supported for list editor kind: {kind}")


def open_editor_final_file(lists_feature, kind: str) -> None:
    """Открывает итоговый list-файл."""
    normalized = normalize_editor_kind(kind)
    if normalized == "netrogat":
        lists_feature.open_netrogat_final_file()
        return
    if normalized == "ipru":
        lists_feature.open_ipset_ru_final_file()
        return
    raise ValueError(f"Final file is not supported for list editor kind: {kind}")


def open_lists_folder_action(lists_feature):
    """Открывает папку lists через feature."""
    return lists_feature.open_lists_folder_action()


def rebuild_hostlists_action(lists_feature):
    """Пересобирает итоговые hostlist/ipset файлы через feature."""
    return lists_feature.rebuild_hostlists_action()


def load_folder_info(lists_feature, category: str):
    """Загружает сведения о папке hostlist/ipset."""
    normalized = str(category or "").strip().lower()
    if normalized == "ipset":
        return lists_feature.load_ipset_folder_info()
    return lists_feature.load_hostlist_folder_info()


def build_editor_status_plan(lists_feature, kind: str, text: str):
    """Строит план статуса для редактора list-файла."""
    normalized = normalize_editor_kind(kind)
    if normalized == "domains":
        return lists_feature.build_custom_domains_status_plan(text)
    if normalized == "ipset":
        return lists_feature.build_custom_ipset_status_plan(text)
    if normalized == "netrogat":
        return lists_feature.build_custom_netrogat_status_plan(text)
    return lists_feature.build_custom_ipru_status_plan(text)


def build_add_editor_entry_plan(lists_feature, kind: str, *, raw_text: str, current_text: str):
    """Строит план добавления записи в пользовательский list-файл."""
    normalized = normalize_editor_kind(kind)
    if normalized == "domains":
        return lists_feature.build_add_custom_domain_plan(raw_text=raw_text, current_text=current_text)
    if normalized == "ipset":
        return lists_feature.build_add_custom_ipset_plan(raw_text=raw_text, current_text=current_text)
    if normalized == "netrogat":
        return lists_feature.build_add_custom_netrogat_plan(raw_text=raw_text, current_text=current_text)
    return lists_feature.build_add_custom_ipru_plan(raw_text=raw_text, current_text=current_text)


def reset_domains_file_action(lists_feature):
    """Сбрасывает пользовательский domains-файл и возвращает action result."""
    return lists_feature.reset_domains_file_action()


def reset_domains_file(lists_feature) -> bool:
    """Сбрасывает пользовательский domains-файл."""
    return bool(lists_feature.reset_domains_file())


def add_missing_netrogat_defaults_action(lists_feature):
    """Добавляет недостающие стандартные netrogat-домены и возвращает action result."""
    return lists_feature.add_missing_netrogat_defaults_action()


def add_missing_netrogat_defaults(lists_feature) -> int:
    """Добавляет недостающие стандартные netrogat-домены."""
    return int(lists_feature.add_missing_netrogat_defaults())


class ListsEditorController:
    """Действия страниц list-редакторов без привязки к QWidget."""

    def __init__(self, lists_feature) -> None:
        self._lists = lists_feature

    def open_lists_folder_action(self):
        return open_lists_folder_action(self._lists)

    def rebuild_hostlists_action(self):
        return rebuild_hostlists_action(self._lists)

    def load_folder_info(self, category: str):
        return load_folder_info(self._lists, category)

    def load_text(self, kind: str):
        return load_editor_text(self._lists, kind)

    def create_text_load_worker(self, request_id: int, kind: str, parent=None):
        from lists.editor_load_worker import ListsEditorTextLoadWorker

        return ListsEditorTextLoadWorker(request_id, self, kind, parent)

    def save_text(self, kind: str, text: str):
        return save_editor_text(self._lists, kind, text)

    def status_plan(self, kind: str, text: str):
        return build_editor_status_plan(self._lists, kind, text)

    def add_entry_plan(self, kind: str, *, raw_text: str, current_text: str):
        return build_add_editor_entry_plan(
            self._lists,
            kind,
            raw_text=raw_text,
            current_text=current_text,
        )

    def open_user_file(self, kind: str) -> None:
        open_editor_user_file(self._lists, kind)

    def open_user_file_action(self, kind: str):
        return open_editor_user_file_action(self._lists, kind)

    def open_final_file(self, kind: str) -> None:
        open_editor_final_file(self._lists, kind)

    def open_final_file_action(self, kind: str):
        return open_editor_final_file_action(self._lists, kind)

    def reset_domains_file_action(self):
        return reset_domains_file_action(self._lists)

    def reset_domains_file(self) -> bool:
        return reset_domains_file(self._lists)

    def add_missing_netrogat_defaults_action(self):
        return add_missing_netrogat_defaults_action(self._lists)

    def add_missing_netrogat_defaults(self) -> int:
        return add_missing_netrogat_defaults(self._lists)
