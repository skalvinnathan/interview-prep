# Lesson 16: Dynamic Programming, Part 2 (LIS, word break, knapsack, edit distance)

All code is Python 3.9. Every code block in this file was run with `python3` (3.9.6) before it was written here.

Read lesson 15 first. We use the same five-question recipe:
1. What is the state? 2. What does `dp[state]` mean? 3. What is the recurrence? 4. What are the base cases? 5. In which order do I fill the table, and where is the answer?

---

## Words you need first

- **Subsequence**: pick some letters (or numbers) from a list **keeping their order**, but you may skip some. From `a b c d e` you can get `a c e`. You cannot get `c a e`. (A *substring* must be a block with no skipping. A *subsequence* may skip.)
- **Knapsack**: you have a bag with a limit (like 7 kg) and items with weight and value. Choose items to get the biggest value without breaking the bag.
- **0/1 knapsack**: each item can be taken **0 times or 1 time** (take it or leave it).
- **Edit distance**: the smallest number of changes (insert, delete, replace one letter) to turn word A into word B.
- **2D table**: a table with rows and columns. Used when the state has two numbers (like "how many letters of word A, how many letters of word B").
- **Prefix**: the first few letters. `"hor"` is a prefix of `"horse"`.

---

## 1. What is this?

Part 1 had problems with one number as the state. Here we meet three new shapes:

**Shape 1: "the best ending at i" (LIS).** `dp[i]` is about the best answer that **ends at position i**. To compute it, you look back at **all** earlier positions `j < i`.

**Shape 2: "can I build it?" (word break, subset sum, knapsack).** `dp[x]` is `True` or `False`: "is it possible to reach this amount / this prefix?".

**Shape 3: "two sequences, a 2D table" (edit distance, longest common subsequence).** `dp[i][j]` is the answer for **the first i letters of A and the first j letters of B**.

**Analogy for shape 3: comparing two shopping lists.**
You walk down both lists at the same time. At each pair of items, you ask: "same item? move on both. Different? Then I either skip one from list A, skip one from list B, or swap one." The table remembers the best answer for every pair of positions so you never compare the same parts again.

---

## 2. When do I use it?

| Words in the problem | Idea |
|---|---|
| "**longest increasing subsequence**", "longest chain" | Shape 1 (LIS) |
| "can the string be **split into dictionary words**" | Shape 2 (word break) |
| "**subset** with a given sum", "split into two equal halves", "pick items under a limit" | Shape 2 / knapsack |
| "**minimum number of operations** to turn string A into B" | Shape 3 (edit distance) |
| "**longest common subsequence** of two strings" | Shape 3 |
| "each item **once**" (take or leave) | 0/1 knapsack |
| "unlimited copies of each item" | Unbounded knapsack (like Coin Change, lesson 15) |

---

## 3. Trace of a tiny example: Longest Increasing Subsequence

**Problem**: Given a list of numbers, find the length of the longest subsequence where numbers go strictly up. Take `[10, 9, 2, 5, 3, 7, 101, 18]`.

**Thinking.** `dp[i]` = length of the longest increasing subsequence that **ends with `nums[i]`**.
For each `i`, look at every earlier `j`. If `nums[j] < nums[i]`, we can put `nums[i]` after the sequence that ends at `j`. So `dp[i] = 1 + max(dp[j])` over all such `j`. If no `j` works, `dp[i] = 1` (just itself).

```
index:   0    1    2    3    4    5    6     7
nums:    10   9    2    5    3    7    101   18
dp:      ?    ?    ?    ?    ?    ?    ?     ?

i=0 (10): no earlier numbers                                   dp[0] = 1
i=1 (9):  earlier 10 is not < 9                                dp[1] = 1
i=2 (2):  earlier 10, 9 are not < 2                            dp[2] = 1
i=3 (5):  earlier smaller: 2 (dp=1)          -> 1 + 1          dp[3] = 2
i=4 (3):  earlier smaller: 2 (dp=1)          -> 1 + 1          dp[4] = 2
i=5 (7):  earlier smaller: 2 (1), 5 (2), 3 (2) -> 1 + 2        dp[5] = 3
i=6 (101): earlier smaller: all of them; best dp is 3 (from 7) -> 1 + 3   dp[6] = 4
i=7 (18): earlier smaller: 10(1) 9(1) 2(1) 5(2) 3(2) 7(3); not 101 -> 1 + 3   dp[7] = 4

index:   0    1    2    3    4    5    6     7
nums:    10   9    2    5    3    7    101   18
dp:      1    1    1    2    2    3    4     4

answer = max(dp) = 4      (for example 2, 5, 7, 101 or 2, 3, 7, 18)
```

