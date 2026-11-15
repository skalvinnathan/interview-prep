# 04. Kubernetes from zero

Legend: `[REAL]` = ran on this Mac on 2026-11-15 (only offline `--dry-run=client` commands; I did not talk to any cluster). `[SAMPLE]` = typical output written to show the shape, names and numbers made up, not run here.

---

## 1. What it is (plain words + analogy)

**Kubernetes (K8s)** is a system that runs containers on many machines and keeps them healthy. You do not say "start this container on that machine". You say **"I want 3 copies of this app running"**, and Kubernetes keeps making it true. If a copy dies, it starts a new one.

Analogy: a **restaurant manager**.
- You give the manager the **menu and the staffing plan** (the YAML files = the *desired state*).
- The manager watches the floor (the *actual state*). If a cook leaves, the manager calls another one. This "watch and fix" loop is called a **control loop** (or reconciliation). It is the one big idea of Kubernetes.

Pieces:
```
 Control plane (the manager's office)               Worker nodes (the kitchens)
 ┌────────────────────────────────────┐             ┌───────────────────────────┐
 │ API server  <- kubectl talks here  │             │ kubelet  (runs the pods)  │
 │ etcd        (database of state)    │ <---------> │ container runtime         │
 │ scheduler   (picks a node per pod) │             │ kube-proxy / CNI (network)│
 │ controllers (the control loops)    │             │  [pod][pod][pod]          │
 └────────────────────────────────────┘             └───────────────────────────┘
```
On AKS (Azure), GKE (Google), and EKS (Amazon) the cloud runs the control plane for you.

Words:
- **Pod**: the smallest unit. One or more containers that share one IP and run together on one node. Pods are **disposable**: when they die they are replaced by *new* pods with *new* IPs.
- **Node**: a worker machine (a VM).
- **Namespace**: a folder to split a cluster into parts (`dev`, `prod`, `team-a`).
- **Label**: a key=value tag on an object (`app=web`). **Selector**: a query on labels.

## 2. Why it matters in interviews

For platform engineering roles (FIS, ScienceLogic, Amazon, Google platform teams), Kubernetes is the main subject. Recent 2026 guides say Kubernetes questions are "scenario-based" (a pod is Pending, a rollout is stuck, a node is NotReady), not trivia, and that they want you to connect user impact to the control loop and workload. You have 3.5 years on AKS, so expect deep follow-up on your own experience. Be ready to run the debug commands from memory.

## 3. How it works, step by step

### 3.1 Pod

A pod is a wrapper around containers. You rarely create bare pods. You create a **Deployment** that creates pods for you.

### 3.2 Deployment -> ReplicaSet -> Pods

```
 Deployment "web"  (desired: 3 replicas, image v2)
     │ owns
     ▼
 ReplicaSet "web-7d9f8" (keeps exactly 3 pods of this template)
     │ owns
     ▼
 Pod web-7d9f8-abcde   Pod web-7d9f8-fghij   Pod web-7d9f8-klmno
```
When you change the pod template (for example the image), the Deployment makes a **new ReplicaSet** and moves pods over slowly. That is a **rolling update**.

`[REAL]` generate YAML without a cluster (`--dry-run=client` does not call any server):
```
$ kubectl create deployment web --image=nginx:1.27 --replicas=2 --dry-run=client -o yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: web
  name: web
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  strategy: {}
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - image: nginx:1.27
        name: nginx
        resources: {}
status: {}
```
Notice: `selector.matchLabels` must match `template.metadata.labels`. That is how the Deployment finds its pods.

### 3.3 Rolling updates

Settings: `maxSurge` (how many extra pods may exist during the update) and `maxUnavailable` (how many may be missing). Both default to 25 percent. `progressDeadlineSeconds` (default 600) is how long Kubernetes waits for progress before marking the rollout failed. `revisionHistoryLimit` (default 10) is how many old ReplicaSets are kept for rollback. (These defaults come from general Kubernetes knowledge; the page I fetched was cut before that section. They are standard and easy to confirm with `kubectl explain deployment.spec.strategy`.)

