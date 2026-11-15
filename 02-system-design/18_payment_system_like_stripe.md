# 18. Design a Payment System (like Stripe)

This file matters most for Stripe interviews. Stripe's public docs and third-party interview reports say the interview stresses API design, data modelling, consistency, and failure handling (see `00`). Read slowly.

---

## 1. The problem in plain words

A shop (the **merchant**) wants to take money from a customer's card. The merchant calls our API: "charge this customer 500 rupees". We talk to the card networks and banks (through partners called acquirers/processors), then tell the merchant "paid" or "failed". Money must **never be lost, never be charged twice, and always add up**.

**Analogy: a bank cashier with a ledger book.** Every rupee that moves is written in a book as two lines: money out of one place, money into another. Lines are never erased. If you made a mistake, you write a new correcting line. At the end of the day the book must balance to zero. The cashier also keeps a receipt number: if you hand him the same slip twice, he says "this one is already done" and gives the old receipt.

---

## 2. Requirements

**Must-have**
1. Create a payment (charge) for an amount and currency using a payment method.
2. Safe retries: a retried request must not charge twice (**idempotency keys**).
3. Payment states: created, processing, succeeded, failed, (refunded, partially refunded, disputed).
4. Refunds.
5. **Webhooks**: tell the merchant when something happens (payment succeeded, refund done).
6. A **ledger**: a double-entry record of every money movement, auditable.
7. Reconciliation with the external bank/processor reports.
8. Merchant payouts (move collected money to the merchant's bank) - brief.

**Non-functional**
- **Correctness above all**: no lost or duplicated money. Strong consistency for the money path.
- High availability for the create-payment API; durable; auditable (every change recorded).
- Security: never store raw card numbers in our normal systems (use tokenisation; card data lives in a small, strongly protected vault that meets PCI rules - mention only).
- Latency: a card authorisation normally takes a second or two because it depends on external parties.

**Out of scope**
- Fraud scoring models, card tokenisation internals, currency exchange, tax, subscriptions and invoicing (extension), disputes workflow details, 3-D Secure flows (mention).

---

## 3. The numbers (estimates)

Assume 1,000 payments per second at peak (a big platform; assumption), average 300 per second, 26M per day.

| Item | Value |
|---|---|
| Payments per day | about 26M (300/s average) |
| Writes per payment | each payment makes several DB writes: payment row, idempotency record, 2+ ledger entries, event rows = say 10 writes |
| DB writes | 1,000/s x 10 = about 10,000 writes/s at peak. A well-tuned sharded SQL cluster handles this |
| Storage | 26M/day x 10 rows x 300 bytes = about 78 GB/day = about 28 TB/year (ledger is never deleted; archive old partitions) |
| Webhooks | 2 to 3 events per payment = about 3,000 per second peak outbound HTTP calls |
| Idempotency records | 26M/day, keep 24 hours or longer = about 26M rows x 1 KB = 26 GB hot |

Meaning: volume is moderate; **correctness and failure handling** are the real work.

---

## 4. The API

Principles (Stripe-style): resources with ids; POST to create; **idempotency keys** on every POST; versioned; consistent errors; webhooks for async updates.

```
POST /v1/payment_intents
  headers: Authorization: Bearer <secret key>
           Idempotency-Key: 8f1c...         (client-generated UUID, one per intended operation)
  body: { "amount": 50000, "currency": "inr",        // integer in smallest unit (paise). NEVER floats for money
          "payment_method": "pm_123", "customer": "cus_9",
          "confirm": true, "metadata": {"order_id": "o7"} }
  reply: 200 { "id": "pi_abc", "status": "processing" | "succeeded" | "requires_action" | "failed", ... }

GET  /v1/payment_intents/{id}
POST /v1/refunds           { "payment_intent": "pi_abc", "amount": 20000 }   (+ Idempotency-Key)
POST /v1/webhook_endpoints { "url": "https://merchant.com/hooks", "events": ["payment_intent.succeeded"] }
GET  /v1/events?cursor=...     (merchant can re-fetch missed events)
```

**Idempotency in Stripe's public API (verified from their docs, https://docs.stripe.com/api/idempotent_requests):**
- The client sends an `Idempotency-Key` header with POST requests.
- For API v1, Stripe saves the status code and body of the first request made with a key (after execution starts) and returns the same result for retries with that key, even for 500 errors.
- Keys can be removed after they are at least 24 hours old.
- If the parameters differ from the original request using the same key, the API returns an error (to catch misuse).
- Keys can be up to 255 characters; random V4 UUIDs are suggested.
- GET and DELETE are idempotent by definition.
I use the same design below; say "similar to how Stripe documents it".

**Amounts:** integers in the smallest currency unit (50000 paise = 500.00 INR), plus a currency code. Floating point numbers cause rounding errors with money.

---

## 5. The data tables

**payment** (current state): `payment_id (PK)`, `merchant_id`, `amount`, `currency`, `status`, `payment_method_ref`, `processor_ref`, `created_at`, `updated_at`, `version`.

**idempotency_key**: `(merchant_id, key) UNIQUE`, `request_hash`, `status` (in_progress/completed), `response_code`, `response_body`, `payment_id`, `created_at`, `locked_until`.

**ledger_entry** (append-only, double entry):

| Column | Note |
|---|---|
| entry_id | PK |
| transaction_id | groups the lines of one movement; **sum of amounts in a transaction = 0** |
| account_id | whose account (customer clearing, merchant balance, platform fees, processor receivable...) |
| amount | positive = debit/credit by convention, integer |
| currency | |
| payment_id / refund_id | reference |
| created_at | never updated, never deleted |

**account**: `account_id`, `type`, `merchant_id`, `currency`. **balance** can be derived as the sum of entries (and cached/snapshotted for speed).

**payment_event** (state history, append-only): `(payment_id, seq, from_state, to_state, reason, ts)`.

**outbox**: `event_id`, `payload`, `published_at` - for reliable event publishing (below).

**webhook_endpoint** and **webhook_delivery**: `delivery_id`, `endpoint_id`, `event_id`, `attempt`, `next_attempt_at`, `status`, `last_response_code`.

**Double-entry example** (customer pays 500, fee 15, merchant gets 485; amounts in rupees for readability):

```
 transaction T1
   debit   processor_receivable   +500      (we will receive 500 from the bank)
   credit  merchant_balance       -485      (we owe the merchant 485)
   credit  platform_revenue       - 15      (our fee)
                                  -----
                          sum =     0
```

Ledger rules: lines are immutable; fix mistakes with new reversing entries; every transaction balances to zero; this gives a full audit trail and a way to detect bugs (if any transaction does not sum to zero, alarm).

---

## 6. Version 1 (simple)

```
 Merchant --POST /charge--> [API server] --call--> Card processor / bank
                                  |
                                  v
                             [SQL DB: payment table]
```

Problems:
1. **Timeout confusion**: we call the processor, the network times out. Did the charge happen? If we retry we may charge twice. If we do not, we may lose a sale.
2. **Crash in the middle**: after the bank charged but before we saved "succeeded" - the customer paid, our DB says nothing.
3. Merchant retries (double click) create two charges.
4. No audit trail.

---

## 7. Growing 100x, step by step

**Step 1. Idempotency keys (solves duplicate requests).**

```
 Request(key K)
   BEGIN TRANSACTION
     INSERT idempotency_key (merchant, K, request_hash, in_progress)   -- UNIQUE constraint
        if it already exists:
            if request_hash differs -> 422 error (key reuse with different body)
            if completed -> return stored response
            if in_progress -> 409 "request in progress" (or wait briefly)
   COMMIT
   ... do the work ...
   UPDATE idempotency_key SET status=completed, response=...
```

The unique constraint makes two simultaneous identical requests safe: one inserts, the other sees the conflict.

**Step 2. Make the payment a state machine.** States and allowed moves only:

```
 created -> processing -> succeeded -> (refunded / partially_refunded)
                |
                +-> failed
                +-> requires_action (e.g. customer must confirm with bank) -> processing
```

Each transition is a conditional update: `UPDATE payment SET status='succeeded' WHERE id=? AND status='processing'`. If 0 rows change, someone else already moved it; stop. This stops two workers from double-processing, and makes retries safe.

**Step 3. Safe talking to the external processor.**
- Save the payment as `processing` **before** calling out (record intent first).
- Call the processor **with our own idempotency key** (we pass the payment id as the processor's idempotency reference, if supported) so our retry does not double charge at the processor.
- Use timeouts, retries with backoff and jitter only with that key, and a circuit breaker. (`03`)
- If the answer is unknown (timeout), the state stays `processing` and a **recovery worker** later **queries the processor** for the true status by reference, then moves the state. This is called **reconciliation of unknown outcomes**. Never guess.

**Step 4. Ledger written in the same transaction as the state change.** When the payment moves to `succeeded`, in **one database transaction**: update payment status, insert the balanced ledger entries, insert the payment_event, insert the outbox row. Either all happen or none. (`01d` ACID.) Because it is a single DB transaction, we keep this part on a single shard: shard by `merchant_id` so all of a merchant's payments, ledger, and balance live together.

**Step 5. Reliable events: the outbox pattern.** Do not call "publish to Kafka" inside the DB transaction (it can fail separately). Instead write the event into the `outbox` table in the same transaction. A relay process reads the outbox and publishes to Kafka (at least once). Consumers (webhook sender, analytics, email receipts) are idempotent by event id. (`01g`)

```
 [Payment service] --(one DB tx)--> payments + ledger + outbox
                                         |
                                    Relay -> Kafka "payment_events"
                                         |-> Webhook delivery service
                                         |-> Receipts, analytics, fraud, payouts
```

**Step 6. Webhooks (telling the merchant).** The merchant's server is outside our control: it can be slow, down, or buggy. Design:
1. Event created (in outbox/Kafka) -> webhook service looks up the merchant's endpoints.
2. Send an HTTP POST with the event JSON, a unique event id, a timestamp, and a **signature** (HMAC of the body with a shared secret) so the merchant can verify it is really us and not replayed (check timestamp).
3. Merchant must reply 2xx quickly. Anything else (or timeout) = failure.
4. **Retry with exponential backoff and jitter** for many hours/days (for example up to 3 days; a design choice), then mark failed and alert the merchant (and disable a broken endpoint after long failures).
5. **At-least-once delivery**, so merchants must be **idempotent** (dedupe by event id). We document that. Order is not guaranteed; events carry the object state or a version, and merchants can re-fetch via `GET /events` or the resource.
6. Per-endpoint queues and rate limits so one slow merchant does not block others (bulkhead). Concurrency limit per endpoint.
7. Store every attempt for debugging; offer a replay button.

**Step 7. Reconciliation (the safety net).** Every day (or more often), compare our records with the processor's/bank's settlement files:
- Payments in our DB but not in their report: possibly never reached them -> investigate.
- In their report but not ours: customer charged but we lost track -> create/repair.
- Amount differences.
It is a batch job producing a diff report and automated fixes for known cases. Also check the ledger invariant (every transaction sums to zero; account balances equal the sum of entries). Reconciliation catches the bugs that all other protections missed.

**Step 8. Scale the data layer.** Shard by merchant_id (consistent hashing, many logical shards). Leader plus synchronous replica(s) in another zone for **no data loss** on failover (money data: prefer synchronous or quorum replication; accept slightly higher write latency). Archive old ledger partitions by date. Hot merchants (a huge platform): give them a dedicated shard or sub-shard by payment id range with care for balance updates (balances derived/cached asynchronously to avoid a hot row).

**Step 9. Balances without hot rows.** If every payment `UPDATE merchant_balance SET amount = amount + x` on one row, that row becomes a bottleneck. Instead: balance = sum of ledger entries (append-only inserts scale), with periodic **balance snapshots** and a cache; check available balance with snapshot + recent entries.

**Step 10. Refunds, payouts.** Refund = new payment-like object, with its own idempotency key, state machine, ledger entries (reverse lines), and webhook. Validate: total refunds <= original amount (conditional update / constraint). Payouts: a scheduled workflow (batch of merchant balances -> bank transfer file/API), also idempotent and reconciled (compare `20` for the workflow engine).

**Step 11. Security and compliance.** Raw card data only in an isolated vault; the rest of the system sees tokens. TLS everywhere, secrets in a secret manager, signed webhooks, audit logs, least-privilege access, rate limiting on API keys (`11`), fraud checks in the path (mention).

**Step 12. Multi-region.** Payments are not "eventually consistent": run the write path active in one region per merchant (home region) with a hot standby elsewhere and tested failover; reads and static data can be replicated widely.

Final picture:

```
 Merchant --> API gateway (auth, rate limit) --> Payment API (idempotency check)
                                                   |
                                                   v
                              +------- DB shard by merchant_id (leader + sync replica) -------+
                              | payments | idempotency | ledger_entries | outbox | events    |
                              +----------------------------------------------------------------+
                                   |                          |
                         Processor client             Relay -> Kafka -> Webhook service -> merchants
                      (timeouts, breaker, idem key)                  -> Receipts / Analytics / Fraud
                                   |
                  Recovery worker (unknown outcomes)      Reconciliation batch (vs bank files)
```

---

## 8. Trade-offs and why

| Choice | Why | Cost |
|---|---|---|
| SQL with transactions | Money needs ACID | Scaling needs sharding discipline |
| Shard by merchant | One transaction stays on one shard | Hot merchants; cross-merchant operations (platform transfers) need sagas |
| Ledger append-only, double entry | Audit, bug detection, no lost updates | More rows; balance needs aggregation/snapshots |
| Idempotency keys stored 24h+ | Safe retries | Storage; key discipline from clients |
| Outbox + Kafka | Atomic state + event | Relay latency (milliseconds to seconds) |
| Webhooks at-least-once | Reliable | Merchants must dedupe and handle disorder |
| Synchronous replication | No money loss on failover | Higher write latency |
| Reconciliation jobs | Catch unknown bugs and external mismatches | Operational work, delayed detection (hours) |
| Async processing for slow external calls | Resilience | Merchants must handle "processing" and wait for webhook |

---

## 9. What breaks and how to fix it

| Failure | Effect | Fix |
|---|---|---|
| Client timeout / retry | Double charge | Idempotency key + unique constraint; stored response |
| Processor timeout | Unknown outcome | Stay `processing`; query processor by reference; recovery worker; never blind retry without key |
| Crash after bank charge, before DB commit | Customer charged, we lost it | Record `processing` intent before the call; recovery worker and reconciliation find it |
| Two workers process same payment | Double transitions | Conditional state update (compare-and-set), row lock, or lease |
| Event publish fails after commit | Merchant never told | Outbox guarantees; relay retries |
| Merchant endpoint down for hours | Missed webhooks | Retries with backoff for days, replay API, `GET /events` |
| Duplicate webhook | Merchant fulfils order twice | Event id; documented merchant dedupe |
| Out-of-order webhooks | Wrong state | Include version/timestamp; merchant fetches latest state |
| DB leader fails | Writes stop | Synchronous replica promoted; idempotency makes client retries safe |
| Ledger imbalance bug | Wrong money | Invariant checks on every write (sum = 0), nightly audit, alerts |
| Hot merchant row | Slow | Ledger inserts + balance snapshots instead of single row updates |
| Replay attack on webhooks | Fake events | Signature with timestamp tolerance |
| Float rounding | Cents lost | Integers in minor units |
| Fraudulent burst | Losses | Rate limits, velocity checks, fraud service (out of scope) |

---

## 10. Questions the interviewer asks next

**Q1. How exactly do idempotency keys work and what do you store?**
A. A table with a unique key per merchant: key, request hash, state, saved response. First request inserts the row (in progress) inside a transaction, then does work, then saves the response and marks completed. A repeat with the same key returns the saved response; the same key with a different body returns an error; a concurrent repeat gets "in progress". Keys expire after about a day.

**Q2. The processor call times out. What do you do?**
A. I do not know if the charge happened. I keep the payment in `processing`, never mark it failed on a timeout, and a recovery worker asks the processor for the status using our reference. If the processor supports idempotency keys I can safely retry with the same key. Reconciliation is the final safety net.

**Q3. How do you guarantee the ledger is correct?**
A. Append-only double-entry lines, grouped by transaction, written in the same database transaction as the state change, with a check that each transaction sums to zero. Balances are derived from entries, and a nightly job re-checks invariants and compares with bank files.

**Q4. Why not publish the event directly to Kafka?**
A. The DB commit and the Kafka publish can fail separately, leaving the state changed without an event, or an event without a state. The outbox table makes the event part of the same transaction, and a relay publishes it afterwards.

**Q5. How do you design webhooks?**
A. Asynchronous delivery from events, signed payloads with timestamps, retries with exponential backoff and jitter for days, per-endpoint queues and limits, delivery logs with replay, at-least-once with merchant-side dedupe by event id, and an events API to catch up.

**Q6. How do you handle exactly-once?**
A. I do not promise it; I build at-least-once with idempotent operations at every boundary: idempotency keys on the API, conditional state transitions, unique constraints, event ids on webhooks. The effect is "exactly once".

**Q7. How do you refund safely?**
A. A refund is its own object with an idempotency key and state machine. A conditional check ensures the sum of refunds does not exceed the original amount (done inside one transaction on the same shard). It writes reversing ledger entries and emits a webhook.

**Q8. SQL or NoSQL?**
A. SQL for the money core because I need multi-row transactions and constraints. NoSQL or a log store is fine for events, webhook delivery logs and analytics.

**Q9. How do you handle multi-currency?**
A. Every amount carries a currency; ledger accounts are per currency; a conversion is two ledger transactions through an exchange account with the rate stored. No mixing currencies in a sum.

**Q10. How do you test a payment system?**
A. A sandbox with fake processors, failure injection (timeouts, duplicates, out-of-order), property tests that ledgers always balance, replaying production-like traffic, and canary releases. Stripe-style test-mode keys are an idea to mention.

**Q11. How would you scale to 10x?**
A. More logical shards by merchant, async read models for dashboards, ledger partitions by time, separate webhook cluster, and caching of static reference data. Keep the write path simple.

---

## 11. Say it out loud (6 sentences)

1. "A payment system moves money through external processors, so correctness comes first: never lose, never duplicate, and always be able to audit."
2. "Every POST carries an idempotency key stored under a unique constraint with the saved response, so client retries and double clicks are safe, similar to how Stripe documents it."
3. "A payment is a state machine updated with conditional writes, and the state change, the append-only double-entry ledger lines, and an outbox event are written in one database transaction on a shard chosen by merchant."
4. "Calls to the processor use timeouts and keyed retries; if the outcome is unknown the payment stays processing and a recovery worker and daily reconciliation against bank files find the truth."
5. "An outbox relay publishes events to Kafka, and a webhook service delivers signed, at-least-once events with exponential backoff, per-endpoint isolation, replay, and merchant-side deduplication."
6. "I use integers for amounts, synchronous replication for money data, balance snapshots instead of hot rows, and invariant checks that every ledger transaction sums to zero."
