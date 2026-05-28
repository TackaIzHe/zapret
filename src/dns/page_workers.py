from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from log.log import log


class DnsPageLoadWorker(QThread):
    loaded = pyqtSignal(object)
    finished_loading = pyqtSignal()

    def __init__(self, load_page_data_fn, parent=None):
        super().__init__(parent)
        self._load_page_data_fn = load_page_data_fn

    def run(self) -> None:
        try:
            state = self._load_page_data_fn()
            self.loaded.emit(state)
        except Exception as exc:
            log(f"DnsPageLoadWorker: ошибка загрузки DNS страницы: {exc}", "ERROR")
        self.finished_loading.emit()


class DnsConnectivityTestWorker(QThread):
    completed = pyqtSignal(list)

    def __init__(self, run_connectivity_test_fn, test_hosts, parent=None):
        super().__init__(parent)
        self._run_connectivity_test_fn = run_connectivity_test_fn
        self._test_hosts = tuple(test_hosts or ())

    def run(self) -> None:
        try:
            results = self._run_connectivity_test_fn(self._test_hosts)
        except Exception as exc:
            log(f"DnsConnectivityTestWorker: ошибка проверки DNS: {exc}", "ERROR")
            results = []
        self.completed.emit(list(results or []))


class DnsForceDnsActionWorker(QThread):
    completed = pyqtSignal(int, str, object, object)
    failed = pyqtSignal(int, str, str, object)

    def __init__(
        self,
        request_id: int,
        dns_feature,
        *,
        action: str,
        enabled: bool | None = None,
        language: str = "ru",
        parent=None,
    ):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._dns = dns_feature
        self._action = str(action or "").strip()
        self._enabled = None if enabled is None else bool(enabled)
        self._language = str(language or "ru")

    def run(self) -> None:
        context = {
            "enabled": self._enabled,
            "language": self._language,
        }
        try:
            if self._action == "toggle":
                result = self._run_toggle()
            elif self._action == "reset_dhcp":
                result = self._run_reset_dhcp()
            else:
                raise ValueError(f"Неизвестное Force DNS действие: {self._action}")
        except Exception as exc:
            log(f"DnsForceDnsActionWorker: действие {self._action} не выполнено: {exc}", "ERROR")
            self.failed.emit(self._request_id, self._action, str(exc), context)
            return
        self.completed.emit(self._request_id, self._action, result, context)

    def _run_toggle(self) -> dict[str, object]:
        from dns.ui import page_plans as dns_page_plans

        requested_enabled = bool(self._enabled)
        current_state = bool(self._dns.get_force_dns_status())
        if requested_enabled == current_state:
            plan = dns_page_plans.NetworkForceDnsTogglePlan(
                final_checked=current_state,
                force_dns_active=current_state,
                details_key=None,
                details_kwargs={},
                details_fallback="",
            )
            return {"plan": plan, "message": "", "changed": False}

        if requested_enabled:
            command_result = self._dns.enable_force_dns(include_disconnected=False)
            plan = dns_page_plans.build_force_dns_toggle_plan(
                requested_enabled=True,
                success=bool(command_result.success),
                ok_count=int(command_result.affected_count or 0),
                total=int(command_result.total_count or 0),
            )
        else:
            command_result = self._dns.disable_force_dns(reset_to_auto=False)
            plan = dns_page_plans.build_force_dns_toggle_plan(
                requested_enabled=False,
                success=bool(command_result.success),
            )
        return {
            "plan": plan,
            "message": str(command_result.message or ""),
            "changed": True,
        }

    def _run_reset_dhcp(self) -> dict[str, object]:
        from dns.ui import page_plans as dns_page_plans

        command_result = self._dns.disable_force_dns(reset_to_auto=True)
        force_dns_active = bool(self._dns.get_force_dns_status())
        plan = dns_page_plans.build_reset_dhcp_result_plan(
            success=bool(command_result.success),
            message=str(command_result.message or ""),
            force_dns_active=force_dns_active,
            language=self._language,
        )
        return {
            "plan": plan,
            "message": str(command_result.message or ""),
        }
