# 00. How to start: reading a problem, the 5-step method, and Big-O

This is the first file. Read it fully before lesson 01.
You do not need to be "smart" for DSA. DSA is a skill like cooking or driving.
You learn a small set of patterns. Then you practise them. That is all.

DSA means "Data Structures and Algorithms".

- A **data structure** is a way to keep data in memory. Example: a list, a dictionary.
- An **algorithm** is a list of steps to solve a problem. Example: "look at every number and remember the biggest".

All code in these files is Python 3.9. Every code block was run before it was written here.

---

## Part 1. How to read a coding problem

A coding problem looks like a story. Your job is to turn the story into three things:

1. **Input**: what do I get? (a list of numbers? a string? a tree?)
2. **Output**: what must I give back? (one number? yes/no? a new list?)
3. **Rules**: what is allowed, and how big can the input be?

### Read it three times

- **First read**: understand the story. Say it in your own words.
- **Second read**: underline the exact words. Words like "sorted", "contiguous", "at most", "exactly", "return the index", "in place".
- **Third read**: look at the limits. "n up to 10^5" tells you which speed is needed (see Part 3).

### Small words that change everything

| Word in problem | What it means |
|---|---|
| sorted | Order is given. Maybe you can use two pointers or binary search. |
| contiguous / subarray / substring | Items must sit next to each other. Often sliding window. |
| subsequence | Items keep order but can have gaps between them. |
| in place | Change the same list. Do not make a new big list. |
| O(1) extra space | Only a few variables are allowed. |
| distinct / unique | No repeats. Often a set. |
| return the indices | Give positions, not values. |
| at most k / at least k | A limit. Check the "equal to k" case carefully. |

---

## Part 2. The 5-step method (use it on EVERY problem)

Use this order every time. In a real interview, say each step out loud.

```text
STEP 1  UNDERSTAND   -> repeat the problem in your own words. Ask questions.
STEP 2  EXAMPLES     -> draw 2 small examples by hand + 1 edge case.
STEP 3  BRUTE FORCE  -> say the simple slow way. Say how slow it is.
STEP 4  IMPROVE      -> find the waste in brute force. Fix it with a pattern.
STEP 5  TEST         -> run your code by hand on an example. Then on edge cases.
```

### Step 1. Understand

Ask the interviewer small questions. This is allowed and good. Examples:

- "Can the list be empty?"
- "Can numbers be negative?"
- "Are there duplicates?"
- "If there are many answers, may I return any one?"

Good questions show that you think like an engineer.

### Step 2. Examples

Take a small input. Solve it with your hands, like a human. Write it on paper.
Notice what YOU did. Your brain already has an algorithm. Your task is to copy it into code.

Then add an **edge case**. An edge case is a strange input at the border:
empty list, one item, all items the same, very large numbers.

### Step 3. Brute force

Brute force means "try everything". It is slow but it is usually easy.
Always say it first. Reasons:

- It shows the interviewer you can solve the problem at all.
- It gives you a correct answer to compare with later.
- The slowness of brute force shows you what to fix.

Say the cost in Big-O words. Example: "Brute force checks every pair. That is O(n^2)."

### Step 4. Improve

Ask: "Where does brute force repeat work?" Then pick a tool:

| If brute force... | Try |
|---|---|
| looks up "have I seen this?" again and again | hash map or set (lesson 02) |
| checks all pairs in a sorted list | two pointers (lesson 03) |
| recomputes a window sum again and again | sliding window (lesson 04) |
| asks "what is the next bigger item?" | monotonic stack (lesson 05) |
| searches a sorted or yes/no-ordered range | binary search (lesson 06) |
| needs fast insert/delete in the middle | linked list (lesson 07) |
| has a parent-child shape | tree and recursion (lesson 08) |

### Step 5. Test

Before you say "done", do these things:

1. Walk through your code line by line with the small example. Write the variables down.
2. Try the empty input and the one-item input.
3. Say the time and space cost.

Many people lose a good interview here. They write code and say "done". Always test.

---

## Part 3. Big-O explained with real life

**Big-O answers one question: "If the input gets 10 times bigger, how much slower does my code get?"**

We use the letter `n` for the size of the input.

### Real-life examples

| Big-O | Name | Real-life picture |
|---|---|---|
| O(1) | constant | You open the first page of a book. Same work for a 10-page or a 1000-page book. |
| O(log n) | logarithmic | You look for a word in a paper dictionary. You open the middle, then half, then half again. A 1000-page book needs about 10 openings. |
| O(n) | linear | You read a book from page 1 to the end to find a name. Twice the pages = twice the work. |
| O(n log n) | linearithmic | You sort a deck of cards smartly (good sorting algorithms). A bit more than reading all cards. |
| O(n^2) | quadratic | Every person in a room shakes hands with every other person. 10 people = 45 handshakes. 100 people = 4950. |
| O(2^n) | exponential | You write all the ways to pick a subset of friends for a party. Each new friend doubles the number of subsets. |

