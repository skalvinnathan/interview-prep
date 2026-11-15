# 17 - Amazon Locker

Python 3.9. All code was run; the output is real.

---

## 1. The problem in plain words

A **locker station** is a wall of boxes (compartments) of different sizes, placed in a shop or a station. A delivery person puts a package in a box. The customer gets a **pickup code**. The customer types the code at the station, the right box opens, and they take the package. If nobody collects the package within a few days, staff remove it and send it back.

**Analogy.** A hotel cloakroom with a numbered token: you give your bag, you get a token, you come back with the token and get exactly that bag.

(A Jointaro candidate report (Amazon SDE II, Austin, May 2022, no offer) says one question was to "design an API for an Amazon Locker system" and then scale it
([Jointaro](https://www.jointaro.com/interviews/companies/amazon/experiences/software-engineer-ii-sde2-austin-tx-may-1-2022-no-offer-neutral-ad02ca44/)). That is one anonymous report and it describes an API design round, so treat it as a hint. Hello Interview lists "Amazon Locker" as one of its practice LLD problems, but that is a practice problem, not a claim about Amazon's real interviews
([Hello Interview](https://www.hellointerview.com/learn/low-level-design/problem-breakdowns/amazon-locker)).)

---

## 2. Requirements I ask the interviewer

1. Compartment sizes? -> *Small, medium, large.*
2. Which box for a package? -> *The smallest free box that fits (a small package may use a bigger box if needed).*
3. How does the customer open the box? -> *A random numeric code, unique among active packages.*
4. How long is a package kept? -> *3 days (configurable). After that the code stops working.*
5. What happens to expired packages? -> *Staff call a "collect expired" action: the packages are removed and the boxes are freed.*
6. What if no box fits? -> *Reject the deposit with a clear error (the delivery system can try another locker).*
7. Several lockers? -> *One station for the core; a network of stations is an extension.*
8. Threads? -> *Yes, several delivery agents and customers at once.*

---

## 3. Classes and methods (the picture)

```text
+---------------------------------------------------+
|                      Locker                       |   <- the boss (one station)
|---------------------------------------------------|
| name, compartments, hold_days                     |
| deposit(package) -> code                          |
| pickup(code) -> package                           |
| collect_expired() -> [packages]                   |
| free_count()                                      |
+--+----------------+--------------+----------------+
   | has many       | uses         | uses
   v                v              v
+-------------+  +-----------------------+  +----------------------+
| Compartment |  | CompartmentSelector   |  | CodeGenerator        |
|-------------|  | (abstract, Strategy)  |  | (abstract, Strategy) |
| id, size    |  | choose(comps, pkg)    |  | generate()           |
| package     |  +-----------+-----------+  +----------+-----------+
| can_fit()   |       SmallestFitSelector        RandomCodeGenerator
+-------------+
      Package(id, size)        AccessToken(code, compartment, expires_at)

 Extension: LockerNetwork (many Locker objects, tries the nearest first)
```

**Why these?**
- `Compartment` knows if a package fits.
- `AccessToken` links a code, a box, and an expiry time.
- Choosing a box and making codes are two things that change (new rules, secure codes), so each is a small Strategy.

---

## 4. Full code

```python
import random                                  # to create random codes
import threading                               # Lock
from abc import ABC, abstractmethod            # "promise" classes
from enum import Enum                          # fixed named choices


class Size(Enum):
    SMALL = 1                                  # number = size rank (bigger number = bigger)
    MEDIUM = 2
    LARGE = 3


class NoSpaceError(Exception):                 # no box fits this package
    pass


class InvalidCodeError(Exception):             # wrong or already used code
    pass


class ExpiredCodeError(Exception):             # code is correct but too late
    pass


class Package:
    def __init__(self, package_id, size):
        self.package_id = package_id
        self.size = size                       # a Size


class Compartment:
    def __init__(self, comp_id, size):
        self.comp_id = comp_id
        self.size = size
        self.package = None                    # None = empty

    def is_free(self):
        return self.package is None

    def can_fit(self, package):
        return self.size.value >= package.size.value   # same rank rule as the parking lot


class AccessToken:
    def __init__(self, code, compartment, expires_at):
        self.code = code                       # what the customer types
        self.compartment = compartment         # which box it opens
        self.expires_at = expires_at           # day number after which it is invalid


# ---------- strategies ----------

class CompartmentSelector(ABC):
    @abstractmethod
    def choose(self, compartments, package):
        pass


class SmallestFitSelector(CompartmentSelector):
    def choose(self, compartments, package):
        fits = [c for c in compartments if c.is_free() and c.can_fit(package)]
        if not fits:
            return None
        # smallest size first; ties broken by id so the result is the same every run
        return min(fits, key=lambda c: (c.size.value, c.comp_id))


class CodeGenerator(ABC):
    @abstractmethod
    def generate(self):
        pass


class RandomCodeGenerator(CodeGenerator):
    def __init__(self, rng, digits=6):
        self.rng = rng                         # a random.Random object (we can give it a seed for repeatable tests)
        self.digits = digits

    def generate(self):
        # a number from 0 to 999999, shown with leading zeros, for example "004217"
        return str(self.rng.randrange(10 ** self.digits)).zfill(self.digits)


# ---------- the boss ----------

class Locker:
    def __init__(self, name, compartments, code_generator, clock, selector=None, hold_days=3):
        self.name = name
        self.compartments = compartments       # list of Compartment
        self.code_generator = code_generator
        self.clock = clock                     # function returning the current day number (float)
        self.selector = selector or SmallestFitSelector()
        self.hold_days = hold_days
        self._tokens = {}                      # code -> AccessToken (only active packages)
        self._lock = threading.Lock()

    def deposit(self, package):
        with self._lock:                       # choose a box and take it: one atomic step
            comp = self.selector.choose(self.compartments, package)
            if comp is None:
                raise NoSpaceError("no free compartment for " + package.size.name)
            code = self.code_generator.generate()
            while code in self._tokens:        # make sure the code is unique among active ones
                code = self.code_generator.generate()
            comp.package = package             # box is now occupied
            self._tokens[code] = AccessToken(code, comp, self.clock() + self.hold_days)
            return code

    def pickup(self, code):
        with self._lock:
            token = self._tokens.get(code)
            if token is None:
                raise InvalidCodeError("code not recognised")
            if self.clock() > token.expires_at:
                raise ExpiredCodeError("code expired; contact support")
            package = token.compartment.package
            token.compartment.package = None   # free the box
            del self._tokens[code]             # a code works only once
            return package

    def collect_expired(self):
        # staff action: remove all packages whose code has expired, free their boxes
        with self._lock:
            now = self.clock()
            removed = []
            for code in list(self._tokens):    # list(...) copy: we delete while looping
                token = self._tokens[code]
                if now > token.expires_at:
                    removed.append(token.compartment.package)
                    token.compartment.package = None
                    del self._tokens[code]
            return removed

    def free_count(self):
        with self._lock:
            return sum(1 for c in self.compartments if c.is_free())


# ---------- EXTENSION: a network of lockers ----------

class LockerNetwork:
    def __init__(self, lockers_by_distance):
        self.lockers = lockers_by_distance     # list of Locker, nearest first

    def deposit_nearest(self, package):
        for locker in self.lockers:            # try the nearest, then the next...
            try:
                return locker.name, locker.deposit(package)
            except NoSpaceError:
                continue
        raise NoSpaceError("all lockers are full for " + package.size.name)


class Clock:
    def __init__(self):
        self.day = 0.0
    def __call__(self):
        return self.day


def make_locker(name, sizes, clock, seed=1):
    comps = [Compartment(name + "-" + str(i + 1), s) for i, s in enumerate(sizes)]
    return Locker(name, comps, RandomCodeGenerator(random.Random(seed)), clock)


def main():
    clock = Clock()
    locker = make_locker("L1", [Size.SMALL, Size.MEDIUM, Size.LARGE], clock)

    code_a = locker.deposit(Package("pkg-A", Size.SMALL))
    code_b = locker.deposit(Package("pkg-B", Size.SMALL))      # small box taken, so this goes to the MEDIUM box
    print("A code:", code_a, "-> box", locker._tokens[code_a].compartment.comp_id)
    print("B code:", code_b, "-> box", locker._tokens[code_b].compartment.comp_id)
    code_c = locker.deposit(Package("pkg-C", Size.LARGE))
    print("free boxes:", locker.free_count())
    try:
        locker.deposit(Package("pkg-D", Size.SMALL))           # everything is full
    except NoSpaceError as e:
        print("deposit refused:", e)

    print("pickup A:", locker.pickup(code_a).package_id)
    try:
        locker.pickup(code_a)                                  # the same code again
    except InvalidCodeError as e:
        print("second use:", e)
    try:
        locker.pickup("000000")
    except InvalidCodeError as e:
        print("guess:", e)

    clock.day = 4.0                                            # 4 days later: B and C are past 3 days
    try:
        locker.pickup(code_b)
    except ExpiredCodeError as e:
        print("pickup B on day 4:", e)
    removed = locker.collect_expired()
    print("staff removed:", [p.package_id for p in removed], "| free boxes:", locker.free_count())

    # ---- extension demo ----
    print("--- extension: network of lockers ---")
    c2 = Clock()
    near = make_locker("NEAR", [Size.SMALL], c2, seed=2)
    far = make_locker("FAR", [Size.SMALL, Size.LARGE], c2, seed=3)
    net = LockerNetwork([near, far])
    print(net.deposit_nearest(Package("p1", Size.SMALL))[0])   # NEAR has space
    print(net.deposit_nearest(Package("p2", Size.SMALL))[0])   # NEAR is full, so FAR
    print(net.deposit_nearest(Package("p3", Size.LARGE))[0])   # only FAR has a large box
    try:
        net.deposit_nearest(Package("p4", Size.LARGE))
    except NoSpaceError as e:
        print("network full:", e)

    # ---- thread test: 20 agents try to use 5 boxes ----
    print("--- thread test ---")
    c3 = Clock()
    busy = make_locker("BUSY", [Size.MEDIUM] * 5, c3, seed=4)
    codes, fails = [], []
    def agent(n):
        try:
            codes.append(busy.deposit(Package("p" + str(n), Size.SMALL)))
        except NoSpaceError:
            fails.append(n)
    threads = [threading.Thread(target=agent, args=(n,)) for n in range(20)]
    for t in threads: t.start()
    for t in threads: t.join()
    print("deposited:", len(codes), "| refused:", len(fails), "| codes all different:", len(set(codes)) == len(codes))


if __name__ == "__main__":
    main()
```

Output I got when I ran it:

```text
A code: 140891 -> box L1-1
B code: 596853 -> box L1-2
free boxes: 0
deposit refused: no free compartment for SMALL
pickup A: pkg-A
second use: code not recognised
guess: code not recognised
pickup B on day 4: code expired; contact support
staff removed: ['pkg-B', 'pkg-C'] | free boxes: 3
--- extension: network of lockers ---
NEAR
FAR
FAR
network full: all lockers are full for LARGE
--- thread test ---
deposited: 5 | refused: 15 | codes all different: True
```

---

## 5. How the code works (walk through)

1. `deposit`: under the lock, the **selector** picks the smallest free box that fits. Then a unique code is created, the box is marked occupied, and an `AccessToken` (code, box, expiry day) is saved in `_tokens`.
2. `pickup`: look up the code. Unknown means `InvalidCodeError`. Past the expiry means `ExpiredCodeError`. Otherwise the box is emptied and the code is deleted (a code works only once).
3. `collect_expired`: staff action. It walks the tokens, and for each expired one removes the package and frees the box. We loop over `list(self._tokens)` (a copy) because we delete during the loop.
4. In the output: package A (small) took the small box; package B (small) was forced into the medium box (smallest *free* fit); on day 4 the old codes are expired, and staff removal frees everything.

The codes come from a seeded random generator only so the output is repeatable. In production the generator must be **unpredictable** (use `secrets` in Python, not `random`).

---

## 6. How to extend it

**"We have many locker stations."** `LockerNetwork` holds several `Locker` objects ordered by distance and tries them in turn. `Locker` is unchanged.

**"Returns: a customer wants to send a package back using the locker."** Add `deposit_return(package, customer_id)` that uses the same selector but creates a *return token* for the delivery driver. Probably a small `TokenType` enum (`PICKUP`, `RETURN`) on `AccessToken`.

**"Give notifications when a package arrives or is about to expire."** Add an observer list on `Locker` (Observer pattern, file 03): `deposit` emits `PACKAGE_READY`; a daily job emits `EXPIRING_SOON`.

**"Better box choice (for example keep large boxes free)."** A new `CompartmentSelector`. Nothing else changes.

---

## 7. Thread-safety notes (plain words)

- **The danger:** two delivery agents ask for a box at the same moment. Both see the same free box and both put a package in it. Or two packages get the same code.
- **The fix:** one lock covers "choose a box + create a code + occupy the box" as a single step. The thread test shows 20 agents and 5 boxes: exactly 5 succeed, and all 5 codes are different.
- `pickup` and `collect_expired` use the same lock, so a customer cannot collect a package at the same moment staff remove it.
- For a **network** of lockers, each station has its own lock, and `LockerNetwork` does not hold any lock while it moves to the next station, so there is no deadlock.

---

## 8. Five follow-up questions with model answers

**Q1. How do you stop someone guessing codes?**
Six digits give a million possibilities, so brute force is possible. Add (1) a limit on failed attempts per station or per minute (use the rate limiter, file 16), (2) longer codes or codes tied to the customer's phone, and (3) generate codes with a secure random source. A failed-attempt counter is a few lines in `pickup`.

**Q2. Why does `pickup` raise different errors for invalid and expired codes?**
The caller can show a different message and take a different action: "wrong code, try again" versus "this package is waiting for return, contact support". Using separate exception classes also keeps the happy path clean.

**Q3. How would you handle a box that is broken?**
Add a `status` to `Compartment` (`OK`, `OUT_OF_SERVICE`), and make `is_free()` return `False` if it is not OK. The selector and `deposit` then skip it automatically. (Same idea as the elevator maintenance state.)

**Q4. How do you choose boxes if many packages arrive at once, to avoid waste?**
The simple "smallest fit" rule can leave large packages without space after small packages used medium boxes. A better approach is to plan the whole batch: sort packages from largest to smallest, assign each to the smallest fitting box. Wrap this in a new `BatchSelector` strategy.

**Q5. Why is `collect_expired` a method and not a background thread?**
Staff need a clear, testable action ("run now"). A background thread adds timing problems that are hard to test. You can still add a scheduler that calls `collect_expired()` once per hour; it just calls the same method.

---

**Next:** `18_splitwise_expense_sharing.md`.
