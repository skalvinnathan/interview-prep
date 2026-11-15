# 02. Numbers and Estimation

Goal: in 3 minutes, turn "1 million users" into "how many requests per second, how much disk, how many servers". Rough answers are fine. **Everything in this file is an estimate** unless a number is exact math (like powers of two).

Why do it? The numbers tell you what design you need. 40 requests per second = one small server. 400,000 per second = a whole fleet, caches, sharding.

---

## 1. Powers of two (exact)

| Power | Exact value | Easy name | Short name |
|---|---|---|---|
| 2^10 | 1,024 | about 1 thousand | 1 KB (kilobyte) |
| 2^20 | 1,048,576 | about 1 million | 1 MB (megabyte) |
| 2^30 | 1,073,741,824 | about 1 billion | 1 GB (gigabyte) |
| 2^40 | about 1.1 x 10^12 | about 1 trillion | 1 TB (terabyte) |
| 2^50 | about 1.1 x 10^15 | about 1 quadrillion | 1 PB (petabyte) |

Trick: every 10 powers of 2 is about 1,000 times more. So 2^32 is about 4 billion (4 x 2^30).

Useful: a 32-bit number has about 4.3 billion values. A 64-bit number has about 1.8 x 10^19.

### Words for big numbers

| Number | Words |
|---|---|
| 1,000 | thousand (K) |
| 1,000,000 | million (M) |
| 1,000,000,000 | billion (B) |
| 10^12 | trillion |

---

## 2. Time shortcuts

| Period | Seconds | For quick math use |
|---|---|---|
| 1 minute | 60 | 60 |
| 1 hour | 3,600 | about 4 x 10^3 |
| 1 day | 86,400 | **about 10^5** (100,000) |
| 1 month | about 2.6 million | about 2.5 x 10^6 |
| 1 year | about 31.5 million | about 3 x 10^7 |

**The golden shortcut:** 1 million requests per day = about 10 requests per second (1,000,000 / 100,000). 100 million per day = about 1,000 per second.

---

## 3. Latency numbers (rough orders of magnitude)

These are the well-known "numbers every programmer should know". They are approximate and vary by hardware and year. Use them to compare, not as exact facts.

| Operation | Rough time |
|---|---|
| Read from CPU cache | ~1 nanosecond (ns) |
| Read from main memory (RAM) | ~100 ns |
| Read 1 MB from memory | ~ tens of microseconds (us) |
| SSD random read | ~100 us |
| Network round trip inside one data centre | ~0.5 milliseconds (ms) |
| Read 1 MB from SSD | ~1 ms |
| Disk (spinning) seek | ~10 ms |
| Network round trip across continents | ~100 to 150 ms |

Lessons:
1. Memory is thousands of times faster than disk or network. That is why caches work.
2. Avoid many network hops in one request.
3. Sequential disk reads are much faster than random ones (why logs and Kafka are fast).
4. Distance costs time. That is why CDNs and regions exist.

---

## 4. Typical sizes (assumptions you can state)

| Item | Rough size |
|---|---|
| A character (ASCII) | 1 byte |
| A tweet-like text message | 100 to 300 bytes |
| A database row for a simple record | 100 bytes to 1 KB |
| A URL | 100 to 200 bytes |
| A profile photo (compressed) | 100 to 300 KB |
| A phone photo | 2 to 5 MB |
| 1 minute of video (HD) | tens of MB (depends on quality) |
| A log line | 100 to 300 bytes |
| An id (64-bit) | 8 bytes |

Always say "I assume ..." and let the interviewer correct you.

---

## 5. Server capacity rules of thumb (estimates!)

These change with the workload. State them as assumptions.

| Thing | Rough number to assume |
|---|---|
| One web/app server | 1,000 to 10,000 simple requests per second (depends on work done) |
| One relational DB primary | about 1,000 to 10,000 simple writes/s; reads higher, with good indexes (very workload-dependent) |
| One Redis node | about 100,000 simple operations per second |
| One WebSocket server | tens of thousands up to ~100,000 idle connections (memory bound) |
| One Kafka broker | hundreds of thousands of small messages per second (hardware dependent) |
| One disk/SSD node | a few TB comfortably |

If an interviewer wants a better number, they will tell you. The method matters more than the exact value.

---

## 6. Availability and "nines"

| Availability | Downtime per year (about) |
|---|---|
| 99% | 3.65 days |
| 99.9% ("three nines") | 8.8 hours |
| 99.99% ("four nines") | 52 minutes |
| 99.999% ("five nines") | 5 minutes |

(Exact math: 365 days x 24 hours x (1 - availability).)

---

## 7. The estimation recipe

1. **Users**: total users, daily active users (DAU). Often DAU = 10 to 50 percent of total (assumption).
2. **Actions per user per day**: e.g. 5 reads, 1 write.
3. **Requests per day** = DAU x actions.
4. **QPS (queries per second)** = requests per day / 86,400 (or /100,000 for quick math).
5. **Peak QPS** = average x 2 to 3 (sometimes x 10 for spiky things like flash sales).
6. **Storage** = items per day x size per item x days kept. Multiply by replicas (usually x3).
7. **Bandwidth** = QPS x size per response.
8. **Servers** = peak QPS / QPS per server, plus spare (at least 2 for safety, and keep 30 to 50 percent headroom).
9. **Cache size**: 80/20 rule - assume 20 percent of the data gets 80 percent of the reads. Cache that 20 percent (or even less).

