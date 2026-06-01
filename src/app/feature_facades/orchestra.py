from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import orchestra.log_context_actions as orchestra_log_context_actions
import orchestra.log_history_workflow as orchestra_log_history_workflow
from orchestra.ratings_workflow import load_orchestra_ratings_state


@dataclass(slots=True, init=False)
class OrchestraFeature:
    _whitelist_runtime_service: Any | None = field(default=None, repr=False, compare=False)
    runner: Any = None

    def __init__(self, whitelist_runtime_service: Any | None = None, runner: Any = None) -> None:
        self._whitelist_runtime_service = whitelist_runtime_service
        self.runner = runner

    @staticmethod
    def _commands():
        import orchestra.commands as orchestra_commands

        return orchestra_commands

    @staticmethod
    def _create_whitelist_runtime_service():
        from core.runtime.orchestra_whitelist_runtime_service import OrchestraWhitelistRuntimeService

        return OrchestraWhitelistRuntimeService()

    @property
    def whitelist_runtime_service(self):
        service = self._whitelist_runtime_service
        if service is None:
            service = self._create_whitelist_runtime_service()
            self._whitelist_runtime_service = service
        return service

    @property
    def ASKEY_ALL(self):
        return self._commands().ASKEY_ALL

    def ensure_runner(self):
        if self.runner is None:
            from orchestra.orchestra_runner import OrchestraRunner

            self.runner = OrchestraRunner()
        return self.runner

    def is_running(self) -> bool:
        runner = self.runner
        if runner is None:
            return False
        try:
            return bool(runner.is_running())
        except Exception:
            return False

    def stop_runner(self) -> bool:
        runner = self.runner
        if runner is None:
            return True
        try:
            runner.stop()
            return True
        except Exception:
            return False

    def clear_learned_data(self) -> None:
        runner = self.runner
        if runner is not None:
            runner.clear_learned_data()

    def clear_learned_data_if_ready(self) -> bool:
        runner = self.runner
        if runner is None:
            return False
        runner.clear_learned_data()
        return True

    def load_log_history(self) -> list[dict]:
        runner = self.runner
        if runner is None:
            return []
        return list(runner.get_log_history() or [])

    def is_strategy_blocked(self, *, domain: str, strategy: int) -> bool:
        return bool(
            orchestra_log_context_actions.is_strategy_blocked(
                runner=self.runner,
                domain=domain,
                strategy=int(strategy or 0),
            )
        )

    def run_log_context_action(self, *, action: str, domain: str, strategy: int, protocol: str):
        runner = self.runner
        if runner is None:
            raise RuntimeError("Orchestra runner is not ready")

        normalized_action = str(action or "").strip()
        if normalized_action == "lock":
            return orchestra_log_context_actions.lock_strategy_from_log(
                runner=runner,
                domain=domain,
                strategy=int(strategy or 0),
                protocol=protocol,
            )
        if normalized_action == "block":
            return orchestra_log_context_actions.block_strategy_from_log(
                runner=runner,
                domain=domain,
                strategy=int(strategy or 0),
                protocol=protocol,
            )
        if normalized_action == "unblock":
            return orchestra_log_context_actions.unblock_strategy_from_log(
                runner=runner,
                domain=domain,
                strategy=int(strategy or 0),
                protocol=protocol,
            )
        if normalized_action == "whitelist":
            return orchestra_log_context_actions.add_to_whitelist_from_log(
                runner=runner,
                domain=domain,
            )
        raise ValueError(f"Неизвестное действие строки лога: {normalized_action}")

    def run_log_history_action(self, *, action: str, log_id: str):
        runner = self.runner
        if runner is None:
            raise RuntimeError("Orchestra runner is not ready")

        normalized_action = str(action or "").strip()
        if normalized_action == "view":
            return orchestra_log_history_workflow.view_log_history_entry(
                runner=runner,
                log_id=str(log_id or ""),
            )
        if normalized_action == "delete":
            return orchestra_log_history_workflow.delete_log_history_entry(
                runner=runner,
                log_id=str(log_id or ""),
            )
        if normalized_action == "clear":
            return orchestra_log_history_workflow.clear_log_history_entries(
                runner=runner,
            )
        raise ValueError(f"Неизвестное действие истории логов: {normalized_action}")

    def create_clear_learned_worker(self, request_id: int, parent=None):
        from orchestra.page_workers import OrchestraClearLearnedWorker

        return OrchestraClearLearnedWorker(request_id, self.clear_learned_data_if_ready, parent)

    def create_log_history_load_worker(self, request_id: int, parent=None):
        from orchestra.page_workers import OrchestraLogHistoryLoadWorker

        return OrchestraLogHistoryLoadWorker(request_id, self.load_log_history, parent)

    def create_log_history_action_worker(self, request_id: int, *, action: str, log_id: str, parent=None):
        from orchestra.page_workers import OrchestraLogHistoryActionWorker

        return OrchestraLogHistoryActionWorker(
            request_id,
            action=action,
            log_id=log_id,
            run_action=self.run_log_history_action,
            parent=parent,
        )

    def create_log_context_action_worker(
        self,
        request_id: int,
        *,
        action: str,
        domain: str,
        strategy: int,
        protocol: str,
        parent=None,
    ):
        from orchestra.page_workers import OrchestraLogContextActionWorker

        return OrchestraLogContextActionWorker(
            request_id,
            action=action,
            domain=domain,
            strategy=int(strategy or 0),
            protocol=protocol,
            run_action=self.run_log_context_action,
            parent=parent,
        )

    def load_ratings_state(self):
        return load_orchestra_ratings_state(self.runner)

    def create_ratings_state_load_worker(self, request_id: int, parent=None):
        from orchestra.ratings_worker import OrchestraRatingsStateLoadWorker

        return OrchestraRatingsStateLoadWorker(request_id, self.load_ratings_state, parent)

    def set_setting(self, key: str, value, *, runner=None) -> None:
        from settings.dpi.public import set_orchestra_setting

        set_orchestra_setting(key, value, runner=self.runner if runner is None else runner)

    def create_setting_save_worker(self, request_id: int, *, key: str, value, parent=None):
        from orchestra.settings_worker import OrchestraSettingSaveWorker

        return OrchestraSettingSaveWorker(
            request_id,
            key=key,
            value=value,
            runner=self.runner,
            set_setting=self.set_setting,
            parent=parent,
        )

    def get_whitelist_snapshot(self, runner, *, refresh: bool = False):
        return self._commands().get_whitelist_snapshot(
            runner,
            whitelist_service=self.whitelist_runtime_service,
            refresh=refresh,
        )

    def add_whitelist_domain(self, runner, domain: str) -> bool:
        return bool(
            self._commands().add_whitelist_domain(
                runner,
                domain,
                whitelist_service=self.whitelist_runtime_service,
            )
        )

    def remove_whitelist_domain(self, runner, domain: str) -> bool:
        return bool(
            self._commands().remove_whitelist_domain(
                runner,
                domain,
                whitelist_service=self.whitelist_runtime_service,
            )
        )

    def clear_whitelist_user_domains(self, runner, domains: list[str]) -> int:
        return int(
            self._commands().clear_whitelist_user_domains(
                runner,
                domains,
                whitelist_service=self.whitelist_runtime_service,
            )
            or 0
        )

    def is_whitelist_runtime_running(self) -> bool:
        runner = self.runner
        return bool(runner is not None and runner.is_running())

    def create_whitelist_snapshot_load_worker(self, request_id: int, *, refresh: bool, parent=None):
        from orchestra.managed_lists_workers import OrchestraWhitelistSnapshotLoadWorker

        return OrchestraWhitelistSnapshotLoadWorker(
            request_id,
            self.load_whitelist_snapshot,
            refresh=refresh,
            parent=parent,
        )

    def create_whitelist_action_worker(
        self,
        request_id: int,
        *,
        action: str,
        domain: str = "",
        user_domains: list[str] | None = None,
        parent=None,
    ):
        from orchestra.managed_lists_workers import OrchestraWhitelistActionWorker

        return OrchestraWhitelistActionWorker(
            request_id,
            self.add_whitelist_domain_to_current_runner,
            self.remove_whitelist_domain_from_current_runner,
            self.clear_current_whitelist_user_domains,
            self.load_whitelist_snapshot,
            action=action,
            domain=domain,
            user_domains=user_domains,
            parent=parent,
        )

    def load_whitelist_snapshot(self, *, refresh: bool):
        return self.get_whitelist_snapshot(
            self.runner,
            refresh=refresh,
        )

    def add_whitelist_domain_to_current_runner(self, *, domain: str):
        from orchestra.managed_lists_workflow import add_whitelist_domain

        return add_whitelist_domain(
            orchestra=self,
            runner=self.runner,
            domain=domain,
        )

    def remove_whitelist_domain_from_current_runner(self, *, domain: str):
        from orchestra.managed_lists_workflow import remove_whitelist_domain

        return remove_whitelist_domain(
            orchestra=self,
            runner=self.runner,
            domain=domain,
        )

    def clear_current_whitelist_user_domains(self, *, user_domains: list[str]):
        from orchestra.managed_lists_workflow import clear_whitelist_user_domains

        return clear_whitelist_user_domains(
            orchestra=self,
            runner=self.runner,
            user_domains=user_domains,
        )

    def create_loaded_blocked_manager(self):
        return self._commands().create_loaded_blocked_manager()

    def create_loaded_locked_manager(self):
        return self._commands().create_loaded_locked_manager()

    def is_default_blocked_pass_domain(self, hostname: str) -> bool:
        return bool(self._commands().is_default_blocked_pass_domain(hostname))


def build_orchestra_feature() -> OrchestraFeature:
    return OrchestraFeature()
