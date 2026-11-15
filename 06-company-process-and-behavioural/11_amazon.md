# 11. Amazon

Checked 15 Nov 2026. Amazon has official pages for this, so many facts below are [Official].

## A common 2026 situation
Many SDE candidates get an Amazon online assessment (OA). One reported version (November 2026): a 100-minute coding challenge that includes a repository question with an AI assistant, a work simulation, and work-style surveys.

**Important:** Amazon's official pages show different timings for different roles. Candidates report different versions. So: **the invitation email you receive is the truth.** Read it twice. Write down every timer.

---

## Part 1: The online assessment (OA), explained from zero

An OA is a test you do on your own, on a website, with no live person. Amazon uses it as the first filter.

### What the official pages say

[Official] SDE II OA page: https://amazon.jobs/content/en/how-we-hire/sde-ii-oa-prep
- Three sections plus an optional survey: **Coding**, **System Design**, **Work Styles**.
- Coding: **90 minutes, 2 questions**, in HackerRank. This is the only timed section. You must write real syntax, not pseudocode.
- System design: about 15 minutes. Work styles: about 10 minutes.
- Plan about 2 hours of quiet time.
- You usually get 7 days from the send date to finish. You hear within 2 days if you move on.
- If you do not advance, you can reapply after 6 months.
- That page does NOT say anything about AI tools, copy-paste or allowed resources.

[Official] University SDE OA page: https://amazon.jobs/content/en/how-we-hire/university/sde-oa
- Coding about 70 minutes, Workstyles about 15 minutes, Work Simulation about 60 minutes, feedback survey about 5 minutes.
- It says public online resources are allowed but warns against copy-pasting, and that your browser usage is logged. This is the university page, not your role. I mention it because it is the official page that names the work simulation.

Your invitation (100 minutes of coding + work simulation + work-style surveys) does not match either page exactly. That is normal. Amazon changes this often.

