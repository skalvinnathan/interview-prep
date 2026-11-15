# 20. Sixty interview questions with model answers (platform / SRE)

How to use this file:
- Each answer is a **model answer you can say out loud** in about 30 to 60 seconds. Use your own words and add one real example from your work (AKS, Helm, Terraform, GitHub Actions, Prometheus/Grafana/Loki). Interviewers trust a real example more than a perfect definition.
- The tag in brackets, like `[file 04]`, tells you where the full explanation and sources are. Facts here were checked in those files (their source lists are at the end of each file). Where a fact was not verified, the topic file says so.
- Question themes match what 2026 prep guides say is common: scenario-based Kubernetes, Terraform state and modules, incident handling and error budgets, and platform "golden path" design. Those guides are prep-site articles, not employer data, so treat them as indicators only (links at the end).
- Simple structure for any answer: **1) what it is, 2) how it works, 3) a trade-off or failure case, 4) your example.**

Sections: A Linux (1-6) | B Networking (7-12) | C Containers (13-16) | D Kubernetes (17-26) | E Helm, Terraform, CI/CD (27-38) | F Observability and SRE (39-46) | G Concurrency and databases (47-52) | H Security and cloud (53-57) | I Platform design and behavior (58-60)

---

## A. Linux

**1. What happens when you run a command like `ls` in the shell?** `[file 01]`
The shell calls `fork()` to copy itself, then the child calls `exec()` to become `ls`. The shell calls `wait()` for it. `ls` prints to file descriptor 1 (stdout) and exits with a code. The shell reads the code and shows the next prompt. Fork then exec lets the child set up redirects or drop rights before the new program starts.

**2. What is a zombie process and how do you get rid of it?** `[file 01]`
A child that finished, but whose parent has not called `wait()` to read its exit code. It uses no CPU or memory, only a process table slot, and shows as state `Z`. You cannot kill it. Fix the parent so it reaps children, or restart the parent; then PID 1 adopts and reaps the zombie.

**3. SIGTERM vs SIGKILL? What is exit code 137?** `[file 01]`
SIGTERM (15) is a polite request that the program can catch to clean up. SIGKILL (9) cannot be caught or ignored. A shell shows 128 plus the signal number, so 137 = 128 + 9 = killed by SIGKILL, often the OOM killer or a kill after the grace period. 143 = SIGTERM.

**4. Free memory shows only 200 MB. Is the server in trouble?** `[file 01]`
Not necessarily. Linux uses spare RAM as page cache (file data kept in memory) and gives it back when needed. Look at `MemAvailable` (`free -h`, column `available`), which the man page defines as an estimate of memory for starting new applications without swapping. Also check swap use, OOM messages in `dmesg`, and memory pressure.

**5. `df` says the disk is 100% full, but `du` finds only a little data. Why?** `[file 01]`
Most likely a deleted file is still open by a process; the space is freed only when the process closes it. Find it with `lsof +L1`, then restart the process or truncate it through `/proc/<pid>/fd/<n>`. Other causes: files hidden under a mount point, reserved blocks, snapshots, and inode exhaustion (`df -i`).

**6. How do you write a file so a crash does not leave it half-written?** `[file 01]`
Write a temp file in the same directory, `fsync` it, `rename()` it over the real name (atomic on one filesystem), then `fsync` the directory. `fsync` on the file alone does not guarantee the directory entry is saved (man page). Readers see the old or the new file, never a mix.

## B. Networking

**7. What happens when I open `https://example.com` in a browser?** `[file 02]`
DNS lookup (resolver, then root, TLD, authoritative; cached for the TTL). TCP handshake (SYN, SYN-ACK, ACK). TLS handshake (certificate check, key exchange; one round trip in TLS 1.3). HTTP request and response, often over HTTP/2 on one reused connection. A CDN or load balancer may sit in front. I can time each step with `curl -w`.

**8. Explain the TCP three-way handshake and TIME_WAIT.** `[file 02]`
Client sends SYN, server sends SYN-ACK, client sends ACK; now both sides agree on starting sequence numbers. The side that closes first waits in TIME_WAIT for 2 x MSL (RFC 9293) to be sure the last ACK arrived and to keep old packets away from new connections. It is normal; it only hurts when you run out of local ports. Fix with connection reuse.

