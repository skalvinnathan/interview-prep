# 13 - Library Management System

Python 3.9. All code was run; the output is real.

---

## 1. The problem in plain words

A library owns books. Members can **search** for books, **borrow** them, and **return** them. A book has a due date; if you return it late, you pay a **fine**. If every copy is borrowed, you can **reserve** (put a hold on) the book. When a copy comes back, the first person in the queue is told.

**Analogy.** A school library: a librarian with a register. She checks how many books you already hold, stamps a due date, and writes your name on a waiting list if the book is out.

---

## 2. Requirements I ask the interviewer

1. Can the library own several copies of the same book? -> *Yes. Title info is shared; each physical copy has its own barcode.*
2. Search by what? -> *Title and author (simple text match).*
3. Borrow limits? -> *Max 3 books per member, 14 days.*
4. Fines? -> *A fixed amount per overdue day. It may change.*
5. Reservations? -> *Yes: a first-come queue per book.*
6. Notifications? -> *When a held book is available, and reminders before due date. Delivery method (email, SMS) should be swappable.*
7. Out of scope? -> *Payment of fines, physical shelves, e-books, UI.*
8. Threads? -> *Several librarians use the system at the same time.*

---

## 3. Classes and methods (the picture)

```text
+-----------------------------------------------------+
|                      Library  (boss)                |
|-----------------------------------------------------|
| checkout(member_id, isbn) -> Loan                   |
| return_item(barcode) -> fine                        |
| reserve(member_id, isbn)                            |
| search(text) -> [Book]                              |
| subscribe(listener)    <- Observer                  |
+---+------------+-----------+-----------+------------+
    |            |           |           |
    v has        v has       v has       v uses
 +------+   +---------+  +--------+   +--------------+
 | Book |<--| BookItem|  | Member |   | FinePolicy   |  (abstract, Strategy)
 |isbn  | 1:n|barcode  |  |id,name |   | fine(loan,   |
 |title |    |available|  |loans   |   |      today)  |
 |author|    +---------+  |max_loans|  +------+-------+
 +------+         ^       +--------+         |
                  |                    PerDayFine
                  |            Loan(item, member, borrowed_on, due_on)
```

- **Book** = the title (what the book *is*). **BookItem** = one physical copy (barcode). Why split? Ten copies of one book share one title and author. Splitting avoids repeating data, and lets us lend copies one by one.
- **FinePolicy**: a Strategy, since fine rules change.
- **Listeners**: Observer. The library says "hold ready" and does not care who listens.

---

## 4. Full code

