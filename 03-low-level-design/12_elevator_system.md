# 12 - Elevator System

Python 3.9. All code was run; the output is real.

---

## 1. The problem in plain words

A building has several floors and several elevators (lifts). People press a button **in the hallway** ("I am on floor 3, I want to go up"). Then, inside the elevator, they press the **floor they want**. The system must decide **which elevator** comes, and each elevator must **move** and **open its doors** at the right floors.

**Analogy.** A taxi dispatcher with a few taxis. A customer calls. The dispatcher sends the best taxi, not always the nearest one: a taxi already driving in that direction is better than a taxi that must turn around.

---

## 2. Requirements I ask the interviewer

1. How many elevators and floors? -> *3 elevators, 10-20 floors (configurable).*
2. Two kinds of buttons? -> *Hall call (floor + direction) and cabin button (destination floor).*
3. How does one elevator choose its path? -> *Keep going in one direction while there are stops ahead, then reverse (the classic "SCAN / LOOK" way, like a real lift).*
4. How do we choose which elevator answers a hall call? -> *The best one by a simple cost (distance, direction). Must be easy to change.*
5. Do I need weight limit, emergency stop, doors timing? -> *Out of scope for the core; mention as extension.*
6. Time: real clock or simulation? -> *Simulation with a `step()` that moves everything by one tick.*
7. Threads? -> *Many people press buttons at the same time.*

---

## 3. Classes and methods (the picture)

```text
                 +---------------------------------------+
                 |          ElevatorController           |  <- the boss
                 |---------------------------------------|
                 | elevators, strategy, lock             |
                 | request_pickup(floor, direction)      |
                 | select_floor(elevator_id, floor)      |
                 | step()                                |
                 +-------+-------------------+-----------+
                         | has many          | uses (passed in)
                         v                   v
              +---------------------+   +---------------------------+
              |      Elevator       |   |    DispatchStrategy       |
              |---------------------|   |  (abstract)               |
              | id, floor, stops    |   | choose(elevators, floor,  |
              | state               |   |        direction)         |
              | add_stop(floor)     |   +-------------+-------------+
              | step()              |                 |
              +----------+----------+       NearestElevatorStrategy
                         | has one (State pattern)
                         v
              +---------------------+
              |   ElevatorState     |  (abstract: step, accepts_requests)
              +---------------------+
                 ^        ^        ^         ^
          IdleState  MovingUp  MovingDown  MaintenanceState (extension)
```

**Why State?** An elevator behaves differently in different modes. "One tick" means: idle -> do nothing or start; moving up -> go up one floor; moving down -> go down. Instead of `if direction == ...` in every method, each mode is a class (State pattern, file 03).

**Why Strategy?** The rule "which elevator answers" is what an interviewer will change ("zones", "peak hours"). So it is a separate, swappable class.

---

## 4. Full code

