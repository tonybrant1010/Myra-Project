import asyncio
from datetime import timedelta
import os
from pathlib import Path
import sys
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parents[1]))

import server  # noqa: E402
from verify_migration import verify as verify_migration  # noqa: E402


async def transaction(action):
    async with server.SessionLocal() as db:
        try:
            result = await action(db)
            await db.commit()
            return result
        except server.HTTPException as exc:
            await db.rollback()
            return exc.status_code


async def main():
    url = urlparse(server.DATABASE_URL.replace("postgresql+asyncpg", "postgresql"))
    if os.environ.get("MYRA_ISOLATED_TEST") != "1" or url.path != "/myra_repair_test":
        raise RuntimeError("This test requires a disposable myra_repair_test database")
    async with server.engine.connect() as conn:
        tables = (await conn.execute(server.sql_text(
            "SELECT count(*) FROM pg_tables WHERE schemaname = 'public'"))).scalar_one()
        if tables:
            raise RuntimeError("Integration test refuses a non-empty database")
    async with server.lifespan(server.app):
        async with server.SessionLocal() as db:
            assert (await db.execute(server.select(server.func.count()).select_from(server.StateCode))).scalar_one() == 256
            user = server.User(id=1, email="integration@example.com", name="Integration", password_hash="unused")
            db.add(user)
            await db.commit()
            refresh = server.create_refresh_token(user)

        async def rotate(db):
            await server.auth_refresh(server.RefreshTokenBody(refresh_token=refresh), db)
            return 200
        assert sorted(await asyncio.gather(transaction(rotate), transaction(rotate))) == [200, 401]
        print("PASS fresh PostgreSQL/vector startup, seed and concurrent refresh rotation")

        challenge_id = "integration-challenge-0001"
        async with server.SessionLocal() as db:
            db.add(server.MfaChallenge(id=challenge_id, user_id=1, purpose="login",
                code_hash=server._hash_mfa_code(challenge_id, "123456"),
                expires_at=server._now() + timedelta(minutes=5)))
            await db.commit()
        async def consume(db):
            owner = await db.get(server.User, 1)
            await server._consume_mfa_challenge(db, owner, challenge_id, "123456", "login")
            return 200
        assert sorted(await asyncio.gather(transaction(consume), transaction(consume))) == [200, 400]
        print("PASS concurrent MFA consumption")

        async with server.SessionLocal() as db:
            owner = await db.get(server.User, 1)
            owner.reset_token = server._hash_reset_token("654321", owner.email)
            owner.token_expires_at = server._now() + timedelta(minutes=5)
            owner.reset_attempts = 0
            await db.commit()
        request = server.Request({"type": "http", "client": ("127.0.0.1", 1234), "headers": []})
        os.environ["DISABLE_RATE_LIMITS"] = "true"

        async def reset_wrong(db):
            await server.auth_reset_password(server.ResetPasswordBody(
                email="integration@example.com", token="000000", new_password="new-test-password"), request, db)
            return 200

        assert await asyncio.gather(transaction(reset_wrong), transaction(reset_wrong)) == [400, 400]
        async with server.SessionLocal() as db:
            assert (await db.get(server.User, 1)).reset_attempts == 2

        async def reset_right(db):
            await server.auth_reset_password(server.ResetPasswordBody(
                email="integration@example.com", token="654321", new_password="new-test-password"), request, db)
            return 200

        assert sorted(await asyncio.gather(transaction(reset_right), transaction(reset_right))) == [200, 400]
        print("PASS atomic password-reset attempts and single consumption")

        async with server.engine.begin() as conn:
            await conn.execute(server.sql_text("DROP INDEX ux_leaderboard_user_game"))
            await conn.execute(server.sql_text("ALTER TABLE leaderboard DROP COLUMN verified_at"))
            await conn.execute(server.sql_text(
                "INSERT INTO leaderboard(user_id, game_type, score) VALUES (1, 'snake', 10), (1, 'snake', 20)"))
        await server._ensure_leaderboard_unique()
        async with server.SessionLocal() as db:
            rows = (await db.execute(server.select(server.LeaderboardEntry))).scalars().all()
            assert len(rows) == 1 and rows[0].score == 20 and rows[0].verified_at is None
        print("PASS legacy leaderboard migration and duplicate preservation")
        await verify_migration()
    print("POSTGRES_INTEGRATION_OK")


if __name__ == "__main__":
    asyncio.run(main())
