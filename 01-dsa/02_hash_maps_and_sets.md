# Lesson 02. Hash Maps and Sets

Before this lesson: [00_how_to_start.md](00_how_to_start.md) and [01_arrays_and_strings.md](01_arrays_and_strings.md).

---

## 1. What is this?

A **hash map** stores pairs: a **key** and a **value**. In Python it is a `dict`. You give a key, you get the value back almost instantly.

A **set** stores only keys (no values) and no repeats. You ask it one thing: "Is this item inside?"

**Analogy 1: the coat check.** At a big party you give your coat and get a ticket number. Later you show the ticket and they hand you the coat at once. They do not search every coat. The ticket is the key. The coat is the value.

**Analogy 2: a guest list.** A guard at the door has a list of names (a set). For each person he asks: "Is your name on the list?" He answers fast, even if the list has a million names.

**How is it fast?** Python runs a small formula (a **hash function**) on your key. The formula gives a locker number. Python goes straight to that locker. This is why lookup, insert and delete cost **O(1) on average**.

Rules to remember:

- Keys must be **hashable**: numbers, strings and tuples are fine. Lists are NOT (they can change).
- A set has no order you can rely on, and no repeats.
- Worst case is slower than O(1), but it is very rare. In interviews we say "O(1) average".

```text
dict  = {"apple": 3, "pear": 5}     key -> value
set   = {"apple", "pear"}           only keys
```

Compare the cost of the question "have I seen 7 before?":

| Tool | Cost of the question |
|---|---|
| list: `7 in nums` | O(n) (looks at every item) |
| set: `7 in seen` | O(1) average |

## 2. When do I use it?

Words that give it away:

- "Have I seen this before?" / "duplicate" / "unique" / "distinct"
- "Count how many times..." / "frequency" / "most common"
- "Find two numbers that add to..." (look for the partner)
- "Group the items that..." (anagrams)
- "First non-repeating..."
- "Longest sequence..." where you can look up neighbours quickly
- A brute force that does a **second loop only to search for something**. Replace that inner loop with a lookup.

Memory trick: **"A hash map trades memory for speed."** You spend O(n) extra space and save a whole loop of time.

## 3. A tiny example, traced line by line

Count the letters of `"banana"` with a dictionary.

```text
counts = {}                       (empty dictionary)

letter 'b': counts.get('b', 0) is 0 -> counts['b'] = 1     counts = {b:1}
letter 'a': counts.get('a', 0) is 0 -> counts['a'] = 1     counts = {b:1, a:1}
letter 'n': counts.get('n', 0) is 0 -> counts['n'] = 1     counts = {b:1, a:1, n:1}
letter 'a': counts.get('a', 0) is 1 -> counts['a'] = 2     counts = {b:1, a:2, n:1}
letter 'n': counts.get('n', 0) is 1 -> counts['n'] = 2     counts = {b:1, a:2, n:2}
letter 'a': counts.get('a', 0) is 2 -> counts['a'] = 3     counts = {b:1, a:3, n:2}
```

`counts.get(key, 0)` means: "give me the value for key, or 0 if the key is not there".

## 4. Template code (a comment on every line)

```python
# TEMPLATE A: counting how many times each item appears
def count_items(items):                       # function: returns a dict item -> how many times
    counts = {}                               # empty dictionary to hold the counts
    for item in items:                        # look at each item once
        counts[item] = counts.get(item, 0) + 1    # old count (or 0 if new) plus one
    return counts                             # the finished counts

print(count_items("banana"))                  # expect {'b': 1, 'a': 3, 'n': 2}
assert count_items("banana") == {"b": 1, "a": 3, "n": 2}   # check by machine
assert count_items([]) == {}                  # empty input gives empty dict
```

```python
# TEMPLATE B: "have I seen it?" with a set (find the first repeated item)
def first_repeat(items):                      # function: returns the first item seen twice, or None
    seen = set()                              # empty set: the guest list so far
    for item in items:                        # walk through the items in order
        if item in seen:                      # is the item already on the list? O(1)
            return item                       # yes: this is the first repeat
        seen.add(item)                        # no: add it to the list
    return None                               # no repeat found

print(first_repeat([4, 2, 7, 2, 4]))          # expect 2
assert first_repeat([4, 2, 7, 2, 4]) == 2     # 2 repeats before 4 does
assert first_repeat([1, 2, 3]) is None        # no repeats
```

