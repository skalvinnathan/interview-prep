# 21. Fifteen "production is down" scenarios, with step-by-step answers

How to use this file:
- Interviewers use scenarios to see **how you think under pressure**, not whether you remember one command. Talk out loud in steps.
- Every scenario has: **Situation**, **First steps**, **Diagnose (commands)**, **Fix**, **Prevent**, and **Say this** (the one-sentence summary).
- Commands are standard and explained in the topic files `[file NN]`. Outputs here are not shown; see the topic files for real or sample output. I did not run these against any cluster.
- Facts about Kubernetes, SRE practice, and tools come from the sources listed in the topic files (Kubernetes docs, Google SRE books, GitHub docs, HashiCorp docs, PostgreSQL docs). The scenarios themselves are my teaching examples. They are not real events.

---

## The universal frame (use it in every scenario)

```
 1. IMPACT    who is hurt, how badly, since when?  (SLO dashboard, error rate, support tickets)
 2. DECLARE   severity, incident commander, one channel, status updates on a clock
 3. CHANGES   what changed just before? deploy, config, flag, traffic, certificate, dependency
 4. MITIGATE  stop the pain first: rollback, flag off, shift traffic, scale, rate-limit
 5. DIAGNOSE  now find the cause, using the four golden signals (latency, traffic, errors, saturation)
 6. CONFIRM   recovery shown by the SLIs, not by feelings; keep watching
 7. LEARN     blameless postmortem, owned and verifiable action items
```
Google's SRE book tells you to alert on **symptoms** and track latency, traffic, errors, and saturation; the SRE Workbook says a postmortem needs owned actions. "Mitigate before you find the root cause" is the habit interviewers look for. `[file 08]`

Keep a **timeline** as you go (time, action, result). It becomes the postmortem.

---

## Scenario 1. All users get 5xx errors right after a deployment

**Situation**: 10 minutes after a release, the error-rate alert pages you. Users see HTTP 500/502.

**First steps**: Check the SLO/error dashboard for the start time. Ask: "what deployed at that time?" Declare the incident (SEV1 or SEV2 depending on the share of users).

**Diagnose**:
```bash
kubectl rollout status deploy/web -n prod
kubectl get pods -n prod -o wide              # new pods Ready? restarts?
kubectl logs deploy/web -n prod --since=15m | tail -50
kubectl get events -n prod --sort-by=.lastTimestamp | tail -20
```
Compare the error start time with the deploy time, and old vs new version in logs and metrics (per-version error rate).

**Fix (mitigate first)**: `kubectl rollout undo deploy/web -n prod` (or `helm rollback web <good-revision>`). If a feature flag guards the change, turn it off instead. Watch the error rate fall.

**Prevent**: readiness probes that really test the app, canary or progressive rollout with automatic rollback on SLO burn, `helm upgrade --wait --rollback-on-failure`, a pre-prod test of the same change, deploy gates. `[file 04, 05]`

**Say this**: "Impact first, then what changed, then roll back. The root cause comes after users are safe."

---

## Scenario 2. New pods are in CrashLoopBackOff after a release

**Situation**: Rollout is stuck, some pods in CrashLoopBackOff. Old pods still serve traffic (the rollout stopped safely).

**First steps**: Because maxUnavailable protected you, there may be little user impact. Still treat it as urgent but calm. Do **not** delete pods repeatedly.

**Diagnose**:
```bash
kubectl get pods -n prod
kubectl logs <new-pod> -n prod --previous       # last words of the crashed container
kubectl describe pod <new-pod> -n prod          # Last State, Exit Code, Reason, probe events
```
Read the exit code: 1 (app error: bad config, missing env var or Secret, cannot reach database), 137 (killed: OOM or too slow to stop), 139 (segfault), 143 (SIGTERM). Look for `Liveness probe failed` (slow start killed by probe). Check recent ConfigMap and Secret changes and image tag.

**Fix**: roll back (`kubectl rollout undo`), or fix the config (missing Secret key, wrong env name) and roll forward. For slow starts add a startup probe.

**Prevent**: validate config in CI (`helm template` + schema checks), smoke test the image in a staging cluster, fail fast and log a clear startup error, do not make liveness probes depend on other services. `[file 04]`

**Say this**: "CrashLoopBackOff is a symptom; `--previous` logs and the exit code tell me why the process exits."

