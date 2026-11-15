# Lesson 17: Tries and Greedy

All code is Python 3.9. Every code block in this file was run with `python3` (3.9.6) before it was written here.

This lesson has two separate ideas. Part A is a data structure for words (the trie). Part B is a way of thinking (greedy).

---

# Part A: Tries

## Words you need first

- **Prefix**: the first few letters of a word. `"ca"` is a prefix of `"cat"` and `"car"`.
- **Trie** (say "try"): a tree where each step down is **one letter**. Words that start the same way share the same path. It is also called a **prefix tree**.
- **Node**: one box in the tree. Here, each node has a dictionary `children` (letter -> next node) and a flag `is_end` ("a word finishes here").
- **Wildcard**: a symbol that matches any letter. In problem 5.2 the dot `.` matches any one letter.

## 1. What is this? (trie)

**Analogy: a phone's autocomplete, or a paper dictionary's thumb index.**
When you type `ca`, the phone does not scan every word. It goes to the `c` page, then the `a` page, and shows everything under it.

A trie stores words so that **the time to look up a word depends on the word's length, not on how many words are stored**. A hash set can also say "is this exact word stored?", but a hash set cannot quickly answer "are there any words that **start with** `ca`?". A trie can.

**Picture.** Insert `cat`, `car`, `dog`. `*` means "a word ends here".

```
root
 |-- c
 |    `-- a
 |         |-- t*      (cat)
 |         `-- r*      (car)
 `-- d
      `-- o
           `-- g*      (dog)
```

## 2. When do I use it? (trie)

| Words in the problem | Idea |
|---|---|
| "words that **start with** ...", "prefix" | Trie |
| "**autocomplete**", "type-ahead", "search suggestions" | Trie |
| "design a dictionary with `insert`, `search`, `startsWith`" | Trie |
| "find **many words** in a grid" (Word Search II) | Trie + backtracking |
| "words with a **wildcard** letter" | Trie + DFS |
| "longest common prefix of many strings" | Trie (or just compare letters) |

## 3. Trace of a tiny example (trie)

Insert `"cat"`, then `"car"`. Then search.

```
insert "cat":
  start at root. 'c' not in root.children -> create node. move to it.
  'a' not in that node's children -> create node. move to it.
  't' not in children -> create node. move to it.
  mark this node is_end = True.
  tree:  root - c - a - t*

insert "car":
  at root. 'c' exists -> just move to it (shared!).
  'a' exists -> just move to it (shared!).
  'r' not in children -> create node. move to it.
  mark is_end = True.
  tree:  root - c - a - t*
                      \- r*

search "car":   follow c, a, r. all exist. last node is_end = True  -> True
search "ca":    follow c, a. both exist. last node is_end = False   -> False  (it is only a prefix)
search "cow":   follow c. then 'o' is not in children               -> False
startsWith "ca": follow c, a. both exist (we do not care about is_end) -> True
```

## 4. Template code (trie)

```python
class TrieNode:                               # one box of the tree
    def __init__(self):                       # a new empty box
        self.children = {}                    # letter -> TrieNode (the next boxes)
        self.is_end = False                   # True if a word finishes at this box


class Trie:                                   # the whole tree
    def __init__(self):                       # start with just a root box
        self.root = TrieNode()                # the root represents the empty prefix

    def insert(self, word):                   # add a word
        node = self.root                      # begin at the root
        for ch in word:                       # for each letter in order
            if ch not in node.children:       # no box for this letter yet?
                node.children[ch] = TrieNode()    # create it
            node = node.children[ch]          # step down into the box
        node.is_end = True                    # a word ends here

    def _walk(self, text):                    # follow the letters; return the last box or None
        node = self.root                      # begin at the root
        for ch in text:                       # for each letter
            if ch not in node.children:       # the path is broken
                return None                   # no such prefix
            node = node.children[ch]          # step down
        return node                           # the box where text ends

    def search(self, word):                   # is this exact word stored?
        node = self._walk(word)               # follow the path
        return node is not None and node.is_end   # the path exists AND a word ends there

    def starts_with(self, prefix):            # does any stored word start with prefix?
        return self._walk(prefix) is not None # the path just needs to exist


