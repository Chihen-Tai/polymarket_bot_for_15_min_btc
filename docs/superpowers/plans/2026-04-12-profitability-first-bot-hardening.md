# Profitability-First Bot Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Polymarket BTC 5-minute bot harder to trick into low-quality trades by fixing runtime truth first, tightening execution/accounting realism second, and only then hardening entry qualification and probability usage.

**Architecture:** The implementation keeps the current bot architecture but changes its priorities. `core/decision_engine.py` continues to generate candidate signals, `core/runner.py` becomes the main qualification layer, `core/exchange.py` and journal/reporting logic become the source of execution truth, and sizing/ranking logic is made more conservative until realized outcomes support stronger EV assumptions.

**Tech Stack:** Python, requests, py-clob-client, existing bot runtime in `core/runner.py`, exchange logic in `core/exchange.py`, configuration in `core/config.py`, runtime persistence in `core/state_store.py` / `core/journal.py` / `core/run_journal.py`, regression tests in `tests/*.py`, and report verification through `scripts/journal_analysis.py` and generated run reports.

---

## File Structure

### Create
- `core/http.py`
  - Centralize safe HTTP JSON requests with TLS verification and sane timeouts.
- `tests/test_http_safety.py`
  - Verify HTTP helpers do not disable certificate verification and use expected defaults.

### Modify
- `main.py`
  - Remove global TLS bypass.
- `core/market_resolver.py`
  - Route market-data fetches through `core/http.py`.
- `core/config.py`
  - Add profitability-first qualification knobs and safer env-loading behavior notes.
- `core/runtime_paths.py`
  - Keep runtime path derivation as the source of truth for dry-run/live path selection.
- `core/state_store.py`
  - Stop freezing `STATE_PATH` at import time; resolve path dynamically per call.
- `core/journal.py`
  - Stop freezing trade journal path at import time.
- `core/run_journal.py`
  - Stop freezing run journal path at import time.
- `core/exchange.py`
  - Repair live account exposure/accounting and real fill-state assumptions.
- `core/runner.py`
  - Harden qualification, maker/taker fallback discipline, and conservative-mode behavior.
- `core/trade_manager.py`
  - Tighten weak-trade cleanup and reduce expensive deadline dependence.
- `core/decision_engine.py`
  - Reduce direct dependence on fixed/high synthetic probabilities for qualification-sensitive paths.
- `scripts/journal_analysis.py`
  - Strengthen actual-vs-observed accounting and fee-adjusted reporting clarity.
- `.env.example`
  - Safer dry-run guidance and comments.
- `.env.live.example`
  - Safer live defaults and comments.
- `README.md`
  - Document the new hardening priorities and verification workflow.
- `tests/test_exit_fix.py`
  - Extend execution/accounting regression coverage.
- `tests/test_trade_manager.py`
  - Extend qualification, conservative mode, and weak-trade recycling coverage.
- `tests/test_runtime_paths.py`
  - Extend path-isolation coverage if needed.

### Verify / Read During Implementation
- `training_datas/latest_run_report-*.txt`
- `training_datas/log-live-*.txt`
- `AI_handoff/AI_HANDOFF_2026-03-29.md`
- `docs/superpowers/specs/2026-04-12-profitability-first-bot-hardening-design.md`

---

### Task 1: Restore transport safety and stop import-time path freezing

**Files:**
- Create: `core/http.py`
- Modify: `main.py`
- Modify: `core/market_resolver.py`
- Modify: `core/state_store.py`
- Modify: `core/journal.py`
- Modify: `core/run_journal.py`
- Test: `tests/test_http_safety.py`
- Test: `tests/test_runtime_paths.py`

- [ ] **Step 1: Write the failing HTTP safety tests**

Create `tests/test_http_safety.py` with:

```python
from core.http import request_json, request_json_with_session


def test_request_json_defaults_to_tls_verification(monkeypatch):
    captured = {}

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    def fake_get(url, **kwargs):
        captured.update(kwargs)
        return DummyResponse()

    monkeypatch.setattr("requests.get", fake_get)

    payload = request_json("https://example.com/markets")

    assert payload == {"ok": True}
    assert captured["verify"] is True
    assert captured["timeout"] == 12


def test_request_json_with_session_uses_verify_true():
    captured = {}

    class DummySession:
        def get(self, url, **kwargs):
            captured.update(kwargs)

            class DummyResponse:
                def raise_for_status(self):
                    return None

                def json(self):
                    return []

            return DummyResponse()

    payload = request_json_with_session(DummySession(), "https://example.com/data")

    assert payload == []
    assert captured["verify"] is True
    assert captured["timeout"] == 12
```

- [ ] **Step 2: Extend runtime path tests so mode-specific files are resolved dynamically**

Add assertions to `tests/test_runtime_paths.py` like:

```python
from core.config import SETTINGS
from core.runtime_paths import runtime_state_path, trade_journal_path, run_journal_path
import core.state_store as state_store
import core.journal as journal
import core.run_journal as run_journal


def test_runtime_paths_follow_current_mode_setting():
    SETTINGS.dry_run = True
    assert runtime_state_path().name == "runtime-state-dryrun.json"
    assert trade_journal_path().name == "trade_journal_dryrun.jsonl"
    assert run_journal_path().name == "run_journal_dryrun.jsonl"

    SETTINGS.dry_run = False
    assert state_store._state_path().name == "runtime-state-live.json"
    assert journal._journal_path().name == "trade_journal_live.jsonl"
    assert run_journal._run_journal_path().name == "run_journal_live.jsonl"
```

- [ ] **Step 3: Run the focused tests to verify they fail**

Run:

```bash
python -m pytest -q tests/test_http_safety.py tests/test_runtime_paths.py
```

Expected: failures because `core.http` does not exist yet and runtime modules still freeze paths at import time.

- [ ] **Step 4: Implement safe HTTP helpers and remove TLS bypass**

Create `core/http.py` with:

```python
from __future__ import annotations

from typing import Any

import requests


DEFAULT_TIMEOUT = 12


def request_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
):
    response = requests.get(url, params=params, timeout=timeout, verify=True)
    response.raise_for_status()
    return response.json()


def request_json_with_session(
    session,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
):
    response = session.get(url, params=params, timeout=timeout, verify=True)
    response.raise_for_status()
    return response.json()
```

Update `main.py` by deleting the global SSL context override entirely.

Update `core/market_resolver.py` to import and use `request_json(...)` instead of raw `requests.get(..., verify=False)`.

- [ ] **Step 5: Implement dynamic path helpers in runtime persistence modules**

Update the modules to stop freezing path constants at import time.

Target shape:

```python
# core/state_store.py
from core.runtime_paths import runtime_state_path


def _state_path():
    return runtime_state_path()


def load_state():
    path = _state_path()
    ...


def save_state(payload):
    path = _state_path()
    ...
```

```python
# core/journal.py
from core.runtime_paths import trade_journal_path


def _journal_path():
    return trade_journal_path()
```

```python
# core/run_journal.py
from core.runtime_paths import run_journal_path


def _run_journal_path():
    return run_journal_path()
```

- [ ] **Step 6: Re-run the focused tests to verify they pass**

Run:

```bash
python -m pytest -q tests/test_http_safety.py tests/test_runtime_paths.py
```

Expected: PASS.

- [ ] **Step 7: Commit the safety foundation if the user explicitly requests commits**

```bash
git add main.py core/http.py core/market_resolver.py core/state_store.py core/journal.py core/run_journal.py tests/test_http_safety.py tests/test_runtime_paths.py
git commit -m "fix: restore transport safety and dynamic runtime paths"
```

---

### Task 2: Make live execution and accounting tell the truth

**Files:**
- Modify: `core/exchange.py`
- Modify: `core/runner.py`
- Modify: `scripts/journal_analysis.py`
- Modify: `.env.live.example`
- Test: `tests/test_exit_fix.py`

- [ ] **Step 1: Write the failing live-accounting tests**

