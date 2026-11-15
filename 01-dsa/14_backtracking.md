# Lesson 14: Backtracking (subsets, permutations, combination sum, word search)

All code is Python 3.9. Every code block in this file was run with `python3` (3.9.6) before it was written here.

---

## Words you need first

- **Backtracking**: try a choice. If it leads nowhere (or after you recorded the result), **undo the choice** and try the next one.
- **Decision tree**: a picture where each step is "what do I choose now?" and each branch is one choice.
- **Recursion**: a function that calls itself. Each call handles "the rest of the problem".
- **Path** (or "current choices"): the list of choices you have made so far.
- **Pruning**: stop early on a branch that cannot work. It saves time.
- **Combination**: a group where **order does not matter** (`[1,2]` is the same as `[2,1]`).
- **Permutation**: a group where **order matters** (`[1,2]` and `[2,1]` are different).
- **Subset**: any group you can pick from the items, including the empty group.

---

## 1. What is this?

Backtracking is **"try everything, but cleverly"**. You build an answer one piece at a time. After each piece you go deeper. When you come back, you remove the last piece and try another one.

**Analogy: finding the way in a maze with chalk.**
At a crossroad you choose a corridor and write an arrow in chalk. You walk. At a dead end you walk back, rub out the arrow, and try the next corridor. You never walk the same corridor twice from the same crossroad.

**The three words to remember: CHOOSE, EXPLORE, UN-CHOOSE.**

```
for each choice available now:
    choose it            (add it to the path)
    explore              (recursive call for the rest of the problem)
    un-choose it         (remove it from the path, so the next choice starts clean)
```

When the path is a complete answer, save a **copy** of it. (If you save the path itself, later changes will change your saved answer. This is the most common bug.)

---

## 2. When do I use it?

| Words in the problem | Idea |
|---|---|
| "**all** subsets / permutations / combinations" | Backtracking (the answer is a list of lists) |
| "**generate all** valid ..." (parentheses, IP addresses) | Backtracking with a validity check |
| "find **all ways** to reach a target sum" | Backtracking |
| "does a **word exist** in the grid" (path with no reuse) | Backtracking on a grid |
| "place N queens", "solve Sudoku" | Backtracking with pruning |
| Input size is small (like n at most 10 to 20) | Strong hint that an exponential answer is expected |

If the problem only asks "how **many** ways" or "the **best** value" (not the list), try dynamic programming (lessons 15 and 16) first. Backtracking is for when you must **list** the answers.

---

## 3. Trace of a tiny example: all subsets of `[1, 2, 3]`

The decision tree. At each step we decide which number to add next. We only add numbers **after** the last one used (so `[1,2]` appears, but `[2,1]` does not).

```
                       []
          /             |             \
        [1]            [2]            [3]
       /    \            |
   [1,2]   [1,3]       [2,3]
     |
  [1,2,3]
```

Every node in this tree is one subset. There are 8 nodes, and `2^3 = 8`. 

Step by step. `start` tells the function from which index it may pick. `path` is the current subset.

```
call (start=0, path=[])        record []
  i=0: choose 1 -> path=[1]
  call (start=1, path=[1])     record [1]
    i=1: choose 2 -> path=[1,2]
    call (start=2, path=[1,2]) record [1,2]
      i=2: choose 3 -> path=[1,2,3]
      call (start=3, path=[1,2,3])  record [1,2,3]   (no more numbers: loop does nothing)
      un-choose 3 -> path=[1,2]
    un-choose 2 -> path=[1]
    i=2: choose 3 -> path=[1,3]
    call (start=3, path=[1,3]) record [1,3]
    un-choose 3 -> path=[1]
  un-choose 1 -> path=[]
  i=1: choose 2 -> path=[2]
  call (start=2, path=[2])     record [2]
    i=2: choose 3 -> path=[2,3]
    call (start=3, path=[2,3]) record [2,3]
    un-choose 3 -> path=[2]
  un-choose 2 -> path=[]
  i=2: choose 3 -> path=[3]
  call (start=3, path=[3])     record [3]
  un-choose 3 -> path=[]
recorded in order: [], [1], [1,2], [1,2,3], [1,3], [2], [2,3], [3]
```

