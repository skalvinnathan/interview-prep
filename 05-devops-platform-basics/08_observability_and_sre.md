# 08. Observability and SRE

Legend: `[REAL]` = I ran it on this Mac on 2026-11-15 (Python scripts with a fixed random seed, so you get the same numbers). `[SAMPLE]` = example written to show the shape. The SRE ideas (four golden signals, SLI/SLO/SLA, error budgets, percentiles, burn-rate alerts, postmortems) and the Prometheus histogram rule were read from Google's SRE books and the Prometheus docs (links at the end).

---

## 1. What it is (plain words + analogy)

**Observability** = being able to ask your running system "what is wrong and why?" using the data it gives out, **without** shipping new code.
**SRE** (Site Reliability Engineering) = treating operations as a software problem: set a clear reliability target, measure it, and use the gap to decide between new features and stability work.

Analogy: a **car dashboard and a mechanic's diary**.
- **Metrics** = the gauges (speed, fuel, temperature). Numbers over time. Cheap and good for "is something wrong?".
- **Logs** = the diary. One line per event ("at 10:03 brakes applied"). Good for "what exactly happened?".
- **Traces** = a GPS track of **one trip** through all the towns (services). Good for "where did this one slow request spend its time?".

Metrics tell you **that** there is a problem. Traces tell you **where**. Logs tell you **why**.

## 2. Why it matters in interviews

SRE and platform interviews (Google, Amazon, ScienceLogic, Unikraft SRE) always include: define SLI/SLO, explain error budgets, "why not average latency?", "how do you alert?", "walk me through an incident", "write a postmortem". 2026 prep guides say SRE questions "center on incident handling and error budgets", for example "what happens when your error budget runs out?" and "how would you respond to rising error rates before customers report them?". You also have real Prometheus/Grafana/Loki experience; be ready to go deep on it.

## 3. How it works, step by step

### 3.1 The three pillars, plus how they connect

```
 Your service ──emits──> metrics  ──> Prometheus ──> Grafana dashboards + Alertmanager (pages)
              ──emits──> logs     ──> Loki       ──> Grafana (search logs)
              ──emits──> traces   ──> Tempo/Jaeger ──> Grafana (view a request's path)
        all three can be sent through the OpenTelemetry Collector
```
Link them with a shared **trace ID** in every log line, so from a slow trace you can jump to its logs.

### 3.2 Prometheus (metrics)

- Prometheus **pulls** ("scrapes") a `/metrics` HTTP page from each target every N seconds and stores the numbers as **time series** (a metric name plus labels). (Pull model: general knowledge.)
- Metric types:
  - **Counter**: only goes up (requests total). Always use `rate()` on it.
  - **Gauge**: goes up and down (memory in use, queue length).
  - **Histogram**: counts observations in **buckets** (how many requests took < 0.1 s, < 0.5 s, ...). Lets you compute percentiles.
  - **Summary**: computes quantiles inside the app.
- **Labels** are `key="value"` tags (`{method="GET", status="500"}`). **Cardinality** = how many different label combinations exist. Never put user IDs, emails, or request IDs in labels: millions of series will crash Prometheus.
- **PromQL** examples:
```promql
# requests per second, per service, over the last 5 minutes
sum by (service) (rate(http_requests_total[5m]))

# error ratio (share of 5xx)
sum(rate(http_requests_total{status=~"5.."}[5m]))
  /
sum(rate(http_requests_total[5m]))

# p99 latency from a classic histogram (keep the "le" label when summing!)
histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
```
The Prometheus docs say it directly: histograms can be **aggregated** because "bucket counts are additive"; summary quantiles are "not aggregatable", and "averaging the quantiles yields statistically nonsensical values". They also recommend native histograms when you can use them.

- **Alertmanager** receives alerts from Prometheus rules, groups them, silences them, and sends to Slack/PagerDuty.
- **Exporters** expose metrics for things you cannot change (node_exporter for Linux, kube-state-metrics for Kubernetes objects, cAdvisor for containers).

### 3.3 Loki (logs)

From Grafana's docs: Loki "does not index the contents of the logs". It indexes only **labels** on each log stream and stores the log text compressed in chunks (object storage like S3 or GCS). So it is cheap, but you must choose a **small set of low-cardinality labels** (app, namespace, pod, level). You search with **LogQL**, which looks like PromQL: pick streams with label matchers, then filter lines.

