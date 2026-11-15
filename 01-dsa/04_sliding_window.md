# Lesson 04. Sliding Window

Before this lesson: [00_how_to_start.md](00_how_to_start.md). Lessons 01 to 03 help (arrays, hash maps, two pointers).

---

## 1. What is this?

A **window** is a continuous piece of a list or string (a subarray or substring). A **sliding window** is a window that moves along the data: its right edge moves forward, and its left edge follows behind. Instead of building every window from scratch, you UPDATE the window: add the new item on the right, remove the old item on the left.

**Analogy 1: a train window.** You sit in a train. The window shows a small piece of the countryside. As the train moves, new trees appear on one side and old trees leave on the other side. You never rebuild the whole view.

**Analogy 2: a caterpillar.** The head moves forward (right pointer). When the caterpillar is too long or the rules are broken, the tail pulls in (left pointer).

There are two kinds:

1. **Fixed size window.** The size `k` is given. You slide it one step at a time.
2. **Variable size window.** The size changes. You **expand** the right edge. When the window breaks a rule, you **shrink** the left edge until the window is valid again.

Why is it fast? Brute force looks at all windows and re-adds everything: O(n^2) or worse. A sliding window touches each item at most twice (once when it enters, once when it leaves): O(n).

## 2. When do I use it?

Words that give it away:

- "**contiguous** subarray" or "**substring**" (items next to each other)
- "**longest** ... such that ..." or "**shortest** ... such that ..."
- "at most k distinct", "no repeating", "sum at least target"
- "window of size k", "every k consecutive items"
- "maximum / minimum / average of every k items"

Warning: the classic window needs a rule that you can fix by shrinking. With positive numbers, a bigger window means a bigger sum, so shrinking helps. With negative numbers, it often does not (use prefix sums and a hash map instead, lesson 02).

## 3. A tiny example, traced line by line

Maximum sum of 3 consecutive numbers in `[2, 1, 5, 1, 3, 2]` (k = 3).

```text
nums = [2, 1, 5, 1, 3, 2]     k = 3

Build the first window: 2 + 1 + 5 = 8.          window_sum = 8, best = 8
Slide by one: remove 2 (leaving), add 1 (new):  8 - 2 + 1 = 7.   window [1,5,1]. best = 8
Slide by one: remove 1, add 3:                  7 - 1 + 3 = 9.   window [5,1,3]. best = 9
Slide by one: remove 5, add 2:                  9 - 5 + 2 = 6.   window [1,3,2]. best = 9

answer = 9
```

We never re-add three numbers. Each slide costs two operations. Total cost: O(n).

## 4. Template code (a comment on every line)

```python
# TEMPLATE A: fixed size window (maximum sum of k consecutive numbers)
def max_sum_k(nums, k):                      # function: biggest sum of any k consecutive numbers
    window_sum = sum(nums[:k])               # sum of the first window (the first k numbers)
    best = window_sum                        # the first window is the best so far
    for right in range(k, len(nums)):        # `right` is the new number entering the window
        window_sum += nums[right]            # add the number that enters on the right
        window_sum -= nums[right - k]        # remove the number that leaves on the left
        best = max(best, window_sum)         # keep the biggest sum
    return best                              # the answer

print(max_sum_k([2, 1, 5, 1, 3, 2], 3))      # expect 9
assert max_sum_k([2, 1, 5, 1, 3, 2], 3) == 9     # the trace above
assert max_sum_k([4], 1) == 4                    # window of one number
```

```python
# TEMPLATE B: variable size window (longest piece with sum <= limit; numbers are positive)
def longest_with_sum_at_most(nums, limit):   # function: length of the longest valid piece
    left = 0                                 # left edge of the window
    window_sum = 0                           # sum of the numbers inside the window
    best = 0                                 # longest valid window length so far
    for right in range(len(nums)):           # expand: the right edge moves one step each time
        window_sum += nums[right]            # the new number joins the window
        while window_sum > limit:            # the window breaks the rule (sum too big)
            window_sum -= nums[left]         # remove the leftmost number
            left += 1                        # shrink: move the left edge right
        best = max(best, right - left + 1)   # the window is valid now; record its length
    return best                              # the answer

print(longest_with_sum_at_most([3, 1, 2, 7, 4], 6))   # expect 3  (the piece 3,1,2)
assert longest_with_sum_at_most([3, 1, 2, 7, 4], 6) == 3     # check
assert longest_with_sum_at_most([9, 9], 5) == 0              # no valid piece
```