```python
# TEMPLATE C: grouping items by a key
from collections import defaultdict           # defaultdict creates a missing value automatically

def group_by_length(words):                   # function: groups words that have the same length
    groups = defaultdict(list)                # a missing key starts as an empty list
    for word in words:                        # look at each word
        groups[len(word)].append(word)        # put the word in the group of its length
    return dict(groups)                       # turn it into a normal dict

print(group_by_length(["hi", "yo", "cat", "dog", "a"]))   # expect {2: ['hi', 'yo'], 3: ['cat', 'dog'], 1: ['a']}
assert group_by_length(["hi", "yo", "cat", "dog", "a"]) == {2: ["hi", "yo"], 3: ["cat", "dog"], 1: ["a"]}   # check
```

---

## 5. Classic problems

### Problem 1. Two Sum

**Problem in plain words.** You get a list of numbers and a target. Find the positions (indices) of the two numbers that add up to the target. There is exactly one answer. You cannot use the same position twice.

Example: `nums = [2, 7, 11, 15]`, `target = 9` gives `[0, 1]` because 2 + 7 = 9.

**Brute force.** Two loops: try every pair. O(n^2) time, O(1) space.

**Better idea, slowly.** For each number `x`, its partner must be `target - x`. Do not search the list for the partner. Instead, keep a dictionary `seen` of numbers you already passed: number -> its index. For each new `x`:

1. Compute `need = target - x`.
2. If `need` is in `seen`, you found the pair. Return the two indices.
3. Otherwise store `x` in `seen` and continue.

Why does one pass work? If a pair (a, b) exists, then when you reach the later one of the two, the earlier one is already in `seen`.

```python
def two_sum(nums, target):
    seen = {}                                  # number -> index where we saw it
    for i, x in enumerate(nums):               # i is the position, x is the number
        need = target - x                      # the partner we are looking for
        if need in seen:                       # did we already pass the partner?
            return [seen[need], i]             # yes: return both positions
        seen[x] = i                            # no: remember this number and position
    return []                                  # no pair found (the problem promises one)

print(two_sum([2, 7, 11, 15], 9))              # expect [0, 1]
assert two_sum([2, 7, 11, 15], 9) == [0, 1]    # the example
assert two_sum([3, 3], 6) == [0, 1]            # two equal numbers
assert two_sum([3, 2, 4], 6) == [1, 2]         # must not use index 0 twice (3 + 3)
assert two_sum([-1, -2, -3, -4], -6) == [1, 3] # negative numbers work
```

**Trace** on `[2, 7, 11, 15]`, target 9:

```text
i=0, x=2 : need = 9-2 = 7. Is 7 in seen {}? no.   seen = {2:0}
i=1, x=7 : need = 9-7 = 2. Is 2 in seen {2:0}? yes -> return [0, 1]
```

**Complexity.** Time O(n): one pass, each lookup is O(1). Space O(n): the dictionary may hold all numbers.

**Two edge cases.** (1) Two equal numbers like `[3, 3]` with target 6: we check `seen` BEFORE adding `x`, so it works. (2) A number that is exactly half the target, like `[3, 2, 4]` with target 6: we must not pair 3 with itself. The "check first, add after" order prevents this.

**How interviewers twist it.** "The list is sorted, use O(1) space" (two pointers, lesson 03). "Return all pairs." "Count the pairs." "3Sum." "Design a data structure that supports add and find." "Input is a binary search tree."

---

### Problem 2. Group Anagrams

**Problem in plain words.** An **anagram** is a word made from the same letters in another order ("eat" and "tea"). Given a list of words, group the words that are anagrams of each other.

Example: `["eat","tea","tan","ate","nat","bat"]` gives `[["eat","tea","ate"],["tan","nat"],["bat"]]` (the order of groups does not matter).

**Brute force.** For each word, compare it with every other word (sort both and compare). O(n^2 * k log k), where k is word length. Too slow for many words.

**Better idea, slowly.** All anagrams become the SAME word if you sort their letters: "eat", "tea", "ate" all become "aet". So the sorted word is a perfect **key** for the group. Use a dictionary: key = sorted letters, value = list of words.

```python
from collections import defaultdict            # lets us skip the "is the key there?" check

def group_anagrams(words):
    groups = defaultdict(list)                 # key (sorted letters) -> list of words
    for word in words:                         # look at each word once
        key = "".join(sorted(word))            # sort the letters; join into a string key
        groups[key].append(word)               # put the word into its group
    return list(groups.values())               # return just the groups

result = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])    # run the example
print(result)                                  # expect three groups
assert sorted(sorted(g) for g in result) == [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]   # order-free check
assert group_anagrams([""]) == [[""]]          # empty word
assert group_anagrams(["a"]) == [["a"]]        # one word
```

