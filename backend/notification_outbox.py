import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
import uuid

from sqlalchemy import select

logger = logging.getLogger(__name__)


async def enqueue(session_factory, model, encrypt, args):
    async with session_factory() as db:
        db.add(model(id=str(uuid.uuid4()), user_id=args[2],
                     payload=encrypt(json.dumps(args, ensure_ascii=False), purpose="notification"),
                     next_attempt_at=datetime.now(timezone.utc)))
        await db.commit()
    return True


async def deliver_one(session_factory, model, decrypt, sender):
    now = datetime.now(timezone.utc)
    async with session_factory() as db:
        row = (await db.execute(select(model).where(model.next_attempt_at <= now)
               .order_by(model.next_attempt_at, model.id).limit(1)
               .with_for_update(skip_locked=True))).scalar_one_or_none()
        if row is None:
            return False
        try:
            args = json.loads(decrypt(row.payload, purpose="notification"))
            sent = await asyncio.to_thread(sender, *args)
        except Exception:
            logger.exception("Notification delivery failed id=%s", row.id)
            sent = False
        if sent:
            logger.info("Notification delivered id=%s", row.id)
            await db.delete(row)
        else:
            row.attempts += 1
            row.next_attempt_at = now + timedelta(seconds=min(3600, 30 * 2 ** min(row.attempts, 7)))
            logger.error("Notification pending id=%s attempt=%s", row.id, row.attempts)
        await db.commit()
        return True


async def run_worker(session_factory, model, decrypt, sender):
    while True:
        try:
            worked = await deliver_one(session_factory, model, decrypt, sender)
        except Exception:
            logger.exception("Notification outbox worker failed")
            worked = False
        await asyncio.sleep(1 if worked else 15)
