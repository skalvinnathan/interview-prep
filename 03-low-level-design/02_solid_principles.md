# 02 - SOLID principles

SOLID is a set of 5 rules for writing classes that are **easy to change**. Each letter is one rule. Interviewers love to ask "which SOLID principle does your design follow?"

| Letter | Name | One-line meaning |
|---|---|---|
| S | Single Responsibility | One class, one reason to change |
| O | Open/Closed | Add new behaviour by adding code, not by editing old code |
| L | Liskov Substitution | A child must work wherever the parent works |
| I | Interface Segregation | Many small promises are better than one huge promise |
| D | Dependency Inversion | Depend on a promise (interface), not on a concrete class |

All code below was run with Python 3.9. Output is real.

---

## S - Single Responsibility Principle (SRP)

**Meaning:** A class should have **one job**, so only **one reason to change**.

**Analogy.** A restaurant has a cook, a waiter and a cashier. If one person does all three, a problem in one job slows the others. If the menu changes, only the cook changes.

**Bad: one class does three jobs (business rule, saving, printing).**

```python
class OrderBad:
    def __init__(self, items):
        self.items = items                      # list of (name, price)

    def total(self):                            # job 1: calculate the price
        return sum(p for _, p in self.items)

    def save_to_db(self):                       # job 2: storage
        return "saved " + str(len(self.items)) + " items to DB"

    def print_invoice(self):                    # job 3: how it looks
        return "INVOICE total=" + str(self.total())

# If the database changes, OR the invoice format changes, OR the price rule changes,
# we must open this same class three times. More edits = more bugs.
o = OrderBad([("pen", 10), ("book", 90)])
print(o.total(), "|", o.save_to_db(), "|", o.print_invoice())
```

Output I got when I ran it:

```text
100 | saved 2 items to DB | INVOICE total=100
```

**Good: three small classes.**

```python
class Order:                                    # only knows the order data and price rule
    def __init__(self, items):
        self.items = items

    def total(self):
        return sum(p for _, p in self.items)

class OrderRepository:                          # only knows how to save
    def save(self, order):
        return "saved " + str(len(order.items)) + " items to DB"

class InvoicePrinter:                           # only knows how to print
    def render(self, order):
        return "INVOICE total=" + str(order.total())

o = Order([("pen", 10), ("book", 90)])
print(o.total(), "|", OrderRepository().save(o), "|", InvoicePrinter().render(o))
```

Output I got when I ran it:

```text
100 | saved 2 items to DB | INVOICE total=100
```

**Test for SRP:** say the class in one sentence **without using the word "and"**.

---

## O - Open/Closed Principle (OCP)

**Meaning:** Classes should be **open for extension** (you can add new things) and **closed for modification** (you do not edit working code).

**Analogy.** A phone with a USB port. To add a new device you plug it in. You do not open the phone and re-solder it.

**Bad: every new discount means editing this function.**

```python
def price_after_discount_bad(kind, price):
    if kind == "student":
        return price * 0.9
    elif kind == "senior":
        return price * 0.8
    # new "festival" discount? Edit here again and risk breaking student/senior.
    return price

print(price_after_discount_bad("student", 100), price_after_discount_bad("senior", 100))
```

Output I got when I ran it:

```text
90.0 80.0
```

**Good: each discount is a class with the same method. Add a class, change nothing old.**

```python
from abc import ABC, abstractmethod

class Discount(ABC):                            # the promise
    @abstractmethod
    def apply(self, price):
        pass

class StudentDiscount(Discount):
    def apply(self, price):
        return price * 0.9

class SeniorDiscount(Discount):
    def apply(self, price):
        return price * 0.8

class FestivalDiscount(Discount):               # NEW rule: just a new class, nothing else edited
    def apply(self, price):
        return price - 15

def checkout(price, discount):                  # this function is "closed": it never changes
    return discount.apply(price)

for d in [StudentDiscount(), SeniorDiscount(), FestivalDiscount()]:
    print(d.__class__.__name__, checkout(100, d))
```

Output I got when I ran it:

```text
StudentDiscount 90.0
SeniorDiscount 80.0
FestivalDiscount 85
```

This is the idea behind the **Strategy** pattern (file 03).

---

## L - Liskov Substitution Principle (LSP)

**Meaning:** If code works with a parent, it must also work with **any child** of that parent, without surprises. A child must not break the parent's promise.

**Analogy.** If you rent a "car" you expect it to drive. If the company gives you a "car" with no engine, it is not a real car, even if it has four wheels.

**Bad: `Penguin` is a `Bird`, but it cannot fly. Code that calls `fly()` on every bird crashes.**

```python
class Bird:
    def fly(self):
        return "flying"

class Sparrow(Bird):
    pass

class Penguin(Bird):
    def fly(self):
        raise Exception("penguins cannot fly!")   # breaks the parent's promise

def send_all_birds_up(birds):
    return [b.fly() for b in birds]               # works for a parent, so should work for children

try:
    print(send_all_birds_up([Sparrow(), Penguin()]))
except Exception as e:
    print("crash:", e)
```

Output I got when I ran it:

```text
crash: penguins cannot fly!
```

**Good: split the promise. Only birds that can fly get `fly()`.**

```python
class Bird:
    def eat(self):
        return "eating"

class FlyingBird(Bird):                           # the flying promise lives only here
    def fly(self):
        return "flying"

class Sparrow(FlyingBird):
    pass

class Penguin(Bird):                              # a bird, but not a FlyingBird: no fake promise
    def swim(self):
        return "swimming"

def send_all_birds_up(birds):
    return [b.fly() for b in birds]               # only accepts FlyingBird objects

print(send_all_birds_up([Sparrow(), Sparrow()]))
print(Penguin().swim())
```

Output I got when I ran it:

```text
['flying', 'flying']
swimming
```

**Warning signs of an LSP break:** a child that raises "not supported", or does nothing for a parent method. In LLD, this often means your inheritance tree is wrong. Use composition or split the interface.

---

## I - Interface Segregation Principle (ISP)

**Meaning:** Do not force a class to implement methods it does not need. Make **small, focused** interfaces.

**Analogy.** A TV remote with 80 buttons when you use 5. Better: a small remote for each job.

**Bad: one fat interface. A simple printer must fake `scan()` and `fax()`.**

```python
from abc import ABC, abstractmethod

class MultiFunctionDevice(ABC):
    @abstractmethod
    def print_doc(self): pass
    @abstractmethod
    def scan_doc(self): pass
    @abstractmethod
    def fax_doc(self): pass

class SimplePrinterBad(MultiFunctionDevice):
    def print_doc(self):
        return "printing"
    def scan_doc(self):
        raise NotImplementedError("I cannot scan")   # forced to write junk
    def fax_doc(self):
        raise NotImplementedError("I cannot fax")    # forced to write junk

p = SimplePrinterBad()
print(p.print_doc())
try:
    p.scan_doc()
except NotImplementedError as e:
    print("junk method:", e)
```

Output I got when I ran it:

```text
printing
junk method: I cannot scan
```

**Good: small interfaces. Each class picks only what it can do.**

```python
from abc import ABC, abstractmethod

class Printer(ABC):
    @abstractmethod
    def print_doc(self): pass

class Scanner(ABC):
    @abstractmethod
    def scan_doc(self): pass

class SimplePrinter(Printer):                       # only the promise it can keep
    def print_doc(self):
        return "printing"

class OfficeMachine(Printer, Scanner):              # can join several small promises
    def print_doc(self):
        return "printing"
    def scan_doc(self):
        return "scanning"

print(SimplePrinter().print_doc())
m = OfficeMachine()
print(m.print_doc(), "and", m.scan_doc())
```

Output I got when I ran it:

```text
printing
printing and scanning
```

---

## D - Dependency Inversion Principle (DIP)

**Meaning:** High-level code (the boss) should not depend on low-level details (the worker). Both should depend on a **promise (interface)**. And you **give** the worker to the boss from outside (this is called *dependency injection*, which just means "pass it in the constructor").

**Analogy.** A lamp depends on the **socket shape**, not on the power station. You can change the power station (coal, solar) and the lamp still works.

**Bad: `Notifier` builds its own `EmailSender` inside. You cannot switch to SMS or test it without sending real emails.**

```python
class EmailSender:
    def send(self, msg):
        return "EMAIL: " + msg

class NotifierBad:
    def __init__(self):
        self.sender = EmailSender()        # hard-wired! locked to email forever

    def notify(self, msg):
        return self.sender.send(msg)

print(NotifierBad().notify("hello"))
```

Output I got when I ran it:

```text
EMAIL: hello
```

**Good: depend on a promise, pass the worker in.**

```python
from abc import ABC, abstractmethod

class Sender(ABC):                          # the promise
    @abstractmethod
    def send(self, msg): pass

class EmailSender(Sender):
    def send(self, msg):
        return "EMAIL: " + msg

class SmsSender(Sender):
    def send(self, msg):
        return "SMS: " + msg

class FakeSender(Sender):                   # for tests: records instead of sending
    def __init__(self):
        self.sent = []
    def send(self, msg):
        self.sent.append(msg)
        return "recorded"

class Notifier:
    def __init__(self, sender):             # the worker is passed IN (injection)
        self.sender = sender

    def notify(self, msg):
        return self.sender.send(msg)

print(Notifier(EmailSender()).notify("hello"))
print(Notifier(SmsSender()).notify("hello"))
fake = FakeSender()
Notifier(fake).notify("test message")       # easy to test: no real email sent
print("fake got:", fake.sent)
```

Output I got when I ran it:

```text
EMAIL: hello
SMS: hello
fake got: ['test message']
```

---

## How to talk about SOLID in an interview

Do not recite the letters. Say it **when it happens in your design**:

- "I keep `PricingStrategy` separate from `Ticket`, so each has one reason to change (SRP)."
- "A new pricing rule is a new class. I do not edit old code (OCP)."
- "`Elevator` receives its scheduler in the constructor, so I can swap it or test it (DIP)."

**Next:** `03_design_patterns_you_need.md`.
