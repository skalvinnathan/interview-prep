# 10. Databases basics

Legend: `[REAL]` = I ran it on this Mac (SQLite 3.51.0 through Python) on 2026-11-15. `[SAMPLE]` = typical output written to show the shape (PostgreSQL), not run here. **No PostgreSQL was available on this Mac, so all PostgreSQL output is `[SAMPLE]` or quoted from the docs.** SQLite is a different database but the idea of indexes and query plans is the same. Isolation levels, `EXPLAIN`, and replication facts were read from the PostgreSQL docs (links at the end).

---

## 1. What it is (plain words + analogy)

A **database** stores data so you can find and change it fast and safely, even when many users act at once and even when the power fails.

Analogy: a **library**.
- **Table** = a shelf of one kind of book. **Row** = one book. **Column** = one fact about the book (title, year).
- **Index** = the **card catalog**. Without it, to find "books by Tolstoy" you walk every shelf (a **full table scan**). With it, you look up the name and go straight to the shelf.
- **Query plan** = the librarian's **route** for fetching your books.
- **Transaction** = a **borrowing slip** with several steps (take book A, return book B). Either all steps happen or none.
- **Replica** = a **branch library** that gets copies of new books a little later than the main one. That delay is **replication lag**.

Words:
- **SQL**: the language to ask for data.
- **ACID**: Atomicity (all or nothing), Consistency (rules stay true), Isolation (transactions do not trample each other), Durability (committed data survives a crash).
- **Primary (leader)**: accepts writes. **Replica (standby, follower)**: copies the primary, often serves reads.
- **OLTP**: many small transactions (orders, logins). **OLAP**: fewer, big analysis queries (reports).

## 2. Why it matters in interviews

Platform and SRE people run databases or depend on them: slow queries cause incidents, replication lag causes "I saved it but cannot see it" bugs, wrong isolation levels cause double-spends, and disks fill up. Expect "why is this query slow?", "what does an index cost?", "what is replication lag and how do you handle it?", "read committed vs repeatable read vs serializable", "row store vs column store, when each?". For Amazon and Google, add "design a system that reads from replicas".

## 3. How it works, step by step

### 3.1 Indexes

Most databases use a **B-tree** index: a sorted tree of key values with pointers to rows. Searching is like a phone book: jump to the middle, narrow down in a few steps (logarithmic time) instead of reading every row.

