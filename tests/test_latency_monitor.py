import unittest
import collections
import statistics

# We'll import these when they exist
# from core.latency_monitor import LatencyMonitor, LATENCY_MONITOR

class TestLatencyMonitor(unittest.TestCase):
    def test_latency_monitor_median(self):
        from core.latency_monitor import LatencyMonitor
        monitor = LatencyMonitor(history_size=5)
        for rtt in [100, 200, 300, 400, 500]:
            monitor.add_rtt(rtt)
        self.assertEqual(monitor.get_median_rtt(), 300)

    def test_latency_monitor_edge_penalty(self):
        from core.latency_monitor import LatencyMonitor
        from core.config import SETTINGS
        monitor = LatencyMonitor(history_size=5)
        # We manually update SETTINGS.latency_edge_buffer to ensure predictable results in this test
        original_buffer = SETTINGS.latency_edge_buffer
        SETTINGS.latency_edge_buffer = 0.015
        try:
            # 100ms -> penalty 0
            monitor.add_rtt(100)
            self.assertEqual(monitor.get_edge_penalty(), 0.0)
            
            # 200ms -> (200-100)/100 * 0.015 = 0.015
            # But median of [100, 200] is 150
            # (150-100)/100 * 0.015 = 0.0075
            monitor.add_rtt(200)
            self.assertEqual(monitor.get_edge_penalty(), 0.0075)
            
            # Median 200
            monitor.add_rtt(300)
            self.assertEqual(monitor.get_edge_penalty(), 0.015)
        finally:
            SETTINGS.latency_edge_buffer = original_buffer

    def test_singleton_instance(self):
        from core.latency_monitor import LatencyMonitor, LATENCY_MONITOR
        self.assertIsInstance(LATENCY_MONITOR, LatencyMonitor)

if __name__ == '__main__':
    unittest.main()
