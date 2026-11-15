# Lesson 03. Two Pointers

Before this lesson: [00_how_to_start.md](00_how_to_start.md). It helps to know lessons 01 and 02.

---

## 1. What is this?

A **pointer** here is just a number that remembers a position (an index) in a list or string. "Two pointers" means: use TWO such numbers at the same time, and move them step by step. You do not need loops inside loops.

There are two main styles:

1. **Opposite ends.** One pointer starts at the left end. The other starts at the right end. They walk toward each other until they meet.
2. **Same direction (slow and fast).** Both start at the left. The fast pointer walks ahead and reads. The slow pointer marks where to write.

**Analogy 1 (opposite ends).** Two friends stand at the two ends of a long corridor and walk toward each other. They stop when they meet. At every step you decide: "Should the left friend move, or the right friend?"

**Analogy 2 (same direction).** One person reads a book fast (the fast pointer). A second person copies only the good lines into a notebook (the slow pointer). The notebook grows slower than the reading.

**Why is it fast?** Brute force checks all pairs: O(n^2). With two pointers, every step throws away at least one candidate for good. So the pointers cross at most n steps in total: O(n).

## 2. When do I use it?

Words that give it away:

- "The array is **sorted**" and you must find a pair or triple (sum equals target).
- "**Palindrome**" (a word that reads the same from both sides).
- "Remove duplicates **in place**" / "move all zeros to the end" / "partition".
- "Two ends": container, squeeze, "from both sides".
- "O(1) extra space" along with an array.

Quick test: "If I know the sum is too big, which pointer should I move?" If you can answer that clearly, two pointers likely works. (This clear answer needs sorted data or a monotone idea.)

## 3. A tiny example, traced line by line

Find two numbers in the sorted list `[1, 3, 4, 6, 9]` that add to 13.

```text
nums = [1, 3, 4, 6, 9]      target = 13
left = 0 (value 1), right = 4 (value 9)

step 1: 1 + 9 = 10.  10 < 13 (too small).  Left number is the smallest. Move left ->  left = 1
step 2: 3 + 9 = 12.  12 < 13 (too small).  Move left ->                              left = 2
step 3: 4 + 9 = 13.  13 = 13  found! return positions 2 and 4
```

Now target = 7 on the same list:

```text
left = 0 (1), right = 4 (9)
step 1: 1 + 9 = 10.  10 > 7 (too big).  Right number is the largest. Move right -> right = 3
step 2: 1 + 6 = 7.   found! return positions 0 and 3
```

The rule:

- Sum too small: move **left** to the right (a bigger number comes in).
- Sum too big: move **right** to the left (a smaller number comes in).

## 4. Template code (a comment on every line)

```python
# TEMPLATE A: opposite ends (is the string a palindrome?)
def is_palindrome(s):                       # function: True if s reads the same both ways
    left = 0                                # left pointer at the first letter
    right = len(s) - 1                      # right pointer at the last letter
    while left < right:                     # continue until the pointers meet or cross
        if s[left] != s[right]:             # do the two letters differ?
            return False                    # yes: it is not a palindrome
        left += 1                           # move the left pointer one step right
        right -= 1                          # move the right pointer one step left
    return True                             # all pairs matched

print(is_palindrome("abcba"))               # expect True
assert is_palindrome("abcba") is True       # odd length palindrome
assert is_palindrome("abca") is False       # not a palindrome
assert is_palindrome("") is True            # empty string counts as a palindrome
```

```python
# TEMPLATE B: opposite ends on a SORTED list (find a pair with a given sum)
def pair_with_sum(nums, target):            # function: returns positions of a pair, or None
    left = 0                                # start at the smallest number
    right = len(nums) - 1                   # start at the largest number
    while left < right:                     # two different positions are needed
        total = nums[left] + nums[right]    # sum of the two numbers
        if total == target:                 # exact match
            return [left, right]            # found the pair
        if total < target:                  # sum is too small
            left += 1                       # use a bigger left number
        else:                               # sum is too big
            right -= 1                      # use a smaller right number
    return None                             # pointers met: no pair exists

print(pair_with_sum([1, 3, 4, 6, 9], 13))   # expect [2, 4]
assert pair_with_sum([1, 3, 4, 6, 9], 13) == [2, 4]   # the first trace
assert pair_with_sum([1, 3, 4, 6, 9], 7) == [0, 3]    # the second trace
assert pair_with_sum([1, 3, 4], 100) is None          # no pair
```

