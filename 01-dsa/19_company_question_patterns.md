# Lesson 19: Company Question Patterns (Google, Amazon, Meta, Stripe, Microsoft) and a 4-Week Plan

Written on 2026-11-15 from public web pages. Every claim has a source link. Where I could not verify something, I say so in plain words.

**How to read this file.**
- "Verified" means I opened the page and read it myself.
- "Seen only in search results" means a search result summary said it, but I did not open the page, or the page blocked me. Treat it as a hint, not a fact.
- All interview experience posts are one person's story. Companies change their process. **Always ask your recruiter what your exact loop will be.**

---

## 1. The honest limits (read this first)

1. **LeetCode's own company tag pages need a paid account.** I did not use them. Instead I read a public GitHub copy of those lists: [liquidslr/leetcode-company-wise-problems](https://github.com/liquidslr/leetcode-company-wise-problems). Its page shows two dates ("Updated as of 20 Oct, 2025" and a README line "updated as of 1 June 2025"), so the data is about a year old, not "2026".
2. **The "frequency" number in those files is a relative score** (the top row is 100). The repo does not explain how it is computed. A big number means "tagged many times by LeetCode users", not "Google asks this every week".
3. **The lists contain some noise.** For example, the Google list ranks "Create Hello World Function" very high. That is a tagging effect, not a sign of what Google asks in a coding round.
4. **I read the CSV files through a page-summary tool**, not by opening a spreadsheet. The titles and numbers below were copied from its output. Spot-check any single row on GitHub before you rely on it.
5. **2026 interview experiences** come from forums and prep sites (LeetCode Discuss, PracHub, Glassdoor, blogs). Many prep sites sell products. I name which are first-person reports and which are guides.

---

## 2. Which patterns each company asks most

I looked at the top rows of each company's "all time" list (the file named `5. All.csv` in each company folder) and sorted the problems into the patterns from lessons 01 to 18. This grouping is **my own reading** of those rows. It is not an official statement and not a statistic.

### 2.1 Google

Rows I read (top of the list, relative frequency in brackets): Two Sum (100), Add Two Numbers (78.6), Median of Two Sorted Arrays (74.3), Trapping Rain Water (73.5), 3Sum (72.8), Longest Substring Without Repeating Characters (72.6), Best Time to Buy and Sell Stock (71.9), Longest Consecutive Sequence (70.8), Container With Most Water (68.4), Subarray Sum Equals K (65.8), Merge Intervals (64.8), Number of Islands (64.1), Climbing Stairs (62.8), Generate Parentheses (61.5), Koko Eating Bananas (59.2), Top K Frequent Elements (58.6), N-Queens (58.5), Split Array Largest Sum (58.2).

Also in the Google list (lower down, from my look-ups): Meeting Rooms II (57.9), House Robber (57.4), Jump Game (55.8), Kth Largest Element (54.9), Subsets (52.2), Longest Increasing Subsequence (52.2), Course Schedule (51.4), Rotting Oranges (51.1), Find Median from Data Stream (50.5), Coin Change (48.1), Edit Distance (45.8), Word Break (43.8), Word Search (42.2), Word Ladder (41.5).

**Patterns, in the order they seem to matter:**
1. Arrays, strings and hash maps (lessons 01, 02).
2. Two pointers and sliding window (lessons 03, 04).
3. **Binary search**, including "binary search on the answer" (Koko, Split Array Largest Sum, Median of Two Sorted Arrays) (lesson 06).
4. Graphs on grids and graph search (lessons 10, 11).
5. Dynamic programming and backtracking (lessons 14, 15, 16).
6. Intervals and heaps (lessons 13, 09).

