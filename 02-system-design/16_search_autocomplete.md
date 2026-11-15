# 16. Design Search Autocomplete (Typeahead)

---

## 1. The problem in plain words

You type "how to" in a search box. Before you finish, the box shows 5 suggestions: "how to tie a tie", "how to lose weight", ... Each time you type a letter, the list updates. It must be **very fast** (it must feel instant) and the suggestions should be the **most popular** or most useful ones.

**Analogy: a helpful shop assistant who knows the crowd.** You say "ba..." and she immediately says "most people who say 'ba' want bananas, bread, or batteries." She does not search the whole shop; she has a short list ready for every starting sound.

---

## 2. Requirements

**Must-have**
1. Given a prefix (what the user has typed), return the top 5 to 10 matching suggestions.
2. Suggestions ranked by popularity (how often people search them), maybe with freshness (trending).
3. Very low latency: under about 100 ms end to end (assumption), ideally less than 50 ms at the server.
4. Suggestions update over time as new searches happen (hourly or daily is fine; trending faster).

**Non-functional**
- High availability; if suggestions fail, search itself still works (graceful degradation).
- Scale to millions of users.
- Safe: no offensive or illegal suggestions (filter list).

**Out of scope**
- The search results page itself (indexing documents, ranking pages), spell correction (mention as extension), deep personalisation, voice search.

---

## 3. The numbers (estimates)

Assume 10M daily active users, 10 searches each per day. While typing a query, the client sends a request for most keystrokes, but with a small **debounce** (wait about 100 to 200 ms after the last key) and caching, about 5 requests per search.

| Item | Value |
|---|---|
| Requests per day | 10M x 10 x 5 = 500M |
| Per second | 500M / 86,400 = about 5,800 average; about 17,000 peak |
| Distinct queries | Assume 100M distinct query strings, average 20 bytes = 2 GB raw text (plus counts) |
| Trie in memory | Say 5 to 10 GB with top-K lists stored in nodes (estimate). Fits on one big machine, but we replicate for throughput |
| Update rate | Query logs: 10M x 10 = 100M searches/day = about 1,160 log events per second. Easy |

Meaning: data is small (GBs), reads are frequent. **Keep it in memory, precompute the answers, replicate the read servers.**

---

## 4. The API

```
GET /v1/suggest?q=how%20to&limit=5&lang=en
  reply: 200 {
    "prefix": "how to",
    "suggestions": [ "how to tie a tie", "how to lose weight", "how to screenshot on mac", ... ]
  }
  headers: Cache-Control: public, max-age=300     (browsers and CDN can cache popular prefixes)
```