```python
# TEMPLATE C: variable window with a dictionary of counts (longest piece with at most k different letters)
def longest_k_distinct(s, k):                # function: longest substring with at most k different letters
    counts = {}                              # letter -> how many times it is inside the window
    left = 0                                 # left edge of the window
    best = 0                                 # best length so far
    for right, ch in enumerate(s):           # expand: add letter s[right]
        counts[ch] = counts.get(ch, 0) + 1   # count the new letter
        while len(counts) > k:               # too many different letters?
            counts[s[left]] -= 1             # remove the leftmost letter from the counts
            if counts[s[left]] == 0:         # did that letter disappear from the window?
                del counts[s[left]]          # yes: delete it so len(counts) is correct
            left += 1                        # shrink the window from the left
        best = max(best, right - left + 1)   # record the window length
    return best                              # the answer

print(longest_k_distinct("eceba", 2))        # expect 3  ("ece")
assert longest_k_distinct("eceba", 2) == 3   # check
assert longest_k_distinct("aa", 1) == 2      # one letter only
```

---

## 5. Classic problems

### Problem 1. Longest Substring Without Repeating Characters

**Problem in plain words.** Given a string, find the length of the longest substring (continuous piece) in which no letter appears twice.

Example: `"abcabcbb"` gives `3` (the piece `"abc"`).

**Brute force.** Check every substring and test if letters repeat (with a set). O(n^2) substrings, and each check costs up to O(n), so O(n^2) to O(n^3).

**Better idea, slowly.** Keep a window `[left .. right]` that has no repeats. Move `right` one step at a time. If the new letter is already INSIDE the window, move `left` to just after the old copy of that letter. For this, keep a dictionary `last` that stores the last position of each letter.

Careful: the old copy only matters if its position is **inside the window** (position >= left). A letter seen long ago, before the window started, does not count.

```python
def length_of_longest_substring(s):
    last = {}                                      # letter -> last position where we saw it
    left = 0                                       # left edge of the window
    best = 0                                       # best length so far
    for right, ch in enumerate(s):                 # right edge moves over each letter
        if ch in last and last[ch] >= left:        # is ch already inside the window?
            left = last[ch] + 1                    # yes: jump left to just after the old copy
        last[ch] = right                           # remember the newest position of ch
        best = max(best, right - left + 1)         # length of the current window
    return best                                    # the answer

print(length_of_longest_substring("abcabcbb"))     # expect 3
assert length_of_longest_substring("abcabcbb") == 3    # example
assert length_of_longest_substring("bbbbb") == 1       # all the same letter
assert length_of_longest_substring("") == 0            # empty string
assert length_of_longest_substring("abba") == 2        # the "last >= left" check matters here
```

**Trace** on `"abcabcbb"`:

```text
right ch  last (after)          left  window      length  best
  0   a   {a:0}                  0    "a"           1      1
  1   b   {a:0,b:1}              0    "ab"          2      2
  2   c   {a:0,b:1,c:2}          0    "abc"         3      3
  3   a   a seen at 0 >= left 0 -> left = 1.  last a=3     "bca"   3   3
  4   b   b seen at 1 >= 1 -> left = 2.  last b=4          "cab"   3   3
  5   c   c seen at 2 >= 2 -> left = 3.  last c=5          "abc"   3   3
  6   b   b seen at 4 >= 3 -> left = 5.  last b=6          "cb"    2   3
  7   b   b seen at 6 >= 5 -> left = 7.  last b=7          "b"     1   3
answer = 3
```

**Complexity.** Time O(n): the right edge moves once over the string; the left edge only jumps forward. Space O(min(n, alphabet size)) for the dictionary.

**Two edge cases.** (1) Empty string: 0. (2) `"abba"`: when the second `a` arrives, its old position (0) is BEFORE `left` (2), so we must not move `left` back. The check `last[ch] >= left` protects us. Answer 2.

**How interviewers twist it.** "At most k distinct letters." "At most two repeats." "Return the substring itself." "Longest substring with all unique digits in a stream."

---