Add to `tests/test_exit_fix.py`:

```python
from core.exchange import PolymarketExchange


def test_live_account_open_exposure_uses_position_notional(monkeypatch):
    ex = PolymarketExchange(dry_run=False)
    ex.client = object()
    ex._funder = "0xtest"

    monkeypatch.setattr(ex, "_get_cash_balance", lambda: 12.0)
    monkeypatch.setattr(ex, "_get_positions_value", lambda: 3.0)
    monkeypatch.setattr(
        ex,
        "get_positions",
        lambda: [
            type(
                "P",
                (),
                {
                    "token_id": "tok1",
                    "size": 10.0,
                    "avg_price": 0.2,
                    "initial_value": 2.0,
                    "current_value": 3.0,
                    "cash_pnl": 1.0,
                    "percent_pnl": 0.5,
                },
            )()
        ],
    )

    acct = ex.get_account()

    assert acct.equity == 15.0
    assert acct.cash == 12.0
    assert acct.open_exposure == 2.0


def test_live_env_example_keeps_loss_guards_enabled():
    text = open(".env.live.example", "r", encoding="utf-8").read()

    assert "MAX_CONSEC_LOSS=99" not in text
    assert "DAILY_MAX_LOSS=999999999" not in text
```

- [ ] **Step 2: Add a failing regression for fake maker-fill confirmation**

Add a helper-level test around the runner-side fill-state logic:

```python
from core.runner import entry_response_has_actionable_state


def test_entry_response_requires_real_order_or_fill_state():
    assert entry_response_has_actionable_state({"ok": True, "filled": False}) is False
    assert entry_response_has_actionable_state({"ok": True, "order_id": "abc"}) is True
```

- [ ] **Step 3: Run the focused test file to verify failures**

Run:

```bash
python -m pytest -q tests/test_exit_fix.py
```

Expected: failures because `get_account()` still under-reports live exposure and runner-side fill truth is still too permissive.

- [ ] **Step 4: Fix live account truth in `core/exchange.py`**

Update `get_account()` to derive exposure from actual open positions.

Target shape:

```python
cash = self._get_cash_balance()
positions_value = self._get_positions_value()
positions = self.get_positions()
open_exposure = sum(
    max(0.0, float(getattr(pos, "initial_value", 0.0) or 0.0))
    for pos in positions
)
equity = cash + positions_value
return Account(equity=equity, cash=cash, open_exposure=open_exposure)
```

- [ ] **Step 5: Tighten actionable-state logic in `core/runner.py`**

Make `entry_response_has_actionable_state()` rely on evidence like `order_id`, `matched`, filled shares, or explicit pending-order state, not on optimistic boolean wrappers.

Target shape:

```python
def entry_response_has_actionable_state(response: dict | None) -> bool:
    if not isinstance(response, dict):
        return False
    if response.get("order_id"):
        return True
    if float(response.get("filled_shares") or 0.0) > 0.0:
        return True
    if bool(response.get("matched")):
        return True
    if bool(response.get("pending_order")):
        return True
    return False
```

- [ ] **Step 6: Make `scripts/journal_analysis.py` surface actual-vs-observed truth more clearly**

Add explicit summary fields for:

```python
summary["actual_minus_observed_gap"] = {
    "count": gap_count,
    "average": avg_gap,
    "sum": sum_gap,
}
summary["close_bucket_actual_vs_observed"] = bucket_gap_summary
```

The goal is to make it obvious when `observed` profitability is still overstating reality.

- [ ] **Step 7: Update `.env.live.example` with safer loss defaults and comments**

Use values shaped like:

```dotenv
MAX_CONSEC_LOSS=3
DAILY_MAX_LOSS=25
LIVE_ORDER_HARD_CAP_USD=20
# Raise only after enough paper/live evidence.
```

- [ ] **Step 8: Re-run the focused tests and a report sanity check**

Run:

```bash
python -m pytest -q tests/test_exit_fix.py
python scripts/journal_analysis.py > /tmp/profitability-hardening-report.txt
```

