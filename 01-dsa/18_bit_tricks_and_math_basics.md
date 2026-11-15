# Lesson 18: Bit Tricks and Math Basics (short)

All code is Python 3.9. Every code block in this file was run with `python3` (3.9.6) before it was written here.

This lesson is short on purpose. These topics are asked less often, but when they come, they are quick wins if you know three or four tricks.

---

## Words you need first

- **Bit**: one binary digit. It is `0` or `1`.
- **Binary number**: a number written with bits. `13` in binary is `1101` because `8 + 4 + 0 + 1 = 13`.
- **Set bit**: a bit that is `1`.
- **Bitwise operator**: an operator that works on every bit of a number separately.
  - `a & b` (AND): the bit is 1 only if **both** bits are 1.
  - `a | b` (OR): the bit is 1 if **at least one** bit is 1.
  - `a ^ b` (XOR): the bit is 1 if the two bits are **different**.
  - `~a` (NOT): flips every bit.
  - `a << k` (left shift): move bits left by `k`. It multiplies by `2^k`.
  - `a >> k` (right shift): move bits right by `k`. It divides by `2^k` (rounding down).
- **Mask**: a number used to pick or clear some bits.
- **GCD**: the greatest common divisor, the biggest number that divides both numbers exactly. `gcd(12, 18) = 6`.
- **Modulo** (`%`): the remainder after division. `17 % 5 = 2`.
- **Prime**: a number above 1 whose only divisors are 1 and itself. 2, 3, 5, 7, 11...

---

## 1. What is this?

**Analogy for bits: a row of light switches.**
A number is a row of switches. `13` is `1101`: switches 3, 2, and 0 are ON. Bit tricks flip or check switches directly, which is very fast and often needs no extra memory.

**The truth table for XOR is the most important one** in interviews:

| a | b | a ^ b |
|---|---|---|
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 0 |

Three facts follow from it:
1. `x ^ x = 0` (a number cancels itself).
2. `x ^ 0 = x` (zero changes nothing).
3. XOR does not care about order: `a ^ b ^ a = b`.

So if you XOR a whole list where every number appears twice except one, **all the pairs cancel and only the lonely number is left**.

**Analogy for math basics: a calculator's shortcuts.**
Euclid's algorithm finds the GCD with a few divisions. A sieve finds all primes up to N by crossing out multiples. Fast power uses the binary digits of the exponent. None of them need clever new ideas. They are recipes to remember.

---

## 2. When do I use it?

| Words in the problem | Idea |
|---|---|
| "every element appears **twice except one**" | XOR everything |
| "**without extra space**" and a tricky counting problem | XOR or bit tricks |
| "count the **number of 1 bits**", "Hamming weight" | `n & (n - 1)` loop |
| "is it a **power of two**" | `n > 0 and n & (n - 1) == 0` |
| "**missing number** in 0..n" | XOR with indexes, or the sum formula |
| "compute `x` to the power `n`" | Fast exponentiation (square the base, halve the exponent) |
| "**GCD**", "LCM", "simplify a fraction" | Euclid's algorithm |
| "count **primes** below N" | Sieve of Eratosthenes |
| "answer modulo 10^9 + 7" | Take `%` after every multiply or add |
| "subsets of a small set (n at most 20)" | Loop over bitmasks `0 .. 2^n - 1` |

---

## 3. Trace of a tiny example: XOR to find the lonely number

`nums = [4, 1, 2, 1, 2]`. Everything appears twice except `4`.

```
binary:  4 = 100    1 = 001    2 = 010

start:      result = 0                 (000)
take 4:     0 ^ 4 = 4                  (000 ^ 100 = 100)
take 1:     4 ^ 1 = 5                  (100 ^ 001 = 101)
take 2:     5 ^ 2 = 7                  (101 ^ 010 = 111)
take 1:     7 ^ 1 = 6                  (111 ^ 001 = 110)   <- the second 1 cancels the first 1
take 2:     6 ^ 2 = 4                  (110 ^ 010 = 100)   <- the second 2 cancels the first 2
answer = 4
```

