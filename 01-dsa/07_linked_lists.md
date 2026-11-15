# Lesson 07. Linked Lists

Before this lesson: [00_how_to_start.md](00_how_to_start.md).

**How to run the code in this lesson.** Put all the Python blocks of this lesson in ONE file, from top to bottom. The first block (Template A) defines `ListNode`, `build` and `to_list`. The later blocks use them. (Other lessons have standalone blocks. This lesson shares the helper code to stay short.)

---

## 1. What is this?

A **linked list** is a chain of small boxes called **nodes**. Each node has two things:

1. a **value** (the data), and
2. a **next** pointer (an arrow to the next node).

The last node's `next` is `None` (it points to nothing). The first node is called the **head**. You only hold the head. To reach other nodes you follow the arrows.

```text
head
 |
 v
+-----+---+    +-----+---+    +-----+------+
|  1  | *-+--> |  2  | *-+--> |  3  | None |
+-----+---+    +-----+---+    +-----+------+
 value next     value next     value next
```

**Analogy: a treasure hunt.** Each clue tells you only where the NEXT clue is hidden. To find clue number 5 you must follow clues 1, 2, 3, 4 first. You cannot jump straight to clue 5.

**Analogy 2: train coaches.** Each coach is joined to the next one. To add a coach in the middle you only change two joints. You do not need to move all coaches.

### Array versus linked list

| | Array (Python list) | Linked list |
|---|---|---|
| Read item number i | O(1) | O(i): you must walk |
| Insert / delete in the middle (when you already hold the node) | O(n): items shift | O(1): change arrows |
| Insert at the front | O(n) | O(1) |
| Memory | one block | many small nodes |

Python has no built-in linked list. In interviews, the node class is given:

```text
class ListNode:
    val  = the value
    next = the next node, or None
```

### Three tricks you must know

1. **Dummy node.** Make a fake node before the head: `dummy.next = head`. Then the head is not a special case. At the end return `dummy.next`.
2. **Fast and slow pointers.** Slow moves 1 step, fast moves 2 steps. When fast reaches the end, slow is in the middle. If there is a cycle, fast catches slow.
3. **Three variables for reversing:** `prev`, `curr`, `next`. Always save `curr.next` BEFORE you change it.

## 2. When do I use it?

Words that give it away:

- "linked list", "head of the list", "node"
- "reverse", "merge two sorted lists", "remove the nth node"
- "cycle", "loop", "detect"
- "middle of the list", "nth from the end" (fast and slow, or a gap between two pointers)
- "in place" or "O(1) extra space"
- "least recently used" (LRU cache: a doubly linked list plus a dictionary)

## 3. A tiny example, traced line by line

Walk through `1 -> 2 -> 3` and count the nodes.

```text
curr = head (node 1), count = 0
loop: curr is not None -> count = 1, curr = curr.next (node 2)
loop: curr is not None -> count = 2, curr = curr.next (node 3)
loop: curr is not None -> count = 3, curr = curr.next (None)
loop: curr is None -> stop.   count = 3
```

Find the middle of `1 -> 2 -> 3 -> 4 -> 5` with slow and fast pointers:

```text
start:        slow = 1, fast = 1
fast and fast.next exist -> slow = 2, fast = 3
fast and fast.next exist -> slow = 3, fast = 5
fast.next is None        -> stop.   slow is the middle: 3
```

## 4. Template code (a comment on every line)

```python
# TEMPLATE A: the node class and two helper functions (used by all later blocks)
class ListNode:                                 # one box of the chain
    def __init__(self, val=0, next=None):       # create a node
        self.val = val                          # the stored value
        self.next = next                        # the arrow to the next node (None = end)

def build(values):                              # make a linked list from a Python list; return the head
    dummy = ListNode()                          # a fake node before the head
    tail = dummy                                # tail is the last node built so far
    for v in values:                            # for every value
        tail.next = ListNode(v)                 # attach a new node after the tail
        tail = tail.next                        # the new node is now the tail
    return dummy.next                           # the real head (None if values is empty)

def to_list(head):                              # turn a linked list into a Python list (for printing/tests)
    out = []                                    # the answer
    while head:                                 # while there is a node
        out.append(head.val)                    # save its value
        head = head.next                        # follow the arrow
    return out                                  # the values in order

print(to_list(build([1, 2, 3])))                # expect [1, 2, 3]
assert to_list(build([1, 2, 3])) == [1, 2, 3]   # round trip works
assert build([]) is None                        # an empty list has no head
```

