# 01e. Caching (and Why Invalidation Is Hard)

---

## 1. What is a cache?

A cache is a small, **fast** place that keeps copies of data you use often, so you do not go to the slow place (the database) every time.

**Analogy:** You keep a water bottle on your desk. Walking to the kitchen (database) for every sip is slow. The bottle (cache) is small, near, and quick. But sometimes the bottle is empty or old, and you must refill it.

Speed idea (rough, order of magnitude; mark as estimate): reading from memory takes about 100 nanoseconds; a database call over the network takes about 1 to 10 milliseconds. That is 10,000 times or more slower. See `02`.

```
 App ---> Cache (Redis/Memcached) ---hit---> return
            | miss
            v
         Database ---> save in cache ---> return
```

- **Hit** = data was in the cache. **Miss** = it was not.
- **Hit ratio** = hits / total. A 95 percent hit ratio means only 5 percent of reads reach the database. If it drops to 80 percent, the database gets 4 times more reads (20 vs 5). Say this - it shows you understand why the hit ratio matters.

When to cache: reads are much more than writes, the same data is asked often, slightly old data is acceptable.

---

## 2. Where can a cache live?

```
Browser cache -> CDN -> API gateway cache -> App-local memory -> Distributed cache (Redis) -> DB buffer cache
 (closest to user)                                                              (closest to data)
```

- **Browser / CDN**: for files and public pages (`01b`).
- **In-process cache** (a map in your app memory): fastest, but each server has its own copy and can differ.
- **Distributed cache** (Redis, Memcached): a separate cluster all servers share. One more network hop, but a single shared view.

---

## 3. The main caching patterns

### Cache-aside (lazy loading) - the most common

1. App asks cache. 
2. On miss, app reads DB.
3. App writes the value into the cache.

Writes: update the DB, then **delete** the cache key (the next read refills it).
Pros: simple, only needed data is cached, cache failure is not fatal. Cons: first read is slow; small chance of stale data.

### Read-through

Same idea, but the cache library itself loads from DB on a miss. App only talks to the cache.

### Write-through

On every write, the app writes to the cache **and** the DB together. Cache is always fresh. Cons: slower writes; caches data that may never be read.

### Write-back (write-behind)

App writes to the cache only; the cache writes to the DB later in a batch. Pros: very fast writes. Cons: **if the cache dies before flushing, data is lost.** Use only where small loss is okay (like view counters).

### Write-around

Write straight to DB, skip the cache; cache fills on the next read. Good when written data is rarely read soon.

| Pattern | Read speed | Write speed | Freshness | Risk |
|---|---|---|---|---|
| Cache-aside | good after first | normal | can be stale a little | low |
| Write-through | good | slower | fresh | low |
| Write-back | good | **fastest** | fresh in cache | **data loss** |

---

## 4. Eviction: what to remove when the cache is full

| Policy | Meaning |
|---|---|
| **LRU** (least recently used) | Throw out what was not used for the longest time. The usual choice |
| **LFU** (least frequently used) | Throw out what is used least often |
| **FIFO** | Oldest first |
| **TTL** | Each key expires after a set time, no matter what |

Practical default: **LRU + TTL**.

Interview bonus: LRU is built with a hash map + doubly linked list (O(1) get and put). Stripe interviews reportedly mention a distributed LRU cache (see `91`).

---

## 5. Invalidation: the famous hard problem

"There are only two hard things in computer science: cache invalidation and naming things." (A well-known joke.)

**Invalidation** means: when the real data changes, the cached copy must be removed or updated. If not, users see old data (**stale**).

Ways to handle it:

1. **TTL only** - accept staleness for N seconds. Simple. Often enough ("profile picture may be 60 seconds old").
2. **Delete on write** - when the DB row changes, delete the cache key. The most common approach.
3. **Update on write** - write the new value into the cache (write-through).
4. **Event-based** - publish "user changed" to a queue; cache subscribers delete their copies. Good across many services.
5. **Versioned keys** - key includes a version: `user:42:v7`. New version = new key. Old keys die by TTL.

### A classic race condition (good to mention)

```
Thread A: reads DB (old value)           
Thread B: updates DB (new value), deletes cache
Thread A: writes OLD value into cache   <-- stale value now sits in cache!
```

Fixes: short TTL as a safety net; use a version or timestamp check when writing; or "delayed double delete" (delete again after a short wait). Say: "TTL is my safety net so wrong data never stays forever."

---

## 6. Cache problems and fixes

| Problem | What happens | Fix |
|---|---|---|
| **Cache stampede / thundering herd** | A popular key expires; 10,000 requests miss at once and hit the DB | Lock so only one request rebuilds (others wait); add random jitter to TTLs; refresh early in the background |
| **Cache penetration** | Requests for keys that **do not exist** always miss and hit DB (or an attacker does it on purpose) | Cache the "not found" answer for a short time; use a Bloom filter to reject impossible keys |
| **Hot key** | One key (a celebrity profile) gets huge traffic on one cache node | Replicate the hot key to many nodes, add a local in-process cache, split into `key#1..#N` |
| **Cold start** | After a restart the cache is empty, DB overloaded | Warm up before taking traffic; rate-limit; keep replicas |
| **Cache outage** | Cache is down, all load goes to DB | Protect DB with rate limits/circuit breaker; fall back gracefully; run cache with replicas |
| **Inconsistency** | Cache and DB disagree | TTL, delete on write, accept eventual consistency |

**Bloom filter in one line:** a tiny structure that says "definitely not present" or "maybe present". It never says "not present" for something that is present. Good for blocking requests for fake keys.

---

## 7. How a distributed cache is spread over machines

With 10 cache servers, which one holds key `user:42`? Use **consistent hashing**: map servers and keys onto a ring; a key goes to the next server clockwise. When a server is added or removed, only a small part of the keys move (not all). More in `01f`.

---

## 8. What to say in an interview (templates)

- "Reads are 100 to 1 over writes, so I add a cache-aside layer with Redis, TTL of 5 minutes, LRU eviction."
- "On update I write to the DB, then delete the key. TTL covers the rare race."
- "To avoid a stampede, I add jitter to TTLs and use a single-flight lock per key."
- "I never cache user-private data on the CDN."

---

## 9. Quick check

1. What happens to the DB load if hit ratio falls from 95 to 90 percent?
2. Cache-aside vs write-through: which one can serve stale data and why?
3. What is a stampede and how do you reduce it?
4. Why is write-back risky?
5. Which is safer for invalidation: TTL only, or delete-on-write plus TTL?