**9. Many sockets are in CLOSE_WAIT. What does it mean?** `[file 02]`
The other side closed the connection, but our application has not called `close()`. It is an application bug (a socket leak), unlike TIME_WAIT. Find the process with `ss -tanp state close-wait` and fix the code (close response bodies, use `finally`/context managers).

**10. Connection refused vs connection timed out?** `[file 02]`
Refused: the host answered with a reset, so it is reachable but nothing listens on that port; it fails instantly. Timed out: no answer at all, usually a firewall dropping packets, a bad route, or a dead host; it fails after the full timeout. curl exit codes: 7 is connect failure, 28 is timeout, 6 is DNS failure.

**11. How does DNS caching work and why can changes seem slow?** `[file 02]`
Each answer has a TTL. Browser, OS, app libraries, and recursive resolvers cache it until the TTL ends, so users may keep the old IP. Lower the TTL before a planned change, then raise it later. Inside Kubernetes, CoreDNS resolves service names, and DNS trouble is a common cause of random timeouts.

**12. What is NAT and what goes wrong at scale?** `[file 02]`
NAT rewrites the source address and port so many private hosts share a public IP, and keeps a table to map replies back. Idle entries expire (surprise resets). Many connections to the same destination can exhaust ports on the shared IP (SNAT port exhaustion), causing random connect timeouts. Fixes: more public IPs, reuse connections, keep-alives.

## C. Containers

**13. What is a container, and how is it different from a VM?** `[file 03]`
A container is a normal Linux process isolated by namespaces (what it sees: pids, network, mounts) and limited by cgroups (what it uses: CPU, memory). It shares the host kernel. A VM has its own kernel on virtual hardware: stronger isolation but heavier and slower to start.

**14. Why was my container OOMKilled when the node has free memory?** `[file 03, file 04]`
The limit applies to the container's cgroup (`memory.max`), not to the node. At the limit, the kernel OOM killer runs inside that cgroup and kills the process (exit 137, reason OOMKilled). Look at memory over time (leak, spike at start, spike per request), then fix the leak, bound caches, or raise the limit with headroom; set runtime heap sizes below the limit.

**15. Latency is bad but CPU use looks low, with a CPU limit set. What is going on?** `[file 03]`
CPU throttling. The limit becomes a quota per 100 ms period (`cpu.max`). A multi-threaded app can use its quota in a few milliseconds and then freeze for the rest of the period. Averages hide it. Check `nr_throttled` and `throttled_usec` in `cpu.stat` (or cAdvisor throttling metrics). Raise or remove the CPU limit, keep a sensible request, or reduce threads.

**16. How do you build a small and safe image? Why is PID 1 special?** `[file 03]`
Multi-stage build (compile in a big stage, copy only the result), minimal base, pinned digest, non-root `USER`, read-only root filesystem, no secrets in layers, copy dependency files before code for layer cache. PID 1 gets no default signal actions, so an app that ignores SIGTERM will not stop on `docker stop`, and PID 1 must reap zombies. Use exec-form `CMD`, `exec` in scripts, or `--init`/tini.

## D. Kubernetes

**17. What happens when you run `kubectl apply -f deployment.yaml`?** `[file 04]`
The API server authenticates, authorizes (RBAC), validates, runs admission, and stores the object in etcd. The Deployment controller creates a ReplicaSet, which creates Pods. The scheduler assigns each Pod to a node. The kubelet pulls the image, starts containers, and runs probes. When ready, the pod joins Service endpoints.

**18. Liveness vs readiness vs startup probes?** `[file 04]`
Liveness failing makes the kubelet restart the container. Readiness failing removes the pod from Service endpoints without a restart. Startup protects slow starters by holding off the others. Keep liveness cheap and do not check the database in it (an outage would restart every pod at once); put dependency checks in readiness.

**19. Requests vs limits, and QoS classes?** `[file 04]`
Requests are what the scheduler reserves; limits are the ceiling. Over the CPU limit the container is throttled; over the memory limit it is OOM-killed. QoS: Guaranteed (requests equal limits for CPU and memory), Burstable, BestEffort; under node pressure BestEffort is evicted first. Requests are also the base for HPA percentages.