t = Trie()                                    # make an empty trie
t.insert("cat")                               # add "cat"
t.insert("car")                               # add "car"
print(t.search("car"), t.search("ca"), t.search("cow"), t.starts_with("ca"))   # expect True False False True
assert t.search("car") is True                # stored word
assert t.search("ca") is False                # only a prefix, not a stored word
assert t.search("cow") is False               # path breaks
assert t.starts_with("ca") is True            # a prefix of two words
assert t.starts_with("d") is False            # nothing starts with d
```

---

## 5. Classic problems (tries)

### 5.1 Implement Trie (Prefix Tree) (LeetCode 208)

**In plain words.** Build a class with three methods: `insert(word)`, `search(word)` (is this exact word stored?), and `startsWith(prefix)`.

**Brute force.** Keep a Python list of words. `search` is `word in list` (O(n x L)). `startsWith` loops over all words and calls `word.startswith(prefix)` (O(n x L)). With a million words, every call is slow.

**Better idea, slowly.** Use the trie from section 4. Every method walks one letter at a time, so the cost depends on the length of the word, not the number of words. `search` and `startsWith` differ only in the last check: `search` also requires `is_end`.

```python
class TrieNode:                               # one box
    def __init__(self):                       # new box
        self.children = {}                    # next boxes by letter
        self.is_end = False                   # True when a word ends here


class Trie:                                   # LeetCode 208
    def __init__(self):                       # make the root
        self.root = TrieNode()                # root = empty prefix

    def insert(self, word: str) -> None:      # add a word
        node = self.root                      # start at the root
        for ch in word:                       # each letter
            node = node.children.setdefault(ch, TrieNode())   # get the box for ch, creating it if missing
        node.is_end = True                    # mark the end of the word

    def search(self, word: str) -> bool:      # exact word?
        node = self._find(word)               # walk the path
        return node is not None and node.is_end   # must exist and must be a word end

    def startsWith(self, prefix: str) -> bool:    # any word with this prefix?
        return self._find(prefix) is not None     # the path must exist

    def _find(self, text: str):               # walk and return the final box, or None
        node = self.root                      # begin at the root
        for ch in text:                       # each letter
            node = node.children.get(ch)      # next box, or None if missing
            if node is None:                  # the path is broken
                return None                   # not found
        return node                           # the final box


trie = Trie()                                 # create it
trie.insert("apple")                          # LeetCode example
print(trie.search("apple"), trie.search("app"), trie.startsWith("app"))   # expect True False True
trie.insert("app")                            # now "app" is a word too
print(trie.search("app"))                     # expect True
assert trie.search("apple") is True           # example
assert trie.search("app") is True             # after inserting "app"
assert trie.startsWith("app") is True         # prefix
assert Trie().search("") is False             # edge case: empty word is not stored in an empty trie
assert Trie().startsWith("") is True          # edge case: the empty prefix always exists
t2 = Trie()                                   # edge case: a word that is a prefix of another
t2.insert("apple")                            # long word
assert t2.search("app") is False              # "app" is only a prefix
```

**Trace**: see section 3 (it is the same walk with `cat` and `car`).

**Complexity.** Each of `insert`, `search`, `startsWith` takes O(L), where L is the length of the word or prefix. Space for the whole trie: O(total number of letters stored) in the worst case (when words share nothing), times the cost of a dictionary entry.

**Edge cases.**
1. A word that is also a prefix of another (`app` and `apple`): the `is_end` flag decides. `search("app")` is `False` until you insert `app`.
2. The empty string: `startsWith("")` is true; `search("")` is false unless you inserted the empty word.

**How interviewers twist it.**
- "Count how many words start with this prefix": keep a counter in each node and add 1 as you pass through it.
- "Delete a word": walk down, unmark `is_end`, and remove boxes that are now useless on the way back.
- "Lowercase letters only": use a list of 26 slots instead of a dictionary. Faster, but a dictionary is simpler and handles any letters.

---

### 5.2 Design Add and Search Words Data Structure (LeetCode 211)

**In plain words.** Build a dictionary with `addWord(word)` and `search(word)`. In `search`, a dot `.` can match **any single letter**. So `search("b..")` can match `"bad"` and `"bat"`.

**Brute force.** Keep a list of words. For each search, compare each word letter by letter, treating `.` as a match. Cost O(n x L) per search.

**Better idea, slowly.**
1. Store the words in a trie (same as 5.1).
2. A normal letter means "follow that one child".
3. A `.` means "try **every** child". So at a dot we use DFS (recursion): for each child, check if the rest of the pattern matches below it.
4. If the letters run out, the answer is `node.is_end`.

```python
from typing import Dict                       # type hints