Expected: tests pass; the report includes explicit actual-vs-observed gap output.

- [ ] **Step 9: Commit the execution-truth layer if the user explicitly requests commits**

```bash
git add core/exchange.py core/runner.py scripts/journal_analysis.py .env.live.example tests/test_exit_fix.py
git commit -m "fix: restore live execution and accounting truth"
```

---

### Task 3: Add a profitability-first qualification layer in runner code

**Files:**
- Modify: `core/config.py`
- Modify: `core/runner.py`
- Modify: `tests/test_trade_manager.py`

- [ ] **Step 1: Write failing qualification tests**

Add to `tests/test_trade_manager.py`:

```python
from core.runner import required_trade_edge, summarize_entry_edge
from core.config import SETTINGS


def test_required_trade_edge_respects_execution_cost_buffer():
    SETTINGS.edge_threshold = 0.02
    SETTINGS.entry_fee_floor_buffer = 1.0
    SETTINGS.entry_execution_cost_buffer = 0.015

    required = required_trade_edge(0.55, 180, history_count=20)

    assert required >= 0.0462


def test_summarize_entry_edge_hard_blocks_neutral_center_prices():
    SETTINGS.entry_neutral_hard_block_half_width = 0.02

    summary = summarize_entry_edge(
        win_rate=0.58,
        entry_price=0.50,
        secs_left=180,
        history_count=20,
    )

    assert summary["ok"] is False
    assert summary["blocked_reason"] == "neutral-no-trade-zone"
```

- [ ] **Step 2: Add a failing conservative-mode regression**

Add to `tests/test_trade_manager.py`:

```python
from core.runner import should_enable_profitability_conservative_mode


def test_conservative_mode_triggers_on_negative_active_close_quality():
    summary = {
        "close_bucket_pnl": {
            "active-close": {
                "count": 3,
                "fee_adjusted_actual_pnl": {"count": 3, "sum": -0.21, "average": -0.07},
            }
        }
    }

    assert should_enable_profitability_conservative_mode(summary) is True
```

- [ ] **Step 3: Run the test file to verify it fails**

Run:

```bash
python -m pytest -q tests/test_trade_manager.py
```

Expected: failures because the new settings and helper behavior do not exist yet.

- [ ] **Step 4: Add qualification knobs to `core/config.py`**

Add environment-backed fields like:

```python
entry_neutral_hard_block_half_width: float = _f("ENTRY_NEUTRAL_HARD_BLOCK_HALF_WIDTH", 0.02)
entry_execution_cost_buffer: float = _f("ENTRY_EXECUTION_COST_BUFFER", 0.015)
entry_require_maker_edge_buffer: float = _f("ENTRY_REQUIRE_MAKER_EDGE_BUFFER", 0.01)
conservative_active_close_loss_streak: int = _i("CONSERVATIVE_ACTIVE_CLOSE_LOSS_STREAK", 3)
conservative_active_close_fee_pnl_floor: float = _f("CONSERVATIVE_ACTIVE_CLOSE_FEE_PNL_FLOOR", -0.05)
conservative_skip_windows: int = _i("CONSERVATIVE_SKIP_WINDOWS", 2)
```

- [ ] **Step 5: Harden `required_trade_edge()` and `summarize_entry_edge()` in `core/runner.py`**

Target shape:

```python
def required_trade_edge(entry_price: float, secs_left: float | None, history_count: int = 0) -> float:
    required = max(0.0, float(getattr(SETTINGS, "edge_threshold", 0.0)))
    fee_floor = float(getattr(SETTINGS, "report_assumed_taker_fee_rate", 0.0156)) * 2.0
    required = max(required, fee_floor * float(getattr(SETTINGS, "entry_fee_floor_buffer", 1.0)))
    required += float(getattr(SETTINGS, "entry_execution_cost_buffer", 0.015) or 0.015)
    # keep existing history / late-entry adjustments here
    return required


def summarize_entry_edge(*, win_rate: float, entry_price: float, secs_left: float | None, history_count: int = 0) -> dict:
    raw_edge = win_rate - entry_price
    neutral_hard_block = abs(float(entry_price) - 0.5) <= float(
        getattr(SETTINGS, "entry_neutral_hard_block_half_width", 0.02) or 0.02
    )
    required = required_trade_edge(entry_price, secs_left, history_count=history_count)
    blocked_reason = "neutral-no-trade-zone" if neutral_hard_block else ""
    return {
        "win_rate": win_rate,
        "entry_price": entry_price,
        "raw_edge": raw_edge,
        "required_edge": required,
        "ok": (raw_edge >= required) and not neutral_hard_block,
        "blocked_reason": blocked_reason,
        "history_count": history_count,
    }
```

