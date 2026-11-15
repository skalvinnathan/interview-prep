# 01 - OOP in plain words

OOP means **Object-Oriented Programming**. It is a way to organise code so that it looks like things in real life.

Every code block in this file was run with Python 3.9. The output shown is real.

Words you will see: **attribute** = a piece of data inside an object (like a name). **Method** = a function inside a class. **`self`** = "this object itself".

---

## 1. Class and object

**Analogy.** A class is a **cookie cutter**. An object is a **cookie** made with it. One cutter can make many cookies. Each cookie can have different sprinkles.

- **Class** = the blueprint (what data it has, what it can do).
- **Object** (also called *instance*) = one real thing made from the blueprint.

```python
class Dog:
    # __init__ runs once when we create a Dog. It sets the starting data.
    def __init__(self, name, age):
        self.name = name   # attribute: every dog has its own name
        self.age = age     # attribute: every dog has its own age

    # a method: something a dog can do
    def bark(self):
        return self.name + " says woof"

# create two objects (two cookies) from one class (one cutter)
rex = Dog("Rex", 3)
bella = Dog("Bella", 5)

print(rex.bark())    # uses rex's own name
print(bella.bark())  # uses bella's own name
print(rex is bella)  # False: they are two different objects
```

Output I got when I ran it:

```text
Rex says woof
Bella says woof
False
```

**In an interview:** classes are your *nouns* (`Vehicle`, `Ticket`, `Elevator`). Objects are the real things at run time.

---

## 2. Encapsulation (hide the inside)

**Big word, simple idea:** keep the data **inside** the class and let outsiders change it **only through methods** that check the rules.

**Analogy.** A bank ATM. You cannot reach into the cash box. You press buttons. The machine checks your PIN and balance first.

**Bad: anyone can break the rule.**

```python
class BadAccount:
    def __init__(self):
        self.balance = 100   # public: anyone can change it directly

acct = BadAccount()
acct.balance = -5000         # nobody stops this! The rule "no negative money" is broken
print("bad balance:", acct.balance)
```

Output I got when I ran it:

```text
bad balance: -5000
```

**Good: data is hidden, a method protects the rule.**

```python
class Account:
    def __init__(self, opening_balance):
        # a leading underscore means "private, please do not touch from outside"
        # (Python does not force it; it is a promise between programmers)
        self._balance = opening_balance

    def withdraw(self, amount):
        # the rule lives in ONE place
        if amount <= 0:
            raise ValueError("amount must be positive")
        if amount > self._balance:
            raise ValueError("not enough money")
        self._balance -= amount

    def balance(self):
        # outsiders can read the balance, but cannot set it directly
        return self._balance

acct = Account(100)
acct.withdraw(30)
print("balance:", acct.balance())
try:
    acct.withdraw(500)       # the rule stops us
except ValueError as e:
    print("blocked:", e)
```

Output I got when I ran it:

```text
balance: 70
blocked: not enough money
```

**Why interviewers like it:** when the rule is in one place, you fix a bug in one place.

---

## 3. Inheritance (is-a) vs composition (has-a)

### Inheritance: "is-a"

A child class **gets everything** from a parent class, and can add or change things.

**Analogy.** A `Car` *is a* `Vehicle`. A `Bike` *is a* `Vehicle`. All vehicles have a plate number.

```python
class Vehicle:
    def __init__(self, plate):
        self.plate = plate           # every vehicle has a plate

    def describe(self):
        return "Vehicle " + self.plate

class Car(Vehicle):                  # Car inherits from Vehicle
    def wheels(self):
        return 4                     # new method only for Car

class Bike(Vehicle):
    def wheels(self):
        return 2

c = Car("KA01-1234")
print(c.describe(), "has", c.wheels(), "wheels")   # describe() came from Vehicle
```

Output I got when I ran it:

```text
Vehicle KA01-1234 has 4 wheels
```

### Composition: "has-a"

An object **holds other objects** and asks them to do work.

**Analogy.** A car *has an* engine. A car is **not** an engine. If you want a new engine, you swap the engine. You do not rebuild the whole car.

**Bad: inheritance used for the wrong reason.** A `Stack` is not a `list`. If it inherits from `list`, users can call `insert(0, x)` and break the stack rules.

```python
class BadStack(list):          # "is-a list": too much power leaks out
    def push(self, x):
        self.append(x)

s = BadStack()
s.push(1)
s.push(2)
s.insert(0, 99)                # a stack must not allow this! It breaks the rule "only top changes"
print("bad stack:", list(s))
```

