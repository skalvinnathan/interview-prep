# Lesson 10: Graphs, BFS and DFS (including grids)

All code is Python 3.9. Every code block in this file was run with `python3` (3.9.6) before it was written here.

---

## Words you need first

- **Graph**: dots and lines. The dots are **nodes** (also called vertices). The lines are **edges**.
- **Neighbour**: a node that shares an edge with you.
- **Adjacency list**: for each node, a list of its neighbours. In Python: `graph = {0: [1, 2], 1: [0, 3], ...}`.
- **Visited**: a set of nodes you already saw. It stops you from walking in circles forever.
- **BFS** (breadth-first search): explore **close nodes first**, then farther ones. Uses a **queue** (first in, first out).
- **DFS** (depth-first search): go **as deep as you can**, then come back. Uses **recursion** or a **stack** (last in, first out).
- **Grid**: a table of cells. Each cell is a node. Its neighbours are up, down, left, right.

---

## 1. What is this?

A graph is any set of things with connections between them: cities and roads, people and friendships, web pages and links, cells in a maze.

BFS and DFS are two ways to **walk through a graph so you visit every reachable node exactly once**.

**Analogy for BFS: a stone dropped in a pond.**
The ripple reaches nodes at distance 1 first, then distance 2, then distance 3. All nodes at the same distance are reached at the same time. This is why BFS finds the **shortest path** when every edge has the same cost.

**Analogy for DFS: exploring a maze with a ball of string.**
You walk down one corridor until it ends. Then you walk back and try the next corridor. You go deep first and back up later.

A **grid** is a graph in disguise. Cell `(row, col)` is a node. Its neighbours are `(row-1, col)`, `(row+1, col)`, `(row, col-1)`, `(row, col+1)`. You do not build the graph. You just compute neighbours on the fly.

---

## 2. When do I use it?

| Words in the problem | Idea |
|---|---|
| "grid of 0s and 1s", "islands", "regions", "connected" | DFS or BFS on the grid, count components |
| "**shortest path**", "minimum steps", "minimum moves" (all moves cost the same) | **BFS** |
| "minimum **minutes** until everything is ..." (spreading, rotting, fire) | **Multi-source BFS** (start with all sources in the queue) |
| "copy / clone a graph", "can I reach B from A?" | DFS or BFS with a visited set or map |
| "all paths", "does a path exist" | DFS |
| "word ladder", "transform one word into another by changing one letter" | BFS where each word is a node |

Choose **BFS** when you need the *fewest steps*. Choose **DFS** when you only need to *visit everything* or explore *all possibilities*.

---

## 3. Trace of a tiny example

Graph with 5 nodes. Edges: `0-1`, `0-2`, `1-3`, `2-3`, `3-4`.

```
        0
       / \
      1   2
       \ /
        3
        |
        4
```

Adjacency list: `0:[1,2]  1:[0,3]  2:[0,3]  3:[1,2,4]  4:[3]`.

BFS from node 0. `queue` is the waiting line. `dist` is the number of edges from node 0.

```
start:     queue=[0]            visited={0}            dist={0:0}
pop 0:     neighbours 1,2: both new -> add them
           queue=[1,2]          visited={0,1,2}        dist={0:0, 1:1, 2:1}
pop 1:     neighbours 0 (seen), 3 (new) -> add 3
           queue=[2,3]          visited={0,1,2,3}      dist adds 3:2
pop 2:     neighbours 0 (seen), 3 (seen) -> nothing new
           queue=[3]
pop 3:     neighbours 1 (seen), 2 (seen), 4 (new) -> add 4
           queue=[4]            visited={0,1,2,3,4}    dist adds 4:3
pop 4:     neighbour 3 (seen)
           queue=[]             -> stop
visit order: 0, 1, 2, 3, 4      distances: 0:0, 1:1, 2:1, 3:2, 4:3
```

DFS from node 0 (recursive, neighbours in list order):