```python
import threading                               # Lock for the controller
from abc import ABC, abstractmethod            # for "promise" classes
from enum import Enum                          # fixed named choices


class Direction(Enum):                         # direction of a hall call
    UP = 1
    DOWN = 2


# ---------- states of one elevator (State pattern) ----------

class ElevatorState(ABC):
    name = "STATE"                             # text used when printing

    def accepts_requests(self):
        return True                            # most states accept new stops

    @abstractmethod
    def step(self, elevator):                  # "one tick of time passes"
        pass


class IdleState(ElevatorState):
    name = "IDLE"

    def step(self, elevator):
        if not elevator.stops:                 # nothing to do
            return
        # go toward the nearest stop (tie: lower floor)
        nearest = min(elevator.stops, key=lambda s: (abs(s - elevator.floor), s))
        if nearest == elevator.floor:
            elevator.serve_current_floor()     # already here: just open the doors
        elif nearest > elevator.floor:
            elevator.set_state(MovingUpState())
            elevator.state.step(elevator)      # start moving in the same tick
        else:
            elevator.set_state(MovingDownState())
            elevator.state.step(elevator)


class MovingUpState(ElevatorState):
    name = "UP"

    def step(self, elevator):
        if elevator.floor in elevator.stops:   # someone wants this floor
            elevator.serve_current_floor()
            return
        if any(s > elevator.floor for s in elevator.stops):
            elevator.floor += 1                # keep going up (one floor per tick)
            if elevator.floor in elevator.stops:
                elevator.serve_current_floor() # arrived at a stop
        elif elevator.stops:                   # stops remain, but only below: turn around
            elevator.set_state(MovingDownState())
        else:
            elevator.set_state(IdleState())


class MovingDownState(ElevatorState):
    name = "DOWN"

    def step(self, elevator):
        if elevator.floor in elevator.stops:
            elevator.serve_current_floor()
            return
        if any(s < elevator.floor for s in elevator.stops):
            elevator.floor -= 1                # keep going down
            if elevator.floor in elevator.stops:
                elevator.serve_current_floor()
        elif elevator.stops:
            elevator.set_state(MovingUpState())    # only stops above: turn around
        else:
            elevator.set_state(IdleState())


class MaintenanceState(ElevatorState):         # EXTENSION: elevator out of service
    name = "MAINT"

    def accepts_requests(self):
        return False                           # controller will not send it work

    def step(self, elevator):
        pass                                   # does nothing


# ---------- one elevator ----------

class Elevator:
    def __init__(self, elevator_id, start_floor, log):
        self.elevator_id = elevator_id         # e.g. 1, 2, 3
        self.floor = start_floor               # where the cabin is now
        self.stops = set()                     # floors where it must stop (a set: pressing twice is harmless)
        self.state = IdleState()               # starts idle
        self._log = log                        # function used to record events

    def set_state(self, new_state):
        self.state = new_state

    def accepts_requests(self):
        return self.state.accepts_requests()   # ask the state

    def add_stop(self, floor):
        if not self.accepts_requests():
            raise RuntimeError("elevator " + str(self.elevator_id) + " is out of service")
        self.stops.add(floor)

    def serve_current_floor(self):
        self.stops.discard(self.floor)         # this stop is done
        self._log("E" + str(self.elevator_id) + " doors open at floor " + str(self.floor))
        if not self.stops:
            self.set_state(IdleState())        # nothing left: rest

    def step(self):
        self.state.step(self)                  # the state decides what one tick means

    def __str__(self):
        return "E" + str(self.elevator_id) + "@" + str(self.floor) + "(" + self.state.name + ")"


# ---------- strategy: which elevator answers a hall call ----------

class DispatchStrategy(ABC):
    @abstractmethod
    def choose(self, elevators, floor, direction):
        pass


class NearestElevatorStrategy(DispatchStrategy):
    PENALTY = 100                              # big number: "this elevator must finish its trip first"

    def cost(self, e, floor, direction):
        distance = abs(e.floor - floor)
        if isinstance(e.state, IdleState):
            return distance                    # idle: just come
        if isinstance(e.state, MovingUpState) and floor >= e.floor and direction == Direction.UP:
            return distance                    # on its way, same direction
        if isinstance(e.state, MovingDownState) and floor <= e.floor and direction == Direction.DOWN:
            return distance
        return distance + self.PENALTY         # would need to turn around first

    def choose(self, elevators, floor, direction):
        candidates = [e for e in elevators if e.accepts_requests()]   # skip broken elevators
        if not candidates:
            raise RuntimeError("no elevator available")
        # smallest cost wins; ties go to the lowest id so results are repeatable
        return min(candidates, key=lambda e: (self.cost(e, floor, direction), e.elevator_id))


# ---------- the boss ----------

class ElevatorController:
    def __init__(self, elevators, strategy, floors, log):
        self.elevators = elevators             # list of Elevator
        self.strategy = strategy               # a DispatchStrategy
        self.floors = floors                   # number of floors: valid floors are 0..floors-1
        self._log = log
        self._lock = threading.Lock()          # protects every elevator's stops and state

    def _check_floor(self, floor):
        if floor < 0 or floor >= self.floors:  # reject nonsense input early
            raise ValueError("bad floor " + str(floor))

    def request_pickup(self, floor, direction):
        # someone in the hallway pressed UP or DOWN
        self._check_floor(floor)
        with self._lock:
            e = self.strategy.choose(self.elevators, floor, direction)
            e.add_stop(floor)
            self._log("hall call floor " + str(floor) + " " + direction.name + " -> E" + str(e.elevator_id))
            return e.elevator_id

    def select_floor(self, elevator_id, floor):
        # someone inside a cabin pressed a floor button
        self._check_floor(floor)
        with self._lock:
            for e in self.elevators:
                if e.elevator_id == elevator_id:
                    e.add_stop(floor)
                    return
            raise ValueError("no such elevator")

    def step(self):
        with self._lock:                       # move every elevator by one tick
            for e in self.elevators:
                e.step()

    def status(self):
        with self._lock:
            return " ".join(str(e) for e in self.elevators)


def main():
    events = []                                # event log
    log = events.append
    ctrl = ElevatorController(
        [Elevator(1, 0, log), Elevator(2, 10, log)],     # E1 at floor 0, E2 at floor 10
        NearestElevatorStrategy(), floors=12, log=log)

    print("start:", ctrl.status())
    ctrl.request_pickup(3, Direction.UP)       # E1 is 3 away, E2 is 7 away -> E1
    ctrl.step()
    print("tick 1:", ctrl.status())             # E1 is moving up
    ctrl.step(); ctrl.step()                   # E1 reaches floor 3
    print("tick 3:", ctrl.status())
    ctrl.select_floor(1, 7)                    # passenger in E1 presses 7
    ctrl.request_pickup(8, Direction.DOWN)     # E1 (going up) would need to turn; E2 is idle at 10 -> E2
    for _ in range(2):
        ctrl.step()
    print("tick 5:", ctrl.status())             # E1 still climbing to 7, E2 already reached 8
    for _ in range(4):
        ctrl.step()
    print("tick 9:", ctrl.status())
    for _ in range(4):
        ctrl.step()
    print("tick 13:", ctrl.status())
    print("--- event log ---")
    for line in events:
        print(line)

    # ---- extension: maintenance mode + zone strategy ----
    print("--- extension: E1 goes out of service ---")
    events.clear()
    ctrl.elevators[0].set_state(MaintenanceState())
    print("hall call goes to E%d" % ctrl.request_pickup(5, Direction.UP))
    try:
        ctrl.select_floor(1, 2)                # pressing a button in a broken elevator
    except RuntimeError as e:
        print("blocked:", e)

    # ---- thread test ----
    print("--- thread test ---")
    ctrl2 = ElevatorController([Elevator(1, 0, log), Elevator(2, 5, log), Elevator(3, 9, log)],
                               NearestElevatorStrategy(), floors=12, log=lambda m: None)
    def press(n):
        ctrl2.request_pickup(n % 12, Direction.UP if n % 2 == 0 else Direction.DOWN)
    threads = [threading.Thread(target=press, args=(n,)) for n in range(24)]
    for t in threads: t.start()
    for t in threads: t.join()
    all_stops = set()
    for e in ctrl2.elevators:
        all_stops |= e.stops
    print("every floor 0..11 is assigned to some elevator:", all_stops == set(range(12)))


if __name__ == "__main__":
    main()
```

