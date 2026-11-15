# Lesson 13: Intervals (merge intervals, meeting rooms)

All code is Python 3.9. Every code block in this file was run with `python3` (3.9.6) before it was written here.

---

## Words you need first

- **Interval**: a start and an end, written `[start, end]`. Example: a meeting from 9 to 11 is `[9, 11]`.
- **Overlap**: two intervals share some time. `[1, 5]` and `[3, 8]` overlap on 3 to 5.
- **Touching**: the end of one equals the start of the other: `[1, 3]` and `[3, 5]`. Is this an overlap? **It depends on the problem.** In "Merge Intervals" touching intervals are merged. In "Meeting Rooms" back-to-back meetings do **not** need two rooms. Always ask or read the examples.
- **Sort by start**: arrange the intervals from the earliest start to the latest start.
- **Greedy**: at each step take the choice that looks best now, and never go back.

---

## 1. What is this?

Interval problems are about **time ranges** (or ranges of numbers): meetings, flights, bookings, ranges of IDs.

**Analogy: a calendar on your wall.**
If your meetings are written in random order on the wall, it is hard to see conflicts. If you **rewrite them in order of start time**, conflicts are easy to see: you only need to compare each meeting with the one just before it. Almost every interval problem is "sort first, then walk once from left to right".

The big trick: **sort by start time**. After sorting, two intervals can overlap only if they are neighbours (or a chain of neighbours). So you never compare far-apart intervals.

Two ways to think about overlap. For two intervals `a` and `b` where `a` starts first (`a.start <= b.start`):
- They overlap if `b.start <= a.end` (use `<` if touching does not count).
- When they overlap, the merged interval is `[a.start, max(a.end, b.end)]`. We need `max` because `b` may end *inside* `a` (like `[1, 10]` and `[2, 3]`).

---

## 2. When do I use it?

| Words in the problem | Idea |
|---|---|
| "**merge** overlapping intervals" | Sort by start, extend the last merged interval |
| "**insert** an interval into a sorted list" | Three phases: before, overlapping, after |
| "can a person attend **all meetings**" | Sort by start, check neighbours |
| "**minimum number of rooms / platforms / machines**" | Min-heap of end times (or sweep line) |
| "**remove** the minimum number of intervals so none overlap" | Greedy: sort by **end** time |
| "**free time**", "gaps between meetings" | Merge first, then look at the gaps |
| "intersection of two lists of intervals" | Two pointers |

---

## 3. Trace of a tiny example

Merge `[[8,10], [1,3], [2,6], [15,18]]`.

Step 0: sort by start.

```
sorted: [1,3]  [2,6]  [8,10]  [15,18]
```

Step 1: walk from left to right. `merged` is the answer list. We always compare the next interval with the **last** one in `merged`.

```
take [1,3]:   merged is empty -> add it.                       merged = [[1,3]]
take [2,6]:   last = [1,3]. Does 2 <= 3 ? yes -> overlap.
              extend the end: max(3, 6) = 6.                   merged = [[1,6]]
take [8,10]:  last = [1,6]. Does 8 <= 6 ? no -> gap. add it.   merged = [[1,6],[8,10]]
take [15,18]: last = [8,10]. Does 15 <= 10 ? no -> gap. add.   merged = [[1,6],[8,10],[15,18]]
```

Picture on a number line:

```
time:  1  2  3  4  5  6  7  8  9  10 ... 15 16 17 18
       [-----]                                         [1,3]
          [-----------]                                [2,6]
                            [-----]                    [8,10]
                                           [--------]  [15,18]
result [--------------]     [-----]        [--------]  [1,6] [8,10] [15,18]
```

---

## 4. Template code

### 4a. The "sort then sweep" template (merge)

```python
def merge_template(intervals):                # intervals is a list of [start, end]
    intervals = sorted(intervals, key=lambda x: x[0])   # sort by start time, keep the input untouched
    merged = []                               # the answer list
    for start, end in intervals:              # visit each interval from left to right
        if not merged or merged[-1][1] < start:   # first one, or a gap after the last merged interval
            merged.append([start, end])       # start a new merged interval
        else:                                 # they overlap (or touch)
            merged[-1][1] = max(merged[-1][1], end)   # stretch the last interval to cover this one
    return merged                             # all merged intervals


print(merge_template([[8, 10], [1, 3], [2, 6], [15, 18]]))   # expect [[1, 6], [8, 10], [15, 18]]
assert merge_template([[8, 10], [1, 3], [2, 6], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]   # same as the trace
```

