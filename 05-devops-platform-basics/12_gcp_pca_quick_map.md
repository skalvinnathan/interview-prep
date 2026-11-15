# 12. Google Cloud quick map (for Professional Cloud Architect holders)

You already have the Google Cloud Professional Cloud Architect certification and a study site. This file is a **short map**: the main services, **when to pick each**, and the one-line "why". It is for interviews (Google loops, FIS, Smallest AI), not for the exam.

Legend: `[SAMPLE]` = shape example, not run. I did not run any `gcloud` command (no Google Cloud login on this machine). Statements marked **(Google docs)** were read on Google's pages today. Everything else is general knowledge and listed at the end as unverified.

---

## 1. What it is (plain words + analogy)

Google Cloud (GCP) is a set of rentable building blocks. Think of a **city**:
- **Compute** = buildings (from an empty plot you build on, to a ready shop).
- **Storage** = warehouses (boxes, shelves, filing cabinets).
- **Networking** = roads, gates, and traffic police.
- **IAM** = the badge office.
- **Data and analytics** = the city's records office and research lab.
- **Operations** = the CCTV and control room.

The skill for an architect (and for an interview) is **choosing the right block** and saying **why**: how much you manage yourself vs how much Google manages, cost, scale, latency, and failure.

## 2. Why it matters in interviews

For Google roles, they expect you to speak their products and trade-offs. For other companies (FIS, ScienceLogic), the same thinking maps to Azure and AWS, so use GCP as your example and name the equivalent. Typical prompts: "which compute option for this workload?", "which database?", "how do you give a CI pipeline access without keys?", "how do you design a multi-region, highly available service?".

## 3. How it works, step by step: the map

### 3.1 The resource hierarchy and IAM (Google docs)

Organization -> Folders -> Projects -> resources. IAM allow policies on a parent are **inherited** by everything below. A **project** is the main unit of billing, quotas, and API enablement. Use **folders** per environment or team, and a **separate project** per environment and per application to limit blast radius. IAM basics (principals, roles, allow policies, inheritance) are in file 11.

### 3.2 Compute: which one?

```
 more control, more work                                              less control, less work
 Compute Engine (VMs) ── GKE Standard ── GKE Autopilot ── Cloud Run (containers) ── Cloud Run functions
```
| Service | What it is | Pick it when |
|---|---|---|
| **Compute Engine** | Virtual machines | you need full OS control, special software, lift-and-shift, GPUs/custom machine shapes, licensing needs |
| **GKE** (Kubernetes Engine) | Managed Kubernetes | you want Kubernetes (many services, portability, custom operators, stateful sets, service mesh) |
| - GKE **Autopilot** | Google manages nodes and scaling | **Google docs**: it "handles most of your infrastructure", and is recommended for most production workloads unless you need privileges or settings Autopilot does not allow |
| - GKE **Standard** | You manage node pools | **Google docs**: you have "direct control over your node infrastructure and autoscaling"; use it when workloads need special privileges or granular infrastructure control |
| **Cloud Run** | Serverless containers | stateless HTTP services, APIs, event handlers, jobs, queue workers, with scale to zero and no cluster to run |
| **Cloud Run functions** | Single-purpose event-driven functions | tiny glue code on events (a file lands, a message arrives) |
| **App Engine** | Older platform for web apps | existing apps; for new work most people choose Cloud Run (general knowledge) |
| **Batch** | Managed batch jobs | large batch computing without managing a cluster |

**Cloud Run facts (Google docs)**: a managed platform for running code, functions, or containers "without creating or managing clusters". Resource types: **service** (HTTP, autoscales), **job** (runs to completion, on demand or on a schedule), **worker pool** (always-on non-HTTP work such as queue consumers), and an **instance** type in Preview. A service with no traffic **scales to zero**; the next request starts an instance and may be slower, so use **minimum instances** to avoid it. Instances are **stateless and disposable** (in-memory file system is lost), and your app can handle `SIGTERM` to flush data before exit (so the PID 1/signal lesson from file 03 applies). Billing is **request-based** (pay while processing, plus a per-request fee) or **instance-based** (pay for the full instance lifetime, no per-request fee), measured in 100 ms increments of allocated CPU and memory.

Decision shortcut for an interview: "Stateless HTTP and no special needs -> **Cloud Run**. Many microservices with Kubernetes skills, or need operators, sidecars, mesh, or stateful sets -> **GKE** (Autopilot first). Need OS-level control or legacy software -> **Compute Engine**. Event glue -> **Cloud Run functions**."