```
 replicas 4, maxSurge 1, maxUnavailable 0:
 old: [v1][v1][v1][v1]
 step1: create 1 new         -> [v1][v1][v1][v1] + [v2 starting]
 step2: new is Ready         -> remove 1 old: [v1][v1][v1] + [v2]
 step3: repeat ...           -> [v2][v2][v2][v2]
```
A pod counts as ready only when its **readiness probe** passes. A bad new version never becomes ready, so the old pods stay and the rollout **stops** (that is the safety).

Commands:
```bash
kubectl rollout status deployment/web       # watch
kubectl rollout history deployment/web      # list revisions
kubectl rollout undo deployment/web         # go back one revision
kubectl rollout undo deployment/web --to-revision=2
kubectl rollout restart deployment/web      # rolling restart (same image)
```

### 3.4 Service

Pod IPs change. A **Service** gives a **stable IP and DNS name** in front of a set of pods chosen by a label selector, and spreads traffic over the ready ones.

```
 client pod ──> Service "web" (ClusterIP 10.0.5.20, DNS web.default.svc.cluster.local)
                  │ selector: app=web
                  ├──> Pod web-abcde 10.244.1.7   (ready)
                  ├──> Pod web-fghij 10.244.2.4   (ready)
                  └──> Pod web-klmno 10.244.1.9   (NOT ready -> no traffic)
```
Types:
- **ClusterIP** (default): reachable only inside the cluster.
- **NodePort**: also opens a port on every node.
- **LoadBalancer**: asks the cloud for an external load balancer.
- (**ExternalName**: a DNS alias.)

If a Service has **no endpoints**, the label selector matches no *ready* pods. This is the most common "service is down" cause. Check `kubectl get endpoints web` (or `get endpointslices`).

### 3.5 Ingress (and Gateway API)

From the Kubernetes docs: Ingress "manages external access to the services in a cluster, typically HTTP", with routing rules (host, path, backend). **"Only creating an Ingress resource has no effect"**: you also need an **Ingress controller** (nginx, Traefik, a cloud one) that carries it out. Ingress handles only HTTP(S); for other ports use NodePort or LoadBalancer.

Current status (verified): the Kubernetes docs say "The Kubernetes project recommends using Gateway instead of Ingress. The Ingress API has been frozen", and there are no plans to remove Ingress. Also, the project announced the retirement of the community **ingress-nginx** controller: best-effort maintenance only until March 2026, after that no releases, bug fixes, or security updates (Kubernetes blog, Nov 2025, restated Jan 2026). Today is November 2026, so if you use ingress-nginx you should have a migration plan (for example to Gateway API with another controller). Mention this in an interview: it shows you follow the ecosystem.

```
 Internet -> cloud LB -> Ingress controller pods -> (rules) -> Service -> Pods
```

### 3.6 Config: ConfigMap and Secret

- **ConfigMap**: non-secret settings as key/value or files.
- **Secret**: sensitive values. **Warning (from the Kubernetes docs): Secret values "are encoded as base64 strings and are stored unencrypted by default"**, and base64 "provides no additional confidentiality over plain text".

