# 20. Design a Job Scheduler and Workflow Engine

This one is close to your real work. Your provisioning platform installs a product into Kubernetes **in dependency order, with retries**. That is a small workflow engine. In the interview you can say: "I have built something like this, so I will design the general version."

---

## 1. The problem in plain words

Two related systems:

1. **Job scheduler**: run a task **at a given time** or **on a repeating schedule** ("every night at 2 am, run the backup"), or run it **once, now, in the background**. Many tasks at once, spread over many machines.
2. **Workflow engine**: run **many tasks that depend on each other** ("first create the database, then install the app that needs it, then run smoke tests"). If a task fails, retry it, or undo earlier steps. If the machine running it crashes, continue later from where it stopped.

**Analogy: a building project manager.** A schedule says "plumbers come Monday". A project plan says "the walls cannot be painted before plastering; if the pipes leak after testing, redo the pipes". The manager keeps a notebook (state), checks who is free (workers), and never loses track of what is done even when the office closes overnight.

---

## 2. Requirements

**Must-have**
1. Submit a job: run now, run at a time, or run on a cron schedule.
2. Workflows: a graph (DAG) of steps with dependencies; steps run when their dependencies finish.
3. **Retries** with backoff; per-step timeout; max attempts.
4. **Durable state**: survive crashes of workers and of the scheduler itself; resume.
5. Status and history: query a run, see step states, logs, errors.
6. Cancel, pause, retry a failed step by hand, rerun.
7. Many jobs in parallel across a pool of workers; priorities; per-tenant limits.
8. At-least-once execution, with tools for idempotency.

**Non-functional**
- Scheduled jobs should start close to their time (within seconds).
- A job must not run twice at the same time by accident (unless allowed).
- Highly available; scale to millions of jobs per day.

**Out of scope**
- Specific business logic of tasks, a visual designer UI, complex distributed data processing (Spark-like), multi-region active-active.

---

## 3. The numbers (estimates)

Assume 10M job runs per day, average 3 steps each (30M step executions per day); peak 5x.

| Item | Value |
|---|---|
| Step executions per second | 30M / 86,400 = about 350/s average, about 1,750/s peak |
| Scheduled triggers | 1M recurring schedules; many fire at the "top of the hour": spike of maybe 50,000 triggers in the same minute (about 800/s) |
| State writes | each step has about 4 state changes (queued, running, done, plus heartbeat) = about 7,000 writes/s peak |
| State storage | 30M steps/day x 1 KB = 30 GB/day = about 11 TB/year; keep recent hot, archive old |
| Workers | If average step takes 60 s: concurrency = 350/s x 60 = about 21,000 concurrent steps average; peak about 100,000 (many steps are tiny; adjust). This tells us workers must scale horizontally |

Meaning: **state writes and timely triggering** are the hot paths; the actual work happens on workers.

---

## 4. The API

```
POST /v1/jobs
  body: { "type": "send_report", "payload": {...}, "run_at": "2026-11-20T02:00:00Z", "max_attempts": 5,
          "priority": "normal", "idempotency_key": "..." }
  reply: 201 { "job_id": "j1" }

POST /v1/schedules      { "cron": "0 2 * * *", "timezone": "Asia/Kolkata", "job_template": {...} }

POST /v1/workflows      (definition)  { "name": "install_product", "steps": [
     {"id":"db",  "action":"install_db"},
     {"id":"app", "action":"install_app", "depends_on":["db"], "retry":{"max":5,"backoff":"exp"}},
     {"id":"test","action":"smoke_test",  "depends_on":["app"]} ] }

POST /v1/workflows/{name}/runs   { "input": {...}, "idempotency_key": "..." }   -> { "run_id": "r9" }
GET  /v1/runs/{run_id}            -> { state, steps: [{id, state, attempts, error}] }
POST /v1/runs/{run_id}/cancel     POST /v1/runs/{run_id}/steps/{id}/retry

Worker protocol (pull model):
POST /internal/tasks/poll         { "worker_id": "w5", "types": ["install_db"] } -> task or empty
POST /internal/tasks/{id}/heartbeat
POST /internal/tasks/{id}/complete   { "result": {...} }   or /fail { "error": "...", "retryable": true }
```

---

## 5. The data tables

**workflow_definition**: `(name, version) PK`, `dag_json`.