---

## 4. Template code

```python
def backtrack_template(items):                # return all subsets of items
    results = []                              # all the answers we collect
    path = []                                 # the choices made so far

    def explore(start):                       # explore from this position
        results.append(path[:])               # record a COPY of the current path (path[:] makes the copy)
        for i in range(start, len(items)):    # try every choice from "start" onward
            path.append(items[i])             # CHOOSE: add the item to the path
            explore(i + 1)                    # EXPLORE: continue, only with later items
            path.pop()                        # UN-CHOOSE: remove it, so the next loop turn starts clean

    explore(0)                                # begin with the whole list available
    return results                            # all collected answers


out = backtrack_template([1, 2, 3])           # run the template
print(out)                                    # the order matches our hand trace
assert out == [[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]]   # same as the trace in section 3
```

The template for other problems changes only three things:
1. **When to record**: at every node (subsets), only when the path is full (permutations), or only when the sum equals the target (combination sum).
2. **Which choices are allowed**: later items only, unused items only, or items that keep the sum within the target.
3. **What to pass down**: `i + 1` (no reuse), `i` (reuse allowed), or nothing (permutations use a `used` marker).

---

## 5. Classic problems

### 5.1 Subsets (LeetCode 78)

**In plain words.** Given a list of different numbers, return every possible subset (the power set). `[1,2,3]` gives 8 subsets, from `[]` to `[1,2,3]`.

**Brute force idea.** Count from `0` to `2^n - 1`. Each number's binary digits say "take this item" or not. It works (and is called the bitmask method), but it is less general than backtracking.

**Better idea (backtracking), slowly.**
1. Each item has two options: **in** or **out**. So the total is `2 x 2 x ... = 2^n`.
2. Our template records the path at every node. Every path is a different subset.
3. To avoid `[1,2]` and `[2,1]` both appearing, each call only picks items **after** the one just used (`start` goes up).

```python
from typing import List                       # type hints


def subsets(nums: List[int]) -> List[List[int]]:   # all subsets
    results: List[List[int]] = []             # answers collected here
    path: List[int] = []                      # current subset

    def explore(start: int) -> None:          # choose next items from index "start"
        results.append(path[:])               # every path is a valid subset: save a copy
        for i in range(start, len(nums)):     # candidates are the items from start onward
            path.append(nums[i])              # choose
            explore(i + 1)                    # explore with only later items
            path.pop()                        # un-choose

    explore(0)                                # begin
    return results                            # all 2^n subsets


print(subsets([1, 2, 3]))                     # expect 8 subsets
assert subsets([1, 2, 3]) == [[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]]   # example 1
assert subsets([0]) == [[], [0]]              # example 2
assert subsets([]) == [[]]                    # edge case: empty input has one subset, the empty one
assert len(subsets(list(range(10)))) == 1024  # edge case: 2^10 subsets
```

**Trace**: it is exactly the trace in section 3.

**Complexity.** Time O(n x 2^n): there are `2^n` subsets and copying one costs up to `n`. Space O(n) for the recursion and the path (not counting the output, which is O(n x 2^n)).

**Edge cases.**
1. Empty input: the answer is `[[]]`, not `[]`. The empty set is a subset.
2. Saving `path` instead of `path[:]`: every saved answer ends up empty at the end. Always copy.

**How interviewers twist it.**
- "The list has **duplicates**" (Subsets II, LeetCode 90): sort first. In the loop, skip an item if it equals the previous one *at the same level*: `if i > start and nums[i] == nums[i-1]: continue`.
- "Only subsets of size k" (Combinations, LeetCode 77): record only when `len(path) == k`, and stop early when not enough items remain.
- "Count subsets with sum S" (not list them): that is dynamic programming, faster.

---