**20. Pod stuck in Pending. How do you debug it?** `[file 04]`
`kubectl describe pod` and read the `FailedScheduling` event. Common causes: not enough CPU or memory on nodes, taints without tolerations, node selector or affinity matching nothing, unbound PVC (also zone mismatch), quota, hostPort use. Then `kubectl describe nodes` for allocated resources, `kubectl get pvc`, `kubectl describe resourcequota`, and the cluster autoscaler status.

**21. Pod in ImagePullBackOff?** `[file 04]`
The kubelet cannot pull the image and retries with growing delays. Check `kubectl describe pod` events for the real message. Causes: wrong image name or tag, image not pushed, private registry without `imagePullSecrets` (or missing ACR/registry attachment), registry unreachable (DNS, firewall), rate limits. Try pulling the same image manually from a node-like environment.

**22. CrashLoopBackOff: what is it and what are your first commands?** `[file 04]`
The container keeps exiting and Kubernetes restarts it with growing back-off (up to 5 minutes). It is a symptom. Run `kubectl logs <pod> --previous`, then `kubectl describe pod` for Last State, reason, and exit code, and check events for probe failures. Exit 1 usually means app or config error, 137 means OOM or kill, and a liveness probe may be killing a slow starter (add a startup probe).

**23. How do you do a zero-downtime rollout?** `[file 04]`
Rolling update with `maxUnavailable: 0`, `maxSurge` of 1 or more, a correct readiness probe, at least 2 replicas spread over nodes and zones, a PDB, and graceful shutdown (handle SIGTERM, a short `preStop` delay so the load balancer drains, enough `terminationGracePeriodSeconds`). Roll back with `kubectl rollout undo`. Database changes must be backward compatible.

**24. How does the HPA work and when does it do nothing?** `[file 04]`
`desired = ceil(current replicas x current metric / target metric)`, evaluated about every 15 s with a 10% tolerance. CPU utilization is relative to the pod's CPU request, so with no request the autoscaler takes no action. It also stops at `maxReplicas`, needs metrics-server for resource metrics, and added pods stay Pending without node capacity (cluster autoscaler needed).

**25. What is a PodDisruptionBudget and how can it hurt?** `[file 04]`
It limits voluntary disruptions (drains, upgrades) with `minAvailable` or `maxUnavailable`. It cannot stop involuntary ones like a node crash. With `maxUnavailable: 0` or `minAvailable` equal to the replica count, a node drain never completes, which blocks cluster upgrades; the same happens with one replica and a strict PDB.

**26. Are Kubernetes Secrets secure? How do RBAC and NetworkPolicy fit in?** `[file 04, file 11]`
Secrets are base64 and stored unencrypted in etcd by default, so enable encryption at rest, restrict get/list/watch, and prefer an external store. RBAC is additive (no deny rules). NetworkPolicy starts as allow-all; once a policy selects a pod only allowed traffic passes, and it works only if the CNI plugin enforces it. Start with default-deny, then allow what is needed.

## E. Helm, Terraform, CI/CD

**27. What is Helm and what are values?** `[file 05]`
Helm is a package manager and template engine for Kubernetes. A chart holds templates and default `values.yaml`; a release is an installed instance with revisions. Values override in order: chart defaults, parent chart, `-f` files (later wins), then `--set`. I keep one values file per environment in Git.

**28. What is an umbrella chart? Pros and cons?** `[file 05]`
A parent chart that depends on subcharts and deploys them as one release. Parent sets subchart values under the subchart's name; `global:` values reach all charts. Pros: one version, one command, one rollback. Cons: all-or-nothing upgrades, one failing subchart blocks the rest, large values. For independent services, separate releases (GitOps) can be better.

**29. What does `helm upgrade --install --atomic` do? What changed in Helm 4?** `[file 05]`
It installs if missing, otherwise upgrades, waits for readiness, and rolls back automatically on failure. In Helm 4, `--atomic` is renamed `--rollback-on-failure` (my Helm 4.3.1 help text shows only the new name). Always capture events and logs before the rollback erases the evidence.

