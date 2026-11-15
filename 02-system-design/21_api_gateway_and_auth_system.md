# 21. Design an API Gateway and Auth System

This is close to your work: an access-control service (roles, groups, permissions, maker-checker approvals), an OIDC gateway, and a shared auth library. Use them as your worked example, in generic words. Stripe interview reports also mention redesigning an internal authorization system across services, and the idea of splitting slow policy management from fast enforcement (see `00`, `91`).

---

## 1. The problem in plain words

Many services sit behind one entrance. We need to:
1. Send each request to the right service (**routing**).
2. Know **who** is calling (**authentication**: "are you really Asha?").
3. Decide **what** they may do (**authorization**: "may Asha approve this payment?").
4. Protect the services (rate limits, TLS, logging).

**Analogy: an office building.**
- The **reception desk** (API gateway) is the only public door. It checks your badge, tells you which floor to go to, and keeps a visitor log.
- The **badge office** (identity provider) issues badges after checking your ID card (login).
- The **rulebook** (authorization service) says which rooms each badge may enter. Room guards (services) can also ask "may this badge enter?".
- **Maker-checker**: for risky actions (like transferring a large sum), one person prepares (maker) and a **different** person must approve (checker). Nobody approves their own work.

---

## 2. Requirements

**Must-have**
1. **Gateway**: single entry; route by path/host; TLS termination; request/response logging; rate limiting (`11`); basic request validation; retries/timeouts to backends.
2. **Authentication**: users log in through an identity provider using OpenID Connect (OIDC) (single sign-on); service-to-service identity; API keys for machine clients.
3. **Authorization**: roles, groups, and permissions (RBAC); optionally attribute-based rules (ABAC); decision "allow/deny" for (subject, action, resource).
4. **Admin APIs** to manage roles, groups, permission assignments; **audit trail** of every change.
5. **Maker-checker workflow** for sensitive changes (a role change, a permission grant, a sensitive action) - needs approval by a second authorised user.
6. **Revocation**: when access is removed it takes effect quickly.

**Non-functional**
- The authorization check is on **every request**: it must be very fast (about 1 to 5 ms; assumption) and highly available.
- Security first: least privilege, no secrets in logs, short-lived tokens, auditability.
- Scale: thousands of requests per second per service, many services.

**Out of scope**
- Building the identity provider from scratch (use an established one such as Keycloak, an OIDC provider), MFA internals, fraud detection, user-facing consent screens.

---

## 3. The numbers (estimates)

Assume 5M users, 20,000 requests per second at peak through the gateway, 100 backend services, 5,000 roles/groups, permissions per user about 50.

| Item | Value |
|---|---|
| Gateway traffic | 20,000 requests/s peak; a gateway node handles several thousand/s, so 10 to 20 nodes for headroom |
| Auth decisions | 1 per request = 20,000/s; to keep latency tiny, decisions must be **local** (in memory or cached), not a remote call each time |
| Tokens | 5M users x 1 login/day = 5M logins/day = about 60/s average (spiky at 9 am: say 1,000/s) |
| Policy data | 5,000 roles x 50 permissions x 100 B = 25 MB. Tiny. Fits in the memory of every service |
| Audit log | 20,000 req/s x 300 B = 6 MB/s = about 500 GB/day if all requests are logged (sample or keep only security-relevant events; compress; short retention for access logs, longer for policy changes) |
| Policy changes | Rare: tens per hour. A very read-heavy workload |

Meaning: policy data is **small and rarely changes**, but is **read on every request**. So: distribute policy to the edge (cache/replicate), keep the admin path separate and slower.

---

## 4. The API

**Gateway (what clients see):**

```
Any request:  Authorization: Bearer <access token (JWT)>
   -> 401 if missing/invalid/expired; 403 if authenticated but not allowed; 429 if rate limited
```

**Authentication (OIDC, simplified authorization code flow):**

```
1. Browser -> App: "open /dashboard"            (no session)
2. App/Gateway redirects the browser to the Identity Provider (IdP) login page
3. User logs in at the IdP (password, MFA ...)
4. IdP redirects back to the app with a one-time CODE
5. App/Gateway exchanges the CODE (server to server) for tokens:
      ID token      (who the user is)
      Access token  (short-lived: 5-15 min, for calling APIs)
      Refresh token (longer-lived: get new access tokens without logging in again)
6. Browser/app uses the access token on API calls
```

**Authorization service (internal):**

