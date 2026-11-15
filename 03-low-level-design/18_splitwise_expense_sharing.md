# 18 - Splitwise (Expense Sharing)

Python 3.9. All code was run; the output is real.

---

## 1. The problem in plain words

Friends share costs. On a trip, one person pays the hotel bill, another pays for dinner. The app records **who paid** and **how the cost is split**. At any time it can answer: "Who owes whom, and how much?" People can also **settle up** (pay back).

**Analogy.** A shared notebook on the fridge. Every time someone pays for something shared, they write: "I paid 1000 for 4 people." The notebook then shows each person's debts.

---

## 2. Requirements I ask the interviewer

1. Split types? -> *Equal, exact amounts, and percentages.*
2. Users and groups? -> *Users only for the core. Groups are an extension.*
3. Show balances? -> *For one user and for everyone: "A owes B 250".*
4. Settle up? -> *A user can record a payment that reduces a debt.*
5. Money precision? -> *Two decimals. Must not lose or invent a paisa.*
6. Debt simplification (fewest payments)? -> *Extension.*
7. Currencies? -> *One currency.*
8. Threads? -> *Yes, several people add expenses at once.*

---

## 3. A key idea: never use `float` for money

`0.1 + 0.2` in Python gives `0.30000000000000004`. Tiny errors add up and balances will not match. So we store money as **integers in the smallest unit** (paise: 1 rupee = 100 paise). 10.50 becomes 1050.

**Splitting 100.00 among 3 people:** 10000 paise / 3 = 3333 remainder 1. We cannot invent or lose one paisa. Rule: give the **leftover paise, one each, to the first people**. The shares are 3334, 3333, 3333 and they add up to exactly 10000.

---

## 4. Classes and methods (the picture)

```text
+---------------------------------------------+
|              ExpenseManager (boss)          |
|---------------------------------------------|
| add_user(id, name)                          |
| add_expense(payer, total, users, kind, vals)|
| settle(from_user, to_user, amount)          |
| balances(user=None) -> [text]               |
| simplify() -> [(debtor, creditor, amount)]  |
+----+---------------+-------------------+----+
     | has many      | uses              | has one
     v               v                   v
+---------+   +---------------+   +--------------------+
|  User   |   | SplitStrategy |   |      Ledger        |
|---------|   | (abstract)    |   |--------------------|
| id,name |   | split(total,  |   | owes[(debtor,      |
+---------+   |  users, vals) |   |       creditor)]   |
              +-------+-------+   | add_debt(...)      |
        Equal  Exact  Percent     | net_per_user()     |
                                  +--------------------+
   SplitFactory.create("EQUAL")  -> picks the strategy (Factory pattern)
   Expense(payer, total, shares) -> a record of one expense
```

- **Strategy** for the split rule: "equal / exact / percent" is exactly the kind of thing the interviewer will extend ("add share-based split: 2 shares for me, 1 for you").
- **Factory**: turns the text `"EQUAL"` into the right strategy object, so `add_expense` has no `if/elif`.
- **Ledger** is its own class: it owns the rule "net out opposite debts", so the manager does not need to know it.

---

## 5. Full code