### The table: n versus number of steps

These are approximate counts of steps. Look at how fast the right columns grow.

| n | O(1) | O(log n) | O(n) | O(n log n) | O(n^2) | O(2^n) |
|---|---|---|---|---|---|---|
| 10 | 1 | about 3 | 10 | about 33 | 100 | 1,024 |
| 100 | 1 | about 7 | 100 | about 664 | 10,000 | about 1.3 x 10^30 (impossible) |
| 1,000 | 1 | about 10 | 1,000 | about 10,000 | 1,000,000 | impossible |
| 100,000 | 1 | about 17 | 100,000 | about 1.7 million | 10 billion (too slow) | impossible |
| 1,000,000 | 1 | about 20 | 1 million | about 20 million | 10^12 (too slow) | impossible |

### Rule of thumb: read the limit, choose the speed

A rough guide. A computer can do about 10 million to 100 million simple steps per second in Python. This is a rough guide, not an exact law.

| If n is up to | You can probably use |
|---|---|
| 10 to 20 | O(2^n) (try all subsets) |
| 1,000 | O(n^2) |
| 100,000 | O(n log n) or O(n) |
| 1,000,000 or more | O(n) or O(log n) |

### Run it yourself

This small program counts the steps of three styles. Run it and see.

```python
# Count how many steps three styles of code take for different n.
def steps_linear(n):
    count = 0                      # start counting at zero
    for _ in range(n):             # one loop over n items
        count += 1                 # one step per item
    return count                   # total steps

def steps_quadratic(n):
    count = 0                      # start counting at zero
    for _ in range(n):             # outer loop: n times
        for _ in range(n):         # inner loop: n times for each outer step
            count += 1             # one step
    return count                   # total steps

def steps_log(n):
    count = 0                      # start counting at zero
    while n > 1:                   # keep going while more than 1 item is left
        n = n // 2                 # cut the work in half each time
        count += 1                 # one step per halving
    return count                   # total steps

for n in [10, 100, 1000]:                      # try three sizes
    print(n, steps_linear(n), steps_quadratic(n), steps_log(n))  # show all three counts
assert steps_linear(100) == 100                # linear = n
assert steps_quadratic(100) == 10000           # quadratic = n * n
assert steps_log(1000) == 9                    # about log2(1000) (it is 9 whole halvings)
```

### How to find the Big-O of your code (3 simple rules)

1. **One loop over n items = O(n).**
2. **A loop inside a loop = multiply: O(n) x O(n) = O(n^2).**
3. **Two loops one after the other = add: O(n) + O(n) = O(2n), and we drop the 2. It is O(n).**

We drop small things. O(3n + 5) is just O(n). O(n^2 + n) is just O(n^2). The biggest part wins.

### Time and space

- **Time complexity** = how many steps.
- **Space complexity** = how much extra memory. The input itself does not count. Only the new things you create (a new list, a dictionary, recursion calls).

### Python cost cheat sheet (very useful)

| Operation | Cost |
|---|---|
| `lst[i]` read by index | O(1) |
| `lst.append(x)` | O(1) (on average) |
| `lst.pop()` (last item) | O(1) |
| `lst.pop(0)` or `lst.insert(0, x)` | **O(n)** (everything shifts) |
| `x in lst` | **O(n)** (looks at each item) |
| `x in set` or `x in dict` | O(1) (on average) |
| `lst.sort()` or `sorted(lst)` | O(n log n) |
| `s1 + s2` strings | O(length of both) (strings are copied) |
| `lst[a:b]` slice | O(b - a) (it makes a copy) |
| `collections.deque.popleft()` | O(1) |

Two common traps: `x in list` inside a loop (hidden O(n^2)), and slicing inside a loop (hidden copy).

---

## Part 4. How Google and Amazon coding rounds work (2026)

**Honest note.** Neither company publishes a full official description of its coding rounds. Most details below come from interview-prep websites and candidate reports. I mark each claim as official (from the company site) or reported (from third parties). Formats change, and your recruiter has the final word. Ask your recruiter exactly what your rounds will be.

### Amazon