### Problem 2. Longest Repeating Character Replacement

**Problem in plain words.** You get a string of capital letters and a number `k`. You may change at most `k` letters to any other letter. After that, what is the longest piece made of one single repeated letter?

Example: `s = "AABABBA"`, `k = 1` gives `4` (take the piece `"AABA"` and change its one `B` to `A`, which gives `"AAAA"`).

**Brute force.** For every substring, count the most common letter and check if `length - most_common <= k`. O(n^2) windows, plus counting. Too slow.

**Better idea, slowly.** A window is valid if the letters we must change are at most `k`. The letters to change = `window length - count of the most common letter in the window` (keep the most common, change the rest). So the rule is:

`window length - max count <= k`

Expand `right`. If the rule breaks, shrink `left` (remove the left letter from the counts) until the rule holds again. The counts dictionary has at most 26 keys, so `max(counts.values())` costs at most 26 steps.

```python
def character_replacement(s, k):
    counts = {}                                           # letter -> count inside the window
    left = 0                                              # left edge of the window
    best = 0                                              # best valid window length
    for right, ch in enumerate(s):                        # expand: add the new letter
        counts[ch] = counts.get(ch, 0) + 1                # count it
        while (right - left + 1) - max(counts.values()) > k:   # more than k letters to change?
            counts[s[left]] -= 1                          # remove the leftmost letter from counts
            left += 1                                     # shrink the window
        best = max(best, right - left + 1)                # the window is valid; record the length
    return best                                           # the answer

print(character_replacement("AABABBA", 1))                # expect 4
assert character_replacement("AABABBA", 1) == 4           # example
assert character_replacement("ABAB", 2) == 4              # change two letters: all the same
assert character_replacement("AAAA", 0) == 4              # already one letter, k = 0
assert character_replacement("A", 0) == 1                 # one letter
```

**Trace** on `"AABABBA"`, `k = 1`:

```text
right ch  counts after add     window len  max count  len-max  action                      best
  0   A   {A:1}                    1          1          0     ok                            1
  1   A   {A:2}                    2          2          0     ok                            2
  2   B   {A:2,B:1}                3          2          1     ok (1 <= 1)                   3
  3   A   {A:3,B:1}                4          3          1     ok                            4
  4   B   {A:3,B:2}                5          3          2     too many: remove s[0]=A -> {A:2,B:2}, left=1
                                   4          2          2     still too many: remove s[1]=A -> {A:1,B:2}, left=2
                                   3          2          1     ok                            4
  5   B   {A:1,B:3}                4          3          1     ok                            4
  6   A   {A:2,B:3}                5          3          2     too many: remove s[2]=B -> {A:2,B:2}, left=3
                                   4          2          2     still too many: remove s[3]=A -> {A:1,B:2}, left=4
                                   3          2          1     ok                            4
answer = 4
```

**Complexity.** Time O(26 * n), which is O(n): each step may compute `max` over at most 26 counts. Space O(26) = O(1).

**Two edge cases.** (1) `k = 0`: the answer is the longest run of one letter. (2) `k` is large (at least n - 1): the answer is the whole string length.

**How interviewers twist it.** "Max Consecutive Ones III" (binary array, flip at most k zeros). "Longest subarray of 1s after deleting one element." "Fruit into baskets" (at most 2 types).

---

### Problem 3. Minimum Size Subarray Sum

**Problem in plain words.** Given a list of POSITIVE integers and a target, find the length of the shortest contiguous piece whose sum is at least the target. If none, return 0.

Example: `target = 7`, `nums = [2, 3, 1, 2, 4, 3]` gives `2` (the piece `[4, 3]`).

**Brute force.** Try all starts and ends: O(n^2).

**Better idea, slowly.** Because all numbers are positive, adding a number makes the sum bigger, and removing one makes it smaller. So: expand `right` and add numbers. As soon as the sum is at least the target, the window is valid. Record its length. Then shrink from the left as long as it stays valid (to find the shortest). This is a "shortest" problem, so we record the answer INSIDE the shrinking loop.

