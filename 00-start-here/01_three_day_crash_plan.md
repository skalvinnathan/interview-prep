# Three-day crash plan (backend engineer: Google and Stripe style loops)

This page is a route through the lessons on this site. It adds no new theory.
It tells you what to read, what to type, in what order, and when to stop.

Labels used here: **[Official]** = the company's own pages. **[Third-party]** = prep sites and candidate reports. **[General advice]** = my own suggestion.

---

## Read this first: what three days can and cannot do

- **Can do:** learn 7 patterns well enough to solve easy and some medium problems, learn one routine you follow on every problem, explain two system designs, and answer basic Linux and Kubernetes questions.
- **Cannot do:** make a beginner fluent at hard graph problems or dynamic programming. One prep site says plainly that a week is not enough from zero and suggests asking for 2 to 3 more weeks **[Third-party: Exponent]**.
- **So the best single move is to ask for time.** A recruiter call usually comes before any technical round. On that call, ask for 2 to 4 weeks before the technical screen. Recruiters hear this every day **[General advice]**.
- Treat these three days as the base. Repeat them, then continue with the lessons you skipped.

## The rules for all three days

1. **No AI and no autocomplete while you practise.** Google bans AI tools in interviews **[Official]**. Reports on Stripe conflict, so assume none unless the recruiter says otherwise in writing **[Third-party]**.
2. **Type every solution yourself.** Reading code teaches almost nothing. Typing it from memory does.
3. **Use a timer.** 30 minutes per problem. If you are stuck after 20 minutes, read the solution in the lesson, close it, and type it again from memory.
4. **Talk out loud while you code.** Both companies grade how you think, not only the answer **[Official: Google interview tips; Third-party: Stripe reports]**.
5. **Keep a "failed" list.** Every problem you could not solve alone goes on it. Redo the list each morning.
6. **Follow the same six steps on every problem** (from [how to start](../01-dsa/00_how_to_start.md)):
   1. Say the problem back in your own words and ask two questions.
   2. Work one small example by hand.
   3. Say the slow, obvious way first.
   4. Say the faster way and why it is faster.
   5. Write the code.
   6. Test it by hand on your example and one edge case, then say the time and space cost.

## Two practice modes (they are different on purpose)

| | Google style | Stripe style |
|---|---|---|
| Problem | Short algorithm puzzle | Practical, multi-part task (parse, validate, total up) |
| Where you write | Plain document, **code does not run** **[Third-party]** | Your own editor, **code must run** **[Third-party]** |
| What counts most | Thinking out loud, correct logic, hand testing, Big-O | Working code, small tests, clear names, handling bad input |
| How to practise | Google Doc or plain text file, no running | VS Code or any editor, run it, write 3 small tests |

---

## Day 1: arrays, strings, hash maps, windows, sorting, binary search

About 8 hours. Take a 10-minute break between blocks.

| Block | Time | Read | Then type these (search the name on LeetCode) |
|---|---|---|---|
| 1 | 1 h | [How to start](../01-dsa/00_how_to_start.md): the method and Big-O | Write the six steps on paper. Keep it next to you. |
| 2 | 2 h | [Arrays and strings](../01-dsa/01_arrays_and_strings.md), [Hash maps and sets](../01-dsa/02_hash_maps_and_sets.md) | Two Sum, Valid Anagram, Group Anagrams |
| 3 | 2 h | [Two pointers](../01-dsa/03_two_pointers.md), [Sliding window](../01-dsa/04_sliding_window.md) | Valid Palindrome, Best Time to Buy and Sell Stock, Longest Substring Without Repeating Characters |
| 4 | 1.5 h | [Intervals](../01-dsa/13_intervals.md) | Merge Intervals, Meeting Rooms |
| 5 | 1 h | [Binary search](../01-dsa/06_binary_search.md) | Binary Search, First Bad Version |
| Evening | 30 min | Your own career story | Say a 60-second "who I am and what I built" out loud, three times. |

