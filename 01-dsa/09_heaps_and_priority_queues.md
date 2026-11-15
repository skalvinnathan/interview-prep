# Lesson 09: Heaps and Priority Queues

All code is Python 3.9. Every code block in this file was run with `python3` (3.9.6) before it was written here.

---

## Words you need first

- **Heap**: a pile of numbers where the **smallest number is always on top**. You can take the top very fast.
- **Priority queue**: a line where the most important item goes first (not the item who came first). A heap is the usual way to build it.
- **Min-heap**: smallest on top. Python's `heapq` is a min-heap.
- **Max-heap**: biggest on top. Python has no direct one. Trick: store negative numbers.
- **O(log n)**: very cheap growth. For 1,000,000 items, about 20 steps.
- **O(n log n)**: sorting cost. For 1,000,000 items, about 20,000,000 steps.

---

## 1. What is this?

A heap is a box that answers one question very fast: **"who is the smallest right now?"**

**Analogy: the hospital emergency room.**
People do not see the doctor in order of arrival. The sickest person goes first. A new patient can arrive at any time, and the nurse always knows who is next. The nurse does not sort the whole waiting room again each time. She only needs the most urgent one.

A heap does the same:
- `push(x)`: a new patient arrives. Cost O(log n).
- `pop()`: take the most urgent one. Cost O(log n).
- `peek` (`heap[0]`): look at the most urgent one without taking it. Cost O(1).

**How is it stored?** As a plain Python list, but with a rule: the item at index `i` is never bigger than its children at index `2*i+1` and `2*i+2`. This is a "tree drawn inside a list". Only the top (index 0) is guaranteed to be the smallest. The rest is only *partly* ordered. That is why a heap is cheap: it does less work than full sorting.

---

## 2. When do I use it?

Look for these words in the problem:

| Words in the problem | Idea |
|---|---|
| "**K largest**", "**K smallest**", "**top K**", "K most frequent", "K closest" | Keep a heap of size K |
| "**Kth** largest / smallest" | Heap of size K, the top is the answer |
| "**merge K sorted** lists / arrays" | Heap holding the front item of each list |
| "**median** of a stream" | Two heaps (one max, one min) |
| "always process the **smallest / earliest / cheapest** next" | Heap as priority queue |
| "schedule tasks", "meeting rooms (how many rooms)" | Heap of end times |

Rule of thumb: if you keep asking "what is the best item *so far*?" while new items keep arriving, think heap.

---

## 3. Trace of a tiny example (the heap list changing)

We push `5, 3, 8, 1` into an empty min-heap, then pop once.

How a push works: put the new item at the **end** of the list, then **swap it upward** with its parent while it is smaller than the parent. The parent of index `i` is index `(i-1)//2`.

```
start:                heap = []
push 5:   [5]                           heap = [5]
push 3:   append -> [5, 3]
          index1 parent is index0 (5). 3 < 5 -> swap
                                        heap = [3, 5]
push 8:   append -> [3, 5, 8]
          index2 parent is index0 (3). 8 < 3? no -> stop
                                        heap = [3, 5, 8]
push 1:   append -> [3, 5, 8, 1]
          index3 parent is index1 (5). 1 < 5 -> swap -> [3, 1, 8, 5]
          index1 parent is index0 (3). 1 < 3 -> swap -> [1, 3, 8, 5]
                                        heap = [1, 3, 8, 5]
```

As a picture (the list drawn as a tree):

```
        1
      /   \
     3     8
    /
   5
```

Now `pop()`:

```
pop:      take the top: 1 (this is the answer we return)
          move the LAST item (5) to the top -> [5, 3, 8]
          sift down: compare 5 with its smaller child (3). 5 > 3 -> swap -> [3, 5, 8]
          5 has no children now -> stop
                                        heap = [3, 5, 8], returned 1
```

The code below prints the same thing, so you can check.

---

## 4. Template code

### 4a. The basic tools of `heapq`

