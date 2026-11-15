# 19. Design an Order Management System (like Amazon: inventory, orders, delivery)

---

## 1. The problem in plain words

A customer picks items, pays, and waits for a parcel. Behind the scenes: check that items are in stock, **reserve** them, take payment, tell the warehouse to pack, hand over to a courier, track the parcel, and handle cancellations and returns. Many separate services must cooperate, and no single database covers all of them.

**Analogy: a restaurant with a ticket and several stations.** A waiter writes one order ticket. The kitchen station, the drinks station and the dessert station each do their part. If the drinks station runs out of lemons, the waiter must tell the guest and perhaps cancel only that item. The ticket shows what is done and what is pending. Nobody can promise the last cake to two tables at once.

---

## 2. Requirements

**Must-have**
1. Browse items with live stock status (available / out of stock).
2. Place an order (several items, one address, one payment).
3. **Inventory reservation**: never sell more than we have (no overselling).
4. Payment integration (use the payment system from `18` as a black box: authorise / capture / refund).
5. Order lifecycle with states: created, payment pending, confirmed, packed, shipped, delivered, cancelled, returned.
6. Fulfilment and delivery tracking (warehouse, courier updates).
7. Cancel and return flows.
8. Order history and status for the customer.

**Non-functional**
- **No overselling** and **no lost orders**: strong correctness on stock and order state.
- Handles flash-sale spikes (millions of users wanting few items).
- High availability for browsing and ordering; eventual consistency is OK for display data (search, recommendations).
- Auditable order history.

**Out of scope**
- Product catalog search and recommendations, pricing/promotions engine details, tax, seller onboarding, warehouse robotics and routing, last-mile route optimisation, fraud scoring.

---

## 3. The numbers (estimates)

Assume 100M daily active users browsing, 2M orders per day on a normal day, 10x on a sale day (20M/day), and a flash sale spike of 100,000 order attempts per second for a few minutes on a handful of products. Average 3 items per order.

| Item | Value |
|---|---|
| Orders per second (normal) | 2M / 86,400 = about 23/s average, about 70/s peak |
| Orders per second (sale day) | 20M / 86,400 = about 230/s average; spikes of thousands per second |
| Flash sale spike | up to 100,000 attempts per second on a few hot stock rows (estimate for stress) |
| Order storage | 2M/day x 3 items x 500 bytes = 3 GB/day = about 1.1 TB/year (small) |
| Inventory records | 100M SKUs x 200 B x (warehouses) = tens of GB |
| Browse reads | 100M DAU x 20 page views = 2B/day = 23,000/s average, much higher peak (cache and CDN heavy) |

Meaning: orders per second are modest; the dangerous part is the **hot stock row** in a flash sale, and the **multi-service consistency** of an order.

---

## 4. The API

```
POST /v1/orders
  headers: Idempotency-Key: <uuid>      (a double click must not make two orders)
  body: { "cart_id": "c1",
          "items": [ {"sku":"A1","qty":2}, {"sku":"B7","qty":1} ],
          "address_id": "ad9", "payment_method": "pm_1" }
  reply: 202 { "order_id": "o123", "status": "pending" }    (accepted; process asynchronously)
         409 if an item is out of stock

GET  /v1/orders/{id}                 status, items, tracking
GET  /v1/orders?cursor=...           history
POST /v1/orders/{id}/cancel          (idempotent; allowed only in certain states)
POST /v1/orders/{id}/returns         { "items": [...], "reason": "damaged" }
GET  /v1/items/{sku}/availability    cached, approximate for browsing

Internal / partner:
POST /internal/inventory/reserve     { order_id, lines: [...] , ttl_s }
POST /internal/inventory/release     { order_id }
POST /internal/shipments/{id}/events (from courier: picked up, in transit, delivered)
```

---

## 5. The data tables

**Order service DB** (SQL, sharded by `order_id` or `customer_id`):