class TrieNode:                               # one box
    def __init__(self):                       # new box
        self.children: Dict[str, "TrieNode"] = {}    # letter -> next box
        self.is_end = False                   # a word ends here


class WordDictionary:                         # LeetCode 211
    def __init__(self):                       # make the root
        self.root = TrieNode()                # empty prefix

    def addWord(self, word: str) -> None:     # add a word
        node = self.root                      # start at root
        for ch in word:                       # each letter
            node = node.children.setdefault(ch, TrieNode())   # go down, creating if needed
        node.is_end = True                    # a word ends here

    def search(self, word: str) -> bool:      # match, where "." is any letter
        def dfs(node: TrieNode, i: int) -> bool:   # can word[i:] match from this box?
            if i == len(word):                # all letters used
                return node.is_end            # success only if a word ends here
            ch = word[i]                      # the letter (or dot) we must match
            if ch == ".":                     # wildcard
                for child in node.children.values():   # try every possible next letter
                    if dfs(child, i + 1):     # does the rest match below this child?
                        return True           # yes: done
                return False                  # no child worked
            if ch not in node.children:       # a normal letter with no matching path
                return False                  # fail
            return dfs(node.children[ch], i + 1)   # follow the one matching child
        return dfs(self.root, 0)              # begin at the root, at letter 0


wd = WordDictionary()                         # create it
for w in ["bad", "dad", "mad"]:               # the LeetCode example words
    wd.addWord(w)                             # add each
print(wd.search("pad"), wd.search("bad"), wd.search(".ad"), wd.search("b.."))   # expect False True True True
assert wd.search("pad") is False              # example: no word "pad"
assert wd.search("bad") is True               # example
assert wd.search(".ad") is True               # example
assert wd.search("b..") is True               # example
assert wd.search("b.") is False               # edge case: wrong length
assert wd.search("....") is False             # edge case: too long
assert WordDictionary().search("a") is False  # edge case: empty dictionary
```

**Trace** of `search(".ad")` with words `bad`, `dad`, `mad`. The trie: `root` has children `b`, `d`, `m`; each leads to `a`, then `d*`.

```
dfs(root, 0): letter is "." -> try each child of root
  try child b: dfs(b, 1): letter 'a' -> b has child 'a' -> dfs(b.a, 2):
      letter 'd' -> b.a has child 'd' -> dfs(b.a.d, 3):
          i == 3 == len(".ad") -> return is_end -> True
  -> True, return True immediately (we do not need to try d and m)
