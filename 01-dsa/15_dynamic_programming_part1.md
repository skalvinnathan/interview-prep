# Lesson 15: Dynamic Programming, Part 1 (remembering answers)

All code is Python 3.9. Every code block in this file was run with `python3` (3.9.6) before it was written here.

Do not be afraid of the name. "Dynamic programming" (DP) is just a fancy name for one simple habit: **do not solve the same small problem twice. Write the answer down and look it up next time.**

---

## Words you need first

- **Subproblem**: a smaller version of the same problem. "Ways to climb 5 stairs" has a smaller version "ways to climb 4 stairs".
- **Overlapping subproblems**: the same small problem shows up again and again while you solve the big one.
- **Memoization** (top-down): write the recursive solution, and **save each answer in a dictionary** (a memo, like a memo note) the first time you compute it.
- **Tabulation** (bottom-up): fill a **table** (a list) from the smallest problem up to the answer, using a loop. No recursion.
- **State**: the few numbers that describe a subproblem. For stairs, the state is "which stair am I on?". The state decides the size of your table.
- **Recurrence**: the rule that gives a bigger answer from smaller answers. Example: `ways(n) = ways(n-1) + ways(n-2)`.
- **Base case**: the smallest answers you know without thinking (like `ways(0) = 1`).

---

## 1. What is this?

**Analogy: your phone's contacts list.**
The first time you need a friend's number, you ask around (slow). Then you **save it**. Next time you just look it up (fast). DP is saving the numbers you worked out.

**A real example: Fibonacci.** `fib(n) = fib(n-1) + fib(n-2)`, with `fib(0)=0`, `fib(1)=1`. A direct recursive function solves the same small problems many times:

```
                     fib(5)
                   /        \
              fib(4)          fib(3)           <- fib(3) is computed here
             /      \         /     \
        fib(3)     fib(2)  fib(2)  fib(1)      <- and here again
        /    \
    fib(2)  fib(1) ...
```

I counted how many function calls the plain recursive version makes (I ran it):

| n | fib(n) | number of calls |
|---|---|---|
| 5 | 5 | 15 |
| 10 | 55 | 177 |
| 20 | 6,765 | 21,891 |
| 30 | 832,040 | 2,692,537 |

The calls grow about 1.6 times for every step of n. With a memo, we compute each `fib(k)` **once**, so it needs only about `n` calls. For n=30 that is about 30 instead of 2.7 million.

**The five-question recipe for any DP problem** (say these out loud in an interview):
1. **What is the state?** What do I need to know to describe a subproblem? (usually an index, an amount, or a pair of indexes)
2. **What does `dp[state]` mean?** Write it in one plain sentence.
3. **What is the recurrence?** How does `dp[state]` come from smaller states?
4. **What are the base cases?** What do I know for the smallest states?
5. **In which order do I fill the table, and where is the final answer?**

---

## 2. When do I use it?

Look for these words:

| Words in the problem | Idea |
|---|---|
| "**how many ways** to ..." | DP (count ways) |
| "**minimum / maximum** cost / number of ..." and you can make choices at each step | DP (optimise) |
| "**can you reach / is it possible**" with choices at each step | DP (true/false) |
| The problem has steps, and the answer for step `i` depends on earlier steps | DP |
| Brute force would try all choices, and the same sub-situation repeats | DP |
| Only need the answer for one best choice with a clear "obviously best next move" | Maybe greedy (lesson 17) |

**Two checks that it is really DP:**
- **Overlapping subproblems**: the same smaller problem appears many times.
- **Optimal substructure**: the best answer for the big problem is built from the best answers of smaller problems.

---

## 3. Trace of a tiny example: Climbing Stairs with a table, step by step

**Problem**: You climb `n` stairs. Each move is 1 or 2 stairs. In how many different ways can you reach the top? Take `n = 5`.

**Thinking.** To stand on stair `i`, your last move was either from stair `i-1` (a 1-step) or from stair `i-2` (a 2-step). So:

`ways(i) = ways(i-1) + ways(i-2)`

Base cases: `ways(0) = 1` (one way to stand at the start: do nothing), `ways(1) = 1` (one single step).

Drawing the table. `dp[i]` = number of ways to reach stair `i`.

