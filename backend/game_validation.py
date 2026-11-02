import math


class Random:
    def __init__(self, seed):
        self.state = seed or 1

    def draw(self, n):
        x = self.state
        x ^= (x << 13) & 0xffffffff
        x ^= x >> 17
        x ^= (x << 5) & 0xffffffff
        self.state = x & 0xffffffff
        return (self.state * n) >> 32

    def shuffle(self, values):
        for i in range(len(values) - 1, 0, -1):
            j = self.draw(i + 1)
            values[i], values[j] = values[j], values[i]


def matches(board):
    found = {}
    for transpose in (False, True):
        for r in range(6):
            start = 0
            for c in range(1, 7):
                previous = board[c - 1][r] if transpose else board[r][c - 1]
                value = (board[c][r] if transpose else board[r][c]) if c < 6 else -1
                if value != previous:
                    if c - start >= 3:
                        for k in range(start, c):
                            found[(k, r) if transpose else (r, k)] = True
                    start = c
    return list(found)


def swapped(board, move):
    r, c, rr, cc = move
    copy = [row[:] for row in board]
    copy[r][c], copy[rr][cc] = copy[rr][cc], copy[r][c]
    return copy


def has_moves(board):
    for r in range(6):
        for c in range(6):
            for rr, cc in ((r + 1, c), (r, c + 1)):
                if rr < 6 and cc < 6 and matches(swapped(board, [r, c, rr, cc])):
                    return True
    return False


def match_board(rng):
    for _ in range(100):
        board = [[rng.draw(6) for _ in range(6)] for _ in range(6)]
        for _ in range(50):
            hits = matches(board)
            if not hits:
                break
            for r, c in hits:
                board[r][c] = rng.draw(6)
        if not matches(board) and has_moves(board):
            return board
    return [[rng.draw(6)] * 6 for _ in range(6)]


def reshuffle(board, rng):
    values = [cell for row in board for cell in row]
    for _ in range(150):
        rng.shuffle(values)
        result = [values[r * 6:(r + 1) * 6] for r in range(6)]
        if not matches(result) and has_moves(result):
            return result
    return board


def match_score(seed, moves, elapsed):
    if len(moves) != 30:
        raise ValueError("A Match eredményhez 30 érvényes lépés kell.")
    rng = Random(seed)
    board, score, cascades = match_board(rng), 0, 0
    for move in moves:
        if (not isinstance(move, list) or len(move) != 4 or
                any(type(n) is not int or not 0 <= n < 6 for n in move)):
            raise ValueError("Érvénytelen Match lépés.")
        r, c, rr, cc = move
        if abs(r - rr) + abs(c - cc) != 1:
            raise ValueError("Csak szomszédos mezők cserélhetők.")
        board = swapped(board, move)
        hits = matches(board)
        if not hits:
            raise ValueError("A lépés nem eredményez találatot.")
        combo = 1
        while hits:
            cascades += 1
            if combo > 100:
                raise ValueError("Túl hosszú kaszkád.")
            score += len(hits) * 10 * combo
            for r, c in hits:
                board[r][c] = -1
            for c in range(6):
                cells = [board[r][c] for r in range(6) if board[r][c] != -1]
                column = [-1] * (6 - len(cells)) + cells
                for r in range(6):
                    board[r][c] = column[r]
            for c in range(6):
                for r in range(6):
                    if board[r][c] == -1:
                        board[r][c] = rng.draw(6)
            hits = matches(board)
            combo += 1
        if not has_moves(board):
            board = reshuffle(board, rng)
    if elapsed + 2 < cascades * 0.74:
        raise ValueError("A játék időtartama túl rövid.")
    return score


def snake_score(seed, moves, elapsed):
    if not moves or len(moves) > 12005 or len(moves) * 0.15 > elapsed + 2:
        raise ValueError("Érvénytelen játékidő vagy lépésszám.")
    rng, snake, food, previous, score = Random(seed), [(6, 6), (6, 7), (6, 8)], (6, 3), "UP", 0
    directions = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
    for index, direction in enumerate(moves):
        if direction not in directions:
            raise ValueError("Érvénytelen irány.")
        dx, dy = directions[direction]
        px, py = directions[previous]
        if (dx, dy) == (-px, -py):
            raise ValueError("A kígyó nem fordulhat vissza.")
        previous = direction
        head = snake[0][0] + dx, snake[0][1] + dy
        eating = head == food
        if not all(0 <= n < 12 for n in head) or head in (snake if eating else snake[:-1]):
            if index != len(moves) - 1:
                raise ValueError("Lépés a játék vége után.")
            return score
        snake = [head] + (snake if eating else snake[:-1])
        if eating:
            score += 10
            if len(snake) == 144:
                if index != len(moves) - 1:
                    raise ValueError("Lépés a megtelt pálya után.")
                return score
            while food in snake:
                food = rng.draw(12), rng.draw(12)
    raise ValueError("A játék még nem ért véget.")


def sudoku_challenge(seed, size):
    rows = 2 if size in (4, 6) else 3
    cols = size // rows
    rng = Random(seed)
    numbers = list(range(1, size + 1))
    rng.shuffle(numbers)
    board = [[numbers[(r * cols + r // rows + c) % size] for c in range(size)] for r in range(size)]
    positions = list(range(size * size))
    rng.shuffle(positions)
    for position in positions[:{4: 8, 6: 18, 9: 42}[size]]:
        board[position // size][position % size] = 0
    return board


def sudoku_score(puzzle, board, elapsed):
    n = len(puzzle)
    if not isinstance(board, list) or len(board) != n or any(not isinstance(row, list) or len(row) != n for row in board):
        raise ValueError("Érvénytelen Sudoku tábla.")
    for r in range(n):
        for c in range(n):
            value = board[r][c]
            if type(value) is not int or not 1 <= value <= n or (puzzle[r][c] and puzzle[r][c] != value):
                raise ValueError("Érvénytelen Sudoku mező.")
    required = set(range(1, n + 1))
    if any(set(row) != required for row in board) or any({board[r][c] for r in range(n)} != required for c in range(n)):
        raise ValueError("Hibás Sudoku megoldás.")
    h, w = (2, n // 2) if n in (4, 6) else (3, 3)
    for r in range(0, n, h):
        for c in range(0, n, w):
            if {board[rr][cc] for rr in range(r, r + h) for cc in range(c, c + w)} != required:
                raise ValueError("Hibás Sudoku blokk.")
    base, factor, floor = {4: (1000, 5, 100), 6: (3000, 3, 300), 9: (10000, 2, 1000)}[n]
    return max(floor, base - factor * math.floor(elapsed))