---

## 4. Template code

### 4a. Bit operations cheat sheet

```python
n = 13                                        # binary 1101
print(bin(n))                                 # bin() shows the binary text: 0b1101
print(n & 1)                                  # last bit: 1 means odd, 0 means even -> 1
print((n >> 2) & 1)                           # check bit number 2 (count from 0 on the right) -> 1
print(n | (1 << 1))                           # set bit 1 to ON: 1101 | 0010 = 1111 -> 15
print(n & ~(1 << 0))                          # clear bit 0 (turn it OFF): 1101 & 1110 = 1100 -> 12
print(n ^ (1 << 3))                           # flip bit 3: 1101 ^ 1000 = 0101 -> 5
print(n & (n - 1))                            # clear the lowest ON bit: 1101 & 1100 = 1100 -> 12
print(n & -n)                                 # keep only the lowest ON bit: 0001 -> 1
print(1 << 4)                                 # 2 to the power 4 -> 16
print(40 >> 3)                                # 40 divided by 8 -> 5
assert n & 1 == 1                             # 13 is odd
assert (n >> 2) & 1 == 1                      # bit 2 is ON
assert n | (1 << 1) == 15                     # set bit 1
assert n & ~(1 << 0) == 12                    # clear bit 0
assert n ^ (1 << 3) == 5                      # flip bit 3
assert n & (n - 1) == 12                      # clear the lowest ON bit
assert n & -n == 1                            # isolate the lowest ON bit
assert (1 << 4) == 16 and (40 >> 3) == 5      # shifts multiply and divide by powers of two
```

### 4b. Math cheat sheet: gcd, prime test, sieve

```python
def gcd(a, b):                                # Euclid's algorithm
    while b:                                  # until the remainder is zero
        a, b = b, a % b                       # replace (a, b) by (b, a mod b): same gcd, smaller numbers
    return a                                  # the last non-zero value is the gcd


def is_prime(n):                              # trial division up to the square root
    if n < 2:                                 # 0, 1 and negatives are not prime
        return False                          # not prime
    i = 2                                     # first possible divisor
    while i * i <= n:                         # a factor bigger than sqrt(n) must pair with a smaller one
        if n % i == 0:                        # i divides n exactly
            return False                      # so n is not prime
        i += 1                                # try the next divisor
    return True                               # no divisor found


def sieve(n):                                 # list of all primes below n (Sieve of Eratosthenes)
    if n < 3:                                 # no primes below 2
        return []                             # empty list
    is_p = [True] * n                         # is_p[i] says "i might be prime"
    is_p[0] = is_p[1] = False                 # 0 and 1 are not prime
    for i in range(2, int(n ** 0.5) + 1):     # only need i up to sqrt(n)
        if is_p[i]:                           # i is prime
            for j in range(i * i, n, i):      # cross out i*i, i*i+i, ... (smaller multiples were crossed already)
                is_p[j] = False               # not prime
    return [i for i in range(n) if is_p[i]]   # collect the survivors


print(gcd(12, 18), is_prime(29), sieve(20))   # expect 6 True [2, 3, 5, 7, 11, 13, 17, 19]
assert gcd(12, 18) == 6                       # common divisor 6
assert gcd(7, 0) == 7                         # gcd with zero is the other number
assert is_prime(29) is True and is_prime(1) is False and is_prime(49) is False   # basic checks
assert sieve(20) == [2, 3, 5, 7, 11, 13, 17, 19]   # primes below 20
assert (12 * 18) // gcd(12, 18) == 36         # LCM = a * b / gcd
```

---

## 5. Classic problems

### 5.1 Single Number (LeetCode 136)

**In plain words.** Every number in the list appears twice, except one that appears once. Find that one. Use O(1) extra memory.

**Brute force.** Count each number with a dictionary (`Counter`) and return the one with count 1. Time O(n), but space O(n). Or sort and compare neighbours: O(n log n).

