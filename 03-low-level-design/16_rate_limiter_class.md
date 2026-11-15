# 16 - Rate Limiter (class design: token bucket and sliding window)

Python 3.9. All code was run; the output is real.

(There is also a *system design* version of this question for many servers. This file is the **LLD version**: one process, clean classes, and correct algorithms.)

---

## 1. The problem in plain words

A **rate limiter** says "yes" or "no" to each request, so that nobody sends too many requests in a short time. Example: "each user may call the API at most 5 times per 10 seconds." Extra requests are rejected.

**Analogy.** A nightclub door. The guard lets in only a few people per minute. Others wait outside or go home.

Why? To protect a server from overload, from abuse, and to be fair to all users.

---

## 2. Requirements I ask the interviewer

1. Limit per what? -> *Per key (user id or IP).*
2. What happens to an extra request? -> *Rejected right away (return `False`). No waiting queue.*
3. Which rule: a smooth refill, or "N per window"? -> *Support both; implement token bucket and sliding window.*
4. Can the limits differ per user type (free, paid)? -> *Possible extension.*
5. Is this inside one process? -> *Yes (class design). A distributed version needs a shared store like Redis (system design).*
6. Time source? -> *Injected, so tests do not sleep.*
7. Threads? -> *Yes, many request threads.*

---

## 3. The algorithms in plain words

### Fixed window counter (simple, but flawed)

Cut time into fixed slots (for example 0-10 s, 10-20 s). Count requests per slot. If count > limit, reject.
**Flaw:** a user sends 3 requests at second 9 and 3 more at second 10. That is 6 requests in about 1 second, although the limit is "3 per 10 seconds". The boundary lets double the traffic through.

### Sliding window log (exact)

Keep the **timestamp of each recent request** (a list). For a new request: throw away timestamps older than the window; if fewer than `limit` remain, accept and store the new timestamp.
**Good:** exact. **Bad:** uses memory for every request in the window (O(limit) per key).

### Token bucket (smooth, memory-small)

**Analogy.** A bucket holds up to `capacity` tokens. Tokens drip in at a steady `refill rate`. Each request must take one token. If the bucket is empty, the request is rejected. If the user was quiet, the bucket fills up, so a **burst** up to `capacity` is allowed.

We do **not** run a timer. We store `tokens` and `last_time`. On each request, we compute how many tokens dripped in since `last_time`:
`tokens = min(capacity, tokens + elapsed * rate)`. This is called **lazy refill**.
**Good:** O(1) memory per key, allows bursts, smooth.

### Sliding window counter (extension: approximate, small memory)

Keep counts for the current and previous fixed windows. Estimate: `previous_count * (fraction of previous window still inside) + current_count`. It fixes most of the boundary flaw with O(1) memory.

---

## 4. Classes and methods (the picture)

```text
        +---------------------------+
        |   RateLimiter (abstract)  |   <- Strategy interface
        |---------------------------|
        | allow(key) -> bool        |
        +------------+--------------+
                     ^
   +-----------------+------------------+--------------------+-----------------------+
   |                 |                  |                    |
 TokenBucket   SlidingWindowLog   FixedWindow       SlidingWindowCounter (extension)
 (capacity,    (limit, window)    (limit, window)    (limit, window)
  refill_rate)

 +----------------------------+
 | PlanBasedLimiter (ext.)    |  picks a limiter by user plan (free / paid), also a RateLimiter
 +----------------------------+

 clock: a function that returns "now" in seconds (injected)
```

All limiters have the **same method** `allow(key)`. A caller can use any of them. That is polymorphism and the Strategy pattern.

---

## 5. Full code

