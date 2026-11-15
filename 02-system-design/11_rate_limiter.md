# 11. Design a Rate Limiter

---

## 1. The problem in plain words

A **rate limiter** stops any one user from sending too many requests in a short time. If a user sends more than the allowed number, we answer "slow down" (HTTP 429) instead of doing the work.

**Analogy: a bouncer at a club.** The club holds 100 people. The bouncer counts. When it is full, new people wait outside. He is polite but firm, and he treats every guest by the same rule.

Why we need it:
1. **Protect servers** from overload (bugs, bad retry loops, traffic spikes).
2. **Fairness**: one noisy customer must not hurt others.
3. **Security**: slow down password guessing, scraping, abuse.
4. **Cost control**: some calls are expensive (SMS, AI, paid APIs).
5. **Business plans**: free tier 100/min, paid tier 1,000/min.

---

## 2. Requirements

**Must-have**
1. Limit requests per **key** (user id, API key, or IP) within a time window.
2. Different limits per endpoint and per plan, changeable without a deploy.
3. Reject excess requests with 429 and `Retry-After`; return headers showing remaining quota.
4. Works across **many servers** (the count is shared, not per server).
5. **Very low added latency** (a few milliseconds).

**Non-functional**
- Highly available: if the limiter fails, what happens? (Decision: **fail open**, i.e. let traffic through, for most APIs; fail closed for security-critical ones such as login.)
- Reasonably accurate. Slight over- or under-counting is acceptable.

**Out of scope**
- Billing and quota reports, DDoS defence at the network level (that is a separate layer, WAF and CDN), distributed tracing details.

---

## 3. The numbers (estimates)

Assume 10 million active API keys, and a whole platform at 500,000 requests per second at peak.

| Item | Estimate |
|---|---|
| Checks per second | 500,000 (every request is checked once) |
| Memory per key | about 100 bytes for a simple counter or token bucket (key, count/tokens, timestamp) |
| Total memory | 10M keys x 100 B = **1 GB**. Tiny. Fits in one Redis node; spread over a cluster for throughput |
| Redis throughput | about 100,000 ops/s per node (rough) so 5 to 10 shards for 500,000 checks/s |
| Latency budget | under 5 ms added (same data centre) |

Meaning: memory is not the problem; **throughput and latency** are.

---

## 4. The API

Often the limiter is a library or sidecar inside the API gateway, but it also has a small service interface:

```
POST /v1/ratelimit/check
  body:  { "key": "user:42", "rule": "api_default", "cost": 1 }
  reply: 200 { "allowed": true, "remaining": 57, "reset_in_ms": 12000 }
         or { "allowed": false, "retry_after_ms": 4000 }
```

What the **client** of the platform sees on every response:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 4
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1731700000
```

(Header names like `X-RateLimit-*` are common conventions, not one standard.)

Rules are config, for example:

```
rule: api_default   limit: 100  window: 60s  by: api_key
rule: login         limit: 5    window: 60s  by: ip
rule: sms_send      limit: 3    window: 3600s by: user
```

---

## 5. The data tables

**Rule store** (small, in a config database or files, cached in memory in each gateway):

| Column | Note |
|---|---|
| rule_id | primary key |
| match (endpoint, plan) | which requests it covers |
| limit | max requests |
| window_seconds | time span |
| algorithm | token_bucket / sliding_window ... |
| fail_mode | open / closed |

**Counter state** (in Redis, **not** SQL - it changes on every request):

```
key:   rl:{rule_id}:{client_key}        (for example rl:api_default:user42)
value: for token bucket -> { tokens: 57, last_refill_ts: 1731699990 }
       for fixed window -> integer counter, with TTL = window