```
 no index:   read row 1, row 2, row 3 ... row 500,000   (SCAN everything)
 with index: root -> branch -> leaf "user_id=4242" -> row pointers  (a few reads)
```
`[REAL]` SQLite, a table `orders` with 500,000 rows, look up one `user_id`. Same query, before and after `CREATE INDEX`:
```
PLAN before index: [(3, 0, 216, 'SCAN orders')]
20 queries: 0.235s
PLAN after index : [(4, 0, 62, 'SEARCH orders USING INDEX idx_orders_user (user_id=?)')]
20 queries: 0.000s
```
`SCAN` = read the whole table. `SEARCH ... USING INDEX` = use the index. (The "0.000s" means under a millisecond for 20 queries at the clock's resolution; the exact speed-up depends on the data. About 12 ms per query before, far less after.)

**Costs of indexes** (always mention both sides):
- Every **write** (insert, update, delete) must also update every index on that table, so more indexes mean slower writes.
- Indexes use **disk and memory**.
- Too many indexes make the planner's choices harder and maintenance (vacuum, reindex) heavier.

**Rules of thumb** (standard database knowledge):
1. Index columns used in `WHERE`, `JOIN`, and `ORDER BY` for queries that matter and are selective.
2. **Composite index** `(a, b, c)` helps queries that filter on `a`, or `a and b`, ... but not on `b` alone. The **leftmost column** order matters. Put equality columns first, range column last.
3. **Do not wrap the indexed column in a function** in the `WHERE`: `WHERE lower(email) = 'x'` cannot use an index on `email` (make an index on `lower(email)` instead). `[REAL]` proof: `user_id + 0 = 4242` forced a scan again even with the index present: `[(2, 0, 216, 'SCAN orders')]`.
4. **Low selectivity** columns (a boolean, status with 3 values) are poor index candidates alone: the database may prefer a full scan if it must read a big share of the table.
5. **Covering index**: an index that contains all the columns the query needs, so the database does not even visit the table.
6. A **primary key** has a unique index automatically. A **unique index** also enforces no duplicates.
7. Leading wildcards (`LIKE '%abc'`) cannot use a normal B-tree.
8. In production, create indexes **concurrently** where supported (PostgreSQL: `CREATE INDEX CONCURRENTLY`) so writes are not blocked.

### 3.2 Query plans: `EXPLAIN`

The **planner** chooses how to run a query: which indexes, which join order, which join method. `EXPLAIN` shows the plan.

From the PostgreSQL docs:
- `EXPLAIN` shows the plan "the planner creates for any query" with **estimates**, and does **not** run the query.
- `EXPLAIN ANALYZE` "actually executes the query, and then displays the true row counts and true run time". Warning: "any side-effects will happen as usual", so wrap data-changing statements in `BEGIN; ... ROLLBACK;`.
- **Seq Scan** reads the whole table. **Index Scan** uses an index and is "most often" chosen when it fetches just a single row. **Bitmap Heap Scan** sits in between for moderately selective conditions.
- Costs are "measured in arbitrary units" (by convention, relative to one sequential page fetch = 1.0). Each node shows a start-up cost and a total cost. Cost is **not** milliseconds.
- The planner can be wrong; compare estimated rows with actual rows (a big gap means stale or poor statistics: run `ANALYZE`).

`[SAMPLE]` PostgreSQL (invented numbers, the shape follows the docs' examples):
```
EXPLAIN ANALYZE SELECT count(*) FROM orders WHERE user_id = 4242;

 Aggregate  (cost=14.5..14.6 rows=1 width=8) (actual time=0.05..0.05 rows=1 loops=1)
   ->  Index Only Scan using idx_orders_user on orders  (cost=0.42..14.2 rows=10 width=0) (actual time=0.03..0.04 rows=10 loops=1)
         Index Cond: (user_id = 4242)
 Planning Time: 0.1 ms
 Execution Time: 0.08 ms
```
How to read a plan: it is a tree, read from the **innermost, most indented** line outward. Look for: a `Seq Scan` on a big table with a selective filter (missing index?), a big difference between `rows=` estimate and actual, many `loops`, sorts that spill to disk, and nested loops over huge row counts.

Slow-query checklist: capture the slow query (`pg_stat_statements`, slow query log) -> `EXPLAIN (ANALYZE, BUFFERS)` -> add or fix an index, rewrite the query (select only needed columns, avoid `SELECT *`, avoid N+1 queries), update statistics, check locks and connection saturation, then consider caching or read replicas. (The tools named are standard PostgreSQL features; I did not check their pages today.)

**N+1 problem**: one query for a list, then one more query per item (1 + N). Fix with a join or a batched `IN (...)` query.

### 3.3 Transactions and isolation levels

A **transaction** groups statements: `BEGIN; ... COMMIT;` (or `ROLLBACK`). **Isolation** says how much one transaction can see of other transactions running at the same time.

Four **problems** (PostgreSQL docs wording):
- **Dirty read**: reading data written by a concurrent **uncommitted** transaction.
- **Nonrepeatable read**: reading a row again and finding it **changed** by a transaction that committed meanwhile.
- **Phantom read**: running the same query again and finding the **set of rows** changed (new or missing rows) by a recently committed transaction.
- **Serialization anomaly**: the result of several committed transactions is inconsistent with **any** order of running them one at a time.

The standard table (PostgreSQL docs):

| Level | Dirty read | Nonrepeatable read | Phantom read | Serialization anomaly |
|---|---|---|---|---|
| Read uncommitted | allowed by standard, **not in PostgreSQL** | possible | possible | possible |
| Read committed | no | possible | possible | possible |
| Repeatable read | no | no | allowed by standard, **not in PostgreSQL** | possible |
| Serializable | no | no | no | no |

PostgreSQL facts:
- It accepts all four names, but "internally only three distinct isolation levels are implemented": **Read Uncommitted behaves like Read Committed**.
- **Read Committed is the default**: each **statement** sees a snapshot from the moment it starts. Two selects in one transaction can see different data.
- **Repeatable Read**: the snapshot is taken at the first non-transaction-control statement in the transaction. Conflicting updates raise "could not serialize access due to concurrent update", and the **application must retry**. In PostgreSQL it is stronger than the standard: it also blocks phantoms.
- **Serializable**: like Repeatable Read, plus detection of dangerous patterns. It can raise "could not serialize access due to read/write dependencies among transactions". Applications must retry on SQLSTATE `40001`. Its predicate locks "do not cause any blocking" and cannot cause deadlocks.
- Set it with `BEGIN; SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;`.
- Different databases implement levels differently (MySQL InnoDB's default is Repeatable Read; general knowledge, not verified today). Never assume names mean the same thing everywhere.

Example of why it matters, **write skew** (a serialization anomaly): two doctors on call; the rule is "at least one must stay on call". Both check "is another doctor on call?" (yes), and both go off duty. Under Repeatable Read both succeed (rows they changed are different, so no direct conflict). Under Serializable one transaction fails and must retry. Without serializable you must use explicit locks (`SELECT ... FOR UPDATE`) or constraints.

Common pattern for counters and balances: `UPDATE accounts SET balance = balance - 10 WHERE id = 1 AND balance >= 10;` as a single atomic statement, then check the affected row count.

### 3.4 Replication and replication lag

**Replication** copies changes from a primary to replicas, for: **high availability** (promote a replica if the primary dies), **read scaling** (send read queries to replicas), and backups.

PostgreSQL streaming replication (docs): the primary "streams WAL records to the standby as they're generated". **WAL** = write-ahead log, the ordered record of every change. A replica replays the WAL.

- **Asynchronous** (default): the commit does **not** wait for the standby. The docs: "there is a small delay between committing a transaction in the primary and the changes becoming visible in the standby", typically under one second. If the primary fails, transactions not yet sent can be **lost**.
- **Synchronous**: the commit waits for one or more standbys (`synchronous_standby_names`, `synchronous_commit` with `remote_write` or `remote_apply` options). Safer for data, but slower: "The minimum wait time is the round-trip time between primary and standby."
- A standby that serves read-only queries is a **hot standby**. Replaying WAL can **conflict** with long queries (the primary may remove rows that a standby query still needs), so a long query on a replica can be cancelled, or replication can be paused for it.

**Replication lag** = how far a replica is behind the primary. Causes: heavy write bursts, long-running transactions or queries on the replica, slow disk or network, a weak replica instance. Measure it by comparing positions (LSNs): on the primary `pg_current_wal_lsn()` and the view `pg_stat_replication`; on the standby `pg_last_wal_receive_lsn()` and `pg_last_wal_replay_lsn()`; the standby view `pg_stat_wal_receiver`. The docs say: big differences between `pg_current_wal_lsn` and `sent_lsn` suggest a **loaded primary**, while differences between `sent_lsn` and `pg_last_wal_receive_lsn` suggest **network delay or a loaded standby**.

`[SAMPLE]` shape of lag measures on the primary (invented numbers):
```
SELECT application_name, state, sent_lsn, replay_lsn,
       pg_wal_lsn_diff(sent_lsn, replay_lsn) AS bytes_behind
FROM pg_stat_replication;

 application_name |   state   | sent_lsn  | replay_lsn | bytes_behind
------------------+-----------+-----------+------------+--------------
 replica-1        | streaming | 0/5A000F8 | 0/5A00000  |          248
```
(`pg_wal_lsn_diff` is a standard PostgreSQL function; I did not check its page today.)

**Symptoms and fixes for users**:
- "I just saved and it is missing": the app read from a lagging replica. Fix with **read-your-writes**: read from the primary for a short time after a write (or for that user's session), or wait until the replica reaches the write's position.
- Alert on **lag in seconds and bytes**, and on replicas that are not `streaming`.
- Route heavy analytics to a dedicated replica so it does not block others; keep `max_standby_streaming_delay` and `hot_standby_feedback` trade-offs in mind (the docs say `hot_standby_feedback` "provides no protection" when the standby is disconnected).
- Never send writes to a replica; plan **failover** (who promotes, how apps find the new primary, how to avoid two primaries: split brain).
- Cloud managed databases (Cloud SQL, AlloyDB, Azure Database for PostgreSQL) hide most of this, but the lag still exists.

### 3.5 Row stores vs column stores

**Row store** (PostgreSQL, MySQL): data of one row is stored together on disk.
```
 row layout:    [id1,name1,age1,city1] [id2,name2,age2,city2] [id3,...]
```
Great for **OLTP**: fetch or update one whole record quickly ("get order 123").

**Column store** (BigQuery, ClickHouse, Redshift, Parquet files): data of one column is stored together.
```
 column layout: id:[1,2,3...]  name:[n1,n2,n3...]  age:[a1,a2,a3...]  city:[c1,c2,c3...]
```
Great for **OLAP**: "average age by city over 1 billion rows" reads only the `age` and `city` columns, not the whole rows. Same-type values side by side **compress very well** and can be processed in bulk by the CPU. Bad for: updating or fetching single rows often, and for many small inserts (usually batch loads).

| | Row store | Column store |
|---|---|---|
| Best for | transactions, point lookups | analytics, scans over few columns |
| Writes | fast single-row | best in big batches |
| Reads a few columns of many rows | reads everything (slow) | reads only needed columns (fast) |
| Examples | PostgreSQL, MySQL | BigQuery, ClickHouse, Redshift, Parquet |

Typical architecture: OLTP database (row store) -> pipeline (CDC, Kafka, batch) -> warehouse (column store) for reports. Do not run heavy reports on the production OLTP primary.

(The row/column description is standard database knowledge; the Google Cloud database page I read says BigQuery is a "fully managed, highly scalable data warehouse" and Cloud SQL is for managed relational databases, which fits this split.)

### 3.6 A few more things that come up

- **Connection pooling** (PgBouncer, application pools): opening a database connection is expensive and the server has a connection limit. A pool reuses connections. Too many app instances times pool size can exhaust the database: size pools carefully.
- **Locks**: `SELECT ... FOR UPDATE` locks rows; long transactions hold locks and block others, and also block cleanup (vacuum) in PostgreSQL.
- **Backups**: a backup you have never restored is not a backup. Know your **RPO** (how much data you can lose) and **RTO** (how long you can be down). Point-in-time recovery uses base backup + WAL archive.
- **Schema migrations without downtime**: expand and contract. Add the new column (nullable), deploy code that writes both, backfill in batches, switch reads, then drop the old column later. Avoid long locks (adding a column with a default, creating indexes without `CONCURRENTLY`).
- **Choosing a Google Cloud database** (from Google's database page): Cloud SQL (managed MySQL, PostgreSQL, SQL Server), AlloyDB (PostgreSQL-compatible for demanding transactional workloads), Spanner (global-scale), Firestore (NoSQL document), Bigtable (wide-column, huge NoSQL), BigQuery (data warehouse), Memorystore (in-memory: Valkey, Redis). More in file 12.

## 4. Commands to try

```bash
# SQLite is on every Mac and most Linux machines. Try an index yourself:
python3 - <<'EOF'
import sqlite3, random, time
random.seed(0)
c = sqlite3.connect(":memory:")
c.execute("create table orders(id integer primary key, user_id int, amount real)")
c.executemany("insert into orders(user_id,amount) values(?,?)",
              [(random.randint(1,50000), random.random()*100) for _ in range(500000)])
q = "select count(*), sum(amount) from orders where user_id = 4242"
print(c.execute("explain query plan "+q).fetchall())
c.execute("create index idx_user on orders(user_id)")
print(c.execute("explain query plan "+q).fetchall())
EOF

# SQLite command-line shell (if installed): .eqp on  shows plans for each query
sqlite3 test.db ".schema"

# PostgreSQL (if you have it, or run: docker run -e POSTGRES_PASSWORD=x -p 5432:5432 postgres)
psql -h localhost -U postgres -c "EXPLAIN SELECT 1;"
psql -c "SHOW transaction_isolation;"                 # default: read committed
psql -c "SELECT * FROM pg_stat_replication;"          # on a primary
psql -c "SELECT pg_is_in_recovery();"                 # true on a standby
psql -c "SELECT now() - pg_last_xact_replay_timestamp() AS lag;"   # on a standby
```
`[SAMPLE]` `SHOW transaction_isolation;` on PostgreSQL:
```
 transaction_isolation
-----------------------
 read committed
```
(The default is read committed, from the docs. The functions in the last two commands are standard; I did not check them on the docs today.)

## 5. Common mistakes

1. No index on a column used for frequent, selective lookups (full scans).
2. Indexing everything (slow writes, big disk) or using an index on a column wrapped in a function.
3. Running `EXPLAIN ANALYZE` on a write query without a transaction and rollback.
4. Reading from a replica right after writing and expecting to see the write.
5. Not retrying on serialization failures and deadlocks.
6. Running heavy reports on the primary OLTP database.
7. Assuming isolation level names behave the same in every database.
8. Never testing restores, or using `SELECT *` and N+1 queries in hot paths.

## 6. Eight interview questions with answers

**Q1. What is an index and what does it cost?**
A data structure (usually a B-tree) that lets the database find rows by a column's value without scanning the whole table. Costs: extra disk and memory, and every insert, update, or delete must update the index, so writes get slower. Index only what real queries need.

**Q2. A query is slow. What do you do?**
Find the exact query, run `EXPLAIN (ANALYZE, BUFFERS)` (inside a transaction with rollback if it modifies data), read the plan from the inside out, look for sequential scans on large tables, a large gap between estimated and actual rows, and spills. Fix with a suitable index or query rewrite, update statistics, remove N+1 patterns; also check locks, connection saturation, and resource limits. Measure before and after.

**Q3. What does `EXPLAIN` vs `EXPLAIN ANALYZE` do?**
`EXPLAIN` shows the plan and estimated costs without running the query. `EXPLAIN ANALYZE` runs the query and adds real row counts and times. Because it really runs, a data-changing statement really changes data unless wrapped in a transaction that is rolled back.

**Q4. Explain the isolation levels and the problems they prevent.**
Read committed: no dirty reads, but a re-read can change (nonrepeatable) and phantoms can appear. Repeatable read: a stable snapshot, no nonrepeatable reads (and in PostgreSQL no phantoms either), but write skew can still happen. Serializable: results equal some one-at-a-time order, no anomalies, at the cost of serialization failures that the app must retry. PostgreSQL's default is Read Committed, and its Read Uncommitted behaves like Read Committed.

**Q5. What is replication lag, what causes it, and how do you deal with it?**
The delay before a replica has applied the primary's changes. Causes: write bursts, slow network or disk, an overloaded replica, long queries on the replica that conflict with replay. Measure with WAL positions or replay timestamps. Handle it with alerts, read-your-writes (read from the primary right after a write), routing only lag-tolerant reads to replicas, bigger replicas, and synchronous replication where data loss is unacceptable (accepting higher commit latency).

**Q6. Synchronous vs asynchronous replication?**
Asynchronous: the primary commits without waiting for the replica, so it is fast, but recent commits can be lost if the primary fails and replicas lag. Synchronous: the commit waits for at least one replica to confirm, so no loss of confirmed data on failover, but every commit pays the round trip and a dead replica can block writes unless configured otherwise.

**Q7. Row store vs column store?**
Row stores keep each row together: best for transactions and fetching or updating whole records. Column stores keep each column together: best for analytics that scan a few columns across huge numbers of rows, with strong compression, but poor for single-row updates. Use a row store for the application database and a column store for the warehouse.

**Q8. How would you run a schema change on a big table with no downtime?**
Use backward-compatible steps (expand and contract): add the new nullable column or table, deploy code that writes to both old and new, backfill in small batches, switch reads, then remove the old structure in a later release. Avoid long exclusive locks, create indexes concurrently, set lock timeouts, and have a rollback plan.

## 7. Self-quiz (answers at the end)

1. Why does `WHERE lower(email) = 'a@b.com'` ignore a plain index on `email`?
2. What is the PostgreSQL default isolation level?
3. Name one problem that Serializable prevents but Repeatable Read does not.
4. A user saves a profile and immediately sees old data. Likely cause and one fix?
5. Which store is better for "average order value per country over 2 billion rows"?

**Answers**
1. The index is on the raw `email` values, but the query asks about the lowered value. Fix: an expression index on `lower(email)`, or store normalized email.
2. Read Committed.
3. A serialization anomaly such as write skew (two transactions each check a rule and both break it together).
4. The read went to a lagging replica. Fix: read your own writes from the primary for a short time, or wait for the replica to reach the write's position.
5. A column store (BigQuery, ClickHouse, Redshift).

## 8. Sources

- PostgreSQL, Transaction Isolation (phenomena, table, defaults, retry rules): https://www.postgresql.org/docs/current/transaction-iso.html
- PostgreSQL, Using EXPLAIN (EXPLAIN vs ANALYZE, scan types, cost units): https://www.postgresql.org/docs/current/using-explain.html
- PostgreSQL, Log-Shipping Standby Servers (streaming replication, async vs sync, lag, hot standby): https://www.postgresql.org/docs/current/warm-standby.html
- Google Cloud, database products overview: https://docs.cloud.google.com/docs/databases
- Local: SQLite 3.51.0 `explain query plan` output, 2026-11-15

Not verified from a source: B-tree description, index rules of thumb (composite index order, covering index, leading wildcard), costs of indexes; `CREATE INDEX CONCURRENTLY`; `pg_stat_statements`; `pg_wal_lsn_diff` and `pg_last_xact_replay_timestamp`; MySQL InnoDB default isolation; row vs column store details and examples (ClickHouse, Redshift, Parquet); connection pooling, backups/RPO/RTO, expand-and-contract migrations (standard practice); the claim that write skew is allowed under Repeatable Read (standard result; the PostgreSQL page says Repeatable Read still allows serialization anomalies); every PostgreSQL `[SAMPLE]` output.
