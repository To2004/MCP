"""The "Bot Day Check" item bank (human study of the dynamic layer).

``items.json`` is embedded in a public web page, so it must hold nothing from the private key:
no scores, strata, gray kinds, labels, agent ids or day numbers. Every card holds the same nine
rows in the same order (one is never shown), ids are opaque and salted, the hand-built cards
share no novelty phrase with a simulator card, and ``cards.txt`` is ``items.json`` rendered. The
selection and rendering are tested on small synthetic inputs (fast, no simulator run); the
committed bank is checked once at the end.
"""

from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

STUDY = (
    Path(__file__).resolve().parents[1] / "reports" / "experiments" / "dynamic_dimensions"
) / "human_study"
sys.path.insert(0, str(STUDY))

from make_items import (  # noqa: E402
    FIRST_ATTENTION_POSITION,
    N_FORMS,
    ROW_MAP,
    build_bank,
)
from normal_org_world import GRAY_KINDS  # noqa: E402
from study_facts import (  # noqa: E402
    HIDDEN_ROWS,
    NOT_RECORDED,
    ROW_IDS,
    DayFacts,
    card_rows,
    collect_facts,
    history_of,
)
from study_notes import AgentProfile, latent_cause  # noqa: E402
from study_pairs import MIN_MARGIN, PAIR_TYPES, STRICT_MARGIN_TYPES, select_pairs  # noqa: E402
from study_scores import DayScore, daily_list  # noqa: E402
from study_select import (  # noqa: E402
    ALERT,
    CHANGE_TAGS,
    GRAY,
    HIDDEN_GRAY_KINDS,
    MAX_BOT_CARDS,
    MAX_BOTS_PER_STRATUM,
    ORDINARY,
    STRATA,
    STRATUM_NAMES,
    AgentDay,
    Usage,
    opaque_id,
    select_cards,
    shuffle_apart,
)
from study_text import (  # noqa: E402
    HAND_CARDS,
    novelty_phrases,
    render_text,
    shared_novelty,
)
from study_words import (  # noqa: E402
    clock,
    hours_text,
    plain_range,
    round_plain,
    size_today,
    size_usual,
)

ITEMS = STUDY / "items.json"
KEY = STUDY / "key.json"
CARDS_TXT = STUDY / "cards.txt"
CARD_ID = re.compile(r"^c[0-9a-f]{4}$")
CARD_ID_IN_TEXT = re.compile(r"\b[cp][0-9a-f]{4}\b")
PAIR_ID = re.compile(r"^p[0-9a-f]{4}$")
AGENT_ID = re.compile(r"\b(?:dev|lead|sre|pm|ci_bot|triage_bot|report_bot)-\d{3}\b")
#: keys that belong to the private key only
KEY_FIELDS = {
    "stratum",
    "gray_kind",
    "gray_kinds",
    "tags",
    "org_event",
    "agent",
    "role",
    "M",
    "R",
    "strongest",
    "s2",
    "listed",
    "list_rank",
    "list_chance",
    "attention",
    "engine_prefers",
    "gray_card",
    "type",
    "expected",
    "history_days",
    "above_ordinary",
    "latent_cause",
    "margin",
    "tie_on_M",
    "close",
    "id_salt",
}
#: the only numbers items.json may hold: a practice card's expected answer
NUMBER_PATHS = re.compile(r"^practice\.\d+\.feedback\.(unusual|check)$")
WEEKDAY_NAMES = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
WEEKEND_NAMES = {"Saturday", "Sunday"}
#: words that must never reach a participant: product names and sizes in KB
FORBIDDEN_WORDS = ("Cursor", "Copilot", "Claude Code", "Claude desktop", " KB", "hand-written")
MIN_WEEKDAYS, MIN_ROLES = 4, 4  # spread of the 16 scored cards
FIRST_DAY, N_DAYS, N_AGENTS = 100, 40, 60
SYNTHETIC_KINDS = (
    "bulk_export",
    "scope_creep",
    "mass_cleanup",
    "off_hours_batch",
    "sensitive_peek",
    "slow_loop",
    "overfetch",
)
SYNTHETIC_TAGS = ("travel", "back_from_vacation", "release_crunch", "new_hire", "client_switch")
SYNTHETIC_CAUSES = ("request_too_big", "tool", "same_call_10m", "asset", "time_of_day", "network")
SYNTHETIC_ROLES = ("dev", "lead", "sre", "pm", "ci_bot")
SYNTHETIC_M_FLOOR, SYNTHETIC_M_RATE = 0.7, 1.2  # M = floor + an exponential draw
SYNTHETIC_SALT = "test-salt"