```
index i:   0   1   2   3   4   5
dp[i]:     ?   ?   ?   ?   ?   ?        <- empty table

Step A: write the base cases
index i:   0   1   2   3   4   5
dp[i]:     1   1   ?   ?   ?   ?

Step B: i = 2:  dp[2] = dp[1] + dp[0] = 1 + 1 = 2
index i:   0   1   2   3   4   5
dp[i]:     1   1   2   ?   ?   ?

Step C: i = 3:  dp[3] = dp[2] + dp[1] = 2 + 1 = 3
index i:   0   1   2   3   4   5
dp[i]:     1   1   2   3   ?   ?

Step D: i = 4:  dp[4] = dp[3] + dp[2] = 3 + 2 = 5
index i:   0   1   2   3   4   5
dp[i]:     1   1   2   3   5   ?

Step E: i = 5:  dp[5] = dp[4] + dp[3] = 5 + 3 = 8
index i:   0   1   2   3   4   5
dp[i]:     1   1   2   3   5   8        <- the answer is dp[5] = 8
```

Check by listing for `n = 3`: `1+1+1`, `1+2`, `2+1` = 3 ways. Matches `dp[3] = 3`.

---

## 4. Template code

### 4a. Top-down (memoization): recursion plus a memo

```python
def fib_memo(n, memo=None):                   # Fibonacci with a memo dictionary
    if memo is None:                          # first call: make a fresh memo
        memo = {}                             # the memo: n -> fib(n)
    if n < 2:                                 # base cases: fib(0)=0 and fib(1)=1
        return n                              # return the base value
    if n in memo:                             # did we already compute this one?
        return memo[n]                        # yes: look it up, no recursion
    memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo)   # compute once and store it
    return memo[n]                            # give the answer


print(fib_memo(30))                           # expect 832040, and it is instant
assert fib_memo(30) == 832040                 # the value from the table above
assert fib_memo(0) == 0 and fib_memo(1) == 1  # base cases
assert fib_memo(90) == 2880067194370816120    # a big n is fast with a memo
```

Python also has a built-in memo helper:

```python
from functools import lru_cache               # a ready-made memo decorator


@lru_cache(maxsize=None)                      # remember every answer by its arguments
def fib(n):                                   # Fibonacci again
    if n < 2:                                 # base cases
        return n                              # fib(0)=0, fib(1)=1
    return fib(n - 1) + fib(n - 2)            # the recurrence; the decorator saves each result


print(fib(30))                                # expect 832040
assert fib(30) == 832040                      # same answer
```

### 4b. Bottom-up (tabulation): a table and a loop

```python
def fib_table(n):                             # Fibonacci with a table
    if n < 2:                                 # tiny cases
        return n                              # fib(0)=0, fib(1)=1
    dp = [0] * (n + 1)                        # dp[i] will hold fib(i)
    dp[1] = 1                                 # base case: fib(1) = 1 (dp[0] is already 0)
    for i in range(2, n + 1):                 # fill from small to big
        dp[i] = dp[i - 1] + dp[i - 2]         # the recurrence
    return dp[n]                              # the answer is the last cell


print(fib_table(30))                          # expect 832040
assert fib_table(30) == 832040                # same answer as before
```

### 4c. Space trick: keep only what you need

`dp[i]` only needs the two cells before it, so we can keep two variables instead of the whole table.

```python
def fib_two_vars(n):                          # Fibonacci with O(1) memory
    a, b = 0, 1                               # a = fib(i), b = fib(i+1), starting at i = 0
    for _ in range(n):                        # move forward n times
        a, b = b, a + b                       # slide the window: new a is old b, new b is the sum
    return a                                  # a is now fib(n)


print(fib_two_vars(30))                       # expect 832040
assert fib_two_vars(30) == 832040             # same answer, only two variables
```

**Which style should I use?**
- Top-down is easier to write, because you just write the recursion and add a memo. Risk: Python's recursion limit (about 1000) for very deep inputs.
- Bottom-up is a loop, so there is no recursion limit and it can use less memory with tricks. Interviewers like it.
- Start with whichever is clearer to you. Mention the other.

---

## 5. Classic problems

### 5.1 Climbing Stairs (LeetCode 70)

**In plain words.** You climb a staircase of `n` stairs, taking 1 or 2 stairs per move. Count the distinct ways to reach the top.

**Brute force.** Recursion: `ways(n) = ways(n-1) + ways(n-2)`. This is the slow Fibonacci tree. Time O(2^n).

**Better idea, slowly.** Exactly the table in section 3. The only trick is to see that the number of ways to reach stair `i` equals the ways to reach `i-1` plus the ways to reach `i-2`. Then keep only the last two numbers.

