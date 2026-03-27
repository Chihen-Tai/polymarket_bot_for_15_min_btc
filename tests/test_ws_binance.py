import os
import sys
from collections import deque

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core.ws_binance as ws_mod
from core.ws_binance import BinanceWebSocket


def main():
    ws = BinanceWebSocket("btcusdt")
    ws.running = False
    ws.bba = {"b": 0.0, "B": 0.0, "a": 0.0, "A": 0.0, "ts": 0.0, "u": 0}
    ws.bba_history = deque([
        {"b": 100.0, "B": 1.0, "a": 101.0, "A": 1.0, "ts": 10.0, "u": 1},
        {"b": 102.0, "B": 1.0, "a": 103.0, "A": 1.0, "ts": 10.6, "u": 2},
        {"b": 104.0, "B": 1.0, "a": 105.0, "A": 1.0, "ts": 11.2, "u": 3},
    ], maxlen=2000)
    ws.bba = ws.bba_history[-1].copy()
    ws.trades = deque([
        {"p": 100.0, "q": 1.0, "m": False, "ts": 9.7},
        {"p": 101.0, "q": 1.0, "m": False, "ts": 10.2},
        {"p": 102.0, "q": 1.0, "m": False, "ts": 10.9},
        {"p": 103.0, "q": 1.0, "m": False, "ts": 11.3},
    ], maxlen=5000)
    ws.recent_prices = deque([
        (10.0, 100.5),
        (10.5, 101.5),
        (11.0, 102.5),
        (11.5, 103.5),
    ], maxlen=200)

    original_time = ws_mod.time.time
    ws_mod.time.time = lambda: 11.5
    try:
        lagged_bba = ws.get_bba(lag_sec=0.5)
        lagged_trades = ws.get_recent_trades(seconds=1.0, lag_sec=0.5)
        lagged_velocity = ws.get_price_velocity(seconds=1.0, lag_sec=0.5)
        current_velocity = ws.get_price_velocity(seconds=1.0, lag_sec=0.0)
    finally:
        ws_mod.time.time = original_time

    cases = [
        ("lagged_bba_uses_snapshot_before_cutoff", abs(lagged_bba["b"] - 102.0) < 1e-9 and abs(lagged_bba["a"] - 103.0) < 1e-9),
        ("lagged_trades_excludes_newest_trade", [round(t["ts"], 1) for t in lagged_trades] == [10.2, 10.9]),
        ("lagged_velocity_uses_window_ending_at_lagged_now", abs(lagged_velocity - ((102.5 - 100.5) / 100.5)) < 1e-9),
        ("current_velocity_still_uses_latest_window", abs(current_velocity - ((103.5 - 101.5) / 101.5)) < 1e-9),
    ]

    failed = [name for name, ok in cases if not ok]
    if failed:
        raise SystemExit(f"FAILED: {', '.join(failed)}")
    print("OK")


def test_main():
    main()


if __name__ == "__main__":
    main()
