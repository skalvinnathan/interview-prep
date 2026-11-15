# 20 - Tic-Tac-Toe (full) and Chess basics

Python 3.9. All code was run; the output is real.

Tic-tac-toe is small enough to finish in 45 minutes, so you get a **complete** design. Chess is too big for one round, so you get the **core** (board, piece classes, legal move geometry, turns) and a list of what to say you would add. Interviewers who ask for chess usually want exactly this core and the discussion.

---

## 1. The problem in plain words

**Tic-tac-toe:** two players take turns putting X or O on a 3x3 grid. The first to fill a whole row, column, or diagonal wins. If the grid fills with no winner, it is a draw.

**Analogy.** A paper game with a referee. The referee (the `Game` class) checks whose turn it is, rejects illegal moves, and says when the game is over.

**Chess basics:** two players move pieces on an 8x8 board. Each piece type moves in its own way. We build the board, the pieces, the move rules, and the turns.

---

## 2. Requirements I ask the interviewer

**Tic-tac-toe**
1. Board size fixed at 3x3, or N x N with N in a row to win? -> *N x N (default 3).*
2. Players: human vs human, or against a computer? -> *Both. A player is controlled by a "move strategy".*
3. Win detection speed? -> *Should not scan the whole board after every move.*
4. Invalid moves (cell taken, out of range, wrong turn)? -> *Reject with an error; the turn does not change.*
5. Undo? -> *Nice extension.*
6. More than two players? -> *Possible extension.*

**Chess**
1. Full rules (check, checkmate, castling, en passant, promotion)? -> *Not now. First: moves, captures, turns.*
2. Computer opponent? -> *Extension through a strategy.*
3. Input format? -> *Algebraic text like `e2 e4`.*

---

## 3. Classes and methods (the picture)

```text
TIC-TAC-TOE
+----------------------------------+
|              Game                |
|----------------------------------|
| board, players, current, status  |
| make_move(symbol, row, col)      |
| play()  (uses each player's      |
|          strategy)               |
| undo_last()                      |
+---------+------------+-----------+
          | has        | has many
          v            v
   +-----------+   +---------------------+   uses   +-------------------------+
   |   Board   |   |       Player        |--------->| MoveStrategy (abstract) |
   |-----------|   |---------------------|          | choose(board, symbol)   |
   | n, grid   |   | name, symbol,       |          +-----------+-------------+
   | place()   |   | strategy            |            Scripted  FirstEmpty  Smart
   | remove()  |   +---------------------+
   | would_win |
   | counters  |   Status: IN_PROGRESS / WON / DRAW
   +-----------+

CHESS
+---------------------+ has 64 cells  +--------------------------------+
|     ChessBoard      |-------------->| Piece (abstract)               |
|---------------------|               | color, symbol                  |
| move(src, dst)      |               | can_move(board, src, dst)      |
+----------+----------+               +----+------+------+------+------+
           |                              Rook Bishop Queen Knight King Pawn
           v
   +---------------+    Queen = Rook moves OR Bishop moves (reuse)
   |  ChessGame    |
   | turn handling |
   +---------------+
```

**Key idea for tic-tac-toe, O(1) win check.** Keep, for each player, a counter per row, per column, and for the two diagonals. When a player places a mark, add 1 to the counters touched. If any counter reaches N, that player wins. We never scan the board.

**Key idea for chess.** Polymorphism: `board.move` does not contain `if piece == "rook"`. It asks the piece: `piece.can_move(...)`. Each class holds its own rule. A new piece (for a fantasy variant) is a new class.

---

## 4. Full code

