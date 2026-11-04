"""The v5 learner (spec 4.4 RF1, RF2, E5): pooled agent-day lines and required steps by window.

Every number here is synthetic: seeded agent-days and messages, not a simulator world.
"""

from __future__ import annotations

import hashlib
import json
import math
import random

import pytest

from mcp_security.behaviour import BehaviourConfig, Message, replace_config, v5_switches_off
from mcp_security.behaviour.engine import ACCEPTED, REJECTED
from mcp_security.behaviour.policy import (
    CONTINUED,
    KB,
    LINE_ALPHA,
    LOGICAL_CALL_TTL_S,
    MIN_LINE_DAYS,
    MIN_TOOL_DAYS_V5,
    AgentDay,
    agent_day_line,
    agent_days,
    config_from_json,
    config_to_json,
    conformal_order_stat,
    derive_policy,
    derive_policy_v5,
    learned_calls,
    learning_day,
    request_lines,
    required_steps,
    tool_reference,
)
from mcp_security.gateway import protocol_era

DAY = 86_400.0
HOUR = 3_600.0
D0 = 20_602  # 2026-05-28 (UTC day number): Chicago is on CDT, UTC-5
T0 = D0 * DAY + 10 * HOUR  # 10:00 UTC: a test day's calls stay on one v5 (04:00 UTC) day
V5 = BehaviourConfig(design="v5")


def _call(agent: str, ts: float, tool: str = "read", **fields: object) -> Message:
    return Message(ts, agent, fields.pop("method", "tools/call"), tool=tool, **fields)


# ── v1-v4 stay bit-identical ──────────────────────────────────────────────────────────────
LEGACY_SEED = 20261026
LEGACY_AGENTS = 12
LEGACY_DAYS = 40
LEGACY_TOOLS = ("read_file", "search", "comment", "write_file", "review", "merge")
LEGACY_MIN_SESSIONS = 20
#: SHA-256 of ``config_to_json(derive_policy(legacy_traffic(), design))`` in the CLI's format,
#: recorded with policy.py as Batch 0 left it, before the v5 learner was added.
LEGACY_DIGESTS = {
    "v1": "fc87ce184d5218fa100b5f367c7008efaa0c45c2a64fbba14ce6d1372c103c05",
    "v2": "cfa55a7045b7953c813b7339b7f9b0cf9f75a755e227a81be691d12ade4d25d8",
    "v3": "30945ae7f91efbcebf6c440606f248ab7d0f52a279c3e87651ba9a9ce6d17b68",
    "v4": "43698a4148adc389ac2332d389da056ab228b9024ae90914be8f687a01ddcd12",
}


def legacy_traffic() -> list[Message]:
    """Sessioned calls by a dozen agents over 40 days, with assets, sizes and a review step."""
    rng = random.Random(LEGACY_SEED)
    out = []
    for day in range(LEGACY_DAYS):
        for a in range(LEGACY_AGENTS):
            if rng.random() < 0.25:
                continue
            agent = f"agent{a}"
            ts = T0 + day * DAY + rng.uniform(0, 8 * HOUR)
            for s in range(rng.randint(1, 3)):
                session = f"{agent}-{day}-{s}"
                for _ in range(rng.randint(2, 12)):
                    tool = rng.choice(LEGACY_TOOLS)
                    if tool == "merge":
                        out.append(
                            Message(
                                ts,
                                agent,
                                "tools/call",
                                session,
                                tool="review",
                                asset=f"repo{rng.randint(0, 9)}",
                                size=300,
                            )
                        )
                        ts += rng.uniform(1, 30)
                    out.append(
                        Message(
                            ts,
                            agent,
                            "tools/call",
                            session,
                            tool=tool,
                            asset=f"repo{rng.randint(0, 9)}" if rng.random() < 0.8 else None,
                            size=int(rng.lognormvariate(7, 1.2)),
                        )
                    )
                    ts += rng.expovariate(1 / 20)
                ts += rng.uniform(600, HOUR)
    return sorted(out, key=lambda m: m.ts)


@pytest.mark.parametrize("design", sorted(LEGACY_DIGESTS))
def test_the_v1_to_v4_learner_writes_its_pre_v5_policy_byte_for_byte(design: str) -> None:
    policy = derive_policy(
        legacy_traffic(),
        base=BehaviourConfig(design=design),
        min_sessions=LEGACY_MIN_SESSIONS,
    )
    text = json.dumps(config_to_json(policy), indent=1)
    assert hashlib.sha256(text.encode()).hexdigest() == LEGACY_DIGESTS[design]