- **orders**: `order_id (PK)`, `customer_id`, `status`, `total`, `currency`, `address_snapshot`, `payment_id`, `idempotency_key (unique)`, `created_at`, `version`.
- **order_items**: `(order_id, line_no)`, `sku`, `qty`, `unit_price`, `status`.
- **order_events**: `(order_id, seq)`, `type`, `data`, `ts` (append-only history).
- **outbox**: events to publish.

**Inventory service DB** (SQL or strongly consistent store):

- **stock**: `(sku, warehouse_id)` PK, `on_hand`, `reserved`, `version`. **Available = on_hand - reserved.**
- **reservation**: `(reservation_id)`, `order_id`, `sku`, `warehouse_id`, `qty`, `status` (held / confirmed / released), `expires_at`.

**Fulfilment / shipment**: `shipment_id`, `order_id`, `warehouse_id`, `carrier`, `tracking_no`, `status`, `events`.

**Catalog** (separate): products, prices, descriptions, served by cache/search (eventually consistent).

Each service owns its data. No other service reads its tables directly (they use APIs or events).

---

## 6. Version 1 (simple)

One application, one database, one transaction:

```
 POST /orders  ->  BEGIN
                     check stock; decrement stock;
                     insert order; charge card (call);
                   COMMIT
```

Works at small scale: a DB transaction guarantees all-or-nothing. Problems at scale: one DB cannot hold everything; the card call inside a transaction holds locks for seconds; when we split into services (catalog, inventory, orders, payment, shipping) a single transaction no longer spans them.

---

## 7. Growing 100x, step by step

**Step 1. Split into services owning their data.** Catalog, Cart, Order, Inventory, Payment (`18`), Fulfilment, Shipping, Notification (`14`). Browse path (catalog, cart) is read-heavy and cacheable; order path is write-critical.

**Step 2. The order is a Saga (a chain of local transactions with undo steps).** No distributed transaction. The **Order service orchestrates** (or services react to events):

```
 1. Order service: create order (status=PENDING)                      -- local tx
 2. Inventory: RESERVE stock for each line (hold, expires in 15 min)  -- local tx
        fail -> mark order FAILED (out of stock), stop
 3. Payment: authorise/charge                                          -- external
        fail -> RELEASE reservation; order FAILED  (compensation)
 4. Order service: CONFIRMED; Inventory: confirm reservation (stock decremented for real)
 5. Fulfilment: create pick-and-pack task -> PACKED
 6. Shipping: hand to courier -> SHIPPED -> DELIVERED (events)
 Any step fails -> run compensations in reverse (refund, release stock, notify customer)
```

```
 [Order] -> Reserve -> [Inventory]
    |                     
    +----> Charge ----> [Payment]
    |        (fail: Release reservation)
    +----> Create fulfilment -> [Warehouse] -> [Shipping]
```

This is the same idea as your provisioner: ordered steps, each can fail and be retried or undone, state is persisted so a crash resumes where it stopped. Say that sentence in the interview (it is true in spirit; keep the details of your platform generic).

**Step 3. Orchestration vs choreography.**
- **Orchestration**: a central orchestrator (the order workflow) tells each service what to do and tracks state. Easier to understand and debug; the orchestrator is a critical component (see `20`).
- **Choreography**: services react to each other's events (`StockReserved` -> payment starts). No central brain, but flows are hard to see.
I choose **orchestration** for the order flow because it is long-running with compensations.

**Step 4. Idempotency everywhere.** Each step has an idempotency key (order_id + step). Reserve called twice reserves once. Charge called twice charges once. Events are processed with dedupe by event id. Order creation uses the client Idempotency-Key. (`03`)

**Step 5. Avoid overselling: the inventory design.** The classic problem: two buyers, one item.

- **Atomic conditional update (simple and correct):**
  `UPDATE stock SET reserved = reserved + :q WHERE sku=:s AND warehouse=:w AND on_hand - reserved >= :q`
  Check rows affected: 1 = reserved, 0 = not enough. The database serialises concurrent updates on the same row, so overselling is impossible.
- **Reservation with expiry:** the hold lasts, say, 15 minutes; a background job releases expired holds (customer abandoned checkout or payment never completed).
- **Cart does not reserve**; reserve at checkout (or at "place order") to avoid people hoarding.