answer: True
```

For `search("pad")`: the first letter `p` is a normal letter, and root has no child `p`, so it returns `False` at once.

**Complexity.** `addWord`: O(L). `search`: O(L) when there are no dots. With dots, the worst case is O(26^d x L) for d dots (we may try every letter at each dot), but the trie only branches where words really exist, so in practice it is bounded by the number of letters stored. Space O(total letters stored).

**Edge cases.**
1. The pattern has the wrong length: the letters run out before (or after) a word ends. Returns `False`.
2. A pattern of all dots: matches any word of that length.

**How interviewers twist it.**
- "Add a `*` wildcard (zero or more letters)": that becomes harder and needs DP or more DFS branching.
- "Return all matching words, not just yes/no": collect words during the DFS.
- "Millions of words": discuss memory (a 26-slot array per node can waste space; a dictionary only keeps used letters).

---

# Part B: Greedy

## Words you need first (greedy)

- **Greedy**: at every step, pick the choice that looks **best right now**, and never undo it.
- **Local choice**: the best move at this step.
- **Global answer**: the best answer for the whole problem. Greedy works when local best choices add up to the global best.
- **Counter-example**: one small input where the idea gives a wrong answer. If you can find one, greedy is wrong for that problem.
- **Exchange argument**: a way to prove greedy is right. "If an optimal solution does not make my greedy choice, I can swap in my choice without making things worse."

## 1. What is this? (greedy)

**Analogy: packing the largest boxes into a car first.**
You have boxes of different sizes and a small car boot. Put in the biggest box first, then the next biggest. For packing, that often works. But for **making change** it can fail. With coins 1, 3, 4 and amount 6, taking the biggest coin first (4) gives `4+1+1` (3 coins), while `3+3` (2 coins) is better. So greedy is **not always right**.

Greedy is wonderful when it works: it is usually a simple loop with O(n) or O(n log n) time and tiny memory. The danger is that it looks right but is wrong.

**How to check greedy in an interview:**
1. State the greedy rule in one sentence.
2. Try to break it with a small tricky input (a counter-example).
3. If you cannot break it, give a short reason (exchange argument).
4. If it breaks, use DP (lessons 15 and 16).

## 2. When do I use it? (greedy)

| Words in the problem | Idea |
|---|---|
| "can you **reach** the end" with jump lengths | Greedy: track the farthest reach |
| "**minimum number** of jumps / arrows / platforms" | Greedy with a sorted order |
| "**schedule** tasks / intervals" | Sort by end time or by frequency |
| "start from which station to complete the circle" | Greedy with a running total |
| "**largest number**", "**smallest** sum" built piece by piece | Sort with a good rule |
| "each step you must choose, and the best choice now never hurts later" | Greedy |

Some greedy problems you have already seen: Non-overlapping Intervals (lesson 13, sort by end), Merge Intervals (lesson 13).

## 3. Trace of a tiny example (greedy): Jump Game

`nums = [2, 3, 1, 1, 4]`. Each number is how far you can jump from that position. Can you reach the last index (4)?

**Greedy idea.** Walk left to right and keep `reach` = the farthest index you can get to so far. If you ever stand on an index bigger than `reach`, you are stuck.

```
index:   0  1  2  3  4
nums:    2  3  1  1  4

start: reach = 0
i=0: i <= reach (0 <= 0) ok.  reach = max(0, 0 + 2) = 2
i=1: 1 <= 2 ok.               reach = max(2, 1 + 3) = 4
i=2: 2 <= 4 ok.               reach = max(4, 2 + 1) = 4
i=3: 3 <= 4 ok.               reach = max(4, 3 + 1) = 4
i=4: 4 <= 4 ok.               reach = max(4, 4 + 4) = 8
we passed every index -> True  (reach 4 already covered the last index at i=1)
```

And for `[3, 2, 1, 0, 4]`:

```
i=0: ok. reach = max(0, 0+3) = 3
i=1: ok. reach = max(3, 1+2) = 3
i=2: ok. reach = max(3, 2+1) = 3
i=3: ok. reach = max(3, 3+0) = 3
i=4: 4 <= 3 ? No. We cannot even stand here -> False
```

## 4. Template code (greedy)

Greedy has no fixed template, but this shape appears again and again: **sort (or scan), keep a running "best so far" variable, update it with one rule.**

```python
def can_jump_template(nums):                  # can we reach the last index?
    reach = 0                                 # the farthest index we can reach so far
    for i, step in enumerate(nums):           # walk through positions with their jump sizes
        if i > reach:                         # we cannot get to position i at all
            return False                      # stuck
        reach = max(reach, i + step)          # one rule: update the farthest reach
    return True                               # we could stand on every position, so the end is reachable


print(can_jump_template([2, 3, 1, 1, 4]), can_jump_template([3, 2, 1, 0, 4]))   # expect True False
assert can_jump_template([2, 3, 1, 1, 4]) is True     # same as the trace
assert can_jump_template([3, 2, 1, 0, 4]) is False    # same as the trace
```

---

## 5. Classic problems (greedy)

### 5.3 Jump Game (LeetCode 55)

**In plain words.** `nums[i]` is the maximum jump length from index `i`. Starting at index 0, can you reach the last index?

**Brute force.** Try every jump length from every index with recursion. Exponential. With a memo (DP) it is O(n^2).

**Better idea, slowly.** The greedy walk from section 3. The key thought: we do not care *how* we get to the farthest point, only how **far** we can get. If we can reach index `i`, then we can reach every index before it too (we may jump less). So the set of reachable indexes is always `0..reach`, with no holes.

```python
from typing import List                       # type hints


