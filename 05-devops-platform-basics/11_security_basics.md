# 11. Security basics (IAM, OAuth2/OIDC/JWT, secrets, supply chain, Trivy)

Legend: `[REAL]` = I ran it on this Mac on 2026-11-15 (a Python script that builds and decodes a demo JWT with a fake secret). `[SAMPLE]` = typical output written to show the shape. **Trivy is not installed on this Mac**, so Trivy output is `[SAMPLE]`; its commands and flags were checked in Trivy's docs where I say so. IAM, OAuth2, OIDC, JWT, and workload identity facts come from the RFCs and cloud docs (links at the end).

---

## 1. What it is (plain words + analogy)

Security basics for a platform engineer answer three questions:
1. **Who are you?** (authentication, "authn")
2. **What are you allowed to do?** (authorization, "authz")
3. **Can I trust the code and secrets I run?** (secrets and supply chain)

Analogy: an **office building**.
- **Badge** = identity (a user, or a program called a **workload**).
- **Door rules** = permissions (who may open which door). The rule of **least privilege** says: give each badge only the doors it needs.
- **Visitor pass for one day** = a short-lived token. Much safer than a master key that never expires.
- **Safe in the manager's office** = a secrets manager.
- **Checking the delivery box before bringing it in** = supply-chain security (scan, verify, pin).

## 2. Why it matters in interviews

Every platform role includes security. FIS (a financial company) and ScienceLogic will care. Expected questions: "how do you manage secrets?", "explain OAuth2 and JWT", "how do pipelines get cloud access without keys?", "what is least privilege?", "how do you secure the supply chain?", "what does Trivy do?". Google's cloud architect exam and loops also stress IAM design.

## 3. How it works, step by step

### 3.1 IAM (Identity and Access Management)

IAM decides **who can do what on which resource**. Google's IAM overview describes the parts:

- **Principal**: the identity getting access. Humans (Google accounts, groups, federated identities) and **workloads** (service accounts, federated workload identities).
- **Permission**: one action, named like `service.resource.verb` (for example `resourcemanager.projects.list`). You "can't directly grant permissions to a principal".
- **Role**: a bundle of permissions. Types: **predefined** (maintained by Google), **custom** (your exact list, more upkeep), **basic** (broad; "suited to testing, not production").
- **Allow policy**: attached to a resource; contains **role bindings** (principal -> role).
- **Resource hierarchy and inheritance**: organization -> folders -> projects -> resources. A role granted high up **applies to everything below**. The effective access is the combination of the resource's policy and all its ancestors'.

```
 Organization  (grant here = everything below gets it)
   └─ Folder "prod"
        └─ Project "web-prod"
             └─ Bucket / VM / Database  (grant here = narrowest)
```
**Least privilege in practice**: grant the **smallest role** at the **lowest level** (a specific project or resource, not the organization); use **groups** instead of single users; prefer predefined roles over basic roles (Owner/Editor/Viewer); give each workload its **own** service account; review access regularly; use temporary elevation (just-in-time) for admin tasks; log and audit (Cloud Audit Logs, Azure Activity Log, CloudTrail).

Kubernetes has its own authorization (RBAC, file 04): additive roles, no deny rules. Cloud IAM controls the cloud; RBAC controls the cluster. A pod reaches cloud services through a **workload identity** (3.5).

Same ideas in other clouds: Azure RBAC with role assignments at management group, subscription, resource group, resource scope; AWS IAM policies and roles. (I did not fetch Azure or AWS IAM docs today.)

### 3.2 OAuth2 in plain words

**OAuth 2.0** (RFC 6749) lets an app get **limited access** to a service on a user's behalf **without the user giving the app their password**. It is about **authorization**.

Four roles (RFC):
- **Resource owner**: the user who owns the data.
- **Client**: the app that wants access.
- **Authorization server**: the login-and-consent server; it issues tokens.
- **Resource server**: the API that holds the data; it accepts access tokens.

Analogy: a **hotel key card**. You (owner) go to the front desk (authorization server), prove who you are, and ask for a card that opens **only your room** for **your stay**. You give the card to the cleaner (client). The cleaner never learns your passport number. The room door (resource server) only checks the card.

