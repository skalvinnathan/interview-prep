# 03 - The 8 design patterns you need

A **design pattern** is a named, proven way to solve a problem that comes again and again. Think of it as a **recipe**. Naming it ("I will use Strategy here") shows the interviewer you know the recipe.

**Golden rule:** use a pattern only when it solves a real problem in your design. A pattern you did not need is a mistake, not a bonus.

| Pattern | Problem it solves |
|---|---|
| Strategy | Many ways to do one thing, and you want to swap them |
| Factory | Creating the right object without `if/else` all over |
| Observer | When one thing changes, many others must be told |
| Singleton | Exactly one shared object |
| State | Behaviour depends on the current mode |
| Builder | Creating an object with many optional parts |
| Decorator | Adding extra behaviour to an object without changing its class |
| Command | Turning a request into an object (so you can queue or undo it) |

All code was run with Python 3.9. Output is real.

---

## 1. Strategy

**Analogy.** Going to the airport. You can take a bus, a taxi or a metro. The goal is the same (reach the airport); the *way* is swappable. You choose at run time.

**When to use:** you have several algorithms for one task (pricing rules, sorting, routing, payment), and rules change often.

**Bad: `if/elif` chain inside the main class.**

```python
class ParkingFeeBad:
    def fee(self, kind, hours):
        if kind == "hourly":
            return 10 * hours
        elif kind == "flat":
            return 50
        # add "weekend" rule? Edit this method again.
        return 0

print(ParkingFeeBad().fee("hourly", 3), ParkingFeeBad().fee("flat", 3))
```

Output I got when I ran it:

```text
30 50
```

**Good: each rule is its own class.**

```python
from abc import ABC, abstractmethod

class FeeStrategy(ABC):                   # the promise
    @abstractmethod
    def fee(self, hours): pass

class HourlyFee(FeeStrategy):
    def fee(self, hours):
        return 10 * hours

class FlatFee(FeeStrategy):
    def fee(self, hours):
        return 50

class WeekendFee(FeeStrategy):            # new rule = new class
    def fee(self, hours):
        return 5 * hours

class Parking:
    def __init__(self, strategy):         # the strategy is passed in
        self.strategy = strategy
    def checkout(self, hours):
        return self.strategy.fee(hours)   # Parking does not care which one

for s in [HourlyFee(), FlatFee(), WeekendFee()]:
    print(s.__class__.__name__, Parking(s).checkout(3))
```

Output I got when I ran it:

```text
HourlyFee 30
FlatFee 50
WeekendFee 15
```

**When NOT to use:** if there are only two simple options that will never grow, a plain `if` is clearer. Strategy adds classes; do not pay that cost without a need.

---

## 2. Factory

**Analogy.** You order "a coffee" at a counter. The staff decide which machine to use and hand you the cup. You do not build the machine.

**When to use:** the code that *uses* an object should not know *how* to build it, especially when you pick the class from a name or a setting.

**Bad: `if/elif` to create objects is repeated in many places.**

```python
class Car:
    def cost(self): return 40
class Bike:
    def cost(self): return 10

def make_vehicle_bad(kind):
    if kind == "car":                      # this chain gets copy-pasted in every place that makes vehicles
        return Car()
    elif kind == "bike":
        return Bike()
    raise ValueError("unknown " + kind)

print(make_vehicle_bad("car").cost())
```

Output I got when I ran it:

```text
40
```

**Good: one factory, one place to add a new type.**

```python
class Car:
    def cost(self): return 40
class Bike:
    def cost(self): return 10
class Truck:                               # new type
    def cost(self): return 80

class VehicleFactory:
    # a dictionary replaces the if/elif chain: name -> class
    _registry = {"car": Car, "bike": Bike, "truck": Truck}

    @classmethod
    def create(cls, kind):
        if kind not in cls._registry:
            raise ValueError("unknown vehicle " + kind)
        return cls._registry[kind]()       # build and return the right object

for k in ["car", "bike", "truck"]:
    print(k, VehicleFactory.create(k).cost())
```

Output I got when I ran it:

```text
car 40
bike 10
truck 80
```

**When NOT to use:** if you create only one class, in one place, just call the constructor `Car()`.

---

## 3. Observer

**Analogy.** A YouTube channel. You **subscribe**. When a new video comes, YouTube **notifies** all subscribers. The channel does not know who they are or what they do with the news.

Words: the **subject** (the channel) keeps a list of **observers** (subscribers). When something happens, it calls each observer.

**When to use:** one event, many listeners (notifications, logging, UI updates, stock price alerts).

**Bad: the subject calls each listener by hand. Adding a listener means editing it.**

```python
class OrderBad:
    def place(self):
        print("order placed")
        print("EMAIL sent")              # hard-coded listener 1
        print("SMS sent")                # hard-coded listener 2
        # warehouse alert? edit this method again.

OrderBad().place()
```

Output I got when I ran it:

```text
order placed
EMAIL sent
SMS sent
```

**Good: the subject has a list; anyone can subscribe.**

