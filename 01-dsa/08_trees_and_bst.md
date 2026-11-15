# Lesson 08. Trees and Binary Search Trees (BST)

Before this lesson: [00_how_to_start.md](00_how_to_start.md). Lesson 05 (stack, queue) and lesson 07 (linked lists) help.

**How to run the code in this lesson.** Put all the Python blocks of this lesson in ONE file, from top to bottom. The first block (Template A) defines `TreeNode`, `build_tree` and `tree_to_list`. The later blocks use them.

---

## 1. What is this?

A **tree** is a shape where one item (the **root**) has children, and those children have their own children. There are no loops.

**Analogy 1: a family tree.** Grandfather at the top. His children below. Their children below them.

**Analogy 2: folders on your computer.** A folder contains folders, which contain more folders and files.

Words you must know:

| Word | Meaning |
|---|---|
| **root** | the top node |
| **node** | one item in the tree |
| **child / parent** | a node below / above another node |
| **leaf** | a node with no children |
| **depth of a node** | number of steps from the root to that node |
| **height of a tree** | the number of levels (the longest path from root to a leaf) |
| **subtree** | a node together with everything below it |

A **binary tree** is a tree where each node has at most TWO children: `left` and `right`.

A **binary search tree (BST)** is a binary tree with an order rule. For EVERY node:

- everything in its LEFT subtree is **smaller** than the node, and
- everything in its RIGHT subtree is **bigger** than the node.

```text
Our sample tree (it is a BST):

        4
       / \
      2   6
     / \ / \
    1  3 5  7
```

Why is a BST useful? To find a value, you go left or right at each node and throw away half the tree. It is like binary search (lesson 06) in tree shape: O(height) steps, which is O(log n) when the tree is balanced.

In code, a node looks like this:

```text
class TreeNode:
    val   = the value
    left  = the left child, or None
    right = the right child, or None
```

### Recursion explained step by step

Most tree problems use **recursion**: a function that calls itself on a SMALLER version of the problem.

**Analogy: asking the person behind you.** You stand in a line and want to know how many people are in the line behind you. You cannot see the end. So you ask the person behind: "How many people are behind YOU?" That person asks the next one, and so on. The last person says "zero". Each person adds 1 and answers back. The answer travels back to you.

Every recursive function has THREE parts:

1. **Base case.** The smallest problem, answered directly. For trees: an empty tree (`None`). Without a base case, the function never stops.
2. **Trust.** Assume the function already works for the left child and the right child. Do not trace them in your head. Just call them.
3. **Combine.** Use the answers from the left and right to make the answer for the current node.

Example: the **height** of a tree.

- Base case: an empty tree has height 0.
- Trust: `left_h = height(left)`, `right_h = height(right)` are correct.
- Combine: this node adds one level: `1 + max(left_h, right_h)`.

```text
Tree:     3
         / \
        9   20
           /  \
          15   7

height(3)
 |-- height(9)            -> its children are None: height(None)=0, height(None)=0 -> 1 + max(0,0) = 1
 |-- height(20)
 |     |-- height(15)     -> 1 + max(0,0) = 1
 |     |-- height(7)      -> 1 + max(0,0) = 1
 |     '-- answer         -> 1 + max(1,1) = 2
 '-- answer: 1 + max(1, 2) = 3
```

The computer keeps a **call stack**: a pile of unfinished function calls. A call waits until the calls below it return. Memory use of recursion = the deepest pile = the height of the tree.

Warning: Python allows about 1000 nested calls by default. A very skewed tree (a long chain) can crash recursion. Then use a stack (iterative).

## 2. When do I use it?

Words that give it away:

- "binary tree", "root", "node", "left", "right", "subtree"
- "BST" / "binary search tree" / "sorted" / "in order"
- "depth", "height", "diameter", "path", "ancestor"
- "level by level", "layers" (BFS with a queue)
- "for every node, check ..." (recursion)

A good habit: for each tree problem ask, "What do I need from my left child and my right child to answer for this node?" That sentence is your recursive function.

Which traversal?

| Need | Use |
|---|---|
| copy the tree, or node before its children | preorder (node, left, right) |
| sorted values from a BST | **inorder** (left, node, right) |
| answer needs children first (height, delete) | postorder (left, right, node) |
| level by level, shortest path | level order (BFS, a queue) |

## 3. A tiny example, traced line by line

Traversals of the sample tree:

