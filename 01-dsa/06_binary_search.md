# Lesson 06. Binary Search (including search on the answer)

Before this lesson: [00_how_to_start.md](00_how_to_start.md).

---

## 1. What is this?

**Binary search** finds something by cutting the search area in HALF at every step. It works when the data has an order (for example a sorted list).

**Analogy 1: the number guessing game.** I think of a number from 1 to 100. You guess 50. I say "higher". Now you know the number is in 51 to 100, so you guess 75. I say "lower". Now it is 51 to 74. Every guess throws away half of the possibilities. After about 7 guesses you always win. Compare with guessing 1, 2, 3, ... which can take 100 guesses.

**Analogy 2: a paper dictionary.** You want the word "mango". You open the book in the middle. You see "kite". "Mango" comes after "kite", so you ignore the first half. You repeat on the second half.

Why is it fast? Each step halves the work. A list of 1,000,000 items needs about 20 steps. That is **O(log n)**.

### The three variables

- `lo` = the left end of the search area.
- `hi` = the right end of the search area.
- `mid` = the middle: `(lo + hi) // 2`. (The double slash `//` means "divide and drop the decimals".)

Every step we look at `mid` and move `lo` or `hi`.

### The big idea: search on the answer

Binary search does not need a list! It needs a **yes/no question whose answers look like this** as the number grows:

```text
number:    1   2   3   4   5   6   7   8
answer:   NO  NO  NO  YES YES YES YES YES
```

All NOs first, then all YESs (or the reverse). Binary search finds the border between NO and YES. Example question: "Can Koko finish her bananas at eating speed 5?" If speed 5 works, speed 6 also works. So the answers form NO, NO, ..., YES, YES. We search for the smallest YES.

## 2. When do I use it?

Words that give it away:

- "The array is **sorted**" (or "rotated sorted").
- "Find in O(log n)" / "do better than O(n)".
- "Find the **minimum** X such that ..." or "the **maximum** X such that ..." (search on the answer).
- "Minimum speed / capacity / days / size so that it is possible".
- "Minimize the maximum" or "maximize the minimum".
- "Find the first / last position of ...".
- "Peak", "boundary", "insert position".

Test for search on the answer: "If X works, do all bigger values also work (or all smaller values)?" If yes, use binary search.

## 3. A tiny example, traced line by line

Find `23` in the sorted list `[2, 5, 8, 12, 16, 23, 38, 56, 72, 91]` (indexes 0 to 9).

```text
index:  0  1  2   3   4   5   6   7   8   9
value:  2  5  8  12  16  23  38  56  72  91

lo=0, hi=9. mid = (0+9)//2 = 4. nums[4] = 16.  16 < 23, so the target is on the RIGHT. lo = mid+1 = 5.
lo=5, hi=9. mid = (5+9)//2 = 7. nums[7] = 56.  56 > 23, so the target is on the LEFT.  hi = mid-1 = 6.
lo=5, hi=6. mid = (5+6)//2 = 5. nums[5] = 23.  Found! Return index 5.
```

Three steps for ten items. If the target is missing, `lo` finally becomes bigger than `hi`, and we return -1.

## 4. Template code (a comment on every line)

```python
# TEMPLATE A: find an exact value in a sorted list (return its index, or -1)
def binary_search(nums, target):                 # function: index of target, or -1 if missing
    lo = 0                                       # left end of the search area
    hi = len(nums) - 1                           # right end of the search area
    while lo <= hi:                              # while the search area is not empty
        mid = (lo + hi) // 2                     # look at the middle position
        if nums[mid] == target:                  # is the middle the target?
            return mid                           # yes: done
        if nums[mid] < target:                   # the middle value is too small
            lo = mid + 1                         # the target is on the right: drop the left half
        else:                                    # the middle value is too big
            hi = mid - 1                         # the target is on the left: drop the right half
    return -1                                    # the area became empty: target is not there

print(binary_search([2, 5, 8, 12, 16, 23, 38, 56, 72, 91], 23))   # expect 5
assert binary_search([2, 5, 8, 12, 16, 23, 38, 56, 72, 91], 23) == 5   # found
assert binary_search([2, 5, 8], 7) == -1         # missing
assert binary_search([], 3) == -1                # empty list
assert binary_search([4], 4) == 0                # one item
```

