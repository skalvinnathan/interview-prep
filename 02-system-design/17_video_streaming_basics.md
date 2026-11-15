# 17. Design Video Streaming Basics (like YouTube or Netflix)

---

## 1. The problem in plain words

Creators upload videos. Viewers press play and watch smoothly on any device (phone on weak network, big TV). The video must start quickly, not freeze, and adapt when the network gets slow.

**Analogy: a factory plus many local shops.**
- The factory (**transcoding pipeline**) takes the raw product (the uploaded video) and makes several versions: big, medium, small.
- The warehouse (**blob storage**) keeps all versions.
- Thousands of small local shops (**CDN edges**) near customers keep copies of popular items. Customers never go to the factory.
- The delivery is not one giant parcel; the video is cut into **small pieces of a few seconds** (segments). If the road is bad, the next piece is sent in a smaller size.

---

## 2. Requirements

**Must-have**
1. Upload a video (can be large, hours long).
2. Watch a video: fast start, smooth playback, adapts to bandwidth.
3. Video metadata: title, description, thumbnail, view count.
4. Search / browse list (basic).

**Non-functional**
- Very high read volume (viewing), huge storage, huge bandwidth.
- Availability for playback is more important than for upload.
- Low start-up delay (a second or two) and few interruptions ("buffering").
- Cost matters: bandwidth and storage are the main bill.

**Out of scope**
- Recommendation system, comments, live streaming (different design: ingest + low-latency packaging), DRM details, ads, copyright matching (mention).

---

## 3. The numbers (estimates)

From `02_numbers_and_estimation.md`: 500,000 uploads per day, average 200 MB raw; 100 million views per day, 50 MB streamed per view.

| Item | Value |
|---|---|
| Upload bandwidth | about 100 TB per day, about 1.2 GB/s (about 10 Gbps) average |
| Stored per video | original + transcoded versions, about 600 MB (assumption: versions total 2x original) |
| New storage per year | about 110 PB (petabytes) |
| View egress | about 5 PB per day, about 58 GB/s (about 460 Gbps) average |
| Views per second | 100M / 86,400 = about 1,160 per second average (peak about 3,500) |
| Metadata | tiny (GBs) |

Meaning: request rate is small (1,000/s). **Bytes** are huge. So: object storage, transcoding workers, and above all a **CDN**.

---

## 4. The API

```
POST /v1/videos/upload-session
  body: { "title": "...", "size": 1073741824, "content_type": "video/mp4" }
  reply: { "video_id": "v77", "upload_url": "<signed, resumable multipart>" }
  // the client uploads straight to blob storage (see 15)

POST /v1/videos/{id}/complete              -> triggers processing (async)
GET  /v1/videos/{id}                       -> metadata + status (processing / ready / failed)
GET  /v1/videos/{id}/manifest              -> playback manifest URL (HLS .m3u8 or DASH .mpd)
GET  /v1/videos?query=...&cursor=...       -> list / search
POST /v1/videos/{id}/view                  -> record a view (async, counted later)
```

Playback itself is plain HTTP GETs of video segments and a small text **manifest** file listing the available qualities and their segment URLs. No special streaming server is needed; a CDN serving files is enough.

---

## 5. The data tables

**video**: `video_id (PK)`, `owner_id`, `title`, `description`, `status`, `duration`, `created_at`, `visibility`. (SQL, sharded by video_id when big.)

**video_asset**: `(video_id, rendition)` PK, `resolution` (240p, 480p, 720p, 1080p...), `bitrate`, `manifest_path`, `segment_prefix` (blob path).

**view_count**: not a hot counter in SQL. Use a stream: view events to Kafka, aggregated counts every few seconds/minutes into a store; show approximate counts. (A "counter" row updated 1,000 times a second would be a hot row.)

**thumbnail**: path in blob storage.

Blob layout: `/videos/{id}/original.mp4`, `/videos/{id}/720p/seg_00001.ts ...`, `/videos/{id}/master.m3u8`.

---

## 6. Version 1 (simple)

```
 Uploader --> [Server] --> saves mp4 on its disk, row in DB
 Viewer   <-- [Server] <-- streams the mp4 file
```