```python
def min_sub_array_len(target, nums):
    left = 0                                      # left edge of the window
    window_sum = 0                                # sum inside the window
    best = float("inf")                           # shortest valid length found (infinity = none yet)
    for right in range(len(nums)):                # expand the right edge
        window_sum += nums[right]                 # add the new number
        while window_sum >= target:               # window is valid: try to make it shorter
            best = min(best, right - left + 1)    # record this valid length
            window_sum -= nums[left]              # remove the leftmost number
            left += 1                             # shrink from the left
    return 0 if best == float("inf") else best    # 0 if we never found a valid window

print(min_sub_array_len(7, [2, 3, 1, 2, 4, 3]))   # expect 2
assert min_sub_array_len(7, [2, 3, 1, 2, 4, 3]) == 2     # example
assert min_sub_array_len(100, [1, 2, 3]) == 0            # target too big
assert min_sub_array_len(7, [7]) == 1                    # one number is enough
```

**Trace** on `target = 7`, `[2, 3, 1, 2, 4, 3]`:

```text
right=0 (2): sum=2
right=1 (3): sum=5
right=2 (1): sum=6
right=3 (2): sum=8 >= 7 -> length 4, best=4. remove 2 -> sum=6, left=1
right=4 (4): sum=10 >= 7 -> length 4 (left 1..4), best=4. remove 3 -> sum=7, left=2
             sum=7 >= 7 -> length 3 (left 2..4), best=3. remove 1 -> sum=6, left=3
right=5 (3): sum=9 >= 7 -> length 3 (left 3..5), best=3. remove 2 -> sum=7, left=4
             sum=7 >= 7 -> length 2 (left 4..5), best=2. remove 4 -> sum=3, left=5
end. answer = 2
```

**Complexity.** Time O(n): both edges only move forward, so at most 2n moves. Space O(1).

**Two edge cases.** (1) The total of all numbers is less than the target: return 0 (do not return infinity). (2) A single number already at least the target: the answer is 1.

**How interviewers twist it.** "The array can have negative numbers" (a plain window fails: use prefix sums and a monotonic deque). "Return the piece itself." "Longest piece with sum at most target" (template B).

---

### Problem 4. Permutation in String

**Problem in plain words.** Given two strings `s1` and `s2`, is some permutation (the same letters in any order) of `s1` hiding as a substring of `s2`?

Example: `s1 = "ab"`, `s2 = "eidbaooo"` gives `True` (the piece `"ba"`).

**Brute force.** Make every permutation of `s1` and search for each in `s2`. That is factorial cost. A smarter brute force: for each piece of `s2` with length `len(s1)`, sort it and compare. O(n * m log m).

**Better idea, slowly.** A permutation has exactly the same letter counts as `s1`. So use a **fixed window** of length `len(s1)` over `s2`. Keep the letter counts of the window. Slide: add the new letter, remove the letter that left. After each slide, compare the window counts with the counts of `s1`. Counts are arrays of 26 numbers, so a comparison costs 26 steps.

```python
def check_inclusion(s1, s2):
    if len(s1) > len(s2):                              # s1 longer than s2: impossible
        return False                                   # no permutation can fit
    need = [0] * 26                                    # letter counts of s1 (a to z)
    have = [0] * 26                                    # letter counts of the current window
    for ch in s1:                                      # count the letters of s1
        need[ord(ch) - ord("a")] += 1                  # ord(ch) - ord('a') maps a..z to 0..25
    size = len(s1)                                     # fixed window size
    for i, ch in enumerate(s2):                        # i is the index of the letter entering
        have[ord(ch) - ord("a")] += 1                  # the new letter enters the window
        if i >= size:                                  # the window is now too long
            have[ord(s2[i - size]) - ord("a")] -= 1    # the oldest letter leaves the window
        if have == need:                               # same counts as s1?
            return True                                # found a permutation
    return False                                       # none found

print(check_inclusion("ab", "eidbaooo"))               # expect True
assert check_inclusion("ab", "eidbaooo") is True       # example
assert check_inclusion("ab", "eidboaoo") is False      # a and b are never next to each other
assert check_inclusion("abc", "ab") is False           # s1 longer than s2
assert check_inclusion("abc", "cba") is True           # equal length, permutation
```

**Trace** on `s1 = "ab"`, `s2 = "eidbao"` (positions e0 i1 d2 b3 a4 o5). We need counts `a:1, b:1`.

