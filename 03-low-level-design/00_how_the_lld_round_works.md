# 00 - How the LLD round works

Read this file first. It tells you what the round is, and gives you one method that you use for every problem.

---

## 1. What is "LLD"?

**LLD** means **Low-Level Design**. Some companies call it **OOD**, which means **Object-Oriented Design**. It is the same round.

In this round the interviewer gives you one small system. For example: "Design a parking lot." Or: "Design an LRU cache."

You do **not** draw big boxes like "load balancer" and "database" (that is *system design*, or HLD = High-Level Design).

You do this instead:

1. You decide which **classes** you need (a class is a blueprint, like a recipe for a cake).
2. You decide what each class **knows** (data) and what it **does** (methods).
3. You decide how the classes **talk to each other**.
4. You write **real code** for the core part.

**Daily-life analogy.** HLD is like drawing the map of a city: roads, airport, train station. LLD is like designing one house: which rooms, where the doors are, where the switches are. The interviewer wants to see that you can design a clean house that is easy to change later.

---

## 2. What the interviewer is checking

Hello Interview, a prep site, lists five things interviewers look at: problem analysis, class design, code quality, extensibility, and communication
([source](https://www.hellointerview.com/learn/low-level-design/in-a-hurry/introduction)).
In simple words:

| They check | What it means for you |
|---|---|
| Problem analysis | You ask questions before you code. You do not guess. |
| Class design | Each class has one clear job. Names are clear. |
| Code quality | Data is hidden inside classes. Code is neat. |
| Extensibility | If they add a new rule, you change a little code, not everything. |
| Communication | You think out loud. You explain why. |

---

## 3. How Amazon runs it (what I could verify)

I searched the internet on 2026-11-15. Here is what I found, split into **official** and **not official**.

### Official (amazon.jobs)

- Amazon's page "Software Development Interview Topics" lists **object-oriented design** as one of the technical topics a candidate should prepare, together with data structures, algorithms, coding, databases, distributed computing and operating systems
  ([Amazon topics page](https://amazon.jobs/content/en/how-we-hire/interview-prep/software-development-topics)).
- Amazon's "SDE II Interview Prep" page says an online assessment comes first, then a loop of four interviews of 55 minutes each, and to "expect at least one question on software systems design". It says to write **real, syntactically correct code, not pseudo code**, and to check edge cases
  ([Amazon SDE II prep](https://amazon.jobs/content/en/how-we-hire/sde-ii-interview-prep)).
  Careful: this page does **not** separate low-level design from high-level design, and its video list names only "High-Level Design".
- Amazon says the process differs from role to role: online application, assessments, phone screen, then the interview loop
  ([Amazon interviewing page](https://www.amazon.jobs/en/landing_pages/interviewing-at-amazon)).

### Not official (third-party guides and candidate posts, treat as hints)

- TechPrep (2026 guide) says the loop has 4-5 rounds, and that low-level design is "more commonly seen in SDE I loops" while system design is aimed at SDE II and above. The page does not say explicitly whether OOD appears at SDE II, so check with your recruiter
  ([TechPrep](https://www.techprep.app/blog/amazon-interview-process)).
- A LeetCode post titled "Amazon | SDE2 | LLD | OOD" exists, so candidates do report LLD at SDE II
  ([LeetCode discuss](https://leetcode.com/discuss/general-discussion/995914/amazon-sde2-lld-ood)). I could not open the post body (the site blocked my tool), so I only know that the title exists.
- Reported question examples from candidate sites. A 1point3acres post is titled "Amazon SDE-2 LLD Round Rule Engine Design"
  ([1point3acres](https://www.1point3acres.com/interview/post/7751773)); I could only read the title (the site blocked my tool), not the post. PracHub tags a parking-lot question (smallest free spot that fits, then EV charging spots, then thread safety and tests) as **Amazon, Software Engineer, technical screen**, level not stated
  ([PracHub](https://prachub.com/interview-questions/parking-lot-design-smallest-fitting-spot-for-three-sizes-then-ev-charging-fallback)).
  These are single candidates' reports, not official Amazon statements.
- Leadership Principles (LPs, Amazon's behavioural values) appear across the loop. TechPrep says each round is roughly half technical and half behavioural, and Amazon's own page says each interviewer typically asks two or three behavioural questions
  ([Amazon SDE II prep](https://amazon.jobs/content/en/how-we-hire/sde-ii-interview-prep)).

**What this means for you:** Amazon officially tells you to prepare OOD and to write real code. Whether *your* loop has a pure LLD round depends on team and level. **Ask your recruiter.** Ask: "Is there a low-level design round, and is it in a coding editor or on a whiteboard?"

## 4. How Google and others run it (what I could verify)

- I found **no official Google page** that describes an LLD round. I could not verify that Google has a dedicated LLD round.
- Third-party guides describe Google loops as mostly coding (data structures and algorithms), a system design round for more senior levels, and a behavioural ("Googleyness") round
  ([Interview Kickstart guide](https://www.interviewkickstart.com/blog/how-google-hires-only-the-best-software-engineers), [Jobrise India guide](https://jobrise.io/en/blog/google-interview-preparation-india/)).
- One candidate post (Google L4, India, May 2025) mentions a class-design question in a coding round
  ([LeetCode post](https://leetcode.com/discuss/post/6752754/google-l4-india-may-2025-offer-by-anonym-7ww2/)). That is one report, not a rule.
- So at Google, expect that **class-design skills may appear inside a coding round**. Treat it as possible, not confirmed.
- Hello Interview says US big-tech companies lean toward partial code in a real language (Java, Python, C++), while interviews at companies in India and Asia are closer to structured pseudocode
  ([Hello Interview](https://www.hellointerview.com/learn/low-level-design/in-a-hurry/introduction)). Prepare for **real code** to be safe, as Amazon asks.

**Things I could not verify:** exact length of an Amazon LLD round, whether concurrency is expected, and the exact Google LLD format. Forum posts disagree on concurrency. This is why every design in this folder has a "thread-safety" section: you can mention it briefly if the interviewer asks.

---

## 5. The 7-step method (use it every time)

Hello Interview suggests a five-step frame: requirements (about 5 minutes), entities and relationships (about 3), class design (10-15), implementation (about 10), extensibility (about 5)
([Hello Interview delivery](https://www.hellointerview.com/learn/low-level-design/in-a-hurry/delivery)). My 7 steps below are the same idea with two extra steps that help you (patterns and testing). The times are my guess for a 45-minute round, not an official rule.

### Step 1. Clarify the requirements (about 5 minutes)

**Why:** The prompt is one sentence. If you start coding at once, you may build the wrong thing.

Ask short questions:

- Who uses it? (One user or many?)
- What are the 3 to 5 main things it must do? (Park a car, remove a car, pay.)
- What is out of scope? (Payment gateway? Network? Database?)
- Do I need to handle many threads at the same time?
- What are the limits? (How many floors? How many items?)

Then **say the list back** to the interviewer: "So I will build A, B and C. I will not build D. Correct?"

### Step 2. Find the nouns and verbs

Read the requirements. Underline the **nouns**: these become **classes** (or fields). Underline the **verbs**: these become **methods**.

Example sentence: "A *driver* parks a *vehicle* in a *spot* and gets a *ticket*."

- Nouns: driver, vehicle, spot, ticket -> classes `Vehicle`, `Spot`, `Ticket`.
- Verbs: parks, gets -> methods `park()`, `issue_ticket()`.

Tip: not every noun is a class. "Driver" may not matter if we never store anything about the driver. Ask: "Does this thing have its own data or rules?" If not, skip it.

### Step 3. Draw the relationships

For each pair of classes ask:

- **"Is-a"** -> inheritance. A `Car` *is a* `Vehicle`.
- **"Has-a"** -> composition. A `ParkingLot` *has* `Floor`s.
- **"Uses"** -> one class calls another.

Draw simple boxes and lines. ASCII is fine:

```text
ParkingLot 1 ---- * Floor 1 ---- * Spot
```

Read it as: one lot has many floors, one floor has many spots.

Also choose one class to be the **boss** (the "orchestrator" or "facade"): the class the outside world talks to, like `ParkingLot`. It gives the interviewer one clear entry point.

### Step 4. Pick patterns only when they help

A design pattern is a known solution to a common problem (see `03_design_patterns_you_need.md`).

Rule: **Write the simple version first.** Add a pattern only when you can finish this sentence: "I need a pattern here because the interviewer might change ____, and without a pattern I would have to edit many places."

Bad: forcing a Singleton and a Factory into a design that has only one vehicle type.
Good: using Strategy for pricing because pricing rules change often.

### Step 5. Code the core

- Start with the **boss class and its main method** (the happy path, where nothing goes wrong).
- Use clear names. Hide data (use `_private` names).
- Do not write every getter. Write the code that shows your thinking.
- Handle a few edge cases: lot full, item not found, bad input.
- Say out loud what you are doing and why.

### Step 6. Test with one example

Walk through a small example by hand, or write a tiny `main()`. Say: "Park a car. Park a bike. Lot is full. Now car leaves." Show the result. This catches bugs and shows you care about quality.

### Step 7. Talk about extension

Interviewers often add: "Now add a new rule." Say where the change goes: "I add a new class that implements the same interface. I do not touch the old code." This is the *Open/Closed* idea (see `02_solid_principles.md`).

Also mention, in one or two sentences: thread safety ("I would add a lock around this method"), and what you would do with more time.

---

## 6. A 45-minute clock (my suggestion)

| Minutes | What |
|---|---|
| 0-5 | Requirements |
| 5-10 | Classes and relationships (draw) |
| 10-35 | Code the core |
| 35-40 | Test with an example |
| 40-45 | Extension and questions |

If you run short of time, **cut code, not talking**. A clear design with half the methods is better than one finished but unexplained class.

---

## 7. Common mistakes (avoid these)

1. Coding in the first minute.
2. Making one giant class that does everything (`God class`).
3. Using `if type == "car"` everywhere instead of polymorphism (see file 01).
4. Adding patterns to look smart.
5. Staying silent while thinking.
6. Forgetting edge cases (empty, full, duplicate, not found).
7. Not testing.

---

## 8. How to use this folder

1. Read 01 (OOP words), 02 (SOLID), 03 (patterns) once.
2. Do the designs 10 to 20, one per day. For each: read the problem, **close the file**, try yourself for 25 minutes, then compare.
3. Re-read `90_cheat_sheet.md` the night before an interview.
4. Do `91_practice_questions.md` out loud, as if with an interviewer.

All code in this folder is Python 3.9. Every code block was run, and the output shown is the real output.
