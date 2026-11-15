# 12. Stripe

Checked 15 Nov 2026. Stripe's own pages say little about its interview steps. Most of the detail is [Anecdotal]. I label everything.

## What Stripe says itself

- Stripe's careers page says most processes include a **recruiter screen**, a **technical or skills-based assessment**, and **a series of interviews with the team you would join**. Timelines vary by role, level and location. [Official, from a search summary of https://stripe.com/careers. I could not open the page myself.]
- Stripe job posts say the interview process is **language agnostic**: use any language you like [Official, from search summary of Stripe job listings, for example https://stripe.com/careers/listing/software-engineer-core-technology/7618977].
- Stripe's old engineering guide (about 8 years old) says one interview is a practical session: you and the interviewer sit side by side and solve a **real, past bug from an open-source project** in your favourite language. It says questions try to see how people solve real problems, not whiteboard tricks. It also says interviewers use written rubrics (marking guides), and recruiters give personal feedback to candidates who are rejected. [Official but old: https://stripe.com/guides/atlas/scaling-eng]
- I could not verify Stripe's current policy on AI tools in interviews. **Ask your recruiter.**

## What candidates report

[Anecdotal] unless stated. Sources: [NodeFlair summary of 273 interviews](https://nodeflair.com/blog/stripe-software-engineer-interview-questions-and-process) (I could not open it; the points below are from a search summary of several guides), [Taro](https://www.jointaro.com/interviews/companies/stripe/experiences/software-engineer-bengaluru-karnataka-january-29-2026-no-offer-positive-7cb602f0/), [Glassdoor Bengaluru, Mar 2026](https://www.glassdoor.com.br/Entrevista/Stripe-Entrevista-E671932-RVW103389192.htm).

### Bengaluru reports (2025 and 2026, small samples)
- **Online assessment:** 60 minutes on HackerRank, one implementation-heavy problem, for example simulating transactions.
- **Tech screen:** 45 minutes, 3 to 4 problems that are linked to each other (each builds on the last).
- **Debugging round:** open-source repo, find and fix bugs in about an hour.
- **A March 2026 report:** test and screening, behavioural interview, a technical SQL round, a reconciliation-focused technical round, and a hiring manager discussion.
- Candidate mood is mixed. One said interviewers felt rushed. One got an automated rejection.

### Global reports of the loop
Guides describe a loop with some of these rounds:
- **Bug squash / bug bash:** you get unfamiliar code (often an open-source project) and a bug. One candidate said the interviewer did not expect the bug to be solved; they wanted to hear a steady stream of thinking.
- **Integration:** you work against a real API or integrate a library, not LeetCode-style puzzles.
- **System design:** often about payments: API contracts, idempotency, error handling.
- **Behavioural:** usually with the hiring manager.
- Other names in guides: Design and Implementation, Refactoring, Pair Programming.

## The words, explained from zero

- **Bug squash:** Find and fix a bug in code you did not write. Daily life example: your friend's bike is making a noise and you must find the cause in 20 minutes with the tools on the table. Steps: reproduce, read, guess, test, fix.
- **Integration round:** Make two things talk to each other. For example, call a payment API correctly: read the docs, send a request, handle errors, handle retries.
- **Idempotency:** If the same request is sent twice, the result is the same as sending it once. Example: pressing "pay" twice must charge only once. This is a favourite Stripe idea because double charging is bad. Platform link: running the same Terraform or Helm command twice should leave the system in the same state.
- **Reconciliation:** Matching two lists of records to find differences. Example: matching bank statement lines against your own payment records.
- **Ledger:** A record of every money movement. Rows are only added, never changed.

## How Stripe differs (from the sources above)
- Less "pure puzzle", more "real work": reading unfamiliar code, using real APIs. [Anecdotal and the official old guide]
- Payments flavour in design questions. [Anecdotal]
- Communication counts. Say what you are thinking. [Anecdotal]
- Very selective: one dataset of 45 interviews reported a 13% pass rate. It is a single source, treat with care. [Anecdotal]

## How to prepare (General advice)
1. **Bug practice:** take a small open-source repo. Pick a closed bug issue. Try to find the fix before reading the real fix. Do this 3 times, 45 minutes each.
2. **Read APIs fast:** read Stripe's public API docs (https://docs.stripe.com) for the Payment Intents and idempotency pages. Understand what idempotency keys are.
3. **System design:** practise a payment system, a rate limiter, a webhook delivery system (retries, signatures, ordering).
4. **Behavioural:** stories about ownership and care for users. Your shared auth library (four languages, many services) and your CI/CD hub (10+ services) show "building for other engineers".
5. **SQL:** one March 2026 Bengaluru report mentions a SQL round. Refresh joins, group by, window functions.
6. **Recruiter call:** ask "Is AI allowed? Which languages? Which rounds will I have?"

## Sources
- Stripe careers [Official]: https://stripe.com/careers
- Stripe scaling engineering guide (old) [Official]: https://stripe.com/guides/atlas/scaling-eng
- NodeFlair [Third-party]: https://nodeflair.com/blog/stripe-software-engineer-interview-questions-and-process
- Taro Bengaluru Jan 2026 [Anecdotal]: https://www.jointaro.com/interviews/companies/stripe/experiences/software-engineer-bengaluru-karnataka-january-29-2026-no-offer-positive-7cb602f0/
- Glassdoor Bengaluru Mar 2026 [Anecdotal]: https://www.glassdoor.com.br/Entrevista/Stripe-Entrevista-E671932-RVW103389192.htm