```python
import heapq                                   # a heap gives the biggest debtor / creditor quickly
import threading                               # Lock
from abc import ABC, abstractmethod            # "promise" classes
from collections import defaultdict            # dictionary that makes missing keys equal 0


def fmt(paise):
    # show integer paise as text with two decimals, e.g. 1050 -> "10.50"
    sign = "-" if paise < 0 else ""
    paise = abs(paise)
    return sign + str(paise // 100) + "." + str(paise % 100).zfill(2)


class User:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name


class ExpenseError(Exception):                 # any invalid input
    pass


# ---------- split strategies ----------
# Each strategy returns a dict: user_id -> share in paise. The shares must add up to the total.

class SplitStrategy(ABC):
    @abstractmethod
    def split(self, total, users, values):
        pass


class EqualSplit(SplitStrategy):
    def split(self, total, users, values):
        n = len(users)
        base, extra = divmod(total, n)         # base for everyone; "extra" paise are left over
        # the first `extra` users get one more paisa, so nothing is lost
        return {u: base + (1 if i < extra else 0) for i, u in enumerate(users)}


class ExactSplit(SplitStrategy):
    def split(self, total, users, values):
        if len(values) != len(users):
            raise ExpenseError("need one amount per user")
        if sum(values) != total:               # amounts must add up exactly
            raise ExpenseError("exact amounts " + fmt(sum(values)) + " do not match total " + fmt(total))
        return dict(zip(users, values))


class PercentSplit(SplitStrategy):
    def split(self, total, users, values):
        if len(values) != len(users) or sum(values) != 100:
            raise ExpenseError("percentages must add up to 100")
        shares = [total * p // 100 for p in values]    # round down each share
        leftover = total - sum(shares)                 # paise lost by rounding down
        for i in range(leftover):                      # give them back one by one, from the first user
            shares[i % len(shares)] += 1
        return dict(zip(users, shares))


class SplitFactory:
    _strategies = {"EQUAL": EqualSplit, "EXACT": ExactSplit, "PERCENT": PercentSplit}

    @classmethod
    def create(cls, kind):
        if kind not in cls._strategies:
            raise ExpenseError("unknown split type " + kind)
        return cls._strategies[kind]()         # build the right strategy


# ---------- records ----------

class Expense:
    def __init__(self, expense_id, payer, total, shares, note):
        self.expense_id = expense_id
        self.payer = payer                     # user_id of who paid
        self.total = total                     # paise
        self.shares = shares                   # user_id -> paise each person is responsible for
        self.note = note


class Ledger:
    """Stores the net debt between each pair of users."""
    def __init__(self):
        self.owes = defaultdict(int)           # (debtor, creditor) -> paise, always > 0 when present

    def add_debt(self, debtor, creditor, amount):
        if debtor == creditor or amount == 0:
            return                             # you cannot owe yourself
        reverse = self.owes.get((creditor, debtor), 0)
        if reverse >= amount:                  # the other person already owed me more: just reduce that
            self._set(creditor, debtor, reverse - amount)
        else:
            self._set(creditor, debtor, 0)     # cancel the reverse debt completely...
            self.owes[(debtor, creditor)] += amount - reverse   # ...and the rest is a new debt this way

    def _set(self, debtor, creditor, amount):
        if amount == 0:
            self.owes.pop((debtor, creditor), None)    # remove zero entries to keep things tidy
        else:
            self.owes[(debtor, creditor)] = amount

    def net_per_user(self):
        # positive = this user should receive money overall; negative = this user should pay overall
        net = defaultdict(int)
        for (debtor, creditor), amount in self.owes.items():
            net[debtor] -= amount
            net[creditor] += amount
        return net


# ---------- the boss ----------

class ExpenseManager:
    def __init__(self):
        self._users = {}                       # user_id -> User
        self._expenses = []                    # history
        self._ledger = Ledger()
        self._lock = threading.Lock()

    def add_user(self, user_id, name):
        with self._lock:
            self._users[user_id] = User(user_id, name)

    def _check_users(self, ids):
        for i in ids:
            if i not in self._users:
                raise ExpenseError("unknown user " + str(i))

    def add_expense(self, payer, total, users, kind="EQUAL", values=None, note=""):
        if total <= 0:
            raise ExpenseError("total must be positive")
        with self._lock:
            self._check_users([payer] + list(users))
            strategy = SplitFactory.create(kind)               # Factory picks the Strategy
            shares = strategy.split(total, list(users), values or [])
            expense = Expense(len(self._expenses) + 1, payer, total, shares, note)
            self._expenses.append(expense)
            for user, share in shares.items():                 # everyone owes the payer their share
                self._ledger.add_debt(user, payer, share)
            return expense

    def settle(self, from_user, to_user, amount):
        with self._lock:
            self._check_users([from_user, to_user])
            # paying back is the opposite of owing: it adds a debt in the reverse direction
            self._ledger.add_debt(to_user, from_user, amount)

    def balances(self, user=None):
        with self._lock:
            lines = []
            for (debtor, creditor), amount in sorted(self._ledger.owes.items()):
                if user is None or user in (debtor, creditor):
                    lines.append(self._users[debtor].name + " owes " + self._users[creditor].name + " " + fmt(amount))
            return lines or ["no balances"]

    # ----- extension: fewest payments to settle everything -----
    def simplify(self):
        with self._lock:
            net = self._ledger.net_per_user()
            creditors = [(-amt, u) for u, amt in net.items() if amt > 0]   # max-heap trick: store negatives
            debtors = [(amt, u) for u, amt in net.items() if amt < 0]      # most negative first
            heapq.heapify(creditors)
            heapq.heapify(debtors)
            payments = []
            while creditors and debtors:
                c_amt, c = heapq.heappop(creditors)                       # biggest creditor
                d_amt, d = heapq.heappop(debtors)                         # biggest debtor
                pay = min(-c_amt, -d_amt)                                 # settle as much as possible
                payments.append((self._users[d].name, self._users[c].name, pay))
                if -c_amt - pay > 0:                                      # creditor still waits for money
                    heapq.heappush(creditors, (c_amt + pay, c))
                if -d_amt - pay > 0:                                      # debtor still owes money
                    heapq.heappush(debtors, (d_amt + pay, d))
            return payments


def main():
    m = ExpenseManager()
    for uid, name in [("a", "Asha"), ("b", "Ben"), ("c", "Chen"), ("d", "Dev")]:
        m.add_user(uid, name)

    m.add_expense("a", 100000, ["a", "b", "c", "d"], "EQUAL", note="hotel 1000.00")
    print("after hotel (1000.00 equal among 4):")
    for line in m.balances(): print("  ", line)

    m.add_expense("b", 40000, ["a", "b", "c"], "EXACT", [10000, 10000, 20000], note="dinner")
    print("after dinner (Ben paid 400.00, exact 100/100/200):")
    for line in m.balances(): print("  ", line)

    e = m.add_expense("a", 10000, ["a", "b", "c"], "EQUAL", note="taxi 100.00")
    print("taxi 100.00 / 3 -> shares:", {u: fmt(s) for u, s in e.shares.items()},
          "| total of shares:", fmt(sum(e.shares.values())))

    e = m.add_expense("c", 20001, ["a", "b", "c"], "PERCENT", [50, 30, 20], note="snacks 200.01")
    print("snacks 200.01 at 50/30/20 ->", {u: fmt(s) for u, s in e.shares.items()},
          "| total of shares:", fmt(sum(e.shares.values())))

    print("Ben's view:")
    for line in m.balances("b"): print("  ", line)

    try:
        m.add_expense("a", 1000, ["a", "b"], "EXACT", [400, 400])
    except ExpenseError as err:
        print("rejected:", err)
    try:
        m.add_expense("a", 1000, ["a", "b"], "PERCENT", [60, 60])
    except ExpenseError as err:
        print("rejected:", err)

    # ---- extension: simplify ----
    print("--- extension: simplify debts ---")
    print("before: ", len(m._ledger.owes), "pairwise debts")
    for payer, receiver, amount in m.simplify():
        print("  ", payer, "pays", receiver, fmt(amount))

    m.settle("d", "a", 25000)                  # Dev pays Asha back 250.00
    print("after Dev settles with Asha:")
    for line in m.balances("d"): print("  ", line)

    # ---- thread test ----
    print("--- thread test ---")
    t = ExpenseManager()
    for uid in ["a", "b", "c"]:
        t.add_user(uid, uid.upper())
    def worker():
        for _ in range(50):
            t.add_expense("a", 3000, ["a", "b", "c"], "EQUAL")   # each share is exactly 10.00
    threads = [threading.Thread(target=worker) for _ in range(8)]
    for th in threads: th.start()
    for th in threads: th.join()
    net = t._ledger.net_per_user()
    print("B owes A:", fmt(t._ledger.owes[("b", "a")]), "(expected", fmt(400 * 1000), ")")
    print("everything sums to zero:", sum(net.values()) == 0)


if __name__ == "__main__":
    main()
```

