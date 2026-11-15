# 03. Containers and Docker

Legend: `[REAL]` = ran on this Mac on 2026-11-15. `[SAMPLE]` = typical output written to show the shape, numbers made up, not run here.
Note: on this Mac the Docker engine (Colima) was **not running**, so I could not run containers. I only captured `docker run --help`. Everything about running containers is `[SAMPLE]` or taken from the docs.

---

## 1. What it is (plain words + analogy)

A **container** is a normal Linux process that is **fenced in**:
- it sees only its own file system, its own process list, and its own network (this is **namespaces**), and
- it can use only a limited amount of CPU and memory (this is **cgroups**).

It is **not** a small virtual machine. It does not have its own kernel. It shares the host's kernel.

Analogy: an apartment building.
- A **virtual machine** is a separate house with its own walls, pipes, and electricity (heavy).
- A **container** is an apartment: own door and own rooms, but shared pipes and electricity (the kernel). Light and quick to build.
- **Namespaces** = the walls and the door numbers. The tenant sees only their own apartment.
- **cgroups** = the electricity and water meter with a limit.
- An **image** = the moving-in box with all the furniture (files) packed. A **container** = the apartment after you unpacked the box and someone lives in it.

Words:
- **Image**: a read-only package of files (a root filesystem) plus settings (what command to run).
- **Container**: a running (or stopped) instance of an image.
- **Registry**: a server that stores images (Docker Hub, GHCR, ACR, Artifact Registry).
- **OCI**: Open Container Initiative, the standard format for images and runtimes, so Docker, containerd, and Podman agree.
- **Dockerfile**: the recipe to build an image.

## 2. Why it matters in interviews

Kubernetes runs containers, so every Kubernetes question sits on this. Interviewers ask: "How is a container different from a VM?", "What is a cgroup?", "Why did my container get OOMKilled while the node has free memory?", "Why is my service slow when CPU use looks low?" (CPU throttling), "How do you make an image small and safe?", "Why run as non-root?", "Why does PID 1 matter?". For SRE roles like Unikraft (which builds a different kind of lightweight isolation, unikernels), knowing exactly what a container does and does not isolate lets you compare them.

## 3. How it works, step by step

### 3.1 Namespaces: what the process can SEE

A namespace gives a process its own view of one kind of thing:

| Namespace | The container sees its own... |
|---|---|
| pid | process list (its first process is PID 1) |
| net | network devices, IP address, routing table, ports |
| mnt | mounted file systems (its own root `/`) |
| uts | hostname |
| ipc | shared memory and message queues |
| user | user and group IDs (root inside can map to a normal user outside) |
| cgroup | its view of the cgroup tree |

```
 HOST kernel
 ├─ pid ns A: PID 1 = nginx   (host sees it as PID 48211)
 ├─ pid ns B: PID 1 = python  (host sees it as PID 48390)
 └─ ...
```
Important: the host can still see and kill every container process. The container cannot see the host's processes.

### 3.2 cgroups: what the process can USE

The kernel docs define a cgroup as "a mechanism to organize processes hierarchically and distribute system resources" (cgroup v2 admin guide). Files in the cgroup folder are the controls:

| File (cgroup v2) | Meaning (from the kernel docs) |
|---|---|
| `memory.max` | "Memory usage hard limit". When usage reaches it and cannot be reduced, the OOM killer runs inside the group |
| `memory.high` | A throttle limit. Over it, the group is slowed and reclaimed hard, "Going over the high limit never invokes the OOM killer" |
| `memory.events` -> `oom_kill` | counter of processes killed by the OOM killer in this group |
| `cpu.max` | two numbers `$MAX $PERIOD` in microseconds, default `max 100000`. The group may use up to `$MAX` of CPU time in each `$PERIOD` |
| `cpu.stat` -> `nr_throttled`, `throttled_usec` | how many periods were throttled and for how long |

### 3.3 CPU throttling under a quota (the one that surprises people)

A **CPU limit** in Docker or Kubernetes becomes `cpu.max`. Example: `--cpus=0.5` or a Kubernetes limit of `500m` means quota 50000 per period of 100000 microseconds (0.1 s).

```
 One 100 ms period, limit = 0.5 CPU  ->  50 ms of CPU time allowed
 Your app has 4 busy threads on 4 cores:

 time ->   0ms        12.5ms                      100ms
 core1  ██████████▌
 core2  ██████████▌       <- 4 threads x 12.5 ms = 50 ms of CPU used
 core3  ██████████▌          the quota is spent at 12.5 ms
 core4  ██████████▌
                    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ THROTTLED (frozen) until 100 ms
```
The app is **frozen for 87 ms** of every 100 ms, even though average CPU use looks like "only 50% of one core". Result: **latency spikes (especially p99) while CPU graphs look fine**. The Kubernetes docs say it plainly: "cpu limits are enforced by CPU throttling... Containers may not use more CPU than is specified in their cpu limit." A container is **throttled, not killed**, for CPU. For memory, it is **killed** ("memory limits are enforced by the kernel with out of memory (OOM) kills").