TTL:   so old keys vanish by themselves
```

---

## 6. The algorithms (the core of this question)

### a) Fixed window counter
Count requests in each clock minute. Key `user42:12:05`. Increment; if > limit, reject. Delete after the window.
- Pros: super simple, little memory.
- **Con: burst at the edge.** A user sends 100 at 12:05:59 and 100 at 12:06:00. That is 200 requests in 2 seconds while the limit is "100 per minute".

### b) Sliding window log
Store a timestamp for every request in a sorted list. Remove entries older than the window. Count the rest.
- Pros: exact.
- Con: lots of memory (one entry per request), slower.

### c) Sliding window counter (a smart middle)
Keep the counts of the current and the previous window. Estimate = `current + previous x (fraction of previous window still inside the sliding window)`.
- Pros: small memory, smooths the edge problem; accurate enough (it assumes requests in the previous window were evenly spread).

### d) Token bucket (most popular; used by many cloud APIs)
A bucket holds up to **B** tokens (the burst size). Tokens are added at **R** per second. Every request takes one token. No token = reject.

```
        refill R tokens/sec
              |
              v
          +-------+
          | o o o |  capacity B
          +---+---+
              | take 1 token per request
              v
          request allowed, or rejected if empty
```
- Pros: allows short bursts (good for users), simple state (2 numbers), steady long-run rate.
- Cons: two parameters to tune.

### e) Leaky bucket
Requests enter a queue (bucket) and leave at a fixed rate. If the bucket is full, new requests are dropped. Smooths output to a constant rate.
- Pros: steady load on the backend. Cons: no bursts; adds waiting.

| Algorithm | Memory | Accuracy | Allows burst | Choose when |
|---|---|---|---|---|
| Fixed window | very low | low at edges | edge double | quick and cheap |
| Sliding log | high | exact | no | small scale, exactness |
| Sliding counter | low | good | smooth | general default |
| Token bucket | low | good | **yes** | public APIs |
| Leaky bucket | low | good | no | protect a fragile backend |

My default answer: **token bucket**, in Redis, per key.

---

## 7. Version 1 (simple)

One app server, in-memory counter per user.

```
Client -> [API server with local map: user -> counter] -> backend
```

Works for one server. Breaks when we have 2+ servers: each has its own counter, so a user can send N requests to each server (limit x number of servers).

---

## 8. Growing 100x, step by step

**Step 1. Shared counters in Redis.** All gateway servers ask the same Redis. The check must be **atomic** (two servers must not both read "99" and both allow). Use a Redis **Lua script** (it runs as one step) or `INCR` plus `EXPIRE` in one script:

```
-- idea, in words:
-- 1. read tokens and last time
-- 2. add tokens for elapsed time, cap at B
-- 3. if tokens >= cost: subtract, allow
--    else: reject
-- 4. save, set TTL
```

**Step 2. Put the check at the edge**, in the API gateway or load balancer layer, before the request touches business servers. (Ties to design `21`.)

```
Client -> LB -> API Gateway [rate limit check] -> Services
                         |
                         v
                  Redis cluster
```

**Step 3. Shard Redis** by key (consistent hashing on `client_key`), so each client's counter lives on exactly one node; add replicas for failover. (`01f`)

**Step 4. Reduce Redis round trips: local + global.** Each gateway keeps a small **local token budget** (for example it takes 10 tokens at a time from Redis and spends them locally). This cuts Redis calls by about 10 times at the cost of small inaccuracy. Another trick: allow each gateway a slice of the limit (limit / number of gateways) and rebalance every second.

**Step 5. Multi-region.** Options: (a) one limit per region (simple; a user can use limit x regions); (b) a global limit with asynchronous sync between regions (approximate); (c) route each user to a home region. Say that exact global limits are costly, and that most products accept approximate.

**Step 6. Rules in a control plane.** A config service stores rules; gateways pull and cache them (with versioning), so changes apply without a deploy. This separates the **slow policy path** (change rules) from the **fast enforcement path** (check requests). Stripe-style interviews reportedly value exactly this separation (see `00` and `91`).

**Step 7. Layers of limits.** Per-IP at the edge (cheap, stops floods), per-API-key in the gateway, per-endpoint and per-tenant inside services, concurrency limits (max in-flight requests), and **load shedding** when the whole system is overloaded.

Final picture:

```
 Client
   |
   v
 CDN / WAF (IP floods)
   |
   v
 LB --> Gateway x N  [local token slices] --> Services
            |   ^
            v   | rules (cached)
        Redis cluster (sharded + replicas)     Rule service + config DB
            
 Metrics -> allowed / rejected counts per rule -> dashboards, alerts