---

## Scenario 3. Latency is high, but CPU and memory graphs look normal

**Situation**: p99 latency tripled. Pods look healthy. CPU "only 30%".

**First steps**: Check which signal moved: latency yes, errors maybe not, traffic same? Look at p99 per endpoint and per version, not the average.

**Diagnose** (work from the edge inward):
1. **CPU throttling**: check cAdvisor throttling metrics, or inside a container `grep throttled /sys/fs/cgroup/cpu.stat` (`nr_throttled`, `throttled_usec`). Kubernetes docs: CPU limits are enforced by throttling. `[file 03]`
2. **Dependency latency**: traces show which downstream call is slow (database, cache, external API).
3. **Database**: slow query (`EXPLAIN ANALYZE`), lock waits, connection pool saturation, replica lag. `[file 10]`
4. **Network/DNS**: `curl -w` timings, `dig` time, retransmissions. `[file 02]`
5. **GC pauses** or thread pool exhaustion in the app; queue depth growing (backpressure missing). `[file 09]`
6. **Noisy neighbor** or node problem: is it one node only? `kubectl get pods -o wide` and compare.

**Fix**: depending on cause: raise or remove the CPU limit (keep the request), add the missing index, enlarge the pool or add timeouts, scale out, drain a bad node.

**Prevent**: alert on p99 and on throttling ratio, trace sampling on, saturation signals on dashboards, load tests.

**Say this**: "Average CPU hides throttling and tails. I check throttling, the slowest dependency in a trace, and the database."

---

## Scenario 4. A node goes NotReady and many pods are Pending or evicted

**Situation**: `kubectl get nodes` shows a node NotReady. Some pods are Terminating or Pending.

**First steps**: Is the service still serving (do you have replicas on other nodes/zones)? If yes, you have time. If a whole zone is affected, jump to scenario 15.

**Diagnose**:
```bash
kubectl get nodes
kubectl describe node <node>                 # Conditions: Ready, MemoryPressure, DiskPressure, PIDPressure; Events
kubectl get pods -A -o wide --field-selector spec.nodeName=<node>
kubectl top node                             # metrics-server
```
On AKS/GKE use the cloud console or CLI to see the VM state, and node pool autoscaler events. Common causes: node out of memory or disk (kubelet evicts), kubelet crashed, network partition, VM host maintenance, a bad node image after an upgrade.

**Fix**: cordon (`kubectl cordon <node>`), drain (`kubectl drain <node> --ignore-daemonsets --delete-emptydir-data`), let the pods reschedule, then reimage or replace the node. If drain hangs, check PDBs (a `maxUnavailable: 0` PDB blocks drains, Kubernetes docs). Pending pods after the loss: check capacity (`describe pod` events) and the cluster autoscaler. `[file 04]`

**Prevent**: multiple replicas spread across nodes and zones (topology spread or anti-affinity), PDBs that allow at least one eviction, requests and limits so nodes are not overcommitted, node auto-repair, alerts on node conditions.

**Say this**: "Replicas on other nodes keep users safe; I cordon, drain, replace, and make sure PDBs and spreading allow it."

---

## Scenario 5. "No space left on device" on a VM or node, but nothing big is found

**Situation**: A service fails writing. `df -h` shows 100% on `/var`.

**First steps**: Free a little space safely so the service can recover (rotate or truncate an old log, clean package caches), but do not delete things blindly.

**Diagnose**: `[file 01]`
```bash
df -h            # which filesystem
df -i            # inode exhaustion?
du -xh /var --max-depth=2 2>/dev/null | sort -h | tail
lsof +L1         # deleted files still held open by a process
```
If `du` shows far less than `df`, a **deleted but open file** is the likely cause (the man page logic: space is freed only when the last open handle closes). Other causes: many tiny files (inodes), container logs and images (`docker system df`, `crictl images`), a runaway core dump, files hidden under a mount.

**Fix**: restart the process that holds the deleted file (or truncate it via `/proc/<pid>/fd/<n>`), delete old logs and unused images, fix log rotation, and for inode exhaustion remove the directory with millions of files.

**Prevent**: log rotation and size limits (`max-size` for container logs), disk usage alerts at 80 percent and a **predictive** alert (will fill in 4 hours), ephemeral-storage requests and limits in Kubernetes, separate volumes for logs and data.