### 5.2 Permutations (LeetCode 46)

**In plain words.** Given different numbers, return all possible orderings. `[1,2,3]` gives 6: `[1,2,3]`, `[1,3,2]`, `[2,1,3]`, `[2,3,1]`, `[3,1,2]`, `[3,2,1]`.

**Brute force idea.** There is no cheaper way than listing them, since there are `n!` answers. Python's `itertools.permutations` does it too, but in an interview you must show the logic.

**Better idea (backtracking), slowly.**
1. A permutation is built **one position at a time**. For position 0, any item can go there. For position 1, any item **not used yet**. And so on.
2. Keep a `used` list of True/False so we know which items are already in the path.
3. The path is complete when its length equals `n`. Only then do we record it.

```python
from typing import List                       # type hints


def permute(nums: List[int]) -> List[List[int]]:   # all orderings
    results: List[List[int]] = []             # answers
    path: List[int] = []                      # the ordering being built
    used = [False] * len(nums)                # used[i] is True if nums[i] is already in the path

    def explore() -> None:                    # fill the next position
        if len(path) == len(nums):            # all positions filled
            results.append(path[:])           # record a copy
            return                            # nothing more to do on this branch
        for i in range(len(nums)):            # any item may be tried here
            if used[i]:                       # already placed earlier in the path
                continue                      # skip it
            used[i] = True                    # choose: mark as used
            path.append(nums[i])              # choose: add to the path
            explore()                         # explore the next position
            path.pop()                        # un-choose: remove from the path
            used[i] = False                   # un-choose: mark as unused again

    explore()                                 # begin with an empty path
    return results                            # all n! orderings


print(permute([1, 2, 3]))                     # expect 6 orderings
assert permute([1, 2, 3]) == [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]   # example 1
assert permute([0, 1]) == [[0, 1], [1, 0]]    # example 2
assert permute([1]) == [[1]]                  # example 3
assert permute([]) == [[]]                    # edge case: one way to arrange nothing
assert len(permute([1, 2, 3, 4, 5])) == 120   # edge case: 5! = 120
```

**Trace** (the first branch only, `nums=[1,2,3]`):

```
explore: path=[]  used=[F,F,F]
 i=0: choose 1 -> path=[1], used=[T,F,F]
  explore: path=[1]
   i=0: used -> skip
   i=1: choose 2 -> path=[1,2], used=[T,T,F]
    explore: path=[1,2]
     i=0: used. i=1: used.
     i=2: choose 3 -> path=[1,2,3], used=[T,T,T]
      explore: length 3 == 3 -> record [1,2,3], return
     un-choose 3 -> path=[1,2], used=[T,T,F]
    (loop ends) return
   un-choose 2 -> path=[1], used=[T,F,F]
   i=2: choose 3 -> path=[1,3], used=[T,F,T]
    explore: path=[1,3]
     i=1: choose 2 -> path=[1,3,2] -> record [1,3,2]
     un-choose 2
    un-choose 3
 un-choose 1 -> path=[], used=[F,F,F]
 i=1: choose 2 -> ... (gives [2,1,3] and [2,3,1])
 i=2: choose 3 -> ... (gives [3,1,2] and [3,2,1])
```

**Complexity.** Time O(n x n!): there are `n!` permutations, and copying each costs `n`. Space O(n) for the recursion, the path and `used`.

**Edge cases.**
1. Empty list: one permutation, the empty one (`[[]]`).
2. One item: just `[[item]]`.

**How interviewers twist it.**
- "Items may repeat" (Permutations II, LeetCode 47): sort, then skip `nums[i]` if it equals `nums[i-1]` and `nums[i-1]` is not used (this stops the same ordering appearing twice).
- "Next permutation" (LeetCode 31): do it in place in O(n), no recursion.
- "Return only the k-th permutation" (LeetCode 60): use factorials to jump straight to it.

---

### 5.3 Combination Sum (LeetCode 39)

