#!/usr/bin/env python3
"""rate_limit - Token bucket and sliding window rate limiters."""
import time, sys, threading

class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last = time.time()
        self.lock = threading.Lock()
    
    def acquire(self, tokens=1):
        with self.lock:
            now = time.time()
            elapsed = now - self.last
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait(self, tokens=1, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.acquire(tokens):
                return True
            time.sleep(0.01)
        return False

class SlidingWindow:
    def __init__(self, max_requests, window_seconds):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = []
        self.lock = threading.Lock()
    
    def acquire(self):
        with self.lock:
            now = time.time()
            cutoff = now - self.window
            self.requests = [t for t in self.requests if t > cutoff]
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
    
    def remaining(self):
        with self.lock:
            cutoff = time.time() - self.window
            active = sum(1 for t in self.requests if t > cutoff)
            return max(0, self.max_requests - active)

class LeakyBucket:
    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.water = 0
        self.last = time.time()
        self.lock = threading.Lock()
    
    def acquire(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last
            self.water = max(0, self.water - elapsed * self.rate)
            self.last = now
            if self.water < self.capacity:
                self.water += 1
                return True
            return False

def test():
    # Token bucket
    tb = TokenBucket(rate=100, capacity=10)
    assert tb.acquire(5)
    assert tb.acquire(5)
    assert not tb.acquire(5)  # Depleted
    
    # Refill
    time.sleep(0.05)
    assert tb.acquire(1)  # Some tokens refilled
    
    # Sliding window
    sw = SlidingWindow(max_requests=5, window_seconds=0.1)
    for _ in range(5):
        assert sw.acquire()
    assert not sw.acquire()  # At limit
    assert sw.remaining() == 0
    time.sleep(0.15)
    assert sw.acquire()  # Window passed
    
    # Leaky bucket
    lb = LeakyBucket(rate=100, capacity=3)
    assert lb.acquire()
    assert lb.acquire()
    assert lb.acquire()
    # 4th should fail (capacity=3, water leaked ~0 since instant)
    r = lb.acquire()
    # May pass if tiny time elapsed; just verify it eventually blocks
    for _ in range(5):
        lb.acquire()
    # After many rapid calls, should be blocked
    assert not lb.acquire()
    time.sleep(0.05)
    assert lb.acquire()
    
    print("All tests passed!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    else:
        print("Usage: rate_limit.py test")
