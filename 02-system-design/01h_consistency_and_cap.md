# 01h. Consistency and the CAP Idea (in Plain Words)

---

## 1. What is consistency?

When data is stored in **more than one place** (copies, replicas, caches), the copies should say the same thing. **Consistency** is about how well they agree, and how fast.

**Analogy:** You and your brother both keep a copy of the family phone list. Mom changes Uncle's number. If she tells you but not him yet, your lists **disagree** for a while. Consistency asks: how long can that last? Is it OK?

---

## 2. Levels of consistency (from strict to relaxed)

| Level | Meaning | Daily example |
|---|---|---|
| **Strong consistency** (linearizable) | After a write is done, **every** read anywhere sees it | Bank balance. After deposit, all screens show the new amount |
| **Read-your-own-writes** | You always see your own changes (others may lag) | You post a comment and see it at once, friends see it in a second |
| **Monotonic reads** | You never see data go "back in time" | Refresh never shows an older post than before |
| **Eventual consistency** | If no new writes come, all copies **become** equal after some time | Like counts, follower counts |

Stronger = simpler for the programmer but slower and less available. Weaker = faster and more available but you must handle stale data.

---

## 3. CAP in plain words

CAP is about distributed systems (many machines connected by a network). Three letters:

- **C - Consistency**: every read gets the latest write (or an error).
- **A - Availability**: every request gets an answer (not an error), even if it may be old.
- **P - Partition tolerance**: the system keeps working even when the network between machines **breaks** (some machines cannot talk to others).

**The idea:** in real networks, partitions **will** happen (cables break, switches fail). So P is not a choice. When a partition happens you must pick:

- **CP**: refuse some requests (return an error or wait) so that data stays correct. Choose **Consistency**.
- **AP**: keep answering from whatever copy you have, even if it might be stale, and fix differences later. Choose **Availability**.

**Analogy: two bank branches lose the phone line between them.**
- CP bank: "Sorry, branch 2 cannot withdraw until the line is back." (Money stays correct, service stops.)
- AP bank: "Go ahead and withdraw, we will sort it out later." (Service continues, but you might overdraw twice in two branches.)

```
        Network partition happens
              |
   +----------+-----------+
   |                      |
 choose C               choose A
 (reject/wait)          (answer, maybe stale)
 e.g. payments,         e.g. social feed,
 inventory, ledger      likes, product views
```

### Important notes (so you do not say wrong things)

1. CAP applies **during a partition**. When the network is fine, you can have both C and A.
2. It is not "pick 2 of 3 forever". It is "when partition happens, C or A".
3. "Consistency" in CAP is different from "C" in ACID. (ACID's C = business rules stay valid; CAP's C = all nodes see the same data.)
4. Real systems are not purely CP or AP; many let you tune per request (for example quorum settings).

### PACELC (one extra line, optional)

Even **without** a partition there is a trade-off: **L**atency vs **C**onsistency. Waiting for all copies to confirm (strong consistency) is slower. So: "If Partition: A or C; Else: L or C." You can mention it to show depth, but do not go on about it.

---

## 4. How systems get consistency or availability

- **Single leader + sync replication** -> strong consistency, lower availability, higher write latency.
- **Single leader + async replication** -> fast, but followers lag (eventual consistency for reads).
- **Quorum reads/writes (W + R > N)** -> tunable (see `01f`).
- **Consensus (Raft/Paxos)** -> a group of nodes agree on each change, a majority must be alive. Used for configuration, leader election, metadata (for example etcd in Kubernetes; you use it daily). CP behaviour: if the majority is lost, writes stop.
- **Conflict resolution for AP systems**: last-write-wins (simple, may lose data), version vectors, or CRDTs (special data types that merge automatically; just know the name).

---

## 5. How to choose in an interview (a simple recipe)

Ask: **"What is the cost of showing old data?"**

| Data | Cost of stale | Choice |
|---|---|---|
| Account balance, ledger entries | Money loss, legal trouble | Strong consistency (CP) |
| Inventory of the last item | Overselling | Strong for the final decrement; cache can be eventual |
| Shopping cart | Small annoyance | Eventual is OK |
| Social feed, like counts | Almost none | Eventual (AP) |
| Permissions / access revoke | Security risk | Short staleness window and fast invalidation; for critical checks, strong |
| Search results, recommendations | None | Eventual |
| Metrics dashboards | None for seconds | Eventual |

A strong sentence: **"I use strong consistency for the money path and eventual consistency for the read paths that users can tolerate being a few seconds old."**

Your access-control service is a good example: when an admin removes a role, how fast must all services stop honouring it? A cached token or permission set may keep allowing access until it expires. So you choose a short token life or an invalidation message - that is a consistency decision.

---

## 6. Idempotency and consistency together

Retries (needed because networks fail) cause duplicates. Eventual consistency causes stale reads. Together they are why you design **idempotent writes** and **tolerant reads**. See `03`.

---

## 7. Quick check

1. In plain words, what is a network partition?
2. During a partition, what does a CP system do? An AP system?
3. Is the "C" in CAP the same as the "C" in ACID?
4. Give one example each of data that needs strong and eventual consistency.
5. What does W + R > N give you?