```
visit 0  -> go to first neighbour 1
 visit 1  -> neighbours: 0 (seen), 3 (new) -> go to 3
  visit 3  -> neighbours: 1 (seen), 2 (new) -> go to 2
   visit 2  -> neighbours: 0 (seen), 3 (seen) -> nothing, go back to 3
  back in 3 -> next neighbour 4 (new) -> go to 4
   visit 4  -> neighbour 3 (seen) -> go back
  back in 3 -> done, back to 1 -> done, back to 0 -> next neighbour 2 (seen) -> done
visit order: 0, 1, 3, 2, 4
```

Notice: BFS visits in rings (0, then 1 and 2, then 3, then 4). DFS dives (0, 1, 3, 2, 4).

---

## 4. Template code

### 4a. BFS on an adjacency list (with distances)

```python
from collections import deque                 # deque is a fast queue


def bfs(graph, start):                        # graph is a dict: node -> list of neighbours
    visited = {start}                         # set of nodes already seen; start is seen
    dist = {start: 0}                         # distance from start, in number of edges
    order = []                                # the order in which we visit nodes
    queue = deque([start])                    # the waiting line, begins with the start node
    while queue:                              # while somebody is still waiting
        node = queue.popleft()                # take the person at the front of the line
        order.append(node)                    # record that we visit it now
        for nb in graph[node]:                # look at each neighbour of this node
            if nb not in visited:             # only if we have not seen it before
                visited.add(nb)               # mark it seen NOW (not later), to avoid duplicates in the queue
                dist[nb] = dist[node] + 1     # it is one step farther than the current node
                queue.append(nb)              # put it at the back of the line
    return order, dist                        # give back what we learned


g = {0: [1, 2], 1: [0, 3], 2: [0, 3], 3: [1, 2, 4], 4: [3]}   # the graph from the trace
order, dist = bfs(g, 0)                       # run BFS from node 0
print(order, dist)                            # shows the visit order and distances
assert order == [0, 1, 2, 3, 4]               # same as the hand trace
assert dist == {0: 0, 1: 1, 2: 1, 3: 2, 4: 3} # same as the hand trace
```

### 4b. DFS on an adjacency list (recursive)

```python
def dfs(graph, start):                        # visit all nodes reachable from start
    visited = set()                           # nodes already seen
    order = []                                # order of visiting

    def visit(node):                          # inner function: explore from this node
        visited.add(node)                     # mark seen
        order.append(node)                    # record visit order
        for nb in graph[node]:                # each neighbour
            if nb not in visited:             # skip the ones already seen
                visit(nb)                     # go deeper (recursion)

    visit(start)                              # begin at the start node
    return order                              # visit order


g = {0: [1, 2], 1: [0, 3], 2: [0, 3], 3: [1, 2, 4], 4: [3]}   # same graph
print(dfs(g, 0))                              # expect [0, 1, 3, 2, 4]
assert dfs(g, 0) == [0, 1, 3, 2, 4]           # same as the hand trace
```

### 4c. The grid walking trick

```python
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]     # down, up, right, left: the four neighbours


def neighbours(r, c, rows, cols):             # list the valid neighbour cells of (r, c)
    out = []                                  # valid cells collected here
    for dr, dc in DIRS:                       # try each direction
        nr, nc = r + dr, c + dc               # the neighbour cell
        if 0 <= nr < rows and 0 <= nc < cols: # check it is inside the grid (no negative or too-big index)
            out.append((nr, nc))              # keep it
    return out                                # done


print(neighbours(0, 0, 3, 3))                 # a corner has only 2 neighbours
assert sorted(neighbours(0, 0, 3, 3)) == [(0, 1), (1, 0)]   # check the corner
assert len(neighbours(1, 1, 3, 3)) == 4       # the centre has 4 neighbours
```

---

## 5. Classic problems

### 5.1 Number of Islands (LeetCode 200)

**In plain words.** A grid has `"1"` for land and `"0"` for water. An island is land cells joined up, down, left or right. Count the islands.

**Brute force.** There is no simple brute force. A natural first idea is "count every `1`", but that overcounts, because one island has many cells. We need to know which cells belong together.

