from __future__ import annotations
from typing import Any, Optional
from core.strategies.base import StrategyResult

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))

def _confidence_from_signal(strength: float, trigger: float, ceiling: float) -> float:
    if ceiling <= trigger:
        return 1.0 if strength >= trigger else 0.0
    return _clamp((strength - trigger) / max(ceiling - trigger, 1e-9), 0.0, 1.0)

def _probability_from_confidence(confidence: float, *, floor: float, ceiling: float) -> float:
    confidence = _clamp(confidence, 0.0, 1.0)
    return floor + (ceiling - floor) * confidence

def get_flash_snipe_signal(
    vel: float,
    up_price: float,
    down_price: float,
    snipe_valid_up: bool,
    snipe_valid_down: bool,
    settings: Any
) -> list[StrategyResult]:
    results = []
    
    flash_threshold = float(getattr(settings, "ws_flash_snipe_threshold", 0.0))
    if flash_threshold <= 0:
        return results

    flash_confidence = _confidence_from_signal(abs(vel), flash_threshold, flash_threshold * 2.0)
    # Raw probability calculation (0.54 - 0.88)
    flash_probability = _probability_from_confidence(flash_confidence, floor=0.54, ceiling=0.88)
    
    # Required edge for momentum strategies in decision_engine.py was effectively 0.05
    required_edge = 0.05

    if vel > flash_threshold and snipe_valid_up:
        results.append(StrategyResult(
            strategy_name="model-ws_flash_snipe_up",
            side="UP",
            trigger_reason="flash_snipe_up",
            entry_price=float(up_price),
            model_probability=flash_probability,
            confidence=flash_confidence,
            required_edge=required_edge,
            raw_edge=flash_probability - float(up_price),
            metadata={"velocity_3s": vel}
        ))
    elif vel < -flash_threshold and snipe_valid_down:
        results.append(StrategyResult(
            strategy_name="model-ws_flash_snipe_down",
            side="DOWN",
            trigger_reason="flash_snipe_down",
            entry_price=float(down_price),
            model_probability=flash_probability,
            confidence=flash_confidence,
            required_edge=required_edge,
            raw_edge=flash_probability - float(down_price),
            metadata={"velocity_3s": vel}
        ))
        
    return results