### What candidates report in 2026 [Anecdotal]
- One traditional algorithm problem plus one **repository task with an AI assistant**. Some candidates get an online VS Code style editor from HackerRank with a built-in AI assistant. Some get traditional-only versions. ([search summary of LeetCode, 1point3acres, PracHub posts](https://prachub.com/resources/amazon-ai-assisted-coding-oa-guide-2026-repository-bugs-ai-prompts-and-hidden-tests))
- Work simulation length is reported anywhere from about 15 to about 50 or 60 minutes. Work-style survey about 6 to 15 minutes. These conflict. Trust your invitation.
- A candidate guide says Amazon has published no scoring rules for the AI-repo format. Its list of what is probably judged is a guess, not a fact.

---

## Part 2: The repository question with an AI assistant

**Plain meaning:** You are given a small existing program (a "repository" or repo). It has bugs or a missing feature. There are tests. You must fix it, using an AI helper if the test allows. Think of it like being the new engineer who gets a messy project on day one.

**What candidates report [Anecdotal / Third-party, PracHub guide]:**
- Several bugs and a test suite. Some tests are visible, some may be hidden.
- Hidden tests probe edge cases: bad input, boundaries, repeated requests, permissions, regressions (old things breaking).
- The goal is to fix correct behaviour **without breaking other things**.
- The AI helper's name and power are not confirmed. Do not assume which one.

**A safe method you can follow (General advice, fits the guide's tips):**
1. **Read the task text slowly.** List what must change.
2. **Run the tests first.** Note which fail and why. Reproduce the failure before you ask the AI anything.
3. **Find the code path.** Start at the entry point (the function the test calls). Follow the data until the wrong value appears. You do this daily in platform work: it is the same as debugging a failing pipeline.
4. **Guess the cause in one sentence.** "I think the loop skips the last item."
5. **Ask the AI a narrow question.** Example: "In function X, why would input Y return Z? Show the smallest fix." Do not say "make all tests pass".
6. **Read every line the AI changes.** Do not paste blindly. You are responsible for the final code.
7. **Do not edit the tests** to match your code, unless the task says a test is wrong.
8. **Re-run the original failing test, then all tests, then try one extra edge case** (empty input, one item, very large input, duplicates).
9. **Keep time.** Leave 10 minutes at the end to re-run everything.

If the rules say "no AI" or you see a warning, follow the rules on screen.

## Part 3: The 100-minute coding part
- Possibly two problems (one normal algorithm, one repo). Split the time before you start, for example 40 minutes + 50 minutes + 10 minutes of buffer. Decide in the first 2 minutes. [General advice]
- Do the easier one first so you bank points.
- Write correct, readable code. Amazon's official SDE II interview page says interviewers look mainly for scalable, robust and well-tested code, and they check edge cases and bad input ([Official](https://amazon.jobs/content/en/how-we-hire/sde-ii-interview-prep)).
- Topics to refresh: arrays and strings, hash maps, sorting, two pointers, sliding window, stacks and queues, heaps, BFS and DFS on graphs and trees, binary search, basic dynamic programming.
- Use one language you know best. Write the brute-force version first if you are stuck, then improve.

## Part 4: Work simulation and work-style surveys

**Work-style survey (official):** Amazon says these ask you to pick how much a statement sounds like you. They connect to the Leadership Principles ([Official](https://amazon.jobs/content/en/how-we-hire/sde-ii-oa-prep); the earlier search summary of Amazon's assessment page says the same).
- Be honest and consistent. The same idea appears in different words. If you answer "I take quick decisions" in one place and "I always wait for full data" in another, it looks inconsistent.
- Read the 16 principles first. Many statements map to Ownership, Bias for Action, Customer Obsession, Dive Deep, Earn Trust.
- Do not try to guess one "perfect" answer. Answer how you really work.

**Work simulation (official description, per Amazon's assessment guidance):** virtual tasks that look like the real job, built around Leadership Principles. [Official, via search summary of Amazon's assessments page; I could not open the page itself.]
- What candidates report [Anecdotal]: you read emails or chat messages from "colleagues" and choose the best action, or rank options. Typical themes: customer problem, tight deadline, a teammate disagrees, unclear requirements.
- How to answer: pick the option that (1) puts the customer first, (2) takes ownership, (3) acts quickly but safely on reversible choices, (4) talks to people openly, (5) goes to the data before deciding.

## Part 5: What to do on the day (OA)
- Quiet room, charger, stable internet, a second device for water breaks only.
- Close other tabs. The browser may be logged.
- Do the practice or tutorial screen if any.
- Do not copy code from other sites.
- Submit every section. The official page says you must complete all sections to submit.

---

## Part 6: After the OA: the loop

[Official] SDE II interview prep page: https://amazon.jobs/content/en/how-we-hire/sde-ii-interview-prep
- **Four interviews of 55 minutes each**, with members of the software development community. Each interviewer checks different skills.
- Includes at least one **system design** question, **coding** (real code, not pseudocode), and **behavioural** questions that map to Leadership Principles. Each interviewer usually asks two or three questions about successes or challenges.
- No brain teasers.
- Results within 5 business days (official).
- The page does not mention the Bar Raiser.

[Official] Amazon's general guide says the loop is 4 to 6 interviews of 45 to 60 minutes. Technical roles spend about half on technical assessment. A **Bar Raiser** is "an objective interviewer from outside the hiring team" ([Amazon guide](https://www.aboutamazon.com/news/workplace/amazon-interview-guide)). Amazon's main "How we hire" page lists the stages as application, assessments, phone screening and interview loop (which includes Bar Raisers) ([Official](https://amazon.jobs/content/en/how-we-hire)).

**Bar Raiser, explained simply:** A trained interviewer from a different team. Their job is to protect the quality standard. Third-party guides say they can block a hire ([Aced](https://www.aced.io/blog/amazon-interview-process)). Candidate reports say their round is mostly behavioural and goes deep on one to three principles. Not every loop has one [Third-party]. A single Bengaluru report says the Bar Raiser was senior (SDE3+) [Anecdotal].

**Leadership Principles (LPs):** 16 rules about how Amazon wants people to behave. Amazon calls them the foundation of every hiring decision. All 16 are listed on Amazon's Leadership Principles page (see Sources).

**Every round, not only one, asks LP questions.** Prepare 8 to 10 stories. One story can serve several principles.

### Levels at Amazon
- Amazon levels: L4 = SDE I, L5 = SDE II, L6 = SDE III (senior). The SDE I/II/III names are Amazon's. The L numbers are widely used. I could not confirm the mapping on an official page.
- Levels.fyi (crowd-sourced, US): L4 typical 1 to 2 years, L5 typical 6 to 7 years, L6 11 to 13 years ([Levels.fyi Amazon](https://www.levels.fyi/companies/amazon/salaries/software-engineer)) [Third-party].
- Candidates in India report SDE II loops with about 3 to 4 years of experience, for example posts titled "Exp 3 to 4 yrs" and "3.3 YOE" (2026) ([LeetCode](https://leetcode.com/discuss/post/8420230/amazon-sde-2-interview-experience-2026-e-t1g8/), [LeetCode](https://leetcode.com/discuss/post/8512004/amazon-sde2-interview-experience-oa-phon-jhvj/)) [Anecdotal]. So SDE II looks like a realistic target for your 3.5 years. The recruiter decides the level, not you.

### India vs abroad
- I could not find an official page about relocation or visas for Amazon roles in the Netherlands, Ireland or Germany. Ask the recruiter. Country visa rules are in file 15.
- The OA and loop format is the same style across countries as far as I can tell, but I could not verify that.

### Behavioural AI-use question
A single Substack says every Amazon loop in 2026 has a question about AI tool use ([dglearning](https://dglearning.substack.com/p/inside-the-amazon-2026-loop-rounds)). It is one source. Still, have one honest example of using AI in your work (what you used it for, how you checked it).

---

## Part 7: A 5-day plan before the OA (General advice)
- **Day 1:** Read the invitation. Do 2 timed LeetCode mediums.
- **Day 2:** Practise a repo-debugging task: take any small open-source project, break a function, find the bug with tests. Practise using an AI assistant with narrow questions.
- **Day 3:** Read all 16 Leadership Principles on Amazon's page (linked below). Write 6 short stories using the STAR method.
- **Day 4:** 2 more timed mediums. Review mistakes.
- **Day 5:** Light revision. Sleep. Test your setup.

## Sources
- Amazon SDE II OA prep [Official]: https://amazon.jobs/content/en/how-we-hire/sde-ii-oa-prep
- Amazon SDE II interview prep [Official]: https://amazon.jobs/content/en/how-we-hire/sde-ii-interview-prep
- Amazon university SDE OA [Official]: https://amazon.jobs/content/en/how-we-hire/university/sde-oa
- Amazon How we hire [Official]: https://amazon.jobs/content/en/how-we-hire
- Amazon interview guide [Official]: https://www.aboutamazon.com/news/workplace/amazon-interview-guide
- Amazon Leadership Principles [Official]: https://www.amazon.jobs/content/en/our-workplace/leadership-principles
- PracHub AI-assisted OA guide [Third-party/anecdotal]: https://prachub.com/resources/amazon-ai-assisted-coding-oa-guide-2026-repository-bugs-ai-prompts-and-hidden-tests
- Aced Amazon process [Third-party]: https://www.aced.io/blog/amazon-interview-process
- Levels.fyi Amazon [Third-party]: https://www.levels.fyi/companies/amazon/salaries/software-engineer
