# 11 - LRU Cache

Python 3.9. All code was run; the output is real.

---

## 1. The problem in plain words

A **cache** is a small, fast memory that keeps recent answers, so you do not need to do slow work again.
**LRU** means **Least Recently Used**. When the cache is full and a new item arrives, we throw away the item that was used **longest ago**.

**Analogy.** Your study desk has space for 3 books. You always keep the 3 books you touched most recently on the desk. When you need a 4th book, you put back on the shelf the book you have not touched for the longest time.

You must build:

- `get(key)` -> returns the value, or "not found". It counts as a "use".
- `put(key, value)` -> saves the value. If the cache is full, remove the least recently used item first.
- **Both must run in O(1) time** (constant time: it does not get slower when the cache grows). This is the famous part of the question.

---

## 2. Requirements I ask the interviewer

1. Fixed capacity given at the start? -> *Yes.*
2. What does `get` return for a missing key? -> *-1 or None (I will use `None`).*
3. Does `put` on an existing key count as a use? -> *Yes, and it updates the value.*
4. Must `get` and `put` be O(1)? -> *Yes.*
5. Multiple threads? -> *Yes, make it safe.*
6. Keys: any hashable type? Values: anything? -> *Yes.*
7. Do items expire after some time? -> *Not now (possible extension).*

---

## 3. Why two data structures? (step by step)

**Attempt 1: only a dictionary (hash map).**
Dictionary gives O(1) to find a key. But a dictionary does not know **which key is the oldest**. Finding it would need a scan: O(n). Too slow.

**Attempt 2: only a list ordered by use.**
We can keep "most recent at the front, oldest at the back". Removing the oldest is easy. But to **find** a key in a list we must scan: O(n). And moving an item from the middle to the front needs a shift: O(n). Too slow.

**Idea: use both.**

- A **hash map**: `key -> node`. This finds any item in O(1).
- A **doubly linked list** of nodes, ordered by use. This moves a node to the front, or removes a node, in O(1) **if we already hold the node**.

The hash map gives us the node. The linked list lets us move it. Together: O(1).

### What is a doubly linked list?

A chain of boxes (called *nodes*). Each node holds: the data, a pointer to the **previous** node, and a pointer to the **next** node. "Pointer" just means "a reference to another node".

**Analogy.** A train. Each coach is connected to the coach in front and the coach behind. To remove one coach you only reconnect its two neighbours. You do not need to move the whole train.

```text
HEAD <-> [A] <-> [B] <-> [C] <-> TAIL
```

- `HEAD` and `TAIL` are two **dummy nodes** (we call them *sentinels*). They hold no data. They exist so that "first node" and "last node" are never special cases: there is always a neighbour on both sides. This removes many `if` checks.
- **Most recently used** is right after HEAD. **Least recently used** is right before TAIL.

### The three small moves

1. **Remove a node** (to unlink it): connect its `prev` and `next` to each other.

```text
before:  P <-> X <-> N
after:   P <-> N          (X is out)
         P.next = N ; N.prev = P
```

2. **Add a node at the front** (right after HEAD):

```text
before:  HEAD <-> A
after:   HEAD <-> X <-> A
         X.prev = HEAD ; X.next = A ; A.prev = X ; HEAD.next = X
```

3. **Mark as used** = remove the node, then add it at the front.

### A full example (capacity 2)

```text
put(1,"a")   map: {1}        list: HEAD <-> [1] <-> TAIL
put(2,"b")   map: {1,2}      list: HEAD <-> [2] <-> [1] <-> TAIL
get(1)       1 becomes newest:  HEAD <-> [1] <-> [2] <-> TAIL
put(3,"c")   FULL! oldest is the node before TAIL = [2]
             remove [2] from list and map, then add [3] at front
             map: {1,3}      list: HEAD <-> [3] <-> [1] <-> TAIL
get(2)       -> None (it was evicted)
```

**Why does the node store the key too?** When we evict the node before TAIL, we know the node but we also need its **key** so that we can delete it from the hash map.

---

## 4. Classes and methods (the picture)

```text
+----------------------------------+            +--------------------+
|            LRUCache              |            |        Node        |
|----------------------------------|  has many  |--------------------|
| capacity                         |----------->| key, value         |
| _map: {key -> Node}              |            | prev, next         |
| _head, _tail  (sentinel Nodes)   |            +--------------------+
| _lock                            |
|----------------------------------|
| get(key) -> value or None        |
| put(key, value)                  |
| _remove(node)   (private helper) |
| _add_front(node)(private helper) |
+----------------------------------+
```

Only two classes are needed. The point of this question is the data structure, not many classes. (Do not force design patterns here.)

---

## 5. Full code

