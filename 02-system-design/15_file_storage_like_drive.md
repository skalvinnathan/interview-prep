# 15. Design File Storage and Sync (like Google Drive or Dropbox)

---

## 1. The problem in plain words

Users upload files (photos, documents, videos) to the cloud, open them from any device, share them with others, and keep a folder **in sync** on their laptop and phone. Edits on one device appear on the others.

**Analogy: a bank locker room with a catalogue.**
- The **lockers** (blob storage) hold the actual boxes (file data). They are big, cheap, and safe.
- The **catalogue** (metadata database) is a notebook that says "Asha's file 'cv.pdf' is in locker 4821, size 200 KB, shared with Ravi".
- Big boxes are cut into **small pieces** (chunks), so a half-finished carry can restart where it stopped, and only the changed pieces move.

---

## 2. Requirements

**Must-have**
1. Upload and download files (up to a few GB each; assumption).
2. Folders and file names; rename, move, delete.
3. Sync across devices: change on one, appears on others.
4. Sharing: share a file or folder with users or by link, with read or edit permission.
5. File version history (restore an old version).

**Non-functional**
- **Durable**: never lose a file (aim for extremely high durability; say "multiple copies in different places").
- Highly available reads; reasonable upload speed; resumable uploads on bad networks.
- Consistent metadata (a folder must not show two files with the same name by accident). Strong consistency for metadata, eventual for sync notifications.

**Out of scope**
- Real-time co-editing of documents (that is a separate hard problem using operational transform or CRDTs; mention it), full-text search, virus scanning details (mention), end-to-end encryption.

---

## 3. The numbers (estimates)

Assume 50M users, 10M daily active; each user stores 5 GB on average; 2 uploads per active user per day, average file 1 MB (many small, a few huge); reads 3 times writes.

| Item | Value |
|---|---|
| Total storage | 50M x 5 GB = 250 PB (petabytes) raw; x about 1.5 with erasure coding, or x3 with plain copies (see later) |
| Uploads per day | 10M x 2 = 20M files per day = about 230 per second (peak ~700) |
| Upload data per day | 20M x 1 MB = 20 TB per day = about 230 MB/s = about 1.9 Gbps average |
| Downloads | 3x: about 700 per second, about 5.5 Gbps average |
| Metadata size | 50M users x 1,000 files x 500 bytes = 25 TB (a sharded DB handles it) |
| Dedup saving | Many users hold identical files; chunk-level deduplication could save a notable fraction (amount depends on data; do not quote a number) |

Meaning: **bytes** are the problem (hundreds of PB), not requests per second. So: blob storage for data, a separate database for metadata.

---

## 4. The API

```
POST /v1/files/upload-session
  body:  { "parent_id": "f12", "name": "cv.pdf", "size": 204800, "checksum": "sha256..." }
  reply: { "upload_id": "u9", "chunk_size": 4194304, "chunks": [ {"index":0,"upload_url":"https://blob/...signed"}, ... ] }
  // Client uploads each chunk DIRECTLY to blob storage with a pre-signed URL. Our servers do not carry the bytes.

PUT  /v1/uploads/{upload_id}/complete       { "chunk_hashes": [...] }  -> creates the file/version
GET  /v1/files/{id}/download-url            -> short-lived signed URL (via CDN)
GET  /v1/folders/{id}/children?cursor=...
PATCH /v1/files/{id}   { "name": "new.pdf", "parent_id": "f77" }       rename/move
POST /v1/files/{id}/share  { "user": "ravi@...", "role": "viewer" }  or  { "link": true }
GET  /v1/changes?cursor=...                 -> list of changes since my last sync cursor (for sync clients)
GET  /v1/files/{id}/versions
```

Key idea: **pre-signed URLs** let the client talk to blob storage directly. App servers handle only small metadata calls. This keeps servers cheap.

---

## 5. The data tables

**users**: `user_id (PK)`, quota, plan.

**file_node** (files and folders - the "tree"): `node_id (PK)`, `owner_id`, `parent_id`, `name`, `type` (file/folder), `current_version_id`, `is_deleted`, `updated_at`. Unique `(parent_id, name)` among non-deleted rows. Index by `(owner_id)`, `(parent_id)`.

**file_version**: `version_id (PK)`, `node_id`, `size`, `created_at`, `created_by`, `chunk_list` (ordered list of chunk hashes).

**chunk**: `chunk_hash (PK)` (SHA-256 of content), `size`, `storage_location`, `ref_count`. Same hash = stored once (**deduplication**).

**share / permission**: `(node_id, principal_id)` PK, `role` (viewer/editor/owner), or `link_token`, `expires_at`.