**In plain words.** You get different positive numbers `candidates` and a `target`. Return all unique combinations whose sum equals `target`. **You may use the same number many times.** `[2,3,6,7]`, target `7` gives `[[2,2,3],[7]]`.

**Brute force idea.** Try all combinations of any size with repeats. There is no natural limit, so you must stop when the sum is too big. That *is* the backtracking idea.

**Better idea, slowly.**
1. Keep the `remaining` target (target minus the sum so far).
2. If `remaining == 0`, the path is an answer. Record it.
3. If `remaining < 0`, we went too far. Stop this branch (**pruning**).
4. Otherwise loop over candidates from `start` onward. Choose one, then call again with `remaining - that number`.
5. Pass `i` (not `i + 1`) because the same number may be used again.
6. Passing `start = i` (never going back to earlier items) stops `[2,3]` and `[3,2]` both appearing.

```python
from typing import List                       # type hints


def combination_sum(candidates: List[int], target: int) -> List[List[int]]:   # all combinations that sum to target
    results: List[List[int]] = []             # answers
    path: List[int] = []                      # current combination
    nums = sorted(candidates)                 # sorting lets us stop early when numbers get too big

    def explore(start: int, remaining: int) -> None:   # remaining = target - sum(path)
        if remaining == 0:                    # exact hit
            results.append(path[:])           # record a copy
            return                            # no need to go deeper
        for i in range(start, len(nums)):     # try numbers from index start onward
            if nums[i] > remaining:           # this number is too big, and later ones are bigger
                break                         # prune: stop the loop
            path.append(nums[i])              # choose
            explore(i, remaining - nums[i])   # explore; pass i (not i+1) because reuse is allowed
            path.pop()                        # un-choose

    explore(0, target)                        # begin
    return results                            # all combinations


print(combination_sum([2, 3, 6, 7], 7))       # expect [[2, 2, 3], [7]]
assert combination_sum([2, 3, 6, 7], 7) == [[2, 2, 3], [7]]   # example 1
assert combination_sum([2, 3, 5], 8) == [[2, 2, 2, 2], [2, 3, 3], [3, 5]]   # example 2
assert combination_sum([2], 1) == []          # example 3 / edge case: impossible
assert combination_sum([1], 3) == [[1, 1, 1]] # edge case: one candidate used many times
assert combination_sum([], 5) == []           # edge case: no candidates
```

**Trace** on `[2,3,6,7]`, target `7`:

```
explore(start=0, remaining=7), path=[]
 i=0: 2 <= 7 -> choose 2, path=[2]
  explore(0, 5)
   i=0: 2 <= 5 -> choose 2, path=[2,2]
    explore(0, 3)
     i=0: 2 <= 3 -> choose 2, path=[2,2,2]
      explore(0, 1)
       i=0: 2 > 1 -> break (prune)
      un-choose 2, path=[2,2]
     i=1: 3 <= 3 -> choose 3, path=[2,2,3]
      explore(1, 0): remaining 0 -> RECORD [2,2,3]
      un-choose 3, path=[2,2]
     i=2: 6 > 3 -> break
    un-choose 2, path=[2]
   i=1: 3 <= 5 -> choose 3, path=[2,3]
    explore(1, 2)
     i=1: 3 > 2 -> break
    un-choose 3, path=[2]
   i=2: 6 > 5 -> break
  un-choose 2, path=[]
 i=1: 3 <= 7 -> choose 3, path=[3]
  explore(1, 4): i=1: 3 <= 4 -> choose 3, path=[3,3], explore(1,1): 3 > 1 break. un-choose.
                 i=2: 6 > 4 -> break
  un-choose 3
 i=2: 6 <= 7 -> choose 6, path=[6]
  explore(2, 1): 6 > 1 -> break
  un-choose 6
 i=3: 7 <= 7 -> choose 7, path=[7]
  explore(3, 0): remaining 0 -> RECORD [7]
  un-choose 7
result: [[2,2,3],[7]]
```