**Better idea, slowly.**
1. Scan the grid cell by cell.
2. When you find a `1` you have not seen, you found a **new island**. Add one to the answer.
3. Immediately "sink" the whole island: run DFS from that cell and turn every connected `1` into `0` (or mark it visited). Then you will never count it again.
4. Keep scanning.

Each cell is sunk at most once. That is why this is fast.

```python
from typing import List                       # type hints


def num_islands(grid: List[List[str]]) -> int:   # count islands in the grid
    if not grid:                              # empty grid has no islands
        return 0                              # so answer is 0
    rows, cols = len(grid), len(grid[0])      # grid size
    count = 0                                 # islands found so far

    def sink(r, c):                           # turn this whole island into water
        if r < 0 or r >= rows or c < 0 or c >= cols:   # outside the grid?
            return                            # stop
        if grid[r][c] != "1":                 # water or already sunk?
            return                            # stop
        grid[r][c] = "0"                      # sink this cell so we never visit it again
        sink(r + 1, c)                        # go down
        sink(r - 1, c)                        # go up
        sink(r, c + 1)                        # go right
        sink(r, c - 1)                        # go left

    for r in range(rows):                     # scan each row
        for c in range(cols):                 # scan each column
            if grid[r][c] == "1":             # found unvisited land
                count += 1                    # it is a new island
                sink(r, c)                    # sink the whole island
    return count                              # total islands


g1 = [list("110"), list("010"), list("001")]  # our example grid (2 islands)
print(num_islands(g1))                        # expect 2
assert num_islands([list("11000"), list("11000"), list("00100"), list("00011")]) == 3   # the LeetCode example
assert num_islands([list("000"), list("000")]) == 0    # edge case: all water
assert num_islands([list("111"), list("111")]) == 1    # edge case: all land
assert num_islands([]) == 0                   # edge case: empty grid
assert num_islands([list("1")]) == 1          # edge case: one cell
```

**Trace** on the grid (rows 0 to 2, columns 0 to 2):

```
1 1 0
0 1 0
0 0 1
```

```
scan (0,0): it is 1 -> count = 1. sink(0,0):
   (0,0) -> 0. try down (1,0): it is 0, stop. up: outside. right (0,1): it is 1 -> sink it.
   (0,1) -> 0. down (1,1): it is 1 -> sink it.
   (1,1) -> 0. down (2,1): 0 stop. right (1,2): 0 stop. left (1,0): 0 stop.
   back up: all other directions stop.
grid now:   0 0 0 / 0 0 0 / 0 0 1
scan (0,1) .. (2,1): all 0, nothing.
scan (2,2): it is 1 -> count = 2. sink(2,2) -> 0.
end: count = 2
```

**Complexity.** Time O(rows x cols): each cell is looked at a few times, and each land cell is sunk once. Space O(rows x cols) in the worst case, because the recursion can go as deep as the number of land cells (a snake-shaped island).

**Edge cases.**
1. Empty grid, or a grid of all water: answer 0.
2. One huge island: recursion can get very deep. Python's default limit is about 1000 calls. Say "I would use an explicit stack or BFS to be safe" (see 5.2 for the BFS style).

**How interviewers twist it.**
- "Do not change the input grid": use a `visited` set instead of writing `"0"`.
- "Max area of an island" (LeetCode 695): make `sink` return the count of cells it sunk.
- "Count islands as land is added one cell at a time" (LeetCode 305): needs **union-find** (lesson 11).
- "Diagonals also connect": add the 4 diagonal directions.

---

### 5.2 Rotting Oranges (LeetCode 994)

**In plain words.** A grid: `0` empty, `1` fresh orange, `2` rotten orange. Every minute, a fresh orange next to a rotten one (up, down, left, right) becomes rotten. How many minutes until no fresh orange is left? If it can never happen, return `-1`.

**Brute force.** Simulate minute by minute. Each minute, scan the whole grid, find fresh oranges next to rotten ones, and rot them. Repeat until nothing changes. Cost: O((rows x cols) x minutes). It works but rescans everything.

