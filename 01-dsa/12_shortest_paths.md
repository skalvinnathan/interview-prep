# Lesson 12: Shortest Paths (Dijkstra in plain words)

All code is Python 3.9. Every code block in this file was run with `python3` (3.9.6) before it was written here.

You should have read lesson 09 (heaps) and lesson 10 (BFS) first.

---

## Words you need first

- **Weighted edge**: a road with a **cost** on it (distance, time, price). Cost is also called **weight**.
- **Shortest path**: the path with the **smallest total cost**. It is not always the path with the fewest edges.
- **Relax an edge**: "I found a cheaper way to get to this place. Update the best known cost." (Why "relax"? It is just the name.)
- **Source**: the place where you start.
- **infinity** (`float("inf")`): "I have not found any way yet". Any real cost is smaller than infinity.
- **Greedy**: always do the best-looking move right now. Dijkstra is greedy.

---

## 1. What is this?

BFS (lesson 10) finds the path with the fewest edges. But what if roads have different lengths?

```
          10
   A ------------- C
   |               |
   1               1
   |               |
   B ------1------ D
```

(Edges: A-C cost 10, A-B cost 1, B-D cost 1, D-C cost 1.)

Going `A -> C` directly costs 10. Going `A -> B -> D -> C` has 3 edges but costs `1 + 1 + 1 = 3`. BFS would pick the direct road (1 edge). The truth is the 3-edge road, because it is cheaper. We need **Dijkstra**.

**Analogy: a fire spreading through a forest, where some paths burn slowly.**
The fire starts at the source at time 0. It reaches each place at some time. Dijkstra keeps asking: "Which place will catch fire **next**?" It is always the place with the smallest arrival time among the places the fire can see. That place's time is now **final**. Nobody can reach it faster, because every other candidate is later or equal, and costs are never negative. Then the fire spreads from that place, and we repeat.

How do we always get "the place with the smallest time"? With a **min-heap** (lesson 09).

**Dijkstra in 5 lines of plain words:**
1. Put `(0, source)` in the heap. Set `dist[source] = 0`.
2. Pop the cheapest `(cost, node)`.
3. If this cost is bigger than `dist[node]`, it is an old, stale entry. Skip it.
4. For each neighbour: `new_cost = cost + edge_weight`. If it is smaller than `dist[neighbour]`, update it and push `(new_cost, neighbour)`.
5. Repeat until the heap is empty.

**Big rule: Dijkstra only works when all weights are zero or positive.** With a negative edge, a "final" answer might not be final. Then use **Bellman-Ford** (see 5.2).

---

## 2. When do I use it?

| Words in the problem | Idea |
|---|---|
| "**shortest / cheapest / fastest** path" and the edges have **different** costs | Dijkstra |
| "minimum **time** for a signal to reach all nodes" | Dijkstra, then take the max distance |
| "path with minimum **effort / maximum probability / minimum largest step**" | Dijkstra with a different meaning of "cost" |
| "at most **K stops / edges**" | Bellman-Ford with K+1 rounds (or Dijkstra with an extra state) |
| All edges cost the same (or the grid has equal steps) | Use plain BFS instead. It is simpler and faster |
| There are **negative** edges | Bellman-Ford |

---

## 3. Trace of a tiny example

Graph (arrow: `from -> to`, number is the cost):

```
0 -> 1 cost 4
0 -> 2 cost 1
2 -> 1 cost 2
1 -> 3 cost 1
2 -> 3 cost 5
```

```
        4
   0 -------> 1 ---1---> 3
   |          ^           ^
   1          2           5
   v          |           |
   2 ---------+-----------+
```

Goal: the cheapest cost from node 0 to every node. `dist` starts as `{0: 0}`, others infinity. The heap holds `(cost, node)`.

```
start:       heap=[(0,0)]   dist: 0:0, 1:inf, 2:inf, 3:inf

pop (0,0):   cost 0 equals dist[0] -> ok, use it.
             edge 0->1 cost 4: 0+4=4 < inf -> dist[1]=4, push (4,1)
             edge 0->2 cost 1: 0+1=1 < inf -> dist[2]=1, push (1,2)
             heap=[(1,2),(4,1)]

pop (1,2):   1 equals dist[2] -> ok.
             edge 2->1 cost 2: 1+2=3 < 4  -> dist[1]=3, push (3,1)   (cheaper way found!)
             edge 2->3 cost 5: 1+5=6 < inf -> dist[3]=6, push (6,3)
             heap=[(3,1),(4,1),(6,3)]

pop (3,1):   3 equals dist[1] -> ok.
             edge 1->3 cost 1: 3+1=4 < 6 -> dist[3]=4, push (4,3)
             heap=[(4,1),(4,3),(6,3)]

pop (4,1):   4 is bigger than dist[1]=3 -> STALE, skip.
pop (4,3):   4 equals dist[3] -> ok. Node 3 has no outgoing edges.
pop (6,3):   6 is bigger than dist[3]=4 -> STALE, skip.
heap empty -> done.

final dist: 0:0, 1:3, 2:1, 3:4
```