**Say this**: "df and du disagree because of deleted-but-open files; `lsof +L1` finds the holder."

---

## Scenario 6. Random timeouts between services; DNS is suspected

**Situation**: Some requests fail with "could not resolve host" or time out after exactly 5 seconds, intermittently.

**First steps**: Check whether it affects one service, one node, or the whole cluster. Look at CoreDNS health.

**Diagnose**: `[file 02]`
```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns         # CoreDNS pods healthy?
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=50
kubectl run dnstest --rm -it --image=busybox:1.36 -- nslookup kubernetes.default
kubectl run dnstest --rm -it --image=busybox:1.36 -- nslookup example.com
kubectl exec -it <pod> -- cat /etc/resolv.conf               # ndots, search domains
```
Time lookups from inside a pod (`time nslookup ...`). Ideas to check: CoreDNS overloaded or throttled (CPU limit!), upstream resolver slow or blocking, a NetworkPolicy blocking UDP/TCP 53, conntrack table full or NAT port exhaustion (UDP DNS packets dropped), `ndots:5` causing many failed lookups for external names (each tries several search suffixes), nodes with a bad resolver config.

**Fix**: scale CoreDNS, raise its CPU limit or remove it, add a node-local DNS cache, use fully qualified names (trailing dot) for external hosts, lower `ndots` for the workloads that need it, allow DNS in NetworkPolicy, fix the upstream.

**Prevent**: CoreDNS dashboards and alerts (latency, errors, SERVFAIL), load test DNS, app-side connection reuse and DNS caching with sane TTL.

**Say this**: "I test DNS from inside the pod, check CoreDNS capacity and throttling, then conntrack and NetworkPolicy."

---

## Scenario 7. Users save data but cannot see it; read replica lag

**Situation**: "I updated my profile and it shows the old value." Appears and disappears.

**First steps**: Suspect replication lag: the app reads from a replica that is behind the primary.

**Diagnose**: `[file 10]`
```sql
-- on the primary (PostgreSQL)
SELECT application_name, state, sent_lsn, replay_lsn,
       pg_wal_lsn_diff(sent_lsn, replay_lsn) AS bytes_behind
FROM pg_stat_replication;
-- on a standby
SELECT now() - pg_last_xact_replay_timestamp() AS lag;
```
The PostgreSQL docs say asynchronous replication has "a small delay" between commit on the primary and visibility on the standby. A big gap between current and sent position hints at a loaded primary; a gap between sent and received hints at network delay or a loaded standby. Look for a long-running query on the replica that conflicts with replay, a write burst (bulk update, big migration), or a weak replica.

**Fix**: short term, route that user's reads to the primary after a write (read-your-writes) or kill the blocking long query on the replica. Medium term, reduce the write burst (batch smaller), size the replica properly, and tune standby conflict settings.

**Prevent**: alert on lag (seconds and bytes), route only lag-tolerant reads to replicas, dedicated analytics replica, tests that read right after write.

**Say this**: "Async replicas are slightly behind by design. I measure lag, and protect read-your-writes by reading from the primary."

---

## Scenario 8. The database is slow and connections are exhausted

**Situation**: API timeouts; logs say "too many connections" or pool timeouts.

**First steps**: Protect the database: reduce load (rate-limit, shed non-critical traffic, pause batch jobs). Check what changed (new release, a new query, a traffic spike).

**Diagnose**: `[file 10, 09]`
```sql
SELECT state, count(*) FROM pg_stat_activity GROUP BY 1;                 -- many "idle in transaction"?
SELECT pid, now()-query_start AS runtime, state, left(query,80)
FROM pg_stat_activity WHERE state <> 'idle' ORDER BY runtime DESC LIMIT 10;   -- long queries
SELECT * FROM pg_locks WHERE NOT granted;                                -- waiting locks
```
Typical causes: a missing index after a new query (full scans), a long transaction holding locks, connection leak in the app, too many app replicas times pool size, retries piling on (retry storm), autoscaling that added pods and so more connections.

**Fix**: cancel or terminate the worst query (`pg_cancel_backend`, then `pg_terminate_backend` if needed), roll back the release that introduced it, add the missing index (concurrently), cap pool sizes, put a pooler (PgBouncer) in front, set statement and idle-in-transaction timeouts.