```python
# TEMPLATE C: same direction, slow and fast (remove duplicates from a sorted list, in place)
def remove_duplicates(nums):                # function: returns how many unique numbers; changes nums in place
    if not nums:                            # empty list has nothing to do
        return 0                            # zero unique numbers
    write = 1                               # slow pointer: next place to write a new unique number
    for read in range(1, len(nums)):        # fast pointer: reads every number from index 1
        if nums[read] != nums[write - 1]:   # is it different from the last unique number we kept?
            nums[write] = nums[read]        # yes: copy it to the write position
            write += 1                      # move the write position forward
    return write                            # the first `write` items are the unique numbers

data = [1, 1, 2, 2, 3]                      # a sorted list with duplicates
k = remove_duplicates(data)                 # run it
print(k, data[:k])                          # expect 3 [1, 2, 3]
assert k == 3 and data[:k] == [1, 2, 3]     # check the result
assert remove_duplicates([]) == 0           # empty list
```

Trace of template C on `[1, 1, 2, 2, 3]`:

```text
write = 1
read=1: nums[1]=1 vs nums[0]=1 -> same, skip.
read=2: nums[2]=2 vs nums[0]=1 -> different: nums[1]=2, write=2.   list = [1, 2, 2, 2, 3]
read=3: nums[3]=2 vs nums[1]=2 -> same, skip.
read=4: nums[4]=3 vs nums[1]=2 -> different: nums[2]=3, write=3.   list = [1, 2, 3, 2, 3]
return 3. The first 3 items [1, 2, 3] are the answer.
```

---

## 5. Classic problems

### Problem 1. Valid Palindrome

**Problem in plain words.** Given a sentence, ignore everything that is not a letter or digit, and ignore upper/lower case. Is it a palindrome?

Example: `"A man, a plan, a canal: Panama"` is `True`. `"race a car"` is `False`.

**Brute force.** Build a clean string (only letters and digits, lowercase) and compare it with its reverse. O(n) time and O(n) extra space. (This is already OK for time. Two pointers saves the extra space.)

**Better idea, slowly.** Use two pointers at the ends. If the left letter is not a letter or digit, move left. If the right one is not, move right. When both are real characters, compare them (in lowercase). If they differ, the answer is `False`. If they match, move both inward.

```python
def is_valid_palindrome(s):
    left, right = 0, len(s) - 1                    # pointers at both ends
    while left < right:                            # until they meet
        while left < right and not s[left].isalnum():     # skip characters that are not letters/digits on the left
            left += 1                              # move left pointer forward
        while left < right and not s[right].isalnum():    # skip such characters on the right
            right -= 1                             # move right pointer backward
        if s[left].lower() != s[right].lower():    # compare ignoring case
            return False                           # mismatch: not a palindrome
        left += 1                                  # these two match, move inward
        right -= 1                                 # move the right pointer inward too
    return True                                    # everything matched

print(is_valid_palindrome("A man, a plan, a canal: Panama"))   # expect True
assert is_valid_palindrome("A man, a plan, a canal: Panama") is True   # example 1
assert is_valid_palindrome("race a car") is False                      # example 2
assert is_valid_palindrome(" ") is True                                # only a space
assert is_valid_palindrome(".,") is True                               # only punctuation
```

**Trace** on `"race a car"` (indexes r0 a1 c2 e3 space4 a5 space6 c7 a8 r9):

```text
left=0 'r', right=9 'r' -> equal.  left=1, right=8
left=1 'a', right=8 'a' -> equal.  left=2, right=7
left=2 'c', right=7 'c' -> equal.  left=3, right=6
left=3 'e', right=6 ' ' -> right is a space, skip: right=5 'a'
compare 'e' and 'a' -> different -> return False
```

**Complexity.** Time O(n): each pointer moves in one direction only. Space O(1): only two numbers.

**Two edge cases.** (1) The string has only spaces or punctuation (like `" "`): after skipping, nothing is left, the answer is `True`. (2) Mixed case and digits (`"0P"` is `False`): compare lowercase, and digits are real characters.

**How interviewers twist it.** "You may delete at most one character" (Valid Palindrome II). "Is a linked list a palindrome?" "Find the longest palindromic substring." "Can the letters be rearranged into a palindrome?"

---

### Problem 2. 3Sum

**Problem in plain words.** Given a list of integers, find all unique triples `[a, b, c]` (from three different positions) with `a + b + c = 0`. No duplicate triples in the answer.