```python
# TEMPLATE B: find the FIRST value x in [lo, hi] where is_ok(x) is True (the NO/YES border)
def first_true(lo, hi, is_ok):                   # function: smallest x with is_ok(x) True; is_ok(hi) must be True
    while lo < hi:                               # keep going while more than one candidate is left
        mid = (lo + hi) // 2                     # look at the middle candidate
        if is_ok(mid):                           # mid works: the answer is mid or something smaller
            hi = mid                             # keep mid in the search area
        else:                                    # mid does not work: the answer is bigger
            lo = mid + 1                         # drop mid and everything smaller
    return lo                                    # lo == hi: the first YES

print(first_true(1, 100, lambda x: x * x >= 50))     # expect 8  (8*8=64 is the first square >= 50)
assert first_true(1, 100, lambda x: x * x >= 50) == 8    # check
assert first_true(5, 5, lambda x: True) == 5             # one candidate
```

```python
# TEMPLATE C: lower bound (first index whose value is >= target) = where to insert target
def lower_bound(nums, target):                   # function: first index i with nums[i] >= target
    lo = 0                                       # leftmost possible answer
    hi = len(nums)                               # len(nums) is allowed: it means "after the end"
    while lo < hi:                               # while more than one candidate is left
        mid = (lo + hi) // 2                     # the middle candidate
        if nums[mid] >= target:                  # this value is big enough
            hi = mid                             # the answer is mid or to the left
        else:                                    # this value is too small
            lo = mid + 1                         # the answer is to the right
    return lo                                    # the first position that is >= target

print(lower_bound([1, 3, 5, 6], 5))              # expect 2
assert lower_bound([1, 3, 5, 6], 5) == 2         # exact match: its own index
assert lower_bound([1, 3, 5, 6], 2) == 1         # missing: where it would be inserted
assert lower_bound([1, 3, 5, 6], 7) == 4         # bigger than all: after the end
assert lower_bound([], 7) == 0                   # empty list
```

Why `mid = (lo + hi) // 2` is safe in Python: Python integers never overflow. (In Java or C++ you write `lo + (hi - lo) / 2`.)

Which template when? A: "is this exact value in the list?". B and C: "find the border" (first position / first value that works). Most hard problems are easier with B or C.

---

## 5. Classic problems

### Problem 1. Find First and Last Position of Element in Sorted Array

**Problem in plain words.** A sorted list may contain the target several times. Return the first and last index of the target. If it is missing, return `[-1, -1]`. Do it in O(log n).

Example: `nums = [5, 7, 7, 8, 8, 10]`, `target = 8` gives `[3, 4]`.

**Brute force.** Walk through the list and note the first and last matches. O(n). Too slow if the interviewer asks for O(log n).

**Better idea, slowly.** The first index of `8` is `lower_bound(8)` (the first index with value at least 8). The index just after the last `8` is `lower_bound(9)`, because 9 is the next integer. So the last index of `8` is `lower_bound(9) - 1`. First check that `8` really exists at `lower_bound(8)`.

```python
def lower_bound(nums, target):
    lo, hi = 0, len(nums)                          # search area: positions 0 to len(nums)
    while lo < hi:                                 # more than one candidate left
        mid = (lo + hi) // 2                       # middle candidate
        if nums[mid] >= target:                    # big enough
            hi = mid                               # answer is mid or left of it
        else:                                      # too small
            lo = mid + 1                           # answer is right of mid
    return lo                                      # first index with value >= target

def search_range(nums, target):
    first = lower_bound(nums, target)              # first index of target (if it exists)
    if first == len(nums) or nums[first] != target:    # past the end, or the value there is different
        return [-1, -1]                            # target is not in the list
    last = lower_bound(nums, target + 1) - 1       # just before the first value bigger than target
    return [first, last]                           # both ends

print(search_range([5, 7, 7, 8, 8, 10], 8))        # expect [3, 4]
assert search_range([5, 7, 7, 8, 8, 10], 8) == [3, 4]      # example
assert search_range([5, 7, 7, 8, 8, 10], 6) == [-1, -1]    # missing, but inside the range
assert search_range([], 0) == [-1, -1]                     # empty list
assert search_range([2, 2], 2) == [0, 1]                   # all items equal the target
assert search_range([1], 1) == [0, 0]                      # one item
```

**Trace** on `[5, 7, 7, 8, 8, 10]`, target 8:

```text
lower_bound(8): lo=0, hi=6
   mid=3 -> nums[3]=8 >= 8  -> hi=3
   mid=1 -> nums[1]=7 <  8  -> lo=2
   mid=2 -> nums[2]=7 <  8  -> lo=3          lo == hi == 3 -> first = 3. nums[3] is 8, so it exists.
lower_bound(9): lo=0, hi=6
   mid=3 -> nums[3]=8 <  9  -> lo=4
   mid=5 -> nums[5]=10 >= 9 -> hi=5
   mid=4 -> nums[4]=8 <  9  -> lo=5          lo == hi == 5 -> last = 5 - 1 = 4.
answer = [3, 4]
```

**Complexity.** Time O(log n): two binary searches. Space O(1).

**Two edge cases.** (1) The target is missing but inside the range (6 above): `nums[first]` is not the target, so return `[-1, -1]`. (2) The target is bigger than everything: `first == len(nums)`, so we check that BEFORE reading `nums[first]` (otherwise an index error).

**How interviewers twist it.** "Count how many times the target appears" (`last - first + 1`). "Search Insert Position." "Find the closest element to the target."

---

### Problem 2. Search in Rotated Sorted Array

**Problem in plain words.** A sorted list of distinct numbers was **rotated**: some items from the front were moved to the back. Example: `[0,1,2,4,5,6,7]` became `[4,5,6,7,0,1,2]`. Find the target's index in O(log n), or return -1.

Example: `nums = [4,5,6,7,0,1,2]`, `target = 0` gives `4`.

**Brute force.** Linear scan: O(n).

**Better idea, slowly.** The whole list is not sorted, but if you cut it at `mid`, **at least one half is sorted**. The trick:

1. Find `mid`. If it equals the target, done.
2. Decide which half is sorted. If `nums[lo] <= nums[mid]`, the LEFT half is sorted. Otherwise the RIGHT half is sorted.
3. Check whether the target lies inside the sorted half (by comparing with its two ends). If yes, search there. If no, search the other half.

```python
def search_rotated(nums, target):
    lo, hi = 0, len(nums) - 1                          # search area is the whole list
    while lo <= hi:                                    # while the search area is not empty
        mid = (lo + hi) // 2                           # middle position
        if nums[mid] == target:                        # found it
            return mid                                 # return the index
        if nums[lo] <= nums[mid]:                      # the LEFT half lo..mid is sorted
            if nums[lo] <= target < nums[mid]:         # does the target sit inside the left half?
                hi = mid - 1                           # yes: search the left half
            else:                                      # no
                lo = mid + 1                           # search the right half
        else:                                          # the RIGHT half mid..hi is sorted
            if nums[mid] < target <= nums[hi]:         # does the target sit inside the right half?
                lo = mid + 1                           # yes: search the right half
            else:                                      # no
                hi = mid - 1                           # search the left half
    return -1                                          # not found

print(search_rotated([4, 5, 6, 7, 0, 1, 2], 0))        # expect 4
assert search_rotated([4, 5, 6, 7, 0, 1, 2], 0) == 4   # example
assert search_rotated([4, 5, 6, 7, 0, 1, 2], 3) == -1  # missing
assert search_rotated([1], 0) == -1                    # one item, missing
assert search_rotated([3, 1], 1) == 1                  # two items
assert search_rotated([1, 2, 3, 4], 3) == 2            # not rotated at all
```

**Trace** on `[4,5,6,7,0,1,2]`, target 0:

```text
lo=0, hi=6, mid=3, nums[3]=7. Not the target.
   nums[lo]=4 <= nums[mid]=7 -> left half [4,5,6,7] is sorted.
   Is 4 <= 0 < 7? no -> target is not in the left half. lo = 4.
lo=4, hi=6, mid=5, nums[5]=1. Not the target.
   nums[lo]=0 <= nums[mid]=1 -> left half [0,1] is sorted.
   Is 0 <= 0 < 1? yes -> hi = 4.
lo=4, hi=4, mid=4, nums[4]=0. Found! return 4.
```

**Complexity.** Time O(log n): we halve the area each step. Space O(1).

**Two edge cases.** (1) Two items like `[3, 1]`: `nums[lo] <= nums[mid]` uses `<=` because `lo` can equal `mid`. With `<` it breaks. (2) A list that is not rotated at all: the logic still works.