The cheapest way to 3 is `0 -> 2 -> 1 -> 3`, cost `1 + 2 + 1 = 4`.

---

## 4. Template code

### 4a. Dijkstra

```python
import heapq                                  # min-heap library


def dijkstra(graph, source, n):               # graph[u] = list of (v, cost); nodes are 0..n-1
    dist = [float("inf")] * n                 # best known cost to each node, none known yet
    dist[source] = 0                          # reaching the source costs nothing
    heap = [(0, source)]                      # the heap holds (cost so far, node)
    while heap:                               # while there are places to explore
        cost, u = heapq.heappop(heap)         # take the cheapest place we know about
        if cost > dist[u]:                    # a better route to u was already found
            continue                          # this entry is stale, skip it
        for v, w in graph[u]:                 # each road leaving u, going to v with cost w
            new_cost = cost + w               # cost to reach v through u
            if new_cost < dist[v]:            # is it better than what we knew?
                dist[v] = new_cost            # yes: remember the better cost
                heapq.heappush(heap, (new_cost, v))   # and explore from v later
    return dist                               # cheapest cost to every node (inf = unreachable)


g = {0: [(1, 4), (2, 1)], 1: [(3, 1)], 2: [(1, 2), (3, 5)], 3: []}   # the graph from the trace
result = dijkstra(g, 0, 4)                    # run from node 0
print(result)                                 # expect [0, 3, 1, 4]
assert result == [0, 3, 1, 4]                 # same as the hand trace
g2 = {0: [(1, 1)], 1: [], 2: []}              # node 2 cannot be reached
assert dijkstra(g2, 0, 3)[2] == float("inf")  # unreachable stays infinity
```

---

## 5. Classic problems

### 5.1 Network Delay Time (LeetCode 743)

**In plain words.** A network has `n` nodes (numbered `1..n`). `times[i] = [u, v, w]` means a signal sent from `u` takes `w` time to reach `v`. You send a signal from node `k`. How long until **all** nodes have received it? If some node never gets it, return `-1`.

**Brute force.** Try all paths from `k` to every node and pick the shortest for each. Too many paths. Another simple idea is Bellman-Ford (repeat relaxing all edges `n-1` times), which costs O(n x E). It is correct, just slower.

**Better idea, slowly.**
1. The signal reaches each node by its **cheapest** path. That is the Dijkstra distance from `k`.
2. All nodes have the signal when the **slowest** node gets it. So the answer is the **maximum** of all distances.
3. If any distance is still infinity, that node is unreachable. Return `-1`.

```python
import heapq                                  # heap
from typing import List                       # type hints


def network_delay_time(times: List[List[int]], n: int, k: int) -> int:   # time for all nodes to hear
    graph = {i: [] for i in range(1, n + 1)}  # graph[u] = list of (v, w); nodes are 1..n
    for u, v, w in times:                     # each directed edge
        graph[u].append((v, w))               # store it
    dist = {i: float("inf") for i in range(1, n + 1)}   # best known time to each node
    dist[k] = 0                               # the start node hears at time 0
    heap = [(0, k)]                           # (time, node)
    while heap:                               # while there are nodes to expand
        t, u = heapq.heappop(heap)            # earliest unexpanded node
        if t > dist[u]:                       # stale entry
            continue                          # skip
        for v, w in graph[u]:                 # each outgoing edge
            if t + w < dist[v]:               # a faster way to v?
                dist[v] = t + w               # remember it
                heapq.heappush(heap, (t + w, v))   # expand from v later
    slowest = max(dist.values())              # the last node to hear decides the answer
    return -1 if slowest == float("inf") else slowest   # infinity means someone never heard


print(network_delay_time([[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2))   # expect 2
assert network_delay_time([[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2) == 2   # example 1
assert network_delay_time([[1, 2, 1]], 2, 1) == 1          # example 2
assert network_delay_time([[1, 2, 1]], 2, 2) == -1         # example 3: node 1 can never be reached
assert network_delay_time([], 1, 1) == 0                   # edge case: one node, nothing to wait for
assert network_delay_time([[1, 2, 5], [1, 3, 1], [3, 2, 1]], 3, 1) == 2   # a cheaper two-step route wins
```