**change_log** (for sync): `(user_id, sequence_no)` PK, `node_id`, `change_type`, `ts`. Every change to a user's visible tree appends an entry; devices ask "changes after sequence N".

**device**: `(user_id, device_id)`, `last_sync_cursor`.

Metadata store: **SQL** (transactions needed for moves/renames and unique names), sharded by `owner_id` (or by node id range per owner). File bytes: **object storage** (S3-like), keyed by chunk hash.

---

## 6. Version 1 (simple)

```
 Client --upload file--> [App server] --> saves file on local disk / one blob bucket
                              |
                              v
                          [SQL DB: file_node (name, path)]
```

Whole file goes through the app server. Problems: slow and expensive for big files; if the upload breaks at 99 percent you start again; one server's disk is a single point of failure; the sync client must re-upload the full file after a tiny edit.

---

## 7. Growing 100x, step by step

**Step 1. Blob storage + pre-signed URLs.** Move bytes to object storage (replicated, very durable, cheap). App servers return signed URLs; clients upload and download directly. (`01d` blob note)

**Step 2. Chunking.** Split files into chunks (for example 4 MB; assumption). Benefits: **resumable** upload (retry only the failed chunk), **parallel** upload (several chunks at once), and **delta sync** (if a user edits a 1 GB file and changes one spot, only the affected chunk is uploaded).

```
 file.bin -> [chunk1][chunk2][chunk3][chunk4]  each: sha256 hash
 Upload: ask server "which of these hashes do you not have?" -> upload only those
```

**Step 3. Deduplication.** Chunk hash is the key. If the hash already exists, skip the upload entirely and just add a reference (`ref_count + 1`). This saves storage and bandwidth. Caveat: cross-user dedup can leak the fact that a file exists (privacy side channel); some systems dedup only within an account. Mention it as a trade-off.

**Step 4. Durability in the blob layer.** Store each chunk in **several places**: either 3 full copies in different zones, or **erasure coding** (split into k data + m parity pieces so any k pieces rebuild the data; for example 10 + 4 gives high durability at about 1.4x storage instead of 3x). Say: "Erasure coding trades CPU and repair traffic for lower storage cost." Periodic **checksum scrubbing** finds bit rot and repairs it.