**workflow_run**: `run_id (PK)`, `definition_version`, `state` (running/succeeded/failed/cancelled), `input`, `idempotency_key (unique)`, `started_at`, `finished_at`.

**step_run** (also called task): `(run_id, step_id)` PK, `state` (pending / ready / running / succeeded / failed / skipped), `attempt`, `max_attempts`, `next_run_at`, `lease_owner`, `lease_expires_at`, `result`, `error`, `version`.

**schedule**: `schedule_id`, `cron`, `timezone`, `next_fire_at` (indexed), `job_template`, `last_fired_at`, `enabled`.

**job** (simple one-off jobs): `job_id`, `type`, `payload`, `state`, `run_at` (indexed), `attempt`, `lease_expires_at`, `priority`.

**event_history** (append-only): `(run_id, seq)`, `type`, `data`, `ts` - lets us **replay** the state and debug.

Database choice: SQL with row-level locking (for example `SELECT ... FOR UPDATE SKIP LOCKED` so many schedulers pick different rows without blocking each other) is a strong and simple choice up to a large scale; shard by `run_id` later. Queue or log systems can carry the "ready" tasks to workers.

---

## 6. Version 1 (simple)

```
 [cron daemon on one machine] --> runs scripts directly
```

or

```
 [Scheduler process] loops every second:
     SELECT jobs WHERE run_at <= now AND state='pending'
     run them in threads
```

Problems: if the machine dies, scheduled jobs are missed and running jobs are lost; no retries; two scheduler instances would run each job twice; dependencies are hand-coded; scaling is limited to one machine.

---

## 7. Growing 100x, step by step

**Step 1. Separate the pieces.**

```
 API --> [State DB] <--> [Scheduler / Orchestrator] --> [Task queues] --> [Worker pool]
                               ^                                              |
                               +------------- results / heartbeats ----------+
```

- **API**: accepts jobs and workflows.
- **State DB**: the source of truth for every run and step.
- **Scheduler/Orchestrator**: decides what is ready to run (time has come, dependencies are done).
- **Queues**: hand ready tasks to workers.
- **Workers**: execute and report. Stateless.

**Step 2. Time-based triggering at scale.** Don't poll the whole table. Index `next_fire_at`. Each scheduler instance repeatedly claims a batch of due rows:

```
 BEGIN;
 SELECT * FROM schedule WHERE next_fire_at <= now() ORDER BY next_fire_at LIMIT 500 FOR UPDATE SKIP LOCKED;
 -- for each: create a job/run (with an idempotent key: schedule_id + fire_time), compute next_fire_at
 COMMIT;
```

`SKIP LOCKED` lets many schedulers share the work without double-firing. The idempotent key `schedule_id + fire_time` makes a retry after a crash safe (the unique constraint stops a double run). Spread "top of the hour" spikes with a small random delay (jitter) if allowed. Alternative for huge delay volumes: a hierarchical timing wheel or a sorted set in Redis; but a DB index works very far.

**Step 3. Dependency resolution (the DAG).** When a run starts, steps with no dependencies become `ready`. When a step succeeds, the orchestrator checks its dependents; a step becomes `ready` when **all** its dependencies are `succeeded`. This is a **topological order** execution. A failed step (after retries) marks the run failed (or lets independent branches finish, depending on policy); dependents become `skipped`.

```
        install_db
         /      \
 install_cache  install_app          ready when ALL deps done
         \      /      \
        smoke_test    migrate_data
```

This is exactly your provisioner pattern: install in dependency order; do not start an app before its database is ready.

**Step 4. Task dispatch: pull model with leases.** Workers **pull** tasks (long-poll or from a queue). When a worker takes a task, it gets a **lease** (for example 60 s) and must **heartbeat** to extend it. If the worker dies, the lease expires, and the scheduler puts the task back to `ready` for another worker. This is how crashes are survived. (Same idea as a visibility timeout in a queue, `01g`.)

```
 task: ready -> running (lease_owner=w5, lease_expires=T+60s)
        heartbeat: lease_expires += 60s
        worker dies: lease expires -> task returns to ready (attempt + 1)
```

Pull is better than push: workers take only what they can handle (natural backpressure), and no need to track worker addresses.

