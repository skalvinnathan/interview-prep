# 05. Helm

Legend: `[REAL]` = ran on this Mac on 2026-11-15 with Helm v4.3.1 (only offline commands: `create`, `lint`, `template`, `--help`; nothing was installed in any cluster). `[SAMPLE]` = typical output written to show the shape, not run here.

Important version note: this Mac has **Helm 4** (v4.3.1). Some flags changed from Helm 3 (see section 3.6). Know both, because many companies still use Helm 3 scripts.

---

## 1. What it is (plain words + analogy)

Kubernetes YAML files are long and repeat a lot (dev, staging, prod are almost the same, but a few numbers differ). **Helm** is a **package manager and template engine** for Kubernetes.

Analogy: a **cake recipe with blanks**.
- The **chart** is the recipe with blanks: "bake for ___ minutes, add ___ sugar".
- **values** are what you write in the blanks for this cake (dev cake, prod cake).
- A **release** is one cake you actually baked from that recipe, with a name, that Helm remembers.
- A **revision** is each time you baked or changed that same cake (revision 1, 2, 3 ...). Helm can go back to an earlier one.

Words:
- **Chart**: a folder of templates plus defaults.
- **Template**: a Kubernetes YAML file with `{{ ... }}` blanks (Go template language).
- **values.yaml**: the default values. You override them with `-f myvalues.yaml` or `--set key=value`.
- **Release**: an installed instance of a chart in a cluster (stored as a Secret in the namespace).
- **Repository / OCI registry**: where charts are published.

## 2. Why it matters in interviews

Your own experience includes Helm on AKS, and umbrella charts (a parent chart that installs many child charts) are on your topic list. Interviewers will ask: how do values override, what does `--atomic` do, how do you roll back, how do you keep secrets out of Git, how do you preview changes (`helm diff`), what are hooks. They also ask the honest question: "when does Helm hurt?" (templating complexity, hidden state, hard-to-read diffs).

## 3. How it works, step by step

### 3.1 Chart structure (verified from Helm docs)

```
mychart/
├── Chart.yaml        # name, version (chart), appVersion (the app), dependencies
├── values.yaml       # default values
├── charts/           # dependency charts (subcharts) land here
├── crds/             # CRDs, plain YAML, NOT templated
└── templates/        # Go-template YAML -> becomes Kubernetes manifests
    ├── deployment.yaml
    ├── service.yaml
    ├── _helpers.tpl  # named template snippets (not rendered by themselves)
    └── NOTES.txt     # text printed after install
```
`version` in `Chart.yaml` is the **chart's** version (SemVer). `appVersion` describes the **application**; "it doesn't affect chart versioning".

`[REAL]` `helm create mychart` made this (Helm 4.3.1):
```
mychart:
Chart.yaml  charts  templates  values.yaml
mychart/templates:
NOTES.txt  _helpers.tpl  deployment.yaml  hpa.yaml  httproute.yaml  ingress.yaml  service.yaml  serviceaccount.yaml  tests
```
(Note `httproute.yaml`: new charts now include a Gateway API route, in line with the Kubernetes move from Ingress to Gateway.)

### 3.2 Render a template (no cluster needed)

`helm template` turns chart + values into plain YAML on your screen. It does not contact a cluster. Use it in CI and to learn.

`[REAL]`
```
$ helm lint mychart
==> Linting mychart
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed

$ helm template demo mychart --set replicaCount=3 | grep -E "^kind:|replicas:|image:"
kind: ServiceAccount
kind: Service
kind: Deployment
  replicas: 3                       <-- our --set value
          image: "nginx:1.16.0"     <-- default from values.yaml / appVersion

$ helm template demo mychart --set replicaCount=3 --set image.tag=1.2.3 | grep "image:"
          image: "nginx:1.2.3"      <-- overridden
```

### 3.3 Values: who wins?