```python
import threading                               # Lock for thread safety
from abc import ABC, abstractmethod            # "promise" classes
from collections import deque                  # fast queue: add at the right, remove at the left


class RateLimiter(ABC):
    @abstractmethod
    def allow(self, key):
        """Return True if this request is allowed, False if it must be rejected."""
        pass


class TokenBucketLimiter(RateLimiter):
    def __init__(self, capacity, refill_per_second, clock):
        self.capacity = capacity               # maximum tokens = biggest burst
        self.rate = refill_per_second          # tokens added per second
        self.clock = clock                     # function that returns now (seconds)
        self._state = {}                       # key -> [tokens, last_time]
        self._lock = threading.Lock()

    def allow(self, key):
        with self._lock:                       # read-modify-write must be one step
            now = self.clock()
            # new users start with a full bucket
            tokens, last = self._state.get(key, (float(self.capacity), now))
            elapsed = now - last               # seconds since we last looked
            # lazy refill: add the tokens that dripped in, but never above capacity
            tokens = min(float(self.capacity), tokens + elapsed * self.rate)
            if tokens >= 1.0:                  # need one whole token
                tokens -= 1.0
                self._state[key] = (tokens, now)
                return True
            self._state[key] = (tokens, now)   # save the refilled value even when rejecting
            return False


class SlidingWindowLogLimiter(RateLimiter):
    def __init__(self, limit, window_seconds, clock):
        self.limit = limit                     # max requests inside any window
        self.window = window_seconds
        self.clock = clock
        self._logs = {}                        # key -> deque of timestamps (oldest on the left)
        self._lock = threading.Lock()

    def allow(self, key):
        with self._lock:
            now = self.clock()
            log = self._logs.setdefault(key, deque())
            # throw away timestamps that are outside the window (older than now - window)
            while log and log[0] <= now - self.window:
                log.popleft()
            if len(log) < self.limit:          # room left in this window
                log.append(now)                # remember this request
                return True
            return False


class FixedWindowLimiter(RateLimiter):         # shown only to demonstrate its boundary flaw
    def __init__(self, limit, window_seconds, clock):
        self.limit = limit
        self.window = window_seconds
        self.clock = clock
        self._counts = {}                      # key -> (window_number, count)
        self._lock = threading.Lock()

    def allow(self, key):
        with self._lock:
            window_no = int(self.clock() // self.window)   # which slot are we in? (0-10s is slot 0, ...)
            slot, count = self._counts.get(key, (window_no, 0))
            if slot != window_no:              # a new slot started: reset the count
                slot, count = window_no, 0
            if count < self.limit:
                self._counts[key] = (slot, count + 1)
                return True
            self._counts[key] = (slot, count)
            return False


# ---------- EXTENSIONS ----------

class SlidingWindowCounterLimiter(RateLimiter):
    """Approximate sliding window using two counters (O(1) memory per key)."""
    def __init__(self, limit, window_seconds, clock):
        self.limit = limit
        self.window = window_seconds
        self.clock = clock
        self._data = {}                        # key -> [window_number, current_count, previous_count]
        self._lock = threading.Lock()

    def allow(self, key):
        with self._lock:
            now = self.clock()
            window_no = int(now // self.window)
            rec = self._data.setdefault(key, [window_no, 0, 0])
            if rec[0] != window_no:            # move forward in time
                # if exactly one slot passed, the old current becomes previous; if more passed, previous is 0
                rec[2] = rec[1] if window_no - rec[0] == 1 else 0
                rec[1] = 0
                rec[0] = window_no
            into_window = (now % self.window) / self.window     # 0.0 at slot start, close to 1.0 at slot end
            estimate = rec[2] * (1.0 - into_window) + rec[1]    # weight the previous slot by how much of it still counts
            if estimate + 1 <= self.limit:
                rec[1] += 1
                return True
            return False


class PlanBasedLimiter(RateLimiter):
    """Chooses a limiter by the user's plan. It is itself a RateLimiter (so callers do not change)."""
    def __init__(self, limiter_by_plan, plan_of_user, default_plan):
        self.limiter_by_plan = limiter_by_plan # dict: plan name -> RateLimiter
        self.plan_of_user = plan_of_user       # function: user key -> plan name
        self.default_plan = default_plan

    def allow(self, key):
        plan = self.plan_of_user(key) or self.default_plan
        return self.limiter_by_plan[plan].allow(key)


class FakeClock:
    def __init__(self):
        self.now = 0.0
    def __call__(self):
        return self.now


def run_requests(limiter, clock, times, key="u1"):
    # helper for the demo: send one request at each given time, return "Y" (allowed) or "n" (rejected)
    out = []
    for t in times:
        clock.now = t
        out.append("Y" if limiter.allow(key) else "n")
    return "".join(out)


def main():
    # --- token bucket: capacity 5, refill 1 token per second ---
    clk = FakeClock()
    tb = TokenBucketLimiter(capacity=5, refill_per_second=1, clock=clk)
    print("token bucket, 7 quick requests at t=0 :", run_requests(tb, clk, [0] * 7))
    print("after 2 seconds, 3 requests           :", run_requests(tb, clk, [2, 2, 2]))
    print("after 100 quiet seconds, 7 requests   :", run_requests(tb, clk, [102] * 7), "(bucket refilled to capacity 5, not more)")

    # --- boundary flaw: limit 3 per 10 seconds, requests at t=9 and t=10 ---
    times = [9, 9, 9, 10, 10, 10]
    c1, c2, c3 = FakeClock(), FakeClock(), FakeClock()
    print("--- same traffic: 3 requests at t=9, 3 at t=10 (limit 3 per 10s) ---")
    print("fixed window   :", run_requests(FixedWindowLimiter(3, 10, c1), c1, times), "(6 allowed in 1 second: flaw)")
    print("sliding log    :", run_requests(SlidingWindowLogLimiter(3, 10, c2), c2, times))
    print("sliding counter:", run_requests(SlidingWindowCounterLimiter(3, 10, c3), c3, times))

    print("--- sliding log recovers as old requests leave the window ---")
    c4 = FakeClock()
    sl = SlidingWindowLogLimiter(3, 10, c4)
    print("t=0,1,2,3 :", run_requests(sl, c4, [0, 1, 2, 3]))
    print("t=10      :", run_requests(sl, c4, [10]), "(request from t=0 left the window)")
    print("t=10.5    :", run_requests(sl, c4, [10.5]), "(request from t=1 not yet out)")
    print("t=11      :", run_requests(sl, c4, [11]), "(request from t=1 now out)")

    # --- different users do not affect each other ---
    c5 = FakeClock()
    tb2 = TokenBucketLimiter(2, 0, c5)
    print("--- per-key limits ---")
    print("alice:", run_requests(tb2, c5, [0, 0, 0], key="alice"), "| bob:", run_requests(tb2, c5, [0, 0, 0], key="bob"))

    # --- extension: plans ---
    print("--- extension: plans (free = 2 per 10s, paid = 5 per 10s) ---")
    c6 = FakeClock()
    plans = {"free": SlidingWindowLogLimiter(2, 10, c6), "paid": SlidingWindowLogLimiter(5, 10, c6)}
    user_plan = {"alice": "paid"}              # bob has no entry, so he gets the default plan
    pb = PlanBasedLimiter(plans, lambda k: user_plan.get(k), "free")
    print("alice (paid):", run_requests(pb, c6, [0] * 6, key="alice"))
    print("bob (free)  :", run_requests(pb, c6, [0] * 6, key="bob"))

    # --- thread test: 20 threads x 10 requests, capacity 50, no refill: exactly 50 allowed ---
    print("--- thread test ---")
    c7 = FakeClock()
    shared = TokenBucketLimiter(50, 0, c7)
    allowed = []
    def hit():
        for _ in range(10):
            allowed.append(shared.allow("api"))
    threads = [threading.Thread(target=hit) for _ in range(20)]
    for t in threads: t.start()
    for t in threads: t.join()
    print("requests:", len(allowed), "| allowed:", sum(allowed), "| rejected:", len(allowed) - sum(allowed))


if __name__ == "__main__":
    main()
```

