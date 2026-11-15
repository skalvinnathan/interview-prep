# 90 - Cheat sheet (read the night before)

Python 3.9. The code block at the bottom was run.

---

## 1. The 7 steps (45 minutes)

| # | Step | Minutes | What you say |
|---|---|---|---|
| 1 | Clarify requirements | 5 | "Who uses it? What are the 3-5 main actions? What is out of scope? Threads?" Then repeat the list back. |
| 2 | Nouns and verbs | 2 | Nouns = classes. Verbs = methods. |
| 3 | Relationships | 3 | is-a (inherit), has-a (compose), uses. Name the **boss class**. |
| 4 | Patterns only if needed | 2 | "I use Strategy here because this rule will change." |
| 5 | Code the core | 20-25 | Boss class + main method first. Happy path, then edge cases. |
| 6 | Test with an example | 3-5 | Walk one small scenario, or write `main()`. |
| 7 | Extension and threads | 5 | "A new rule is a new class; I do not edit old code. For threads I add a lock here." |

**Cut code, not talking.** If time is short, a clear design with fewer methods beats finished but silent code.

---

## 2. OOP words in one line each

| Word | One line |
|---|---|
| Class / object | cookie cutter / cookie |
| Encapsulation | hide data, change it only through methods that check the rules |
| Inheritance | "is-a": child gets parent's code |
| Composition | "has-a": object holds other objects (prefer this) |
| Polymorphism | same method name, each class does it its own way (kills `if type ==`) |
| Interface / ABC | a promise of methods (`abc.ABC` and `@abstractmethod`) |

## 3. SOLID in one line each

| Letter | Say this |
|---|---|
| S | One class, one reason to change. |
| O | Add new behaviour by adding a class, not editing old code. |
| L | A child must work wherever the parent works (no "not supported" methods). |
| I | Several small interfaces beat one fat one. |
| D | Depend on an interface; pass the worker in the constructor. |

## 4. Patterns: trigger phrase -> pattern

| If the interviewer says... | Use | Remember |
|---|---|---|
| "different pricing / algorithms / rules, may change" | **Strategy** | interface + one class per rule, passed in |
| "create the right object by name or type" | **Factory** | dict `name -> class` |
| "when X happens, tell many others" | **Observer** | list of listeners, loop and call |
| "exactly one shared instance" | **Singleton** | usually better: create once and pass in |
| "behaviour depends on mode / status" | **State** | one class per state; the state picks the next state |
| "object with many optional parts" | **Builder** | chained methods, `build()` validates |
| "add features in any combination" | **Decorator** | wrap an object with the same interface |
| "undo, queue, log, schedule actions" | **Command** | `execute()` and `undo()` objects |

**Do not** force a pattern. Say: "I start simple. If the rule changes, I would extract a Strategy here."

## 5. What each worked design teaches

| File | Core idea | Patterns |
|---|---|---|
| 10 Parking lot | smallest-fit allocation, ticket, fee | Strategy |
| 11 LRU cache | hash map + doubly linked list = O(1) | none |
| 12 Elevator | SCAN movement, dispatch cost | State, Strategy |
| 13 Library | copies vs titles, holds queue, fines | Observer, Strategy |
| 14 Vending machine | state transitions | State |
| 15 ATM | state + transactions as objects; plan, debit, commit order | State, Command |
| 16 Rate limiter | token bucket (lazy refill), sliding window | Strategy |
| 17 Amazon locker | size match, one-time code, expiry | Strategy |
| 18 Splitwise | money in integers, split strategies, net debts | Strategy, Factory |
| 19 Logger / notifications | one event, many destinations | Observer, Strategy, Decorator |
| 20 Tic-tac-toe / chess | O(1) win check; each piece owns its move rule | Strategy, polymorphism |

## 6. Thread-safety in 5 lines

1. **Find the shared data** (anything two threads can both change).
2. **Find the multi-step operations** ("check, then change"). Those are the danger.
3. Put **one lock** around each such operation (`with self._lock:`). Keep it short; do not call slow things inside.
4. **One owner of the lock** (usually the boss class). Use `RLock` if a locked method calls another locked method.
5. Python's GIL does **not** protect multi-step operations. For bigger scale: lock per key or per shard, or a database transaction.

## 7. Complexity reminders

| Thing | Time |
|---|---|
| dict get/put | O(1) average |
| list append / pop at end | O(1) |
| list search | O(n) |
| `deque` add/remove at either end | O(1) |
| heap push / pop | O(log n) |
| linked list: remove a node you hold (doubly) | O(1) |
| scan all spots / items | O(n) (say how you would speed it up) |

## 8. Phrases that sound good (and are true)

- "Before I code, let me confirm the requirements."
- "I will keep it simple first, then show where it extends."
- "This class has one job: ..."
- "I pass this in through the constructor, so I can swap it in a test."
- "The check and the change must be atomic, so I take a lock here."
- "A new rule is a new class; I do not edit working code."
- "Money is stored as integers to avoid float errors."
- "Here is what I did not handle: ... and how I would."

## 9. Edge cases to mention every time

Empty, full, duplicate, not found, invalid input (negative, zero, wrong type), expired, already used, two threads at once, what if a step fails halfway (rollback or order the steps so the risky one comes first).

## 10. Python 3.9 reminders

- No `match` statement, no `X | Y` type unions. Use `Optional[X]` from `typing` if you write type hints.
- `from abc import ABC, abstractmethod` for interfaces.
- `from enum import Enum` for fixed choices.
- `threading.Lock()` and `with lock:`. `threading.RLock()` when re-entry is possible.
- `collections.deque`, `collections.defaultdict`, `heapq`, `dataclasses.dataclass` (3.7+).

## 11. A skeleton you can type in 2 minutes

This runs. It has the shape of almost every design in this folder: an enum, an interface (Strategy), a boss class with a lock, an error class, and a `main()`.

```python
import threading                               # Lock for thread safety
from abc import ABC, abstractmethod            # for the interface
from enum import Enum                          # for fixed choices


class Kind(Enum):                              # a fixed set of options
    SMALL = 1
    LARGE = 2


class NoRoomError(Exception):                  # our own error with a clear name
    pass


class Item:                                    # a simple "noun" class
    def __init__(self, name, kind):
        self.name = name
        self.kind = kind


class Policy(ABC):                             # the part that may change (Strategy)
    @abstractmethod
    def price(self, item):
        pass


class FlatPolicy(Policy):                      # one concrete rule
    def price(self, item):
        return 10 if item.kind == Kind.SMALL else 20


class Manager:                                 # the boss: the one class the outside world uses
    def __init__(self, capacity, policy):
        self.capacity = capacity
        self.policy = policy                   # passed in (dependency injection)
        self._items = []
        self._lock = threading.Lock()          # one lock for shared data

    def add(self, item):
        with self._lock:                       # "check then change" must be one atomic step
            if len(self._items) >= self.capacity:
                raise NoRoomError("full")
            self._items.append(item)
            return self.policy.price(item)


def main():
    m = Manager(2, FlatPolicy())
    print(m.add(Item("a", Kind.SMALL)), m.add(Item("b", Kind.LARGE)))
    try:
        m.add(Item("c", Kind.SMALL))
    except NoRoomError as e:
        print("error:", e)


if __name__ == "__main__":
    main()
```

Output I got when I ran it:

```text
10 20
error: full
```
