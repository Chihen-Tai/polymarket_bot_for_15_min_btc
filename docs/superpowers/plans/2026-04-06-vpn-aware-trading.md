# VPN-Aware Trading Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add VPN-specific settings to core/config.py and create the LatencyMonitor class to handle network latency in trading decisions.

**Architecture:** Update the global configuration with VPN-aware parameters and implement a rolling-window latency monitor that calculates edge penalties based on network performance.

**Tech Stack:** Python, standard library (collections, statistics), pytest for testing.

---

### Task 1: Update core/config.py

**Files:**
- Modify: `core/config.py`

- [ ] **Step 1: Add VPN-specific settings to Settings dataclass**

Add the following fields to `Settings` in `core/config.py`:
- `vpn_safe_mode`: bool = _b("VPN_SAFE_MODE", True)
- `max_vpn_latency_ms`: float = _f("MAX_VPN_LATENCY_MS", 600.0)
- `aggressive_volume_mode`: bool = _b("AGGRESSIVE_VOLUME_MODE", True)
- `max_concurrent_trades`: int = _i("MAX_CONCURRENT_TRADES", 3)
- `latency_edge_buffer`: float = _f("LATENCY_EDGE_BUFFER", 0.015)

### Task 2: Create core/latency_monitor.py

**Files:**
- Create: `core/latency_monitor.py`

- [ ] **Step 1: Write the failing test for LatencyMonitor**

Create `tests/test_latency_monitor.py`.

```python
import pytest
from core.latency_monitor import LatencyMonitor

def test_latency_monitor_median():
    monitor = LatencyMonitor(history_size=5)
    for rtt in [100, 200, 300, 400, 500]:
        monitor.add_rtt(rtt)
    assert monitor.get_median_rtt() == 300

def test_latency_monitor_edge_penalty():
    monitor = LatencyMonitor(history_size=5)
    monitor.latency_edge_buffer = 0.015
    
    # 100ms -> penalty 0
    monitor.add_rtt(100)
    assert monitor.get_edge_penalty() == 0.0
    
    # 200ms -> (200-100)/100 * 0.015 = 0.015
    monitor.add_rtt(200)
    # Median of [100, 200] is 150
    # (150-100)/100 * 0.015 = 0.0075
    assert monitor.get_edge_penalty() == 0.0075
    
    monitor.add_rtt(300) # Median 200
    # (200-100)/100 * 0.015 = 0.015
    assert monitor.get_edge_penalty() == 0.015
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_latency_monitor.py`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement LatencyMonitor**

```python
import collections
import statistics

class LatencyMonitor:
    def __init__(self, history_size=20):
        self.rtts = collections.deque(maxlen=history_size)
        # We will import SETTINGS here to avoid circular imports if needed, 
        # or just use a default that can be overridden.
        self.latency_edge_buffer = 0.015 

    def add_rtt(self, rtt_ms: float):
        self.rtts.append(rtt_ms)

    def get_median_rtt(self) -> float:
        if not self.rtts:
            return 0.0
        return statistics.median(self.rtts)

    def get_edge_penalty(self) -> float:
        median_rtt = self.get_median_rtt()
        return max(0.0, (median_rtt - 100.0) / 100.0 * self.latency_edge_buffer)

LATENCY_MONITOR = LatencyMonitor()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_latency_monitor.py`
Expected: PASS

- [ ] **Step 5: Integrate SETTINGS into LATENCY_MONITOR**

Update `core/latency_monitor.py` to use `SETTINGS.latency_edge_buffer`.

```python
from core.config import SETTINGS

class LatencyMonitor:
    def __init__(self, history_size=20):
        self.rtts = collections.deque(maxlen=history_size)

    def add_rtt(self, rtt_ms: float):
        self.rtts.append(rtt_ms)

    def get_median_rtt(self) -> float:
        if not self.rtts:
            return 0.0
        return statistics.median(self.rtts)

    def get_edge_penalty(self) -> float:
        median_rtt = self.get_median_rtt()
        return max(0.0, (median_rtt - 100.0) / 100.0 * SETTINGS.latency_edge_buffer)

LATENCY_MONITOR = LatencyMonitor()
```

- [ ] **Step 6: Final Verification and Commit**

Run: `pytest tests/test_latency_monitor.py`
Commit: `git add core/config.py core/latency_monitor.py tests/test_latency_monitor.py && git commit -m "feat: add latency monitor and vpn-aware configs"`
