"""Tests for the X2 per-actor cadence extractor (``gharchive_actor_cadence``).

Every event here is synthetic: invented logins, organisations and repositories. The windows,
runs and usuals are checked against the shipped engine (v4 windows, E4's ``own_session``,
``memory.DailyMean`` and ``memory.SlotQuantile``) on the same calls.
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from mcp_security.behaviour import own_session
from mcp_security.behaviour.clock import DAY_S, local_day
from mcp_security.behaviour.engine import (
    ASSETS_LAST_HOUR,
    BURST,
    CALL_METHOD,
    CALLS_LAST_HOUR,
    MINUTE_S,
    READ,
    SAME_CALL_10M,
    SESSION_LENGTH,
    WRITE,
    WRITES_LAST_HOUR,
    BehaviourConfig,
    BehaviourEngine,
    Message,
)
from mcp_security.behaviour.memory import HOUR_SLOT_S, REPETITION_SLOT_S, SlotQuantile, slot_of
from reports.experiments.dynamic_dimensions.heldout import gharchive_actor_cadence as cad
from reports.experiments.dynamic_dimensions.heldout import gharchive_request_sizes as gs
from tests.dynamic_dimensions.gharchive_support import (
    DAY,
    HOUR,
    MINUTE,
    MONDAY,
    ORG_A,
    ORG_B,
    OTHER_KEY,
    PERSON_A,
    assert_no_identities,
    comment,
    issue,
    pseudo,
    push,
    stamp,
    star,
)

FRIDAY = DAY - 1
RUN_GAP_S = 20 * MINUTE  # an always-on account's spacing, well under E4's 30 minutes
TOOLS = ("PushEvent", "IssueCommentEvent:created", "WatchEvent:started", "IssuesEvent:opened")
WRITE_TOOLS = frozenset({"PushEvent", "IssueCommentEvent:created", "IssuesEvent:opened"})
REPOS = ("r1", "r2", "r3", "r4")
#: Gaps that sit on and around every window edge and E4's idle gap.
GAPS = (0, 1, 5, 30, 59, 60, 61, 300, 599, 600, 601, 900, 1799, 1800, 1801, 3599, 3600, 3601)
LONG_GAPS = (7200, 14400, 30000)
STREAMS, STREAM_DAYS = 60, 3
#: B7's slots as memory.py defines them: clock hours, 10 minutes for Repetition.
B7_SLOTS = {
    CALLS_LAST_HOUR: HOUR_SLOT_S,
    WRITES_LAST_HOUR: HOUR_SLOT_S,
    ASSETS_LAST_HOUR: HOUR_SLOT_S,
    SAME_CALL_10M: REPETITION_SLOT_S,
}


def _parts(events: list[dict], first: int, last: int, **kw) -> list[cad.CadencePart]:
    """Each UTC day's parts from one stream, as one extract task per day would write them
    (each task keeps its day and the hour before it)."""
    parts = []
    for day in range(first, last + 1):
        parts += cad.extract_cadence(events, pseudo(), day, **kw).parts
    return parts


def _one_day(events: list[dict], day: int = DAY, **kw) -> cad.CadenceDay:
    """The v4 day ``day`` of the only actor in ``events`` (its parts merged)."""
    (row,) = cad.actor_days(_parts(events, day, day, **kw), gs.V4_DAYS)
    return row


# ── windows ────────────────────────────────────────────────────────────────────────────────


def test_part_maxima_follow_the_engine_windows() -> None:
    lookback = [comment("prev", day=DAY - 1, seconds=DAY_S - 600)]
    day = [
        comment("a", seconds=300),
        comment("b", seconds=310),
        push(repo="gears", seconds=320),
        issue("t", "b", seconds=320 + 3601),
        star(repo="sprockets", seconds=320 + 3601 + 1700),
        comment("next day", day=DAY + 1, seconds=5),
        comment("long before", day=DAY - 1, seconds=3600),
        comment("other org", org=ORG_B, seconds=400),
    ]
    keep = frozenset({gs.pseudonym(pseudo(), gs.ORG_ROLE, ORG_A)})
    out = cad.extract_cadence(day, pseudo(), DAY, lookback=lookback, orgs=keep)
    (part,) = out.parts
    assert (part.day, part.part, part.events, part.writes) == (DAY, gs.EARLY, 5, 4)
    assert part.maxima == {
        CALLS_LAST_HOUR: 4,  # the lookback comment is in the first events' hour
        WRITES_LAST_HOUR: 4,
        ASSETS_LAST_HOUR: 2,
        SAME_CALL_10M: 2,
        BURST: 3,
    }
    assert part.hours == {0: 3, 1: 2} and part.hour_assets == {0: 2, 1: 2}
    assert part.tools == {
        "IssueCommentEvent:created": 2,
        "IssuesEvent:opened": 1,
        "PushEvent": 1,
        "WatchEvent:started": 1,
    }
    assert len(part.assets) == 3
    assert out.stats["outside_day"] == 2 and out.stats["other_org"] == 1
    (row,) = cad.actor_days(out.parts, gs.V4_DAYS)
    assert row.maxima[SESSION_LENGTH] == 1700 / MINUTE_S  # the run after the hour's gap
    assert row.amounts()[cad.ACTIVE_HOURS] == 2 and row.amounts()[cad.DISTINCT_TOOLS] == 4
    assert row.weekday_class == cad.WEEKEND  # a Saturday
    without = cad.extract_cadence(day, pseudo(), DAY, orgs=keep).parts[0]
    assert without.maxima[CALLS_LAST_HOUR] == 3


@pytest.mark.parametrize(
    ("amount", "repo_b", "gap", "inside", "outside"),
    [
        (BURST, "widgets", 60, 2, 1),
        (SAME_CALL_10M, "widgets", 600, 2, 1),
        (CALLS_LAST_HOUR, "widgets", 3600, 2, 1),
        (WRITES_LAST_HOUR, "gears", 3600, 2, 1),
        (ASSETS_LAST_HOUR, "gears", 3600, 2, 1),
    ],
)
def test_window_edges_are_the_engines(
    amount: str, repo_b: str, gap: int, inside: int, outside: int
) -> None:
    # A window holds (ts - w, ts]: a call w - 1 seconds before still counts, w seconds not.
    start = 5 * HOUR
    for seconds, want in ((gap - 1, inside), (gap, outside)):
        events = [comment("x", seconds=start), comment("y", repo=repo_b, seconds=start + seconds)]
        assert _one_day(events).maxima[amount] == want


def test_breadth_and_repetition_follow_the_touched_repository() -> None:
    apart = _one_day(
        [comment("a", seconds=5 * HOUR), comment("b", repo="gears", seconds=5 * HOUR + 30 * MINUTE)]
    )
    assert (apart.maxima[ASSETS_LAST_HOUR], apart.maxima[BURST]) == (2, 1)
    two_repos = _one_day([push(seconds=5 * HOUR), push(repo="gears", seconds=5 * HOUR + 60)])
    assert two_repos.maxima[SAME_CALL_10M] == 1  # one tool key, two repositories
    one_repo = _one_day([push(seconds=5 * HOUR), push(seconds=5 * HOUR + 60)])
    assert one_repo.maxima[SAME_CALL_10M] == 2


def test_write_rate_is_read_at_every_call() -> None:
    # Pushes at 23:30, 23:40 and 23:50, a star at 00:10, a push at 01:00: at the star three
    # writes are in its hour, as the engine reads writes_last_hour at every call.
    lookback = [push(day=DAY - 1, seconds=DAY_S - m * MINUTE) for m in (30, 20, 10)]
    events = [star(seconds=10 * MINUTE), push(seconds=HOUR)]
    row = _one_day(events, lookback=lookback)
    assert row.maxima[WRITES_LAST_HOUR] == 3


# ── E4 runs across parts and days ──────────────────────────────────────────────────────────


def test_a_run_from_before_midnight_continues_into_the_day() -> None:
    # A call every 10 minutes from 23:10 (50 minutes before midnight) to 00:40.
    events = [comment("x", day=DAY - 1, seconds=DAY_S - m * MINUTE) for m in (50, 40, 30, 20, 10)]
    events += [comment("x", seconds=m * MINUTE) for m in (0, 10, 20, 30, 40)]
    parts = _parts(events, DAY - 1, DAY)
    v4 = {row.day: row.maxima[SESSION_LENGTH] for row in cad.actor_days(parts, gs.V4_DAYS)}
    assert v4 == {DAY - 1: 40.0, DAY: 90.0}
    (v5,) = cad.actor_days(parts, gs.V5_DAYS)  # 00:40 is still the v5 day before
    assert (v5.day, v5.maxima[SESSION_LENGTH]) == (DAY - 1, 90.0)
    # Without the day before, the run is seen from midnight only: a lower bound.
    alone = cad.actor_days(_parts(events, DAY, DAY), gs.V4_DAYS)
    assert alone[0].maxima[SESSION_LENGTH] == 40.0


def test_an_always_on_account_keeps_one_run_across_days() -> None:
    times = [DAY * DAY_S + k * RUN_GAP_S for k in range(int(3 * DAY_S // RUN_GAP_S))]
    events = [push(day=0, seconds=ts) for ts in times]
    parts = _parts(events, DAY, DAY + 2)
    rows = cad.actor_days(parts, gs.V4_DAYS)
    last = (DAY_S - RUN_GAP_S) / MINUTE_S  # 23:40, in minutes
    assert [r.maxima[SESSION_LENGTH] for r in rows] == [last, last + 1440, last + 2880]
    session, engine = None, Counter()
    for ts in times:
        session = own_session.advance(session, ts)
        day = int(ts // DAY_S)
        engine[day] = max(engine[day], session.minutes_at(ts))
    assert [engine[r.day] for r in rows] == [r.maxima[SESSION_LENGTH] for r in rows]
    per_part = cad.stitch_runs(sorted(parts, key=lambda p: (p.day, p.part)))
    assert max(s.longest for s in per_part) == last + 2880
    with pytest.raises(ValueError, match="order"):
        cad.stitch_runs(sorted(parts, key=lambda p: (p.day, p.part), reverse=True))


# ── against the engine on random streams ───────────────────────────────────────────────────


def _random_stream(rng: random.Random) -> list[dict]:
    """One actor's calls over STREAM_DAYS days, gaps on and around every window edge."""
    events, at = [], DAY * DAY_S + rng.choice((0, 600, 3000))
    while True:
        at += rng.choice(GAPS + LONG_GAPS)
        if at >= (DAY + STREAM_DAYS) * DAY_S:
            return events
        tool, repo = rng.choice(TOOLS), rng.choice(REPOS)
        kind, _, action = tool.partition(":")
        payload = {"action": action} if action else {}
        if kind == "IssueCommentEvent":
            payload |= {"issue": {"number": 1}, "comment": {"body": "x"}}
        events.append(
            {
                "type": kind,
                "actor": {"login": PERSON_A},
                "org": {"login": ORG_A},
                "repo": {"name": f"{ORG_A}/{repo}"},
                "payload": payload,
                "created_at": stamp(0, at),
            }
        )


