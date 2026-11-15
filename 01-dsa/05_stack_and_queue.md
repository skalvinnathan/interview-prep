# Lesson 05. Stack and Queue (including the monotonic stack)

Before this lesson: [00_how_to_start.md](00_how_to_start.md).

---

## 1. What is this?

### Stack

A **stack** is a pile where you only touch the TOP. The last item you put in is the first item you take out. This rule is called **LIFO**: Last In, First Out.

**Analogy: a pile of plates.** You put a new plate on top. You take a plate from the top. You never pull a plate from the middle.

Another picture: the **Undo** button. The last thing you did is the first thing that gets undone.

In Python, a stack is just a `list`:

- `stack.append(x)` pushes x on top. O(1).
- `stack.pop()` removes and returns the top item. O(1).
- `stack[-1]` looks at the top without removing it ("peek"). O(1).

### Queue

A **queue** is a line of people. The first person who comes is the first person served. This rule is **FIFO**: First In, First Out.

**Analogy: the line at a ticket counter.** New people join at the back. The person at the front leaves first.

In Python, use `collections.deque`:

- `queue.append(x)` joins at the back. O(1).
- `queue.popleft()` removes the front. O(1).

Do NOT use `list.pop(0)` for a queue. It is O(n), because all other items shift.

```text
STACK (one open end)              QUEUE (two open ends)
   push/pop here                  leave here           join here
        |                              |                    |
      +---+                          +---+---+---+---+---+
      | c |  <- top                  | a | b | c | d | e |
      | b |                          +---+---+---+---+---+
      | a |                          front              back
      +---+
```

### Monotonic stack (a special trick)

A **monotonic stack** is a stack whose items are always in order (always getting bigger, or always getting smaller). Before you push a new item, you pop the items that would break the order. Each popped item has just found its answer: "the first bigger item to my right is this new one."

**Analogy: people standing in a queue for a photo, and a tall person arrives.** All shorter people in front of the stack who were "waiting to see a taller person" are now satisfied. They leave the waiting pile.

## 2. When do I use it?

Stack:

- "Matching brackets" / "valid parentheses" / "nested" structure
- "Undo", "most recent first", "go back"
- "Evaluate an expression", "decode a string like 3[a]"
- "Next greater element", "next warmer day", "next smaller element" (monotonic stack)
- "Largest rectangle", "stock span"
- Any time you do **depth-first** things without recursion

Queue:

- "In order of arrival", "first come first served"
- "Level by level" (breadth-first search, lesson 08)
- "Number of recent calls in the last X seconds" (a window of recent items)
- Implement a queue with stacks (or the reverse)

## 3. A tiny example, traced line by line

### Stack: reverse the letters `a, b, c`

```text
stack = []
push 'a'  -> stack = [a]            (top is on the right)
push 'b'  -> stack = [a, b]
push 'c'  -> stack = [a, b, c]
pop       -> returns 'c'  stack = [a, b]
pop       -> returns 'b'  stack = [a]
pop       -> returns 'a'  stack = []
We got c, b, a: the letters came out reversed.
```

### Monotonic stack: next greater number for `[2, 1, 5, 3]`

The stack keeps INDEXES of numbers that still wait for a bigger number to their right. Their values go from big (bottom) to small (top).

```text
nums = [2, 1, 5, 3]      result = [-1, -1, -1, -1]      stack = []

i=0, x=2: stack empty, nothing to pop.         push 0.   stack = [0]
i=1, x=1: is 1 > nums[top=0]=2? no.            push 1.   stack = [0, 1]
i=2, x=5: is 5 > nums[1]=1? yes -> pop 1, result[1] = 5
          is 5 > nums[0]=2? yes -> pop 0, result[0] = 5
          stack empty.                         push 2.   stack = [2]
i=3, x=3: is 3 > nums[2]=5? no.                push 3.   stack = [2, 3]
end: indexes 2 and 3 never found a bigger number, so they stay -1.

result = [5, 5, -1, -1]
```

Each index is pushed one time and popped at most one time. So the cost is O(n), even with a `while` loop inside the `for` loop.

## 4. Template code (a comment on every line)