def can_jump(nums: List[int]) -> bool:        # can we reach the last index?
    reach = 0                                 # farthest index reachable so far
    for i, step in enumerate(nums):           # position and its jump size
        if i > reach:                         # position i is beyond what we can reach
            return False                      # stuck before arriving
        reach = max(reach, i + step)          # update the farthest reach
        if reach >= len(nums) - 1:            # the last index is already reachable
            return True                       # no need to continue
    return True                               # (only for an empty list)


print(can_jump([2, 3, 1, 1, 4]), can_jump([3, 2, 1, 0, 4]))   # expect True False
assert can_jump([2, 3, 1, 1, 4]) is True      # example 1
assert can_jump([3, 2, 1, 0, 4]) is False     # example 2
assert can_jump([0]) is True                  # edge case: already at the end
assert can_jump([0, 1]) is False              # edge case: stuck at the start
assert can_jump([1, 1, 1, 1]) is True         # edge case: tiny steps are enough
assert can_jump([2, 0, 0]) is True            # edge case: a zero we can jump over
```

**Trace**: see section 3.

**Complexity.** Time O(n): one pass. Space O(1): one variable.

**Edge cases.**
1. A single element: you are already at the last index, so `True`.
2. A `0` is not always a trap: you can jump over it if an earlier step reaches far enough (`[2,0,0]`).

**How interviewers twist it.**
- "Jump Game II" (LeetCode 45): the **minimum number of jumps**. Greedy by "levels" (like BFS): jump as far as the current level allows, count a jump when you pass the current level's end.
- "Jump Game with exact jump lengths backwards and forwards" (LeetCode 1306): BFS or DFS.
- "Prove the greedy": the reachable indexes form one block `0..reach`, so tracking one number is enough.

---

### 5.4 Gas Station (LeetCode 134)

**In plain words.** Stations are on a circle. `gas[i]` is the fuel you gain at station `i`. `cost[i]` is the fuel you need to drive from station `i` to station `i+1`. Your tank starts empty. Return the index of the station to start from so you can drive around the whole circle once, or `-1` if impossible. (The answer is unique if it exists.)

**Brute force.** Try each station as the start and simulate the whole trip. O(n^2).

**Better idea, slowly.** Two facts:
1. **If the total gas is less than the total cost, it is impossible.** Return `-1`. (There is simply not enough fuel in the world.)
2. Otherwise a solution exists. Walk once with a running `tank`. If `tank` goes below 0 at station `i`, then **none** of the starts from the previous start up to `i` can work. (Why? If a start `s` could reach `i` with a tank of 0 or more, then the stations between were all in profit. The first station that made us fail is where the loss began, so any start in between fails at `i` too, with even less fuel.) So we try `i + 1` as the new start and reset the tank to 0.
3. At the end, the last candidate start is the answer.

```python
from typing import List                       # type hints


def can_complete_circuit(gas: List[int], cost: List[int]) -> int:   # the start index or -1
    if sum(gas) < sum(cost):                  # not enough fuel in total
        return -1                             # impossible
    start = 0                                 # candidate starting station
    tank = 0                                  # fuel in the tank since the candidate start
    for i in range(len(gas)):                 # visit stations in order
        tank += gas[i] - cost[i]              # fill up here, then drive to the next station
        if tank < 0:                          # we could not reach station i + 1
            start = i + 1                     # so the new candidate start is the next station
            tank = 0                          # begin again with an empty tank
    return start                              # the last candidate is the answer


