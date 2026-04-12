# Execution Quality Research and Attribution Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a mechanism to attribute performance by strategy, price bucket, seconds-to-expiry, etc., by enhancing the trade journal and creating a research report script.

**Architecture:** 
1. Enhance `PendingOrder` and `OpenPos` in `core/runner.py` to track signal price and strategy name.
2. Update `append_event` calls in `core/runner.py` and `core/journal.py` to include `signal_price`, `fill_price`, `slippage`, and `strategy_name`.
3. Update `TradePairRow` and `TradeLeg` in `scripts/journal_analysis.py` to support these new fields.
4. Implement `scripts/research_report.py` to aggregate and report metrics from the journal.

**Tech Stack:** Python, Standard Libraries (json, dataclasses, collections, datetime), Existing project core modules.

---

### Task 1: Update core data structures and journal logic

**Files:**
- Modify: `core/runner.py` (PendingOrder, OpenPos, track_pending_fill, and main loop entry logic)
- Modify: `core/journal.py` (replay_open_positions)
- Modify: `scripts/journal_analysis.py` (TradeLeg, TradePairRow, _finalize_pair_row)

- [ ] **Step 1: Update PendingOrder and OpenPos in core/runner.py**
    - Add `signal_price: float = 0.0` to `PendingOrder`.
    - Add `signal_price: float = 0.0` and `fill_price: float = 0.0` to `OpenPos`.
    - Note: `entry_reason` already serves as `strategy_name`.

- [ ] **Step 2: Update track_pending_fill in core/runner.py**
    - Pass `signal_price` from `PendingOrder` to `OpenPos` and `append_event`.
    - Calculate `fill_price` and `slippage`.

- [ ] **Step 3: Update taker entry logic in core/runner.py (around line 8000)**
    - Include `signal_price`, `fill_price`, `slippage`, and `strategy_name` in the `append_event` call.

- [ ] **Step 4: Update replay_open_positions in core/journal.py**
    - Ensure `signal_price`, `fill_price`, `slippage`, and `strategy_name` are captured in the `lots` dictionary.

- [ ] **Step 5: Update scripts/journal_analysis.py**
    - Add `signal_price`, `fill_price`, `slippage`, and `strategy_name` to `TradeLeg` and `TradePairRow`.
    - Update `build_trade_pairs` and `_finalize_pair_row` to populate these fields.

### Task 2: Implement Research Report Script

**Files:**
- Create: `scripts/research_report.py`

- [ ] **Step 1: Implement scripts/research_report.py**
    - Load events using `read_events`.
    - Use `build_trade_pairs` from `scripts/journal_analysis.py` to get trade rows.
    - Implement bucketing logic for `strategy`, `entry_price_bucket` (0.05 increments), `seconds_to_expiry_bucket` (60s increments), and `realized_slippage_bucket` (0.001 increments).
    - Aggregate metrics: `trade_count`, `win_rate`, `gross_pnl`, `fee_adjusted_pnl`, `average_slippage`, and `average_hold_time`.
    - Print a formatted report.

### Task 3: Verification and Commitment

- [ ] **Step 1: Verify with mock data or existing journal**
    - Run `python scripts/research_report.py` and ensure it doesn't crash and produces reasonable output.

- [ ] **Step 2: Commit the changes**
    - `git add scripts/research_report.py core/journal.py core/runner.py scripts/journal_analysis.py`
    - `git commit -m "feat: add performance attribution reporting pipeline"`

---