```python
import threading                               # Lock
from abc import ABC, abstractmethod            # "promise" classes
from enum import Enum                          # fixed named choices


class GameError(Exception):                    # any illegal action
    pass


class Status(Enum):
    IN_PROGRESS = 1
    WON = 2
    DRAW = 3


# =====================  TIC-TAC-TOE  =====================

class Board:
    def __init__(self, n=3):
        self.n = n                             # board is n x n, and n in a row wins
        self.grid = [[None] * n for _ in range(n)]     # None means empty
        # per-symbol counters: how many marks that symbol has in each row / column / diagonal
        self._rows, self._cols, self._diag, self._anti = {}, {}, {}, {}
        self.filled = 0                        # number of occupied cells

    def _counters(self, symbol):
        # create the counters the first time we see a symbol
        if symbol not in self._rows:
            self._rows[symbol] = [0] * self.n
            self._cols[symbol] = [0] * self.n
            self._diag[symbol] = 0
            self._anti[symbol] = 0
        return self._rows[symbol], self._cols[symbol]

    def in_range(self, r, c):
        return 0 <= r < self.n and 0 <= c < self.n

    def is_empty(self, r, c):
        return self.grid[r][c] is None

    def place(self, r, c, symbol):
        # put a mark and update the counters; return True if this move wins
        if not self.in_range(r, c):
            raise GameError("cell out of range")
        if not self.is_empty(r, c):
            raise GameError("cell already taken")
        rows, cols = self._counters(symbol)
        self.grid[r][c] = symbol
        self.filled += 1
        rows[r] += 1
        cols[c] += 1
        if r == c:
            self._diag[symbol] += 1            # on the main diagonal
        if r + c == self.n - 1:
            self._anti[symbol] += 1            # on the other diagonal
        return (rows[r] == self.n or cols[c] == self.n
                or self._diag[symbol] == self.n or self._anti[symbol] == self.n)

    def remove(self, r, c):
        # undo a placement (used by undo)
        symbol = self.grid[r][c]
        rows, cols = self._counters(symbol)
        self.grid[r][c] = None
        self.filled -= 1
        rows[r] -= 1
        cols[c] -= 1
        if r == c:
            self._diag[symbol] -= 1
        if r + c == self.n - 1:
            self._anti[symbol] -= 1

    def would_win(self, r, c, symbol):
        # would placing here complete a line? (does not change anything)
        rows, cols = self._counters(symbol)
        return (rows[r] + 1 == self.n or cols[c] + 1 == self.n
                or (r == c and self._diag[symbol] + 1 == self.n)
                or (r + c == self.n - 1 and self._anti[symbol] + 1 == self.n))

    def empty_cells(self):
        return [(r, c) for r in range(self.n) for c in range(self.n) if self.grid[r][c] is None]

    def render(self):
        return "\n".join(" ".join(cell or "." for cell in row) for row in self.grid)


class MoveStrategy(ABC):
    @abstractmethod
    def choose(self, board, symbol):
        pass


class ScriptedStrategy(MoveStrategy):          # plays a fixed list of moves (a stand-in for a human)
    def __init__(self, moves):
        self.moves = list(moves)
    def choose(self, board, symbol):
        return self.moves.pop(0)


class FirstEmptyStrategy(MoveStrategy):        # easy computer: first free cell
    def choose(self, board, symbol):
        return board.empty_cells()[0]


class SmartStrategy(MoveStrategy):             # medium computer: win, else block, else centre, else first free
    def __init__(self, all_symbols):
        self.all_symbols = all_symbols
    def choose(self, board, symbol):
        cells = board.empty_cells()
        for (r, c) in cells:                   # 1. can I win now?
            if board.would_win(r, c, symbol):
                return (r, c)
        for other in self.all_symbols:         # 2. can an opponent win next move? block it
            if other != symbol:
                for (r, c) in cells:
                    if board.would_win(r, c, other):
                        return (r, c)
        centre = (board.n // 2, board.n // 2)
        if centre in cells:                    # 3. take the centre
            return centre
        return cells[0]                        # 4. anything free


class Player:
    def __init__(self, name, symbol, strategy):
        self.name = name
        self.symbol = symbol
        self.strategy = strategy


class Game:
    def __init__(self, players, n=3):
        self.board = Board(n)
        self.players = players                 # list of Player, in turn order
        self.turn = 0                          # index of the player who moves now
        self.status = Status.IN_PROGRESS
        self.winner = None
        self.history = []                      # list of (row, col, turn index) for undo
        self._lock = threading.Lock()

    @property
    def current(self):
        return self.players[self.turn]

    def make_move(self, symbol, r, c):
        with self._lock:                       # check turn + place + switch turn = one atomic step
            if self.status != Status.IN_PROGRESS:
                raise GameError("game is over")
            if symbol != self.current.symbol:
                raise GameError("not your turn")
            won = self.board.place(r, c, symbol)
            self.history.append((r, c, self.turn))
            if won:
                self.status, self.winner = Status.WON, self.current
            elif self.board.filled == self.board.n ** 2:
                self.status = Status.DRAW
            else:
                self.turn = (self.turn + 1) % len(self.players)   # next player
            return self.status

    def undo_last(self):
        with self._lock:
            if not self.history:
                raise GameError("nothing to undo")
            r, c, turn = self.history.pop()
            self.board.remove(r, c)
            self.turn = turn                   # give the turn back
            self.status, self.winner = Status.IN_PROGRESS, None

    def play(self):
        # let each player's strategy choose moves until the game ends
        while self.status == Status.IN_PROGRESS:
            p = self.current
            r, c = p.strategy.choose(self.board, p.symbol)
            self.make_move(p.symbol, r, c)
        return self.status


# =====================  CHESS BASICS  =====================

class Piece(ABC):
    def __init__(self, color):
        self.color = color                     # "white" or "black"

    letter = "?"                               # each piece class sets its letter

    @property
    def symbol(self):
        return self.letter.upper() if self.color == "white" else self.letter.lower()

    @abstractmethod
    def can_move(self, board, src, dst):       # only the piece's own movement rule (not check)
        pass


def clear_path(board, src, dst):
    # True if every square strictly between src and dst is empty (for straight / diagonal slides)
    dr = (dst[0] > src[0]) - (dst[0] < src[0])         # -1, 0 or +1
    dc = (dst[1] > src[1]) - (dst[1] < src[1])
    r, c = src[0] + dr, src[1] + dc
    while (r, c) != dst:
        if board.grid[r][c] is not None:
            return False
        r, c = r + dr, c + dc
    return True


class Rook(Piece):
    letter = "r"
    def can_move(self, board, src, dst):
        straight = src[0] == dst[0] or src[1] == dst[1]
        return straight and clear_path(board, src, dst)


class Bishop(Piece):
    letter = "b"
    def can_move(self, board, src, dst):
        diagonal = abs(src[0] - dst[0]) == abs(src[1] - dst[1])
        return diagonal and clear_path(board, src, dst)


class Queen(Piece):
    letter = "q"
    def can_move(self, board, src, dst):
        # a queen moves like a rook OR a bishop: we reuse their rules
        return Rook(self.color).can_move(board, src, dst) or Bishop(self.color).can_move(board, src, dst)


class Knight(Piece):
    letter = "n"
    def can_move(self, board, src, dst):
        dr, dc = abs(src[0] - dst[0]), abs(src[1] - dst[1])
        return (dr, dc) in ((1, 2), (2, 1))    # the L shape; knights jump, so no path check


class King(Piece):
    letter = "k"
    def can_move(self, board, src, dst):
        return max(abs(src[0] - dst[0]), abs(src[1] - dst[1])) == 1


class Pawn(Piece):
    letter = "p"
    def can_move(self, board, src, dst):
        direction = -1 if self.color == "white" else 1     # white goes up the screen (row numbers fall)
        start_row = 6 if self.color == "white" else 1
        dr, dc = dst[0] - src[0], dst[1] - src[1]
        target = board.grid[dst[0]][dst[1]]
        if dc == 0 and dr == direction:
            return target is None              # one step forward, only onto an empty square
        if dc == 0 and dr == 2 * direction and src[0] == start_row:
            middle = board.grid[src[0] + direction][src[1]]
            return target is None and middle is None       # two steps from the start row
        if abs(dc) == 1 and dr == direction:
            return target is not None and target.color != self.color   # diagonal only to capture
        return False


class ChessBoard:
    def __init__(self):
        self.grid = [[None] * 8 for _ in range(8)]
        order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col, cls in enumerate(order):      # back ranks
            self.grid[0][col] = cls("black")
            self.grid[7][col] = cls("white")
        for col in range(8):                   # pawns
            self.grid[1][col] = Pawn("black")
            self.grid[6][col] = Pawn("white")

    @staticmethod
    def parse(square):
        # "e2" -> (row, col): file letter a-h is the column; rank 8 is row 0
        return 8 - int(square[1]), ord(square[0]) - ord("a")

    def move(self, src, dst, color):
        piece = self.grid[src[0]][src[1]]
        if piece is None:
            raise GameError("no piece on the start square")
        if piece.color != color:
            raise GameError("that is not your piece")
        target = self.grid[dst[0]][dst[1]]
        if target is not None and target.color == color:
            raise GameError("cannot capture your own piece")
        if not piece.can_move(self, src, dst):
            raise GameError(type(piece).__name__ + " cannot move like that")
        self.grid[dst[0]][dst[1]] = piece      # move (this also removes a captured piece)
        self.grid[src[0]][src[1]] = None
        return target                          # the captured piece, or None

    def render(self):
        lines = []
        for r in range(8):
            lines.append(str(8 - r) + " " + " ".join(p.symbol if p else "." for p in self.grid[r]))
        lines.append("  a b c d e f g h")
        return "\n".join(lines)


class ChessGame:
    def __init__(self):
        self.board = ChessBoard()
        self.turn = "white"                    # white starts

    def play(self, text):
        src_text, dst_text = text.split()
        captured = self.board.move(ChessBoard.parse(src_text), ChessBoard.parse(dst_text), self.turn)
        self.turn = "black" if self.turn == "white" else "white"   # switch only after a legal move
        return "captured " + type(captured).__name__ if captured else "ok"


def main():
    print("===== Tic-tac-toe: X wins with the top row (scripted humans) =====")
    px = Player("Asha", "X", ScriptedStrategy([(0, 0), (0, 1), (0, 2)]))
    po = Player("Ben", "O", ScriptedStrategy([(1, 0), (1, 1)]))
    g = Game([px, po])
    print("result:", g.play().name, "| winner:", g.winner.name)
    print(g.board.render())

    print("===== Smart vs smart on 3x3 =====")
    g2 = Game([Player("S1", "X", SmartStrategy(["X", "O"])), Player("S2", "O", SmartStrategy(["X", "O"]))])
    print("result:", g2.play().name)
    print(g2.board.render())

    print("===== Errors and undo =====")
    g3 = Game([Player("A", "X", None), Player("B", "O", None)])
    g3.make_move("X", 1, 1)
    for label, args in [("wrong turn", ("X", 0, 0)), ("taken cell", ("O", 1, 1)), ("out of range", ("O", 5, 5))]:
        try:
            g3.make_move(*args)
        except GameError as e:
            print(label, "->", e)
    g3.undo_last()
    print("after undo, centre empty:", g3.board.is_empty(1, 1), "| turn:", g3.current.name)

    # ---- extension: 4x4 board with three players ----
    print("===== Extension: 4x4, three players (X, O, Z) =====")
    sy = ["X", "O", "Z"]
    g4 = Game([Player("P1", "X", SmartStrategy(sy)), Player("P2", "O", SmartStrategy(sy)),
               Player("P3", "Z", FirstEmptyStrategy())], n=4)
    print("result:", g4.play().name, "| winner:", g4.winner.name if g4.winner else None)
    print(g4.board.render())

    # ---- chess ----
    print("===== Chess basics =====")
    chess = ChessGame()
    for mv in ["e2 e4", "e7 e5", "g1 f3", "b8 c6", "f1 b5"]:
        print(chess.turn, mv, "->", chess.play(mv))
    for mv in ["a8 a5", "c6 c4", "e5 e3"]:     # three illegal moves for black
        try:
            chess.play(mv)
        except GameError as e:
            print("illegal", mv, "->", e)
    print(chess.turn, "a7 a6 ->", chess.play("a7 a6"))
    print(chess.turn, "b5 c6 ->", chess.play("b5 c6"))
    print(chess.board.render())

    # ---- thread test: 9 threads all try to take cell (0,0) as X on turn 1 ----
    print("===== Thread test =====")
    g5 = Game([Player("A", "X", None), Player("B", "O", None)])
    outcomes = []
    def grab():
        try:
            g5.make_move("X", 0, 0)
            outcomes.append("ok")
        except GameError:
            outcomes.append("refused")
    threads = [threading.Thread(target=grab) for _ in range(9)]
    for t in threads: t.start()
    for t in threads: t.join()
    print("accepted:", outcomes.count("ok"), "| refused:", outcomes.count("refused"))


if __name__ == "__main__":
    main()
```