```text
        4
       / \
      2   6
     / \ / \
    1  3 5  7
```

**Inorder** (left, node, right). Call `inorder(4)`:

```text
inorder(4): first go left -> inorder(2)
  inorder(2): first go left -> inorder(1)
    inorder(1): left is None, nothing. ADD 1.  right is None, nothing.         out = [1]
  back in 2: ADD 2.                                                             out = [1, 2]
  go right -> inorder(3): ADD 3.                                                out = [1, 2, 3]
back in 4: ADD 4.                                                               out = [1, 2, 3, 4]
go right -> inorder(6)
  inorder(5): ADD 5.                                                            out = [1, 2, 3, 4, 5]
  back in 6: ADD 6.                                                             out = [1, 2, 3, 4, 5, 6]
  inorder(7): ADD 7.                                                            out = [1, 2, 3, 4, 5, 6, 7]
```

The inorder of a BST is always **sorted**. Remember this: it solves many BST problems.

The other orders on the same tree:

```text
preorder   (node, left, right): 4 2 1 3 6 5 7
inorder    (left, node, right): 1 2 3 4 5 6 7
postorder  (left, right, node): 1 3 2 5 7 6 4
level order (row by row):       [4] [2, 6] [1, 3, 5, 7]
```

## 4. Template code (a comment on every line)

```python
# TEMPLATE A: the node class and two helpers (used by all later blocks)
from collections import deque                       # deque is a queue we need for building and printing

class TreeNode:                                     # one node of a binary tree
    def __init__(self, val=0, left=None, right=None):   # create a node
        self.val = val                              # the stored value
        self.left = left                            # the left child (None if missing)
        self.right = right                          # the right child (None if missing)

def build_tree(values):                             # build a tree from a level-order list; None means "no node"
    if not values or values[0] is None:             # empty input means an empty tree
        return None                                 # no root
    root = TreeNode(values[0])                      # the first value is the root
    queue = deque([root])                           # nodes waiting to get their children
    i = 1                                           # index of the next value to use
    while queue and i < len(values):                # while nodes wait and values remain
        node = queue.popleft()                      # take the next node from the front
        if i < len(values) and values[i] is not None:       # is there a left child value?
            node.left = TreeNode(values[i])         # create the left child
            queue.append(node.left)                 # it will get children later
        i += 1                                      # move to the next value
        if i < len(values) and values[i] is not None:       # is there a right child value?
            node.right = TreeNode(values[i])        # create the right child
            queue.append(node.right)                # it will get children later
        i += 1                                      # move to the next value
    return root                                     # the finished tree

def tree_to_list(root):                             # turn a tree back into a level-order list (for tests)
    out = []                                        # the answer
    queue = deque([root])                           # start with the root
    while queue:                                    # while nodes remain
        node = queue.popleft()                      # take the front node
        if node is None:                            # a missing child
            out.append(None)                        # record it as None
        else:                                       # a real node
            out.append(node.val)                    # record its value
            queue.append(node.left)                 # queue the left child (may be None)
            queue.append(node.right)                # queue the right child (may be None)
    while out and out[-1] is None:                  # remove the Nones at the end
        out.pop()                                   # they carry no information
    return out                                      # the level-order list

sample = build_tree([4, 2, 6, 1, 3, 5, 7])          # our sample BST
print(tree_to_list(sample))                         # expect [4, 2, 6, 1, 3, 5, 7]
assert tree_to_list(sample) == [4, 2, 6, 1, 3, 5, 7]    # round trip works
assert tree_to_list(build_tree([])) == []           # empty tree
assert tree_to_list(build_tree([1, None, 2])) == [1, None, 2]   # a missing left child
```

```python
# TEMPLATE B: recursive depth-first traversals (preorder, inorder, postorder)
def preorder(node, out):                            # visit: node, then left, then right
    if node is None:                                # base case: empty tree
        return                                      # nothing to do
    out.append(node.val)                            # visit the node first
    preorder(node.left, out)                        # then the whole left subtree
    preorder(node.right, out)                       # then the whole right subtree

def inorder(node, out):                             # visit: left, then node, then right
    if node is None:                                # base case: empty tree
        return                                      # nothing to do
    inorder(node.left, out)                         # the whole left subtree first
    out.append(node.val)                            # then the node itself
    inorder(node.right, out)                        # then the whole right subtree

def postorder(node, out):                           # visit: left, then right, then node
    if node is None:                                # base case: empty tree
        return                                      # nothing to do
    postorder(node.left, out)                       # the whole left subtree first
    postorder(node.right, out)                      # then the whole right subtree
    out.append(node.val)                            # the node last

a, b, c = [], [], []                                # three result lists
preorder(sample, a)                                 # fill a
inorder(sample, b)                                  # fill b
postorder(sample, c)                                # fill c
print(a, b, c)                                      # show all three
assert a == [4, 2, 1, 3, 6, 5, 7]                   # preorder
assert b == [1, 2, 3, 4, 5, 6, 7]                   # inorder: sorted for a BST
assert c == [1, 3, 2, 5, 7, 6, 4]                   # postorder
```