**Better idea, slowly.**
1. Rot spreads **in rings**, like the pond ripple. That is BFS.
2. There can be **many** starting rotten oranges. That is fine: put **all** of them in the queue at the start. This is called **multi-source BFS**.
3. Process the queue **one level at a time**. One level = one minute.
4. Count the fresh oranges at the start. Each time one rots, subtract 1.
5. At the end, if fresh is still above 0, some orange was cut off: return `-1`.

```python
from collections import deque                 # queue
from typing import List                       # type hints


def oranges_rotting(grid: List[List[int]]) -> int:   # minutes until all rot, or -1
    rows, cols = len(grid), len(grid[0])      # grid size
    queue = deque()                           # holds the cells of rotten oranges
    fresh = 0                                 # how many fresh oranges exist
    for r in range(rows):                     # scan rows
        for c in range(cols):                 # scan columns
            if grid[r][c] == 2:               # a rotten orange
                queue.append((r, c))          # it is a starting point
            elif grid[r][c] == 1:             # a fresh orange
                fresh += 1                    # count it
    minutes = 0                               # time passed
    while queue and fresh > 0:                # continue while rot can spread and fresh remain
        for _ in range(len(queue)):           # handle exactly one "minute" (the current level)
            r, c = queue.popleft()            # a rotten orange
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:   # its four neighbours
                nr, nc = r + dr, c + dc       # neighbour cell
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:   # inside and fresh?
                    grid[nr][nc] = 2          # it rots now (also marks it as visited)
                    fresh -= 1                # one less fresh orange
                    queue.append((nr, nc))    # it will spread rot next minute
        minutes += 1                          # one full minute has passed
    return minutes if fresh == 0 else -1      # -1 if some orange was never reached


print(oranges_rotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]]))   # expect 4
assert oranges_rotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]]) == 4   # check the example
assert oranges_rotting([[2, 1, 1], [0, 1, 1], [1, 0, 1]]) == -1  # bottom-left orange is cut off
assert oranges_rotting([[0, 2]]) == 0         # edge case: no fresh orange at all
assert oranges_rotting([[0]]) == 0            # edge case: empty cell only
assert oranges_rotting([[1]]) == -1           # edge case: fresh orange, nothing to rot it
```

**Trace** on `[[2,1,1],[1,1,0],[0,1,1]]`. Start: rotten at `(0,0)`. Fresh = 6.

```
queue = [(0,0)]  fresh = 6  minutes = 0
minute 1: pop (0,0). Neighbours: (1,0) fresh -> rot, (0,1) fresh -> rot.
          fresh = 4, queue = [(1,0),(0,1)], minutes = 1
minute 2: pop (1,0): neighbours (1,1) fresh -> rot. pop (0,1): (0,2) fresh -> rot, (1,1) already rotten.
          fresh = 2, queue = [(1,1),(0,2)], minutes = 2
minute 3: pop (1,1): (2,1) fresh -> rot. pop (0,2): nothing new.
          fresh = 1, queue = [(2,1)], minutes = 3
minute 4: pop (2,1): (2,2) fresh -> rot.
          fresh = 0, minutes = 4
loop stops because fresh = 0. Answer 4.
```

**Complexity.** Time O(rows x cols): each cell enters the queue at most once. Space O(rows x cols): the queue could hold many cells.

**Edge cases.**
1. No fresh oranges at the start: answer 0 (even if there are no rotten ones either).
2. A fresh orange surrounded by empty cells: answer -1.

**How interviewers twist it.**
- "Walls and Gates": same multi-source BFS. Start from all gates, fill distance to nearest gate.
- "01 Matrix" (distance to the nearest 0): same idea.
- "Fire spreads and you must escape": run BFS for fire first, then BFS for the person with the time check.

---

### 5.3 Clone Graph (LeetCode 133)

**In plain words.** You get one node of a connected graph. Each node has a value and a list of neighbours. Make a **deep copy**: all new node objects, with the same shape. Return the copy of the node you were given.