### 4b. The "rooms" template (min-heap of end times)

```python
import heapq                                  # heap library


def min_rooms_template(intervals):            # how many rooms do we need at the same time?
    rooms = []                                # min-heap holding the END time of every room in use
    for start, end in sorted(intervals):      # go through meetings in order of start time
        if rooms and rooms[0] <= start:       # the room that frees up first is free by now
            heapq.heapreplace(rooms, end)     # reuse that room: its new end time is this meeting's end
        else:                                 # every room is still busy
            heapq.heappush(rooms, end)        # open a new room
    return len(rooms)                         # the number of rooms ever opened


print(min_rooms_template([[0, 30], [5, 10], [15, 20]]))   # expect 2
assert min_rooms_template([[0, 30], [5, 10], [15, 20]]) == 2   # same as the trace in 5.4
```

---

## 5. Classic problems

### 5.1 Merge Intervals (LeetCode 56)

**In plain words.** Given a list of intervals, merge all that overlap, and return the result. `[[1,3],[2,6],[8,10],[15,18]]` gives `[[1,6],[8,10],[15,18]]`.

**Brute force.** Compare every interval with every other interval, merge any pair that overlaps, and repeat until nothing changes. Cost is about O(n^2) or worse.

**Better idea, slowly.**
1. Sort by start. Now any interval can only overlap the **last merged one** (all earlier merged ones end before it begins, otherwise they would already be merged).
2. Walk through. If the new interval's start is bigger than the last merged end, there is a gap, so start a new merged interval.
3. Otherwise they overlap. Extend the last merged end with `max`. (Without `max`, `[1,10]` and `[2,3]` would wrongly shrink to `[1,3]`.)

```python
from typing import List                       # type hints


def merge(intervals: List[List[int]]) -> List[List[int]]:   # merge overlapping intervals
    intervals = sorted(intervals, key=lambda x: x[0])   # sort by start
    merged: List[List[int]] = []              # answer list
    for start, end in intervals:              # each interval in order
        if not merged or merged[-1][1] < start:   # no overlap with the last merged one
            merged.append([start, end])       # add as a new interval
        else:                                 # overlap or touching
            merged[-1][1] = max(merged[-1][1], end)   # extend the end, never shrink it
    return merged                             # done


print(merge([[1, 3], [2, 6], [8, 10], [15, 18]]))   # expect [[1, 6], [8, 10], [15, 18]]
assert merge([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]   # example 1
assert merge([[1, 4], [4, 5]]) == [[1, 5]]    # example 2: touching intervals are merged
assert merge([[1, 10], [2, 3]]) == [[1, 10]]  # edge case: one interval inside another (needs max)
assert merge([[5, 6]]) == [[5, 6]]            # edge case: a single interval
assert merge([]) == []                        # edge case: empty input
assert merge([[2, 3], [4, 5], [6, 7]]) == [[2, 3], [4, 5], [6, 7]]   # edge case: nothing overlaps
```

**Trace**: see section 3 (same idea, run on `[[8,10],[1,3],[2,6],[15,18]]`).

Second trace, to show why `max` matters, on `[[1,10],[2,3],[4,12]]`:

```
sorted: [1,10] [2,3] [4,12]
take [1,10]: empty -> add.                     merged = [[1,10]]
take [2,3]:  last end 10 < 2 ? no -> overlap.  end = max(10, 3) = 10.   merged = [[1,10]]
take [4,12]: last end 10 < 4 ? no -> overlap.  end = max(10, 12) = 12.  merged = [[1,12]]
```

**Complexity.** Time O(n log n): sorting dominates. The sweep is O(n). Space O(n) for the answer (and the sorted copy).

