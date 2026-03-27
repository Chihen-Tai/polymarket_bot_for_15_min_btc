import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.runner import OpenPos, PendingOrder, clear_expired_market_state
from core.runtime_paths import mode_label, run_journal_path, runtime_state_path, trade_journal_path


def main():
    cases = [
        ("dryrun_mode_label", mode_label(dry_run=True) == "dryrun"),
        ("live_mode_label", mode_label(dry_run=False) == "live"),
        ("dryrun_trade_journal_is_separate", trade_journal_path(dry_run=True).name == "trade_journal-dryrun.jsonl"),
        ("live_trade_journal_is_separate", trade_journal_path(dry_run=False).name == "trade_journal-live.jsonl"),
        ("dryrun_run_journal_is_separate", run_journal_path(dry_run=True).name == "run_journal-dryrun.jsonl"),
        ("live_run_journal_is_separate", run_journal_path(dry_run=False).name == "run_journal-live.jsonl"),
        ("dryrun_state_is_separate", runtime_state_path(dry_run=True).name == ".runtime_state-dryrun.json"),
        ("live_state_is_separate", runtime_state_path(dry_run=False).name == ".runtime_state-live.json"),
    ]

    canceled: list[str] = []
    kept_positions, kept_pending, cleanup_notes = clear_expired_market_state(
        "btc-updown-5m-current",
        [
            OpenPos(
                slug="btc-updown-5m-old",
                side="UP",
                token_id="oldtok",
                shares=5.0,
                cost_usd=2.0,
                opened_ts=1.0,
            ),
            OpenPos(
                slug="btc-updown-5m-current",
                side="DOWN",
                token_id="curtok",
                shares=5.0,
                cost_usd=2.0,
                opened_ts=1.0,
            ),
        ],
        [
            PendingOrder(
                order_id="old-order",
                slug="btc-updown-5m-old",
                side="UP",
                token_id="oldtok",
                placed_ts=1.0,
                order_usd=1.0,
            ),
            PendingOrder(
                order_id="cur-order",
                slug="btc-updown-5m-current",
                side="DOWN",
                token_id="curtok",
                placed_ts=1.0,
                order_usd=1.0,
            ),
        ],
        cancel_order=lambda order_id: canceled.append(order_id),
    )
    cases.extend([
        ("expired_market_keeps_only_current_position", len(kept_positions) == 1 and kept_positions[0].slug == "btc-updown-5m-current"),
        ("expired_market_keeps_only_current_pending_order", len(kept_pending) == 1 and kept_pending[0].slug == "btc-updown-5m-current"),
        ("expired_market_cancels_old_pending_order", canceled == ["old-order"]),
        ("expired_market_logs_cleanup", any("clear expired live runtime position" in note for note in cleanup_notes)),
    ])

    failed = [name for name, ok in cases if not ok]
    if failed:
        raise SystemExit(f"FAILED: {', '.join(failed)}")
    print("OK")


def test_main():
    main()


if __name__ == "__main__":
    main()
