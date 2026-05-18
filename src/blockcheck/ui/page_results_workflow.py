"""Workflow отрисовки результатов BlockCheck."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTableWidgetItem

from blockcheck.ui.helpers import (
    build_family_tooltip,
    build_target_detail_text,
    format_result_detail,
    sort_results_by_family,
    truncate_detail,
)
from ui.widgets.fluent_item_tooltip import set_fluent_item_tooltip


DPI_BADGE_COLORS = {
    "none": ("#52c477", "#1a3a24"),
    "dns_fake": ("#e0a854", "#3a2e1a"),
    "http_inject": ("#e07854", "#3a221a"),
    "isp_page": ("#e05454", "#3a1a1a"),
    "tls_dpi": ("#e05454", "#3a1a1a"),
    "tls_mitm": ("#e05454", "#3a1a1a"),
    "tcp_reset": ("#e07854", "#3a221a"),
    "tcp_16_20": ("#e0a854", "#3a2e1a"),
    "stun_block": ("#e0a854", "#3a2e1a"),
    "full_block": ("#e05454", "#3a1a1a"),
}

DPI_LABELS_RU = {
    "none": "DPI не обнаружен",
    "dns_fake": "DNS подмена",
    "http_inject": "HTTP инъекция",
    "isp_page": "Страница-заглушка ISP",
    "tls_dpi": "TLS DPI (RST/EOF)",
    "tls_mitm": "TLS MITM прокси",
    "tcp_reset": "TCP RST",
    "tcp_16_20": "TCP блок 16-20KB",
    "stun_block": "STUN/UDP блокировка",
    "full_block": "Полная блокировка",
}


def make_readonly_item(text: str) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


def find_table_row(table, name: str) -> int:
    for row in range(table.rowCount()):
        item = table.item(row, 0)
        if item and item.text() == name:
            return row
    return -1


def find_tcp_row(tcp_table, target_id: str) -> int:
    if tcp_table is None:
        return -1
    for row in range(tcp_table.rowCount()):
        item = tcp_table.item(row, 0)
        if item and item.text() == target_id:
            return row
    return -1


def result_display_rank(result) -> int:
    from blockcheck.models import TestStatus

    if result.status == TestStatus.FAIL:
        return 0
    if result.status == TestStatus.ERROR:
        return 1
    if result.status == TestStatus.TIMEOUT:
        return 2
    if result.status == TestStatus.UNSUPPORTED:
        return 3
    return 4


def set_status_cell(table, row: int, col: int, result) -> None:
    from blockcheck.models import TestStatus

    if result.status == TestStatus.OK:
        text = "OK"
        if result.time_ms:
            text += f" ({result.time_ms:.0f}ms)"
        item = make_readonly_item(text)
        item.setForeground(QColor("#52c477"))
    elif result.status == TestStatus.UNSUPPORTED:
        item = make_readonly_item("UNSUP")
        item.setForeground(QColor("#e0a854"))
    elif result.status == TestStatus.TIMEOUT:
        item = make_readonly_item("TIMEOUT")
        item.setForeground(QColor("#e0a854"))
    else:
        text = result.error_code or "FAIL"
        item = make_readonly_item(text)
        item.setForeground(QColor("#e05454"))

    set_fluent_item_tooltip(item, result.detail)
    table.setItem(row, col, item)


def set_dualstack_status_cell(table, row: int, col: int, results: list) -> None:
    from blockcheck.models import TestStatus

    if not results:
        return

    if len(results) == 1:
        set_status_cell(table, row, col, results[0])
        return

    sorted_results = sort_results_by_family(results)
    ok_results = [result for result in sorted_results if result.status == TestStatus.OK]
    non_ok_results = [result for result in sorted_results if result.status != TestStatus.OK]

    if ok_results and non_ok_results:
        item = make_readonly_item("MIXED")
        item.setForeground(QColor("#e0a854"))
    elif ok_results:
        best_ok = min(ok_results, key=lambda result: result.time_ms or 999999.0)
        text = "OK"
        if best_ok.time_ms:
            text += f" ({best_ok.time_ms:.0f}ms)"
        item = make_readonly_item(text)
        item.setForeground(QColor("#52c477"))
    elif all(result.status == TestStatus.TIMEOUT for result in sorted_results):
        item = make_readonly_item("TIMEOUT")
        item.setForeground(QColor("#e0a854"))
    elif all(result.status == TestStatus.UNSUPPORTED for result in sorted_results):
        item = make_readonly_item("UNSUP")
        item.setForeground(QColor("#e0a854"))
    else:
        primary = sorted(non_ok_results, key=result_display_rank)[0] if non_ok_results else sorted_results[0]
        text = primary.error_code or "FAIL"
        item = make_readonly_item(text)
        item.setForeground(QColor("#e05454"))

    set_fluent_item_tooltip(item, build_family_tooltip(sorted_results))
    table.setItem(row, col, item)


def tcp_status_text_and_color(result) -> tuple[str, str]:
    from blockcheck.models import TestStatus

    if result.status == TestStatus.OK:
        return "OK", "#52c477"
    if result.status == TestStatus.TIMEOUT:
        return "TIMEOUT", "#e0a854"
    if result.error_code == "TCP_16_20":
        return "DETECTED", "#e05454"
    if result.status == TestStatus.UNSUPPORTED:
        return "UNSUP", "#e0a854"
    if result.status == TestStatus.ERROR:
        return "ERROR", "#e05454"
    return (result.error_code or "FAIL"), "#e05454"


def update_tcp_result_table(*, target_result, tcp_table, tcp_section_label) -> None:
    from blockcheck.models import TestType

    if tcp_table is None:
        return

    tcp_tests = sorted(
        [test for test in target_result.tests if test.test_type == TestType.TCP_16_20],
        key=lambda test: (test.raw_data or {}).get("target_id") or test.target_name or "",
    )
    if not tcp_tests:
        return

    if tcp_section_label is not None:
        tcp_section_label.setVisible(True)
    tcp_table.setVisible(True)

    for test in tcp_tests:
        raw = test.raw_data or {}
        target_id = str(raw.get("target_id") or test.target_name or "-")
        asn_raw = str(raw.get("asn") or "").strip()
        provider = str(raw.get("provider") or "-")

        if asn_raw:
            asn_text = asn_raw.upper() if asn_raw.upper().startswith("AS") else f"AS{asn_raw}"
        else:
            asn_text = "-"

        row = find_tcp_row(tcp_table, target_id)
        if row == -1:
            row = tcp_table.rowCount()
            tcp_table.insertRow(row)

        tcp_table.setItem(row, 0, make_readonly_item(target_id))
        tcp_table.setItem(row, 1, make_readonly_item(asn_text))
        tcp_table.setItem(row, 2, make_readonly_item(provider))

        status_text, color = tcp_status_text_and_color(test)
        status_item = make_readonly_item(status_text)
        status_item.setForeground(QColor(color))
        set_fluent_item_tooltip(status_item, format_result_detail(test))
        tcp_table.setItem(row, 3, status_item)

        detail_text = format_result_detail(test)
        bytes_received = raw.get("bytes_received")
        if isinstance(bytes_received, int) and bytes_received > 0:
            detail_text += f" | {bytes_received}B"
        detail_item = make_readonly_item(truncate_detail(detail_text))
        detail_item.setForeground(QColor("#9aa0a6"))
        set_fluent_item_tooltip(detail_item, detail_text)
        tcp_table.setItem(row, 4, detail_item)


def update_target_result_table(*, target_result, table, tcp_table, tcp_section_label) -> None:
    from blockcheck.models import DPIClassification, TestStatus, TestType

    tests = target_result.tests

    if str(target_result.value).startswith("TCP:"):
        update_tcp_result_table(
            target_result=target_result,
            tcp_table=tcp_table,
            tcp_section_label=tcp_section_label,
        )
        return

    row = find_table_row(table, target_result.name)
    if row == -1:
        row = table.rowCount()
        table.insertRow(row)
        table.setItem(row, 0, make_readonly_item(target_result.name))

    http_tests = [test for test in tests if test.test_type == TestType.HTTP]
    if http_tests:
        set_dualstack_status_cell(table, row, 1, http_tests)

    tls12 = [test for test in tests if test.test_type == TestType.TLS_12]
    tls13 = [test for test in tests if test.test_type == TestType.TLS_13]
    if tls12:
        tls13_ok = any(result.status == TestStatus.OK for result in tls13)
        tls12_all_fail = all(result.status != TestStatus.OK for result in tls12)
        if tls12_all_fail and tls13_ok:
            detail = build_family_tooltip(tls12)
            detail += "\nDPI блокирует SNI в TLS 1.2; сайт работает через TLS 1.3"
            item = make_readonly_item("DPI 1.2")
            item.setForeground(QColor("#e0a854"))
            set_fluent_item_tooltip(item, detail)
            table.setItem(row, 2, item)
        else:
            set_dualstack_status_cell(table, row, 2, tls12)

    if tls13:
        set_dualstack_status_cell(table, row, 3, tls13)

    dns_tests = [
        test for test in tests
        if test.test_type in (TestType.DNS_UDP, TestType.DNS_DOH)
    ]
    isp_tests = [test for test in tests if test.test_type == TestType.ISP_PAGE]
    if dns_tests:
        set_status_cell(table, row, 4, dns_tests[0])
    elif isp_tests:
        set_status_cell(table, row, 4, isp_tests[0])

    cls = target_result.classification
    if cls != DPIClassification.NONE:
        label = DPI_LABELS_RU.get(cls.value, cls.value)
        item = make_readonly_item(label)
        color = DPI_BADGE_COLORS.get(cls.value, ("#e0a854", "#3a2e1a"))
        item.setForeground(QColor(color[0]))
        table.setItem(row, 5, item)
    else:
        table.setItem(row, 5, make_readonly_item("—"))

    ping = [test for test in tests if test.test_type == TestType.PING]
    if ping:
        set_dualstack_status_cell(table, row, 6, ping)

    stun = [test for test in tests if test.test_type == TestType.STUN]
    if stun and not http_tests:
        set_status_cell(table, row, 1, stun[0])

    detail_text = build_target_detail_text(tests)
    detail_cell = make_readonly_item(truncate_detail(detail_text))
    detail_cell.setForeground(QColor("#9aa0a6"))
    set_fluent_item_tooltip(detail_cell, detail_text)
    table.setItem(row, 7, detail_cell)