Note: the answer is `max(dp)`, not `dp[-1]`, because the best sequence does not have to end at the last number.

---

## 4. Template code

### 4a. 0/1 Knapsack (take it or leave it)

State: `dp[w]` = the best value we can get with a bag limit of exactly `w` (or less). For each item, we decide to take it or not. We loop `w` **from high to low** so each item is used at most once.

```python
def knapsack(weights, values, capacity):      # best total value within the weight limit
    dp = [0] * (capacity + 1)                 # dp[w] = best value with weight limit w; all zero at first
    for i in range(len(weights)):             # consider the items one by one
        wt, val = weights[i], values[i]       # this item's weight and value
        for w in range(capacity, wt - 1, -1): # go from the biggest limit DOWN to wt (down, so we use the item once)
            dp[w] = max(dp[w], dp[w - wt] + val)   # leave it (dp[w]) or take it (value + best of the remaining room)
    return dp[capacity]                       # best value for the full limit


print(knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7))   # expect 9 (items with weight 3 and 4)
assert knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7) == 9   # take weights 3 and 4: value 4 + 5
assert knapsack([5], [10], 3) == 0            # edge case: the only item does not fit
assert knapsack([], [], 10) == 0              # edge case: no items
```

**Trace** (weights `[1,3,4,5]`, values `[1,4,5,7]`, capacity 7). The row shows `dp[0..7]` after each item:

```
w:            0  1  2  3  4  5  6  7
start:        0  0  0  0  0  0  0  0
item (w1,v1): 0  1  1  1  1  1  1  1     (with 1 item, we can take it whenever w >= 1)
item (w3,v4): 0  1  1  4  5  5  5  5     (w=3: take it -> 4.  w=4: 4+dp[1]=5 ...)
item (w4,v5): 0  1  1  4  5  6  6  9     (w=7: take it -> 5 + dp[3] = 5 + 4 = 9)
item (w5,v7): 0  1  1  4  5  7  8  9     (w=5: 7.  w=6: 7 + dp[1] = 8.  w=7: 7 + dp[2] = 8, not better than 9)
answer dp[7] = 9
```

### 4b. 2D table for two strings (the skeleton)

```python
def two_string_table(a, b):                   # skeleton: dp[i][j] for the first i letters of a and first j of b
    m, n = len(a), len(b)                     # lengths of the two strings
    dp = [[0] * (n + 1) for _ in range(m + 1)]    # (m+1) rows, (n+1) columns; row 0 and column 0 mean "empty string"
    for i in range(1, m + 1):                 # go through the letters of a
        for j in range(1, n + 1):             # go through the letters of b
            if a[i - 1] == b[j - 1]:          # the two current letters are equal (index i-1 because the table has an extra row)
                dp[i][j] = dp[i - 1][j - 1] + 1    # they match: extend the answer from the diagonal
            else:                             # the letters differ
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])   # take the better of "skip a's letter" or "skip b's letter"
    return dp[m][n]                           # the answer uses all letters of both strings


print(two_string_table("abcde", "ace"))       # this skeleton is the longest common subsequence; expect 3
assert two_string_table("abcde", "ace") == 3  # "ace"
```

---

## 5. Classic problems

### 5.1 Longest Increasing Subsequence (LeetCode 300)

**In plain words.** Find the length of the longest strictly increasing subsequence of a list. `[10,9,2,5,3,7,101,18]` gives 4.