Example: `[-1, 0, 1, 2, -1, -4]` gives `[[-1, -1, 2], [-1, 0, 1]]`.

**Brute force.** Three loops over all triples: O(n^3). You also need a set to remove duplicate triples.

**Better idea, slowly.**

1. **Sort** the list. Sorting makes two pointers possible and makes duplicates sit side by side.
2. Fix the first number `nums[i]`. The other two must add to `-nums[i]`. That is the sorted "pair with sum" problem on the part to the right of `i`. Use left and right pointers.
3. **Skip duplicates.** If `nums[i]` equals the previous number, skip it (it would give the same triples). After you find a triple, move `left` forward past equal numbers.
4. A small speed-up: if `nums[i] > 0`, stop. All numbers after it are positive and the sum cannot be 0.

```python
def three_sum(nums):
    nums = sorted(nums)                               # sort a copy of the list
    result = []                                       # triples we find
    n = len(nums)                                     # how many numbers
    for i in range(n - 2):                            # first number of the triple
        if nums[i] > 0:                               # all later numbers are bigger, sum can't be 0
            break                                     # stop early
        if i > 0 and nums[i] == nums[i - 1]:          # same first number as before?
            continue                                  # skip it to avoid duplicate triples
        left, right = i + 1, n - 1                    # two pointers on the part to the right of i
        while left < right:                           # search for a pair
            total = nums[i] + nums[left] + nums[right]    # sum of the three numbers
            if total < 0:                             # too small
                left += 1                             # need a bigger number
            elif total > 0:                           # too big
                right -= 1                            # need a smaller number
            else:                                     # total is 0: a valid triple
                result.append([nums[i], nums[left], nums[right]])   # save it
                left += 1                             # move both pointers inward
                right -= 1                            # to look for more pairs
                while left < right and nums[left] == nums[left - 1]:   # skip equal numbers on the left
                    left += 1                         # avoid duplicate triples
    return result                                     # all unique triples

print(three_sum([-1, 0, 1, 2, -1, -4]))               # expect [[-1, -1, 2], [-1, 0, 1]]
assert three_sum([-1, 0, 1, 2, -1, -4]) == [[-1, -1, 2], [-1, 0, 1]]   # the example
assert three_sum([0, 0, 0, 0]) == [[0, 0, 0]]         # many zeros, one triple only
assert three_sum([1, 2, 3]) == []                     # all positive
assert three_sum([1, -1]) == []                       # fewer than 3 numbers
```

**Trace** on `[-1, 0, 1, 2, -1, -4]`. After sorting: `[-4, -1, -1, 0, 1, 2]`.

```text
i=0 (-4): left=1 (-1), right=5 (2):  sum=-3 <0 -> left=2
                       left=2 (-1), right=5 (2):  sum=-3 <0 -> left=3
                       left=3 (0),  right=5 (2):  sum=-2 <0 -> left=4
                       left=4 (1),  right=5 (2):  sum=-1 <0 -> left=5  -> pointers meet, stop
i=1 (-1): left=2 (-1), right=5 (2):  sum=0   -> save [-1,-1,2]. left=3, right=4
                       left=3 (0),  right=4 (1):  sum=0   -> save [-1,0,1]. left=4, right=3 -> stop
i=2 (-1): same as nums[1] -> skip
i=3 (0):  left=4 (1), right=5 (2):  sum=3 >0 -> right=4 -> pointers meet, stop
result = [[-1,-1,2], [-1,0,1]]
```

**Complexity.** Time O(n^2): sorting is O(n log n). Then for each `i` the two pointers walk the rest once, O(n). Space O(1) extra if we do not count the output (the sort may use some memory).

**Two edge cases.** (1) `[0, 0, 0, 0]`: only ONE triple `[0,0,0]`; duplicate skipping must work. (2) Fewer than three numbers, or all positive numbers: return `[]`.

**How interviewers twist it.** "3Sum closest to a target." "4Sum." "Count triples with sum less than target." "Return indices, not values" (then sorting changes the indices: keep the original indices).

---

### Problem 3. Container With Most Water

**Problem in plain words.** You get a list of heights of vertical lines placed at positions 0, 1, 2, ... Choose two lines. Together with the x-axis they form a container. Its water volume = (distance between the lines) x (height of the shorter line). Find the biggest volume.