**Step 5. Retries.** On failure, if `retryable` and `attempt < max_attempts`: set `next_run_at = now + backoff(attempt) + jitter` and state `ready` (delayed). Non-retryable errors (bad input) fail at once. Step timeouts: if a step runs longer than its timeout, the orchestrator cancels it (or lets the lease expire) and counts an attempt. After max attempts: `failed`, alert, optional **compensation** (undo steps in reverse order: the saga idea from `19`). Retry policy is configured per step. (`03`)

**Step 6. Idempotent tasks (because delivery is at-least-once).** A task may run twice (worker finished the work but crashed before reporting). So each task action should be idempotent (use "create if not exists", "apply desired state"), or use an idempotency token `run_id + step_id + attempt-independent key` passed to the target system. This is the same rule as Kubernetes `apply`: declare desired state and re-running is safe. Say it.

**Step 7. Exactly-once-ish for the state machine.** State transitions are conditional updates (`WHERE state='running' AND lease_owner=w5`). A late "complete" from a worker whose lease already expired is **rejected** (fencing): the lease owner or a version number must match. This stops "zombie" workers from corrupting state.

**Step 8. Priorities and fairness.** Separate queues by priority (critical/normal/batch) and by tenant. Per-tenant concurrency caps so one customer cannot take all workers (`11` for limits). Reserved capacity for critical jobs. Weighted fair scheduling.

**Step 9. Scheduler high availability.** Run several orchestrator instances. They coordinate through the DB (`SKIP LOCKED`) or through **leader election** (etcd/ZooKeeper lease) when only one should do a certain job (for example the cron firing loop). If the leader dies, another takes over within seconds. Remember **misfire policy** for downtime: if the scheduler was down at 02:00, on recovery either run the missed job once now ("catch-up once"), run all missed ones, or skip. Make it a per-schedule setting.

**Step 10. Scale the state store.** Shard by `run_id` (consistent hashing); keep the hot set small by archiving finished runs to cheap storage after N days; partition tables by time; read replicas for the UI/history queries. A single well-indexed Postgres handles thousands of state writes per second; sharding comes after that.

**Step 11. Long-running and human steps.** For steps that wait for something (a Kubernetes rollout, an approval, an external callback): the step goes `waiting` with an external token; a callback or a poller moves it on; use timeouts. (Your maker-checker approvals are exactly a human step in a workflow - nice link to `21`.)

**Step 12. Observability.** Metrics: queue depth and age per type, task start delay (scheduled time vs actual start), success/failure rates, retry counts, lease expirations, stuck runs (running too long). Logs and traces per run id and step id. Alert on SLO such as "99 percent of scheduled jobs start within 10 seconds of their time" (example target).

Final picture:

```
 Clients/API ---> [API servers] ---> [State DB (sharded by run_id) + event history]
                                         ^       ^
                      claim due rows     |       |  conditional state updates
                   [Scheduler/cron loops x N] [Orchestrators x N (DAG logic)]
                                         |
                                         v
                              Task queues (per type, priority, tenant)
                                         |
                         pull + lease + heartbeat
                                         v
                              [Worker pools (autoscaled, per type)]
                                         |
                       results/fail ---> Orchestrator ---> next steps / retries / compensation
 Metrics/Logs/Traces + dashboards + alerts; DLQ + manual retry UI
```

---

## 8. Trade-offs and why

| Choice | Why | Cost |
|---|---|---|
| State in SQL with `SKIP LOCKED` | Simple, strongly consistent, scales far | The DB is the central bottleneck eventually (shard) |
| Pull workers with leases | Crash safe, natural backpressure | Polling overhead; latency of a poll interval (use long-poll) |
| At-least-once execution | Never lose work | Tasks must be idempotent |
| Central orchestrator | Clear control and visibility | A critical component to keep highly available |
| Event history append-only | Debug and replay | Storage growth |
| Cron fire with idempotency key | No double fire | Key design needed |
| Catch-up policy per schedule | Business-specific correctness | More options to explain |
| Retries with backoff | Handle transient failure | Longer completion time; need max attempts |

---

## 9. What breaks and how to fix it

