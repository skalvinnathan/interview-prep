# 14 - Vending Machine (State pattern)

Python 3.9. All code was run; the output is real.

---

## 1. The problem in plain words

A snack machine. You put money in. You choose a product. If you gave enough money, the machine drops the product and gives back change. If you change your mind, you press cancel and get your money back.

**Analogy.** The machine is like a shop assistant who behaves differently depending on **what is happening now**. If no money was given, "choose a product" means "please pay first". If money was given, the same button means "here is your snack". The same button, different behaviour, depending on the **state**. This is the reason the State pattern (file 03) fits.

---

## 2. Requirements I ask the interviewer

1. Which actions? -> *Insert money, select product, cancel (refund), refill (admin).*
2. What money? -> *Whole numbers (for example rupees); no cents. Coins/notes are all simply "amount".*
3. Does the machine keep the balance after a failed choice (not enough money)? -> *Yes, the user may add more money or cancel.*
4. Out of stock product? -> *Tell the user; keep the money in balance.*
5. Change? -> *Give back the rest. (How to split change into coins: extension.)*
6. What if the whole machine is empty? -> *Sold-out mode; refunds money if any.*
7. Admin mode? -> *Yes, as an extension.*
8. Threads? -> *One user at a time physically, but make internal state safe.*

---

## 3. States and transitions (the picture)

A **state diagram** shows the modes and which action moves you to the next mode.

```text
                   insert_money                    select_product
   +-------+  ------------------>  +-----------+  (enough money, in stock)  +------------+
   | Idle  |                       | HasMoney  | -------------------------> | Dispensing |
   +-------+  <------------------  +-----------+                            +-----+------+
       ^          cancel               ^  |  select_product (too little money        |
       |                               |  |  or out of stock) -> stay in HasMoney    |
       |                               +--+                                          |
       +------------------------------------------------------------------------------+
                         product dropped + change returned -> back to Idle
                         (or SoldOut if the machine is now empty)

   SoldOut: every action is refused until refill() -> Idle
```

Classes:

```text
+--------------------------+   has one   +----------------------+
|     VendingMachine       |-----------> |   State (abstract)   |
|--------------------------|             | insert_money(m, amt) |
| inventory, balance       |             | select_product(m, c) |
| insert_money(amt)        |             | cancel(m)            |
| select_product(code)     |             +----------+-----------+
| cancel()  refill(...)    |       Idle   HasMoney  Dispensing  SoldOut  (Maintenance: extension)
+-----------+--------------+
            | has           +--------------------+
            v               | ChangeMaker (abs.) |  Strategy: how to describe change
      +-----------+         +--------------------+
      | Inventory |
      +-----------+   Product(code, name, price)
```

---

## 4. Full code

