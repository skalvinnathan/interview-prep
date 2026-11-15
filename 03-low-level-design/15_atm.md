# 15 - ATM

Python 3.9. All code was run; the output is real.

---

## 1. The problem in plain words

An ATM (Automated Teller Machine) lets a bank customer put in a **card**, type a **PIN** (secret number), and then **check balance**, **withdraw cash**, or **deposit**. If the PIN is wrong three times, the card is blocked.

**Analogy.** A bank clerk behind glass: first asks "show your card", then "say your secret number", only then does the real work. If you cannot say the number, she keeps the card.

Two ideas make this design clean:

- **State pattern**: what the ATM does for a button depends on whether a card is in, and whether the PIN was accepted (like the vending machine, file 14).
- **Command pattern**: each transaction (withdraw, deposit, balance) is an **object** with an `execute()` method. So adding "transfer money" is a new class, and every transaction can be recorded in a history.

---

## 2. Requirements I ask the interviewer

1. Which operations? -> *Balance check, withdraw, deposit.*
2. PIN rule? -> *3 wrong attempts: card blocked, session ends.*
3. Where is the money truth stored? -> *In the bank, behind an interface. The ATM only calls it (the bank is "another service").*
4. Cash in the ATM? -> *Limited notes of 500, 200, 100. It must refuse amounts it cannot pay.*
5. What if the bank debit works but the cash does not come out? -> *Must never happen: plan the notes first, then debit, then dispense.*
6. Limits (daily limit)? -> *Extension.*
7. Many ATMs on the same account at the same time? -> *Yes: the bank must stay correct.*
8. Out of scope? -> *Hardware, network protocols, encryption, receipts.*

---

## 3. Classes and methods (the picture)

```text
                        +--------------------------------+
                        |              ATM               |
                        |--------------------------------|
                        | state, card_no, history, rules |
                        | insert_card(card_no)           |
                        | enter_pin(pin)                 |
                        | withdraw(amt) deposit(amt)     |
                        | check_balance() eject_card()   |
                        +---+------------+----------+----+
                has one     |            | uses     | uses
             (State)        v            v          v
 +-----------------+  +-------------+ +-----------------+  +------------------+
 | ATMState (base) |  | BankService | | CashDispenser   |  | WithdrawalRule   |
 +--------+--------+  | (abstract)  | | plan(amount)    |  | (Strategy, ext.) |
   Idle  PinEntry Menu | verify_pin  | | commit(plan)    |  | check / record   |
                      | debit/credit|  +-----------------+  +------------------+
                      +------+------+
                       InMemoryBank
                                          Command objects:
                                          WithdrawCommand, DepositCommand,
                                          BalanceCommand  -> execute(atm)
```

State flow:

```text
Idle --insert_card--> PinEntry --correct PIN--> Menu --eject--> Idle
                         |  3 wrong PINs: card blocked, back to Idle
```

---

## 4. Full code

