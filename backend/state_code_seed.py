import itertools
import json
from pathlib import Path

CATALOGUE = Path(__file__).parent / "seed" / "state_codes.json"


def validate_catalogue(items):
    expected = {"".join(code) for code in itertools.product("1234", repeat=4)}
    if len(items) != 256 or {item["code"] for item in items} != expected:
        raise ValueError("The catalogue must contain all 256 unique state codes")
    for item in items:
        if any(item[key] != int(digit) for key, digit in zip(("a", "p", "h", "c"), item["code"])):
            raise ValueError("State-code dimensions do not match the code")
        if not item["title"] or not item["profile"]:
            raise ValueError("State-code text is missing")
    return items


def load_catalogue(path=CATALOGUE):
    return validate_catalogue(json.loads(Path(path).read_text(encoding="utf-8")))


async def ensure_catalogue(db, model):
    if db.bind.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    statement = insert(model).values(load_catalogue()).on_conflict_do_nothing(index_elements=["code"])
    await db.execute(statement)