```python
# TEMPLATE A: a stack (reverse items using push and pop)
def reverse_with_stack(items):                 # function: returns the items in reverse order
    stack = []                                 # an empty stack (a Python list)
    for x in items:                            # go through the items in order
        stack.append(x)                        # push each item on top
    result = []                                # the answer list
    while stack:                               # while the stack is not empty
        result.append(stack.pop())             # pop the top item and add it to the result
    return result                              # the items now come out reversed

print(reverse_with_stack(["a", "b", "c"]))     # expect ['c', 'b', 'a']
assert reverse_with_stack(["a", "b", "c"]) == ["c", "b", "a"]   # check
assert reverse_with_stack([]) == []            # empty input
```

```python
# TEMPLATE B: a queue with deque (serve people in order of arrival)
from collections import deque                  # deque is a fast two-ended queue

def serve_in_order(customers):                 # function: returns customers in the order they are served
    queue = deque(customers)                   # put everyone in the line, first customer at the front
    served = []                                # the order in which people were served
    while queue:                               # while someone is still waiting
        served.append(queue.popleft())         # serve the person at the FRONT of the line
    return served                              # same order as arrival (FIFO)

print(serve_in_order(["Asha", "Ben", "Chen"]))     # expect ['Asha', 'Ben', 'Chen']
assert serve_in_order(["Asha", "Ben", "Chen"]) == ["Asha", "Ben", "Chen"]   # first in, first out
assert serve_in_order([]) == []                # nobody in line
```

```python
# TEMPLATE C: monotonic stack (next greater number to the right of each item)
def next_greater(nums):                        # function: for each item, the next bigger item on its right, else -1
    result = [-1] * len(nums)                  # answer for each position, default -1 (none found)
    stack = []                                 # indexes of items still waiting for a bigger number
    for i, x in enumerate(nums):               # look at each number with its index
        while stack and x > nums[stack[-1]]:   # does x beat the number waiting on top of the stack?
            j = stack.pop()                    # yes: that waiting index j has found its answer
            result[j] = x                      # its next greater number is x
        stack.append(i)                        # now x waits for its own bigger number
    return result                              # indexes left on the stack keep -1

print(next_greater([2, 1, 5, 3]))              # expect [5, 5, -1, -1]
assert next_greater([2, 1, 5, 3]) == [5, 5, -1, -1]   # the trace above
assert next_greater([3, 2, 1]) == [-1, -1, -1]        # falling numbers: nobody finds a bigger one
assert next_greater([]) == []                          # empty input
```

---

## 5. Classic problems

### Problem 1. Valid Parentheses

**Problem in plain words.** A string has only the characters `()[]{}`. Is it valid? Valid means: every opening bracket is closed by the same kind of bracket, and in the correct order.

Examples: `"()[]{}"` is valid. `"(]"` is not. `"([)]"` is not.

**Brute force.** Keep removing the pairs `()`, `[]`, `{}` from the string over and over until nothing changes. If the string becomes empty, it is valid. Each removal pass costs O(n), and there may be up to n/2 passes, so O(n^2).

**Better idea, slowly.** The most recent opening bracket must be closed first. "Most recent first" is exactly a stack. So:

- When you see an opening bracket, push it.
- When you see a closing bracket, look at the top of the stack. It must be the matching opening bracket. If yes, pop it. If not (or the stack is empty), the string is invalid.
- At the end, the stack must be empty (no opening bracket is left open).

```python
def is_valid(s):
    pairs = {")": "(", "]": "[", "}": "{"}        # each closing bracket -> its matching opening bracket
    stack = []                                    # holds the opening brackets that are still open
    for ch in s:                                  # read the string one character at a time
        if ch in pairs:                           # is it a closing bracket?
            if not stack or stack[-1] != pairs[ch]:   # no open bracket, or the top is the wrong kind
                return False                      # invalid string
            stack.pop()                           # matched: remove the opening bracket
        else:                                     # it is an opening bracket
            stack.append(ch)                      # push it and wait for its closing bracket
    return len(stack) == 0                        # valid only if nothing is left open

print(is_valid("()[]{}"))                         # expect True
assert is_valid("()[]{}") is True                 # example 1
assert is_valid("(]") is False                    # example 2
assert is_valid("([)]") is False                  # wrong order
assert is_valid("{[]}") is True                   # nested
assert is_valid("") is True                       # empty string
assert is_valid("(") is False                     # opened but never closed
assert is_valid(")") is False                     # closing with nothing open
```

**Trace** on `"([{}])"` (valid) and then `"([)]"` (invalid):