```python
import threading                               # Lock for thread safety
from abc import ABC, abstractmethod            # "promise" classes
from collections import deque                  # fast queue for holds (reservations)


class LibraryError(Exception):                 # base class for all our errors
    pass


class Book:
    def __init__(self, isbn, title, author):
        self.isbn = isbn                       # unique id of the title (like a product code)
        self.title = title
        self.author = author


class BookItem:
    def __init__(self, barcode, book):
        self.barcode = barcode                 # unique id of this physical copy
        self.book = book                       # which title it is
        self.available = True                  # False while on loan


class Member:
    max_loans = 3                              # default limit (subclasses can change it)

    def __init__(self, member_id, name):
        self.member_id = member_id
        self.name = name
        self.active_loans = []                 # loans not yet returned


class Loan:
    def __init__(self, item, member, borrowed_on, due_on):
        self.item = item                       # the copy
        self.member = member                   # who has it
        self.borrowed_on = borrowed_on         # day number
        self.due_on = due_on                   # day number


# ---------- fine strategy ----------

class FinePolicy(ABC):
    @abstractmethod
    def fine(self, loan, today):
        pass


class PerDayFine(FinePolicy):
    def __init__(self, rate):
        self.rate = rate                       # money per overdue day

    def fine(self, loan, today):
        late_days = max(0, today - loan.due_on)    # never negative: on time = 0
        return late_days * self.rate


# ---------- listeners (Observer) ----------

class Listener(ABC):
    @abstractmethod
    def on_event(self, event, payload):
        pass


class RecordingListener(Listener):             # stands in for email/SMS: it just records messages
    def __init__(self):
        self.messages = []

    def on_event(self, event, payload):
        self.messages.append(event + ": " + payload)


# ---------- the boss ----------

class Library:
    def __init__(self, fine_policy, clock, loan_days=14):
        self.fine_policy = fine_policy         # injected Strategy
        self.clock = clock                     # function returning today's day number
        self.loan_days = loan_days
        self._books = {}                       # isbn -> Book
        self._copies = {}                      # isbn -> list of BookItem
        self._items = {}                       # barcode -> BookItem
        self._members = {}                     # member_id -> Member
        self._loans = {}                       # barcode -> Loan (only active loans)
        self._holds = {}                       # isbn -> deque of member_ids waiting
        self._listeners = []                   # Observer list
        self._lock = threading.RLock()         # one lock for all shared data

    # --- setup ---
    def subscribe(self, listener):
        self._listeners.append(listener)

    def _notify(self, event, payload):
        for l in self._listeners:              # tell everybody, without knowing who they are
            l.on_event(event, payload)

    def add_book(self, book, copies):
        with self._lock:
            self._books[book.isbn] = book
            self._copies.setdefault(book.isbn, [])
            for i in range(copies):            # create one BookItem per physical copy
                item = BookItem(book.isbn + "-" + str(len(self._copies[book.isbn]) + 1), book)
                self._copies[book.isbn].append(item)
                self._items[item.barcode] = item

    def register(self, member):
        with self._lock:
            self._members[member.member_id] = member

    # --- search ---
    def search(self, text):
        text = text.lower()                    # case-insensitive match
        with self._lock:
            return [b for b in self._books.values()
                    if text in b.title.lower() or text in b.author.lower()]

    # --- core operations ---
    def checkout(self, member_id, isbn):
        with self._lock:                       # check and change must be one unit
            member = self._members.get(member_id)
            if member is None:
                raise LibraryError("unknown member")
            if isbn not in self._books:
                raise LibraryError("unknown book")
            if len(member.active_loans) >= member.max_loans:
                raise LibraryError("limit reached: " + str(member.max_loans) + " books")
            queue = self._holds.get(isbn)
            if queue and queue[0] != member_id:    # someone is waiting; the book is for them first
                raise LibraryError("book is on hold for another member")
            item = next((c for c in self._copies[isbn] if c.available), None)
            if item is None:
                raise LibraryError("no copy available; you may reserve it")
            if queue and queue[0] == member_id:
                queue.popleft()                # the waiting member now got the book: leave the queue
            item.available = False
            today = self.clock()
            loan = Loan(item, member, today, today + self.loan_days)
            self._loans[item.barcode] = loan
            member.active_loans.append(loan)
            return loan

    def return_item(self, barcode):
        with self._lock:
            loan = self._loans.pop(barcode, None)  # remove from active loans
            if loan is None:
                raise LibraryError("this copy is not on loan")
            loan.item.available = True
            loan.member.active_loans.remove(loan)
            amount = self.fine_policy.fine(loan, self.clock())
            queue = self._holds.get(loan.item.book.isbn)
            if queue:                          # someone is waiting: tell the first person
                self._notify("HOLD_READY", "member " + str(queue[0]) + " can borrow " + loan.item.book.title)
            return amount

    def reserve(self, member_id, isbn):
        with self._lock:
            if member_id not in self._members or isbn not in self._books:
                raise LibraryError("unknown member or book")
            if any(c.available for c in self._copies[isbn]):
                raise LibraryError("a copy is available: borrow it instead")
            queue = self._holds.setdefault(isbn, deque())
            if member_id in queue:
                raise LibraryError("already reserved")
            queue.append(member_id)            # join the end of the queue
            return len(queue)                  # position in the queue

    def send_due_reminders(self, within_days=2):
        with self._lock:                       # periodic job: warn about loans due soon
            today = self.clock()
            for loan in self._loans.values():
                if 0 <= loan.due_on - today <= within_days:
                    self._notify("DUE_SOON", loan.member.name + " must return '" +
                                 loan.item.book.title + "' by day " + str(loan.due_on))


# ---------- EXTENSION: new rules, no change to Library ----------

class PremiumMember(Member):
    max_loans = 10                             # premium members can borrow more


class CappedFine(FinePolicy):
    """Wraps another policy but never charges more than a maximum."""
    def __init__(self, inner, cap):
        self.inner = inner
        self.cap = cap

    def fine(self, loan, today):
        return min(self.cap, self.inner.fine(loan, today))


class Clock:
    def __init__(self):
        self.day = 1
    def __call__(self):
        return self.day


def main():
    clock = Clock()
    lib = Library(PerDayFine(rate=2), clock)
    notes = RecordingListener()
    lib.subscribe(notes)

    lib.add_book(Book("111", "Clean Code", "Robert Martin"), copies=1)
    lib.add_book(Book("222", "Python Basics", "Jane Roe"), copies=2)
    lib.register(Member(1, "Asha"))
    lib.register(Member(2, "Ravi"))

    print("search 'clean':", [b.title for b in lib.search("clean")])
    loan = lib.checkout(1, "111")              # Asha borrows the only copy
    print("Asha borrowed:", loan.item.barcode, "due day", loan.due_on)
    try:
        lib.checkout(2, "111")                 # Ravi tries: no copy left
    except LibraryError as e:
        print("Ravi blocked:", e)
    print("Ravi reserves, queue position:", lib.reserve(2, "111"))

    clock.day = 14
    lib.send_due_reminders()                   # due on day 15: within 2 days
    clock.day = 19                             # 4 days late
    print("fine for late return:", lib.return_item("111-1"))
    for m in notes.messages:
        print("  notice ->", m)

    loan2 = lib.checkout(2, "111")             # now Ravi can borrow it
    print("Ravi borrowed:", loan2.item.barcode)

    lib.add_book(Book("555", "Many Copies", "Z"), copies=5)
    for i in range(3):                         # Asha borrows 3 books: that is her limit
        lib.checkout(1, "555")
    try:
        lib.checkout(1, "555")                 # the 4th one must be refused
    except LibraryError as e:
        print("Asha blocked:", e)

    # ---- extension demo ----
    print("--- extension: premium member + capped fine ---")
    clock2 = Clock()
    lib2 = Library(CappedFine(PerDayFine(2), cap=10), clock2)
    lib2.add_book(Book("333", "Algorithms", "A. Author"), copies=1)
    lib2.register(PremiumMember(5, "Meera"))
    print("Meera's limit:", lib2._members[5].max_loans)
    lib2.checkout(5, "333")
    clock2.day = 100                       # very late: 100 - 15 = 85 days
    print("fine (capped at 10):", lib2.return_item("333-1"))

    # ---- thread test: 10 members race for the last copy ----
    print("--- thread test ---")
    lib3 = Library(PerDayFine(1), Clock())
    lib3.add_book(Book("444", "Last Copy", "X"), copies=1)
    for n in range(10):
        lib3.register(Member(n, "M" + str(n)))
    outcomes = []
    def grab(n):
        try:
            lib3.checkout(n, "444")
            outcomes.append("got")
        except LibraryError:
            outcomes.append("no")
    threads = [threading.Thread(target=grab, args=(n,)) for n in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
    print("got the book:", outcomes.count("got"), "| refused:", outcomes.count("no"))


if __name__ == "__main__":
    main()
```

