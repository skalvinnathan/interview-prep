# 06. Terraform

Legend: `[SAMPLE]` = typical output written to show the shape, names and numbers made up. **Terraform is not installed on this Mac**, so I captured no real Terraform output. Everything shown as output is `[SAMPLE]`. Facts about locking, backends, import, and workspaces were checked against HashiCorp's docs (links at the end).

---

## 1. What it is (plain words + analogy)

**Terraform** lets you describe cloud things (networks, clusters, databases, DNS records) in text files, and then **creates, changes, or deletes** the real things to match the text. This is called **Infrastructure as Code (IaC)**. The language is **HCL** (HashiCorp Configuration Language). You say **what you want**, not the steps. Terraform works out the steps. This is **declarative**.

Analogy: a **building plan and a site manager**.
- Your `.tf` files are the **plan**: "3 rooms, 1 door".
- The cloud is the **real building**.
- Terraform's **state file** is the manager's **notebook**: "room 1 is cloud object id abc123".
- `terraform plan` = the manager walks the site, compares plan vs building, and writes a to-do list. It changes nothing.
- `terraform apply` = the manager does the to-do list.

Words:
- **Provider**: a plugin that talks to one platform (azurerm, google, aws, kubernetes, helm).
- **Resource**: one real thing (`azurerm_resource_group`, `google_storage_bucket`).
- **Data source**: read-only lookup of something that already exists.
- **Variable / output**: input and output of a module or config.
- **Module**: a folder of Terraform code you call like a function.
- **State**: Terraform's record of what it manages.

(Note: Terraform now belongs to IBM since it bought HashiCorp, and the open-source fork **OpenTofu** exists with nearly the same commands. This is general knowledge; I did not verify the current license or version details.)

## 2. Why it matters in interviews

Recent 2026 prep guides say Terraform questions commonly cover **state management, module structure, remote backends, and drift detection**. Interviewers also love failure stories: "two people applied at once", "someone changed a resource in the console", "state file has a secret in it", "how do you import something that already exists". Your CI/CD and Helm experience connect here: pipelines run `plan` on pull requests and `apply` after merge.

## 3. How it works, step by step

### 3.1 The core loop

```
 write .tf files
       │
 terraform init      download providers/modules, set up the backend
       │
 terraform validate  syntax and internal consistency check (no cloud calls)
 terraform fmt       format code
       │
 terraform plan      1) read state  2) refresh (ask the cloud what exists)  3) compare with config  4) show diff
       │
 terraform apply     do the diff, update the state
       │
 terraform destroy   delete everything this config manages (careful!)
```

Tiny example:
```hcl
terraform {
  required_version = ">= 1.9"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 6.0" }
  }
}

variable "bucket_name" { type = string }

resource "google_storage_bucket" "logs" {
  name     = var.bucket_name
  location = "ASIA-SOUTH1"
  uniform_bucket_level_access = true
}

output "bucket_url" { value = google_storage_bucket.logs.url }
```
(Version numbers are examples. Pin versions in real code.)

`[SAMPLE]` `terraform plan`:
```
Terraform will perform the following actions:

  # google_storage_bucket.logs will be created
  + resource "google_storage_bucket" "logs" {
      + name     = "demo-logs-12345"
      + location = "ASIA-SOUTH1"
      ...
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```
Symbols: `+` create, `-` destroy, `~` change in place, `-/+` **destroy and recreate** (watch for this one: data loss risk).

Best practice for CI: `terraform plan -out=tfplan` on the pull request, review it, then `terraform apply tfplan` applies **exactly** that reviewed plan (not a new one). (General practice; standard flags.)

### 3.2 State: what it is and why it is dangerous

The state file (`terraform.tfstate`, JSON) maps each resource in your code to the real object id, and stores all its attributes. Terraform needs it to know what it owns and what to change.

Important facts:
- **State can contain secrets** in plain text (database passwords, keys) because attributes are stored. Protect and encrypt the state, limit who can read it, and never commit it to Git. (Well-known; the S3 backend page offers encryption options such as `encrypt`, `kms_key_id`, and customer-provided keys, which shows why.)
- Losing the state means Terraform forgets what it created. It would try to create everything again, or you must re-import.
- Never edit state by hand. Use `terraform state` commands.

### 3.3 Remote backends and locking

