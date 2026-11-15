# 03. Reliability Patterns

Networks fail. Servers crash. Disks fill. Dependencies get slow. A good design **expects** this. These patterns are the tools. Learn them well: every design file uses them, and Stripe especially cares about them.

You already use many of these in your provisioner (retries, ordering, health checks). When you explain a pattern, add one sentence from your real work.

---

## 1. Timeouts

**Problem:** A call to another service hangs. Your thread waits forever. Soon all threads wait and your service is dead too.

**Analogy:** You phone a shop; nobody answers. You do not hold the phone for 3 hours. You hang up after a minute.

**Rule:** Every network call has a timeout. No exceptions.
- **Connect timeout** (can I reach it?) is short.
- **Read/total timeout** (did it answer?) matches the expected speed: for example, p99 latency of the dependency plus some margin.
- **Deadline propagation:** if the user's request has 2 seconds in total, pass the remaining time down to each call so inner calls do not run longer than the outer one.

Trade-off: too short = false failures; too long = resources stuck.

---

## 2. Retries with exponential backoff and jitter

**Problem:** A call fails (network blip, server busy). Many failures are short-lived, so trying again often works.

**Bad retry:** retry immediately, many times. If the server is overloaded, 10,000 clients retrying at once make it worse (a **retry storm**).

**Good retry:**
1. **Exponential backoff:** wait longer after each failure: 1s, 2s, 4s, 8s... up to a maximum.
2. **Jitter:** add randomness so clients do not all retry at the same instant.
3. **Max attempts** (for example 3 to 5), then give up or send to a dead-letter queue.
4. **Retry only what is safe:** retry on timeouts, 5xx, 429 (respect `Retry-After`). Do **not** retry 4xx like 400/404 (your request is wrong).
5. **Only retry idempotent operations** - or use an idempotency key (next section).
6. **Retry at one layer only.** If 3 layers each retry 3 times, one failure becomes 27 calls (a **retry amplification**).

```
attempt 1 -- fail --> wait random(0..1s)
attempt 2 -- fail --> wait random(0..2s)
attempt 3 -- fail --> wait random(0..4s)
attempt 4 -- fail --> give up / dead-letter
```

"Full jitter" idea: `sleep = random(0, min(cap, base * 2^attempt))`.

**Your work:** Your provisioner retries failed installation steps; the dependency order and a retry limit prevent endless loops. Say that.

---

## 3. Idempotency

**Idempotent** = doing it once or many times gives the **same final result**.

**Analogy:** Pressing the lift button 5 times is the same as pressing once (idempotent). Putting a coin in a vending machine 5 times buys 5 snacks (not idempotent).

Why it matters: because of retries and at-least-once queues, the same request **will** arrive twice. If "charge 500 rupees" runs twice, the customer pays double. Terrible.

### Naturally idempotent
- `PUT /users/5 {name: "Asha"}` (set the same value again: no change)
- `DELETE /orders/9`
- `SET status = 'paid'`

### Not idempotent
- `POST /payments` (creates a new payment each time)
- `balance = balance + 100`

### Idempotency key (the standard fix)

1. Client makes a unique key (a UUID) for **one intended operation**, and sends it in a header: `Idempotency-Key: 7f3a...`
2. Server, on the first request: stores the key with status "in progress", does the work, stores the **result** with the key.
3. If the same key arrives again: server returns the **saved result**, does not do the work again.
4. If it arrives while the first is still running: wait or return 409 "in progress".
5. If the same key arrives with a **different body**: reject with an error (misuse).
6. Keys expire after some time (for example 24 hours; a design choice).

```
Request(key=K) --> [lookup K in keys table]
                    |- not found: insert K (in_progress), do work, save result, return
                    |- found + done: return saved result (no work)
                    |- found + in_progress: 409 or wait
```

Make it safe in the database with a **unique constraint on the key**: two simultaneous requests cannot both insert it. Stripe's public API docs describe idempotency keys in this way (see https://docs.stripe.com/api/idempotent_requests - read it once).

**Consumer side:** store `message_id` in a `processed_messages` table inside the **same transaction** as the effect.

---

## 4. Rate limiting

**Problem:** One client (or a bug, or an attacker) sends too many requests and hurts everyone.

**Analogy:** A club entrance: only 100 people inside at a time; others wait outside.

Common algorithms (full details in `11`):
- **Token bucket:** a bucket fills with tokens at a steady rate; each request takes one token; allows short bursts.
- **Leaky bucket:** requests drain at a fixed speed; smooths traffic.
- **Fixed window counter:** count per minute; simple, but allows double bursts at the window edge.
- **Sliding window:** more accurate, more memory.

Response: HTTP **429 Too Many Requests** + `Retry-After`. Limit by user id, API key, or IP; use different limits for different endpoints. Also protects **you** from your own clients' retry storms.

---

## 5. Circuit breaker

**Problem:** A dependency is failing. If you keep calling it, each call waits for a timeout, threads pile up, and you fail too (a **cascading failure**).

**Analogy:** The fuse in your house. When there is a dangerous overload, the fuse cuts the circuit so the house does not burn. Later you reset it.

