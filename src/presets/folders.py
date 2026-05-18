from __future__ import annotations

from typing import Any

from folders.defaults import build_default_preset_folders, classify_preset_folder
from folders.ordering import build_folder_rows
from folders.store import FolderLibraryStore, normalize_folder_state
from settings import store as settings_store
from settings.mode import ENGINE_WINWS1, ENGINE_WINWS2


def load_preset_folder_state(scope_key: str) -> dict[str, Any]:
    scope = _normalize_scope(scope_key)
    folders = settings_store.get_folders_settings()
    presets = folders.get("presets", {}) if isinstance(folders, dict) else {}
    raw_state = presets.get(scope) if isinstance(presets, dict) else None
    return normalize_folder_state(raw_state, build_default_preset_folders())


def save_preset_folder_state(scope_key: str, state: dict[str, Any]) -> dict[str, Any]:
    scope = _normalize_scope(scope_key)
    folders = settings_store.get_folders_settings()
    presets = folders.get("presets", {}) if isinstance(folders, dict) else {}
    if not isinstance(presets, dict):
        presets = {}
    presets[scope] = normalize_folder_state(state, build_default_preset_folders())
    folders["presets"] = presets
    return settings_store.set_folders_settings(folders)["presets"][scope]


def move_preset_to_folder(scope_key: str, file_name: str, folder_key: str) -> bool:
    state = load_preset_folder_state(scope_key)
    store = FolderLibraryStore(state, default_state=build_default_preset_folders())
    if not store.set_item_folder(file_name, folder_key):
        return False
    next_state = store.to_dict()
    _move_item_to_end(next_state, file_name, folder_key)
    save_preset_folder_state(scope_key, next_state)
    return True


def move_preset_before(scope_key: str, source_file_name: str, destination_file_name: str) -> bool:
    state = load_preset_folder_state(scope_key)
    source = str(source_file_name or "").strip()
    destination = str(destination_file_name or "").strip()
    items = state.setdefault("items", {})
    if not source or not destination or source == destination:
        return False
    destination_meta = items.setdefault(destination, {"folder_key": "common", "order": None, "rating": 0})
    folder_key = str(destination_meta.get("folder_key") or "common")
    source_meta = items.setdefault(source, {"folder_key": folder_key, "order": None, "rating": 0})
    source_meta["folder_key"] = folder_key
    ordered = [
        key
        for key, meta in _ordered_item_meta(items)
        if str(meta.get("folder_key") or "common") == folder_key and key != source
    ]
    if destination not in ordered:
        ordered.append(destination)
    ordered.insert(ordered.index(destination), source)
    for index, key in enumerate(ordered):
        items.setdefault(key, {"folder_key": folder_key, "order": None, "rating": 0})["order"] = index
    save_preset_folder_state(scope_key, state)
    return True


def move_preset_to_end(scope_key: str, file_name: str) -> bool:
    state = load_preset_folder_state(scope_key)
    source = str(file_name or "").strip()
    items = state.setdefault("items", {})
    if not source:
        return False
    meta = items.setdefault(source, {"folder_key": "common", "order": None, "rating": 0})
    folder_key = str(meta.get("folder_key") or "common")
    _move_item_to_end(state, source, folder_key)
    save_preset_folder_state(scope_key, state)
    return True