```python
import threading                               # Lock for thread safety
from abc import ABC, abstractmethod            # "promise" classes


class Product:
    def __init__(self, code, name, price):
        self.code = code                       # button code like "A1"
        self.name = name
        self.price = price                     # whole number


class Inventory:
    def __init__(self):
        self._products = {}                    # code -> Product
        self._stock = {}                       # code -> how many left

    def add(self, product, qty):
        self._products[product.code] = product
        self._stock[product.code] = self._stock.get(product.code, 0) + qty

    def has_product(self, code):
        return code in self._products

    def get(self, code):
        return self._products[code]

    def in_stock(self, code):
        return self._stock.get(code, 0) > 0

    def take_one(self, code):
        self._stock[code] -= 1                 # one item leaves the machine

    def total_stock(self):
        return sum(self._stock.values())       # how many items in the whole machine


# ---------- change strategy ----------

class ChangeMaker(ABC):
    @abstractmethod
    def make(self, amount):
        pass


class TotalOnlyChange(ChangeMaker):            # simplest: just report the total
    def make(self, amount):
        return str(amount)


# ---------- states (State pattern) ----------

class State(ABC):
    name = "STATE"

    @abstractmethod
    def insert_money(self, m, amount):
        pass

    @abstractmethod
    def select_product(self, m, code):
        pass

    @abstractmethod
    def cancel(self, m):
        pass


class IdleState(State):
    name = "IDLE"

    def insert_money(self, m, amount):
        if amount <= 0:
            return "invalid amount"
        m.add_balance(amount)                  # take the money
        m.set_state(HasMoneyState())           # now we have money: change mode
        return "balance " + str(m.balance)

    def select_product(self, m, code):
        return "insert money first"            # same button, different behaviour

    def cancel(self, m):
        return "nothing to cancel"


class HasMoneyState(State):
    name = "HAS_MONEY"

    def insert_money(self, m, amount):
        if amount <= 0:
            return "invalid amount"
        m.add_balance(amount)
        return "balance " + str(m.balance)

    def select_product(self, m, code):
        if not m.inventory.has_product(code):
            return "unknown product " + code
        if not m.inventory.in_stock(code):
            return code + " is sold out; choose another or cancel"
        price = m.inventory.get(code).price
        if m.balance < price:
            return "need " + str(price - m.balance) + " more"   # stay in this state
        m.set_state(DispensingState())         # enough money: go to dispensing
        return m.state.dispense(m, code)       # and do it right away

    def cancel(self, m):
        refund = m.refund_all()                # give all money back
        m.set_state(IdleState())
        return "refunded " + str(refund)


class DispensingState(State):
    name = "DISPENSING"

    def dispense(self, m, code):
        product = m.inventory.get(code)
        m.inventory.take_one(code)             # remove item from stock
        change = m.balance - product.price
        m.record_sale(product.price)           # money is now revenue
        m.clear_balance()
        m.record_refund(change)                # change goes back to the user
        # choose the next mode: empty machine -> SoldOut, else Idle
        m.set_state(SoldOutState() if m.inventory.total_stock() == 0 else IdleState())
        return "dispensed " + product.name + ", change " + m.change_maker.make(change)

    # while dispensing, the machine ignores everything else
    def insert_money(self, m, amount):
        return "please wait, dispensing"

    def select_product(self, m, code):
        return "please wait, dispensing"

    def cancel(self, m):
        return "please wait, dispensing"


class SoldOutState(State):
    name = "SOLD_OUT"

    def insert_money(self, m, amount):
        return "machine empty, money not accepted"

    def select_product(self, m, code):
        return "machine empty"

    def cancel(self, m):
        return "nothing to cancel"


# ---------- the machine ----------

class VendingMachine:
    def __init__(self, inventory, change_maker=None):
        self.inventory = inventory
        self.change_maker = change_maker or TotalOnlyChange()   # default Strategy
        self.balance = 0                       # money inserted for the current purchase
        self.cash_in = 0                       # total money ever inserted (for the checks)
        self.revenue = 0                       # money kept for sold products
        self.refunded = 0                      # money given back
        self._lock = threading.RLock()
        self.state = SoldOutState() if inventory.total_stock() == 0 else IdleState()

    # --- small helpers used by the states ---
    def set_state(self, state):
        self.state = state

    def add_balance(self, amount):
        self.balance += amount
        self.cash_in += amount

    def clear_balance(self):
        self.balance = 0

    def refund_all(self):
        amount = self.balance
        self.balance = 0
        self.refunded += amount
        return amount

    def record_sale(self, price):
        self.revenue += price

    def record_refund(self, amount):
        self.refunded += amount

    # --- public API: lock, then let the current state decide ---
    def insert_money(self, amount):
        with self._lock:
            return self.state.insert_money(self, amount)

    def select_product(self, code):
        with self._lock:
            return self.state.select_product(self, code)

    def cancel(self):
        with self._lock:
            return self.state.cancel(self)

    def refill(self, product, qty):
        with self._lock:                       # admin action, allowed in Idle or SoldOut
            self.inventory.add(product, qty)
            if isinstance(self.state, SoldOutState):
                self.state = IdleState()       # back in business

    def books_balance(self):
        # accounting rule: every coin inserted is either revenue, refunded, or still in balance
        with self._lock:
            return self.cash_in == self.revenue + self.refunded + self.balance


# ---------- EXTENSION: new state and new change strategy ----------

class MaintenanceState(State):
    name = "MAINTENANCE"

    def insert_money(self, m, amount):
        return "out of service"

    def select_product(self, m, code):
        return "out of service"

    def cancel(self, m):
        return "out of service"


class GreedyChange(ChangeMaker):
    """Splits change into notes/coins, biggest first."""
    def __init__(self, denominations):
        self.denominations = sorted(denominations, reverse=True)   # e.g. [10, 5, 2, 1]

    def make(self, amount):
        parts = []
        remaining = amount
        for d in self.denominations:
            while remaining >= d:              # take as many of this size as fit
                parts.append(d)
                remaining -= d
        return str(amount) + (" = " + " + ".join(str(p) for p in parts) if parts else "")


def main():
    inv = Inventory()
    inv.add(Product("A1", "Chips", 20), 2)
    inv.add(Product("B1", "Cola", 35), 1)
    vm = VendingMachine(inv)

    print("state:", vm.state.name)
    print("select A1 first    ->", vm.select_product("A1"))
    print("insert 10          ->", vm.insert_money(10), "| state:", vm.state.name)
    print("select A1 (short)  ->", vm.select_product("A1"))
    print("insert 20          ->", vm.insert_money(20))
    print("select A1          ->", vm.select_product("A1"), "| state:", vm.state.name)
    print("insert 50, cancel  ->", vm.insert_money(50), "|", vm.cancel())
    print("insert 35, select B1 ->", vm.insert_money(35), "|", vm.select_product("B1"))
    print("insert 20, select B1 (sold out) ->", vm.insert_money(20), "|", vm.select_product("B1"))
    print("select A1 (last chips) ->", vm.select_product("A1"), "| state:", vm.state.name)
    print("insert 5           ->", vm.insert_money(5))
    vm.refill(Product("A1", "Chips", 20), 1)
    print("after refill, state:", vm.state.name)
    print("books balance:", vm.books_balance())

    # ---- extension demo ----
    print("--- extension: greedy change + maintenance state ---")
    inv2 = Inventory()
    inv2.add(Product("C1", "Biscuits", 12), 3)
    vm2 = VendingMachine(inv2, GreedyChange([10, 5, 2, 1]))
    vm2.insert_money(20)
    print(vm2.select_product("C1"))            # change 8 = 5 + 2 + 1
    vm2.set_state(MaintenanceState())          # admin switches the machine off
    print("maintenance ->", vm2.insert_money(10))

    # ---- thread test ----
    print("--- thread test ---")
    inv3 = Inventory()
    inv3.add(Product("D1", "Gum", 10), 50)
    vm3 = VendingMachine(inv3)
    def customer():
        for _ in range(100):
            vm3.insert_money(10)
            vm3.select_product("D1")
    threads = [threading.Thread(target=customer) for _ in range(8)]
    for t in threads: t.start()
    for t in threads: t.join()
    print("books balance after 8 threads:", vm3.books_balance(),
          "| gum left:", vm3.inventory._stock["D1"], "| revenue:", vm3.revenue)


if __name__ == "__main__":
    main()
```

