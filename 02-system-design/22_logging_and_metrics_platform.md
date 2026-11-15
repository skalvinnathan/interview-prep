# 22. Design a Logging and Metrics Platform

This is close to your work: an observability stack with Prometheus (metrics), Grafana (dashboards) and Loki (logs). Google's system design questions reportedly include a logs and metrics pipeline, and Stripe's include a metrics service and an application performance monitoring system (see `91` for sources). You can say: "I operate this kind of stack, so I know the real pain points."

---

## 1. The problem in plain words

Hundreds of services and thousands of machines produce **logs** (text lines about what happened) and **metrics** (numbers over time, like CPU or request count). Engineers need to:
- **See** the health of the system on dashboards (metrics),
- **Get alerted** when something is wrong (metrics + rules),
- **Search** what happened in detail when debugging (logs).

The platform must collect, store, query and alert, without ever falling over when the thing being observed is on fire. (Exactly when systems fail, they produce the most data.)

**Analogy: a hospital monitoring room.**
- **Metrics** are the heart-rate monitors: small numbers, every second, drawn as lines. An alarm rings if the line crosses a threshold.
- **Logs** are the doctor's detailed notes for each patient event. Big, text, searched when something went wrong.
- **Traces** (extra) follow one patient through every department and show where time was lost.
- The monitoring room must stay powered even if the hospital loses power.

---

## 2. Requirements

**Must-have**
1. **Collect** metrics and logs from many services (agents/sidecars/SDKs).
2. **Store** them for a retention period (for example metrics: 15 days at full detail, 1 year downsampled; logs: 14 to 30 days; assumptions).
3. **Query**: metrics by name and labels over a time range (aggregations, rates); logs by time range, labels and text search.
4. **Dashboards**: charts that refresh quickly.
5. **Alerting**: rules evaluated continuously ("error rate above 5 percent for 5 minutes") with notifications (`14`), grouping, silencing.
6. Multi-tenant: teams see their own data; limits per team.

**Non-functional**
- **High write throughput**, write-mostly workload (reads are rare compared to writes).
- The platform must be **more available than what it monitors**. Alerts must work during an outage.
- Tolerate **loss of a little data** (a few samples) but not blocked ingestion.
- Cost control: storage and cardinality limits.
- Query latency: dashboards in a few seconds.

**Out of scope**
- Full distributed tracing storage and analysis (mention as a third pillar), anomaly detection with machine learning, long-term analytics warehouse, security event correlation (SIEM).

---

## 3. The numbers (estimates)

Let us size a big company (assumption): 100,000 pods/instances. Each exposes 500 metric series, scraped every 15 seconds. Each pod logs 50 lines per second at 200 bytes.

| Item | Value |
|---|---|
| Metric series | 100,000 x 500 = 50 million active series |
| Samples per second | 50M / 15 s = about 3.3 million samples/s |
| Bytes per sample after compression | about 1 to 2 bytes (time-series databases compress well; Prometheus-style stores are commonly cited at this order; treat as an estimate) |
| Metric storage per day | 3.3M x 86,400 = about 288 billion samples x 2 B = about 570 GB/day (about 8.6 TB for 15 days) |
| Log lines per second | 100,000 x 50 = 5 million lines/s |
| Log bytes per second | 5M x 200 B = 1 GB/s = about 86 TB/day raw. With compression about 10x = about 8.6 TB/day stored. For 14 days = about 120 TB |
| Queries | Dashboards and alerts: maybe 5,000 queries/s total, most are alert rules (cheap, repeated) |

Meaning: **logs dominate size** (and cost); metrics dominate **sample rate**; both are write-heavy. This is why Loki indexes only labels, not full text (see below), to save cost.

(Your own stack is much smaller than this; use the method, not these exact numbers.)

---

## 4. The API

**Metrics ingest** (push) or scrape (pull):

```
Pull (Prometheus style): server calls GET http://pod:9100/metrics every 15 s
   text lines like:  http_requests_total{service="pay",code="200"} 12345

Push (remote write): POST /api/v1/push   body: compressed batch of series [{labels, samples:[(ts,value)]}]
```

**Log ingest:**

```
POST /loki/api/v1/push   (Loki-style push API; shown for flavour)
  body: { "streams": [ { "stream": {"service":"pay","env":"prod","pod":"p1"},
                          "values": [ ["1731700000123000000", "payment failed: timeout"], ... ] } ] }
```

**Query:**

```
GET /api/v1/query_range?query=sum(rate(http_requests_total{service="pay",code=~"5.."}[5m]))&start=...&end=...&step=15s
GET /logs/query_range?query={service="pay",env="prod"} |= "timeout"&start=...&end=...&limit=1000
```

