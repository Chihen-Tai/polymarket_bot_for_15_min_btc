
import unittest
from unittest.mock import MagicMock, patch
from collections import deque
from core.decision_engine import explain_choose_side
from core.strategies.base import StrategyResult

class TestDecisionEngineLatency(unittest.TestCase):
    def setUp(self):
        self.market = {
            "outcomes": ["Up", "Down"],
            "outcomePrices": ["0.50", "0.50"],
            "endDate": "2026-12-31T23:59:59Z",
            "question": "Will BTC be above $100,000?"
        }
        self.yes_window = deque([0.5] * 20, maxlen=20)
        self.up_window = deque([0.5] * 20, maxlen=20)
        self.down_window = deque([0.5] * 20, maxlen=20)

    @patch("core.decision_engine.LATENCY_MONITOR")
    @patch("core.decision_engine.mean_reversion")
    def test_latency_filter(self, mock_mr, mock_latency):
        # Mock high latency penalty
        mock_latency.get_edge_penalty.return_value = 0.10
        
        # Mock a strategy result that should fail the edge filter
        # model_prob 0.60, price 0.50 -> raw_edge 0.10
        # required_edge 0.05 + penalty 0.10 = 0.15
        # 0.10 < 0.15 -> should be filtered
        mock_mr.run.return_value = StrategyResult(
            strategy_name="mean_reversion",
            side="UP",
            trigger_reason="test",
            entry_price=0.50,
            model_probability=0.60,
            confidence=1.0,
            required_edge=0.05,
            raw_edge=0.10
        )

        res = explain_choose_side(
            self.market,
            self.yes_window,
            self.up_window,
            self.down_window,
            observed_up=0.50,
            observed_down=0.50
        )

        self.assertFalse(res["ok"])
        self.assertIn("flow_too_weak", res["reason"])
        self.assertIn("lat0.100", res["reason"])

    @patch("core.decision_engine.LATENCY_MONITOR")
    @patch("core.decision_engine.mean_reversion")
    def test_latency_pass(self, mock_mr, mock_latency):
        # Mock low latency penalty
        mock_latency.get_edge_penalty.return_value = 0.01
        
        # Mock a strategy result that should pass the edge filter
        # model_prob 0.60, price 0.50 -> raw_edge 0.10
        # required_edge 0.05 + penalty 0.01 = 0.06
        # 0.10 >= 0.06 -> should pass
        mock_mr.run.return_value = StrategyResult(
            strategy_name="mean_reversion",
            side="UP",
            trigger_reason="test",
            entry_price=0.50,
            model_probability=0.60,
            confidence=1.0,
            required_edge=0.05,
            raw_edge=0.10
        )

        res = explain_choose_side(
            self.market,
            self.yes_window,
            self.up_window,
            self.down_window,
            observed_up=0.50,
            observed_down=0.50
        )

        self.assertTrue(res["ok"])
        self.assertEqual(res["side"], "UP")

if __name__ == "__main__":
    unittest.main()