**Edge cases.**
1. Intervals that only touch (`[1,4]`, `[4,5]`): merged, because `4 < 4` is false.
2. An interval completely inside another: the `max` keeps the big end.

**How interviewers twist it.**
- "The input is already sorted": skip the sort, so it is O(n).
- "Intervals arrive one at a time" (Data Stream as Disjoint Intervals, LeetCode 352): keep a sorted structure and binary search.
- "Return the total covered length": sum `end - start` after merging.

---

### 5.2 Insert Interval (LeetCode 57)

**In plain words.** You get a list of **non-overlapping intervals sorted by start**, and one new interval. Insert the new one, and merge if needed. `[[1,3],[6,9]]` plus `[2,5]` gives `[[1,5],[6,9]]`.

**Brute force.** Append the new interval, then run Merge Intervals (sort and sweep). Cost O(n log n). It is correct, and a good first answer.

**Better idea, slowly (O(n), because the list is already sorted).**
Walk through the list in three phases:
1. **Before**: intervals that end **before** the new one starts (`end < new_start`). Copy them unchanged.
2. **Overlapping**: intervals that start **before or when** the new one ends (`start <= new_end`). Merge them into the new interval: `new_start = min(...)`, `new_end = max(...)`.
3. **After**: everything left. Copy unchanged.

Add the merged new interval between phase 1 and phase 3.

```python
from typing import List                       # type hints


def insert(intervals: List[List[int]], new_interval: List[int]) -> List[List[int]]:   # insert and merge
    result = []                               # the answer
    i, n = 0, len(intervals)                  # i is our position, n the length
    new_start, new_end = new_interval         # the interval we are inserting
    while i < n and intervals[i][1] < new_start:   # phase 1: intervals fully before the new one
        result.append(intervals[i])           # copy them unchanged
        i += 1                                # next interval
    while i < n and intervals[i][0] <= new_end:    # phase 2: intervals that overlap the new one
        new_start = min(new_start, intervals[i][0])   # the merged start is the smaller start
        new_end = max(new_end, intervals[i][1])       # the merged end is the bigger end
        i += 1                                # next interval
    result.append([new_start, new_end])       # put the merged new interval in place
    while i < n:                              # phase 3: intervals fully after
        result.append(intervals[i])           # copy them unchanged
        i += 1                                # next interval
    return result                             # done


print(insert([[1, 3], [6, 9]], [2, 5]))       # expect [[1, 5], [6, 9]]
assert insert([[1, 3], [6, 9]], [2, 5]) == [[1, 5], [6, 9]]   # example 1
assert insert([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]) == [[1, 2], [3, 10], [12, 16]]   # example 2: swallows three
assert insert([], [5, 7]) == [[5, 7]]         # edge case: empty list
assert insert([[1, 5]], [2, 3]) == [[1, 5]]   # edge case: new interval inside an old one
assert insert([[3, 5]], [0, 1]) == [[0, 1], [3, 5]]   # edge case: new interval goes first
assert insert([[1, 2]], [5, 6]) == [[1, 2], [5, 6]]   # edge case: new interval goes last
```

**Trace** on `[[1,2],[3,5],[6,7],[8,10],[12,16]]` with new `[4,8]`:

```
new_start=4, new_end=8
phase 1: [1,2]: end 2 < 4 ? yes -> copy.         result=[[1,2]]
         [3,5]: end 5 < 4 ? no -> stop phase 1.
phase 2: [3,5]: start 3 <= 8 ? yes -> new_start=min(4,3)=3, new_end=max(8,5)=8
         [6,7]: start 6 <= 8 ? yes -> new_start=3, new_end=max(8,7)=8
         [8,10]: start 8 <= 8 ? yes -> new_start=3, new_end=max(8,10)=10
         [12,16]: start 12 <= 10 ? no -> stop phase 2.
add [3,10]:                                       result=[[1,2],[3,10]]
phase 3: [12,16] -> copy.                         result=[[1,2],[3,10],[12,16]]
```

**Complexity.** Time O(n): each interval is looked at once. Space O(n) for the result.

**Edge cases.**
1. Empty list: result is just the new interval.
2. The new interval touches an old one (`[3,5]` and new `[5,7]`): phase 2 uses `<=`, so they merge.