def test_derive_policy_hands_a_v5_base_to_the_v5_learner_and_refuses_v4_knobs() -> None:
    traffic = legacy_traffic()
    assert derive_policy(traffic, base=V5) == derive_policy_v5(traffic, V5)
    with pytest.raises(ValueError, match="v1-v4's"):
        derive_policy(traffic, base=V5, quantile=0.99)
    with pytest.raises(ValueError, match="learns design v5"):
        derive_policy_v5(traffic, BehaviourConfig(design="v4"))


# ── agent-days: baseline key and local day (B1, B9) ───────────────────────────────────────
CHICAGO_EVENING = D0 * DAY + 23 * HOUR  # 18:00 CDT on D0
CHICAGO_NIGHT = (D0 + 1) * DAY + 7.5 * HOUR  # 02:30 CDT the next date: still D0's local day


def test_an_agent_day_is_the_callers_local_day_rolling_over_at_four() -> None:
    calls = [
        _call("alice", CHICAGO_EVENING, zone="America/Chicago"),
        _call("alice", CHICAGO_NIGHT, zone="America/Chicago"),
        _call("bob", CHICAGO_NIGHT, zone="America/Chicago"),  # another baseline key
    ]
    assert [(d.caller, d.day) for d in agent_days(calls, V5)] == [("alice", D0), ("bob", D0)]
    utc = v5_switches_off()  # B9 off: v4's UTC days, so the same evening is two days
    assert [(d.caller, d.day) for d in agent_days(calls, utc)] == [
        ("alice", D0),
        ("alice", D0 + 1),
        ("bob", D0 + 1),
    ]