```
POST /v1/authz/check    { "subject": "user:42", "action": "payment:approve", "resource": "payment:900",
                          "context": {"amount": 500000} }
  reply: { "allow": true | false, "reason": "role:approver", "policy_version": 118 }

Admin (slower, audited):
POST /v1/roles                         { name, permissions: [...] }
POST /v1/groups/{id}/members           { user_id }
POST /v1/role-bindings                 { subject, role, scope }
POST /v1/change-requests               { type: "grant_role", payload: {...} }     <- maker creates
POST /v1/change-requests/{id}/approve  (checker; must be a different user)
POST /v1/change-requests/{id}/reject
GET  /v1/audit?actor=...&from=...
```

---

## 5. The data tables

**user** (often owned by the IdP): `user_id`, `email`, `status`, `attributes`.

**group**: `group_id`, `name`. **group_member**: `(group_id, user_id)`.

**role**: `role_id`, `name`, `description`. **permission**: `permission_id`, `action` (for example `payment:approve`), `resource_type`. **role_permission**: `(role_id, permission_id)`.

**role_binding** (who has which role where): `(subject_type, subject_id, role_id, scope)` - subject is a user or a group; scope is global / tenant / project (for multi-tenant).

**change_request** (maker-checker): `request_id`, `type`, `payload`, `maker_id`, `status` (pending/approved/rejected/applied/expired), `checker_id`, `created_at`, `decided_at`, `reason`. Rule enforced in code **and** a DB constraint/check: `checker_id <> maker_id`.

**policy_version**: a counter that increases on every applied change (used for cache invalidation).

**audit_log** (append-only): `event_id`, `actor`, `action`, `target`, `before`, `after`, `ts`, `request_id`. Write-once storage (no updates or deletes).

**api_key**: `key_id`, `hashed_secret` (never store the raw secret), `owner`, `scopes`, `expires_at`, `revoked`.

**Storage choice:** policy and bindings in SQL (transactions, relations, constraints); published as a read-only snapshot to caches. Audit log in an append-only store.

---

## 6. Version 1 (simple)

```
 Client --> [Monolith app]
              - login page, passwords table
              - session cookie in server memory
              - if (user.role == "admin") allow
```

Problems: every service re-implements login and permission checks differently; sessions in memory break with 2 servers; roles are hard-coded; no audit; no approval step; no SSO across apps.

---

## 7. Growing 100x, step by step

**Step 1. Use an identity provider with OIDC (single sign-on).** One login for all apps. Services never see passwords. Tokens prove identity. (Keycloak-style IdP.)

**Step 2. Put an API gateway in front.** All traffic enters through the gateway: TLS termination, routing, rate limiting, request IDs for tracing, and **token validation** (first line of defence). Backends sit on a private network.

```
 Client --> [LB] --> [API Gateway x N] --> Service A / B / C
                         |  validates JWT (signature, expiry, audience)
                         |  rate limit, logging
                         v
                    (IdP keys via JWKS, cached)
```

**Step 3. Stateless tokens (JWT).** The access token is a signed JSON document (header.payload.signature) containing `sub` (user), `exp` (expiry), `aud` (which API), `iss` (issuer), and claims such as roles or groups. A service can **verify the signature locally** with the IdP's public key (fetched once from the JWKS URL and cached), so no call to the IdP on each request. This is why the gateway scales. Keep tokens **short-lived** (minutes) so a stolen or outdated token dies soon.

**Step 4. A shared auth library.** Every service uses the same small library for: JWT validation, extracting the user, calling the authorization check, standard 401/403 responses, audit hooks, and test helpers. This avoids "each team wrote its own wrong version". It is a good place for consistent behaviour; the trade-off is that library upgrades must roll out to all services (versioning, backwards compatibility, security patch process). (You built one; mention it in one sentence.)

**Step 5. Centralised authorization service + local enforcement (the key idea).** Separate:
- **Policy administration (slow path)**: admin APIs, approvals, audit. Low traffic.
- **Policy decision/enforcement (fast path)**: every request.

Because policy data is tiny (25 MB), push it to where decisions happen:
- **Option A: claims in the token.** Put roles/groups in the JWT. Check locally, zero network. Con: permission changes only take effect when the token expires or refreshes (stale up to token lifetime). Also tokens get large with many roles.
- **Option B: local policy cache in each service/gateway.** The auth library keeps an in-memory copy of policies and bindings, refreshed by **events** (a "policy_version changed" message) or by polling every few seconds. Decisions are local and fast; changes propagate in seconds.
- **Option C: remote check per request** to the authorization service (with a local cache of recent decisions). Most accurate, but adds a network hop and makes the service a critical dependency (needs very high availability).

My choice: **B (with A for coarse claims)**: token carries identity and coarse roles; the library resolves fine-grained permissions from a locally cached policy snapshot that is pushed by events with a version number. For very sensitive actions, call the authorization service directly (option C) for the freshest decision.