**Better idea, slowly.**
1. XOR of a number with itself is 0. XOR with 0 changes nothing.
2. XOR the whole list. Pairs cancel (`a ^ a = 0`). Only the lonely number is left.
3. Order does not matter, so the pairs do not have to be next to each other.

```python
from typing import List                       # type hints


def single_number(nums: List[int]) -> int:    # find the number that appears once
    result = 0                                # start with 0 (it changes nothing in XOR)
    for x in nums:                            # visit every number
        result ^= x                           # XOR it in; equal pairs cancel out
    return result                             # only the lonely number is left


print(single_number([4, 1, 2, 1, 2]))         # expect 4
assert single_number([2, 2, 1]) == 1          # example 1
assert single_number([4, 1, 2, 1, 2]) == 4    # example 2 (the trace)
assert single_number([1]) == 1                # example 3 / edge case: one number
assert single_number([-1, -1, -7]) == -7      # edge case: negative numbers work too
assert single_number([0, 5, 5]) == 0          # edge case: the lonely number is zero
```

**Trace**: see section 3.

**Complexity.** Time O(n): one pass. Space O(1): one variable.

**Edge cases.**
1. A single element: the answer is that element.
2. The lonely number is `0`: the result is `0`, which is correct.

**How interviewers twist it.**
- "Single Number II" (LeetCode 137): every number appears **three** times except one. Count each bit position modulo 3.
- "Single Number III" (LeetCode 260): **two** numbers appear once. XOR everything to get `a ^ b`, find one bit where they differ, and split the list into two groups by that bit.
- "Find the duplicate / missing number": see 5.4.

---

### 5.2 Number of 1 Bits (LeetCode 191)

**In plain words.** Count how many bits are `1` in the binary form of a non-negative integer. `11` (`1011`) has 3.

**Brute force.** Check the last bit, shift right, and repeat until the number is zero. This takes as many steps as the number has bits (up to 32). It is fine.

**Better idea, slowly.**
1. `n & (n - 1)` turns the **lowest ON bit** to OFF (see the cheat sheet).
2. So repeating `n = n & (n - 1)` removes one ON bit each time.
3. Count how many times we can do it before `n` becomes 0. That count is the number of ON bits.
4. This loop runs only as many times as there are ON bits, not as many times as there are bits.

```python
def hamming_weight(n: int) -> int:            # count the 1 bits
    count = 0                                 # how many ON bits so far
    while n:                                  # while some bit is still ON
        n &= n - 1                            # remove the lowest ON bit
        count += 1                            # we removed one
    return count                              # the number of ON bits


print(hamming_weight(11))                     # expect 3
assert hamming_weight(11) == 3                # example 1: 1011
assert hamming_weight(128) == 1               # example 2: 10000000
assert hamming_weight(0) == 0                 # edge case: zero has no ON bits
assert hamming_weight(2 ** 31 - 1) == 31      # edge case: 31 ON bits
assert hamming_weight(7) == bin(7).count("1") # cross-check with Python's text method
```

**Trace** on `n = 11` (binary `1011`):

```
start:    n = 1011 (11), count = 0
step 1:   n - 1 = 1010.   n & (n-1) = 1011 & 1010 = 1010 (10).   count = 1
step 2:   n - 1 = 1001.   1010 & 1001 = 1000 (8).                count = 2
step 3:   n - 1 = 0111.   1000 & 0111 = 0000 (0).                count = 3
n is 0 -> stop. answer 3
```

**Complexity.** Time O(k), where k is the number of ON bits (at most 32 here). Space O(1).

**Edge cases.**
1. `n = 0`: the loop never runs. Answer 0.
2. In Python, integers have no fixed size. If a problem gives you a *negative* number and a 32-bit rule, first do `n &= 0xFFFFFFFF` to see it as 32 bits. Otherwise `n & (n-1)` on a negative number never reaches 0.

**How interviewers twist it.**
- "Power of Two" (LeetCode 231): `n > 0 and n & (n - 1) == 0`. A power of two has exactly one ON bit.
- "Hamming Distance" (LeetCode 461): count the 1 bits of `x ^ y`.
- "Reverse Bits" (LeetCode 190): build the result bit by bit with shifts.

