from __future__ import annotations

from dataclasses import dataclass
import ipaddress
from pathlib import Path, PureWindowsPath
import re

from .models import Profile


@dataclass(frozen=True)
class ProfileListFileReference:
    kind: str = ""
    file_name: str = ""
    display_path: str = ""
    editable: bool = False
    error_text: str = ""


_FILE_MATCH_NAMES = {
    "--hostlist": "hostlist",
    "--ipset": "ipset",
    "--hostlist-exclude": "hostlist",
    "--ipset-exclude": "ipset",
}


def profile_list_file_reference(profile: Profile, lists_root: Path) -> ProfileListFileReference:
    for wanted_names in (("--hostlist", "--ipset"), ("--hostlist-exclude", "--ipset-exclude")):
        for segment in getattr(profile, "segments", ()) or ():
            name = str(getattr(segment, "name", "") or "").strip().lower()
            if name not in wanted_names:
                continue
            kind = _FILE_MATCH_NAMES.get(name, "")
            value = str(getattr(segment, "value", "") or "").strip().strip('"').strip("'").lstrip("@")
            if not value:
                return ProfileListFileReference(kind=kind, editable=False, error_text="В profile указан пустой файл списка.")
            if "," in value:
                return ProfileListFileReference(
                    kind=kind,
                    editable=False,
                    error_text="В profile указано несколько файлов списка. Разделите profile на отдельные строки.",
                )
            file_name = _safe_list_file_name(value)
            if not file_name:
                return ProfileListFileReference(
                    kind=kind,
                    editable=False,
                    error_text="Не удалось определить имя файла списка.",
                )
            return ProfileListFileReference(
                kind=kind,
                file_name=file_name,
                display_path=f"lists/{file_name}",
                editable=True,
            )
    return ProfileListFileReference(
        editable=False,
        error_text="У этого profile нет отдельного hostlist/ipset-файла для редактирования.",
    )


def read_profile_list_file_text(lists_root: Path, reference: ProfileListFileReference) -> str:
    if not reference.editable or not reference.file_name:
        return ""
    path = _list_file_path(lists_root, reference.file_name)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_profile_list_file_text(lists_root: Path, reference: ProfileListFileReference, text: str) -> None:
    if not reference.editable or not reference.file_name:
        raise ValueError(reference.error_text or "Файл списка недоступен для редактирования.")
    invalid_lines = validate_profile_list_file_text(reference.kind, text)
    if invalid_lines:
        line, value = invalid_lines[0]
        raise ValueError(f"Строка {line}: неверная запись `{value}`.")
    path = _list_file_path(lists_root, reference.file_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    if normalized and not normalized.endswith("\n"):
        normalized += "\n"
    path.write_text(normalized, encoding="utf-8", newline="\n")


def validate_profile_list_file_text(kind: str, text: str) -> tuple[tuple[int, str], ...]:
    normalized_kind = str(kind or "").strip().lower()
    invalid: list[tuple[int, str]] = []
    for line_number, raw_line in enumerate(str(text or "").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if normalized_kind == "ipset":
            if not _valid_ipset_line(line):
                invalid.append((line_number, line))
            continue
        if not _valid_hostlist_line(line):
            invalid.append((line_number, line))
    return tuple(invalid)


def _list_file_path(lists_root: Path, file_name: str) -> Path:
    return Path(lists_root) / _safe_list_file_name(file_name)


def _safe_list_file_name(value: str) -> str:
    name = PureWindowsPath(str(value or "").replace("\\", "/")).name.strip()
    if not name or name in {".", ".."}:
        return ""
    return name


def _valid_ipset_line(line: str) -> bool:
    if "-" in line:
        return False
    try:
        if "/" in line:
            ipaddress.ip_network(line, strict=False)
        else:
            ipaddress.ip_address(line)
        return True
    except Exception:
        return False


def _valid_hostlist_line(line: str) -> bool:
    value = str(line or "").strip().lower()
    if value.startswith("^"):
        value = value[1:].strip()
    if value.startswith("*."):
        value = value[2:].strip()
    if value.startswith("."):
        value = value[1:].strip()
    if not value or "://" in value or "/" in value or ":" in value:
        return False
    try:
        ascii_domain = value.encode("idna").decode("ascii")
    except Exception:
        return False
    if len(ascii_domain) > 253 or "." not in ascii_domain:
        return False
    labels = ascii_domain.rstrip(".").split(".")
    if len(labels) < 2:
        return False
    label_re = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)
    return all(label_re.fullmatch(label or "") for label in labels)