Output I got when I ran it:

```text
search 'clean': ['Clean Code']
Asha borrowed: 111-1 due day 15
Ravi blocked: no copy available; you may reserve it
Ravi reserves, queue position: 1
fine for late return: 8
  notice -> DUE_SOON: Asha must return 'Clean Code' by day 15
  notice -> HOLD_READY: member 2 can borrow Clean Code
Ravi borrowed: 111-1
Asha blocked: limit reached: 3 books
--- extension: premium member + capped fine ---
Meera's limit: 10
fine (capped at 10): 10
--- thread test ---
got the book: 1 | refused: 9
```

---

## 5. How the code works (walk through)

1. `add_book` creates one `BookItem` per copy. Lending always works on copies; searching works on `Book`.
2. `checkout` runs several checks (member exists, limit, queue fairness, copy available) inside one lock. Then it marks the copy unavailable and records a `Loan`.
3. `return_item` computes the fine through the `FinePolicy`, frees the copy, and, if someone is in the hold queue, **notifies** them (Observer).
4. The hold queue is fair: while someone is waiting, only the first person in the queue can borrow that title.
5. In the output: Asha returned 4 days late and paid 4 x 2 = 8. Ravi got a `HOLD_READY` notice, then borrowed.

---

## 6. How to extend it

**"Premium members can borrow 10 books."** `PremiumMember` is a subclass that changes one class attribute. `Library` reads `member.max_loans`, so it needs no edit.

