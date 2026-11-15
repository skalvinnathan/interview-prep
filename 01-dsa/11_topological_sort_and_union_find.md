# Lesson 11: Topological Sort and Union-Find

All code is Python 3.9. Every code block in this file was run with `python3` (3.9.6) before it was written here.

This lesson has two tools. They look different, but both answer questions about **connections**:
- **Topological sort**: "In what order can I do these tasks, if some tasks must come before others?"
- **Union-Find**: "Are these two things in the same group? Join two groups."

---

## Words you need first

- **Directed edge** (an arrow): `A -> B` means "A comes before B". It has a direction.
- **Prerequisite**: a task you must finish first. To take "Algorithms" you must first pass "Programming".
- **In-degree**: how many arrows point **into** a node. In-degree 0 means "no prerequisites, I can start now".
- **Cycle**: arrows that go around in a circle: `A -> B -> A`. With a cycle, no valid order exists.
- **Topological order**: a list of all nodes such that every arrow goes from earlier to later.
- **Group / component**: a set of nodes that are all connected to each other.
- **Root (leader)**: one chosen member who represents a group.

---

## 1. What is this?

### Topological sort

**Analogy: getting dressed.**
Socks before shoes. Underwear before trousers. Trousers before belt. Many orders work, but "shoes before socks" never works. A topological sort finds *one* valid order. If the rules contradict each other (shoes before socks AND socks before shoes), no order exists, and the algorithm tells you so.

**Kahn's algorithm** (the easy one):
1. Count the in-degree of every node.
2. Put every node with in-degree 0 into a queue. They are free to start.
3. Take one out. Write it in the answer. Pretend it is done: reduce the in-degree of everything it points to by 1.
4. Any node that now has in-degree 0 joins the queue.
5. Repeat. If you wrote all nodes, you have an order. If not, there is a cycle.

### Union-Find (also called Disjoint Set Union, DSU)

**Analogy: friend groups at a party.**
At first everybody is alone and is their own leader. When two people become friends, their two groups merge: one leader steps down and follows the other. To ask "are Asha and Ravi in the same group?", you ask both "who is your leader?" If the leaders are the same person, then yes.

Two operations:
- `find(x)`: who is the leader of x's group?
- `union(a, b)`: merge the groups of a and b.

Two speed tricks:
- **Path compression**: while walking up to the leader, make everybody point straight at the leader. Next time it is one step.
- **Union by size**: when merging, attach the *smaller* group under the *bigger* group's leader. Chains stay short.

With both tricks, each operation is almost O(1) (the formal name is "inverse Ackermann", which is below 5 for any input you will ever see).

---

## 2. When do I use it?

**Topological sort:**

| Words in the problem | Idea |
|---|---|
| "**prerequisites**", "course schedule", "can you finish all courses" | Topological sort, check for a cycle |
| "**order** of tasks", "build order", "dependencies" | Topological sort |
| "does this directed graph have a **cycle**?" | Kahn's: if not all nodes are processed, there is a cycle |
| "alien dictionary", "order of letters" | Build arrows from the word list, then topological sort |

**Union-Find:**

| Words in the problem | Idea |
|---|---|
| "number of **connected components / provinces / groups**" | Union-Find (or DFS) |
| "are A and B **connected**?" asked many times, with edges added over time | Union-Find |
| "which edge **creates a cycle**" in an undirected graph, "redundant connection" | Union-Find: if the two ends already share a leader, this edge is the extra one |
| "merge accounts / emails that share something" | Union-Find |

---

## 3. Trace of a tiny example

### Topological sort (Kahn's)

4 courses. Rules: 0 before 1, 0 before 2, 1 before 3, 2 before 3.

```
 0 --> 1 --> 3
 |           ^
 +---> 2 ----+
```

In-degrees: `0:0  1:1  2:1  3:2`.

```
start:   queue=[0]            (only node 0 has in-degree 0)     order=[]
pop 0:   order=[0]. Arrows from 0 go to 1 and 2.
         in-degree of 1 becomes 0 -> push. in-degree of 2 becomes 0 -> push.
         queue=[1,2]
pop 1:   order=[0,1]. Arrow from 1 goes to 3: in-degree of 3 becomes 1. Not zero yet.
         queue=[2]
pop 2:   order=[0,1,2]. Arrow from 2 goes to 3: in-degree of 3 becomes 0 -> push.
         queue=[3]
pop 3:   order=[0,1,2,3]. No arrows out.
         queue=[]
order has 4 nodes = all nodes -> valid order exists: 0, 1, 2, 3
```