**Done when:** you can type Two Sum and Merge Intervals from a blank page in under 10 minutes each, and say why each is the speed it is.

## Day 2: trees, graphs, heaps, then Stripe-style tasks

| Block | Time | Read | Then type these |
|---|---|---|---|
| 0 | 20 min | Your failed list | Redo yesterday's failed problems from a blank page. |
| 1 | 2 h | [Trees](../01-dsa/08_trees_and_bst.md) | Maximum Depth of Binary Tree, Invert Binary Tree, Binary Tree Level Order Traversal |
| 2 | 2 h | [Graphs: BFS and DFS](../01-dsa/10_graphs_bfs_dfs.md) | Number of Islands, Flood Fill, Rotting Oranges |
| 3 | 1 h | [Heaps](../01-dsa/09_heaps_and_priority_queues.md) | Kth Largest Element in an Array, Top K Frequent Elements |
| 4 | 2.5 h | The three tasks below | Stripe mode: run the code and write tests. |
| Evening | 30 min | Behavioural basics | Write three stories in Situation, Task, Action, Result form: one win, one failure, one conflict. |

### Three Stripe-style tasks (themes candidates report **[Third-party]**)

Do them in your own editor. Each has parts. Finish part 1 fully, with tests, before reading part 2.

**Task A: balances from transactions.**
1. You get lines like `alice,bob,25.50` (payer, receiver, amount). Print each person's final balance.
2. Skip bad lines (missing field, amount that is not a number, negative amount) and count how many you skipped.
3. Print the fewest payments that would settle everyone back to zero.

**Task B: rate limiter.**
1. Write `allow(user_id, timestamp)` that returns False when the user has made more than 5 calls in the last 60 seconds.
2. Make the limit and the window settings, not fixed numbers.
3. Explain what breaks if two servers each run their own copy. Compare with [the rate limiter class](../03-low-level-design/16_rate_limiter_class.md).

**Task C: currency conversion.**
1. You get rates like `USD,EUR,0.9`. Write `convert("USD", "INR", 100)` when a direct rate exists.
2. Make it work through one or more middle currencies. This is BFS from Day 2, block 2.
3. Return the best rate, not just any rate.

**Done when:** Number of Islands is on paper from memory, and Task A parts 1 and 2 run with tests.

## Day 3: system design, Linux, Kubernetes, then a mock

| Block | Time | Read | Then do |
|---|---|---|---|
| 0 | 20 min | Your failed list | Redo. |
| 1 | 2.5 h | [How the round works](../02-system-design/00_how_the_round_works.md), [Load balancers](../02-system-design/01c_load_balancers.md), [Databases](../02-system-design/01d_databases.md), [Caching](../02-system-design/01e_caching.md), [Queues](../02-system-design/01g_message_queues_and_streams.md), [Consistency](../02-system-design/01h_consistency_and_cap.md) | For each page, write three lines: what it is, when to use it, what goes wrong. |
| 2 | 1.5 h | [Rate limiter](../02-system-design/11_rate_limiter.md), [Payment system](../02-system-design/18_payment_system_like_stripe.md) | Set a 20-minute timer. Explain the payment design out loud to an empty room. Use the word "idempotency key" and say what it protects against. |
| 3 | 1.5 h | [Linux](../05-devops-platform-basics/01_linux_processes_memory_files.md), [Networking](../05-devops-platform-basics/02_networking.md) | Answer out loud: what happens when you type a URL and press Enter? |
| 4 | 1.5 h | [Kubernetes from zero](../05-devops-platform-basics/04_kubernetes_from_zero.md), [Questions with answers](../05-devops-platform-basics/20_interview_questions_with_answers.md) | Cover the answers. Say yours first. Mark the ones you miss. |
| 5 | 1.5 h | Mock | One Day 1 problem in a plain document, 35 minutes, talking out loud, no running. Then Task B from Day 2 again from blank, 40 minutes, with tests. |
| Evening | 30 min | [Questions to ask](../06-company-process-and-behavioural/24_questions_to_ask_interviewers.md), [Day checklist](../06-company-process-and-behavioural/26_interview_day_checklists.md), [System design cheat sheet](../02-system-design/90_cheat_sheet.md) | Write your five questions for the recruiter. |

