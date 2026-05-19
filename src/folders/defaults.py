from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

COMMON_FOLDER_KEY = "common"
PINNED_FOLDER_KEY = "pinned"


_PRESET_FOLDERS: tuple[tuple[str, str, bool], ...] = (
    ("all-tcp-udp", "ALL TCP & UDP", False),
    (COMMON_FOLDER_KEY, "Общие", True),
    ("game-filter", "Game filter", False),
    ("circular", "Circular", False),
)

_PROFILE_FOLDERS: tuple[tuple[str, str, bool], ...] = (
    ("youtube", "YouTube", False),
    ("discord", "Discord", False),
    ("messengers", "Мессенджеры", False),
    ("social", "Соцсети", False),
    ("games", "Игры", False),
    ("hosters", "Хостеры", False),
    ("sites", "Сайты", False),
    ("zapretkvn", "ZapretKVN", False),
    (COMMON_FOLDER_KEY, "Общие", True),
    ("all-sites", "Все сайты", False),
)


def build_default_preset_folders() -> dict[str, Any]:
    return _build_default_state(_PRESET_FOLDERS)


def build_default_profile_folders() -> dict[str, Any]:
    return _build_default_state(_PROFILE_FOLDERS)


def classify_preset_folder(name: object) -> str:
    text = str(name or "").strip().lower()
    if "all tcp" in text and "udp" in text:
        return "all-tcp-udp"
    if "game filter" in text:
        return "game-filter"
    if "circular" in text:
        return "circular"
    return COMMON_FOLDER_KEY


def classify_profile_folder(text: object) -> str:
    value = str(text or "").strip().lower()
    if not value:
        return COMMON_FOLDER_KEY
    if "youtube" in value or "googlevideo" in value:
        return "youtube"
    if "discord" in value:
        return "discord"
    if any(token in value for token in ("telegram", "whatsapp", "viber", "signal", "mtproto")):
        return "messengers"
    if any(token in value for token in ("facebook", "instagram", "tiktok", "twitter", "x.com", "vk.com", "vk ")):
        return "social"
    if any(token in value for token in ("game", "valorant", "riot", "steam", "itch.io", "roblox", "lol", "league of legends", "battlenet", "battle.net", "wow", "dead by daylight")):
        return "games"
    if any(token in value for token in ("amazon", "cloudflare", "ovh", "warp")):
        return "hosters"
    if any(token in value for token in ("timeweb", "zapretkvn")):
        return "zapretkvn"
    if _looks_like_all_sites_profile(value):
        return "all-sites"
    if _mentions_site_or_list(value):
        return "sites"
    return COMMON_FOLDER_KEY


def _build_default_state(folder_specs: tuple[tuple[str, str, bool], ...]) -> dict[str, Any]:
    return {
        "version": 1,
        "folders": {
            key: {
                "name": name,
                "order": index,
                "collapsed": False,
                "system": system,
            }
            for index, (key, name, system) in enumerate(folder_specs)
        },
        "items": {},
    }


def _looks_like_all_sites_profile(text: str) -> bool:
    if any(token in text for token in ("allsite", "all-site", "all sites", "все сайты")):
        return True
    has_include = any(token in text for token in ("--hostlist=", "--hostlist-domains=", "--ipset=", "--ipset-ip="))
    has_exclude = any(token in text for token in ("--hostlist-exclude", "--ipset-exclude"))
    return has_exclude and not has_include


def _mentions_site_or_list(text: str) -> bool:
    if any(token in text for token in ("--hostlist=", "--hostlist-domains=", "--ipset=", "--ipset-ip=")):
        return True
    return bool(re.search(r"\b[a-z0-9-]+\.(?:ru|com|org|net|io|gg|tv)\b", text))


def clone_default_preset_folders() -> dict[str, Any]:
    return deepcopy(build_default_preset_folders())


def clone_default_profile_folders() -> dict[str, Any]:
    return deepcopy(build_default_profile_folders())


__all__ = [
    "COMMON_FOLDER_KEY",
    "PINNED_FOLDER_KEY",
    "build_default_preset_folders",
    "build_default_profile_folders",
    "classify_preset_folder",
    "classify_profile_folder",
    "clone_default_preset_folders",
    "clone_default_profile_folders",
]