print(can_complete_circuit([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]))   # expect 3
assert can_complete_circuit([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]) == 3   # example 1
assert can_complete_circuit([2, 3, 4], [3, 4, 3]) == -1     # example 2: total gas 9 < total cost 10
assert can_complete_circuit([5], [4]) == 0    # edge case: one station with enough gas
assert can_complete_circuit([5], [6]) == -1   # edge case: one station without enough gas
assert can_complete_circuit([3, 1, 1], [1, 2, 2]) == 0     # edge case: the first station works
assert can_complete_circuit([2, 0, 0, 5], [1, 1, 1, 1]) == 3   # edge case: must start at the last station
```

**Trace** on `gas = [1,2,3,4,5]`, `cost = [3,4,5,1,2]`. The gain at each station is `gas - cost = [-2, -2, -2, 3, 3]`. Total = 0, which is not below 0, so a solution exists.

```
start=0, tank=0
i=0: tank = 0 + (-2) = -2  < 0 -> start = 1, tank = 0
i=1: tank = 0 + (-2) = -2  < 0 -> start = 2, tank = 0
i=2: tank = 0 + (-2) = -2  < 0 -> start = 3, tank = 0
i=3: tank = 0 + 3 = 3      ok
i=4: tank = 3 + 3 = 6      ok
return start = 3
```

Check by driving from station 3: gain 4, spend 1 -> 3. Station 4: +5 - 2 -> 6. Station 0: +1 - 3 -> 4. Station 1: +2 - 4 -> 2. Station 2: +3 - 5 -> 0. We arrive back with 0, never below 0. It works.

**Complexity.** Time O(n): one pass for the sums, one for the walk. Space O(1).

**Edge cases.**
1. Total gas below total cost: `-1`.
2. One station: `gas[0] >= cost[0]` gives `0`.

**How interviewers twist it.**
- "Several valid starts": the problem usually guarantees uniqueness. If not, you can collect all starts with the prefix sums.
- "Return the minimum tank needed": prefix sums, take the minimum.
- "Circular array" problems like "Maximum Sum Circular Subarray" (LeetCode 918): same family of prefix-sum thinking.

---

### 5.5 Task Scheduler (LeetCode 621)

**In plain words.** You have tasks labelled by letters. Each task takes 1 unit of time. The same letter must be separated by at least `n` units (cool-down). In each unit, the CPU runs one task or sits idle. What is the **minimum total time** to run all tasks? `["A","A","A","B","B","B"]` with `n = 2` gives 8: `A B idle A B idle A B`.

**Brute force.** Try all orders and simulate. Exponential.

**Better idea, slowly (counting).**
1. The most frequent task controls everything. Let `max_freq` be its count (3 for `A` here).
2. Imagine a skeleton with `max_freq` rows: `A _ _ | A _ _ | A`. Each row is `n + 1` slots long (the task plus `n` waiting slots). The last row only needs 1 slot.
3. That skeleton has length `(max_freq - 1) x (n + 1) + 1`.
4. If several tasks tie for the maximum count (`A` and `B` both 3), each of them adds one more slot in the last row. Let `count_max` be how many tasks have `max_freq`. Length = `(max_freq - 1) x (n + 1) + count_max`.
5. The other tasks fit into the empty slots in the skeleton. If there are even more tasks than slots, no idle time is needed at all, and the answer is just the number of tasks.
6. So the answer is `max(len(tasks), (max_freq - 1) x (n + 1) + count_max)`.

```python
from collections import Counter               # counts items
from typing import List                       # type hints


def least_interval(tasks: List[str], n: int) -> int:   # minimum time to finish all tasks
    counts = Counter(tasks)                   # how many times each task appears
    max_freq = max(counts.values())           # the count of the most frequent task
    count_max = sum(1 for c in counts.values() if c == max_freq)   # how many tasks share that top count
    frame = (max_freq - 1) * (n + 1) + count_max   # length of the skeleton described above
    return max(len(tasks), frame)             # if tasks overflow the skeleton, no idle time is needed


print(least_interval(["A", "A", "A", "B", "B", "B"], 2))   # expect 8
assert least_interval(["A", "A", "A", "B", "B", "B"], 2) == 8      # example 1
assert least_interval(["A", "A", "A", "B", "B", "B"], 0) == 6      # example 2: no cool-down
assert least_interval(["A", "A", "A", "A", "A", "A", "B", "C", "D", "E", "F", "G"], 2) == 16   # example 3
assert least_interval(["A"], 5) == 1          # edge case: one task, no waiting needed
assert least_interval(["A", "B", "C", "D"], 3) == 4      # edge case: all different, no idle time
assert least_interval(["A", "A"], 3) == 5     # edge case: A, three idle slots, A
```

**Trace** on `["A","A","A","B","B","B"]`, `n = 2`:

```
counts = {A: 3, B: 3}
max_freq = 3
count_max = 2          (both A and B have 3)
frame = (3 - 1) * (2 + 1) + 2 = 2 * 3 + 2 = 8
len(tasks) = 6
answer = max(6, 8) = 8