# ── synthetic inputs ─────────────────────────────────────────────────────────────────────
def synthetic_days(seed: int = 5) -> list[AgentDay]:
    """A small organisation: 60 agents over 40 days, ranked by M, top 4 listed each day."""
    rng = random.Random(seed)
    out = []
    for day in range(FIRST_DAY, FIRST_DAY + N_DAYS):
        rows = []
        for a in range(N_AGENTS):
            x = rng.random()
            gray = (rng.choice(SYNTHETIC_KINDS),) if x < 0.15 else ()
            tags = (rng.choice(SYNTHETIC_TAGS),) if 0.15 <= x < 0.4 else ()
            m = SYNTHETIC_M_FLOOR + rng.expovariate(SYNTHETIC_M_RATE)
            rows.append((f"{SYNTHETIC_ROLES[a % len(SYNTHETIC_ROLES)]}-{a:03d}", m, gray, tags))
        rows.sort(key=lambda r: -r[1])
        for rank, (agent, m, gray, tags) in enumerate(rows, start=1):
            out.append(
                AgentDay(
                    agent=agent,
                    day=day,
                    role=agent.rsplit("-", 1)[0],
                    multiplier=m,
                    risk=3 * m,
                    strongest=rng.choice(SYNTHETIC_CAUSES),
                    second=0.1,
                    above_ordinary=(),
                    rank=rank,
                    chance=1.0 if rank <= 4 else 0.0,
                    tags=tags,
                    gray_kinds=gray,
                    history_days=60,
                    org_event="vpn_change" if day % 9 == 0 else None,
                    actions=40,
                    local_dates=(day,),
                    latent_cause="isp_change" if rank % 3 == 0 else None,
                )
            )
    return out


def synthetic_facts(agent_index: int) -> dict[int, DayFacts]:
    """An agent's days 0..139: work 9 am-5 pm on three projects, every day."""
    days = {}
    for day in range(FIRST_DAY + N_DAYS):
        calls = 40 + (day * 7 + agent_index) % 30
        days[day] = DayFacts(
            calls=calls,
            hours=set(range(9, 17)),
            assets={f"t0-svc{(day + k) % 4}": 2 for k in range(3)},
            writes=calls // 10,
            max_size=2_000 + 100 * (day % 20),
            max_repeat=2 + day % 3,
            local_dates={day},
            networks={"203.0.0.0/16"},
            apps={"cursor"},
            tools=Counter({"get_file_contents": calls - 5, "search_code": 5}),
        )
    return days


def synthetic_bank(seed: int = 11, salt: str = SYNTHETIC_SALT) -> tuple[dict, dict]:
    """items and key built from the synthetic organisation."""
    days = synthetic_days()
    rng = random.Random(seed)
    usage = Usage()
    picks = select_cards(days, rng, usage)
    pairs = select_pairs(days, rng, usage)
    agents = sorted({d.agent for d in days})
    profiles = {a: AgentProfile(a, a.rsplit("-", 1)[0], 0.0, None) for a in agents}
    facts = {a: synthetic_facts(i) for i, a in enumerate(agents)}
    return build_bank(picks, pairs, profiles, facts, rng, (salt, "test", seed))