Output I got when I ran it:

```text
after hotel (1000.00 equal among 4):
   Ben owes Asha 250.00
   Chen owes Asha 250.00
   Dev owes Asha 250.00
after dinner (Ben paid 400.00, exact 100/100/200):
   Ben owes Asha 150.00
   Chen owes Asha 250.00
   Chen owes Ben 200.00
   Dev owes Asha 250.00
taxi 100.00 / 3 -> shares: {'a': '33.34', 'b': '33.33', 'c': '33.33'} | total of shares: 100.00
snacks 200.01 at 50/30/20 -> {'a': '100.01', 'b': '60.00', 'c': '40.00'} | total of shares: 200.01
Ben's view:
   Ben owes Asha 183.33
   Chen owes Ben 140.00
rejected: exact amounts 8.00 do not match total 10.00
rejected: percentages must add up to 100
--- extension: simplify debts ---
before:  4 pairwise debts
   Chen pays Asha 323.32
   Dev pays Asha 250.00
   Ben pays Asha 43.33
after Dev settles with Asha:
   no balances
--- thread test ---
B owes A: 4000.00 (expected 4000.00 )
everything sums to zero: True
```

---

## 6. How the code works (walk through)

1. `add_expense`: the **factory** turns `"EQUAL"` into a strategy. The strategy returns `shares`, a dict of how much each user is responsible for. Then, for each user, the ledger records "user owes payer share".
2. `Ledger.add_debt` **nets** opposite debts. If Ben owes Asha 250 and then Asha owes Ben 100, the ledger stores only "Ben owes Asha 150". That keeps balances short and readable.
3. The equal split gives leftover paise to the first people. In the output, 100.00 / 3 becomes 33.34, 33.33, 33.33, which adds up to exactly 100.00.
4. `simplify` computes each person's **net** (total to receive minus total to pay), then repeatedly matches the biggest debtor with the biggest creditor. This gives at most (number of people - 1) payments.
5. `settle` is just an expense in the opposite direction.