**Trace** on `["eat","tea","tan","ate","nat","bat"]`:

```text
"eat" -> key "aet" -> groups = {aet:[eat]}
"tea" -> key "aet" -> groups = {aet:[eat, tea]}
"tan" -> key "ant" -> groups = {aet:[eat, tea], ant:[tan]}
"ate" -> key "aet" -> groups = {aet:[eat, tea, ate], ant:[tan]}
"nat" -> key "ant" -> groups = {aet:[eat, tea, ate], ant:[tan, nat]}
"bat" -> key "abt" -> groups = {aet:[...], ant:[...], abt:[bat]}
```

**Complexity.** Time O(n * k log k): for n words of length k, sorting each word costs k log k. Space O(n * k): we store all the words.

A faster key for lowercase words: a tuple of 26 letter counts. That makes the time O(n * k).

**Two edge cases.** (1) The empty string `""`: its sorted key is `""`, and it forms its own group. (2) Words with different lengths are never anagrams, and their keys differ, so they stay separate.

**How interviewers twist it.** "Use the count-tuple key to avoid sorting." "Group shifted strings (abc, bcd)." "Find all anagrams of p inside s" (sliding window, lesson 04). "Words are in a huge file."

---

### Problem 3. Top K Frequent Elements

**Problem in plain words.** Given a list of numbers and a number `k`, return the `k` numbers that appear most often.

Example: `nums = [1,1,1,2,2,3]`, `k = 2` gives `[1, 2]`.

**Brute force.** Count each number, then sort the counts from big to small and take the first k. Cost: O(n log n). This is fine, but the interviewer often asks for better than O(n log n).

**Better idea, slowly (bucket sort).** The count of any number is between 1 and n (the list length). So make n + 1 buckets. Bucket number `c` holds all numbers that appear exactly `c` times. Then walk from the biggest bucket to the smallest and collect numbers until you have `k`.

Think of it as putting students in rows by "how many books they read". Then you read the names from the top row downward.

```python
def top_k_frequent(nums, k):
    counts = {}                                    # number -> how many times it appears
    for x in nums:                                 # count every number
        counts[x] = counts.get(x, 0) + 1           # add one to its count
    buckets = [[] for _ in range(len(nums) + 1)]   # buckets[c] = numbers that appear c times
    for x, c in counts.items():                    # for each number and its count
        buckets[c].append(x)                       # put the number into bucket c
    answer = []                                    # the result list
    for c in range(len(buckets) - 1, 0, -1):       # go from the highest count down to 1
        for x in buckets[c]:                       # every number in this bucket
            answer.append(x)                       # take it
            if len(answer) == k:                   # do we have k numbers yet?
                return answer                      # yes: stop and return
    return answer                                  # (only reached if k is too big)

print(top_k_frequent([1, 1, 1, 2, 2, 3], 2))       # expect [1, 2]
assert top_k_frequent([1, 1, 1, 2, 2, 3], 2) == [1, 2]    # the example
assert top_k_frequent([5, 5, 5], 1) == [5]                # one distinct number
assert sorted(top_k_frequent([4, 4, 6, 6, 9], 2)) == [4, 6]   # a tie for the top
```

**Trace** on `[1,1,1,2,2,3]`, `k = 2`:

```text
counts  = {1:3, 2:2, 3:1}
buckets (index 0..6) = [ [], [3], [2], [1], [], [], [] ]
go down from index 6:
c=6,5,4 -> empty
c=3 -> bucket [1]  -> answer = [1]       (1 number, need 2)
c=2 -> bucket [2]  -> answer = [1, 2]    (2 numbers = k) -> return [1, 2]
```

**Complexity.** Time O(n): counting is O(n), filling buckets is O(n), walking the buckets is O(n). Space O(n): the dict and the buckets.

(Alternative: a heap with `heapq.nlargest(k, counts, key=counts.get)` costs O(n log k).)

**Two edge cases.** (1) All numbers equal, such as `[5,5,5]`, k=1: one bucket is full. (2) `k` equals the number of distinct values: you return every distinct value. Ties at the cut-off: the real problem promises a unique answer.

**How interviewers twist it.** "Top K frequent WORDS, ties broken alphabetically." "K closest points to origin." "Kth largest element." "The numbers come as a stream" (use a heap).

---