```python
import threading                               # Lock for thread safety


class Node:
    # one box in the doubly linked list
    def __init__(self, key=None, value=None):
        self.key = key                         # we keep the key so we can delete it from the map on eviction
        self.value = value                     # the cached data
        self.prev = None                       # pointer to the node on the left (more recent)
        self.next = None                       # pointer to the node on the right (older)


class LRUCache:
    def __init__(self, capacity):
        if capacity <= 0:                      # a cache that holds nothing makes no sense
            raise ValueError("capacity must be positive")
        self.capacity = capacity               # maximum number of items
        self._map = {}                         # key -> Node, gives O(1) lookup
        self._head = Node()                    # dummy node on the left end (most recent side)
        self._tail = Node()                    # dummy node on the right end (oldest side)
        self._head.next = self._tail           # empty list: HEAD <-> TAIL
        self._tail.prev = self._head
        self._lock = threading.RLock()         # RLock: the same thread may lock twice (helps in subclasses)

    # ----- private helpers: each is O(1) -----

    def _remove(self, node):
        node.prev.next = node.next             # left neighbour now points past node
        node.next.prev = node.prev             # right neighbour now points back past node

    def _add_front(self, node):
        node.prev = self._head                 # new node sits right after HEAD
        node.next = self._head.next            # and points to what used to be first
        self._head.next.prev = node            # old first points back to the new node
        self._head.next = node                 # HEAD points to the new node

    # ----- public API -----

    def get(self, key):
        with self._lock:                       # lock because we change the list order
            node = self._map.get(key)          # O(1) dictionary lookup
            if node is None:
                return None                    # cache miss
            self._remove(node)                 # take it out of its old position...
            self._add_front(node)              # ...and make it the most recent
            return node.value

    def put(self, key, value):
        with self._lock:
            node = self._map.get(key)
            if node is not None:               # key already there: update and refresh
                node.value = value
                self._remove(node)
                self._add_front(node)
                return
            if len(self._map) >= self.capacity:    # full: evict the least recently used
                oldest = self._tail.prev           # the node just before TAIL
                self._remove(oldest)               # unlink it from the list
                del self._map[oldest.key]          # and from the map (this is why Node stores the key)
            new_node = Node(key, value)
            self._map[key] = new_node          # register in the map
            self._add_front(new_node)          # newest goes to the front

    def delete(self, key):
        with self._lock:
            node = self._map.pop(key, None)    # remove from map (None if missing)
            if node is None:
                return False
            self._remove(node)                 # and from the list
            return True

    def keys_recent_first(self):
        # helper for the demo: walk the list from HEAD to TAIL
        with self._lock:
            out = []
            cur = self._head.next
            while cur is not self._tail:       # stop at the dummy end node
                out.append(cur.key)
                cur = cur.next
            return out

    def __len__(self):
        return len(self._map)                  # number of items stored


# ---------- EXTENSION: items that expire (TTL = time to live) ----------

class TTLCache(LRUCache):
    def __init__(self, capacity, ttl_seconds, clock):
        super().__init__(capacity)             # reuse all LRU behaviour
        self.ttl = ttl_seconds                 # how long an item lives
        self.clock = clock                     # function returning "now"; easy to fake in tests
        self._expires_at = {}                  # key -> time when it dies

    def put(self, key, value):
        with self._lock:
            super().put(key, value)            # normal LRU put (may evict)
            self._expires_at[key] = self.clock() + self.ttl   # set a new death time

    def get(self, key):
        with self._lock:
            died = self._expires_at.get(key)
            if died is not None and self.clock() >= died:     # too old?
                self.delete(key)               # remove it (lazy expiry: we only notice when asked)
                self._expires_at.pop(key, None)
                return None
            return super().get(key)            # normal LRU get


class FakeClock:
    def __init__(self):
        self.now = 0
    def __call__(self):
        return self.now


def main():
    cache = LRUCache(2)
    cache.put(1, "a")
    cache.put(2, "b")
    print("after put 1,2   :", cache.keys_recent_first())
    print("get(1)          :", cache.get(1), "->", cache.keys_recent_first())
    cache.put(3, "c")                          # evicts key 2 (least recently used)
    print("after put 3     :", cache.keys_recent_first())
    print("get(2)          :", cache.get(2), "(evicted)")
    cache.put(1, "A")                          # update existing key: no eviction, 1 becomes newest
    print("update 1        :", cache.get(1), cache.keys_recent_first())
    cache.put(4, "d")                          # evicts 3 (older than 1)
    print("after put 4     :", cache.keys_recent_first(), "len =", len(cache))

    # ---- extension demo ----
    print("--- TTL extension ---")
    clk = FakeClock()
    ttl = TTLCache(3, ttl_seconds=10, clock=clk)
    ttl.put("x", 1)
    clk.now = 5
    print("t=5  get x:", ttl.get("x"))
    clk.now = 10
    print("t=10 get x:", ttl.get("x"), "(expired)")

    # ---- thread test: 8 threads hammer a cache of size 50 ----
    print("--- thread test ---")
    shared = LRUCache(50)
    def worker(n):
        for i in range(2000):
            shared.put((n * 7 + i) % 120, i)   # writes spread over 120 keys
            shared.get((n * 3 + i) % 120)      # reads
    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for t in threads: t.start()
    for t in threads: t.join()
    ordered = shared.keys_recent_first()
    # the list and the map must agree: same size, no duplicates, never above capacity
    print("size:", len(shared), "list length:", len(ordered),
          "no duplicates:", len(set(ordered)) == len(ordered),
          "within capacity:", len(shared) <= 50)


if __name__ == "__main__":
    main()
```

