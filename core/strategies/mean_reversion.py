from __future__ import annotations
from collections import deque
from typing import Optional
from core.strategies.base import StrategyResult

def run(
    yes_price: Optional[float], 
    yes_window: deque, 
    settings: any
) -> Optional[StrategyResult]:
    """
    Standardized Mean Reversion strategy.
    Extracts the logic from decision_engine for cleaner multi-strategy management.
    """
    if yes_price is None or len(yes_window) < 10:
        return None
        
    vals = list(yes_window)
    mean = sum(vals) / len(vals)
    var = sum((x - mean) ** 2 for x in vals) / len(vals)
    std = var**0.5
    
    if std <= 1e-9:
        return None
        
    z = (yes_price - mean) / std
    
    # Threshold check
    threshold = float(getattr(settings, "zscore_threshold", 2.0))
    if abs(z) < threshold:
        return None
        
    side = "DOWN" if z > threshold else "UP"
    
    # Calculate confidence and probability
    # Logic matched from original decision_engine.py
    def _clamp(value: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, value))

    def _confidence_from_signal(strength: float, trigger: float, ceiling: float) -> float:
        if ceiling <= trigger:
            return 1.0 if strength >= trigger else 0.0
        return _clamp((strength - trigger) / max(ceiling - trigger, 1e-9), 0.0, 1.0)

    def _probability_from_confidence(confidence: float, *, floor: float, ceiling: float) -> float:
        confidence = _clamp(confidence, 0.0, 1.0)
        return floor + (ceiling - floor) * confidence

    mr_confidence = _confidence_from_signal(
        abs(z),
        threshold,
        threshold * 2.0,
    )
    # signal_score represents the heuristic strength of the setup
    # A z-score of 2.0+ starts at 0.55 score, up to 0.85 at z-score 4.0+
    signal_score = 0.55 + (0.30 * mr_confidence)
    
    # Required edge baseline before dynamic fee evaluation
    required_edge = 0.05
    
    return StrategyResult(
        strategy_name="mean_reversion",
        side=side,
        entry_price=float(yes_price),
        signal_score=signal_score,
        confidence=mr_confidence,
        required_edge=required_edge,
        raw_edge=signal_score - yes_price,
        trigger_reason=f"zscore_{z:.2f}",
        metadata={"mr_zscore": z}
    )