**"Cap fines at a maximum."** `CappedFine` wraps another policy (Decorator idea). Pass it to `Library`.

**"Send notices by email and SMS."** Write `EmailListener` and `SmsListener` classes with `on_event` and `subscribe` them. `Library` is unchanged.

**"Add DVDs and magazines."** Make `Book` one kind of `Item` (a base class `CatalogItem` with `loan_days`), and let each kind give its own loan period. Do this only if asked: avoid building it up front.

---

## 7. Thread-safety notes (plain words)

- **The danger:** two librarians lend the last copy at the same time. Both see `available == True`; both succeed. One copy, two borrowers.
- **The fix:** one `RLock` around each public method. "Check availability" and "mark unavailable" form a single atomic step. The thread test shows 10 members racing and only 1 gets the book.
- The listeners are called while the lock is held. A slow listener (a real email call) would slow everyone. In real life, put events on a queue and let a worker thread deliver them after the lock is released.
- I used `RLock` so that a method can call another locked method without freezing.

---

## 8. Five follow-up questions with model answers

**Q1. Why separate `Book` and `BookItem`?**
Data that belongs to the title (name, author, isbn) should be stored once. Data that belongs to one physical copy (barcode, is it on loan) is per copy. If we merged them, we would copy the title for every copy, and a typo fix would need many edits.

**Q2. How would search become fast for 1 million books?**
Right now `search` scans all books: O(N). Build an **inverted index**: a dictionary from word -> set of isbns, filled in `add_book`. A query looks up the words and intersects the sets. For huge data you would use a real search engine (that is a system design topic).

**Q3. A member never returns a book. What happens?**
Add a method that finds overdue loans (`due_on < today`) and emits an `OVERDUE` event. The fine keeps growing with days. A policy might also block new checkouts when the member has an overdue loan or unpaid fine: add one check in `checkout`, or better, a list of `CheckoutRule` objects (Strategy) so that new rules are new classes.

**Q4. What if the hold queue member never comes to collect?**
Store a hold with an expiry day. When the hold has expired, drop it and notify the next person. The queue stays a `deque`; each entry becomes `(member_id, expires_on)`.

**Q5. How would you save everything to a database?**
Introduce a `Repository` interface (`save_loan`, `find_item`, ...) and let `Library` use it instead of the dictionaries. The in-memory dictionaries become `InMemoryRepository`. This is Dependency Inversion (file 02). A database transaction replaces the lock for the "check then change" step.

---

**Next:** `14_vending_machine.md`.