- [ ] **Step 6: Add conservative-mode helper and wire it into candidate selection**

Target shape:

```python
def should_enable_profitability_conservative_mode(summary: dict | None) -> bool:
    active_close = ((summary or {}).get("close_bucket_pnl") or {}).get("active-close") or {}
    pnl = active_close.get("fee_adjusted_actual_pnl") or {}
    count = int(pnl.get("count") or 0)
    average = float(pnl.get("average") or 0.0)
    loss_streak = int(getattr(SETTINGS, "conservative_active_close_loss_streak", 3) or 3)
    floor = float(getattr(SETTINGS, "conservative_active_close_fee_pnl_floor", -0.05) or -0.05)
    return count >= loss_streak and average <= floor
```

When the helper returns true, widen required edge and/or skip the next N windows before entering.

- [ ] **Step 7: Re-run the qualification tests**

Run:

```bash
python -m pytest -q tests/test_trade_manager.py
```

Expected: PASS for the new qualification and conservative-mode checks.

- [ ] **Step 8: Commit the qualification layer if the user explicitly requests commits**

```bash
git add core/config.py core/runner.py tests/test_trade_manager.py
git commit -m "feat: add profitability-first qualification layer"
```

---

### Task 4: Tighten weak-trade cleanup and de-risk heuristic probability usage

**Files:**
- Modify: `core/trade_manager.py`
- Modify: `core/decision_engine.py`
- Modify: `tests/test_trade_manager.py`

- [ ] **Step 1: Write a failing weak-trade cleanup regression**

Add a helper-level regression to `tests/test_trade_manager.py` that proves a weak, pre-principal position exits earlier instead of drifting to deadline cleanup.

Use a target like:

```python
def test_pre_principal_weak_trade_recycles_before_deadline():
    decision = decide_position_action(
        observed_return=-0.01,
        profit_return=-0.01,
        max_favorable_excursion=0.01,
        secs_left=70,
        hold_sec=22,
        principal_extracted=False,
        ...,
    )

    assert decision in {"stalled-exit", "failed-follow-through-exit", "close-weak-trade"}
```

- [ ] **Step 2: Write a failing probability-skepticism regression**

Add a decision-engine test proving an extreme hardcoded probability is not allowed to bypass qualification on its own.

Target shape:

```python
def test_fixed_probability_candidate_still_requires_runner_qualification():
    candidate = {
        "ok": True,
        "side": "UP",
        "entry_price": 0.5,
        "model_probability": 0.99,
        "signal_confidence": 1.0,
    }

    scored = score_entry_candidate(candidate, ws_velocity=0.0, secs_left=150, scoreboard=None)

    assert scored["entry_edge"]["ok"] is False
```

- [ ] **Step 3: Run the focused test file and verify failures**

Run:

```bash
python -m pytest -q tests/test_trade_manager.py
```

Expected: failures because weak-trade cleanup is not yet aggressive enough and synthetic confidence still leaks too much influence.

- [ ] **Step 4: Tighten weak-trade cleanup in `core/trade_manager.py`**

Bias the pre-principal branch toward smaller earlier exits.

Target shape:

```python
if not principal_extracted and secs_left is not None and secs_left <= 75:
    if mfe_pct <= weak_trade_max_mfe and current_pnl_pct <= weak_trade_floor:
        return "close-weak-trade"
```