**Complexity.** Time: there is no clean formula. It depends on how many paths of valid length exist. Roughly, with the smallest number `m`, the depth is at most `target / m`, and each level can branch up to `n` ways, so we say "exponential in `target / m`". Space O(`target / m`) for the recursion depth and path.

**Edge cases.**
1. No combination exists (`[2]`, target `1`): return `[]`.
2. A candidate larger than the target is skipped by the `break`.

**How interviewers twist it.**
- "Each number may be used **only once**" (Combination Sum II, LeetCode 40): pass `i + 1`, and skip equal neighbours at the same level (sort first).
- "Return only the **count** of ways" (Coin Change II style): dynamic programming (lesson 15).
- "Only numbers 1 to 9, exactly k numbers" (Combination Sum III, LeetCode 216): add a length check.

---

### 5.4 Word Search (LeetCode 79)

**In plain words.** A grid of letters. Does the given word exist in the grid? You build the word by moving up, down, left or right from letter to letter. You **cannot use the same cell twice** in one word.

**Brute force idea.** Try each cell as a start, and follow all paths. That *is* backtracking. The only question is how to avoid reusing a cell.

**Better idea, slowly.**
1. For each cell that matches the first letter, start a search.
2. `search(r, c, k)` means: "Cell `(r, c)` should match `word[k]`. Can we finish the word from here?"
3. Base case: if `k == len(word)`, we matched every letter, so return `True`.
4. If the cell is outside the grid, or its letter is not `word[k]`, return `False`.
5. **Choose**: mark the cell as used by replacing its letter with `"#"`. **Explore** four neighbours with `k + 1`. **Un-choose**: put the original letter back.
6. If any neighbour returns `True`, return `True`.

```python
from typing import List                       # type hints


def exist(board: List[List[str]], word: str) -> bool:   # does the word exist in the grid?
    rows, cols = len(board), len(board[0])    # grid size

    def search(r: int, c: int, k: int) -> bool:   # can we match word[k:] starting at (r, c)?
        if k == len(word):                    # every letter matched
            return True                       # success
        if r < 0 or r >= rows or c < 0 or c >= cols:   # outside the grid
            return False                      # fail
        if board[r][c] != word[k]:            # wrong letter (this also catches "#", the used marker)
            return False                      # fail
        saved = board[r][c]                   # remember the letter
        board[r][c] = "#"                     # choose: mark the cell as used
        found = (search(r + 1, c, k + 1) or search(r - 1, c, k + 1)     # explore down and up
                 or search(r, c + 1, k + 1) or search(r, c - 1, k + 1)) # and right and left
        board[r][c] = saved                   # un-choose: put the letter back
        return found                          # tell the caller

    for r in range(rows):                     # try every cell as the start
        for c in range(cols):                 # every column
            if search(r, c, 0):               # does the word start here?
                return True                   # yes
    return False                              # no start worked


grid = [list("ABCE"), list("SFCS"), list("ADEE")]   # the LeetCode example grid
print(exist(grid, "ABCCED"), exist(grid, "SEE"), exist(grid, "ABCB"))   # expect True True False
assert exist(grid, "ABCCED") is True          # example 1
assert exist(grid, "SEE") is True             # example 2
assert exist(grid, "ABCB") is False           # example 3: would need B twice
assert exist([list("A")], "A") is True        # edge case: one cell
assert exist([list("A")], "AA") is False      # edge case: word longer than the grid
assert grid == [list("ABCE"), list("SFCS"), list("ADEE")]   # the board is restored after the search
```

**Trace** on `word = "SEE"`, same grid (rows written out):

```
row0:  A B C E
row1:  S F C S
row2:  A D E E
```