How to see it: `cpu.stat` has `nr_throttled` and `throttled_usec`. In Prometheus, cAdvisor exposes `container_cpu_cfs_throttled_periods_total` and `container_cpu_cfs_periods_total`; their ratio is the share of throttled periods. (Metric names are from cAdvisor; I did not re-verify them today.)

`[SAMPLE]` inside a container on Linux with cgroup v2:
```
$ cat /sys/fs/cgroup/cpu.max
50000 100000
$ grep -E 'nr_periods|nr_throttled|throttled_usec' /sys/fs/cgroup/cpu.stat
nr_periods 18342
nr_throttled 9120          <-- about half of the periods were throttled
throttled_usec 411230000
```
Fixes: raise or remove the CPU limit (keep the request), reduce threads, or fix the hot code. Whether to set CPU limits at all is a debated topic: requests decide scheduling and fair share; limits cause throttling. Many teams set memory limits but leave CPU limits off. That is an opinion, not a rule; say "it depends" and explain the trade-off.

Memory is different: a container that goes over `memory.max` is killed (exit code 137, reason `OOMKilled` in Kubernetes). Kubernetes notes that a container "may use more memory than its memory limit, but if it does, it may get killed" (kills happen when the kernel sees memory pressure).

### 3.4 Images and layers

An image is a stack of **read-only layers**. Each Dockerfile instruction that changes files makes a new layer. When you run a container, Docker adds one thin **writable layer** on top.

```
 Dockerfile                          Image layers (read-only)         Container
 FROM python:3.12-slim      ---->   [ base OS + python      ]
 COPY requirements.txt .    ---->   [ requirements.txt      ]
 RUN pip install -r ...     ---->   [ installed packages    ]
 COPY . .                   ---->   [ your code             ]       + [ writable layer ] (lost on delete)
```

- Layers are **cached**. If an instruction and everything before it is unchanged, Docker reuses the layer. So put things that change **rarely first** (dependencies) and things that change **often last** (your code). That is why you copy `requirements.txt` and install **before** copying the rest.
- Layers are shared between images, so pulling a second image that uses the same base is fast.
- Files you delete in a later layer are **still in the earlier layer** (the image stays big). Clean up in the same `RUN`.
- Data written inside a running container is **lost** when the container is removed. Use a **volume** for data that must stay.
- **Tags are mutable** (the tag `v1` can point to a different image tomorrow). A **digest** (`image@sha256:...`) is exact. Docker's best-practice page says to pin to a digest "to fully secure your supply chain integrity".
- Avoid `:latest` in production. Kubernetes docs warn it is "harder to track which version of the image is running and more difficult to roll back properly".

### 3.5 Multi-stage builds

One Dockerfile, several `FROM` lines. Build tools stay in the early stage; only the result is copied to the last stage. Docker's docs call the result "a tiny production image with nothing but the binary inside".