```python
# TEMPLATE B: walk the list, and the dummy-node trick (remove every node with a given value)
def length(head):                               # function: how many nodes
    count = 0                                   # nodes counted so far
    curr = head                                 # start at the head
    while curr:                                 # while we stand on a real node
        count += 1                              # count it
        curr = curr.next                        # move to the next node
    return count                                # total nodes

def remove_value(head, target):                 # function: delete all nodes whose value is target
    dummy = ListNode(0, head)                   # fake node in front, so removing the head is not special
    prev = dummy                                # prev is the node before curr
    curr = head                                 # curr is the node we are checking
    while curr:                                 # walk the whole list
        if curr.val == target:                  # this node must go
            prev.next = curr.next               # skip over it: prev now points past curr
        else:                                   # this node stays
            prev = curr                         # move prev forward
        curr = curr.next                        # always move curr forward
    return dummy.next                           # the (possibly new) head

assert length(build([1, 2, 3])) == 3            # three nodes
assert length(None) == 0                        # empty list
assert to_list(remove_value(build([1, 2, 6, 3, 6]), 6)) == [1, 2, 3]   # remove the 6s
assert to_list(remove_value(build([6, 6, 1]), 6)) == [1]               # the head is removed too
print("template B ok")                          # show that all checks above passed
```

```python
# TEMPLATE C: fast and slow pointers (find the middle node)
def middle(head):                               # function: the middle node (the second one if two)
    slow = head                                 # slow moves 1 step at a time
    fast = head                                 # fast moves 2 steps at a time
    while fast and fast.next:                   # while fast can still take two steps
        slow = slow.next                        # slow takes one step
        fast = fast.next.next                   # fast takes two steps
    return slow                                 # when fast is at the end, slow is in the middle

assert middle(build([1, 2, 3, 4, 5])).val == 3  # odd length: the exact middle
assert middle(build([1, 2, 3, 4])).val == 3     # even length: the second of the two middles
assert middle(build([7])).val == 7              # one node
print("template C ok")                          # show that all checks above passed
```

---

## 5. Classic problems

### Problem 1. Reverse Linked List

**Problem in plain words.** Reverse a linked list and return the new head.

Example: `1 -> 2 -> 3 -> None` becomes `3 -> 2 -> 1 -> None`.

**Brute force.** Copy all values into a Python list, reverse it, and build a new linked list. O(n) time but O(n) extra space, and you create new nodes. The interviewer wants you to reverse the arrows in place.

**Better idea, slowly.** Walk along the list. At each node, turn its arrow backwards, so it points to the previous node. You need three variables:

- `prev`: the node behind (starts as `None`, because the new last node must point to nothing).
- `curr`: the node you are fixing now.
- `nxt`: the node ahead. Save it FIRST: after you flip `curr.next`, you would lose the rest of the list.

Steps for each node: save `nxt = curr.next`; flip `curr.next = prev`; move `prev = curr`; move `curr = nxt`.

```python
def reverse_list(head):
    prev = None                               # the node behind curr; the new tail will point to None
    curr = head                               # the node we are turning around
    while curr:                               # until we run off the end
        nxt = curr.next                       # 1. save the rest of the list
        curr.next = prev                      # 2. flip the arrow backwards
        prev = curr                           # 3. prev steps forward to curr
        curr = nxt                            # 4. curr steps forward to the saved next node
    return prev                               # prev is the last node we touched: the new head

print(to_list(reverse_list(build([1, 2, 3]))))            # expect [3, 2, 1]
assert to_list(reverse_list(build([1, 2, 3]))) == [3, 2, 1]    # example
assert reverse_list(None) is None                          # empty list
assert to_list(reverse_list(build([5]))) == [5]            # one node
assert to_list(reverse_list(build([1, 2]))) == [2, 1]      # two nodes
```

