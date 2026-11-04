"""The caller's local calendar (B9): his day, hour and weekend, from a timestamp and a zone.

Design v4 counts days, hours and weekends in UTC (``engine.py``; ``memory.is_weekend``). At
UTC-6 a working day then falls on two UTC dates, and at UTC+10 Monday morning is Sunday.
Design v5 uses the caller's own wall clock, from the IANA time-zone database (daylight saving
included), with a day that starts at 04:00 local time, so a late evening stays on the day it
began::

    L    = ts + the zone's UTC offset at ts      (seconds on the local wall clock)
    day  = floor((L - day_start_hour * 3600) / 86400)
    hour = floor((L mod 86400) / 3600)           (the wall-clock hour; its day is ``day``)
    weekend when the weekday of ``day`` is in ``weekend_days`` (Monday = 0)

Every function here is pure: the same arguments always give the same answer. With zone
``UTC`` and ``day_start_hour = 0`` they give v4's UTC day, hour and weekend.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DAY_S = 86_400.0
HOUR_S = 3_600.0
HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7
DEFAULT_ZONE = "UTC"
DAY_START_HOUR = 4.0  # v5: a local day runs from 04:00 to 04:00
WEEKEND_DAYS = (5, 6)  # Saturday and Sunday, Monday = 0 (Python's ``date.weekday``)
EPOCH_WEEKDAY = 3  # day 0, 1970-01-01, was a Thursday
ZONE_CACHE = 512  # distinct zones kept loaded


@lru_cache(maxsize=ZONE_CACHE)
def zone(name: str) -> ZoneInfo:
    """The IANA zone ``name`` (``Europe/Berlin``, ``UTC``); ``ValueError`` if it is unknown."""
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"unknown time zone {name!r}") from exc


def check_day_start(day_start_hour: float) -> None:
    """``ValueError`` unless the day starts at an hour in [0, 24)."""
    if not 0 <= day_start_hour < HOURS_PER_DAY:
        raise ValueError(f"day_start_hour must be in [0, 24), not {day_start_hour!r}")


def local_seconds(ts: float, zone_name: str = DEFAULT_ZONE) -> float:
    """``ts`` on the zone's wall clock: ``ts`` plus the zone's UTC offset at that instant."""
    offset = datetime.fromtimestamp(ts, zone(zone_name)).utcoffset()
    return ts + (offset.total_seconds() if offset is not None else 0.0)


def local_day(
    ts: float, zone_name: str = DEFAULT_ZONE, day_start_hour: float = DAY_START_HOUR
) -> int:
    """The local day ``ts`` belongs to, counted from 1970-01-01, rolling over at
    ``day_start_hour`` local time (04:00 by default: 03:59 still belongs to the day before)."""
    check_day_start(day_start_hour)
    return math.floor((local_seconds(ts, zone_name) - day_start_hour * HOUR_S) / DAY_S)


def local_hour(ts: float, zone_name: str = DEFAULT_ZONE) -> int:
    """The wall-clock hour, 0-23, at ``ts`` in the zone. The rollover does not shift it: a
    call at 02:30 is hour 2 of the day before (see :func:`local_day`)."""
    return int((local_seconds(ts, zone_name) % DAY_S) // HOUR_S)


def weekday(day: int) -> int:
    """The weekday of a day number (from 1970-01-01), Monday = 0 ... Sunday = 6."""
    return (day + EPOCH_WEEKDAY) % DAYS_PER_WEEK


def is_weekend(day: int, weekend_days: Iterable[int] = WEEKEND_DAYS) -> bool:
    """Whether a day number falls on one of ``weekend_days`` (Saturday and Sunday by default,
    which is what ``memory.is_weekend`` gives for UTC days)."""
    return weekday(day) in tuple(weekend_days)