**Three states:**

```
        failures > threshold
 CLOSED ----------------------> OPEN
 (calls go through)             (calls fail immediately, no waiting)
    ^                              |
    |   success                    | after a cool-down time
    |                              v
    +------------------------- HALF-OPEN
        (let a few test calls through;
         success -> CLOSED, failure -> OPEN)
```

While OPEN, return a **fallback**: cached data, a default, a friendly error. It gives the sick service time to recover.

Pair with: **bulkheads** (separate thread/connection pools per dependency, like watertight compartments in a ship, so one slow dependency cannot use all resources) and **load shedding** (when overloaded, deliberately reject low-priority work).

---

## 6. Health checks

Two different questions:

- **Liveness:** "Is the process alive or stuck?" If not, **restart** it.
- **Readiness:** "Can it take traffic now?" If not, **stop sending** requests but do not restart (it may be warming up or temporarily busy).

You know both from Kubernetes probes. Rules:
- Keep checks cheap and fast.
- Do not make liveness depend on a shared external service (a database blip would restart every pod at once).
- A **deep health check** (tests dependencies) is useful for dashboards and readiness, but be careful of removing every server at once.
- Load balancers use health checks to remove bad servers (`01c`).

---

## 7. SLI, SLO, SLA, error budget

You know these from SRE work. Say them simply.

| Term | Meaning | Example |
|---|---|---|
| **SLI** (indicator) | A number that measures service quality | % of requests answered successfully in under 300 ms |
| **SLO** (objective) | The target for the SLI | 99.9% of requests succeed over 30 days |
| **SLA** (agreement) | A promise to a customer, usually with money penalties | Refund if availability drops below 99.5% |
| **Error budget** | How much failure the SLO allows | 99.9% over 30 days = about 43 minutes of "bad" time |

Math: 30 days = 43,200 minutes. 0.1% = 43.2 minutes.

Use of the budget: while there is budget left, ship features. When the budget is nearly spent, slow down and fix reliability. This gives a fair rule between speed and safety.

Good SLIs: availability, latency (use percentiles p50, p95, p99, not just the average), freshness (how old is the data), correctness, durability.

**Percentiles:** p99 latency = 99 percent of requests are faster than this. Averages hide slow users.

In a design, say: "I would set an SLO like 99.9 percent availability and p99 under 300 ms for the read path, alert on burn rate (how fast the error budget is being used), and keep dashboards for the four golden signals: latency, traffic, errors, saturation."

---

## 8. Other useful patterns

- **Graceful degradation:** when something fails, offer less, not nothing. (Show the feed without recommendations if the recommendation service is down.)
- **Redundancy:** no single point of failure (SPOF). Two of everything important, in different zones.
- **Failover and multi-AZ/region:** survive a data centre loss.
- **Bulkheads / isolation:** separate resources per tenant or per dependency (you built multi-tenant isolation, so use this story).
- **Backpressure:** tell producers to slow down when consumers cannot cope.
- **Dead-letter queues:** park messages that keep failing.
- **Saga and compensation:** for multi-step work across services; if step 4 fails, undo steps 3, 2, 1 with compensating actions (uninstall, refund). Your provisioner is the model example.
- **Outbox pattern:** make DB update and event publish atomic (`01g`).
- **Reconciliation:** a background job that compares two systems and fixes differences (for example payments vs the ledger). A safety net that every money system has.
- **Graceful shutdown and draining:** finish in-flight work before exit.
- **Canary / gradual rollout and feature flags:** release to 1 percent first; roll back fast.
- **Chaos testing:** break things on purpose (in safe ways) to learn.

---

## 9. How the patterns fit together on one call

```
Client
  | sends Idempotency-Key, has a deadline
  v
Service A  --[rate limit]--> --[timeout 500ms]--> --[circuit breaker]--> Service B
              retries (max 3, backoff + jitter) only because the call is idempotent
              fallback if breaker is open
              metrics: latency, errors, saturation -> alerts on SLO burn
```

---

## 10. Interview questions

**Q: A downstream service is slow. What happens to you and what do you do?**
A: Without protection, my threads wait, queues grow, and I fail too. I set timeouts, use a circuit breaker with a fallback, bulkhead the connection pool, and shed low-priority load. I alert on latency of that dependency.

**Q: How do you make payment creation safe against double clicks and retries?**
A: Client sends an idempotency key. Server stores key and result under a unique constraint; repeated key returns the first result. The DB insert and the money movement share one transaction or are driven by a state machine.

**Q: Why jitter?**
A: Without jitter, all clients that failed together retry together and overload the server again and again. Random waiting spreads them out.

**Q: Liveness vs readiness?**
A: Liveness decides restart. Readiness decides if traffic is sent. I never tie liveness to external dependencies.

---

## Quick check

1. Why retry only idempotent operations?
2. Name the three states of a circuit breaker.
3. What is an error budget for 99.95 percent over 30 days? (Answer: 0.05% of 43,200 minutes = 21.6 minutes.)
4. What problem does jitter solve?
5. What is the difference between a timeout and a circuit breaker?
