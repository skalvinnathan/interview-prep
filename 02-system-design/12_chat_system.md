# 12. Design a Chat System (like WhatsApp or Slack)

---

## 1. The problem in plain words

Two people (or a group) send text messages to each other. The message must reach them **fast**, **in order**, and **never get lost**, even if the receiver is offline right now.

**Analogy: a post office with express delivery.** You hand a letter to the post office (server). If your friend is home (online), a courier runs to the door at once. If not, the letter waits in her mailbox (stored) and is handed over when she returns. Every letter in a conversation is numbered so she reads them in order.

---

## 2. Requirements

**Must-have**
1. One-to-one chat.
2. Group chat (up to, say, 500 members; assumption).
3. Online / offline presence ("last seen").
4. Message delivery states: sent, delivered, read.
5. Offline delivery: messages wait and arrive when the user comes back.
6. Chat history is stored and can be loaded (pagination).
7. Multiple devices per user (phone + laptop) see the same chat.

**Non-functional**
- Low latency (under about 200 ms delivery when both online, assumption).
- **Never lose a message**, and keep order inside one chat.
- Highly available. Scale to tens of millions of users.

**Out of scope**
- Voice/video calls, end-to-end encryption details (mention as a future item), media upload processing (mention blob storage + CDN), message search, bots.

---

## 3. The numbers (estimates)

From `02_numbers_and_estimation.md` (50M DAU, 40 messages per user per day, 100 bytes per message):

| Item | Value |
|---|---|
| Messages per day | 2 billion |
| Messages per second | about 23,000 average, 70,000 peak |
| Storage | about 200 GB/day, about 73 TB/year (raw, before copies and indexes) |
| Concurrent connections | about 10 million at peak (20 percent of DAU) |
| Chat servers | 10M / 100,000 per server = about 100, plus spare |
| Group fan-out | stored once, delivered to each member (see example in `02`) |

---

## 4. The API

Chat has two kinds of traffic: normal HTTP calls and a **persistent connection** for real-time.

**WebSocket (real-time):** (see `01a` for why: server must push without the client asking)

```
Client connects: wss://chat.example.com/ws   (with auth token)

Client -> Server:  { "type": "send", "chat_id": "c9", "client_msg_id": "uuid-1", "text": "hi" }
Server -> Client:  { "type": "ack",  "client_msg_id": "uuid-1", "msg_id": 4012, "ts": ... }   (server stored it)
Server -> Client:  { "type": "message", "chat_id": "c9", "msg_id": 4013, "from": "u7", "text": "hello", "ts": ... }
Client -> Server:  { "type": "delivered", "chat_id": "c9", "msg_id": 4013 }
Client -> Server:  { "type": "read", "chat_id": "c9", "up_to": 4013 }
```

`client_msg_id` makes sending **idempotent**: if the client retries after a dropped connection, the server sees the same id and does not create a second message. (`03`)

**HTTP (non-real-time):**

```
GET  /v1/chats?cursor=...                       list my chats
GET  /v1/chats/{id}/messages?before=4000&limit=50   history (paginated)
POST /v1/chats                                   create group
POST /v1/chats/{id}/members
POST /v1/media/upload-url                        get a pre-signed URL to upload a file to blob storage
```

---

## 5. The data tables

**users**: `user_id (PK)`, name, phone, created_at. (SQL.)

**chats**: `chat_id (PK)`, type (direct/group), name, created_at.

**chat_members**: `(chat_id, user_id)` PK, role, joined_at, `last_read_msg_id`. Also an index by `user_id` to list my chats.

**messages** - the big one (wide-column store such as Cassandra/HBase, or sharded SQL):

| Column | Note |
|---|---|
| chat_id | **partition key**: all messages of one chat live together |
| msg_id | **clustering/sort key**: increasing id, sorts by time inside the chat |
| sender_id | |
| client_msg_id | for idempotency (unique per sender per chat) |
| body | text or pointer to a media file |
| created_at | |

Why this design: the main query is "give me the latest 50 messages of chat X". Partition by chat, sort by message id -> one fast range read.