**Authorization Code flow** (the common one), as the RFC describes it:
```
 1. Client sends the user's browser to the Authorization Server (with client_id, scope, redirect_uri, state).
 2. User signs in and approves.
 3. Authorization Server redirects the browser back to the client with a short-lived CODE.
 4. Client (authenticating itself) sends the code to the token endpoint.
 5. Authorization Server returns an ACCESS TOKEN (and maybe a REFRESH TOKEN).
 6. Client calls the API with:  Authorization: Bearer <access token>
```
RFC note: the owner's credentials never reach the client, and the access token isn't passed through the browser. The RFC defines an access token as "a string representing an authorization issued to the client" and the client usually cannot interpret it. It has a **scope** and a **lifetime**.

Other things to know (general knowledge, not read today): public clients (mobile apps, single-page apps) should use **PKCE** with the code flow; the **client credentials** flow is for machine-to-machine calls (no user); **refresh tokens** get new access tokens without a new login and must be guarded or rotated; the older implicit and password flows are discouraged.

### 3.3 OIDC: login on top of OAuth2

OAuth2 does not say **who the user is**. **OpenID Connect (OIDC)** adds that. The spec calls it "a simple identity layer on top of the OAuth 2.0 protocol". You add the scope `openid`, and you also receive an **ID token**: a signed **JWT** with claims about the login (issuer, subject, audience, expiry, and a **nonce** to stop replay). There is also a **UserInfo endpoint** for profile data.

```
 Access token = "this app may call this API (scope: read)"      -> sent to the API
 ID token     = "this person just logged in, id=42, via Google" -> read by the app, NOT sent to the API
```
Keycloak, Microsoft Entra ID, Okta, Google Sign-In, and Auth0 are OIDC/OAuth2 providers. SSO (single sign-on) is typically built with OIDC or SAML.

### 3.4 JWT in plain words

A **JWT** (JSON Web Token, RFC 7519) is "a compact, URL-safe means of representing claims". A signed JWT has **three parts** separated by dots, each **base64url**-encoded:

```
 header . payload . signature
 {"alg":"HS256","typ":"JWT"} . {"iss":..., "sub":..., "exp":...} . (signature bytes)
```
- **header**: which algorithm signs it.
- **payload**: the **claims** (statements). Registered claims from the RFC: `iss` (issuer), `sub` (subject), `aud` (audience: who it is for), `exp` (expiry: do not accept after), `nbf` (not before), `iat` (issued at), `jti` (unique id, helps stop replay).
- **signature**: proves the token was made by the key holder and not changed.

**Big point: a JWT is signed, NOT encrypted.** Anyone can read the payload. Never put secrets in it.

`[REAL]` I built a demo token (fake secret `demo-secret-not-real`) and decoded it:
```
eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJpc3MiOiAiaHR0cHM6Ly9sb2dpbi5leGFtcGxlLmNvbSIsICJzdWIiOiAidXNlci00MiIsICJhdWQiOiAiYmlsbGluZy1hcGkiLCAiZXhwIjogMTg5MzQ1NjAwMCwgInNjb3BlIjogInJlYWQifQ.C6t5V2edh601kzq_2ZyOee0OR9MyNIWT-vL8XvuUmU8
header : {'alg': 'HS256', 'typ': 'JWT'}
payload: {'iss': 'https://login.example.com', 'sub': 'user-42', 'aud': 'billing-api', 'exp': 1893456000, 'scope': 'read'}
signature (bytes, not readable): C6t5V2edh601kzq_2ZyO...
```
Anyone can decode the first two parts with `base64 -d`. Only the signature needs the key.

