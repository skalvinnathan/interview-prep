# 13. Design a News Feed (like Instagram, Facebook or Twitter/X home timeline)

---

## 1. The problem in plain words

Users follow other users. When you open the app, you see a list of recent posts from the people you follow, newest (or most relevant) first. It must open fast, even if you follow 1,000 people.

**Analogy: a newspaper stand with personal newspapers.** Two ways to give you your morning paper:
- **Pull (fan-out on read):** when you arrive, the seller runs to 1,000 shops, collects the latest article from each, and builds your paper on the spot. Always fresh, but you wait.
- **Push (fan-out on write):** every time an author writes an article, the seller immediately puts a copy into the personal folder of each follower. When you arrive, your paper is already ready. Fast for you, but if an author has 50 million followers, writing one article means 50 million copies.

The whole design is about choosing between these two and mixing them.

---

## 2. Requirements

**Must-have**
1. Create a post (text, optionally image/video link).
2. Follow / unfollow users.
3. View the home feed: posts from people I follow, newest first, paginated (infinite scroll).
4. Feed loads fast (under about 300 ms for the first page; assumption).

**Non-functional**
- Highly available. Eventual consistency is fine: a post may take a few seconds to appear in followers' feeds.
- Scale: hundreds of millions of users; a few users have tens of millions of followers (celebrities).

**Out of scope**
- Ranking by machine learning (mention as extension: a ranking service re-orders candidates), ads, comments and likes details, notifications (`14`), media processing (`17`, `15`), search.

---

## 3. The numbers (estimates)

Assumptions: 100M daily active users (DAU). Each opens the feed 5 times a day. 10M new posts per day. Average user has 200 followers. Feed shows 20 posts per page.

| Item | Value |
|---|---|
| Feed reads per day | 100M x 5 = 500M |
| Feed reads per second | 500M / 86,400 = about 5,800 average; about 17,000 peak (x3) |
| New posts per second | 10M / 86,400 = about 115 average; about 350 peak |
| Fan-out on write | 10M posts x 200 followers = 2 billion feed inserts per day = about 23,000 per second |
| Post storage | 10M/day x 1 KB (text + metadata) = 10 GB/day = 3.6 TB/year (media is separate in blob storage) |
| Feed cache | Keep latest 500 post ids per user: 500 x 8 bytes = 4 KB per user. 100M users x 4 KB = 400 GB. Fits in a Redis cluster |

Meaning: reads (17,000/s) are about 50 times more than posts (350/s). So **do more work at write time to make reads cheap**: push model for normal users.

---

## 4. The API

```
POST /v1/posts
  body:  { "text": "hello", "media_ids": ["m1"] }
  reply: 201 { "post_id": "p123", "created_at": ... }

POST   /v1/users/{id}/follow         DELETE /v1/users/{id}/follow

GET /v1/feed?cursor=<opaque>&limit=20
  reply: { "posts": [ {post_id, author, text, ts, ...} ], "next_cursor": "..." }

GET /v1/users/{id}/posts?cursor=...      a profile page (user's own posts)
```

Use **cursor pagination** (the cursor holds "last seen timestamp + post id"). Page numbers break when new posts arrive while you scroll (you would see duplicates).

---

## 5. The data tables

**users**: `user_id (PK)`, name, ... (SQL)

**follows** (the social graph): `(follower_id, followee_id)` PK, `created_at`. Needs two lookups:
- "who do I follow?" (index by follower_id)
- "who follows me?" (index by followee_id) - used for fan-out

For huge scale, a graph-like store or two sharded tables (one by follower, one by followee).

**posts**: `post_id (PK)` - a time-sortable id (Snowflake-like, so ids sort by time), `author_id`, `text`, `media_refs`, `created_at`. Sharded by `post_id` or by `author_id`; index on `(author_id, created_at)` for profile pages.

**feed (precomputed)**: in Redis: `feed:{user_id}` is a sorted list (sorted set) of `post_id` by time, capped at 500. Only ids are stored. Details (text, author name) are fetched from a post cache (hydration).

---

## 6. Version 1 (simple): pull model

```
 Client -> App server -> DB
   GET /feed:
     1. SELECT followee_id FROM follows WHERE follower_id = me           (1,000 rows)
     2. SELECT * FROM posts WHERE author_id IN (...) ORDER BY created_at DESC LIMIT 20
```

Works for small data. Breaks because that second query touches many shards and many rows on **every feed load**: 17,000 times per second x 1,000 authors.

---

## 7. Growing 100x, step by step

**Step 1. Fan-out on write (push) for normal users.**

```
 POST /posts --> Post service --> save post in DB
                          |
                          +--> Kafka "new_post" event
                                    |
                              Fan-out workers:
                                for each follower f of author:
                                  Redis: ZADD feed:f  (post_id, time)   (keep latest 500)
```

Reading the feed is now: `ZREVRANGE feed:me 0 19` (20 ids), then fetch 20 posts from a post cache by id, then return. Two fast memory reads. This is why a feed opens in milliseconds.

**Step 2. The celebrity problem.** A user with 50M followers posts. Fan-out on write = 50M Redis writes for one post. Too slow and wasteful (most followers are inactive).

Fix: **hybrid model**.
- Normal authors (under a threshold, for example 10,000 followers; assumption): **push**.
- Celebrities: **do not push**. When a user reads the feed, the server takes the precomputed feed (push part) and **merges** the latest posts of the few celebrities this user follows (pull part), sorted by time.

```
 Read feed = merge( feed:me (from push), latest posts of followed celebrities (pull) )
```

**Step 3. Skip inactive users.** Do not fan out to users who have not logged in for 30 days (they build their feed on first login). Saves a large part of the writes.

