import pytest
import json
from pathlib import Path
import shutil
import subprocess

from game_validation import Random, match_board, match_score, snake_score, sudoku_challenge, sudoku_score
from test_leaderboard import solve


def test_real_frontend_match_replays_identically_on_backend():
    root = Path(__file__).parents[2]
    if not shutil.which("node") or not (root / "frontend/node_modules/typescript").exists():
        pytest.skip("Cross-runtime test requires frontend npm ci and Node")
    result = subprocess.run(["node", str(root / "frontend/scripts/game-proof-check.js")],
                            capture_output=True, text=True, check=True, timeout=30)
    for game in json.loads(result.stdout):
        assert match_board(Random(game["seed"])) == game["original"]
        assert match_score(game["seed"], game["moves"], 1800) == game["score"]
        with pytest.raises(ValueError):
            match_score(game["seed"], game["moves"], 0)


def test_random_sequence_stable():
    rng = Random(1)
    assert [rng.draw(4294967296) for _ in range(5)] == [270369, 67634689, 2647435461, 307599695, 2398689233]


def test_match_starts_without_existing_matches():
    from game_validation import matches, has_moves
    for seed in (1, 42, 123456, 0xffffffff):
        board = match_board(Random(seed))
        assert not matches(board)
        assert has_moves(board)


def test_incomplete_match_proof_rejected():
    with pytest.raises(ValueError):
        match_score(1, [], 60)


def test_snake_score_replayed_and_early_or_impossible_run_rejected():
    assert snake_score(1, ["UP"] * 7, 3) == 10
    with pytest.raises(ValueError):
        snake_score(1, ["UP", "DOWN"], 3)
    with pytest.raises(ValueError):
        snake_score(1, ["UP"] * 8, 3)
    with pytest.raises(ValueError):
        snake_score(1, ["UP"] * 3, 3)
    with pytest.raises(ValueError):
        snake_score(1, ["UP"] * 100, 0)


@pytest.mark.parametrize("size", [4, 6, 9])
def test_sudoku_issued_clues_cannot_be_replaced(size):
    puzzle = sudoku_challenge(42, size)
    board = [row[:] for row in puzzle]
    assert solve(board)
    assert sudoku_score(puzzle, board, 20) > 0
    changed = [[(value % size) + 1 for value in row] for row in board]
    with pytest.raises(ValueError):
        sudoku_score(puzzle, changed, 20)