```python
# TEMPLATE C: "answer from the children" pattern (height of a tree)
def height(node):                                   # function: number of levels below and including node
    if node is None:                                # base case: an empty tree has height 0
        return 0                                    # no levels
    left_h = height(node.left)                      # trust: the height of the left subtree
    right_h = height(node.right)                    # trust: the height of the right subtree
    return 1 + max(left_h, right_h)                 # combine: this node adds one level

tree = build_tree([3, 9, 20, None, None, 15, 7])    # the tree from the drawing above
print(height(tree))                                 # expect 3
assert height(tree) == 3                            # check
assert height(None) == 0                            # empty tree
assert height(build_tree([1])) == 1                 # one node
```

```python
# TEMPLATE D: inorder traversal WITHOUT recursion (using our own stack)
def inorder_iterative(root):                        # function: inorder values using a stack
    result = []                                     # the answer
    stack = []                                      # nodes we have passed but not yet visited
    curr = root                                     # the node we are looking at
    while curr or stack:                            # while there is work to do
        while curr:                                 # go as far left as possible
            stack.append(curr)                      # remember the path back
            curr = curr.left                        # step to the left child
        curr = stack.pop()                          # the last remembered node: leftmost not yet visited
        result.append(curr.val)                     # visit it
        curr = curr.right                           # then handle its right subtree
    return result                                   # sorted order for a BST

print(inorder_iterative(sample))                    # expect [1, 2, 3, 4, 5, 6, 7]
assert inorder_iterative(sample) == [1, 2, 3, 4, 5, 6, 7]   # same as the recursive version
assert inorder_iterative(None) == []                # empty tree
```

Time for all traversals: O(n) (every node is visited once). Space: O(h), where h is the height of the tree: that is O(log n) for a balanced tree and O(n) for a chain.

---

## 5. Classic problems

### Problem 1. Invert Binary Tree

**Problem in plain words.** Mirror the tree: swap the left and right child of EVERY node. Return the root.

Example: `[4, 2, 7, 1, 3, 6, 9]` becomes `[4, 7, 2, 9, 6, 3, 1]`.

**Brute force.** Build a brand new mirrored copy of the tree, node by node. This is O(n) time but O(n) extra memory. (Honest note: here the simple recursion below is already the best idea, and it needs no extra tree.)

**Better idea, slowly.** Think recursively:

- Base case: an empty tree stays empty.
- Trust: `invert(root.left)` returns the mirrored left subtree, and `invert(root.right)` the mirrored right subtree.
- Combine: put the mirrored RIGHT subtree on the left, and the mirrored LEFT subtree on the right.

```python
def invert_tree(root):
    if root is None:                                  # base case: nothing to invert
        return None                                   # an empty tree stays empty
    inverted_left = invert_tree(root.left)            # trust: the left subtree, mirrored
    inverted_right = invert_tree(root.right)          # trust: the right subtree, mirrored
    root.left = inverted_right                        # combine: the mirrored right side goes left
    root.right = inverted_left                        # and the mirrored left side goes right
    return root                                       # return the same root node

result = invert_tree(build_tree([4, 2, 7, 1, 3, 6, 9]))      # run the example
print(tree_to_list(result))                           # expect [4, 7, 2, 9, 6, 3, 1]
assert tree_to_list(result) == [4, 7, 2, 9, 6, 3, 1]  # example
assert tree_to_list(invert_tree(build_tree([2, 1, 3]))) == [2, 3, 1]    # small tree
assert invert_tree(None) is None                      # empty tree
assert tree_to_list(invert_tree(build_tree([1, 2]))) == [1, None, 2]    # one child moves to the other side
```

**Trace** on `[2, 1, 3]` (root 2, left child 1, right child 3):