**How interviewers twist it.**
- "Do it with binary search to find the place": the search is O(log n) but copying is still O(n).
- "Intervals are not sorted": append then use Merge Intervals.
- "Remove an interval range instead" (Remove Interval, LeetCode 1272): same three-way split of each old interval.

---

### 5.3 Meeting Rooms (LeetCode 252)

**In plain words.** Given meeting times `[start, end]`, can one person attend **all** of them? (That is: do no two meetings overlap?) Back-to-back meetings (`[5,10]` then `[10,15]`) are fine.

**Brute force.** Compare every pair of meetings. O(n^2).

**Better idea, slowly.**
1. Sort by start.
2. If any meeting starts **before** the previous meeting ends, there is an overlap, and the answer is `False`.
3. Only neighbours need checking, because the list is sorted.

```python
from typing import List                       # type hints


def can_attend_meetings(intervals: List[List[int]]) -> bool:   # True if no two meetings overlap
    intervals = sorted(intervals, key=lambda x: x[0])   # sort by start time
    for i in range(1, len(intervals)):        # compare each meeting with the one before it
        if intervals[i][0] < intervals[i - 1][1]:   # starts before the previous one ends
            return False                      # overlap found
    return True                               # no overlaps at all


print(can_attend_meetings([[0, 30], [5, 10], [15, 20]]))   # expect False
assert can_attend_meetings([[0, 30], [5, 10], [15, 20]]) is False   # example 1
assert can_attend_meetings([[7, 10], [2, 4]]) is True      # example 2
assert can_attend_meetings([[5, 10], [10, 15]]) is True    # edge case: back-to-back is fine
assert can_attend_meetings([]) is True        # edge case: no meetings
assert can_attend_meetings([[1, 2]]) is True  # edge case: one meeting
```

**Trace** on `[[0,30],[5,10],[15,20]]`:

```
sorted: [0,30] [5,10] [15,20]
i=1: [5,10] starts at 5. previous ends at 30. 5 < 30 ? yes -> overlap -> return False
```

And on `[[7,10],[2,4]]`:

```
sorted: [2,4] [7,10]
i=1: [7,10] starts at 7. previous ends at 4. 7 < 4 ? no -> fine
loop ends -> return True
```

**Complexity.** Time O(n log n) for the sort. Space O(n) for the sorted copy (O(1) extra if you sort in place).

**Edge cases.**
1. Back-to-back meetings: use `<`, not `<=`.
2. Zero or one meeting: always `True`.

**How interviewers twist it.**
- "How many rooms are needed?" The next problem.
- "Given a new meeting, can it be booked?" (My Calendar I, LeetCode 729): check overlap with each booked one, or use a sorted list with binary search.
- "Meetings can repeat daily": expand them first, or discuss modulo time.

---

### 5.4 Meeting Rooms II (LeetCode 253)

**In plain words.** Given meeting times, find the **minimum number of rooms** needed so that no two overlapping meetings share a room.

**Brute force.** For each meeting, count how many other meetings overlap its start time, and take the maximum. O(n^2).