**Brute force.** Try every subsequence (`2^n` of them) and check if it is increasing. Too slow.

**Better idea, slowly.** The table in section 3. Cost O(n^2). Then there is an even faster idea (O(n log n)):

**The "tails" idea (O(n log n)).** Keep a list `tails` where `tails[k]` is the **smallest possible last number of an increasing subsequence of length `k+1`**. For each number `x`:
- If `x` is bigger than all tails, it extends the longest one: append it.
- Otherwise, find the first tail that is `>= x` (binary search with `bisect_left`) and replace it with `x`. This makes a length-`k+1` sequence end with a smaller number, which is better for the future.
The length of `tails` is the answer. (Note: `tails` itself is not always a real subsequence, only its length is right.)

```python
from bisect import bisect_left                # binary search helper
from typing import List                       # type hints


def length_of_lis_n2(nums: List[int]) -> int:   # the simple O(n^2) table version
    if not nums:                              # empty list
        return 0                              # no sequence
    dp = [1] * len(nums)                      # dp[i] = longest sequence ending at i; at least 1 (itself)
    for i in range(len(nums)):                # for each position i
        for j in range(i):                    # look at every earlier position j
            if nums[j] < nums[i]:             # nums[i] can come after nums[j]
                dp[i] = max(dp[i], dp[j] + 1) # extend the sequence that ends at j
    return max(dp)                            # the best sequence can end anywhere


def length_of_lis(nums: List[int]) -> int:    # the O(n log n) "tails" version
    tails: List[int] = []                     # tails[k] = smallest last number of an increasing sequence of length k+1
    for x in nums:                            # go through the numbers
        pos = bisect_left(tails, x)           # first place where tails[pos] >= x
        if pos == len(tails):                 # x is bigger than every tail
            tails.append(x)                   # we found a longer sequence
        else:                                 # x can improve an existing length
            tails[pos] = x                    # replace with the smaller ending number
    return len(tails)                         # the number of lengths we reached


data = [10, 9, 2, 5, 3, 7, 101, 18]           # the example
print(length_of_lis_n2(data), length_of_lis(data))   # expect 4 4
assert length_of_lis_n2(data) == 4 and length_of_lis(data) == 4   # example 1
assert length_of_lis([0, 1, 0, 3, 2, 3]) == 4      # example 2
assert length_of_lis([7, 7, 7, 7, 7]) == 1         # example 3: strictly increasing, equal numbers do not count
assert length_of_lis([]) == 0                      # edge case: empty
assert length_of_lis([5]) == 1                     # edge case: one number
assert length_of_lis([5, 4, 3, 2, 1]) == 1         # edge case: strictly decreasing
assert length_of_lis_n2([0, 1, 0, 3, 2, 3]) == 4   # the O(n^2) version agrees
```

**Trace** of the `tails` version on `[10, 9, 2, 5, 3, 7, 101, 18]`:

```
x=10:  tails=[]          10 is bigger than all -> append          tails=[10]
x=9:   first tail >= 9 is 10 (position 0) -> replace              tails=[9]
x=2:   first tail >= 2 is 9 (position 0)  -> replace              tails=[2]
x=5:   5 is bigger than all -> append                              tails=[2, 5]
x=3:   first tail >= 3 is 5 (position 1)  -> replace              tails=[2, 3]
x=7:   bigger than all -> append                                   tails=[2, 3, 7]
x=101: bigger than all -> append                                   tails=[2, 3, 7, 101]
x=18:  first tail >= 18 is 101 (position 3) -> replace            tails=[2, 3, 7, 18]
answer = len(tails) = 4
```

The O(n^2) trace is in section 3.

**Complexity.** The table version: time O(n^2), space O(n). The tails version: time O(n log n) (n numbers, each a binary search), space O(n).

**Edge cases.**
1. Equal numbers do not count (strictly increasing). `bisect_left` handles this: an equal number replaces instead of extending.
2. A strictly decreasing list gives 1.