**Prevent**: slow query log and `EXPLAIN` in review, connection budgets per service, timeouts and retry budgets, load tests, alert on connections used percent.

**Say this**: "First reduce load, then find the long query or leak, kill or roll back, and then fix with an index, pool limits, and timeouts."

---

## Scenario 9. A TLS certificate expired

**Situation**: Browsers show "certificate expired"; service-to-service calls fail with handshake errors.

**First steps**: Confirm which certificate and where (public edge, ingress, internal service, a client cert, a CA).

**Diagnose**: `[file 02]`
```bash
echo | openssl s_client -connect host:443 -servername host 2>/dev/null | openssl x509 -noout -dates -subject -issuer
kubectl get certificate -A                       # if using cert-manager
kubectl describe certificate <name> -n <ns>      # events: why renewal failed
kubectl get secret <tls-secret> -n <ns> -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -dates
```
Also check the client's clock (a wrong clock looks like "not yet valid"/"expired"). Why did renewal fail? Common: cert-manager cannot complete the ACME challenge (DNS or HTTP route blocked), an expired API token for the DNS provider, rate limit, the issuer changed, or nobody owned renewal for a manually managed certificate.

**Fix**: renew or reissue now; for cert-manager fix the cause (challenge route, credentials) and trigger renewal; deploy the new secret; make sure the pods reload it (some apps need a restart; ingress controllers usually reload). Verify with `openssl s_client` from outside.

**Prevent**: automate renewal, alert **30 days and 7 days before** expiry from an external probe (blackbox exporter) and from cert-manager metrics, keep an inventory with owners, test renewal.

**Say this**: "Fix by renewing and reloading, then make expiry impossible to miss: automation plus alerts weeks ahead."

---

## Scenario 10. A small slowdown turns into a full outage (retry storm, cascading failure)

**Situation**: A downstream service slowed briefly. Now everything is timing out and load keeps rising even though user traffic did not increase.

**First steps**: Recognize the pattern: callers time out and retry, which adds load, which slows the service more. The SRE book says retries can keep a backend overloaded even after the original traffic drops.

**Diagnose**: `[file 09]` Compare request rates **into** the failing service vs user requests (is it 3 to 10 times higher?). Look at retry metrics, queue length, thread pool use, in-flight requests, and timeouts configured at each layer.

**Mitigate**:
1. **Cut the retries** (config flag or lower retry limits) and **shed load**: return 503 with `Retry-After` early and cheaply, rate-limit, or temporarily block non-critical callers.
2. Scale the failing service **only if** it can actually help (adding pods to a database-bound service does not).
3. If needed, briefly reduce traffic to near zero so the system can recover, then ramp up slowly.
4. Roll back any recent change that started the slowdown.

**Prevent**: retries only at one layer, exponential backoff with jitter, retry budgets, timeouts from latency percentiles, circuit breakers, bounded queues, deadlines passed downstream, graceful degradation, load testing and game days. `[file 09]`

**Say this**: "I stop the amplification first: fewer retries, shed load, then restore capacity gradually."

---

## Scenario 11. A pod keeps getting OOMKilled

**Situation**: A service restarts every few hours; `kubectl describe` shows `Reason: OOMKilled`, exit code 137.

**First steps**: Impact is probably brief per restart; find out if it is leak, spike, or a limit set too low.

**Diagnose**: `[file 04, 03, 01]`
```bash
kubectl describe pod <pod> | grep -A6 "Last State"
kubectl top pod <pod> --containers
# Prometheus: container_memory_working_set_bytes{pod="..."} over 24h
```
Shape of the memory graph: **steady climb** until kill = leak; **jump at start** = limit too low for warm-up; **spikes on certain requests** = unbounded buffering or large payloads; **sawtooth** = garbage collection (check heap settings relative to the limit). Remember the container limit counts page cache of its own files and in-memory `emptyDir` volumes. The node may still have free memory; the limit is per container (cgroup `memory.max`).

**Fix**: short term raise the limit with headroom (or restart schedule as a bandaid, labeled as such). Long term fix the leak (heap profile), cap caches and queues, stream large data, set runtime memory flags below the container limit.

**Prevent**: memory alerts at 80 percent of the limit, load tests with realistic payloads, memory profiling in staging, requests set close to real use (VPA recommendations help).

**Say this**: "The memory graph shape tells me leak, low limit, or spiky requests; I fix the cause and keep headroom, not just a bigger limit."