**Trace** on `times=[[2,1,1],[2,3,1],[3,4,1]]`, `n=4`, `k=2`:

```
dist: 1:inf 2:0 3:inf 4:inf     heap=[(0,2)]
pop (0,2): edge 2->1 w1 -> dist[1]=1, push.  edge 2->3 w1 -> dist[3]=1, push.
pop (1,1): node 1 has no outgoing edges.
pop (1,3): edge 3->4 w1 -> dist[4]=2, push.
pop (2,4): node 4 has no outgoing edges.
dist: 1:1 2:0 3:1 4:2     max = 2   -> answer 2
```

**Complexity.** Time O(E log V): each edge can cause one heap push, and each push or pop costs log of the heap size. Space O(V + E).

**Edge cases.**
1. A node cannot be reached: some distance stays infinity, return `-1`.
2. `n = 1`: the answer is 0.

**How interviewers twist it.**
- "Return the path, not just the time": keep a `parent` dictionary and walk back from the target.
- "Edges can be negative": Dijkstra breaks. Use Bellman-Ford.
- "Many sources start at once": push all of them with cost 0 at the start (like multi-source BFS).

---

### 5.2 Cheapest Flights Within K Stops (LeetCode 787)

**In plain words.** `n` cities. `flights[i] = [from, to, price]`. Find the cheapest price from `src` to `dst` with **at most `k` stops** (a stop is a city in the middle, so at most `k+1` flights). Return `-1` if impossible.

**Brute force.** DFS through all routes of length up to `k+1` and keep the cheapest. Cost grows like (flights per city)^(k+1). Too slow for large inputs.

**Why plain Dijkstra is risky here.** The cheapest route might use too many stops. A slightly more expensive route with fewer stops may be the only valid one. Dijkstra throws away the "more expensive" way to reach a city, even if it was the one with fewer stops.

**Better idea (Bellman-Ford with limited rounds), slowly.**
1. Keep `dist[city]` = cheapest known price to reach it.
2. **Round 1** allows paths with at most 1 flight. **Round 2** allows paths with at most 2 flights. And so on.
3. In each round, go through all flights. Try `new = prev[from] + price`. If `new` beats `cur[to]`, update `cur[to]`. Important: use the distances from the **previous** round (`prev`), so one round adds only one flight.
4. Do `k + 1` rounds. Then `dist[dst]` is the answer.

```python
from typing import List                       # type hints


def find_cheapest_price(n: int, flights: List[List[int]], src: int, dst: int, k: int) -> int:   # cheapest price
    INF = float("inf")                        # a number bigger than any price
    dist = [INF] * n                          # cheapest known price to each city
    dist[src] = 0                             # we are at the source for free
    for _ in range(k + 1):                    # at most k stops means at most k+1 flights
        prev = dist[:]                        # snapshot: prices using fewer flights
        for u, v, price in flights:           # check every flight
            if prev[u] != INF and prev[u] + price < dist[v]:   # can we reach v cheaper using this flight?
                dist[v] = prev[u] + price     # yes: update (based on the snapshot, so only one more flight)
    return -1 if dist[dst] == INF else dist[dst]   # -1 when dst cannot be reached within the limit


flights = [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]]   # the LeetCode example
print(find_cheapest_price(4, flights, 0, 3, 1))     # expect 700
assert find_cheapest_price(4, flights, 0, 3, 1) == 700    # with 1 stop: 0->1->3
assert find_cheapest_price(4, flights, 0, 3, 2) == 400    # with 2 stops: 0->1->2->3 is cheaper
assert find_cheapest_price(4, flights, 0, 3, 0) == -1     # edge case: no stops, no direct flight
assert find_cheapest_price(3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 0) == 500   # direct flight only
assert find_cheapest_price(3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 1) == 200   # one stop is cheaper
assert find_cheapest_price(2, [[0, 1, 5]], 0, 0, 0) == 0  # edge case: source equals destination
```

**Trace** on the first example with `k = 1` (so 2 rounds), `src=0`, `dst=3`:

```
start:   dist = [0, inf, inf, inf]
round 1: prev = [0, inf, inf, inf]
         flight 0->1 (100): prev[0]=0 -> dist[1]=100
         flight 1->2: prev[1]=inf -> skip.  2->0: prev[2]=inf -> skip.
         flight 1->3: skip.  2->3: skip.
         dist = [0, 100, inf, inf]
round 2: prev = [0, 100, inf, inf]
         flight 0->1: 0+100=100 not better than 100.
         flight 1->2 (100): prev[1]=100 -> dist[2]=200
         flight 2->0: prev[2]=inf -> skip.
         flight 1->3 (600): prev[1]=100 -> dist[3]=700
         flight 2->3: prev[2]=inf -> skip (prev, not dist!)
         dist = [0, 100, 200, 700]
done 2 rounds -> dist[3] = 700
```

If we had allowed one more round (`k=2`), round 3 would use `prev[2]=200` and `200 + 200 = 400 < 700`, so the answer becomes 400.

**Complexity.** Time O(k x E): `k+1` rounds, each looks at every flight once. Space O(n) for two price arrays.

**Edge cases.**
1. `k = 0`: only a direct flight is allowed. Answer is that price or `-1`.
2. `src == dst`: price 0.

**How interviewers twist it.**
- "Solve it with Dijkstra": keep `(price, city, stops_used)` in the heap and also remember the fewest stops with which you reached each city.
- "Solve it with BFS by levels": level = number of flights, run `k+1` levels while tracking the best price per city.
- "Negative prices (credits)": Bellman-Ford still works. Dijkstra does not.

---

### 5.3 Path With Minimum Effort (LeetCode 1631)

**In plain words.** A grid of heights. You walk from the top-left to the bottom-right, moving up, down, left or right. The **effort** of a path is the **biggest height difference** between two neighbouring cells on the path. Find the path with the smallest effort.

**Brute force.** DFS over all paths, compute the effort of each, take the minimum. Exponential.

**Better idea, slowly.**
1. This looks like a "shortest path", but the cost of a path is the **maximum** step, not the sum.
2. Dijkstra still works. The cost to reach a cell = `max(cost to the previous cell, height difference of this step)`.
3. The heap always gives us the cell reachable with the smallest effort so far. The first time we pop the bottom-right cell, that effort is final.

Why does it still work with `max`? The key rule for Dijkstra is that going further never makes the cost *smaller*. With `max`, adding a step can only keep the cost the same or raise it. So the rule holds.

```python
import heapq                                  # heap
from typing import List                       # type hints


def minimum_effort_path(heights: List[List[int]]) -> int:   # smallest possible biggest step
    rows, cols = len(heights), len(heights[0])   # grid size
    best = [[float("inf")] * cols for _ in range(rows)]   # smallest effort found to reach each cell
    best[0][0] = 0                            # start: no steps yet
    heap = [(0, 0, 0)]                        # (effort, row, col)
    while heap:                               # while cells remain to explore
        effort, r, c = heapq.heappop(heap)    # the cell reachable with the smallest effort
        if r == rows - 1 and c == cols - 1:   # reached the goal?
            return effort                     # first time we pop it is the best
        if effort > best[r][c]:               # stale entry
            continue                          # skip
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:   # four neighbours
            nr, nc = r + dr, c + dc           # neighbour cell
            if 0 <= nr < rows and 0 <= nc < cols:   # inside the grid
                step = abs(heights[nr][nc] - heights[r][c])   # height difference of this step
                new_effort = max(effort, step)    # path effort is the biggest step so far
                if new_effort < best[nr][nc]:     # better than what we knew?
                    best[nr][nc] = new_effort     # remember it
                    heapq.heappush(heap, (new_effort, nr, nc))   # explore it later
    return 0                                  # not reached for a non-empty grid


print(minimum_effort_path([[1, 2, 2], [3, 8, 2], [5, 3, 5]]))   # expect 2
assert minimum_effort_path([[1, 2, 2], [3, 8, 2], [5, 3, 5]]) == 2   # example 1
assert minimum_effort_path([[1, 2, 3], [3, 8, 4], [5, 3, 5]]) == 1   # example 2
assert minimum_effort_path([[1, 2, 1, 1, 1], [1, 2, 1, 2, 1], [1, 2, 1, 2, 1], [1, 2, 1, 2, 1], [1, 1, 1, 2, 1]]) == 0   # example 3
assert minimum_effort_path([[7]]) == 0        # edge case: one cell
assert minimum_effort_path([[1, 10]]) == 9    # edge case: one forced step
```