# ── checks shared by the synthetic and the committed bank ────────────────────────────────
def leaves(value: object, path: str = ""):
    """(dotted path, leaf) of every leaf in a JSON value."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield from leaves(v, f"{path}.{k}" if path else str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from leaves(v, f"{path}.{i}" if path else str(i))
    else:
        yield path, value


def all_keys(value: object) -> set[str]:
    """Every dict key anywhere in a JSON value."""
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in all_keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in all_keys(v)}
    return set()


def every_card(items: dict) -> list[dict]:
    """Practice cards, cards and the cards inside pairs."""
    return items["practice"] + items["cards"] + [c for p in items["pairs"] for c in p["cards"]]


def assert_public(items: dict, key: dict) -> None:
    """items.json holds nothing from the key."""
    leaked = all_keys(items) & KEY_FIELDS
    assert not leaked, f"key fields in items.json: {sorted(leaked)}"
    for path, value in leaves(items):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            assert NUMBER_PATHS.match(path), f"a number in items.json at {path}: {value}"
    text = json.dumps(items)
    assert not AGENT_ID.search(text), "an agent id in items.json"
    for word in FORBIDDEN_WORDS:
        assert word not in text, f"{word!r} in items.json"
    assert key.get("id_salt") is None or key["id_salt"] not in text
    labels = set(GRAY_KINDS) | {"bot_loop"} | set(CHANGE_TAGS) | set(ROW_MAP) | set(PAIR_TYPES)
    # only labels that cannot be plain words ("travel" is a tag, "traveling" a note)
    forbidden = {w for w in labels if "_" in w} | {"overfetch"} | set(STRATUM_NAMES.values())
    for word in sorted(forbidden):
        assert word not in text, f"{word!r} in items.json"
    for card in key["cards"].values():
        if card["agent"]:
            assert card["agent"] not in text


def assert_cards_well_formed(items: dict) -> None:
    """Fixed rows on every card, weekday names, opaque unique ids, valid card orders."""
    assert [r["id"] for r in items["rows"]] == list(ROW_IDS)
    assert {r["id"] for r in items["rows"] if not r["shown"]} == HIDDEN_ROWS
    ids = []
    for card in every_card(items):
        assert CARD_ID.match(card["id"]), card["id"]
        ids.append(card["id"])
        assert [r["id"] for r in card["rows"]] == list(ROW_IDS)
        for row in card["rows"]:
            assert isinstance(row["usual"], str) and row["usual"]
            assert isinstance(row["today"], str) and row["today"]
        downloads = next(r for r in card["rows"] if r["id"] == "downloads")
        assert downloads["usual"] == downloads["today"] == NOT_RECORDED
        assert card["day"] in WEEKDAY_NAMES
        assert isinstance(card["who"], str) and card["who"]
        for note in ("calendar", "company"):
            assert card[note] is None or isinstance(card[note], str)
    for pair in items["pairs"]:
        assert PAIR_ID.match(pair["id"]), pair["id"]
        assert len(pair["cards"]) == 2
        ids.append(pair["id"])
    assert len(ids) == len(set(ids)), "ids are not unique"
    forms = items["forms"]
    assert len(forms) == N_FORMS and forms[0]["cards"] == [c["id"] for c in items["cards"]]
    assert len({tuple(f["cards"]) for f in forms}) == N_FORMS, "two card orders are the same"
    for form in forms:
        assert sorted(form["cards"]) == sorted(c["id"] for c in items["cards"])


def assert_forms_keep_strata_apart(items: dict, key: dict) -> None:
    """Every card order: no neighbours from one stratum, attention checks not first, one late."""
    for form in items["forms"]:
        strata = [key["cards"][cid]["stratum"] for cid in form["cards"]]
        assert all(a != b for a, b in zip(strata, strata[1:])), form["id"]
        attention = [i for i, cid in enumerate(form["cards"]) if key["cards"][cid]["attention"]]
        assert min(attention) >= FIRST_ATTENTION_POSITION, form["id"]
        assert max(attention) >= len(form["cards"]) // 2, form["id"]


def assert_no_shared_phrases(items: dict, key: dict) -> None:
    """The hand-built cards' novelty phrases appear on no simulator card."""
    attention = [c for c in items["cards"] if key["cards"][c["id"]]["attention"]]
    real = [c for c in items["cards"] if not key["cards"][c["id"]]["attention"]]
    real += [c for p in items["pairs"] for c in p["cards"]]
    assert not shared_novelty(items["practice"] + attention, real)