```python
import heapq                                  # heapq is Python's built-in heap library

heap = []                                     # a heap is just an ordinary list
for x in [5, 3, 8, 1]:                        # go through the numbers one by one
    heapq.heappush(heap, x)                   # push x, the library keeps the heap rule true
print(heap)                                   # shows the list: [1, 3, 8, 5]
assert heap == [1, 3, 8, 5]                   # same as our hand trace above

print(heap[0])                                # peek at the smallest without removing: 1
smallest = heapq.heappop(heap)                # remove and return the smallest
print(smallest, heap)                         # shows: 1 [3, 5, 8]
assert smallest == 1 and heap == [3, 5, 8]    # same as our hand trace above

nums = [9, 4, 7, 1]                           # an ordinary unsorted list
heapq.heapify(nums)                           # turn the list into a heap in place, cost O(n)
print(nums[0])                                # the smallest is now on top: 1
assert nums[0] == 1                           # check it

# MAX-heap trick: store the NEGATIVE of each number
maxheap = []                                  # this heap will behave like a max-heap
for x in [5, 3, 8, 1]:                        # same numbers again
    heapq.heappush(maxheap, -x)               # push the negative, so the biggest becomes the smallest
print(-maxheap[0])                            # undo the minus sign: biggest is 8
assert -maxheap[0] == 8                       # check it

# tuples are compared left to right, so (priority, thing) works
tasks = []                                    # a heap of (priority, name) pairs
heapq.heappush(tasks, (2, "write code"))      # priority 2
heapq.heappush(tasks, (1, "wake up"))         # priority 1 is more urgent
print(heapq.heappop(tasks))                   # shows: (1, 'wake up')
assert heapq.heappop(tasks) == (2, "write code")  # the other one comes second

print(heapq.nlargest(2, [3, 2, 1, 5, 6, 4]))  # shortcut: the 2 biggest -> [6, 5]
print(heapq.nsmallest(2, [3, 2, 1, 5, 6, 4])) # shortcut: the 2 smallest -> [1, 2]
```

### 4b. The "top K" template (heap of size K)

Idea: keep only K items in a **min-heap**. The top of the heap is the *weakest of the K strong ones*. A new item must beat the top to enter.

```python
import heapq                                  # we need the heap library


def top_k_largest(nums, k):                   # return the k biggest numbers (any order)
    heap = []                                 # min-heap that will hold at most k numbers
    for x in nums:                            # look at every number once
        if len(heap) < k:                     # room left in the heap?
            heapq.heappush(heap, x)           # yes: just add it
        elif x > heap[0]:                     # heap full: is x bigger than the weakest of the K?
            heapq.heapreplace(heap, x)        # yes: pop the weakest and push x in one step
        # else: x is too small, ignore it     # (a comment line, nothing runs)
    return heap                               # the heap holds the k biggest numbers


result = top_k_largest([3, 2, 1, 5, 6, 4], 2)  # try it on a small example
print(sorted(result))                         # shows: [5, 6]
assert sorted(result) == [5, 6]               # check it
```

Cost: each number costs at most O(log k). Total O(n log k). Space O(k).

---

## 5. Classic problems

### 5.1 Kth Largest Element in an Array (LeetCode 215)

**In plain words.** You get a list of numbers. Give the number that would be in position K if you sorted the list from biggest to smallest. Example: `[3,2,1,5,6,4]`, `k=2` gives `5`.

**Brute force.** Sort the list, then take the item at position `len - k`. Cost O(n log n) time. This is fine and simple. Say it first in an interview, then improve.

**Better idea, slowly.**
1. We only care about the K biggest numbers. We do not care about the order of the others.
2. Keep a min-heap of size K. It holds "the K biggest seen so far".
3. The top of that heap is the *smallest of the K biggest*. That is exactly the Kth largest.
4. For every new number: if it is bigger than the top, it deserves to be inside. Replace the top with it.

Why a min-heap and not a max-heap? Because we need quick access to the *weakest* member, so we can kick it out.