**Trace** on `1 -> 2 -> 3`:

```text
start:   prev = None, curr = 1          list: 1 -> 2 -> 3 -> None

step 1:  nxt = 2.   1.next = None.  prev = 1.  curr = 2.
         now:  None <- 1     2 -> 3 -> None

step 2:  nxt = 3.   2.next = 1.     prev = 2.  curr = 3.
         now:  None <- 1 <- 2     3 -> None

step 3:  nxt = None. 3.next = 2.    prev = 3.  curr = None.
         now:  None <- 1 <- 2 <- 3

curr is None -> stop. return prev = node 3.   Result: 3 -> 2 -> 1 -> None
```

**Complexity.** Time O(n): each node is visited once. Space O(1): only three variables.

**Two edge cases.** (1) Empty list (`head` is `None`): the loop does not run and we return `None`. (2) One node: `prev` becomes that node, return it.

**How interviewers twist it.** "Reverse only from position left to right." "Reverse in groups of k." "Do it recursively." "Check if the list is a palindrome" (reverse the second half).

---

### Problem 2. Merge Two Sorted Lists

**Problem in plain words.** You get two sorted linked lists. Join them into ONE sorted linked list by re-using the nodes.

Example: `1 -> 2 -> 4` and `1 -> 3 -> 4` give `1 -> 1 -> 2 -> 3 -> 4 -> 4`.

**Brute force.** Put all values in a Python list, sort it, and build a new linked list. O((n + m) log(n + m)) time, O(n + m) space. It ignores that the lists are already sorted.

**Better idea, slowly.** Like merging two lines of people sorted by height. Look at the FIRST person of each line. Take the shorter one and put them in the new line. Repeat. When one line is empty, put the whole other line at the end.

Use a `dummy` node and a `tail` pointer to build the result without special cases.

```python
def merge_two_lists(l1, l2):
    dummy = ListNode()                            # fake start of the merged list
    tail = dummy                                  # tail = last node of the merged list so far
    while l1 and l2:                              # while both lists still have nodes
        if l1.val <= l2.val:                      # the front of l1 is smaller (or equal)
            tail.next = l1                        # attach that node to the result
            l1 = l1.next                          # move l1 to its next node
        else:                                     # the front of l2 is smaller
            tail.next = l2                        # attach that node to the result
            l2 = l2.next                          # move l2 to its next node
        tail = tail.next                          # the tail is now the node we just attached
    tail.next = l1 if l1 else l2                  # one list ended: attach the rest of the other one
    return dummy.next                             # skip the fake node

merged = merge_two_lists(build([1, 2, 4]), build([1, 3, 4]))      # run the example
print(to_list(merged))                            # expect [1, 1, 2, 3, 4, 4]
assert to_list(merged) == [1, 1, 2, 3, 4, 4]      # example
assert merge_two_lists(None, None) is None        # both empty
assert to_list(merge_two_lists(None, build([0]))) == [0]          # one empty
assert to_list(merge_two_lists(build([1, 2, 3]), build([7, 8, 9, 10]))) == [1, 2, 3, 7, 8, 9, 10]   # different lengths
```

**Trace** on `l1 = 1 -> 2 -> 4`, `l2 = 1 -> 3 -> 4`:

```text
compare 1 (l1) and 1 (l2): 1 <= 1 -> take l1's 1.    result: 1             l1 = 2 -> 4
compare 2 (l1) and 1 (l2): 2 >  1 -> take l2's 1.    result: 1 1           l2 = 3 -> 4
compare 2 (l1) and 3 (l2): 2 <= 3 -> take l1's 2.    result: 1 1 2         l1 = 4
compare 4 (l1) and 3 (l2): 4 >  3 -> take l2's 3.    result: 1 1 2 3       l2 = 4
compare 4 (l1) and 4 (l2): 4 <= 4 -> take l1's 4.    result: 1 1 2 3 4     l1 = None
l1 is empty -> attach the rest of l2 (the last 4).   result: 1 1 2 3 4 4
```