A cycle example: 0 before 1, and 1 before 0. In-degrees `0:1  1:1`. No node has in-degree 0, so the queue starts empty. We process 0 nodes out of 2, so there is a cycle.

### Union-Find

5 people `0..4`. `parent[i]` is who i follows. Start: everybody follows themselves.

```
start:        parent = [0, 1, 2, 3, 4]   size = [1,1,1,1,1]
union(0,1):   leaders 0 and 1, same size -> attach 1 under 0
              parent = [0, 0, 2, 3, 4]   size[0] = 2
union(1,2):   find(1) -> 1 points to 0, 0 points to itself -> leader 0
              find(2) -> leader 2
              size[0]=2 is bigger than size[2]=1 -> attach 2 under 0
              parent = [0, 0, 0, 3, 4]   size[0] = 3
union(3,4):   leaders 3 and 4, same size -> attach 4 under 3
              parent = [0, 0, 0, 3, 3]   size[3] = 2
find(2) == find(0)?  0 == 0 -> yes, connected
find(4) == find(0)?  3 != 0 -> no
groups left = 5 - 3 successful unions = 2   ({0,1,2} and {3,4})
```

---

## 4. Template code

### 4a. Topological sort (Kahn's algorithm)

```python
from collections import deque                 # queue


def topo_sort(n, edges):                      # n nodes numbered 0..n-1, edges are (a, b) meaning a before b
    graph = [[] for _ in range(n)]            # graph[a] = list of nodes that come after a
    indeg = [0] * n                           # indeg[x] = how many arrows point into x
    for a, b in edges:                        # read each rule "a before b"
        graph[a].append(b)                    # draw the arrow a -> b
        indeg[b] += 1                         # b now has one more prerequisite
    queue = deque(i for i in range(n) if indeg[i] == 0)   # all nodes with no prerequisites can start
    order = []                                # the answer, built step by step
    while queue:                              # while some node is free to do
        node = queue.popleft()                # take one free node
        order.append(node)                    # do it now
        for nxt in graph[node]:               # everything that waited for this node
            indeg[nxt] -= 1                   # one prerequisite less
            if indeg[nxt] == 0:               # no prerequisites left?
                queue.append(nxt)             # it is free now
    if len(order) == n:                       # did we manage to do every node?
        return order                          # yes: a valid order
    return []                                 # no: there is a cycle, no order exists


print(topo_sort(4, [(0, 1), (0, 2), (1, 3), (2, 3)]))   # expect [0, 1, 2, 3]
print(topo_sort(2, [(0, 1), (1, 0)]))         # a cycle: expect []
assert topo_sort(4, [(0, 1), (0, 2), (1, 3), (2, 3)]) == [0, 1, 2, 3]   # same as the hand trace
assert topo_sort(2, [(0, 1), (1, 0)]) == []   # cycle gives an empty list
```

### 4b. Union-Find class

```python
class UnionFind:                              # groups with fast find and union
    def __init__(self, n):                    # n people numbered 0..n-1
        self.parent = list(range(n))          # at first everybody follows themselves
        self.size = [1] * n                   # every group has size 1
        self.groups = n                       # number of separate groups

    def find(self, x):                        # who is the leader of x?
        while self.parent[x] != x:            # a leader follows themselves; keep climbing until one
            self.parent[x] = self.parent[self.parent[x]]   # path compression: skip one level up
            x = self.parent[x]                # climb to the parent
        return x                              # x is the leader now

    def union(self, a, b):                    # merge the groups of a and b
        ra, rb = self.find(a), self.find(b)   # find both leaders
        if ra == rb:                          # same leader: already one group
            return False                      # nothing was merged
        if self.size[ra] < self.size[rb]:     # make ra the bigger group's leader
            ra, rb = rb, ra                   # swap them
        self.parent[rb] = ra                  # the smaller group follows the bigger group
        self.size[ra] += self.size[rb]        # the bigger group grew
        self.groups -= 1                      # two groups became one
        return True                           # a real merge happened


uf = UnionFind(5)                             # five people, five groups
uf.union(0, 1)                                # 0 and 1 become friends
uf.union(1, 2)                                # 1 and 2 become friends
uf.union(3, 4)                                # 3 and 4 become friends
print(uf.parent, uf.groups)                   # expect [0, 0, 0, 3, 3] 2
assert uf.parent == [0, 0, 0, 3, 3]           # same as the hand trace
assert uf.groups == 2                         # two groups left
assert uf.find(2) == uf.find(0)               # 2 and 0 are connected
assert uf.find(4) != uf.find(0)               # 4 and 0 are not connected
assert uf.union(0, 2) is False                # already together, so no merge
```

