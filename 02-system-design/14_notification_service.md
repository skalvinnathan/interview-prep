# 14. Design a Notification Service

---

## 1. The problem in plain words

Many different systems (orders, payments, chat, marketing) need to tell users something: a push notification on the phone, an SMS, an email, an in-app message. Instead of each team writing its own code for each channel, we build **one service**: other systems say "tell user 42 that order 7 shipped" and the notification service handles **how, when, and how many times**.

**Analogy: a company post room.** Every department hands letters to the post room. The post room knows each person's preferred way (email, SMS, courier), prints the right template, sends it, retries if the courier fails, and does not send the same letter twice or ten letters in a minute.

---

## 2. Requirements

**Must-have**
1. Channels: mobile push (APNs for iOS, FCM for Android), SMS, email, in-app.
2. Other services call an API (or publish an event) to send a notification.
3. **Templates** with variables and languages ("Hi {name}, your order {id} shipped").
4. **User preferences**: opt out per channel or type; quiet hours.
5. **Delivery guarantee**: at least once, with retries; try not to duplicate.
6. **Scheduling** (send later) and **bulk** campaigns (send to 10 million users).
7. Delivery status tracking (sent, delivered, failed).

**Non-functional**
- High availability; notifications may be delayed by seconds but critical ones (one-time passwords) should be near-instant.
- Scale to millions per hour with huge spikes (a marketing blast, a flash sale).
- Do not overwhelm users or providers (rate limits).

**Out of scope**
- Building our own SMS/email delivery network (we use providers like Twilio-type, SES-type, APNs, FCM), rich analytics (open rates), A/B testing.

---

## 3. The numbers (estimates)

Assume 50M users; average 3 notifications per user per day (mix of channels); a campaign can send 10M in one hour; OTP messages need under 5 seconds.

| Item | Value |
|---|---|
| Normal volume | 50M x 3 = 150M per day = about 1,700 per second average |
| Peak (x5 assumption for bursts) | about 8,500 per second |
| Campaign | 10M in 1 hour = about 2,800 per second extra |
| Storage of notification log | 150M/day x 300 bytes = 45 GB/day = about 16 TB/year (keep 30 to 90 days hot, archive the rest) |
| Preferences | 50M users x 1 KB = 50 GB (cacheable) |
| Device tokens | 50M users x 2 devices x 200 bytes = 20 GB |

Meaning: moderate throughput, spiky; the hard parts are reliability, third-party limits, priorities and duplicates, not raw size.

---

## 4. The API

```
POST /v1/notifications
  headers: Idempotency-Key: <uuid>
  body: {
     "user_id": "u42",
     "type": "order_shipped",           // maps to template + default channels + priority
     "channels": ["push","email"],      // optional override
     "data": { "order_id": "o7", "name": "Asha" },
     "priority": "normal",              // critical | normal | bulk
     "send_at": "2026-11-20T09:00:00Z"  // optional
  }
  reply: 202 Accepted { "notification_id": "n1001" }     (accepted, will be sent async)

POST /v1/campaigns        { "segment_id": "...", "template": "...", "send_at": ... }

GET  /v1/notifications/{id}               status
PUT  /v1/users/{id}/preferences           { "email": {"marketing": false}, "quiet_hours": ... }
POST /v1/devices                          register a device push token
```

Note the **202 Accepted**: we promise to try, not that it is delivered yet. The same idempotency idea from `03`: a retry with the same key must not send twice.

---

## 5. The data tables

**notification** (log): `notification_id (PK)`, `user_id`, `type`, `channel`, `status` (queued/sent/delivered/failed), `attempts`, `provider_message_id`, `idempotency_key` (unique), `created_at`, `updated_at`. (Wide-column or sharded SQL, partition by user_id or by day.)

**template**: `(type, channel, language) PK`, `subject`, `body_template`, `version`.

**user_preferences**: `user_id (PK)`, channel opt-ins per category, `quiet_hours`, `timezone`, `locale`. (Read-heavy; cached.)

**device_token**: `(user_id, device_id) PK`, `platform`, `token`, `last_seen`. Invalid tokens (provider says "unregistered") are deleted.