Output I got when I ran it:

```text
===== Tic-tac-toe: X wins with the top row (scripted humans) =====
result: WON | winner: Asha
X X X
O O .
. . .
===== Smart vs smart on 3x3 =====
result: WON
O X X
X X .
O O O
===== Errors and undo =====
wrong turn -> not your turn
taken cell -> cell already taken
out of range -> cell out of range
after undo, centre empty: True | turn: A
===== Extension: 4x4, three players (X, O, Z) =====
result: DRAW | winner: None
O Z X O
Z X O Z
X O X Z
X O Z X
===== Chess basics =====
white e2 e4 -> ok
black e7 e5 -> ok
white g1 f3 -> ok
black b8 c6 -> ok
white f1 b5 -> ok
illegal a8 a5 -> Rook cannot move like that
illegal c6 c4 -> Knight cannot move like that
illegal e5 e3 -> Pawn cannot move like that
black a7 a6 -> ok
white b5 c6 -> captured Knight
8 r . b q k b n r
7 . p p p . p p p
6 p . B . . . . .
5 . . . . p . . .
4 . . . . P . . .
3 . . . . . N . .
2 P P P P . P P P
1 R N B Q K . . R
  a b c d e f g h
===== Thread test =====
accepted: 1 | refused: 8
```

---