def test_a_caller_without_a_zone_takes_the_routes_and_off_is_v4s_utc_day() -> None:
    chicago = replace_config(V5, route_zone="America/Chicago")
    assert learning_day(CHICAGO_NIGHT, None, chicago) == D0
    assert learning_day(CHICAGO_NIGHT, None, V5) == D0 + 1  # 07:30 UTC on a UTC route
    for ts in (CHICAGO_EVENING, CHICAGO_NIGHT, T0):
        assert learning_day(ts, "Asia/Tokyo", v5_switches_off()) == int(ts // DAY)


def test_only_accepted_scored_calls_count_once_per_logical_call() -> None:
    messages = [
        _call("a", T0, logical_call="x/1"),
        _call("a", T0 + 1, logical_call="x/1"),  # an MRTR continuation of x/1
        _call("a", T0 + 2, logical_call="x/2", outcome=REJECTED),  # never committed
        _call("a", T0 + 3, logical_call="x/2", outcome=ACCEPTED),  # its retry is learned
        _call("a", T0 + 4, tool=None, method="tools/list"),  # not a scored method
        _call("a", T0 + 5, tool="doc", method="resources/read"),  # scored in v5 (AI-10)
        _call("a", T0 + 6, logical_call="x/3", outcome=CONTINUED),  # input_required, then
        _call("a", T0 + 7, logical_call="x/3", outcome=REJECTED),  # rejected: it never ran
        _call("a", T0 + 8, logical_call="x/4", outcome=CONTINUED),  # input_required, then
        _call("a", T0 + 9, logical_call="x/4", outcome=ACCEPTED),  # accepted: its first leg
        _call("a", T0 + 10, logical_call="x/5", outcome=CONTINUED),  # never continued
        _call("a", T0 + 11, outcome=CONTINUED),  # no key: only its continuation is the call
        _call("a", T0 + 12, outcome=ACCEPTED),
        _call("b", T0 + 13, logical_call="x/1"),  # another caller's key is another call
        _call("a", T0 + DAY, logical_call="x/1"),  # a day later: another call
    ]
    assert [m.ts - T0 for m in learned_calls(messages, V5)] == [0, 3, 5, 8, 12, 13, DAY]
    v4_methods = replace_config(V5, scored_methods=("tools/call",))
    assert len(learned_calls(messages, v4_methods)) == len(learned_calls(messages, V5)) - 1


def test_a_logical_call_across_the_rollover_is_learned_once() -> None:
    rollover = D0 * DAY + 4 * HOUR  # 04:00 UTC: a v5 day on a UTC route starts here
    first, second = (_call("a", rollover + gap, logical_call="k") for gap in (-1, 1))
    assert learning_day(first.ts, None, V5) != learning_day(second.ts, None, V5)
    assert learned_calls([first, second], V5) == [first]
    late = _call("a", first.ts + LOGICAL_CALL_TTL_S + 1, logical_call="k")
    assert learned_calls([first, late], V5) == [first, late]  # past the TTL: two calls
    newer = _call("a", first.ts + 50, logical_call="j")  # logged before ``first``, stamped later
    assert learned_calls([newer, first, late], V5) == [newer, first, late]


def test_the_fold_uses_the_gateways_outcome_values_and_continuation_lifetime() -> None:
    assert (ACCEPTED, REJECTED, CONTINUED) == protocol_era.OUTCOMES
    assert LOGICAL_CALL_TTL_S == protocol_era.REQUEST_STATE_TTL_S


def test_the_conformal_order_statistic_needs_199_values_at_half_a_percent() -> None:
    assert conformal_order_stat(range(MIN_LINE_DAYS - 1)) is None
    assert conformal_order_stat(range(MIN_LINE_DAYS)) == MIN_LINE_DAYS - 1  # the maximum
    assert conformal_order_stat(range(400)) == 398  # rank ceil(0.995 * 401) = 399
    assert conformal_order_stat(range(400), alpha=0.01) == 396  # rank ceil(0.99 * 401) = 397


def _calm(callers: int) -> list[tuple[str, float]]:
    """One agent-day each, all at the same value."""
    return [(f"c{i:03d}", 5) for i in range(callers)]


def test_a_line_needs_199_agent_days_left_after_the_leave_out() -> None:
    # the order statistic is in its own "at or above" tail, so someone always goes
    assert agent_day_line(_calm(MIN_LINE_DAYS), leave_top_out=False).value == 5
    assert agent_day_line(_calm(MIN_LINE_DAYS)) is None  # 198 are left
    line = agent_day_line(_calm(MIN_LINE_DAYS + 1))
    assert (line.value, line.days, line.left_out) == (5, MIN_LINE_DAYS, "c000")


def test_a_tie_in_the_tail_leaves_out_the_smallest_key() -> None:
    values = _calm(200) + [("b", 9), ("b", 9), ("a", 9), ("a", 9)]  # rank 204 of 204: 9
    line = agent_day_line(values)
    assert (line.left_out, line.value, line.days) == ("a", 9, 202)  # b's 9s remain


def test_calls_exactly_a_minute_apart_are_not_in_one_minute() -> None:
    def busiest(gap: float) -> int:
        (day,) = agent_days([_call("a", T0), _call("a", T0 + gap)], V5)
        return day.busiest_minute

    assert busiest(60.0) == 1  # the engine's Burst counts the calls in (ts - 60 s, ts]
    assert busiest(59.5) == 2


# ── RF1: the pooled agent-day line on argument bytes ──────────────────────────────────────
TOOLS = 6
TOOLS_PER_DAY = 4
SMALLEST_MEDIAN, LARGEST_MEDIAN = 300.0, 50_000.0
IDENTITIES, LEARN_DAYS = 60, 30
BAND_REPLICATIONS, BAND_TEST_DAYS = 100, 100
BAND_LEVEL = 0.99
INFLATION = 100
POISONER = "a7"
#: Leaving out one caller of 60 rather than another (and rounding to a KB) moves a line by up
#: to this share (synthetic: at most 9.5% here).
ONE_CALLER_SHIFT = 0.15


def _tool_sizes() -> dict[str, tuple[float, float]]:
    """tool key -> (median argument bytes, lognormal sigma): medians 300 B to 50 KB."""
    step = math.log(LARGEST_MEDIAN / SMALLEST_MEDIAN) / (TOOLS - 1)
    return {
        f"tool{i}": (SMALLEST_MEDIAN * math.exp(i * step), 0.6 + 0.08 * i) for i in range(TOOLS)
    }


SIZES = _tool_sizes()
CLASSES = {tool: ("write" if i % 2 else "read") for i, tool in enumerate(SIZES)}


def synthetic_days(
    rng: random.Random,
    identities: int,
    days: int,
    prefix: str = "a",
    inflated: str = "",
    factor: float = INFLATION,
) -> list[AgentDay]:
    """Agent-days using 1-4 tools each, every tool's largest request lognormal; the
    ``inflated`` identity's requests are ``factor`` times larger."""
    callers = (f"{prefix}{a}" for a in range(identities))
    return scaled_days(rng, {c: factor if c == inflated else 1 for c in callers}, days)


def scaled_days(rng: random.Random, scales: dict[str, float], days: int) -> list[AgentDay]:
    """``days`` agent-days per caller of ``scales``, each caller's sizes times his scale."""
    out = []
    for caller, scale in scales.items():
        for day in range(days):
            used = rng.sample(sorted(SIZES), rng.randint(1, TOOLS_PER_DAY))
            largest = {
                t: int(scale * rng.lognormvariate(math.log(SIZES[t][0]), SIZES[t][1])) for t in used
            }
            out.append(AgentDay(caller, day, 1, None, largest))
    return out


def _raised(limits: dict[str, int], fallback: int, day: AgentDay) -> bool:
    return any(size > limits.get(t, fallback) for t, size in day.largest_request.items())


def _binomial_band(n: int, p: float, level: float) -> tuple[int, int]:
    """The central ``level`` interval of Binomial(n, p): (lower, upper) counts."""
    tail = (1 - level) / 2
    pmf, cdf, lower = (1 - p) ** n, 0.0, None
    for k in range(n + 1):
        cdf += pmf
        if lower is None and cdf >= tail:
            lower = k
        if cdf >= 1 - tail:
            return lower, k
        pmf *= (n - k) / (k + 1) * p / (1 - p)
    return lower, n


def test_the_pooled_line_is_raised_on_half_a_percent_of_new_agent_days() -> None:
    # Many small replications (learn on 1,800 agent-days, test 100 fresh ones), so the
    # count of raised test days is close to binomial around the 0.5% budget.
    raised = per_tool_raised = tested = 0
    for replication in range(BAND_REPLICATIONS):
        rng = random.Random(5_000 + replication)
        learning = synthetic_days(rng, IDENTITIES, LEARN_DAYS)
        lines = request_lines(learning, CLASSES)
        per_tool = {  # v4's multiplicity: one 0.5% line per tool, so m tests a day
            t: math.ceil(conformal_order_stat(sizes) / 1_000) * 1_000
            for t in SIZES
            if (sizes := [d.largest_request[t] for d in learning if t in d.largest_request])
        }
        test = synthetic_days(rng, BAND_TEST_DAYS, 1, prefix="new")
        raised += sum(_raised(dict(lines.limits), lines.fallback, d) for d in test)
        per_tool_raised += sum(_raised(per_tool, 0, d) for d in test)
        tested += len(test)
    lower, upper = _binomial_band(tested, LINE_ALPHA, BAND_LEVEL)
    assert lower <= raised <= upper, (raised, tested, (lower, upper))
    assert per_tool_raised > upper  # lines per tool spend the budget once per tool used


# A small route of callers of unlike scale (lognormal sigma 0.5 around the same tools): the
# case the band test above cannot see, as its 60 callers share one distribution.
UNLIKE_CALLERS, UNLIKE_DAYS, UNLIKE_SIGMA = 10, 30, 0.5
BURST_REPLICATIONS, BURST_TEST_DAYS = 400, 5
RF1_REPLICATIONS, RF1_TEST_DAYS = 150, 10
#: Shares of the 0.5% budget the realised raise rates stay within, or above (synthetic: the
#: rates on these seeds are Burst 1.4% with the leave-out, RF1 0.7% with its reference
#: leave-outs and 1.6% read once; the shares leave a margin).
BURST_LEAVE_OUT_MAX_SHARE, RF1_MAX_SHARE, RF1_ONCE_MIN_SHARE = 4.0, 2.0, 2.5


def _unlike_scales(rng: random.Random) -> dict[str, float]:
    return {f"c{i}": rng.lognormvariate(0, UNLIKE_SIGMA) for i in range(UNLIKE_CALLERS)}


def _busiest_minute(rng: random.Random, scale: float) -> int:
    """A burst-like agent-day value: gamma calls in the busiest minute, times the scale."""
    return int(rng.gammavariate(4, 2.5 * scale)) + 1


def test_on_a_small_route_of_unlike_callers_the_leave_out_costs_burst_its_budget() -> None:
    # 300 agent-days: the line is their maximum, so the caller holding it always goes (the
    # tail is "at or above") and the line drops to another caller's maximum. This is the cost
    # of the tie-safe leave-out, an open author decision: read once, the line keeps 0.5%.
    once = left_out = tested = 0
    for replication in range(BURST_REPLICATIONS):
        rng = random.Random(9_000 + replication)
        scales = _unlike_scales(rng)
        learning = [
            (c, _busiest_minute(rng, s)) for c, s in scales.items() for _ in range(UNLIKE_DAYS)
        ]
        line, plain = agent_day_line(learning), agent_day_line(learning, leave_top_out=False)
        test = [_busiest_minute(rng, s) for s in scales.values() for _ in range(BURST_TEST_DAYS)]
        left_out += sum(value > line.value for value in test)
        once += sum(value > plain.value for value in test)
        tested += len(test)
    _, upper = _binomial_band(tested, LINE_ALPHA, BAND_LEVEL)
    assert once <= upper, (once, tested)
    assert upper < left_out <= BURST_LEAVE_OUT_MAX_SHARE * LINE_ALPHA * tested, (left_out, tested)


def test_on_a_small_route_of_unlike_callers_reference_leave_outs_keep_rf1_near_budget() -> None:
    # Read once, each tool's reference is its sample maximum (100-198 agent-days a tool), so
    # k is 1 and each line that maximum: a day using m tools faces m tests again. With each
    # reference's top caller left out, his days are the ones k is read from.
    once = left_out = tested = 0
    for replication in range(RF1_REPLICATIONS):
        rng = random.Random(7_000 + replication)
        scales = _unlike_scales(rng)
        learning = scaled_days(rng, scales, UNLIKE_DAYS)
        lines = request_lines(learning, CLASSES)
        plain = request_lines(learning, CLASSES, leave_top_out=False)
        test = scaled_days(rng, scales, RF1_TEST_DAYS)
        if lines is None:  # every key fell under 100 agent-days once its top caller was out
            continue
        left_out += sum(_raised(dict(lines.limits), lines.fallback, d) for d in test)
        once += sum(_raised(dict(plain.limits), plain.fallback, d) for d in test)
        tested += len(test)
    assert left_out <= RF1_MAX_SHARE * LINE_ALPHA * tested, (left_out, tested)
    assert once >= RF1_ONCE_MIN_SHARE * LINE_ALPHA * tested, (once, tested)


def test_one_inflated_identity_does_not_move_the_line() -> None:
    def world(factor: float) -> list[AgentDay]:
        return synthetic_days(random.Random(1), IDENTITIES, LEARN_DAYS, "a", POISONER, factor)

    lines = request_lines(world(INFLATION), CLASSES)
    assert lines.left_out == POISONER
    assert request_lines(world(INFLATION**2), CLASSES) == lines  # he has no say in any line
    clean = request_lines(world(1), CLASSES)  # leaves out its own top caller, not him
    assert all(abs(lines.limits[t] / clean.limits[t] - 1) <= ONE_CALLER_SHIFT for t in SIZES)
    kept = request_lines(world(INFLATION), CLASSES, leave_top_out=False)  # what he would get
    assert max(kept.limits[t] / clean.limits[t] for t in SIZES) > INFLATION / 10


def _small_read_world(bot_days: int, bot_size: int) -> list[AgentDay]:
    """40 callers x 10 days of a small read and a big write (400 agent-days each), plus a
    bot with ``bot_days`` days of the small read at one flat size."""
    rng = random.Random(0)
    days = [
        AgentDay(
            f"a{a}",
            d,
            1,
            None,
            {
                "read_small": int(rng.lognormvariate(math.log(500), 0.5)),
                "write_big": int(rng.lognormvariate(math.log(40_000), 0.5)),
            },
        )
        for a in range(40)
        for d in range(10)
    ]
    return days + [AgentDay("bot", d, 1, None, {"read_small": bot_size}) for d in range(bot_days)]


@pytest.mark.parametrize("bot_days", [5, 8, 12])  # 1.2%, 2% and 2.9% of read_small's days
def test_a_flat_identity_holding_a_tools_reference_tail_does_not_move_its_line(
    bot_days: int,
) -> None:
    # read once, the bot's tied days are r_t itself: his ratio is exactly 1, below k, so k's
    # leave-out alone never sees him; the reference's own leave-out does
    classes = {"read_small": "read", "write_big": "write"}
    clean = request_lines(_small_read_world(0, 0), classes).limits["read_small"]
    for size in (50_000, 500_000):
        lines = request_lines(_small_read_world(bot_days, size), classes)
        assert lines.left_out == "bot"
        assert abs(lines.limits["read_small"] - clean) <= KB
        once = request_lines(_small_read_world(bot_days, size), classes, leave_top_out=False)
        assert once.limits["read_small"] >= size


def test_a_tool_key_only_the_left_out_identity_used_keeps_its_class_line() -> None:
    rng = random.Random(2)
    days = []
    for a in range(40):
        for d in range(10):
            factor = INFLATION if a == 0 else 1
            used = {
                "get_file": factor * int(rng.lognormvariate(math.log(400), 0.4)),
                "push": int(rng.lognormvariate(math.log(30_000), 0.4)),
            }
            if a == 0:
                used["list_tags"] = 60  # only he lists tags
            days.append(AgentDay(f"a{a}", d, 1, None, used))
    lines = request_lines(days, {"get_file": "read", "push": "write", "list_tags": "read"})
    assert lines.left_out == "a0"
    assert "list_tags" in lines.borrowed
    assert lines.references["list_tags"] == lines.references["get_file"]  # the read median
    assert lines.limits["list_tags"] == lines.limits["get_file"] < lines.fallback


def test_a_reference_is_the_99th_percentile_order_statistic_read_again_without_its_tail() -> None:
    sizes = [(f"c{i:03d}", 1_000.0 * i) for i in range(1, 251)]  # one agent-day per caller
    assert tool_reference(sizes, leave_top_out=False).value == 249_000  # rank 249 of 250
    again = tool_reference(sizes)
    assert again.left_out == "c249"  # 249 and 250 KB, a day each, tie: the smallest key
    assert (again.value, again.days) == (248_000, 249)  # rank ceil(0.99 * 250) = 248
    assert tool_reference(sizes[:MIN_TOOL_DAYS_V5]) is None  # 99 left: the class median
    assert tool_reference(sizes[: MIN_TOOL_DAYS_V5 + 1]).value == 100_000


def test_a_tie_at_k_leaves_the_tied_identity_out() -> None:
    flat, tied = 10_000, 15_000
    days = [AgentDay(f"c{i:02d}", d, 1, None, {"t": flat}) for i in range(99) for d in range(3)]
    days += [AgentDay("z", d, 1, None, {"t": tied}) for d in range(3)]
    lines = request_lines(days)
    assert lines.left_out == "z"  # his ratio 1.5 is k itself, with nothing above it
    assert lines.limits["t"] == flat


def _sized_messages(callers: int, days: int, tools: dict[str, tuple[int, int]]) -> list[Message]:
    """Each caller, each day, one call of every tool in ``tools`` ({tool: (smallest, largest)
    argument bytes}); the operation is write for a name starting with "write", else read."""
    rng = random.Random(7)
    out = []
    for c in range(callers):
        for day in range(days):
            for i, (tool, (low, high)) in enumerate(tools.items()):
                out.append(
                    _call(
                        f"c{c}",
                        T0 + day * DAY + c * 60 + i,
                        tool,
                        arg_bytes=rng.randint(low, high),
                        size=5_000_000,  # the whole message: never what the line is on
                        operation="write" if tool.startswith("write") else "read",
                    )
                )
    return out


def test_a_tool_with_few_agent_days_borrows_its_class_median_not_its_own_maximum() -> None:
    tools = {
        "read_a": (800, 1_000),
        "read_b": (2_800, 3_000),
        "read_c": (4_800, 5_000),
        "write_w": (40_000, 50_000),
    }
    rare_days, rare_max = 30, 20_000  # v4 would set its line at its own sample maximum
    rare = [
        _call(f"c{d}", T0 + (d % 10) * DAY + 3_600, "read_rare", arg_bytes=600, operation="read")
        for d in range(rare_days - 1)
    ]
    rare.append(_call("c0", T0 + 9 * DAY + 3_600, "read_rare", arg_bytes=rare_max))
    calls = sorted(_sized_messages(50, 10, tools) + rare, key=lambda m: m.ts)
    classes = {"read_a": "read", "read_b": "read", "read_c": "read", "read_rare": "read"}
    lines = request_lines(agent_days(calls, V5), classes | {"write_w": "write"})
    assert lines.borrowed == {"read_rare"}
    assert lines.references["read_rare"] == lines.references["read_b"]  # the read median
    assert lines.limits["read_rare"] == lines.limits["read_b"] < rare_max
    policy = derive_policy_v5(calls, V5)  # classes from the calls' operation labels
    assert policy.request_limit_by_tool == dict(lines.limits)
    own = [lines.limits[t] for t in tools]
    assert policy.request_limit_bytes == lines.fallback == max(own)  # an unseen tool: k x top


def test_the_line_is_on_argument_bytes_and_a_route_without_them_keeps_its_default() -> None:
    messages = _sized_messages(25, 10, {"read_a": (400, 500), "read_b": (1_500, 1_800)})
    policy = derive_policy_v5(messages, V5)  # each message is 5 MB; its arguments are not
    assert policy.request_limit_by_tool == {"read_a": 1_000, "read_b": 2_000}
    unsized = [_call(m.agent, m.ts, m.tool, size=m.size) for m in messages]  # no arg_bytes
    written = replace_config(V5, request_limit_bytes=12_000, request_limit_by_tool={"x": 5})
    unlearned = derive_policy_v5(unsized, written)
    assert (unlearned.request_limit_bytes, unlearned.request_limit_by_tool) == (12_000, {"x": 5})


def test_with_the_pooled_line_off_v5_learns_v4s_request_lines_on_whole_messages() -> None:
    traffic = legacy_traffic()
    v4 = derive_policy(traffic, base=BehaviourConfig(design="v4"))
    off = derive_policy_v5(traffic, v5_switches_off())  # RF1 off, and UTC days as v4's
    assert off.request_limit_bytes == v4.request_limit_bytes
    assert off.request_limit_by_tool == v4.request_limit_by_tool
    assert set(v4.request_limit_by_tool) == set(LEGACY_TOOLS)  # every tool has its own line
    messages = _sized_messages(25, 10, {"read_a": (400, 500), "read_b": (1_500, 1_800)})
    whole = derive_policy_v5(messages, replace_config(V5, request_limit_pooled=False))
    assert whole.request_limit_by_tool == {"read_a": 5_000_000, "read_b": 5_000_000}
    assert whole.request_limit_bytes == 5_000_000  # each message is 5 MB: the engine's v4 check
    written = replace_config(V5, request_limit_pooled=False, request_limit_bytes=12_000)
    assert derive_policy_v5([], written).request_limit_bytes == 12_000


def test_below_199_agent_days_every_written_default_stays() -> None:
    written = replace_config(
        V5, burst_per_minute=33, many_assets_per_hour=9, request_limit_bytes=12_000
    )
    few = _sized_messages(18, 11, {"read_a": (400, 500)})  # 198 agent-days
    few = [_call(m.agent, m.ts, m.tool, arg_bytes=m.arg_bytes, asset="repo") for m in few]
    assert len(agent_days(few, V5)) == MIN_LINE_DAYS - 1
    assert derive_policy_v5(few, written) == written


# ── RF2: Burst and Sweep by the same agent-day procedure ──────────────────────────────────
BURST_IDENTITIES, BURST_DAYS, POISONED_DAYS, POISONED_RATE = 150, 20, 20, 200


def test_twenty_inflated_burst_days_of_one_identity_leave_the_line_alone() -> None:
    rng = random.Random(3)
    clean = [
        (f"c{a}", int(rng.gammavariate(4, 2.5)) + 1)
        for a in range(BURST_IDENTITIES)
        for _ in range(BURST_DAYS)
    ]
    poisoned = clean + [("evil", POISONED_RATE)] * POISONED_DAYS
    line, clean_line = agent_day_line(poisoned), agent_day_line(clean)
    assert line.left_out == "evil"
    assert abs(line.value - clean_line.value) <= 1
    # his days tie at the line, so only an "at or above" tail can leave him out
    assert agent_day_line(poisoned, leave_top_out=False).value == POISONED_RATE


def _minute_of(agent: str, day: int, calls: int, **fields: object) -> list[Message]:
    return [_call(agent, T0 + day * DAY + i * 0.5, **fields) for i in range(calls)]


def test_burst_is_the_agent_days_busiest_minute_at_the_order_statistic() -> None:
    traffic = [m for a in range(10) for d in range(45) for m in _minute_of(f"a{a}", d, 6)]
    traffic += _minute_of("a0", 60, 60)  # one wild minute
    policy = derive_policy_v5(sorted(traffic, key=lambda m: m.ts), V5)
    assert policy.burst_per_minute == 6
    hundred_days = traffic[:600]  # a0 and a1's 45 days each, a2's first 10
    assert derive_policy_v5(hundred_days, V5).burst_per_minute == V5.burst_per_minute


def test_sweep_counts_touched_assets_and_every_container_a_call_names() -> None:
    def day_of(agent: str, day: int) -> list[Message]:
        return [
            _call(
                agent,
                T0 + day * DAY + i * 60.0,
                asset=f"repo{i % 4}",
                more_assets=(f"fork{i % 4}",),
            )
            for i in range(30)
        ]

    traffic = [m for a in range(10) for d in range(25) for m in day_of(f"a{a}", d)]
    traffic += [_call("a0", T0 + 30 * DAY + i) for i in range(3)]  # no asset: not a sweep day
    assert derive_policy_v5(traffic, V5).many_assets_per_hour == 8  # AI-12: 4 repos + 4 forks
    primary = replace_config(V5, multi_asset_breadth=False)
    assert derive_policy_v5(traffic, primary).many_assets_per_hour == 4
    assert derive_policy_v5([_call("a", T0)], V5).many_assets_per_hour is None


# ── E5: required steps by window, no sessions ─────────────────────────────────────────────
MERGES = 60


def _review_then_merge(
    gap: float, review_repo: str | None = "r", merge_repo: str | None = "r"
) -> list[Message]:
    out = []
    for i in range(MERGES):
        start = T0 + i * 2 * DAY
        out.append(
            _call(
                f"dev{i % 5}",
                start,
                "review",
                asset=None if review_repo is None else f"{review_repo}{i}",
            )
        )
        out.append(
            _call(
                f"dev{i % 5}",
                start + gap,
                "merge",
                asset=None if merge_repo is None else f"{merge_repo}{i}",
            )
        )
    return out


def test_merge_requires_review_is_learned_from_sessionless_traffic() -> None:
    traffic = _review_then_merge(3 * HOUR)
    assert required_steps(traffic, V5) == {"merge": frozenset({"review"})}
    assert derive_policy_v5(traffic, V5).requires_before == {"merge": frozenset({"review"})}
    v4 = derive_policy(traffic, base=BehaviourConfig(design="v4"))
    assert v4.requires_before == {}  # the session learner needs sessions


def test_the_window_and_the_asset_tie_are_the_engines() -> None:
    assert required_steps(_review_then_merge(25 * HOUR), V5) == {}  # past 24 h
    assert required_steps(_review_then_merge(DAY), V5) == {"merge": frozenset({"review"})}
    assert required_steps(_review_then_merge(DAY + 1), V5) == {}  # the engine's [ts - 24 h, ts]
    other_repo = _review_then_merge(HOUR, review_repo="x")  # a review of another repository
    assert required_steps(other_repo, V5) == {}
    tool_only = replace_config(V5, requires_same_asset=False)
    assert required_steps(other_repo, tool_only) == {"merge": frozenset({"review"})}
    for unresolved in (
        _review_then_merge(HOUR, review_repo=None),
        _review_then_merge(HOUR, merge_repo=None),
    ):
        assert required_steps(unresolved, V5) == {"merge": frozenset({"review"})}


def test_a_lower_share_tolerates_exactly_its_share_of_skipped_steps() -> None:
    # 60 merges after a review; the first ``skipped`` merges come before any review, so a
    # pair dropped too early (the learner stops checking dead pairs) would be lost
    def traffic(skipped: int) -> list[Message]:
        lone = [_call("dev0", T0 - (i + 1) * DAY, "merge", asset=f"r{i}") for i in range(skipped)]
        return sorted(lone, key=lambda m: m.ts) + _review_then_merge(HOUR)

    share = 0.9  # 6 of 66 merges skipped is 90.9%; 7 of 67 is 89.6%
    assert required_steps(traffic(6), V5, share) == {"merge": frozenset({"review"})}
    assert required_steps(traffic(7), V5, share) == {}


def test_too_few_calls_or_one_skipped_step_learns_nothing_and_written_steps_stay() -> None:
    traffic = _review_then_merge(HOUR)
    assert required_steps(traffic[: 2 * 40], V5) == {}  # 40 merges < 50
    skipped = traffic + [_call("dev0", T0 + 200 * DAY, "merge", asset="lone")]
    assert required_steps(skipped, V5) == {}  # 60 of 61 merges < 99.5%
    written = replace_config(V5, requires_before={"deploy": frozenset({"plan"})})
    assert derive_policy_v5(traffic, written).requires_before == {
        "deploy": frozenset({"plan"}),
        "merge": frozenset({"review"}),
    }


def test_with_the_window_off_v5_learns_steps_by_session() -> None:
    traffic = [
        _call("a", T0 + s * 600 + i, tool, session=f"s{s}")
        for s in range(100)
        for i, tool in enumerate(("review", "merge"))
    ]
    sessions = replace_config(V5, requires_window_s=None)
    assert required_steps(traffic, sessions, min_calls=20) == {"merge": frozenset({"review"})}
    unsessioned = [_call(m.agent, m.ts, m.tool) for m in traffic]
    assert required_steps(unsessioned, sessions, min_calls=20) == {}


def test_a_learned_v5_policy_survives_json() -> None:
    traffic = [m for a in range(10) for d in range(45) for m in _minute_of(f"a{a}", d, 6)]
    traffic += _review_then_merge(HOUR)
    policy = derive_policy_v5(sorted(traffic, key=lambda m: m.ts), V5)
    assert policy.burst_per_minute == 6 and policy.requires_before
    assert config_from_json(json.loads(json.dumps(config_to_json(policy)))) == policy