```python
import heapq                                  # heap library
from typing import List                       # type hints for readability


def find_kth_largest(nums: List[int], k: int) -> int:   # return the kth largest number
    heap = []                                 # min-heap holding the k biggest so far
    for x in nums:                            # visit each number once
        if len(heap) < k:                     # heap not full yet
            heapq.heappush(heap, x)           # add x
        elif x > heap[0]:                     # heap full and x beats the weakest member
            heapq.heapreplace(heap, x)        # remove weakest, add x (one O(log k) step)
    return heap[0]                            # the weakest of the k biggest = kth largest


print(find_kth_largest([3, 2, 1, 5, 6, 4], 2))             # expect 5
print(find_kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4))    # expect 4
assert find_kth_largest([3, 2, 1, 5, 6, 4], 2) == 5        # check example 1
assert find_kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4  # check example 2
assert find_kth_largest([1], 1) == 1                       # edge case: single item
assert find_kth_largest([2, 2, 2], 2) == 2                 # edge case: duplicates
```

**Trace** on `[3,2,1,5,6,4]`, `k=2`:

```
x=3: heap size 0 < 2 -> push        heap = [3]
x=2: heap size 1 < 2 -> push        heap = [2, 3]
x=1: heap full. 1 > heap[0]=2? no -> skip     heap = [2, 3]
x=5: heap full. 5 > 2? yes -> replace top     heap = [3, 5]
x=6: heap full. 6 > 3? yes -> replace top     heap = [5, 6]
x=4: heap full. 4 > 5? no -> skip             heap = [5, 6]
answer = heap[0] = 5
```

**Complexity.** Time O(n log k): we touch n numbers, and each heap step costs log k. Space O(k): the heap never has more than k items.

**Edge cases.**
1. `k = 1` means the maximum. The heap has one item.
2. Duplicates: `[2,2,2]`, `k=2` gives `2`. Duplicates count as separate items.

**How interviewers twist it.**
- "Now the numbers arrive as a stream, and you must answer after each one" (LeetCode 703). The same heap works, just keep it alive between calls.
- "Can you do it in O(n) average?" Answer: **quickselect** (partition like quicksort, go into one side only). Mention it, and say you would use the heap for safety.
- "Memory is tiny": the heap of size K is the answer, because you never store all n items.

---

### 5.2 Top K Frequent Elements (LeetCode 347)

**In plain words.** Given a list, return the K values that appear the most times. `[1,1,1,2,2,3]`, `k=2` gives `[1,2]`.

**Brute force.** Count every value with a dictionary. Sort all (value, count) pairs by count. Take the first K. Cost O(n log n) because up to n different values may exist.

**Better idea, slowly.**
1. Step one is always the same: **count** with a dictionary (`Counter`). Cost O(n).
2. Now we have pairs `(value, count)`. We want the K pairs with the biggest count. This is "top K" again.
3. Use the top-K template, but compare by **count**. Push `(count, value)` so Python compares counts first.
4. Keep the heap at size K. When it is too big, pop the smallest count.

```python
import heapq                                  # heap library
from collections import Counter               # Counter counts items for us
from typing import List                       # type hints


def top_k_frequent(nums: List[int], k: int) -> List[int]:   # return the k most frequent values
    counts = Counter(nums)                    # counts[v] = how many times v appears
    heap = []                                 # min-heap of (count, value), at most k items
    for value, count in counts.items():       # go through each distinct value
        heapq.heappush(heap, (count, value))  # push the pair, smallest count floats to the top
        if len(heap) > k:                     # too many in the heap?
            heapq.heappop(heap)               # remove the one with the smallest count
    return [value for count, value in heap]   # keep only the values


print(sorted(top_k_frequent([1, 1, 1, 2, 2, 3], 2)))       # expect [1, 2]
assert sorted(top_k_frequent([1, 1, 1, 2, 2, 3], 2)) == [1, 2]   # check example 1
assert top_k_frequent([1], 1) == [1]                        # edge case: one element
assert sorted(top_k_frequent([4, 4, 5, 5, 6], 2)) == [4, 5] # edge case: tie, only two fit
```

**Trace** on `[1,1,1,2,2,3]`, `k=2`:

```
counts = {1: 3, 2: 2, 3: 1}
value=1, count=3: push (3,1)          heap = [(3,1)]
value=2, count=2: push (2,2)          heap = [(2,2), (3,1)]
value=3, count=1: push (1,3)          heap = [(1,3), (3,1), (2,2)]  size 3 > 2
                  pop smallest (1,3)  heap = [(2,2), (3,1)]
return values -> [2, 1]  (order does not matter)
```

