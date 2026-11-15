# Lesson 01. Arrays and Strings

Read [00_how_to_start.md](00_how_to_start.md) first. It explains Big-O and the 5-step method.

---

## 1. What is this?

An **array** is a row of boxes. Each box holds one value. Each box has a number called an **index**. The first box is index 0, not 1.

In Python an array is a `list`. A **string** is almost the same thing: a row of letters. The difference: you cannot change a letter inside a string. Strings are **immutable** (they cannot be changed). To "change" a string you build a new one.

**Analogy.** Think of a row of lockers in a school, numbered 0, 1, 2, 3, ... If I tell you "open locker 4", you walk straight to it. You do not check lockers 0 to 3 first. This is why reading by index is fast: O(1).

```text
index:   0    1    2    3    4
       +----+----+----+----+----+
nums = | 3  | 7  | 2  | 9  | 4  |
       +----+----+----+----+----+
```

Good to know:

- `nums[0]` is the first item. `nums[-1]` is the last item.
- `len(nums)` is how many items there are.
- A **subarray** is a piece of the array where items sit next to each other. Example: `[7, 2, 9]` is a subarray of the list above.

## 2. When do I use it?

Almost every problem has an array or string. These words tell you the "array tricks" are needed:

- "Given an array of integers..."
- "contiguous subarray" (items next to each other)
- "in place" (change the same list, no big new list)
- "maximum / minimum profit / sum / product"
- "merge", "rotate", "reverse", "sort first"
- "prefix", "running total"

Three ideas solve a huge part of array problems:

1. **One pass with a running answer.** Walk through the list once. Keep one or two variables, such as "best so far".
2. **Prefix sums.** Pre-compute running totals so any range sum is one subtraction.
3. **Sort first.** After sorting, neighbours are related. Merging and comparing become easy.

## 3. A tiny example, traced line by line

We find the biggest number in `[3, 7, 2, 9, 4]` with a running answer (see template A below).

```text
nums = [3, 7, 2, 9, 4]
best = nums[0]            -> best = 3

i = 1, nums[1] = 7  : is 7 > best (3)? yes -> best = 7
i = 2, nums[2] = 2  : is 2 > best (7)? no  -> best stays 7
i = 3, nums[3] = 9  : is 9 > best (7)? yes -> best = 9
i = 4, nums[4] = 4  : is 4 > best (9)? no  -> best stays 9

return best -> 9
```

We looked at each item one time. So the cost is O(n).

Prefix sums on `[2, 4, 1, 3]`:

```text
prefix starts as [0]
add 2 -> prefix = [0, 2]
add 4 -> prefix = [0, 2, 6]
add 1 -> prefix = [0, 2, 6, 7]
add 3 -> prefix = [0, 2, 6, 7, 10]

Sum of nums[1..2] (that is 4 + 1)  = prefix[3] - prefix[1] = 7 - 2 = 5
```

## 4. Template code (a comment on every line)

```python
# TEMPLATE A: one pass with a running answer
def running_max(nums):                  # function: takes a list, returns the biggest item
    best = nums[0]                      # start with the first item as the best so far
    for i in range(1, len(nums)):       # look at every other item, by index
        if nums[i] > best:              # is this item bigger than our best?
            best = nums[i]              # yes: remember it as the new best
    return best                         # after the loop, best is the biggest item

print(running_max([3, 7, 2, 9, 4]))     # expect 9
assert running_max([3, 7, 2, 9, 4]) == 9    # check it by machine
assert running_max([5]) == 5                # one item is fine too
```

```python
# TEMPLATE B: prefix sums (running totals)
def build_prefix(nums):                 # function: returns the list of running totals
    prefix = [0]                        # prefix[k] = sum of the first k items; starts at 0 items
    for x in nums:                      # go through each number once
        prefix.append(prefix[-1] + x)   # new total = last total + this number
    return prefix                       # the list of running totals

def range_sum(prefix, left, right):     # function: sum of nums[left..right] in O(1)
    return prefix[right + 1] - prefix[left]   # sum of nums[left..right], both included

p = build_prefix([2, 4, 1, 3])          # make the prefix list
print(p)                                # expect [0, 2, 6, 7, 10]
print(range_sum(p, 1, 2))               # expect 5  (4 + 1)
assert p == [0, 2, 6, 7, 10]            # check the list
assert range_sum(p, 1, 2) == 5          # check the range sum
assert range_sum(p, 0, 3) == 10         # whole array
```