**campaign**: `campaign_id`, `segment`, `template`, `schedule`, `state`, `progress cursor`.

---

## 6. Version 1 (simple)

```
 Order service --HTTP--> [Notification service] --> send email directly (SMTP/provider API)
                                |
                                +--> DB (log)
```

Problems: the order service waits for the email provider (slow); if the provider is down, the order call fails; no retries; no preferences; a burst kills it.

---

## 7. Growing 100x, step by step

**Step 1. Accept fast, send later (queue).** The API only validates, checks idempotency, saves a record, and puts a message on a queue, then returns 202. Workers send. (`01g`)

```
 Producers --> [API / ingest] --> Queue --> [Workers] --> Providers
```

**Step 2. One queue per channel and per priority.** Separate queues: `push-critical`, `push-normal`, `sms-critical`, `email-bulk`... Why: a marketing blast (bulk) must never delay a one-time password (critical). Critical queues have reserved workers.

```
 Ingest --> Router (prefs, templates) --> [push-critical][push-normal][sms][email][email-bulk]
                                                 |           |         |     |        |
                                              workers     workers   workers ...   (each pool scales alone)
```

**Step 3. Pipeline stages.** (1) Validate and dedupe. (2) Look up user preferences and quiet hours; drop or delay. (3) Render the template for the user's language. (4) Pick channel(s). (5) Send through a provider adapter. (6) Record status. Keep stages as separate consumers so each can scale and fail alone.

**Step 4. Provider adapters with retries and fallback.** Each channel has an adapter. Retries with exponential backoff and jitter on 5xx/timeouts; do not retry permanent errors (invalid phone). After max attempts, move to a **dead-letter queue** and alert. For SMS, keep two providers and **fail over** if the first has a high error rate (circuit breaker). (`03`)

**Step 5. Rate limiting both ways.** (a) Outbound to providers: APNs/FCM/SMS providers have their own limits (and cost money); throttle workers with a token bucket. (b) Per user: no more than N marketing messages a day (`11`).

**Step 6. Idempotency and deduplication.** Idempotency key from the caller is unique-constrained in the notification table; a retry returns the existing id. Workers use "claim" semantics: set status `queued -> sending` atomically so two workers do not send the same one. Providers can still deliver twice if our ack is lost: accept rare duplicates (at-least-once) and use provider-side dedup ids when offered.

**Step 7. Scheduling and bulk campaigns.** Scheduled messages go in a delay store (a table indexed by `send_at`, polled by a scheduler, or a delay queue). Campaigns: a campaign job reads the segment in **batches** (cursor), writes batches of notifications into the bulk queue at a controlled rate, and stores progress so it can resume after a crash. (Compare with the job scheduler in `20`.)

**Step 8. Shard and scale storage.** Notification log partitioned by user_id (or day) with TTL; preferences cached in Redis with write-through updates; device tokens cached.

**Step 9. Feedback loop.** Providers send **webhooks/callbacks** (delivered, bounced, unsubscribed, invalid token). A callback consumer updates status, removes dead tokens, and suppresses bounced emails. (Webhook design details in `18`.)

**Step 10. Multi-region and observability.** Deploy ingest in several regions; queues per region; keep a single preference source of truth (replicated). Metrics: queue depth and age per priority, send success rate per provider, end-to-end latency (p99 for critical), DLQ size. SLO example: 99 percent of critical notifications handed to a provider within 5 seconds.

Final picture:

```
 Services / Events / Campaign scheduler
              |
              v
        [Ingest API] -- idempotency check --> Notification DB
              |
              v
          [Router/Enricher] <-- Preferences cache, Templates, Device tokens
              |
   +----------+-----------+------------+-------------+
   v          v           v            v             v
 push-crit  push-norm   sms-crit   email-norm   email-bulk       (queues)
   |          |           |            |             |
 workers    workers     workers      workers       workers  --> adapters --> APNs/FCM/SMS/Email providers
   |  retry+backoff, breaker, rate limit, provider failover
   v
 DLQ + alerts          Provider callbacks --> Status updater --> DB
```

---

## 8. Trade-offs and why