```text
"([{}])":
  '(' -> push.   stack = [ ( ]
  '[' -> push.   stack = [ ( [ ]
  '{' -> push.   stack = [ ( [ { ]
  '}' -> top is '{' = match. pop.   stack = [ ( [ ]
  ']' -> top is '[' = match. pop.   stack = [ ( ]
  ')' -> top is '(' = match. pop.   stack = [ ]
  end, stack empty -> True

"([)]":
  '(' -> push.   stack = [ ( ]
  '[' -> push.   stack = [ ( [ ]
  ')' -> top is '[' but ')' needs '(' -> mismatch -> False
```

**Complexity.** Time O(n): one pass, each push/pop is O(1). Space O(n): in the worst case, all characters are opening brackets.

**Two edge cases.** (1) Only a closing bracket, like `")"`: the stack is empty, so we must check `not stack` before looking at `stack[-1]`. (2) Only opening brackets, like `"((("`: the loop finishes with a non-empty stack, so the answer is `False`.

**How interviewers twist it.** "Minimum number of brackets to add to make it valid." "Longest valid parentheses substring." "Generate all valid combinations of n pairs." "Remove the minimum brackets to make it valid." "The string also contains letters."

---

### Problem 2. Min Stack

**Problem in plain words.** Design a stack that supports `push`, `pop`, `top`, and `get_min` (the smallest number now in the stack). All four must run in O(1) time.

**Brute force.** For `get_min`, scan the whole stack: O(n). Not allowed.

**Better idea, slowly.** The trick: with every number, also store "the smallest number in the stack up to and including this one". Store pairs `(value, min_so_far)`. When you push `x`, the new min is `min(x, previous min)`. When you pop, the min of the remaining stack is already stored in the new top. Nothing needs to be recomputed.

```python
class MinStack:
    def __init__(self):
        self.stack = []                            # list of pairs (value, minimum so far)

    def push(self, x):
        if self.stack:                             # is the stack not empty?
            current_min = min(x, self.stack[-1][1])    # smaller of x and the old minimum
        else:                                      # first item
            current_min = x                        # it is the minimum by itself
        self.stack.append((x, current_min))        # store the value with the minimum so far

    def pop(self):
        self.stack.pop()                           # remove the top pair

    def top(self):
        return self.stack[-1][0]                   # the value of the top pair

    def get_min(self):
        return self.stack[-1][1]                   # the stored minimum of the top pair

s = MinStack()                                     # make a new min stack
s.push(-2)                                         # push -2
s.push(0)                                          # push 0
s.push(-3)                                         # push -3
assert s.get_min() == -3                           # smallest is -3
s.pop()                                            # remove -3
assert s.top() == 0                                # now the top is 0
assert s.get_min() == -2                           # the minimum goes back to -2
s.push(-2)                                         # push a duplicate of the minimum
s.pop()                                            # remove the duplicate
assert s.get_min() == -2                           # -2 is still there
print("MinStack works")
```

**Trace:**

```text
push -2 -> stack = [(-2,-2)]
push  0 -> min(0, -2) = -2     stack = [(-2,-2), (0,-2)]
push -3 -> min(-3, -2) = -3    stack = [(-2,-2), (0,-2), (-3,-3)]
get_min -> top pair is (-3,-3) -> -3
pop     -> stack = [(-2,-2), (0,-2)]
top     -> 0
get_min -> top pair is (0,-2) -> -2
```

**Complexity.** Every operation is O(1) time. Space is O(n) because each item stores one extra number.

**Two edge cases.** (1) Duplicate minimums (push -2, push -2, pop): pairs handle this correctly, because each item carries its own minimum. (2) After popping everything, a new push must start a fresh minimum (we check `if self.stack`).

**How interviewers twist it.** "Max stack" (also `pop_max`). "Get the min in O(1) space for the extra stack." "Queue with `get_min`." "Stack with `increment(k, val)`."

---

### Problem 3. Daily Temperatures

**Problem in plain words.** Given a list of daily temperatures, return a list where `answer[i]` = how many days you must wait after day `i` for a WARMER day. If no warmer day comes, put 0.

Example: `[73, 74, 75, 71, 69, 72, 76, 73]` gives `[1, 1, 4, 2, 1, 1, 0, 0]`.

**Brute force.** For each day, look forward until you find a warmer day. O(n^2) in the worst case (for example, falling temperatures).