```python
# TEMPLATE C: reverse in place by swapping from both ends
def reverse_string(s):                  # function: returns the string reversed
    chars = list(s)                     # strings cannot change, so copy letters to a list
    left = 0                            # pointer at the first letter
    right = len(chars) - 1              # pointer at the last letter
    while left < right:                 # stop when the pointers meet in the middle
        chars[left], chars[right] = chars[right], chars[left]   # swap the two letters
        left += 1                       # move the left pointer to the right
        right -= 1                      # move the right pointer to the left
    return "".join(chars)               # glue the letters back into one string

print(reverse_string("hello"))          # expect olleh
assert reverse_string("hello") == "olleh"   # normal case
assert reverse_string("") == ""             # empty string
assert reverse_string("a") == "a"           # one letter
```

---

## 5. Classic problems

### Problem 1. Best Time to Buy and Sell Stock

**Problem in plain words.** You get a list of prices, one price per day. You may buy on one day and sell on a LATER day, only once. What is the biggest profit? If you cannot make profit, return 0.

Example: `[7, 1, 5, 3, 6, 4]` gives `5` (buy at 1, sell at 6).

**Brute force.** Try every pair (buy day, sell day later). Keep the best profit. Cost: O(n^2) time, O(1) space. For 100,000 days that is about 5 billion pairs. Too slow.

**Better idea, slowly.** Imagine you walk through the days one by one. On each day you ask yourself one question: "If I sell TODAY, what is the best buy day so far?" The best buy day is simply the lowest price you saw before. So you keep two variables:

- `min_price` = the lowest price seen so far.
- `best` = the biggest profit seen so far.

For each price: first update `min_price`. Then profit today = `price - min_price`. Update `best`. One pass is enough.

```python
def max_profit(prices):
    min_price = float("inf")                 # lowest price seen so far (start at "infinity")
    best = 0                                 # best profit so far (0 means: do not trade)
    for price in prices:                     # walk through the days in order
        min_price = min(min_price, price)    # maybe today is the cheapest day so far
        best = max(best, price - min_price)  # profit if we sell today; keep the larger
    return best                              # the biggest profit we found

print(max_profit([7, 1, 5, 3, 6, 4]))        # expect 5
assert max_profit([7, 1, 5, 3, 6, 4]) == 5   # the example
assert max_profit([7, 6, 4, 3, 1]) == 0      # prices only fall: no profit
assert max_profit([5]) == 0                  # one day: cannot sell later
```

**Trace** on `[7, 1, 5, 3, 6, 4]`:

```text
price | min_price | price - min_price | best
  7   |    7      |        0          |  0
  1   |    1      |        0          |  0
  5   |    1      |        4          |  4
  3   |    1      |        2          |  4
  6   |    1      |        5          |  5
  4   |    1      |        3          |  5
answer = 5
```

**Complexity.** Time O(n) because we look at each price once. Space O(1) because we keep only two numbers.

**Two edge cases.** (1) Prices only go down, for example `[7, 6, 4, 3, 1]`: answer 0. (2) Only one price: answer 0.

**How interviewers twist it.** "You may buy and sell many times" (Best Time II: add every upward step). "With a cooldown day." "At most 2 (or k) transactions." "There is a fee per trade."

---

### Problem 2. Maximum Subarray (Kadane's idea)

**Problem in plain words.** Given a list of numbers (some negative), find the contiguous piece with the biggest sum. Return that sum.

Example: `[-2, 1, -3, 4, -1, 2, 1, -5, 4]` gives `6` (the piece `[4, -1, 2, 1]`).

**Brute force.** For every start and every end, add the numbers. With a running sum this is O(n^2) time. If you re-add from scratch each time, it is O(n^3).

**Better idea, slowly.** Walk left to right. At each number, ask: "Is it better to join the piece I was building, or to start a new piece here?"

- If my current piece has a **positive** total, joining helps.
- If my current piece has a **negative** total, it only hurts. I throw it away and start fresh at this number.

Formula: `cur = max(x, cur + x)`. Here `cur` is "the best sum of a piece that ENDS at this number". We also keep `best`, the biggest `cur` ever seen.

```python
def max_subarray(nums):
    cur = nums[0]                      # best sum of a piece that ends at the current item
    best = nums[0]                     # best sum seen anywhere
    for x in nums[1:]:                 # look at each remaining number
        cur = max(x, cur + x)          # either start fresh at x, or extend the old piece
        best = max(best, cur)          # remember the biggest piece sum so far
    return best                        # answer

print(max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]))   # expect 6
assert max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6   # the example
assert max_subarray([-3, -1, -2]) == -1                     # all negative: pick the least bad
assert max_subarray([5]) == 5                               # one item
```

**Trace** on `[-2, 1, -3, 4, -1, 2, 1, -5, 4]`:

```text
start: cur = -2, best = -2
x =  1: cur = max(1, -2+1=-1)  = 1   best = 1
x = -3: cur = max(-3, 1-3=-2)  = -2  best = 1
x =  4: cur = max(4, -2+4=2)   = 4   best = 4
x = -1: cur = max(-1, 4-1=3)   = 3   best = 4
x =  2: cur = max(2, 3+2=5)    = 5   best = 5
x =  1: cur = max(1, 5+1=6)    = 6   best = 6
x = -5: cur = max(-5, 6-5=1)   = 1   best = 6
x =  4: cur = max(4, 1+4=5)    = 5   best = 6
answer = 6
```

**Complexity.** Time O(n): one pass. Space O(1): two variables.

**Two edge cases.** (1) All numbers negative, such as `[-3, -1, -2]`: answer is `-1`. A common bug is to start `best` at 0 and wrongly return 0. (2) One number: return it.

**How interviewers twist it.** "Return the start and end index too" (remember where `cur` restarted). "The array is circular." "Maximum product subarray." "Subarray must have length at least k."

---

### Problem 3. Product of Array Except Self

**Problem in plain words.** Given a list `nums`, return a list `answer` where `answer[i]` is the product of all numbers EXCEPT `nums[i]`. You may not use division.

Example: `[1, 2, 3, 4]` gives `[24, 12, 8, 6]`.

**Brute force.** For each position, multiply all the other numbers. O(n^2) time.

**Why not divide?** Total product divided by `nums[i]` breaks when a number is 0. (And the problem forbids division.)

**Better idea, slowly.** The product of "everything except i" = (product of everything LEFT of i) x (product of everything RIGHT of i). So:

1. Pass left to right. Before using `nums[i]`, store the product of all items to its left in `result[i]`.
2. Pass right to left. Multiply `result[i]` by the product of all items to its right.

```python
def product_except_self(nums):
    n = len(nums)                          # how many numbers
    result = [1] * n                       # result starts as all 1s
    left = 1                               # product of everything to the left so far
    for i in range(n):                     # first pass: left to right
        result[i] = left                   # store product of all items left of i
        left *= nums[i]                    # now include nums[i] for the next position
    right = 1                              # product of everything to the right so far
    for i in range(n - 1, -1, -1):         # second pass: right to left
        result[i] *= right                 # multiply by product of all items right of i
        right *= nums[i]                   # include nums[i] for the next position (to its left)
    return result                          # each slot now has left * right

print(product_except_self([1, 2, 3, 4]))   # expect [24, 12, 8, 6]
assert product_except_self([1, 2, 3, 4]) == [24, 12, 8, 6]   # the example
assert product_except_self([1, 0, 3, 4]) == [0, 12, 0, 0]    # one zero
assert product_except_self([0, 0, 2]) == [0, 0, 0]           # two zeros: everything is 0
```

**Trace** on `[1, 2, 3, 4]`:

```text
Pass 1 (left products):
i=0: result[0] = 1,  left becomes 1*1 = 1
i=1: result[1] = 1,  left becomes 1*2 = 2
i=2: result[2] = 2,  left becomes 2*3 = 6
i=3: result[3] = 6,  left becomes 6*4 = 24
result = [1, 1, 2, 6]

Pass 2 (multiply by right products):
i=3: result[3] = 6*1  = 6,   right becomes 1*4 = 4
i=2: result[2] = 2*4  = 8,   right becomes 4*3 = 12
i=1: result[1] = 1*12 = 12,  right becomes 12*2 = 24
i=0: result[0] = 1*24 = 24,  right becomes 24*1 = 24
result = [24, 12, 8, 6]
```

**Complexity.** Time O(n): two passes. Space O(1) extra (the output list is not counted).

**Two edge cases.** (1) One zero: only the slot of the zero is non-zero. (2) Two or more zeros: every slot is 0. Our method handles both without special code.

**How interviewers twist it.** "Do it with division, handle zeros." "Return the sum except self." "Same, but with a modulo." (They check you really see the left and right idea.)

---

### Problem 4. Merge Intervals

**Problem in plain words.** You get a list of intervals like `[start, end]`. Merge all that overlap. Return the merged list.

Example: `[[1,3],[2,6],[8,10],[15,18]]` gives `[[1,6],[8,10],[15,18]]`.

**Brute force.** Compare every pair. If two overlap, merge them. Repeat until nothing changes. This is O(n^2) or worse.

**Better idea, slowly.** If the intervals are **sorted by start**, then overlapping ones must be neighbours. So:

1. Sort by start.
2. Put the first interval in the answer.
3. For each next interval: if its start is less than or equal to the end of the last answer interval, they overlap. Stretch the last answer interval: new end = bigger of the two ends. Otherwise, there is a gap. Add it as a new interval.

Use `max` for the end, because a small interval can sit fully inside a big one (`[1,4]` and `[2,3]`).