---

## 5. Classic problems

### 5.1 Course Schedule (LeetCode 207)

**In plain words.** There are `numCourses` courses (numbered `0` to `n-1`). A pair `[a, b]` means "to take course `a` you must first take course `b`". Can you finish all the courses? (Meaning: is there NO cycle in the rules?)

**Brute force.** Try every order of courses and check the rules. That is `n!` orders. Far too slow.

**Better idea, slowly.**
1. Draw an arrow `b -> a` for each pair `[a, b]` (b first, then a).
2. If there is a cycle (`a` needs `b`, `b` needs `c`, `c` needs `a`), nobody in the circle can ever start. So the answer is `False`.
3. Run Kahn's algorithm. Count how many courses you could finish.
4. If you could finish all `n`, return `True`. Otherwise `False`.

```python
from collections import deque                 # queue
from typing import List                       # type hints


def can_finish(num_courses: int, prerequisites: List[List[int]]) -> bool:   # can we finish every course?
    graph = [[] for _ in range(num_courses)]  # graph[b] = courses that need b
    indeg = [0] * num_courses                 # indeg[a] = how many prerequisites course a has
    for a, b in prerequisites:                # pair [a, b]: take b before a
        graph[b].append(a)                    # arrow b -> a
        indeg[a] += 1                         # a has one more prerequisite
    queue = deque(i for i in range(num_courses) if indeg[i] == 0)   # courses with no prerequisites
    done = 0                                  # courses finished so far
    while queue:                              # while some course can be taken
        course = queue.popleft()              # take it
        done += 1                             # one more finished
        for nxt in graph[course]:             # courses that were waiting for it
            indeg[nxt] -= 1                   # one prerequisite less
            if indeg[nxt] == 0:               # all prerequisites done?
                queue.append(nxt)             # now it can be taken
    return done == num_courses                # true only if no course got stuck in a cycle


print(can_finish(2, [[1, 0]]))                # expect True
print(can_finish(2, [[1, 0], [0, 1]]))        # expect False
assert can_finish(2, [[1, 0]]) is True        # example 1
assert can_finish(2, [[1, 0], [0, 1]]) is False   # example 2: a cycle
assert can_finish(1, []) is True              # edge case: one course, no rules
assert can_finish(3, []) is True              # edge case: no rules at all
assert can_finish(1, [[0, 0]]) is False       # edge case: a course needs itself
assert can_finish(4, [[1, 0], [2, 1], [3, 2], [1, 3]]) is False   # a cycle hidden at the end of a chain
```

**Trace** on `n=2`, `[[1,0],[0,1]]`:

```
arrows: 0 -> 1 (from [1,0]), 1 -> 0 (from [0,1])
indeg = [1, 1]
queue = []  (nobody has indeg 0)
done = 0, which is not 2 -> return False
```

And on `n=2`, `[[1,0]]`:

```
arrows: 0 -> 1.  indeg = [0, 1].  queue = [0]
pop 0: done = 1. indeg[1] becomes 0 -> queue = [1]
pop 1: done = 2.
done == 2 -> return True
```

**Complexity.** Time O(V + E): V = courses, E = prerequisite pairs. Each course is queued once, each pair is used once. Space O(V + E) for the graph.