**Better idea, slowly (monotonic stack).** Keep a stack of the indexes of days that are still waiting for a warmer day. Their temperatures go from high (bottom) to low (top), because a day only stays on the stack if no warmer day has arrived yet. When a new day arrives, it may be warmer than some waiting days. Pop them: each popped day waits `new index - popped index` days. Then push the new day.

```python
def daily_temperatures(temps):
    answer = [0] * len(temps)                     # default 0: no warmer day found
    stack = []                                    # indexes of days waiting for a warmer day
    for i, t in enumerate(temps):                 # go through the days in order
        while stack and t > temps[stack[-1]]:     # today is warmer than the day on top?
            j = stack.pop()                       # that earlier day j can stop waiting
            answer[j] = i - j                     # it waited i - j days
        stack.append(i)                           # today now waits for a warmer day
    return answer                                 # leftover days keep 0

print(daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]))      # expect [1, 1, 4, 2, 1, 1, 0, 0]
assert daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]) == [1, 1, 4, 2, 1, 1, 0, 0]   # example
assert daily_temperatures([5, 4, 3]) == [0, 0, 0]     # falling: never warmer
assert daily_temperatures([5, 5, 5]) == [0, 0, 0]     # equal is NOT warmer
assert daily_temperatures([30]) == [0]                # one day
```

**Trace** on `[73, 74, 75, 71, 69, 72, 76, 73]` (stack holds indexes):

```text
i=0 t=73: nothing to pop.                                       stack = [0]
i=1 t=74: 74 > 73 -> pop 0, answer[0] = 1-0 = 1.                stack = [1]
i=2 t=75: 75 > 74 -> pop 1, answer[1] = 2-1 = 1.                stack = [2]
i=3 t=71: 71 > 75? no.                                          stack = [2, 3]
i=4 t=69: 69 > 71? no.                                          stack = [2, 3, 4]
i=5 t=72: 72 > 69 -> pop 4, answer[4] = 5-4 = 1.
          72 > 71 -> pop 3, answer[3] = 5-3 = 2.
          72 > 75? no.                                          stack = [2, 5]
i=6 t=76: 76 > 72 -> pop 5, answer[5] = 6-5 = 1.
          76 > 75 -> pop 2, answer[2] = 6-2 = 4.                stack = [6]
i=7 t=73: 73 > 76? no.                                          stack = [6, 7]
end: days 6 and 7 stay 0.
answer = [1, 1, 4, 2, 1, 1, 0, 0]
```

**Complexity.** Time O(n): each index is pushed once and popped at most once. Space O(n) for the stack.

**Two edge cases.** (1) Strictly falling temperatures: nobody is ever popped, the answer is all zeros. (2) Equal temperatures: "warmer" means strictly greater, so we use `>` and not `>=`.

**How interviewers twist it.** "Next Greater Element" (and its circular version: loop over the list twice). "Stock span." "Next smaller element." "Sum of subarray minimums."

---

### Problem 4. Largest Rectangle in Histogram

**Problem in plain words.** A histogram is a row of bars, each with width 1 and a given height. Find the area of the largest rectangle that fits inside the histogram (it can span several bars).

Example: `[2, 1, 5, 6, 2, 3]` gives `10` (the bars of height 5 and 6 give a rectangle of height 5, width 2).

**Brute force.** For each bar, expand left and right while bars are at least as tall. Area = height x width. O(n^2).

**Better idea, slowly.** For each bar, the biggest rectangle that uses its full height reaches left and right until a SHORTER bar stops it. So for every bar we need "the first shorter bar on the left" and "the first shorter bar on the right". A monotonic stack finds both in one pass.

Keep a stack of indexes with **increasing** heights. When a new bar `h` is shorter than the bar on top, the top bar cannot extend any further to the right. Pop it and compute its rectangle:

- height = the popped bar's height
- right edge = the current index `i` (a shorter bar stops it here)
- left edge = the index now on top of the stack (the first shorter bar on the left), or -1 if the stack is empty
- width = `i - left - 1`

At the end, add a bar of height 0 (a "sentinel") so that every bar still on the stack gets popped.

