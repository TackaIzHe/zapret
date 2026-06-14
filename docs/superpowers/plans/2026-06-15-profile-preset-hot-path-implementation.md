# Profile Preset Hot Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Сделать смену готовой стратегии и preset-а точечной: маленькое действие должно обновлять только нужный кусок GUI, сводку и runtime, а не будить весь профильный экран без причины.

**Architecture:** `ProfilePresetService` становится владельцем точного плана изменения. GUI показывает быстрый отклик и применяет готовый результат. `PresetFileService` сохраняет файл. `PresetRuntimeCoordinator` применяет активный preset к `winws`. Кэш остаётся ускорителем, но не определяет правильность поведения.

**Tech Stack:** PyQt6, qfluentwidgets, `ProfilePresetService`, `ProfileFeature`, `ProfileStrategyApplyWorker`, `PresetSetupPageBase`, `PresetRuntimeCoordinator`, focused unittest, `app.architecture_checks`.

---

### Task 1: Зафиксировать контракт результата

**Files:**
- Modify: `src/profile/state.py`
- Modify: `src/profile/service.py`
- Modify: `src/profile/profile_setup_loader.py`
- Test: `tests/test_profile_service_apply_strategy_guards.py`
- Test: `tests/test_profile_setup_page_contract.py`

- [ ] **Step 1: Write failing tests**

Add tests for `StrategyApplyResult`:

- existing profile strategy change returns `status="applied"`;
- result has `change_kind="strategy_only"`;
- result says `list_structure_changed=False`;
- result says one profile payload changed;
- result says one profile list row may change;
- result says summary changed;
- result says runtime apply is needed;
- clicking the already selected strategy keeps the current no-save/no-rebuild behavior.

- [ ] **Step 2: Run red tests**

Run: `PYTHONPATH=src python -m unittest tests.test_profile_service_apply_strategy_guards tests.test_profile_setup_page_contract`

- [ ] **Step 3: Extend result without changing GUI behavior yet**

Add explicit fields to `StrategyApplyResult` while keeping old fields alive:

```text
change_kind
list_structure_changed
profile_payload_changed
profile_list_item_changed
summary_changed
runtime_apply_needed
```

Keep `should_reload` for stale and missing-profile cases. Do not make GUI parse preset text.

- [ ] **Step 4: Run green tests**

Run: `PYTHONPATH=src python -m unittest tests.test_profile_service_apply_strategy_guards tests.test_profile_setup_page_contract`

### Task 2: Развести событие GUI и событие runtime

**Files:**
- Modify: `src/profile/service.py`
- Modify: `src/presets/service.py`
- Modify: `src/core/runtime/preset_runtime_coordinator.py`
- Modify: `src/app/state_store.py`
- Test: `tests/test_preset_runtime_coordinator.py`
- Test: `tests/test_preset_ui_store_guards.py`
- Test: `tests/test_profile_service_apply_strategy_guards.py`

- [ ] **Step 1: Write failing tests**

Add tests that prove a strategy change still schedules runtime apply for the active preset, but GUI can receive the precise profile-change plan without relying only on `preset_content_revision`.

- [ ] **Step 2: Run red tests**

Run: `PYTHONPATH=src python -m unittest tests.test_preset_runtime_coordinator tests.test_preset_ui_store_guards tests.test_profile_service_apply_strategy_guards`

- [ ] **Step 3: Add a precise change reason next to the broad revision**

Keep the broad revision for runtime, raw editors and unknown changes. Add a precise reason/path for known profile changes, for example through a small change object or explicit fields in the service result.

Important rule: `PresetRuntimeCoordinator` may react to "active preset content changed", but GUI should not need to rebuild the whole profile list when `ProfilePresetService` already returned `strategy_only`.

- [ ] **Step 4: Run green tests**

Run: `PYTHONPATH=src python -m unittest tests.test_preset_runtime_coordinator tests.test_preset_ui_store_guards tests.test_profile_service_apply_strategy_guards`

### Task 3: Сделать GUI потребителем точного плана

**Files:**
- Modify: `src/profile/ui/profile_setup_page.py`
- Modify: `src/profile/ui/preset_setup_page.py`
- Test: `tests/test_profile_setup_page_contract.py`
- Test: `tests/test_preset_profile_async_architecture.py`

- [ ] **Step 1: Write failing tests**