| Choice | Why | Cost |
|---|---|---|
| Async (202 + queue) | Callers are not blocked; spikes buffered | Not instant; need status API |
| Separate priority queues | Protect critical messages | More queues/workers to run |
| At-least-once + idempotency | Never lose; avoid most duplicates | Rare duplicates possible |
| Provider failover | Higher delivery rate | Cost, different behaviours, number reputation |
| Cached preferences | Fast, avoid DB load | Short staleness: a user who just opted out may get one more message (use short TTL + invalidate on change; for legal opt-outs check the DB) |
| Store log with TTL | Cost control | Old history archived |

---

## 9. What breaks and how to fix it

| Failure | Effect | Fix |
|---|---|---|
| Provider down or slow | Messages pile up | Retries with backoff; circuit breaker; failover provider; queue buffers |
| Campaign floods the system | Delays for everyone | Separate bulk queues, rate-limited release, separate worker pool |
| Duplicate messages | Annoyed users | Idempotency key; claim before send; dedup window per (user, type, entity) |
| Worker crashes mid-send | Unknown if sent | At-least-once: message returns to queue; accept possible duplicate; use provider dedup id |
| Poison message | Worker loop | Max attempts, then DLQ |
| Wrong template or bad data | Mass bad sends | Template validation, staged rollout, kill switch per campaign |
| Time zones | Night-time marketing | Per-user timezone, quiet hours, scheduler respects them |
| Invalid device tokens pile up | Wasted calls | Delete tokens on provider "unregistered" responses |
| Preference DB down | Cannot check opt-outs | Cache fallback; **fail closed** for marketing (do not send), **fail open** for critical alerts |
| Thundering retry after outage | Provider overloaded again | Jitter and rate limit on release |

---

## 10. Questions the interviewer asks next

**Q1. How do you make sure a notification is not sent twice?**
A. Caller supplies an idempotency key with a unique constraint. Workers claim a notification atomically before sending. The queue is at-least-once, so a crash after sending can cause a duplicate; I reduce this with provider-level message ids and accept the small remainder, because losing an OTP is worse than sending it twice.

**Q2. How do you prioritise?**
A. Priority queues with separate worker pools and separate rate limits. Critical traffic has its own capacity that bulk traffic cannot use.

**Q3. How do you send 10 million emails for a campaign?**
A. A campaign job pages through the segment, enqueues in batches into the bulk queue at a controlled rate, stores a cursor for resume, and workers send at the provider's allowed rate. It takes hours, which is acceptable.

**Q4. How do you handle user preferences and unsubscribes?**
A. A preferences service is the source of truth; ingest and workers check it (with a cache). Unsubscribe links and provider webhooks update it. Legal opt-outs are checked against the database right before sending.

**Q5. How do you track delivered and read?**
A. Providers call our webhook with status. We store provider message ids and update status. Push "delivered" is best effort; email open tracking uses pixels (privacy issues), so treat as approximate.

**Q6. What if APNs or FCM rate-limits us?**
A. Respect their responses (back off), spread sending over time, use HTTP/2 connection reuse, and queue the rest.

**Q7. How do you support multiple languages?**
A. Templates are keyed by (type, channel, language) with a default fallback; the user's locale is in preferences.

**Q8. Synchronous send for OTP?**
A. Critical path: dedicated queue and workers, tight timeout and provider failover; the API can return 202 and the app shows "code sent". For extra safety allow the caller to request a synchronous-ish wait up to a short deadline.

---

## 11. Say it out loud (6 sentences)

1. "A notification service lets other systems send push, SMS, email and in-app messages through one API, while it handles templates, preferences, retries and rate limits."
2. "Volume is moderate, about 1,700 per second average with spikes to roughly 8,500, so the hard parts are reliability, priority and third-party limits."
3. "The API validates, checks an idempotency key, stores the request and returns 202, then a queue-based pipeline enriches, renders and sends it."
4. "I use separate queues and worker pools per channel and priority so a marketing blast can never delay a one-time password."
5. "Workers retry with exponential backoff and jitter, use circuit breakers and a fallback provider, and send poison messages to a dead-letter queue."
6. "Provider webhooks update delivery status and remove invalid tokens, delivery is at-least-once with idempotency to avoid most duplicates, and preferences decide what is allowed."