Order, from weakest to strongest (Helm docs, standard behavior):
1. The chart's `values.yaml`
2. A parent chart's values (for a subchart)
3. Files given with `-f` (later `-f` files win over earlier ones)
4. `--set` / `--set-string` / `--set-file` (win over files)

```
 values.yaml (defaults)  <  -f base.yaml  <  -f prod.yaml  <  --set replicaCount=5
```
Template snippet:
```yaml
replicas: {{ .Values.replicaCount }}
image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
```
Tip: **keep one `values-<env>.yaml` per environment in Git** and do not scatter `--set` in scripts. `--set` is invisible in review.

### 3.4 Umbrella charts and subcharts

An **umbrella chart** is a parent chart that depends on child charts (subcharts). You list them in `Chart.yaml`:

```yaml
dependencies:
  - name: mysql
    version: 3.2.1
    repository: https://another.example.com/charts
```
`helm dependency update` (short: `helm dep up`) downloads them into `charts/`.

Values rules (verified):
- A parent sets a subchart's values under a key equal to the **subchart name**:
  ```yaml
  mysql:
    password: "secret"      # parent reads .Values.mysql.password; the subchart sees .Values.password
  ```
- "Values are namespaced, but namespaces are pruned": the subchart cannot see the parent's values.
- `global:` values are passed to **every** chart in the tree and read as `.Values.global.<key>`. They flow downward only. If both define the same global, the parent wins.
- Fields `condition`, `tags`, and `alias` let you switch subcharts on or off or install one twice.

```
 platform (umbrella)
 ├── values.yaml           global: {env: prod, domain: x.example.com}
 │                         api:    {replicaCount: 3}
 ├── charts/api            sees .Values.replicaCount = 3 and .Values.global.env = prod
 ├── charts/worker
 └── charts/frontend
```
Trade-offs to say out loud: umbrella charts give **one release, one version, one rollback** for the whole stack (good for a platform bundle that ships as one numbered version). The cost: one bad subchart fails the whole release, upgrades are all-or-nothing, and values files get large. Alternatives: one release per service, with a GitOps tool such as Argo CD or Flux ordering them.

### 3.5 The release lifecycle

```
helm install  myrel ./chart -f values.yaml     -> revision 1
helm upgrade  myrel ./chart -f values.yaml     -> revision 2
helm upgrade  myrel ./chart -f values.yaml     -> revision 3 (bad!)
helm rollback myrel 2                          -> revision 4 (same content as 2)
helm uninstall myrel
```
A rollback does **not** erase history: it creates a **new revision** with the old content (standard Helm behavior; I could not open the rollback docs page today, it returned 404, so treat the detail as general knowledge). `helm history myrel` lists the revisions. Helm keeps up to `--history-max` revisions per release (default **10**, `0` = unlimited, from `helm upgrade --help`).

Idempotent deploy command used in CI:
```bash
helm upgrade --install myrel ./chart -n myns --create-namespace -f values-prod.yaml --wait --timeout 10m --rollback-on-failure
```
`--install`: "if a release by this name doesn't already exist, run an install".

### 3.6 `--wait`, `--timeout`, and atomic (Helm 3 vs Helm 4)

- `--wait`: do not say success until the resources are ready, "up to --timeout". Without it, Helm returns as soon as the objects are *created*, not when pods are healthy.
- `--timeout`: here, "time to wait for any individual Kubernetes operation (like Jobs for hooks)" (default **5m0s**).
- **Helm 3**: `--atomic` = wait, and if the upgrade fails, **automatically roll back** (for `install`, uninstall). It implies `--wait`.
- **Helm 4**: `--atomic` was **renamed** `--rollback-on-failure` (`--force` became `--force-replace`). Helm's overview lists the renames, and says the old names still work with a deprecation warning (that sentence came from a search summary, not read on the Helm page itself). The `helm upgrade --help` of Helm 4.3.1 on this Mac shows only the new name:

`[REAL]`
```
$ helm upgrade --help | grep -E "rollback-on-failure|--wait |--timeout|--install"
  -i, --install                        if a release by this name doesn't already exist, run an install
      --rollback-on-failure            if set, Helm will rollback the upgrade to previous success release upon failure. The --wait flag will ...
      --timeout duration               time to wait for any individual Kubernetes operation (like Jobs for hooks) (default 5m0s)
      --wait WaitStrategy[=watcher]    wait until resources are ready (up to --timeout). Use '--wait' alone for 'watcher' strategy ...
```
Also in Helm 4: `--wait` has strategies, and a "watcher" strategy is the default when you set rollback-on-failure; **server-side apply** is the default for **new** installs (older releases keep their previous apply method). (From a Helm 4 migration summary; confirm in the Helm docs before relying on it.)

Pros and cons of automatic rollback: it protects the cluster from a half-broken release, but it **hides the failure reason** if you do not capture events and logs, and it can roll back a database-migration hook's effect only if your migration is reversible. Always print `kubectl get events` and pod logs on failure in CI.

### 3.7 Values merging on upgrade: `--reuse-values` vs `--reset-values`

- `--reuse-values`: "reuse the last release's values and merge in any overrides from the command line".
- `--reset-values`: "reset the values to the ones built into the chart".
- Helm 4 also has `--reset-then-reuse-values` (seen in the local help): reset to chart defaults, then apply the last release's values, then your overrides.

Trap: `--reuse-values` ignores **new defaults** added to `values.yaml` in the new chart version, so new keys can be missing. Safest habit: pass the **full values files** every time (GitOps style) and avoid `--reuse-values`.

### 3.8 `helm diff` (preview before you apply)

`helm diff` is a **plugin**. It "generates a diff between the latest deployed version of a release" and what the chart would produce now.

```bash
helm plugin install https://github.com/databus23/helm-diff     # Helm 3.18+ required per the project
helm diff upgrade myrel ./chart -f values-prod.yaml            # what would change?
helm diff upgrade myrel ./chart -f values-prod.yaml --install  # also for a release that does not exist yet
helm diff upgrade myrel ./chart -f values-prod.yaml --detailed-exitcode   # exit code 2 when changes exist -> good for CI gates
helm diff revision myrel 3 4                                   # compare two revisions
helm diff rollback myrel 2                                     # what a rollback would change
```
Helm 4 note from the plugin page: Helm 4 verifies plugin provenance by default and "git repo URLs do not support provenance verification", so Helm 4 users should install from a release tarball URL after importing the maintainer's public key. (Details on that page.) On this Mac `helm plugin list` is empty, so I did not run a diff.

`[SAMPLE]` diff output shape (the `-`/`+` lines):
```
default, web, Deployment (apps) has changed:
  spec:
    replicas: 2
-   image: web:1.4.0
+   image: web:1.5.0
```
In CI the usual flow is: `helm lint` -> `helm template | kubeconform` (validate against schemas) -> `helm diff` (post as a PR comment) -> `helm upgrade --install --wait --rollback-on-failure`.

### 3.9 Hooks

A **hook** is a resource (often a Job) that Helm runs at a point in the lifecycle. Mark it with `helm.sh/hook`:
- `pre-install`, `post-install`, `pre-upgrade`, `post-upgrade`, `pre-delete`, `post-delete`, `pre-rollback`, `post-rollback`, `test` (runs with `helm test`).
- `helm.sh/hook-weight`: order (lowest runs first).
- `helm.sh/hook-delete-policy`: `before-hook-creation` (default), `hook-succeeded`, `hook-failed`.
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ .Release.Name }}-db-migrate
  annotations:
    "helm.sh/hook": pre-upgrade
    "helm.sh/hook-weight": "0"
    "helm.sh/hook-delete-policy": before-hook-creation