**Better idea, slowly.**
1. Sort meetings by start time.
2. Keep a **min-heap of end times**, one for each room in use. The top is the room that becomes free first.
3. For each meeting: if the room freeing first is already free (`top <= start`), **reuse** it (replace its end time by this meeting's end). If not, **open a new room** (push the end time).
4. The number of rooms at the end is the size of the heap.

```python
import heapq                                  # heap library
from typing import List                       # type hints


def min_meeting_rooms(intervals: List[List[int]]) -> int:   # minimum rooms needed
    rooms: List[int] = []                     # min-heap with the end time of each room in use
    for start, end in sorted(intervals):      # meetings in order of start time
        if rooms and rooms[0] <= start:       # the earliest-ending room is free before this meeting starts
            heapq.heapreplace(rooms, end)     # reuse it: pop old end time, push the new one
        else:                                 # all rooms busy
            heapq.heappush(rooms, end)        # open a new room
    return len(rooms)                         # rooms opened = rooms needed


print(min_meeting_rooms([[0, 30], [5, 10], [15, 20]]))   # expect 2
assert min_meeting_rooms([[0, 30], [5, 10], [15, 20]]) == 2   # example 1
assert min_meeting_rooms([[7, 10], [2, 4]]) == 1          # example 2
assert min_meeting_rooms([[1, 5], [5, 10]]) == 1          # edge case: back-to-back reuses the room
assert min_meeting_rooms([]) == 0             # edge case: no meetings
assert min_meeting_rooms([[1, 10], [2, 9], [3, 8]]) == 3  # edge case: all overlap
```

**Trace** on `[[0,30],[5,10],[15,20]]` (the heap holds end times):

```
sorted: [0,30] [5,10] [15,20]
[0,30]:   rooms empty -> open a room.                            rooms = [30]
[5,10]:   earliest end is 30. 30 <= 5 ? no -> all busy, open one. rooms = [10, 30]
[15,20]:  earliest end is 10. 10 <= 15 ? yes -> reuse that room.
          replace 10 by 20.                                      rooms = [20, 30]
answer = len(rooms) = 2
```

**Complexity.** Time O(n log n): sorting, plus n heap operations each O(log n). Space O(n) for the heap.

**Edge cases.**
1. Back-to-back meetings share a room: the check is `rooms[0] <= start`.
2. All meetings overlap: the answer is n.

**How interviewers twist it.**
- "Sweep line without a heap": make two sorted lists, all starts and all ends. Walk with two pointers. When a start comes before the next end, add 1 to the current rooms; otherwise subtract 1. The answer is the highest value.
- "Return the actual room assignment": store `(end, room_id)` in the heap.
- "Car Pooling" (LeetCode 1094) and "Minimum Platforms" are the same problem in other clothes.

---

### 5.5 Non-overlapping Intervals (LeetCode 435)

**In plain words.** Given intervals, remove the **minimum number** of them so that the rest do not overlap. Touching is fine. `[[1,2],[2,3],[3,4],[1,3]]` gives `1` (remove `[1,3]`).

**Brute force.** Try every subset of intervals to remove, from small to large, and check. Exponential.

**Better idea, slowly (greedy).**
1. Think of it as the reverse: **keep as many intervals as possible**. Answer = total - kept.
2. Which interval should we keep first? The one that **ends earliest**. It leaves the most room for the others. (Like choosing the shortest-ending meeting so more meetings fit in your day.)
3. So sort by **end** time. Keep an interval if it starts at or after the end of the last kept one. Otherwise, it overlaps, so we **remove** it (count 1).

Why sort by end and not by start? A very long interval that starts early blocks many others. Sorting by end puts short-ending ones first, so we never regret choosing them.

```python
from typing import List                       # type hints


def erase_overlap_intervals(intervals: List[List[int]]) -> int:   # fewest intervals to remove
    if not intervals:                         # nothing to remove from an empty list
        return 0                              # zero removals
    intervals = sorted(intervals, key=lambda x: x[1])   # sort by END time
    last_end = intervals[0][1]                # we always keep the first one (it ends earliest)
    removed = 0                               # count of removed intervals
    for start, end in intervals[1:]:          # look at the rest in order
        if start >= last_end:                 # starts after (or when) the last kept one ends
            last_end = end                    # keep it, and now it is the last kept one
        else:                                 # overlaps the last kept one
            removed += 1                      # remove this one (it ends later, so it is the worse choice)
    return removed                            # the minimum number removed


print(erase_overlap_intervals([[1, 2], [2, 3], [3, 4], [1, 3]]))   # expect 1
assert erase_overlap_intervals([[1, 2], [2, 3], [3, 4], [1, 3]]) == 1   # example 1
assert erase_overlap_intervals([[1, 2], [1, 2], [1, 2]]) == 2           # example 2: three copies, keep one
assert erase_overlap_intervals([[1, 2], [2, 3]]) == 0                   # example 3: touching is fine
assert erase_overlap_intervals([]) == 0       # edge case: empty
assert erase_overlap_intervals([[1, 100], [11, 22], [1, 11], [2, 12]]) == 2   # edge case: a long interval blocks others
```

**Trace** on `[[1,2],[2,3],[3,4],[1,3]]`:

```
sort by end: [1,2] (end 2), [2,3] (end 3), [1,3] (end 3), [3,4] (end 4)
keep [1,2]:   last_end = 2, removed = 0
[2,3]: start 2 >= 2 ? yes -> keep. last_end = 3
[1,3]: start 1 >= 3 ? no  -> overlap. removed = 1
[3,4]: start 3 >= 3 ? yes -> keep. last_end = 4
answer = 1
```

**Complexity.** Time O(n log n) for the sort; one pass after. Space O(n) for the sorted copy.

**Edge cases.**
1. Identical intervals: keep one, remove the others.
2. Touching intervals are not overlapping: use `>=`.

**How interviewers twist it.**
- "Minimum Number of Arrows to Burst Balloons" (LeetCode 452): the same greedy, sorted by end. Count groups of overlapping balloons.
- "Maximum number of meetings you can attend": same as keeping the most intervals.
- "Weighted Job Scheduling": each interval has a profit. Greedy fails. Use dynamic programming (lessons 15 and 16).

---

## 6. Common mistakes

1. **Not sorting first.** Almost every solution here depends on sorted input.
2. **Forgetting `max` when merging.** `[1,10]` and `[2,3]` must stay `[1,10]`.
3. **Using `<` vs `<=` wrongly.** Decide: does touching count as overlap? Merge Intervals: yes (merge). Meeting Rooms: no. Test with `[1,2],[2,3]`.
4. **Sorting by start when the greedy needs sort by end** (Non-overlapping Intervals, Arrows). If your answer is wrong on a long interval, this is the usual reason.
5. **Changing the input list in place** when the caller may not want it. Use `sorted(...)`, not `.sort()`, unless told otherwise.
6. **Comparing the new interval with the first merged interval** instead of the **last**.
7. **Using a max-heap for rooms.** Rooms need the **earliest** end time on top, so a min-heap.

---

## 7. Practice list (8 more problems)

Tags come from public LeetCode company-tag lists I read (GitHub mirror, snapshot Oct 2025; see lesson 19). A tag means "the problem is in that company's list". No tag means not verified. For reference, the problems taught above are also tagged: Merge Intervals (Amazon, Google, Meta, Microsoft, Stripe), Insert Interval (Amazon, Google, Meta, Microsoft), Meeting Rooms II (Amazon, Google, Meta, Microsoft), Non-overlapping Intervals (Amazon, Google, Meta).

| # | Problem | Difficulty | Tagged for |
|---|---|---|---|
| 1 | Summary Ranges (228) | Easy | not verified |
| 2 | Interval List Intersections (986) | Medium | Meta |
| 3 | Minimum Number of Arrows to Burst Balloons (452) | Medium | not verified |
| 4 | My Calendar I (729) | Medium | not verified |
| 5 | Car Pooling (1094) | Medium | not verified |
| 6 | Remove Covered Intervals (1288) | Medium | not verified |
| 7 | Employee Free Time (759) | Hard | not verified |
| 8 | Data Stream as Disjoint Intervals (352) | Hard | not verified |

---

## 8. Self-quiz (5 questions)

1. Why do we sort intervals by start time before merging?
2. When you merge `[1,10]` and `[2,3]`, what must the new end be, and what code gives it?
3. In Meeting Rooms II, what does the heap hold and why do we need the smallest value on top?
4. For "remove the fewest intervals so none overlap", do we sort by start or by end? Why?
5. Do `[1,4]` and `[4,5]` overlap? Answer for Merge Intervals and for Meeting Rooms.

**Answers.**
1. After sorting, an interval can only overlap the last merged one, so we compare neighbours only. Without sorting we would have to compare all pairs.
2. The end must be 10. The code is `max(10, 3)`.
3. The heap holds the end time of each room in use. The smallest end time is the room that frees up first, and that is the only room we should try to reuse.
4. By end. The interval that ends earliest leaves the most room for the others, so choosing it first never costs us.
5. In Merge Intervals they merge into `[1,5]` (touching counts). In Meeting Rooms they do not overlap, so one room is enough.
