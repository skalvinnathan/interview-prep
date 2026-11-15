# 19 - Logger and Notification System (Observer and Strategy)

Python 3.9. All code was run; the output is real.

This file has **two small designs in one program**, because they use the same two patterns:

- **Logger framework**: one `log` call goes to many places (screen, file, memory) in different formats.
- **Notification system**: one event ("order shipped") goes to many users through the channels each user likes (email, SMS, push).

---

## 1. The problem in plain words

**Logger.** Programs write messages like "payment failed" so that people can find bugs later. We want: levels (DEBUG, INFO, WARN, ERROR), the ability to hide low-level messages, and to send messages to several destinations, each with its own format.

**Notification system.** When something happens (for example "order shipped"), tell every interested user. Each user chooses how to be told: email, SMS, push message.

**Analogy.** A **school announcement**. The principal makes one announcement (one event). It goes to the loudspeaker, the notice board, and the class WhatsApp group (many channels). The principal does not know or care who is listening (**Observer**), and each channel has its own way to deliver (**Strategy**).

---

## 2. Requirements I ask the interviewer

**Logger**
1. Levels? -> *DEBUG < INFO < WARN < ERROR. A logger has a minimum level.*
2. Destinations? -> *Console, memory (for tests), later files. Several at once.*
3. Format? -> *Plain text and JSON. Per destination.*
4. Many named loggers? -> *Yes, `get_logger("payments")`; the same name returns the same logger.*
5. Slow destinations must not slow the app? -> *Yes: optional async mode.*
6. Threads? -> *Yes. Lines must never be mixed up inside one line.*

**Notifications**
1. Who gets what? -> *Users subscribe to event types.*
2. Channels? -> *Email, SMS, push. More later.*
3. Do users choose channels? -> *Yes, a set per user.*
4. If a channel fails? -> *One user's failure must not stop others; log it. Retry is an extension.*
5. Message text? -> *A template per event with placeholders.*

---

## 3. Classes and methods (the picture)

```text
LOGGER                                          NOTIFICATIONS
------                                          -------------
+-------------------+  has many  +---------+    +----------------------+   has many   +---------+
|      Logger       |----------->| Appender|    | NotificationService  |------------->| Channel |
|-------------------|  (Observer)| (abstr.)|    |----------------------|  (Strategy)  | (abstr.)|
| name, level       |            | append( |    | subscribe(event,user)|              | send(   |
| debug/info/warn/  |            |  record)|    | publish(event, **d)  |              | user,   |
|   error(msg)      |            +----+----+    | templates            |              | text)   |
+---------+---------+            Stream | Memory +-----------+----------+              +----+----+
          |                      Appender Appender            | has many                Email Sms Push
          | creates              AsyncAppender (wraps one)    v (Observer)               RetryingChannel (ext.)
          v                                           +----------------+
   LogRecord(level, name,      Formatter (abstract)   | User           |
   message, timestamp)         Plain / Json           | name, channels |
                                                      +----------------+
   LogManager.get_logger(name)  <- registry: one logger per name
```

**Where are the patterns?**
- **Observer:** a `Logger` holds a list of appenders and tells each one about every record. `NotificationService` holds subscribers per event.
- **Strategy:** `Formatter` (how to write a record) and `Channel` (how to deliver). Each can be swapped.
- **Decorator:** `AsyncAppender` and `RetryingChannel` wrap another object that has the same interface and add behaviour.

---

## 4. Full code