Use existing stop/failed-follow-through/stalled-exit logic where possible instead of adding many new overlapping branches.

- [ ] **Step 5: De-risk synthetic probability usage in `core/decision_engine.py`**

Do not remove all strategy outputs. Instead:

```python
extras = {
    ...,
    "probability_source": "heuristic",
}
```

And avoid using extreme fixed probabilities to bypass stabilization-sensitive paths. Prefer moderate ranges or let runner-side qualification dominate final accept/reject decisions.

- [ ] **Step 6: Re-run qualification/cleanup tests**

Run:

```bash
python -m pytest -q tests/test_trade_manager.py
```

Expected: PASS for the new weak-trade and synthetic-probability regressions.

- [ ] **Step 7: Commit the cleanup/calibration pass if the user explicitly requests commits**

```bash
git add core/trade_manager.py core/decision_engine.py tests/test_trade_manager.py
git commit -m "refactor: de-risk weak trades and synthetic probability usage"
```

---

### Task 5: Verify with code tests and report evidence

**Files:**
- Verify: `tests/test_http_safety.py`
- Verify: `tests/test_runtime_paths.py`
- Verify: `tests/test_exit_fix.py`
- Verify: `tests/test_trade_manager.py`
- Verify: `scripts/journal_analysis.py`
- Read: `training_datas/latest_run_report-*.txt`

- [ ] **Step 1: Run the focused regression suite**

Run:

```bash
python -m pytest -q tests/test_http_safety.py tests/test_runtime_paths.py tests/test_exit_fix.py tests/test_trade_manager.py
```

Expected: PASS.

- [ ] **Step 2: Run syntax verification on touched modules**

Run:

```bash
python -m py_compile main.py core/*.py scripts/journal_analysis.py tests/test_http_safety.py tests/test_exit_fix.py tests/test_trade_manager.py tests/test_runtime_paths.py
```

Expected: no output, exit code 0.

- [ ] **Step 3: Run report generation against available data**

Run:

```bash
python scripts/journal_analysis.py > /tmp/polymarket-profitability-report.txt
```

Expected: report generation succeeds and exposes actual-vs-observed gaps.

- [ ] **Step 4: Inspect report quality, not just test status**

Confirm the generated report or recent `training_datas/latest_run_report-*.txt` shows movement in the intended direction:

```text
- fewer neutral-zone trades
- lower deadline-active-close dependence
- clearer actual-vs-observed separation
- no evidence that heuristic probabilities bypass qualification
```

- [ ] **Step 5: Update README guidance**

Document:

```markdown
- live mode now assumes TLS verification and safer defaults
- qualification is stricter than before
- actual-vs-observed report deltas must be reviewed before claiming profitability improvements
- do not increase size until fee-adjusted active-close results improve
```

- [ ] **Step 6: Commit documentation and verification updates if the user explicitly requests commits**

```bash
git add README.md tests/test_http_safety.py tests/test_runtime_paths.py tests/test_exit_fix.py tests/test_trade_manager.py scripts/journal_analysis.py
git commit -m "docs: document profitability-first verification workflow"
```

---

## Self-Review

### Spec coverage

- Truth layer: covered by Task 1 and Task 2.
- Qualification layer: covered by Task 3.
- Signal de-risking and weak-trade cleanup: covered by Task 4.
- Reporting validation: covered by Task 5.

### Placeholder scan

- No `TODO`, `TBD`, or "implement later" placeholders remain.
- Each task includes exact file paths, commands, and target code shapes.

### Type consistency

- Helper names used in tests (`_state_path`, `_journal_path`, `_run_journal_path`, `should_enable_profitability_conservative_mode`) are defined in the plan before later references.
- The plan keeps `core/decision_engine.py` as signal generation and `core/runner.py` as final qualification, matching the design spec.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-12-profitability-first-bot-hardening.md`.

Two execution options:

**1. Subagent-Driven (recommended)** — execute one task at a time with a fresh subagent and review between tasks.

**2. Inline Execution** — execute tasks in this session in controlled batches with checkpoints.