Example: `[1, 8, 6, 2, 5, 4, 8, 3, 7]` gives `49` (lines of height 8 at index 1 and 7 at index 8: min height 7, width 7).

**Brute force.** Try every pair of lines: O(n^2).

**Better idea, slowly.** Start with the widest container: first line and last line. Compute its area. Now, to find a better container, we must move one line inwards. The width shrinks for sure. So the only hope is a TALLER shorter-side.

- The water level is limited by the **shorter** line.
- If we move the **taller** line inward, the shorter line still limits us and the width is smaller. The area cannot get bigger. So moving the taller line is useless.
- So we always move the **shorter** line inward. It might find a taller line.

```python
def max_area(height):
    left, right = 0, len(height) - 1                  # start with the widest container
    best = 0                                          # biggest area found
    while left < right:                               # until the two lines meet
        width = right - left                          # distance between the lines
        h = min(height[left], height[right])          # water level = shorter line
        best = max(best, width * h)                   # update the best area
        if height[left] < height[right]:              # left line is shorter
            left += 1                                 # move the shorter line inward
        else:                                         # right line is shorter or equal
            right -= 1                                # move the right line inward
    return best                                       # the answer

print(max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]))          # expect 49
assert max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49    # the example
assert max_area([1, 1]) == 1                          # two lines
assert max_area([0, 0]) == 0                          # no water
```

**Trace** on `[1, 8, 6, 2, 5, 4, 8, 3, 7]`:

```text
left right  heights   width  area      best  move
 0     8    1 and 7     8     1*8 = 8     8   left (1 < 7)  -> left=1
 1     8    8 and 7     7     7*7 = 49   49   right (8 >= 7)-> right=7
 1     7    8 and 3     6     3*6 = 18   49   right         -> right=6
 1     6    8 and 8     5     8*5 = 40   49   right (equal)  -> right=5
 1     5    8 and 4     4     4*4 = 16   49   right         -> right=4
 1     4    8 and 5     3     5*3 = 15   49   right         -> right=3
 1     3    8 and 2     2     2*2 = 4    49   right         -> right=2
 1     2    8 and 6     1     6*1 = 6    49   right         -> right=1  stop
answer = 49
```

**Complexity.** Time O(n): each step moves a pointer, at most n steps. Space O(1).

**Two edge cases.** (1) Only two lines: the answer is `min(a, b) * 1`. (2) Heights of 0 give area 0.

**How interviewers twist it.** "Trapping Rain Water" (next problem; here the walls are filled in, not just two lines). "Largest rectangle in a histogram" (lesson 05). "3D version."

---

### Problem 4. Trapping Rain Water

**Problem in plain words.** A list of non-negative numbers shows the height of bars of width 1. After rain, how much water stays trapped between the bars?

Example: `[0,1,0,2,1,0,1,3,2,1,2,1]` gives `6`.

**Brute force.** Water above bar `i` = `min(tallest bar to the left, tallest bar to the right) - height[i]` (if positive). For each bar, scan left and right: O(n^2). A common O(n) time / O(n) space trick: pre-compute the tallest-left and tallest-right arrays first.

**Better idea, slowly (two pointers, O(1) space).** Keep `left` and `right` pointers, and two numbers: `left_max` and `right_max` (the tallest bar seen so far from each side).

- Look at which side has the shorter bar at the pointers. Say `height[left] < height[right]`.
- Then the right side has a wall at least as tall as `height[right]`, which is taller than `height[left]`. So the water at `left` depends only on `left_max`. We can finish `left` now: water = `left_max - height[left]`. Then move `left` inward.
- Else do the same on the right side.

```python
def trap(height):
    left, right = 0, len(height) - 1              # pointers at both ends
    left_max = 0                                  # tallest bar seen from the left
    right_max = 0                                 # tallest bar seen from the right
    water = 0                                     # total trapped water
    while left < right:                           # until the pointers meet
        if height[left] < height[right]:          # the left bar is the shorter side
            left_max = max(left_max, height[left])        # update the tallest wall on the left
            water += left_max - height[left]              # water held above this bar (0 or more)
            left += 1                                     # this bar is done, move inward
        else:                                     # the right bar is shorter or equal
            right_max = max(right_max, height[right])     # update the tallest wall on the right
            water += right_max - height[right]            # water held above this bar
            right -= 1                                    # this bar is done, move inward
    return water                                  # total water

print(trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]))        # expect 6
assert trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6   # the example
assert trap([3, 0, 2, 0, 4]) == 7                        # the small trace below
assert trap([1, 2, 3]) == 0                              # increasing: no water
assert trap([5]) == 0                                    # one bar
```