**Brute force idea.** Copy a node, then copy each neighbour, then copy their neighbours... This loops forever if the graph has a cycle (A knows B, B knows A). The problem is not the copying. The problem is **knowing which nodes you already copied**.

**Better idea, slowly.**
1. Keep a dictionary `copies`: old node -> new node.
2. To clone node X:
   - If X is already in `copies`, return that copy. This stops cycles.
   - Otherwise create a new node with X's value. **Save it in `copies` immediately**, before looking at neighbours.
   - For each neighbour of X, clone it (recursion) and append the clone to the new node's neighbour list.
3. Return the copy of the starting node.

```python
from typing import Dict, List, Optional       # type hints


class Node:                                   # a graph node
    def __init__(self, val=0, neighbors=None):   # value and neighbour list
        self.val = val                        # the number stored in the node
        self.neighbors = neighbors if neighbors is not None else []   # list of neighbour nodes


def clone_graph(node: Optional[Node]) -> Optional[Node]:   # deep copy the graph
    if node is None:                          # empty graph
        return None                           # nothing to copy
    copies: Dict[Node, Node] = {}             # old node -> its copy

    def clone(old: Node) -> Node:             # copy one node (and everything reachable)
        if old in copies:                     # already copied?
            return copies[old]                # return the existing copy (this breaks cycles)
        new = Node(old.val)                   # make a new node with the same value
        copies[old] = new                     # remember it BEFORE visiting neighbours
        for nb in old.neighbors:              # go through the old node's neighbours
            new.neighbors.append(clone(nb))   # clone each and attach to the new node
        return new                            # give back the copy

    return clone(node)                        # start from the given node


def build(adj: List[List[int]]) -> Optional[Node]:   # helper: build a graph from LeetCode's adjacency list
    if not adj:                               # empty input
        return None                           # no nodes
    nodes = [Node(i + 1) for i in range(len(adj))]   # node values are 1..n
    for i, nbs in enumerate(adj):             # for each node
        nodes[i].neighbors = [nodes[j - 1] for j in nbs]   # connect to its neighbours
    return nodes[0]                           # return node 1


def to_adj(start: Optional[Node]) -> List[List[int]]:   # helper: read a graph back into adjacency lists
    if start is None:                         # empty graph
        return []                             # empty list
    seen = {}                                 # value -> list of neighbour values
    stack = [start]                           # nodes still to look at
    ids = set()                               # ids of nodes already seen
    while stack:                              # while something is left to look at
        cur = stack.pop()                     # take one
        if id(cur) in ids:                    # seen already?
            continue                          # skip it
        ids.add(id(cur))                      # mark it seen
        seen[cur.val] = [nb.val for nb in cur.neighbors]   # save its neighbour values
        stack.extend(cur.neighbors)           # look at the neighbours later
    return [seen[k] for k in sorted(seen)]    # list in order of value


original = build([[2, 4], [1, 3], [2, 4], [1, 3]])   # a square: 1-2, 2-3, 3-4, 4-1
copy = clone_graph(original)                  # clone it
print(to_adj(copy))                           # expect [[2, 4], [1, 3], [2, 4], [1, 3]]
assert to_adj(copy) == [[2, 4], [1, 3], [2, 4], [1, 3]]   # same shape
assert copy is not original                   # but a different object
assert copy.neighbors[0] is not original.neighbors[0]     # neighbours are also new objects
assert clone_graph(None) is None              # edge case: empty graph
single = clone_graph(build([[]]))             # edge case: one node, no neighbours
assert single.val == 1 and single.neighbors == []         # the copy is a lone node
```

**Trace** on a tiny graph: node 1 and node 2 are neighbours of each other.

```
clone(1): 1 not in copies. new1 = Node(1). copies = {1: new1}
   neighbour of 1 is 2 -> clone(2):
      2 not in copies. new2 = Node(2). copies = {1: new1, 2: new2}
      neighbour of 2 is 1 -> clone(1): 1 IS in copies -> return new1   (cycle stopped here)
      new2.neighbors = [new1]
      return new2
   new1.neighbors = [new2]
   return new1
result: new1 <-> new2, both new objects with the same links.
```