**How interviewers twist it.** "The list has duplicates" (the sorted-half test can fail, worst case becomes O(n)). "Find the rotation point." "Find the minimum" (next problem).

---

### Problem 3. Find Minimum in Rotated Sorted Array

**Problem in plain words.** Same rotated list of distinct numbers. Return the smallest number in O(log n).

Example: `[3, 4, 5, 1, 2]` gives `1`.

**Brute force.** `min(nums)`: O(n).

**Better idea, slowly.** The minimum sits at the "break" where the list drops. Compare `nums[mid]` with the LAST number `nums[hi]`:

- If `nums[mid] > nums[hi]`, the drop is to the right of `mid` (the right part has the break). So the minimum is in `mid + 1 .. hi`. Move `lo = mid + 1`.
- Otherwise `nums[mid] <= nums[hi]`, the right part is sorted. The minimum is at `mid` or to its left. Move `hi = mid` (keep `mid`, it might be the answer).

This is a "first true" search, so we use `while lo < hi`.

```python
def find_min(nums):
    lo, hi = 0, len(nums) - 1                  # search area is the whole list
    while lo < hi:                             # until one candidate is left
        mid = (lo + hi) // 2                   # middle position
        if nums[mid] > nums[hi]:               # mid is in the big left part: the break is to the right
            lo = mid + 1                       # minimum is right of mid
        else:                                  # right part is sorted: the minimum is mid or left of it
            hi = mid                           # keep mid in the search area
    return nums[lo]                            # lo == hi: the smallest number

print(find_min([3, 4, 5, 1, 2]))               # expect 1
assert find_min([3, 4, 5, 1, 2]) == 1          # example
assert find_min([4, 5, 6, 7, 0, 1, 2]) == 0    # example 2
assert find_min([1, 2, 3]) == 1                # not rotated
assert find_min([2, 1]) == 1                   # two items
assert find_min([7]) == 7                      # one item
```

**Trace** on `[3, 4, 5, 1, 2]`:

```text
lo=0, hi=4, mid=2. nums[2]=5 > nums[4]=2 -> minimum is to the right. lo=3.
lo=3, hi=4, mid=3. nums[3]=1 > nums[4]=2? no -> hi=3.
lo=3, hi=3 -> stop. answer nums[3] = 1.
```

**Complexity.** Time O(log n). Space O(1).

**Two edge cases.** (1) Not rotated (`[1,2,3]`): `nums[mid] > nums[hi]` is never true, so `hi` keeps shrinking to 0. Answer 1. (2) One item: the loop does not start; we return `nums[0]`.

**How interviewers twist it.** "The list has duplicates" (when `nums[mid] == nums[hi]`, do `hi -= 1`; worst case O(n)). "Return how many times the list was rotated" (return the index `lo`). "Search in the rotated array" (combine).

---

### Problem 4. Koko Eating Bananas (search on the answer)

**Problem in plain words.** Koko has piles of bananas. The guards come back in `h` hours. Each hour Koko picks ONE pile and eats up to `k` bananas from it (if the pile has fewer than `k`, she eats the whole pile and wastes the rest of that hour). Find the smallest integer speed `k` so that she finishes all piles within `h` hours.

Example: `piles = [3, 6, 7, 11]`, `h = 8` gives `4`.

**Brute force.** Try `k = 1, 2, 3, ...` and compute the hours each time until it fits. If the biggest pile is `M`, this costs up to O(n * M).

**Better idea, slowly.**

1. Speed `k` takes `sum(ceil(pile / k))` hours. (`ceil` means round up.)
2. If speed `k` works, any faster speed also works. So the answers are `NO NO NO YES YES YES`. We want the first YES.
3. The speed is between 1 and `max(piles)` (eating the biggest pile in one hour is always fast enough, if `h >= number of piles`).
4. Use template B (`first_true`) on speeds from 1 to `max(piles)`.

To round up with whole numbers, use `(pile + k - 1) // k`.

