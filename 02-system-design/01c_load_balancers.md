# 01c. Load Balancers

---

## 1. What is a load balancer?

A **load balancer (LB)** stands in front of many servers. It receives every request and sends each one to one of the servers.

**Analogy: the host at a restaurant.** Ten waiters work in the hall. The host at the door sends each new family to a waiter who is free. If a waiter is sick, the host stops sending guests to him.

```
             +-------------+        +-----------+
Clients ---> | Load        | -----> | Server A  |
             | balancer    | -----> | Server B  |
             |             | -----> | Server C  |
             +-------------+        +-----------+
```

### Why we need it

1. **Spread the work** so no server is overloaded.
2. **High availability**: if one server dies, the others keep serving.
3. **Easy scaling**: add or remove servers without clients knowing.
4. **One public address** for many private servers.
5. **Extras**: HTTPS termination (decrypt once at the LB), rate limiting, simple security.

It requires servers to be **stateless** (see `01a`), or to share state elsewhere.

---

## 2. Layer 4 vs Layer 7

Networks have layers. You only need two:

| Type | Looks at | Speed | Smart routing? | Example use |
|---|---|---|---|---|
| **L4** (transport) | IP address and port only | Very fast | No | Raw TCP traffic, databases, huge throughput |
| **L7** (application) | The HTTP request: URL, headers, cookies | A bit slower | **Yes** | `/api/*` to API servers, `/images/*` to image servers |

**Analogy:** L4 is a post-office sorter who reads only the city on the envelope. L7 opens the envelope and reads the letter to decide the best desk.

---

## 3. How does the LB pick a server? (algorithms)

| Algorithm | Idea | Good when | Weak when |
|---|---|---|---|
| **Round robin** | A, B, C, A, B, C... | Servers equal, requests similar | Requests differ a lot in cost |
| **Weighted round robin** | Stronger server gets more | Mixed machine sizes | Still ignores live load |
| **Least connections** | Send to the server with fewest open connections | Long-lived or uneven requests | Needs tracking |
| **Least response time** | Send to the fastest server | Latency-sensitive | More tracking |
| **IP hash** | Same client IP -> same server | Need "sticky" behaviour | Uneven if many users share one IP |
| **Consistent hashing** | Key (like user id) -> same server, and few keys move when servers change | Caches, sharded stores | More complex |

### Sticky sessions

"Sticky" means the same user always returns to the same server. Used when the server keeps session data in memory. It is a bandage. The better fix is stateless servers with shared session store.

---

## 4. Health checks

The LB must know which servers are alive.

- **Active check**: LB calls `GET /health` on each server every few seconds. Two or three failures in a row = remove from rotation.
- **Passive check**: LB watches real traffic. Too many errors from a server = remove it.

Good health endpoint: checks that the app can really work (can it reach the database?), but is cheap. A bad health check that is too strict can remove **all** servers at once during a short database blip. Know this trade-off. (More in `03`.)

**Draining**: before removing a server for a deploy, stop new requests but let current ones finish. In Kubernetes this is what readiness probes and graceful shutdown do - you know this from your own work.

---

## 5. Who load-balances the load balancer?

A single LB is a single point of failure. Solutions:

- **Two LBs, active + standby** with a shared virtual IP (if the active one dies, standby takes over).
- **Many LBs** behind DNS or an **anycast** address.
- **Cloud managed LB** (the provider runs many LB instances for you).

```
DNS -> [LB1][LB2] (active/active or active/passive) -> app servers
```

---

## 6. Types by place in the design

- **Edge / global LB** (or DNS): picks a region.
- **Regional LB**: picks a data centre or zone.
- **Internal LB / service mesh**: between your own microservices.
- **Client-side LB**: the client library knows all server addresses and picks one (used in gRPC and service discovery).

In Kubernetes: a `Service` gives a stable address and spreads traffic over pods; an `Ingress` is an L7 load balancer at the entrance. Your OIDC gateway sits at this kind of entrance.

---

## 7. Common interview questions

**Q: What if the LB gets too much traffic?**
A: Scale the LB layer horizontally (many LBs behind DNS/anycast), use L4 LBs for raw throughput, and terminate TLS on dedicated nodes if CPU is the problem.

**Q: How do you do zero-downtime deploys?**
A: Rolling update: start new servers, wait until health checks pass, send traffic to them, drain old ones. Or blue-green: two full environments, switch traffic at the LB.

**Q: Round robin vs least connections?**
A: Round robin is simple and fine when requests cost about the same. Least connections is better when some requests take much longer.

---

## Quick check

1. Why must web servers be stateless behind a load balancer?
2. What can an L7 load balancer do that L4 cannot?
3. What is draining?
4. Why can a too-strict health check cause an outage?