`[REAL]` base64 is not encryption, anyone can reverse it:
```
$ kubectl create secret generic db --from-literal=password=s3cret --dry-run=client -o yaml
apiVersion: v1
data:
  password: czNjcmV0
kind: Secret
metadata:
  name: db
$ echo 'czNjcmV0' | base64 -d
s3cret
```
Good practice (from the docs' Secrets good-practices page): turn on **encryption at rest** for etcd; give **least-privilege RBAC** (note: "Granting list access to Secrets implicitly lets the subject fetch the contents"); remember that anyone who can create a pod that uses a Secret can probably read it; use an **external secret store** (Secrets Store CSI Driver, External Secrets Operator) so the value never lives in Git. Never commit Secret YAML with real values.

Ways a pod uses them: as **environment variables** (read once at start; changing the Secret does not change a running pod) or as **mounted files** (updated eventually in the running pod, but the app must re-read the file).

### 3.7 Probes

The kubelet checks your container with **probes**:

| Probe | Question | If it fails |
|---|---|---|
| **startup** | "Has the app finished starting?" | other probes wait; if it never passes, container restarts |
| **liveness** | "Is the app stuck beyond repair?" | kubelet **kills and restarts** the container |
| **readiness** | "Can it take traffic now?" | pod is **removed from Service endpoints** (no restart) |

Fields: `initialDelaySeconds`, `periodSeconds`, `timeoutSeconds` (default 1 s), `failureThreshold` (default 3), `successThreshold`. HTTP success is "any code greater than or equal to 200 and less than 400".

```yaml
readinessProbe:
  httpGet: { path: /ready, port: 8080 }
  periodSeconds: 5
  failureThreshold: 3
livenessProbe:
  httpGet: { path: /healthz, port: 8080 }
  periodSeconds: 10
  failureThreshold: 3
startupProbe:
  httpGet: { path: /healthz, port: 8080 }
  periodSeconds: 5
  failureThreshold: 30        # up to 150 s to start
```
Common advice (widely repeated, not from one official page): keep liveness cheap and **do not check the database in liveness**. If the database is down, every pod would restart at the same time and make things worse. Put dependency checks in readiness, not liveness. Use a startup probe for slow apps instead of a huge `initialDelaySeconds`.

### 3.8 Requests and limits

- **Request**: what the container is *promised*. The scheduler uses it to pick a node ("the kube-scheduler uses this information to decide which node to place the Pod on"), and the kubelet reserves it.
- **Limit**: the ceiling. CPU over the limit is **throttled**; memory over the limit gets **OOM-killed** (see file 03).
- A container may use more than its request if the node has room. If you set only a limit, Kubernetes copies it as the request.
- Units: CPU `500m` = half a core; memory `256Mi` (mebibytes).

QoS classes (a label that decides who is evicted first when the node runs short):
- **Guaranteed**: every container has CPU and memory limits equal to requests. Evicted last.
- **Burstable**: some requests/limits set, but not Guaranteed.
- **BestEffort**: nothing set. Evicted first.
(From general Kubernetes knowledge; the doc page I fetched was cut before this part. Check the "Pod Quality of Service Classes" page.)

```yaml
resources:
  requests: { cpu: "250m", memory: "256Mi" }
  limits:   { memory: "512Mi" }       # many teams leave CPU limit off; discuss trade-offs
```

### 3.9 HPA (Horizontal Pod Autoscaler)

Adds or removes **pods** based on a metric. The formula from the docs:

`desiredReplicas = ceil( currentReplicas × currentMetricValue / desiredMetricValue )`

Example from the docs: current 200m, target 100m -> replicas double. It ignores changes when the ratio is within a tolerance of 0.1. It runs every 15 seconds by default. For CPU the utilization is **a percent of the pod's CPU *request***: "CPU utilization for the Pod will not be defined and the autoscaler will not take any action" if requests are missing. So: **no requests, no HPA**.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: web }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: web }
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target: { type: Utilization, averageUtilization: 60 }
```
Scale-down is slowed by a stabilization window (commonly 300 s, set via `behavior.scaleDown.stabilizationWindowSeconds`; not verified on the full page). HPA adds pods; if there is no room, the **Cluster Autoscaler** (or Karpenter) adds nodes. Pods stay Pending until the node arrives. VPA changes requests; KEDA scales on events like queue length (general knowledge).

### 3.10 PDB (PodDisruptionBudget)

Limits how many pods of an app may be taken down **on purpose** (a "voluntary disruption": node drain, cluster upgrade) at the same time. Set **one** of `minAvailable` or `maxUnavailable`. It cannot stop **involuntary** disruptions like a node crash (the docs: "The budget can only protect against voluntary evictions").

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: web }
spec:
  maxUnavailable: 1
  selector:
    matchLabels: { app: web }
```
Trap from the docs: with `maxUnavailable: 0` (or `minAvailable` equal to the replica count), "you cannot successfully drain a Node running one of those Pods... the drain never completes". This blocks AKS/GKE upgrades. Also a 1-replica Deployment with a PDB blocks drains.

### 3.11 RBAC

Who can do what in the cluster.
- **Role**: permissions inside one namespace. **ClusterRole**: cluster-wide, or reusable.
- **RoleBinding**: gives a Role (or ClusterRole) to a user, group, or **ServiceAccount** in one namespace. **ClusterRoleBinding**: for the whole cluster.
- "Permissions are purely additive (there are no 'deny' rules)."
- A **ServiceAccount** is the identity a pod uses to call the API.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { namespace: default, name: pod-reader }
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { namespace: default, name: read-pods }
subjects:
- kind: ServiceAccount
  name: my-app
  namespace: default
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```
Check with: `kubectl auth can-i list pods -n default --as=system:serviceaccount:default:my-app`. (The Role YAML is from the Kubernetes RBAC page; the RoleBinding is the standard shape.)

### 3.12 NetworkPolicy

By default every pod can talk to every pod ("By default, a pod is non-isolated for egress/ingress; all connections are allowed"). A **NetworkPolicy** limits that. Once a policy **selects** a pod for a direction, only traffic that some policy allows is permitted. Policies are **additive**. Both ends must agree: the source's egress and the destination's ingress. **Important**: policies are enforced by the network plugin (CNI). "Creating a NetworkPolicy resource without a controller that implements it will have no effect." (Calico, Cilium, Antrea, Kube-router are named in the docs.)

Default deny for ingress in a namespace (shape from the docs):
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-ingress, namespace: default }
spec:
  podSelector: {}
  policyTypes: ["Ingress"]
```
Then add allow policies, for example "only pods labeled `app=web` may reach `app=db` on port 5432".

### 3.13 Debugging cheat sheet (the exact commands)

**Always start here:**
```bash
kubectl get pods -n <ns> -o wide                         # status, restarts, node, IP
kubectl describe pod <pod> -n <ns>                       # read the Events at the bottom!
kubectl get events -n <ns> --sort-by=.lastTimestamp      # recent cluster events
kubectl logs <pod> -n <ns>                               # current logs
kubectl logs <pod> -n <ns> --previous                    # logs of the crashed one
kubectl logs <pod> -n <ns> -c <container>                # a specific container
```
The Kubernetes docs say: "For any pod problem, first check its state and recent events" with `kubectl describe`.

#### A. Pending (the pod is not placed on a node)
Meaning: the scheduler cannot find a node. Run `kubectl describe pod`. Look at Events for a line starting `FailedScheduling`.

`[SAMPLE]`
```
Events:
  Type     Reason            Age   From               Message
  Warning  FailedScheduling  30s   default-scheduler  0/5 nodes are available: 3 Insufficient memory, 2 node(s) had untolerated taint {dedicated: gpu}.
```
Causes and checks:
- **Not enough CPU/memory on nodes** (official docs name this): `kubectl describe nodes | grep -A8 "Allocated resources"`, `kubectl top nodes`. Fix: lower requests, add nodes, check the cluster autoscaler.
- **Taints** without a matching toleration, **nodeSelector/affinity** that matches nothing: compare `kubectl get nodes --show-labels` and `kubectl describe node <n> | grep Taints`.
- **PVC not bound** (storage): `kubectl get pvc -n <ns>`, `kubectl describe pvc <name>`. Check StorageClass, zone mismatch (a disk in zone 1 and a node only in zone 2).
- **hostPort** use (official docs name this).
- **Quota**: `kubectl describe resourcequota -n <ns>`.

#### B. ImagePullBackOff / ErrImagePull
Meaning: the node cannot download the image, and retries with growing waits. The official page says the most common cause of a pod stuck in Waiting is an image pull failure; check the name, check the image was pushed, try pulling manually.

`[SAMPLE]`
```
Events:
  Warning  Failed   12s  kubelet  Failed to pull image "myreg.azurecr.io/web:v9": ... not found
  Warning  Failed   12s  kubelet  Error: ErrImagePull
  Normal   BackOff  10s  kubelet  Back-off pulling image "myreg.azurecr.io/web:v9"
```
Checks: typo in image or tag; tag does not exist; **private registry without credentials** (`imagePullSecrets`, or on AKS the ACR attachment `az aks update --attach-acr`); registry unreachable (network, DNS, firewall); rate limits (Docker Hub). Test: `kubectl run tmp --rm -it --image=<same image> -- sh` or `docker pull` from a machine with the same access. Defaults worth knowing: tag `:latest` or no tag -> `imagePullPolicy: Always`; a digest -> `IfNotPresent`.

#### C. CrashLoopBackOff
Meaning: the container starts, exits, and Kubernetes restarts it with growing delay (10 s, 20 s, 40 s ... up to 5 minutes). It is a **symptom**, not a cause. The cause is why the process exits.

`[SAMPLE]`
```
NAME                   READY   STATUS             RESTARTS      AGE
web-7d9f8-abcde        0/1     CrashLoopBackOff   6 (45s ago)   8m
```
Steps:
1. `kubectl logs <pod> --previous` (the dead container's last words).
2. `kubectl describe pod <pod>`: look at `Last State: Terminated`, `Reason`, `Exit Code`.
   - Exit 1 or other: app error (bad config, missing env var or Secret, cannot reach DB).
   - Exit 137: killed (OOM or too slow to stop). Exit 139: segfault. Exit 143: SIGTERM.
   - `Reason: Error` vs `OOMKilled` vs `Completed` (a container that finishes immediately in a Deployment will crash-loop; use a Job).
3. Liveness probe killing a slow-starting app: look for `Liveness probe failed` in Events. Fix with a startup probe.
4. Wrong `command` or `args`, wrong file permissions, read-only root filesystem with an app that writes.
5. Cannot read logs because it dies too fast? Use `kubectl debug` to copy the pod with a different command, or run the image locally with `docker run`.

#### D. OOMKilled
Meaning: the container used more memory than its **limit**; the kernel killed it (file 01 and 03). How to confirm:
```bash
kubectl describe pod <pod> | grep -A6 "Last State"
kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[*].lastState.terminated}'
```
`[SAMPLE]`
```
    Last State:     Terminated
      Reason:       OOMKilled
      Exit Code:    137
      Started:      Sun, 15 Nov 2026 21:30:02 +0530
      Finished:     Sun, 15 Nov 2026 21:34:19 +0530
```
(The Kubernetes docs page on this topic explains how to read `lastState.terminated`; the reason value `OOMKilled` is set by the kubelet and runtime. Exit code 137 = 128 + 9.)
Next: `kubectl top pod <pod> --containers` (needs metrics-server), look at the memory graph over time (a steady climb = leak; a spike at start = too low a limit; a spike on a big request = unbounded buffering). Fix: raise the limit with headroom, fix the leak, bound caches and queues, set runtime heap flags (JVM `-XX:MaxRAMPercentage`, Go `GOMEMLIMIT`; check your version). Remember: the memory limit includes page cache used by the container's own files, and `tmpfs`/`emptyDir: {medium: Memory}` counts toward the limit.

#### E. Other things to check quickly
```bash
kubectl get endpoints <svc> -n <ns>                  # empty = selector/readiness problem
kubectl get svc,ingress -n <ns>
kubectl exec -it <pod> -n <ns> -- sh                 # look inside
kubectl port-forward svc/<svc> 8080:80 -n <ns>       # test a service from your laptop
kubectl run net --rm -it --image=busybox -- sh       # temp pod: nslookup, wget, nc
kubectl debug -it <pod> --image=busybox --target=<container>   # ephemeral debug container
kubectl get nodes                                    # NotReady?
kubectl describe node <node>                         # Conditions: MemoryPressure, DiskPressure
kubectl auth can-i ...                               # RBAC
kubectl get pod <pod> -o yaml                        # the full truth
kubectl rollout status deploy/<d> ; kubectl rollout undo deploy/<d>
```
`kubectl debug` with ephemeral containers lets you attach a debug container to a running pod even if the image has no shell (one guide says available from 1.23; I did not verify from the official page).

## 4. Commands to try (without a cluster)

```bash
kubectl create deployment web --image=nginx:1.27 --dry-run=client -o yaml
kubectl create secret generic db --from-literal=password=x --dry-run=client -o yaml
kubectl explain deployment.spec.strategy.rollingUpdate        # needs a cluster (reads its API)
# local practice cluster: kind, minikube, or Docker Desktop Kubernetes
```
Careful: some `kubectl` commands, even with `--dry-run=client`, may still try to reach whatever cluster your kubeconfig points to (for example `kubectl create role ...` did that on this Mac and failed with a DNS error to an old cluster). Check `kubectl config current-context` first, and never run mutating commands against production by habit.

## 5. Common mistakes

1. No resource requests (HPA does nothing, scheduler cannot plan, bad QoS).
2. Memory limit equal to normal usage with no headroom, then OOMKilled on a spike.
3. Liveness probe that checks the database, or that is too strict, causing restart storms.
4. No readiness probe, so traffic hits pods that are not ready during a rollout.
5. Using `:latest`, so a rollout may not change anything (or changes unexpectedly).
6. Believing a Secret is encrypted. It is base64, readable by anyone with `get secrets`.
7. A PDB with `maxUnavailable: 0`, blocking node upgrades. Or no PDB at all with 1 replica.
8. Creating a NetworkPolicy on a cluster whose network plugin does not enforce them (no effect).

## 6. Eight interview questions with answers

**Q1. What happens when you run `kubectl apply -f deployment.yaml`?**
kubectl sends the object to the API server, which authenticates, authorizes (RBAC), validates, runs admission, and stores it in etcd. The Deployment controller sees it and creates a ReplicaSet. The ReplicaSet controller creates Pod objects. The scheduler picks a node for each pod. The kubelet on that node tells the container runtime to pull the image and start containers, and runs probes. When the pod is Ready, the endpoints controller adds it to Service endpoints.

**Q2. Pod vs Deployment vs ReplicaSet vs StatefulSet?**
A pod is one or more containers on one node, and is disposable. A ReplicaSet keeps N identical pods running. A Deployment manages ReplicaSets and gives rolling updates and rollback. A StatefulSet is for stateful apps: stable names (`db-0`, `db-1`), stable storage per pod, ordered start and stop.

**Q3. Liveness vs readiness vs startup probes?**
Liveness failing restarts the container. Readiness failing removes the pod from Service endpoints without restart. Startup holds off the other two until the app has started, protecting slow starters. Keep liveness cheap and independent of dependencies; put dependency checks in readiness.

**Q4. Requests vs limits? What happens when a container goes over each?**
Requests are what the scheduler reserves for the pod. Limits are the ceiling. Over the CPU limit: throttled (slowed, not killed). Over the memory limit: OOM-killed (exit 137). Requests also decide QoS class and the base for HPA percentages.

**Q5. How does an HPA decide how many replicas?**
`desired = ceil(current × currentMetric / targetMetric)`, checked about every 15 seconds, ignoring small changes (10 percent tolerance). For CPU, utilization is measured against the pod's CPU request, so requests must be set. Scale-down waits through a stabilization window to avoid flapping. If pods stay Pending after scale-up, the node autoscaler must add nodes.

**Q6. A pod is Pending. How do you debug it?**
`kubectl describe pod`, read the `FailedScheduling` event. Common causes: insufficient CPU/memory on nodes, taints without tolerations, node selector or affinity matching nothing, unbound PVC, quota. Then check `kubectl describe nodes` (allocated resources), `kubectl get pvc`, `kubectl describe resourcequota`, and the cluster autoscaler logs.

**Q7. CrashLoopBackOff: what is it, and what are your first three commands?**
The container keeps exiting and Kubernetes restarts it with increasing backoff (up to 5 minutes). It is a symptom. First: `kubectl logs <pod> --previous`. Second: `kubectl describe pod <pod>` for Last State, exit code, reason, and probe events. Third: `kubectl get events --sort-by=.lastTimestamp`, or check config (env, Secrets, ConfigMaps) the app reads. Exit 137 points to OOM, exit 1 to an app error.

**Q8. How do you do a zero-downtime deployment, and what can break it?**
Rolling update with `maxUnavailable: 0` (or small), `maxSurge: 1+`, a correct readiness probe, a PDB, at least 2 replicas spread over nodes/zones, and graceful shutdown (handle SIGTERM, a `preStop` sleep so the load balancer stops sending traffic first, a long enough `terminationGracePeriodSeconds`). What breaks it: no readiness probe, apps that ignore SIGTERM, database migrations that are not backward-compatible, a single replica, and a PDB that blocks node drains.

## 7. Self-quiz (answers at the end)

1. Which Kubernetes object gives pods a stable IP and DNS name?
2. A Service has no endpoints. Name two reasons.
3. You see exit code 137 and reason `OOMKilled`. Which setting is involved?
4. Why can an HPA based on CPU do nothing even when CPU is at 100 percent?
5. What is the risk of a PDB with `minAvailable` equal to the replica count?

**Answers**
1. A Service.
2. The selector matches no pods (label mismatch), or the matching pods are not Ready (readiness probe failing), or the pods do not exist.
3. The container's memory **limit**.
4. The pods have no CPU **requests**, so utilization is undefined (the docs: the autoscaler "will not take any action"). Also possible: max replicas reached, or the metrics-server is missing.
5. It allows zero voluntary evictions, so `kubectl drain` and cluster upgrades hang forever.

## 8. Sources

- Debug pods (Pending, Waiting, `kubectl describe` first): https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/
- Resource management (requests, limits, throttling, OOM): https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- Probes: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
- HPA: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- PodDisruptionBudget: https://kubernetes.io/docs/tasks/run-application/configure-pdb/
- Deployments: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- NetworkPolicy: https://kubernetes.io/docs/concepts/services-networking/network-policies/
- Ingress (frozen, Gateway recommended): https://kubernetes.io/docs/concepts/services-networking/ingress/
- Ingress NGINX retirement (Nov 2025) https://kubernetes.io/blog/2025/11/11/ingress-Nginx-retirement/ and statement (Jan 2026) https://www.kubernetes.io/blog/2026/01/29/ingress-nginx-statement/ (I saw these two links in search results; I confirmed the March 2026 date from the search summaries of them, not from reading the pages)
- Secrets good practices: https://kubernetes.io/docs/concepts/security/secrets-good-practices/
- RBAC: https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- Reading termination reason and exit code: https://kubernetes.io/docs/tasks/debug/debug-application/determine-reason-pod-failure/
- Container images (pull policy, `:latest`): https://kubernetes.io/docs/concepts/containers/images/
- 2026 interview-topic summaries (prep sites, treat as indicators only): https://prachub.com/resources/kubernetes-interview-questions-for-sre-and-platform-engineers-production-scenarios-not-trivia and https://www.kore1.com/platform-engineer-interview-questions/

Not verified from a source: Deployment defaults (maxSurge/maxUnavailable 25 percent, progressDeadline 600 s, history limit 10); QoS class rules and eviction order; HPA 300 s scale-down window; CrashLoopBackOff delay values (10 s doubling to 5 minutes); exit codes 139 and 143 meaning; the full apply flow in Q1; the AKS `az aks update --attach-acr` command; ephemeral containers from 1.23; the JVM and Go memory flags; StatefulSet behavior. These are standard Kubernetes facts, but I did not read an official page for them today.
