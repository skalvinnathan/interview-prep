# 01b. DNS and CDN

---

## Part A. DNS (the phone book of the internet)

Computers find each other by numbers (IP addresses). Humans remember names. **DNS** (Domain Name System) turns a name like `shop.com` into an IP like `203.0.113.10`.

**Analogy:** You want to call "Ravi's Pizza". You look up the name in a phone book and get a number. DNS is that phone book.

### How a lookup works

```
Your laptop
   |  1. "IP of shop.com?"
   v
Resolver (your ISP or 8.8.8.8)  -- has a cache? yes -> answer right away
   |  2. if not cached, ask in order:
   v
Root server  -> "ask the .com servers"
   v
.com (TLD) server -> "ask shop.com's own name server"
   v
Authoritative name server for shop.com -> "203.0.113.10"
```

The answer is **cached** at many levels for a time called **TTL** (time to live). Example: TTL 300 seconds = cache for 5 minutes.

### Common record types

| Record | Meaning |
|---|---|
| A | name -> IPv4 address |
| AAAA | name -> IPv6 address |
| CNAME | name -> another name (an alias) |
| MX | where to deliver email |
| TXT | free text (used for verification) |
| NS | which servers are authoritative |

### Why DNS matters in system design

1. **Load distribution.** One name can return many IPs (DNS round robin). Simple, but DNS does not know if a server is dead.
2. **Geo routing.** Return the IP of the nearest data centre. A user in Bengaluru gets the Mumbai server; a user in Paris gets Frankfurt. (This is often called geo-DNS or latency-based routing.)
3. **Failover.** If region A is down, change the answer to region B. Because of TTL, some users keep the old answer for a while. So: use **short TTL** for things that may fail over (but short TTL means more lookups).
4. **It is a hidden single point of failure.** Many big outages were DNS problems. Use a reliable provider.

**Trade-off to say:** long TTL = faster and cheaper, but slow to change. Short TTL = quick to change, more lookups.

---

## Part B. CDN (Content Delivery Network)

A **CDN** is a group of servers placed all over the world. They keep **copies** of your files (images, videos, scripts, even some pages). Users get the file from the closest copy.

**Analogy:** A book publisher in Delhi. If every reader in the country must order from Delhi, delivery is slow. So the publisher puts copies in a small shop in each city. Readers go to the nearest shop. The shop is the CDN **edge**; Delhi is the **origin**.

```
                      +--------------------+
                      |  Origin (your app) |
                      +---------^----------+
                                | only on cache MISS
        +-----------+  +--------+--+  +-----------+
        | Edge      |  | Edge      |  | Edge      |
        | Mumbai    |  | Frankfurt |  | Virginia  |
        +-----^-----+  +-----^-----+  +-----^-----+
              |              |              |
         user India     user Europe     user USA
```

### Cache hit and miss

- **Hit**: the edge has the file. Fast (maybe tens of milliseconds).
- **Miss**: the edge does not have it. It asks the origin, saves a copy, and returns it. Slower, but only the first time.

### Two ways to fill a CDN

- **Pull**: edge fetches from origin on the first request (most common, easy).
- **Push**: you upload files to the CDN yourself ahead of time (good for big files you know will be popular, like a new video).

### What to put on a CDN

Good: images, videos, CSS, JavaScript, downloadable files, public pages that rarely change.
Bad: private data, per-user pages, things that change every second.

### Controlling freshness

- **Cache-Control header** tells the CDN how long to keep a file (`max-age=3600`).
- **Versioned file names** (`app.v123.js`): change the name when the file changes, so no stale copy ever. This is the best trick.
- **Purge / invalidate**: tell the CDN to delete a file now. Works but costs time and money.

### Benefits (say these in the interview)

1. **Lower latency** - physical distance matters (light is only so fast).
2. **Less load on your servers** - the origin sees only misses.
3. **Absorbs traffic spikes** - and some attacks.
4. **Cheaper bandwidth** than serving everything from your own data centre.

### Risks

- Stale content if freshness is not handled.
- Cost for very large traffic.
- Security: never cache private or user-specific responses by mistake.

---

## Part C. Where DNS + CDN sit in a big design

```
User -> DNS (pick nearest region/CDN) -> CDN edge -> (miss) -> Load balancer -> App servers -> Cache -> DB
```

In designs like the video streaming system (`17`) and the file storage system (`15`), the CDN is a main character. In the URL shortener (`10`), a CDN can cache hot redirects.

---

## Quick check

1. What does a TTL do? What is the trade-off of a short TTL?
2. What is the difference between an origin and an edge?
3. Name two things you should not put on a CDN.
4. How does versioned file naming solve stale cache?
