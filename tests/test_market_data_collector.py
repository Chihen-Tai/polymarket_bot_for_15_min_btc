import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.market_data_collector import (
    build_capture_dir_name,
    parse_event_ts,
    safe_fragment,
    summarize_binance_trades,
)


def test_market_data_collector_helpers():
    event = {
        "ts": "2026-03-28T13:18:19",
        "kind": "entry",
        "side": "UP",
        "slug": "btc-updown-5m-1774674900",
        "event_id": "evt_abc123",
    }
    summary = summarize_binance_trades(
        [
            {"p": "100000", "q": "0.10", "m": True},
            {"p": "100100", "q": "0.05", "m": False},
        ]
    )

    assert parse_event_ts(event["ts"]) > 0
    assert safe_fragment("btc/updown?test") == "btc_updown_test"
    assert build_capture_dir_name(event).startswith("2026-03-28T13_18_19_entry_UP_btc-updown-5m-1774674900")
    assert abs(summary["buy_qty"] - 0.10) < 1e-9
    assert abs(summary["sell_qty"] - 0.05) < 1e-9
    assert abs(summary["net_qty"] - 0.05) < 1e-9