**Complexity.** Time O(n + m log k) where m is the number of distinct values (m is at most n). Counting is O(n). Each of m pushes costs log k. Space O(m) for the counter plus O(k) for the heap.

**Edge cases.**
1. Only one distinct value: the answer is that value.
2. Ties at the border: the problem usually promises a unique answer. If not, ask the interviewer how to break ties.

**How interviewers twist it.**
- "Do better than O(n log n)": **bucket sort**. Make a list of buckets where index = count. Put each value into `buckets[count]`. Walk from the highest count down. This is O(n).
- "Top K frequent *words*, tie broken alphabetically" (LeetCode 692): push `(-count, word)` so that more frequent comes first and alphabetical order breaks ties.
- "Top K in a stream that never ends": keep the counter and a heap, and discuss approximate methods (count-min sketch) if asked.

---

### 5.3 Merge K Sorted Lists (LeetCode 23)

**In plain words.** You get K linked lists. Each list is already sorted from small to big. Merge them into ONE sorted linked list.

**Brute force.** Put every value in one Python list, sort it, and build a new linked list. Cost O(N log N), where N is the total number of values. It works, but it ignores that the lists are already sorted.

**Better idea, slowly.**
1. Picture K queues of people, each sorted by height. You want one line sorted by height.
2. The next person in the final line must be the shortest among the **fronts** of the K queues.
3. So hold only the K fronts in a min-heap. Take the smallest front. Then put *the next person from that same queue* into the heap.
4. Repeat until the heap is empty.

The heap never has more than K items, so each step costs O(log K).

Trap: if two fronts have equal values, Python tries to compare the next tuple item, which would be the `ListNode`. Nodes cannot be compared, and Python raises an error. So we add a small unique number (`order`) in the middle: `(value, order, node)`.

```python
import heapq                                  # heap library
from typing import List, Optional             # type hints


class ListNode:                               # one box in a linked list
    def __init__(self, val=0, next=None):     # a box has a value and a pointer to the next box
        self.val = val                        # store the value
        self.next = next                      # store the pointer


def build(values: List[int]) -> Optional[ListNode]:   # helper: make a linked list from a Python list
    dummy = ListNode()                        # a fake first box so we can append easily
    tail = dummy                              # tail points to the last box so far
    for v in values:                          # each value in order
        tail.next = ListNode(v)               # add a new box after tail
        tail = tail.next                      # move tail forward
    return dummy.next                         # skip the fake box


def to_list(node: Optional[ListNode]) -> List[int]:   # helper: linked list back to Python list
    out = []                                  # collected values
    while node:                               # while there is a box
        out.append(node.val)                  # save its value
        node = node.next                      # go to the next box
    return out                                # done


def merge_k_lists(lists: List[Optional[ListNode]]) -> Optional[ListNode]:   # main function
    heap = []                                 # min-heap of (value, order, node)
    order = 0                                 # unique counter to break ties between equal values
    for node in lists:                        # look at the front box of every list
        if node:                              # skip empty lists
            heapq.heappush(heap, (node.val, order, node))   # add the front box
            order += 1                        # next unique number
    dummy = ListNode()                        # fake first box of the answer
    tail = dummy                              # tail of the answer
    while heap:                               # while some list still has boxes
        val, _, node = heapq.heappop(heap)    # take the smallest front box
        tail.next = node                      # attach it to the answer
        tail = tail.next                      # move the answer's tail
        if node.next:                         # does that list have a next box?
            heapq.heappush(heap, (node.next.val, order, node.next))   # push the next box
            order += 1                        # next unique number
    return dummy.next                         # skip the fake box


lists = [build([1, 4, 5]), build([1, 3, 4]), build([2, 6])]   # the example from the problem
print(to_list(merge_k_lists(lists)))          # expect [1, 1, 2, 3, 4, 4, 5, 6]
assert to_list(merge_k_lists([build([1, 4, 5]), build([1, 3, 4]), build([2, 6])])) == [1, 1, 2, 3, 4, 4, 5, 6]   # check
assert merge_k_lists([]) is None              # edge case: no lists at all
assert merge_k_lists([None, None]) is None    # edge case: all lists empty
assert to_list(merge_k_lists([None, build([7])])) == [7]   # edge case: one empty, one not
```

