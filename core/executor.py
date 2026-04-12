import time
import logging
import concurrent.futures
from core.latency_monitor import LATENCY_MONITOR

logger = logging.getLogger(__name__)

class AsyncExecutor:
    def __init__(self, max_workers=3):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def submit_entry(self, func, *args, **kwargs):
        """
        Submits a function to the executor, timing its execution and reporting
        the RTT to LATENCY_MONITOR.
        """
        def wrapper(*w_args, **w_kwargs):
            start_ts = time.perf_counter()
            try:
                result = func(*w_args, **w_kwargs)
                rtt_ms = (time.perf_counter() - start_ts) * 1000.0
                LATENCY_MONITOR.add_rtt(rtt_ms)
                logger.info(f"AsyncExecutor: {func.__name__} completed in {rtt_ms:.2f}ms")
                return result
            except Exception as e:
                rtt_ms = (time.perf_counter() - start_ts) * 1000.0
                LATENCY_MONITOR.add_rtt(rtt_ms)
                logger.error(f"AsyncExecutor: {func.__name__} failed after {rtt_ms:.2f}ms: {e}")
                raise

        return self.executor.submit(wrapper, *args, **kwargs)

EXECUTOR = AsyncExecutor()