```python
def largest_rectangle(heights):
    stack = []                                         # indexes of bars with increasing heights
    best = 0                                           # biggest area found
    for i, h in enumerate(heights + [0]):              # add a 0-height bar at the end to flush the stack
        while stack and heights[stack[-1]] > h:        # the top bar is taller than the new bar?
            height = heights[stack.pop()]              # pop it: this is the rectangle's height
            left = stack[-1] if stack else -1          # first shorter bar on the left (or -1)
            width = i - left - 1                       # bars strictly between left and i
            best = max(best, height * width)           # keep the largest area
        stack.append(i)                                # push the current bar
    return best                                        # the answer

print(largest_rectangle([2, 1, 5, 6, 2, 3]))           # expect 10
assert largest_rectangle([2, 1, 5, 6, 2, 3]) == 10     # example
assert largest_rectangle([2, 4]) == 4                  # two bars
assert largest_rectangle([3, 3, 3]) == 9               # equal bars: one wide rectangle
assert largest_rectangle([]) == 0                      # no bars
assert largest_rectangle([5]) == 5                     # one bar
```

**Trace** on `[2, 1, 5, 6, 2, 3]` plus the sentinel `0` at index 6:

```text
i=0 h=2: stack empty.                                         push 0.  stack = [0]
i=1 h=1: top bar 2 > 1 -> pop 0: height 2, left = -1 (empty), width = 1-(-1)-1 = 1, area 2. best=2
         push 1.                                              stack = [1]
i=2 h=5: top bar 1 > 5? no.                                   push 2.  stack = [1, 2]
i=3 h=6: top bar 5 > 6? no.                                   push 3.  stack = [1, 2, 3]
i=4 h=2: top bar 6 > 2 -> pop 3: height 6, left = 2, width = 4-2-1 = 1, area 6. best=6
         top bar 5 > 2 -> pop 2: height 5, left = 1, width = 4-1-1 = 2, area 10. best=10
         top bar 1 > 2? no.                                   push 4.  stack = [1, 4]
i=5 h=3: top bar 2 > 3? no.                                   push 5.  stack = [1, 4, 5]
i=6 h=0 (sentinel):
         pop 5: height 3, left = 4, width = 6-4-1 = 1, area 3.
         pop 4: height 2, left = 1, width = 6-1-1 = 4, area 8.
         pop 1: height 1, left = -1, width = 6-(-1)-1 = 6, area 6.
best = 10
```

**Complexity.** Time O(n): each bar is pushed once and popped once. Space O(n) for the stack.

**Two edge cases.** (1) Equal bars (`[3, 3, 3]`): we only pop when strictly taller, so equal bars stay, and the last one gets the wide rectangle at the end (area 9). (2) Empty list gives 0; one bar gives its own height.

**How interviewers twist it.** "Maximal rectangle in a binary matrix" (run this for every row). "Trapping rain water" (a stack solution exists). "Largest rectangle with at most k changes."

---

### Problem 5. Implement Queue using Stacks

**Problem in plain words.** Build a queue (first in, first out) using only stacks (last in, first out). Support `push`, `pop` (from the front), `peek` (front), and `empty`.

**Brute force.** On every `push`, move all items to a helper stack, add the new item at the bottom, and move everything back. That makes `push` cost O(n).

**Better idea, slowly.** Use TWO stacks:

- `in_stack`: new items are pushed here.
- `out_stack`: items are popped from here.

When `out_stack` is empty and you need the front, move ALL items from `in_stack` into `out_stack`, one by one. Moving reverses the order, so the oldest item ends up on top of `out_stack`. That is the front of the queue.

Each item moves at most once from `in_stack` to `out_stack`. So the average cost per operation is O(1) (called **amortized** O(1): some single calls are slow, but the average is fast).

```python
class MyQueue:
    def __init__(self):
        self.in_stack = []                        # new items go here
        self.out_stack = []                       # items leave from here

    def push(self, x):
        self.in_stack.append(x)                   # add to the back of the queue

    def _move(self):
        if not self.out_stack:                    # only refill when the out stack is empty
            while self.in_stack:                  # move every item over
                self.out_stack.append(self.in_stack.pop())   # this reverses the order

    def pop(self):
        self._move()                              # make sure the front is on top of out_stack
        return self.out_stack.pop()               # remove and return the front item

    def peek(self):
        self._move()                              # make sure the front is on top of out_stack
        return self.out_stack[-1]                 # look at the front item

    def empty(self):
        return not self.in_stack and not self.out_stack   # empty only if both stacks are empty

q = MyQueue()                                     # make a queue
q.push(1)                                         # queue: 1
q.push(2)                                         # queue: 1 2
q.push(3)                                         # queue: 1 2 3
assert q.pop() == 1                               # first in, first out
q.push(4)                                         # queue: 2 3 4
assert q.peek() == 2                              # the front is 2
assert q.pop() == 2                               # remove 2
assert q.pop() == 3                               # remove 3
assert q.pop() == 4                               # remove 4
assert q.empty() is True                          # nothing left
print("MyQueue works")
```

