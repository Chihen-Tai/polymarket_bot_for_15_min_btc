import time
import logging
from core.executor import EXECUTOR
from core.latency_monitor import LATENCY_MONITOR

logging.basicConfig(level=logging.INFO)

def dummy_function(x, delay=0.1):
    time.sleep(delay)
    return x * 2

def test():
    print("Testing AsyncExecutor...")
    future = EXECUTOR.submit_entry(dummy_function, 21, delay=0.2)
    print("Function submitted.")
    
    result = future.result()
    print(f"Result: {result}")
    
    median_rtt = LATENCY_MONITOR.get_median_rtt()
    print(f"Median RTT: {median_rtt:.2f}ms")
    
    assert result == 42
    assert median_rtt >= 200  # Should be at least 200ms because of delay=0.2
    print("Test passed!")

if __name__ == "__main__":
    test()