```python
import threading                               # Locks
from abc import ABC, abstractmethod            # "promise" classes


class InsufficientFunds(Exception):            # raised by the bank when the balance is too low
    pass


# ---------- the bank side (a separate service; the ATM talks to it through an interface) ----------

class BankService(ABC):
    @abstractmethod
    def is_blocked(self, card_no): pass
    @abstractmethod
    def verify_pin(self, card_no, pin): pass
    @abstractmethod
    def block_card(self, card_no): pass
    @abstractmethod
    def balance(self, card_no): pass
    @abstractmethod
    def debit(self, card_no, amount): pass
    @abstractmethod
    def credit(self, card_no, amount): pass


class Account:
    def __init__(self, pin, balance):
        self.pin = pin                         # DEMO ONLY: real banks never store a plain PIN (they use hashes / secure hardware)
        self.balance = balance
        self.lock = threading.Lock()           # protects this one account's balance


class InMemoryBank(BankService):
    def __init__(self):
        self._accounts = {}                    # card_no -> Account
        self._blocked = set()

    def add_account(self, card_no, pin, balance):
        self._accounts[card_no] = Account(pin, balance)

    def is_blocked(self, card_no):
        return card_no in self._blocked

    def verify_pin(self, card_no, pin):
        acc = self._accounts.get(card_no)
        return acc is not None and acc.pin == pin

    def block_card(self, card_no):
        self._blocked.add(card_no)

    def balance(self, card_no):
        return self._accounts[card_no].balance

    def debit(self, card_no, amount):
        acc = self._accounts[card_no]
        with acc.lock:                         # "check balance then subtract" must be one step
            if acc.balance < amount:
                raise InsufficientFunds()
            acc.balance -= amount

    def credit(self, card_no, amount):
        acc = self._accounts[card_no]
        with acc.lock:
            acc.balance += amount


# ---------- cash inside the machine ----------

class CashDispenser:
    def __init__(self, notes):
        self.notes = dict(notes)               # denomination -> count, e.g. {500: 4, 200: 5, 100: 10}
        self._lock = threading.Lock()

    def plan(self, amount):
        # decide which notes to give WITHOUT removing them yet (biggest notes first)
        with self._lock:
            remaining = amount
            result = {}
            for d in sorted(self.notes, reverse=True):
                use = min(remaining // d, self.notes[d])   # as many as we need and have
                if use:
                    result[d] = use
                    remaining -= use * d
            return result if remaining == 0 else None      # None = cannot pay this exact amount

    def commit(self, plan):
        with self._lock:                       # now really remove the notes
            for d, n in plan.items():
                self.notes[d] -= n


# ---------- transaction rules (Strategy; empty by default) ----------

class WithdrawalRule(ABC):
    @abstractmethod
    def check(self, card_no, amount):          # return None if OK, or an error text
        pass
    def record(self, card_no, amount):         # called after a successful withdrawal
        pass


# ---------- transactions as Command objects ----------

class Command(ABC):
    name = "COMMAND"
    @abstractmethod
    def execute(self, atm):
        pass


class BalanceCommand(Command):
    name = "BALANCE"
    def execute(self, atm):
        return "balance " + str(atm.bank.balance(atm.card_no))


class DepositCommand(Command):
    name = "DEPOSIT"
    def __init__(self, amount):
        self.amount = amount
    def execute(self, atm):
        if self.amount <= 0:
            return "invalid amount"
        atm.bank.credit(atm.card_no, self.amount)
        return "deposited " + str(self.amount)


class WithdrawCommand(Command):
    name = "WITHDRAW"
    def __init__(self, amount):
        self.amount = amount
    def execute(self, atm):
        if self.amount <= 0:
            return "invalid amount"
        for rule in atm.rules:                 # extra rules (daily limit etc.)
            problem = rule.check(atm.card_no, self.amount)
            if problem:
                return problem
        plan = atm.dispenser.plan(self.amount)         # step 1: can we pay in notes? (nothing changes yet)
        if plan is None:
            return "ATM cannot pay this amount"
        try:
            atm.bank.debit(atm.card_no, self.amount)   # step 2: take money from the account
        except InsufficientFunds:
            return "insufficient funds"
        atm.dispenser.commit(plan)                     # step 3: give notes (cannot fail: we planned them)
        for rule in atm.rules:
            rule.record(atm.card_no, self.amount)
        return "dispensed " + str(self.amount) + " as " + str(plan)


# ---------- ATM states ----------

class ATMState:
    name = "STATE"
    # defaults: every action is refused unless a state overrides it
    def insert_card(self, atm, card_no): return "not allowed now (" + self.name + ")"
    def enter_pin(self, atm, pin):       return "not allowed now (" + self.name + ")"
    def perform(self, atm, command):     return "not allowed now (" + self.name + ")"
    def eject(self, atm):                return "no card"


class IdleState(ATMState):
    name = "IDLE"
    def insert_card(self, atm, card_no):
        if atm.bank.is_blocked(card_no):
            return "card is blocked, contact your bank"
        atm.card_no = card_no
        atm.pin_attempts = 0
        atm.state = PinEntryState()
        return "enter PIN"


class PinEntryState(ATMState):
    name = "PIN_ENTRY"
    MAX_ATTEMPTS = 3
    def enter_pin(self, atm, pin):
        if atm.bank.verify_pin(atm.card_no, pin):
            atm.state = MenuState()
            return "welcome"
        atm.pin_attempts += 1
        if atm.pin_attempts >= self.MAX_ATTEMPTS:
            atm.bank.block_card(atm.card_no)   # too many wrong tries
            atm.reset()
            return "wrong PIN, card blocked"
        return "wrong PIN, " + str(self.MAX_ATTEMPTS - atm.pin_attempts) + " tries left"
    def eject(self, atm):
        atm.reset()
        return "card returned"


class MenuState(ATMState):
    name = "MENU"
    def perform(self, atm, command):
        result = command.execute(atm)          # the command does the real work
        atm.history.append((command.name, result))     # every transaction is recorded
        return result
    def eject(self, atm):
        atm.reset()
        return "card returned"


# ---------- the ATM ----------

class ATM:
    def __init__(self, bank, dispenser, rules=None):
        self.bank = bank
        self.dispenser = dispenser
        self.rules = rules or []               # list of WithdrawalRule
        self.state = IdleState()
        self.card_no = None
        self.pin_attempts = 0
        self.history = []
        self._lock = threading.RLock()

    def reset(self):
        self.card_no = None                    # forget the customer completely
        self.pin_attempts = 0
        self.state = IdleState()

    # public API: lock, then let the current state decide
    def insert_card(self, card_no):
        with self._lock: return self.state.insert_card(self, card_no)
    def enter_pin(self, pin):
        with self._lock: return self.state.enter_pin(self, pin)
    def withdraw(self, amount):
        with self._lock: return self.state.perform(self, WithdrawCommand(amount))
    def deposit(self, amount):
        with self._lock: return self.state.perform(self, DepositCommand(amount))
    def check_balance(self):
        with self._lock: return self.state.perform(self, BalanceCommand())
    def eject_card(self):
        with self._lock: return self.state.eject(self)


# ---------- EXTENSION: a daily withdrawal limit (new class only) ----------

class DailyLimitRule(WithdrawalRule):
    def __init__(self, limit):
        self.limit = limit
        self.used = {}                         # card_no -> amount withdrawn today
    def check(self, card_no, amount):
        if self.used.get(card_no, 0) + amount > self.limit:
            return "daily limit " + str(self.limit) + " exceeded"
        return None
    def record(self, card_no, amount):
        self.used[card_no] = self.used.get(card_no, 0) + amount


class TransferCommand(Command):                # EXTENSION: new transaction = new Command class
    name = "TRANSFER"
    def __init__(self, to_card, amount):
        self.to_card = to_card
        self.amount = amount
    def execute(self, atm):
        try:
            atm.bank.debit(atm.card_no, self.amount)
        except InsufficientFunds:
            return "insufficient funds"
        atm.bank.credit(self.to_card, self.amount)
        return "transferred " + str(self.amount) + " to " + self.to_card


def main():
    bank = InMemoryBank()
    bank.add_account("CARD-1", "1234", 5000)
    bank.add_account("CARD-2", "9999", 800)
    atm = ATM(bank, CashDispenser({500: 20, 200: 5, 100: 10}))

    print("withdraw without card ->", atm.withdraw(100))
    print("insert card   ->", atm.insert_card("CARD-1"))
    print("wrong PIN     ->", atm.enter_pin("0000"))
    print("right PIN     ->", atm.enter_pin("1234"))
    print("balance       ->", atm.check_balance())
    print("withdraw 1700 ->", atm.withdraw(1700))
    print("withdraw 25   ->", atm.withdraw(25))
    print("withdraw 6000 ->", atm.withdraw(6000))
    print("deposit 300   ->", atm.deposit(300))
    print("balance       ->", atm.check_balance())
    print("eject         ->", atm.eject_card())
    print("history       ->", atm.history)

    print("--- three wrong PINs ---")
    print(atm.insert_card("CARD-2"))
    for _ in range(3):
        print(atm.enter_pin("1111"))
    print("insert again  ->", atm.insert_card("CARD-2"))

    # ---- known weakness of the greedy note plan ----
    print("--- greedy weakness ---")
    print("plan 600 with {500: 1, 200: 3} ->", CashDispenser({500: 1, 200: 3}).plan(600),
          "(but 3 x 200 would work!)")

    # ---- extension demo ----
    print("--- extension: daily limit + transfer ---")
    atm2 = ATM(bank, CashDispenser({500: 10}), rules=[DailyLimitRule(1000)])
    atm2.insert_card("CARD-1"); atm2.enter_pin("1234")
    print(atm2.withdraw(500))
    print(atm2.withdraw(500))
    print(atm2.withdraw(500))                  # would reach 1500 > limit 1000
    print(atm2.state.perform(atm2, TransferCommand("CARD-2", 250)))
    print("CARD-2 balance now:", bank.balance("CARD-2"))

    # ---- thread test: 10 ATMs withdraw 200 each from one account that holds 1000 ----
    print("--- thread test ---")
    bank3 = InMemoryBank()
    bank3.add_account("SHARED", "1", 1000)
    results = []
    def user():
        a = ATM(bank3, CashDispenser({200: 50}))       # each thread has its own ATM, same bank account
        a.insert_card("SHARED"); a.enter_pin("1")
        results.append(a.withdraw(200))
    threads = [threading.Thread(target=user) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
    ok = sum(1 for r in results if r.startswith("dispensed"))
    print("successful withdrawals:", ok, "| final balance:", bank3.balance("SHARED"))


if __name__ == "__main__":
    main()
```

