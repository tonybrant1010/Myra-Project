from datetime import datetime, timedelta, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


try:
    from zoneinfo import ZoneInfo
    _BUDAPEST_TZ = ZoneInfo("Europe/Budapest")
except Exception:
    _BUDAPEST_TZ = None


def _last_sunday_utc(year: int, month: int) -> datetime:
    d = datetime(year, month, 31, tzinfo=timezone.utc)
    d -= timedelta(days=(d.weekday() + 1) % 7)
    return d.replace(hour=1, minute=0, second=0, microsecond=0)


def _to_local(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if _BUDAPEST_TZ is not None:
        return dt.astimezone(_BUDAPEST_TZ)
    u = dt.astimezone(timezone.utc)
    dst = _last_sunday_utc(u.year, 3) <= u < _last_sunday_utc(u.year, 10)
    return u.astimezone(timezone(timedelta(hours=2 if dst else 1)))