**Trace** on `[[1,2,2],[3,8,2],[5,3,5]]` (cells written as `(row,col)`):

```
heap=[(0,(0,0))]
pop (0,(0,0)): neighbours (1,0) step |3-1|=2 -> effort 2.  (0,1) step 1 -> effort 1.
pop (1,(0,1)): (0,2) step 0 -> 1.  (1,1) step |8-2|=6 -> 6.
pop (1,(0,2)): (1,2) step 0 -> 1.
pop (1,(1,2)): (2,2) step |5-2|=3 -> 3.  (1,1) step 6 -> 6, not better than 6.
pop (2,(1,0)): (2,0) step 2 -> 2.  (1,1) step 5 -> max(2,5)=5, better than 6 -> update.
pop (2,(2,0)): (2,1) step |3-5|=2 -> 2.
pop (2,(2,1)): (2,2) step |5-3|=2 -> max(2,2)=2, better than 3 -> update.
pop (2,(2,2)): this is the goal -> return 2.
```

The route is `1 -> 3 -> 5 -> 3 -> 5` and its steps are 2, 2, 2, 2. The biggest is 2.

**Complexity.** Time O(R x C x log(R x C)): each cell can be pushed a few times, and each push costs log. Space O(R x C).

**Edge cases.**
1. A single cell: effort 0.
2. A grid with only two cells: the effort is the one forced step.

**How interviewers twist it.**
- "Solve it with binary search + BFS": binary-search the effort `E`, and use BFS to check "can I reach the goal using only steps of at most `E`?" Also correct.
- "Swim in Rising Water" (LeetCode 778): same idea, with cost = max height on the path.
- "Union-Find alternative": sort edges by cost and add them until start and goal are connected.

---

### 5.4 Path With Maximum Probability (LeetCode 1514)

**In plain words.** An undirected graph. Each edge has a success probability (a number between 0 and 1). The probability of a path is the **product** of its edge probabilities. Find the path from `start` to `end` with the **highest** probability. Return `0` if there is no path.

**Brute force.** Try all paths. Exponential.

**Better idea, slowly.**
1. Multiplying numbers between 0 and 1 only makes them smaller or equal. So extending a path never improves it. That is the same rule Dijkstra needs, but now we want the **biggest** value instead of the smallest.
2. Python's heap gives the smallest. So we store **negative** probability, then the biggest probability is on top.
3. Everything else is Dijkstra: pop the best node, try to improve each neighbour.

```python
import heapq                                  # heap
from typing import List                       # type hints


def max_probability(n: int, edges: List[List[int]], succ_prob: List[float], start: int, end: int) -> float:   # best probability
    graph = [[] for _ in range(n)]            # graph[u] = list of (v, probability)
    for (a, b), p in zip(edges, succ_prob):   # each undirected edge with its probability
        graph[a].append((b, p))               # a -> b
        graph[b].append((a, p))               # b -> a
    best = [0.0] * n                          # best known probability to reach each node
    best[start] = 1.0                         # we are at the start with probability 1
    heap = [(-1.0, start)]                    # negative probability so the biggest comes first
    while heap:                               # while nodes remain
        neg_p, u = heapq.heappop(heap)        # the most likely node so far
        p = -neg_p                            # turn it back to a normal probability
        if u == end:                          # reached the target
            return p                          # its probability is final
        if p < best[u]:                       # stale entry
            continue                          # skip
        for v, q in graph[u]:                 # each neighbour
            if p * q > best[v]:               # a more likely route to v?
                best[v] = p * q               # remember it
                heapq.heappush(heap, (-(p * q), v))   # explore later
    return 0.0                                # target unreachable


print(max_probability(3, [[0, 1], [1, 2], [0, 2]], [0.5, 0.5, 0.2], 0, 2))   # expect 0.25
assert max_probability(3, [[0, 1], [1, 2], [0, 2]], [0.5, 0.5, 0.2], 0, 2) == 0.25   # example 1
assert max_probability(3, [[0, 1], [1, 2], [0, 2]], [0.5, 0.5, 0.3], 0, 2) == 0.3    # example 2: direct is better
assert max_probability(3, [[0, 1]], [0.5], 0, 2) == 0.0       # example 3: no path
assert max_probability(2, [[0, 1]], [1.0], 0, 0) == 1.0       # edge case: start equals end
```