**Trace** on `[1,4,5]`, `[1,3,4]`, `[2,6]`:

```
start: push the fronts: (1,#0) from list A, (1,#1) from list B, (2,#2) from list C
heap holds: 1A, 1B, 2C                      answer = []
pop 1A -> answer [1]; A's next is 4 -> push 4A      heap: 1B, 2C, 4A
pop 1B -> answer [1,1]; B's next is 3 -> push 3B    heap: 2C, 3B, 4A
pop 2C -> answer [1,1,2]; C's next is 6 -> push 6C  heap: 3B, 4A, 6C
pop 3B -> answer [1,1,2,3]; B's next is 4 -> push 4B   heap: 4A, 4B, 6C
pop 4A -> answer [1,1,2,3,4]; A's next is 5 -> push 5A  heap: 4B, 5A, 6C
pop 4B -> answer [...,4,4]; B has no next            heap: 5A, 6C
pop 5A -> answer [...,5]; A has no next              heap: 6C
pop 6C -> answer [...,6]; C has no next              heap: empty -> done
final: [1,1,2,3,4,4,5,6]
```

**Complexity.** Time O(N log K): every one of the N boxes is pushed and popped once, each costing log K. Space O(K) for the heap (the answer reuses the old boxes).

**Edge cases.**
1. `lists = []` or all lists empty: return `None`.
2. One list is much longer than the others: the heap simply shrinks to one item and still works.

**How interviewers twist it.**
- "Do it without a heap": **divide and conquer**. Merge lists two at a time (like merge sort). Also O(N log K), space O(1) extra.
- "Merge K sorted *arrays*" or "K sorted files that don't fit in memory": same heap idea, with `(value, array_index, position)`.
- "Smallest range covering one element from each of K lists" (LeetCode 632): same heap, but also track the current maximum.

---

### 5.4 K Closest Points to Origin (LeetCode 973)

**In plain words.** You get points like `[x, y]`. Return the K points nearest to `(0, 0)`.

**Brute force.** Sort all points by distance and take the first K. O(n log n).

**Better idea, slowly.**
1. Distance is `sqrt(x*x + y*y)`. We do not need the square root. Comparing `x*x + y*y` gives the same order, and it avoids decimals.
2. We want the K *smallest* distances. "K smallest" means we keep a heap of size K where the top is the **largest** of the K (the worst one to kick out first). That is a **max-heap**.
3. Python has min-heaps, so store the negative distance.
4. For each point: push `(-dist, x, y)`. If the heap has more than K, pop. The popped one is the farthest, which is correct to throw away.

```python
import heapq                                  # heap library
from typing import List                       # type hints


def k_closest(points: List[List[int]], k: int) -> List[List[int]]:   # return k nearest points
    heap = []                                 # max-heap (by negative distance) with at most k points
    for x, y in points:                       # visit every point
        dist = x * x + y * y                  # squared distance, no square root needed
        heapq.heappush(heap, (-dist, x, y))   # push negative distance so the farthest is on top
        if len(heap) > k:                     # more than k points inside?
            heapq.heappop(heap)               # throw out the farthest one
    return [[x, y] for _, x, y in heap]       # drop the distances, return the points


print(sorted(k_closest([[1, 3], [-2, 2]], 1)))              # expect [[-2, 2]]
print(sorted(k_closest([[3, 3], [5, -1], [-2, 4]], 2)))     # expect [[-2, 4], [3, 3]]
assert sorted(k_closest([[1, 3], [-2, 2]], 1)) == [[-2, 2]]   # check example 1
assert sorted(k_closest([[3, 3], [5, -1], [-2, 4]], 2)) == [[-2, 4], [3, 3]]   # check example 2
assert k_closest([[0, 1]], 1) == [[0, 1]]     # edge case: one point
assert sorted(k_closest([[1, 1], [-1, -1], [2, 2]], 2)) == [[-1, -1], [1, 1]]  # edge case: equal distances
```

**Trace** on `[[3,3],[5,-1],[-2,4]]`, `k=2`:

```
point (3,3):  dist = 9+9 = 18    push (-18,3,3)         heap = [(-18,3,3)]
point (5,-1): dist = 25+1 = 26   push (-26,5,-1)        heap = [(-26,5,-1), (-18,3,3)]
point (-2,4): dist = 4+16 = 20   push (-20,-2,4)        size 3 > 2
              pop smallest tuple = (-26,5,-1), the farthest point
                                                         heap = [(-20,-2,4), (-18,3,3)]
answer = [[-2,4], [3,3]]
```

**Complexity.** Time O(n log k): n pushes, each at most log k. Space O(k).

**Edge cases.**
1. Several points at the same distance: the tuple falls back to comparing `x` then `y`, which are numbers, so no crash.
2. `k` equals the number of points: nothing is ever popped. Return all points.

**How interviewers twist it.**
- "n is huge and K is small": the heap of size K is the point of the question.
- "Closest to a different point (a, b)": subtract `a` and `b` first.
- "Do it in O(n) average": quickselect on the distances.

---

### 5.5 Find Median from a Data Stream (LeetCode 295)

**In plain words.** Numbers arrive one at a time. After each, you must be able to say the **median** (the middle value when sorted; if there are two middles, their average).

**Brute force.** Keep a list. After each number, sort and read the middle. Cost O(n log n) per query. Better: insert in sorted position with `bisect.insort` (O(n) per insert, O(1) per query). Still slow for a long stream.

**Better idea, slowly.**
1. Split all numbers into a **small half** and a **big half**, like cutting a sorted line in the middle.
2. The median lives at the cut. It is the **biggest of the small half** and/or the **smallest of the big half**.
3. Biggest of the small half: a **max-heap** (`lo`, stored as negatives).
4. Smallest of the big half: a **min-heap** (`hi`).
5. Rule: `lo` has the same size as `hi`, or one more. Then:
   - odd count: median is the top of `lo`.
   - even count: median is the average of both tops.
6. To add a number: put it in `lo`, move `lo`'s biggest to `hi` (this keeps every small number smaller than every big number), then if `hi` became bigger, move one back.

```python
import heapq                                  # heap library


class MedianFinder:                           # keeps a running median
    def __init__(self):                       # start empty
        self.lo = []                          # max-heap of the small half (stored as negatives)
        self.hi = []                          # min-heap of the big half

    def add_num(self, num: int) -> None:      # add one number from the stream
        heapq.heappush(self.lo, -num)         # put it in the small half first
        moved = -heapq.heappop(self.lo)       # take the biggest of the small half
        heapq.heappush(self.hi, moved)        # and give it to the big half
        if len(self.hi) > len(self.lo):       # big half grew larger than small half?
            back = heapq.heappop(self.hi)     # take the smallest of the big half
            heapq.heappush(self.lo, -back)    # return it to the small half

    def find_median(self) -> float:           # read the median now
        if len(self.lo) > len(self.hi):       # odd count: small half has one extra
            return float(-self.lo[0])         # median is the biggest of the small half
        return (-self.lo[0] + self.hi[0]) / 2.0   # even count: average of the two middle numbers


mf = MedianFinder()                           # make a finder
medians = []                                  # collect the medians after each number
for n in [5, 15, 1, 3]:                       # stream from our trace
    mf.add_num(n)                             # add the number
    medians.append(mf.find_median())          # read the median
print(medians)                                # expect [5.0, 10.0, 5.0, 4.0]
assert medians == [5.0, 10.0, 5.0, 4.0]       # check it
m2 = MedianFinder()                           # edge case: negative numbers and duplicates
for n in [-1, -1, -1]:                        # three equal negatives
    m2.add_num(n)                             # add each
assert m2.find_median() == -1.0               # median is -1
m3 = MedianFinder()                           # edge case: single number
m3.add_num(42)                                # add it
assert m3.find_median() == 42.0               # median is that number
```

**Trace** on the stream `5, 15, 1, 3` (`lo` is shown as real numbers, biggest first, to make it readable):