**Complexity.** Time O(V + E): V = nodes, E = edges. Each node is created once, and each edge is looked at once from each side. Space O(V) for the dictionary and the recursion.

**Edge cases.**
1. `None` input: return `None`.
2. One node with no neighbours: return a new lone node.

**How interviewers twist it.**
- "Do it with BFS, no recursion": same dictionary, but use a queue.
- "Copy List with Random Pointer" (LeetCode 138): the same old-to-new dictionary idea on a linked list.
- "Clone a binary tree / N-ary tree": simpler, no cycles, so no dictionary is needed.

---

### 5.4 Shortest Path in a Binary Matrix (LeetCode 1091)

**In plain words.** A square grid of 0 (open) and 1 (blocked). You start at the top-left, you want to reach the bottom-right. You may move in **8 directions** (including diagonals) through open cells. Return the length of the shortest path (count of cells on the path), or `-1`.

**Brute force.** Try all possible paths with DFS and keep the shortest. Cost: exponential, because the number of paths explodes.

**Better idea, slowly.**
1. All moves cost 1. So "shortest path" means BFS.
2. Start the queue with `(0, 0, 1)`: row, column, path length so far (1 cell counted).
3. When you pop a cell, if it is the goal, return its length. The first time BFS reaches the goal is the shortest way.
4. Otherwise push all open, unvisited neighbours with length + 1. Mark them visited **when you push them**.
5. If the queue empties, no path: return `-1`.

```python
from collections import deque                 # queue
from typing import List                       # type hints


def shortest_path_binary_matrix(grid: List[List[int]]) -> int:   # length of the shortest path or -1
    n = len(grid)                             # the grid is n by n
    if grid[0][0] == 1 or grid[n - 1][n - 1] == 1:   # start or goal is blocked
        return -1                             # impossible
    dirs = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]   # all 8 directions
    queue = deque([(0, 0, 1)])                # (row, col, number of cells on the path so far)
    visited = {(0, 0)}                        # cells already pushed
    while queue:                              # while there is something to explore
        r, c, length = queue.popleft()        # take the oldest cell in the line
        if r == n - 1 and c == n - 1:         # reached the goal?
            return length                     # first arrival is the shortest
        for dr, dc in dirs:                   # try the 8 neighbours
            nr, nc = r + dr, c + dc           # neighbour cell
            if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0 and (nr, nc) not in visited:   # valid, open, new
                visited.add((nr, nc))         # mark visited when pushing
                queue.append((nr, nc, length + 1))   # one more cell on the path
    return -1                                 # the queue ran out: no path


print(shortest_path_binary_matrix([[0, 0, 0], [1, 1, 0], [1, 1, 0]]))   # expect 4
assert shortest_path_binary_matrix([[0, 1], [1, 0]]) == 2     # a diagonal step
assert shortest_path_binary_matrix([[0, 0, 0], [1, 1, 0], [1, 1, 0]]) == 4   # example 2
assert shortest_path_binary_matrix([[1, 0, 0], [1, 1, 0], [1, 1, 0]]) == -1  # edge case: start is blocked
assert shortest_path_binary_matrix([[0]]) == 1                # edge case: start is also the goal
assert shortest_path_binary_matrix([[0, 1, 0], [1, 1, 0], [0, 0, 0]]) == -1  # edge case: start is walled in
```

**Trace** on `[[0,0,0],[1,1,0],[1,1,0]]` (goal is `(2,2)`):

```
queue=[(0,0,1)]  visited={(0,0)}
pop (0,0,1): not goal. neighbours open and new: (0,1) -> push (0,1,2).
             (1,0),(1,1) are blocked (1).
queue=[(0,1,2)]
pop (0,1,2): not goal. open and new: (0,2) -> push (0,2,3), (1,2) -> push (1,2,3).
             (0,0) visited. (1,0),(1,1) blocked.
queue=[(0,2,3),(1,2,3)]
pop (0,2,3): not goal. neighbours: (1,2) already visited, others blocked or visited.
pop (1,2,3): not goal. open and new: (2,2) -> push (2,2,4). (2,1) blocked.
pop (2,2,4): it is the goal -> return 4.
```

