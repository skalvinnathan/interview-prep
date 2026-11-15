# 01f. Sharding and Replication

Two ways to spread a database over many machines. They solve **different** problems. Do not mix them up.

| | Replication | Sharding (partitioning) |
|---|---|---|
| What | Many **copies** of the **same** data | The data is **split**, each machine holds a **part** |
| Solves | Availability, read scale | Storage size, write scale |
| Analogy | Photocopies of one book in many libraries | One encyclopedia split into volumes A-F, G-M, N-Z |

---

## Part A. Replication

### Why

1. **Survive failure**: if one machine dies, a copy remains.
2. **Read scale**: spread reads over many copies.
3. **Latency**: place a copy near users in another region.

### Leader-follower (primary-replica) - the most common

- One **leader** accepts all writes.
- **Followers** copy the leader's changes and serve reads.

```
         writes
 App ---------------> [ Leader ]
                         | replicates (log)
              +----------+----------+
              v                     v
          [Follower 1]          [Follower 2]  <--- reads
```

### Sync vs async replication

| Type | How | Pros | Cons |
|---|---|---|---|
| **Synchronous** | Leader waits for follower to confirm before saying "done" | No data loss on leader crash | Slower; if follower is down, writes block |
| **Asynchronous** | Leader says "done" at once, followers catch up later | Fast | **Replication lag**: followers can be seconds behind; if leader dies, last writes may be lost |
| **Semi-sync** | Wait for one follower only | Balance | |

### Replication lag: a problem you must know

You update your profile (write goes to leader), then reload the page (read goes to a follower that is still behind) and see the OLD profile. Fixes:

- **Read-your-own-writes**: after a user writes, read their data from the leader for a few seconds.
- Route critical reads to the leader.
- Use sticky reads per user.

### Failover

When the leader dies, a follower is **promoted** to leader. Tricky points: detecting that the leader is really dead (not just slow), choosing the follower with the newest data, making sure the old leader does not come back and think it is still leader ("split brain"). Use a consensus system or managed service for this. (Name: Raft or Paxos are the consensus algorithms - just know they exist for electing a leader safely.)

### Other models (just names)

- **Multi-leader**: several leaders accept writes (for multi-region). Conflicts must be resolved. Complex.
- **Leaderless** (Cassandra/Dynamo style): client writes to several nodes; uses **quorums**. See below.

### Quorum (simple)

With N copies, write to W of them and read from R of them. If **W + R > N**, a read always sees at least one fresh copy. Example N=3, W=2, R=2. Tune W and R for speed vs safety.

---

## Part B. Sharding (partitioning)

### Why

One machine has limits: disk size, memory, write speed. When data is too big or writes too many, you **split** the data across machines. Each part is a **shard**.

### Choosing the shard key (the most important decision)

The **shard key** decides which shard a row goes to. A good key:

1. **Spreads data and load evenly** (no hot shard).
2. **Matches your main query**, so a query goes to one shard, not all.

Example: user data sharded by `user_id`. "Get orders of user 5" goes to one shard. Good.
Bad: shard by `country`. India has far more users than Iceland, so one shard is overloaded (**hot shard**). Shard by `created_date`: all today's writes hit one shard (**hot spot**).

### Strategies

| Strategy | How | Pros | Cons |
|---|---|---|---|
| **Range** | A-F on shard 1, G-M on shard 2 | Easy range queries | Hot spots (everyone with names starting 'S') |
| **Hash** | `shard = hash(key) mod N` | Even spread | Changing N moves almost all keys; range queries are hard |
| **Consistent hashing** | Servers and keys on a ring; key goes to next server clockwise | Adding/removing a server moves only about 1/N of keys | Slightly more complex; use virtual nodes for even spread |
| **Directory / lookup** | A small service says which shard holds which key | Flexible, can move one key | Lookup service is a new bottleneck/single point of failure |

### Consistent hashing in a picture

```
            Server A
         .-----*-----.
       *               *  Server B
   key1 .             .
       *               *
         '-----*-----'
            Server C

A key goes clockwise to the first server it meets.
Add a server D: only the keys between D and its neighbour move.
Virtual nodes: each server appears at many points, so load is even.
```

### Problems sharding creates

1. **Cross-shard queries**: JOIN or count across all shards is slow/complex. Avoid by good key choice; or keep a separate search/analytics store.
2. **Cross-shard transactions**: hard. Use sagas or design so one transaction stays in one shard.
3. **Resharding**: moving data when you add shards. Plan it: use many small logical shards (for example 1,024) mapped to few machines, so adding machines means moving whole logical shards, not rehashing.
4. **Hot shards / celebrity problem**: one key with huge load. Split that key, cache it, or give it its own shard.
5. **Unique ids across shards**: auto-increment no longer works. Use UUIDs or a Snowflake-style id (timestamp + machine id + sequence). See `10`.
6. **Operational cost**: backups, schema changes, monitoring across many shards.

**Golden rule to say:** "Do not shard until you must. First try: indexes, caching, read replicas, a bigger machine."

---

## Part C. Together

Real systems use both: each shard is itself a leader with followers.

```
            Router / app logic: shard = hash(user_id) % 4
                 |          |          |          |
              Shard 1    Shard 2    Shard 3    Shard 4
              Leader     Leader     Leader     Leader
              +2 repl    +2 repl    +2 repl    +2 repl
```

---

## Part D. Interview questions

**Q: Your DB is slow. What do you do before sharding?**
A: Check queries and add indexes; add a cache; add read replicas; move big blobs out; archive old data; scale up. Shard only when writes or storage cannot fit on one primary.

**Q: How do you add a shard without downtime?**
A: Use consistent hashing or many logical shards. Copy the moving logical shard to the new machine while the old one still serves; keep changes flowing (replication/dual write); switch the routing entry; remove the old copy.

**Q: Replication lag broke my UI. Fix?**
A: Read-your-own-writes: for a few seconds after a write, read from the leader (or the replica known to have caught up).

---

## Quick check

1. Replication vs sharding: which increases storage capacity?
2. Why is `hash(key) mod N` bad when N changes?
3. Give an example of a bad shard key and say why.
4. What does W + R > N guarantee?