Output I got when I ran it:

```text
start: E1@0(IDLE) E2@10(IDLE)
tick 1: E1@1(UP) E2@10(IDLE)
tick 3: E1@3(IDLE) E2@10(IDLE)
tick 5: E1@5(UP) E2@8(IDLE)
tick 9: E1@7(IDLE) E2@8(IDLE)
tick 13: E1@7(IDLE) E2@8(IDLE)
--- event log ---
hall call floor 3 UP -> E1
E1 doors open at floor 3
hall call floor 8 DOWN -> E2
E2 doors open at floor 8
E1 doors open at floor 7
--- extension: E1 goes out of service ---
hall call goes to E2
blocked: elevator 1 is out of service
--- thread test ---
every floor 0..11 is assigned to some elevator: True
```

---

## 5. How the code works (walk through)

1. `request_pickup(3, UP)`: the controller asks the **strategy** for the best elevator. E1 (idle at 0, distance 3) beats E2 (idle at 10, distance 7). The stop is added.
2. `step()` gives every elevator one tick. `IdleState` sees a stop above, switches to `MovingUpState`, and the elevator climbs one floor per tick.
3. When it reaches a stop, `serve_current_floor` removes the stop and writes "doors open".
4. The second hall call (floor 8, DOWN): E1 is moving up and the call wants to go down, so E1 gets a **penalty** (it would have to finish its trip first). E2 is idle at floor 10, distance 2. E2 wins.
5. When no stops remain, the elevator goes back to `IdleState`.