Problems: one big file in one quality (a phone on 3G cannot play a 1080p file); the server disk and bandwidth are the limit; far-away viewers get slow start; one server failure kills everything.

---

## 7. Growing 100x, step by step

**Step 1. Blob storage and direct upload.** Same as file storage (`15`): resumable multipart upload to object storage using signed URLs.

**Step 2. Transcoding pipeline (async).** After upload completes, a message goes on a queue. Workers:
1. **Probe and validate** the file (is it really a video? length? size limits? virus/policy scan).
2. **Split** the video into chunks (for example by scene or fixed time) so many workers process in parallel (like a map-reduce / DAG).
3. **Transcode** each chunk into multiple **renditions** (resolution and bitrate pairs), for example 240p, 480p, 720p, 1080p, and codecs (H.264 for compatibility, maybe newer ones for savings).
4. **Package** into short **segments** (2 to 10 seconds each) and create the **manifest** (HLS or MPEG-DASH formats).
5. **Thumbnails** and preview images.
6. Write to blob storage, mark video `ready`, update the DB.

```
 upload complete -> Queue -> [Split] -> [Transcode workers x N, per chunk x per rendition] -> [Package + manifest] -> blob + DB(status=ready)
```

This is a **workflow / DAG** with retries per task. (Compare `20`: it is the same shape as your provisioner: steps with dependencies, retries, status.) Transcoding is CPU heavy: use autoscaled worker pools, possibly spot/preemptible machines, because a failed task can simply be retried (idempotent tasks writing to deterministic output paths).

**Step 3. Adaptive bitrate streaming (ABR).** The player downloads the manifest, starts with a low or medium quality, measures how fast segments arrive, and **switches quality between segments** up or down. This is how video continues on weak networks (quality drops, not freezing).

```
 Player: read master manifest -> picks 480p -> downloads seg1, seg2 ... measures speed
         speed improves -> next segment from 1080p; speed drops -> down to 240p
```

**Step 4. CDN does the heavy lifting.** Segments are static files, ideal for caching. Viewers fetch from the nearest edge. Edge miss -> a mid-tier cache -> origin (blob storage) with **request collapsing** (many simultaneous misses for the same segment become one origin request). Popular videos are warm at edges. Large providers also place cache boxes inside ISP networks (mention only as a known approach). Pre-warm (push) new popular releases. (`01b`)

**Step 5. Long-tail strategy.** Most videos are rarely watched. Keep popular ones hot at the CDN; store the long tail in cheaper storage tiers, perhaps store fewer renditions for rarely watched videos and transcode on demand (trade CPU later for storage now).

**Step 6. Metadata path.** Video metadata in sharded SQL with a Redis cache; search in Elasticsearch-like index fed by events. Home page lists use a separate recommendation system (out of scope).

**Step 7. View counts and analytics.** Player sends heartbeat/view events to Kafka -> stream aggregation -> counts store. Display approximate counts (eventually consistent). De-duplicate by user and time window; filter bots.

**Step 8. Protect content and costs.** Signed, expiring URLs (or signed cookies) for private/paid videos; hotlink protection; DRM for premium content (mention only).

**Step 9. Multi-region.** Blobs replicated to 2 or more regions for durability; CDN is global; transcoding runs in the region of upload; metadata has a primary and replicas.

Final picture:

```
 Creator -> signed URL -> [Blob: originals] -> event -> Queue -> [Transcoding DAG workers] -> [Blob: segments + manifests]
                                                                         |                              |
                                                                  DB: status=ready                      v
                                                                                                  CDN (edges, mid-tier)
 Viewer -> API (metadata, manifest URL, signed) -> Player -> CDN edge -> segments (ABR)
 Player events -> Kafka -> counters / analytics
```

---

## 8. Trade-offs and why