---

## Scenario 12. `terraform apply` is stuck on a lock, or someone changed production by hand

**Situation A**: CI fails with "Error acquiring the state lock". **Situation B**: `plan` shows unexpected changes (drift) in production.

**First steps (A)**: Read **Who**, **Operation**, and **Created** in the lock info. Is a job really still running? Check CI.

**Diagnose and fix (A)**: `[file 06]`
- If a job is running, wait.
- If the job died, confirm nobody is applying, then `terraform force-unlock <LOCK_ID>`. The docs warn: unlocking someone else's active lock can lead to multiple writers and state corruption.
- Never use `-lock=false` to bypass.

**First steps (B)**: Do not apply blindly. Read the plan: `~` change in place, `-/+` destroy and recreate (danger). Find out who changed what (cloud audit logs).

**Diagnose and fix (B)**: `terraform plan -refresh-only` shows only outside changes. Decide per change: **accept** (update the code to match reality) or **revert** (apply to restore the declared state). Production data resources (databases) need extra care: check `prevent_destroy` and backups before applying a replace.

**Prevent**: remote state with locking and versioning (S3 `use_lockfile`, bucket versioning recommended by the docs), CI-only applies, restrict console write access, nightly drift plan with `-detailed-exitcode`, small states to reduce blast radius, saved plans (`plan -out`, `apply tfplan`) with review.

**Say this**: "Never bypass the lock or apply a plan I have not read; I check who holds the lock and read every replace line."

---

## Scenario 13. A secret was committed to Git or leaked in CI logs

**Situation**: A scanner or a teammate reports an access key in a public or internal repository (or in a build log).

**First steps**: Treat it as compromised. Time matters because bots scrape public repos within minutes.

**Steps**: `[file 11, 07]`
1. **Revoke or rotate first** (disable the key, issue a new one, update where it is used through the secrets manager). Deleting the commit is not enough: it may already be cloned or cached, and it stays in Git history.
2. **Assess use**: check the provider's audit logs for activity with that credential since it was exposed (unknown IPs, new resources, data reads, new keys or users).
3. **Contain**: if misuse is found, revoke sessions, remove created resources or access, widen the investigation, and follow the security incident process (declare, communicate).
4. **Clean up** the repository history only as an extra step (it does not make the secret safe again). For a CI log, delete the log and rotate (GitHub docs advise exactly this).
5. **Root cause**: how did it get there (`.env` committed, hardcoded, printed in debug)? Fix the process.

**Prevent**: no long-lived keys (OIDC and workload identity), secrets manager, pre-commit and CI secret scanning (gitleaks, GitHub secret scanning), masked variables in CI, least privilege so a leaked credential can do little, short expiry.

**Say this**: "Rotate first, then check the audit logs for misuse, then fix how it leaked. History cleaning is not a fix."

---

## Scenario 14. Users get 502 / 504 from the load balancer or ingress

**Situation**: Intermittent 502 Bad Gateway or 504 Gateway Timeout for some requests.

**First steps**: Understand the codes: **502** = the proxy got a bad answer or the connection to the backend failed; **504** = the backend did not answer in time. Which hop returns it: CDN, cloud load balancer, ingress controller, service mesh?

**Diagnose**: `[file 04, 02]`
```bash
kubectl get pods -n prod                      # restarts? NotReady?
kubectl get endpoints web -n prod             # empty or shrinking endpoints?
kubectl logs -n ingress -l app.kubernetes.io/name=<controller> --tail=100    # upstream errors
kubectl describe ingress web -n prod
kubectl rollout status deploy/web -n prod     # a rollout in progress?
```
Common causes:
- **Pods removed while still receiving traffic** (rollout or scale-down): app does not handle SIGTERM, no `preStop` delay, so the load balancer sends requests to a pod that is shutting down. Look for 502s that match deploy times.
- **Readiness probe too lenient or missing**: traffic goes to pods that cannot serve.
- **Backend slower than the proxy timeout** (504): slow dependency or database; compare proxy timeout with p99 latency.
- **Idle timeout mismatch**: the load balancer keeps a connection the app already closed (keep-alive timeout shorter in the app than in the proxy) giving sporadic 502 resets.
- **Backend overloaded**: CPU throttling, thread pool exhausted, queues full.
- Wrong service port or selector after a change (endpoints empty).