**30. How do you handle rollbacks and secrets in Helm?** `[file 05]`
`helm history` then `helm rollback <release> <revision>`; it makes a new revision with the old content. It does not undo database changes. For secrets: no plaintext in values in Git; use an external secret store with an operator or CSI driver, or SOPS/Sealed Secrets, or workload identity. Release records in the cluster contain rendered values, so lock down Secret access.

**31. What is Terraform state and why is it risky?** `[file 06]`
It maps your resource blocks to real object IDs and attributes. Without it Terraform cannot know what it owns. It may hold secrets in plain text, so store it remotely, encrypted, with access control and versioning. If lost, Terraform may try to recreate resources.

**32. Remote backends and locking: what if two people apply at once?** `[file 06]`
Terraform locks state for operations that could write it; the second run waits or fails with "Error acquiring the state lock". On S3 use `use_lockfile = true` (DynamoDB locking is deprecated). `terraform force-unlock <ID>` only for your own stale lock; unlocking someone else's active lock can corrupt state.

**33. Drift and import?** `[file 06]`
Drift is real infrastructure changed outside Terraform. `terraform plan` shows it; `-refresh-only` shows only outside changes; a nightly plan can alert. For import use an `import` block (and `terraform plan -generate-config-out` to draft the resource block), review the plan, then apply. The older CLI import only updates state.

**34. Workspaces or directories for dev, stage, prod?** `[file 06]`
Separate root configurations (directories) with their own backends and credentials, sharing modules. HashiCorp says CLI workspaces share one backend and are not a suitable isolation mechanism for different stages or teams with different credentials. Workspaces are fine for temporary copies, like branch previews.

**35. Reusable workflows vs composite actions in GitHub Actions?** `[file 07]`
A reusable workflow (`workflow_call`) is a whole workflow with its own jobs and permissions, called from a job; limits include 10 nesting levels and 50 unique workflows per file. A composite action bundles steps and runs inside the caller's job, called from a step. Use reusable workflows for a shared pipeline, composites for repeated step groups.

**36. How do you remove long-lived cloud keys from CI?** `[file 07, file 11]`
OIDC federation: the job requests a short-lived signed token (`id-token: write`), the cloud validates it against a trust policy limited to the repository, branch or environment, and returns short-lived credentials. Keep trust rules narrow, and note GitHub changed the `sub` claim format for repos created after July 15, 2026.

**37. What is script injection in Actions and how do you prevent it?** `[file 07]`
Putting untrusted text (PR title, branch name) into `run:` through `${{ }}` lets it become shell code. Pass it through an environment variable with `env:` and use `"$VAR"`, or pass it as an action input. Also avoid `pull_request_target` with untrusted checkouts, pin actions to full commit SHAs, and keep `GITHUB_TOKEN` read-only by default.

**38. How do you speed up pipelines safely?** `[file 07]`
Cache dependencies by lockfile hash (10 GB per repo default, entries unused for 7 days are removed, never cache secrets), run jobs in parallel, use path filters and concurrency cancellation, cache Docker layers, build once and promote the same image digest. Keep security gates in the PR path.

## F. Observability and SRE

**39. Metrics, logs, traces: when do you use each?** `[file 08]`
Metrics are cheap numbers over time, good for dashboards and alerts. Logs record events, good for the exact error. Traces follow one request across services, good for finding where time goes. A shared trace ID links them. OpenTelemetry lets me instrument once and choose backends later.

**40. What are the four golden signals?** `[file 08]`
Latency, traffic, errors, saturation (Google SRE book). Track latency of successful and failed requests separately; errors include wrong-content and too-slow responses; saturation is how full the most constrained resource is.

**41. Define SLI, SLO, SLA, and error budget.** `[file 08]`
SLI is a measured number (share of requests under 300 ms and non-5xx). SLO is the target (99.9% over 30 days). SLA is a contract with consequences. Error budget is 1 minus the SLO: 0.1% means about 43.2 minutes of full outage per 30 days. When it is spent, slow feature releases and fix reliability.