```python
def climb_stairs(n: int) -> int:              # number of ways to climb n stairs
    if n <= 1:                                # 0 or 1 stair: only one way
        return 1                              # (do nothing, or take one step)
    prev2, prev1 = 1, 1                       # ways(0) = 1 and ways(1) = 1
    for _ in range(2, n + 1):                 # build ways(2), ways(3), ... ways(n)
        current = prev1 + prev2               # ways(i) = ways(i-1) + ways(i-2)
        prev2, prev1 = prev1, current         # slide the window one stair up
    return prev1                              # ways(n)


print([climb_stairs(i) for i in range(1, 8)]) # expect [1, 2, 3, 5, 8, 13, 21]
assert climb_stairs(2) == 2                   # example 1
assert climb_stairs(3) == 3                   # example 2
assert climb_stairs(5) == 8                   # the table in section 3
assert climb_stairs(1) == 1                   # edge case: one stair
assert climb_stairs(45) == 1836311903         # edge case: the largest n in LeetCode, still instant
```

**Trace** on `n = 5`:

```
start:       prev2=1 (ways(0)), prev1=1 (ways(1))
i=2: current = 1 + 1 = 2        -> prev2=1, prev1=2
i=3: current = 2 + 1 = 3        -> prev2=2, prev1=3
i=4: current = 3 + 2 = 5        -> prev2=3, prev1=5
i=5: current = 5 + 3 = 8        -> prev2=5, prev1=8
return 8
```

**Complexity.** Time O(n): one loop. Space O(1): only a few variables.

**Edge cases.**
1. `n = 1`: answer 1.
2. Big `n` (45): the answer needs more than 30 bits but fits in Python's integers. No overflow in Python.

**How interviewers twist it.**
- "You may take 1, 2 or 3 steps": `ways(i) = ways(i-1) + ways(i-2) + ways(i-3)`.
- "Some stairs are broken": set `dp[broken] = 0`.
- "Each stair has a cost, find the cheapest way" (Min Cost Climbing Stairs, LeetCode 746): `dp[i] = cost[i] + min(dp[i-1], dp[i-2])`.

---

### 5.2 House Robber (LeetCode 198)

**In plain words.** Houses in a row, each with some money `nums[i]`. You cannot rob **two houses next to each other** (the alarm rings). What is the most money you can take?

**Brute force.** For each house choose rob or skip, check no neighbours are both robbed, take the best. `2^n` choices.

**Better idea, slowly.**
1. State: `dp[i]` = the best money you can get from the **first `i+1` houses** (houses `0..i`).
2. For house `i` there are two choices:
   - **Skip it**: you keep the best of the earlier houses: `dp[i-1]`.
   - **Rob it**: you cannot rob house `i-1`, so you add `nums[i]` to the best of houses up to `i-2`: `dp[i-2] + nums[i]`.
3. Take the bigger one: `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`.
4. Base cases: `dp[0] = nums[0]`. For `i=1`: `dp[1] = max(nums[0], nums[1])`.

```python
from typing import List                       # type hints


def rob(nums: List[int]) -> int:              # the most money without robbing neighbours
    if not nums:                              # no houses
        return 0                              # no money
    if len(nums) == 1:                        # one house
        return nums[0]                        # rob it
    dp = [0] * len(nums)                      # dp[i] = best money using houses 0..i
    dp[0] = nums[0]                           # base: with one house, rob it
    dp[1] = max(nums[0], nums[1])             # base: with two houses, rob the richer one
    for i in range(2, len(nums)):             # fill the table left to right
        dp[i] = max(dp[i - 1], dp[i - 2] + nums[i])   # skip house i, or rob it plus best up to i-2
    return dp[-1]                             # the answer is the last cell


print(rob([2, 7, 9, 3, 1]))                   # expect 12
assert rob([1, 2, 3, 1]) == 4                 # example 1: rob houses 0 and 2
assert rob([2, 7, 9, 3, 1]) == 12             # example 2: rob houses 0, 2 and 4
assert rob([]) == 0                           # edge case: no houses
assert rob([5]) == 5                          # edge case: one house
assert rob([2, 1, 1, 2]) == 4                 # edge case: best is the two ends, not the middle
```

**Trace** on `[2, 7, 9, 3, 1]`, filling the table:

```
nums:   2   7   9   3   1
index:  0   1   2   3   4

Step A: base cases
dp:     2   7   ?   ?   ?        dp[0] = 2,  dp[1] = max(2, 7) = 7

Step B: i=2 (house worth 9): skip -> dp[1] = 7.  rob -> dp[0] + 9 = 2 + 9 = 11.  max = 11
dp:     2   7   11  ?   ?

Step C: i=3 (house worth 3): skip -> dp[2] = 11.  rob -> dp[1] + 3 = 7 + 3 = 10.  max = 11
dp:     2   7   11  11  ?

Step D: i=4 (house worth 1): skip -> dp[3] = 11.  rob -> dp[2] + 1 = 11 + 1 = 12.  max = 12
dp:     2   7   11  11  12       <- answer dp[4] = 12  (rob houses 0, 2, 4: 2+9+1)
```

**Complexity.** Time O(n). Space O(n) for the table; it can be O(1) by keeping only `dp[i-1]` and `dp[i-2]`.

**Edge cases.**
1. Empty list or one house.
2. `[2,1,1,2]`: a greedy "take the biggest first" would fail. DP gets 4 (the two ends).

**How interviewers twist it.**
- "Houses are in a **circle**" (House Robber II, LeetCode 213): run the solution twice: once without the first house, once without the last, and take the max.
- "Houses are a **tree**" (House Robber III, LeetCode 337): DP on a binary tree, returning (robbed, skipped) for each node.
- "Return which houses you robbed": walk back through the table.

---

### 5.3 Coin Change (LeetCode 322)

**In plain words.** You have coin values (like `[1, 2, 5]`) and an infinite supply of each. What is the **fewest coins** that make exactly `amount`? Return `-1` if impossible.

**Brute force.** Try every combination of coins that sums to `amount`. Exponential. (The tempting shortcut "always take the biggest coin first", called greedy, is wrong for some coin sets: with coins `[1, 3, 4]` and amount `6`, greedy gives `4+1+1` = 3 coins but the best is `3+3` = 2 coins.)

**Better idea, slowly.**
1. State: `dp[a]` = the fewest coins to make amount `a`.
2. Base: `dp[0] = 0` (zero coins make amount 0).
3. For each amount `a` from 1 up to `amount`, try every coin `c` that is not bigger than `a`. If we use coin `c` last, we need `dp[a - c]` coins for the rest, plus 1 for coin `c`. Take the smallest over all coins:
   `dp[a] = min(dp[a - c] + 1)` over all coins `c <= a`.
4. Start every `dp[a]` as "impossible" (a huge number, `amount + 1` works because we can never need more than `amount` coins of value 1).
5. At the end, if `dp[amount]` is still huge, return `-1`.

```python
from typing import List                       # type hints


def coin_change(coins: List[int], amount: int) -> int:   # fewest coins for the amount, or -1
    INF = amount + 1                          # a value that means "impossible" (bigger than any real answer)
    dp = [INF] * (amount + 1)                 # dp[a] = fewest coins for amount a; all impossible at first
    dp[0] = 0                                 # base: amount 0 needs 0 coins
    for a in range(1, amount + 1):            # compute amounts 1, 2, 3, ... amount
        for c in coins:                       # try every coin as the LAST coin used
            if c <= a:                        # the coin must fit into the amount
                dp[a] = min(dp[a], dp[a - c] + 1)   # best of: current best, or (best for the rest) + this coin
    return dp[amount] if dp[amount] != INF else -1   # still impossible means return -1


print(coin_change([1, 2, 5], 11))             # expect 3
assert coin_change([1, 2, 5], 11) == 3        # example 1: 5 + 5 + 1
assert coin_change([2], 3) == -1              # example 2: impossible
assert coin_change([1], 0) == 0               # example 3: amount 0 needs no coins
assert coin_change([1, 3, 4], 6) == 2         # edge case: greedy would say 3, DP says 2 (3+3)
assert coin_change([186, 419, 83, 408], 6249) == 20   # a larger input (LeetCode test), still fast
assert coin_change([5], 3) == -1              # edge case: every coin is too big
```

**Trace**: `coins = [1, 2, 5]`, `amount = 11`. `X` means "impossible so far".

