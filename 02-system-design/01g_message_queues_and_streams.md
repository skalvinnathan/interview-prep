# 01g. Message Queues and Streams (Kafka Basics)

---

## 1. The problem a queue solves

Without a queue, services call each other directly and wait.

```
Order service --(waits)--> Email service --(waits)--> Email provider (slow!)
```

If the email service is slow or down, the order service is slow or fails. Also, if traffic suddenly goes 10 times higher, the email service falls over.

**With a queue:** the order service drops a message in a box and goes on. The email service picks messages up when it can.

**Analogy: the post office / a restaurant order rail.** The waiter pins an order slip on the rail (queue) and goes back to the guests. The cook takes slips one by one at his own speed. If many guests arrive, the slips pile up on the rail; they are not lost.

```
Producer ---> [ m5 | m4 | m3 | m2 | m1 ] ---> Consumer
              (queue holds messages)
```

- **Producer** = sends messages.
- **Consumer** = receives and processes messages.
- **Broker** = the server that stores the queue.

### Benefits

1. **Decoupling**: producer and consumer do not know each other.
2. **Buffering (load levelling)**: absorbs spikes; the consumer works at steady speed.
3. **Reliability**: if the consumer is down, messages wait.
4. **Scaling**: add more consumers to process faster.
5. **Async work**: user gets a fast answer ("we got your request"), heavy work happens later.

### Costs

- More moving parts, more to monitor.
- Work becomes **asynchronous**: the result is not immediate; you need status checks or callbacks.
- Ordering and duplicates need care.

---

## 2. Queue vs publish-subscribe vs stream

| Model | What | Example tools |
|---|---|---|
| **Queue** (work queue) | Each message goes to **one** consumer; deleted after it is processed | RabbitMQ, SQS, Celery |
| **Pub/Sub** | Each message goes to **every** subscriber | SNS, Google Pub/Sub, Redis Pub/Sub |
| **Log / stream** | Messages are appended to a durable log; many consumers read at their own position; messages stay for days | **Kafka**, Kinesis, Pulsar |

---

## 3. Delivery guarantees (very common question)

| Guarantee | Meaning | Risk |
|---|---|---|
| **At most once** | Message may be lost, never duplicated | Lost work |
| **At least once** | Never lost, **may be duplicated** (retry after a timeout) | Duplicates |
| **Exactly once** | Processed once only | Hard and costly in reality |

Practical truth to say: **"Most systems are at-least-once. So I make consumers idempotent, which gives the same result as exactly-once."** Idempotent = processing the same message twice has the same effect as once (for example, using a message id and a "processed ids" table). See `03`.

### How acknowledgement works

1. Consumer receives a message (it becomes hidden for a **visibility timeout**).
2. Consumer processes it.
3. Consumer sends **ack**. The broker deletes it.
4. If no ack in time, the broker makes it visible again -> another try. (This is why duplicates happen.)

### Dead-letter queue (DLQ)

If a message fails again and again (a "poison message"), after N tries it is moved to a **dead-letter queue** for humans to inspect. Without a DLQ, one bad message can block everything or loop forever.

### Backpressure

If consumers are slower than producers, the queue grows. Watch **queue depth** and **consumer lag**. Fix: add consumers, speed up processing, or slow down producers (reject or throttle).

---

## 4. Kafka basics

Kafka is a distributed, durable **log**.

```
Topic "orders"  (split into partitions)
 Partition 0: [0][1][2][3][4] ...
 Partition 1: [0][1][2][3]    ...
 Partition 2: [0][1][2][3][4][5] ...
                 ^offset = position in the log
```

Terms:

- **Topic**: a named stream (like a folder). Example: `orders`.
- **Partition**: a topic is split into partitions for parallelism. Each partition is an **ordered**, append-only log.
- **Offset**: the number of a message inside a partition. The consumer remembers "I have read up to offset 41".
- **Producer**: appends to a partition. If you give a **key** (for example `user_id`), the same key always goes to the same partition, so **messages of one key stay in order**.
- **Consumer group**: a team of consumers that share a topic. **Each partition is read by exactly one consumer in the group.** So the maximum useful consumers = number of partitions.
- **Different groups** each get **all** messages (so "billing" and "analytics" both read the same topic independently).
- **Replication**: each partition has copies on other brokers (a leader and followers). If a broker dies, a follower takes over.
- **Retention**: messages are kept for a time (for example 7 days) or size, **not deleted when read**. So you can **replay** (re-read from an old offset). Great for fixing bugs or building new views.

```
                    +--- Consumer group A (billing): c1 reads P0, c2 reads P1,P2
Producers -> Topic -+
                    +--- Consumer group B (analytics): its own position
```

### Ordering rules (say clearly)

- Order is guaranteed **only inside one partition**.
- Choose the partition key so related messages (same order id, same user) go to the same partition.
- More partitions = more throughput, but more overhead and no global order.

### Offsets and commits

Consumer **commits** its offset after processing. Commit before processing = may lose messages (at most once). Commit after processing = may reprocess after a crash (at least once). Usually: process first, commit after, with idempotent processing.

### Kafka vs a traditional queue

| | Kafka-style log | SQS/RabbitMQ-style queue |
|---|---|---|
| Message after read | Stays (until retention) | Deleted after ack |
| Replay | Yes | No |
| Throughput | Very high | High |
| Ordering | Per partition | Often none (or FIFO option, lower throughput) |
| Per-message retry/delay | Harder, needs extra topics | Built in (visibility timeout, DLQ, delay) |
| Best for | Event streams, logs, many readers | Task queues, jobs |

I am describing common design differences; features differ by product and version, so in an interview say "typically".

---

## 5. Common patterns

1. **Work queue**: web server drops "send email" jobs; workers send them.
2. **Fan-out**: one event, many consumers (order placed -> email, inventory, analytics).
3. **Event sourcing** (idea): store all events as the truth; the current state is built by replaying them. A ledger is a similar idea (`18`).
4. **Outbox pattern**: when a service must update its DB **and** publish an event, it writes the event into an `outbox` table in the **same DB transaction**, and a separate process publishes it. This avoids "DB updated but event lost". A very good thing to mention.
5. **Change data capture (CDC)**: stream database changes into Kafka to keep search indexes/caches in sync.
6. **Delay / retry queue**: failed messages are re-sent after a wait (backoff).

```
Service --(1 transaction)--> [orders table + outbox table]
                                        |
                                   Relay process
                                        v
                                      Kafka -> consumers
```

---

## 6. Where this appears in your work

Your provisioner runs steps in dependency order and retries failed steps; a job queue plus worker model is the same idea (`20`). Your observability stack (Loki, Prometheus) can be fed through a stream so spikes do not overload storage (`22`).

---

## 7. Interview questions

**Q: How do you avoid processing a message twice?**
A: I cannot fully avoid it with at-least-once delivery, so I make the consumer idempotent: store the message id (or use a natural unique key) and skip if seen; or make the operation naturally repeatable (`SET status = 'paid'`).

**Q: One consumer is too slow. What now?**
A: Add consumers in the group up to the partition count; add partitions if needed (careful: key-to-partition mapping changes); optimise the processing; batch.

**Q: What if the consumer keeps failing on one message?**
A: Retry a few times with backoff, then send to a dead-letter queue and alert. Do not block the partition forever.

---

## Quick check

1. Queue vs pub/sub: who gets the message?
2. Why is ordering only per partition?
3. What does at-least-once mean, and what must you do because of it?
4. What is a dead-letter queue?
5. What problem does the outbox pattern solve?