**Step 6. Flash-sale hot row.** 100,000 requests per second on one stock row would melt a database (row lock contention). Options:
1. **Split the counter**: instead of one row with 10,000 units, make 100 rows ("slots") with 100 units each; pick a slot at random (or by user hash); if a slot is empty try another. Contention drops 100x. (Total is the sum of slots.)
2. **Pre-filter in memory**: put the stock count in Redis (atomic `DECR`); only requests that win a unit continue to the DB. The DB remains the source of truth; reconcile on completion. Rejected requests return "sold out" in microseconds.
3. **Queue the requests**: put orders in a queue (a virtual waiting room); process at a rate the DB can handle. Users see "you are in line". Fair and stable.
4. **Rate limit and bot protection** (`11`).
Say: "I use Redis for fast rejection, a queue to smooth spikes, and the DB conditional update as the final truth."

**Step 7. Multiple warehouses.** Choose which warehouse fulfils each line (nearest to the address with stock; may split a shipment). The reservation records the warehouse. A small allocation service picks; inventory is sharded by SKU (hot SKUs get the slot trick).

**Step 8. Order state machine.**

```
 PENDING -> CONFIRMED -> PACKED -> SHIPPED -> DELIVERED -> (RETURN_REQUESTED -> RETURNED -> REFUNDED)
    |           |
    +-> FAILED  +-> CANCELLED (allowed before SHIPPED; triggers release + refund)
```

Transitions are conditional updates with version numbers, and every change appends an `order_event`. Cancellation after shipping is not allowed; it becomes a return.

**Step 9. Events and read models.** Services publish events (outbox -> Kafka: `OrderCreated`, `StockReserved`, `PaymentSucceeded`, `Shipped`...). Other consumers: notifications, analytics, search of "my orders" (a read-optimised view built from events, CQRS style), customer support tools. (`01g`)

**Step 10. Delivery tracking.** Carriers send events through webhooks or we poll their APIs (with rate limits and retries). A tracking consumer updates shipment status; the customer sees it in the order page; a notification goes out at key milestones. Store raw carrier events (append-only) and derive status.

**Step 11. Scale the stores.** Orders sharded by customer_id (so "my orders" is one shard), inventory by SKU, caches for catalog and availability (approximate), CDN for images, read replicas for history. (`01f`)

**Step 12. Multi-region.** Customer-facing browse is replicated and served locally; stock truth for a warehouse lives with the region of that warehouse; orders are homed by customer region. Cross-region needs async events and careful reconciliation.

Final picture:

```
 Client -> CDN/LB -> API gateway
                       |-> Catalog (cache, search)   (eventual)
                       |-> Cart (Redis/DB)
                       |-> Order service + Saga orchestrator  --outbox--> Kafka
                              |        |         |                         |
                              v        v         v                         v
                         Inventory   Payment   Fulfilment -> Shipping   Notifications, Analytics,
                       (stock, reservations)     (WMS)        (carrier events)   Order-history read model
 Flash sale: Redis counter + waiting-room queue in front of Inventory
```

---

## 8. Trade-offs and why

| Choice | Why | Cost |
|---|---|---|
| Saga instead of distributed transaction | Works across services, no global locks | Temporary inconsistency; compensation logic |
| Orchestration | Clear flow, easy debug | Orchestrator must be reliable and scalable |
| Reserve with expiry | No overselling, no permanent holds | Background cleanup; user may lose items if slow |
| Conditional UPDATE for stock | Simple, correct | Hot row limits throughput (fix with slots/queue) |
| Redis pre-check | Absorbs spikes | Two sources to reconcile |
| Eventual consistency for browsing | Fast and cheap | "In stock" may be wrong; final check at checkout |
| 202 Accepted + async | Handles spikes, retries | Customer waits for confirmation |
| Event-driven read models | Fast order history | Slight lag |

---

## 9. What breaks and how to fix it

