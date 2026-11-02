import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

os.environ["DB_DIALECT"] = "sqlite"
os.environ["ENVIRONMENT"] = "development"

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from server import app, Base, User, get_db, get_current_user

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def init_db():
    app.dependency_overrides[get_db] = override_get_db
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()


def start_game_session(client: TestClient, headers: dict, game_type: str) -> str:
    r = client.post("/api/leaderboard/start", json={"game_type": game_type}, headers=headers)
    assert r.status_code == 200, f"Nem sikerult jatek-sessiont inditani: {r.text}"
    token = r.json().get("session_token")
    assert isinstance(token, str) and len(token) >= 16
    return token


def submit_score(client: TestClient, headers: dict, game_type: str, score: int):
    token = start_game_session(client, headers, game_type)
    return client.post("/api/leaderboard/submit", json={
        "game_type": game_type,
        "score": score,
        "session_token": token,
    }, headers=headers)


def solve(board):
    import game_validation
    n = len(board)
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                h, w = (2, n // 2) if n in (4, 6) else (3, 3)
                for value in range(1, n + 1):
                    if (value not in board[r] and all(row[c] != value for row in board)
                        and all(board[rr][cc] != value for rr in range(r // h * h, r // h * h + h)
                                for cc in range(c // w * w, c // w * w + w))):
                        board[r][c] = value
                        if solve(board):
                            return True
                        board[r][c] = 0
                return False
    game_validation.sudoku_score([[0] * n for _ in range(n)], board, 0)
    return True


@pytest.mark.anyio
async def test_scores_require_proof_and_are_calculated_on_server():
    import server
    from datetime import timedelta
    async with TestingSessionLocal() as db:
        user = User(id=1, email="game@example.com", name="Player", password_hash="unused")
        db.add(user)
        await db.commit()
    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app)
    async with TestingSessionLocal() as db:
        db.add(server.LeaderboardEntry(user_id=1, game_type="sudoku", score=999999))
        await db.commit()
    assert client.get("/api/leaderboard").json()["sudoku"] == []
    started = client.post("/api/leaderboard/start", json={"game_type": "sudoku", "board_size": 4}).json()
    token = started["session_token"]
    payload = {"session_token": token, "game_type": "sudoku", "score": 999999}
    assert client.post("/api/leaderboard/submit", json=payload).status_code == 400
    board = started["challenge"]["puzzle"]
    assert solve(board)
    async with TestingSessionLocal() as db:
        session = (await db.execute(select(server.GameSession))).scalar_one()
        session.issued_at = server._now() - timedelta(seconds=20)
        await db.commit()
    payload["game_proof"] = {"board": board}
    result = client.post("/api/leaderboard/submit", json=payload)
    assert result.status_code == 200, result.text
    assert 895 <= result.json()["best_score"] <= 900
    assert client.post("/api/leaderboard/submit", json=payload).status_code == 403
    assert len(client.get("/api/leaderboard").json()["sudoku"]) == 1


@pytest.mark.anyio
async def test_session_limit_and_account_ownership():
    async with TestingSessionLocal() as db:
        first = User(id=1, email="first@example.com", name="First", password_hash="unused")
        second = User(id=2, email="second@example.com", name="Second", password_hash="unused")
        db.add_all([first, second])
        await db.commit()
    app.dependency_overrides[get_current_user] = lambda: first
    client = TestClient(app)
    tokens = [start_game_session(client, {}, "snake") for _ in range(5)]
    assert client.post("/api/leaderboard/start", json={"game_type": "snake"}).status_code == 429
    app.dependency_overrides[get_current_user] = lambda: second
    assert client.post("/api/leaderboard/submit", json={
        "game_type": "snake", "session_token": tokens[0], "score": 0,
        "game_proof": {"moves": ["LEFT"] * 7},
    }).status_code == 403