By default state is a local file. That does not work for a team. A **backend** stores state remotely (S3, Azure Blob Storage, GCS, Terraform Cloud). Good backends give you:
1. **Shared state** for the team and CI.
2. **Locking**: while one run could write state, others must wait.
3. **Versioning / history** for recovery.
4. **Encryption**.

Locking facts (HashiCorp docs):
- "Terraform will lock your state for all operations that could write state." It is automatic. If locking fails, Terraform stops.
- Not every backend supports locking; check yours.
- You can turn it off with `-lock=false`, but the docs advise against it.
- If a run dies and leaves a lock, use `terraform force-unlock <LOCK_ID>`. The docs warn to use it only for **your own** lock when automatic unlock failed, because unlocking someone else's active lock "can lead to multiple writers and state corruption". The lock ID is printed in the error.

```
 CI job A: plan/apply ──[takes lock]── writing state ──[releases lock]
 CI job B:   starts ------ "Error acquiring the state lock" (waits or fails)
```

S3 backend specifics (current doc):
- Locking is **opt-in**: `use_lockfile = true` makes Terraform write a `<key>.tflock` object next to the state (native S3 locking). The IAM policy must allow get/put/delete on that lock object.
- The older **DynamoDB** locking (`dynamodb_table`) is marked **Deprecated**, and "will be removed in a future minor version". Both can be set together while migrating.
- S3 **bucket versioning** is "highly recommended" so you can recover from deletion or mistakes.
```hcl
terraform {
  backend "s3" {
    bucket       = "my-tf-state"
    key          = "platform/prod/terraform.tfstate"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true
  }
}
```
(Azure Blob and GCS backends also lock; check their pages. I did not fetch those today.) Backend blocks cannot use variables, so people pass settings with `terraform init -backend-config=...`.

### 3.4 Modules

A **module** is a folder with `.tf` files. The root config calls it with inputs:
```hcl
module "network" {
  source  = "./modules/network"       # or a registry/Git address
  version = "1.2.0"                   # only for registry modules
  cidr    = "10.10.0.0/16"
}
# use: module.network.vpc_id
```
Good habits: small modules with a clear purpose, inputs with types and descriptions, outputs for what callers need, **pin versions**, no hidden provider config inside modules (pass providers in), keep examples and tests. Avoid "one giant module that creates everything" and avoid wrappers around a single resource that add nothing.

### 3.5 Drift

**Drift** = the real world no longer matches the state/config, usually because someone changed something by hand (console, CLI, another tool). How to find it:
- `terraform plan` shows differences, because plan refreshes real values first.
- `terraform plan -refresh-only` shows only what changed outside Terraform, and `terraform apply -refresh-only` updates the state to match reality without changing infrastructure. (Standard flags; not re-checked today.)
- Run a **scheduled plan** in CI (nightly) and alert if the plan is not empty. Use `-detailed-exitcode` (exit code 2 = changes pending) for the check.

Fix choices: change the code to match reality (keep their change), or run apply to put reality back to the code. Then reduce the cause: restrict console write access, use policy.

### 3.6 Import

**Import** brings an existing real resource under Terraform control (so you do not have to delete and recreate it).

Modern way (config-driven, Terraform 1.5+; the HashiCorp page describes `import` blocks):
```hcl
import {
  to = google_storage_bucket.logs
  id = "demo-logs-12345"
}
```
Then:
- Write the matching `resource` block yourself, **or** run `terraform plan -generate-config-out=generated.tf` and let Terraform write a starting `resource` block for you (review it before using it).
- Run `terraform plan` to check it shows no unwanted changes, then `terraform apply` to import.
The older way is the CLI command `terraform import ADDRESS ID`, which only updates the state (you must write the code yourself). Import does **not** write code in that older form. (The CLI page was not part of my fetch, so this comparison is general knowledge.)

Related: `terraform state mv` and `moved { from = ... to = ... }` blocks rename or move resources without destroying them; `terraform state rm` makes Terraform forget a resource without deleting it (`removed` blocks exist too; general knowledge).

### 3.7 Workspaces vs separate directories

**CLI workspaces** are "separate instances of state data within the same Terraform working directory". Every directory starts with a workspace called `default`. Commands: `terraform workspace new dev`, `list`, `select`.