```
index a:  0  1  2  3  4  5  6  7  8  9  10 11
Step A: base
dp:       0  X  X  X  X  X  X  X  X  X  X  X

Step B: a=1: coin 1 -> dp[0]+1 = 1.  (2 and 5 do not fit)                       dp[1]=1
Step C: a=2: coin 1 -> dp[1]+1 = 2.  coin 2 -> dp[0]+1 = 1.  min = 1            dp[2]=1
Step D: a=3: coin 1 -> dp[2]+1 = 2.  coin 2 -> dp[1]+1 = 2.  min = 2            dp[3]=2
Step E: a=4: coin 1 -> dp[3]+1 = 3.  coin 2 -> dp[2]+1 = 2.  min = 2            dp[4]=2
Step F: a=5: coin 1 -> dp[4]+1 = 3.  coin 2 -> dp[3]+1 = 3.  coin 5 -> dp[0]+1 = 1.  min = 1   dp[5]=1
Step G: a=6: coin 1 -> dp[5]+1 = 2.  coin 2 -> dp[4]+1 = 3.  coin 5 -> dp[1]+1 = 2.  min = 2   dp[6]=2
Step H: a=7: coin 1 -> dp[6]+1 = 3.  coin 2 -> dp[5]+1 = 2.  coin 5 -> dp[2]+1 = 2.  min = 2   dp[7]=2
Step I: a=8: coin 1 -> dp[7]+1 = 3.  coin 2 -> dp[6]+1 = 3.  coin 5 -> dp[3]+1 = 3.  min = 3   dp[8]=3
Step J: a=9: coin 1 -> dp[8]+1 = 4.  coin 2 -> dp[7]+1 = 3.  coin 5 -> dp[4]+1 = 3.  min = 3   dp[9]=3
Step K: a=10: coin 1 -> dp[9]+1 = 4. coin 2 -> dp[8]+1 = 4.  coin 5 -> dp[5]+1 = 2.  min = 2   dp[10]=2
Step L: a=11: coin 1 -> dp[10]+1 = 3. coin 2 -> dp[9]+1 = 4. coin 5 -> dp[6]+1 = 3.  min = 3   dp[11]=3

final table:
index a:  0  1  2  3  4  5  6  7  8  9  10 11
dp:       0  1  1  2  2  1  2  2  3  3  2  3      <- answer dp[11] = 3  (5 + 5 + 1)
```

**Complexity.** Time O(amount x number of coins): two loops. Space O(amount) for the table.

**Edge cases.**
1. `amount = 0`: answer 0.
2. No combination possible (`[2]`, amount `3`): `-1`. This is why we start with "impossible" values and check at the end.
3. Greedy trap: `[1,3,4]`, amount `6`.

**How interviewers twist it.**
- "Count the **number of ways** to make the amount" (Coin Change II, LeetCode 518): `dp[a] += dp[a - c]`, with the **coin loop outside** and the amount loop inside, to count combinations not orders.
- "Return the coins used": store which coin gave the best value at each amount, then walk back.
- "Each coin can be used once": it becomes a 0/1 knapsack (lesson 16).

---

### 5.4 Unique Paths (LeetCode 62)

**In plain words.** A robot is on the top-left of an `m x n` grid. It can only move **right** or **down**. How many different paths lead to the bottom-right?

**Brute force.** Recursion: `paths(r, c) = paths(r-1, c) + paths(r, c-1)`. The same cells are recomputed again and again. O(2^(m+n)).

**Better idea, slowly.**
1. State: `dp[r][c]` = number of paths from the top-left to cell `(r, c)`.
2. To arrive at `(r, c)`, the robot came from above `(r-1, c)` or from the left `(r, c-1)`. So `dp[r][c] = dp[r-1][c] + dp[r][c-1]`.
3. The whole first row and first column have exactly one path (straight line). So fill them with 1.
4. Fill the rest row by row.

```python
def unique_paths(m: int, n: int) -> int:      # number of paths in an m-row, n-column grid
    dp = [[1] * n for _ in range(m)]          # start with all 1s: the first row and column are all 1
    for r in range(1, m):                     # from the second row down
        for c in range(1, n):                 # from the second column right
            dp[r][c] = dp[r - 1][c] + dp[r][c - 1]   # paths from above plus paths from the left
    return dp[m - 1][n - 1]                   # the bottom-right cell


print(unique_paths(3, 3))                     # expect 6
assert unique_paths(3, 7) == 28               # example 1
assert unique_paths(3, 2) == 3                # example 2
assert unique_paths(1, 1) == 1                # edge case: already at the goal
assert unique_paths(1, 10) == 1               # edge case: a single row has one path
assert unique_paths(10, 10) == 48620          # a bigger grid
```

