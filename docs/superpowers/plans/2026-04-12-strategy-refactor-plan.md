# Strategy Layer Refactor & Research Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the bloated decision engine into modular, unbiased strategy units and establish a data-driven attribution pipeline for real edge verification.

**Architecture:** Moving from a monolithic `if/else` block in `decision_engine.py` to a plugin-based orchestrator. Exits are simplified into a clean 5-state machine. Performance is tracked via a new attribution-aware journal.

**Tech Stack:** Python, Dataclasses, Pytest.

---

### Task 1: Foundation - Strategy Base and Schema

**Files:**
- Create: `core/strategies/base.py`
- Create: `core/strategies/__init__.py`

- [ ] **Step 1: Define the `StrategyResult` dataclass**
Standardize the output for all strategies.

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class StrategyResult:
    strategy_name: str
    side: str  # "UP" | "DOWN"
    trigger_reason: str
    entry_price: float
    model_probability: float  # Unbiased raw probability
    confidence: float         # 0.0 - 1.0
    required_edge: float
    raw_edge: float          # model_probability - entry_price
    execution_preference: str = "hybrid"  # "maker" | "taker" | "hybrid"
    metadata: Dict[str, Any] = field(default_factory=dict)
```

- [ ] **Step 2: Commit base structure**
```bash
git add core/strategies/
git commit -m "refactor: add strategy base schema"
```

---

### Task 2: Extract Core Strategies (Phase 1: WS Flow & Snipe)

**Files:**
- Create: `core/strategies/ws_order_flow.py`
- Create: `core/strategies/ws_flash_snipe.py`
- Create: `tests/test_strategies_migration.py`

- [ ] **Step 1: Implement WS Order Flow Strategy**
Port logic from `decision_engine.py` without probability inflation.

```python
# core/strategies/ws_order_flow.py
from .base import StrategyResult
from core.indicators import compute_buy_sell_pressure

def get_ofi_signal(ws_trades, up_price, down_price, settings) -> list[StrategyResult]:
    # ... logic from Strategy 6 ...
    # Return StrategyResult with raw ofi_probability
```

- [ ] **Step 2: Write tests for WS Order Flow**
Verify it triggers correctly given mock trade data.

- [ ] **Step 3: Implement WS Flash Snipe Strategy**
Port Strategy 7.

- [ ] **Step 4: Commit Phase 1 strategies**
```bash
git add core/strategies/ tests/
git commit -m "feat: migrate ws_order_flow and ws_flash_snipe to modular form"
```

---

### Task 3: Simplify Exit State Machine

**Files:**
- Modify: `core/trade_manager.py`

- [ ] **Step 1: Define the 5 core states**
Replace the tiered `if/else` with a clear state transition check.

```python
# core/trade_manager.py
# States: FRESH_ENTRY, SOFT_PROFIT, PRINCIPAL_EXTRACTED, EMERGENCY_LOSS, EXPIRY_HOLD
```

- [ ] **Step 2: Refactor `decide_exit`**
Minimize rule overlap. Ensure `emergency_loss` (hard stop) and `expiry_hold` (deadline) have clear precedence.

- [ ] **Step 3: Verify exit tests**
Run `pytest tests/test_trade_manager.py` to ensure no regression in safety.

- [ ] **Step 4: Commit exit refactor**
```bash
git commit -am "refactor: simplify trade manager into 5-state machine"
```

---

### Task 4: Orchestrate Decision Engine & Remove Inflation

**Files:**
- Modify: `core/decision_engine.py`

- [ ] **Step 1: Replace hardcoded strategy blocks with module calls**
Loop through registered strategies in `core/strategies/`.

- [ ] **Step 2: Remove `_build_candidate` probability boosting**
Delete the code that adds 0.05 to probability just to pass edge filters.

- [ ] **Step 3: Commit engine cleanup**
```bash
git commit -am "refactor: convert decision_engine to orchestrator and remove bias"
```

---

### Task 5: Research Pipeline - Attribution & Reporting

**Files:**
- Modify: `core/journal.py`
- Create: `scripts/research_report.py`

- [ ] **Step 1: Add instrumentation for signal vs fill price**
Record `signal_price` at the moment of `StrategyResult` generation.

- [ ] **Step 2: Implement Reporting Script**
Create a script that parses logs/journal and buckets PnL by Strategy, Time-to-Expiry, and Slippage.

- [ ] **Step 3: Run report on existing logs (if any compatible)**
```bash
python scripts/research_report.py
```

- [ ] **Step 4: Commit reporting tools**
```bash
git add scripts/research_report.py
git commit -m "feat: add performance attribution reporting pipeline"
```
