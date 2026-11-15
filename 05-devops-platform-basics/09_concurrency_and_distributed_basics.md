# 09. Concurrency and distributed basics

Legend: `[REAL]` = I ran the Python script on this Mac (Python 3.9.6, macOS 26) on 2026-11-15. `[SAMPLE]` = shape example, not run. The retry/backoff/jitter, idempotency, load-shedding, and timeout rules were checked against the AWS Builders' Library, Google's SRE book, and Stripe's docs (links at the end).

---

## 1. What it is (plain words + analogy)

**Concurrency** = many things in progress at the same time (threads, processes, requests, servers).
**Distributed system** = many computers that work together over a network, where any part can fail alone.

Analogy 1, a **shared notebook**: two people read "balance = 100", both add 10, both write "110". The right answer is 120. One update is lost. That is a **race condition**.
Analogy 2, a **phone call that drops**: you say "send the money" and the line dies. Did the other side hear you? You do not know. You can only ask again. That is **partial failure**, and why we need **idempotency** (asking twice must be safe).

Words:
- **Race condition**: the result depends on timing of operations from different threads/processes.
- **Lock (mutex)**: only one holder at a time; others wait.
- **Deadlock**: A waits for B and B waits for A, forever.
- **Idempotent**: doing it once or many times gives the same final result.
- **Latency**: how long a call takes. **Throughput**: how many calls per second.
- **Backpressure**: a slow consumer telling a fast producer "slow down".

## 2. Why it matters in interviews

Google and Amazon loops and Smallest AI's fundamentals call like questions such as "what is a race condition?", "how do you make a retry safe?", "why do retries make an outage worse?", "can you trust the clock?". Platform interviews add "what happens when a node dies mid-request?". 2026 guides place these inside system design and incident questions. The answers are short and follow patterns; learn the patterns.

## 3. How it works, step by step

### 3.1 Race conditions

The classic bug is **read-modify-write**: read a value, change it, write it back. Another thread can sneak in between.

```
 Thread A: read count (0)                       write count = 1
 Thread B:            read count (0)  write count = 1
 Result: 1, not 2. One increment is lost.
```
`[REAL]` Four threads each add 1 to a shared counter 200,000 times (expected 800,000). I made Python switch threads very often so the race shows up:
```
expected 800000, got 280239          <-- lost updates, no lock
with lock: expected 800000, got 800000   <-- with a lock, always correct
```
(The exact number changes each run. On normal settings the race may not show for a long time, which is exactly why races are dangerous: they hide in tests and appear in production.)

How to fix:
1. **Do not share**: give each worker its own data, then combine at the end.
2. **Lock** around the critical section (small and quick).
3. **Atomic operations** (an atomic increment, or `UPDATE counter SET n = n + 1` in the database, which the database runs as one step).
4. **Optimistic concurrency**: read a version number, write only `WHERE version = old`; if 0 rows changed, retry (compare-and-swap).
5. **One owner**: put work in a queue handled by one consumer.

Races also happen **between processes and servers**: two pods both check "does file X exist?" then both create it; two CI jobs both run `terraform apply` (that is why state locking exists, file 06); two cron jobs run at the same time (use a lock or a single scheduler).

### 3.2 Locks and deadlocks

Deadlock needs four things together (the Coffman conditions, general computer-science knowledge): mutual exclusion, hold-and-wait, no preemption, circular wait.