Output I got when I ran it:

```text
token bucket, 7 quick requests at t=0 : YYYYYnn
after 2 seconds, 3 requests           : YYn
after 100 quiet seconds, 7 requests   : YYYYYnn (bucket refilled to capacity 5, not more)
--- same traffic: 3 requests at t=9, 3 at t=10 (limit 3 per 10s) ---
fixed window   : YYYYYY (6 allowed in 1 second: flaw)
sliding log    : YYYnnn
sliding counter: YYYnnn
--- sliding log recovers as old requests leave the window ---
t=0,1,2,3 : YYYn
t=10      : Y (request from t=0 left the window)
t=10.5    : n (request from t=1 not yet out)
t=11      : Y (request from t=1 now out)
--- per-key limits ---
alice: YYn | bob: YYn
--- extension: plans (free = 2 per 10s, paid = 5 per 10s) ---
alice (paid): YYYYYn
bob (free)  : YYnnnn
--- thread test ---
requests: 200 | allowed: 50 | rejected: 150
```

---

## 6. How the code works (walk through)

- **Token bucket:** it stores `(tokens, last_time)` per key. `allow` first adds the tokens that dripped in since `last_time` (`elapsed * rate`, never above capacity), then takes one token if at least one is available. First line of the demo: 5 allowed, then 2 rejected. After 2 seconds, 2 tokens came back, so `YYn`. After a long quiet time the bucket is full (5), not more.
- **Sliding window log:** the deque holds timestamps, oldest on the left. Old ones are removed from the left. If fewer than `limit` remain, the new request is accepted. The demo shows requests being accepted again exactly when old ones leave the window.
- **Fixed window:** the boundary flaw is real: all 6 requests pass in the demo. The sliding log accepts only 3 and the sliding counter accepts 3 here too.
- All limiters have the same `allow(key)` method, so a caller can swap them.