## 5. How the code works (walk through)

**Tic-tac-toe**
1. `Board.place` writes the mark and increases four counters (row, column, and the diagonals if the cell is on them). The method returns `True` if any counter reached N. That is the O(1) win test. No scanning.
2. `Game.make_move` is the referee: it checks the game is not over, checks the turn, asks the board to place, then either ends the game (win or draw) or passes the turn. If anything is illegal, an exception is raised **before** the turn changes.
3. `Game.play` asks the current player's **strategy** for a move. A human can be a strategy that reads input; the computer uses `SmartStrategy` (win, block, centre, else any).
4. `would_win` lets the smart strategy ask "would this move win?" without changing the board, using the same counters.
5. Undo calls `board.remove`, which reverses the counter changes.
6. Look at the "smart vs smart" output: one side **won**. `SmartStrategy` is only "medium" (win, block, centre). It does not look ahead, so it can be beaten by a trap (a "fork"). A perfect player needs `MinimaxStrategy`, which is why it is listed as an extension.

**Chess**
1. `ChessBoard.move` checks the common rules (a piece exists, it is yours, you do not capture your own piece) and then asks the **piece** `can_move`. Each piece class contains only its own rule.
2. `Queen` reuses `Rook` and `Bishop`. `Pawn` has the most special cases (forward only to empty squares, diagonal only to capture, two steps from the start row).
3. In the output the three illegal moves were rejected, and the turn did not change. Then white's bishop captured the knight.