```python
def min_eating_speed(piles, h):
    def hours_needed(k):                               # hours Koko needs at speed k
        return sum((p + k - 1) // k for p in piles)    # each pile takes ceil(p / k) hours

    lo, hi = 1, max(piles)                             # speed is between 1 and the biggest pile
    while lo < hi:                                     # find the smallest speed that works
        mid = (lo + hi) // 2                           # try the middle speed
        if hours_needed(mid) <= h:                     # fast enough: mid works
            hi = mid                                   # maybe a slower speed works too
        else:                                          # too slow
            lo = mid + 1                               # we need a faster speed
    return lo                                          # the smallest working speed

print(min_eating_speed([3, 6, 7, 11], 8))              # expect 4
assert min_eating_speed([3, 6, 7, 11], 8) == 4         # example
assert min_eating_speed([30, 11, 23, 4, 20], 5) == 30  # h equals the number of piles
assert min_eating_speed([30, 11, 23, 4, 20], 6) == 23  # one spare hour
assert min_eating_speed([10], 2) == 5                  # one pile
assert min_eating_speed([1, 1], 100) == 1              # lots of time: speed 1
```

**Trace** on `piles = [3, 6, 7, 11]`, `h = 8`:

```text
lo=1, hi=11
 mid=6: hours = 1 + 1 + 2 + 2 = 6  <= 8  -> works.   hi=6
 mid=3: hours = 1 + 2 + 3 + 4 = 10 >  8  -> too slow. lo=4
 mid=5: hours = 1 + 2 + 2 + 3 = 8  <= 8  -> works.   hi=5
 mid=4: hours = 1 + 2 + 2 + 3 = 8  <= 8  -> works.   hi=4
lo=4, hi=4 -> answer 4
```

**Complexity.** Time O(n log M): about log M steps (M = biggest pile), each step costs O(n) to compute the hours. Space O(1).

**Two edge cases.** (1) `h` equals the number of piles: Koko needs one pile per hour, so the speed must be `max(piles)`. (2) `h` is huge: the answer is 1.

**How interviewers twist it.** "Minimum number of days to make m bouquets." "Split array largest sum." "Magnetic force between balls" (maximize the minimum distance). "Smallest divisor given a threshold." Same pattern every time: write a `can_do(x)` function and binary search on `x`.

---

### Problem 5. Capacity To Ship Packages Within D Days

**Problem in plain words.** Packages have weights and must be shipped IN ORDER. Each day a ship carries consecutive packages, as long as the total weight is at most the ship's capacity. Find the smallest capacity that ships everything within `days` days.

Example: `weights = [1,2,3,4,5,6,7,8,9,10]`, `days = 5` gives `15`.

**Brute force.** Try capacity `max(weights), max(weights)+1, ...` until it works. Could be up to the total weight, each try costing O(n).

**Better idea, slowly.**

1. For a given capacity, count the days greedily: keep loading packages onto the current day until the next one would overflow, then start a new day.
2. If capacity `c` works, any bigger capacity also works. So: `NO NO NO YES YES`.
3. The smallest possible capacity is `max(weights)` (the heaviest package must fit). The biggest useful capacity is `sum(weights)` (everything in one day).
4. Binary search for the first YES.

```python
def ship_within_days(weights, days):
    def days_needed(capacity):                         # how many days a ship of this capacity needs
        count = 1                                      # we start on day 1
        load = 0                                       # weight loaded on the current day
        for w in weights:                              # packages in their given order
            if load + w > capacity:                    # this package does not fit today
                count += 1                             # start a new day
                load = 0                               # the new day starts empty
            load += w                                  # load the package
        return count                                   # total days

    lo, hi = max(weights), sum(weights)                # smallest and largest useful capacity
    while lo < hi:                                     # find the smallest capacity that works
        mid = (lo + hi) // 2                           # try the middle capacity
        if days_needed(mid) <= days:                   # fast enough: capacity works
            hi = mid                                   # maybe a smaller capacity works too
        else:                                          # needs too many days
            lo = mid + 1                               # we need a bigger capacity
    return lo                                          # smallest capacity that works

print(ship_within_days([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5))    # expect 15
assert ship_within_days([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5) == 15   # example
assert ship_within_days([3, 2, 2, 4, 1, 4], 3) == 6            # second example
assert ship_within_days([1, 2, 3, 1, 1], 4) == 3               # third example
assert ship_within_days([5, 5, 5], 1) == 15                    # one day: total weight
assert ship_within_days([5, 5, 5], 3) == 5                     # one package per day
```

**Trace** on `weights = [1..10]`, `days = 5`. The search starts at `lo = 10`, `hi = 55`.