def assert_key_matches(items: dict, key: dict) -> None:
    """Strata, attention checks and pairs as specified, and in step with items.json."""
    assert len(items["practice"]) == 2
    assert [c["id"] for c in items["cards"]] == list(key["cards"])
    assert [p["id"] for p in items["pairs"]] == list(key["pairs"])
    strata = Counter(c["stratum"] for c in key["cards"].values())
    assert strata == Counter({**STRATA, "attention": 2})
    assert sorted(c["attention"] for c in key["cards"].values() if c["attention"]) == [
        "normal",
        "wild",
    ]
    order = [key["cards"][c["id"]]["stratum"] for c in items["cards"]]
    assert all(a != b for a, b in zip(order, order[1:])), "neighbouring cards share a stratum"
    assert_forms_keep_strata_apart(items, key)
    assert_no_shared_phrases(items, key)
    by_stratum: dict[str, list[dict]] = {}
    for card in key["cards"].values():
        by_stratum.setdefault(card["stratum"], []).append(card)
    caught, alarms, missed = by_stratum["A"], by_stratum["B"], by_stratum["C"]
    changes, plain = by_stratum["D"], by_stratum["E"]
    assert all(c["listed"] and c["gray_kind"] for c in caught)
    assert len({c["gray_kind"] for c in caught}) == len(caught)
    assert all(c["listed"] and not c["gray_kind"] and not c["tags"] for c in alarms)
    assert len({c["strongest"] for c in alarms}) == len(alarms)
    assert any(c["latent_cause"] is None for c in alarms), "every false alarm has a latent cause"
    assert all(c["list_chance"] == 0 and c["gray_kind"] for c in missed)
    assert len({c["gray_kind"] for c in missed}) == len(missed)
    assert not {c["gray_kind"] for c in missed} & HIDDEN_GRAY_KINDS
    assert all(c["tags"] and not c["gray_kind"] for c in changes)
    assert any(c["M"] >= ALERT for c in changes) and any(c["M"] < ALERT for c in changes)
    assert all(c["list_chance"] == 0 and c["M"] <= 1 and not c["tags"] for c in plain)
    assert Counter(p["type"] for p in key["pairs"].values()) == Counter(PAIR_TYPES)
    card_days = {(c["agent"], c["day"]) for c in key["cards"].values() if c["agent"]}
    agents = [c["agent"] for c in key["cards"].values() if c["agent"]]
    for pair_id, pair in key["pairs"].items():
        shown = [c["id"] for c in next(p for p in items["pairs"] if p["id"] == pair_id)["cards"]]
        assert sorted(pair["cards"]) == sorted(shown)
        assert pair["engine_prefers"] in shown
        assert pair["gray_card"] is None or pair["gray_card"] in shown
        details = pair["cards"]
        assert len({d["day"] for d in details.values()}) == 1, "a pair spans two days"
        preferred = details[pair["engine_prefers"]]
        other = next(d for cid, d in details.items() if cid != pair["engine_prefers"])
        assert preferred["list_rank"] < other["list_rank"]
        assert preferred["M"] > other["M"] and not pair["tie_on_M"], "a tie decided by s2"
        assert pair["close"] == (pair["margin"] < MIN_MARGIN)
        if pair["type"] in STRICT_MARGIN_TYPES:
            assert pair["margin"] >= MIN_MARGIN
        if pair["type"] == "gray_over_ordinary":
            assert preferred["listed"] and preferred["gray_kind"]
            assert other["list_chance"] == 0 and not other["gray_kind"] and not other["tags"]
        elif pair["type"] == "false_alarm_over_gray":
            assert preferred["listed"] and not preferred["gray_kind"] and not preferred["tags"]
            assert other["list_chance"] == 0 and other["gray_kind"]
        else:
            assert preferred["list_rank"] == 1 and other["list_rank"] == 4
            assert preferred["listed"] and other["listed"]
        for d in details.values():
            assert (d["agent"], d["day"]) not in card_days, "a pair reuses a card"
            agents.append(d["agent"])
    assert len(agents) == len(set(agents)), "an agent appears twice"


# ── selection on synthetic input ─────────────────────────────────────────────────────────
def test_select_cards_fills_every_stratum() -> None:
    days = synthetic_days()
    picks = select_cards(days, random.Random(1), Usage())
    assert Counter(p.stratum for p in picks) == Counter(STRATA)
    by = {s: [p.day for p in picks if p.stratum == s] for s in STRATA}
    assert all(d.category == GRAY and d.listed for d in by["A"])
    assert all(d.category == ORDINARY and d.listed for d in by["B"])
    assert all(d.category == GRAY and d.unlisted for d in by["C"])
    assert all(d.category == "change" for d in by["D"])
    assert all(d.category == ORDINARY and d.unlisted and d.multiplier <= 1 for d in by["E"])
    assert len({d.gray_kind for d in by["A"]}) == STRATA["A"]
    assert not {d.gray_kind for d in by["C"]} & HIDDEN_GRAY_KINDS
    assert {d.multiplier >= ALERT for d in by["D"]} == {True, False}
    assert len({p.day.agent for p in picks}) == len(picks)