Autoscaling and availability on Compute Engine: **managed instance groups** (MIGs) with autohealing and autoscaling, spread over zones, behind a load balancer. **Regional** MIGs and **regional** GKE clusters survive a zone failure. (General knowledge.)

### 3.3 Storage

| Service | Type | Pick it for |
|---|---|---|
| **Cloud Storage** | object storage (buckets) | files, backups, logs, data lake, static sites; storage classes (Standard, Nearline, Coldline, Archive) trade cost vs access frequency; lifecycle rules move or delete data |
| **Persistent Disk / Hyperdisk** | block storage for VMs and GKE volumes | databases on VMs, boot disks; zonal or regional |
| **Filestore** | managed NFS file share | shared POSIX file system for many VMs/pods |

### 3.4 Databases (Google docs database overview)

| Service | Google's one-line description | Pick it when |
|---|---|---|
| **Cloud SQL** | "fully-managed database service" for MySQL, PostgreSQL, SQL Server | a normal relational app database at moderate scale; least effort |
| **AlloyDB** | "PostgreSQL-compatible database for demanding transactional workloads" | PostgreSQL apps needing higher performance and analytics speed |
| **Spanner** | "mission-critical, global-scale database service" | relational with global scale and strong consistency across regions; very high availability needs |
| **Firestore** | "flexible, scalable NoSQL document database" (a MongoDB-compatible edition is available) | mobile/web apps, document data, simple scaling |
| **Bigtable** | "terabytes or petabytes" in a NoSQL wide-column service | huge key-value/time-series workloads with very high throughput and low latency |
| **BigQuery** | "fully managed, highly scalable data warehouse with built-in ML" | analytics (column store, file 10), not application transactions |
| **Memorystore** | in-memory (Valkey, Redis, Redis Cluster; the page notes Memcached is deprecated) | caches, sessions, leaderboards |

(The "pick it when" column is my reading of the descriptions, as the Google page itself gives no selection rules.)

### 3.5 Networking

- **VPC**: your private network. Google VPCs are **global** (subnets are regional); firewall rules apply per VPC (general knowledge; check the docs when quoting).
- **Cloud Load Balancing**: global external HTTP(S) load balancer (one anycast IP, can route to backends in many regions), plus regional and internal load balancers, and TCP/UDP load balancers.
- **Cloud CDN**: caches content at the edge. **Cloud Armor**: WAF and DDoS protection in front of the load balancer.
- **Cloud DNS**: managed DNS (see file 02 for how DNS works).
- **Cloud NAT**: outbound internet for private VMs/pods without public IPs (NAT, file 02; watch port exhaustion).
- **Private Google Access / Private Service Connect**: reach Google APIs and published services privately.
- **VPN, Cloud Interconnect**: connect on-premises to GCP (VPN over the internet; Interconnect is a dedicated link).
- **Shared VPC**: one host project owns the network; service projects use it.
- **VPC Service Controls**: a perimeter to reduce data exfiltration from Google APIs.

### 3.6 Messaging and data pipelines

- **Pub/Sub**: global asynchronous messaging; **at-least-once delivery** by default (so consumers must be idempotent, file 09); decouples producers and consumers and absorbs bursts (backpressure helper).
- **Dataflow**: managed stream and batch processing (Apache Beam). **Dataproc**: managed Spark/Hadoop. **BigQuery**: warehouse. **Cloud Composer**: managed Airflow for workflows. **Dataform**/scheduled queries for SQL pipelines.
- **Cloud Tasks / Workflows / Eventarc / Cloud Scheduler**: task queues, orchestration, event routing, cron.

### 3.7 Operations and DevOps tooling

- **Cloud Monitoring** (metrics, dashboards, alerting, SLO monitoring), **Cloud Logging**, **Cloud Trace**, **Error Reporting**, **Managed Service for Prometheus** (Prometheus-compatible metrics). Concepts match file 08.
- **Artifact Registry**: stores container images and packages. **Cloud Build**: managed CI. **Cloud Deploy**: managed delivery pipelines to GKE/Cloud Run. (Many teams use GitHub Actions instead; see file 07.)
- **Secret Manager**: secrets storage. **Cloud KMS**: encryption keys. **Workload Identity Federation**: external workloads (GitHub Actions, AWS, Azure, on-prem) access Google Cloud **without service account keys**, with short-lived tokens, attribute mappings, and conditions **(Google docs)**. GKE has its own Workload Identity for pods.
- **Cloud Audit Logs**: who did what. **Organization Policy**: guardrails (for example block service account key creation, restrict regions).
- **Terraform**: the usual way to manage GCP as code (file 06).

