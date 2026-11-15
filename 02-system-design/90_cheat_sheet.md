# 90. Cheat Sheet (one page)

## The 7 steps (45 minutes)
| # | Step | Min | Say / draw |
|---|---|---|---|
| 1 | **R**equirements | 5 | Ask: users? top 2-3 features? read or write heavy? stale OK? loss OK? Say out-of-scope |
| 2 | **S**cale | 3 | DAU x actions / 86,400 = QPS; peak x3; storage x years x copies (3) |
| 3 | **A**PI | 3 | 2-4 calls; Idempotency-Key on POST; cursor pagination |
| 4 | **D**ata | 3 | Tables, primary key, shard key, SQL or NoSQL + why |
| 5 | **H**igh-level | 8 | V1 simple, then LB, cache, queue, replicas |
| 6 | **D**eep dive | 10 | The hardest part (id generation, fan-out, hot key, state machine) |
| 7 | **T**rade-offs and failures | 5 | What dies? What is slow? Monitor what? |

Memory line: *Really Smart Architects Draw Huge Diagrams Thoughtfully.*

## Numbers
- 1 day = 86,400 s (use 10^5). 1M req/day = 10 req/s. 100M/day = 1,000/s.
- 2^10 = 1 thousand (KB), 2^20 = 1 million (MB), 2^30 = 1 billion (GB), 2^40 = TB, 2^50 = PB.
- RAM ~100 ns; SSD ~100 us; same-DC network ~0.5 ms; cross-continent ~100+ ms (rough).
- 99.9% = 8.8 h/yr down; 99.99% = 52 min/yr. Error budget 99.9% over 30 d = 43 min.
- One server ~1k-10k simple req/s; Redis node ~100k ops/s (rough, state as assumptions).
- base62: 62^6 = 56.8 billion, 62^7 = 3.5 trillion.

## Building blocks: one line each
- **Stateless servers** + load balancer = easy scale out. L4 = fast, L7 = smart routing.
- **DNS** (name -> IP, TTL) + **CDN** (copies near users; pull/push; versioned file names).
- **SQL**: transactions, joins, money. **NoSQL**: scale, simple access by key. Start with SQL unless a reason.
- **Index**: fast reads, slower writes. Composite index: left-to-right order.
- **Cache**: cache-aside + TTL + LRU. Invalidate by delete-on-write. Fix stampede (lock, jitter), penetration (cache nulls, Bloom filter), hot key (replicate).
- **Replication** = copies (availability, read scale; lag!). **Sharding** = split (size, write scale). Key choice matters. Consistent hashing. Do not shard first.
- **Queue**: decouple, buffer, retry. At-least-once + idempotent consumer. DLQ for poison. Kafka: order per partition, consumer group, offsets, replay.
- **CAP**: during a network partition choose C (reject) or A (stale). Money = C; feeds/likes = A. PACELC: else latency vs consistency.

## Reliability checklist (say at least 3 in every design)
1. **Timeout** on every call. 2. **Retry** with exponential backoff + **jitter**, max attempts, only if idempotent, one layer only.
3. **Idempotency key** (unique constraint, store response). 4. **Rate limit** (token bucket; 429 + Retry-After).
5. **Circuit breaker** (closed / open / half-open) + fallback. 6. **Bulkhead**, load shedding.
7. **Liveness** (restart) vs **readiness** (traffic). 8. **SLI/SLO/error budget**; alert on burn rate.
9. **Outbox** for DB + event atomic. 10. **Saga** + compensation for multi-service. 11. **Reconciliation** job as safety net.
12. **Dead-letter queue** + alert. 13. **Multi-zone**, no single point of failure.

## Design pattern quick map
| Problem | Core idea |
|---|---|
| URL shortener | Base62 code, counter ranges, cache-aside, 302 |
| Rate limiter | Token bucket in Redis + Lua, fail open, gateway |
| Chat | WebSocket, store-then-deliver, per-chat order, sync by last msg id |
| News feed | Hybrid push/pull, fan-out via Kafka, ids in Redis |
| Notification | Queue per channel/priority, idempotency, provider failover, DLQ |
| File storage | Chunks + hashes, blob + metadata split, change-log sync, conflict copy |
| Autocomplete | Trie / prefix -> top-K, precomputed, snapshot swap, CDN |
| Video | Transcode DAG, segments, adaptive bitrate, CDN |
| Payments | Idempotency, state machine, double-entry ledger, outbox, webhooks, reconcile |
| Orders | Saga, reservation with expiry, atomic conditional update, flash-sale slots |
| Job scheduler | SKIP LOCKED claim, DAG, lease + heartbeat, retries, fencing |
| Gateway + auth | OIDC, JWT local verify, policy cache + events, maker-checker, deny-list |
| Logs + metrics | Agents -> Kafka -> ingesters -> object storage, cardinality limits, watchdog |

## Phrases
- "Before I design, can I ask a few questions?"
- "Let me assume ... tell me if that is wrong."
- "The simplest version is ... it breaks when ... so I add ..."
- "The trade-off is X versus Y; I choose X because ..."
- "What happens if this box dies?"
- "I would make this idempotent so retries are safe."
- "I use strong consistency for money and eventual for reads users can tolerate."

## If stuck
Pause (say so) -> go back to requirements -> make it simple (one user, then a million) -> compare two options -> ask for a hint politely -> park it as a risk and finish the whole design.

## Your own stories (keep true and short)
Provisioner = DAG, dependency order, retries, resume (-> job scheduler, saga, order flow). Access-control service + OIDC gateway + shared library + maker-checker (-> auth design, consistency of revocation). Observability stack (-> metrics and logs, SLOs, alert fatigue). CI/CD hub (-> pipelines as workflows, idempotent steps, rollbacks).