**Trace** on `n=3`, edges `0-1 (0.5)`, `1-2 (0.5)`, `0-2 (0.2)`, from 0 to 2:

```
best = [1.0, 0, 0]    heap = [(-1.0, 0)]
pop node 0, p=1.0: neighbour 1: 1.0*0.5=0.5 > 0 -> best[1]=0.5, push.
                   neighbour 2: 1.0*0.2=0.2 > 0 -> best[2]=0.2, push.
pop node 1, p=0.5: neighbour 0: 0.5*0.5=0.25 > 1.0? no.
                   neighbour 2: 0.5*0.5=0.25 > 0.2 -> best[2]=0.25, push.
pop node 2, p=0.25: it is the target -> return 0.25
(the old entry for node 2 with 0.2 is stale and would be skipped)
```

**Complexity.** Time O(E log V). Space O(V + E).

**Edge cases.**
1. `start == end`: probability 1.
2. The target cannot be reached: return `0`.

**How interviewers twist it.**
- "Use logarithms": turn products into sums with `-log(p)`, then it is a normal shortest path.
- "Bellman-Ford version": also works. Just relax edges repeatedly.
- "Reliability of a network where each link may fail": same problem in different clothes.

---

## 6. Common mistakes

1. **Using Dijkstra when edges can be negative.** It gives wrong answers. Use Bellman-Ford.
2. **Using Dijkstra when all costs are equal.** BFS is simpler and faster. Interviewers may notice.
3. **Forgetting the stale check** (`if cost > dist[u]: continue`). The answer is still right but you do extra work (slower on big graphs).
4. **Marking a node as "done" when it is pushed instead of when it is popped.** In Dijkstra the first push is not always the best. The *pop* is the moment the cost is final.
5. **Pushing `(node, cost)` instead of `(cost, node)`.** The heap orders by the first item. Cost must come first.
6. **Using `dist = {}` and then `dist[v]` for a missing key.** Start with all infinity.
7. **"At most K stops" solved by plain Dijkstra.** It can drop the route that has the needed number of stops. Use rounds (Bellman-Ford) or add the stops count to the state.
8. **Copying `prev` forgotten in Bellman-Ford with a limit.** Without the snapshot, one round can use many flights.

---

## 7. Practice list (8 more problems)

These are for more practice with weighted paths. I did not verify company tags for any problem in this table. For reference, the two problems taught above are in public company-tag lists: Network Delay Time (Google, Amazon) and Cheapest Flights Within K Stops (Stripe, Google, Meta, Microsoft). Source and caveats are in lesson 19.

| # | Problem | Difficulty | Tagged for |
|---|---|---|---|
| 1 | Find the City With the Smallest Number of Neighbors at a Threshold Distance (1334) | Medium | not verified |
| 2 | Number of Ways to Arrive at Destination (1976) | Medium | not verified |
| 3 | Min Cost to Connect All Points (1584) | Medium | not verified |
| 4 | Swim in Rising Water (778) | Hard | not verified |
| 5 | Minimum Obstacle Removal to Reach Corner (2290) | Hard | not verified |
| 6 | Shortest Path Visiting All Nodes (847) | Hard | not verified |
| 7 | Reconstruct Itinerary (332) | Hard | not verified |
| 8 | Bus Routes (815) | Hard | not verified |

---

## 8. Self-quiz (5 questions)

1. Why does BFS not work when roads have different costs?
2. In Dijkstra, why is a node's distance "final" when we pop it from the heap?
3. What does the line `if cost > dist[u]: continue` do and why is it needed?
4. Why does Dijkstra fail with negative edges?
5. In "Cheapest Flights Within K Stops", why do we copy `dist` into `prev` at the start of each round?

**Answers.**
1. BFS counts edges, not costs. The path with the fewest edges may have a big total cost.
2. Every other waiting node has a cost that is bigger or equal. Since costs are never negative, no other route can come back and give this node a smaller cost.
3. A node can be pushed several times with different costs. When an older, bigger entry is popped later, `cost > dist[u]` is true. We skip it because a better route was already handled. Without it we do extra work.
4. A negative edge could make a path cheaper after we already declared the node "final". The greedy idea "nothing can improve this" is no longer true.
5. We want round `i` to use paths with exactly one more flight than round `i-1`. If we updated `dist` and read from `dist` in the same round, one round could chain many flights and break the "at most K stops" limit.