The skeleton:  A B idle | A B idle | A B      -> 8 slots
```

For `["A","A","A","A","A","A","B","C","D","E","F","G"]`, `n = 2`: `max_freq = 6`, `count_max = 1`, `frame = 5 x 3 + 1 = 16`, `len = 12`, so the answer is 16. The six `A`s need 5 gaps of 3 slots, and the other 6 tasks fill 5 x 2 = 10 spare slots, with 4 idle.

**Complexity.** Time O(n_tasks): counting. Space O(1) (at most 26 letters).

**Edge cases.**
1. `n = 0`: no cool-down, so the answer is the number of tasks.
2. Many different tasks: the frame is shorter than the task count, so the task count wins.

**How interviewers twist it.**
- "Return the actual schedule": use a max-heap of counts (lesson 09): each round, take up to `n + 1` different tasks from the heap.
- "Reorganize String" (LeetCode 767): a heap version of the same idea with `n = 1`.
- "Different durations per task": greedy by frequency may fail, so ask for constraints before coding.

---

## 6. Common mistakes

**Tries**
1. **Forgetting `is_end`.** Then `search("app")` returns `True` just because `"apple"` was stored.
2. **Using a list as the `children` default value shared by all nodes.** Create a new dictionary inside `__init__` for each node.
3. **Not handling `.` with a loop over children** in wildcard search.
4. **Recursion depth** for very long words. Python's limit is about 1000. Words are rarely that long, but mention it.

**Greedy**
5. **Believing greedy works without testing a counter-example.** Coin Change with `[1,3,4]` is the classic trap.
6. **Sorting by the wrong key.** Intervals: sort by end. Jobs by deadline. Think about which choice leaves the most room.
7. **Not resetting the running value** (the tank in Gas Station) after a failure.
8. **Forgetting the global check** (Gas Station: total gas versus total cost).

---

## 7. Practice list (8 more problems)

Tags come from public LeetCode company-tag lists I read (GitHub mirror, snapshot Oct 2025; see lesson 19). A tag means "the problem is in that company's list". No tag means not verified. The problems taught above are tagged too: Implement Trie, Jump Game and Task Scheduler are each in the lists of Amazon, Google, Meta and Microsoft. Gas Station is in the lists of Amazon and Google.

| # | Problem | Difficulty | Tagged for |
|---|---|---|---|
| 1 | Longest Common Prefix (14) | Easy | Amazon, Google, Microsoft |
| 2 | Replace Words (648) | Medium | not verified |
| 3 | Jump Game II (45) | Medium | not verified |
| 4 | Partition Labels (763) | Medium | not verified |
| 5 | Hand of Straights (846) | Medium | not verified |
| 6 | Maximum XOR of Two Numbers in an Array (421, trie) | Medium | not verified |
| 7 | Word Search II (212, trie + backtracking) | Hard | Amazon, Google, Meta, Microsoft |
| 8 | Candy (135) | Hard | not verified |

---

## 8. Self-quiz (5 questions)

1. What question can a trie answer quickly that a hash set cannot?
2. In a trie, what is the `is_end` flag for, and what goes wrong if you forget it?
3. In "Add and Search Words", what do we do when the next letter of the pattern is `.`?
4. Give one example where the greedy "take the biggest first" is wrong.
5. In Jump Game, why is it enough to track one number, `reach`?

**Answers.**
1. "Does any stored word start with this prefix?" A trie answers it in O(length of the prefix).
2. `is_end` says that a stored word finishes at that node. Without it, `search("app")` would return `True` when only `"apple"` is stored, because the path exists.
3. We try every child of the current node (a loop), and use DFS (recursion) to check whether the rest of the pattern matches below that child.
4. Coin Change with coins `[1, 3, 4]` and amount `6`. Greedy gives `4+1+1` (3 coins). The best is `3+3` (2 coins).
5. If you can reach index `i`, you can reach every index before `i` (by jumping less). So the reachable indexes always form one block `0..reach`. One number describes it.