```dockerfile
# ---- stage 1: build (big, has compilers) ----
FROM golang:1.26 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download                 # cached unless go.mod changes
COPY . .
RUN CGO_ENABLED=0 go build -o /out/app ./cmd/app

# ---- stage 2: run (tiny) ----
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/app /app
USER nonroot:nonroot
ENTRYPOINT ["/app"]
```
(The `golang:1.26` tag comes from Docker's own example page. The distroless image name is a common choice; check the current tag before use.)

Benefits: smaller image (faster pull, less to attack), no compilers or secrets left inside, one file to maintain. `docker build --target build .` stops at the named stage (useful for debugging or running tests).

### 3.6 Run as non-root

By default the process in a container is `root` (UID 0) **inside** the container. If an attacker escapes the container, being root makes things worse. Docker's best-practice page: "If a service can run without privileges, use USER to change to a non-root user."

```dockerfile
RUN useradd --system --uid 10001 appuser
USER 10001
```
Tips:
- Use a numeric UID. Kubernetes can then check `runAsNonRoot`.
- In Kubernetes: `securityContext: { runAsNonRoot: true, readOnlyRootFilesystem: true, allowPrivilegeEscalation: false, capabilities: { drop: ["ALL"] } }`. (Common hardening; the Docker flags `--user` and `--read-only` exist, confirmed in `docker run --help`.)
- Ports below 1024 need extra rights; listen on 8080 and map it.
- Remember: a container shares the host kernel, so it is **not** as strong a wall as a VM.

`[REAL]` flags that exist in this Docker (v29.9.3 client):
```
$ docker run --help | grep -E "init|memory |cpus|read-only|user "
      --cpus decimal                     Number of CPUs
      --init                             Run an init inside the container
  -m, --memory bytes                     Memory limit
      --read-only                        Mount the container's root
  -u, --user string                      Username or UID (format:
```

### 3.7 Why PID 1 is special in a container

The first process in the container's pid namespace is PID 1. Two special rules (see file 01):
1. **Signals**: with no handler for a signal, PID 1 ignores it. So an app that does not handle SIGTERM will not stop on `docker stop`; after the timeout Docker sends SIGKILL. Docker's docs say that without an init, "a PID 1 process ignores signals that have no handler".
2. **Zombies**: PID 1 must reap orphaned children. Many apps do not, so zombies pile up.

Fixes:
- `docker run --init` (or `init: true` in Compose) puts a tiny init (`tini`, via `docker-init`) as PID 1. The docs: it "forwards signals and reaps processes".
- Use **exec form** `CMD ["app", "arg"]`, not shell form `CMD app arg`. Shell form starts `/bin/sh -c "app arg"`, so the shell is PID 1 and does not forward signals. Docker's best-practice page recommends the JSON array form for CMD.
- If you use a start script, end it with `exec app ...` so the app replaces the shell.
- In Kubernetes there is no `--init` flag on a pod. Put an init in the image (tini) or use `shareProcessNamespace`, or make sure your app handles signals. Know that this is a known gotcha.

### 3.8 What a container does NOT isolate

- The **kernel** is shared (a kernel bug can affect all containers).
- The **clock** is shared (time namespaces exist but are rarely used).
- Some **/proc and /sys** values show **host** numbers, not container numbers (for example older tools read the host's CPU count and memory). This breaks apps that size thread pools from the host CPU count. Modern runtimes (Java 10+, Go 1.25+) read cgroup limits. (Check your language and version; I did not verify the versions.)

## 4. Commands to try

```bash
# build and run
docker build -t myapp:1.0 .
docker build --target build -t myapp:build .       # stop at a named stage
docker run --rm -it myapp:1.0 sh
docker run --rm --init -m 256m --cpus 0.5 myapp:1.0
docker run --rm --read-only --user 10001 myapp:1.0

# look inside
docker ps                       docker ps -a
docker logs -f <name>           docker exec -it <name> sh
docker inspect <name> | jq '.[0].State'        # OOMKilled true/false, ExitCode
docker stats --no-stream                       # live CPU/mem per container
docker history myapp:1.0                       # layers and sizes
docker image ls                                # sizes
docker top <name>                              # processes of the container
docker diff <name>                             # files changed in the writable layer

# cgroup numbers (inside a Linux container, cgroup v2)
cat /sys/fs/cgroup/memory.max  /sys/fs/cgroup/cpu.max
cat /sys/fs/cgroup/memory.events               # oom_kill counter
grep throttled /sys/fs/cgroup/cpu.stat

# on the host: see the namespaces of a process (Linux)
ls -l /proc/<pid>/ns
lsns                                           # list namespaces
```

`[SAMPLE]` `docker inspect` after an OOM kill (Linux host):
```
$ docker inspect web --format '{{.State.OOMKilled}} {{.State.ExitCode}}'
true 137
```
`[SAMPLE]` `docker history`:
```
IMAGE          CREATED        CREATED BY                                      SIZE
a1b2c3d4e5f6   2 minutes ago  ENTRYPOINT ["/app"]                             0B
<missing>      2 minutes ago  COPY /out/app /app # buildkit                   9.1MB
<missing>      3 weeks ago    (distroless base layers)                        ~2MB
```
`[SAMPLE]` size win of multi-stage: a Go app can drop from about 800 MB (full `golang` image) to about 10-20 MB. The exact numbers depend on your app.

## 5. Common mistakes

1. Thinking a container is a VM (it has no own kernel).
2. Running as root, with a writable root filesystem, with all Linux capabilities.
3. Using `:latest`, or tags instead of digests, so builds are not repeatable.
4. Copying all source before installing dependencies, so the cache is useless on every build.
5. Putting secrets in the image (`COPY .env`, or `ARG` with a password). They stay in layers forever. Use runtime secrets or BuildKit secret mounts.
6. Shell-form `CMD` or a start script without `exec`, so SIGTERM never reaches the app.
7. Setting a CPU limit too low and then seeing p99 latency spikes with "normal" CPU graphs.
8. Storing data in the container filesystem. It disappears with the container.

## 6. Eight interview questions with answers

**Q1. What is a container? How is it different from a VM?**
A container is an ordinary Linux process, isolated by namespaces (what it can see) and limited by cgroups (what it can use). It shares the host kernel. A VM runs a full guest OS on virtual hardware with its own kernel: stronger isolation, heavier, slower to start. Containers are light and quick but share the kernel, so the isolation boundary is weaker.

**Q2. What do namespaces and cgroups do?**
Namespaces give a process its own view of pids, network, mounts, hostname, IPC, and users. Cgroups limit and account resources: CPU, memory, I/O, number of processes. Together with a layered filesystem they make a container.

**Q3. Explain image layers and why instruction order matters in a Dockerfile.**
Each instruction creates a read-only layer, and layers are cached. If a layer and all before it are unchanged, Docker reuses it. Put rarely changing steps (install dependencies) first and often changing steps (copy code) last, so most builds only redo the last layers. Also, deleting a file in a later layer does not shrink the image.

**Q4. What is a multi-stage build and why use it?**
Several `FROM` stages in one Dockerfile. Compile in a big stage, then `COPY --from=` only the result into a small final stage. Smaller image, less attack surface, no build tools or source in production, one Dockerfile.

**Q5. Why should a container not run as root? How do you fix it?**
Root in the container is UID 0, and a container escape would give the attacker strong rights on the host. Use `USER <numeric uid>` in the Dockerfile, and in Kubernetes set `runAsNonRoot`, a read-only root filesystem, drop all capabilities, and disallow privilege escalation. Listen on a high port.

**Q6. What is special about PID 1 in a container?**
The kernel does not apply default signal actions to it, so unhandled SIGTERM is ignored, and it must reap orphaned children. If the app is PID 1 and does neither, `docker stop` takes the full timeout then SIGKILL, and zombies pile up. Use `--init`/tini, exec-form CMD, `exec` in scripts, and handle SIGTERM in the app.

**Q7. My container has a 500m CPU limit. CPU usage graph shows 20%, but latency is bad. Why?**
CPU throttling. The quota is counted per 100 ms period. A multi-threaded app can spend its whole quota in a few milliseconds and then be frozen for the rest of the period. Average CPU hides this. Check `nr_throttled` and `throttled_usec` in `cpu.stat` (or the cAdvisor throttling metrics). Fix: raise or remove the CPU limit (keep a sensible request), reduce thread count, or optimize the code.

**Q8. Container got OOMKilled but the node has lots of free memory. Why?**
The memory limit applies to the container's cgroup, not the node. When the container reaches `memory.max` and cannot reclaim enough, the kernel OOM killer runs inside that cgroup and kills a process (exit code 137). Fix: find the real usage (`kubectl top`, metrics, heap profile), fix leaks, or raise the limit; for JVM and similar runtimes also set the heap size below the container limit.

## 7. Self-quiz (answers at the end)

1. What two Linux features make a container?
2. What exit code do you see when the OOM killer ends a container, and why that number?
3. Why copy `requirements.txt` before the rest of the code?
4. `CMD python app.py` versus `CMD ["python", "app.py"]`: which handles SIGTERM better and why?
5. What does `cpu.max` of `50000 100000` mean?

**Answers**
1. Namespaces (isolated view) and cgroups (resource limits). Plus a layered filesystem.
2. 137 = 128 + 9 (SIGKILL).
3. So the dependency-install layer is cached and only re-runs when the requirements change.
4. The exec (JSON array) form. Shell form makes `/bin/sh` PID 1, which does not forward SIGTERM to Python.
5. The group may use 50,000 microseconds (50 ms) of CPU per 100,000 microsecond (100 ms) period, which is half of one CPU.

## 8. Sources

- Docker docs, multi-stage builds: https://docs.docker.com/build/building/multi-stage/
- Docker docs, build best practices (USER, digest pinning, exec-form CMD, minimal images): https://docs.docker.com/build/building/best-practices/
- Docker docs, `docker run` (`--init`, `--memory`, `--cpus`, `--user`, `--read-only`): https://docs.docker.com/reference/cli/docker/container/run/
- Kernel docs, cgroup v2 (`cpu.max`, `cpu.stat`, `memory.max`, `memory.high`, `memory.events`): https://docs.kernel.org/admin-guide/cgroup-v2.html
- Kubernetes, resource management (CPU throttling, memory OOM kills): https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- Kubernetes, container images (`:latest`, digests): https://kubernetes.io/docs/concepts/containers/images/

Not verified from a source: the list of namespace types; copy-on-write and layer details (general Docker knowledge); cAdvisor metric names; the claim that Java 10+ and Go 1.25+ read cgroup limits; the distroless image tag; the "800 MB to 10-20 MB" size example (illustrative); that many teams skip CPU limits (opinion); the Kubernetes `securityContext` field names (standard API fields, but check the docs for your version); that Docker Desktop/Colima behave the same as native Linux for `/sys/fs/cgroup` paths.