---

### 5.3 Counting Bits (LeetCode 338)

**In plain words.** For every number from `0` to `n`, return the count of 1 bits. For `n = 5`: `[0, 1, 1, 2, 1, 2]`.

**Brute force.** Run the loop from 5.2 for each number. Time O(n x bits).

**Better idea (a little DP), slowly.**
1. Look at `i` and `i >> 1` (that is `i` divided by 2, which drops the last bit).
2. `i` has the same ON bits as `i >> 1`, plus one more **if the last bit of `i` is 1**.
3. So `bits[i] = bits[i >> 1] + (i & 1)`.
4. `i >> 1` is smaller than `i`, so it is already computed. This is the DP idea from lessons 15 and 16.

```python
from typing import List                       # type hints


def count_bits(n: int) -> List[int]:          # ON-bit counts for 0..n
    bits = [0] * (n + 1)                      # bits[i] will hold the count for i; bits[0] = 0 already
    for i in range(1, n + 1):                 # fill from small to big
        bits[i] = bits[i >> 1] + (i & 1)      # same as half of i, plus the dropped last bit
    return bits                               # the full list


print(count_bits(5))                          # expect [0, 1, 1, 2, 1, 2]
assert count_bits(2) == [0, 1, 1]             # example 1
assert count_bits(5) == [0, 1, 1, 2, 1, 2]    # example 2
assert count_bits(0) == [0]                   # edge case: only zero
assert count_bits(16)[16] == 1                # edge case: a power of two has one ON bit
```

**Trace** for `n = 5`:

```
i=1 (001): bits[0] + (1 & 1) = 0 + 1 = 1
i=2 (010): bits[1] + (2 & 1) = 1 + 0 = 1
i=3 (011): bits[1] + (3 & 1) = 1 + 1 = 2
i=4 (100): bits[2] + (4 & 1) = 1 + 0 = 1
i=5 (101): bits[2] + (5 & 1) = 1 + 1 = 2
result: [0, 1, 1, 2, 1, 2]
```

**Complexity.** Time O(n): one step per number. Space O(n) for the answer (the output itself needs it).

**Edge cases.**
1. `n = 0`: the answer is `[0]`.
2. Powers of two (1, 2, 4, 8, ...) always give 1.

**How interviewers twist it.**
- "Use the lowest-bit trick": `bits[i] = bits[i & (i - 1)] + 1`. Also correct.
- "Sum of bits for all numbers up to n": sum the list.
- "Total Hamming distance": count the ON bits at each position across all numbers.

---

### 5.4 Missing Number (LeetCode 268)

**In plain words.** A list has `n` different numbers taken from `0..n`. So exactly one number from `0..n` is missing. Find it. `[3, 0, 1]` gives `2`.

**Brute force.** Sort, then find the first index where `nums[i] != i`. O(n log n). Or use a set and test every number from 0 to n: O(n) time, O(n) space.

**Better idea, slowly.** Two good ways with O(1) space:
1. **Sum formula**: the sum of `0..n` is `n(n+1)/2`. Subtract the sum of the list. The difference is the missing number.
2. **XOR**: XOR together all numbers `0..n` and all list values. Every present number appears twice and cancels. The missing number appears once and stays.

The sum method can overflow in languages like C or Java for large `n`. Python never overflows, but interviewers like to hear that XOR is safe everywhere.

```python
from typing import List                       # type hints


def missing_number_xor(nums: List[int]) -> int:    # XOR method
    result = len(nums)                        # start with n (the index loop below only covers 0..n-1)
    for i, x in enumerate(nums):              # visit each position and value
        result ^= i ^ x                       # XOR the index and the value into the result
    return result                             # the number that never cancelled


def missing_number_sum(nums: List[int]) -> int:    # sum method
    n = len(nums)                             # the list holds n numbers from 0..n
    return n * (n + 1) // 2 - sum(nums)       # expected total minus actual total


print(missing_number_xor([3, 0, 1]), missing_number_sum([3, 0, 1]))   # expect 2 2
assert missing_number_xor([3, 0, 1]) == 2 and missing_number_sum([3, 0, 1]) == 2   # example 1
assert missing_number_xor([0, 1]) == 2 and missing_number_sum([0, 1]) == 2         # example 2: the top one is missing
assert missing_number_xor([9, 6, 4, 2, 3, 5, 7, 0, 1]) == 8   # example 3
assert missing_number_xor([0]) == 1           # edge case: one number
assert missing_number_xor([1]) == 0           # edge case: zero is missing
```