**Complexity.** Time O(n + m): every node is attached once. Space O(1): we re-use the nodes; no new nodes (except the dummy).

**Two edge cases.** (1) One list is empty: the `while` loop never runs, and `tail.next` becomes the other list. (2) Equal values: `<=` keeps the merge stable (items of `l1` come first).

**How interviewers twist it.** "Merge k sorted lists" (use a min-heap). "Sort a linked list" (merge sort uses this as a step). "Merge two sorted arrays in place."

---

### Problem 3. Linked List Cycle

**Problem in plain words.** Does the linked list have a cycle (a node whose `next` points back to an earlier node, so the list never ends)?

**Brute force.** Walk the list and store every visited node in a set. If you see a node twice, there is a cycle. O(n) time, O(n) space.

**Better idea, slowly (Floyd's tortoise and hare).** Two runners on a track. The slow one walks 1 step, the fast one walks 2 steps. If the track is a straight line, the fast one reaches the end (`None`). If the track is a loop, the fast one runs around and catches up with the slow one from behind. Each step the gap shrinks by 1, so they MUST meet. If they meet, there is a cycle.

```python
def has_cycle(head):
    slow = head                                   # the tortoise: 1 step at a time
    fast = head                                   # the hare: 2 steps at a time
    while fast and fast.next:                     # if fast hits the end, there is no cycle
        slow = slow.next                          # slow moves one step
        fast = fast.next.next                     # fast moves two steps
        if slow is fast:                          # they stand on the same node
            return True                           # fast caught slow: there is a cycle
    return False                                  # fast reached the end: no cycle

def build_cycle(values, pos):                     # test helper: tail points back to the node at index pos
    head = build(values)                          # build a normal list
    if pos < 0 or head is None:                   # pos = -1 means: no cycle
        return head                               # return the plain list
    nodes = []                                    # collect all nodes
    node = head                                   # start at the head
    while node:                                   # walk the list
        nodes.append(node)                        # remember the node
        node = node.next                          # move forward
    nodes[-1].next = nodes[pos]                   # make the last node point back to nodes[pos]
    return head                                   # return the head of the cyclic list

print(has_cycle(build_cycle([3, 2, 0, -4], 1)))   # expect True
assert has_cycle(build_cycle([3, 2, 0, -4], 1)) is True     # example: -4 points back to 2
assert has_cycle(build_cycle([1, 2], 0)) is True            # 2 points back to 1
assert has_cycle(build_cycle([1], 0)) is True               # one node pointing to itself
assert has_cycle(build([1, 2, 3])) is False                 # straight list
assert has_cycle(None) is False                             # empty list
```

**Trace** on `3 -> 2 -> 0 -> -4`, where `-4` points back to `2` (call the nodes A=3, B=2, C=0, D=-4):

```text
start:   slow = A, fast = A
step 1:  slow = B, fast = C        (fast went A -> B -> C)         not the same node
step 2:  slow = C, fast = B        (fast went C -> D -> B)         not the same node
step 3:  slow = D, fast = D        (fast went B -> C -> D)         same node! -> True
```

**Complexity.** Time O(n): the pointers meet within a number of steps proportional to the list size. Space O(1): two pointers (the set solution needs O(n)).

**Two edge cases.** (1) Empty list or one node without a cycle: the `while` condition `fast and fast.next` stops at once. (2) One node pointing to itself: `slow` and `fast` both move to that node, so they meet.

**How interviewers twist it.** "Return the node where the cycle STARTS" (Linked List Cycle II): after they meet, put one pointer back at the head and move both ONE step at a time; where they meet again is the start of the cycle.

```python
def cycle_start(head):
    slow = fast = head                            # both pointers start at the head
    while fast and fast.next:                     # move until fast ends or they meet
        slow = slow.next                          # slow: 1 step
        fast = fast.next.next                     # fast: 2 steps
        if slow is fast:                          # they met inside the cycle
            ptr = head                            # a new pointer starts at the head
            while ptr is not slow:                # move both by one step until they meet
                ptr = ptr.next                    # the new pointer moves
                slow = slow.next                  # the old pointer moves
            return ptr                            # the meeting point is the start of the cycle
    return None                                   # no cycle

start_node = cycle_start(build_cycle([3, 2, 0, -4], 1))   # the cycle starts at the node with value 2
assert start_node.val == 2                        # check
assert cycle_start(build([1, 2, 3])) is None      # no cycle
print("cycle_start ok")
```

---

### Problem 4. Remove Nth Node From End of List

**Problem in plain words.** Remove the n-th node counting from the END of the list. Return the head.

Example: `1 -> 2 -> 3 -> 4 -> 5`, `n = 2` gives `1 -> 2 -> 3 -> 5`.

**Brute force.** Pass 1: count the length `L`. Pass 2: walk `L - n` steps and remove the next node. Two passes, O(n) time, O(1) space. This is fine, but the interviewer often asks for ONE pass.

**Better idea, slowly (a gap of n between two pointers).** Let `fast` run `n` steps ahead of `slow`. Then move both at the same speed. When `fast` reaches the LAST node, `slow` is exactly the node BEFORE the one to delete (the gap stays n). Use a dummy node, so deleting the head works too.

```python
def remove_nth_from_end(head, n):
    dummy = ListNode(0, head)                     # fake node in front, so the head can be removed too
    slow = dummy                                  # will end up just before the node to delete
    fast = dummy                                  # runs ahead by n steps
    for _ in range(n):                            # move fast n steps forward
        fast = fast.next                          # one step
    while fast.next:                              # move both until fast is on the last node
        fast = fast.next                          # fast moves one step
        slow = slow.next                          # slow moves one step (keeps the gap)
    slow.next = slow.next.next                    # skip over the node to delete
    return dummy.next                             # the new head

print(to_list(remove_nth_from_end(build([1, 2, 3, 4, 5]), 2)))    # expect [1, 2, 3, 5]
assert to_list(remove_nth_from_end(build([1, 2, 3, 4, 5]), 2)) == [1, 2, 3, 5]    # example
assert remove_nth_from_end(build([1]), 1) is None                # remove the only node
assert to_list(remove_nth_from_end(build([1, 2]), 2)) == [2]     # remove the head
assert to_list(remove_nth_from_end(build([1, 2]), 1)) == [1]     # remove the last node
```

**Trace** on `1 -> 2 -> 3 -> 4 -> 5`, `n = 2` (list with dummy: `D -> 1 -> 2 -> 3 -> 4 -> 5`):

```text
start:            slow = D, fast = D
move fast 2 steps: fast = 1, then fast = 2.        slow = D
fast.next exists: fast = 3, slow = 1
fast.next exists: fast = 4, slow = 2
fast.next exists: fast = 5, slow = 3
fast.next is None -> stop.  slow = 3.
slow.next is 4 -> the node to delete. Set 3.next = 5.
result: 1 -> 2 -> 3 -> 5
```

**Complexity.** Time O(n): one pass. Space O(1).

**Two edge cases.** (1) Remove the head (`n` equals the length): the dummy node makes `slow` stay at `dummy`, and `dummy.next = head.next` works without special code. (2) One node and `n = 1`: the result is `None`.

**How interviewers twist it.** "Delete the middle node." "Rotate the list to the right by k." "Find the k-th node from the end" (same gap trick, no delete).

---

### Problem 5. LRU Cache

**Problem in plain words.** Design a **cache** (a small fast memory) that keeps at most `capacity` items. It has two operations:

- `get(key)`: return the value, or -1 if the key is not there. This counts as "using" the key.
- `put(key, value)`: add or update a key. If the cache is full, first remove the **Least Recently Used** key (the one not touched for the longest time).

Both operations must be O(1).

**Brute force.** Keep a Python list of keys in usage order. To mark a key as used you must find it and move it: O(n).

**Better idea, slowly.** We need two things at once:

1. Find a key in O(1): a **dictionary** `key -> node`.
2. Move a key to "most recent" and remove the oldest in O(1): a **doubly linked list** (each node has `prev` AND `next`). With a node in your hand, you can unlink it in O(1) because you know both neighbours. A singly linked list cannot do this.

Layout: the list goes from least recent (near `head`) to most recent (near `tail`). Two fake nodes (`head` and `tail`) avoid edge cases.

- To "use" a key: unlink its node and re-attach it just before `tail`.
- To evict: remove the node right after `head`.

```python
class Node:
    def __init__(self, key=0, val=0):
        self.key = key                            # the key (needed when we evict: to delete it from the dict)
        self.val = val                            # the value
        self.prev = None                          # arrow to the node before
        self.next = None                          # arrow to the node after

class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity                       # maximum number of items
        self.map = {}                             # key -> node
        self.head = Node()                        # fake node on the "least recent" side
        self.tail = Node()                        # fake node on the "most recent" side
        self.head.next = self.tail                # empty list: head <-> tail
        self.tail.prev = self.head                # and the other direction

    def _remove(self, node):
        node.prev.next = node.next                # the node before skips over this node
        node.next.prev = node.prev                # the node after skips back over this node

    def _add_last(self, node):
        last = self.tail.prev                     # the current most recent node
        last.next = node                          # it points forward to the new node
        node.prev = last                          # the new node points back to it
        node.next = self.tail                     # the new node points forward to the fake tail
        self.tail.prev = node                     # the fake tail points back to the new node

    def get(self, key):
        if key not in self.map:                   # unknown key
            return -1                             # nothing to return; order does not change
        node = self.map[key]                      # find the node in O(1)
        self._remove(node)                        # unlink it from its old place
        self._add_last(node)                      # re-attach it as the most recent
        return node.val                           # return the value

    def put(self, key, value):
        if key in self.map:                       # the key already exists
            self._remove(self.map[key])           # unlink the old node (we will insert a fresh one)
        node = Node(key, value)                   # make a node for the new value
        self.map[key] = node                      # store it in the dictionary
        self._add_last(node)                      # it is now the most recent
        if len(self.map) > self.cap:              # too many items?
            oldest = self.head.next               # the least recent node is right after the fake head
            self._remove(oldest)                  # unlink it from the list
            del self.map[oldest.key]              # and delete it from the dictionary

cache = LRUCache(2)                               # capacity 2
cache.put(1, 1)                                   # cache: 1
cache.put(2, 2)                                   # cache: 1 2
assert cache.get(1) == 1                          # 1 becomes most recent: 2 1
cache.put(3, 3)                                   # full: evicts 2 (least recent). cache: 1 3
assert cache.get(2) == -1                         # 2 is gone
cache.put(4, 4)                                   # full: evicts 1. cache: 3 4
assert cache.get(1) == -1                         # 1 is gone
assert cache.get(3) == 3                          # 3 becomes most recent: 4 3
assert cache.get(4) == 4                          # 4 becomes most recent: 3 4
one = LRUCache(1)                                 # capacity 1
one.put(5, 50)                                    # cache: 5
one.put(5, 51)                                    # update the same key: no eviction
assert one.get(5) == 51                           # updated value
one.put(6, 60)                                    # evicts 5
assert one.get(5) == -1                           # gone
print("LRUCache works")
```

**Trace** (capacity 2). The list is written from least recent (left) to most recent (right):

```text
put(1,1)   list: [1]
put(2,2)   list: [1, 2]
get(1)     returns 1. Move 1 to the right end.     list: [2, 1]
put(3,3)   add 3 on the right: [2, 1, 3]. Over capacity (3 > 2): evict the leftmost, 2.   list: [1, 3]
get(2)     2 is not in the dictionary -> -1.        list: [1, 3]
put(4,4)   add 4: [1, 3, 4]. Evict the leftmost, 1.  list: [3, 4]
get(1)     -> -1
get(3)     returns 3. Move 3 to the right end.     list: [4, 3]
get(4)     returns 4. Move 4 to the right end.     list: [3, 4]
```

**Complexity.** Time O(1) for `get` and `put` (dictionary lookup and a fixed number of pointer changes). Space O(capacity).

**Python shortcut.** `collections.OrderedDict` does the same with `move_to_end(key)` and `popitem(last=False)`. In an interview, first ask if you may use it. Many interviewers want the hand-made version above.

**Two edge cases.** (1) `put` on an EXISTING key must update the value, make it most recent, and NOT evict anything. (2) Capacity 1: every new key evicts the old one.

**How interviewers twist it.** "LFU cache" (least frequently used). "Add expiry times (TTL)." "Make it thread-safe." "What if the cache is distributed across machines?"

---

## 6. Common mistakes

1. **Losing the rest of the list.** In reversal, always save `nxt = curr.next` BEFORE you change `curr.next`.
2. **Not using a dummy node,** then writing special code for the head.
3. **`fast.next.next` on `None`.** Always check `fast and fast.next` first.
4. **Forgetting `None`** at the end of a list you cut. This may create a hidden cycle.
5. **Comparing nodes with `==` on values** when you mean the same node. Use `is`.
6. **Off-by-one in "nth from the end".** Move `fast` n steps, and stop when `fast.next` is `None` (not when `fast` is `None`).
7. **Not storing the key inside the node** in LRU. You need it to delete from the dictionary when you evict.
8. **Changing arrows in the wrong order** in a doubly linked list. Draw boxes and arrows on paper first.

## 7. Practice list (8 more problems)

"Asked at" means the problem appears on that company's list in the community repo [liquidslr/leetcode-company-wise-problems](https://github.com/liquidslr/leetcode-company-wise-problems) (checked 2026-11-15). Difficulty is the LeetCode label from the same data.

| # | Problem | Difficulty | Asked at (per those lists) |
|---|---|---|---|
| 1 | Middle of the Linked List | Easy | Amazon, Google, Meta, Microsoft |
| 2 | Palindrome Linked List | Easy | Amazon, Google, Meta, Microsoft |
| 3 | Intersection of Two Linked Lists | Easy | Amazon, Google, Meta, Microsoft |
| 4 | Add Two Numbers | Medium | Amazon, Google, Meta, Microsoft |
| 5 | Linked List Cycle II | Medium | Amazon, Google, Meta, Microsoft |
| 6 | Reorder List | Medium | Amazon, Google, Meta, Microsoft |
| 7 | Copy List with Random Pointer | Medium | Amazon, Google, Meta, Microsoft |
| 8 | Merge k Sorted Lists | Hard | Amazon, Google, Meta, Microsoft |

## 8. Self-quiz (5 questions)

1. Why can you not jump straight to the 5th node of a linked list?
2. What is a dummy node and why is it useful?
3. In reversing a list, why must you save `curr.next` first?
4. In Floyd's cycle detection, why must the fast and slow pointers meet if there is a cycle?
5. Why does LRU Cache need BOTH a dictionary and a doubly linked list?

### Answers

1. You only hold the head. Each node only knows the next node, so you must follow the arrows one by one.
2. A fake node placed before the head. With it, adding or removing the head is the same as for any other node, and you return `dummy.next` at the end.
3. After you flip `curr.next` to point backward, the rest of the list is no longer reachable from `curr`. Saving it first keeps the link to the remaining nodes.
4. Inside the cycle, the fast pointer gains one step on the slow pointer each round, so the gap goes down by one each time until it is zero.
5. The dictionary finds a key in O(1). The doubly linked list moves a node to "most recent" and removes the oldest node in O(1). Either one alone makes one of the operations O(n).

Next: [08_trees_and_bst.md](08_trees_and_bst.md)