**Alerts:**

```
rule: alert: HighErrorRate
      expr: sum(rate(http_requests_total{code=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
      for: 5m
      labels: { severity: page }
      annotations: { summary: "Error rate above 5 percent" }
```

(The syntax above follows the common Prometheus and Loki styles; check the official docs for exact details.)

---

## 5. The data model

### Metrics: a time series

A series = **name + labels** (key-value pairs), and a list of `(timestamp, value)` samples.

```
http_requests_total{service="pay", code="200", pod="p1"}  ->  (t1, 100), (t2, 130), (t3, 170) ...
```

Types: **counter** (only goes up: requests), **gauge** (up and down: memory), **histogram** (counts in buckets: latency distribution; allows p50/p95/p99).

**Cardinality** = number of distinct series. Every unique label combination is a new series. Putting `user_id` as a label creates millions of series and kills the database. **Cardinality is the number one cause of metrics outages.** Rule: labels must have a small, bounded set of values.

Storage layout (time-series DB): data is grouped in **blocks of time** (for example 2 hours), compressed (delta-of-delta for timestamps, XOR for values), with an **inverted index** from label values to series ids so queries like `service="pay"` find series fast. The newest data sits in memory plus a **write-ahead log**, then flushes to disk.

### Logs: lines in streams

Each log entry: `(timestamp, labels (stream), line)`. Two main design philosophies:

| Approach | Example | Index | Cost | Search |
|---|---|---|---|---|
| **Full-text index** | Elasticsearch/OpenSearch | Index every word | High (index can be as big as the data) | Very fast, rich text queries |
| **Label-only index** | Loki | Index only labels (service, env, pod); store compressed chunks of lines | Low (cheap object storage) | Select streams by labels, then **scan** the lines (grep) in the time range |

Trade-off to say: Loki-style is much cheaper and fits "I know which service and time, now find the line", but searching all logs for a random word across everything over days is slow. Elasticsearch-style is expensive but quick for ad-hoc text search.

### Other data
- **Alert rules**, **dashboards** (JSON), **tenants and quotas** in a small SQL database.
- **Long-term storage** in object storage (cheap, durable): old metric blocks (downsampled) and log chunks.

---

## 6. Version 1 (simple)

```
 [Services] --> write logs to local files (and /metrics endpoint)
 [One Prometheus server] scrapes all /metrics, stores on local disk
 [Grafana] --> queries Prometheus
 [Engineers] ssh to servers and grep log files
```

Works for a small company. Problems at scale: one Prometheus has limited memory and disk (millions of series is the limit of one node); if it dies, you lose data and alerts; logs on a dead machine disappear; grepping across hundreds of machines is impossible; no long-term retention.

---

## 7. Growing 100x, step by step

**Step 1. Agents collect and ship logs.** A small agent on each node (DaemonSet in Kubernetes; for example Promtail/Fluent Bit/Alloy style) tails container logs, adds labels (namespace, pod, service) and ships batches to a central ingest. Local buffering on disk handles short outages. Logs are no longer lost with the machine.

**Step 2. Split ingest from storage with a buffer.** Put a **durable queue (Kafka)** between collectors and storage. If storage is slow or down, the queue holds data (hours). Spikes (an incident produces 10x logs) are smoothed. Consumers scale independently. (`01g`)

```
 Agents -> [Ingest gateway: auth, tenant, rate limit] -> Kafka -> [Writers/Ingesters] -> Storage
```

**Step 3. Shard metrics by series.** One Prometheus per team or per cluster (**federation / sharding**). Each scrapes its own targets (sharded by target or by hash of series). A global layer (Thanos, Mimir, Cortex style) provides:
- **Remote write**: each Prometheus ships samples to a central, horizontally scalable store.
- **Distributor** -> hashes each series to **ingesters** (consistent hashing, replication factor 3) -> flushes blocks to object storage.
- **Querier** fans out to ingesters (recent data) and object storage (old data) and merges.
- A **query frontend** splits big range queries into daily pieces, caches results, and queues per tenant.

```
 Prometheus (per cluster) --remote write--> [Distributor] --hash(series)--> [Ingesters x N, replicated x3]
                                                                               | flush blocks every ~2h
                                                                               v
 Grafana --> [Query frontend (cache, split)] --> [Queriers] --> ingesters + [Object storage (blocks)]
                                                                               ^
                                                              [Compactor: merge, downsample, apply retention]
```

**Step 4. Same pattern for logs.** Distributor -> ingesters (in memory chunks per stream, WAL) -> flush compressed chunks to object storage; a small **index** (labels -> chunks) in a key-value store or object storage; queriers read index then fetch and scan chunks; caches for chunks and query results. (This is the architecture style of Loki; it is simple because object storage is the primary store.) 