**Trace** on `[3, 0, 2, 0, 4]`:

```text
left=0 right=4  heights 3 and 4. 3 < 4 -> left side. left_max=3. water += 3-3 = 0.  left=1
left=1 right=4  heights 0 and 4. 0 < 4 -> left side. left_max=3. water += 3-0 = 3.  left=2   (water=3)
left=2 right=4  heights 2 and 4. 2 < 4 -> left side. left_max=3. water += 3-2 = 1.  left=3   (water=4)
left=3 right=4  heights 0 and 4. 0 < 4 -> left side. left_max=3. water += 3-0 = 3.  left=4   (water=7)
left=4 = right -> stop. answer = 7
```

(You can check by eye: the tall walls are 3 and 4, so the water level is 3. Holes at heights 0, 2, 0 hold 3 + 1 + 3 = 7.)

**Complexity.** Time O(n): every step moves a pointer. Space O(1): four variables.

**Two edge cases.** (1) Fewer than 3 bars or a list that only goes up (or only down): no water, answer 0. (2) A very tall bar at one end: the other side decides the water; the code handles it by moving the shorter side.

**How interviewers twist it.** "Solve it with a stack" (lesson 05). "2D trapping rain water" (needs a heap). "Return the water level per bar." "What if bars have different widths?"

---

## 6. Common mistakes

1. **Using two pointers on unsorted data** when the move rule depends on order (pair sum). Sort first, or use a hash map.
2. **Wrong loop condition.** Use `left < right` when the two pointers must be different positions.
3. **Forgetting to move a pointer** after a match. Infinite loop.
4. **Not skipping duplicates** (3Sum), so the answer has repeated triples.
5. **Skipping duplicates too early.** Skip only AFTER you used the value once.
6. **Moving the wrong pointer** in Container and Trapping Water. Always reason: "which pointer is the limit?"
7. **Index out of range** when a skip loop runs past the end. Keep `left < right` inside the skip loops.
8. **Sorting and losing indices** when the problem asks for original positions.

## 7. Practice list (8 more problems)

"Asked at" means the problem appears on that company's list in the community repo [liquidslr/leetcode-company-wise-problems](https://github.com/liquidslr/leetcode-company-wise-problems) (checked 2026-11-15). Difficulty is the LeetCode label from the same data.

| # | Problem | Difficulty | Asked at (per those lists) |
|---|---|---|---|
| 1 | Two Sum II - Input Array Is Sorted | Medium | Amazon, Google, Meta, Microsoft |
| 2 | Move Zeroes (also in lesson 01: do it with slow and fast pointers) | Easy | Amazon, Google, Meta, Microsoft |
| 3 | Sort Colors | Medium | Amazon, Google, Meta, Microsoft |
| 4 | 3Sum Closest | Medium | Amazon, Google, Meta, Microsoft |
| 5 | Squares of a Sorted Array | Easy | Amazon, Google, Meta, Microsoft |
| 6 | Valid Palindrome II | Easy | Amazon, Google, Meta, Microsoft |
| 7 | Merge Sorted Array | Easy | Amazon, Google, Meta, Microsoft |
| 8 | Boats to Save People | Medium | Amazon, Google, Meta, Microsoft |

## 8. Self-quiz (5 questions)

1. For a sorted list and a target sum, when the current sum is too big, which pointer moves and in which direction?
2. Why is the total work of the opposite-ends method O(n) and not O(n^2)?
3. In 3Sum, why do we sort first?
4. In Container With Most Water, why do we move the pointer of the SHORTER line?
5. In Trapping Rain Water, if `height[left] < height[right]`, why can we finish the water at `left` using only `left_max`?

### Answers

1. The right pointer moves left (to a smaller number).
2. Each step moves one pointer by one place, and the pointers never go back. So there are at most n steps in total.
3. Sorting lets us use two pointers for the last two numbers and puts duplicates next to each other so we can skip them.
4. The water level is limited by the shorter line. Moving the taller line can only make the width smaller without raising the limit, so it can never give a bigger area.
5. The right side has a bar at least as tall as `height[right]`, which is taller than `height[left]`. So the right wall is never the limit for the bar at `left`. Only the left wall (`left_max`) matters.

Next: [04_sliding_window.md](04_sliding_window.md)