```python
class Order:
    def __init__(self):
        self._observers = []               # the subscriber list

    def subscribe(self, observer):
        self._observers.append(observer)

    def place(self):
        print("order placed")
        for ob in self._observers:         # tell everyone, without knowing who they are
            ob.update("order placed")

class EmailListener:
    def update(self, event):
        print("EMAIL for:", event)

class SmsListener:
    def update(self, event):
        print("SMS for:", event)

class WarehouseListener:                   # new listener: no change to Order
    def update(self, event):
        print("WAREHOUSE pack for:", event)

o = Order()
o.subscribe(EmailListener())
o.subscribe(SmsListener())
o.subscribe(WarehouseListener())
o.place()
```

Output I got when I ran it:

```text
order placed
EMAIL for: order placed
SMS for: order placed
WAREHOUSE pack for: order placed
```

**When NOT to use:** when only one fixed listener exists, a direct call is simpler. Also be careful: too many observers makes the flow hard to follow ("who reacted to this?").

---

## 4. Singleton

**Analogy.** A country has one president at a time. Everyone who asks "who is the president?" gets the same person.

**When to use:** you truly need exactly **one** shared object (a config, a connection pool, a logger registry).

**Bad: everyone builds their own, so the settings drift apart.**

```python
class ConfigBad:
    def __init__(self):
        self.values = {}

a = ConfigBad()
b = ConfigBad()
a.values["mode"] = "prod"
print("b sees:", b.values.get("mode"))     # None! two different configs
print("same object?", a is b)
```

Output I got when I ran it:

```text
b sees: None
same object? False
```

**Good: only one instance is ever made (thread-safe version).**

```python
import threading

class Config:
    _instance = None                         # holds the one and only object
    _lock = threading.Lock()                 # stops two threads creating two objects at once

    def __new__(cls):
        # __new__ runs BEFORE __init__ and decides which object to return
        if cls._instance is None:            # first check (fast, no lock)
            with cls._lock:                  # only one thread enters here at a time
                if cls._instance is None:    # second check (safe)
                    obj = super().__new__(cls)
                    obj.values = {}          # set up the data once
                    cls._instance = obj
        return cls._instance                 # everyone gets the same object

a = Config()
b = Config()
a.values["mode"] = "prod"
print("b sees:", b.values.get("mode"))
print("same object?", a is b)
```

Output I got when I ran it:

```text
b sees: prod
same object? True
```

**When NOT to use (important):** Singleton is a **global variable in disguise**. It makes tests hard (state leaks between tests) and hides dependencies. In an interview, prefer to **create one object and pass it in** (dependency injection, see file 02). Use Singleton only when "one instance" is a real rule, and say that you know the downside.

---

## 5. State

**Analogy.** A traffic light. The same action ("timer ticks") does different things depending on the current colour: green goes to yellow, yellow goes to red.

**When to use:** an object behaves differently in different **modes**, and the modes change over time (vending machine, order status, ATM, media player).

**Bad: one class with `if state == ...` in every method.**

```python
class DoorBad:
    def __init__(self):
        self.state = "closed"

    def push_button(self):
        if self.state == "closed":          # every method needs this chain
            self.state = "open"
        elif self.state == "open":
            self.state = "closed"
        # add a "locked" state? Edit EVERY method.
        return self.state

d = DoorBad()
print(d.push_button(), d.push_button())
```

Output I got when I ran it:

```text
open closed
```

**Good: each state is a class that knows what to do and what comes next.**

```python
from abc import ABC, abstractmethod

class DoorState(ABC):
    @abstractmethod
    def push_button(self, door): pass

class Closed(DoorState):
    def push_button(self, door):
        door.state = Open()                  # closed + button -> open
        return "now open"

class Open(DoorState):
    def push_button(self, door):
        door.state = Closed()                # open + button -> closed
        return "now closed"

class Locked(DoorState):                     # new state: just one new class
    def push_button(self, door):
        return "locked! button ignored"

class Door:
    def __init__(self):
        self.state = Closed()                # start in a state object

    def push_button(self):
        return self.state.push_button(self)  # let the current state decide

d = Door()
print(d.push_button(), "|", d.push_button())
d.state = Locked()
print(d.push_button())
```

Output I got when I ran it:

```text
now open | now closed
locked! button ignored
```

**When NOT to use:** if there are only two states and one or two methods, a simple enum plus `if` is fine. Use State when the `if` chains start to repeat.

---

## 6. Builder

**Analogy.** Ordering a burger: bun, patty, cheese (optional), sauce (optional). You add steps one by one, then say "done" and get the burger.

**When to use:** an object has many **optional** settings. A constructor with ten parameters is hard to read.

**Bad: a long constructor. Which `True` means what?**

```python
class PizzaBad:
    def __init__(self, size, cheese, olives, mushrooms, extra_sauce):
        self.desc = (size, cheese, olives, mushrooms, extra_sauce)

p = PizzaBad("large", True, False, True, False)   # what do True/False mean? Hard to read.
print(p.desc)
```

Output I got when I ran it:

```text
('large', True, False, True, False)
```

**Good: a builder with named steps.**