```
 Admin UI --> [Policy service + SQL] --publishes--> Kafka "policy_changed(version)"
                                                          |
              +-------------------------------------------+---------------+
              v                                           v               v
     [Gateway lib cache]                         [Service A lib cache]  [Service B lib cache]
        (in-memory snapshot, version N)
```

**Step 6. Revocation and staleness.** Questions to settle:
- "How fast must a removed permission stop working?" For normal actions: seconds to minutes (event push + short token life). For emergencies (fired employee, stolen credentials): a **deny list** of revoked token ids / user ids checked by the gateway (small, replicated, in memory), and **refresh token revocation** at the IdP. This is the consistency trade-off from `01h`: you accept short staleness for speed, with an emergency path for instant revoke.

**Step 7. Maker-checker workflow.** Sensitive changes are **not applied directly**.

```
 Maker: POST change-request (grant role X to user Y)     -> status = pending
 System: validates maker has permission to *request* it; notifies eligible checkers (`14`)
 Checker (different user, has approve permission): approve / reject (with reason)
 System: re-validates (state still valid, policy not changed, request not expired),
         applies the change in ONE transaction (+ audit entry + policy_version++), emits event
         -> status = applied
```

Rules: maker != checker (enforced in code and DB), requests expire (for example 7 days), approvals are idempotent, everything is audited, and the "apply" step is a small workflow with retries (compare `20`: a human approval step in a workflow). For higher risk, require 2 approvers or specific roles ("four eyes" or "n-of-m").

**Step 8. Service-to-service authentication.** Services also need identity: use mutual TLS (each service has a certificate, often issued by a service mesh) or short-lived service tokens (OIDC client credentials). Authorization for services uses the same policy engine ("service A may call endpoint X of service B"). Also propagate the **original user identity** in a header/token (token exchange) so downstream services can enforce user-level rules (avoid the "confused deputy" problem: a powerful service acting on behalf of a weak user).

**Step 9. Multi-tenancy.** Tokens carry a tenant id; every query and policy is scoped by tenant; role bindings have a scope; the gateway rejects cross-tenant resource ids. Isolate noisy tenants with per-tenant rate limits. (You run multi-tenant platforms, so it is a good story.)

**Step 10. Gateway scale and availability.** Gateway nodes are stateless; scale horizontally behind an L4/L7 load balancer; deploy across zones; use health checks; rate-limit state in Redis (`11`); config (routes, policies) from a control plane with versioned, validated rollouts; timeouts, retries (idempotent only), circuit breakers toward backends (`03`). Avoid putting business logic in the gateway.

**Step 11. Audit and observability.** Every decision and every admin change produces a structured event: who, what, when, from where, result, policy version, request id. Send to the logging platform (`22`). Alert on unusual patterns: spikes of 403, privilege escalation, approvals outside hours. Keep policy-change audit forever (or by regulation); sample or shorten access logs.

**Step 12. Security hardening.** Short-lived access tokens; rotate signing keys (support multiple keys in JWKS during rotation); validate `iss`, `aud`, `exp`, `nbf` and algorithm; store hashed API keys; PKCE for public clients; secure cookies for browser sessions (HttpOnly, SameSite); never log tokens; least-privilege defaults (deny by default).

Final picture:

```
 Browser/Mobile/Partner
        |
     [CDN/WAF] -> [LB] -> [API Gateway x N] ---- rate limit (Redis)
                              | validate JWT (JWKS cache), deny-list, route
                              v
                   +-------------------+     +--------------------------+
                   | Services A,B,C    | <-- | Shared auth library      |
                   | (private network) |     | (JWT check, local policy |
                   +-------------------+     |  cache, audit hook)      |
                                             +------------^-------------+
 [Identity Provider (OIDC)]  <--login/tokens--             | events: policy_changed(version)
 [Policy admin service + SQL + change_request workflow] ---+--> Kafka --> caches
        | audit events
        v
 Append-only audit store -> logging/metrics platform (22)
```

---

## 8. Trade-offs and why

| Choice | Why | Cost |
|---|---|---|
| JWT, local verification | No IdP call per request; scales | Cannot be revoked until expiry (mitigate: short life, deny-list) |
| Short token life + refresh | Limits damage of theft | More refresh traffic; session handling |
| Local policy cache pushed by events | Fast, resilient if auth service is down | Staleness window; cache invalidation logic |
| Remote check for sensitive actions | Freshest decision | Latency and dependency |
| Shared library | Consistency, less duplication | Rollout coupling; language support |
| Separate admin path from decision path | Different load and risk profiles | Two systems to run |
| Maker-checker | Prevents single-person abuse/mistakes | Slower changes; approval backlog |
| RBAC (roles) with optional attributes | Simple to reason about | Role explosion; use groups and scopes; add ABAC rules where needed |
| Deny by default | Safe | More setup work |