```text
invert(2)
  invert(2.left = 1): both children are None -> returns node 1 unchanged
  invert(2.right = 3): both children are None -> returns node 3 unchanged
  now: 2.left = node 3, 2.right = node 1
  return node 2
result: 2 with left 3 and right 1  ->  [2, 3, 1]
```

**Complexity.** Time O(n): every node is visited once. Space O(h): the call stack (h = height).

**Two edge cases.** (1) Empty tree: return `None`. (2) A node with only one child: the child moves to the other side (`[1, 2]` becomes `[1, None, 2]`). A chain-shaped tree is inverted into a chain on the other side.

**How interviewers twist it.** "Do it without recursion (queue or stack)." "Is the tree symmetric?" "Are two trees the same?" "Flip equivalent binary trees."

---

### Problem 2. Diameter of Binary Tree

**Problem in plain words.** The **diameter** is the length (counted in EDGES, not nodes) of the longest path between any two nodes. The path does not have to pass through the root.

Example: `[1, 2, 3, 4, 5]` gives `3` (the path 4 -> 2 -> 1 -> 3, which has 3 edges).

**Brute force.** For every node, compute the height of its left and right subtree separately, then add them. Height costs O(n), and doing it for every node makes O(n^2) in the worst case (a chain).

**Better idea, slowly.** The longest path that turns at a node goes down the deepest left side and the deepest right side. Its length is `left_height + right_height`. So:

1. Write the `height` function (Template C).
2. While computing the height of each node, ALSO check "what is the path that turns here?" = `left_h + right_h`. Keep the biggest such number in a variable `best`.
3. Return `best` at the end.

So we compute heights once and collect diameters on the way. This is the "answer from the children" pattern with a side variable.

```python
def diameter_of_binary_tree(root):
    best = [0]                                        # a list so the inner function can change it

    def depth(node):                                  # returns the height of node; updates best on the way
        if node is None:                              # base case: empty tree
            return 0                                  # height 0
        left_h = depth(node.left)                     # trust: height of the left side
        right_h = depth(node.right)                   # trust: height of the right side
        best[0] = max(best[0], left_h + right_h)      # the longest path that turns at this node
        return 1 + max(left_h, right_h)               # height of this node for its parent

    depth(root)                                       # run the recursion from the root
    return best[0]                                    # the longest path found, in edges

print(diameter_of_binary_tree(build_tree([1, 2, 3, 4, 5])))   # expect 3
assert diameter_of_binary_tree(build_tree([1, 2, 3, 4, 5])) == 3   # example
assert diameter_of_binary_tree(build_tree([1])) == 0               # one node: no edges
assert diameter_of_binary_tree(None) == 0                          # empty tree
assert diameter_of_binary_tree(build_tree([1, 2])) == 1            # two nodes: one edge
assert diameter_of_binary_tree(build_tree([1, 2, None, 3, 4, 5, None, None, 6])) == 4   # path 5-3-2-4-6 skips the root
```

**Trace** on `[1, 2, 3, 4, 5]` (node 1 has children 2 and 3; node 2 has children 4 and 5):

```text
depth(1)
  depth(2)
    depth(4): leaf. left_h=0, right_h=0.  best = max(0, 0) = 0.  returns 1
    depth(5): leaf. left_h=0, right_h=0.  best = 0.              returns 1
    at node 2: left_h=1, right_h=1.  best = max(0, 1+1) = 2.     returns 2
  depth(3): leaf. best stays 2.                                   returns 1
  at node 1: left_h=2, right_h=1.  best = max(2, 2+1) = 3.       returns 3
answer = 3
```

**Complexity.** Time O(n): every node once. Space O(h): the call stack.

**Two edge cases.** (1) A single node: the diameter is 0 edges. (2) The longest path can skip the root (last test above). That is why we update `best` at EVERY node, not only at the root.

**How interviewers twist it.** "Binary Tree Maximum Path Sum" (the same pattern, but with node values and negative numbers). "Longest univalue path." "Diameter of an N-ary tree."

---

### Problem 3. Binary Tree Level Order Traversal

**Problem in plain words.** Return the node values level by level, from left to right, as a list of lists.

Example: `[3, 9, 20, None, None, 15, 7]` gives `[[3], [9, 20], [15, 7]]`.