```
try (0,0)=A: not S -> False.  (0,1)=B, (0,2)=C, (0,3)=E: not S -> False.
try (1,0)=S: matches word[0]='S'. mark (1,0)='#'.
   neighbour down (2,0)=A: not 'E' -> False.
   neighbour up (0,0)=A: not 'E' -> False.
   neighbour right (1,1)=F: not 'E' -> False.
   neighbour left: outside -> False.
   un-mark (1,0)='S'. result False.
try (1,1)=F, (1,2)=C: not S -> False.
try (1,3)=S: matches. mark (1,3)='#'.
   down (2,3)=E: matches word[1]='E'. mark (2,3)='#'.
      down: outside.  up (1,3)='#': not 'E'.  right: outside.
      left (2,2)=E: matches word[2]='E'. mark it. k becomes 3 == len(word) at the next call -> True.
   returns True all the way up.
answer: True
```

**Complexity.** Time O(R x C x 3^L), where L is the word length. From each start we can go in at most 3 new directions at each step (not back where we came from), for L steps. Space O(L) for the recursion depth (the board is changed in place, not copied).

**Edge cases.**
1. The word needs the same cell twice (`"ABCB"`): the `"#"` marker prevents it.
2. Forgetting to restore the cell: later searches see a damaged board and give wrong answers.

**How interviewers twist it.**
- "Find **all** words from a list" (Word Search II, LeetCode 212): use a **trie** (lesson 17) so you search for all words at once.
- "Early exit": count the letters in the board and the word first. If the word needs more of some letter than the board has, return `False` at once. Also, if the last letter of the word is rarer than the first letter, search for the reversed word.
- "Diagonal moves also allowed": add four directions.

---

### 5.5 Generate Parentheses (LeetCode 22)

**In plain words.** Given `n` pairs of parentheses, list all valid (well-formed) strings. For `n = 3` there are 5: `((()))`, `(()())`, `(())()`, `()(())`, `()()()`.

**Brute force.** Generate all `2^(2n)` strings of `(` and `)`, and test each for validity. Wasteful: most are invalid.

**Better idea, slowly.**
1. Build the string one character at a time. At each step we may add `(` or `)`.
2. Add `(` only if we have not used all `n` open brackets yet.
3. Add `)` only if it will not break the string, which means there are more `(` than `)` so far.
4. These two rules keep the string valid at every step, so we never build garbage. This is **pruning**.
5. When the string has length `2n`, record it.

```python
from typing import List                       # type hints


def generate_parenthesis(n: int) -> List[str]:   # all valid strings with n pairs
    results: List[str] = []                   # answers
    path: List[str] = []                      # characters chosen so far

    def explore(open_count: int, close_count: int) -> None:   # how many ( and ) used so far
        if len(path) == 2 * n:                # the string is complete
            results.append("".join(path))     # join the characters and record
            return                            # done with this branch
        if open_count < n:                    # we may still open a bracket
            path.append("(")                  # choose "("
            explore(open_count + 1, close_count)   # explore
            path.pop()                        # un-choose
        if close_count < open_count:          # a ")" is valid only if some "(" is still unclosed
            path.append(")")                  # choose ")"
            explore(open_count, close_count + 1)   # explore
            path.pop()                        # un-choose

    explore(0, 0)                             # begin with nothing used
    return results                            # all valid strings


print(generate_parenthesis(3))                # expect 5 strings
assert generate_parenthesis(3) == ["((()))", "(()())", "(())()", "()(())", "()()()"]   # example 1
assert generate_parenthesis(1) == ["()"]      # example 2
assert generate_parenthesis(0) == [""]        # edge case: zero pairs gives one empty string
assert len(generate_parenthesis(4)) == 14     # edge case: n=4 has 14 answers (Catalan number)
```

**Trace** on `n = 2`:

```
explore(open=0, close=0), path=""
 open 0 < 2 -> add "(" -> path="("
  explore(1,0)
   open 1 < 2 -> add "(" -> path="(("
    explore(2,0)
     open 2 < 2? no.  close 0 < open 2 -> add ")" -> path="(()"
      explore(2,1)
       open? no.  close 1 < 2 -> add ")" -> path="(())"
        explore(2,2): length 4 -> RECORD "(())"
       un-choose
      un-choose
    un-choose "("   (path="(")
   close 0 < open 1 -> add ")" -> path="()"
    explore(1,1)
     open 1 < 2 -> add "(" -> path="()("
      explore(2,1)
       open? no.  close 1 < 2 -> add ")" -> path="()()"
        explore(2,2): length 4 -> RECORD "()()"
result: ["(())", "()()"]
```