---

## 7. How to extend it

**"Different limits per plan."** `PlanBasedLimiter` is a `RateLimiter` that picks another limiter. Callers still use `allow(key)`. Nothing old changes.

**"Return how long to wait (`Retry-After`)."** Change `allow` to return a small result object `(allowed, retry_after_seconds)`. For the token bucket: `retry_after = (1 - tokens) / rate`. This is a change of the interface, so decide it early.

**"Limit by cost (an expensive request uses 5 tokens)."** Add a `cost=1` parameter to `allow`; the token bucket subtracts `cost`.

**"Many servers."** The state (tokens, timestamps) must move to a shared store such as Redis, and the read-modify-write must be atomic (a Lua script or a transaction). That is the system-design version of this question.

---

## 8. Thread-safety notes (plain words)

- **The danger:** `allow` does "read tokens, compute, write tokens". Two threads can read the same value of `tokens` and both subtract one. The result: more requests than allowed pass.
- **The fix:** a lock around the whole read-modify-write. The thread test: 20 threads send 200 requests at a bucket with 50 tokens (no refill). Exactly 50 pass.
- **Speed:** one lock for all keys means all users wait for each other. Improve it with **lock striping**: make N locks and use `locks[hash(key) % N]`. Different users now mostly use different locks.
- **Memory:** the dictionaries grow with the number of keys. A background cleanup should delete keys that have been idle for longer than a window (for the token bucket, idle for long enough that the bucket would be full again).

---

## 9. Five follow-up questions with model answers

**Q1. Token bucket or sliding window: which would you choose?**
Token bucket when you want to allow short bursts and keep memory tiny (one number pair per user). Sliding window log when you need an exact "N in any T seconds" rule and N is small. Sliding window counter when N is large and an approximate answer is fine. I would ask the interviewer which behaviour the product wants.

**Q2. Why do you not run a timer thread to refill the buckets?**
A timer for millions of keys is expensive and wasteful. Lazy refill computes the right number of tokens at the moment a request arrives, using the clock, so there is no background work. It is exactly equal in result.

**Q3. How do you test a rate limiter without waiting?**
The clock is injected (a function). Tests pass a `FakeClock` and set `now` by hand, as `main()` does. No `time.sleep`, no flaky tests.

**Q4. Memory grows forever with new keys (for example IP addresses). What do you do?**
Remove idle keys. For the sliding log: when the deque becomes empty after trimming, delete the key. For the token bucket: periodically delete keys whose last request is older than `capacity / rate` seconds (their bucket would be full anyway, so a new key behaves the same). Or use an LRU cache (file 11) as the key store with a maximum size.

**Q5. How do you make this work across 10 servers?**
Move the state to a shared store and keep the read-modify-write atomic. With Redis, a Lua script runs the token-bucket math atomically. Alternative: each server gets `limit / 10` (cheap but not exact if load is uneven). I would state that this is a system-design extension and keep the class design the same: the `RateLimiter` interface does not change, only the implementation behind it.

---

**Next:** `17_amazon_locker.md`.