```python
import io                                      # io.StringIO: a fake file that lives in memory
import json                                    # JSON formatting
import queue                                   # thread-safe queue for the async appender
import threading                               # Lock and Thread
from abc import ABC, abstractmethod            # "promise" classes
from enum import Enum                          # fixed named choices


# =====================  PART A: LOGGER  =====================

class Level(Enum):
    DEBUG = 10                                 # numbers let us compare levels
    INFO = 20
    WARN = 30
    ERROR = 40


class LogRecord:
    def __init__(self, level, logger_name, message, timestamp):
        self.level = level
        self.logger_name = logger_name
        self.message = message
        self.timestamp = timestamp             # injected time (a number here) so tests are repeatable


# ---- formatters (Strategy) ----

class Formatter(ABC):
    @abstractmethod
    def format(self, record):
        pass


class PlainFormatter(Formatter):
    def format(self, record):
        # example: [t=1] INFO  app: started   (level padded to 5 characters so columns line up)
        return "[t=%s] %-5s %s: %s" % (record.timestamp, record.level.name, record.logger_name, record.message)


class JsonFormatter(Formatter):
    def format(self, record):
        # sort_keys makes the output the same every time
        return json.dumps({"t": record.timestamp, "level": record.level.name,
                           "logger": record.logger_name, "msg": record.message}, sort_keys=True)


# ---- appenders (the Observers of a logger) ----

class Appender(ABC):
    @abstractmethod
    def append(self, record):
        pass


class FormattingAppender(Appender):
    """Common part: filter by its own minimum level, format, then write."""
    def __init__(self, formatter, min_level=Level.DEBUG):
        self.formatter = formatter
        self.min_level = min_level
        self._lock = threading.Lock()          # so two threads never mix their text inside one line

    def append(self, record):
        if record.level.value < self.min_level.value:
            return                             # this destination does not want low-level messages
        text = self.formatter.format(record)
        with self._lock:
            self._write(text)

    @abstractmethod
    def _write(self, text):
        pass


class StreamAppender(FormattingAppender):      # writes to any file-like object (screen, file, StringIO)
    def __init__(self, stream, formatter, min_level=Level.DEBUG):
        super().__init__(formatter, min_level)
        self.stream = stream

    def _write(self, text):
        self.stream.write(text + "\n")


class MemoryAppender(FormattingAppender):      # keeps lines in a list (great for tests)
    def __init__(self, formatter, min_level=Level.DEBUG):
        super().__init__(formatter, min_level)
        self.lines = []

    def _write(self, text):
        self.lines.append(text)


class AsyncAppender(Appender):
    """Decorator: the caller only puts the record on a queue; a worker thread does the slow writing."""
    _STOP = object()                           # a special marker meaning "stop the worker"

    def __init__(self, inner):
        self.inner = inner
        self._queue = queue.Queue()            # thread-safe: many threads can put, one thread gets
        self._worker = threading.Thread(target=self._run)
        self._worker.start()

    def append(self, record):
        self._queue.put(record)                # returns at once, never waits for the slow inner appender

    def _run(self):
        while True:
            item = self._queue.get()           # waits until something arrives
            if item is self._STOP:
                return
            self.inner.append(item)

    def close(self):
        self._queue.put(self._STOP)            # ask the worker to finish after the records already queued
        self._worker.join()                    # wait for it


# ---- logger and registry ----

class Logger:
    def __init__(self, name, level, clock):
        self.name = name
        self.level = level                     # minimum level this logger accepts
        self.clock = clock
        self._appenders = []
        self._lock = threading.Lock()

    def add_appender(self, appender):
        with self._lock:
            self._appenders.append(appender)

    def log(self, level, message):
        if level.value < self.level.value:
            return                             # cheap early exit: this is why levels exist
        record = LogRecord(level, self.name, message, self.clock())
        with self._lock:
            targets = list(self._appenders)    # copy, so adding an appender while logging is safe
        for a in targets:                      # tell every observer
            a.append(record)

    def debug(self, m): self.log(Level.DEBUG, m)
    def info(self, m): self.log(Level.INFO, m)
    def warn(self, m): self.log(Level.WARN, m)
    def error(self, m): self.log(Level.ERROR, m)


class LogManager:
    _loggers = {}                              # name -> Logger  (a simple registry)
    _lock = threading.Lock()

    @classmethod
    def get_logger(cls, name, clock, level=Level.INFO):
        with cls._lock:                        # two threads asking for the same name must get the same logger
            if name not in cls._loggers:
                cls._loggers[name] = Logger(name, level, clock)
            return cls._loggers[name]


# =====================  PART B: NOTIFICATIONS  =====================

class User:
    def __init__(self, name, channels):
        self.name = name
        self.channels = channels               # list of channel names the user likes, e.g. ["email", "push"]


class Channel(ABC):
    name = "channel"
    @abstractmethod
    def send(self, user, text):
        pass


class OutboxChannel(Channel):
    """Demo channel: instead of really sending, it writes into a shared list called an outbox."""
    def __init__(self, name, outbox):
        self.name = name
        self.outbox = outbox

    def send(self, user, text):
        self.outbox.append(self.name.upper() + " to " + user.name + ": " + text)


class NotificationService:
    def __init__(self, channels, templates, logger):
        self.channels = {c.name: c for c in channels}   # name -> Channel
        self.templates = templates                      # event -> text with {placeholders}
        self.logger = logger
        self._subs = {}                                 # event -> list of users (the Observers)
        self._lock = threading.Lock()

    def subscribe(self, event, user):
        with self._lock:
            self._subs.setdefault(event, []).append(user)

    def publish(self, event, **data):
        text = self.templates[event].format(**data)     # fill the template: "Order {order_id} shipped" -> "Order 7 shipped"
        with self._lock:
            users = list(self._subs.get(event, []))     # copy so we do not hold the lock while sending
        sent, failed = 0, 0
        for user in users:
            for ch_name in user.channels:
                channel = self.channels.get(ch_name)
                if channel is None:
                    self.logger.warn("unknown channel " + ch_name + " for " + user.name)
                    continue
                try:
                    channel.send(user, text)
                    sent += 1
                except Exception as e:                  # one failure must not stop the others
                    failed += 1
                    self.logger.error("send failed via " + ch_name + " to " + user.name + ": " + str(e))
        return sent, failed


# ---------- EXTENSION: retry (Decorator), a flaky channel for testing ----------

class RetryingChannel(Channel):
    def __init__(self, inner, attempts):
        self.inner = inner
        self.attempts = attempts
        self.name = inner.name                          # looks exactly like the inner channel

    def send(self, user, text):
        last_error = None
        for _ in range(self.attempts):
            try:
                return self.inner.send(user, text)      # success: done
            except Exception as e:
                last_error = e                          # remember and try again
        raise last_error                                # still failing after all attempts


class FlakyChannel(Channel):
    """Fails the first `failures` times, then works (to test retries)."""
    def __init__(self, name, outbox, failures):
        self.name = name
        self.outbox = outbox
        self.failures = failures

    def send(self, user, text):
        if self.failures > 0:
            self.failures -= 1
            raise ConnectionError("network down")
        self.outbox.append(self.name.upper() + " to " + user.name + ": " + text)


class Ticker:
    """A fake clock that goes 1, 2, 3 ... each time it is read."""
    def __init__(self):
        self.t = 0
        self._lock = threading.Lock()
    def __call__(self):
        with self._lock:
            self.t += 1
            return self.t


def main():
    print("===== Logger =====")
    screen = io.StringIO()                              # pretend this is the console
    plain = StreamAppender(screen, PlainFormatter())
    mem_json = MemoryAppender(JsonFormatter(), min_level=Level.WARN)   # this destination only wants WARN and above
    log = LogManager.get_logger("app", Ticker(), level=Level.INFO)
    log.add_appender(plain)
    log.add_appender(mem_json)

    log.debug("hidden: below the logger level")         # dropped by the logger
    log.info("service started")
    log.warn("disk 85 percent full")
    log.error("payment failed")
    print("console (plain, all levels >= INFO):")
    print(screen.getvalue().rstrip())
    print("memory (json, only >= WARN):")
    for line in mem_json.lines:
        print(" ", line)
    print("same name gives same logger:", LogManager.get_logger("app", Ticker()) is log)

    print("===== Notifications =====")
    outbox = []
    notif_log_lines = MemoryAppender(PlainFormatter())
    nlog = Logger("notify", Level.INFO, Ticker())
    nlog.add_appender(notif_log_lines)
    service = NotificationService(
        [OutboxChannel("email", outbox), OutboxChannel("sms", outbox), OutboxChannel("push", outbox)],
        {"ORDER_SHIPPED": "Order {order_id} has shipped"}, nlog)
    asha = User("Asha", ["email", "push"])
    ben = User("Ben", ["sms"])
    service.subscribe("ORDER_SHIPPED", asha)
    service.subscribe("ORDER_SHIPPED", ben)
    print("publish ->", service.publish("ORDER_SHIPPED", order_id=7), "(sent, failed)")
    for line in outbox:
        print(" ", line)

    # ---- extension demo ----
    print("--- extension: flaky channel, then retry decorator ---")
    out2 = []
    elog = MemoryAppender(PlainFormatter())
    lg = Logger("notify2", Level.INFO, Ticker())
    lg.add_appender(elog)
    u = User("Cara", ["email"])
    s1 = NotificationService([FlakyChannel("email", out2, failures=2)], {"E": "hello {x}"}, lg)
    s1.subscribe("E", u)
    print("without retry:", s1.publish("E", x=1), "| outbox:", out2)
    s2 = NotificationService([RetryingChannel(FlakyChannel("email", out2, failures=2), attempts=3)], {"E": "hello {x}"}, lg)
    s2.subscribe("E", u)
    print("with retry   :", s2.publish("E", x=2), "| outbox:", out2)
    print("error log line:", elog.lines[0])

    # ---- extension: async appender ----
    print("--- extension: async appender ---")
    target = MemoryAppender(PlainFormatter())
    async_app = AsyncAppender(target)
    alog = Logger("async", Level.INFO, Ticker())
    alog.add_appender(async_app)
    for i in range(3):
        alog.info("message " + str(i))
    async_app.close()                                   # wait until the worker has written everything
    print(target.lines)

    # ---- thread test ----
    print("--- thread test ---")
    shared = MemoryAppender(PlainFormatter())
    tlog = Logger("threads", Level.INFO, Ticker())
    tlog.add_appender(shared)
    def worker(n):
        for i in range(100):
            tlog.info("worker " + str(n) + " line " + str(i))
    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for t in threads: t.start()
    for t in threads: t.join()
    print("lines:", len(shared.lines), "(expected 800)",
          "| all lines complete:", all(l.endswith(tuple(str(i) for i in range(100))) and "worker" in l for l in shared.lines),
          "| unique timestamps:", len({l.split("]")[0] for l in shared.lines}) == 800)


if __name__ == "__main__":
    main()
```