```
 Thread A: lock(X) ... wants lock(Y)  ──┐
 Thread B: lock(Y) ... wants lock(X)  ◄─┘  both wait forever
```
Prevent: always take locks in the **same global order**; hold locks for the shortest time; use timeouts on lock acquire; avoid calling unknown code while holding a lock. Databases detect deadlocks and abort one transaction, so applications must be ready to **retry** (see PostgreSQL's serialization failure note in file 10).

**Distributed locks** (a lock shared by many servers, for example in Redis, etcd, or a database) are harder: a holder can pause (long GC pause, VM freeze), its lock **lease** expires, someone else takes the lock, then the first holder wakes up and still thinks it holds the lock. Defense: **fencing tokens**, a number that increases with each lock grant; the protected resource rejects writes with an older number. (General knowledge from distributed systems literature; not verified today.) Kubernetes uses **leases** for leader election, the same idea.

### 3.3 Idempotency

An operation is idempotent if repeating it does not change the result after the first time.

- Naturally idempotent: `GET`, `PUT /user/5 {name: "A"}`, `DELETE /user/5`, "set value to 5", `kubectl apply`, `terraform apply`.
- **Not** idempotent: `POST /payments` (creates a new payment each time), "add 10 to balance", "send email".

Make a non-idempotent operation safe with an **idempotency key**: the client generates a unique key (a UUID) and sends it with the request. The server stores the key with the result. If the same key comes again, it returns the **saved result** instead of doing the work again.

Stripe's docs describe exactly this: you send an `Idempotency-Key` header with `POST` requests; "retries with the same key return the saved response" (API v1, even `500` errors); keys are up to **255 characters**, V4 UUIDs are suggested, you should not put sensitive data in them; for v1 keys can be removed after at least **24 hours**; the server compares the new parameters with the original request and errors if they differ, to catch misuse; `GET` and `DELETE` do not need keys "because they are idempotent by definition".

```
 client ── POST /charge  Idempotency-Key: k1 ──> server: new key, do the charge, save result
 client <── (network drops, no response seen)
 client ── POST /charge  Idempotency-Key: k1 ──> server: key k1 known -> return saved result (no second charge)
```
Server-side recipe: a table with a **unique constraint on the key**. Insert the key first (`INSERT ... ON CONFLICT DO NOTHING`); if it already exists, return the stored response. Also store a **request fingerprint** to detect reuse with different data. Handle the "in progress" state: a second request arriving while the first is still running.

### 3.4 Delivery guarantees: at-most-once, at-least-once, exactly-once

For messages (Kafka, queues, webhooks, retries):
- **At-most-once**: send once, never retry. May **lose** messages. No duplicates.
- **At-least-once**: retry until acknowledged. Never loses, but can **duplicate**. This is the common default.
- **Exactly-once** (delivery): not possible in general over an unreliable network, because the sender cannot tell "lost message" from "lost acknowledgment". What systems really offer is **exactly-once processing effect** = **at-least-once delivery + idempotent processing** (or transactions inside one system, as some Kafka features do).

So the interview answer is: **design consumers to be idempotent**. Use a message ID and a "processed" table, or make the operation naturally idempotent (upsert by key).

### 3.5 Retries, exponential backoff, and jitter

Failures are often temporary (a blip, a restart), so retrying helps. But **careless retries cause outages**.

From the AWS Builders' Library:
- Retries add load to an already overloaded system: "retries can make the overload worse instead of better".
- Retries **multiply across layers**. Their example: three retries at each of five layers can multiply load on a database by **243 times**. Google's SRE book gives another example: three layers with 3 retries each can turn one user action into **64** attempts on the database. (The two articles count tries a little differently, so do not memorize the exact numbers. Remember the idea: the numbers **multiply** layer by layer.) **Retry at one layer only.**
- **Exponential backoff**: wait longer after each failure ("the wait time is increased exponentially after every attempt"), with a **cap**.
- **Jitter**: add randomness so many clients do not retry at the same moment. "Failed clients that back off to the same moment collide again."
- **Limit retries**: a maximum count, and a **retry budget** (for example a token bucket; Google gives the example of a server-wide budget such as 60 retries per minute).
- **Idempotency** is required before retrying anything with side effects.
- Do not retry **permanent errors** (400 Bad Request, 404, bad credentials), only temporary ones (timeouts, 503, 429 with `Retry-After`).
- Set **timeouts** on every remote call, using the dependency's latency percentiles. Too high wastes resources; too low causes extra retries.

`[REAL]` my demo, base 0.1 s, cap 10 s. "Full jitter" picks a random wait between 0 and the exponential value:
```
attempt  no-jitter   full-jitter(random 0..that)
1          0.2s       0.03s
2          0.4s       0.34s
3          0.8s       0.61s
4          1.6s       0.41s
5          3.2s       1.59s
6          6.4s       2.88s
7         10.0s       6.52s
8         10.0s       7.89s
```
Without jitter, 1,000 clients that failed together retry together at 0.2 s, 0.4 s, 0.8 s ... in waves. With jitter, the retries spread out. (The jitter variants "full jitter" and "decorrelated jitter" are described in AWS material; here I used full jitter as an example.)

Code shape:
```python
import random, time

def call_with_retry(fn, max_tries=5, base=0.1, cap=10.0):
    for attempt in range(1, max_tries + 1):
        try:
            return fn()
        except TemporaryError:
            if attempt == max_tries:
                raise
            time.sleep(random.uniform(0, min(cap, base * 2 ** attempt)))   # full jitter
```

### 3.6 Backpressure, queues, load shedding

If producers are faster than consumers, a queue grows without limit, memory runs out, latency climbs (work waits in line), and eventually everything falls over.

Tools:
- **Bounded queues**: when full, **reject or block** (this is backpressure). Never use an unbounded queue in production.
- **Load shedding**: Google's book: servers should "fail early and cheaply" when overloaded; for example return HTTP 503 when in-flight requests pass a limit. Keep queues short relative to the thread pool so rejection is early. Prefer shedding requests the client has probably already given up on.
- **Rate limiting** (token bucket, leaky bucket) at the proxy, load balancer, or per client.
- **Deadlines/timeouts propagated downstream**: "Use deadline propagation so downstream calls inherit the remaining time" so doomed work stops.
- **Graceful degradation**: return a cheaper answer (cached, partial) instead of failing.
- **Circuit breaker**: after many failures, stop calling the broken dependency for a while ("open"), then try a few calls ("half-open"). (Common pattern; general knowledge.)
- **Bulkheads**: separate pools per dependency so one slow dependency cannot use all threads.
- **Autoscaling** helps only if the bottleneck can scale, and is slower than a spike.

```
 clients ─> [ rate limit ] ─> [ bounded queue ] ─> workers ─> database
                 │ 429               │ 503 when full              ▲
                 └───────────────────┴─ clients back off + jitter ─┘
```
**Cascading failure**: one overloaded part slows down, its callers time out and retry, which adds more load, which slows it more. The SRE book notes retries can keep a backend overloaded **even after the original traffic drops**. Breaking the loop needs shedding load, cutting retries, or turning traffic off.

### 3.7 Clocks

Computers do not share one clock.
- **Wall-clock time** (`time.time()`, "2026-11-15 21:00:00") can **jump** (NTP corrections, manual changes, leap seconds) and differs between machines (**clock skew**), often by milliseconds, sometimes by seconds when NTP is broken.
- **Monotonic time** (`time.monotonic()`) only moves forward and is correct for **measuring durations** on one machine, but meaningless between machines.

Rules:
1. Measure elapsed time with a **monotonic** clock.
2. Do **not** use wall clocks from different machines to decide "which event happened first" or "last write wins" if you care about correctness: skew can make the older write look newer.
3. For ordering across machines use **logical clocks** (sequence numbers, version numbers, Lamport clocks), a single leader that assigns order, or a database transaction log.
4. Expiry times (tokens, certificates, locks) depend on wall clocks; allow a small tolerance for skew (JWT `nbf`/`exp` checks usually allow a few seconds, see file 11). A wrong clock can break TLS ("certificate not yet valid") and authentication.
5. Always run NTP/chrony and alert on clock drift.

(These are standard distributed-systems points; I did not verify them against one source today.)

### 3.8 Partial failure

In a single program, a function call either works or throws. Across a network, there is a third outcome: **you do not know**.

```
 client ──request──> server
 outcomes: (1) request lost   (2) server crashed before doing it   (3) server did it, crashed before replying
           (4) server did it, reply lost                          (5) it is just very slow
 The client sees the same thing in all five: a timeout.
```
So: every remote call needs a **timeout**, a **retry policy** with backoff and jitter, and the operation must be **idempotent** (or the client must be able to check the state first). Also think about:
- **Timeouts that are too long** hold threads and sockets (a slow dependency becomes your outage).
- **Health checks**: a node that is slow may look dead and is replaced while still working (the **split brain** problem when two nodes both think they are the leader). Use quorum and leases, and fencing.
- **Sagas / compensation** for multi-step business flows across services: if step 3 fails, run "undo" actions for steps 1 and 2 (there is no global transaction).
- The **CAP idea**: when the network splits, you must choose between consistency and availability for that data. (General knowledge; keep the answer simple: "during a partition, choose what is worse for this feature, wrong data or no data".)
- **Eventual consistency**: replicas may briefly disagree (file 10, replication lag). Read-your-writes may fail unless you route reads to the primary.

## 4. Commands to try

```bash
# Prove the race yourself (Python 3, no installs)
python3 - <<'EOF'
import threading, sys
sys.setswitchinterval(1e-6)       # switch threads very often so the race shows
count = 0
def work():
    global count
    for _ in range(200000):
        tmp = count
        count = tmp + 1
ts=[threading.Thread(target=work) for _ in range(4)]
[t.start() for t in ts]; [t.join() for t in ts]
print("expected 800000, got", count)
EOF

# See retry behavior with curl (retries only on transient errors)
curl --retry 3 --retry-delay 1 --retry-max-time 20 -sS https://example.com -o /dev/null

# Use a lock file so two cron jobs do not overlap (Linux; flock)
flock -n /tmp/job.lock ./run_job.sh || echo "already running"

# Check clock sync on Linux
timedatectl status          # shows "System clock synchronized: yes"
chronyc tracking            # offset from the time source
```
`[SAMPLE]` `timedatectl status` (Linux):
```
               Local time: Sun 2026-11-15 21:58:12 IST
           Universal time: Sun 2026-11-15 16:28:12 UTC
System clock synchronized: yes
              NTP service: active
```

## 5. Common mistakes

1. Read-modify-write without a lock, atomic update, or version check.
2. Retrying immediately, forever, at every layer (retry storm).
3. Retrying non-idempotent calls (double charge, duplicate orders).
4. No timeouts (default "wait forever") or one huge timeout for everything.
5. Unbounded queues and thread pools.
6. Using wall-clock time from different machines for ordering or "last write wins".
7. Assuming "exactly-once" delivery exists, without idempotent consumers.
8. Holding locks while doing slow network calls.

## 6. Eight interview questions with answers

**Q1. What is a race condition? Give an example and fixes.**
Two or more actors access shared data and the result depends on timing. Example: two threads read a counter, both add 1, both write, and one increment is lost. Fixes: avoid sharing, use a lock around the critical section, use atomic operations (database `UPDATE n = n + 1`), use optimistic concurrency with a version check and retry, or funnel changes through a single owner or queue.

**Q2. What is a deadlock and how do you avoid it?**
Two or more actors each hold something and wait for the other's, forever. Avoid it with one consistent lock order, short lock holding, timeouts on lock acquisition, and no slow external calls inside locks. Databases detect it and abort one transaction, so callers must retry.

**Q3. What does idempotent mean, and how do you make a POST idempotent?**
Repeating the operation gives the same final result. Use an idempotency key: the client sends a unique key; the server stores key and result with a unique constraint; a repeated key returns the stored result without redoing the work; it checks the parameters match the first request. Stripe's API works this way (key up to 255 characters, saved response returned on retry, keys pruned after at least 24 hours).

**Q4. At-most-once vs at-least-once vs exactly-once?**
At-most-once: no retries, may lose messages. At-least-once: retry until acknowledged, may duplicate. Exactly-once delivery over an unreliable network is not generally achievable; practical systems provide at-least-once delivery plus idempotent processing (or transactions inside one system) so the effect happens once.

**Q5. How do you design retries safely?**
Retry only temporary errors and only idempotent operations. Use exponential backoff with a cap and jitter, a maximum number of attempts, and a retry budget. Retry at one layer only, because layers multiply (three retries at each of three layers means 64 database calls per user action in Google's example). Set timeouts from the dependency's latency percentiles, and honor `Retry-After`.

**Q6. What is backpressure? How do you protect a service from overload?**
Backpressure makes a slow consumer limit its producers (bounded queues that reject or block, rate limits, 429/503 responses with `Retry-After`). Protect the service by load shedding (fail early and cheaply), bounded queues, per-client rate limits, deadline propagation, circuit breakers, bulkheads, graceful degradation, and autoscaling for slower growth. Unbounded queues turn overload into memory exhaustion and huge latency.

**Q7. Can you trust the system clock in a distributed system?**
Not for ordering or correctness. Wall clocks drift, jump (NTP), and differ between machines. Use monotonic clocks to measure durations on one machine, and sequence or version numbers, a single leader, or consensus to order events. Allow skew tolerance in token expiry checks, and keep NTP healthy and monitored.

**Q8. A client times out calling a payment service. What do you do?**
Do not assume failure. The payment may have happened. Retry with the **same idempotency key**, using backoff and jitter, so a repeat returns the first result. Or query the payment status by key or order ID before retrying. If it stays unknown, mark the order "pending" and reconcile later with the provider. Alert on the rate of unknown outcomes.

## 7. Self-quiz (answers at the end)

1. Why can `count = count + 1` lose updates with two threads?
2. What is the difference between exponential backoff and jitter, and why use both?
3. Which clock do you use to measure how long something took?
4. What makes "exactly-once processing" possible in practice?
5. What is a retry storm, and one way to prevent it?

**Answers**
1. It is three steps (read, add, write). Another thread can read the old value before the first writes, so one update overwrites the other.
2. Backoff spaces retries further apart over time. Jitter randomizes the spacing so clients that failed together do not retry together. Together they reduce load and avoid synchronized waves.
3. A monotonic clock.
4. At-least-once delivery plus idempotent processing (dedupe by ID or a naturally idempotent operation), or transactions within one system.
5. Many clients and layers retry at once and add load to an overloaded service. Prevent it with limited retries, backoff with jitter, retry budgets, retrying at one layer, and load shedding.

## 8. Sources

- AWS Builders' Library, Timeouts, retries, and backoff with jitter (retry amplification, 243x example, backoff, jitter, token-bucket retry limit, idempotency, timeouts): https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter
- Google SRE book, Addressing Cascading Failures (retries, 64-attempt example, 60 retries per minute budget, load shedding, graceful degradation, deadline propagation): https://sre.google/sre-book/addressing-cascading-failures/
- Stripe, idempotent requests (key length, saved response, 24 hours, parameter comparison): https://docs.stripe.com/api/idempotent_requests
- PostgreSQL isolation levels (serialization failures need retry): https://www.postgresql.org/docs/current/transaction-iso.html
- Local: Python race and backoff scripts run on this Mac, 2026-11-15

Not verified from a source: Coffman conditions; fencing tokens and lease expiry issues; circuit breaker and bulkhead patterns; clock behavior, NTP, monotonic vs wall clock rules; the CAP and saga summaries; the "exactly-once is impossible in general" claim (standard distributed-systems result, I did not cite a paper); `flock`, `timedatectl`, and `chronyc` usage; the exact retry-count arithmetic behind the 243x and 64-attempt examples (quoted as the sources state them); the `curl --retry` flags (documented in curl's man page).