HashiCorp's guidance (verified): workspaces are good for a quick parallel copy of infra to test a change (for example per feature branch). They are **not** suitable to separate stages like dev/staging/prod or different teams, especially if they need **different credentials and access controls**, because CLI workspaces share one backend and "are not a suitable isolation mechanism for this scenario". HashiCorp recommends **separate configurations, each with its own backend**, built on shared reusable modules.

```
 Directory layout (recommended for real environments)
 infra/
 ├── modules/            # shared, versioned building blocks
 │   ├── network/
 │   └── cluster/
 ├── envs/
 │   ├── dev/    main.tf  backend.tf  (own state, own cloud account/credentials)
 │   ├── stage/  main.tf  backend.tf
 │   └── prod/   main.tf  backend.tf
```
Pros of directories: separate state files and credentials, a smaller blast radius, easy to see per-environment differences in code review. Cons: some repetition (reduce with modules, or a wrapper tool such as Terragrunt; general knowledge).

### 3.8 Other things interviewers ask

- **`count` vs `for_each`**: `count` indexes by number (removing item 0 shifts all others, causing recreation); `for_each` keys by name (stable). Prefer `for_each` for sets of resources.
- **`depends_on`, implicit dependencies**: Terraform builds a graph from references. Use `depends_on` only when a dependency is hidden.
- **`lifecycle`**: `prevent_destroy`, `create_before_destroy`, `ignore_changes`.
- **Secrets**: do not put secrets in `.tf` or `tfvars` in Git. Use a secret manager data source or environment variables (`TF_VAR_x`), and mark variables `sensitive = true` (this hides them in output but **not** in state).
- **Provider auth in CI**: use OIDC federation, no stored keys (see file 07).
- **Policy/security scans in CI**: `terraform validate`, `tflint`, Trivy config scan (it scans Terraform misconfigurations per its docs), and a manual approval gate before `apply` to prod.
- **Blast radius**: split state by team/service/environment so one mistake or lock does not block everyone.

## 4. Commands to try

```bash
terraform version
terraform init                          # providers, modules, backend
terraform init -backend-config=backend-dev.hcl
terraform validate
terraform fmt -recursive
terraform plan -out=tfplan
terraform show tfplan                   # read the saved plan
terraform apply tfplan
terraform plan -refresh-only            # drift check
terraform plan -detailed-exitcode       # 0 = no change, 1 = error, 2 = changes
terraform state list                    # what is in state
terraform state show google_storage_bucket.logs
terraform state mv A B
terraform force-unlock <LOCK_ID>        # last resort
terraform workspace list
terraform output
terraform graph | dot -Tpng > g.png     # dependency graph (needs graphviz)
terraform destroy                       # dangerous, always read the plan
```
`[SAMPLE]` a lock error:
```
Error: Error acquiring the state lock

Error message: ... state blob is already locked
Lock Info:
  ID:        6a5c2b1e-1111-2222-3333-444455556666
  Path:      tfstate/prod.tfstate
  Operation: OperationTypeApply
  Who:       ci-runner@build-17
  Created:   2026-11-15 15:41:07 UTC
```
(Look at **Who** and **Created**. If the job really died, then `terraform force-unlock 6a5c...`.)

## 5. Common mistakes

1. Local state on a laptop, or state in Git.
2. No locking, or `-lock=false` "to make it work".
3. One huge state for everything (slow plans, big blast radius, lock contention).
4. Using workspaces to separate dev/stage/prod with the same credentials.
5. Not reading `-/+` (replace) lines in a plan, and destroying a database.
6. Running `apply` without a saved plan, so what you apply differs from what was reviewed.
7. Secrets in code or `tfvars` committed to Git, or assuming `sensitive = true` protects state.
8. Unpinned provider and module versions, so a new provider release changes the plan.

## 6. Eight interview questions with answers

**Q1. What is Terraform state and why does it matter?**
State is Terraform's record that maps your resource blocks to real object IDs and attributes. Terraform uses it to compute what to create, change, or delete. If it is lost or corrupted, Terraform can try to recreate existing things. It can hold secrets, so store it remotely, encrypted, with limited access and versioning.

