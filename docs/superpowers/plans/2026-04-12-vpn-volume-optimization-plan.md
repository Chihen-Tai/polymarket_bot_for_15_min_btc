# VPN Robustness & Volume Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the bot into an asynchronous, latency-aware system that handles VPN jitter while increasing trade frequency through multi-strategy parallelism.

**Architecture:** Moving from a synchronous "Scan-Decide-Order" loop to a decoupled "Producer (Signal) - Consumer (Execution)" pattern. Introducing a Latency Monitor to dynamically penalize edges based on real-time RTT.

**Tech Stack:** Python, ThreadPoolExecutor, Dataclasses, Pytest.

---

### Task 1: Foundation - Latency Monitor & Config

**Files:**
- Modify: `core/config.py`
- Create: `core/latency_monitor.py`

- [ ] **Step 1: Add VPN-specific settings to `core/config.py`**
Include safety modes, latency thresholds, and volume optimization flags.

```python
# core/config.py
SETTINGS.vpn_safe_mode = True
SETTINGS.max_vpn_latency_ms = 600
SETTINGS.aggressive_volume_mode = True
SETTINGS.max_concurrent_trades = 3
SETTINGS.latency_edge_buffer = 0.015
```

- [ ] **Step 2: Implement `core/latency_monitor.py`**
Create a singleton to track median RTT and calculate edge penalties.

```python
import time
import statistics

class LatencyMonitor:
    def __init__(self):
        self.rtt_history = []
    def record_rtt(self, ms: float):
        self.rtt_history.append(ms)
        if len(self.rtt_history) > 20: self.rtt_history.pop(0)
    def get_current_rtt(self) -> float:
        return statistics.median(self.rtt_history) if self.rtt_history else 300.0
    def get_edge_penalty(self) -> float:
        rtt = self.get_current_rtt()
        return max(0, (rtt - 100) / 100 * 0.015) # Example formula

LATENCY_MONITOR = LatencyMonitor()
```

- [ ] **Step 3: Commit foundation**
```bash
git add core/config.py core/latency_monitor.py
git commit -m "feat: add latency monitor and vpn-aware configs"
```

---

### Task 2: Async Executor - Decoupling Orders from Signal

**Files:**
- Create: `core/executor.py`
- Modify: `core/runner.py`

- [ ] **Step 1: Create `AsyncExecutor` using ThreadPoolExecutor**
Handle API calls in the background to prevent VPN jitter from blocking the signal loop.

```python
from concurrent.futures import ThreadPoolExecutor
from core.latency_monitor import LATENCY_MONITOR
import time

class AsyncExecutor:
    def __init__(self, max_workers=3):
        self.pool = ThreadPoolExecutor(max_workers=max_workers)
    def submit_order(self, func, *args, **kwargs):
        def wrapper():
            start = time.time()
            res = func(*args, **kwargs)
            LATENCY_MONITOR.record_rtt((time.time() - start) * 1000)
            return res
        self.pool.submit(wrapper)

EXECUTOR = AsyncExecutor()
```

- [ ] **Step 2: Update `core/runner.py` to use `EXECUTOR`**
Replace synchronous `place_entry_order_with_retry` calls with `EXECUTOR.submit_order`.

- [ ] **Step 3: Commit async executor**
```bash
git add core/executor.py core/runner.py
git commit -m "feat: decouple order execution via AsyncExecutor"
```

---

### Task 3: Multi-Strategy Orchestration & Latency Penalty

**Files:**
- Modify: `core/decision_engine.py`
- Create: `core/strategies/mean_reversion.py` (Modularized)

- [ ] **Step 1: Update `explain_choose_side` to return multiple candidates**
Allow the engine to return all strategies that meet the edge requirement (plus latency penalty).

```python
# core/decision_engine.py
def explain_choose_side(...):
    # ...
    penalty = LATENCY_MONITOR.get_edge_penalty()
    candidates = []
    # Loop through strategies...
    if res.raw_edge >= (res.required_edge + penalty):
        candidates.append(res)
    return {"ok": True, "candidates": candidates}
```

- [ ] **Step 2: Modularize `Mean Reversion` strategy**
Extract it from the monolith to allow independent execution and testing.

- [ ] **Step 3: Commit orchestration changes**
```bash
git commit -am "refactor: support multi-strategy scanning and latency-aware edge"
```

---

### Task 4: Parallel Trade Management

**Files:**
- Modify: `core/risk.py`
- Modify: `core/runner.py`

- [ ] **Step 1: Update Risk module to allow concurrent trades**
Instead of `has_open_pos`, check `num_open_pos < SETTINGS.max_concurrent_trades`.

- [ ] **Step 2: Update Runner main loop to iterate through candidates**
Dispatch each candidate to the `AsyncExecutor` if risk limits allow.

- [ ] **Step 3: Verify and Commit**
```bash
git commit -am "feat: enable concurrent trade execution and risk management"
```

---

### Task 5: Research Instrumentation for Latency

**Files:**
- Modify: `core/journal.py`
- Modify: `scripts/research_report.py`

- [ ] **Step 1: Record RTT in trade events**
Log the median RTT and signal-to-fill delay for every trade.

- [ ] **Step 2: Update Research Report**
Add "Latency Bucket" and "Execution Delay" to the performance attribution report.

- [ ] **Step 3: Commit research tools**
```bash
git commit -am "feat: add latency attribution to research reporting"
```