Add tests that prove `strategy_only` does not request a full profile list reload from `PresetSetupPageBase` when the page already received the updated profile payload from `ProfileStrategyApplyWorker`.

Also keep tests for full reload when:

- active preset changed;
- preset structure changed;
- stale profile result asks for reload;
- raw preset/content editor changes the preset without a precise profile plan.

- [ ] **Step 2: Run red tests**

Run: `PYTHONPATH=src python -m unittest tests.test_profile_setup_page_contract tests.test_preset_profile_async_architecture`

- [ ] **Step 3: Use result fields in the setup page**

When `ProfileStrategyApplyWorker` returns a precise `strategy_only` result:

- keep instant local highlight;
- apply returned profile payload to the current page;
- call the existing profile-changed callback with the updated item;
- refresh summary through the existing profile callback path;
- do not treat the generic preset content revision as a reason to rebuild the whole list.

Do not add preset parsing to the page. The page only reads the plan returned by the service.

- [ ] **Step 4: Keep broad reload for broad actions**

Keep full reload for preset selection, structure changes, raw preset edits, imports, deletes, resets and stale-state recovery.

- [ ] **Step 5: Run green tests**

Run: `PYTHONPATH=src python -m unittest tests.test_profile_setup_page_contract tests.test_preset_profile_async_architecture`

### Task 4: Сузить сброс кэша

**Files:**
- Modify: `src/profile/service.py`
- Modify: `src/app/feature_facades/profile.py`
- Test: `tests/test_profile_list_payload.py`
- Test: `tests/test_profile_service_apply_strategy_guards.py`

- [ ] **Step 1: Write failing tests**

Add tests that prove:

- `strategy_only` does not throw away the whole profile list snapshot;
- setup payload for the changed profile is refreshed;
- summary is refreshed;
- switching preset still uses preset-specific warmed payload and does not reuse payload from another preset.

- [ ] **Step 2: Run red tests**

Run: `PYTHONPATH=src python -m unittest tests.test_profile_list_payload tests.test_profile_service_apply_strategy_guards`

- [ ] **Step 3: Narrow invalidation**

For `strategy_only`, invalidate only:

- changed profile setup payload;
- changed row/item payload if it is cached separately;
- summary payload.

Keep full invalidation for preset selection and preset structure changes.

Do not remove the warmed preset cache from `ProfileFeature`. It is compatible with this architecture, but it stays only an accelerator.

- [ ] **Step 4: Run green tests**

Run: `PYTHONPATH=src python -m unittest tests.test_profile_list_payload tests.test_profile_service_apply_strategy_guards`

### Task 5: Убрать лишние широкие fallback-пути

**Files:**
- Modify: `src/profile/ui/preset_setup_page.py`
- Modify: `src/profile/ui/profile_setup_page.py`
- Modify: `src/app/feature_facades/profile.py`
- Test: `tests/test_profile_setup_page_contract.py`
- Test: `tests/test_preset_profile_async_architecture.py`

- [ ] **Step 1: Write failing tests**

Add contract tests that fail if normal `strategy_only` again goes through full list reload.

- [ ] **Step 2: Remove obsolete broad paths**

Remove only the fallback paths that are now covered by precise tests. Keep broad reload for unknown external changes and stale recovery.

- [ ] **Step 3: Run green tests**

Run: `PYTHONPATH=src python -m unittest tests.test_profile_setup_page_contract tests.test_preset_profile_async_architecture`

### Task 6: Final Verification

**Files:**
- No new files.

- [ ] **Step 1: Run focused profile checks**

Run:

```bash
PYTHONPATH=src python -m unittest \
  tests.test_profile_service_apply_strategy_guards \
  tests.test_profile_setup_page_contract \
  tests.test_preset_profile_async_architecture \
  tests.test_profile_list_payload \
  tests.test_preset_runtime_coordinator \
  tests.test_preset_ui_store_guards
```

- [ ] **Step 2: Run architecture checks**

Run: `PYTHONPATH=src python -m app.architecture_checks`

- [ ] **Step 3: Inspect runtime logs after a Windows build or live run**

Check `C:\Zapret\Dev\logs` and confirm that normal strategy clicks no longer trigger repeated full `profile_list_item.build` work.

- [ ] **Step 4: Inspect git scope**

Run: `git status --short --untracked-files=all`

Only stage files touched by this architecture change. Do not stage unrelated local work.