### Problem 4. Longest Consecutive Sequence

**Problem in plain words.** Given an unsorted list of numbers, find the length of the longest run of numbers that follow each other by 1 (like 1, 2, 3, 4). The numbers do not need to be next to each other in the list. Aim for O(n) time.

Example: `[100, 4, 200, 1, 3, 2]` gives `4` (the run 1, 2, 3, 4).

**Brute force.** Sort the list, then walk and count runs. O(n log n). Works, but is not O(n).

**Better idea, slowly.** Put all numbers in a **set**, so "is x in the list?" costs O(1). Now think about a run like 1, 2, 3, 4. Only ONE number in it is the start: the one whose "number minus 1" is NOT in the set. So:

1. For each number `x`: if `x - 1` is in the set, skip it (it is in the middle of a run).
2. Otherwise `x` is a start. Count upward: x+1, x+2, ... while they are in the set.
3. Keep the longest count.

Each number is counted at most once as part of a run, because we only start at run beginnings. So the total work is O(n).

```python
def longest_consecutive(nums):
    num_set = set(nums)                       # all numbers in a set; also removes duplicates
    best = 0                                  # longest run found so far
    for x in num_set:                         # look at each distinct number
        if x - 1 in num_set:                  # is there a number just before x?
            continue                          # yes: x is not a start, skip it
        length = 1                            # x is a start; the run has length 1 so far
        while x + length in num_set:          # does the next number exist?
            length += 1                       # yes: the run gets longer
        best = max(best, length)              # keep the longest run
    return best                               # answer

print(longest_consecutive([100, 4, 200, 1, 3, 2]))     # expect 4
assert longest_consecutive([100, 4, 200, 1, 3, 2]) == 4    # the example
assert longest_consecutive([]) == 0                        # empty list
assert longest_consecutive([1, 2, 2, 3]) == 3              # duplicates do not count twice
assert longest_consecutive([-1, 0, 1]) == 3                # negative numbers
```

**Trace** on `[100, 4, 200, 1, 3, 2]` (set = {100, 4, 200, 1, 3, 2}):

```text
x=100: is 99 in set? no  -> start. 101 in set? no.        length=1  best=1
x=4  : is 3 in set?  yes -> skip.
x=200: is 199 in set? no -> start. 201 in set? no.        length=1  best=1
x=1  : is 0 in set?  no  -> start. 2 yes, 3 yes, 4 yes, 5 no. length=4  best=4
x=3  : is 2 in set?  yes -> skip.
x=2  : is 1 in set?  yes -> skip.
answer = 4
```

(The set may be visited in a different order. The result is the same.)

**Complexity.** Time O(n): the `while` loop runs only for run starts, and each number is passed once overall. Space O(n): the set.

**Two edge cases.** (1) Empty list: the answer is 0. (2) Duplicates like `[1,2,2,3]`: the set removes them, so the run is 3.

**How interviewers twist it.** "Return the sequence, not only its length." "Solve with union-find." "Allow one gap." "The numbers are in a stream."

---

### Problem 5. Subarray Sum Equals K

**Problem in plain words.** Given a list of integers (can be negative) and a number `k`, count how many contiguous subarrays have a sum equal to `k`.

Example: `nums = [1, 2, 3]`, `k = 3` gives `2` (the pieces `[1, 2]` and `[3]`).

**Brute force.** Try every start and end, keep a running sum. O(n^2) time.

**Why not a sliding window?** Sliding window needs all numbers positive. With negative numbers, the sum can go down and up again. So a different idea is needed.

**Better idea, slowly (prefix sums + hash map).** Let `s` be the running total after the current number (the prefix sum). A subarray that ENDS here and starts later has sum `s - (an earlier prefix)`. We want that to be `k`. So we need an earlier prefix equal to `s - k`.

So we keep a dictionary: prefix sum -> how many times it happened. At each position, add `counts[s - k]` to the answer. Start with `{0: 1}`, which means "an empty prefix with sum 0 exists once". This handles pieces that start at index 0.

```python
def subarray_sum(nums, k):
    counts = {0: 1}                          # prefix sum -> times seen; empty prefix has sum 0
    s = 0                                    # running total (prefix sum)
    total = 0                                # how many subarrays we found
    for x in nums:                           # go through the numbers
        s += x                               # update the running total
        total += counts.get(s - k, 0)        # earlier prefixes equal to s-k make a subarray with sum k
        counts[s] = counts.get(s, 0) + 1     # record this prefix sum for the future
    return total                             # answer

print(subarray_sum([1, 2, 3], 3))            # expect 2
assert subarray_sum([1, 2, 3], 3) == 2       # the example
assert subarray_sum([1, -1, 0], 0) == 3      # negatives and zeros: [1,-1], [1,-1,0], [0]
assert subarray_sum([0, 0, 0], 0) == 6       # all zeros: every piece counts
assert subarray_sum([], 5) == 0              # empty list
```

