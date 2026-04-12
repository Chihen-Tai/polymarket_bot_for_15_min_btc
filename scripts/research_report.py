#!/usr/bin/env python3
import json
import sys
from collections import defaultdict, Counter
from pathlib import Path

def get_bucket(val, thresholds, labels):
    for i, t in enumerate(thresholds):
        if val < t:
            return labels[i]
    return labels[-1]

def analyze_journal(journal_path):
    if not Path(journal_path).exists():
        print(f"Error: {journal_path} not found.")
        return

    stats = defaultdict(lambda: {
        "count": 0, "wins": 0, "gross_pnl": 0.0, 
        "total_slippage": 0.0, "total_hold": 0.0,
        "fee_adjusted_pnl": 0.0
    })

    # Global counters
    total_trades = 0
    shadow_signals = []

    with open(journal_path, "r") as f:
        trades = {} # token_id -> entry_event
        
        for line in f:
            try:
                ev = json.loads(line)
            except:
                continue
                
            kind = ev.get("kind")
            if kind == "shadow_signal":
                shadow_signals.append(ev)
                continue

            token_id = ev.get("token_id")
            if not token_id: continue

            if kind == "entry":
                trades[token_id] = ev
            elif kind == "exit" and token_id in trades:
                entry = trades[token_id]
                exit_ev = ev
                
                strategy = entry.get("strategy_name") or entry.get("entry_reason") or "unknown"
                profile = entry.get("market_profile") or "btc_5m"
                regime = entry.get("regime") or "unknown"
                price = float(entry.get("signal_price") or entry.get("entry_price") or 0.5)
                secs_left = float(entry.get("secs_left") or 120)
                slippage = float(exit_ev.get("slippage") or 0.0)
                
                pnl = float(exit_ev.get("actual_realized_pnl_usd") or exit_ev.get("observed_realized_pnl_usd") or 0.0)
                win = 1 if pnl > 0 else 0
                
                fees = float(exit_ev.get("fees_usd") or 0.0)
                if fees == 0:
                    fees = (float(entry.get("cost_usd") or 0) + float(exit_ev.get("realized_cost_usd") or 0)) * 0.001
                
                fee_adj_pnl = pnl - fees
                hold_time = float(exit_ev.get("hold_sec") or 0.0)
                rtt_ms = float(entry.get("rtt_ms") or 0.0)

                # Bucketing
                price_bucket = get_bucket(price, [0.3, 0.5, 0.7, 0.85, 0.90], ["<0.3", "0.3-0.5", "0.5-0.7", "0.7-0.85", "0.85-0.90", ">0.90"])
                
                # Update Stats
                group_keys = [
                    ("strategy", strategy), 
                    ("profile", profile), 
                    ("regime", regime),
                    ("price", price_bucket)
                ]
                for key in group_keys:
                    s = stats[key]
                    s["count"] += 1
                    s["wins"] += win
                    s["gross_pnl"] += pnl
                    s["fee_adjusted_pnl"] += fee_adj_pnl
                    s["total_slippage"] += slippage
                    s["total_hold"] += hold_time
                
                total_trades += 1

    # Print Report
    print(f"\n{'='*80}")
    print(f" RESEARCH ATTRIBUTION REPORT (Total Trades: {total_trades}) ")
    print(f"{'='*80}\n")

    if shadow_signals:
        print(f"--- Blocked Trades (Shadow Journal) ---")
        reasons = Counter(s.get("reason") for s in shadow_signals)
        print(f"Total Blocked: {len(shadow_signals)}")
        for r, count in reasons.most_common(5):
            print(f"  {r:<40}: {count}")
        print()

    for category in ["profile", "regime", "strategy", "price"]:
        print(f"--- By {category.capitalize()} ---")
        print(f"{'Key':<25} | {'Count':<5} | {'Win%':<6} | {'Gross PnL':<10} | {'Fee-Adj PnL':<10} | {'Slippage':<8}")
        print("-" * 80)
        
        items = [item for item in stats.items() if item[0][0] == category]
        items.sort(key=lambda x: x[1]["fee_adjusted_pnl"], reverse=True)
        
        for (cat, key), s in items:
            win_rate = (s["wins"] / s["count"] * 100) if s["count"] > 0 else 0
            avg_slip = (s["total_slippage"] / s["count"]) if s["count"] > 0 else 0
            print(f"{key:<25} | {s['count']:<5} | {win_rate:>5.1f}% | {s['gross_pnl']:>10.4f} | {s['fee_adjusted_pnl']:>10.4f} | {avg_slip:>8.4f}")
        print()

if __name__ == "__main__":
    path = "market_data/trade_journal.jsonl"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    analyze_journal(path)