**42. Why use percentiles, and why can't you average them?** `[file 08]`
The mean hides slow tail requests. A percentile is a position in a sorted list, so p99s from two servers cannot be averaged: in my demo, p99s of 2007 ms and 62 ms averaged to 1035 ms, while the true combined p99 was 2004 ms. Sum histogram buckets and compute the percentile from the sum (`histogram_quantile`), or use a good/total ratio SLO.

**43. How do you design alerts?** `[file 08]`
Page on symptoms users feel (error ratio, latency, SLO burn rate), not causes like CPU 80%. Use multiwindow burn-rate alerts: for a 99.9% SLO, page at 14.4x burn over 1 hour (and 5 minutes), page at 6x over 6 hours, ticket at 1x over 3 days. Every alert needs an owner and a runbook; remove noisy alerts.

**44. How does Prometheus store and query data, and what is cardinality?** `[file 08]`
It scrapes `/metrics` endpoints and stores time series (metric name plus labels). Use `rate()` on counters and `histogram_quantile` on histogram buckets. Cardinality is the number of distinct label combinations; user IDs or request IDs in labels create millions of series and can crash it. Loki follows the same rule for log labels.

**45. How do you run an incident?** `[file 08, file 21]`
Triage impact and severity, declare it, assign an incident commander and a communicator, check recent changes, mitigate first (rollback, flag off, shift traffic), communicate on a schedule, confirm recovery with SLIs. After that, a blameless postmortem with an owner and verifiable action items.

**46. What goes into a blameless postmortem?** `[file 08]`
Summary, impact (duration, users, SLO budget used), trigger and root causes, timeline, what went well or poorly or was lucky, and action items each with owner, priority, ticket, and a verifiable end state. Focus on system gaps, use neutral language, and share it widely. A postmortem without action is the same as none (Google SRE Workbook).

## G. Concurrency and databases

**47. What is a race condition and how do you prevent it?** `[file 09]`
Two actors touch shared data and the result depends on timing: two threads read a counter, both add 1, one update is lost (my demo got 280,239 instead of 800,000 without a lock). Prevent with no sharing, locks, atomic operations (`UPDATE n = n + 1`), optimistic version checks with retry, or a single owner via a queue.

**48. What does idempotent mean? How do you retry a POST safely?** `[file 09]`
Repeating the operation gives the same result. Use an idempotency key: the client sends a unique key, the server stores key and result under a unique constraint and returns the saved result for repeats, checking that the parameters match. Stripe's API works this way.

**49. How do you design retries? What is a retry storm?** `[file 09]`
Retry only temporary errors and only idempotent calls, with exponential backoff, a cap, jitter, a maximum count, and a retry budget, at one layer only. Retries multiply across layers and add load to a struggling dependency, which makes the outage worse; that is a retry storm. Set timeouts from latency percentiles.

**50. Exactly-once delivery: is it possible?** `[file 09]`
Not in general over an unreliable network, because a sender cannot tell a lost message from a lost acknowledgment. Practical systems give at-least-once delivery plus idempotent processing (or transactions inside one system) so the effect happens once.

**51. How do indexes work and what do they cost? How do you debug a slow query?** `[file 10]`
A B-tree index lets the database find rows without scanning the table, but every write must update it and it uses space. For a slow query: find it, run `EXPLAIN (ANALYZE, BUFFERS)` (in a rolled-back transaction if it writes), look for sequential scans and estimate-vs-actual gaps, then fix the index, the query, or the statistics. In my SQLite test an index changed `SCAN` into `SEARCH ... USING INDEX`.

**52. Isolation levels and replication lag?** `[file 10]`
Read committed (PostgreSQL default) stops dirty reads; repeatable read gives a stable snapshot; serializable also prevents serialization anomalies but needs retries on failure. Replication lag is how far a replica is behind; asynchronous replication is fast but can lose recent commits and show stale reads, so read your own writes from the primary and alert on lag.

## H. Security and cloud

**53. Explain OAuth2, OIDC, and JWT in simple words.** `[file 11]`
OAuth2 lets an app get limited access to a user's data without the password: the user logs in at the authorization server, the app exchanges a short-lived code for a scoped access token, and calls the API. OIDC adds an ID token so the app knows who logged in. A JWT is a signed (not encrypted) token with header, payload claims, and signature; the API must verify signature, `iss`, `aud`, and `exp`.