**Fix**: roll back a bad change, fix readiness and graceful shutdown, align timeouts (app keep-alive longer than the proxy idle timeout), scale or fix the slow dependency, correct the service config.

**Prevent**: readiness probes, graceful termination, PDBs and surge, timeout budgets documented per hop, dashboards per hop showing status codes and latency.

**Say this**: "502 means a bad or failed backend answer, 504 means no timely answer; I match the errors to deploy times, endpoints, and timeouts."

---

## Scenario 15. A cloud zone (or a major dependency) is down

**Situation**: The cloud provider reports a zone or regional problem, or a third-party API you rely on is down. Error rates rise.

**First steps**: Check the provider status pages and your dashboards. Is the failure confined to one zone or region? What is the user impact now? Declare the incident and assign a communicator (external status updates matter here).

**Diagnose**: Which of your components live in the affected zone? (`kubectl get nodes -L topology.kubernetes.io/zone`, which pods are on those nodes, where the database primary lives, where load balancer backends are.) Are health checks removing bad backends automatically? Do you have capacity left elsewhere?

**Mitigate**:
1. Make sure traffic **leaves the failed zone**: load balancer health checks, remove the zone from backends, cordon nodes in the zone.
2. Add capacity in healthy zones (scale node pools; check quotas, since everyone else is scaling too).
3. **Database failover** if the primary is affected: follow the runbook (promote a replica, switch the endpoint). Know that async replication may lose the last commits (RPO) and avoid two primaries (split brain). `[file 10]`
4. For a **third-party dependency** outage: enable graceful degradation (cached data, queue and retry later, hide the feature), use circuit breakers so you do not hang on it, communicate to customers.
5. Reduce non-essential load and pause risky deploys.

**Prevent**: spread replicas over at least three zones (topology spread constraints), enough spare capacity to lose a zone, tested database failover, multi-region plan matched to the SLO and budget, timeouts, circuit breakers and fallbacks for dependencies, regular game days. Define RPO and RTO per service. `[file 12, 09]`

**Say this**: "Move traffic away from the failed zone, add capacity elsewhere, fail over data carefully, degrade gracefully, and communicate."

---

## Bonus: how to describe your own incident (Behavioral)

Structure (about 2 minutes): **Situation** (what broke, user impact in numbers) -> **Role** (what you owned) -> **Actions** (first check, hypothesis, mitigation) -> **Result** (time to mitigate, what recovered) -> **Learning** (what changed: alert, test, runbook, automation). Prepare two stories: one where you found the cause quickly, and one where you were wrong at first and changed your mind.

## Sources

- Kubernetes docs (debug pods, probes, PDB, resource management, NetworkPolicy): https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/ , https://kubernetes.io/docs/tasks/run-application/configure-pdb/ , https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- Google SRE book, Monitoring Distributed Systems (golden signals, symptoms vs causes): https://sre.google/sre-book/monitoring-distributed-systems/
- Google SRE book, Addressing Cascading Failures (retries, load shedding, deadlines): https://sre.google/sre-book/addressing-cascading-failures/
- Google SRE Workbook, Postmortem Culture: https://sre.google/workbook/postmortem-culture/
- HashiCorp, state locking and `force-unlock`: https://developer.hashicorp.com/terraform/language/state/locking
- PostgreSQL, streaming replication and lag: https://www.postgresql.org/docs/current/warm-standby.html
- GitHub Actions secure use (leaked secrets in logs): https://docs.github.com/en/actions/reference/security/secure-use
- 2026 interview-theme summaries about incident questions (prep sites, indicators only): https://prachub.com/resources/incident-response-interview-questions-for-sre-and-senior-engineers and https://www.kore1.com/sre-interview-questions/

Not verified from a source (general engineering practice, check against your own systems): the specific commands for `cert-manager`, `crictl`, `docker system df`, PostgreSQL `pg_stat_activity`/`pg_locks`/`pg_cancel_backend`; HTTP 502 vs 504 meanings and the keep-alive/idle-timeout mismatch cause; `ndots:5` behavior in Kubernetes DNS; conntrack and NAT port exhaustion causes; node auto-repair; topology spread constraints; the cloud audit-log advice; the exact steps of the failover runbook (your own runbook is the authority). The scenarios are teaching examples, not real events.