**How interviewers twist it.**
- "Return the actual subsequence": in the O(n^2) version, store `prev[i]` (the `j` that gave the best), then walk back from the best `i`.
- "Count how many LIS exist" (LeetCode 673): keep a second array of counts.
- "Russian Doll Envelopes" (LeetCode 354): sort by width (and height descending for equal widths), then LIS on heights.

---

### 5.2 Word Break (LeetCode 139)

**In plain words.** Given a string `s` and a dictionary of words, can `s` be split into one or more dictionary words (words may be reused)? `s = "leetcode"`, dictionary `["leet","code"]` gives `True`.

**Brute force.** Recursion: try every first word, then solve the rest. The same suffixes are solved again and again: exponential.

**Better idea, slowly.**
1. State: `dp[i]` = `True` if the **first `i` letters** (`s[:i]`) can be split into dictionary words.
2. Base: `dp[0] = True` (the empty string needs no words).
3. For each `i` from 1 to `len(s)`: look for a split point `j < i` such that `dp[j]` is `True` (the first `j` letters work) **and** `s[j:i]` is in the dictionary. If we find one, `dp[i] = True`.
4. Answer: `dp[len(s)]`.

Using a `set` for the dictionary makes each word lookup fast.

```python
from typing import List                       # type hints


def word_break(s: str, word_dict: List[str]) -> bool:   # can s be split into dictionary words?
    words = set(word_dict)                    # a set for fast "is it a word?" checks
    dp = [False] * (len(s) + 1)               # dp[i] = can s[:i] be split? all False at first
    dp[0] = True                              # base: the empty prefix is fine
    for i in range(1, len(s) + 1):            # for each prefix length i
        for j in range(i):                    # try each split point j
            if dp[j] and s[j:i] in words:     # the first j letters work AND the piece s[j:i] is a word
                dp[i] = True                  # then the first i letters work
                break                         # one valid split is enough, stop searching
    return dp[len(s)]                         # can the whole string be split?


print(word_break("leetcode", ["leet", "code"]))   # expect True
assert word_break("leetcode", ["leet", "code"]) is True        # example 1
assert word_break("applepenapple", ["apple", "pen"]) is True   # example 2: words reused
assert word_break("catsandog", ["cats", "dog", "sand", "and", "cat"]) is False   # example 3
assert word_break("", ["a"]) is True          # edge case: empty string
assert word_break("a", []) is False           # edge case: empty dictionary
assert word_break("aaaaaaa", ["aaaa", "aaa"]) is True   # edge case: 4 + 3
```

**Trace** on `s = "leetcode"`, dictionary `{leet, code}`. Index `i` means "first i letters". `T` for True, `F` for False.

```
index i:   0   1   2   3   4   5   6   7   8
prefix:    ""  l   le  lee leet leetc leetco leetcod leetcode
Step A: base
dp:        T   F   F   F   F   F   F   F   F

i=1..3: any j with dp[j]=True? only j=0.  s[0:1]="l", s[0:2]="le", s[0:3]="lee": none are words.   dp stays F
i=4:    j=0: dp[0]=T and s[0:4]="leet" is a word -> dp[4] = T
dp:        T   F   F   F   T   F   F   F   F
i=5..7: dp[0]=T with s[0:5]="leetc", "leetco", "leetcod": not words.
        dp[4]=T with s[4:5]="c", s[4:6]="co", s[4:7]="cod": not words.   dp stays F
i=8:    j=0: s[0:8]="leetcode" is not a word.
        j=4: dp[4]=T and s[4:8]="code" is a word -> dp[8] = T
dp:        T   F   F   F   T   F   F   F   T      <- answer dp[8] = True
```

**Complexity.** Time O(n^2) checks of a piece, and each slice or lookup costs up to O(n), so O(n^3) in the worst case if you count the slicing. (You can reduce it by only trying `j` where `i - j` is at most the longest word length.) Space O(n) for `dp` plus the set.

**Edge cases.**
1. Empty string: `True` (by the base case).
2. Words that overlap in a tricky way (`"aaaaaaa"` with `["aaaa","aaa"]`): DP tries all splits, so it finds `4 + 3`.