| Failure | Effect | Fix |
|---|---|---|
| Payment succeeds, order service crashes | Paid but no confirmation | Persisted saga state; workflow resumes; recovery job re-checks pending orders against payment status |
| Reserve succeeded, payment failed | Stock stuck | Compensation releases; expiry job as safety net |
| Duplicate order (double click, retry) | Two orders | Idempotency key unique on orders |
| Overselling | Angry customers | Atomic conditional update; reconciliation of stock counts with physical counts |
| Stock drift (damaged, lost) | Wrong availability | Periodic cycle counts; adjustments through audited stock events |
| Flash-sale hot row | DB lock storms | Slots, Redis pre-check, waiting room |
| Event lost between services | Stuck order | Outbox, retries, DLQ, "stuck order" monitor that alerts when an order stays in a state too long |
| Compensation fails (refund call fails) | Money owed | Retry with backoff; DLQ and manual work queue; alerts |
| Carrier webhook missing | No tracking update | Poll fallback; timeouts that flag orders |
| Partial fulfilment (one item missing) | Split orders | Per-line status; partial shipment/refund |
| Warehouse region down | Cannot fulfil | Reallocate to another warehouse; release/re-reserve |

---

## 10. Questions the interviewer asks next

**Q1. How do you prevent two people buying the last item?**
A. One atomic conditional update on the stock row (`reserved + q <= on_hand`); the database serialises it. Only one succeeds; the other gets "out of stock". The reservation has an expiry.

**Q2. Why a saga and not a distributed transaction (2PC)?**
A. 2PC needs all services to lock resources until the coordinator decides, which is slow, fragile and does not work with external systems like payment gateways. A saga uses local transactions plus compensations, which scale and tolerate failure, at the cost of temporary inconsistency.

**Q3. What if the compensation itself fails?**
A. It is retried with backoff; if it keeps failing it goes to a dead-letter queue and a human work queue with alerts. All steps are idempotent so retries are safe.

**Q4. How do you handle a flash sale?**
A. Rate limit and bot filtering at the edge, a waiting room queue, an in-memory counter to reject quickly after sold out, sharded stock slots to cut row contention, and the DB conditional update as the final authority. Autoscale stateless services in advance.

**Q5. When do you reserve stock: add-to-cart or checkout?**
A. At checkout (order placement). Reserving at add-to-cart lets people block stock without buying. Show approximate availability in the cart and verify at checkout.

**Q6. How do you keep search results and stock display consistent?**
A. They are eventually consistent: stock changes publish events that update a cache/search index. The checkout step revalidates against inventory truth.

**Q7. How does order history load fast?**
A. Orders are sharded by customer id, so one query hits one shard, with an index on (customer_id, created_at) and a cache for recent orders; or a read model built from events.

**Q8. How do you choose the warehouse?**
A. An allocation service scores warehouses by stock, distance to the address, shipping speed and cost; it can split a multi-item order. The decision is saved with the reservation.

**Q9. How do you do returns?**
A. A return is another small saga: create return request, authorise, courier pickup, receive and inspect at warehouse, restock or discard (inventory event), refund through payment (idempotent), notify customer.

**Q10. How do you monitor?**
A. Orders per state and age (stuck-order alerts), reservation expiry counts, payment success rate, stock mismatch reports, queue depths and lag, p99 for place-order, SLO such as 99.9 percent of orders confirmed or failed definitively within 1 minute (example).

---

## 11. Say it out loud (6 sentences)

1. "An order system coordinates inventory, payment and delivery across separate services, so I use a saga with compensations, not one big transaction."
2. "Order volume is modest, about 70 per second at peak on a normal day, but a flash sale creates a hot stock row, which is the main risk."
3. "I reserve stock at checkout with an atomic conditional update and an expiry time, so we can never oversell, and I release the hold if payment fails."
4. "For flash sales I add a rate limit, a waiting-room queue, a Redis counter for fast rejection and split stock slots, while the database stays the source of truth."
5. "An orchestrator drives the steps reserve, pay, confirm, pack, ship with idempotency keys and persisted state, and an outbox publishes events for notifications, tracking and read models."
6. "Stuck-order monitors, retries with a dead-letter queue, and reconciliation of stock and payments catch whatever slips through."