def _engine_calls(events: list[dict]) -> list[tuple[float, str, str, dict[str, float]]]:
    """Each call's (ts, tool key, repository, the engine's window values and E4 minutes),
    read from a v4 engine and own_session fed the whole stream."""
    engine = BehaviourEngine(BehaviourConfig(design="v4"))
    session, out = None, []
    for e in events:
        ts, tool, repo = gs.event_time(e), cad.tool_key(e), e["repo"]["name"]
        operation = WRITE if tool in WRITE_TOOLS else READ
        engine.observe(
            Message(
                ts=ts, agent="a", method=CALL_METHOD, tool=tool, asset=repo, operation=operation
            )
        )
        session = own_session.advance(session, ts)
        st = engine.agents["a"]
        values = {
            CALLS_LAST_HOUR: len(st.recent),
            BURST: sum(1 for t in st.recent if t > ts - MINUTE_S),
            ASSETS_LAST_HOUR: st.assets_hour.distinct(),
            WRITES_LAST_HOUR: st.writes_hour.total(),
            SAME_CALL_10M: st.same_calls.count((tool, repo)),
            SESSION_LENGTH: session.minutes_at(ts),
        }
        out.append((ts, tool, repo, values))
    return out


def test_day_maxima_and_sums_equal_the_engine_on_random_streams() -> None:
    rng = random.Random(2026)
    compared = 0
    for _ in range(STREAMS):
        events = _random_stream(rng)
        calls = _engine_calls(events)
        parts = _parts(events, DAY, DAY + STREAM_DAYS - 1)
        for convention, rollover in ((gs.V4_DAYS, 0.0), (gs.V5_DAYS, 4.0)):
            peak: dict[int, Counter] = defaultdict(Counter)
            sums: dict[int, Counter] = defaultdict(Counter)
            counts: Counter = Counter()
            for ts, _, _, values in calls:
                day = local_day(ts, "UTC", rollover)
                counts[day] += 1
                for name, value in values.items():
                    peak[day][name] = max(peak[day][name], value)
                    sums[day][name] += value
            rows = cad.actor_days(parts, convention, utc_range=(DAY, DAY + STREAM_DAYS - 1))
            whole = range(DAY, DAY + STREAM_DAYS - (convention == gs.V5_DAYS))
            assert {r.day for r in rows} == {d for d in whole if counts[d]}
            for row in rows:
                compared += 1
                assert row.events == counts[row.day]
                assert row.maxima == {n: peak[row.day][n] for n in cad.DAY_AMOUNTS}
                for name in (*cad.USUAL_AMOUNTS, SESSION_LENGTH):
                    assert row.sums[name] == pytest.approx(sums[row.day][name], rel=1e-12)
    assert compared > 2 * STREAMS