**Step 4. Cache layers.**
- Post cache: `post_id -> post JSON` (Redis), hit ratio high because recent posts are read over and over.
- User cache for author names/avatars.
- CDN for media. (`01b`)

**Step 5. Shard and replicate.**
- Posts DB sharded by post_id; follows sharded by follower and by followee (two copies of the graph for the two queries).
- Redis feed cluster sharded by user_id with replicas. (`01f`)

**Step 6. Queue absorbs spikes.** Fan-out is asynchronous: the post call returns after saving the post and publishing to Kafka. Fan-out workers scale with the lag. Partition by author id so one author's posts fan out in order. (`01g`)

**Step 7. Ranking (optional extension).** Feed service fetches candidates (say 500 ids), a ranking service scores them (recency, relationship strength, engagement), returns top 20. It adds latency and complexity; keep a simple chronological fallback.

**Step 8. Unfollow/delete handling.** On delete post: mark deleted in post store; hydration step filters deleted posts, so we need not scrub every feed. On unfollow: filter at read time by checking the current follow list for some entries, or lazily clean.

**Step 9. Multi-region.** Each region has feed caches and post caches; posts replicate asynchronously across regions; follower fan-out happens in each region for its local users.

Final picture:

```
 Client --> LB --> [Feed service] --> Redis feed (ids) --> Post cache --> Post DB shards
                         |  (celebrity pull merge)           ^
                         v                                   |
                    Ranking (optional)           [Fan-out workers] <-- Kafka <-- [Post service]
                                                        |
                                                  Graph DB (follows)
 Media: client --> blob storage --> CDN
```

---

## 8. Trade-offs and why

| Choice | Why | Cost |
|---|---|---|
| Push for normal users | Reads are 50x more than writes; make reads O(1) | Heavy writes; storage for feed copies |
| Pull for celebrities | Avoid 50M writes per post | Slightly slower read (merge) |
| Feed stores ids only | Small memory; fix edits and deletes in one place | One extra hydration lookup |
| Eventual consistency | Fan-out is async, scalable | A post can appear seconds late; own posts shown at once by adding to my own feed on write |
| Cursor pagination | Stable scrolling | Cursor handling logic |
| Cap feed at 500 | Bounded memory | Deep scrolling beyond 500 needs a fallback to pull |
| Skip inactive users | Save writes | First login after a long time is slower |

---

## 9. What breaks and how to fix it

| Failure | Effect | Fix |
|---|---|---|
| Redis feed node dies | Those users' feeds are gone | Replicas; if lost, **rebuild** from the posts DB with the pull method (slow path), then re-cache |
| Fan-out workers lag | Posts appear late | Autoscale workers on queue lag; prioritise active users; alert on lag SLO |
| Celebrity posts | Write storm | Hybrid model with pull for celebrities |
| Hot post (viral) | Post cache key overloaded | Replicate hot key; local cache |
| Poison event in Kafka | Fan-out stuck | Retry with backoff; dead-letter queue |
| Duplicate fan-out (retries) | Post twice in feed | Sorted set by post_id means the same id is stored once (idempotent) |
| Post DB shard down | Hydration fails for some posts | Replicas; return feed without those posts (graceful degradation) |
| Follow graph inconsistent | Wrong fan-out | Source of truth is the graph DB; periodic reconciliation |
| Ranking service down | No ranked feed | Fallback to chronological |

---

## 10. Questions the interviewer asks next

**Q1. Push or pull?**
A. Hybrid. Push for normal users because feed reads are far more frequent than posts; pull for celebrities to avoid giant write storms. I choose the threshold using follower counts and measure it.

**Q2. How do you handle a user who follows 5,000 people?**
A. Their feed is built by push as usual (it is the authors' follower count that decides push cost, not how many I follow). For celebrity pull, I only merge the celebrities among the 5,000 (a short list, cached).

**Q3. How do you show my own new post immediately?**
A. On post, I also write to my own feed (read-your-own-writes), so I see it even before fan-out finishes.

**Q4. What if a user deletes a post?**
A. Mark it deleted in the post store. Feeds contain only ids; the hydration step drops deleted ids. A background job cleans old ids.

**Q5. How do you paginate?**
A. Cursor of (timestamp, post_id). The server returns posts older than the cursor. No duplicates when new posts arrive.

**Q6. How do you store the follow graph for fan-out?**
A. A table sharded by followee_id for "who follows X" (batched reads for fan-out workers) and another sharded by follower_id for "who do I follow". Updated together by an event or transaction; reconciled in the background.

**Q7. How would you add ranking?**
A. A candidate generator takes recent ids from the feed and celebrity pulls; a ranker scores them using features; the feed service returns top N. If ranking is slow or fails, fall back to time order.

**Q8. How do you handle consistency across regions?**
A. Eventual. A follower in another region may see the post a bit later; acceptable for a feed.

**Q9. What would you monitor?**
A. Feed read p99, fan-out lag, cache hit ratios, Redis memory, error rates; SLOs like 99.9 percent of first-page loads under 300 ms and 99 percent of posts visible to followers within 10 seconds (example targets).

---

## 11. Say it out loud (6 sentences)

1. "A news feed shows each user the latest posts from people they follow, and it must load fast."
2. "Feed reads are about 50 times more frequent than posts, so I do work at write time: about 17,000 reads per second but only 350 posts per second at peak."
3. "For normal authors I fan out on write: a Kafka event triggers workers that insert the post id into each follower's Redis feed list, capped at 500."
4. "For celebrities I do not fan out; I merge their latest posts into the feed when the user reads it, which is the hybrid model."
5. "The feed stores only post ids and I hydrate them from a post cache, so edits and deletes are handled in one place."
6. "Fan-out is asynchronous and eventually consistent; if a feed cache is lost I rebuild it from the posts database with the pull method, and if ranking fails I fall back to time order."