**Trace** of the XOR method on `[3, 0, 1]` (`n = 3`):

```
start:      result = 3
i=0, x=3:   result = 3 ^ 0 ^ 3 = 0
i=1, x=0:   result = 0 ^ 1 ^ 0 = 1
i=2, x=1:   result = 1 ^ 2 ^ 1 = 2
answer = 2
```

**Complexity.** Time O(n). Space O(1).

**Edge cases.**
1. The missing number is `n` (the largest): `[0, 1]` gives 2. This is why we start `result` at `n`.
2. The missing number is `0`.

**How interviewers twist it.**
- "Find the duplicate number" (LeetCode 287): the list has `n + 1` numbers from `1..n`. Use cycle detection (fast and slow pointers, lesson 07) or binary search on the value.
- "Find all missing numbers" (LeetCode 448): mark seen numbers by making `nums[x-1]` negative.
- "The list is sorted": binary search for the first index where `nums[i] != i`.

---

### 5.5 Pow(x, n) (LeetCode 50, fast exponentiation)

**In plain words.** Compute `x` raised to the power `n` (n may be negative). `2^10 = 1024`.

**Brute force.** Multiply `x` by itself `n` times. O(n). For `n = 2 billion`, far too slow.

**Better idea, slowly (square and halve).**
1. `x^10 = (x^2)^5`. Squaring the base and halving the exponent shrinks the problem fast.
2. If the exponent is odd, take one `x` out first: `x^5 = x * x^4`.
3. In loop form: keep `result = 1` and `base = x`. While the exponent is above 0: if its last bit is 1, multiply `result` by `base`. Then square `base` and shift the exponent right by one bit.
4. For a negative exponent: compute with `-n`, then take `1 / result`.

```python
def my_pow(x: float, n: int) -> float:        # x to the power n
    if n < 0:                                 # negative exponent
        x = 1 / x                             # use the reciprocal ...
        n = -n                                # ... and a positive exponent
    result = 1.0                              # the answer so far
    base = x                                  # the current power of x: x, x^2, x^4, x^8, ...
    while n > 0:                              # while there are exponent bits left
        if n & 1:                             # the last bit is 1: this power is needed
            result *= base                    # include it in the answer
        base *= base                          # square the base
        n >>= 1                               # drop the last bit of the exponent
    return result                             # done


print(my_pow(2.0, 10))                        # expect 1024.0
assert my_pow(2.0, 10) == 1024.0              # example 1
assert abs(my_pow(2.1, 3) - 9.261) < 1e-9     # example 2 (decimals: compare with a small tolerance)
assert my_pow(2.0, -2) == 0.25                # example 3: negative exponent
assert my_pow(5.0, 0) == 1.0                  # edge case: anything to the power 0 is 1
assert my_pow(0.0, 5) == 0.0                  # edge case: zero base
assert my_pow(1.0, 2 ** 31 - 1) == 1.0        # edge case: huge exponent is still fast
```

**Trace** of `my_pow(2, 10)`. The exponent `10` is `1010` in binary.

```
start:  result = 1,  base = 2,    n = 10 (1010)
loop 1: last bit of n is 0 -> skip.         base = 4,     n = 5 (101)
loop 2: last bit is 1 -> result = 1*4 = 4.  base = 16,    n = 2 (10)
loop 3: last bit is 0 -> skip.              base = 256,   n = 1 (1)
loop 4: last bit is 1 -> result = 4*256 = 1024.  base = 65536, n = 0
n is 0 -> stop. answer 1024
```

