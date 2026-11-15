# 91 - Practice questions (20)

How to use: set a timer for 45 minutes. Say everything out loud as if an interviewer is there. Use the 7 steps from `00_how_the_lld_round_works.md`. After you finish, compare with the worked design (if one exists in this folder).

**About company tags.** I put a company tag **only** where I found a source (a candidate report or a page that I could open). All of them are **anonymous, self-reported** posts, not official statements from the company. If a question has no tag, I could not verify any company, and it is just a classic practice problem. Do not tell yourself "Company X always asks this".

---

## A. Questions with a worked design in this folder

| # | Question | Worked design | Company tag (source) |
|---|---|---|---|
| 1 | Design a parking lot. Pick the smallest free spot that fits three vehicle sizes. Then add EV charging spots with fallback. | `10_parking_lot.md` | **Amazon**, Software Engineer, technical screen, level not stated ([PracHub](https://prachub.com/interview-questions/parking-lot-design-smallest-fitting-spot-for-three-sizes-then-ev-charging-fallback)) |
| 2 | Design and implement an LRU cache with O(1) `get` and `put`. Then add expiry (TTL). | `11_lru_cache.md` | **Amazon**, SDE II, Vancouver, Feb 2025 report ([Jointaro](https://www.jointaro.com/interviews/companies/amazon/experiences/software-development-engineer-sde-ii-vancouver-bc-february-1-2025-no-offer-positive-b42b95f3)). Also a post titled "Google L4 Software Engineer Interview: LRU Cache and URL Shortening" ([1point3acres](https://www.1point3acres.com/interview/post/7685567)); I could read only the title, not the post. |
| 3 | Design an elevator system with several elevators and a dispatch rule. | `12_elevator_system.md` | no verified tag |
| 4 | Design a library management system with search, borrow, return, fines, and holds. | `13_library_management.md` | no verified tag |
| 5 | Design a vending machine. | `14_vending_machine.md` | no verified tag |
| 6 | Design an ATM (PIN, withdraw, deposit, balance). | `15_atm.md` | no verified tag |
| 7 | Design a rate limiter class (token bucket and sliding window). | `16_rate_limiter_class.md` | no verified tag for the class-design version |
| 8 | Design an Amazon Locker system. | `17_amazon_locker.md` | **Amazon**, SDE II, Austin, May 2022 report: "design an API for an Amazon Locker system" ([Jointaro](https://www.jointaro.com/interviews/companies/amazon/experiences/software-engineer-ii-sde2-austin-tx-may-1-2022-no-offer-neutral-ad02ca44/)). Hello Interview also has it as a practice problem ([Hello Interview](https://www.hellointerview.com/learn/low-level-design/problem-breakdowns/amazon-locker)), which is not a claim about real interviews. |
| 9 | Design an expense sharing app (Splitwise). Equal, exact, percent split. Show balances. | `18_splitwise_expense_sharing.md` | no verified tag |
| 10 | Design a logging framework (levels, many destinations, formats). | `19_logger_and_notification_system.md` | no verified tag |
| 11 | Design a notification system (email, SMS, push; user preferences). | `19_logger_and_notification_system.md` | no verified tag |
| 12 | Design tic-tac-toe for an N x N board with O(1) win check. | `20_tic_tac_toe_or_chess_basics.md` | no verified tag |
| 13 | Design the core of a chess game (board, pieces, legal moves, turns). | `20_tic_tac_toe_or_chess_basics.md` | no verified tag |

## B. Questions to try on your own (no worked design, hints included)

| # | Question | Hints |
|---|---|---|
| 14 | **Rule engine.** Design a system that evaluates rules (for example "order total > 500 AND country == IN") and returns a decision. Discuss how to avoid a class explosion. | Tag: **Amazon SDE-2 LLD** is the title of a [1point3acres post](https://www.1point3acres.com/interview/post/7751773); I could not read the body, so I do not know the exact prompt. Hints: `Rule` interface with `evaluate(context)`; `AndRule`, `OrRule`, `NotRule` that hold other rules (Composite idea); rules as data so new rules need no new class. |
| 15 | **Snake and ladder** for N players. | no verified tag. Hints: `Board` with a dict `start -> end` for snakes and ladders; `Dice` as a Strategy (so tests can fix the roll); `Game` loop; exact-finish rule is a requirement to ask. |
| 16 | **Movie ticket booking** (BookMyShow): show seats, hold a seat for a few minutes, pay, release. | no verified tag. Hints: `Seat` with status AVAILABLE/HELD/BOOKED (State); hold with expiry time; lock per show; two users picking the same seat is the core thread problem. |
| 17 | **Cab booking** (rider asks, nearest driver gets matched). | no verified tag. Hints: `Driver` status (State); `MatchingStrategy` (nearest, rating); `PricingStrategy`; trip as a state machine REQUESTED -> ACCEPTED -> STARTED -> ENDED. |
| 18 | **In-memory key-value store with TTL and transactions** (begin, commit, rollback). | no verified tag. Hints: dict of key -> (value, expiry); a stack of "change logs" for nested transactions; rollback pops the top log and undoes it (Command idea). |
| 19 | **Text editor with undo and redo.** | no verified tag. Hints: Command pattern: `InsertCommand`, `DeleteCommand` with `execute` and `undo`; two stacks (undo and redo); a new edit clears the redo stack. |
| 20 | **Hit counter / logger rate limiter**: count requests in the last 5 minutes; or "print each message at most once every 10 seconds". | no verified tag for the exact wording. Hints: a `deque` of timestamps (drop old ones from the left), or a dict `message -> last printed time`; discuss out-of-order timestamps and memory growth. |

---

## C. How to practise well

1. **First attempt without help.** Think for 25 minutes, then look.
2. **Always ask requirement questions first**, even when practising alone. Write them down.
3. **Run your code.** A design that you never ran often has small bugs.
4. **Ask yourself the extension question:** "What if the interviewer adds X? Which class do I add, and which do I leave untouched?"
5. **Say the thread-safety sentence:** "The shared data is ..., the multi-step operation is ..., so I lock ..."
6. **Order of practice (suggested):** 11 (LRU) -> 10 (parking) -> 14 (vending) -> 16 (rate limiter) -> 18 (Splitwise) -> 12 (elevator) -> 13 -> 15 -> 17 -> 19 -> 20, then the self-study questions 14 to 20.