```text
i=0 add e                      window "e"   (size not reached yet; counts differ)
i=1 add i                      window "ei"  counts differ from need
i=2 add d, remove s2[0]=e      window "id"  counts differ
i=3 add b, remove s2[1]=i      window "db"  counts differ (b ok, but d is extra, a missing)
i=4 add a, remove s2[2]=d      window "ba"  a:1, b:1 equals need -> return True
```

**Complexity.** Time O(26 * m), which is O(m), where m = len(s2): each step compares two arrays of size 26. Space O(1): two arrays of 26.

**Two edge cases.** (1) `s1` longer than `s2`: `False` at once. (2) `s1` has repeated letters (like `"aab"`): the counts handle it.

**How interviewers twist it.** "Find All Anagrams in a String" (return every start index). "Do it with a single `matches` counter, so each slide is O(1)." "Unicode letters" (use a dictionary instead of 26 slots).

---

### Problem 5. Minimum Window Substring (hard)

**Problem in plain words.** Given strings `s` and `t`, find the smallest substring of `s` that contains every letter of `t` (with the right number of copies). If none, return `""`.

Example: `s = "ADOBECODEBANC"`, `t = "ABC"` gives `"BANC"`.

**Brute force.** Check every substring of `s` for whether it covers `t`. O(n^2) substrings and each check costs O(n + m). Too slow.

**Better idea, slowly.** This is a variable window with a "must contain" rule:

1. Make `need`: how many copies of each letter we still need. Also `missing` = total number of letters still missing (starts as `len(t)`).
2. Expand `right`. If the new letter is still needed (`need[ch] > 0`), then `missing` goes down by 1. Always do `need[ch] -= 1`. A NEGATIVE `need` value means we have extra copies of that letter.
3. When `missing == 0`, the window covers `t`. Now shrink from the left while the leftmost letter is extra (`need < 0`). This makes the window as short as possible. Save it if it is the best so far.
4. Then remove one needed letter from the left to break the window (`missing` goes to 1) and continue expanding to look for the next window.

```python
def min_window(s, t):
    if not t or len(t) > len(s):                     # nothing to find, or t is longer than s
        return ""                                    # no window is possible
    need = {}                                        # letter -> copies still needed (negative = extra)
    for ch in t:                                     # count the letters of t
        need[ch] = need.get(ch, 0) + 1               # add one for each copy
    missing = len(t)                                 # how many letters are still missing in total
    left = 0                                         # left edge of the window
    best_start, best_len = 0, float("inf")           # best window found so far
    for right, ch in enumerate(s):                   # expand the window on the right
        if need.get(ch, 0) > 0:                      # is this letter still needed?
            missing -= 1                             # one less letter missing
        need[ch] = need.get(ch, 0) - 1               # use up one copy (can go negative: extra)
        if missing == 0:                             # the window now covers all of t
            while need[s[left]] < 0:                 # the leftmost letter is an extra copy?
                need[s[left]] += 1                   # give the extra copy back
                left += 1                            # shrink the window
            if right - left + 1 < best_len:          # is this the shortest window so far?
                best_len = right - left + 1          # save its length
                best_start = left                    # and its start
            need[s[left]] += 1                       # drop a needed letter to break the window
            missing += 1                             # one letter is missing again
            left += 1                                # move the left edge past it
    if best_len == float("inf"):                     # we never found a covering window
        return ""                                    # report none
    return s[best_start:best_start + best_len]       # cut out the best window

print(min_window("ADOBECODEBANC", "ABC"))            # expect BANC
assert min_window("ADOBECODEBANC", "ABC") == "BANC"  # example
assert min_window("a", "a") == "a"                   # smallest case
assert min_window("a", "aa") == ""                   # t needs two a's, s has one
assert min_window("ab", "b") == "b"                  # shortest piece
```

**Trace** on `s = "ADOBECODEBANC"` (A0 D1 O2 B3 E4 C5 O6 D7 E8 B9 A10 N11 C12), `t = "ABC"`:

```text
need = {A:1, B:1, C:1}, missing = 3

right=0..5 reads A D O B E C.  After C arrives, missing = 0.  Window [0..5] = "ADOBEC" (length 6).
   Leftmost A is needed (need[A] = 0, not negative), so we cannot shrink. Save "ADOBEC".
   Drop A to break the window: missing = 1, left = 1.

right=6..9 reads O D E B: nothing new is needed (extra copies). missing stays 1.
right=10 reads A: missing = 0.  Window [1..10] = "DOBECODEBA".
   Shrink while the left letter is extra: remove D, O, B, E (all extra) -> left = 5.
   Window [5..10] = "CODEBA" (length 6). Not shorter than 6. Drop C: missing = 1, left = 6.

right=11 reads N: nothing needed.
right=12 reads C: missing = 0. Window [6..12] = "ODEBANC".
   Shrink: remove O, D, E (extra) -> left = 9.  Window [9..12] = "BANC" (length 4). New best!
   Drop B: missing = 1, left = 10. The loop ends.

answer = "BANC"
```

**Complexity.** Time O(n + m): the right edge moves n steps, the left edge moves at most n steps, and counting `t` costs m. Space O(k), where k is the number of different letters.

**Two edge cases.** (1) `t` longer than `s`, or `t` needs more copies of a letter than `s` has (`"a"` and `"aa"`): return `""`. (2) `t` has repeated letters: `need` counts copies, so duplicates work.

**How interviewers twist it.** "Substring with concatenation of all words." "Smallest range covering elements from k lists." "Shortest substring containing all vowels." "Stream of characters."

---

## 6. Common mistakes

1. **Using `if` instead of `while` for shrinking.** One removal may not be enough to fix the window.
2. **Recording the answer at the wrong time.** For "longest": record after the window is valid. For "shortest": record inside the shrink loop.
3. **Forgetting to remove the letter that leaves** (counts get wrong).
4. **Not deleting a count of 0** when you use `len(counts)` as "number of different letters".
5. **Off-by-one in the window length.** The length is `right - left + 1`.
6. **Trying a window with negative numbers.** The shrink logic breaks. Use prefix sums.
7. **Not checking `last[ch] >= left`** in the "no repeats" problem (`"abba"`).
8. **Returning infinity** when no window exists. Return 0 or "" as the problem says.

## 7. Practice list (8 more problems)

"Asked at" means the problem appears on that company's list in the community repo [liquidslr/leetcode-company-wise-problems](https://github.com/liquidslr/leetcode-company-wise-problems) (checked 2026-11-15). Difficulty is the LeetCode label from the same data.

| # | Problem | Difficulty | Asked at (per those lists) |
|---|---|---|---|
| 1 | Maximum Average Subarray I | Easy | Amazon, Google, Meta, Microsoft |
| 2 | Contains Duplicate II | Easy | Amazon, Google, Meta, Microsoft |
| 3 | Fruit Into Baskets | Medium | Amazon, Google, Meta, Microsoft |
| 4 | Max Consecutive Ones III | Medium | Amazon, Google, Meta, Microsoft |
| 5 | Find All Anagrams in a String | Medium | Amazon, Google, Meta, Microsoft |
| 6 | Longest Subarray of 1's After Deleting One Element | Medium | Amazon, Google, Meta, Microsoft |
| 7 | Sliding Window Maximum (needs a deque, see lesson 05 ideas) | Hard | Amazon, Google, Meta, Microsoft |
| 8 | Subarrays with K Different Integers | Hard | Amazon, Google, Meta, Microsoft |

## 8. Self-quiz (5 questions)

1. What is the difference between a fixed window and a variable window?
2. Why is a sliding window O(n) even though there is a `while` loop inside a `for` loop?
3. In a "longest valid window" problem, when do you record the length? In a "shortest valid window" problem?
4. Why does the plain sliding window usually need positive numbers?
5. In Minimum Window Substring, what does a negative value in `need` mean?

### Answers

1. Fixed: the size `k` never changes. Variable: the right edge expands and the left edge shrinks to keep the window valid, so the size changes.
2. The left edge only moves forward and never goes back. Each item enters once and leaves at most once, so the total work is at most 2n steps.
3. Longest: after the window is valid again (after the shrink loop). Shortest: inside the shrink loop, while the window is valid.
4. With positive numbers, a bigger window means a bigger sum and a smaller window means a smaller sum, so shrinking always fixes the rule. With negative numbers, this stops being true.
5. It means the window holds extra copies of that letter, more than `t` needs. Those extra letters can be removed safely from the left.

Next: [05_stack_and_queue.md](05_stack_and_queue.md)