**Message ids:** need order **inside one chat**, not global order. Options: a per-chat counter (the chat's owning server increments), or a time-based sortable id (Snowflake-like). Say: "I only need ordering per chat, so a per-chat sequence is enough."

**delivery state / inbox for offline users:** `(user_id, device_id, chat_id, msg_id)` pending list, or just track each device's "last synced msg_id per chat" and let it pull anything newer. The second is simpler and more robust.

**presence:** key-value in Redis: `presence:{user_id} -> last_heartbeat_ts` with a TTL (for example 30 s). Not durable; that is fine.

Media files: blob storage (S3-like); the message holds only the URL. CDN for downloads.

---

## 6. Version 1 (simple)

```
 Phone A ---HTTP POST /send---> [ Single server ] ---> [ DB ]
 Phone B ---HTTP GET /poll every 2 s---> [ Single server ]
```

B asks every 2 seconds "any new message?" (polling). It works but: slow (up to 2 s late), wasteful (most polls return nothing), and the single server is a single point of failure. So the first upgrade is a persistent connection.

---

## 7. Growing 100x, step by step

**Step 1. WebSockets for real-time.** Each client keeps one open connection to a **chat server**. Messages flow both ways without polling. (`01a`)

**Step 2. Stateless API + stateful connection layer.** Normal HTTP (history, group creation) goes to stateless API servers. WebSocket connections go to **connection servers** that hold the sockets in memory. Different scaling rules for each.

**Step 3. Session registry: "which server holds user X's socket?"** A Redis (or similar) map `user_id -> connection server id` (per device). When A sends to B:

```
 A --> [Conn server 1] --> store message (DB) --> look up B in registry
                                               |
                       B online on server 7 ---+--> [Conn server 7] --push--> B
                       B offline ------------------> keep stored; send push notification (APNs/FCM) via notification service (`14`)
```

Server 1 talks to server 7 through an internal **pub/sub or message bus** (for example topics per server) or direct RPC.

**Step 4. Store first, then deliver (durability).** Order of operations: (1) save the message to the DB (or a durable queue), (2) ack to the sender ("sent"), (3) try to push to receivers. If the push fails, the message is still stored. Receivers **sync from their last known msg_id** when they reconnect. That is how nothing is lost.

**Step 5. Use a queue/log between connection servers and storage.** Connection servers write to Kafka partitioned by `chat_id` (so one chat's messages stay ordered); consumers (a) write to the messages store, (b) fan out to receivers' servers, (c) trigger offline pushes. This absorbs spikes. (`01g`)

**Step 6. Shard the message store by `chat_id`** (consistent hashing). Replicate 3 times. A write-optimised store handles 70,000 writes/s peak comfortably across many nodes. (`01f`)

**Step 7. Group chat fan-out.** Small groups: when a message arrives, for each member look up their connection server and push (**fan-out on write** for delivery). Big groups (thousands): keep the message once; members pull "new since msg_id" when active; push only a lightweight "new message" signal. Limit group size at first.

**Step 8. Presence at scale.** Heartbeat every N seconds sets a key with TTL in Redis. Do **not** broadcast every status change to all friends (too heavy); fetch presence on demand when a chat is opened, or only broadcast to people currently viewing that user's chat.

**Step 9. Multi-device and multi-region.** Each device keeps its own `last_synced_msg_id` per chat. Users are pinned to a home region (by user or chat) for writes; geo-DNS sends them to the nearest region. Cross-region messages go through region-to-region replication.

Final picture:

```
 Clients (WebSocket)
      |
   Global LB / DNS
      |
 [Connection servers x ~100+]  <-->  Session registry (Redis)
      |                                  
      v
   Kafka (partition = chat_id)
      |        |             |
      v        v             v
  Message    Fan-out      Notification
  writer     workers      service (offline push)
      |
      v
 Message store (sharded, wide-column)       Blob storage + CDN (media)
 Users/chats DB (SQL, replicated)           Presence (Redis, TTL)
```

---

## 8. Trade-offs and why

| Choice | Why | Cost |
|---|---|---|
| WebSocket | Real-time push, low overhead | Long-lived state; reconnect logic; load balancer must support it |
| Store-then-deliver | No loss | Small extra latency (a DB/queue write) |
| Order only per chat | Cheap, sufficient | No global timeline (not needed) |
| Wide-column store partitioned by chat | Fast "latest N" reads and huge write volume | Poor ad-hoc queries (search needs another system) |
| Pull for big groups | Avoid huge fan-out spikes | Slightly less instant |
| At-least-once delivery + idempotent ids | Reliable | Client dedups by msg_id |
| Presence is best effort (TTL) | Cheap | May be seconds wrong |

---

## 9. What breaks and how to fix it

| Failure | Effect | Fix |
|---|---|---|
| Connection server dies | All its sockets drop (100k users) | Clients auto-reconnect with backoff + jitter to another server (avoid reconnect storm); sync from last msg_id; registry entries expire by TTL |
| Reconnect storm | New servers overwhelmed | Jitter, rate-limit connects, spare capacity |
| Message duplicated by retries | User sees it twice | `client_msg_id` unique key; client dedup by msg_id |
| Messages arrive out of order | Confusing chat | Per-chat sequence number; client sorts by it; Kafka key = chat_id |
| Registry stale (says B is on server 7, but he left) | Push lost | Message is stored anyway; B syncs on reconnect; push fails gracefully |
| Hot chat (huge group or viral channel) | One partition overloaded | Limit group size; split big channels; separate path for broadcast channels |
| DB shard down | Chats on it unavailable | Replicas, quorum reads/writes; queue holds writes meanwhile |
| Offline push provider slow | Late notifications | Retry with backoff; DLQ (`14`) |
| Clock skew between servers | Wrong timestamps | Order by sequence, not wall clock |

---

## 10. Questions the interviewer asks next

**Q1. Why WebSocket and not polling?**
A. Polling wastes bandwidth and adds delay. WebSocket keeps one connection so the server can push the instant a message arrives. Fallbacks (long polling) exist for networks that block sockets.

**Q2. How do you guarantee order?**
A. Order within a chat only. Each chat has an increasing sequence number given by one owner (a partition leader or per-chat counter). Messages of a chat go to one Kafka partition (key = chat_id). The client displays by sequence number.

**Q3. How do you know a message was delivered or read?**
A. The receiver app sends a "delivered" ack when it stores the message and a "read" event when it is shown. The server stores per-member `last_delivered` and `last_read` pointers (not one row per message per member) and tells the sender.

**Q4. How do you handle a user offline for a week?**
A. Messages are stored. When she connects, the app sends `last_synced_msg_id` per chat and the server returns newer messages in pages. Push notifications are only a nudge.

**Q5. How would you store 73 TB a year?**
A. Wide-column store sharded by chat_id with replication factor 3, plus tiering: old messages move to cheaper storage and are loaded on demand.

**Q6. What about end-to-end encryption?**
A. Servers then store only encrypted blobs and cannot search or moderate content. Keys are exchanged between devices. It is a large topic; I would state it as a requirement change and not go deep unless asked.

**Q7. How do you support multiple devices?**
A. Each device has its own connection and its own sync pointer. A message is delivered to all connected devices of each member; others sync later.

**Q8. How do you scale presence?**
A. Heartbeats into Redis with TTL. Subscribers fetch on demand or only for open chats. Avoid fan-out of every change.

**Q9. How do you handle "typing..." indicators?**
A. Ephemeral events sent over the socket to online members only. Never stored. Rate-limit them.

---

## 11. Say it out loud (6 sentences)

1. "A chat system must deliver messages fast, in order inside a chat, and never lose one, even when the receiver is offline."
2. "At 50 million daily users I expect about 70,000 messages per second at peak, 73 TB a year, and about 10 million open connections, so roughly 100 connection servers."
3. "Clients keep WebSocket connections to stateful connection servers, while history and group management use stateless HTTP APIs."
4. "A message is first made durable, in Kafka partitioned by chat id and then in a store sharded by chat id, then acknowledged to the sender, and then pushed to online receivers found through a session registry."
5. "Offline users sync from their last message id when they reconnect, and a notification service sends mobile pushes as a nudge."
6. "Retries are safe because every message has a client id for deduplication, and server failures cause jittered reconnects, not lost data."
