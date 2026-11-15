# 02. Networking: TCP, DNS, TLS, NAT

Legend: `[REAL]` = I ran it on this Mac (macOS 26) on 2026-11-15. `[SAMPLE]` = typical output written to show the shape, numbers made up, not run here.
Mac vs Linux: `ss` and `ip` are Linux tools. On this Mac I used `netstat` and `lsof`, which show the same facts.

---

## 1. What it is (plain words + analogy)

Networking is how two programs on different machines talk. Think of the **post office** and the **phone**:

- **IP address** = the street address of a machine (`93.184.x.x`).
- **Port** = the apartment number inside the building (443 = web over TLS, 22 = SSH, 53 = DNS).
- **TCP** = a **phone call**. You dial, the other side picks up, you both confirm, then you talk. Nothing is lost; if a word is missed it is repeated, and words arrive in order.
- **UDP** = **postcards**. You send them and hope. No call setup, no resend, no order. Very fast and light.
- **DNS** = the **phone book**: it turns `example.com` into an IP address.
- **TLS** = a **sealed, signed envelope**: nobody on the road can read or change the letter, and you know who signed it.
- **NAT** = the **office reception desk**: many people inside share one public phone number; reception remembers who called out so replies go to the right desk.

## 2. Why it matters in interviews

"A request is slow / fails / times out. Where do you look?" is the classic platform and SRE question. You must know the steps a request goes through (DNS, TCP connect, TLS, send, wait, read) and which tool shows each step. Typical follow-ups: what is TIME_WAIT, why do we see many CLOSE_WAIT, what is the difference between connect timeout and read timeout, what does a load balancer idle timeout do. 2026 prep guides also list networking and DNS inside Kubernetes (services, CoreDNS, NetworkPolicy) as scenario topics.

## 3. How it works, step by step

### 3.1 What happens when you run `curl https://example.com`

```
 1. DNS lookup        name -> IP                         (UDP port 53 usually)
 2. TCP handshake     SYN -> SYN/ACK -> ACK              (1 round trip)
 3. TLS handshake     hellos, certificate check, keys    (1 round trip for TLS 1.3)
 4. HTTP request      GET / ...
 5. wait              server thinks                      (time to first byte)
 6. HTTP response     headers + body
 7. close             FIN / ACK ...
```

`[REAL]` `curl` can print the time of each step. The numbers are **cumulative** (each one includes the earlier steps):

```
$ curl -s -o /dev/null -w "dns=%{time_namelookup} connect=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n" https://example.com
dns=0.061493 connect=0.067212 tls=0.080103 ttfb=0.091943 total=0.092069
```
Read it like this:
- DNS took about 61 ms.
- TCP connect finished at 67 ms, so the handshake itself cost about 6 ms (a short trip here, because the server is close).
- TLS finished at 80 ms, so TLS cost about 13 ms.
- First byte at 92 ms, so the server waited about 12 ms.

If `dns` is big, suspect DNS. If `connect - dns` is big, suspect the network path or a full server queue. If `tls - connect` is big, suspect certificates or slow crypto. If `ttfb - tls` is big, the application is slow.

### 3.2 The TCP handshake (RFC 9293)

TCP sets up a connection with a **three-way handshake**:

```
 Client                         Server
   |  ---- SYN (seq=100) ---->    |   "I want to talk. My counter starts at 100."
   |  <--- SYN+ACK (seq=300, ack=101) --- |   "OK. Mine starts at 300. I got your 100."
   |  ---- ACK (ack=301) ---->    |   "Got it. Go."
   |         ESTABLISHED          |
```
(The numbers are the RFC's own example: A sends SYN 100, B answers with SYN 300 and ACK 101.)

SYN = "synchronize", ACK = "acknowledge". The cost is one **round trip time (RTT)** before you can send data. That is why connection reuse (keep-alive, connection pools, HTTP/2) matters.

### 3.3 TCP states

The RFC lists these states. The ones you must know:

| State | Meaning (simple) |
|---|---|
| LISTEN | server waiting for new connections |
| SYN-SENT | client sent SYN, waiting for answer |
| SYN-RECEIVED | server got SYN, sent SYN+ACK, waiting for the final ACK |
| ESTABLISHED | connection open, data flows |
| FIN-WAIT-1 / FIN-WAIT-2 | I started closing, waiting for the other side |
| CLOSE-WAIT | the other side closed; **my application has not closed yet** |
| LAST-ACK | I closed after the other side; waiting for the last ACK |
| TIME-WAIT | I closed first; waiting a while before the connection can be fully forgotten |

Closing uses FIN packets:

```
 Active closer (client)                 Passive closer (server)
   | ---- FIN ---->                          |  client: FIN-WAIT-1
   | <--- ACK -----                          |  client: FIN-WAIT-2   server: CLOSE-WAIT
   |        (server app still has to call close())
   | <--- FIN -----                          |  server: LAST-ACK
   | ---- ACK ---->                          |  server: CLOSED
   |  client: TIME-WAIT (waits 2 x MSL)      |
```

**TIME_WAIT**: the side that closes first stays in TIME-WAIT. The RFC says it "MUST linger in the TIME-WAIT state for a time 2xMSL" (MSL = Maximum Segment Lifetime; the RFC takes MSL as 2 minutes). Two reasons: (1) make sure the other side got the last ACK; (2) stop late packets from an old connection being mixed into a new one on the same address/port pair. TIME_WAIT is **normal**. Many TIME_WAIT sockets on a busy client or proxy only matter when you run out of free local ports (about 28,000 by default on Linux, `net.ipv4.ip_local_port_range`; check yours). Linux's timeout is commonly said to be 60 seconds, not 4 minutes (not verified here).

**CLOSE_WAIT** is different and is a **bug signal**: the other side closed, but your program never called `close()`. A growing pile of CLOSE_WAIT = a socket leak in the application.

`[REAL]` I started a listener on localhost port 9099, connected, closed. The states, in order:
```
tcp4  0  0  127.0.0.1.9099      *.*               LISTEN
tcp4  0  0  127.0.0.1.9099      127.0.0.1.50107   ESTABLISHED     <-- server side of connection
tcp4  0  0  127.0.0.1.50107     127.0.0.1.9099    ESTABLISHED     <-- client side (random port 50107)
... a few seconds later, after the client closed:
tcp4  0  0  127.0.0.1.50107     127.0.0.1.9099    TIME_WAIT       <-- the closer waits
```

### 3.4 Timeouts (three different ones)

1. **Connect timeout**: how long to wait for the handshake. If the target drops packets silently (firewall), you wait the full timeout. If nothing listens, you get an instant "connection refused" (a RST packet).
2. **Read (response) timeout**: how long to wait for data after you sent the request.
3. **Idle timeout** in middleboxes (load balancers, NAT, proxies): a quiet connection is cut after N seconds. The next write fails with "connection reset". Fix with keep-alive pings shorter than the idle timeout, or reconnect on error.

Rule from the AWS Builders' Library: set a timeout on every remote call, "based on downstream latency percentiles" (their idea: look at the p99.9 of the dependency, then add margin). Too high wastes resources; too low causes extra retries.

`[REAL]` three failure shapes and their curl exit codes:
```
$ curl -sS -m 3 http://127.0.0.1:1
curl: (7) Failed to connect to 127.0.0.1 port 1 after 0 ms: Couldn't connect to server     <-- refused, instant
$ curl -sS -m 2 http://10.255.255.1
curl: (28) Connection timed out after 2002 milliseconds                                    <-- silent drop, waits full timeout
$ curl -sS https://nonexistent-zzz-12345.invalid
curl: (6) Could not resolve host: nonexistent-zzz-12345.invalid                            <-- DNS failure
```
Memory trick: 6 = DNS, 7 = connect refused, 28 = timeout.

### 3.5 DNS lookup and caching

DNS is a tree. Your computer asks a **recursive resolver** (your router, your company DNS, or 8.8.8.8). The resolver does the work:

```
 you ──> resolver ──> root server  ("who knows .com?")      -> list of .com servers
                  ──> .com TLD server ("who knows example.com?") -> its name servers
                  ──> example.com's authoritative name server ("what is the A record?") -> 104.20.23.154
 resolver caches the answer for TTL seconds, then answers you
```

- **Record types**: `A` (name -> IPv4), `AAAA` (IPv6), `CNAME` (alias to another name), `NS` (which servers are in charge), `MX` (mail), `TXT` (text, used for verification).
- **TTL** (time to live): how many seconds a cache may keep the answer. After that it must ask again.
- **Caching happens at many layers**: browser, OS, your app/library, the resolver. This is why "I changed the DNS record but some users still see the old IP" happens: wait for the TTL.
- A **short TTL** gives fast changes but more DNS load. A **long TTL** is cheaper but slow to change. Lower the TTL *before* a planned migration.
- Failure answers: `NXDOMAIN` (name does not exist), `SERVFAIL` (the resolver could not get an answer).
- In Kubernetes, pods use **CoreDNS** inside the cluster. A service name like `web.default.svc.cluster.local` resolves to the Service's cluster IP. Slow or failing DNS inside a cluster is a very common cause of "random timeouts" (a favorite scenario).

`[REAL]` the TTL counting down (it is a cache, so the number drops each second):
```
$ dig +noall +answer example.com
example.com.   217   IN   A   172.66.147.243      <-- first call: TTL 217 seconds left
example.com.   217   IN   A   104.20.23.154
(some seconds later)
example.com.   191   IN   A   172.66.147.243      <-- same cache entry, TTL smaller
```
`[REAL]` the delegation chain (who is in charge at each level):
```
$ dig +short NS com. | head -3
k.gtld-servers.net.
h.gtld-servers.net.
d.gtld-servers.net.
$ dig +short NS example.com | head -3
hera.ns.cloudflare.com.
elliott.ns.cloudflare.com.
```
`[REAL]` the `dig` stats line: `;; Query time: 59 msec` and `;; SERVER: ...#53(...)` tell you which resolver answered and how fast.

### 3.6 TLS handshake cost

TLS gives three things: **authentication** (the server proves who it is with a certificate), **key exchange** (both sides create a shared secret), and **protection** of data. RFC 8446 says the server is always authenticated and the client is optional.

- TLS 1.3 needs **one round trip** for a full handshake (the RFC calls it the "1-RTT handshake"). TLS 1.2 needed two.
- With a saved session key, TLS 1.3 can do **0-RTT**: the client sends data in the first flight. Warning from the RFC: "There are no guarantees of non-replay between connections", so 0-RTT is only safe for requests that can be repeated safely (idempotent, see file 09).
- Cost = network round trips + some CPU for crypto + certificate checks. The fix for repeated cost is **connection reuse** and **session resumption**.
- HTTP/2 lets many requests share one TLS connection.

`[REAL]` `openssl` shows what was negotiated:
```
$ openssl s_client -connect example.com:443 -tls1_3 -brief </dev/null
CONNECTION ESTABLISHED
Protocol version: TLSv1.3
Ciphersuite: TLS_AES_256_GCM_SHA384
Peer certificate: CN=example.com
Signature type: ecdsa_secp256r1_sha256
Verification: OK
```
`[REAL]` `curl -v` says `* ALPN: server accepted h2` and `< HTTP/2 200` (it spoke HTTP/2 over TLS 1.3).

Common TLS failures: expired certificate, wrong host name (the name in the cert does not match), missing intermediate certificate, clock wrong on the client, client does not trust the CA.

### 3.7 NAT

**NAT** (network address translation): many private machines (10.x, 192.168.x, pod IPs) share one or a few public IPs. The NAT device **rewrites** the source address and port of outgoing packets and keeps a table to rewrite replies back.

```
 pod 10.0.1.5:40001 ──> [NAT]  src becomes 52.1.2.3:61001 ──> internet server
 pod 10.0.1.5:40001 <── [NAT]  dst 52.1.2.3:61001 -> back to 10.0.1.5:40001
                          table: (10.0.1.5:40001) <-> (52.1.2.3:61001)
```

Facts that come up:
- The table entry has a timeout. Idle connections lose their entry; the next packet gets a reset.
- Each outgoing connection to the same destination needs its own public source port. With few public IPs you can run out of ports (**SNAT port exhaustion**): symptom is random connect timeouts under high traffic to the same destination. Fix: more IPs on the NAT, connection reuse, fewer short-lived connections. (This is well known on cloud NAT gateways and AKS; I did not verify the exact limits, so check your cloud's doc.)
- Inbound needs port forwarding or a load balancer. That is why servers behind NAT are not reachable from the internet by default.

### 3.8 UDP vs TCP

| | TCP | UDP |
|---|---|---|
| Setup | handshake | none |
| Reliable and in order | yes | no |
| Speed / overhead | more | less |
| Use | web, SSH, databases | DNS queries, video calls, games, QUIC (HTTP/3 runs over UDP) |

DNS uses UDP first and falls back to TCP when the answer is too big.

## 4. Commands to try

```bash
# names
dig example.com                 # full answer with stats
dig +short example.com          # only the IPs
dig @8.8.8.8 example.com        # ask a specific resolver
dig +trace example.com          # walk root -> TLD -> authoritative
dig +noall +answer example.com  # only the answer lines (shows TTL)
nslookup example.com            # older tool, works everywhere

# connect and time
curl -v https://example.com                   # shows each step
curl -sS -o /dev/null -w "%{http_code} %{time_total}s\n" https://example.com
curl --connect-timeout 3 -m 10 https://example.com   # connect timeout 3s, total 10s
nc -zv host 443                 # "can I open a TCP connection to port 443?"
openssl s_client -connect host:443 -servername host   # inspect the certificate

# sockets on this machine (Linux)
ss -tan                         # all TCP sockets with state
ss -tanp state established      # with process (needs privileges for others' processes)
ss -ltnp                        # listening sockets + process
ss -s                           # summary counts (look at timewait)
ip addr   ip route   ip neigh   # addresses, routes, ARP table

# sockets on Mac
netstat -an -p tcp | grep -E "LISTEN|TIME_WAIT"
lsof -nP -iTCP -sTCP:LISTEN

# packets (needs root; do not run on production without a filter)
sudo tcpdump -i any -nn port 53                 # DNS only
sudo tcpdump -i any -nn host 10.0.0.5 and port 443 -c 20
sudo tcpdump -i any -nn 'tcp[tcpflags] & (tcp-syn) != 0'   # only SYN packets
```

`[SAMPLE]` `ss -s` on Linux:
```
Total: 812
TCP:   640 (estab 410, closed 180, orphaned 2, timewait 175)
```
`[SAMPLE]` `tcpdump` DNS lookup (Linux, the format is `time IP src > dst: id type? name`):
```
21:50:01.123456 IP 10.0.0.5.53211 > 10.0.0.2.53: 4821+ A? example.com. (29)
21:50:01.140100 IP 10.0.0.2.53 > 10.0.0.5.53211: 4821 2/0/0 A 104.20.23.154, A 172.66.147.243 (61)
```
`[SAMPLE]` SYN with no answer (what a silent firewall drop looks like; you see SYN again and again, never SYN-ACK):
```
IP 10.0.0.5.40422 > 10.9.9.9.443: Flags [S], seq 1, win 64240, length 0
IP 10.0.0.5.40422 > 10.9.9.9.443: Flags [S], seq 1, win 64240, length 0   (retransmit after ~1 s)
```
(Flags: `[S]` SYN, `[S.]` SYN-ACK, `[.]` ACK, `[F.]` FIN, `[R]` RST.) I did not run tcpdump here because it needs root.

## 5. Common mistakes

1. Blaming "the network" before checking DNS. Always time the steps (`curl -w`).
2. Panicking at many TIME_WAIT sockets. They are normal; only port exhaustion hurts.
3. Ignoring CLOSE_WAIT. That one is an application bug.
4. Same timeout everywhere, or no timeout at all (default "wait forever" in many libraries).
5. Retrying without backoff and jitter (see file 09). It turns a small outage into a big one.
6. Forgetting DNS caching when changing records or moving to a new IP.
7. Opening a new TCP+TLS connection for every request instead of reusing connections.
8. Assuming `ping` works means the service works. Ping uses ICMP, not your port. Use `nc -zv` or `curl`.

## 6. Eight interview questions with answers

**Q1. Explain the TCP three-way handshake. Why three steps?**
Client sends SYN with its starting sequence number. Server replies SYN+ACK with its own number and acknowledges the client's. Client sends ACK. Both sides now know the other can send and receive and have agreed on starting numbers. The server's SYN and ACK travel together, so it is three messages instead of four.

**Q2. What is TIME_WAIT and should I worry about it?**
The side that closes first waits 2 x MSL before forgetting the connection. It makes sure the last ACK arrived and keeps late packets of the old connection away from a new one. It is normal. Worry only if you run out of local ports (clients or proxies making huge numbers of short connections). Fix by reusing connections (keep-alive, pools), not by tweaking kernel flags first.

**Q3. Many sockets are in CLOSE_WAIT. What does it mean?**
The remote side closed the connection but our application never called `close()`. It is a leak in our code (for example an HTTP client that never closes response bodies). Find the process with `ss -tanp state close-wait`, then fix the code.

**Q4. Walk me through what happens when I type a URL and press Enter.**
Browser checks cache, then the OS resolver asks DNS (recursive resolver -> root -> TLD -> authoritative) and caches the answer for the TTL. It opens a TCP connection (handshake), then TLS (certificate check, key exchange, one round trip in TLS 1.3), then sends an HTTP request. Server may sit behind a load balancer and CDN. The response comes back, the browser renders and may open more connections.

**Q5. A service is "slow sometimes". How do you tell if it is DNS, TCP, TLS, or the app?**
Time each step: `curl -w` with `time_namelookup`, `time_connect`, `time_appconnect`, `time_starttransfer`. The big jump shows the slow step. Then go deeper with the right tool: `dig` for DNS, `tcpdump`/`ss` for TCP retransmits, `openssl s_client` for TLS, app metrics and traces for the application.

**Q6. Connection refused vs connection timed out?**
Refused: the machine answered with a RST, so the host is reachable but nothing listens on that port (or a firewall rejects actively). It fails instantly. Timed out: no answer at all, usually a firewall dropping packets, a wrong route, or a dead host. It fails only after the full timeout.

**Q7. What is NAT and what problem can it cause at scale?**
NAT rewrites source IP and port so many private hosts share a public IP. It keeps a table. Problems: entries expire for idle connections (surprise resets), and port exhaustion when many connections go to the same destination from one public IP (random connect timeouts). Fixes: more public IPs, connection reuse, keep-alives, fewer short connections.

**Q8. Why is TLS 1.3 faster to set up than TLS 1.2, and what is the risk of 0-RTT?**
A full TLS 1.3 handshake takes one round trip (TLS 1.2 took two). With a saved key, 0-RTT lets the client send data in the first message, saving another trip. The risk: an attacker can replay that first message, so only idempotent requests (safe to repeat) should use it.

## 7. Self-quiz (answers at the end)

1. In a `curl -w` output, `connect=0.067` and `dns=0.061`. How long did the TCP handshake take?
2. Which side stays in TIME_WAIT?
3. What does `curl: (28)` tell you, and how is it different from `(7)`?
4. You change an A record. Some users still hit the old IP for 10 minutes. Why?
5. Name one reason a NAT gateway causes random connect timeouts.

**Answers**
1. About 6 ms (0.067 - 0.061), because curl's numbers are cumulative.
2. The side that closes first (the active closer).
3. 28 = timeout (no answer within the limit, often a silent drop). 7 = refused or could not connect immediately (host answered "no" or no route).
4. DNS caching. Resolvers and clients keep the old answer until its TTL runs out.
5. Port exhaustion (too many connections to one destination share too few public IP:port pairs), or idle NAT table entries expiring.

## 8. Sources

- RFC 9293 (TCP): handshake, states, TIME-WAIT: https://www.rfc-editor.org/rfc/rfc9293.html
- RFC 8446 (TLS 1.3): 1-RTT, 0-RTT replay warning: https://www.rfc-editor.org/rfc/rfc8446.html
- AWS Builders' Library, timeouts, retries, backoff with jitter: https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter

Not verified from a source (general knowledge): TLS 1.2 needing two round trips; Linux TIME_WAIT being 60 s; Linux ephemeral port range about 28,000; SNAT exhaustion details and limits per cloud; DNS record type list; DNS using UDP then TCP for large answers; curl exit codes 6, 7, 28 (I saw them on this Mac, they are documented in the curl man page); CoreDNS being the default DNS in Kubernetes; tcpdump flag notation (documented in the tcpdump man page).