**How interviewers twist it.**
- "Return **all** the possible sentences" (Word Break II, LeetCode 140): backtracking with a memo, or build the sentences from DP.
- "Use a **trie** for the dictionary" (lesson 17): quick prefix checks.
- "Minimum number of words" or "number of ways": change `dp` from `True/False` to a count or a minimum.

---

### 5.3 Partition Equal Subset Sum (LeetCode 416, the knapsack idea)

**In plain words.** Given positive numbers, can you split them into two groups with **equal sum**? `[1,5,11,5]` gives `True` (`11` and `1+5+5`).

**Brute force.** Try every subset (`2^n`), and check whether one sums to half the total.

**Better idea, slowly.**
1. If the total is odd, return `False` at once. You cannot split an odd number into two equal integers.
2. Now the question is: **can some subset add up to `total / 2`?** This is the 0/1 knapsack idea: each number is taken once or not at all.
3. State: `dp[s]` = `True` if some subset of the numbers seen so far sums to exactly `s`.
4. Base: `dp[0] = True` (the empty subset sums to 0).
5. For each number `x`, go **backwards** from `target` down to `x`: `dp[s] = dp[s] or dp[s - x]`. Going backwards makes sure we use each number only once.

```python
from typing import List                       # type hints


def can_partition(nums: List[int]) -> bool:   # can we split into two equal-sum groups?
    total = sum(nums)                         # total of all numbers
    if total % 2 == 1:                        # odd total: impossible
        return False                          # cannot split evenly
    target = total // 2                       # each group must sum to this
    dp = [False] * (target + 1)               # dp[s] = is sum s reachable by some subset?
    dp[0] = True                              # the empty subset gives sum 0
    for x in nums:                            # take the numbers one by one
        for s in range(target, x - 1, -1):    # go from target DOWN to x (so each number is used once)
            if dp[s - x]:                     # if sum (s - x) was reachable before ...
                dp[s] = True                  # ... then sum s is reachable by adding x
    return dp[target]                         # can we reach exactly half?


print(can_partition([1, 5, 11, 5]))           # expect True
assert can_partition([1, 5, 11, 5]) is True   # example 1
assert can_partition([1, 2, 3, 5]) is False   # example 2: total 11 is odd
assert can_partition([1, 2, 5]) is False      # edge case: total 8, but nothing sums to 4
assert can_partition([2, 2]) is True          # edge case: two equal numbers
assert can_partition([100]) is False          # edge case: one number cannot be split
```

**Trace** on `[1, 5, 11, 5]`. Total = 22, target = 11. The row shows which sums `0..11` are reachable (`T`) after each number.

```
sum s:        0  1  2  3  4  5  6  7  8  9  10 11
start:        T  F  F  F  F  F  F  F  F  F  F  F
after 1:      T  T  F  F  F  F  F  F  F  F  F  F     (sum 1 = 0 + 1)
after 5:      T  T  F  F  F  T  T  F  F  F  F  F     (sum 5 = 0 + 5, sum 6 = 1 + 5)
after 11:     T  T  F  F  F  T  T  F  F  F  F  T     (sum 11 = 0 + 11)  <- the target is reachable
after 5:      T  T  F  F  F  T  T  F  F  F  T  T     (sum 10 = 5 + 5, sum 11 stays T; 11 = 1 + 5 + 5 as well)
answer dp[11] = True
```

**Complexity.** Time O(n x target): for each number we loop over the sums. Space O(target) for the one-dimensional table.

**Edge cases.**
1. Odd total: return `False` before doing any work.
2. A single number cannot be split (the other group would be empty with sum 0, unequal for a positive number).

**How interviewers twist it.**
- "Target Sum" (LeetCode 494): put `+` or `-` in front of each number to reach a target. Reduce it to "count subsets with a given sum".
- "Last Stone Weight II" (LeetCode 1049): the same subset-sum idea to minimise the difference.
- "Print the subset": keep a 2D table and walk back.

---

### 5.4 Edit Distance (LeetCode 72)