```logql
{namespace="prod", app="api"} |= "error" != "healthcheck"
{app="api"} | json | status >= 500
sum by (app) (rate({namespace="prod"} |= "error" [5m]))     # logs turned into a metric
```
Good logging: structured (JSON) lines, a trace ID, a level, **no secrets or personal data**, and a sane volume (logs cost money). Grafana's docs name **Grafana Alloy** as an agent to ship logs (Promtail is an older agent; I did not verify its status, check the current docs).

### 3.4 Grafana

A dashboard and alerting UI that reads many data sources (Prometheus, Loki, Tempo, cloud monitors). Good dashboards: start with the four golden signals per service; link to logs and traces; show SLO status and burn rate; avoid a wall of 60 charts.

### 3.5 OpenTelemetry (OTel)

An open standard and set of tools for creating and moving telemetry. From the docs, its signals are **traces** (follow a request's route), **metrics** (runtime measurements), **logs** (individual events), and **baggage** (context carried between signals). Main parts (general knowledge; the signals page I read did not cover them): **SDKs/auto-instrumentation** in your code, **OTLP** (the wire protocol), and the **Collector** (a small service that receives, processes, and exports telemetry to any backend). Traces are made of **spans** (one timed operation, such as a DB call). A **trace ID** passed along in HTTP headers ties spans from many services together (context propagation). Why it matters: you instrument once and can change the backend later without changing code.

### 3.6 The four golden signals (Google SRE book)

For every user-facing service, watch:

| Signal | Plain meaning | Note from the book |
|---|---|---|
| **Latency** | time to serve a request | "Track successful and failed requests separately": "a slow error is even worse than a fast error" |
| **Traffic** | how much demand | e.g. HTTP requests per second |
| **Errors** | rate of failing requests | explicit (HTTP 500), implicit (200 with wrong content), or by policy (too slow) |
| **Saturation** | how full the service is | the most constrained resource; many systems degrade before 100 percent |

Related methods you may hear: **RED** (Rate, Errors, Duration, for services) and **USE** (Utilization, Saturation, Errors, for resources like CPU and disks). They are similar ideas.

### 3.7 SLI, SLO, SLA, error budget

- **SLI** (indicator): a measured number about the service. "Share of requests that succeeded and took under 300 ms."
- **SLO** (objective): the target for the SLI. "99.9 percent of requests good over 30 days."
- **SLA** (agreement): a contract with consequences if the SLO is missed (refunds). Google's book: if there is no explicit consequence, "you're probably looking at an SLO". An SLA is looser than the internal SLO.
- **Error budget** = `1 - SLO` = the amount of failure you are **allowed**. The book calls it "an SLO for meeting other SLOs".

Maths you should be able to do in your head (30-day month = 43,200 minutes):

| SLO | Allowed bad | Downtime per 30 days |
|---|---|---|
| 99% | 1% | 432 min (7.2 hours) |
| 99.5% | 0.5% | 216 min (3.6 hours) |
| 99.9% | 0.1% | 43.2 min |
| 99.95% | 0.05% | 21.6 min |
| 99.99% | 0.01% | 4.32 min |

(I computed these: minutes × allowed fraction.) For request-based SLIs, budget = allowed failed requests. If the SLO is 99.9% and you serve 10 million requests in the window, you may fail 10,000.

How budget is used: while budget remains, the team ships features. When it is nearly spent, the team **slows releases and does reliability work**. This turns "dev wants speed vs ops wants stability" into one number both sides agreed on. The book says teams track it daily or weekly, with monthly or quarterly reviews, and the gap between the observed violation rate and the budget is used to decide on releases.

Choosing good SLIs: measure **what users feel** (successful, fast responses at the edge/load balancer), not what the server feels (CPU). Do not set 100 percent: it is too costly, and users cannot tell the difference beyond what their own network gives.

### 3.8 Percentiles, and why you cannot average them

**Percentile**: p99 = "99 percent of requests were faster than this number". p50 = median.

Why not the mean: Google's book says averages "can hide a long tail" of slow requests; use percentiles. Its example: typical request about 50 ms but 5 percent about 20 times slower, which average-based monitoring misses. And in the monitoring chapter: a service averaging 100 ms at 1,000 requests per second can still have 1 percent of requests taking 5 seconds.

`[REAL]` my demo: 950 requests near 50 ms and 50 requests near 1000 ms (5 percent slow):
```
mean  = 98 ms          <- looks fine
p50   = 50 ms          <- looks fine
p95   = 69 ms
p99   = 1104 ms        <- the slow users are visible only here
```
One in twenty users waits about a second, and the mean (98 ms) hides it.

**Why you cannot average percentiles across servers**: a percentile is a position in a sorted list. The positions of two separate lists tell you nothing about the position in the merged list. `[REAL]` demo: server A had 1000 requests (3 percent slow, 2000 ms) and server B had 100 fast requests:
```
server A (1000 requests) p99 = 2007 ms
server B ( 100 requests) p99 = 62 ms
average of the two p99s   = 1035 ms   <- WRONG
p99 of all 1100 requests  = 2004 ms   <- RIGHT
```
The average (1035 ms) matches no real user experience. B's tiny traffic got equal weight to A's big traffic. **Fix**: keep **histogram buckets** (counts are additive), sum buckets across servers, then compute the percentile from the summed buckets (`histogram_quantile` in Prometheus). Do the same across time windows: do not average p99 over 5-minute points to get an hourly p99.

Honest limits: bucket-based percentiles are **estimates** (accuracy depends on bucket boundaries). Native histograms improve that. Also, SLOs are often written as "99% of requests under 300 ms" (a ratio of good events), which **can** be aggregated by simply adding good and total counts. That is often better than quoting p99.

### 3.9 Alerting: symptoms, not causes

Google's book: "it's better to spend much more effort on catching symptoms than causes." Page a human when **users are hurt now** (error ratio high, latency high, SLO burning fast). Do not page on "CPU is 85 percent" or "pod restarted once" unless it is a very definite, very imminent cause (disk will be full in 30 minutes). Cause-level signals belong on dashboards and low-priority tickets. Every page should be **urgent, actionable, and need a human**. Noisy alerts cause alert fatigue, and people stop trusting them.

**Burn-rate alerts** (Google SRE Workbook): burn rate = "how fast, relative to the SLO, the service consumes the error budget". Burn rate 1 would use up exactly the whole budget at the end of the window. The workbook's recommended multiwindow, multi-burn-rate alerts for a 99.9 percent SLO over 30 days:

| Action | Long window | Short window | Burn rate | Budget used when it fires |
|---|---|---|---|---|
| Page | 1 hour | 5 min | 14.4 | 2% |
| Page | 6 hours | 30 min | 6 | 5% |
| Ticket | 3 days | 6 hours | 1 | 10% |

An alert fires only when **both** windows exceed the threshold: the long window shows it is real and significant, the short window shows it is **still happening** (suggested short window is 1/12 of the long one). Check the maths: 14.4 × (1 hour / 720 hours) = 2 percent.

```yaml
# Prometheus alert shape (error ratio recording rule names are examples)
groups:
- name: slo
  rules:
  - alert: HighErrorBudgetBurn
    expr: |
      job:slo_errors_per_request:ratio_rate1h  > (14.4 * 0.001)
      and
      job:slo_errors_per_request:ratio_rate5m  > (14.4 * 0.001)
    for: 2m
    labels: { severity: page }
    annotations:
      summary: "Burning error budget 14.4x too fast"
      runbook_url: https://wiki.example.com/runbooks/api-errors
```
Every alert needs a **runbook link** and an owner.

### 3.10 Incident response

Goal: **reduce user impact fast**, then learn. Not "find the root cause first".

```
 detect -> triage (severity, who is hit?) -> declare incident -> mitigate -> resolve -> postmortem -> action items
```
Roles (as described in 2026 prep material): an **Incident Commander** (decides, coordinates, does not debug), a **communications lead** (updates status page and stakeholders), and **responders/subject experts** (investigate and fix). One channel for the incident. Write a **timeline** as you go.

Order of thinking:
1. **What is the impact?** Which users, how many, since when, which regions? (Look at the SLO dashboard.)
2. **What changed?** Deploys, config changes, feature flags, traffic spikes, cert expiry, a dependency outage. Most incidents follow a change.
3. **Mitigate first**: roll back, turn off a feature flag, shift traffic away, scale up, rate-limit. Fix the root cause later.
4. **Communicate** on a fixed rhythm (for example every 30 minutes), even if it says "no new information".
5. Confirm recovery with the SLIs, not with feelings. Keep watching.
6. **Postmortem** within a few days.

Severity example (define your own): SEV1 = most users down or data loss; SEV2 = a major feature broken or heavy degradation; SEV3 = minor.

### 3.11 Blameless postmortem template

Principles from Google's SRE Workbook chapter on postmortem culture: focus on **system gaps, not people** ("Individuals act in good faith and make decisions based on the best information available"); use neutral, factual language; one owner; include everyone involved; write promptly; share widely; "a postmortem without subsequent action is indistinguishable from no postmortem".

Template (sections follow the workbook's example; wording is mine):
```
# Postmortem: <short title>            Date: <YYYY-MM-DD>   Owner: <name>   Status: <draft/final>

## Summary
Two or three sentences: what broke, who was affected, how long, how it ended.

## Impact
- Duration: <start> to <end> (<N> minutes)
- Users/requests affected: <number or %>, which regions/products
- Business impact: <revenue, SLA, support tickets>
- SLO/error budget used: <x% of the monthly budget>

## Detection
How we found out (alert? customer?). Time from start to detection.

## Root causes and trigger
Trigger: the event that set it off.
Root causes: the system weaknesses that let it happen (not "person X made a typo").

## Timeline (all times in one timezone)
10:02  deploy 4.7 started
10:09  error-rate alert fired (page)
10:14  IC declared SEV2
10:21  decision to roll back
10:26  rollback done, errors falling
10:40  recovery confirmed

## What went well / what went poorly / where we got lucky

## Action items
| # | Action | Type (prevent/detect/mitigate) | Owner | Priority | Ticket | Done when (verifiable) |
```
Make action items **owned, tracked, and verifiable**, and include prevention, not only mitigation.

## 4. Commands to try

I ran the percentile demo above with Python. Other things to try:

```bash
# Percentiles yourself (Python 3, no installs)
python3 - <<'EOF'
import random, statistics
random.seed(42)
lat = sorted([random.gauss(50,5) for _ in range(950)] + [random.gauss(1000,100) for _ in range(50)])
p = lambda q: lat[int(len(lat)*q/100)-1]
print("mean", round(statistics.mean(lat)), "p50", round(p(50)), "p99", round(p(99)))
EOF

# Prometheus / Grafana locally (needs Docker running)
docker run -d -p 9090:9090 prom/prometheus
docker run -d -p 3000:3000 grafana/grafana

# Query Prometheus from the shell
curl -s 'http://localhost:9090/api/v1/query?query=up' | jq .

# Kubernetes quick signals
kubectl top pods -A --sort-by=memory | head       # needs metrics-server
kubectl get events -A --sort-by=.lastTimestamp | tail
kubectl logs deploy/api --since=15m | grep -i error | tail
```
`[SAMPLE]` Prometheus API answer:
```
{"status":"success","data":{"resultType":"vector","result":[{"metric":{"__name__":"up","job":"prometheus"},"value":[1763243000.1,"1"]}]}}
```

## 5. Common mistakes

1. Using the average latency (hides the tail).
2. Averaging percentiles across servers or time windows.
3. High-cardinality labels (user ID, URL with IDs) in Prometheus or Loki.
4. Alerting on causes (CPU 80 percent) so people get paged for non-problems; no runbooks.
5. SLOs of 100 percent, or SLIs that measure the server instead of the user.
6. Looking for the root cause before mitigating during an incident.
7. Postmortems that name and blame a person, or that have no owned follow-up actions.
8. Logs with secrets or personal data, or logging so much that cost and noise explode.

## 6. Eight interview questions with answers

**Q1. Explain metrics, logs, and traces and when you use each.**
Metrics are cheap numbers over time: good for dashboards, alerts, and spotting that something is wrong. Logs are detailed event records: good for finding the exact error. Traces follow one request across services showing time per hop: good for finding where latency comes from. Link them with a trace ID.

**Q2. What are the four golden signals?**
Latency, traffic, errors, saturation. Track latency of successful and failed requests separately, count errors including wrong-content responses and too-slow ones, and measure saturation on the most constrained resource.

**Q3. Define SLI, SLO, SLA, and error budget with an example.**
SLI: percent of HTTP requests that return non-5xx within 300 ms. SLO: 99.9 percent over 30 days. SLA: the contract, for example refunds if monthly availability falls below 99.5 percent. Error budget: 0.1 percent, about 43 minutes per 30 days, or 10,000 failed requests out of 10 million. When it is used up, we slow feature releases and fix reliability.

**Q4. Why do we use percentiles instead of the average? Why can't we average percentiles?**
The mean hides slow tail requests, and tail users are real people. Percentiles show the distribution. A percentile is a position in a sorted list, so the p99s of two servers cannot be averaged: the result depends on how many requests each served and where the slow ones are. Keep histogram buckets, sum the buckets, then compute the percentile (`histogram_quantile`), or define the SLO as a ratio of good to total events.

**Q5. How should alerting be designed?**
Page on symptoms users feel (error ratio, latency, SLO burn rate), not on causes. Use multiwindow multi-burn-rate alerts: for a 99.9 percent SLO, page at 14.4x burn over 1 hour (and 5 minutes), page at 6x over 6 hours (and 30 minutes), ticket at 1x over 3 days. Every alert is actionable and has a runbook; remove or downgrade noisy ones.

**Q6. The error budget is exhausted. What happens?**
Per the agreed error-budget policy: pause risky feature releases, focus engineering time on reliability (fix the top causes of budget burn), and allow only urgent fixes until the budget recovers. It works only if product and engineering agreed on the policy beforehand.

**Q7. Why does Loki only index labels, and what is the catch?**
Indexing only labels keeps the index small and storage cheap, with compressed chunks in object storage. The catch: queries filter log text at query time (slower on huge ranges), and you must keep labels few and low-cardinality (app, namespace, pod, level), or Loki gets slow and expensive.

**Q8. Walk me through how you run an incident and what the postmortem contains.**
Detect and triage impact and severity, declare the incident, assign an incident commander and a communicator, check recent changes, mitigate first (rollback, flag off, shift traffic), communicate on a schedule, confirm recovery on SLIs. Then a blameless postmortem: summary, impact, trigger and root causes, timeline, what went well or poorly, and owned, prioritized, verifiable action items.

## 7. Self-quiz (answers at the end)

1. For a 99.9% SLO over 30 days, how many minutes of full outage is the budget?
2. Server A p99 = 200 ms, server B p99 = 400 ms. Can you say the combined p99 is 300 ms?
3. Name the four golden signals.
4. What does burn rate 1 mean? What does burn rate 14.4 over one hour mean for the budget?
5. Why is a high-cardinality label dangerous in Prometheus?

**Answers**
1. 43.2 minutes (0.001 × 43,200).
2. No. Percentiles cannot be averaged; it depends on request counts and distributions. Merge histogram buckets and recompute.
3. Latency, traffic, errors, saturation.
4. Burn rate 1: the budget would be used up exactly at the end of the window. 14.4 for one hour uses 2 percent of the 30-day budget (14.4 × 1/720).
5. Each label combination is a separate time series, so millions of series use huge memory and slow queries.

## 8. Sources

- Google SRE book, Service Level Objectives (SLI/SLO/SLA, percentiles, error budgets): https://sre.google/sre-book/service-level-objectives/
- Google SRE book, Monitoring Distributed Systems (four golden signals, symptoms vs causes, averages hide the tail): https://sre.google/sre-book/monitoring-distributed-systems/
- Google SRE Workbook, Alerting on SLOs (burn rate table): https://sre.google/workbook/alerting-on-slos/
- Google SRE Workbook, Postmortem Culture: https://sre.google/workbook/postmortem-culture/
- Prometheus, histograms and summaries: https://prometheus.io/docs/practices/histograms/
- Grafana Loki overview: https://grafana.com/docs/loki/latest/get-started/overview/
- OpenTelemetry signals: https://opentelemetry.io/docs/concepts/signals/
- 2026 SRE interview-theme summaries (prep sites; indicators only): https://www.kore1.com/sre-interview-questions/ and https://prachub.com/resources/incident-response-interview-questions-for-sre-and-senior-engineers
- Local demos: Python scripts run on this Mac, 2026-11-15

Not verified from a source: Prometheus pull model and metric type definitions; PromQL for the error ratio; Alertmanager and exporter descriptions; LogQL examples; OTel Collector, OTLP, span, and context-propagation descriptions; RED and USE methods; Promtail status; incident roles (summary of prep sites); the severity levels and the postmortem template wording (mine); SLO table arithmetic (computed by me).