**Complexity.** Time about O(4^n / sqrt(n)): that is the number of valid strings (the Catalan number), times the work of building each. Space O(n) for the recursion depth.

**Edge cases.**
1. `n = 0`: one result, the empty string.
2. Adding `)` too early (like `)(`): the rule `close < open` forbids it.

**How interviewers twist it.**
- "Valid Parentheses" (check one string): that is a stack problem (lesson 05).
- "Remove the minimum number of invalid parentheses" (LeetCode 301): BFS or backtracking with counters.
- "Three kinds of brackets": the choose step tries `(`, `[`, `{`, with a stack to know which close bracket is allowed.

---

## 6. Common mistakes

1. **Saving `path` instead of a copy** (`path[:]` or `list(path)`). All your answers become the same (usually empty) list.
2. **Forgetting to un-choose.** Then the path keeps old choices, and answers are wrong.
3. **Passing `i + 1` when reuse is allowed (Combination Sum), or `i` when it is not.** Check the problem statement.
4. **Starting the loop at 0 every time for subsets and combinations.** You will get `[1,2]` and `[2,1]` both. Use `start`.
5. **Not pruning.** The code is right but slow. Use `break` when sorted numbers exceed the remainder.
6. **Not restoring the grid in Word Search.** The `"#"` stays and breaks the next start.
7. **Mixing up the complexity.** The output size itself is exponential. That is normal for these problems. Say so to the interviewer.
8. **Forgetting duplicates.** If the input can contain duplicates, sort and skip equal neighbours at the same level.

---

## 7. Practice list (8 more problems)

Tags come from public LeetCode company-tag lists I read (GitHub mirror, snapshot Oct 2025; see lesson 19). A tag means "the problem is in that company's list". No tag means not verified. The problems taught above are tagged too: Subsets, Permutations, Combination Sum and Word Search are each in the lists of Amazon, Google, Meta and Microsoft. Generate Parentheses is in the lists of Amazon, Google and Microsoft.

| # | Problem | Difficulty | Tagged for |
|---|---|---|---|
| 1 | Subsets II (90) | Medium | not verified |
| 2 | Permutations II (47) | Medium | not verified |
| 3 | Combination Sum II (40) | Medium | not verified |
| 4 | Letter Combinations of a Phone Number (17) | Medium | Amazon, Google, Meta, Microsoft |
| 5 | Palindrome Partitioning (131) | Medium | Amazon, Google |
| 6 | N-Queens (51) | Hard | Google |
| 7 | Word Search II (212) | Hard | Amazon, Google, Meta, Microsoft |
| 8 | Sudoku Solver (37) | Hard | not verified |

---

## 8. Self-quiz (5 questions)

1. What are the three steps inside every backtracking loop?
2. Why must you save `path[:]` and not `path` when recording an answer?
3. In Combination Sum we call `explore(i, ...)` but in Subsets we call `explore(i + 1)`. Why?
4. How many subsets does a list of 10 different numbers have? How many permutations?
5. What does "pruning" mean, and give one example from this lesson.

**Answers.**
1. Choose (add to path), explore (recursive call), un-choose (remove from path).
2. `path` is one list that keeps changing. If you save the list itself, later changes change your saved answer. `path[:]` makes an independent copy.
3. In Combination Sum the same number may be reused, so the next call may pick index `i` again. In Subsets each item is used at most once, so the next call starts after `i`.
4. Subsets: `2^10 = 1024`. Permutations: `10! = 3,628,800`.
5. Pruning means stopping a branch early when it cannot lead to an answer. Example: in Combination Sum, if the number is bigger than the remaining target, we `break`. In Generate Parentheses, we never add `)` unless a `(` is open.
