from datetime import timedelta

import pytest
from sqlalchemy import select, update

import server
import notification_outbox
from conftest import TestingSessionLocal


@pytest.mark.anyio
async def test_failed_notification_survives_new_session_then_delivers(init_db):
    async with TestingSessionLocal() as db:
        db.add(server.User(id=401, email="outbox@example.com", name="Test", password_hash="unused"))
        await db.commit()
    args = ("Test", "outbox@example.com", 401, "sensitive excerpt", "date", "reason", "stage", "note")
    await notification_outbox.enqueue(TestingSessionLocal, server.CrisisNotification, server._encrypt_field, args)
    async with TestingSessionLocal() as db:
        row = (await db.execute(select(server.CrisisNotification))).scalar_one()
        assert "sensitive excerpt" not in row.payload
    await notification_outbox.deliver_one(TestingSessionLocal, server.CrisisNotification, server._decrypt_field, lambda *a: False)
    async with TestingSessionLocal() as db:
        row = (await db.execute(select(server.CrisisNotification))).scalar_one()
        assert row.attempts == 1
        await db.execute(update(server.CrisisNotification).values(next_attempt_at=server._now() - timedelta(seconds=1)))
        await db.commit()
    delivered = []
    def sender(*a):
        delivered.append(a)
        return True
    await notification_outbox.deliver_one(TestingSessionLocal, server.CrisisNotification, server._decrypt_field, sender)
    assert delivered == [args]
    async with TestingSessionLocal() as db:
        assert (await db.execute(select(server.CrisisNotification))).first() is None


@pytest.mark.anyio
async def test_user_deletion_removes_pending_notification(init_db):
    async with TestingSessionLocal() as db:
        db.add(server.User(id=402, email="delete-outbox@example.com", name="Test", password_hash="unused"))
        await db.commit()
    await notification_outbox.enqueue(TestingSessionLocal, server.CrisisNotification, server._encrypt_field,
                                      ("Test", "delete-outbox@example.com", 402, "excerpt"))
    async with TestingSessionLocal() as db:
        await server._delete_user_completely(db, 402)
        await db.commit()
        assert (await db.execute(select(server.CrisisNotification))).first() is None