The path is (0,0), (0,1), (1,2), (2,2). Four cells. The diagonal step from (0,1) to (1,2) saved one move.

**Complexity.** Time O(n x n): every cell is pushed at most once, and each does 8 checks (a fixed number). Space O(n x n) for the queue and the visited set.

**Edge cases.**
1. Start or goal is blocked: `-1` at once.
2. `1 x 1` grid with `0`: answer is 1 (the path is one cell).

**How interviewers twist it.**
- "Return the actual path, not only the length": store the parent of each cell, then walk back from the goal.
- "Moves have different costs": BFS is not enough. Use Dijkstra (lesson 12).
- "You can break up to K walls" (LeetCode 1293): add `walls_used` to the state `(r, c, k)` and to `visited`.

---

## 6. Common mistakes

1. **Marking visited when you pop, not when you push (in BFS).** The same cell gets pushed many times. It may still give the right answer but can be slow or give wrong distances. Mark when you push.
2. **Forgetting `visited` in a graph with cycles.** Infinite loop or stack overflow.
3. **Checking the grid bounds after reading `grid[nr][nc]`.** Negative indexes in Python do not crash. They silently wrap to the other side, giving a wrong answer. Always check `0 <= nr < rows` first.
4. **Using DFS for shortest path.** DFS can reach a node by a long path first. Use BFS for fewest steps.
5. **Using a list as a queue** (`list.pop(0)` is O(n)). Use `collections.deque`.
6. **Mixing up `(row, col)` and `(x, y)`.** In a grid, `grid[row][col]`. Row goes down, column goes right.
7. **Not processing BFS level by level** when the answer is "number of minutes / steps". Use `for _ in range(len(queue))` to separate levels, or store the distance in the queue.

---

## 7. Practice list (8 more problems)

Tags come from public LeetCode company-tag lists I read (GitHub mirror, snapshot Oct 2025; see lesson 19). A tag means "the problem is in that company's list". No tag means not verified.

| # | Problem | Difficulty | Tagged for |
|---|---|---|---|
| 1 | Flood Fill (733) | Easy | not verified |
| 2 | Max Area of Island (695) | Medium | not verified |
| 3 | Surrounded Regions (130) | Medium | not verified |
| 4 | Pacific Atlantic Water Flow (417) | Medium | Amazon, Google, Meta, Microsoft |
| 5 | Walls and Gates (286) | Medium | not verified |
| 6 | Number of Connected Components in an Undirected Graph (323) | Medium | Amazon |
| 7 | Word Ladder (127) | Hard | Amazon, Google, Meta, Microsoft |
| 8 | Making A Large Island (827) | Hard | Meta |

---

## 8. Self-quiz (5 questions)

1. What is the difference between BFS and DFS in one sentence each? Which data structure does each use?
2. Why does BFS find the shortest path when all edges cost the same?
3. In a graph with a cycle, what goes wrong if you skip the `visited` set?
4. In Rotting Oranges, why do we put **all** rotten oranges in the queue at the start?
5. What is the time complexity of Number of Islands on an `R x C` grid, and why is it not `O((R x C)^2)`?

**Answers.**
1. BFS explores nearest nodes first, using a queue. DFS goes as deep as possible first, using recursion or a stack.
2. BFS reaches nodes in rings: all nodes at distance 1, then all at distance 2, and so on. The first time you reach a node is by the fewest edges.
3. You walk around the cycle forever (infinite loop) or the recursion never ends.
4. All rotten oranges spread rot at the same time. Starting them together in one queue means each level of BFS equals one minute for all of them (multi-source BFS).
5. O(R x C). Each cell is sunk at most once, so after it is sunk, later scans skip it. The scan itself visits each cell once.