**Trace:**

```text
push 1,2,3      in_stack = [1, 2, 3]            out_stack = []
pop:            out_stack is empty -> move all. out_stack = [3, 2, 1]  in_stack = []
                out_stack.pop() -> 1            out_stack = [3, 2]
push 4          in_stack = [4]                  out_stack = [3, 2]
peek:           out_stack not empty -> top is 2 -> returns 2
pop             -> 2                            out_stack = [3]
pop             -> 3                            out_stack = []
pop:            out_stack empty -> move [4].    out_stack = [4] -> pop returns 4
empty           -> True
```

**Complexity.** Amortized O(1) per operation: each item is pushed twice and popped twice in its whole life. Space O(n).

**Two edge cases.** (1) Mixing pushes and pops: do NOT move items while `out_stack` still has items, or the order breaks. (2) `empty` must check BOTH stacks.

**How interviewers twist it.** "Implement a stack using queues." "Circular queue." "Queue that also returns the maximum in O(1)." "Design a hit counter."

---

## 6. Common mistakes

1. **Popping from an empty stack.** Check `if stack` first. It raises `IndexError`.
2. **Using `list.pop(0)` as a queue.** It is O(n). Use `deque.popleft()`.
3. **Forgetting leftover items.** After the loop, items still on the stack have no answer (or must be handled).
4. **Mixing up `>` and `>=`** in monotonic stacks. "Strictly warmer" needs `>`.
5. **Storing values when you need indexes.** For "how many days later" you need the index.
6. **Forgetting the sentinel** in the histogram problem. Bars left on the stack never get processed.
7. **Moving items into `out_stack` too early** in the queue-from-stacks design.
8. **Not checking the stack is empty at the end** in the bracket problem.

## 7. Practice list (8 more problems)

"Asked at" means the problem appears on that company's list in the community repo [liquidslr/leetcode-company-wise-problems](https://github.com/liquidslr/leetcode-company-wise-problems) (checked 2026-11-15). Difficulty is the LeetCode label from the same data.

| # | Problem | Difficulty | Asked at (per those lists) |
|---|---|---|---|
| 1 | Number of Recent Calls (a queue) | Easy | Amazon, Google, Meta, Microsoft |
| 2 | Next Greater Element I | Easy | Amazon, Google, Meta, Microsoft |
| 3 | Evaluate Reverse Polish Notation | Medium | Amazon, Google, Meta, Microsoft |
| 4 | Next Greater Element II | Medium | Amazon, Google, Meta, Microsoft |
| 5 | Decode String | Medium | Amazon, Google, Meta, Microsoft |
| 6 | Asteroid Collision | Medium | Amazon, Google, Meta, Microsoft |
| 7 | Online Stock Span | Medium | Amazon, Google, Meta, Microsoft |
| 8 | Basic Calculator | Hard | Amazon, Google, Meta, Microsoft |

## 8. Self-quiz (5 questions)

1. What does LIFO mean? Which Python type do you use for a stack, and which for a queue?
2. Why is `list.pop(0)` a bad queue operation?
3. In Daily Temperatures, why do we store indexes on the stack, not temperatures?
4. A monotonic stack has a `while` loop inside a `for` loop. Why is it still O(n)?
5. In Min Stack, why do we store the minimum with every item?

### Answers

1. Last In, First Out. A `list` for a stack; a `collections.deque` for a queue.
2. It removes the first item and shifts all other items one place left: O(n). `deque.popleft()` is O(1).
3. The answer is a distance in days (`i - j`). We need the index to calculate it. The temperature can be read from the list using the index.
4. Every item is pushed once and popped at most once. So the total number of pops is at most n.
5. When we pop, the minimum of the remaining items must be known at once. Each item's stored minimum is the minimum of everything below it and itself, so after a pop the new top already knows it.

Next: [06_binary_search.md](06_binary_search.md)