**Edge cases.**
1. No prerequisites: always `True`.
2. A course that needs itself `[0, 0]`: a one-node cycle, so `False`. (Kahn's handles it: indeg of 0 is 1, queue starts empty.)

**How interviewers twist it.**
- "Return one valid order" (LeetCode 210): the next problem.
- "Minimum number of semesters if you can take any number of courses per semester" (LeetCode 1136, Parallel Courses): count the levels of Kahn's BFS.
- "Detect the cycle with DFS instead": use 3 colours (not seen, in progress, done). If you reach an "in progress" node, you found a cycle.

---

### 5.2 Course Schedule II (LeetCode 210)

**In plain words.** Same input as above. Return **an order** to take all the courses. If impossible, return an empty list.

**Brute force.** Try every permutation and check. `n!` again.

**Better idea, slowly.** Exactly Kahn's algorithm. The only change: instead of counting finished courses, **write them in a list** in the order they leave the queue. That list is a valid order. If the list is shorter than `n`, there was a cycle: return `[]`.

```python
from collections import deque                 # queue
from typing import List                       # type hints


def find_order(num_courses: int, prerequisites: List[List[int]]) -> List[int]:   # an order, or []
    graph = [[] for _ in range(num_courses)]  # graph[b] = courses that need b
    indeg = [0] * num_courses                 # number of prerequisites per course
    for a, b in prerequisites:                # [a, b] means b before a
        graph[b].append(a)                    # arrow b -> a
        indeg[a] += 1                         # a has one more prerequisite
    queue = deque(i for i in range(num_courses) if indeg[i] == 0)   # free courses
    order = []                                # the courses in a valid order
    while queue:                              # while a course is free
        course = queue.popleft()              # take it
        order.append(course)                  # write it down
        for nxt in graph[course]:             # courses waiting on it
            indeg[nxt] -= 1                   # one prerequisite less
            if indeg[nxt] == 0:               # all done?
                queue.append(nxt)             # it is free now
    return order if len(order) == num_courses else []   # empty list when a cycle blocks some courses


def is_valid(order, prerequisites):           # test helper: does every rule hold in this order?
    pos = {c: i for i, c in enumerate(order)} # position of each course in the order
    return all(pos[b] < pos[a] for a, b in prerequisites)   # b must come before a


res = find_order(4, [[1, 0], [2, 0], [3, 1], [3, 2]])   # four courses, a diamond of rules
print(res)                                    # expect [0, 1, 2, 3]
assert res == [0, 1, 2, 3]                    # same as the hand trace
assert is_valid(res, [[1, 0], [2, 0], [3, 1], [3, 2]])   # every rule is satisfied
assert find_order(2, [[1, 0], [0, 1]]) == []  # cycle gives empty list
assert find_order(1, []) == [0]               # edge case: single course
assert sorted(find_order(3, [])) == [0, 1, 2] # edge case: no rules, any order works
```

**Trace** on `n=4`, `[[1,0],[2,0],[3,1],[3,2]]`: this is exactly the Kahn's trace in section 3. Result `[0,1,2,3]`.

**Complexity.** Time O(V + E). Space O(V + E). Same as before.

**Edge cases.**
1. A cycle anywhere in the graph (even far from the free nodes): the order is shorter than `n`, so return `[]`.
2. Many valid answers: the problem accepts any. Do not worry if your order is different from the sample.

**How interviewers twist it.**
- "Alien Dictionary" (LeetCode 269): you are given sorted words in an unknown alphabet. Compare neighbouring words to find rules like `t before f`, build the graph, then run this same algorithm on letters.
- "Return the *lexicographically smallest* order": replace the queue with a min-heap (lesson 09).
- "Build order with dependencies between projects": same problem, named differently.

---

### 5.3 Number of Provinces (LeetCode 547)

**In plain words.** `n` cities. `isConnected[i][j] == 1` means city `i` and city `j` are directly connected. A **province** is a group of cities connected directly or indirectly. Count the provinces.

**Brute force / first idea.** Run DFS from each unvisited city and count how many times you start. This is correct and O(n^2). It is a fine answer. Union-Find is another correct answer, and is what you need for the harder follow-ups.

**Better idea (Union-Find), slowly.**
1. Start with `n` groups: every city alone.
2. For each pair `(i, j)` with a `1`, `union(i, j)`.
3. Each successful union reduces the number of groups by one.
4. At the end, the number of groups is the answer.

```python
from typing import List                       # type hints


class UnionFind:                              # same class as the template
    def __init__(self, n):                    # n elements
        self.parent = list(range(n))          # everybody leads themselves
        self.size = [1] * n                   # group sizes
        self.groups = n                       # number of groups

    def find(self, x):                        # leader of x
        while self.parent[x] != x:            # climb until a leader
            self.parent[x] = self.parent[self.parent[x]]   # path compression
            x = self.parent[x]                # step up
        return x                              # the leader

    def union(self, a, b):                    # merge two groups
        ra, rb = self.find(a), self.find(b)   # leaders
        if ra == rb:                          # same group
            return False                      # no merge
        if self.size[ra] < self.size[rb]:     # keep ra as the bigger one
            ra, rb = rb, ra                   # swap
        self.parent[rb] = ra                  # attach smaller under bigger
        self.size[ra] += self.size[rb]        # update size
        self.groups -= 1                      # one group less
        return True                           # merged


def find_circle_num(is_connected: List[List[int]]) -> int:   # number of provinces
    n = len(is_connected)                     # number of cities
    uf = UnionFind(n)                         # every city starts alone
    for i in range(n):                        # for each city i
        for j in range(i + 1, n):             # and each later city j (the matrix is symmetric)
            if is_connected[i][j] == 1:       # directly connected?
                uf.union(i, j)                # join their groups
    return uf.groups                          # groups left = provinces


print(find_circle_num([[1, 1, 0], [1, 1, 0], [0, 0, 1]]))   # expect 2
assert find_circle_num([[1, 1, 0], [1, 1, 0], [0, 0, 1]]) == 2   # example 1
assert find_circle_num([[1, 0, 0], [0, 1, 0], [0, 0, 1]]) == 3   # example 2: nobody connected
assert find_circle_num([[1]]) == 1            # edge case: one city
assert find_circle_num([[1, 1, 1], [1, 1, 1], [1, 1, 1]]) == 1   # edge case: all connected
assert find_circle_num([[1, 0, 1], [0, 1, 0], [1, 0, 1]]) == 2   # 0 and 2 joined, 1 alone
```

**Trace** on `[[1,1,0],[1,1,0],[0,0,1]]`:

```
start:   parent=[0,1,2]  groups=3
(i=0,j=1): value 1 -> union(0,1): leaders 0 and 1, equal size -> parent[1]=0.  groups=2
(i=0,j=2): value 0 -> skip
(i=1,j=2): value 0 -> skip
answer = groups = 2   ({0,1} and {2})
```

**Complexity.** Time O(n^2 x alpha(n)), which is basically O(n^2): we read each cell of the matrix once, and each union is almost O(1). Space O(n) for the parent and size lists.

**Edge cases.**
1. Diagonal entries `isConnected[i][i]` are always 1. We start `j` at `i+1` so we ignore them.
2. A single city: answer 1.

**How interviewers twist it.**
- "Edges are given as a list, not a matrix" (Number of Connected Components, LeetCode 323): the same, with `for a, b in edges: uf.union(a, b)`.
- "Largest group size": read `max(uf.size)` over leaders.
- "Edges come in over time and after each one tell me the number of groups": Union-Find shines, and DFS does not.

---

### 5.4 Redundant Connection (LeetCode 684)

**In plain words.** A tree with `n` nodes (numbered `1..n`) had **one extra edge** added, so now it has a cycle. The edges are given in a list. Return the edge that can be removed so the rest is a tree. If several answers exist, return the one that appears **last** in the list.

**Brute force.** For each edge (from the last to the first), remove it and test with DFS whether the remaining graph is connected and has no cycle. Cost O(n^2).

**Better idea, slowly.**
1. Add the edges one at a time, as friendships.
2. When we add edge `(a, b)`: if `a` and `b` already have the same leader, they are already connected. This new edge closes a circle. It is the redundant edge.
3. Otherwise, union them and continue.
4. Because we go through the list in order and return the first edge that closes a cycle, we return the last edge of that cycle in list order. That matches the rule.

```python
from typing import List                       # type hints


def find_redundant_connection(edges: List[List[int]]) -> List[int]:   # the extra edge
    parent = list(range(len(edges) + 1))      # nodes are 1..n, so we make n+1 slots (slot 0 unused)
    size = [1] * (len(edges) + 1)             # group sizes

    def find(x):                              # leader of x
        while parent[x] != x:                 # climb until a leader
            parent[x] = parent[parent[x]]     # path compression
            x = parent[x]                     # step up
        return x                              # the leader

    for a, b in edges:                        # add the edges in order
        ra, rb = find(a), find(b)             # leaders of both ends
        if ra == rb:                          # already connected: this edge closes a circle
            return [a, b]                     # this is the redundant edge
        if size[ra] < size[rb]:               # keep ra as the bigger one
            ra, rb = rb, ra                   # swap
        parent[rb] = ra                       # attach smaller under bigger
        size[ra] += size[rb]                  # update size
    return []                                 # not reached for valid input


print(find_redundant_connection([[1, 2], [1, 3], [2, 3]]))   # expect [2, 3]
assert find_redundant_connection([[1, 2], [1, 3], [2, 3]]) == [2, 3]   # example 1
assert find_redundant_connection([[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]) == [1, 4]   # example 2
assert find_redundant_connection([[1, 2], [2, 1]]) == [2, 1]   # edge case: a double edge
assert find_redundant_connection([[1, 2], [2, 3], [1, 3], [3, 4]]) == [1, 3]   # extra edge is not last
```

**Trace** on `[[1,2],[1,3],[2,3]]`:

```
start:   parent=[0,1,2,3]
edge (1,2): leaders 1 and 2 differ -> union. parent=[0,1,1,3]   (2 follows 1)
edge (1,3): leaders 1 and 3 differ -> union. parent=[0,1,1,1]   (3 follows 1)
edge (2,3): find(2) -> 1.  find(3) -> 1.  Same leader!
            2 and 3 were already connected through 1 -> return [2,3]
```

**Complexity.** Time O(n x alpha(n)), basically O(n): one pass over the edges, each `find` and `union` almost O(1). Space O(n).

**Edge cases.**
1. A double edge `[[1,2],[2,1]]`: the second edge connects two already-connected nodes.
2. The extra edge may be in the middle of the list, and later edges may be harmless (`[[1,2],[2,3],[1,3],[3,4]]` gives `[1,3]`).

**How interviewers twist it.**
- "Directed graph version" (Redundant Connection II, LeetCode 685, Hard): a node may have two parents. Needs more care.
- "Is this graph a valid tree?" (LeetCode 261): a tree has exactly `n-1` edges and no cycle. Union-Find: no failed union, and `groups == 1`.
- "Minimum Spanning Tree" (Kruskal's algorithm): sort edges by weight and use exactly this loop.

---

## 6. Common mistakes

1. **Drawing the arrow the wrong way.** `[a, b]` in Course Schedule means "b first, then a". The arrow is `b -> a`. Say it out loud before you code.
2. **Forgetting courses that have no rules at all.** They have in-degree 0 and must start in the queue. Build the in-degree array for all `n` nodes, not only for those in the edge list.
3. **Declaring "no cycle" when the queue empties.** Check `len(order) == n`. An empty queue with unprocessed nodes means a cycle.
4. **Union-Find: comparing `parent[a] == parent[b]` instead of `find(a) == find(b)`.** `parent` is only the direct parent, not the leader.
5. **Union-Find: array of size `n` when nodes are numbered `1..n`.** Use `n + 1`.
6. **Union-Find without path compression or union by size.** Works but can be slow on a long chain (O(n) per find).
7. **Using Union-Find on a directed graph for cycle detection.** Union-Find answers questions about *undirected* connection. For directed cycles, use Kahn's or DFS colours.

---

## 7. Practice list (8 more problems)

Tags come from public LeetCode company-tag lists I read (GitHub mirror, snapshot Oct 2025; see lesson 19). A tag means "the problem is in that company's list". No tag means not verified.

| # | Problem | Difficulty | Tagged for |
|---|---|---|---|
| 1 | Number of Connected Components in an Undirected Graph (323) | Medium | Amazon |
| 2 | Graph Valid Tree (261) | Medium | not verified |
| 3 | Accounts Merge (721) | Medium | Amazon, Google, Meta, Microsoft |
| 4 | Minimum Height Trees (310) | Medium | not verified |
| 5 | Evaluate Division (399) | Medium | not verified |
| 6 | Parallel Courses III (2050) | Hard | Stripe |
| 7 | Alien Dictionary (269) | Hard | not verified |
| 8 | Redundant Connection II (685) | Hard | not verified |

---

## 8. Self-quiz (5 questions)

1. What does "in-degree 0" mean, and why do we start Kahn's algorithm with those nodes?
2. How does Kahn's algorithm tell you that a cycle exists?
3. In Union-Find, what is the leader (root) of a group, and how do you find it?
4. Name the two speed tricks of Union-Find and say in one sentence what each does.
5. You add edges one by one to an undirected graph. How do you know an edge creates a cycle?

**Answers.**
1. No arrow points into the node, so it has no prerequisites. It can be done right now. Everything else must wait for something.
2. After the queue runs empty, if the answer list has fewer than `n` nodes, the missing nodes are stuck in or behind a cycle (each waits for another one in the circle).
3. The leader is the node whose parent is itself. You find it by following parent links upward until you reach a node that is its own parent.
4. Path compression: while climbing, make nodes point closer to the leader so the next climb is short. Union by size: attach the smaller group under the bigger one so trees stay shallow.
5. If both ends of the new edge already have the same leader, they were already connected, so the new edge closes a circle.
