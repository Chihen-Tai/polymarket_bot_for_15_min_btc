from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.config import SETTINGS


@dataclass
class ExitDecision:
    should_close: bool
    reason: str = ""
    pnl_pct: float = 0.0
    hold_sec: float = 0.0


@dataclass
class EntryDecision:
    side: Optional[str]
    reason: str = ""


def _decide_exit_15m(
    *,
    pnl_pct: float,
    hold_sec: float,
    secs_left: Optional[float] = None,
    fair_value: float = 0.5,
    side: str = "UP",
    ob_bids: list = None,
    shares: float = 0.0,
) -> ExitDecision:
    """
    Sniper 模式出場邏輯：持倉到期 (Hold-to-Expiry)。
    我們在高邊際進場，目標是獲取全額賠付。
    """
    # 1. 災難性止損 (30%) - 針對極端波動的寬鬆止損
    if pnl_pct <= -0.30:
        return ExitDecision(True, "catastrophic-reversal-stop", pnl_pct, hold_sec)

    # 2. 確定性持倉 (Expiry-First Certainty Hold)
    # 如果已經快到期，且勝率極高，絕對不平倉。
    pos_fv = fair_value if side == "UP" else (1.0 - fair_value)
    if secs_left is not None and secs_left <= 15.0:
        if pos_fv >= 0.90:
            return ExitDecision(False, "sniper-hold-to-settle", pnl_pct, hold_sec)
        
        # 否則在最後 15 秒清理不確定部位
        reason = "deadline-exit-loss" if pnl_pct <= 0 else "deadline-exit-win"
        return ExitDecision(True, reason, pnl_pct, hold_sec)

    # 3. 預設：持有到期
    # 移除所有中間的 strategic-take-profit，因為 Taker 費與價差會吃掉優勢。
    return ExitDecision(False, "hold", pnl_pct, hold_sec)


def decide_exit(
    *,
    pnl_pct: float,
    hold_sec: float,
    secs_left: Optional[float] = None,
    fair_value: float = 0.5,
    side: str = "UP",
    ob_bids: list = None,
    shares: float = 0.0,
) -> ExitDecision:
    # 0. 15m Default Path (Execution-First: Expiry Priority)
    if SETTINGS.market_profile == "btc_15m":
        return _decide_exit_15m(
            pnl_pct=pnl_pct,
            hold_sec=hold_sec,
            secs_left=secs_left,
            fair_value=fair_value,
            side=side,
            ob_bids=ob_bids,
            shares=shares,
        )

    # Legacy 5m / Non-15m Path (Maintained for safety, but simplified)
    # 1. Hard Stop Loss (Absolute Safety)
    if pnl_pct <= -SETTINGS.stop_loss_pct:
        return ExitDecision(True, "hard-stop-loss", pnl_pct, hold_sec)

    # 2. Hold to Expiry / Deadline Exit
    if secs_left is not None:
        exit_deadline = float(getattr(SETTINGS, "exit_deadline_sec", 15.0))
        if secs_left <= exit_deadline:
            if pnl_pct <= 0:
                return ExitDecision(True, "deadline-exit-loss", pnl_pct, hold_sec)
            return ExitDecision(True, "deadline-exit-win", pnl_pct, hold_sec)

    # 3. Max Hold Failsafe
    if hold_sec >= SETTINGS.max_hold_seconds and pnl_pct < 0:
        return ExitDecision(True, "max-hold-loss", pnl_pct, hold_sec)

    return ExitDecision(False, "hold", pnl_pct, hold_sec)


def maybe_reverse_entry(
    *, signal_side: Optional[str], live_consec_losses: int, last_loss_side: str
) -> EntryDecision:
    if (
        signal_side in {"UP", "DOWN"}
        and live_consec_losses >= 2
        and last_loss_side == signal_side
    ):
        return EntryDecision("DOWN" if signal_side == "UP" else "UP", "loss-reversal")
    return EntryDecision(signal_side, "")


def should_block_same_market_reentry(
    exit_reason: str | None,
    *,
    remaining_shares: float = 0.0,
    realized_pnl_usd: Optional[float] = None,
) -> bool:
    """
    Classifies exit reasons to determine if same-market reentry should be blocked.
    """
    if float(remaining_shares or 0.0) > 1e-6:
        return False

    normalized = str(exit_reason or "").strip().lower()
    
    # Category A: Hard Block (Losses, Defensive exits, Failures)
    hard_block_reasons = {
        "hard-stop-loss",
        "stop-loss",
        "stop-loss-full",
        "stop-loss-scale-out",
        "failed-follow-through",
        "stalled-trade",
        "deadline-exit-loss",
        "residual-force-close",
        "post-scaleout-stop-loss",
        "max-hold-loss",
        "max-hold-loss-extended",
        "binance-adverse-exit",
        "moonbag-drawdown-stop",
    }
    
    if normalized in hard_block_reasons:
        return True

    # If we realized a net loss, block reentry to prevent revenge trading
    if realized_pnl_usd is not None and float(realized_pnl_usd) < -0.01:
        return True

    # Category B & C: Profits and Benign outcomes do NOT block reentry.
    # Examples: deadline-exit-win, strategic-take-profit, signal-but-no-fill, etc.
    return False


def can_reenter_same_market(
    *,
    has_current_market_pos: bool,
    closed_any: bool,
    secs_left: Optional[float],
    current_market_slug: str = "",
    blocked_market_slug: str = "",
) -> bool:
    min_secs_left = float(getattr(SETTINGS, "same_market_reentry_min_secs_left", 60))
    if has_current_market_pos or secs_left is None or secs_left < min_secs_left:
        return False
    normalized_current_slug = str(current_market_slug or "").strip()
    normalized_blocked_slug = str(blocked_market_slug or "").strip()
    if (
        normalized_current_slug
        and normalized_blocked_slug
        and normalized_current_slug == normalized_blocked_slug
    ):
        return False
    return bool(closed_any or not normalized_blocked_slug)