```python
class Pizza:
    def __init__(self, size, toppings):
        self.size = size
        self.toppings = toppings
    def __str__(self):
        return self.size + " pizza with " + ", ".join(self.toppings)

class PizzaBuilder:
    def __init__(self):
        self._size = "medium"                # sensible defaults
        self._toppings = []

    def size(self, s):
        self._size = s
        return self                          # returning self lets us chain calls

    def add(self, topping):
        self._toppings.append(topping)
        return self

    def build(self):
        if not self._toppings:               # one place to check the rules
            raise ValueError("a pizza needs at least one topping")
        return Pizza(self._size, list(self._toppings))

p = PizzaBuilder().size("large").add("cheese").add("mushrooms").build()
print(p)
```

Output I got when I ran it:

```text
large pizza with cheese, mushrooms
```

**When NOT to use:** if the object has two or three fields, use a normal constructor. In Python, **keyword arguments** (`Pizza(size="large", cheese=True)`) often replace a Builder.

---

## 7. Decorator

**Analogy.** Coffee. You start with a plain coffee. You wrap it with milk, then with sugar. Each wrap adds cost and a note, and it is still "a coffee".

(Do not confuse this with Python's `@decorator` syntax. The idea is similar, but here we mean the *object* pattern.)

**When to use:** you want to add features **at run time**, in any combination, without a class for every combination.

**Bad: a class for every combination (class explosion).**

```python
class Coffee:
    def cost(self): return 50
class CoffeeWithMilk:
    def cost(self): return 60
class CoffeeWithSugar:
    def cost(self): return 55
class CoffeeWithMilkAndSugar:       # 3 add-ons = 8 classes, 10 add-ons = 1024 classes!
    def cost(self): return 65

print(CoffeeWithMilkAndSugar().cost())
```

Output I got when I ran it:

```text
65
```

**Good: wrap objects like layers.**

```python
class Coffee:
    def cost(self): return 50
    def label(self): return "coffee"

class AddOn:                                  # base for all wrappers
    def __init__(self, inner):
        self.inner = inner                    # the thing we wrap (has-a)

class Milk(AddOn):
    def cost(self): return self.inner.cost() + 10          # inner cost + my cost
    def label(self): return self.inner.label() + " + milk"

class Sugar(AddOn):
    def cost(self): return self.inner.cost() + 5
    def label(self): return self.inner.label() + " + sugar"

order = Sugar(Milk(Coffee()))                 # wrap in any order, any number of times
print(order.label(), "=", order.cost())
print(Milk(Milk(Coffee())).label(), "=", Milk(Milk(Coffee())).cost())   # double milk, no new class
```

Output I got when I ran it:

```text
coffee + milk + sugar = 65
coffee + milk + milk = 70
```

**When NOT to use:** if the add-on set is small and fixed, plain fields or flags are simpler. Wrapping many layers also makes debugging harder.

---

## 8. Command

**Analogy.** A restaurant order slip. The waiter writes your request on paper (the request becomes an *object*). The kitchen can queue it, do it later, or cancel it.

**When to use:** you need to **queue**, **log**, **schedule**, or **undo** actions (text editor undo, remote control, task queue).

**Bad: calling methods directly, so there is no way to undo.**

```python
class LampBad:
    def __init__(self):
        self.on = False

lamp = LampBad()
lamp.on = True          # direct change, no record of what we did, so no undo
print("lamp on?", lamp.on)
```

Output I got when I ran it:

```text
lamp on? True
```

**Good: each action is an object with `execute` and `undo`.**

```python
class Lamp:
    def __init__(self):
        self.on = False

class TurnOn:                            # a command object
    def __init__(self, lamp):
        self.lamp = lamp
    def execute(self):
        self.lamp.on = True
    def undo(self):
        self.lamp.on = False             # how to reverse this action

class Remote:
    def __init__(self):
        self.history = []                # stack of commands already done

    def press(self, command):
        command.execute()
        self.history.append(command)     # remember it

    def undo_last(self):
        if self.history:
            self.history.pop().undo()    # reverse the most recent action

lamp = Lamp()
remote = Remote()
remote.press(TurnOn(lamp))
print("after press:", lamp.on)
remote.undo_last()
print("after undo:", lamp.on)
```

Output I got when I ran it:

```text
after press: True
after undo: False
```

**When NOT to use:** if you never need to queue, log or undo, a plain method call is enough. Command adds a class per action.

---

## Which pattern in which design? (preview)

| Design | Patterns used |
|---|---|
| Parking lot | Strategy (pricing, spot choice), Factory (vehicles) |
| LRU cache | none needed (data structures are the point) |
| Elevator | State, Strategy (scheduling) |
| Library | Observer (due-date notices), Factory |
| Vending machine | State |
| ATM | State, Command (transactions) |
| Rate limiter | Strategy (algorithms) |
| Amazon locker | Strategy (size matching), Factory |
| Splitwise | Strategy (split types), Factory |
| Logger / notifications | Observer, Strategy |
| Tic-tac-toe | Strategy (players) |

**Next:** `10_parking_lot.md`.