Output I got when I ran it:

```text
state: IDLE
select A1 first    -> insert money first
insert 10          -> balance 10 | state: HAS_MONEY
select A1 (short)  -> need 10 more
insert 20          -> balance 30
select A1          -> dispensed Chips, change 10 | state: IDLE
insert 50, cancel  -> balance 50 | refunded 50
insert 35, select B1 -> balance 35 | dispensed Cola, change 0
insert 20, select B1 (sold out) -> balance 20 | B1 is sold out; choose another or cancel
select A1 (last chips) -> dispensed Chips, change 0 | state: SOLD_OUT
insert 5           -> machine empty, money not accepted
after refill, state: IDLE
books balance: True
--- extension: greedy change + maintenance state ---
dispensed Biscuits, change 8 = 5 + 2 + 1
maintenance -> out of service
--- thread test ---
books balance after 8 threads: True | gum left: 0 | revenue: 500
```

---

## 5. How the code works (walk through)

1. `VendingMachine` has one `state` object. Every public method takes the lock and passes the call to the state: `self.state.insert_money(self, amount)`. The machine **never** asks "which state am I in?". This is the State pattern.
2. A state does the action **and** chooses the next state with `m.set_state(...)`. `IdleState.insert_money` moves to `HasMoneyState`.
3. When the product is chosen and money is enough, `HasMoneyState` switches to `DispensingState`, which takes one item from stock, records the sale, returns change, then moves to `Idle` (or `SoldOut` if the machine is now empty).
4. A failed choice (too little money, sold out) keeps the user in `HasMoneyState`, so the balance is kept.
5. `books_balance()` is a small safety check: every inserted coin must be revenue, refunded, or still in the balance.