**Step 5. Metadata service and database.** Separate from blobs. Sharded SQL by `owner_id` with replicas. Moves and renames are single-row or few-row transactions inside one shard (shared folders across owners add complexity: store permissions separately and keep the tree under the owner's shard).

**Step 6. Sync with a change log.** The server appends each change to `change_log`. Clients keep a cursor: `GET /changes?cursor=N`. For fast notifications, the client holds a **long-poll / WebSocket / push channel** that only says "something changed"; the client then calls `/changes`. (Do not send data over the notify channel; keep it small.)

```
 Device A edits -> uploads changed chunks -> metadata commit (new version) -> change_log entry
                                                               |
                                                notify channel (WebSocket) -> Device B
                                                               |
                            Device B: GET /changes?cursor -> downloads only new chunks
```

**Step 7. Conflicts.** Two devices edit the same file offline. Rule: the first commit wins the main name; the second commit is detected by `base_version != current_version` and saved as a **conflict copy** ("cv (Ravi's conflicted copy).pdf"). Simple and safe; never silently overwrite.

**Step 8. CDN and caching for downloads.** Popular or shared files are served from a CDN with short-lived signed URLs. Metadata (folder listings) cached in Redis; invalidated on change. (`01b`, `01e`)

**Step 9. Async jobs through queues.** After upload completes, queue jobs: virus scan, thumbnail/preview generation, text extraction for search, usage accounting. These must not block the upload response. (`01g`)

**Step 10. Tiering and cleanup.** Hot (SSD/standard), warm, cold (archive) storage tiers by access age. **Garbage collection** of chunks with `ref_count = 0` after a grace period (to avoid races with in-flight uploads). Soft delete (trash) for 30 days.

**Step 11. Multi-region.** Replicate blobs cross-region asynchronously for disaster recovery; keep metadata primary in one region per user with replicas elsewhere.

Final picture:

```
 Client (desktop/mobile/web)
   |  metadata calls                       |  chunk bytes (signed URLs)
   v                                       v
 [LB] -> [API servers] -> [Metadata DB shards + replicas]     [Blob storage: chunks, erasure-coded, multi-zone]
              |  ^                                                  ^
              |  +-- Redis cache (listings, perms)                  |
              v                                                     |
   [Queue] -> workers: virus scan, thumbnails, indexing, GC ---------+
              |
   Notification channel (WebSocket/push) -> clients;   CDN in front of downloads
```

---

## 8. Trade-offs and why

| Choice | Why | Cost |
|---|---|---|
| Direct-to-blob uploads | App servers stay light | More complex client; security via signed URLs |
| Chunking (4 MB) | Resume, parallel, delta sync | More metadata; small-file overhead (small files can be one chunk) |
| Dedup by hash | Saves storage and bandwidth | Privacy side channel; ref-count bookkeeping |
| Erasure coding | Cheaper than 3 copies | Slower repair, more CPU |
| SQL metadata | Transactions, unique names | Needs sharding at scale |
| Conflict copies | Never lose edits | Users must merge by hand |
| Change log + cursor | Simple, reliable sync | Log growth; compaction needed |

---

## 9. What breaks and how to fix it

| Failure | Effect | Fix |
|---|---|---|
| Upload interrupted | Partial file | Chunk-level resume; upload session expires; GC removes orphan chunks |
| Blob node/zone lost | Data at risk | Replication or erasure coding across zones; automatic repair |
| Metadata shard down | Folder unavailable | Replica promotion; reads from replicas; queue writes (no) - fail with retry |
| Chunk exists in metadata but missing in blob | Corrupt file | Verify chunks exist before commit; checksum on read; scrubbing |
| Race: delete vs upload with same chunk | Lost chunk | Grace period before GC; ref-count updates in transactions |
| Hot shared file (viral link) | Bandwidth spike | CDN, rate limits, per-link bandwidth caps |
| Sync loop (A and B keep overwriting) | Churn | Version numbers and base-version checks; conflict copies |
| Huge folder listing | Slow | Pagination, indexes, cache |
| Quota abuse | Cost | Per-user quotas enforced at upload-session creation |
| Signed URL leaks | Unauthorised access | Short expiry, single-use or scoped, check permissions at URL issue time |

---

## 10. Questions the interviewer asks next

**Q1. How does resumable upload work?**
A. The upload session lists chunk indexes. The client uploads chunks (in parallel) and the server records which arrived. After a break the client asks which chunks are missing and sends only those. Then it calls `complete` and the server commits the version.

**Q2. How does delta sync work?**
A. The file is chunked by content-defined chunk boundaries (rolling hash) or fixed sizes. The client hashes chunks, asks the server which hashes are missing, and uploads only those. A small edit changes one or two chunks. (Fixed-size chunks break if bytes are inserted at the start; content-defined chunking is better for that.)

**Q3. How do you guarantee we never lose a file?**
A. Multiple copies across zones (or erasure coding), checksums verified on write and in background scrubbing, automatic repair, cross-region backup, soft delete, and a rule that metadata commits only after all chunks are durably stored.

**Q4. How do you do sharing and permissions?**
A. A permission table (node, principal, role). Permissions inherit down folders; we compute effective permission by walking up the tree (cache results). Link sharing uses an unguessable token with optional expiry and password.

**Q5. How do you list "files shared with me" quickly?**
A. A reverse index table `(principal_id, node_id)` maintained on share/unshare.

**Q6. Strong or eventual consistency?**
A. Metadata is strongly consistent within a user's shard (unique names, moves). Notifications and other devices' views are eventual (seconds). Blob storage reads after write should be strongly consistent for committed chunks.

**Q7. How would you add real-time co-editing?**
A. A separate service with operational transform or CRDTs and its own session servers; periodic snapshots saved as versions in this storage system. I would state that as a different design.

**Q8. How do you delete a file that other files share chunks with?**
A. Reference counting: deleting a version decrements chunk refs; chunks with zero refs are deleted by a garbage collector after a grace period.

**Q9. How do you handle very large files (50 GB)?**
A. Same chunking, with bigger parallelism and a limit on chunks per file; multipart uploads at the blob layer; resume support.

---

## 11. Say it out loud (6 sentences)

1. "A file storage system keeps file bytes in cheap, durable object storage and keeps names, folders, versions and permissions in a separate metadata database."
2. "At 250 petabytes the data size, not request rate, is the challenge, so clients upload chunks directly to blob storage with pre-signed URLs."
3. "Chunking with content hashes gives resumable uploads, parallel transfer, delta sync, and deduplication, and chunks are protected by replication or erasure coding across zones."
4. "The metadata store is a sharded SQL database with strong consistency for names and moves, and it commits a new version only after all chunks are safely stored."
5. "Sync uses a per-user change log and cursor, with a small notification channel that tells devices to pull changes, and conflicts become conflict copies instead of lost edits."
6. "Background workers do virus scanning, thumbnails and garbage collection of unreferenced chunks, and a CDN serves popular downloads."