**Brute force / alternative.** A recursive depth-first walk that carries the `depth` and appends each value to `levels[depth]`. It is also O(n). The standard answer is a queue (BFS), which matches "level by level" more naturally.

**Better idea, slowly (BFS with a queue).** A queue is first in, first out. Put the root in the queue. Repeat: for the current level, you know how many nodes are in the queue right now (`size`). Take exactly `size` nodes out, record their values, and put their children in the queue. The children are the next level.

```python
from collections import deque                        # deque is a fast queue

def level_order(root):
    if root is None:                                 # empty tree
        return []                                    # no levels
    result = []                                      # list of levels
    queue = deque([root])                            # start with the root in the queue
    while queue:                                     # while there are nodes to process
        size = len(queue)                            # how many nodes are in the CURRENT level
        level = []                                   # values of this level
        for _ in range(size):                        # process exactly one level
            node = queue.popleft()                   # take the front node
            level.append(node.val)                   # record its value
            if node.left:                            # does it have a left child?
                queue.append(node.left)              # queue it for the next level
            if node.right:                           # does it have a right child?
                queue.append(node.right)             # queue it for the next level
        result.append(level)                         # save this level
    return result                                    # all levels

print(level_order(build_tree([3, 9, 20, None, None, 15, 7])))    # expect [[3], [9, 20], [15, 7]]
assert level_order(build_tree([3, 9, 20, None, None, 15, 7])) == [[3], [9, 20], [15, 7]]   # example
assert level_order(None) == []                       # empty tree
assert level_order(build_tree([1])) == [[1]]         # one node
assert level_order(build_tree([1, 2, None, 3])) == [[1], [2], [3]]   # a chain: one node per level
```

**Trace** on `[3, 9, 20, None, None, 15, 7]`:

```text
queue = [3]
round 1: size = 1. take 3 -> level [3]. queue gets 9 and 20.       queue = [9, 20].        result = [[3]]
round 2: size = 2. take 9 -> no children. take 20 -> adds 15, 7.   level [9, 20]. queue = [15, 7].  result = [[3], [9, 20]]
round 3: size = 2. take 15, take 7 -> no children.                 level [15, 7]. queue = [].        result = [[3], [9, 20], [15, 7]]
queue is empty -> stop.
```

**Complexity.** Time O(n): each node enters and leaves the queue once. Space O(w): the queue holds at most one full level (w = the widest level; up to about n/2).

**Two edge cases.** (1) Empty tree: return `[]` (not `[[]]`). (2) Skewed chain: each level has one node.

**How interviewers twist it.** "Zigzag level order" (reverse every second level). "Right side view" (the last value of each level). "Average of each level." "Bottom-up level order." "Minimum depth." The `size = len(queue)` trick appears in all of them.

---

### Problem 4. Validate Binary Search Tree

**Problem in plain words.** Is the tree a valid BST? Remember: for EVERY node, everything on its left is smaller and everything on its right is bigger (strictly: no equal values here).

Example: `[2, 1, 3]` is valid. `[5, 1, 4, None, None, 3, 6]` is NOT valid: node 3 sits in the right subtree of 5, but 3 < 5.

**Brute force.** For every node, scan its whole left subtree (all values must be smaller) and its whole right subtree (all values must be bigger). O(n^2) in the worst case.

**A common wrong idea.** Check only `node.left.val < node.val < node.right.val` for each node. This misses the case above: node 4 is fine with its children 3 and 6 (3 < 4 < 6), but 3 must also be bigger than 5.

**Better idea, slowly.** Pass a **range** down the tree. Each node must be strictly between `low` and `high`.

- At the root the range is (minus infinity, plus infinity).
- Going LEFT from a node with value `v`: the new upper limit is `v`. (Everything on the left must be smaller than `v`.)
- Going RIGHT: the new lower limit is `v`.

If any node is outside its range, it is not a BST.

```python
def is_valid_bst(root, low=float("-inf"), high=float("inf")):
    if root is None:                                  # base case: an empty tree is a valid BST
        return True                                   # nothing can be wrong
    if not (low < root.val < high):                   # is this value outside its allowed range?
        return False                                  # then the tree is not a BST
    left_ok = is_valid_bst(root.left, low, root.val)  # left side: values must be below root.val
    right_ok = is_valid_bst(root.right, root.val, high)   # right side: values must be above root.val
    return left_ok and right_ok                       # both sides must be valid

print(is_valid_bst(build_tree([2, 1, 3])))            # expect True
assert is_valid_bst(build_tree([2, 1, 3])) is True    # example 1
assert is_valid_bst(build_tree([5, 1, 4, None, None, 3, 6])) is False    # example 2
assert is_valid_bst(build_tree([2, 2, 2])) is False   # equal values are not allowed
assert is_valid_bst(build_tree([1])) is True          # one node
assert is_valid_bst(None) is True                     # empty tree
assert is_valid_bst(sample) is True                   # our sample tree
assert is_valid_bst(build_tree([5, 4, 6, None, None, 3, 7])) is False    # 3 is inside the right side of 5
```