Output I got when I ran it:

```text
===== Logger =====
console (plain, all levels >= INFO):
[t=1] INFO  app: service started
[t=2] WARN  app: disk 85 percent full
[t=3] ERROR app: payment failed
memory (json, only >= WARN):
  {"level": "WARN", "logger": "app", "msg": "disk 85 percent full", "t": 2}
  {"level": "ERROR", "logger": "app", "msg": "payment failed", "t": 3}
same name gives same logger: True
===== Notifications =====
publish -> (3, 0) (sent, failed)
  EMAIL to Asha: Order 7 has shipped
  PUSH to Asha: Order 7 has shipped
  SMS to Ben: Order 7 has shipped
--- extension: flaky channel, then retry decorator ---
without retry: (0, 1) | outbox: []
with retry   : (1, 0) | outbox: ['EMAIL to Cara: hello 2']
error log line: [t=1] ERROR notify2: send failed via email to Cara: network down
--- extension: async appender ---
['[t=1] INFO  async: message 0', '[t=2] INFO  async: message 1', '[t=3] INFO  async: message 2']
--- thread test ---
lines: 800 (expected 800) | all lines complete: True | unique timestamps: True
```

---

## 5. How the code works (walk through)

**Logger**
1. `logger.info("...")` calls `log(Level.INFO, ...)`. If the level is below the logger's minimum, it returns at once. This is the cheapest filter.
2. Otherwise it builds one `LogRecord`, and gives it to **every appender** (Observer). Each appender has its **own** minimum level and its **own formatter** (Strategy). In the output, the JSON memory appender only received WARN and ERROR, while the console received INFO, WARN, ERROR.
3. `LogManager.get_logger` is a registry: asking for `"app"` twice returns the same object.

