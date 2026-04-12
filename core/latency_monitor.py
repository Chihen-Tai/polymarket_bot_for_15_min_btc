import collections
import statistics
from core.config import SETTINGS

class LatencyMonitor:
    def __init__(self, history_size=20):
        self.rtts = collections.deque(maxlen=history_size)

    def add_rtt(self, rtt_ms: float):
        self.rtts.append(rtt_ms)

    def get_median_rtt(self) -> float:
        if not self.rtts:
            return 0.0
        return statistics.median(self.rtts)

    def get_edge_penalty(self) -> float:
        median_rtt = self.get_median_rtt()
        # formula: max(0, (median_rtt - 100) / 100 * latency_edge_buffer)
        return max(0.0, (median_rtt - 100.0) / 100.0 * SETTINGS.latency_edge_buffer)

LATENCY_MONITOR = LatencyMonitor()