def test_select_pairs_same_day_and_new_agents() -> None:
    days = synthetic_days()
    usage = Usage()
    picks = select_cards(days, random.Random(1), usage)
    card_agents = {p.day.agent for p in picks}
    pairs = select_pairs(days, random.Random(1), usage)
    assert Counter(p.pair_type for p in pairs) == Counter(PAIR_TYPES)
    for pair in pairs:
        assert pair.preferred.day == pair.other.day
        assert pair.preferred.rank < pair.other.rank
        assert not {pair.preferred.agent, pair.other.agent} & card_agents
    assert len({p.preferred.day for p in pairs}) == len(pairs), "two pairs on one day"


def test_selection_is_deterministic_and_order_free() -> None:
    days = synthetic_days()
    first = select_cards(days, random.Random(3), Usage())
    again = select_cards(list(reversed(days)), random.Random(3), Usage())
    assert first == again


def test_bank_is_deterministic_and_public() -> None:
    items, key = synthetic_bank()
    items_again, key_again = synthetic_bank()
    assert json.dumps(items) == json.dumps(items_again)
    assert json.dumps(key) == json.dumps(key_again)
    assert render_text(items) == render_text(items_again)
    assert_public(items, key)
    assert_cards_well_formed(items)
    assert_key_matches(items, key)


def test_the_salt_changes_every_id_and_nothing_else() -> None:
    items, _ = synthetic_bank()
    salted, _ = synthetic_bank(salt="another secret")
    ids = {c["id"] for c in items["cards"]} | {p["id"] for p in items["pairs"]}
    other = {c["id"] for c in salted["cards"]} | {p["id"] for p in salted["pairs"]}
    assert not ids & other
    assert [c["rows"] for c in items["cards"]] == [c["rows"] for c in salted["cards"]]


def test_hand_cards_novelty_phrases_and_overlap_check() -> None:
    wild = HAND_CARDS["practice_wild"]
    assert novelty_phrases(wild) == {
        "delete a project",
        "change who can see a project",
        "a phone app",
    }
    copycat = {"rows": [{"id": "kinds", "usual": "x", "today": "delete a project (new to it)"}]}
    assert shared_novelty([wild], [copycat]) == {"delete a project"}
    assert not shared_novelty([wild], [HAND_CARDS["practice_normal"]])
    report = HAND_CARDS["attention_wild"]
    assert novelty_phrases(report) == {
        "change the project settings",
        "delete a task",
        "invite someone to a project",
        "a network in another country",
    }


def test_opaque_id_rehashes_on_collision() -> None:
    taken: set[str] = set()
    first = opaque_id("c", ("x", 1), taken)
    second = opaque_id("c", ("x", 1), taken)
    assert CARD_ID.match(first) and CARD_ID.match(second) and first != second


def test_shuffle_apart_keeps_groups_apart() -> None:
    items = [(group, i) for group, n in (("a", 4), ("b", 3), ("c", 3)) for i in range(n)]
    out = shuffle_apart(items, lambda x: x[0], random.Random(2))
    assert sorted(out) == sorted(items)
    assert all(a[0] != b[0] for a, b in zip(out, out[1:]))
    assert out == shuffle_apart(items, lambda x: x[0], random.Random(2))


def test_daily_list_ranks_and_ties_at_the_cut() -> None:
    multipliers = (5, 4, 3, 2, 2, 1)
    scores = {(f"a{i}", 100): DayScore(m, m, "tool", 0.0, ()) for i, m in enumerate(multipliers)}
    places = daily_list(scores, list_size=4)
    assert [places[(f"a{i}", 100)].rank for i in range(6)] == [1, 2, 3, 4, 4, 6]
    assert [places[(f"a{i}", 100)].chance for i in range(6)] == [1, 1, 1, 0.5, 0.5, 0]


