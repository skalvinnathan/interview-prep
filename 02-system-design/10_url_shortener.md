# 10. Design a URL Shortener

Start here. It is small, and it teaches the whole method.

---

## 1. The problem in plain words

Long links are ugly: `https://shop.com/products/electronics/phones?id=84721&ref=mail&utm=abc`. A **URL shortener** gives a tiny link: `https://sho.rt/aZ3kP9`. When someone opens the tiny link, the system sends them to the long one.

**Analogy: a coat-check at a theatre.** You give a big coat (long URL) and get a small token (short code). Later you show the token and get the coat back.

```
User opens sho.rt/aZ3kP9 --> Server looks up "aZ3kP9" --> replies "go to https://shop.com/..." (redirect)
```

---

## 2. Requirements

**Must-have (functional)**
1. Create a short link from a long URL.
2. Opening the short link redirects to the long URL.
3. Short links should not clash (two different long URLs never get the same code).
4. Links can have an optional expiry date.

**Non-functional**
- Redirects must be **very fast** (target under 100 ms, assumption) and **highly available** (a dead short link breaks other people's pages).
- Short codes should be hard to guess (so private links stay private enough).
- Reads are far more than writes.

**Out of scope (say it out loud)**
- User accounts and login, custom analytics dashboards, QR codes, link editing, abuse detection (mention as future work).
- Custom aliases: optional extra (see deep dive).

---

## 3. The numbers (estimates)

From `02_numbers_and_estimation.md` (assumptions: 100M new links/month, reads 100x writes, keep 5 years, 500 bytes per record):

| Item | Value |
|---|---|
| Writes | about 40 per second |
| Reads (redirects) | about 4,000 per second average, 12,000 peak |
| Links in 5 years | 6 billion |
| Storage in 5 years | about 3 TB (9 TB with 3 copies) |
| Code length | 6 characters of base62 = 56.8 billion codes (enough); 7 characters gives 3.5 trillion for more room |
| Cache | about 20 to 35 GB hot data (rough) |

Meaning: small data, read-heavy. One database with replicas plus a cache is enough at first.

---

## 4. The API

```
POST /v1/links
  headers: Authorization (API key), Idempotency-Key (optional)
  body:    { "long_url": "https://...", "expires_at": "2027-01-01T00:00:00Z", "alias": "mycode" (optional) }
  reply:   201 { "short_url": "https://sho.rt/aZ3kP9", "code": "aZ3kP9" }
  errors:  400 invalid URL, 409 alias taken, 429 rate limited

GET /{code}
  reply:   301 or 302 with header Location: <long_url>
           404 if unknown, 410 if expired

DELETE /v1/links/{code}   (owner only)
```

**301 vs 302 (a favourite question):**
- **301 Moved Permanently**: browsers and CDNs cache it. Fewer hits on your server, but you cannot count clicks or change the target later.
- **302 Found (temporary)**: every click comes to your server. You can count clicks, expire links, change target. Costs more traffic.
Choose 302 if you need analytics or expiry; 301 if you want the lowest load.

---

## 5. The data tables

One main table is enough.

**links**

| Column | Type | Note |
|---|---|---|
| code | string(7) | **Primary key**. The thing we look up |
| long_url | text | |
| owner_id | bigint | optional |
| created_at | timestamp | |
| expires_at | timestamp | nullable |

Access pattern: "get by code" only. That is a pure key-value lookup, so a key-value or wide-column store (DynamoDB, Cassandra) fits well, **or** a plain SQL table with a primary-key index also works for this scale. Say: "At 40 writes/s and 3 TB, even PostgreSQL works. I choose SQL first for simplicity, and note that a key-value store scales out more easily if volume grows 100x."

Optional **clicks** table (if analytics): `(code, ts, country, user_agent)` - append-only, better in a separate analytics store fed by a queue.

---

## 6. Version 1 (simple)

```
 Browser
    |
    v
+-----------+        +-------------------+
| Web server| -----> | Database          |
| (1 app)   |        | links(code, url)  |
+-----------+        +-------------------+
```

Create: server generates a code, inserts a row. Redirect: server reads the row and sends 302.

How to generate a code in V1: take an auto-increment number from the database (1, 2, 3...) and convert it to base62. Id 125 becomes "21" in base62. Short, unique, simple.

Problem: codes are **guessable and sequential** (anyone can scan 1, 2, 3...). Fine for V1; fixed below.

---

## 7. Growing 100x, step by step

Now 400,000 redirects per second instead of 4,000, and 4,000 creates per second.

**Step 1. Add a load balancer and many stateless app servers.** The app keeps no state, so add servers freely. (`01c`)

```
Browser -> LB -> [App][App][App][App] -> DB
```

**Step 2. Add a cache (Redis) in front of the database.** Cache-aside on `code -> long_url`. Hot links are served from memory; with a 90+ percent hit ratio the DB sees under 10 percent of reads. TTL on entries (for example one day) plus LRU eviction. Negative-cache unknown codes for a short time, so attackers guessing codes cannot hammer the DB. (`01e`)

**Step 3. Add read replicas.** Followers serve cache misses. Writes go to the leader. Redirects can tolerate a few seconds of lag (a brand-new link might 404 for a moment; fix: read the leader if the replica says not found). (`01f`)

**Step 4. CDN / edge for the hottest links.** A 301/302 with `Cache-Control` for a short period can be cached at the edge. Only possible if you accept less accurate click counting. (`01b`)

**Step 5. Shard the database (if needed).** Shard by `code` using hash or consistent hashing (the code is already random-looking, so spread is even). Every lookup is by code, so every query goes to exactly one shard. (`01f`)

**Step 6. Make code generation scale (the real design problem).** With many app servers and shards, one auto-increment counter is a bottleneck. Options:

| Option | How | Pros | Cons |
|---|---|---|---|
| **A. Random code + check** | Make random 7 chars; insert; on a clash (unique constraint), retry | Simple; unguessable | Clash chance grows as the table fills; extra retry |
| **B. Hash of URL** | md5/sha of long URL, take first 7 chars | Same URL gives same code (dedupe) | Collisions happen; handle by re-hashing with a salt |
| **C. Counter ranges** | A small service (or ZooKeeper/etcd, or a DB table) hands each app server a **block** of numbers (for example 1,000,000 at a time). Server uses them locally; converts to base62 | No clash by design; very fast; no per-create DB call for id | If a server dies, its unused block is lost (fine, ids are plentiful); codes are sequential (shuffle bits or add a secret permutation to hide order) |
| **D. Snowflake-style id** | timestamp + machine id + sequence, base62-encode | No coordination | Longer code (about 11 chars for 64-bit) |
| **E. Pre-generated key pool** | A background job fills a "unused keys" table; creators take one | Fast, no clash | Another system to run; must make "take" atomic |

My choice (say it): **C, counter ranges, then base62 with a bit-shuffle** so codes are short, unique, and not easily guessable. If an interviewer prefers simplicity, say A with a unique constraint is fine at 4,000 creates/s because the table is 6 B out of 56.8 B (about 10 percent full after 5 years, so a clash happens on about 1 in 10 tries at the end; that is cheap to retry).

**Step 7. Multi-region.** Put full read stacks (cache + replica) in several regions. Route users by geo-DNS to the nearest. Writes go to one home region (or each region owns its own code range prefix). Replicate asynchronously.

Final picture:

```
User -> DNS (geo) -> CDN edge --miss--> LB -> [App servers x N]
                                           |         |
                                       Redis cluster | (create)
                                           |         v
                                           |   ID range service (etcd/DB)
                                           v
                              DB shards (leader + replicas each)
                              
   App -> Kafka (click events) -> Analytics store (async, off the hot path)
```

---

## 8. Trade-offs and why

| Choice | Why | Cost |
|---|---|---|
| 302 instead of 301 | Can count clicks, expire links | More traffic |
| Cache-aside Redis | Reads dominate | Stale for TTL; extra system |
| Counter ranges | No clashes, fast | Sequential unless shuffled; a lost block when a server dies |
| SQL first, key-value later | Simplicity now, easy growth path | A migration later |
| Click counts through a queue | Keep redirect path fast | Counts are eventually consistent (seconds late) |
| Eventual consistency on replicas | Cheap reads | New link may be briefly missing; solved with read-your-write on creator |

---

## 9. What breaks and how to fix it

| Failure | Effect | Fix |
|---|---|---|
| Cache node dies | More DB reads | Redis replicas; DB can handle some; warm up; rate-limit misses |
| Hot link (viral) | One cache key overloaded | Local in-process cache for ultra hot keys; CDN; replicate key |
| Cache stampede when hot key expires | DB spike | Single-flight lock, TTL jitter |
| DB leader dies | Creates fail | Automatic failover to a replica; redirects continue from cache and replicas |
| Code clash | Create fails | Retry with a new code; with counter ranges it cannot happen |
| Abuse (spam, phishing links) | Reputation damage | Rate limit creates per user/IP; scan URLs against blocklists; allow reporting; disable codes |
| Attackers scan codes | DB load | Negative cache, rate limit per IP, longer codes |
| Expired links remain | Wasted space | TTL in DB, or a nightly cleanup job; returns 410 |
| Duplicate creates from retries | Two codes for one click | Idempotency key |

---

## 10. Questions the interviewer asks next (with model answers)

**Q1. How do you make sure two users never get the same code?**
A. The code is the primary key, so the database enforces uniqueness. On top of that I use counter ranges so servers never produce the same number. If I used random codes, a unique constraint plus retry catches a clash.

**Q2. Same long URL submitted twice. Same code or a new one?**
A. Depends on requirements. If every user needs their own link (to track their own clicks), make a new code. If we want to save space, keep an index on a hash of the long URL and return the old code. I would ask the interviewer; default is new code per request, with idempotency key for retries.

**Q3. How do you support custom aliases like `sho.rt/mysale`?**
A. Same table, the alias is the code. Insert with a unique constraint; return 409 if taken. Reserve a keyspace (for example codes longer than 7 or with a prefix) so generated codes never clash with aliases, and block reserved words like `admin`.

**Q4. How do you count clicks without slowing redirects?**
A. On redirect, the server sends an event to Kafka (fire and forget, with a local buffer) and answers right away. A consumer aggregates counts into an analytics store. Counts may be seconds late and, if Kafka is down, a few clicks can be lost; I accept that, since redirects matter more.

**Q5. How do you expire links?**
A. Store `expires_at`. On read, if expired, return 410. A background job deletes old rows. Cache TTL is min(default, time to expiry).

**Q6. What if the cache is cold after a deploy or an outage?**
A. Warm it by replaying recent hot keys, roll out gradually, and protect the DB with rate limiting and a circuit breaker.

**Q7. What do you monitor?**
A. Redirect success rate, p99 latency, cache hit ratio, DB replica lag, create error rate, key-range exhaustion. SLO example: 99.99 percent of redirects succeed, p99 under 100 ms.

**Q8. SQL or NoSQL?**
A. Access is only by key and the data is small, so both work. I start with SQL for simplicity and strong uniqueness; I would move to a key-value store when I need to shard widely.

**Q9. Why not hash the URL?**
A. A short hash collides more easily and the same URL always maps to one code, which prevents per-user links. Collisions need a handling path anyway. Counter ranges are simpler to reason about.

---

## 11. Say it out loud (6 sentences)

1. "A URL shortener maps a short code to a long URL, with far more reads than writes, so I design for fast redirects."
2. "My numbers: about 40 creates and 4,000 redirects per second, 6 billion links in 5 years, about 3 TB, so a 6 to 7 character base62 code is enough."
3. "I expose POST /v1/links and GET /{code} returning a 302, and I store one table keyed by code."
4. "Version 1 is one app server and one database; to scale I add a load balancer, a Redis cache, read replicas, and finally shard by code."
5. "I generate codes with counter ranges handed to each server, then base62 with shuffled bits, so there are no clashes and codes are hard to guess."
6. "Clicks go through Kafka off the hot path, and I protect the system from hot keys, stampedes and abuse with caching, jitter and rate limits."