### 3.8 Reliability design in GCP (how to answer "design for high availability")

```
 Users ─> global HTTPS Load Balancer (Cloud Armor, CDN)
             ├─> Region A: GKE/Cloud Run/MIG across 3 zones ─> regional DB (HA replica)
             └─> Region B: same (active-active or warm standby)
        data: Spanner (multi-region) or Cloud SQL/AlloyDB with cross-region replica + backups to Cloud Storage
```
Points to say: **zones** are failure domains inside a region; **regions** are far apart (disaster recovery). Define **SLOs** first (file 08), then choose the cost level: single zone < multi-zone < multi-region. Know **RPO/RTO** (data loss and downtime allowed). Test failover. Use health checks, autohealing, graceful shutdown, retries with jitter, and load shedding (file 09). Back up data and **test restores**.

### 3.9 Cost basics

Use the right size (rightsizing recommendations), autoscaling, **committed use discounts** for steady load, **Spot VMs** for fault-tolerant batch (can be reclaimed at short notice), storage lifecycle policies, labels for cost reporting, budgets and alerts, and turn off idle resources. (General knowledge; I did not verify current discount names or numbers.)

### 3.10 Equivalent services (useful when the interviewer uses Azure or AWS)

| Idea | GCP | Azure | AWS |
|---|---|---|---|
| VMs | Compute Engine | Virtual Machines | EC2 |
| Managed Kubernetes | GKE | AKS | EKS |
| Serverless containers | Cloud Run | Container Apps | App Runner / Fargate |
| Object storage | Cloud Storage | Blob Storage | S3 |
| Managed relational DB | Cloud SQL | Azure Database for PostgreSQL/MySQL, SQL Database | RDS |
| Warehouse | BigQuery | Synapse / Fabric | Redshift |
| Messaging | Pub/Sub | Service Bus / Event Hubs | SNS+SQS / Kinesis |
| Secrets | Secret Manager | Key Vault | Secrets Manager |
| Identity for pods | Workload Identity | Entra Workload ID (verified in file 11) | IRSA / EKS Pod Identity |
(Rows other than the AKS Workload ID are from general knowledge. AWS Well-Architected is Amazon's framework for design reviews; I opened its welcome page, which describes it as helping you build "secure, reliable, efficient, cost-effective, and sustainable" workloads.)

## 4. Commands to try

```bash
gcloud auth login                       # (needs your account; do not share tokens)
gcloud config list
gcloud projects list
gcloud compute instances list
gcloud container clusters list
gcloud run services list --region asia-south1
gcloud sql instances list
gcloud storage ls
gcloud projects get-iam-policy <project-id> --format=json | jq '.bindings'
gcloud logging read 'severity>=ERROR' --limit 10
```
`[SAMPLE]` `gcloud run services list`:
```
   SERVICE  REGION        URL                              LAST DEPLOYED BY    LAST DEPLOYED AT
✔  web      asia-south1   https://web-xxxxx-el.a.run.app   dev@example.com     2026-11-14T10:20:30Z
```
(`gcloud` subcommand names are real in general; I did not run them, so check `gcloud <group> --help`.)

## 5. Common mistakes

1. One big project for everything, or grants at the organization level.
2. Using service account keys when Workload Identity Federation exists.
3. Choosing GKE when Cloud Run would do (more to operate), or Compute Engine VMs for stateless apps.
4. Running analytics on Cloud SQL instead of BigQuery.
5. Forgetting that Cloud Run scales to zero (cold starts) and instances are stateless.
6. Single-zone deployments and untested backups, with no RPO/RTO defined.
7. Ignoring egress and cross-region network costs.
8. No Pub/Sub idempotency (duplicates under at-least-once delivery).

## 6. Eight interview questions with answers

**Q1. Cloud Run, GKE, or Compute Engine for a new stateless API?**
Cloud Run first: no cluster to run, autoscaling including to zero, simple deploys, pay per use. Choose GKE if the team already runs many services on Kubernetes or needs operators, sidecars, mesh, GPUs with special scheduling, or stateful sets. Choose Compute Engine for OS-level control or legacy software. Prefer the least operational burden that meets the requirements.

**Q2. GKE Autopilot vs Standard?**
In Autopilot, GKE manages nodes and scaling and you focus on pods; Google recommends it for most production workloads unless you need privileges or settings Autopilot does not allow. In Standard you manage node pools and have granular control over infrastructure, at the cost of more operations. They can be mixed to a degree (Standard clusters can run Autopilot-style workloads through compute classes).

**Q3. How do you choose a database on Google Cloud?**
Relational, moderate scale: Cloud SQL. PostgreSQL needing more performance: AlloyDB. Relational with global scale and strong consistency: Spanner. Document and mobile-friendly: Firestore. Massive wide-column or time-series throughput: Bigtable. Analytics: BigQuery. Cache: Memorystore. Decide by data model, consistency, scale, latency, and cost.

**Q4. How would a GitHub Actions pipeline deploy to GCP without keys?**
Workload Identity Federation: a workload identity pool and provider trust GitHub's OIDC issuer; attribute mappings and conditions restrict to the specific repository and branch; the job uses `id-token: write`, exchanges its token through Google's STS for short-lived credentials, and either holds IAM roles directly or impersonates a narrowly scoped service account.

**Q5. What is the resource hierarchy and why does it matter?**
Organization, folders, projects, resources. IAM policies and organization policies inherit downward, so you set broad guardrails high and specific access low. Projects are boundaries for billing, quotas, and blast radius; use separate projects per environment and application.

**Q6. Design a highly available web service on GCP.**
Global external HTTPS load balancer with Cloud Armor (and CDN for static content), stateless services on GKE or Cloud Run across at least three zones (and two regions if the SLO needs it), a database with an HA configuration (regional Cloud SQL/AlloyDB with a cross-region replica, or Spanner multi-region), Pub/Sub to decouple async work, health checks and autohealing, graceful shutdown, retries with jitter, SLO-based alerts, backups with tested restores, and defined RPO/RTO.

**Q7. Pub/Sub delivery guarantees and what you must do in consumers?**
Delivery is at-least-once by default, so duplicates can happen and ordering is not guaranteed unless you use ordering keys. Make consumers idempotent (dedupe by message ID or use upserts), acknowledge only after successful processing, set a dead-letter topic for poison messages, and use backoff for retries.

**Q8. How do you keep cloud costs under control?**
Right-size resources, autoscale, use committed use discounts for steady workloads and Spot VMs for fault-tolerant batch, lifecycle rules for storage, scale-to-zero services where suitable, labels and budgets with alerts, and regular review of recommendations. Watch network egress and cross-region traffic.

## 7. Self-quiz (answers at the end)

1. Which service is the managed data warehouse, and is it row or column oriented?
2. Which Cloud Run resource type runs a task to completion on a schedule?
3. What does a Cloud Run service do when there is no traffic?
4. Name the levels of the GCP resource hierarchy.
5. What replaces service account keys for an external CI system?

**Answers**
1. BigQuery; column oriented.
2. A Cloud Run **job**.
3. It scales to zero (all instances removed); the next request starts a new instance and may be slower. Set minimum instances to avoid that.
4. Organization, folders, projects, resources.
5. Workload Identity Federation (short-lived tokens through OIDC or SAML, no keys).

## 8. Sources

- Cloud Run overview (service, job, worker pool, scale to zero, stateless, billing): https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run
- GKE Autopilot vs Standard: https://docs.cloud.google.com/kubernetes-engine/docs/concepts/choose-cluster-mode
- Google Cloud databases overview: https://docs.cloud.google.com/docs/databases
- IAM overview and resource hierarchy: https://docs.cloud.google.com/iam/docs/overview
- Workload Identity Federation: https://docs.cloud.google.com/iam/docs/workload-identity-federation
- AWS Well-Architected Framework welcome page: https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html
- Microsoft Entra Workload ID on AKS (for the equivalence row): https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview

I tried to read Google's "choosing a compute option" and "products" pages but they returned only titles, so the compute decision table, storage, networking, messaging, operations, cost, and equivalent-services sections are **general knowledge, not verified today**. Specifically unverified: Compute Engine/MIG/regional behavior, storage classes, VPC being global, load balancer types, Cloud Armor/CDN/NAT/Interconnect/Shared VPC/VPC Service Controls descriptions, Pub/Sub at-least-once and ordering keys, Dataflow/Dataproc/Composer descriptions, Cloud Build/Deploy, Spot VMs and committed use discounts, the Azure and AWS equivalents (except AKS Workload ID), and all `gcloud` command names. For anything exam-related, trust your own study site.