**Q2. How do remote backends and locking work? What happens if two people apply at once?**
A remote backend (S3, Azure Blob, GCS, and others) stores shared state. For operations that could write state, Terraform takes a lock first, so the second run waits or fails with "Error acquiring the state lock". On S3, use `use_lockfile = true` (DynamoDB locking is deprecated). If a crashed run leaves a stale lock, check who holds it and use `terraform force-unlock <ID>` only when sure nobody is running.

**Q3. Explain plan vs apply, and how you use them in CI.**
`plan` computes the difference between config, state, and real infrastructure and changes nothing. `apply` executes it. In CI: run `plan -out=tfplan` on pull requests and post it for review; after merge and approval run `apply tfplan` so exactly the reviewed plan is applied. Use `-detailed-exitcode` for checks.

**Q4. What is drift and how do you detect and handle it?**
Drift is real infrastructure changed outside Terraform. A plain `plan` shows it, `plan -refresh-only` shows only outside changes, and a nightly scheduled plan can alert on non-empty results. Handle it by either updating code to accept the change or applying to restore the declared state. Prevent it with restricted console access and policies.

**Q5. How do you bring an existing resource under Terraform?**
Add an `import` block (`to = address`, `id = real id`) plus a `resource` block (or generate one with `terraform plan -generate-config-out`), review the plan for unwanted changes, then apply. The older CLI `terraform import` only updates state and you write the code yourself. Move or rename with `moved` blocks or `terraform state mv`.

**Q6. Workspaces or separate directories for environments?**
Separate directories (or separate root configs) with their own backends and credentials, sharing modules. HashiCorp says CLI workspaces share one backend and are not a suitable isolation mechanism for different stages or teams with different credentials. Workspaces are fine for temporary copies, like a branch preview.

**Q7. How do you structure modules?**
Small, focused modules with typed and documented inputs, clear outputs, pinned versions, and no hardcoded environment details. Root configs per environment call the modules. Keep provider configuration in the root. Test modules (for example with `terraform validate`, `plan` on examples, or Terratest).

**Q8. A `terraform apply` failed halfway. What state are we in, and what do you do?**
Terraform saves state after each resource finishes, so resources created before the error are in state, and the failed one may be partially created. Read the error, fix the cause (permission, quota, name conflict), and run `plan` again. It will show what remains. If a resource was created but missing from state, import it. Do not delete state to "start clean".

## 7. Self-quiz (answers at the end)

1. What do the symbols `+`, `~`, and `-/+` mean in a plan?
2. Which S3 backend setting turns on native locking, and what older setting is deprecated?
3. Why are CLI workspaces a poor way to separate prod from dev?
4. Name two ways state can hurt you.
5. What does `terraform force-unlock` need, and when is it safe?

**Answers**
1. `+` create, `~` change in place, `-/+` destroy then recreate.
2. `use_lockfile = true`. The DynamoDB `dynamodb_table` setting is deprecated.
3. They share one backend, so state and credentials are not separated. HashiCorp recommends separate configurations with separate backends.
4. It can contain secrets in plain text; it can be lost or corrupted; two writers can corrupt it without locking; it can drift from reality.
5. The lock ID shown in the error. It is safe only for your own stale lock after confirming no run is active.

## 8. Sources

- State locking, `-lock`, `force-unlock`: https://developer.hashicorp.com/terraform/language/state/locking
- S3 backend (`use_lockfile`, DynamoDB deprecated, versioning, encryption): https://developer.hashicorp.com/terraform/language/backend/s3
- Import blocks and `-generate-config-out`: https://developer.hashicorp.com/terraform/language/import
- CLI workspaces and when not to use them: https://developer.hashicorp.com/terraform/cli/workspaces
- 2026 topic summaries (prep sites, indicators only): https://www.kore1.com/devops-engineer-interview-questions/ and https://prachub.com/resources/devops-engineer-interview-questions-2026-ci-cd-docker-kubernetes-terraform-and-incidents
- Trivy scans IaC misconfigurations (Terraform among them): https://trivy.dev/latest/docs/

Not verified from a source: the plan symbol meanings and `-detailed-exitcode` codes; `-refresh-only`; `moved`/`removed` blocks; `count` vs `for_each`; `lifecycle` options; that state holds secrets in plain text (standard behavior, widely documented); the IBM/HashiCorp and OpenTofu notes; Azure Blob and GCS backend locking; Terragrunt; the exact version pins in the example; every `[SAMPLE]` output (invented for shape, not captured).