---

## 7. How to extend it

**"Add a share-based split (2 shares, 1 share, 1 share)."** One new class `ShareSplit(SplitStrategy)` and one line in the factory dictionary. The manager is unchanged. This is the main reason for the Strategy pattern here.

**"Add groups."** A `Group` class with a set of user ids and its own `Ledger` (or one ledger and a group tag on each expense). `add_expense` takes a `group_id`.

**"Edit or delete an expense."** Keep the `Expense` list (we already do). To delete, **reverse** the effect: for each share, add the opposite debt. (Reversing is safer than recomputing everything.)

**"Multiple currencies."** `Expense` gets a `currency`. A `CurrencyConverter` interface converts to a base currency when adding to the ledger.

---

## 8. Thread-safety notes (plain words)

- **The danger:** `add_debt` is "read the reverse debt, compare, update two entries". Two threads adding expenses at the same time can both read the same old value and overwrite each other, so some expense is lost or counted twice.
- **The fix:** one lock in `ExpenseManager` for every method that changes or reads the ledger. The thread test adds 400 expenses from 8 threads and the total is exactly what we expect, and the net amounts add up to zero (a good self-check for any ledger: money is only moved, never created).
- **Better for scale:** per-group locks (expenses in different groups are independent), or a database transaction.

---

## 9. Five follow-up questions with model answers

**Q1. Why integers (paise) and not `float` or `Decimal`?**
`float` cannot represent many decimal amounts exactly, and the errors pile up. Integers in the smallest unit are exact and fast. `Decimal` is also exact and fine, but then I still must decide *who gets the leftover paisa* when dividing. With either, the leftover rule is the real design decision, and mine is "first users get one extra paisa each".

**Q2. What is the time complexity of `simplify`?**
Computing the net is O(E) for E pairwise debts. Each heap pop and push is O(log N) for N users, and each step settles at least one person, so there are at most N steps. Total O(E + N log N). The result has at most N - 1 payments. Finding the **true minimum** number of payments is NP-hard (it reduces to a subset-sum type problem); this greedy method is a good practical answer.

**Q3. What if a user is removed from a group but still owes money?**
Do not delete the user record; mark it inactive. Their debts stay in the ledger, and they can still settle. Deleting would make balances point to someone who does not exist.

**Q4. How do you show a history of "who paid what"?**
We keep every `Expense` in a list. A method `history(user_id)` filters expenses where the user is the payer or has a share. For large data, index by user id (a dictionary `user_id -> list of expenses`).

**Q5. Why not store only each user's net balance and skip the pairwise ledger?**
Net balances are enough for `simplify`, but users want to see "you owe Ben 150" (a specific person). The pairwise ledger keeps that. It also keeps a privacy-friendly view: a user sees only debts that involve them.

---

**Next:** `19_logger_and_notification_system.md`.