| Choice | Why | Cost |
|---|---|---|
| Many renditions | Works on all networks/devices (ABR) | Storage x2 or more; transcoding cost |
| Short segments (2 to 10 s) | Fast quality switching, cache-friendly | More files and requests; small latency overhead |
| Transcode all upfront | Instant playback quality | Wasted work for videos nobody watches |
| On-demand transcode for long tail | Saves storage/CPU | First viewer waits |
| CDN for everything | Low latency, cheap origin | CDN bill; stale content risks |
| Approximate view counts | Scales | Not exact |
| HLS/DASH over HTTP | Works on plain web servers and CDNs | Latency of several seconds (fine for VOD; live needs more) |

---

## 9. What breaks and how to fix it

| Failure | Effect | Fix |
|---|---|---|
| Transcode worker dies | Task lost | Task retried from queue (idempotent output path); visibility timeout; DLQ for poison files |
| Corrupt or huge upload | Pipeline stuck | Validate early, size/time limits, timeouts per task, quarantine |
| Backlog of uploads (event, outage) | Late publishing | Autoscale workers, prioritise short videos or paying creators, show "processing" |
| Viral video | Origin overloaded when edges are cold | Request collapsing, origin shield (mid-tier), pre-warm, rate limits |
| CDN region outage | Poor playback in a region | Multi-CDN or fallback to another edge group; DNS failover |
| Missing segment (data loss) | Playback stalls | Checksum and verify after packaging; replicas; player retries and falls back to lower rendition |
| Manifest points to unready renditions | Errors | Publish manifest only after all segments are written (atomic switch) |
| Hot counter row | DB overload | Stream aggregation instead of row updates |
| Hotlinking / content theft | Cost and legal | Signed URLs, short expiry |
| Cost explosion | Bills | Tiering, per-rendition policies, cache hit ratio monitoring |

---

## 10. Questions the interviewer asks next

**Q1. Why not stream one big MP4 file?**
A. One quality cannot fit every device and network. Cutting into segments with several renditions lets the player switch quality, start quickly, seek anywhere, and lets CDNs cache small files.

**Q2. How does adaptive bitrate work?**
A. The manifest lists renditions and segment URLs. The player measures download speed and buffer level and picks the best rendition for the next segment; it changes between segments without stopping.

**Q3. How do you speed up transcoding of a 2-hour video?**
A. Split into chunks, transcode chunks in parallel on many workers and several renditions at once, then stitch the manifests. This is a DAG with per-chunk retries.

**Q4. How does the CDN get the video?**
A. Pull: the first viewer's request misses at the edge, the edge fetches from origin (through a mid-tier shield), caches it for the next viewers. For known hits, push or pre-warm.

**Q5. How do you count views at this scale?**
A. Events to Kafka, deduplicated and aggregated by a stream job, stored in a counter store, and displayed approximately. Never `UPDATE views = views + 1` on one row.

**Q6. Where do you save money?**
A. High CDN hit ratio, tiered storage for old content, fewer renditions or on-demand transcoding for the long tail, efficient codecs for popular videos.

**Q7. How do you handle live streaming?**
A. Different design: ingest servers receive the stream (for example RTMP), transcode and package in real time into short segments with low-latency settings, and push to CDN; tradeoff is latency vs stability. I would call that a separate design.

**Q8. How do you protect private videos?**
A. Authenticated manifest request returns signed URLs or cookies with short expiry; segment URLs are not guessable; check permissions when issuing them.

---

## 11. Say it out loud (6 sentences)

1. "A video platform has small request rates, about 1,000 views per second, but huge bytes: about 100 terabytes uploaded and 5 petabytes streamed per day in my estimate."
2. "Creators upload straight to object storage, and an asynchronous pipeline splits the video, transcodes it in parallel into several renditions, packages short segments and writes a manifest."
3. "Playback is just HTTP downloads of the manifest and segments, and the player switches quality between segments to match the viewer's bandwidth, which is adaptive bitrate streaming."
4. "A CDN serves almost all traffic, with edge caches, a mid-tier shield and request collapsing so the origin storage is protected."
5. "Metadata lives in a small sharded SQL database with a cache, search lives in an index, and view counts are aggregated from a Kafka stream, not updated row by row."
6. "I control cost with storage tiers and on-demand transcoding for the long tail, handle failures with idempotent retried tasks, and publish a video only when all its segments are ready."