# ── facts and plain words ────────────────────────────────────────────────────────────────
def sim_row(
    ts: float,
    tool: str | None = "get_issue",
    asset: str | None = "t0-svc0",
    sens: int | None = 2,
    op: str | None = "read",
    address: str = "203.0.1.1",
    size: int = 200,
) -> tuple:
    """One message in ``normal_org_world.ROW`` layout; ``tool=None`` is an ``initialize``."""
    method = "tools/call" if tool else "initialize"
    return (ts, method, "s", tool, asset, sens, op, address, "cursor/1.0", size, 3, "", "")


def test_an_agent_day_spanning_two_local_dates_is_not_usable() -> None:
    """A tz=-6 owner working 8 am-8 pm local: the evening falls on the next server day."""
    day = 100
    local_8am = (20_003 + day) * 86_400.0 + (8 + 6) * 3_600.0
    rows = [sim_row(local_8am + h * 3_600.0) for h in range(13)]  # 8 am .. 8 pm local
    facts = collect_facts(rows, tz=-6)
    assert facts[day].local_dates == {day} and facts[day + 1].local_dates == {day}
    assert facts[day + 1].hours == {18, 19, 20}  # 6-8 pm of the day before, local

    def agent_day(d: int) -> AgentDay:
        dates = tuple(sorted(facts[d].local_dates))
        return AgentDay(
            "dev-001",
            d,
            "dev",
            1.0,
            1.0,
            "tool",
            0.0,
            (),
            9,
            0.0,
            history_days=60,
            actions=facts[d].calls,
            local_dates=dates,
        )

    assert agent_day(day).usable and not agent_day(day + 1).usable


def test_latent_cause_marks_the_first_day_on_a_new_home_line() -> None:
    person = SimpleNamespace(isp_change=(120, (70, 12)), switch_day=10**9, switch_to="")
    agent = AgentProfile("dev-001", "dev", 0.0, person)
    old, new = {"70.11.0.0/16"}, {"70.12.0.0/16"}
    days = {d: DayFacts(calls=5, networks=old if d < 124 else new) for d in range(110, 130)}
    assert latent_cause(agent, days, 124, set()) == "isp_change"
    assert latent_cause(agent, days, 125, set()) is None  # not the first day any more
    assert latent_cause(agent, days, 124, {"isp_change"}) is None  # labelled: not latent
    assert latent_cause(AgentProfile("ci_bot-001", "ci_bot", 0.0, None), days, 124, set()) is None


def test_collect_facts_counts_one_day() -> None:
    base = (20_003 + 100) * 86_400.0 + 9 * 3_600.0  # day 100, 9:00 on the server's clock
    rows = [
        sim_row(base - 1, tool=None, asset=None, sens=None, op=None),
        sim_row(base),
        sim_row(base + 60),
        sim_row(base + 120, "update_issue", "secrets", 5, "write", "70.10.3.4", 4_500),
        sim_row(base + 900),
    ]
    day = collect_facts(rows, tz=-6)[100]
    assert day.calls == 4 and day.writes == 1 and day.max_size == 4_500
    assert day.max_repeat == 2  # the third get_issue is 15 minutes after the first
    assert day.hours == {3}  # 9:00 on the server's clock is 3 am six hours behind
    assert day.local_dates == {100}
    assert day.networks == {"203.0.0.0/16", "70.10.0.0/16"} and day.apps == {"cursor"}
    assert day.assets == {"t0-svc0": 2, "secrets": 5}


def test_card_rows_fixed_order_and_novelty() -> None:
    facts = synthetic_facts(0)
    history = history_of(facts, 120)
    usual = card_rows(facts[120], history)
    assert [r["id"] for r in usual] == list(ROW_IDS)
    rows = {r["id"]: r for r in usual}
    assert rows["kinds"]["today"] == "nothing new"
    assert rows["connection"]["today"] == "office; its usual app (nothing new)"
    assert rows["connection"]["usual"] == "office (every day); 1 app"
    assert rows["projects"]["today"] == "3 projects. New to it: 0. Marked sensitive: 0."
    odd = DayFacts(
        calls=900,
        hours={2, 3},
        assets={"payroll": 5, "t0-svc1": 2},
        writes=0,
        max_size=300_000,
        max_repeat=250,
        networks={"20.5.0.0/16"},
        apps={"python-requests"},
        tools=Counter({"fork_repository": 900}),
    )
    rows = {r["id"]: r for r in card_rows(odd, history)}
    assert rows["hours"]["today"] == "2-4 am"
    assert rows["kinds"]["today"] == "copy a project (new to it)"
    assert rows["projects"]["today"] == (
        "2 projects. New to it: 1. Marked sensitive: 1 (new to it)."
    )
    assert rows["connection"]["today"] == (
        "the cloud (new to it); its own small program instead of an app (new to it)"
    )
    assert rows["upload"]["today"] == "about 100 pages"
    assert rows["repeats"]["today"] == "249"
    assert rows["changes"]["today"] == "0"