**How an API must verify a JWT** (all checks, in this order):
1. Check the **signature** with the **expected** key (for RS256/ES256, the issuer's **public key** from its JWKS URL; for HS256, a shared secret). **Pin the allowed algorithms**; never accept `alg: none` and never let the token choose a weak algorithm. (Standard guidance; not read today.)
2. Check `iss` is your trusted issuer.
3. Check `aud` is **you** (otherwise a token meant for another API could be replayed to yours).
4. Check `exp` (and `nbf`) with a small tolerance for clock skew (see file 09).
5. Check scopes/roles for the action.

Symmetric (HS256, one shared secret) vs asymmetric (RS256/ES256, private key signs, public key verifies): prefer asymmetric when many services only need to **verify**.

Problems: a JWT **cannot be revoked** before it expires (the server has no state). So keep access tokens **short-lived** (minutes), use refresh tokens, and keep a deny-list only if you must. Do not store tokens in places scripts can read (browser `localStorage`) without thinking about XSS (general guidance).

### 3.5 Workload identity: no secret at all

Best secret = **no secret**. A workload proves who it is with a **short-lived token** from a trusted issuer; the cloud exchanges it for access.

- **GitHub Actions -> cloud**: OIDC federation (file 07). Google's **Workload Identity Federation** gives outside workloads access "without a service account key", using short-lived tokens, with attribute mappings and conditions to limit who can authenticate. Keys are called "powerful credentials" that "can present a security risk if they are not managed correctly".
- **Pod -> Azure** (AKS): **Microsoft Entra Workload ID** uses a Kubernetes **service account token** (projected into the pod) and OIDC federation. The AKS cluster is the token **issuer**; Entra ID uses OIDC discovery to get the public signing keys, verifies the token, and exchanges it for an Entra token. You annotate the service account (`azure.workload.identity/client-id`) and label the pod `azure.workload.identity/use: "true"` (required in the pod template). Entra tokens expire in 24 hours; the projected Kubernetes token's default expiry is 3600 seconds. You then use `DefaultAzureCredential` in your code. Replaces the older pod-managed identity.
- **Pod -> Google Cloud** (GKE): Workload Identity (the same idea; I did not fetch that page today).

```
 pod ── projected K8s service account token (JWT, 1h) ──> Entra ID / Google STS
                                                           verifies via cluster's OIDC keys
 pod <── short-lived cloud access token ────────────────── then calls Key Vault / Storage
```

### 3.6 Secrets management

A **secret** is any value that gives access: passwords, API keys, tokens, private keys, certificates, database URLs with passwords.

Rules:
1. **Never in Git** (not in code, `.env`, Helm values, Terraform `tfvars`, Dockerfiles, or images). Once pushed, assume leaked; **rotate** it. Deleting the commit is not enough.
2. Store in a **secrets manager**: HashiCorp Vault, Azure Key Vault, Google Secret Manager, AWS Secrets Manager. Benefits: encryption, access control by identity, audit logs, **rotation**, versions.
3. Prefer **short-lived, dynamically issued** credentials (workload identity, Vault dynamic database users) over long-lived static ones.
4. **Least privilege** per secret and per workload; separate secrets per environment.
5. Deliver to pods carefully. The Kubernetes docs note Secrets are **base64, unencrypted by default**; enable **encryption at rest** for etcd; limit `get/list/watch` on Secrets by RBAC ("Granting list access to Secrets implicitly lets the subject fetch the contents"); anyone who can create a pod using a Secret can probably read it; prefer an external store through the **Secrets Store CSI Driver** or External Secrets Operator. Expose a secret only to the container that needs it, and make sure apps do not log it.
6. **Scan for leaked secrets** in repos and CI (gitleaks, trufflehog, GitHub secret scanning; Trivy also has a secret scanner).
7. **Rotate** regularly and after any exposure; design apps to reload secrets without a restart where possible.
8. Mask secrets in CI logs; GitHub docs: if a secret leaks into a log, delete the log **and rotate** the secret.

Cheat sheet:
```
 Weak                                Better                               Best
 password in code / .env in Git  ->  CI secret store / Kubernetes Secret ->  secrets manager + workload identity
 long-lived key, shared by all   ->  per-service key, rotated             ->  short-lived token, no key to steal
```

### 3.7 Supply chain security

The **software supply chain** is everything between "developer types code" and "code runs in production": dependencies, base images, build tools, CI, registries. Attackers target any step.

Controls (mix of verified docs and standard practice):
- **Pin versions and digests**: Docker's best practices say pin the base image "to a specific digest" for supply-chain integrity (tags are mutable) and use Dependabot to update digests. Same for GitHub Actions: pin to a full commit SHA (file 07). Same for Terraform providers and Helm charts (lock files).
- **Minimal base images** (distroless, slim, Alpine): less to attack. Multi-stage builds so compilers and secrets are not shipped (file 03). Run as non-root.
- **Scan** images and dependencies for known vulnerabilities (CVEs), and IaC/Kubernetes manifests for misconfigurations, in CI and also on a schedule (new CVEs appear after you ship).
- **SBOM** (software bill of materials): a list of what is inside an artifact, so when a new CVE appears you can answer "are we affected?" quickly. Trivy can scan SBOMs.
- **Sign and verify** images (Sigstore cosign) and **admission control** in the cluster that only allows signed or approved images (Kyverno, OPA Gatekeeper, or built-in policies).
- **Provenance**: a signed statement of **how and where** an artifact was built. **SLSA** (Supply-chain Levels for Software Artifacts) is a framework for this. The SLSA v1.0 spec has a single **Build track** with levels 1 to 3. (The page I read said "Version 1.2 is now current" and the v1.0 page is marked retired, so check the current version when you cite it.)
- **Trusted registries** only; private mirror/proxy for public packages; restrict who can push.
- **Protect CI**: least-privilege tokens, OIDC, protected branches, required reviews, no `pull_request_target` mistakes (file 07).
- **Dependency hygiene**: lock files, Dependabot or Renovate, review new dependencies, watch for typosquatting.
- Vulnerability handling: triage by **severity and exploitability** (is the vulnerable code reachable? is a fix available?), fix or mitigate, track exceptions with an expiry date.

### 3.8 Trivy

**Trivy** is an open-source scanner. From its docs: targets include **container images, filesystems, rootfs, code repositories, VM images, Kubernetes, and SBOMs**; scanners include **vulnerabilities, misconfigurations (IaC for Terraform, Kubernetes, Docker, Helm and more), secrets, licenses**, and cryptographic assets. A plain `trivy image` run does vulnerability and secret scanning by default.

Commands from the docs:
```bash
trivy image python:3.4-alpine                       # scan an image
trivy image --scanners vuln myapp:1.0               # only vulnerabilities
trivy image --input ruby-3.1.tar                    # scan a saved image tarball
trivy image --severity HIGH,CRITICAL myapp:1.0      # filter by severity
trivy image --ignore-unfixed myapp:1.0              # hide issues that have no fix yet
trivy config --severity HIGH,CRITICAL ./infra       # misconfigurations in Terraform/K8s/Dockerfile
```
Ignore a finding on purpose with a `.trivyignore` file (one ID per line; comments with `#`; the docs show an expiry form such as `CVE-2019-14697 exp:2023-01-01`, which forces a re-review). For CI gating, Trivy has an `--exit-code` option to make the build fail when findings exist (for example `--exit-code 1 --severity HIGH,CRITICAL`); the docs page I read did **not** cover `--exit-code`, so check `trivy image --help` for the exact behavior.

`[SAMPLE]` output shape (invented findings):
```
myapp:1.0 (debian 12.7)
=======================
Total: 3 (HIGH: 2, CRITICAL: 1)

┌──────────────┬────────────────┬──────────┬──────────────┬───────────────────┬───────────────┐
│   Library    │ Vulnerability  │ Severity │ Installed    │ Fixed Version     │    Title      │
├──────────────┼────────────────┼──────────┼──────────────┼───────────────────┼───────────────┤
│ libexample1  │ CVE-2026-0001  │ CRITICAL │ 1.2.3-1      │ 1.2.3-2           │ example issue │
└──────────────┴────────────────┴──────────┴──────────────┴───────────────────┴───────────────┘
```
How to talk about it: scan on every build, block on **fixable** HIGH/CRITICAL, keep a time-boxed ignore list, rescan stored images on a schedule, and remember a scanner finds **known** issues only.

### 3.9 A few more basics

- **Defense in depth**: many layers (network policy, RBAC, non-root, read-only filesystem, scanning, audit logs), so one failure is not fatal.
- **TLS everywhere**; **mTLS** (both sides present certificates) between services, often via a service mesh.
- **Encryption**: in transit (TLS), at rest (disk, buckets, etcd), key management with KMS and rotation.
- **OWASP Top 10**: the web application risk list. The current edition shown on OWASP's site is **2025**; I could not see the category names on that page, so read https://owasp.org/Top10/2025/ before quoting any. Injection, broken access control, and misconfiguration have been on it for years (general knowledge).
- **Audit and logging**: who did what, when; send logs off the machine; protect log integrity.
- **Incident basics for secrets**: revoke, rotate, find how it leaked, check usage logs for misuse, fix the cause.

## 4. Commands to try

```bash
# Decode a JWT yourself (never paste production tokens into random websites)
TOKEN="<paste a test token>"
echo "$TOKEN" | cut -d. -f1 | tr '_-' '/+' | base64 -d 2>/dev/null; echo
echo "$TOKEN" | cut -d. -f2 | tr '_-' '/+' | base64 -d 2>/dev/null; echo
# (padding may be missing; add '=' if base64 complains)

# Kubernetes: who can do what (needs a cluster; careful with your context)
kubectl auth can-i list secrets -n prod --as=system:serviceaccount:prod:my-app
kubectl get secret db -n dev -o jsonpath='{.data.password}' | base64 -d

# GCP IAM (needs gcloud)
gcloud projects get-iam-policy my-project --format=json | jq '.bindings[] | {role, members}'
gcloud iam service-accounts list

# Look for leaked secrets in a repo (install first)
gitleaks detect --source .

# Vulnerability scan (install trivy first)
trivy image --severity HIGH,CRITICAL myapp:1.0
trivy config .
```
`[SAMPLE]` `gcloud projects get-iam-policy` shape:
```
{ "role": "roles/storage.objectViewer", "members": ["group:data-readers@example.com"] }
{ "role": "roles/owner", "members": ["user:admin@example.com"] }     <-- review this kind of broad role
```

## 5. Common mistakes

1. Basic roles (Owner/Editor) or organization-level grants for convenience.
2. Long-lived service account keys or cloud keys stored in CI secrets.
3. Thinking a JWT is encrypted, putting secrets in it, or skipping `aud`/`iss`/`exp` checks.
4. Accepting any algorithm in JWT verification.
5. Secrets in Git history, Docker layers, Helm values, or logs; "deleted the file" without rotating.
6. Believing Kubernetes Secrets are encrypted; giving broad `list secrets` rights.
7. Using tags (`latest`, `v1`) for images and actions instead of digests and SHAs.
8. Scanning once and never again; or ignoring findings with no expiry.

## 6. Eight interview questions with answers

**Q1. Authentication vs authorization?**
Authentication proves who you are (password, certificate, token). Authorization decides what you may do (roles, policies). Example: login with OIDC is authentication; the API checking your scope or role is authorization.

**Q2. Explain OAuth2 in simple words.**
It lets an app get limited access to a user's data on a service without the user's password. The user logs in at the authorization server and consents. The app gets a short-lived code, exchanges it for an access token with limited scope and lifetime, and calls the API with the token. Roles: resource owner, client, authorization server, resource server. OIDC adds an ID token (a JWT) so the app also learns who the user is.

**Q3. What is a JWT, and what must a server check?**
A signed, base64url-encoded token with three parts: header, payload (claims such as `iss`, `sub`, `aud`, `exp`), and signature. It is signed, not encrypted, so never put secrets in it. The server must verify the signature with the expected key and an allowed algorithm, then check `iss`, `aud`, `exp`/`nbf`, and scopes. JWTs cannot be revoked before expiry, so keep them short-lived.

**Q4. How do you apply least privilege in a cloud like GCP?**
Predefined or custom roles instead of basic roles, granted at the lowest level (project or resource), to groups, with a separate service account per workload, no service account keys (use workload identity federation), regular access review, and audit logs. Inheritance means a high-level grant reaches everything below, so be careful.

**Q5. How do you manage secrets in Kubernetes?**
Prefer no secret (workload identity). Otherwise keep values in an external manager (Key Vault, Secret Manager, Vault) and sync or mount them using the CSI driver or External Secrets Operator. If you use native Secrets: enable etcd encryption at rest, restrict RBAC for get/list/watch, do not commit manifests, and remember base64 is not encryption. Rotate and avoid printing secrets in logs.

**Q6. How can a CI pipeline deploy to the cloud without stored keys?**
OIDC federation: the job gets a short-lived signed token from the CI platform; the cloud validates it against a trust policy limited to the specific repository, branch or environment, and returns short-lived credentials. No long-lived key exists to leak or rotate.

**Q7. What is supply-chain security and what are your top controls?**
Protecting everything that goes into production. Top controls: pin dependencies, base images (digest), and CI actions (SHA); minimal images and non-root; scan images, dependencies, and IaC in CI and on schedule (Trivy); generate SBOMs; sign images and enforce signatures at admission; keep build provenance (SLSA); protect CI credentials and branches; review new dependencies.

**Q8. What does Trivy do and how would you use it in a pipeline?**
It scans images, filesystems, repos, Kubernetes, IaC, and SBOMs for vulnerabilities, misconfigurations, secrets, and licenses. In CI: scan the built image, filter to HIGH and CRITICAL (optionally only fixable with `--ignore-unfixed`), fail the build on findings via the exit-code option, keep a reviewed `.trivyignore` with expiry dates, publish the report, and rescan stored images regularly since new CVEs appear over time.

## 7. Self-quiz (answers at the end)

1. Is a JWT encrypted? How can you read its payload?
2. Name the four roles in OAuth 2.0.
3. Why is `aud` important when validating a JWT?
4. What is wrong with granting the Owner role at the organization level to a CI service account?
5. Why is "just delete the commit" not enough after pushing a secret?

**Answers**
1. No, only signed. Base64url-decode the second part.
2. Resource owner, client, authorization server, resource server.
3. It says who the token is meant for. Without checking it, a token issued for another API could be replayed to yours.
4. It violates least privilege: a compromised pipeline would control the whole organization. Use a narrow predefined role on one project with workload identity federation.
5. The secret may already be cloned, cached, or scraped, and remains in Git history. Treat it as leaked and rotate it.

## 8. Sources

- RFC 6749, OAuth 2.0 (roles, authorization code grant, access token): https://datatracker.ietf.org/doc/html/rfc6749
- RFC 7519, JWT (structure, registered claims): https://datatracker.ietf.org/doc/html/rfc7519
- OpenID Connect Core (identity layer, ID token, UserInfo): https://openid.net/specs/openid-connect-core-1_0.html
- Google Cloud IAM overview (principals, roles, allow policies, inheritance): https://docs.cloud.google.com/iam/docs/overview
- Google Cloud Workload Identity Federation: https://docs.cloud.google.com/iam/docs/workload-identity-federation
- Microsoft Entra Workload ID on AKS: https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview
- Kubernetes Secrets good practices: https://kubernetes.io/docs/concepts/security/secrets-good-practices/
- Docker build best practices (non-root, digest pinning): https://docs.docker.com/build/building/best-practices/
- GitHub Actions secure use (secrets, pinning): https://docs.github.com/en/actions/reference/security/secure-use
- Trivy docs: https://trivy.dev/latest/docs/ , image scanning https://trivy.dev/latest/docs/target/container_image/ , filtering https://trivy.dev/latest/docs/configuration/filtering/
- SLSA v1.0 about page: https://slsa.dev/spec/v1.0/about
- OWASP Top 10 project page (edition 2025): https://owasp.org/www-project-top-ten/
- Local: Python demo JWT built and decoded on this Mac, 2026-11-15 (fake secret)

Not verified from a source: PKCE, client credentials, refresh token advice; JWT verification checklist details (alg pinning, `alg: none`), HS256 vs RS256 advice, localStorage/XSS note; GKE Workload Identity; Azure and AWS IAM; Vault, CSI driver and External Secrets product details beyond what the Kubernetes page names; gitleaks, trufflehog, cosign, Kyverno, OPA Gatekeeper, SBOM descriptions; Trivy `--exit-code` semantics and the Trivy default-scanner statement beyond what the docs show; mTLS and service mesh remarks; OWASP category names; the sample outputs marked `[SAMPLE]`.