Output I got when I ran it:

```text
withdraw without card -> not allowed now (IDLE)
insert card   -> enter PIN
wrong PIN     -> wrong PIN, 2 tries left
right PIN     -> welcome
balance       -> balance 5000
withdraw 1700 -> dispensed 1700 as {500: 3, 200: 1}
withdraw 25   -> ATM cannot pay this amount
withdraw 6000 -> insufficient funds
deposit 300   -> deposited 300
balance       -> balance 3600
eject         -> card returned
history       -> [('BALANCE', 'balance 5000'), ('WITHDRAW', 'dispensed 1700 as {500: 3, 200: 1}'), ('WITHDRAW', 'ATM cannot pay this amount'), ('WITHDRAW', 'insufficient funds'), ('DEPOSIT', 'deposited 300'), ('BALANCE', 'balance 3600')]
--- three wrong PINs ---
enter PIN
wrong PIN, 2 tries left
wrong PIN, 1 tries left
wrong PIN, card blocked
insert again  -> card is blocked, contact your bank
--- greedy weakness ---
plan 600 with {500: 1, 200: 3} -> None (but 3 x 200 would work!)
--- extension: daily limit + transfer ---
dispensed 500 as {500: 1}
dispensed 500 as {500: 1}
daily limit 1000 exceeded
transferred 250 to CARD-2
CARD-2 balance now: 1050
--- thread test ---
successful withdrawals: 5 | final balance: 0
```