This movement rule is "keep going while there are stops ahead, then reverse". It avoids the elevator going up and down for no reason.

---

## 6. How to extend it

**"One elevator is under repair."** I added `MaintenanceState` (a new state class). It says `accepts_requests() == False`, and the strategy skips such elevators. No `if` was added to the controller. See "extension" in the output.

**"Add a new dispatch rule (zones, express lift, peak hours)."** Write a new class that extends `DispatchStrategy`. Pass it to the controller. Nothing else changes (Open/Closed, file 02).

**"Add a door state and a timer."** Add `DoorOpenState` that stays for N ticks then moves on. It is just one more State class.

**"Add a weight limit."** Give `Elevator` a `load_kg` and a `max_kg`. In `add_stop` or at boarding, refuse extra people. A new `OverloadedState` can hold the doors open.

---

## 7. Thread-safety notes (plain words)

- **The danger:** one thread presses a button (adds to `stops`) while another thread calls `step()` (which reads `stops`). Python can raise "set changed size during iteration", or two threads can both pick "the best elevator" from the same stale data.
- **The fix:** every public method of the controller takes one lock. All access to elevators goes through the controller, so the elevators themselves have no locks. (Rule: **one owner for the lock**.)
- In a real building, `step()` is called by a timer thread, and button presses come from other threads. With one lock that is safe, but a long `step()` blocks buttons. Steps are tiny here, so that is fine.
- For many buildings, give each building its own controller (and its own lock).

---

## 8. Five follow-up questions with model answers

**Q1. Why use a set for `stops` instead of a list?**
Pressing the same floor twice must not stop the elevator twice. A set ignores duplicates and gives O(1) add and remove. The cost is that we lose "order of arrival", which we do not need, because the elevator's direction decides the order.

**Q2. Why not always send the nearest elevator?**
The nearest elevator may be going the wrong way, so it would need to finish its trip first. A farther elevator that is idle or already heading toward the caller can arrive sooner. My cost adds a penalty when the elevator would have to turn around.

**Q3. How would you handle 50 floors and "express" elevators that only stop at certain floors?**
Give each `Elevator` a set `allowed_floors`. In `add_stop`, reject floors outside it. In the strategy, only consider elevators that allow the requested floor. The change lives in the strategy and the elevator, not in the controller.

**Q4. How do you test this without waiting?**
`step()` is a simulated tick, so a test just calls it N times and checks `floor` and the event log (that is what `main()` does). No sleeping and no real clock. This is the benefit of simulating time instead of using `time.sleep`.

**Q5. What if two elevators are chosen for the same floor over time (both stop there)?**
When a hall call is assigned, only one elevator gets the stop, so only one comes. If you want re-assignment (for example the first elevator is overloaded), keep the pending hall calls in the controller. On each tick, re-run the strategy for unserved calls. That is a good extension, but I would first ask the interviewer if they need it.

---

**Next:** `13_library_management.md`.
