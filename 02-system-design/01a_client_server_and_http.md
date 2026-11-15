# 01a. Client, Server and HTTP

Everything in system design starts here. Learn this one well.

---

## 1. Client and server

- **Client** = the one who asks. Your phone app, your browser, another program.
- **Server** = the one who answers. A computer that runs a program all day, waiting for requests.

**Analogy: a restaurant.** The guest (client) tells the waiter what he wants. The kitchen (server) makes it and sends it back. The guest never goes into the kitchen.

```
 +--------+   1. request ("give me page X")    +--------+
 | Client | ---------------------------------> | Server |
 | (phone)| <--------------------------------- |        |
 +--------+   2. response (the page)           +--------+
```

One server can serve many clients. A client can talk to many servers.

---

## 2. IP address, port, DNS (short version)

- **IP address** = the house number of a computer. Example `142.250.1.1`.
- **Port** = the door number in that house. Web uses port 80 (HTTP) and 443 (HTTPS).
- **DNS** = the phone book that turns `google.com` into an IP address. See `01b`.

---

## 3. What is HTTP?

**HTTP** is the language a client and server use on the web. It is a set of simple rules: "send me a message in this shape, I will reply in that shape."

- **HTTPS** = HTTP with a lock (encryption). Nobody in the middle can read the message. Always use it.

### A request has

```
POST /v1/orders HTTP/1.1            <- method + path
Host: api.shop.com                  <- headers (extra info)
Authorization: Bearer abc123
Content-Type: application/json

{"item": "book", "qty": 2}          <- body (the data)
```

### A response has

```
HTTP/1.1 201 Created                <- status code
Content-Type: application/json

{"order_id": "o_789"}               <- body
```

### Methods (verbs)

| Method | Meaning | Daily-life example | Safe to repeat? |
|---|---|---|---|
| GET | Read something | Read the menu | Yes |
| POST | Create something | Place a new order | **No** (may create two) |
| PUT | Replace something fully | Rewrite my whole order | Yes |
| PATCH | Change a part | Change only the quantity | Usually |
| DELETE | Remove | Cancel the order | Yes |

"Safe to repeat" has a fancy name: **idempotent** (see `03_reliability_patterns.md`). It matters a lot when the network fails and the client retries.

### Status codes (learn the groups)

| Code | Meaning | Example |
|---|---|---|
| 2xx | Success | 200 OK, 201 Created, 204 No Content |
| 3xx | Go somewhere else | 301 moved forever, 302 temporary redirect |
| 4xx | **Client** made a mistake | 400 bad request, 401 not logged in, 403 not allowed, 404 not found, 409 conflict, 429 too many requests |
| 5xx | **Server** has a problem | 500 error, 502 bad gateway, 503 unavailable, 504 gateway timeout |

Rule: 4xx = do not retry blindly (your request is wrong). 5xx and 429 = may retry later with a wait.

---

## 4. Stateless vs stateful servers

- **Stateful**: the server remembers you between requests (it keeps your session in its own memory). If that server dies, you lose your session. Also, you must always return to the same server.
- **Stateless**: the server remembers nothing. Every request carries everything needed (for example a token). The state lives in a database or cache outside.

**Analogy:** A stateless waiter reads your table card each time. Any waiter can serve you. A stateful waiter "remembers" you; if he goes home, you are lost.

**Why stateless is good:** you can add 10 more identical servers and put a load balancer in front (see `01c`). Interviewers love this sentence: **"I keep the web servers stateless so I can scale them horizontally."**

---

## 5. Scaling: up or out

- **Vertical scaling (scale up)** = buy a bigger machine (more CPU, more RAM). Simple, but it has a limit and costs a lot at the top. Also one machine = one point of failure.
- **Horizontal scaling (scale out)** = add more machines. Cheaper, no real limit, but you need a load balancer and a design that works across machines.

```
Scale up:     [ small ] ---> [ BIG BIG BIG ]
Scale out:    [ s ] ---> [ s ][ s ][ s ][ s ]
```

---

## 6. Ways to talk: REST, gRPC, WebSocket, polling

| Style | What it is | Use it for |
|---|---|---|
| **REST** (HTTP + JSON) | Resources with URLs: `GET /users/42` | Most public APIs. Easy to debug |
| **gRPC** | Fast binary calls between services, with a strict contract file | Service-to-service inside your company |
| **GraphQL** | Client asks exactly the fields it wants | Mobile apps with varied screens |
| **Polling** | Client asks again and again: "anything new?" | Simple, wasteful |
| **Long polling** | Client asks; server holds the call open until there is news | Better than polling, still HTTP |
| **WebSocket** | One long-lived two-way connection | Chat, live scores, games |
| **Server-Sent Events (SSE)** | Server pushes a stream to the client (one way) | Live feeds, progress bars |
| **Webhook** | Server calls **your** URL when something happens | Payment done, build finished |

**Analogy:** Polling = you call the shop every 5 minutes: "is my parcel ready?" Webhook = the shop calls you when it is ready.

---

## 7. API design basics (you will do this in Step 3 of every design)

1. **Use nouns in URLs, verbs in methods.** `POST /orders`, not `/createOrder`.
2. **Version your API.** `/v1/...`. You can change v2 later without breaking old clients.
3. **Pagination for lists.** Never return 10 million rows. Use `?limit=20&cursor=abc`. (Cursor is better than page numbers when data changes.)
4. **Idempotency for creates.** Client sends an `Idempotency-Key` header so a retry does not create two orders. (See `03`.)
5. **Clear errors.** Status code + a short machine-readable code + a human message.
6. **Authentication** (who are you?) and **authorization** (what may you do?). Different things. (See `21`.)
7. **Rate limits.** Return 429 with a `Retry-After` header. (See `11`.)

---

## 8. A request's journey (the "what happens when you open a website" answer)

A very common question. Say it in order:

1. Browser asks DNS: "IP of `shop.com`?" (cache is checked first).
2. Browser opens a TCP connection to that IP, then does a TLS handshake (the lock).
3. Browser sends the HTTP request.
4. A CDN or load balancer receives it and picks a healthy server.
5. The web server checks login (token), maybe asks a cache.
6. If not in cache, it asks the database.
7. It builds the response and sends it back.
8. Browser draws the page; asks for images and scripts (often from a CDN).

```
Browser -> DNS -> CDN -> Load balancer -> Web server -> Cache -> Database
```

---

## 9. Where this shows in your own work

Your OIDC gateway and access-control service are a client-server system: apps are clients, the gateway checks a token and forwards to a stateless backend. Your provisioner calls Kubernetes APIs over HTTPS too. You already use these ideas daily; here you only give them names.

---

## 10. Quick check (answer out loud)

1. Why is a stateless server easier to scale?
2. Which HTTP methods are safe to repeat?
3. Is 429 a client or server problem? What should the client do?
4. Polling vs webhook: which is better for "payment finished"?
