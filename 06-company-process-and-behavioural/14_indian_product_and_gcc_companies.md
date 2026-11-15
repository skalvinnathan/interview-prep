# 14. Indian product companies and GCCs

GCC = Global Capability Centre. It is the India office of a big foreign company (for example Walmart Global Tech, Intuit, Oracle, Mastercard, PayPal, Atlassian). It does real engineering work for the parent company.

Checked 15 Nov 2026. I found **no official** interview descriptions for these companies. Everything below is [Anecdotal] from Glassdoor, LeetCode and prep sites, mixed years and levels. **Confirm the format with your recruiter.** Where the reports disagree, I say so.

## Quick table (what usually appears)

| Company | Typical rounds reported | Notes |
|---|---|---|
| Walmart Global Tech | DSA, then design or LLD, then hiring manager | 3 to 4 rounds, 2 to 3 weeks |
| Intuit | Online test, DSA/LLD, a "craft" or project demo, hiring manager | Rounds can be on one day |
| Atlassian | Coding, system design, "craft"/leadership, values, manager | Values round carries weight |
| Oracle (OCI) | 3 to 4 technical rounds, then manager round | Java, Spring, DSA seen |
| Mastercard | 3 to 4 rounds, Java/Spring heavy | Fewer reports for 2026 |
| PayPal | DSA, 2 system design, hiring manager | Reported for Bengaluru MTS1 |
| Razorpay | 4 to 6 rounds incl. DSA and HLD | Machine coding unclear for backend |
| PhonePe | Machine coding/LLD, DSA, HLD, hiring manager | Machine coding is the big filter |

## Words explained
- **DSA:** data structures and algorithms (coding puzzles).
- **LLD:** low-level design. Write clean classes for a small system.
- **HLD:** high-level design. Draw the big system.
- **Machine coding:** a timed round (often 60 to 120 minutes) where you build a small working program (for example a parking lot or splitwise) on your own laptop or editor. It is judged on working code, clean structure and tests. Not only on the answer.
- **Hiring manager (HM) round:** the future boss digs into your past projects.
- **MTS / SMTS:** Member of Technical Staff, Senior MTS. These are titles at Oracle, PayPal and similar companies.

## One by one

### Walmart Global Tech (Bengaluru)
- Reports: a DSA round (medium LeetCode), then LLD and/or system design, then a hiring manager discussion. 3 to 4 rounds. A 2026 prep blog is similar but is a commercial source.
- No report mentions a named machine-coding round. LLD does appear.
- HM round: deep questions about your projects and resume.
- Sources: [Glassdoor reports](https://www.glassdoor.com/Interview/Walmart-Global-Tech-Interview-E3293060-RVW87440165.htm), [prep blog](https://claveprep.com/blog/walmart-global-tech-india-interview-preparation-2026).

### Intuit (Bengaluru)
- Reports: an online assessment of about an hour, one or more technical rounds (DSA, LLD, or an API/project task), a **craft** round (a demo of something you build, often UI-flavoured; one report says a weather app task), and a hiring manager round.
- Timeline reports range from 1 week to 2 months. Some candidates had all rounds on one day.
- One report mentions a Spring Boot development exercise (90 minutes) with a project shared in advance.
- Sources: [LeetCode Dec 2024](https://leetcode.com/discuss/interview-experience/6217757/), [1point3acres](https://www.1point3acres.com/interview/thread/1115789), [LeetCode accepted](https://leetcode.com/discuss/interview-experience/7079757).

### Atlassian (Bengaluru)
- Reports describe: application and some craft or coding assessment, recruiter screen, a virtual loop (coding, system design), a **leadership and craft** interview (delivery, stakeholders, mentoring), a **values** interview, then a decision by a committee. 3 to 6 weeks.
- Clean, runnable code is stressed over pseudocode.
- The values round has real weight. Atlassian has five company values. Read them on Atlassian's own website and prepare a story for each (I did not open the page; check it yourself).
- I found no source for a round called "data club". It is unverified, so ignore it unless the recruiter mentions it.
- Sources: [DesignGurus](https://www.designgurus.io/answers/detail/what-is-the-atlassian-interview-process-like-round-by-round), [Interview Query](https://interviewquery.com/interview-guides/atlassian), [Taro Bengaluru](https://www.jointaro.com/interviews/companies/atlassian/experiences/principal-engineer-bengaluru-october-1-2021-accepted-offer-positive-0b47077c) (a Principal level, older).

### Oracle (OCI, Bengaluru)
- Reports: 3 to 4 technical rounds and a manager round. A distributed hash map design question was reported. Java, Spring Boot, array programs, stacks and trees came up. One older report for a principal level also had a director round.
- Source: [Glassdoor](https://www.glassdoor.co.in/Interview/Oracle-Interview-E1737-RVW94411330.htm) (and similar reviews).

### Mastercard (Pune)
- Reports: a June 2026 Software Engineer II report had four rounds (automation testing, technical discussion, problem solving, final talk with technical leaders). A Sept 2024 report had three technical rounds: coding, algorithms and system design. Java and Spring appear often. Glassdoor's average is based on only four interviews, so it is not reliable.
- Source: [Glassdoor Mastercard Pune](https://static.glassdoor.sg/Interview/Mastercard-Software-Engineer-II-Interview-Questions-EI_IE3677.0,10_KO11,31.htm).

### PayPal (Bengaluru)
- Reports: an Oct 2025 MTS1 report had 5 rounds: 1 DSA, 2 system design, 1 hiring manager (one more not described). An MTS-3 report in Aug 2024 had a DSA question and an API/DB design for a peer-to-peer chat. Questions touched RDBMS vs NoSQL and caching.
- Sources: [Taro Oct 2025](https://www.jointaro.com/interviews/companies/paypal/experiences/mts1-software-engineer-bengaluru-october-14-2025-accepted-offer-positive-b2427079).

### Razorpay
- Sources disagree: 4 to 5 rounds in one guide, 4 to 6 in another. SDE-2: one medium DSA and one HLD problem. A frontend SDE-2 report has machine coding. I found no source confirming a machine-coding round for backend SDE-2.
- Sources: [JobRise](https://jobrise.io/en/blog/razorpay-interview-questions-2026/), [TechPrep](https://www.techprep.app/blog/razorpay-interview-process).

### PhonePe
- A Sept 2026 LeetCode report for SDE-2 backend had 4 rounds: **machine coding/LLD, DSA, HLD, hiring manager**. TechPrep calls machine coding PhonePe's main filter.
- HLD centres on distributed systems. HM round is a deep dive into past work.
- Sources: [LeetCode](https://leetcode.com/discuss/post/8547106), [TechPrep](https://www.techprep.app/blog/phonepe-interview-process).

## What is common across all of them
1. **DSA never goes away.** Do mediums with a timer.
2. **Design matters at SDE II.** HLD and LLD both appear.
3. **The HM round decides.** They ask "tell me more" about every line of your resume. Know your projects deeply. Files in `04-my-work-explained` will help.
4. **Payments companies** (PayPal, Razorpay, PhonePe, Mastercard) often ask about consistency, retries, idempotency and failures. See file 12 for the idea of idempotency.

## How to prepare for machine coding (General advice)
1. Pick a classic: parking lot, elevator, splitwise, rate limiter, library system.
2. Give yourself 90 minutes. Write: clear classes, simple interfaces, a few tests, a main file to demo.
3. Do not over-engineer. Make it work, then clean it.
4. Keep names plain. Add 3 tests. Write a short README of how to run.