**Done when:** you can draw the payment system from memory and explain a pod, a deployment and a service in one sentence each.

---

## What to skip for now

Dynamic programming, backtracking, tries, union-find, shortest paths, bit tricks. One count of Google mock interviews puts arrays, strings, trees and graphs far ahead of these **[Third-party: interviewing.io]**, and a well-known study guide rates dynamic programming low priority when time is short **[Third-party: Tech Interview Handbook]**. No source gives exact percentages for Google, so treat this as a ranking, not a guarantee.

## What each company's later rounds look like

**Google (Software Engineer III, level L4) [Third-party unless marked]**
- One technical phone screen, 45 to 60 minutes: one medium problem or two short ones.
- Then two or three coding rounds and one behavioural ("Googleyness") round. Google itself only says "a panel of interviews" scored with "clear rubrics" **[Official]**.
- Sources disagree on whether L4 gets a system design round, and on whether you type in a Google Doc or Google's own interview editor. All agree the code does not run.
- Infrastructure teams sometimes swap one coding round for a domain round. No source shows a Kubernetes or Linux round at L4.

**Stripe (backend) [Third-party; I could not load Stripe's own pages]**
- 30-minute recruiter call, then a technical screen of about 60 minutes with one practical multi-part task.
- Onsite of four or five rounds: coding, bug squash (fix a bug in code you have never seen), integration (use an API from its documentation), system design, and a behavioural round.
- Design themes reported: rate limiter, payment processing, webhook delivery with retries, ledger. Idempotency comes up often.
- More detail: [Stripe page](../06-company-process-and-behavioural/12_stripe.md), [Google page](../06-company-process-and-behavioural/10_google.md).

## Questions to ask the recruiter

- How many rounds are there, and what is each one?
- How long do I have before the technical screen? Can I have two to four weeks?
- Which editor will I use? Will the code run?
- Which languages are allowed?
- Are AI tools or web search allowed? (Ask Stripe to confirm in writing.)
- Is there a system design round or a domain round at my level?
- Does team matching happen before or after the hiring committee? (Google)

## After the three days

1. Repeat Day 1 and Day 2 problems until none are on the failed list.
2. Add [stacks and queues](../01-dsa/05_stack_and_queue.md), [linked lists](../01-dsa/07_linked_lists.md) and [topological sort](../01-dsa/11_topological_sort_and_union_find.md).
3. Do one Google-mode problem and one Stripe-mode task every day.
4. For Stripe's bug squash: clone a small open-source Python project, pick a closed bug report, and try to find the fix yourself in 45 minutes.
5. Only then start [dynamic programming](../01-dsa/15_dynamic_programming_part1.md).

## Sources

- Google, How we hire: https://www.google.com/about/careers/applications/how-we-hire/
- Google, Interview tips: https://www.google.com/about/careers/applications/interview-tips/
- interviewing.io, Google hiring process: https://interviewing.io/guides/hiring-process/google
- Hello Interview, Google L4: https://www.hellointerview.com/guides/google/l4
- Prepfully, Google phone screen: https://prepfully.com/interview-guides/google-software-engineer-technical-phone-screen
- Tech Interview Handbook, study plan: https://www.techinterviewhandbook.org/coding-interview-study-plan/
- Aced, last-minute prep: https://www.aced.io/blog/last-minute-coding-interview-prep
- Aced, Stripe software engineer interview: https://www.aced.io/guides/stripe-software-engineer-interview
- interviewing.io, Stripe: https://interviewing.io/stripe-interview-questions
- Exponent, Stripe process: https://www.tryexponent.com/blog/stripe-interview-process
- Exponent, Stripe system design: https://www.tryexponent.com/blog/stripe-system-design-interview