**54. How do you manage secrets?** `[file 11]`
Best is no secret: workload identity or OIDC federation. Otherwise a secrets manager with identity-based access, rotation, and audit; never in Git, images, or logs; per-workload least privilege; scan for leaks. If one leaks, revoke and rotate. In Kubernetes remember base64 is not encryption.

**55. What is supply-chain security and what does Trivy do?** `[file 11]`
Protecting everything that goes into production: pin dependencies, image digests, and action SHAs; minimal non-root images; scan images, dependencies, and IaC; SBOMs; sign images and enforce at admission; provenance (SLSA). Trivy scans images, filesystems, repos, Kubernetes, IaC, and SBOMs for vulnerabilities, misconfigurations, secrets, and licenses; use `--severity` and `--ignore-unfixed`, and a reviewed `.trivyignore`.

**56. Cloud Run, GKE, or Compute Engine?** `[file 12]`
Cloud Run for stateless HTTP and event workloads with no cluster to run (scales to zero, instances are stateless). GKE (Autopilot first) for many services, operators, sidecars, or stateful sets. Compute Engine for OS-level control or legacy software. Choose the least operational burden that meets the requirements.

**57. How do you apply least privilege in a cloud?** `[file 11, file 12]`
Smallest predefined or custom role, at the lowest level (project or resource), to groups, a separate service account per workload, no long-lived keys (federation), regular reviews and audit logs. Remember inheritance: a grant high in the hierarchy reaches everything below.

## I. Platform design and behavior

**58. What is a "golden path" and what does a platform team build?** `[file 04, file 07]`
A golden path is the easy, supported way to ship a service: templates, a standard pipeline (reusable workflows), default Helm charts, observability and security built in, and docs. The platform is a product with internal users: measure adoption and developer time-to-first-deploy, hide Kubernetes details where possible, and allow escape hatches. (Prep guides say golden-path and internal developer platform design questions appear in many 2026 platform loops; they are indicators, not proof.)

**59. Design a safe multi-tenant Kubernetes platform for several teams.** `[file 04, file 11]`
Namespace per team with ResourceQuota and LimitRange, RBAC per team (least privilege), default-deny NetworkPolicy, pod security settings (non-root, drop capabilities), workload identity instead of secrets, admission policies (signed images, no `:latest`), PDBs and requests required, cost labels, shared observability with per-team dashboards and SLOs, GitOps for deployment, and a clear upgrade process (PDBs and surge). Note that namespaces are a soft boundary; stronger isolation needs separate clusters or node pools.

**60. Tell me about a production incident you handled.** `[file 21]`
Use this shape: situation (what broke and user impact), your role, what you checked first and why (impact, recent change), the mitigation, the root cause, and what you changed so it does not repeat (alert, test, runbook, automation). Give numbers (minutes to detect, minutes to mitigate, percent of users). Be honest about mistakes; blameless language shows maturity.

---

## Sources for this file

All technical facts come from the topic files 01 to 12 in this folder, which list their own sources (Linux man pages, kernel docs, RFC 9293 and 8446, Docker, Kubernetes, Helm, HashiCorp, GitHub, Google SRE books, Prometheus, Grafana, OpenTelemetry, PostgreSQL, Google Cloud, Trivy).

2026 interview-theme summaries (prep-site articles, indicators only, not employer data):
- https://www.kore1.com/platform-engineer-interview-questions/
- https://www.kore1.com/sre-interview-questions/
- https://www.kore1.com/devops-engineer-interview-questions/
- https://prachub.com/resources/kubernetes-interview-questions-for-sre-and-platform-engineers-production-scenarios-not-trivia
- https://prachub.com/resources/incident-response-interview-questions-for-sre-and-senior-engineers
- https://startup.jobs/interview-questions/platform-engineer

Not verified: that these exact 60 questions are asked at any specific company. They are built from the topic list you gave me and the general 2026 themes in the articles above. The golden-path and multi-tenancy answers (Q58, Q59) mix verified Kubernetes facts with general platform-engineering practice.