| Failure | Effect | Fix |
|---|---|---|
| Worker dies mid-task | Task stuck "running" | Lease expiry returns task to ready; idempotent tasks |
| Zombie worker reports late | Corrupted state | Fencing: complete only if lease owner/version matches |
| Scheduler dies | Missed triggers | N instances, `SKIP LOCKED`; misfire policy; alert on trigger delay |
| Two schedulers fire the same schedule | Duplicate runs | Unique key (schedule_id, fire_time) |
| Thundering herd at the top of the hour | Overload | Jitter, rate-limited dispatch, autoscaling, queue buffer |
| Poison task retries forever | Wasted capacity | Max attempts, DLQ, circuit breaker per task type |
| Downstream system overloaded by retries | Cascading failure | Backoff + jitter, per-target concurrency limits, breaker |
| State DB slow | Everything slows | Index hygiene, archive old rows, shard, read replicas for UI |
| Long task blocks the pool | Starvation | Per-type pools, timeouts, priority queues |
| Compensation fails | Inconsistent environment | Retry; park and alert; manual runbook |
| Workflow definition changes mid-run | Confusing behaviour | Versioned definitions; running runs keep their version |
| Clock skew | Wrong trigger times | Use DB time; NTP; store UTC and timezone separately |

---

## 10. Questions the interviewer asks next

**Q1. How do you guarantee a job is not run twice?**
A. I guarantee at-least-once, not exactly-once. Claiming uses row locks or leases so two workers do not run the same attempt at the same time, state transitions are conditional, and tasks are idempotent so a duplicate run has the same effect.

**Q2. What happens if the scheduler is down for an hour?**
A. After recovery it finds all rows with `next_fire_at` in the past and applies the schedule's misfire policy: run once now, run all missed, or skip. Alerts fire on trigger delay.

**Q3. How do you execute a DAG?**
A. Store step states. A step is ready when all dependencies succeeded. After each completion the orchestrator re-evaluates the dependents inside a transaction. Failure of a step either fails the run or skips dependents, by policy.

**Q4. How do you handle a task that runs for hours?**
A. Heartbeats extend the lease, checkpointing allows resume, and the task reports progress. If the worker dies, another worker resumes from the checkpoint (or restarts if the task is idempotent).

**Q5. Push or pull for workers?**
A. Pull. Workers ask for work when free, so slow workers do not get overloaded, and we need no service discovery for workers. Push is lower latency but needs health tracking and can overload.

**Q6. How do you do retries without hammering a failing dependency?**
A. Exponential backoff with jitter, a per-target concurrency limit, a circuit breaker, and error classification (retryable or not).

**Q7. How is this like your provisioner?**
A. My provisioner installs components into Kubernetes in dependency order: it is a DAG of steps, each with retries and waits for readiness. State has to survive restarts so a rerun continues. The general engine adds scheduling, leases, multi-tenancy and a durable event history. (Keep the real details at the level you are comfortable with.)

**Q8. How would you build the same with existing tools?**
A. For production I would usually adopt a proven engine (Temporal-style durable execution, Airflow for batch data pipelines, Argo Workflows for Kubernetes) unless I have a special need; I would build custom only when needs are narrow and simple. Knowing the internals helps pick and operate them.

**Q9. How do you keep a multi-tenant system fair?**
A. Per-tenant queues and concurrency caps, weighted scheduling, quotas, and priority classes for system jobs.

**Q10. How do you test a workflow engine?**
A. Deterministic tests with a fake clock; chaos tests that kill workers and schedulers mid-run; property tests (every step ends in a terminal state); replay of history.

---

## 11. Say it out loud (6 sentences)

1. "A job scheduler runs tasks at the right time and a workflow engine runs a graph of dependent steps with retries, and both need durable state so crashes do not lose work."
2. "My estimate is about 1,750 step executions per second at peak, so state writes and timely triggering matter more than raw compute."
3. "State lives in a SQL database; schedulers claim due rows with SKIP LOCKED and a unique key of schedule and fire time so nothing fires twice."
4. "An orchestrator marks a step ready when all its dependencies have succeeded, and stateless workers pull tasks with a lease and heartbeat, so a dead worker's task simply returns to the queue."
5. "Failures retry with exponential backoff and jitter up to a limit, then go to a dead-letter queue or trigger compensating steps, and every task must be idempotent because execution is at-least-once."
6. "Fencing rejects late results from zombie workers, per-tenant limits keep things fair, and I monitor trigger delay, queue age and stuck runs against SLOs."