```

---

## 9. Trade-offs and why

| Choice | Why | Cost |
|---|---|---|
| Token bucket | Burst-friendly, tiny state | Needs tuning of B and R |
| Redis, central | Shared view, simple | Extra hop (about 1 ms); a dependency |
| Local slices to cut calls | Lower latency and cost | Small inaccuracy; unfair between gateways |
| Fail open | Availability of the main product | Brief unprotected period; fail closed for login |
| Approximate multi-region | Low latency | A user may exceed the global limit a little |
| Per-key limits | Fairness | Many keys (memory) and key-spoofing risk (use authenticated identity, not a header the client controls) |

---

## 10. What breaks and how to fix it

| Failure | Effect | Fix |
|---|---|---|
| Redis down | No counters | Fail open with a local in-memory fallback limit per gateway; alert; replicas |
| Redis slow | Added latency to every request | Strict timeout (for example 5 ms), then fail open; circuit breaker |
| Race condition | Over-limit requests allowed | Atomic Lua script; single-key operations |
| Hot key (one huge customer) | One Redis shard overloaded | Local slices; split key into sub-keys (`user42#1..#8`) and sum; dedicated shard |
| Clock differences | Wrong refill | Use Redis server time (inside the script), not app server time |
| Retry storm after 429 | Clients hammer you | `Retry-After` header; recommend backoff with jitter; client SDK honours it |
| Attacker rotates IPs | Evades per-IP limit | Also limit per account/API key; use fingerprints; CAPTCHA (out of scope) |
| Config mistake (limit 0) | Everyone blocked | Rule validation, staged rollout, quick rollback, max guard |

---

## 11. Questions the interviewer asks next

**Q1. Where do you place the rate limiter: client, server, or middleware?**
A. Never trust the client alone (it can be bypassed). Best place is a middleware layer, the API gateway, in front of services. Optionally the client SDK also respects limits to be polite.

**Q2. How do you stop two requests from both reading the same count?**
A. The read-modify-write must be atomic. In Redis I use a Lua script or an atomic `INCR`. In SQL I would use `UPDATE ... SET count = count + 1 WHERE count < limit` and check the affected rows.

**Q3. Fixed window versus sliding window?**
A. Fixed window is simple but allows twice the limit at the boundary. Sliding window counter fixes most of that with two counters per key.

**Q4. How do you do distributed limiting across regions?**
A. Prefer approximate: each region has a share of the quota and syncs usage periodically; or route a user to one home region. Exact global counters would need a cross-region call per request, which is too slow.

**Q5. What do you return and what should clients do?**
A. 429 with `Retry-After` and quota headers. Clients wait with exponential backoff and jitter.

**Q6. How do you rate limit by different dimensions at once (user and IP and endpoint)?**
A. Check several rules in one pass; request is allowed only if all pass. Use separate keys per rule, and run the checks in one Redis script or pipeline to save round trips.

**Q7. How do you test it?**
A. Unit tests on the algorithm with a fake clock; load tests; shadow mode (count but do not block) before enforcing a new rule; dashboards of would-be rejections.

**Q8. How would you limit by cost (a heavy request costs 10 tokens)?**
A. Token bucket supports a `cost` parameter naturally: subtract cost tokens at once.

---

## 12. Say it out loud (6 sentences)

1. "A rate limiter protects services and keeps customers fair by rejecting requests over a quota with a 429 and a Retry-After header."
2. "Memory is small, about 1 GB for 10 million keys, so the real challenge is atomic checks at 500,000 per second with a few milliseconds of latency."
3. "I use a token bucket per key, stored in Redis and updated by an atomic Lua script, because it allows bursts and needs only two numbers."
4. "The check lives in the API gateway, Redis is sharded by key with replicas, and gateways keep small local token slices to cut Redis calls."
5. "Rules live in a separate control plane that gateways cache, so the slow policy path is separate from the fast enforcement path."
6. "If Redis fails I fail open with a local limit for normal APIs and fail closed for login, and I watch rejected-request metrics and use shadow mode before enforcing new rules."