```text
capacity 32 -> days: [1..7]=28, [8,9,10]=27   -> 2 days <= 5  works.  hi=32
capacity 21 -> [1..6]=21, [7,8]=15, [9,10]=19 -> 3 days <= 5  works.  hi=21
capacity 15 -> [1..5], [6,7], [8], [9], [10]   -> 5 days <= 5  works.  hi=15
capacity 12 -> [1..4], [5,6], [7], [8], [9], [10] -> 6 days > 5 fails.  lo=13
capacity 14 -> [1..4], [5,6], [7], [8], [9], [10] -> 6 days > 5 fails.  lo=15
lo = hi = 15 -> answer 15
```

(The mids tried are 32, 21, 15, 12, 14 in this order.)

**Complexity.** Time O(n log(sum of weights)). Space O(1).

**Two edge cases.** (1) `days = 1`: the answer is the total weight. (2) `days >= number of packages`: the answer is the heaviest single package (this is why `lo` starts at `max(weights)`, NOT at 1).

**How interviewers twist it.** "Split Array Largest Sum" (identical idea). "Painter's partition." "Minimum days to deliver all orders." "Allocate books to students."

---

## 6. Common mistakes

1. **Infinite loop.** With `while lo < hi` and `hi = mid`, you must use `lo = mid + 1` on the other side. With `lo = mid` the loop can freeze.
2. **Mixing the two styles.** Style 1: `while lo <= hi` with `hi = mid - 1` (exact search). Style 2: `while lo < hi` with `hi = mid` (border search). Do not mix them.
3. **Wrong search range.** The smallest useful capacity is `max(weights)`, not 1.
4. **Not proving the yes/no is monotone.** If bigger values might fail while smaller succeed, binary search is invalid.
5. **Using `<` instead of `<=`** in the rotated-array half test.
6. **Reading `nums[first]` when `first == len(nums)`.** Index error.
7. **Using binary search on unsorted data.**
8. **Rounding errors.** Use integer ceil `(a + b - 1) // b`, not floats.

## 7. Practice list (8 more problems)

"Asked at" means the problem appears on that company's list in the community repo [liquidslr/leetcode-company-wise-problems](https://github.com/liquidslr/leetcode-company-wise-problems) (checked 2026-11-15). Difficulty is the LeetCode label from the same data. (The plain "Binary Search" problem is Template A; solve it first.)

| # | Problem | Difficulty | Asked at (per those lists) |
|---|---|---|---|
| 1 | Search Insert Position | Easy | Amazon, Google, Meta, Microsoft |
| 2 | Sqrt(x) | Easy | Amazon, Google, Meta, Microsoft |
| 3 | Search a 2D Matrix | Medium | Amazon, Google, Meta, Microsoft |
| 4 | Find Peak Element | Medium | Amazon, Google, Meta, Microsoft |
| 5 | Single Element in a Sorted Array | Medium | Amazon, Google, Meta, Microsoft |
| 6 | Minimum Number of Days to Make m Bouquets | Medium | Amazon, Google, Meta, Microsoft |
| 7 | Time Based Key-Value Store | Medium | Amazon, Google, Meta, Microsoft |
| 8 | Median of Two Sorted Arrays | Hard | Amazon, Google, Meta, Microsoft |

## 8. Self-quiz (5 questions)

1. About how many steps does binary search need for a sorted list of 1,000,000 items?
2. What is the difference between `while lo <= hi` and `while lo < hi`? When do you use each?
3. What is "search on the answer"? What must be true for it to work?
4. In Koko Eating Bananas, why is the search range `1` to `max(piles)`?
5. In the rotated array search, how do you decide which half is sorted?

### Answers

1. About 20 steps (log base 2 of 1,000,000 is about 20).
2. `lo <= hi` with `hi = mid - 1` is for finding an exact value (the area can become empty). `lo < hi` with `hi = mid` is for finding a border (the first position that works).
3. We binary search over possible answers, not over a list. It works if the yes/no question is monotone: all NOs first, then all YESs (or the reverse).
4. Speed 1 is the slowest sensible speed. Speed `max(piles)` finishes any pile in one hour, so it always works (when `h >= number of piles`); nothing faster is needed.
5. If `nums[lo] <= nums[mid]`, the left half is sorted. Otherwise the right half is sorted.

Next: [07_linked_lists.md](07_linked_lists.md)