---

## 8. Worked example 1: URL shortener

**Assumptions (all estimates):** 100 million new short links per month. Reads are 100 times writes. Keep links 5 years. Each record is about 500 bytes (long URL, short code, dates, owner).

**Writes per second**
- 1 month = about 2.6 million seconds.
- 100,000,000 / 2,600,000 = about **40 writes/s**.

**Reads per second**
- 40 x 100 = **4,000 reads/s** on average.
- Peak (x3 assumption) = about **12,000 reads/s**.

**Storage in 5 years**
- Links = 100M x 12 months x 5 years = 6 billion links.
- 6,000,000,000 x 500 bytes = 3 x 10^12 bytes = **about 3 TB**.
- With 3 copies = about 9 TB. Fits easily on a few machines.

**Short code length**
- Use base62 (a-z, A-Z, 0-9 = 62 symbols).
- 62^6 = about 56.8 billion codes; 62^7 = about 3.5 trillion.
- We need 6 billion codes. 6 characters (56.8 B) is enough, with room to spare.

**Cache**
- 80/20 rule: hot 20 percent of reads. Daily reads = 4,000 x 86,400 = about 345 million. Hot links data: if we cache 20 percent of daily-unique items, each at 500 bytes... roughly 345M x 0.2 x 500 bytes = about 35 GB. Fits in one or two Redis nodes. (Overestimate, since many reads repeat the same link.)

**Conclusion:** 12,000 reads/s peak is easily served by a few app servers plus a cache; 3 TB is small. A single database with replicas works at first; sharding is not needed on day one.

---

## 9. Worked example 2: Chat messages

**Assumptions:** 50 million daily active users (DAU). Each sends 40 messages per day. Average message 100 bytes. Keep messages forever (or 5 years for the math). 20 percent of DAU are online at the same time at peak.

**Messages per day** = 50M x 40 = 2 billion.

**Messages per second**
- 2,000,000,000 / 86,400 = about **23,000/s** average.
- Peak (x3) = about **70,000/s**.

**Storage**
- Per day: 2B x 100 bytes = 200 GB/day.
- Per year: 200 GB x 365 = about **73 TB/year**. (Add metadata and index: maybe x2 = about 150 TB/year.)
- With 3 copies: about 220 TB/year just for raw. That is why a write-friendly store and sharding are needed.

**Connections**
- 20 percent of 50M = **10 million** connections open at peak.
- If one WebSocket server handles 100,000 connections (assumption), we need 10,000,000 / 100,000 = **100 servers** (plus spare, so about 150).

**Delivery fan-out** (group chat): a message to a group of 100 means 100 deliveries. If 10 percent of messages are group chats of 100: 70,000 x (0.9 x 1 + 0.1 x 100) = 70,000 x 10.9 = about 760,000 deliveries/s at peak. Messages are stored once, but pushed many times.

**Conclusion:** Many connections (100s of servers), lots of writes (shard by chat id), many TBs/year (use a wide-column store).

---

## 10. Worked example 3: Video streaming

**Assumptions:** 500,000 new videos uploaded per day. Average raw upload 200 MB. We store several quality versions (transcoded), which together are about 2 times the original (assumption). 100 million video views per day. Average watch uses 50 MB of data. Keep forever (use per-year numbers).

**Upload bandwidth**
- 500,000 x 200 MB = 100,000,000 MB = 100 TB/day.
- 100 TB / 86,400 s = about 1.2 GB/s = about **9 to 10 Gbps** (x8 bits) average inbound.

**Storage**
- Original + transcoded = 200 MB x 3 (original plus 2x versions) = 600 MB per video.
- 500,000 x 600 MB = 300 TB/day.
- Per year: 300 TB x 365 = about 110 PB (petabytes). Huge. This must be in cheap object storage; old and rarely watched videos can move to cold storage.

**Viewing (egress) bandwidth**
- 100M x 50 MB = 5,000,000,000 MB = 5 PB/day.
- 5 PB / 86,400 s = about 58 GB/s = about **460 Gbps** average. Peak maybe 2 to 3 times more.
- No single data centre should serve this. **A CDN serves almost all of it.**

**Metadata (small):** 500,000 videos/day x 1 KB = 0.5 GB/day. Tiny. A normal database holds it.

**Conclusion:** Bytes dominate, not requests. Object storage, CDN and a transcoding pipeline (queue + workers) are the heart. Database size is not the problem.

---

## 11. Common mistakes in estimation

1. Mixing up bits and bytes (network speed is in bits: 1 byte = 8 bits).
2. Forgetting replication (x3) and index overhead.
3. Using average QPS only. Always think of peak.
4. Giving numbers with fake accuracy. Say "about" and round.
5. Spending 10 minutes on math. Limit to 3.
6. Not saying what the number **means** for the design. Always end with "so we need..."

---

## 12. Practice

1. 200 million daily users, each opens the app 5 times a day: how many requests per second? (Answer: 200M x 5 = 1B/day, /100,000 = 10,000 per second average. Peak x3 = 30,000.)
2. Photo app: 10M photos uploaded per day, 3 MB each. Storage per year? (10M x 3 MB = 30 TB/day, x365 = about 11 PB/year.)
3. 5,000 requests per second, one server handles 1,000 per second. How many servers with 50 percent headroom? (5 needed at full load; with 50 percent headroom = 10 servers.)