**In plain words.** Turn word `a` into word `b` using the fewest operations. One operation is: insert a letter, delete a letter, or replace a letter. `"horse"` to `"ros"` needs 3.

**Brute force.** Try every sequence of operations. Exponential.

**Better idea, slowly.**
1. State: `dp[i][j]` = the fewest operations to turn the **first `i` letters of `a`** into the **first `j` letters of `b`**.
2. Base cases: turning `a[:i]` into the empty string needs `i` deletes: `dp[i][0] = i`. Turning an empty string into `b[:j]` needs `j` inserts: `dp[0][j] = j`.
3. Look at the last letters `a[i-1]` and `b[j-1]`:
   - If they are **equal**: no work needed for them: `dp[i][j] = dp[i-1][j-1]`.
   - If they **differ**: choose the cheapest of three, and add 1:
     - **replace** `a[i-1]` by `b[j-1]`: `dp[i-1][j-1]`
     - **delete** `a[i-1]`: `dp[i-1][j]`
     - **insert** `b[j-1]` at the end of `a`: `dp[i][j-1]`
4. Answer: `dp[len(a)][len(b)]`.

```python
def min_distance(a: str, b: str) -> int:      # the edit distance between a and b
    m, n = len(a), len(b)                     # lengths
    dp = [[0] * (n + 1) for _ in range(m + 1)]    # dp[i][j]: first i letters of a to first j letters of b
    for i in range(m + 1):                    # first column: turn a[:i] into ""
        dp[i][0] = i                          # needs i deletes
    for j in range(n + 1):                    # first row: turn "" into b[:j]
        dp[0][j] = j                          # needs j inserts
    for i in range(1, m + 1):                 # fill row by row
        for j in range(1, n + 1):             # and column by column
            if a[i - 1] == b[j - 1]:          # last letters are equal
                dp[i][j] = dp[i - 1][j - 1]   # no operation needed for them
            else:                             # last letters differ
                dp[i][j] = 1 + min(dp[i - 1][j - 1],   # replace
                                   dp[i - 1][j],       # delete from a
                                   dp[i][j - 1])       # insert into a
    return dp[m][n]                           # the answer is the bottom-right cell


print(min_distance("horse", "ros"))           # expect 3
assert min_distance("horse", "ros") == 3      # example 1
assert min_distance("intention", "execution") == 5   # example 2
assert min_distance("", "abc") == 3           # edge case: three inserts
assert min_distance("abc", "") == 3           # edge case: three deletes
assert min_distance("same", "same") == 0      # edge case: equal words
assert min_distance("a", "b") == 1            # edge case: one replace
```

**Trace** on `a = "horse"`, `b = "ros"`. Rows are letters of `horse`, columns are letters of `ros`.

```
Step A: base cases (first row and first column)
        ""   r   o   s
""      0    1   2   3
h       1
o       2
r       3
s       4
e       5

Step B: row "h"
   (h,r): h != r. replace dp[0][0]=0, delete dp[0][1]=1, insert dp[1][0]=1. min=0, +1 = 1
   (h,o): h != o. replace dp[0][1]=1, delete dp[0][2]=2, insert dp[1][1]=1. min=1, +1 = 2
   (h,s): h != s. replace dp[0][2]=2, delete dp[0][3]=3, insert dp[1][2]=2. min=2, +1 = 3
        ""   r   o   s
h       1    1   2   3

Step C: row "o"
   (o,r): o != r. replace dp[1][0]=1, delete dp[1][1]=1, insert dp[2][0]=2. min=1, +1 = 2
   (o,o): equal! take the diagonal dp[1][1] = 1
   (o,s): o != s. replace dp[1][2]=2, delete dp[1][3]=3, insert dp[2][2]=1. min=1, +1 = 2
o       2    2   1   2

Step D: row "r"
   (r,r): equal! diagonal dp[2][0] = 2
   (r,o): r != o. replace dp[2][1]=2, delete dp[2][2]=1, insert dp[3][1]=2. min=1, +1 = 2
   (r,s): r != s. replace dp[2][2]=1, delete dp[2][3]=2, insert dp[3][2]=2. min=1, +1 = 2
r       3    2   2   2

Step E: row "s"
   (s,r): s != r. replace dp[3][0]=3, delete dp[3][1]=2, insert dp[4][0]=4. min=2, +1 = 3
   (s,o): s != o. replace dp[3][1]=2, delete dp[3][2]=2, insert dp[4][1]=3. min=2, +1 = 3
   (s,s): equal! diagonal dp[3][2] = 2
s       4    3   3   2

Step F: row "e"
   (e,r): e != r. replace dp[4][0]=4, delete dp[4][1]=3, insert dp[5][0]=5. min=3, +1 = 4
   (e,o): e != o. replace dp[4][1]=3, delete dp[4][2]=3, insert dp[5][1]=4. min=3, +1 = 4
   (e,s): e != s. replace dp[4][2]=3, delete dp[4][3]=2, insert dp[5][2]=4. min=2, +1 = 3
e       5    4   4   3

final table:
        ""   r   o   s
""      0    1   2   3
h       1    1   2   3
o       2    2   1   2
r       3    2   2   2
s       4    3   3   2
e       5    4   4   3      <- answer dp[5][3] = 3
```

