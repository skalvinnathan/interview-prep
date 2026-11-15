# 00. How the System Design Round Works

Read this file first. It tells you what the round is, what the interviewer is thinking, and a method you can use for every question.

---

## Part 1. What is a system design round?

An interviewer gives you a big, vague problem. For example: "Design a URL shortener" or "Design a chat app".

You do **not** write code. You draw boxes and arrows on a whiteboard or an online drawing tool. You talk the whole time. You explain:

- what the system must do,
- how many users it has,
- what the pieces are (servers, databases, caches, queues),
- why you picked each piece,
- what can break and how you fix it.

**Daily-life analogy.** Imagine a friend says: "I want to open a restaurant." You do not cook. You ask: How many guests? What food? How big is the kitchen? Where do we keep the rice? What if the cook is sick? That is system design. You are the architect, not the cook.

There is **no single right answer**. The interviewer checks how you think.

---

## Part 2. What the rounds look like at Google, Amazon and Stripe

Important honesty note: Google, Amazon and Stripe do not publish a full rubric (scoring sheet) for system design. Most of what is below comes from **candidate reports and prep websites**. They sometimes disagree with each other. Your recruiter's schedule email is the most accurate source for **your** loop. Always trust it first.

What I could verify (with links), and what I could not, is marked below.

### Google