This works because `10 = 8 + 2`, so `x^10 = x^8 * x^2 = 256 * 4`. The loop picks exactly the powers that match the ON bits of the exponent.

**Complexity.** Time O(log n): the exponent loses one bit each loop. Space O(1).

**Edge cases.**
1. `n = 0`: always 1.
2. Negative `n`, including the smallest 32-bit integer: in Python, `-n` is safe. In other languages `-(-2^31)` overflows, so use a 64-bit type there.

**How interviewers twist it.**
- "`Sqrt(x)`" (LeetCode 69): binary search on the answer (lesson 06).
- "Compute `x^n mod m`": multiply with `% m` after each step. This is **modular exponentiation**, used all over cryptography, and Python has `pow(x, n, m)` built in.
- "Matrix power for Fibonacci in O(log n)": same loop with matrices.

---

## 6. Common mistakes

1. **Operator precedence.** In Python, `n & 1 == 1` works as you expect, because `&` binds tighter than `==`. In C, C++ and Java it does NOT (there it means `n & (1 == 1)`), and that is a classic bug. Write `(n & 1) == 1` with brackets as a safe habit, and say so in the interview.
2. **Mixing `^` and `**`.** In Python `^` is XOR, not power. Power is `**`.
3. **Negative numbers and bit tricks.** Python integers have infinite bits. Mask with `& 0xFFFFFFFF` if the problem says 32 bits.
4. **`>>` rounds down.** `-5 >> 1` is `-3`, not `-2`.
5. **Floating-point comparison.** Do not compare floats with `==` after many multiplications. Use a tolerance.
6. **Slow primes.** Testing divisors up to `n` instead of `sqrt(n)`, or using trial division for every number when a sieve is needed.
7. **Forgetting `% m` at each step** in "answer modulo 10^9+7" problems (in other languages the numbers overflow before the final `%`).
8. **Forgetting that in Python integers never overflow**, then telling the interviewer the code is overflow-safe in all languages. Mention what you would do in Java or C++.

---

## 7. Practice list (8 more problems)

Tags come from public LeetCode company-tag lists I read (GitHub mirror, snapshot Oct 2025; see lesson 19). A tag means "the problem is in that company's list". No tag means not verified. The problems taught above are tagged too: Single Number and Number of 1 Bits are each in the lists of Amazon, Google, Meta and Microsoft. Pow(x, n) is in Meta's list.

| # | Problem | Difficulty | Tagged for |
|---|---|---|---|
| 1 | Power of Two (231) | Easy | not verified |
| 2 | Hamming Distance (461) | Easy | not verified |
| 3 | Reverse Bits (190) | Easy | not verified |
| 4 | Sum of Two Integers (371) | Medium | not verified |
| 5 | Single Number II (137) | Medium | not verified |
| 6 | Count Primes (204) | Medium | not verified |
| 7 | Sqrt(x) (69) | Easy | not verified |
| 8 | Reverse Integer (7) | Medium | Google, Microsoft |

---

## 8. Self-quiz (5 questions)

1. What are `x ^ x` and `x ^ 0`? How does that help to find the lonely number in a list?
2. What does `n & (n - 1)` do to the binary form of `n`?
3. How can you test if a positive number is a power of two in one line?
4. Why does fast exponentiation take O(log n) steps instead of O(n)?
5. How do you find the GCD of two numbers with Euclid's algorithm? Try `gcd(48, 18)`.

**Answers.**
1. `x ^ x = 0` and `x ^ 0 = x`. If you XOR the whole list, every pair cancels to 0 and only the lonely number remains.
2. It turns off the lowest bit that is ON.
3. `n > 0 and n & (n - 1) == 0`. A power of two has exactly one ON bit, and removing it leaves 0.
4. Each loop squares the base and halves the exponent, so the exponent loses one bit per step. The number of bits in `n` is about `log2(n)`.
5. Replace `(a, b)` by `(b, a % b)` until `b` is 0. `gcd(48, 18)`: `(48, 18)` -> `(18, 12)` -> `(12, 6)` -> `(6, 0)`. The answer is 6.
