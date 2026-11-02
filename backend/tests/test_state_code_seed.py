import pytest
from sqlalchemy import select

import server
from state_code_seed import ensure_catalogue, load_catalogue
from conftest import TestingSessionLocal


def test_catalogue_complete():
    assert len(load_catalogue()) == 256


@pytest.mark.anyio
async def test_seed_fills_missing_without_overwriting_admin_edits(init_db):
    async with TestingSessionLocal() as db:
        db.add(server.StateCode(code="1111", a=1, p=1, h=1, c=1,
                                title="Editorial title", profile="Edited profile"))
        await db.commit()
        await ensure_catalogue(db, server.StateCode)
        await ensure_catalogue(db, server.StateCode)
        await db.commit()
        rows = (await db.execute(select(server.StateCode))).scalars().all()
        assert len(rows) == 256
        edited = next(row for row in rows if row.code == "1111")
        assert edited.title == "Editorial title"
        assert edited.profile == "Edited profile"