**Official (Amazon's own pages):**

- Amazon's hiring pages list four steps for many roles: online application, assessments, phone screening, interview loop. The process varies by role. Source: [Interviewing at Amazon](https://www.amazon.jobs/en/landing_pages/interviewing-at-amazon).
- Amazon's page of software development interview topics lists these areas: programming language, data structures, algorithms, coding, object-oriented design, databases, distributed computing, operating systems, internet topics, and general machine learning and AI. It says interviewers want to see you apply what you know to solve problems "efficiently and effectively". It also advises practising coding outside an IDE. Source: [Amazon Software Development Interview Topics](https://amazon.jobs/content/en/how-we-hire/interview-prep/software-development-topics).
- Amazon has an online assessment prep page for SDE II with a coding section. Source: [Online Assessment Prep: SDE II](https://amazon.jobs/content/en/how-we-hire/sde-ii-oa-prep).
- Amazon's page on in-person interviews says you meet employees one by one in an "interview loop", and each interviewer looks at different skills. Source: [Amazon interview page](https://www.amazon.jobs/en/landing_pages/in-person-interview).

**Reported (third-party, treat as approximate):**

- One prep newsletter describes a recruiter screen, a phone screen, then a five-round loop for SDE candidates, with two coding rounds of one LeetCode-style problem each (the first usually medium, the second often harder), a behavioural round, and a "Bar Raiser" round. It says the whole process often takes 4 to 8 weeks. Source: [dglearning Amazon 2026 loop](https://dglearning.substack.com/p/inside-the-amazon-2026-loop-rounds). The same article says the Bar Raiser is a trained interviewer from another team and that this person's "no-hire" cannot be overridden. This is that author's description, not an Amazon statement.
- Other guides agree on the shape (online assessment, phone screen, 4 to 5 round virtual loop with a Bar Raiser) and say coding is usually LeetCode medium level. Sources disagree on details such as the online assessment length. See the search results summarised from [codemia](https://codemia.io/guides/amazon-software-engineer) and [Simplify](https://simplify.jobs/blog/amazon-swe-interview-new-grads).
- Amazon's Leadership Principles (behavioural stories) matter in every round, according to many guides. One guide claims 2026 loops include a question about how you use AI tools. I only found this in one source, so I cannot call it confirmed.

What to do with this: practise medium problems. Practise explaining your thinking. Prepare behavioural stories (the STAR method: Situation, Task, Action, Result) for the coding rounds too, because behavioural questions can appear at the end of a coding round.

### Google

**Reported (I could not load Google's official interview page, so everything below is third-party):**

- A typical shape: recruiter screen, one or two technical phone screens, then a virtual onsite of about four to five interviews with coding, system design (usually from L4 up), and a "Googleyness" behavioural round. A hiring committee reviews feedback, then team matching happens. Source: [techprep Google interview process](https://www.techprep.app/blog/google-interview-process). Another summary of search results says the number of rounds differs by level and source (roughly 4 to 6 rounds in total). See [DEV Community guide](https://dev.to/feng_zhang_cedb4581bee881/google-software-engineer-interview-guide-2026-5f1e) and [Exponent](https://www.tryexponent.com/blog/google-interview-process).
- Coding rounds are about 45 minutes each. The same techprep article says you may write code in a shared Google Doc or a plain text editor, with no autocomplete, and explain your reasoning and the time and space cost aloud.
- **AI-assisted round (2026):** A prep article reports that Google is piloting a coding round where the candidate may use an approved AI assistant, for example to read, debug and speed up an existing codebase. This is based on press reports of an internal document. A Google spokesperson confirmed the pilot uses Google's own Gemini model. The pilot is reported to target junior and mid-level roles on selected US teams. Details are not officially confirmed. Source: [aced.io: Google AI coding interview](https://www.aced.io/blog/google-ai-coding-interview). Do not assume your rounds are AI-assisted. Ask your recruiter. Prepare for the classic format first.

What to do with this: be able to write correct Python without autocomplete. Say your thinking aloud. State time and space complexity every time. Test your code by hand at the end.

### Claims I could not verify

- Exact number of rounds for your level and team.
- Whether your Google round will be AI-assisted.
- Exact length and content of the Amazon online assessment in 2026.

---

## Part 5. Where problem tags come from

In lessons 01 to 08 each practice problem may carry the tag "Asked at: ...". I only add a company when I saw the problem on that company's list in this public community copy of LeetCode company tags: [liquidslr/leetcode-company-wise-problems](https://github.com/liquidslr/leetcode-company-wise-problems) (folders for Amazon, Google, Meta, Microsoft, Stripe). Being on the list means "candidates reported or LeetCode tagged it for that company". It does NOT mean the company will ask it to you. The Stripe list in that repo is very short (12 problems), so most problems have no Stripe tag.

## Part 6. A daily study habit that works

1. Read one lesson slowly. Do not rush. Trace the example on paper.
2. Type the template code yourself (do not copy-paste).
3. Solve the classic problems WITHOUT looking, then compare.
4. Next day, redo yesterday's hardest problem from memory.
5. Do 1 or 2 new problems from the practice list. Time yourself: 25 minutes, then look at hints.
6. Keep a notebook: problem name, pattern, the trick, what you got wrong.

When you are stuck for more than 20 minutes, read the idea only (not the code). Close it. Try again.

Next: [01_arrays_and_strings.md](01_arrays_and_strings.md)