| Point | What sources say | Confidence |
|---|---|---|
| Length | About 45 minutes, one round, at L5 and above | Third-party guides agree ([Hello Interview, Google L5](https://www.hellointerview.com/guides/google/l5), [aced.io](https://www.aced.io/blog/google-system-design-interview)) |
| Who gets it | Standalone round at L5+. For L3/L4 the sources disagree: some say design is folded into a coding round, some say a simpler design round exists | Mixed. Ask your recruiter |
| Prompt | Deliberately vague. You must set requirements: users, scale, latency | Third-party |
| What is scored | Requirements first; sound high-level design; depth (partitioning, indexing, failure handling); trade-offs said out loud; reacting well to new constraints; clear communication | Third-party. Google publishes no rubric |
| Tool | Plain doc or whiteboard. Google's own virtual interview guide says design interviews may need diagramming and suggests practising with Google Drawings ([Google candidate guide PDF](https://services.google.com/fh/files/misc/general_virtual_interviews_candidate_resource.pdf)) | From a search-result summary of the PDF |
| After the loop | A hiring committee reviews all feedback, then team matching | Third-party |

Google's own pages: [Our hiring process](https://www.google.com/about/careers/applications/how-we-hire) and [Interview tips](https://www.google.com/about/careers/applications/interview-tips/). I could not read the full text of these pages with my tools, so I do not quote them.

### Amazon

| Point | What sources say | Confidence |
|---|---|---|
| Loop size | 4 to 6 interviews, 45 to 60 minutes each. A **Bar Raiser** (an interviewer from outside the hiring team) is part of it | **Official**: [Amazon interview guide](https://www.aboutamazon.com/news/workplace/amazon-interview-guide) |
| Leadership Principles (LPs) | Amazon's 16 LPs underpin every hiring decision. Use the STAR method (Situation, Task, Action, Result) with numbers and "I" statements | **Official**, same page |
| Technical roles | About half the process is technical (coding, system design); the rest is behavioral | **Official**, same page |
| SDE II loop | Two coding rounds, one 60-minute system design round, one round of low-level design or another coding round, plus the Bar Raiser. Only about 30 minutes of the design round is the design itself. Every technical round also has 20 to 30 minutes of behavioral questions | Third-party: [Hello Interview, Amazon L5](https://www.hellointerview.com/guides/amazon/l5) |
| What is scored in design | Architecture thinking, scale and trade-offs, asking clarifying questions, clear talking | Third-party (same) |

Takeaway for Amazon: prepare **stories** for the Leadership Principles as seriously as you prepare designs. In a design round, expect a few behavioral questions too. Practical, "build it with common cloud pieces" designs are what is usually described.

### Stripe

| Point | What sources say | Confidence |
|---|---|---|
| Overall loop | Stripe's careers page says most processes include a recruiter screen, a technical or skills-based assessment, and interviews with the team ([Stripe careers](https://stripe.com/careers)) | Official, general |
| Rounds reported | Recruiter screen, coding screen, general coding, a debugging round ("Bug Squash" - fix a real historical bug from an open-source project; confirmed on Stripe's pages), an integration round (build a small feature with a given API), system design, behavioral | Third-party list: [aced.io Stripe guide](https://www.aced.io/guides/stripe-software-engineer-interview). Bug Squash itself: Stripe site |
| System design | 45 to 60 minutes for mid-level and above. New grads often skip it | Third-party ([aced.io](https://www.aced.io/blog/stripe-system-design-interview)) |
| Style | Prompts are tied to Stripe's payments world. They feel like a real design review. Reported tool: Whimsical, not a physical whiteboard | Third-party (same) |
| What is scored | Problem framing, API and data-model design ("easy to use, hard to misuse"), failure and scale reasoning, separation of concerns, rollout, testing and monitoring | Third-party (same) |

Takeaway for Stripe: spend extra time on the **API** and **data model** steps, and on **failure handling** (retries, duplicate requests, money safety). Files `18_payment_system_like_stripe.md` and `03_reliability_patterns.md` are your most important files for Stripe.

### What I could NOT verify

- Exact 2026 round counts for each company. Sources conflict, and some are old.
- Whether Google asks system design at your exact level (L4 vs L5). Ask your recruiter.
- Any "secret rubric". None is public. Everything above about scoring is how prep sites describe it.

---

## Part 3. What the interviewer is really checking

Whatever the company, interviewers in these rounds usually look for the same five things. (This is a summary of what the sources above describe, in my words.)

1. **Do you ask questions first?** A good engineer does not start building before knowing what to build.
2. **Can you make a sensible design?** Not fancy. Sensible.
3. **Do you know why?** Every box has a reason. "I use a cache because reads are 100 times more than writes."
4. **Do you see problems before they happen?** What if a server dies? What if one user sends 1 million requests?
5. **Can you talk clearly and take hints?** Interviewers give hints. Take them. It is a conversation, not an exam.

A level note: at SDE II (about 3 to 5 years' experience), you are not expected to know every secret of huge systems. You are expected to give a **clean, working design**, name the **main trade-offs**, and handle **follow-up questions** calmly.

---

## Part 4. The 7-step method (use it for EVERY question)

Learn these seven words in order:

> **R**equirements - **S**cale - **A**PI - **D**ata - **H**igh-level design - **D**eep dive - **T**rade-offs and failures

A memory sentence: **"Really Smart Architects Draw Huge Diagrams Thoughtfully."**

### Step 1. Requirements (about 5 minutes)

Ask questions. Split into:

- **Functional requirements** = what the system does. ("A user can paste a long link and get a short link.")
- **Non-functional requirements** = how well it does it. (Fast? Always available? Never lose data?)
- **Out of scope** = what you will NOT do. Say it out loud so the interviewer agrees. ("I will skip user accounts and analytics for now.")

Good questions to always ask:
- Who are the users? How many?
- Which features are the most important? (Pick 2 or 3.)
- Do we read more or write more?
- Is it okay if data is a few seconds old? (This is about consistency; see `01h`.)
- Is it okay to lose a message? Or must we never lose one?
- Is it one country or the whole world?

**Analogy:** The waiter asks "Vegetarian? Allergies? How many people?" before the kitchen cooks.

### Step 2. Scale estimate (about 3 minutes)

Do rough math (see `02_numbers_and_estimation.md`):
- How many requests per second (QPS)?
- How much data per day, per year?
- Reads or writes heavy?

Say "this is an estimate". The goal is only to know: is it one server, ten servers, or a thousand? Does the data fit on one disk?

### Step 3. API (about 3 minutes)

Write the main calls. Keep it short. Example:

```
POST /v1/links        body: {long_url}       -> {short_code}
GET  /{short_code}                            -> 302 redirect
```

Say: who calls it, what goes in, what comes out, and how you handle errors and duplicates.

### Step 4. Data model (about 3 minutes)

Write the main tables or collections: names, key columns, which column is the primary key, which column you search by. Say SQL or NoSQL and **why**.

### Step 5. High-level design (about 8 minutes)

Draw **version 1**: the simplest thing that works. Client, server, database. Walk through one request from start to end. Then add what you need for scale: load balancer, cache, queue, replicas.

Rule: **start simple, then grow.** Do not draw 20 boxes on the first minute.

### Step 6. Deep dive (about 10 minutes)

The interviewer will pick one or two parts and ask "how does this really work?" Or you choose the hardest part. Go deep: algorithm, schema, how you shard, how you avoid duplicates.

### Step 7. Trade-offs and failures (about 5 minutes)

- What are the weak points? (single point of failure, hot spot, slow query)
- What happens if a server, a database, or a whole data centre fails?
- What would you monitor?
- What would you build next if you had more time?

---

## Part 5. Using the 45 minutes

```
Minute  0 ----- 5 ----- 8 ----- 11 ----- 14 ------ 22 ------ 32 ------ 40 --- 45
        | Reqs  | Scale | API   | Data   | High-    | Deep     | Trade-  | Wrap
        |       |       |       |        | level    | dive     | offs,   |
        |       |       |       |        | design   |          | failure |
```

| Step | Minutes | Output on the board |
|---|---|---|
| Requirements | 5 | Bullet list: must-have, out-of-scope |
| Scale | 3 | 3 or 4 numbers |
| API | 3 | 2 to 4 calls |
| Data | 3 | 2 to 3 tables |
| High-level design | 8 | One diagram, then one growth step |
| Deep dive | 10 | Detail on the hardest part |
| Trade-offs and failures | 5 | List of risks and fixes |
| Wrap-up | 3 | Summary in 6 sentences; questions |

Notes:
- At Amazon the design part may be only about 30 minutes of a 60-minute slot (the rest is behavioral). Shrink every step a little, but keep the order.
- If the interviewer jumps in early with questions, that is good. Follow them. Return to the plan afterward.
- Keep one eye on the clock. If you pass minute 20 and have no diagram, draw the simplest version **now**.

---

## Part 6. How to talk

Interviewers cannot read your mind. Only spoken words count.

1. **Think aloud.** "I am thinking about two options: a SQL table or a key-value store. Let me compare."
2. **Say the plan first.** "I will do requirements, then numbers, then API, then the design." This calms you and the interviewer.
3. **Use short sentences.** Simple English is fine. Clear is better than fancy.
4. **Say "because".** Every choice needs a because. "I choose a queue **because** the email provider is slow and I do not want users to wait."
5. **Name trade-offs.** "This gives faster reads, but the data can be a few seconds old."
6. **Check in.** "Does this match what you had in mind? Should I go deeper here or move on?"
7. **Write while you talk.** Boxes, arrows, numbers. Label arrows ("HTTP", "async").
8. **Use your real work.** "In my provisioning platform we retry failed installs with backoff, so I would do the same here." Real stories show real skill. Keep them short and true.
9. **Do not argue.** If the interviewer says "what about X?", say "good point" and answer. Hints are gifts.

### Phrases you can use (copy them)

- "Before I design, can I ask a few questions?"
- "Let me make an assumption and tell me if it is wrong."
- "This is a rough estimate, but it tells me we need..."
- "The simplest version is... It will break when... so next I add..."
- "The trade-off here is X versus Y. I choose X because..."
- "I am not 100 percent sure about this detail. My reasoning is... Is that on the right track?"

---

## Part 7. What to do when you get stuck

It happens to everyone. Do not freeze. Use this list:

1. **Pause and breathe. Say it.** "Let me take a moment to think." Silence of 10 seconds is fine. Silence of 2 minutes is not.
2. **Go back one step.** Re-read your requirements. Often the answer is there.
3. **Make it simple.** "If there was only one user, what would I build?" Then ask "what breaks with a million users?"
4. **Compare two options.** Even if you do not know the best one, saying "A is simpler, B scales more" shows judgment.
5. **Say what you know.** "I have not used this exactly, but in my work on a similar problem we did..."
6. **Ask for a hint, politely.** "I am torn between X and Y. Do you have a preference for this exercise?" This is allowed and normal.
7. **Park the hard part.** "I will mark this as a risk and come back to it." Then move on so you finish the whole design.
8. **If you made a mistake, fix it out loud.** "Actually, that would break because... let me change it." Fixing a mistake calmly scores well.

### Common mistakes (avoid them)

- Starting to draw before asking questions.
- Giving a final answer with 15 boxes and no reason.
- Naming tools (Kafka, Redis) without saying why.
- Forgetting failures. Every box can die.
- Never doing numbers.
- Talking only about the "happy path" (when everything works).
- Going too deep on a small part and never finishing.

---

## Part 8. Your study plan for this folder

| Order | File | Purpose |
|---|---|---|
| 1 | `00_how_the_round_works.md` (this) | The method |
| 2 | `01a` to `01h` | Building blocks (the Lego bricks) |
| 3 | `02_numbers_and_estimation.md` | The math |
| 4 | `03_reliability_patterns.md` | Making things safe |
| 5 | `10` to `22` | Full designs, one by one. Start with 10, 11, 12 |
| 6 | `90_cheat_sheet.md` | Revise the night before |
| 7 | `91_practice_questions.md` | Practice out loud, with a timer |

Practice plan: 1 design per day. Read it once, close it, then explain it **out loud for 30 minutes** to a wall or a friend. Use the "say it out loud" summary at the end of each file as your last 1 minute.

---

## Sources used in this file

- Amazon (official): https://www.aboutamazon.com/news/workplace/amazon-interview-guide
- Stripe careers (official, general): https://stripe.com/careers
- Google hiring pages (official; text not readable with my tools): https://www.google.com/about/careers/applications/how-we-hire
- Google virtual interview guide (PDF, via search summary): https://services.google.com/fh/files/misc/general_virtual_interviews_candidate_resource.pdf
- Hello Interview, Google L5 loop (third party): https://www.hellointerview.com/guides/google/l5
- Hello Interview, Amazon L5 loop (third party): https://www.hellointerview.com/guides/amazon/l5
- aced.io (ex-Exponent), Google system design (third party): https://www.aced.io/blog/google-system-design-interview
- aced.io, Stripe system design (third party): https://www.aced.io/blog/stripe-system-design-interview
- aced.io, Stripe SWE guide (third party): https://www.aced.io/guides/stripe-software-engineer-interview