```
Hooks are **not part of the release's tracked resources**, so `helm uninstall` and `rollback` do not manage them like normal objects. A failing hook fails the release. A migration in a `pre-upgrade` hook runs **before** the new pods, so the migration must work with the old code too (backward compatible).

### 3.10 Secrets with Helm

Rule: **never put plain secrets in `values.yaml` in Git**. Also remember a release record (a Secret in the cluster, `sh.helm.release.v1...`) stores the **rendered values and manifests**, so anyone who can read Secrets in that namespace can read your values. Options (general practice, I did not verify each tool's docs today):
1. **External secret store + operator**: chart creates an `ExternalSecret` (External Secrets Operator) or uses the Secrets Store CSI driver; the real value stays in Key Vault / Secret Manager / Vault. Best option for most teams.
2. **Encrypted values in Git**: SOPS with `helm-secrets` plugin, or Sealed Secrets (encrypted in Git, decrypted only in-cluster).
3. **Inject at deploy time** from the CI secret store: `--set-file` or `--set` from a masked variable (risky: the value ends up in the release record, and in shell history if typed).
4. **Workload identity** (no secret at all): pods get cloud access through federation (AKS Workload Identity; see file 11).

## 4. Commands to try

```bash
helm create mychart                       # sample chart
helm lint ./mychart
helm template demo ./mychart -f values.yaml            # render locally
helm template demo ./mychart --set image.tag=1.2.3 | less
helm install demo ./mychart --dry-run=client           # (Helm 4 syntax; Helm 3: --dry-run)
helm upgrade --install demo ./mychart -n dev --create-namespace --wait --timeout 5m
helm list -A                              # all releases in all namespaces
helm status demo -n dev
helm history demo -n dev
helm get values demo -n dev               # user-supplied values
helm get values demo -n dev --all         # merged with defaults
helm get manifest demo -n dev             # YAML as applied
helm rollback demo 1 -n dev
helm uninstall demo -n dev
helm dependency update ./umbrella
helm package ./mychart                    # make a .tgz
helm show values bitnami/postgresql       # defaults of a published chart (after helm repo add)
```
`[SAMPLE]` `helm history`:
```
REVISION  UPDATED                   STATUS      CHART        APP VERSION  DESCRIPTION
1         Sun Nov 15 20:00:01 2026  superseded  web-0.1.0    1.4.0        Install complete
2         Sun Nov 15 20:30:12 2026  superseded  web-0.1.0    1.5.0        Upgrade complete
3         Sun Nov 15 21:00:40 2026  failed      web-0.2.0    1.6.0        Upgrade "web" failed: context deadline exceeded
4         Sun Nov 15 21:05:00 2026  deployed    web-0.1.0    1.5.0        Rollback to 2
```

## 5. Common mistakes

1. Secrets in `values.yaml` or `--set` on the command line.
2. Using `--reuse-values` and then missing new default keys.
3. Not using `--wait`, so CI says "success" while pods crash.
4. Using `helm upgrade` without `--install` in a script that must work on a fresh cluster.
5. Using `--atomic` and losing the error evidence (no logs saved).
6. Putting CRDs in `templates/` (they cannot be upgraded or deleted safely that way); `crds/` installs them but Helm does not upgrade them (known limitation, general knowledge).
7. Not pinning chart versions of dependencies (`~1.2.0` or none), so a rebuild pulls different code.
8. Huge `{{ if }}` logic nobody can read. If a chart is mostly templating, consider Kustomize or simpler charts.

## 6. Eight interview questions with answers

**Q1. What is Helm and why use it instead of plain YAML?**
Helm packages Kubernetes manifests as a chart with templates and default values. One chart serves many environments by changing values. It tracks each install as a release with revisions, so you can upgrade and roll back as one unit. It also gives dependency management (subcharts) and hooks.

**Q2. How do values override each other?**
Chart `values.yaml` is weakest, then a parent chart's values for a subchart, then `-f` files in order (later wins), then `--set` flags (strongest). A parent sets subchart values under the subchart's name; `global:` values reach all charts.

**Q3. What is an umbrella chart, and what are its pros and cons?**
A parent chart whose job is to depend on several subcharts, deployed as one release. Pros: one version, one command, one rollback, shared `global` values. Cons: all-or-nothing upgrades, one failure blocks all, big values files, subchart coupling. Good for a platform bundle; for independent services, separate releases (often via GitOps) can be better.

**Q4. What does `--atomic` do? What changed in Helm 4?**
In Helm 3, `--atomic` waits for readiness and, if the upgrade fails or times out, rolls back automatically (and for install it removes the release); it implies `--wait`. In Helm 4 it is renamed `--rollback-on-failure`. Caveat: always keep logs and events, since the failed state is gone after rollback.

**Q5. How do you roll back, and what happens to revision numbers?**
`helm history <rel>` to find a good revision, then `helm rollback <rel> <revision>`. Helm creates a new revision with the old content (history is kept, up to `--history-max`, default 10). Rollback only reverts Kubernetes objects Helm manages; it does not undo database changes or manual edits.

**Q6. How do you see what an upgrade will change before running it?**
`helm template` to render, and the `helm diff upgrade` plugin to compare against the deployed release (`--detailed-exitcode` for CI gates). Also `helm lint` and schema validation. Post the diff on the pull request so reviewers see the real impact.

**Q7. How do you handle secrets in Helm charts?**
Not in plain values in Git. Use an external secret store with External Secrets Operator or CSI driver, or encrypt in Git (SOPS/helm-secrets, Sealed Secrets), or use workload identity so no secret exists. Remember that release records in the cluster contain rendered values, so lock down RBAC for Secrets.

**Q8. What are Helm hooks, and what is a risk of using them?**
Annotated resources (usually Jobs) that run at lifecycle points (pre-install, pre-upgrade, post-upgrade, pre-rollback, test, and so on), ordered by weight, cleaned by delete policy. Risks: they are not tracked like normal resources, a failing hook fails the release, and a pre-upgrade migration runs while old pods still serve traffic, so it must be backward compatible and idempotent.

## 7. Self-quiz (answers at the end)

1. Which command renders YAML locally without a cluster?
2. In Helm 4, what is the new name of `--atomic`?
3. How does a parent chart set a value inside subchart `mysql`?
4. After `helm rollback web 2` from revision 3, which revision number is created?
5. Why is `--reuse-values` risky?

**Answers**
1. `helm template`.
2. `--rollback-on-failure`.
3. Under a key named after the subchart: `mysql: { password: ... }`.
4. Revision 4 (a new revision with revision 2's content).
5. It reuses the old release's values and so ignores new defaults introduced by the new chart version; missing keys can break templates.

## 8. Sources

- Helm, chart structure, dependencies, values scoping, globals: https://helm.sh/docs/topics/charts/
- Helm, hooks: https://helm.sh/docs/topics/charts_hooks/
- Helm, `helm upgrade` reference (`--rollback-on-failure`, `--wait`, `--timeout`, `--reuse-values`, `--history-max`): https://helm.sh/docs/helm/helm_upgrade/
- helm-diff plugin: https://github.com/databus23/helm-diff
- Helm 4 overview (renamed flags, per search summary): https://helm.sh/docs/overview
- Local: `helm upgrade --help`, `helm install --help` on Helm v4.3.1, captured 2026-11-15
- Kubernetes Secrets good practices (for the secrets section): https://kubernetes.io/docs/concepts/security/secrets-good-practices/

Not verified from a source: Helm 3 `--atomic` exact behavior (known behavior; Helm 4 help text confirms the renamed flag); old flag names still working in Helm 4; server-side apply default in Helm 4 (secondary summary only); rollback creating a new revision (the Helm rollback page returned 404); values precedence list (standard Helm behavior, I did not re-read the page); `helm install --dry-run=client` syntax; the `crds/` upgrade limitation; SOPS, helm-secrets, Sealed Secrets, External Secrets Operator specifics; hooks not being tracked by rollback/uninstall; kubeconform usage.
