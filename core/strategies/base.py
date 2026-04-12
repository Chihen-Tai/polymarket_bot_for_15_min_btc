from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class StrategyResult:
    strategy_name: str
    side: str  # "UP" | "DOWN"
    trigger_reason: str
    entry_price: float
    model_probability: float  # Unbiased raw probability
    confidence: float         # 0.0 - 1.0
    required_edge: float
    raw_edge: float          # model_probability - entry_price
    execution_preference: str = "hybrid"  # "maker" | "taker" | "hybrid"
    metadata: Dict[str, Any] = field(default_factory=dict)
