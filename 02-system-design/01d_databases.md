# 01d. Databases: SQL vs NoSQL, Indexes, Transactions

---

## 1. What is a database?

A place that stores data safely on disk and lets you find it quickly. Memory is lost when the power goes off; a database is not.

**Analogy:** a library. Books (data) stay on shelves (disk). The catalog (index) helps you find a book without walking every shelf. The librarian (database engine) keeps rules so two people do not borrow the same copy at the same time.

---

## 2. SQL (relational) databases

Data lives in **tables** with **rows** and **columns**. Tables are linked by keys. You query with SQL.

Examples: PostgreSQL, MySQL.

```
users                         orders
+----+-------+                +----+---------+--------+
| id | name  |                | id | user_id | total  |
+----+-------+                +----+---------+--------+
| 1  | Asha  | <------------- | 10 | 1       | 500    |
| 2  | Ravi  |                | 11 | 1       | 120    |
+----+-------+                +----+---------+--------+
```

- **Primary key**: unique id of a row (`id`).
- **Foreign key**: a column that points to another table (`user_id`).
- **JOIN**: combine rows from two tables.
- **Schema**: the fixed shape of tables. You must declare it first.

**Strengths:** strong rules, transactions (ACID), flexible queries, JOINs. Great for money, orders, accounts.
**Weak points:** scaling writes across many machines is harder (needs sharding, see `01f`).

---

## 3. NoSQL databases

"NoSQL" = "not only SQL". It is a group of different designs:

| Family | Idea | Examples | Good for |
|---|---|---|---|
| **Key-value** | `key -> value`, very fast | Redis, DynamoDB | Sessions, caches, simple lookups |
| **Document** | Stores JSON-like documents | MongoDB, Firestore | Flexible objects, product catalogs |
| **Wide-column** | Rows with many columns, built for huge writes | Cassandra, Bigtable, HBase | Time series, messages, logs, huge scale |
| **Graph** | Nodes and edges | Neo4j | Social links, recommendations |
| **Search engine** | Inverted index for text | Elasticsearch, OpenSearch | Full-text search, logs |

**Strengths:** scale out easily, flexible schema, very fast for the access pattern they were designed for.
**Weak points:** weaker JOINs, often weaker transactions, you must design tables around your queries.

### SQL vs NoSQL: how to choose (the answer to say in interviews)

| Question | Lean SQL | Lean NoSQL |
|---|---|---|
| Is data relational, and are there many different queries? | Yes | No |
| Do you need strong transactions (money, inventory)? | Yes | Not always |
| Is it a huge write volume (millions per second) with simple access? | Hard | Yes |
| Is the shape of data changing a lot? | No | Yes |
| Do you know your queries upfront? | Not needed | Required |

Honest advice: **start with SQL unless you have a clear reason.** Modern PostgreSQL handles a lot (a single good machine can handle thousands of writes per second and much more reads; mark this as a rough rule, not a promise). Say: "I choose X **because** my access pattern is Y."

---

## 4. Indexes (the catalog)

Without an index, to find a user by email the database reads **every row** (a "full table scan"). With an index on `email`, it jumps to the row directly.

**Analogy:** the index at the back of a textbook. You do not read the whole book to find "Kubernetes".

- Most indexes are **B-trees**: a sorted tree. Lookup cost grows slowly with data size (about log N). Good for equality and range (`WHERE created_at > ...`).
- Some NoSQL stores use **LSM trees**: writes go to memory and append-only files, then merge in the background. Very fast writes; reads may check several files. (Cassandra, RocksDB use this. Just know the name and "good for writes".)
- **Hash index**: fast for exact match only.

### Index trade-offs

| Benefit | Cost |
|---|---|
| Reads become fast | Every write must also update the index (writes slower) |
| | Takes disk space |

So: do not index every column. Index the columns you filter, join, or sort by.

### Useful index ideas

- **Composite index** `(user_id, created_at)`: good for "latest orders of user 5". **Column order matters**: it works for `user_id` alone, and `user_id + created_at`, but not `created_at` alone.
- **Unique index**: also enforces no duplicates (great for idempotency keys, short codes).
- **Covering index**: contains all columns the query needs, so the table is not touched.

---

## 5. Transactions and ACID

A **transaction** is a group of steps that must succeed **all together or not at all**.

**Classic example: bank transfer.** Take 100 from Asha and add 100 to Ravi. If the system crashes after step 1, 100 rupees vanish. A transaction prevents this.

**ACID** (four promises):

| Letter | Meaning | Plain words |
|---|---|---|
| **A**tomicity | All or nothing | Both steps happen, or neither |
| **C**onsistency | Rules stay true | Balance cannot go negative if a rule says so |
| **I**solation | Parallel transactions do not mess each other | Two people booking the last seat: only one wins |
| **D**urability | Once committed, it survives a crash | Data is on disk |

### Isolation problems (just know the names)

- **Dirty read**: you read data another transaction has not committed yet.
- **Non-repeatable read**: you read a row twice and get different values.
- **Phantom read**: you run the same query twice and new rows appear.
- **Lost update**: two people read 10, both add 1, both write 11 (should be 12).

Isolation levels (read committed, repeatable read, serializable) trade safety for speed. Simple summary: higher level = safer but slower and more conflicts.

### Handling concurrent updates

- **Pessimistic lock**: `SELECT ... FOR UPDATE` locks the row; others wait. Safe, can be slow.
- **Optimistic lock**: keep a `version` column. Update only `WHERE version = 5`; if 0 rows changed, someone else won - retry. Fast when conflicts are rare.
- **Atomic operation**: `UPDATE stock SET qty = qty - 1 WHERE id = 7 AND qty > 0`. Often the simplest and best.

### Transactions across many databases or services

Hard. Options: **Saga** (a series of local transactions with undo steps called compensations), or **two-phase commit** (rarely used at scale; slow and blocks). In interviews, say: "I avoid distributed transactions; I use a saga with idempotent steps." You will see this in `18` and `19`. Your provisioner (install in dependency order, undo on failure) is a saga-like workflow.

---

## 6. BASE (the NoSQL side)

Many NoSQL systems choose: **B**asically **A**vailable, **S**oft state, **E**ventually consistent. Meaning: always answer, data may be slightly stale for a short time, it will become the same everywhere eventually. See `01h`.

---

## 7. Other useful terms

- **Normalization**: do not repeat data; store a fact in one place (SQL style). Good for correctness.
- **Denormalization**: copy data to avoid JOINs (NoSQL style, or for speed). Good for reads, but you must keep copies in sync.
- **Write-ahead log (WAL)**: the database first writes the change to a log, then to tables. After a crash it replays the log. This is how durability works.
- **Connection pool**: opening a database connection is costly; apps keep a pool of ready connections. Databases accept a limited number, so many app servers can overload them. A proxy (like PgBouncer) helps.
- **Blob storage** (S3-like): store big files (images, videos) there, and keep only the URL in the database. Never put big files in database rows.

---

## 8. Quick check

1. Give two reasons to pick SQL for a payment system.
2. Why does adding too many indexes slow writes?
3. What is the order rule for composite indexes?
4. What is a lost update and how do you stop it?
5. Why do we store images in blob storage, not in the database?