**Trace** on `[5, 1, 4, None, None, 3, 6]`:

```text
check(5, low=-inf, high=+inf): is -inf < 5 < +inf? yes.
  check(1, low=-inf, high=5):  is -inf < 1 < 5?   yes. Its children are None -> True.
  check(4, low=5,   high=+inf): is 5 < 4 < +inf?  NO -> return False.
result: False
```

And on `[2, 1, 3]`:

```text
check(2, -inf, +inf): ok.
  check(1, -inf, 2): -inf < 1 < 2 ok.  children None -> True
  check(3, 2, +inf): 2 < 3 < +inf ok.  children None -> True
result: True
```

**Complexity.** Time O(n): each node is checked once. Space O(h): the call stack.

**Another way (good to mention).** The inorder traversal of a valid BST is strictly increasing. So do an inorder walk and check that each value is bigger than the previous one.

**Two edge cases.** (1) Duplicates such as `[2, 2, 2]`: invalid (we use strict `<`). Ask the interviewer if duplicates are allowed. (2) Use `float("-inf")` and `float("inf")`, not a number like 0 or `-2**31`, because node values can be very small or very large.

**How interviewers twist it.** "Kth smallest element in a BST" (inorder walk). "Recover a BST where two nodes were swapped." "BST iterator." "Convert a sorted array to a balanced BST." "Lowest common ancestor of a BST."

---

### Problem 5. Lowest Common Ancestor of a Binary Tree

**Problem in plain words.** Given two nodes `p` and `q` in a binary tree, find their **lowest common ancestor (LCA)**: the lowest node that has both `p` and `q` below it. A node counts as its own descendant.

Example: tree `[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4]`. The LCA of 5 and 1 is 3. The LCA of 5 and 4 is 5 (because 4 is below 5).

**Brute force.** Find the path from the root to `p` and the path from the root to `q` (store them as lists). Walk both lists together; the last node that is the same is the LCA. O(n) time and O(n) space for the paths.

**Better idea, slowly (one recursive walk).** Define `lca(node)` as: "returns `p` or `q` if it is found in this subtree (or their LCA if both are), else `None`."

- Base case: if `node` is `None`, return `None`. If `node` is `p` or `q`, return `node` (we found one; no need to go deeper, because if the other is below, this node is the LCA).
- Trust: ask the left subtree and the right subtree.
- Combine:
  - If BOTH sides returned something, then `p` is on one side and `q` is on the other, so THIS node is the LCA.
  - If only one side returned something, pass it up.

```python
def lowest_common_ancestor(root, p, q):
    if root is None or root is p or root is q:        # base case: nothing here, or we found p or q
        return root                                   # return what we found (None, p or q)
    left = lowest_common_ancestor(root.left, p, q)    # trust: result from the left subtree
    right = lowest_common_ancestor(root.right, p, q)  # trust: result from the right subtree
    if left and right:                                # p and q were found on different sides
        return root                                   # so this node is the lowest common ancestor
    return left if left else right                    # otherwise pass up whichever side found something

def find(root, val):                                  # test helper: return the node with this value
    if root is None:                                  # reached the bottom
        return None                                   # not found here
    if root.val == val:                               # this is the node
        return root                                   # return it
    return find(root.left, val) or find(root.right, val)    # search left, then right

big = build_tree([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])    # the example tree
assert lowest_common_ancestor(big, find(big, 5), find(big, 1)).val == 3    # different sides: the root
assert lowest_common_ancestor(big, find(big, 5), find(big, 4)).val == 5    # q is below p
assert lowest_common_ancestor(big, find(big, 6), find(big, 4)).val == 5    # both below node 5
assert lowest_common_ancestor(big, find(big, 7), find(big, 7)).val == 7    # p and q are the same node
print("LCA ok")
```

**Trace** for `p = 6`, `q = 4` (the answer should be 5):

