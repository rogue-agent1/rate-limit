#!/usr/bin/env python3
"""Rate limiter implementations."""
import time, threading

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: int = 1) -> bool:
        with self._lock:
            now = time.monotonic()
            self._tokens = min(self.capacity, self._tokens + (now - self._last) * self.rate)
            self._last = now
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    @property
    def tokens(self):
        return self._tokens

class SlidingWindow:
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window = window_seconds
        self._timestamps = []
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        with self._lock:
            now = time.monotonic()
            cutoff = now - self.window
            self._timestamps = [t for t in self._timestamps if t > cutoff]
            if len(self._timestamps) < self.max_requests:
                self._timestamps.append(now)
                return True
            return False

if __name__ == "__main__":
    rl = TokenBucket(rate=10, capacity=10)
    for i in range(15):
        print(f"Request {i}: {'allowed' if rl.acquire() else 'denied'}")

def test():
    # Token bucket
    tb = TokenBucket(rate=1000, capacity=5)
    for _ in range(5):
        assert tb.acquire()
    assert not tb.acquire()
    time.sleep(0.01)
    assert tb.acquire()  # refilled
    # Sliding window
    sw = SlidingWindow(max_requests=3, window_seconds=0.1)
    assert sw.acquire()
    assert sw.acquire()
    assert sw.acquire()
    assert not sw.acquire()
    time.sleep(0.15)
    assert sw.acquire()  # window passed
    print("  rate_limit: ALL TESTS PASSED")