Log API (internal, async, not part of the user's wait):

```
event: { "query": "how to tie a tie", "ts": ..., "user_hash": ..., "country": "IN" }
```

The client does: **debounce** (do not call on every key), cancel old requests, cache previous answers (if "ho" was fetched, reuse for the back-space), and only call after 1 or 2 characters.

---

## 5. The data

**Query log** (append-only, huge): events of completed searches. Stored in Kafka then in a data lake / object storage.

**Query frequency table**: `(query_string, count_in_window, last_seen)`. Built by an aggregation job (batch: daily or hourly, using Spark/MapReduce-style; or stream: counts per 5 minutes).

**Trie (prefix tree)** - the main structure, built from the frequency table:

```
            (root)
           /   |   \
          b    c    h
         /     |     \
        a      a      o
       / \     |      |
      n   t    r      w
      |   |    |      |
     (ban)(bat)(car)  (how)   each node stores top-K suggestions for that prefix
```

At each node store the **top 5 to 10 completions** for that prefix, already sorted by score. Then a lookup is: walk down the tree by the prefix (cost = length of prefix) and return the stored list. **No searching below the node at query time.**

Alternative that is simpler to run: a key-value store: `prefix -> [top suggestions]`. Precompute for every prefix of every popular query (up to length 20, say). A lookup is one key read. This is easy to shard and cache. Say: "Logically it is a trie; physically I can store it as prefix -> top-K in a key-value store."

Node/KV memory estimate: if we keep only prefixes of the top 10M queries, average 15 prefixes each = 150M keys x (key ~15 B + 5 suggestions of ~20 B = ~115 B) = about 17 GB. (Estimate.) Fits in memory on a few machines.

---

## 6. Version 1 (simple)

```
 Client --GET /suggest?q=ho--> [Server] --> SQL: SELECT query FROM queries
                                                  WHERE query LIKE 'ho%' ORDER BY count DESC LIMIT 5
```

Problem: `LIKE 'ho%'` over 100M rows plus sorting on every keystroke is slow. Even with an index, "order by count" over many matches is costly. At 17,000/s the DB dies.

---

## 7. Growing 100x, step by step

**Step 1. Precompute top-K per prefix (the trie / prefix map).** Move the work from query time to build time. Query time becomes one memory lookup. (This single idea is the answer.)

**Step 2. Two paths: serving (fast) and building (slow).**

```
 Serving path (milliseconds):   Client -> LB -> Suggest servers (in-memory trie) -> answer
 Build path (minutes/hours):    Search logs -> Kafka -> Aggregator -> Ranker -> Trie builder -> snapshot -> push to servers
```

**Step 3. The builder.** (1) Collect search logs. (2) Count queries over a window with time decay (recent searches count more). (3) Filter bad words, low-count noise, and personal data. (4) Build the trie with top-K lists. (5) Write a **versioned snapshot** to object storage. (6) Suggest servers load the new snapshot in the background and **swap** it in atomically (no downtime). Rebuild daily, plus a smaller frequent update for trending queries.

**Step 4. Replicate suggest servers.** Because the data is small, every server holds the whole trie; scale by adding servers behind a load balancer (stateless readers). If one machine cannot hold it (very large languages/regions), **shard by first characters** (a-f, g-m, ...) or by language/region; hot prefixes like "a" or "the" need extra replicas. (`01f`)

**Step 5. Cache aggressively.** Short prefixes (1 to 3 characters) are asked millions of times and the answers are almost the same for everybody. Cache at the **CDN / browser** (`max-age` minutes) and in a Redis layer. Result: most traffic never reaches the suggest servers. (`01b`, `01e`)

**Step 6. Client-side tricks.** Debounce, cancel stale requests, reuse earlier answers, prefetch popular prefixes. This can cut traffic several times (estimate).

**Step 7. Freshness and trending.** A streaming job (Kafka + Flink-like stream processor) counts queries per 5-minute window and detects spikes. A small "hot list" overlay is merged into answers at query time (for example, last 1 hour trending terms matching the prefix). Keep the main snapshot stable and the overlay tiny.

**Step 8. Personalisation (optional).** Merge a few personal suggestions (user's history) with global ones. Done at the edge or in a separate small service; do not mix into the shared trie.

**Step 9. Multi-region and localisation.** One trie per language and region (users in India type different queries than users in Brazil). Build per locale; deploy near users.

Final picture:

```
 Browser (debounce, cache)
     |
    CDN (short prefixes cached) --miss--> LB --> [Suggest servers x N, in-memory trie snapshot v42]
                                                       ^                      ^
                                           hot overlay (trending)       swap to v43
                                                       ^                      ^
 Search service --log--> Kafka --> Stream counts ------+      Batch builder (daily) --> snapshot in object store
```

---

## 8. Trade-offs and why

| Choice | Why | Cost |
|---|---|---|
| Precompute top-K per prefix | O(prefix length) lookup, tiny latency | More memory; results are stale until rebuild |
| Batch rebuild + small trending overlay | Simple, stable, still fresh enough | Two paths to maintain |
| Whole trie per server | No network hops; simple scaling | Memory per node; reload time |
| CDN caching of short prefixes | Removes most traffic | Stale for minutes; less personal |
| Trie vs key-value | Trie: compact; KV: easy to shard and operate | Choose by team and scale |
| Approximate counts / sampling | Cheap logging | Slight inaccuracy |
| Filter lists | Safety | Needs human review and updates |

---

## 9. What breaks and how to fix it

| Failure | Effect | Fix |
|---|---|---|
| Suggest server dies | Capacity loss | LB health checks; N+2 replicas; clients tolerate missing suggestions |
| Bad snapshot (corrupt / offensive) | Wrong suggestions everywhere | Validate before publish (size, sample checks, blocklist); keep previous version; fast rollback by switching version pointer |
| Snapshot load causes memory spike | OOM | Load in a separate process, then swap; stagger rollout (canary 5 percent first) |
| Hot prefixes ("a", "the") | Overloaded shard | CDN cache, extra replicas, local cache |
| Spam / manipulation (bots flood a query to make it trend) | Bad suggestions | Count unique users not raw hits; rate limit per user/IP; anomaly detection |
| Typing a new brand-new term | No suggestion | Trending overlay; fallback to no suggestions (fine) |
| Pipeline lag | Stale suggestions | Monitor freshness SLO (age of snapshot), alert |
| Privacy | User queries leak | Only aggregate, drop rare queries (k-anonymity: need many different users), hash ids |
| Suggest path outage | Search box feels broken | Client hides suggestions; search still works |

---

## 10. Questions the interviewer asks next

**Q1. Why a trie and not SQL LIKE?**
A. LIKE has to scan and sort many rows per keystroke. A trie with precomputed top-K per node makes the lookup cost depend only on prefix length, not on data size.

**Q2. How do you rank suggestions?**
A. By frequency with time decay (recent counts weigh more), maybe boosted by freshness, location, and click-through. Keep it a simple score at build time so lookups stay cheap.

**Q3. How do you update when new queries appear?**
A. Daily or hourly batch rebuild creates a new snapshot; a streaming job produces a small trending overlay. Servers swap snapshots atomically.

**Q4. The trie is too big for one machine. What now?**
A. Shard by prefix range or by language/region, with replicas per shard. The client or a router picks the shard from the first characters. Watch for hot shards (letter "s" is common) and split them further.

**Q5. How do you handle typos?**
A. Out of scope for v1. Extension: spell-correction service or fuzzy match (edit distance) as a fallback when few results; or index common misspellings.

**Q6. How do you keep latency under 50 ms?**
A. In-memory lookup, no DB on the path, CDN for common prefixes, debounce on client, servers near users, small responses.

**Q7. How do you remove a bad suggestion fast?**
A. A blocklist checked at serve time (cheap set lookup) so removal is instant, and the next rebuild drops it for good.

**Q8. What about personalised suggestions?**
A. Keep the global trie shared; add a small per-user list (recent searches) merged at the edge. Never put one user's private data into the shared structure.

---

## 11. Say it out loud (6 sentences)

1. "Autocomplete returns the top few popular completions for the prefix the user has typed, and it has to answer in a few tens of milliseconds."
2. "The data is small, a few gigabytes, but requests are frequent, about 17,000 per second at peak, so I precompute answers and serve from memory."
3. "Logically the structure is a trie where each node stores the top 5 to 10 completions, so a lookup only walks the prefix length; physically it can be a prefix-to-list key-value map."
4. "A separate build pipeline aggregates search logs with time decay, filters bad terms, builds a versioned snapshot, and the stateless suggest servers swap it in atomically."
5. "A CDN and browser cache absorb short popular prefixes, the client debounces and cancels requests, and a small streaming overlay adds trending queries."
6. "If anything fails, search still works without suggestions, and I protect quality with a blocklist, snapshot validation, canary rollout and quick rollback."