---

## 5. How the code works (walk through)

1. `ATM` public methods lock, then call the **current state**. `IdleState` accepts only `insert_card`; `PinEntryState` only `enter_pin`; `MenuState` accepts transactions. The base class `ATMState` refuses everything by default, so each state lists only what it allows.
2. `WithdrawCommand.execute` is the key method. It has three steps in a careful order: **plan the notes** (nothing changes), **debit the account** (can fail: no change to cash), then **commit the notes** (cannot fail, as it was planned). So the bank never loses money without cash coming out, and cash never comes out without a debit.
3. The `MenuState` stores every `(command name, result)` in `history`: a free audit trail thanks to the Command pattern.
4. Three wrong PINs call `bank.block_card` and reset the ATM, so the next `insert_card` is refused.

---

## 6. How to extend it

**"Add a daily limit."** `DailyLimitRule` is a new class passed in `rules`. `WithdrawCommand` already loops over rules. (Small honest note: a real limit needs a date; here `used` never resets. Say that out loud.)

**"Add money transfer."** `TransferCommand` is a new `Command` class. No state or ATM code changes. See the extension output.

**"Add a PIN change, mini-statement, or cardless cash."** Each one is a new `Command`. For cardless cash, add a new state before `PinEntry`.

**"Support different note sets per country."** The `CashDispenser` already takes the notes in its constructor. For a smarter payout, make `plan` a Strategy (`GreedyPlan`, `MinimumNotesDP`).

---

## 7. Thread-safety notes (plain words)

- **One ATM, one customer:** the ATM has a lock so that its own state never mixes two actions.
- **Many ATMs, one account:** this is the real danger. Two ATMs read balance 1000 at the same time and both pay 200 ... eventually the account is overdrawn. **The check and the subtraction must be one atomic step**, so `debit` holds the account's lock for both. The thread test: 10 ATMs try to take 200 from 1000; exactly 5 succeed and the final balance is 0.
- **Lock order:** the ATM lock is taken first, then the bank's account lock. A thread never takes them in the other order, so they cannot deadlock.
- In a real system the bank is a remote database; the same idea is done with a transaction (`UPDATE ... SET balance = balance - 200 WHERE balance >= 200`).

---

## 8. Five follow-up questions with model answers

**Q1. Why is the order "plan notes, debit, commit notes"?**
Each step is easier to undo or cannot fail. Planning changes nothing. Debit can fail, and if it does, we stop with nothing changed. Commit of planned notes cannot fail. If I debited first and then found the ATM had no notes, I would have to reverse the debit (a *compensation*), which is more complex.

**Q2. Why Command objects, not just methods on `ATM`?**
A Command is an object, so I can store it (history), log it, or even queue or undo it. Adding "transfer" means adding one class, and the ATM and states are untouched (Open/Closed). The cost is one small class per transaction.

**Q3. What if the network to the bank goes down during a withdrawal?**
The ATM does not know if the debit happened. Use an **idempotency key**: each withdrawal gets a unique id; the bank remembers ids it already processed. After the network returns, the ATM asks "did transaction X succeed?" and either dispenses or cancels. I would mention this and not code it.

**Q4. How do you store the PIN safely?**
Never plain text. The bank stores a salted hash, and the PIN is checked inside secure hardware. In my demo, I store it in plain text only to keep the code short, and I say so.

**Q5. Is the greedy note plan always correct?**
No. Greedy takes the biggest notes first, and with **limited counts** it can fail even when a valid payout exists. The demo shows it: the ATM has one 500 note and three 200 notes, and the amount is 600. Greedy takes the 500, is left with 100, cannot pay it, and returns `None`, but three 200 notes would work. The safe general answer is dynamic programming (a "bounded coin change"), or trying other combinations when greedy fails. I would ask the interviewer if they want this; greedy plus this explanation is usually enough.

---

**Next:** `16_rate_limiter_class.md`.