**Trace** on `m = 3`, `n = 3`:

```
Step A: start with all 1s
1  1  1
1  1  1
1  1  1

Step B: r=1, c=1: dp = above (1) + left (1) = 2
1  1  1
1  2  1
1  1  1

Step C: r=1, c=2: dp = above (1) + left (2) = 3
1  1  1
1  2  3
1  1  1

Step D: r=2, c=1: dp = above (2) + left (1) = 3
1  1  1
1  2  3
1  3  1

Step E: r=2, c=2: dp = above (3) + left (3) = 6
1  1  1
1  2  3
1  3  6          <- answer: 6
```

**Complexity.** Time O(m x n): each cell is filled once. Space O(m x n); it can be O(n) by keeping only one row.

**Edge cases.**
1. A single row or column: only one path.
2. A `1 x 1` grid: one path (you are already there).

**How interviewers twist it.**
- "Some cells have obstacles" (Unique Paths II, LeetCode 63): if a cell is blocked, `dp = 0` there.
- "Find the path with the smallest sum" (Minimum Path Sum, LeetCode 64): `dp[r][c] = grid[r][c] + min(above, left)`.
- "Math solution": the answer is `C(m+n-2, m-1)`, "choose which of the moves are down". Mention it after the DP.

---

## 6. Common mistakes

1. **Not saying what `dp[i]` means.** If you cannot say it in one sentence, the recurrence will be wrong.
2. **Wrong base cases.** Check the smallest input by hand (`n = 0`, `n = 1`).
3. **Filling the table in the wrong order.** When computing `dp[i]`, the cells it uses must already be filled.
4. **Using greedy when DP is needed** (Coin Change with `[1,3,4]`).
5. **Off-by-one in the table size.** For "amount up to N" use `N + 1` cells (`0..N`).
6. **Using `0` as "impossible" when `0` is a valid answer.** Use a large number (or `float("inf")`).
7. **Memo with a mutable default argument** like `def f(n, memo={})`. It shares one dictionary between calls. Use `memo=None` as in section 4a, or `lru_cache`.
8. **Recursion too deep.** Python stops at about 1000 calls. For large `n` use the table version.

---

## 7. Practice list (8 more problems)

Tags come from public LeetCode company-tag lists I read (GitHub mirror, snapshot Oct 2025; see lesson 19). A tag means "the problem is in that company's list". No tag means not verified. The problems taught above are tagged too: Climbing Stairs, House Robber, Coin Change and Unique Paths are each in the lists of Amazon, Google, Meta and Microsoft.

| # | Problem | Difficulty | Tagged for |
|---|---|---|---|
| 1 | Min Cost Climbing Stairs (746) | Easy | Amazon |
| 2 | Decode Ways (91) | Medium | Amazon, Google, Meta, Microsoft |
| 3 | House Robber II (213) | Medium | not verified |
| 4 | Coin Change II (518) | Medium | not verified |
| 5 | Minimum Path Sum (64) | Medium | not verified |
| 6 | Perfect Squares (279) | Medium | not verified |
| 7 | Jump Game (55) | Medium | Amazon, Google, Meta, Microsoft |
| 8 | Maximum Product Subarray (152) | Medium | not verified |

---

## 8. Self-quiz (5 questions)

1. In your own words, what two things must be true for a problem to be a good fit for DP?
2. What is the difference between memoization and tabulation?
3. In Climbing Stairs, why is `dp[i] = dp[i-1] + dp[i-2]`?
4. Why does the greedy "biggest coin first" fail for coins `[1, 3, 4]` and amount `6`?
5. In House Robber, what are the two choices at house `i`, and what does each add up to?

**Answers.**
1. Overlapping subproblems (the same small problem repeats) and optimal substructure (the best big answer is made from best small answers).
2. Memoization is recursion from the top, saving each answer in a dictionary the first time. Tabulation is a loop that fills a table from the smallest case up to the answer.
3. The last move to reach stair `i` was either a 1-step from `i-1` or a 2-step from `i-2`. The ways add up.
4. Greedy takes 4 first, then needs 2 more, so `4+1+1` is 3 coins. But `3+3` is 2 coins. Taking the biggest coin first is not always best.
5. Skip house `i`: keep `dp[i-1]`. Rob house `i`: take `dp[i-2] + nums[i]` (you cannot use house `i-1`). Pick the larger.
