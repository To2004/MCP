"""The caller's local calendar (B9): local day with a 04:00 rollover, hour, weekend, DST."""

from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from mcp_security.behaviour import clock
from mcp_security.behaviour.memory import is_weekend as utc_is_weekend

HOUR_S, DAY_S = 3_600.0, 86_400.0
EPOCH = date(1970, 1, 1)
NEW_YORK, BERLIN, SYDNEY, KOLKATA = (
    "America/New_York",
    "Europe/Berlin",
    "Australia/Sydney",
    "Asia/Kolkata",
)
UTC_STEP_S = 1_234.5  # an odd step, so every hour and both sides of midnight are sampled
UTC_SPAN_DAYS = 16


def at(zone_name: str, *when: int, fold: int = 0) -> float:
    """The timestamp of a wall-clock time in a zone (``fold=1``: the second of a repeat)."""
    return datetime(*when, tzinfo=ZoneInfo(zone_name), fold=fold).timestamp()


def day_of(year: int, month: int, day: int) -> int:
    return (date(year, month, day) - EPOCH).days


def test_utc_with_a_midnight_rollover_is_v4s_day_hour_and_weekend() -> None:
    start = datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp()
    ts = start
    while ts < start + UTC_SPAN_DAYS * DAY_S:
        day = clock.local_day(ts, "UTC", 0.0)
        assert day == int(ts // DAY_S)
        assert clock.local_hour(ts, "UTC") == int((ts % DAY_S) // HOUR_S)
        assert clock.is_weekend(day) == utc_is_weekend(day)
        ts += UTC_STEP_S


def test_the_day_rolls_over_at_four_in_the_morning_local_time() -> None:
    assert clock.local_day(at(BERLIN, 2026, 7, 15, 3, 59, 59), BERLIN) == day_of(2026, 7, 14)
    assert clock.local_day(at(BERLIN, 2026, 7, 15, 4, 0, 0), BERLIN) == day_of(2026, 7, 15)
    late = at(BERLIN, 2026, 7, 15, 2, 30)  # still the evening's day, but hour 2
    assert (clock.local_day(late, BERLIN), clock.local_hour(late, BERLIN)) == (
        day_of(2026, 7, 14),
        2,
    )


def test_spring_forward_skips_an_hour_and_shortens_that_local_day() -> None:
    before = at(NEW_YORK, 2026, 3, 8, 1, 59)  # EST
    after = before + 60.0  # 03:00 EDT: 02:00-02:59 never happens
    assert [clock.local_hour(t, NEW_YORK) for t in (before, after)] == [1, 3]
    assert clock.local_day(before, NEW_YORK) == clock.local_day(after, NEW_YORK)
    assert clock.local_day(after, NEW_YORK) == day_of(2026, 3, 7)
    start, end = at(NEW_YORK, 2026, 3, 7, 4), at(NEW_YORK, 2026, 3, 8, 4)
    assert clock.local_day(end, NEW_YORK) == clock.local_day(start, NEW_YORK) + 1
    assert end - start == 23 * HOUR_S


def test_fall_back_repeats_an_hour_on_the_same_local_day() -> None:
    first = at(NEW_YORK, 2026, 11, 1, 1, 30, fold=0)  # EDT
    second = at(NEW_YORK, 2026, 11, 1, 1, 30, fold=1)  # EST, an hour later
    assert second - first == HOUR_S
    assert clock.local_hour(first, NEW_YORK) == clock.local_hour(second, NEW_YORK) == 1
    assert clock.local_day(first, NEW_YORK) == clock.local_day(second, NEW_YORK)
    assert clock.local_day(first, NEW_YORK) == day_of(2026, 10, 31)
    start, end = at(NEW_YORK, 2026, 10, 31, 4), at(NEW_YORK, 2026, 11, 1, 4)
    assert end - start == 25 * HOUR_S


def test_european_switches_move_the_hour_not_the_day() -> None:
    spring = at(BERLIN, 2026, 3, 29, 1, 59)
    assert clock.local_hour(spring + 60.0, BERLIN) == 3  # 02:00 CET is 03:00 CEST
    autumn = at(BERLIN, 2026, 10, 25, 2, 30, fold=1)
    assert clock.local_hour(autumn, BERLIN) == 2
    assert clock.local_day(autumn, BERLIN) == day_of(2026, 10, 24)


def test_monday_morning_in_sydney_is_not_a_weekend_though_utc_says_sunday() -> None:
    monday = at(SYDNEY, 2026, 6, 1, 8)
    utc_day = int(monday // DAY_S)
    assert utc_is_weekend(utc_day)  # Sunday 22:00 UTC
    day = clock.local_day(monday, SYDNEY)
    assert day == day_of(2026, 6, 1) and not clock.is_weekend(day)
    assert clock.local_hour(monday, SYDNEY) == 8


def test_a_half_hour_zone_and_custom_weekend_days() -> None:
    midnight_utc = datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp()
    assert clock.local_hour(midnight_utc, KOLKATA) == 5  # 05:30 local
    assert clock.local_day(midnight_utc, KOLKATA) == day_of(2026, 6, 1)
    friday = day_of(2026, 6, 5)
    assert clock.weekday(friday) == 4 and clock.weekday(0) == clock.EPOCH_WEEKDAY
    assert clock.is_weekend(friday, (4, 5)) and not clock.is_weekend(friday)


@pytest.mark.parametrize("bad_zone", ["Mars/Olympus_Mons", "", "../etc/passwd"])
def test_an_unknown_zone_is_an_error(bad_zone: str) -> None:
    with pytest.raises(ValueError, match="unknown time zone"):
        clock.local_day(0.0, bad_zone)


@pytest.mark.parametrize("hour", [-1.0, 24.0])
def test_a_day_start_outside_the_day_is_an_error(hour: float) -> None:
    with pytest.raises(ValueError, match="day_start_hour"):
        clock.local_day(0.0, "UTC", hour)
