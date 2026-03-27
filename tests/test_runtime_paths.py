import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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

    failed = [name for name, ok in cases if not ok]
    if failed:
        raise SystemExit(f"FAILED: {', '.join(failed)}")
    print("OK")


def test_main():
    main()


if __name__ == "__main__":
    main()