**Step 5. Control cardinality and volume.** The ingest gateway enforces **per-tenant limits**: max active series, max label count and length, max log line size, max ingest rate. Drop or reject beyond limits with clear errors (and a metric) rather than crash. Provide dashboards showing top series by cardinality so teams fix offenders. Sampling or dropping noisy debug logs at the agent. (Rate limiting design: `11`.)

**Step 6. Retention and downsampling.** Keep raw resolution (15 s) for 15 days; then downsample to 5-minute and 1-hour points (min/max/avg/count) for a year. Compactor job does it. Logs: shorter retention, or tiering (hot 7 days fast, then cold object storage). Storage cost drops by 10x or more.

**Step 7. Alerting path (highest reliability).** Alert rules are evaluated by a separate **ruler** that queries the store every minute (or evaluates in the Prometheus itself). Firing alerts go to an **Alertmanager** cluster that **deduplicates, groups, silences, routes** (by severity and team) to pager/Slack/email (`14`). Run Alertmanager as a gossip cluster (several nodes) so one dying does not lose alerts. Add a **dead man's switch**: an always-firing alert that must keep arriving at an external service; if it stops, the monitoring system itself is broken and someone gets paged. And keep **an independent small monitoring path** for the monitoring system (watch the watchers).

**Step 8. Multi-tenancy.** Each team = tenant id in a header; data separated by tenant in storage; per-tenant limits for ingest and queries (max query range, concurrency); fair queueing in the query frontend so one heavy dashboard cannot starve others. Access control through the gateway (`21`).

**Step 9. Query performance.** Dashboards reuse queries often: cache results (query frontend), pre-compute expensive aggregations with **recording rules** (for example per-service request rate saved as a new series), limit query range, and use downsampled data for long ranges. Avoid regex over huge series sets.

**Step 10. Multi-region / high availability.** Run the platform in at least two zones; replication factor 3 for ingesters across zones; Kafka replicated; object storage replicates; a second small independent copy of critical alerting in another region. Accept that cross-region queries are slower.

**Step 11. Traces (third pillar, brief).** Add distributed tracing (OpenTelemetry-style): sampled traces stored in a trace store, linked to logs and metrics via trace id and exemplars. Sample (for example 1 percent plus all errors) because full capture is too costly.

Final picture:

```
 Services/Pods (metrics endpoints, logs, traces via OpenTelemetry)
      |             |
  Prometheus/     Log agents
  scrapers        (buffer on disk)
      |remote write     |
      v                 v
 [Ingest gateway: auth, tenant, limits] ----> Kafka (buffer, replicated)
      |                                           |
      v                                           v
 [Distributors] -> [Ingesters (replicated, WAL)] -> Object storage (blocks/chunks) <- [Compactor, retention, downsampling]
                                 ^                                   ^
 Grafana -> [Query frontend (split, cache, fair queue)] -> [Queriers]
 [Ruler: alert + recording rules] -> [Alertmanager cluster: dedupe, group, route] -> Pager/Slack/Email
 Watchdog (dead man's switch) -> external service
```

---

## 8. Trade-offs and why

| Choice | Why | Cost |
|---|---|---|
| Pull (scrape) for metrics | Simple, service discovery, you know when a target is down | Hard for short-lived jobs (use push gateway) and across firewalls |
| Push (remote write) for central store | Scales out ingest | Need back-pressure and retries |
| Label-only log index | 10x cheaper | Slow full-text across everything |
| Kafka buffer | Absorbs spikes, decouples | More infrastructure; latency of seconds |
| Object storage as main store | Cheap, durable | Slower reads; need caches |
| Replication factor 3 for ingesters | No loss when a node dies | 3x memory/network for recent data |
| Downsampling | Cheap long retention | Loss of precision |
| Cardinality limits | Protect the platform | Teams must follow rules; some data rejected |
| Sampling traces/logs | Cost | May miss rare events (always keep errors) |
| Eventual consistency of data in queries | Scale | Data a few seconds late |

---

## 9. What breaks and how to fix it