Output I got when I ran it:

```text
bad stack: [99, 1, 2]
```

**Good: composition. The stack HAS a list, and shows only what it wants.**

```python
class Stack:
    def __init__(self):
        self._items = []       # has-a list, hidden inside

    def push(self, x):
        self._items.append(x)

    def pop(self):
        return self._items.pop()   # only the top can leave

s = Stack()
s.push(1)
s.push(2)
print("popped:", s.pop())
print("has insert method?", hasattr(s, "insert"))   # False: users cannot break the rule
```

Output I got when I ran it:

```text
popped: 2
has insert method? False
```

**Rule of thumb:** *Prefer composition over inheritance.* Use inheritance only when it is truly "is-a" **and** the child can do everything the parent can (this is the Liskov rule in file 02).

---

## 4. Polymorphism ("many shapes")

**Idea:** you call the **same method name** on different objects, and each object does it **in its own way**. The caller does not need `if` checks.

**Analogy.** You say "make a sound" to a dog, a cat and a cow. Each answers differently. You do not need to know the animal type before you ask.

**Bad: `if/elif` on type. Add a new animal and you must edit this function.**

```python
def make_sound_bad(animal_type):
    if animal_type == "dog":
        return "woof"
    elif animal_type == "cat":
        return "meow"
    # new animal? you must come back and edit this function every time
    return "?"

print(make_sound_bad("dog"), make_sound_bad("cow"))
```

Output I got when I ran it:

```text
woof ?
```

**Good: each class knows its own sound.**

```python
class Dog:
    def sound(self):
        return "woof"

class Cat:
    def sound(self):
        return "meow"

class Cow:                      # new animal: we add a class, we change NOTHING else
    def sound(self):
        return "moo"

def make_sound(animal):
    return animal.sound()       # same call, different behaviour

for a in [Dog(), Cat(), Cow()]:
    print(a.__class__.__name__, "->", make_sound(a))
```

Output I got when I ran it:

```text
Dog -> woof
Cat -> meow
Cow -> moo
```

**In an interview:** whenever you want to write `if kind == ...` many times, stop and think: "Should this be a class with a method?"

---

## 5. Interfaces and abstract classes

An **interface** is a **promise**: "any class that joins me will have these methods." It lists *what*, not *how*.

**Analogy.** A **power socket**. The socket promises "I give 230 volts with this plug shape". Any device with that plug works. The socket does not care if it is a lamp or a fan.

In Python we make this promise with `abc` (Abstract Base Class).
An **abstract class** can have a mix: some methods only promise (abstract), some already have code.

```python
from abc import ABC, abstractmethod

class PaymentMethod(ABC):                  # ABC = "this is a promise class"
    @abstractmethod
    def pay(self, amount):                 # abstract: no body, children MUST write it
        pass

    def receipt(self, amount):             # normal method: shared code that children get free
        return "Paid " + str(amount) + " using " + self.__class__.__name__

class Card(PaymentMethod):
    def pay(self, amount):
        return "charged card " + str(amount)

class Upi(PaymentMethod):
    def pay(self, amount):
        return "sent UPI " + str(amount)

class Broken(PaymentMethod):
    pass                                    # forgot to write pay()

for m in [Card(), Upi()]:
    print(m.pay(100), "|", m.receipt(100))

try:
    Broken()                                # Python refuses to build an incomplete class
except TypeError as e:
    print("error:", e)
```

Output I got when I ran it:

```text
charged card 100 | Paid 100 using Card
sent UPI 100 | Paid 100 using Upi
error: Can't instantiate abstract class Broken with abstract method pay
```

**Interface vs abstract class (simple):**

| | Interface idea | Abstract class |
|---|---|---|
| Has code? | No, only promises | Can have some code |
| Use when | Many unrelated classes need the same ability | Related classes share some code |

Python has no special `interface` keyword. We use an `ABC` with only abstract methods.

---

## 6. Quick summary

| Word | One-line meaning | Daily life |
|---|---|---|
| Class | blueprint | cookie cutter |
| Object | one real thing | one cookie |
| Encapsulation | hide data, guard with methods | ATM |
| Inheritance | child gets parent's stuff (is-a) | car is a vehicle |
| Composition | object holds other objects (has-a) | car has an engine |
| Polymorphism | same call, different behaviour | "make a sound" |
| Interface / abstract | a promise of methods | power socket |

**Next:** `02_solid_principles.md`.