Output I got when I ran it:

```text
after put 1,2   : [2, 1]
get(1)          : a -> [1, 2]
after put 3     : [3, 1]
get(2)          : None (evicted)
update 1        : A [1, 3]
after put 4     : [4, 1] len = 2
--- TTL extension ---
t=5  get x: 1
t=10 get x: None (expired)
--- thread test ---
size: 50 list length: 50 no duplicates: True within capacity: True
```

---

## 6. How the code works (walk through)

- `get`: look in the map (O(1)). If found, `_remove` + `_add_front` moves the node to the "newest" spot (O(1)). Return the value.
- `put` (new key, cache full): the **oldest node is always `_tail.prev`**. We unlink it, delete its key from the map, then add the new node at the front.
- Every step is a fixed number of pointer changes, so both operations are **O(1)**. Memory is O(capacity).
- The output matches the hand example in section 3: after `get(1)`, key 2 is the oldest, so `put(3)` throws key 2 out.

**Shortcut to mention (do not use it unless allowed):** Python's `collections.OrderedDict` has `move_to_end()` and `popitem(last=False)`, which does the same job in a few lines. Interviewers usually want you to build the list yourself. Mention that you know the shortcut at the end.

---

## 7. How to extend it

**"Add expiry (TTL)."** I built `TTLCache` as a subclass. It reuses the LRU code and only adds a dictionary `key -> death time`. Expiry is **lazy**: we check the time when `get` is called. For eager cleanup, add a background thread or a min-heap of death times. Small known flaw: `_expires_at` keeps the entry of a key that LRU evicted. In real code you would clean it (for example, override `_remove`/evict to pop it too). Say this out loud; it shows you review your own code.

**"Make it a generic cache with different eviction rules (LRU, LFU, FIFO)."** Define an `EvictionPolicy` interface with `on_access(key)`, `on_insert(key)`, `evict() -> key`. The cache holds a policy (Strategy pattern, file 03). `LRUPolicy` would be the linked list above.

**"Add a loader for misses (read-through cache)."** Pass a `loader(key)` function in the constructor. On a miss, call the loader, then `put`.

---

## 8. Thread-safety notes (plain words)

- **The danger:** `get` looks like a "read", but it **changes the list order**. So two threads calling `get` can corrupt the pointers (one removes the node while the other moves it). Even `get` needs a lock.
- **The fix:** one lock around every public method. The thread test checks that the map and the list never disagree.
- I used `RLock` (re-entrant lock): the same thread can take it again. `TTLCache.get` calls `delete` and `super().get`, which also lock. With a plain `Lock` this would hang forever (deadlock).
- **Cost:** one lock = one thread at a time. For higher speed, split into several small caches by `hash(key) % N`, each with its own lock (this is called *sharding*).
- Python's GIL (Global Interpreter Lock) does **not** make multi-step operations safe. Do not rely on it.

---

## 9. Five follow-up questions with model answers

**Q1. Why a doubly linked list and not a singly linked list?**
To remove a node in O(1) I need its **previous** node. A singly linked list only knows `next`, so finding the previous node would be a scan, O(n). The `prev` pointer removes that scan.

**Q2. Why dummy head and tail nodes?**
Without them, removing the first or last node needs special `if` branches (`if node.prev is None`...). With dummies every real node always has two neighbours, so `_remove` and `_add_front` are the same code for every position. Less code, fewer bugs.

**Q3. Why store the key inside the node?**
On eviction I get the oldest node from the list. I must also delete it from the map, and deleting from the map needs the key. Without the key I would scan the map.

**Q4. How would you make this faster with many threads?**
Shard it: make N independent `LRUCache` objects, pick one with `hash(key) % N`. Threads working on different shards do not wait for each other. The downside: eviction is now "least recent *inside the shard*", which is only approximately global LRU. That is usually fine.

**Q5. How is LFU (Least Frequently Used) different, and how would you build it in O(1)?**
LFU evicts the item used the fewest times. One known O(1) design: a map `key -> node` plus a map `count -> doubly linked list of nodes with that count`, and a variable `min_count`. On access, move the node from list `count` to list `count+1`. On eviction, remove the oldest node in list `min_count`. (If asked, say this is the idea and explain tie-breaking by recency inside each list.)

---

**Next:** `12_elevator_system.md`.