def test_plain_words() -> None:
    assert [clock(h) for h in (0, 9, 12, 17)] == ["midnight", "9 am", "noon", "5 pm"]
    assert hours_text(set(range(9, 17))) == "9 am-5 pm"
    assert hours_text({23, 0, 1}) == "11 pm-2 am"
    assert hours_text(set(range(24))) == "around the clock"
    assert size_today(3_200) == "about 1 page"
    assert size_today(1_000) == "less than a page"
    assert size_today(25_000) == "about 8 pages"
    assert size_usual([500, 800, 900]) == "less than a page"
    assert size_usual([5_000, 9_000, 13_000]) == "2-4 pages"
    assert size_usual([100, 200, 30_000]) == "up to 8 pages"
    assert plain_range([0, 0, 0]) == "0 (never)"
    assert plain_range([0, 1, 1, 0]) == "0-1"
    assert plain_range([60, 61, 62]) == "about 60"
    assert [round_plain(v) for v in (7, 37, 123, 1_449)] == [7, 35, 120, 1_400]


def test_hand_cards_have_every_row() -> None:
    for name, card in HAND_CARDS.items():
        assert [r["id"] for r in card["rows"]] == list(ROW_IDS), name
    assert {c.get("expected") for c in HAND_CARDS.values()} >= {"normal", "wild"}


# ── the committed bank ───────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def committed() -> tuple[dict, dict]:
    return json.loads(ITEMS.read_text()), json.loads(KEY.read_text())


def test_committed_items_hold_nothing_from_the_key(committed: tuple[dict, dict]) -> None:
    items, key = committed
    assert_public(items, key)
    assert_cards_well_formed(items)


def test_committed_key_matches_the_spec(committed: tuple[dict, dict]) -> None:
    items, key = committed
    assert key["bank_version"] == items["bank_version"]
    assert key["engine"]["design"] == "v4"
    assert {"git_sha", "profile", "agents", "seed"} <= set(key["engine"])
    assert set(key["row_map"].values()) <= set(ROW_IDS)
    assert_key_matches(items, key)


def test_committed_cards_txt_is_items_rendered(committed: tuple[dict, dict]) -> None:
    items, _ = committed
    text = CARDS_TXT.read_text()
    assert text == render_text(items)
    hidden = [r["label"] for r in items["rows"] if not r["shown"]]
    assert hidden and not any(label in text for label in hidden)
    assert not CARD_ID_IN_TEXT.search(text), "an id in cards.txt"


def test_committed_cards_spread_over_roles_weekdays_and_notes(
    committed: tuple[dict, dict],
) -> None:
    _, key = committed
    scored = [c for c in key["cards"].values() if not c["attention"]]
    bots = [c for c in scored if "bot" in c["role"]]
    assert len(bots) <= MAX_BOT_CARDS
    assert max(Counter(c["stratum"] for c in bots).values(), default=0) <= MAX_BOTS_PER_STRATUM
    assert len({c["weekday"] for c in scored}) >= MIN_WEEKDAYS
    assert len({c["role"] for c in scored}) >= MIN_ROLES
    gray = [c for c in scored if c["gray_kind"]]
    assert any(c["org_event"] for c in gray), "no gray card has a company note"
    assert any(c["weekday"] in WEEKEND_NAMES for c in scored if not c["gray_kind"])
    for stratum in STRATA:
        days = [c["weekday"] for c in scored if c["stratum"] == stratum]
        assert len(set(days)) > 1, f"stratum {stratum} falls on one weekday"


def test_committed_key_records_the_salt_and_the_list_mix(committed: tuple[dict, dict]) -> None:
    _, key = committed
    assert isinstance(key["id_salt"], str) and key["id_salt"]
    mix = key["context"]["list_composition"]
    assert set(mix) == {"gray", "change", "ordinary"}
    assert abs(sum(mix.values()) - 1) < 1e-3
