# 10 - Parking Lot

Time to practise: 45 minutes. Python 3.9. Every line of code below was run. The output is real.

---

## 1. The problem in plain words

You must design the software for a **car park** (parking lot). Cars, bikes and trucks come in. The system gives each vehicle a **free spot** and a **ticket**. When the vehicle leaves, the system takes the ticket, works out the **fee**, and frees the spot.

**Analogy.** A multi-storey mall car park. At the gate a machine gives you a paper ticket with the spot number. At exit you pay.

The interviewer is not checking if you can write `for` loops. They want to see: Are the classes clear? Can you add a new rule later (new vehicle, new pricing) without rewriting everything?

(A candidate-question site, PracHub, tags a version of this problem as **Amazon, Software Engineer, technical screen** (level not stated). It asks for the *smallest free spot that fits*, then adds EV charging spots with fallback in both directions, plus thread safety and tests
([PracHub post](https://prachub.com/interview-questions/parking-lot-design-smallest-fitting-spot-for-three-sizes-then-ev-charging-fallback)). It is one candidate's report, not an official Amazon statement. I built both ideas below.)

---

## 2. Requirements I ask the interviewer

Ask these out loud, then write the answers down:

1. What vehicle types? -> *Motorcycle, car, truck.*
2. How many floors, and are spots different sizes? -> *Many floors. Spots are small, medium, large.*
3. Can a small vehicle use a bigger spot? -> *Yes, if no exact spot is free. Never the other way round.*
4. Which spot do we choose? -> *The smallest spot that fits; on a tie, the lowest floor.*
5. How is the fee computed? -> *Per hour, part of an hour counts as a full hour, price depends on vehicle type.*
6. What happens when the lot is full? -> *Reject the vehicle with a clear error.*
7. Many gates at the same time (threads)? -> *Yes, two gates may issue tickets at once.*
8. Out of scope? -> *Real payment, cameras, database.*

---

## 3. Classes and methods (the picture)

```text
                    +-----------------------------+
                    |         ParkingLot          |   <- the boss (facade)
                    |-----------------------------|
                    | floors, assignment, pricing |
                    | park(vehicle) -> Ticket     |
                    | unpark(ticket_id) -> fee    |
                    +--------+-------+------------+
                             |       |
          has many           |       | uses (passed in)
       +---------------------+       +-----------------------------+
       v                                                           v
+-------------+  has many  +-------------+      +---------------------------+  +----------------+
|   Floor     |----------->| ParkingSpot |      | SpotAssignmentStrategy    |  | PricingStrategy|
|-------------|            |-------------|      |  (abstract)               |  |  (abstract)    |
| floor_no    |            | spot_id     |      | choose(floors, vehicle)   |  | fee(ticket,now)|
| spots       |            | size        |      +-------------+-------------+  +--------+-------+
+-------------+            | vehicle     |                    |                         |
                           | can_fit()   |         SmallestFitStrategy            HourlyPricing
                           | park()/leave|
                           +-------------+

 Vehicle(plate, vtype)      Ticket(id, vehicle, spot, entry_time)
```

**Why these classes?** I underlined the nouns in the requirements: vehicle, floor, spot, ticket, fee. The **verbs** are park, unpark, choose, price.

- `ParkingSpot` knows if it is free and if a vehicle fits (it owns that rule).
- `Floor` just groups spots.
- Two **Strategy** classes (file 03) are used because the interviewer will very likely change "which spot" and "how to price".
- `ParkingLot` is the single entry point.

---

## 4. Full code

```python
import math                                   # math.ceil rounds hours up
import threading                              # Lock keeps two gates from taking the same spot
from abc import ABC, abstractmethod           # ABC lets us define "promise" classes
from enum import Enum                         # Enum gives fixed, named choices


# ---------- simple value types ----------

class VehicleType(Enum):                      # the kinds of vehicle we support
    MOTORCYCLE = 1                            # the number is the "size rank" of the vehicle
    CAR = 2
    TRUCK = 3


class SpotSize(Enum):                         # the kinds of spot
    SMALL = 1                                 # same rank numbers so we can compare easily
    MEDIUM = 2
    LARGE = 3


class LotFullError(Exception):                # our own error: no spot for this vehicle
    pass


class InvalidTicketError(Exception):          # our own error: ticket unknown or already used
    pass


class Vehicle:
    def __init__(self, plate, vtype):
        self.plate = plate                    # licence plate text, e.g. "KA01"
        self.vtype = vtype                    # a VehicleType


class ParkingSpot:
    has_charger = False                       # class-level default; an EV spot will change it later

    def __init__(self, spot_id, size, floor_no):
        self.spot_id = spot_id                # unique name like "F0-S2"
        self.size = size                      # a SpotSize
        self.floor_no = floor_no              # which floor this spot is on
        self.vehicle = None                   # None means the spot is free

    def is_free(self):
        return self.vehicle is None           # free when nobody is parked

    def can_fit(self, vehicle):
        # a spot fits when its size rank is >= the vehicle's rank (a bike fits a large spot, not a truck in a small)
        return self.size.value >= vehicle.vtype.value

    def park(self, vehicle):
        self.vehicle = vehicle                # mark the spot as used

    def leave(self):
        self.vehicle = None                   # mark the spot as free again


class EvSpot(ParkingSpot):                    # used only by the extension at the bottom
    has_charger = True                        # this spot has a charger


class Floor:
    def __init__(self, floor_no, spots):
        self.floor_no = floor_no              # floor number
        self.spots = spots                    # list of ParkingSpot on this floor


class Ticket:
    def __init__(self, ticket_id, vehicle, spot, entry_time):
        self.ticket_id = ticket_id            # unique id printed on the paper
        self.vehicle = vehicle                # who parked
        self.spot = spot                      # where they parked
        self.entry_time = entry_time          # seconds when they came in


# ---------- strategies (the parts that will change) ----------

class SpotAssignmentStrategy(ABC):            # promise: "I can choose a spot"
    @abstractmethod
    def choose(self, floors, vehicle):
        pass


class SmallestFitStrategy(SpotAssignmentStrategy):
    def choose(self, floors, vehicle):
        best = None                           # best spot found so far
        for floor in floors:                  # look at every floor
            for spot in floor.spots:          # and every spot on it
                if not spot.is_free() or not spot.can_fit(vehicle):
                    continue                  # skip used spots and spots that are too small
                # key = (size rank, floor number): smaller key is better
                key = (spot.size.value, spot.floor_no)
                if best is None or key < best[0]:
                    best = (key, spot)        # remember this better spot
        return None if best is None else best[1]   # None when nothing fits


class PricingStrategy(ABC):                   # promise: "I can compute a fee"
    @abstractmethod
    def fee(self, ticket, exit_time):
        pass


class HourlyPricing(PricingStrategy):
    def __init__(self, rate_per_hour):
        self.rate_per_hour = rate_per_hour    # dict: VehicleType -> price per hour

    def fee(self, ticket, exit_time):
        seconds = exit_time - ticket.entry_time          # how long they stayed
        hours = max(1, math.ceil(seconds / 3600))        # part of an hour counts as full; minimum 1 hour
        return hours * self.rate_per_hour[ticket.vehicle.vtype]


# ---------- the boss ----------

class ParkingLot:
    def __init__(self, floors, assignment, pricing, clock):
        self.floors = floors                  # list of Floor
        self.assignment = assignment          # a SpotAssignmentStrategy (passed in = dependency injection)
        self.pricing = pricing                # a PricingStrategy
        self.clock = clock                    # a function that returns "now" in seconds (easy to fake in tests)
        self._active = {}                     # ticket_id -> Ticket, only for cars currently inside
        self._next_id = 1                     # simple counter for ticket ids
        self._lock = threading.Lock()         # one lock protects all the shared data above

    def park(self, vehicle):
        with self._lock:                      # only one thread at a time can choose and take a spot
            spot = self.assignment.choose(self.floors, vehicle)
            if spot is None:                  # nothing free that fits
                raise LotFullError("no spot for " + vehicle.vtype.name)
            spot.park(vehicle)                # take the spot
            ticket = Ticket(self._next_id, vehicle, spot, self.clock())
            self._active[ticket.ticket_id] = ticket   # remember the ticket
            self._next_id += 1
            return ticket

    def unpark(self, ticket_id):
        with self._lock:
            ticket = self._active.pop(ticket_id, None)   # remove it so it cannot be used twice
            if ticket is None:
                raise InvalidTicketError("unknown ticket " + str(ticket_id))
            amount = self.pricing.fee(ticket, self.clock())
            ticket.spot.leave()               # free the spot
            return amount

    def free_spots(self):
        # count free spots per size (useful for a display board)
        counts = {size.name: 0 for size in SpotSize}
        for floor in self.floors:
            for spot in floor.spots:
                if spot.is_free():
                    counts[spot.size.name] += 1
        return counts


# ---------- helper used only by the demo ----------

class FakeClock:
    def __init__(self):
        self.now = 0                          # fake time in seconds
    def __call__(self):
        return self.now                       # calling the object returns the time
    def advance_hours(self, h):
        self.now += int(h * 3600)


def build_lot(clock):
    # floor 0 has 1 small, 1 medium, 1 large; floor 1 has 1 medium, 1 large
    f0 = Floor(0, [ParkingSpot("F0-S", SpotSize.SMALL, 0),
                   ParkingSpot("F0-M", SpotSize.MEDIUM, 0),
                   ParkingSpot("F0-L", SpotSize.LARGE, 0)])
    f1 = Floor(1, [ParkingSpot("F1-M", SpotSize.MEDIUM, 1),
                   ParkingSpot("F1-L", SpotSize.LARGE, 1)])
    rates = {VehicleType.MOTORCYCLE: 10, VehicleType.CAR: 20, VehicleType.TRUCK: 40}
    return ParkingLot([f0, f1], SmallestFitStrategy(), HourlyPricing(rates), clock)


# ---------- EXTENSION: new rules added WITHOUT editing the classes above ----------

class ElectricCar(Vehicle):                   # a car that needs a charger
    is_electric = True


class EvAwareStrategy(SpotAssignmentStrategy):
    """Electric cars prefer charger spots; other cars prefer normal spots. Each can fall back to the other kind."""
    def choose(self, floors, vehicle):
        # every free spot that physically fits this vehicle
        free_fit = [s for f in floors for s in f.spots if s.is_free() and s.can_fit(vehicle)]
        if getattr(vehicle, "is_electric", False):          # only electric vehicles have this flag
            preferred = [s for s in free_fit if s.has_charger]       # EV wants a charger
        else:
            preferred = [s for s in free_fit if not s.has_charger]   # normal car keeps chargers free
        pool = preferred or free_fit                        # fallback: use the other kind if preferred is empty
        if not pool:
            return None                                     # lot full for this vehicle
        return min(pool, key=lambda s: (s.size.value, s.floor_no))   # still "smallest fit, lowest floor"


class WeekendPricing(PricingStrategy):
    """Wraps another pricing and gives 50 percent off (a Decorator-like idea)."""
    def __init__(self, inner):
        self.inner = inner
    def fee(self, ticket, exit_time):
        return self.inner.fee(ticket, exit_time) * 0.5


def main():
    clock = FakeClock()
    lot = build_lot(clock)
    print("free at start:", lot.free_spots())

    bike = Vehicle("BIKE-1", VehicleType.MOTORCYCLE)
    car = Vehicle("CAR-1", VehicleType.CAR)
    t1 = lot.park(bike)                       # bike should take the SMALL spot
    t2 = lot.park(car)                        # car should take the smallest MEDIUM (floor 0)
    print("bike ->", t1.spot.spot_id, "| car ->", t2.spot.spot_id)

    truck = Vehicle("TRUCK-1", VehicleType.TRUCK)
    t3 = lot.park(truck)                      # truck needs LARGE: F0-L
    t4 = lot.park(Vehicle("CAR-2", VehicleType.CAR))     # next medium is on floor 1
    t5 = lot.park(Vehicle("CAR-3", VehicleType.CAR))     # medium all used, so this car takes F1-L (bigger spot is OK)
    print("truck ->", t3.spot.spot_id, "| car2 ->", t4.spot.spot_id, "| car3 ->", t5.spot.spot_id)
    print("free now:", lot.free_spots())

    try:
        lot.park(Vehicle("TRUCK-2", VehicleType.TRUCK))  # all large spots are used
    except LotFullError as e:
        print("rejected:", e)

    clock.advance_hours(2.5)                  # 2.5 hours pass: 3 billed hours
    print("car fee:", lot.unpark(t2.ticket_id), "(3 hours x 20)")
    try:
        lot.unpark(t2.ticket_id)              # same ticket again
    except InvalidTicketError as e:
        print("second use blocked:", e)

    print("free after car leaves:", lot.free_spots())

    # ---- extension demo ----
    print("--- extension: EV spots and weekend pricing ---")
    rates = {VehicleType.MOTORCYCLE: 10, VehicleType.CAR: 20, VehicleType.TRUCK: 40}

    def small_ev_lot(clk):                    # helper: one normal spot and one EV spot
        floor = Floor(0, [ParkingSpot("F0-M", SpotSize.MEDIUM, 0),
                          EvSpot("F0-EV", SpotSize.MEDIUM, 0)])
        return ParkingLot([floor], EvAwareStrategy(),
                          WeekendPricing(HourlyPricing(rates)), clk)

    clock2 = FakeClock()
    lot2 = small_ev_lot(clock2)
    tev = lot2.park(ElectricCar("EV-1", VehicleType.CAR))      # EV prefers the charger
    tnorm = lot2.park(Vehicle("CAR-9", VehicleType.CAR))       # normal car takes the normal spot
    print("EV car ->", tev.spot.spot_id, "| normal car ->", tnorm.spot.spot_id)
    clock2.advance_hours(2)
    print("weekend fee for 2 hours:", lot2.unpark(tev.ticket_id))

    lot_a = small_ev_lot(FakeClock())         # two normal cars: the second must fall back to the EV spot
    print("normal1 ->", lot_a.park(Vehicle("N1", VehicleType.CAR)).spot.spot_id,
          "| normal2 (fallback) ->", lot_a.park(Vehicle("N2", VehicleType.CAR)).spot.spot_id)
    lot_b = small_ev_lot(FakeClock())         # two EVs: the second must fall back to the normal spot
    print("EV1 ->", lot_b.park(ElectricCar("E1", VehicleType.CAR)).spot.spot_id,
          "| EV2 (fallback) ->", lot_b.park(ElectricCar("E2", VehicleType.CAR)).spot.spot_id)

    # ---- thread demo: 10 threads fight for 3 spots, exactly 3 must win ----
    print("--- thread test ---")
    clock3 = FakeClock()
    lot3 = ParkingLot([Floor(0, [ParkingSpot("S" + str(i), SpotSize.MEDIUM, 0) for i in range(3)])],
                      SmallestFitStrategy(), HourlyPricing(rates), clock3)
    results = []                              # list.append is safe between threads in CPython
    def try_park(n):
        try:
            lot3.park(Vehicle("T" + str(n), VehicleType.CAR))
            results.append("ok")
        except LotFullError:
            results.append("full")
    threads = [threading.Thread(target=try_park, args=(n,)) for n in range(10)]
    for t in threads: t.start()               # start all threads
    for t in threads: t.join()                # wait for all to finish
    print("parked:", results.count("ok"), "rejected:", results.count("full"))


if __name__ == "__main__":
    main()
```

Output I got when I ran it:

```text
free at start: {'SMALL': 1, 'MEDIUM': 2, 'LARGE': 2}
bike -> F0-S | car -> F0-M
truck -> F0-L | car2 -> F1-M | car3 -> F1-L
free now: {'SMALL': 0, 'MEDIUM': 0, 'LARGE': 0}
rejected: no spot for TRUCK
car fee: 60 (3 hours x 20)
second use blocked: unknown ticket 2
free after car leaves: {'SMALL': 0, 'MEDIUM': 1, 'LARGE': 0}
--- extension: EV spots and weekend pricing ---
EV car -> F0-EV | normal car -> F0-M
weekend fee for 2 hours: 20.0
normal1 -> F0-M | normal2 (fallback) -> F0-EV
EV1 -> F0-EV | EV2 (fallback) -> F0-M
--- thread test ---
parked: 3 rejected: 7
```

---

## 5. How the code works (walk through)

1. `ParkingLot.park` takes the lock. Then it asks the **assignment strategy** for a spot. The strategy only *looks*; the lot does the *taking*.
2. `SmallestFitStrategy` checks every free spot that fits and keeps the one with the smallest `(size, floor)` pair. This gives "smallest fitting spot, lowest floor".
3. A `Ticket` is stored in `_active`. `unpark` removes it from `_active`, so one ticket cannot be used twice.
4. The fee comes from the **pricing strategy**, so pricing rules never touch the lot code.

Look at the output: the bike took the small spot, the car took the medium spot, and "CAR-3" took a large spot because all medium spots were busy. That is the "smallest fit, fall back to bigger" rule.

Time and space cost: `park` scans all spots: **O(N)** for N spots. That is fine for an interview. See follow-up question 1 for how to make it faster.

---

## 6. How to extend it

**Interviewer adds: "Electric vehicles need charging spots."**

- I add `EvSpot` (a spot with a charger) and `ElectricCar`.
- I add `EvAwareStrategy`: electric cars prefer charger spots, normal cars prefer normal spots, and each can fall back to the other kind when its preferred kind is full.
- I do **not** change `ParkingLot`. This is the **Open/Closed** principle (file 02). See "extension demo" in the output.

**Interviewer adds: "Weekend discount."** I add `WeekendPricing` that wraps another pricing. `ParkingLot` is unchanged.

**Interviewer adds: "Pay by card at exit."** Add a `PaymentProcessor` interface and pass it to `unpark`, or make `unpark` return the fee and let a separate `PaymentService` take the money. Single Responsibility says the lot should not know about payments.

---

## 7. Thread-safety notes (plain words)

- **The danger:** two gates call `park` at the same moment. Both see the *same* last free spot, both take it. Two cars in one spot!
- **The fix:** one `threading.Lock`. Only one thread can be inside `with self._lock:` at a time. The "choose" and the "take" are one unit.
- The thread test in the output shows 10 threads and 3 spots: exactly 3 got in.
- **Cost:** one lock means gates wait for each other. For a real car park this is fine (parking takes seconds, the lock takes microseconds).
- **Better for big systems:** one lock per floor, or a database transaction.

---

## 8. Five follow-up questions with model answers

**Q1. `park` is O(N). How do you make it faster?**
Keep, for each spot size, a **min-heap** (or a sorted set) of free spots keyed by `(floor, spot_id)`. To park, look at the heap for the exact size, then the next size up, and pop the best. `leave` pushes the spot back. Now `park` is O(log N) instead of O(N).

**Q2. How do you add a new vehicle type, like a bus?**
Add `BUS = 4` to `VehicleType`, add a `SpotSize.XL = 4` if needed, and add the price to the rate dictionary. The `can_fit` rule (size rank compare) works without any other change. That is why I used ranks.

**Q3. What if the lot has multiple entry gates, each in a different process (not threads)?**
A Python lock only works inside one process. The "who owns this spot" data must move to shared storage (a database), and I would use a transaction or an atomic "compare and set" (update the spot only if it is still free). That is a system design topic, so I would mention it and stay with the single-process design.

**Q4. A driver loses the ticket. What now?**
Look up the vehicle by plate: keep a second dictionary `plate -> ticket_id`. Then charge the normal fee (maybe plus a lost-ticket fine). It needs one extra dictionary and one method `unpark_by_plate`. The design absorbs it.

**Q5. Why Strategy for pricing and for assignment? Isn't it too many classes?**
Because these are exactly the two rules that real car parks change often (peak hours, VIP parking, EV spots). Each is one small class. If the interviewer said "pricing will never change", I would use a simple function. I add a pattern only when it removes a real edit.

---

**Next:** `11_lru_cache.md`.