| Failure | Effect | Fix |
|---|---|---|
| Cardinality explosion (a label with user ids) | Memory blowup, slow queries, OOM | Per-tenant series limits, reject at ingest, top-cardinality dashboard, relabel/drop rules, education |
| Log storm during an incident | Ingest overwhelmed | Kafka buffer, per-tenant rate limits, drop debug level, agent-side sampling, autoscale |
| Ingester crashes | Recent unflushed data at risk | WAL replay, replication x3, restart quickly |
| Object storage slow | Slow queries | Caches, query frontend limits, retry with backoff |
| Expensive query | Everyone slow | Query limits (range, series, time), per-tenant concurrency, timeouts, fair queues, recording rules |
| Alerting pipeline down | No pages in an outage | Redundant Alertmanagers, dead-man's-switch, independent watcher |
| Alert flood (alert storm) | Pager fatigue | Grouping, inhibition (root-cause alert suppresses symptoms), rate-limit notifications, good thresholds |
| Clock skew on hosts | Samples rejected or misordered | NTP; accept small out-of-order window; reject too old/new |
| Disk full on agent buffer | Data loss | Bounded buffer, drop oldest, alert on buffer use |
| Silent data loss (collector broken) | Blind spot | Meta-monitoring: samples ingested per tenant, scrape success, last-seen per target; alert on drops |
| Sensitive data in logs (passwords, tokens, PII) | Security incident | Redaction at agent, log schema rules, access control, short retention |
| Monitoring needs monitoring | Circular failure | Separate small instance monitors the platform |

---

## 10. Questions the interviewer asks next

**Q1. Push or pull for metrics?**
A. Pull gives easy discovery and health (a failed scrape means a down target) and central control of scrape rate. Push is better for short-lived jobs and crossing networks. Many setups use pull at the edge and push (remote write) to the central store.

**Q2. What is cardinality and why does it matter?**
A. The number of distinct label combinations, i.e. series. Memory and index size grow with it. One bad label like user id can create millions of series and crash the store. I enforce limits per tenant and review label design.

**Q3. Why does Loki not index log text?**
A. Indexing every word makes the index as big as the logs and costs a lot. Loki indexes only labels and keeps compressed chunks in cheap object storage. Queries select streams by labels and time first, then scan. It is cheap and good for known-service debugging, weaker for broad free-text search.

**Q4. How do you make sure alerts always fire?**
A. Redundant evaluators and Alertmanager cluster, rules close to the data, and a watchdog alert that must continuously reach an external system; if it stops, a separate path pages us. Also meta-monitoring of ingest and rule evaluation failures.

**Q5. How do you keep dashboards fast?**
A. Query frontend with splitting and caching, recording rules for heavy aggregations, downsampled data for long ranges, query limits, and per-tenant fairness.

**Q6. How do you handle 10x log volume during an incident?**
A. Kafka absorbs the burst; per-tenant rate limits protect others; agents can sample or drop low-level logs under pressure; storage scales out; and we keep errors with priority.

**Q7. How do you store a year of metrics cheaply?**
A. Compact old blocks into object storage and downsample to coarse resolution (5 minute, 1 hour). Raw data kept only short term.

**Q8. How do you design multi-tenant limits?**
A. Tenant id on every request; limits on ingest rate, active series, label sizes, query range, concurrency, and rejections returned with explicit errors and counted in metrics.

**Q9. Metrics, logs, traces: when do you use each?**
A. Metrics tell you **that** something is wrong and how big (cheap, aggregated). Traces show **where** time is spent across services. Logs explain **why** with details. Alert on metrics, investigate with traces and logs.

**Q10. What are SLO alerts?**
A. Alerts on burn rate of the error budget (for example, consuming the monthly budget 14 times faster than allowed over 1 hour) rather than raw thresholds; fewer false alarms and tied to user impact. (See `03`.)

**Q11. What do you monitor about the platform itself?**
A. Ingest rate and rejections, active series per tenant, ingester memory and WAL replay time, queue lag, query latency and errors, rule evaluation duration and misses, object storage errors, Alertmanager delivery failures, and the watchdog.

---

## 11. Say it out loud (6 sentences)

1. "A logging and metrics platform collects huge write-heavy streams of numbers and text, stores them cheaply, and powers dashboards and alerts, and it must be more reliable than the systems it watches."
2. "In my estimate 50 million series scraped every 15 seconds give about 3.3 million samples per second, and logs dominate storage at tens of terabytes a day, so cost drives the design."
3. "Agents ship data through an ingest gateway with per-tenant limits into Kafka, which absorbs incident spikes, and then to distributors and ingesters that hash by series or stream, replicate three times, and flush compressed blocks to object storage."
4. "For logs I prefer a label-only index like Loki because it is far cheaper than full-text indexing, accepting slower broad text search."
5. "Cardinality is the biggest risk, so I enforce series and label limits per tenant, and I protect queries with a frontend that splits, caches and fairly queues them, plus recording rules and downsampling."
6. "Alerting runs on a redundant ruler and Alertmanager cluster with grouping and a dead-man's-switch watchdog, and I monitor the platform itself so silent data loss is detected."