```python
def merge_intervals(intervals):
    intervals = sorted(intervals, key=lambda p: p[0])    # sort by the start of each interval
    merged = [list(intervals[0])]                        # begin with a copy of the first interval
    for start, end in intervals[1:]:                     # look at the rest, in order
        if start <= merged[-1][1]:                       # starts before the last one ends: overlap
            merged[-1][1] = max(merged[-1][1], end)      # stretch the last interval if needed
        else:                                            # a gap: no overlap
            merged.append([start, end])                  # start a new interval
    return merged                                        # the final list

print(merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]))     # expect [[1, 6], [8, 10], [15, 18]]
assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]   # example
assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]        # touching counts as overlap
assert merge_intervals([[1, 4], [2, 3]]) == [[1, 4]]        # one inside another
assert merge_intervals([[5, 6], [1, 2]]) == [[1, 2], [5, 6]]    # unsorted input
```

**Trace** on `[[1,3],[2,6],[8,10],[15,18]]`:

```text
after sort: same order. merged = [[1,3]]
[2,6]  : 2 <= 3 (end of last)?  yes -> end = max(3,6) = 6   merged = [[1,6]]
[8,10] : 8 <= 6?                no  -> append               merged = [[1,6],[8,10]]
[15,18]: 15 <= 10?              no  -> append               merged = [[1,6],[8,10],[15,18]]
```

**Complexity.** Time O(n log n) because of the sort (the loop itself is O(n)). Space O(n) for the answer.

**Two edge cases.** (1) Intervals that touch, like `[1,4]` and `[4,5]`: they merge (ask if touching counts). (2) One interval fully inside another: the `max` keeps the bigger end. Also remember: the input may be unsorted.

**How interviewers twist it.** "Insert a new interval into a sorted list." "Minimum number of meeting rooms." "Find the free time gaps." "Intersection of two interval lists." This problem also appears on the Stripe list in the public repo from lesson 00.

---

## 6. Common mistakes

1. **Off-by-one errors.** `range(len(nums))` goes from 0 to n-1. Using `nums[len(nums)]` crashes.
2. **Starting `best` at 0 when numbers can be negative.** Start at the first item, or at minus infinity.
3. **Modifying a list while looping over it.** Items are skipped. Build a new list instead.
4. **`x in nums` inside a loop.** Hidden O(n^2). Use a set (lesson 02).
5. **Slicing inside a loop** (`nums[i:]`). It copies and costs O(n) each time.
6. **Forgetting empty input.** `nums[0]` crashes on `[]`. Ask if empty is possible.
7. **Building a string with `+=` in a loop.** Many copies. Use a list and `"".join(...)`.
8. **Mutating the input** when the interviewer expects it unchanged (we copied intervals above).

## 7. Practice list (8 more problems)

"Asked at" means the problem appears on that company's list in the community repo [liquidslr/leetcode-company-wise-problems](https://github.com/liquidslr/leetcode-company-wise-problems) (checked 2026-11-15). Difficulty is the LeetCode label from the same data.

| # | Problem | Difficulty | Asked at (per those lists) |
|---|---|---|---|
| 1 | Move Zeroes | Easy | Amazon, Google, Meta, Microsoft |
| 2 | Longest Common Prefix | Easy | Amazon, Google, Meta, Microsoft |
| 3 | Rotate Array | Medium | Amazon, Google, Meta, Microsoft |
| 4 | Spiral Matrix | Medium | Amazon, Google, Meta, Microsoft |
| 5 | Rotate Image | Medium | Amazon, Google, Meta, Microsoft |
| 6 | Set Matrix Zeroes | Medium | Amazon, Google, Meta, Microsoft |
| 7 | Reverse Words in a String | Medium | Amazon, Google, Meta, Microsoft |
| 8 | Next Permutation | Medium | Amazon, Google, Meta, Microsoft, Stripe |

Being on a list does not mean you will get it. It means the pattern is common.

## 8. Self-quiz (5 questions)

1. What is the index of the first item in a Python list? What is `nums[-1]`?
2. Why is `x in my_list` slow when used inside a loop? What is a faster tool?
3. In Maximum Subarray, why do we write `cur = max(x, cur + x)`?
4. Using prefix sums, how do you get the sum of `nums[2..5]` in O(1) time after building them?
5. Why do we sort first in Merge Intervals? What is the cost of that step?

### Answers

1. Index 0. `nums[-1]` is the last item.
2. It checks items one by one, so it costs O(n) per check. Inside a loop of n steps the total is O(n^2). A set (or dict) checks in O(1) on average.
3. It chooses between two options: start a new piece at x, or extend the old piece. If the old piece total is negative, starting fresh is better.
4. `prefix[6] - prefix[2]` (that is `prefix[right + 1] - prefix[left]`).
5. After sorting by start, overlapping intervals are neighbours, so one pass is enough. Sorting costs O(n log n).

Next: [02_hash_maps_and_sets.md](02_hash_maps_and_sets.md)