---

## 6. How to extend it

**Tic-tac-toe**
- *Bigger board, three players:* already supported (`n` and the player list). The counters are keyed by symbol, so nothing else changes. See the 4x4 output.
- *Harder AI:* write a `MinimaxStrategy(MoveStrategy)`. No change to `Game`.
- *Replay:* the `history` list already records all moves.
- *Score board across many games:* a `Tournament` class that holds many `Game` objects.

**Chess (what to say you would add, in order)**
1. **Check and checkmate:** after a move, find the king's square and ask every enemy piece `can_move` onto it. A move that leaves your own king attacked is illegal (try the move, test, undo it).
2. **Special moves:** castling, en passant, pawn promotion. Each can be a small `SpecialMoveRule` object (Strategy), so `Pawn` does not become huge.
3. **Move history and undo:** store each move as a **Command** object with `execute`/`undo` (file 03).
4. **Computer player:** a `ChessStrategy` interface, as `MoveStrategy` above.
5. **Draw rules:** stalemate, repetition.

---

## 7. Thread-safety notes (plain words)

- A game is turn-based, so only one player moves at a time. But a web server may deliver two requests at once ("both players clicked"), or a player may double-click.
- **The danger:** two threads both pass the checks "cell empty" and "my turn", and both place a mark; or the turn flips twice.
- **The fix:** one lock inside `make_move`, so "check turn, check cell, place, switch turn" is a single step. The thread test: 9 threads all try to take the same cell; exactly one is accepted, the others are refused ("not your turn" or "cell taken").
- Different games are independent, so each `Game` has its own lock. A server can run thousands of games in parallel without them waiting for each other.

---

## 8. Five follow-up questions with model answers

**Q1. How do you check a win in O(1) instead of scanning the board?**
Keep counters per player for each row, column, and both diagonals. A move updates at most 4 counters. If one reaches N, the player won. Time per move is O(1); memory is O(N) per player.

**Q2. Why is the computer a `MoveStrategy` and not a subclass of `Player`?**
The only difference between a human and a computer is *how the move is chosen*. If I made `HumanPlayer` and `ComputerPlayer` subclasses, a "human who switches to computer help" would need a new class. With Strategy, I swap the move source at run time, and `Player` stays one class.

**Q3. How would you implement undo for chess?**
Each move is a Command that stores everything needed to reverse it: source, destination, the captured piece, and whether it was a first pawn move. `undo` puts the piece back and restores the captured piece. For special moves (castling), the command stores both piece movements.

**Q4. How do you detect check?**
Find the king of the side to move, and test whether any enemy piece `can_move` to the king's square. Because every piece has `can_move`, there is no per-piece `if`. For legal-move checking, make the move temporarily on the board, test whether your own king is attacked, and undo it.

**Q5. How would you avoid having a huge `Pawn` class with all the special rules?**
Move the special rules out into small rule objects (promotion rule, en passant rule) and let the board consult a list of rules after the basic geometry check. That keeps each class small (Single Responsibility) and lets you turn rules on or off for variants.

---

**Next:** `90_cheat_sheet.md`.