**Notifications**
1. `publish` fills the template, then goes through the subscribers. Each user gets the message on each of their chosen channels.
2. A failure in one channel is caught, logged as an error, and the loop continues (so one bad channel does not block Ben's SMS).
3. In the extension, `RetryingChannel` wraps the flaky channel and has the same `name` and `send` method, so the service does not know the difference (Decorator).

---

## 6. How to extend it

**"Log to a file."** Pass `open("app.log", "a")` into a `StreamAppender`. No new class. For daily rotation, write a `RotatingFileAppender(FormattingAppender)`.

**"Add a Slack channel."** One class `SlackChannel(Channel)`. Pass it to the service.

**"Users can mute some events."** Add `muted_events` to `User`; skip in `publish`. Or make a `NotificationFilter` interface (Strategy) if rules grow.

**"Priority: critical alerts go to all channels."** Add a `priority` argument to `publish` and a rule object that chooses channels (instead of `user.channels`).

**"Do not block the caller when sending."** Use the same trick as `AsyncAppender`: a queue and a worker. Wrap any `Channel` in an `AsyncChannel` decorator.

---

## 7. Thread-safety notes (plain words)

- **Logger list:** a thread may add an appender while another is logging. Iterating a list that changes causes errors. Fix: copy the list under a lock, then loop over the copy (`targets = list(self._appenders)`).
- **Lines must not mix:** two threads writing to one file may interleave characters. Fix: a lock inside the appender around the write (`FormattingAppender._lock`). The thread test: 8 threads write 800 lines; all are complete.
- **Do not hold a lock while doing slow work.** `publish` copies the subscriber list under the lock and releases it **before** sending messages, so a slow SMS service does not block `subscribe`.
- **AsyncAppender** uses `queue.Queue`, which is already thread-safe. Many threads `put`, one worker `get`s. `close()` sends a stop marker so no message is lost.
- **Registry:** `get_logger` has a lock so two threads asking for the same new name cannot create two loggers.

---

## 8. Five follow-up questions with model answers

**Q1. Why do both the logger and each appender have a level?**
The logger level is a fast global switch ("this program only cares about INFO and above") and avoids creating records at all. The appender level lets different destinations differ: for example, the console shows INFO but the alerting file only wants ERROR.

**Q2. What happens to messages in the async queue if the program crashes?**
They are lost. That is the trade-off of async logging: speed against safety. Options: flush on `ERROR` synchronously; bound the queue size (and decide: block or drop when full); register a shutdown hook that calls `close()`. I would ask the interviewer which matters more.

**Q3. Observer or just a direct call? Why is Observer worth it here?**
With a direct call, `Logger` would need to know about console, files, and JSON. Every new destination would change `Logger`. With Observer, `Logger` knows only the `Appender` interface. The cost is a little indirection, which is worth it when destinations are expected to grow (and they will).

**Q4. How do you avoid sending the same notification twice (retries, duplicates)?**
Give each notification a unique id, and let each channel (or a store) remember ids already delivered, so a repeat is ignored. This is **idempotency**. Retries are then safe.

**Q5. How would this scale to millions of users?**
Do not loop through all users inside `publish`. Put the event on a message queue (Kafka, SQS) and let many worker processes pick it up, each handling a slice of the users and calling channels in batches. The classes stay almost the same: `Channel` and template logic live in the workers. This is where LLD meets system design; I would say so and keep the LLD simple.

---

**Next:** `20_tic_tac_toe_or_chess_basics.md`.