**What I could verify about the loop in 2026:**
- A guide describes two 45-minute coding rounds, then system design and a behavioural round, and a recruiter screen plus one or two phone screens before the onsite. The same page contains claims it does not source (timing, committee sizes) and it names no specific topics. Source: [dglearning, "Inside the Google 2026 Loop"](https://dglearning.substack.com/p/inside-the-google-2026-loop-rounds) (opened).
- A first-person report (Software Engineer, Canada, reported July 2026, no offer): recruiter screen, then a first round that mixed a "Googleyness" talk and a coding problem, then two more coding interviews, and **team matching only after** the coding rounds. It names no problems. Source: [PracHub report](https://prachub.com/interview-experiences/google-software-engineer-interview-recruiter-screen-and-four-linear-rounds-1356c8893d) (opened).
- A news article from 22 Aug 2025 says Google's CEO said Google will "definitely introduce at least one round" of in-person interviews for technical roles, because of AI-assisted cheating. The article links no primary source, so treat it as a report, not a Google announcement. Source: [trak.in article](https://trak.in/stories/google-brings-back-in-person-interviews-to-stop-ai-enabled-cheating/) (opened). **Ask your recruiter** whether your rounds are on-site or virtual.

**Not verified:** whether Google lets candidates use an AI tool in coding rounds. I saw this claimed only in a search summary, so I do not state it as fact.

### 2.2 Amazon

Rows I read (relative frequency in brackets): Two Sum (100), Trapping Rain Water (87.9), LRU Cache (87.9), Number of Islands (85.0), Longest Substring Without Repeating Characters (83.9), Best Time to Buy and Sell Stock (83.8), Group Anagrams (80.1), Reorganize String (78.0), Merge Intervals (76.4), Koko Eating Bananas (74.9), **Course Schedule (74.5)**, Subarray Sum Equals K (74.0), **Merge k Sorted Lists (73.5)**, **Rotting Oranges (73.3)**, Top K Frequent Elements (71.5), Copy List with Random Pointer (68.9), Word Ladder (67.1), House Robber (67.1), Sliding Window Maximum (66.4), Jump Game (65.7).

Also in the Amazon list (my look-ups): Word Search (64.7), Course Schedule II (64.7), Subsets (64.5), Coin Change (63.2), Find Median from Data Stream (63.2), Task Scheduler (62.4), Kth Largest Element (62.5), Meeting Rooms II (61.3), Unique Paths (60.5), Word Break (58.7).

**Patterns, in the order they seem to matter:**
1. Arrays, strings, hash maps, sliding window (lessons 01 to 04).
2. **Graph search on grids and prerequisites**: Number of Islands, Rotting Oranges, Course Schedule, Word Ladder (lessons 10, 11).
3. **Heaps / top-K / merge**: Reorganize String, Top K Frequent, Merge k Sorted Lists, Task Scheduler (lesson 09).
4. Design with a hash map and a linked list: LRU Cache, Copy List with Random Pointer (lesson 07).
5. Intervals, basic DP, backtracking (lessons 13, 14, 15).

**Amazon's online assessment (OA) in 2026, as far as I could verify.** Sources disagree on names and numbering, so use your invite email as the truth.
- The OA is commonly described as three parts: **coding** (two problems, about 70 to 90 minutes), a **Work Simulation** (about 50 minutes, a pretend inbox with multiple-choice and multi-select questions about prioritising and debugging, scored against Amazon's Leadership Principles, no coding), and a **Work Style Assessment** (about 15 to 20 minutes, a situational survey). Source: [Lodely guide](https://www.lodely.com/blog/amazon-online-assessment-2025) (opened). This is a commercial prep site and its numbers are its own claims.
- The same page says typical coding topics are arrays and hash maps, sliding window, intervals, trees, graph BFS/DFS, DP, two pointers, binary search, stacks, heaps and linked lists, with SDE I at easy-to-medium and SDE II at medium-to-hard. That matches the tag list above.
- A first-person blog says some candidates now get an **"AI Assisted Coding" OA**: an existing codebase (handlers, helpers, tests) with an AI assistant, where you find bugs and fix or improve the code, and hidden tests check edge cases. The author also promotes a paid prep service, and gives no time limit. Source: [DEV Community post](https://dev.to/net_programhelp_e160eef28/amazon-coding-oa-experience-pitfalls-guide-2026-latest-4885) (opened).
- Seen only in search results (the pages returned HTTP 403 for me): LeetCode Discuss posts about 2026 Amazon OAs, one saying an invite had one traditional coding problem plus one AI-assisted repo problem. Links for you to read yourself: [Amazon SDE Intern OA 2026](https://leetcode.com/discuss/post/8444926/amazon-sde-online-assessment-2026-recent-etbq/), [Amazon OA Experience, 9 October 2026](https://leetcode.com/discuss/post/8564893/amazon-oa-experience-9-october-2026-by-r-9907/).
- **Not verified:** which parts apply to experienced (SDE II) hires in India. One guide lists an extra 20-minute systems design section for SDE II, and I found that in a single source only.

### 2.3 Meta

Rows I read (relative frequency in brackets): Minimum Remove to Make Valid Parentheses (100), Valid Word Abbreviation (96.9), Valid Palindrome II (95.7), **Kth Largest Element in an Array (93.9)**, Binary Tree Vertical Order Traversal (93.6), Two Sum (92.9), Basic Calculator II (89.5), Subarray Sum Equals K (88.0), Lowest Common Ancestor of a Binary Tree III (88.0), Diameter of Binary Tree (87.9), Random Pick with Weight (87.0), Binary Tree Right Side View (86.2), Find Peak Element (86.1), Merge Intervals (84.7), Pow(x, n) (84.4), Valid Palindrome (83.8), Simplify Path (83.7), Top K Frequent Elements (82.3), **Shortest Path in Binary Matrix (80.2)**, LRU Cache (79.2), K Closest Points to Origin (76.6), Max Consecutive Ones III (75.8), Merge k Sorted Lists (75.6), Making A Large Island (74.1), Interval List Intersections (73.5), Minimum Window Substring (73.4).

**Patterns, in the order they seem to matter:**
1. **Strings and stack tricks** (valid parentheses variations, calculators, path simplifying) (lesson 05).
2. **Trees** (vertical order, LCA, diameter, right side view) (lesson 08).
3. Hash maps with prefix sums, binary search, two pointers (lessons 02, 03, 06).
4. Heaps and top-K (lesson 09).
5. BFS on grids (lesson 10), sliding window (lesson 04), intervals (lesson 13).

**What I could verify about the loop in 2026:**
- Many reports describe a **traditional coding round with two algorithm problems and no AI**, and a newer **AI-enabled coding round** in a CoderPad environment with an AI assistant, a multi-file project you did not write, runnable tests and one problem in several parts that build on each other (part 1 is often a bug fix). Evaluation areas listed: problem solving, code quality, verification and communication. Five 2026 reports on that page describe two AI-enabled coding rounds and no traditional one. The page's counts come from its own bank of 35 reports, and its dates are inconsistent, so treat the numbers as soft. Source: [PracHub, Meta AI coding interview](https://prachub.com/resources/meta-ai-coding-interview) (opened).
- **Not verified:** how often DP appears at Meta. The same page says "rarely" but rests that on two reports.

### 2.4 Stripe

Rows I read (all 12 rows of the Stripe list; relative frequency in brackets): Minimum Penalty for a Shop (100), Calculate Amount Paid in Taxes (97.2), Invalid Transactions (94.0), **Cheapest Flights Within K Stops (86.0)**, Brace Expansion (80.8), Merge Intervals (73.9), Parallel Courses III (64.3), One Edit Distance (64.3), Number of Black Blocks (64.3), Alert Using Same Key-Card Three or More Times in a One Hour Period (64.3), Simple Bank System (64.3), Next Permutation (64.3).

This list is tiny (12 rows), so do not draw strong conclusions. It leans towards **parsing and simulation of money, logs and transactions** (hash maps, sorting, strings), plus a few graph and interval problems.

**What I could verify about the loop:**
- Candidate reports from 2026 describe an online assessment, more coding, a **bug squash** round (debugging an existing codebase) and an **API integration** round, plus a behavioural round. Source: [PracHub report, Durham NC, July 2026, no offer](https://prachub.com/interview-experiences/stripe-software-engineer-interview-with-coding-bug-squash-api-integration-and-bq-rounds-cf992a00e3) (opened). The author felt later rounds tested practical debugging and API work, not isolated algorithm puzzles. Level not stated.
- A third-party guide says Stripe coding is **not LeetCode-style**: practical tasks like a rate limiter or parsing a billing file, extending or debugging a small codebase, and a payments-flavoured system design round. The guide cites no sources, so treat it as an opinion. Source: [techinterview.org Stripe guide](https://www.techinterview.org/companies/stripe/?format=md) (opened).
- **What this means for practice:** algorithms (lessons 01 to 18) still matter for the first assessment, but also practise reading unfamiliar code, writing small clean programs with tests, handling edge cases, and calling an API. Practice writing code that reads like a pull request: clear names, small functions, edge cases handled.

### 2.5 Microsoft

Rows I read (relative frequency in brackets): Two Sum (100), Add Two Numbers (81.6), Longest Substring Without Repeating Characters (80.0), Longest Palindromic Substring (79.9), Best Time to Buy and Sell Stock (78.0), Trapping Rain Water (77.9), LRU Cache (77.9), Median of Two Sorted Arrays (75.2), Subarray Sum Equals K (75.2), 3Sum (74.9), Maximum Subarray (74.8), Number of Islands (72.4), Merge Intervals (72.2), Valid Parentheses (72.0), Group Anagrams (70.0), Search in Rotated Sorted Array (68.7), Next Permutation (66.8), Spiral Matrix (66.6), Reverse Linked List (65.8), Merge k Sorted Lists (64.4), Product of Array Except Self (63.5).

**Patterns, in the order they seem to matter:**
1. Arrays, strings, hash maps, two pointers (lessons 01 to 03).
2. **Linked lists** (Add Two Numbers, Reverse Linked List, Merge k Sorted Lists) (lesson 07).
3. Matrix manipulation (Spiral Matrix, Rotate Image) and classic "next permutation" style problems.
4. DP basics, intervals, graph search (lessons 10, 13, 15).

**What I could verify about the loop in 2026:**
- A first-person report (Software Engineer, Cairo, July 2026, no offer): an online assessment, then two live coding interviews. The first was a medium binary-search problem and the second was graph problems. Source: [PracHub report](https://prachub.com/interview-experiences/microsoft-software-engineer-interview-experience-binary-search-first-then-graph-problems-b49aeafff0) (opened). This is one person; other reports mention extra system design rounds and an AI-assisted coding round (seen only in a search summary, not opened). One such report, if you want to read it yourself: [PracHub, Microsoft senior SWE, CoreAI loop with an AI coding round](https://prachub.com/interview-experiences/microsoft-senior-software-engineer-interview-experience-coreai-loop-with-an-ai-coding-round-after-11-loops-in-a-year) (I saw only its title in search results).
- **Not verified:** the exact rounds for your level and team. Microsoft loops vary a lot by team.

### 2.6 One table to remember

| Pattern | Google | Amazon | Meta | Stripe | Microsoft |
|---|---|---|---|---|---|
| Arrays, strings, hash maps | strong | strong | strong | some | strong |
| Two pointers / sliding window | strong | strong | strong | not seen | strong |
| Binary search (incl. on the answer) | strong | some | some | not seen | some |
| Stack, parentheses, calculators | some | some | **strong** | some (Brace Expansion) | some |
| Linked lists, LRU design | some | **strong** | some | not seen | **strong** |
| Trees | some | some | **strong** | not seen | some |
| Heaps, top-K, merge k | some | **strong** | strong | not seen | some |
| Graph search on grids, prerequisites | strong | **strong** | some | some | some |
| Intervals | strong | strong | strong | yes | strong |
| DP | some | some | less | some (edit distance) | some |
| Backtracking | some (N-Queens, parentheses) | some | less | some (Brace Expansion) | some |
| Code reading, debugging, API work | n/a | AI-assisted OA reported | AI-enabled round | **bug squash, integration** | AI round reported (unverified) |

"strong / some / less / not seen" is my reading of the top rows above plus the loop reports. It is a rough guide for where to spend time, not a measurement.

---

## 3. Google rounds in 2026: what to expect (short)

From the two sources I opened (see 2.1), plus clear caveats:
1. **Recruiter screen**, then **one or two coding phone screens**.
2. **Onsite loop of about four to five rounds** (guide) or "recruiter screen, coding rounds, Googleyness, team match" (first-person report). Mostly **45-minute rounds with one algorithm problem** and follow-ups, judged on understanding the problem, finding the pattern, correct code, stating complexity, talking while you think, and reacting to hints (this list is from the guide).
3. **A behavioural ("Googleyness") conversation**, possibly mixed into a coding round (as in the report).
4. **System design** is described in the guide as a round of its own. I could not verify at which levels it applies, so ask your recruiter.
5. **Team matching** happens after the interviews.
6. **On-site vs virtual**: reports of an in-person comeback exist (see 2.1), but I could not find a Google statement. Ask.

How to prepare for the algorithm rounds: the same patterns as in this folder. Practise saying your thinking out loud, always state time and space complexity at the end, and test your code with 2 edge cases by hand before you say "done".

---

## 4. A 4-week practice schedule (1.5 hours a day)

This plan is **mine**, built to go through lessons 01 to 18 in order. It is not taken from a website. The idea is simple: **one new problem a day, and redo an old one**. Repeating old problems from a blank page is what makes patterns stick.

**Every 90-minute day follows the same shape:**
| Minutes | What |
|---|---|
| 0 to 15 | Read the part of the lesson for the day. Close it. Write the template from memory on paper. |
| 15 to 60 | **One problem from the lesson.** Set a 35-minute timer first. Speak out loud: restate the problem, give the brute force and its cost, then the better idea, then code. |
| 60 to 75 | Compare with the lesson's solution. Write one line: "my mistake was ...". |
| 75 to 90 | **Redo from a blank page** the problem from 2 days ago (or the one you got wrong). |

Plan: 6 working days a week. Day 7 is a **mock** (or rest). If you miss a day, do not double up: skip the new problem and keep the redo.

Lessons 01 to 08 are written by another author in this folder (arrays, hash maps, two pointers, sliding window, stack and queue, binary search, linked lists, trees). I list them by topic.

### Week 1: the everyday tools (lessons 01 to 06)

| Day | Lesson and topic | Problem for the day |
|---|---|---|
| 1 | 01 Arrays | Best Time to Buy and Sell Stock, then Product of Array Except Self |
| 2 | 02 Hash maps | Two Sum, then Subarray Sum Equals K |
| 3 | 03 Two pointers | 3Sum, then Container With Most Water |
| 4 | 04 Sliding window | Longest Substring Without Repeating Characters |
| 5 | 05 Stack and queue | Valid Parentheses, then Minimum Remove to Make Valid Parentheses |
| 6 | 06 Binary search | Search in Rotated Sorted Array, then Koko Eating Bananas |
| 7 | Mock 1 (45 min, one medium, talk aloud) + review of mistakes | Pick one unseen medium from the same topics |

### Week 2: structures (lessons 07 to 10)

| Day | Lesson and topic | Problem for the day |
|---|---|---|
| 8 | 07 Linked lists | Reverse Linked List, then LRU Cache |
| 9 | 08 Trees | Diameter of Binary Tree, then Lowest Common Ancestor |
| 10 | 08 Trees (again) | Binary Tree Right Side View |
| 11 | 09 Heaps | Kth Largest Element in an Array, then Top K Frequent Elements |
| 12 | 10 Graphs (BFS, DFS) | Number of Islands |
| 13 | 10 Graphs (grids) | Rotting Oranges |
| 14 | Mock 2 (45 min, one medium graph or tree problem) | Clone Graph or a tree problem you have not seen |

### Week 3: harder patterns (lessons 11 to 14)

| Day | Lesson and topic | Problem for the day |
|---|---|---|
| 15 | 11 Topological sort | Course Schedule, then Course Schedule II |
| 16 | 11 Union-find | Number of Provinces, then Redundant Connection |
| 17 | 12 Shortest paths | Network Delay Time |
| 18 | 13 Intervals | Merge Intervals, then Meeting Rooms II |
| 19 | 14 Backtracking | Subsets, then Permutations |
| 20 | 14 Backtracking | Combination Sum, then Word Search |
| 21 | Mock 3: **Amazon OA style**. 70 minutes, two mediums, no hints, no looking at notes | Meeting Rooms II or Merge k Sorted Lists, plus Rotting Oranges |

### Week 4: DP, extras, and mocks (lessons 15 to 19)

| Day | Lesson and topic | Problem for the day |
|---|---|---|
| 22 | 15 DP part 1 | Climbing Stairs, then House Robber |
| 23 | 15 DP part 1 | Coin Change, then Unique Paths |
| 24 | 16 DP part 2 | Longest Increasing Subsequence, then Word Break |
| 25 | 16 DP part 2 | Edit Distance (draw the table by hand first) |
| 26 | 17 Tries and greedy | Implement Trie, then Jump Game |
| 27 | 18 Bits and math (short), then redo your three weakest problems of the month | Single Number, Pow(x, n) |
| 28 | **Final mocks**: one 45-minute Google-style round (one medium or hard, talk aloud) and write 3 behavioural stories (see below) | Pick an unseen problem from the practice lists in lessons 09 to 17 |

**Behavioural stories** (Amazon's work simulation and work-style parts are scored on its Leadership Principles; Google has a Googleyness conversation): write 3 stories from your own work, each in the form Situation, Task, Action, Result, with a number if you can. Reuse them across companies.

**For Stripe in particular:** twice in the month (for example days 10 and 20), replace your daily problem with a **practical task**: read a small open-source function you did not write and fix a bug in it, or write a small command-line program that parses a file and handles bad input, with tests. This matches the "bug squash" and "integration" rounds reported above.

**For Meta in particular:** once in week 4, practise with an AI assistant on: "here is a messy multi-file project with a failing test. Fix it, explain every change, and check the AI's code yourself." The round reportedly rewards checking and explaining.

---

## 5. What I could not verify (so you know)

- That the GitHub tag lists reflect what each company asks **today**. They are about a year old and the frequency score is not explained.
- How the Amazon OA is structured for **experienced hires in India** in late 2026. Guides disagree on part names and numbering. Check your invite.
- Whether Google allows AI help in coding rounds. Whether Google rounds are in person for your location.
- How often Meta and Microsoft ask DP. The numbers I saw rest on very few reports.
- Any pass-rate statistic. I saw one (a Stripe Bengaluru aggregate with 11 experiences) and did not use it, because the sample is too small.
- The two LeetCode Discuss pages about Amazon 2026 OAs (HTTP 403 for my tools). I list them as links only.

---

## 6. Sources

Opened and read by me:
- [liquidslr/leetcode-company-wise-problems (GitHub)](https://github.com/liquidslr/leetcode-company-wise-problems): company tag lists (Google, Amazon, Meta, Microsoft, Stripe `5. All.csv` files, read via the raw file links under that repo).
- [dglearning: Inside the Google 2026 Loop](https://dglearning.substack.com/p/inside-the-google-2026-loop-rounds)
- [PracHub: Google SE report (Canada, 2026)](https://prachub.com/interview-experiences/google-software-engineer-interview-recruiter-screen-and-four-linear-rounds-1356c8893d)
- [trak.in: Google in-person interviews article (22 Aug 2025)](https://trak.in/stories/google-brings-back-in-person-interviews-to-stop-ai-enabled-cheating/)
- [Lodely: Amazon Online Assessment 2026 guide](https://www.lodely.com/blog/amazon-online-assessment-2025)
- [DEV Community: Amazon coding OA experience and AI-assisted OA](https://dev.to/net_programhelp_e160eef28/amazon-coding-oa-experience-pitfalls-guide-2026-latest-4885)
- [PracHub: Meta AI-enabled coding interview](https://prachub.com/resources/meta-ai-coding-interview)
- [PracHub: Stripe SE report (coding, bug squash, API integration)](https://prachub.com/interview-experiences/stripe-software-engineer-interview-with-coding-bug-squash-api-integration-and-bq-rounds-cf992a00e3)
- [techinterview.org: Stripe interview guide](https://www.techinterview.org/companies/stripe/?format=md)
- [PracHub: Microsoft SE report (Cairo, 2026)](https://prachub.com/interview-experiences/microsoft-software-engineer-interview-experience-binary-search-first-then-graph-problems-b49aeafff0)

Seen only in search results (not opened, or blocked):
- [LeetCode Discuss: Amazon SDE Intern OA 2026](https://leetcode.com/discuss/post/8444926/amazon-sde-online-assessment-2026-recent-etbq/)
- [LeetCode Discuss: Amazon OA Experience, 9 October 2026](https://leetcode.com/discuss/post/8564893/amazon-oa-experience-9-october-2026-by-r-9907/)
- [PracHub: Microsoft senior SWE CoreAI loop with an AI coding round](https://prachub.com/interview-experiences/microsoft-senior-software-engineer-interview-experience-coreai-loop-with-an-ai-coding-round-after-11-loops-in-a-year)