---

## 6. How to extend it

**"Add maintenance mode."** One new class, `MaintenanceState`. The machine did not change. (See the extension in the output.)

**"Give change in notes and coins."** `ChangeMaker` is a Strategy. `GreedyChange` splits the amount by denomination. Caveat to say out loud: greedy works for normal currency systems, but a real machine must also know how many coins it *has*. That needs a coin inventory, and the algorithm becomes a coin-change problem (dynamic programming).

**"Accept card or UPI."** Add a `PaymentMethod` interface; `CashPayment` is today's behaviour, `CardPayment` charges the exact price at selection time and skips the balance. The state classes call the payment method rather than touching `balance` directly.

**"Add a new product type with a pick-up delay."** Add a state or a field on `Product`; the machine itself does not change.

---

## 7. Thread-safety notes (plain words)

- A real machine serves one person at a time, but it has a coin handler, a display, a network monitor, and a refill door. They may run on different threads.
- **The danger:** `insert_money` is "read balance, add, write balance". Two threads can both read 10 and both write 20, losing a coin. Or two threads choose the last item at once and the stock goes negative.
- **The fix:** one `RLock` in the machine, taken by every public method. The state objects never lock; they run inside the machine's lock. (**One owner of the lock.**)
- The thread test inserts and buys from 8 threads at once. The accounting check `books_balance()` stays `True`.
- Note how the 8 threads share one balance. A real machine allows one customer at a time; here the test only proves that state does not get corrupted.

---

## 8. Five follow-up questions with model answers

**Q1. Why State pattern, and not just an `if state == ...` in each method?**
With `if`, every method needs a chain over all states, and adding a state (like Maintenance) means editing every method, which risks old bugs. With State, each mode is one small class, and a new mode is a new class. The cost is more classes, so for a machine with only two modes I would use a simple `if`.

**Q2. Where do the transitions live: in the machine or in the states?**
In the states (each state decides the next state). That keeps the machine simple and puts the rules next to the behaviour. The alternative is a transition table (a dictionary `(state, action) -> next_state`), which is good when there are many states and you want to see the whole graph in one place.

**Q3. What if the power fails while dispensing?**
Write the intent first: record "sale in progress" in persistent storage before moving money or items, then mark it complete. On restart, a recovery step looks for incomplete sales and either completes or refunds them. That is the idea of a *write-ahead log*. I would mention it, but stay with the in-memory design.

**Q4. How do you stop someone entering a negative amount, or 0?**
The states check `amount <= 0` and return "invalid amount". Validation lives at the edge (the entry methods), so inside the machine the balance is always sane.

**Q5. How would you test it?**
Because states are plain objects and the machine has no hidden clock or hardware, a test can create an `Inventory`, call methods in order, and assert on returned messages and `state.name`. For hardware (coin slot), I would put it behind an interface so a fake can be injected (Dependency Inversion, file 02).

---

**Next:** `15_atm.md`.