def test_day_sums_rebuild_the_engines_usual() -> None:
    rng = random.Random(7)
    events = [e for e in _random_stream(rng) if gs.event_time(e) < (DAY + 2) * DAY_S]
    rows = cad.actor_days(_parts(events, DAY, DAY + 2), gs.V4_DAYS)
    past = [r for r in rows if r.day < DAY + 2]
    assert len(past) == 2
    engine = BehaviourEngine(BehaviourConfig(design="v4"))
    for e in events:
        tool, ts, repo = cad.tool_key(e), gs.event_time(e), e["repo"]["name"]
        operation = WRITE if tool in WRITE_TOOLS else READ
        engine.observe(
            Message(
                ts=ts, agent="a", method=CALL_METHOD, tool=tool, asset=repo, operation=operation
            )
        )
    st = engine.agents["a"]
    assert cad.usual_mean(past, CALLS_LAST_HOUR) == st.calls_last_hour.mean(DAY + 2)
    for name in (ASSETS_LAST_HOUR, WRITES_LAST_HOUR, SAME_CALL_10M):
        assert cad.usual_mean(past, name) == st.window_means[name].mean(DAY + 2)
    assert cad.usual_mean([], CALLS_LAST_HOUR) is None


def test_slot_histograms_rebuild_the_b7_usual() -> None:
    rng = random.Random(11)
    events = [e for e in _random_stream(rng) if gs.event_time(e) < (DAY + 2) * DAY_S]
    rows = cad.actor_days(_parts(events, DAY, DAY + 2), gs.V4_DAYS)
    stores = {name: SlotQuantile() for name in B7_SLOTS}
    for ts, _, _, values in _engine_calls(events):
        for name, store in stores.items():
            store.observe(int(ts // DAY_S), slot_of(ts, B7_SLOTS[name]), values[name])
    assert set(cad.USUAL_AMOUNTS) == set(B7_SLOTS)
    for name, store in stores.items():
        store.roll(DAY + 2, DAY)
        # Each day's histogram of slot maxima is the store's own, so is the usual.
        saved = {day: dict(counts) for day, counts in store.to_json()["by_day"]}
        assert {row.day: dict(row.slots[name]) for row in rows} == saved
        assert cad.usual_slot_quantile(rows, name) == store.usual() is not None
    with pytest.raises(ValueError):
        cad.usual_slot_quantile(rows, BURST)


# ── days, conventions and gaps ─────────────────────────────────────────────────────────────


def test_weekday_classes_follow_each_conventions_day() -> None:
    noon, two = 12 * HOUR, 2 * HOUR
    events = [
        comment("fri", day=FRIDAY, seconds=noon),
        comment("sat early", day=DAY, seconds=two),
        comment("sat", day=DAY, seconds=noon),
        comment("mon early", day=MONDAY, seconds=two),
        comment("mon", day=MONDAY, seconds=noon),
    ]
    parts, read = _parts(events, FRIDAY, MONDAY + 1), (FRIDAY, MONDAY + 1)
    v4_rows = cad.actor_days(parts, gs.V4_DAYS, utc_range=read)
    v4 = {r.day: (r.weekday_class, r.events) for r in v4_rows}
    assert v4 == {
        FRIDAY: (cad.WEEKDAY, 1),
        DAY: (cad.WEEKEND, 2),
        MONDAY: (cad.WEEKDAY, 2),
    }
    v5_rows = cad.actor_days(parts, gs.V5_DAYS, utc_range=read)
    v5 = {r.day: (r.weekday_class, r.events) for r in v5_rows}
    assert v5 == {  # 00:00-04:00 belongs to the day before
        FRIDAY: (cad.WEEKDAY, 2),
        DAY: (cad.WEEKEND, 1),
        MONDAY - 1: (cad.WEEKEND, 1),
        MONDAY: (cad.WEEKDAY, 1),
    }


def test_missing_days_drop_the_days_they_touch_and_end_runs() -> None:
    times = [(DAY - 1) * DAY_S + k * RUN_GAP_S for k in range(int(4 * DAY_S // RUN_GAP_S))]
    parts = _parts([push(day=0, seconds=ts) for ts in times], DAY - 1, DAY + 2)
    by_day = defaultdict(list)
    for part in parts:
        by_day[part.day].append(part)
    batches = [(DAY - 1, by_day[DAY - 1]), (DAY, None), (DAY + 1, by_day[DAY + 1])]
    batches.append((DAY + 2, by_day[DAY + 2]))
    v4 = list(cad.iter_actor_days(batches, gs.V4_DAYS))
    assert [r.day for r in v4] == [DAY - 1, DAY + 1, DAY + 2]
    assert v4[1].maxima[SESSION_LENGTH] == (DAY_S - RUN_GAP_S) / MINUTE_S  # starts afresh
    v5 = list(cad.iter_actor_days(batches, gs.V5_DAYS))
    assert [r.day for r in v5] == [DAY + 1]  # DAY - 1 and DAY touch DAY; DAY + 2 is the edge
    with pytest.raises(ValueError, match="consecutive"):
        list(cad.iter_actor_days([(DAY, []), (DAY + 2, [])]))


def test_extract_files_round_trip_hide_identities_and_check_keys(tmp_path: Path) -> None:
    events = [comment("a", seconds=300), push(repo="gears", seconds=5 * HOUR)]
    events += [comment("b", day=DAY + 2, seconds=300)]
    paths = []
    for day in (DAY, DAY + 2):
        out = cad.extract_cadence(events, pseudo(), day)
        text = json.dumps(out.to_json())
        assert_no_identities(text)
        assert cad.CadenceExtract.from_json(json.loads(text)).to_json() == out.to_json()
        paths.append(tmp_path / f"{gs.iso_day(day)}.json.gz")
        gs.write_json(paths[-1], out.to_json())
    loaded = cad.load_cadence(paths)
    keys = [(p.day, p.part) for p in loaded]
    assert keys == [(DAY, gs.EARLY), (DAY, gs.LATE), (DAY + 2, gs.EARLY)]
    with pytest.raises(ValueError, match="twice"):
        cad.load_cadence([paths[0], paths[0]])
    assert [(day, parts is None) for day, parts in cad.read_batches(paths)] == [
        (DAY, False),
        (DAY + 1, True),
        (DAY + 2, False),
    ]
    with pytest.raises(ValueError, match="order"):
        list(cad.read_batches([paths[1], paths[0]]))
    other = tmp_path / "other.json.gz"
    gs.write_json(other, cad.extract_cadence(events, pseudo(OTHER_KEY), DAY + 3).to_json())
    with pytest.raises(ValueError, match="key"):
        list(cad.read_batches([paths[0], other]))
    streams = cad.actor_streams(loaded, gs.V4_DAYS)
    assert [[d.day for d in s] for s in streams.values()] == [[DAY, DAY + 2]]


def test_streamed_summary_equals_the_in_memory_days(tmp_path: Path) -> None:
    rng = random.Random(5)
    events = []
    for i in range(14):
        login = f"{PERSON_A}{i}" if i < 12 else f"helper{i}[bot]"
        for day in range(DAY - 1, DAY + 4):
            for _ in range(rng.randint(0, 3)):
                events.append(comment("x", login=login, day=day, seconds=rng.randrange(86_400)))
    paths = []
    for day in range(DAY - 1, DAY + 4):
        paths.append(tmp_path / f"{gs.iso_day(day)}.json.gz")
        gs.write_json(paths[-1], cad.extract_cadence(events, pseudo(), day).to_json())
    for convention in gs.DAY_CONVENTIONS:
        streamed = cad.summarise_cadence(cad.iter_actor_days(cad.read_batches(paths), convention))
        rows = cad.actor_days(cad.load_cadence(paths), convention)
        assert streamed == cad.summarise_cadence(rows)
        cell = streamed["cells"][gs.PERSON][cad.ALL_DAYS]
        people = [r for r in rows if r.actor_class == gs.PERSON]
        assert cell["actor_days"] == len(people)
        for amount in cad.SUMMARY_AMOUNTS:
            values = [r.amounts()[amount] for r in people]
            assert cell["quantiles"][amount]["q0.9"] == gs.nearest_rank(values, 0.9)
        assert streamed["cells"][gs.BOT][cad.ALL_DAYS] == {"suppressed": True}  # 2 bots
        assert streamed["convention"] == convention
        assert streamed["caller_key"] == gs.CALLER_KEY


def _row(actor: str, day: int, events: int, cls: str, convention: str = gs.V5_DAYS):
    maxima = {name: float(events) for name in cad.DAY_AMOUNTS}
    return cad.CadenceDay(
        org="org",
        actor=actor,
        actor_class=cls,
        day=day,
        convention=convention,
        events=events,
        writes=events,
        maxima=maxima,
        sums=maxima,
        slots={},
        hours={9: events},
        hour_assets={9: 1},
        tools={"PushEvent": events},
        assets=("r",),
    )


def test_summary_suppresses_cells_under_ten_actors() -> None:
    rows = [_row(f"p{i}", MONDAY, i + 1, gs.PERSON) for i in range(12)]
    rows += [_row(f"b{i}", MONDAY, 50, gs.BOT) for i in range(gs.MIN_PUBLISH_ACTORS - 1)]
    rows += [_row(f"a{i}", MONDAY, 5, gs.AGENT) for i in range(gs.MIN_PUBLISH_ACTORS)]
    cells = cad.summarise_cadence(rows)["cells"]
    weekday = cells[gs.PERSON][cad.WEEKDAY]
    assert (weekday["actors"], weekday["actor_days"], weekday["orgs"]) == (12, 12, 1)
    assert weekday["quantiles"]["events"]["q0.5"] == gs.nearest_rank(list(range(1, 13)), 0.5)
    assert cells[gs.BOT][cad.WEEKDAY] == {"suppressed": True}  # 9 actors
    assert cells[gs.AGENT][cad.WEEKDAY]["actors"] == gs.MIN_PUBLISH_ACTORS
    assert cells[gs.PERSON][cad.WEEKEND] == {"suppressed": True}
    assert cells[gs.ALL_CLASSES][cad.ALL_DAYS]["actors"] == 12 + 9 + 10
    with pytest.raises(ValueError, match="conventions"):
        cad.summarise_cadence([*rows, _row("x", MONDAY, 1, gs.PERSON, gs.V4_DAYS)])


def test_summarise_command_reports_missing_days(tmp_path: Path) -> None:
    events = [comment("x", day=d, seconds=5 * HOUR) for d in (DAY, DAY + 2)]
    paths = []
    for day in (DAY, DAY + 2):
        paths.append(tmp_path / f"{gs.iso_day(day)}.json.gz")
        gs.write_json(paths[-1], cad.extract_cadence(events, pseudo(), day).to_json())
    out = tmp_path / "summary.json"
    cad.main(["summarise", "--days", gs.V4_DAYS, "--out", str(out), *map(str, reversed(paths))])
    days = gs.read_json(out)["utc_days"]
    assert days == {
        "first": gs.iso_day(DAY),
        "last": gs.iso_day(DAY + 2),
        "missing": [gs.iso_day(DAY + 1)],
    }