def build_preset_folder_rows(
    *,
    all_presets: dict[str, dict[str, Any]],
    visible_entries: list[dict[str, Any]],
    hierarchy,
    active_file_name: str,
    folder_state: dict[str, Any] | None = None,
    query: str = "",
) -> list[dict[str, Any]]:
    state = normalize_folder_state(folder_state, build_default_preset_folders())
    live_items: list[dict[str, Any]] = []
    for entry in visible_entries:
        file_name = str(entry.get("file_name") or "").strip()
        if not file_name:
            continue
        preset = all_presets.get(file_name) or {}
        display_name = str(preset.get("display_name") or entry.get("display_name") or file_name).strip()
        meta = _preset_meta(hierarchy, file_name)
        _ensure_item_meta(state, file_name, display_name, meta)
        live_items.append(
            {
                "key": file_name,
                "name": display_name,
                "rating": int(meta.get("rating", 0) or 0),
                "pinned": bool(meta.get("pinned", False)),
            }
        )

    folder_rows = build_folder_rows(
        state,
        live_items=live_items,
        include_pinned_folder=True,
        query=query,
    )
    rows: list[dict[str, Any]] = []
    for row in folder_rows:
        if row.get("kind") == "folder":
            rows.append(
                {
                    "kind": "folder",
                    "folder_key": str(row.get("key") or ""),
                    "name": str(row.get("name") or ""),
                    "text": str(row.get("name") or ""),
                    "is_collapsed": bool(row.get("collapsed", False)),
                    "is_system": bool(row.get("system", False)),
                    "is_service": bool(row.get("service", False)),
                    "count": int(row.get("count", 0) or 0),
                    "depth": 0,
                }
            )
            continue

        file_name = str(row.get("key") or "").strip()
        preset = all_presets.get(file_name) or {}
        meta = _preset_meta(hierarchy, file_name)
        rows.append(
            {
                "kind": "preset",
                "name": str(preset.get("display_name") or row.get("name") or file_name).strip(),
                "file_name": file_name,
                "description": str(preset.get("description") or ""),
                "date": str(preset.get("modified_display") or ""),
                "is_active": bool(file_name and file_name == str(active_file_name or "").strip()),
                "is_builtin": bool(preset.get("is_builtin", False)),
                "icon_color": str(preset.get("icon_color") or ""),
                "depth": 1,
                "folder_key": str(row.get("folder_key") or ""),
                "is_pinned": bool(meta.get("pinned", False)),
                "rating": int(meta.get("rating", 0) or 0),
            }
        )
    return rows


def _ensure_item_meta(state: dict[str, Any], file_name: str, display_name: str, meta: dict[str, Any]) -> None:
    items = state.setdefault("items", {})
    item = items.setdefault(
        file_name,
        {
            "folder_key": classify_preset_folder(display_name or file_name),
            "order": meta.get("order"),
            "rating": int(meta.get("rating", 0) or 0),
        },
    )
    if item.get("order") is None and meta.get("order") is not None:
        item["order"] = meta.get("order")
    item["rating"] = int(meta.get("rating", item.get("rating", 0)) or 0)
    if bool(meta.get("pinned", False)):
        item["pinned"] = True
    else:
        item.pop("pinned", None)


def _preset_meta(hierarchy, file_name: str) -> dict[str, Any]:
    try:
        meta = hierarchy.get_preset_meta(file_name)
        return meta if isinstance(meta, dict) else {}
    except Exception:
        return {}


def _normalize_scope(scope_key: str) -> str:
    scope = str(scope_key or "").strip().lower()
    return scope if scope in {ENGINE_WINWS1, ENGINE_WINWS2} else ENGINE_WINWS2


def _move_item_to_end(state: dict[str, Any], file_name: str, folder_key: str) -> None:
    items = state.setdefault("items", {})
    folder_items = [
        key
        for key, meta in _ordered_item_meta(items)
        if str(meta.get("folder_key") or "common") == folder_key and key != file_name
    ]
    folder_items.append(file_name)
    for index, key in enumerate(folder_items):
        meta = items.setdefault(key, {"folder_key": folder_key, "order": None, "rating": 0})
        meta["folder_key"] = folder_key
        meta["order"] = index


def _ordered_item_meta(items: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    normalized: list[tuple[str, dict[str, Any]]] = []
    for key, meta in items.items():
        if isinstance(meta, dict):
            normalized.append((str(key), meta))
    return sorted(
        normalized,
        key=lambda pair: (
            0 if pair[1].get("order") is not None else 1,
            int(pair[1].get("order") or 0),
            str(pair[0]).lower(),
        ),
    )


__all__ = [
    "build_preset_folder_rows",
    "load_preset_folder_state",
    "move_preset_before",
    "move_preset_to_end",
    "move_preset_to_folder",
    "save_preset_folder_state",
]