```
add 5:   lo={5}        hi={}          (push 5 to lo, move 5 to hi, hi bigger -> move 5 back)
         median: lo is bigger -> 5
add 15:  push to lo -> lo={15,5}; move 15 to hi -> lo={5}, hi={15}
         sizes equal (1 and 1) -> no move back
         median = (5 + 15) / 2 = 10
add 1:   push to lo -> lo={5,1}; move 5 to hi -> lo={1}, hi={5,15}
         hi bigger (2 vs 1) -> move 5 back -> lo={5,1}, hi={15}
         median: lo is bigger -> 5
add 3:   push to lo -> lo={5,3,1}; move 5 to hi -> lo={3,1}, hi={5,15}
         sizes equal -> no move back
         median = (3 + 5) / 2 = 4
```

Check by sorting: `[5]` median 5. `[5,15]` median 10. `[1,5,15]` median 5. `[1,3,5,15]` median (3+5)/2 = 4. It matches.

**Complexity.** `add_num`: O(log n), because a few heap pushes and pops happen. `find_median`: O(1), because we only read the tops. Space O(n) because every number is stored.

**Edge cases.**
1. Only one number so far: median is that number.
2. Even count: result may be a decimal (`.5`). Use `/ 2.0`.

**How interviewers twist it.**
- "All numbers are between 0 and 100": use a count array of size 101 and walk it. O(1) add.
- "99 percent of numbers are in 0 to 100": count array plus two small counters for the rest.
- "Sliding window median" (LeetCode 480): needs removal of old values. Harder. Say: lazy deletion with heaps, or a sorted list with `bisect`.

---

## 6. Common mistakes

1. **Thinking `heapq` is a max-heap.** It is a min-heap. For max, push negatives and remember to negate again when you read.
2. **Looking at `heap[1]` or the whole list and expecting it sorted.** Only `heap[0]` is guaranteed smallest. Use `sorted(heap)` if you need order.
3. **Using a max-heap of size K when you need a min-heap of size K.** For "K largest", keep the weakest of the strong on top, so use a **min**-heap. For "K smallest", use a **max**-heap (negatives).
4. **Pushing objects that cannot be compared** (like `ListNode`) when two keys tie. Add a unique counter in the tuple.
5. **Forgetting `heapq.heappush(heap, x)`** and writing `heap.append(x)`. The list will not stay a heap.
6. **Sorting when a heap would do.** Sorting everything for a K of 5 out of 10 million is wasteful.

---

## 7. Practice list (8 more problems)

Company tags below come from public LeetCode company-tag lists that I read (a GitHub mirror of those lists, snapshot Oct 2025; see lesson 19 for links). A tag means "the problem is in that company's list". It does not mean it is asked this year. No tag means I did not verify it.

| # | Problem | Difficulty | Tagged for |
|---|---|---|---|
| 1 | Kth Largest Element in a Stream (703) | Easy | not verified |
| 2 | Last Stone Weight (1046) | Easy | not verified |
| 3 | Task Scheduler (621) | Medium | Amazon, Google, Meta, Microsoft |
| 4 | Reorganize String (767) | Medium | Amazon |
| 5 | Meeting Rooms II (253) | Medium | Amazon, Google, Meta, Microsoft |
| 6 | Top K Frequent Words (692) | Medium | not verified |
| 7 | Find Median from Data Stream (295), solve it again from memory | Hard | Amazon, Google, Meta, Microsoft |
| 8 | Smallest Range Covering Elements from K Lists (632) | Hard | not verified |

---

## 8. Self-quiz (5 questions)

1. Python's `heapq` gives you which on top: the smallest or the biggest?
2. To find the 10 **largest** numbers in a huge list, do you keep a min-heap or a max-heap of size 10? Why?
3. What is the time cost of `heappush`, `heappop`, and `heap[0]`?
4. In "Merge K Sorted Lists", why do we put an extra counter in the tuple `(value, order, node)`?
5. In the two-heap median trick, which heap holds the small half, and how do we make it a max-heap?

**Answers.**
1. The smallest.
2. A **min**-heap of size 10. Its top is the weakest of the current top 10. A new number must beat it to enter, and then the weakest leaves.
3. `heappush` O(log n). `heappop` O(log n). `heap[0]` O(1).
4. When two values are equal, Python compares the next tuple item. `ListNode` objects cannot be compared and that raises an error. The counter is always different, so Python never reaches the node.
5. `lo` holds the small half. We store negative numbers in it, so Python's min-heap acts like a max-heap.