---

## 9. What breaks and how to fix it

| Failure | Effect | Fix |
|---|---|---|
| IdP down | Nobody can log in | Existing tokens still work until expiry (local validation); IdP HA, multi-zone; cache JWKS; longer-lived session for already logged-in users within limits |
| JWKS key rotation mishap | All tokens rejected | Publish new key before use; support multiple keys; cache with refresh on unknown `kid` |
| Policy service down | Cannot administer; decisions? | Services keep last snapshot (fail static); alert; admin path degraded only |
| Policy cache stale / event lost | Wrong decisions for a while | Version numbers on tokens/requests; periodic full resync; poll as backup |
| Stolen token | Abuse until expiry | Short life; deny-list; anomaly alerts; revoke refresh token |
| Privilege escalation via role changes | Security incident | Maker-checker, audit alerts, least privilege, review of role definitions |
| Maker approves own request | Control bypass | Enforce maker != checker in code and DB; test it; log |
| Gateway overloaded | Outage at the entrance | Autoscale, rate limits, load shedding, zone redundancy |
| Confused deputy | Service acts beyond user's rights | Propagate user identity; check permissions at the service too |
| Token too large (many roles) | Header size errors | Put only coarse roles/groups in token; fetch the rest locally |
| Clock skew | Valid tokens rejected | Small leeway (for example 60 s) on exp/nbf; NTP |
| Audit log tampering | Loss of trust | Append-only store, restricted access, hashes/chaining, forward to separate system |

---

## 10. Questions the interviewer asks next

**Q1. Authentication vs authorization?**
A. Authentication proves who you are (login, token). Authorization decides what you may do (roles, permissions). The gateway does the first, and both the gateway and each service enforce the second.

**Q2. How does OIDC login work?**
A. Redirect to the IdP, user logs in there, IdP returns a one-time code to the app, the app exchanges the code at the IdP's token endpoint for ID, access and refresh tokens. Services only validate tokens; they never touch passwords.

**Q3. How can the gateway validate tokens without calling the IdP every time?**
A. The JWT is signed. The gateway verifies the signature using the IdP's public key (from the JWKS endpoint, cached), and checks expiry, issuer and audience.

**Q4. A user's role is removed. When does it stop working?**
A. For normal paths, when the policy event reaches the service caches (seconds) and any token claims expire (minutes). For urgent cases, add the user to the deny-list at the gateway for immediate effect and revoke refresh tokens. It is a deliberate consistency trade-off.

**Q5. Where do you enforce authorization: gateway or service?**
A. Both. Gateway: coarse checks (is the token valid, may this client call this route). Service: fine-grained checks (may this user approve this specific payment), because only the service knows the resource. Defence in depth.

**Q6. RBAC or ABAC?**
A. RBAC as the base: easy to explain and audit. Add attribute rules where needed (amount limits, tenant, time of day), keeping them in the same policy store.

**Q7. How does maker-checker work technically?**
A. A change request record in `pending`; a checker with the approve permission, different from the maker, approves; the apply step revalidates and executes in a transaction with audit and a policy version bump; requests expire; notifications go out.

**Q8. What about service-to-service calls?**
A. Mutual TLS or client-credentials tokens for service identity, with policies saying which service may call which endpoint, plus propagation of the end-user identity.

**Q9. How do you make the shared auth library safe to change?**
A. Semantic versioning, backward-compatible defaults, contract tests across services, a staged rollout, and a way to push urgent security fixes (dependency bot, deadline policy).

**Q10. How do you avoid the gateway becoming a bottleneck or single point of failure?**
A. Stateless nodes, horizontal scaling behind a load balancer across zones, light work only (no business logic), cached keys and policies, and health-checked autoscaling.

**Q11. What would you audit?**
A. All admin changes with before/after; approvals; authentication failures; denied decisions at a sampled rate; token issuance for privileged roles. Stored append-only with retention rules.

---

## 11. Say it out loud (6 sentences)

1. "An API gateway is the single entrance that routes, rate-limits and authenticates requests, while an authorization system decides what each caller may do."
2. "Policy data is tiny and changes rarely but is read on every request, so I separate the slow, audited admin path from the fast enforcement path."
3. "Users log in through an OIDC identity provider; access tokens are short-lived signed JWTs that the gateway verifies locally using cached public keys."
4. "A shared auth library in every service caches the policy snapshot in memory, refreshed by policy-change events with a version number, and sensitive actions can call the authorization service for the freshest answer."
5. "Revocation is a trade-off: short token life and event-driven cache refresh for normal cases, plus a deny-list and refresh-token revocation for emergencies."
6. "Sensitive changes go through maker-checker, where a different authorised user approves and the apply step runs in one transaction with an immutable audit entry."