**Trace** on `[1, 2, 3]`, `k = 3`:

```text
start: counts = {0:1}, s = 0, total = 0
x=1: s=1. need s-k = -2 -> count 0.         total=0.  counts = {0:1, 1:1}
x=2: s=3. need s-k =  0 -> count 1.         total=1.  counts = {0:1, 1:1, 3:1}
x=3: s=6. need s-k =  3 -> count 1.         total=2.  counts = {0:1, 1:1, 3:1, 6:1}
answer = 2
```

Check: the `1` at step 2 means prefix 0 to prefix 3 is the piece `[1, 2]`. The `1` at step 3 means prefix 3 to prefix 6 is the piece `[3]`.

**Complexity.** Time O(n): one pass with O(1) dictionary work. Space O(n): the dictionary.

**Two edge cases.** (1) Many zeros with `k = 0`: every piece counts, so counts grow fast (3 zeros give 6). (2) Negative numbers: that is the reason we use prefix sums and not a window. Empty list gives 0.

**How interviewers twist it.** "Longest subarray with sum k" (store the FIRST index of each prefix). "Subarray sum divisible by k" (store prefix sum modulo k). "Binary array with equal 0s and 1s" (change 0 to -1, then find sum 0). "Count in a 2D grid."

---

## 6. Common mistakes

1. **Adding to `seen` before checking it** (Two Sum). You may pair a number with itself.
2. **Using a list as a key.** Lists are not hashable. Use a tuple or a string.
3. **Forgetting `counts.get(x, 0)`.** `counts[x] += 1` crashes with `KeyError` for a new key (or use `defaultdict` or `Counter`).
4. **Changing a dict while looping over it.** Python raises an error. Loop over a copy of the keys.
5. **Forgetting `{0: 1}` in prefix-sum problems.** You miss subarrays that start at index 0.
6. **Assuming order.** Sets have no reliable order. If the answer order matters, sort or track it.
7. **Wrong complexity claim.** A dictionary lookup is O(1) on average, but a long string key costs O(length) to hash.
8. **Using `x in list`** when a set would do.

## 7. Practice list (8 more problems)

"Asked at" means the problem appears on that company's list in the community repo [liquidslr/leetcode-company-wise-problems](https://github.com/liquidslr/leetcode-company-wise-problems) (checked 2026-11-15). Difficulty is the LeetCode label from the same data.

| # | Problem | Difficulty | Asked at (per those lists) |
|---|---|---|---|
| 1 | Contains Duplicate | Easy | Amazon, Google, Meta, Microsoft |
| 2 | Valid Anagram | Easy | Amazon, Google, Meta, Microsoft |
| 3 | Ransom Note | Easy | Amazon, Google, Meta, Microsoft |
| 4 | Isomorphic Strings | Easy | Amazon, Google, Meta, Microsoft |
| 5 | Word Pattern | Easy | Amazon, Google, Meta, Microsoft |
| 6 | Happy Number | Easy | Amazon, Google, Meta, Microsoft |
| 7 | Insert Delete GetRandom O(1) | Medium | Amazon, Google, Meta, Microsoft |
| 8 | 4Sum II | Medium | Amazon, Google, Meta, Microsoft |

## 8. Self-quiz (5 questions)

1. What is the average cost of `x in my_set`? What is the cost of `x in my_list`?
2. Why can a list not be a dictionary key? What can you use instead?
3. In Two Sum, why do we check `seen` before we add the current number?
4. In Longest Consecutive Sequence, why do we skip a number `x` when `x - 1` is in the set?
5. In Subarray Sum Equals K, why do we start with `{0: 1}`?

### Answers

1. Set: O(1) on average. List: O(n).
2. A list can change, so its hash would change. Use a tuple (or a string).
3. So that a number is not paired with itself (same index used twice).
4. Because `x` is in the middle of a run, not at its start. Counting from every number would repeat work and become O(n^2).
5. It stands for the empty prefix (sum 0). Without it, we miss subarrays that start at the very first element.

Next: [03_two_pointers.md](03_two_pointers.md)