```text
lca(3)
  left = lca(5)
    left = lca(6)  -> node 6 is p -> returns 6
    right = lca(2)
        left = lca(7)  -> 7 is not p or q, no children -> returns None
        right = lca(4) -> node 4 is q -> returns 4
        only the right side found something -> returns 4
    at node 5: left = 6 and right = 4 are both found -> node 5 is the LCA. returns 5
  right = lca(1)
    lca(0) -> None, lca(8) -> None  -> returns None
  at node 3: left = 5, right = None -> only left found something -> returns 5
answer: node 5
```

**Complexity.** Time O(n): every node is visited at most once. Space O(h): the call stack.

**Two edge cases.** (1) `p` is an ancestor of `q` (for example 5 and 4): we return `p` as soon as we meet it, which is right, because `q` is below it. (2) `p` and `q` are the same node: the answer is that node.

**How interviewers twist it.** "LCA of a BST" (faster: if both values are smaller than the node, go left; if both bigger, go right; else this node is the LCA; O(h)). "Nodes have parent pointers" (like the intersection of two linked lists). "One of the nodes may not exist." "LCA of the deepest leaves."

---

## 6. Common mistakes

1. **No base case**, or a wrong one (`root.left is None` instead of `root is None`). The function crashes on `None.val`.
2. **Forgetting to `return` the result of the recursive call.** The function gives `None`.
3. **Validating a BST by comparing only parent and child** (the wrong idea shown above).
4. **Mixing up nodes and values.** `root.val` is a number; `root` is a node.
5. **Using `queue.pop(0)` on a list** for BFS. Use `deque.popleft()`.
6. **Forgetting `size = len(queue)`** in level order. The levels get mixed.
7. **Counting nodes instead of edges** (diameter) or edges instead of nodes (height). Read the question.
8. **Deep recursion crash** on a chain with 100,000 nodes. Use an iterative version with a stack.

## 7. Practice list (8 more problems)

"Asked at" means the problem appears on that company's list in the community repo [liquidslr/leetcode-company-wise-problems](https://github.com/liquidslr/leetcode-company-wise-problems) (checked 2026-11-15). Difficulty is the LeetCode label from the same data.

| # | Problem | Difficulty | Asked at (per those lists) |
|---|---|---|---|
| 1 | Maximum Depth of Binary Tree | Easy | Amazon, Google, Meta, Microsoft |
| 2 | Same Tree | Easy | Amazon, Google, Meta, Microsoft |
| 3 | Symmetric Tree | Easy | Amazon, Google, Meta, Microsoft |
| 4 | Path Sum | Easy | Amazon, Google, Meta, Microsoft |
| 5 | Binary Tree Right Side View | Medium | Amazon, Google, Meta, Microsoft |
| 6 | Kth Smallest Element in a BST | Medium | Amazon, Google, Meta, Microsoft |
| 7 | Lowest Common Ancestor of a Binary Search Tree | Medium | Amazon, Google, Meta, Microsoft |
| 8 | Binary Tree Maximum Path Sum | Hard | Amazon, Google, Meta, Microsoft |

## 8. Self-quiz (5 questions)

1. What are the three parts of every recursive function?
2. What order does an inorder traversal visit nodes in? What do you get from a BST?
3. In level order traversal, why do we save `size = len(queue)` before the inner loop?
4. Why is comparing only a node with its direct children not enough to validate a BST?
5. In the LCA solution, what does it mean when BOTH `left` and `right` are not `None`?

### Answers

1. A base case (the smallest problem), trust (the function already works for the children), and combine (build the answer for this node from the children's answers).
2. Left subtree, then the node, then the right subtree. For a BST, the values come out sorted from small to big.
3. Because the queue grows while we add children. `size` tells us how many nodes belong to the current level, so we stop after exactly one level.
4. A value deep in the left subtree can still be bigger than an ancestor higher up (or the reverse for the right side). We must carry the allowed range `(low, high)` from all ancestors.
5. `p` was found in one side and `q` in the other side. So the current node is the lowest node that has both below it: it is the LCA.

---

You finished the first 8 lessons. Next steps: redo the hardest problem of each lesson from memory after one day, then after one week. When these feel easy, the next patterns to learn are heaps, graphs (BFS/DFS on grids), backtracking, and dynamic programming.

Back to the start: [00_how_to_start.md](00_how_to_start.md)