One way to do it with 3 operations: `horse` -> `rorse` (replace h with r) -> `rose` (delete r) -> `ros` (delete e).

**Complexity.** Time O(m x n): each cell is filled in O(1). Space O(m x n); it can be O(n) by keeping only two rows.

**Edge cases.**
1. One word is empty: the answer is the length of the other word.
2. Equal words: 0.

**How interviewers twist it.**
- "Print the sequence of operations": walk back from the bottom-right, choosing the cell that gave each value.
- "Only insert and delete" (Delete Operation for Two Strings, LeetCode 583): answer is `m + n - 2 x LCS`.
- "One Edit Distance" (LeetCode 161): only checks if the distance is exactly 1, which is simpler, O(n), no table.

---

### 5.5 Longest Common Subsequence (LeetCode 1143)

**In plain words.** Given two strings, find the length of their longest common subsequence. `"abcde"` and `"ace"` gives 3 (`"ace"`).

**Brute force.** Generate all subsequences of one string (`2^n`) and check each against the other.

**Better idea, slowly.**
1. State: `dp[i][j]` = LCS length of the **first `i` letters of `a`** and the **first `j` letters of `b`**.
2. Base: if either string is empty, the LCS is 0. So row 0 and column 0 are all 0 (that is what an all-zero table gives us).
3. If the last letters are **equal**, they are part of the common subsequence: `dp[i][j] = dp[i-1][j-1] + 1`.
4. If they **differ**, the answer is the better of dropping one letter from either side: `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`.
5. Answer: `dp[len(a)][len(b)]`.

```python
def longest_common_subsequence(a: str, b: str) -> int:   # LCS length
    m, n = len(a), len(b)                     # lengths of the two strings
    dp = [[0] * (n + 1) for _ in range(m + 1)]    # zeros: an empty string has LCS 0 with anything
    for i in range(1, m + 1):                 # letters of a
        for j in range(1, n + 1):             # letters of b
            if a[i - 1] == b[j - 1]:          # the last letters match
                dp[i][j] = dp[i - 1][j - 1] + 1    # extend the LCS found without these two letters
            else:                             # they do not match
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])   # drop a letter from a, or from b
    return dp[m][n]                           # the answer


print(longest_common_subsequence("abcde", "ace"))   # expect 3
assert longest_common_subsequence("abcde", "ace") == 3     # example 1
assert longest_common_subsequence("abc", "abc") == 3       # example 2
assert longest_common_subsequence("abc", "def") == 0       # example 3: nothing in common
assert longest_common_subsequence("", "abc") == 0          # edge case: empty string
assert longest_common_subsequence("bl", "yby") == 1        # edge case: only one shared letter
```

**Trace** on `a = "abcde"`, `b = "ace"`:

```
        ""   a   c   e
""      0    0   0   0
a       0    1   1   1     (a,a) equal -> diagonal 0 + 1 = 1.  Then (a,c), (a,e): max(up, left) = 1
b       0    1   1   1     b matches none: max(up, left)
c       0    1   2   2     (c,c) equal -> diagonal dp[2][1]=1, +1 = 2
d       0    1   2   2     d matches none
e       0    1   2   3     (e,e) equal -> diagonal dp[4][2]=2, +1 = 3
answer dp[5][3] = 3
```

**Complexity.** Time O(m x n). Space O(m x n), or O(n) with two rows.

**Edge cases.**
1. No common letters: 0.
2. Identical strings: the full length.

**How interviewers twist it.**
- "Return the actual subsequence": walk back from the bottom-right. If letters are equal, take the letter and go diagonally. Else move to the larger neighbour (up or left).
- "Longest Palindromic Subsequence" (LeetCode 516): LCS of a string and its reverse.
- "Shortest Common Supersequence": length = `m + n - LCS`.

---

## 6. Common mistakes

1. **Knapsack loop in the wrong direction.** For 0/1 (each item once), loop the capacity **downward**. Upward lets one item be used many times (that is the unbounded knapsack, like Coin Change).
2. **LIS: returning `dp[-1]`** instead of `max(dp)`.
3. **LIS: using `bisect_right`** (this allows equal numbers, which makes a non-strict sequence).
4. **String tables: mixing `a[i]` with `a[i-1]`.** The table has an extra row and column, so row `i` means "first `i` letters", and the last of them is `a[i-1]`.
5. **Forgetting base cases** for edit distance (first row and column are `0..n` and `0..m`, not all zeros).
6. **Word Break: not using a set** for the dictionary, or not stopping at the first success (`break`).
7. **Partition: forgetting the odd-total check.**
8. **Subsequence vs substring confusion.** Subsequence may skip letters.

---

## 7. Practice list (8 more problems)

Tags come from public LeetCode company-tag lists I read (GitHub mirror, snapshot Oct 2025; see lesson 19). A tag means "the problem is in that company's list". No tag means not verified. The problems taught above are tagged too: Longest Increasing Subsequence, Word Break, Partition Equal Subset Sum and Edit Distance are each in the lists of Amazon, Google, Meta and Microsoft. Longest Common Subsequence is in the lists of Amazon and Google.

| # | Problem | Difficulty | Tagged for |
|---|---|---|---|
| 1 | Maximum Subarray (53) | Medium | Amazon, Google, Microsoft |
| 2 | Longest Palindromic Substring (5) | Medium | Amazon, Google, Microsoft |
| 3 | Palindromic Substrings (647) | Medium | not verified |
| 4 | Longest Palindromic Subsequence (516) | Medium | not verified |
| 5 | Target Sum (494) | Medium | not verified |
| 6 | Word Break II (140) | Hard | not verified |
| 7 | Distinct Subsequences (115) | Hard | not verified |
| 8 | Regular Expression Matching (10) | Hard | not verified |

---

## 8. Self-quiz (5 questions)

1. In LIS, what does `dp[i]` mean, and why is the answer `max(dp)`?
2. In Word Break, what two things must be true for `dp[i]` to become `True`?
3. In 0/1 knapsack, why do we loop the capacity from high to low?
4. In Edit Distance, which three cells do we look at when the letters differ, and what does each mean?
5. What is the difference between a subsequence and a substring?

**Answers.**
1. `dp[i]` is the length of the longest increasing subsequence that ends exactly at position `i`. The best sequence can end at any position, so we take the maximum over all `i`.
2. `dp[j]` is `True` for some earlier `j` (the first `j` letters can be split), and the piece `s[j:i]` is a dictionary word.
3. Going from high to low means `dp[s - x]` still holds the value from **before** we used the current item. So the item is used at most once. Going upward would reuse the item.
4. Diagonal `dp[i-1][j-1]` = replace a letter. Up `dp[i-1][j]` = delete a letter from `a`. Left `dp[i][j-1]` = insert a letter into `a`. Take the smallest and add 1.
5. A substring is a continuous block of letters. A subsequence keeps the order but may skip letters.
