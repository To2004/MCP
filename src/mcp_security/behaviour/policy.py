"""The behaviour layer's policy, learned from traffic for now: limits and required steps.

Until an organisation writes these down, they are read from its own ordinary traffic (no
labels needed), at the level of an *agent-day*: a busy agent makes hundreds of calls a day,
so a limit set on calls would still fire for him every day. Each limit is set so the rule
fires on at most ``1 - quantile`` of ordinary agent-days:

- ``burst_per_minute``: the agent-days' busiest minute (most tool calls in 60 s), at the
  quantile, rounded up;
- ``request_limit_bytes``: the agent-days' largest tool-call request, at the quantile,
  rounded up to the next KB;
- ``request_limit_by_tool`` (designs v3, v4): the same per tool, for each tool used on at least
  ``min_tool_days`` agent-days: one limit for all tools is set by the tool with the biggest
  requests (file writes) and misses a big paste into an issue;
- ``many_assets_per_hour`` (v3, v4): the agent-days' busiest hour, in distinct assets. It needs
  the assets calls resolve to, which a v1-v4 gateway log does not carry: learned from such a
  log alone, it stays off (a v5 log carries them on its decision lines, below);
- ``requires_before``: tool B requires tool A when, in at least ``sequence_share`` of the
  sessions where B was called, A was called earlier in the same session (and B was called in
  at least ``min_sessions`` sessions). B's required tools are "any one of". Learned steps are
  added to the ones the policy already has (``base``), never replacing them.

These are the limits of the rules in the Red Flags group (the paper's burst, sweep, oversized
request and unsafe sequence). The rule values themselves (0.9 -> x3.6, protocol skip 0.7 ->
x1.9) stay as designed.

**Design v5** (:func:`derive_policy_v5`; spec 4.4 RF1, RF2, E5, AI-6). The agent-day is the
caller's baseline key (B1: per agent, spec 8 D5) and his local day (B9, ``clock.py``); only
calls of the scored methods the server accepted count, once per logical call (ARG-1, AI-10).

Every line is a split-conformal order statistic: read once from exchangeable agent-days, a
new ordinary one crosses it with probability at most ``LINE_ALPHA`` (0.5%); for RF1 that also
needs the references fit on other days than k. Each line, and each RF1 reference, is then
read again once without the identity holding the most agent-days at or above it, so no single
caller sets one by filling its tail. Keeping that leave-out is an open author decision, as it
costs something: the order statistic is in its own tail, so someone is always left out.

- A line needs ``MIN_LINE_DAYS`` (199) agent-days *left after* the leave-out: in effect 199
  plus the left-out identity's days. Below that the written default stays.
- The line sits lower than the plain order statistic. Where callers differ in scale, ordinary
  days cross it more often than 0.5% (synthetic, Burst at 10 callers x 30 days: about 1.5%,
  against 0.2% read once; at 20-150 callers 0.65-0.8% against 0.5%). The 0.5% guarantee
  holds only without the leave-out.
- For RF1 the reference leave-out pays for itself on small routes. Read once, a tool's
  reference is near its own sample maximum, so k stays near 1 and a day using m tools faces
  m tests again (synthetic, 10 callers x 30 days: 0.7% with it, 1.6-1.8% read once).

The lines:

- Oversized request (RF1): one pooled agent-day line on *argument* bytes. Each tool key gets a
  reference r_t, the ``REFERENCE_QUANTILE`` (99%) order statistic of its agent-days' largest
  request, with the same leave-out, once it has ``MIN_TOOL_DAYS_V5`` (100) agent-days left;
  fewer borrow the median reference of their operation class. One multiple k is the order
  statistic of each agent-day's worst ratio ``max_t size / r_t``, and the tool's line is
  ``k r_t`` rounded up to a KB. With ``request_limit_pooled`` off (RF1's off value) v4's
  per-tool lines on whole-message bytes are learned instead, over the same agent-days;
- Burst and Sweep (RF2): the order statistic of the agent-days' busiest minute (scored calls)
  and busiest hour (distinct touched assets, AI-12 included). A v5 gateway log carries the
  touched assets on its decision lines, which :func:`messages_from_log` joins to the requests
  (AI-6), so Sweep is learnable from a log;
- required steps (E5): B requires A when at least ``sequence_share`` of B's calls had an A call
  by the same caller in the ``requires_window_s`` (24 h) before it, on the same touched asset
  when ``requires_same_asset`` (or either unresolved), the check the v5 engine makes. No
  protocol session is read, so a modern-era route learns them too.

RF4's re-learn to a versioned file is deferred (``RELEARN_DAYS``, ``MAX_GROWTH``).

    uv run python -m mcp_security.behaviour.policy --log runs/gateway/github.jsonl \\
        --out runs/gateway/github.behaviour.json --days 30 [--design v1|v2|v3|v4|v5]
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, OrderedDict, defaultdict, deque
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path

from mcp_security.behaviour import clock
from mcp_security.behaviour.engine import (
    ACCEPTED,
    CALL_METHOD,
    DAY_S,
    DERIVED_FIELDS,
    DESIGN_VALUES,
    DESIGNS,
    HOUR_S,
    LEGACY_DESIGNS,
    MINUTE_S,
    REJECTED,
    V4,
    V5,
    BehaviourConfig,
    Message,
)
from mcp_security.behaviour.memory import SlidingCounts

QUANTILE = 0.995  # a learned rule fires on at most 0.5% of ordinary agent-days
SEQUENCE_SHARE = 0.995
MIN_SESSIONS = 50
MIN_TOOL_DAYS = 50  # agent-days with a tool before it gets its own request limit
KB = 1_000
TO_SERVER = "agent->server"
#: v5 (RF1, RF2; spec 4.4): the pooled agent-day lines that ``derive_policy`` for v5 sets
#: (Batch 1). Read once, a line fires on at most LINE_ALPHA of exchangeable agent-days (RF1's
#: references are read at REFERENCE_QUANTILE); it is learned only with MIN_LINE_DAYS
#: agent-days left once the top identity is out (the module docstring has the leave-out's cost).
LINE_ALPHA = 0.005
REFERENCE_QUANTILE = 0.99
MIN_LINE_DAYS = 199
#: RF4 (deferred until after submission): the offline re-learn's period and the most a
#: re-learned limit may grow at once. Not config fields until RF4 is built.
RELEARN_DAYS = 30
MAX_GROWTH = 1.25
#: RF1: agent-days with a tool key, left after its reference's leave-out, before it gets its
#: own reference; fewer borrow the median reference of the tool's operation class
#: (``red_flag_arms.py``: ``min_ref=100``).
MIN_TOOL_DAYS_V5 = 100
#: E5: calls of tool B before "B requires A" can be learned (v4 counts sessions instead).
MIN_SEQUENCE_CALLS = MIN_SESSIONS
UNKNOWN_CLASS = "(unknown)"  # RF1: the operation class of a tool no call labelled
MIN_REFERENCE_BYTES = 1.0  # RF1: a reference is at least a byte, so a ratio is always defined
ORDER_TOLERANCE = 1e-9  # an order statistic's rank is ceil(q (n + 1)) up to float error
#: AI-6: the v5 log lines the learner joins. A request line and its decision line share
#: (``gateway.exchange_id``, ``jsonrpc.request.id``); the decision is written after the
#: request, later still under background scoring, so lines are joined on that key, never on
#: adjacency. The names equal ``gateway/wire_log.py``'s (a test checks they agree).
FROM_GATEWAY = "gateway"
EXCHANGE_ID_FIELD = "gateway.exchange_id"
REQUEST_ID_FIELD = "jsonrpc.request.id"
DECISION_FIELD = "gateway.decision"
BASELINE_KEY_FIELD = "gateway.baseline_key"  # B1
ZONE_FIELD = "gateway.zone"  # B9d
LOGICAL_CALL_FIELD = "gateway.logical_call"  # ARG-1
ARG_BYTES_FIELD = "gateway.arg_bytes"  # ARG-1: bytes of params.arguments (request, decision)
#: ARG-1: the server's answer, on the reply line; a bodiless reply (no request id) gives the
#: outcome of every call in its exchange.
OUTCOME_FIELD = "gateway.outcome"
#: The engine inputs the v5 gateway's decision (``RouteScorer.score``, INF-2) carries for
#: the learner: what the engine itself saw. A decision without them (v1-v4, or a scoring
#: error) gives a message without them, as a v4 log does.
DECISION_TOOL = "behaviour_tool"  # AI-7: the tool key
DECISION_ASSET = "behaviour_asset"  # AI-2: the touched asset (or its pseudonym)
DECISION_MORE_ASSETS = "behaviour_more_assets"  # AI-12
DECISION_SENSITIVITY = "behaviour_sensitivity"
DECISION_OPERATION = "behaviour_operation"  # AI-7: "read" or "write"
GATEWAY_CALLER = "gateway"  # the caller of a line that names none (as v1-v4)
#: AI-6: after the learning window ends, lines are still read this long for the decisions
#: and outcomes of the window's last requests (background scoring writes them later).
JOIN_GRACE_S = HOUR_S
#: ARG-1: what the gateway logs as the outcome of an MRTR ``input_required`` answer. It is
#: not a real outcome: the logical call goes on in a continuation (``gateway/protocol_era.py``'s
#: ``CONTINUED``; a test checks they agree).
CONTINUED = "continued"
#: ARG-1: a logical call none of whose answers accepted it, and whose last answer is one of
#: these, never ran (rejected, or a continuation that was rejected or never came): it is
#: never learned.
NOT_ACCEPTED = frozenset({REJECTED, CONTINUED})
#: ARG-1: messages with one logical-call key more than this apart are separate calls. It is
#: the longest a continuation may follow its call: an MRTR request state's lifetime
#: (``protocol_era.REQUEST_STATE_TTL_S``; a test checks they agree).
LOGICAL_CALL_TTL_S = HOUR_S


def derive_policy(
    messages: Iterable[Message],
    base: BehaviourConfig | None = None,
    quantile: float = QUANTILE,
    sequence_share: float = SEQUENCE_SHARE,
    min_sessions: int = MIN_SESSIONS,
    min_tool_days: int = MIN_TOOL_DAYS,
) -> BehaviourConfig:
    """``base`` with its limits and required steps read from ``messages`` (arrival order).

    A v5 ``base`` is learned by :func:`derive_policy_v5` (``sequence_share`` and
    ``min_sessions``, as its ``min_calls``, pass through); ``quantile`` and ``min_tool_days``
    are the v1-v4 procedure's, and setting them for v5 is an error."""
    base = base or BehaviourConfig()
    if base.design == V5:
        if quantile != QUANTILE or min_tool_days != MIN_TOOL_DAYS:
            raise ValueError("quantile and min_tool_days are v1-v4's: use derive_policy_v5")
        return derive_policy_v5(
            messages, base, sequence_share=sequence_share, min_calls=min_sessions
        )
    burst: dict[tuple[str, int], int] = defaultdict(int)  # agent-day -> busiest minute
    biggest: dict[tuple[str, int], int] = defaultdict(int)  # agent-day -> largest request
    biggest_by_tool: dict[str, dict[tuple[str, int], int]] = defaultdict(dict)
    widest: dict[tuple[str, int], int] = defaultdict(int)  # agent-day -> most assets in an hour
    hour_assets: dict[str, SlidingCounts] = {}
    recent: dict[str, deque] = defaultdict(deque)
    earlier: dict[tuple[str, str], set] = defaultdict(set)  # session -> tools so far
    sessions_with: Counter = Counter()  # tool -> sessions it was called in
    preceded: Counter = Counter()  # (tool, earlier tool) -> sessions
    for m in messages:
        if m.method != CALL_METHOD or not m.tool:
            continue
        day = (m.agent, int(m.ts // DAY_S))
        q = recent[m.agent]
        q.append(m.ts)
        while q and q[0] <= m.ts - MINUTE_S:
            q.popleft()
        burst[day] = max(burst[day], len(q))
        biggest[day] = max(biggest[day], m.size)
        by_tool = biggest_by_tool[m.tool]
        by_tool[day] = max(by_tool.get(day, 0), m.size)
        if m.asset:
            window = hour_assets.setdefault(m.agent, SlidingCounts(HOUR_S))
            window.add(m.ts, m.asset)
            window.expire(m.ts)
            widest[day] = max(widest[day], window.distinct())
        if m.session:
            seen = earlier[(m.agent, m.session)]
            if m.tool not in seen:  # B's first call in this session
                sessions_with[m.tool] += 1
                for before in seen:
                    preceded[(m.tool, before)] += 1
            seen.add(m.tool)
    if not burst:
        return base
    requires: dict[str, set[str]] = defaultdict(set)
    for tool, before in base.requires_before.items():  # written steps stay
        requires[tool].update(before)
    for (tool, before), n in preceded.items():
        total = sessions_with[tool]
        if total >= min_sessions and n >= sequence_share * total:
            requires[tool].add(before)
    by_tool = {
        tool: _whole_kb(_quantile(list(days.values()), quantile))
        for tool, days in biggest_by_tool.items()
        if len(days) >= min_tool_days
    }
    return replace(
        base,
        burst_per_minute=_quantile(list(burst.values()), quantile),
        request_limit_bytes=_whole_kb(_quantile(list(biggest.values()), quantile)),
        request_limit_by_tool={**base.request_limit_by_tool, **by_tool},
        many_assets_per_hour=(
            _quantile(list(widest.values()), quantile) if widest else base.many_assets_per_hour
        ),
        requires_before={tool: frozenset(before) for tool, before in requires.items()},
    )


def _whole_kb(size: int) -> int:
    return math.ceil(size / KB) * KB


def _quantile(values: list[int], q: float) -> int:
    values = sorted(values)
    return int(values[min(len(values) - 1, math.ceil(q * len(values)) - 1)])


def config_to_json(config: BehaviourConfig) -> dict:
    """A config as JSON-safe data (``requires_before`` sets become sorted lists), holding
    only the fields its design uses (INF-4).

    A v1-v4 config leaves out every field v5 added while it holds its v1-v4 value, so a v4
    policy file is byte for byte what it was before v5 and its digest does not move. One set
    away from that value (``legacy_fixes`` on v4, say) is kept, so it survives a round trip.
    A v5 config keeps every field except the derived ones (``alert_line``,
    ``alert_floor_rate``) while they equal their derivation from ``alert_alpha``: the file
    then stores only alpha, and editing it moves the line with it.
    """
    data = asdict(config)
    data["requires_before"] = {t: sorted(b) for t, b in config.requires_before.items()}
    if config.design != V5:
        for name, (legacy, _) in DESIGN_VALUES.items():
            if getattr(config, name) == legacy:
                del data[name]
    else:
        for name in DERIVED_FIELDS:
            if getattr(config, name) == config.derived_value(name):
                del data[name]
    return data


def config_from_json(data: dict) -> BehaviourConfig:
    """``config_to_json`` output back; unknown keys are an error, missing ones the default
    for the file's design. A v5-only switch set on a v1-v4 design is an error too."""
    known = {f.name for f in fields(BehaviourConfig)}
    unknown = set(data) - known
    if unknown:
        raise ValueError(f"unknown behaviour policy keys: {sorted(unknown)}")
    data = dict(data)
    if "requires_before" in data:
        data["requires_before"] = {t: frozenset(b) for t, b in data["requires_before"].items()}
    return BehaviourConfig(**data)  # lists of v5 tuple fields become tuples there


def load_policy(path: str | Path) -> BehaviourConfig:
    return config_from_json(json.loads(Path(path).read_text(encoding="utf-8")))


def messages_from_log(
    records: Iterable[dict], days: float | None = None, *, design: str = V4
) -> list[Message]:
    """The agent-to-server requests of a gateway log (gateway-log/2 or /3), as messages;
    ``days``: only the first ``days`` days of the log.

    ``design`` v5 (AI-6) also joins each request with its decision line and with the line
    carrying its outcome, on (``gateway.exchange_id``, ``jsonrpc.request.id``), and reads the
    engine's own inputs from them (see :func:`_messages_from_log_v5`). v1-v4 read the request
    lines alone, exactly as before v5."""
    if design == V5:
        return _messages_from_log_v5(records, days)
    if design not in LEGACY_DESIGNS:
        raise ValueError(f"design must be one of {DESIGNS}, not {design!r}")
    out: list[Message] = []
    start = None
    for record in records:
        if record.get("gateway.direction") != TO_SERVER:
            continue
        ts = record["ts"]
        start = ts if start is None else start
        if days is not None and ts - start > days * DAY_S:
            break
        message = record.get("message") or {}
        out.append(
            Message(
                ts=ts,
                agent=record.get("gateway.agent_id") or record.get("gateway.agent") or "gateway",
                method=record.get("mcp.method.name") or message.get("method") or "",
                session=record.get("mcp.session.id"),
                tool=record.get("gen_ai.tool.name"),
                address=record.get("client.address"),
                client=record.get("gateway.client"),
                size=record.get("gateway.message_bytes", 0),
            )
        )
    return out


# ── v5: pooled agent-day lines (RF1, RF2), required steps by window (E5), log join (AI-6) ──


@dataclass(frozen=True)
class AgentDay:
    """One caller's local day as the v5 learner sees it: what a daily agent-day extract holds.

    ``caller`` is the baseline key (B1: per agent) and ``day`` the local day (B9). The rest are
    the day's maxima the lines are learned from: ``busiest_minute`` (scored calls in any 60 s),
    ``busiest_hour_assets`` (distinct touched assets in any hour; None on a day no call
    resolved one), ``largest_request`` (tool key -> the day's largest argument bytes, for
    the calls whose argument size is known) and ``largest_message`` (tool key -> the day's
    largest whole message, ``Message.size``: v4's request lines, learned with
    ``request_limit_pooled`` off). Treat the mappings as read-only."""

    caller: str
    day: int
    busiest_minute: int
    busiest_hour_assets: int | None
    largest_request: Mapping[str, int]
    largest_message: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class LearnedLine:
    """A line learned by the agent-day procedure (RF2): the order statistic ``value``, the
    agent-days it was read from, and the identity left out before reading it (None: none)."""

    value: float
    days: int
    left_out: str | None = None


@dataclass(frozen=True)
class RequestLines:
    """RF1's pooled agent-day line on argument bytes.

    ``multiple`` is k. ``references`` holds r_t for every tool key seen while learning, the
    keys only the identity left out of k used included: its own (:func:`tool_reference`, read
    without ``reference_left_out[t]``, who held the most of its agent-days at or above it) or,
    for the keys in ``borrowed``, its operation class's median own reference (the largest own
    one when its class has none). A key borrows when fewer than ``min_tool_days`` of its
    agent-days are left after its leave-out, or when only the identity left out of k used it.
    ``limits`` holds each key's line ``ceil(k r_t / KB) KB``; ``fallback`` is the line of a key
    not seen while learning, ``k`` times the largest own reference. ``days`` counts the
    agent-days k was read from, and ``left_out`` names the identity left out of k."""

    multiple: float
    references: Mapping[str, float]
    borrowed: frozenset[str]
    limits: Mapping[str, int]
    fallback: int
    days: int
    left_out: str | None = None
    reference_left_out: Mapping[str, str] = field(default_factory=dict)


def derive_policy_v5(
    messages: Iterable[Message],
    base: BehaviourConfig | None = None,
    *,
    alpha: float = LINE_ALPHA,
    reference_quantile: float = REFERENCE_QUANTILE,
    min_line_days: int = MIN_LINE_DAYS,
    min_tool_days: int = MIN_TOOL_DAYS_V5,
    sequence_share: float = SEQUENCE_SHARE,
    min_calls: int = MIN_SEQUENCE_CALLS,
    tool_classes: Mapping[str, str] | None = None,
) -> BehaviourConfig:
    """A v5 ``base`` with its Red Flags lines and required steps learned from ``messages``
    (arrival order): Burst and Sweep (RF2), Oversized request (RF1) and the required earlier
    steps (E5). See the module docstring for the procedure.

    A line that cannot be learned keeps ``base``'s written value: fewer than
    ``min_line_days`` agent-days left once the top identity is out (someone always is, so in
    effect ``min_line_days`` plus his days), or for RF1 no tool key with ``min_tool_days``
    agent-days left after its own leave-out. Learned per-tool lines replace written ones for
    the same key; written required steps stay and learned ones are added. ``tool_classes``
    maps tool keys to operation classes for RF1's fallback (the scan's labels, such as read,
    metadata, write and write with content); a key it leaves out takes the operation its
    calls carried most. With ``request_limit_pooled`` off (RF1's off value), the request
    lines are v4's instead (:func:`message_size_lines`), so the engine's v4 check on the
    whole message meets lines learned on whole messages.
    """
    base = base or BehaviourConfig(design=V5)
    if base.design != V5:
        raise ValueError(f"derive_policy_v5 learns design v5, not {base.design!r}")
    for name, rate in (("alpha", alpha), ("reference_quantile", reference_quantile)):
        if not 0 < rate < 1:
            raise ValueError(f"{name} must be in (0, 1), not {rate!r}")
    if min(min_line_days, min_tool_days, min_calls) < 1:
        raise ValueError("min_line_days, min_tool_days and min_calls must be at least 1")
    calls = learned_calls(messages, base)
    days = agent_days(calls, base)
    burst = agent_day_line([(d.caller, d.busiest_minute) for d in days], alpha, min_line_days)
    widest = [(d.caller, d.busiest_hour_assets) for d in days if d.busiest_hour_assets is not None]
    sweep = agent_day_line(widest, alpha, min_line_days)
    if base.request_limit_pooled:
        request = request_lines(
            days,
            operation_classes(calls) | dict(tool_classes or {}),
            alpha=alpha,
            reference_quantile=reference_quantile,
            min_tool_days=min_tool_days,
            min_days=min_line_days,
        )
        request_limit = request.fallback if request else base.request_limit_bytes
        by_tool = dict(request.limits) if request else {}
    else:
        request_limit, by_tool = message_size_lines(days, base.request_limit_bytes)
    requires = {tool: set(before) for tool, before in base.requires_before.items()}
    for tool, before in required_steps(calls, base, sequence_share, min_calls).items():
        requires.setdefault(tool, set()).update(before)
    return replace(
        base,
        burst_per_minute=int(burst.value) if burst else base.burst_per_minute,
        many_assets_per_hour=int(sweep.value) if sweep else base.many_assets_per_hour,
        request_limit_bytes=request_limit,
        request_limit_by_tool={**base.request_limit_by_tool, **by_tool},
        requires_before={tool: frozenset(before) for tool, before in requires.items()},
    )


def learning_day(ts: float, zone: str | None, config: BehaviourConfig) -> int:
    """The day a call at ``ts`` belongs to in ``config``'s calendar (B9): with ``local_day``
    on, the caller's local day (his ``zone``, else the route's ``route_zone``); off, the UTC
    day. Either rolls over at ``day_start_hour``, so with both at their v1-v4 values it is
    v4's ``int(ts // DAY_S)``."""
    where = (zone or config.route_zone) if config.local_day else clock.DEFAULT_ZONE
    return clock.local_day(ts, where, config.day_start_hour)


def learned_calls(messages: Iterable[Message], config: BehaviourConfig) -> list[Message]:
    """The calls the v5 learner learns from, in arrival order: the scored methods only
    (AI-10), each logical call once, and only calls the server accepted (ARG-1: a call is
    committed to history only then).

    A logical call is one caller's messages with one ``logical_call`` key, each within
    :data:`LOGICAL_CALL_TTL_S` of the one before (an MRTR continuation, a retry after a
    rejection), so a call that crosses the day's rollover is still one call. It is learned
    once, as its first message the server did not reject (so an MRTR call keeps its first
    request's sizes), unless none of its answers accepted it and its last answer is in
    :data:`NOT_ACCEPTED`: such a call never ran, as when an MRTR continuation is rejected or
    never comes. A message without a key is a call of its own, learned unless its answer is
    in :data:`NOT_ACCEPTED`. No outcome (None, as in a log written without them) counts as
    accepted."""
    scored = [m for m in messages if m.method in config.scored_methods]
    kept = [m.logical_call is None and m.outcome not in NOT_ACCEPTED for m in scored]
    for legs in _logical_calls(scored):
        outcomes = [scored[i].outcome for i in legs]
        if ACCEPTED in outcomes or outcomes[-1] not in NOT_ACCEPTED:
            kept[next(i for i in legs if scored[i].outcome != REJECTED)] = True
    return [m for m, keep in zip(scored, kept, strict=True) if keep]


def agent_days(calls: Iterable[Message], config: BehaviourConfig) -> list[AgentDay]:
    """``calls`` (from :func:`learned_calls`, arrival order) folded into agent-days, keyed by
    caller (his baseline key, the message's ``agent``) and :func:`learning_day`, in the order
    they first appear. A call counts toward its own day's maxima; its minute and hour windows
    may reach back across the rollover. Sweep counts the touched asset and, with
    ``multi_asset_breadth`` (AI-12), every further container the call names."""
    recent: dict[str, deque] = defaultdict(deque)  # caller -> call times, last minute
    windows: dict[str, SlidingCounts] = {}  # caller -> touched assets, last hour
    busiest: dict[tuple[str, int], int] = {}
    widest: dict[tuple[str, int], int] = {}
    largest: dict[tuple[str, int], dict[str, int]] = {}  # agent-day -> tool -> argument bytes
    whole: dict[tuple[str, int], dict[str, int]] = {}  # agent-day -> tool -> message bytes
    for m in calls:
        key = (m.agent, learning_day(m.ts, m.zone, config))
        minute = recent[m.agent]
        minute.append(m.ts)
        while minute and minute[0] <= m.ts - MINUTE_S:
            minute.popleft()
        busiest[key] = max(busiest.get(key, 0), len(minute))
        touched = _touched_assets(m, config)
        if touched:
            window = windows.get(m.agent)
            if window is None:
                window = windows[m.agent] = SlidingCounts(HOUR_S)
            for asset in touched:
                window.add(m.ts, asset)
            window.expire(m.ts)
            widest[key] = max(widest.get(key, 0), window.distinct())
        arguments, message = largest.setdefault(key, {}), whole.setdefault(key, {})
        if m.tool:
            message[m.tool] = max(message.get(m.tool, 0), m.size)
            if m.arg_bytes is not None:
                arguments[m.tool] = max(arguments.get(m.tool, 0), m.arg_bytes)
    return [
        AgentDay(key[0], key[1], count, widest.get(key), largest[key], whole[key])
        for key, count in busiest.items()
    ]


def operation_classes(calls: Iterable[Message]) -> dict[str, str]:
    """Each tool key's operation class for RF1's fallback: the operation label its calls
    carried most often (the first one seen on a tie), :data:`UNKNOWN_CLASS` for none."""
    labels: dict[str, Counter] = defaultdict(Counter)
    for m in calls:
        if m.tool:
            labels[m.tool][m.operation or UNKNOWN_CLASS] += 1
    return {tool: counts.most_common(1)[0][0] for tool, counts in labels.items()}


def conformal_order_stat(values: Iterable[float], alpha: float = LINE_ALPHA) -> float | None:
    """The split-conformal line: the ceil((1 - alpha)(n + 1))-th smallest of the ``n``
    values, so a new value exchangeable with them exceeds it with probability at most
    ``alpha``. None when that rank is past ``n`` (fewer than 199 values at 0.5%)."""
    ordered = sorted(values)
    rank = _rank(1 - alpha, len(ordered))
    return ordered[rank - 1] if rank <= len(ordered) else None


def agent_day_line(
    values: Sequence[tuple[str, float]],
    alpha: float = LINE_ALPHA,
    min_days: int = MIN_LINE_DAYS,
    *,
    leave_top_out: bool = True,
) -> LearnedLine | None:
    """RF2: the line over agent-day values ``(caller, value)``, raised by a value above it.
    It is the conformal order statistic, read again once without the caller holding the most
    values at or above the first one (ties: the smallest key; see
    :func:`_leave_top_identity_out` for what that costs). None when fewer than ``min_days``
    values are left at either reading. ``leave_top_out=False`` reads it once (the E8
    poisoning arm's baseline, and the only reading the 0.5% guarantee covers)."""
    return _read_leaving_top_out(
        values, lambda kept: conformal_order_stat(kept, alpha), min_days, leave_top_out
    )


def tool_reference(
    sizes: Sequence[tuple[str, float]],
    quantile: float = REFERENCE_QUANTILE,
    min_days: int = MIN_TOOL_DAYS_V5,
    *,
    leave_top_out: bool = True,
) -> LearnedLine | None:
    """RF1: a tool key's reference r_t over its agent-days' largest requests ``(caller,
    size)``: the ceil(q (n + 1))-th smallest (the largest when that rank is past n), at least
    a byte, read again once without the caller holding the most sizes at or above the first
    reading (ties: the smallest key). Without that, a caller holding just over 1% of a key's
    agent-days at one flat size would set its reference; his ratio is then exactly 1, below
    k, so k's leave-out would never see him. None when fewer than ``min_days`` sizes are left
    at either reading: the key then borrows its class's median."""

    def read(kept: list[float]) -> float:
        return max(MIN_REFERENCE_BYTES, _clipped_order_stat(kept, quantile))

    return _read_leaving_top_out(sizes, read, min_days, leave_top_out)


def message_size_lines(
    days: Iterable[AgentDay],
    default: int,
    quantile: float = QUANTILE,
    min_tool_days: int = MIN_TOOL_DAYS,
) -> tuple[int, dict[str, int]]:
    """RF1 off (``request_limit_pooled`` False): v4's request lines over the v5 agent-days,
    on whole-message bytes. Returns (the agent-days' largest message at ``quantile``,
    rounded up to a KB; tool key -> the same over its agent-days, for each key with at least
    ``min_tool_days`` of them). ``(default, {})`` when no agent-day holds a tool call, as v4
    keeps its written limit then."""
    largest: list[int] = []
    per_tool: dict[str, list[int]] = defaultdict(list)
    for day in days:
        if not day.largest_message:
            continue
        largest.append(max(day.largest_message.values()))
        for tool, size in day.largest_message.items():
            per_tool[tool].append(size)
    if not largest:
        return default, {}
    by_tool = {
        tool: _whole_kb(_quantile(sizes, quantile))
        for tool, sizes in per_tool.items()
        if len(sizes) >= min_tool_days
    }
    return _whole_kb(_quantile(largest, quantile)), by_tool


def request_lines(
    days: Iterable[AgentDay],
    classes: Mapping[str, str] | None = None,
    *,
    alpha: float = LINE_ALPHA,
    reference_quantile: float = REFERENCE_QUANTILE,
    min_tool_days: int = MIN_TOOL_DAYS_V5,
    min_days: int = MIN_LINE_DAYS,
    leave_top_out: bool = True,
) -> RequestLines | None:
    """RF1: the pooled agent-day line on argument bytes, from the agent-days with a known
    request size. One budget per agent-day, not per tool: k is set on each day's worst ratio
    ``max_t size / r_t``, so a day using m tools faces one test, not m.

    The top identity is left out at both levels. Each key's reference leaves out the caller
    holding the most of its agent-days at or above it (:func:`tool_reference`). Then the
    caller holding the most agent-days at or above k is left out once and the line learned
    again *from scratch* (references and k), so an identity in k's tail does not keep a
    reference inflated either. A key only he used still gets a line, from its class's median
    reference, not the loosest ``fallback``. None when it cannot be learned (see
    :func:`derive_policy_v5`). ``leave_top_out=False`` reads it once at both levels (the E8
    poisoning arm's baseline)."""
    sized = [d for d in days if d.largest_request]
    classes = classes or {}
    tools = list(dict.fromkeys(tool for d in sized for tool in d.largest_request))

    def learn(kept: Sequence[AgentDay]) -> RequestLines | None:
        return _request_lines_once(
            kept,
            classes,
            tools,
            alpha=alpha,
            reference_quantile=reference_quantile,
            min_tool_days=min_tool_days,
            min_days=min_days,
            leave_top_out=leave_top_out,
        )

    if not leave_top_out:
        return learn(sized)
    learned = _leave_top_identity_out(
        sized,
        learn,
        lambda lines, day: _worst_ratio(day, lines.references) >= lines.multiple,
        lambda day: day.caller,
    )
    return None if learned is None else replace(learned[0], left_out=learned[1])


def required_steps(
    calls: Iterable[Message],
    config: BehaviourConfig,
    sequence_share: float = SEQUENCE_SHARE,
    min_calls: int = MIN_SEQUENCE_CALLS,
) -> dict[str, frozenset[str]]:
    """E5: the earlier steps learned from ``calls`` (from :func:`learned_calls`).

    With ``requires_window_s`` set (v5's default), B requires A when B was called at least
    ``min_calls`` times and at least ``sequence_share`` of those calls had an A call by the
    same caller earlier in arrival order and at most ``requires_window_s`` before it: on the
    same touched asset when ``requires_same_asset`` is on, or with either asset unresolved,
    which is the check the v5 engine makes. With it None (E5 off) the session learner of
    v1-v4 runs, counting B's sessions instead of its calls."""
    window = config.requires_window_s
    if window is None:
        return _steps_by_session(calls, sequence_share, min_calls)
    calls = [m for m in calls if m.tool]
    totals = Counter(m.tool for m in calls)
    # A pair (B, A) is learned iff A preceded at least ceil(share n_B) of B's n_B calls, so
    # once B has missed A more than ``spare[B]`` times the pair is dead for good (misses only
    # grow): it is no longer checked, which keeps the learner linear in practice.
    spare = {t: n - math.ceil(sequence_share * n) for t, n in totals.items() if n >= min_calls}
    last_call: dict[str, dict[str, float]] = defaultdict(dict)  # caller -> tool -> last ts
    last_on: dict[str, dict[tuple[str, str | None], float]] = defaultdict(dict)  # (tool, asset)
    so_far: Counter = Counter()  # B -> its calls so far
    preceded: dict[str, Counter] = defaultdict(Counter)  # B -> A -> B's calls A preceded
    alive: dict[str, set[str]] = {}  # B -> the A's still able to reach the share
    for m in calls:
        tool, mine, on = m.tool, last_call[m.agent], last_on[m.agent]
        if tool in spare:
            for before in alive[tool] & mine.keys() if tool in alive else list(mine):
                if before != tool and m.ts - mine[before] <= window:
                    if not config.requires_same_asset or _on_same_asset(on, before, m, window):
                        preceded[tool][before] += 1
            so_far[tool] += 1
            if so_far[tool] > spare[tool]:
                candidates = alive.get(tool, preceded[tool].keys())
                alive[tool] = {
                    a for a in candidates if so_far[tool] - preceded[tool][a] <= spare[tool]
                }
        mine[tool] = m.ts
        on[(tool, m.asset)] = m.ts
    pairs = Counter({(b, a): n for b, counts in preceded.items() for a, n in counts.items()})
    return _learned_steps(pairs, totals, sequence_share, min_calls)


def _touched_assets(m: Message, config: BehaviourConfig) -> list[str]:
    """The touched assets Sweep counts for ``m``: its asset, plus AI-12's further ones."""
    touched = [m.asset] if m.asset else []
    if config.multi_asset_breadth:
        touched += [asset for asset in m.more_assets if asset]
    return touched


def _rank(q: float, n: int) -> int:
    """The 1-based rank ceil(q (n + 1)), robust to float error in the product."""
    return math.ceil(q * (n + 1) - ORDER_TOLERANCE)


def _kb_line(size: float) -> int:
    """A line in bytes rounded up to a whole KB (float error in ``k r_t`` aside)."""
    return math.ceil(size / KB - ORDER_TOLERANCE) * KB


def _leave_top_identity_out[T, L](
    items: Sequence[T],
    learn: Callable[[Sequence[T]], L | None],
    above: Callable[[L, T], bool],
    caller: Callable[[T], str],
) -> tuple[L, str | None] | None:
    """``learn(items)``, then once more without the caller holding the most items ``above``
    the first result (ties: the smallest key): (the result, who was left out) or None when
    either reading cannot be learned. Nobody is left out when no item is above it.

    ``above`` counts items *at or above* the line, not only past it: a caller whose inflated
    agent-days all tie holds the order statistic itself, with nothing strictly above it, and
    would otherwise never be left out (20 days at 200 calls/min among 3,000 ordinary ones).

    The cost, for the author to weigh against that (Part A's RF1 and RF2 formulas and the
    probes use ">"): the order statistic itself is always in the tail, so a caller is always
    left out. The second reading has fewer days, so a line needs ``min_days`` left after it,
    and at 199-398 agent-days, where the line is the maximum, the caller holding the maximum
    day always goes. The line then sits lower than the plain order statistic: on a route of
    few callers of unlike scale, ordinary days cross it more often than alpha (see the module
    docstring). ">" leaves no one out at 199-398 agent-days, so it cannot stop one inflated
    day there."""
    first = learn(items)
    if first is None:
        return None
    tail = Counter(caller(item) for item in items if above(first, item))
    if not tail:
        return first, None
    worst = min(tail, key=lambda who: (-tail[who], who))
    second = learn([item for item in items if caller(item) != worst])
    return None if second is None else (second, worst)


def _read_leaving_top_out(
    values: Sequence[tuple[str, float]],
    read: Callable[[list[float]], float | None],
    min_days: int,
    leave_top_out: bool,
) -> LearnedLine | None:
    """``read`` over the values of ``(caller, value)`` pairs, from at least ``min_days`` (and
    one) of them; with ``leave_top_out``, read again once without the caller holding the most
    values at or above the first reading (:func:`_leave_top_identity_out`)."""

    def learn(kept: Sequence[tuple[str, float]]) -> LearnedLine | None:
        if len(kept) < max(min_days, 1):
            return None
        value = read([v for _, v in kept])
        return None if value is None else LearnedLine(value, len(kept))

    if not leave_top_out:
        return learn(values)
    learned = _leave_top_identity_out(
        values, learn, lambda line, item: item[1] >= line.value, lambda item: item[0]
    )
    return None if learned is None else replace(learned[0], left_out=learned[1])


def _request_lines_once(
    days: Sequence[AgentDay],
    classes: Mapping[str, str],
    tools: Sequence[str],
    *,
    alpha: float,
    reference_quantile: float,
    min_tool_days: int,
    min_days: int,
    leave_top_out: bool,
) -> RequestLines | None:
    """RF1 on one set of agent-days with the leave-out at the reference level only
    (``pooled_line_rates.learn_line`` plus :func:`tool_reference`). Every key in ``tools``
    gets a line: a key none of ``days`` used, or one with too few of them, borrows."""
    if len(days) < min_days:
        return None
    per_tool: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for day in days:
        for tool, size in day.largest_request.items():
            per_tool[tool].append((day.caller, size))
    own: dict[str, float] = {}
    left_out: dict[str, str] = {}
    for tool, sizes in per_tool.items():
        reference = tool_reference(
            sizes, reference_quantile, min_tool_days, leave_top_out=leave_top_out
        )
        if reference is not None:
            own[tool] = reference.value
            if reference.left_out is not None:
                left_out[tool] = reference.left_out
    if not own:
        return None
    by_class: dict[str, list[float]] = defaultdict(list)
    for tool, reference in own.items():
        by_class[classes.get(tool, UNKNOWN_CLASS)].append(reference)
    medians = {name: sorted(refs)[len(refs) // 2] for name, refs in by_class.items()}
    top = max(own.values())
    references = {
        tool: own[tool] if tool in own else medians.get(classes.get(tool, UNKNOWN_CLASS), top)
        for tool in tools
    }
    multiple = conformal_order_stat((_worst_ratio(d, references) for d in days), alpha)
    if multiple is None:
        return None
    return RequestLines(
        multiple=multiple,
        references=references,
        borrowed=frozenset(tools) - set(own),
        limits={tool: _kb_line(multiple * ref) for tool, ref in references.items()},
        fallback=_kb_line(multiple * top),
        days=len(days),
        reference_left_out=left_out,
    )


def _logical_calls(scored: Sequence[Message]) -> list[list[int]]:
    """ARG-1: the messages of each logical call among ``scored`` (their indexes, arrival
    order): one caller's messages with one ``logical_call`` key, each within
    :data:`LOGICAL_CALL_TTL_S` of the one before. Only the calls with a message in the last
    TTL are held while reading."""
    calls: list[list[int]] = []
    recent: OrderedDict[tuple[str, str], tuple[int, float]] = OrderedDict()  # -> (call, last)
    for index, m in enumerate(scored):
        if m.logical_call is None:
            continue
        while recent:  # forget the calls idle past the TTL, the longest idle first
            _, (_, last) = next(iter(recent.items()))
            if m.ts - last <= LOGICAL_CALL_TTL_S:
                break
            recent.popitem(last=False)
        key = (m.agent, m.logical_call)
        found = recent.pop(key, None)
        if found is None or m.ts - found[1] > LOGICAL_CALL_TTL_S:
            found = (len(calls), m.ts)
            calls.append([])
        calls[found[0]].append(index)
        recent[key] = (found[0], m.ts)
    return calls


def _clipped_order_stat(values: Sequence[float], q: float) -> float:
    """The ceil(q (n + 1))-th smallest value, or the largest when that rank is past n (a
    tool's reference: ``red_flag_arms.p4_limits``)."""
    ordered = sorted(values)
    return ordered[min(len(ordered), _rank(q, len(ordered))) - 1]


def _worst_ratio(day: AgentDay, references: Mapping[str, float]) -> float:
    """rho: the agent-day's largest ``size / r_t`` over the tool keys it used."""
    return max(size / references[tool] for tool, size in day.largest_request.items())


def _on_same_asset(
    last_on: Mapping[tuple[str, str | None], float], before: str, m: Message, window: float
) -> bool:
    """E5 (A)'s asset tie: a ``before`` call in the window on ``m``'s touched asset or with
    none resolved; any ``before`` call when ``m`` has none resolved."""
    if m.asset is None:
        return True
    for asset in (m.asset, None):
        ts = last_on.get((before, asset))
        if ts is not None and m.ts - ts <= window:
            return True
    return False


def _steps_by_session(
    calls: Iterable[Message], sequence_share: float, min_sessions: int
) -> dict[str, frozenset[str]]:
    """E5 off: v1-v4's procedure, B's sessions with A earlier in the same session."""
    earlier: dict[tuple[str, str], set[str]] = defaultdict(set)  # session -> tools so far
    sessions_with: Counter = Counter()
    preceded: Counter = Counter()
    for m in calls:
        if not m.tool or not m.session:
            continue
        seen = earlier[(m.agent, m.session)]
        if m.tool not in seen:  # B's first call in this session
            sessions_with[m.tool] += 1
            for before in seen:
                preceded[(m.tool, before)] += 1
        seen.add(m.tool)
    return _learned_steps(preceded, sessions_with, sequence_share, min_sessions)


def _learned_steps(
    preceded: Counter, totals: Counter, share: float, minimum: int
) -> dict[str, frozenset[str]]:
    """B -> the A's that came before at least ``share`` of B's ``totals`` (at least
    ``minimum`` of them), by tool name."""
    steps: dict[str, set[str]] = defaultdict(set)
    for (tool, before), n in preceded.items():
        if totals[tool] >= minimum and n >= share * totals[tool]:
            steps[tool].add(before)
    return {tool: frozenset(steps[tool]) for tool in sorted(steps)}


def _messages_from_log_v5(records: Iterable[dict], days: float | None) -> list[Message]:
    """AI-6: the requests of a v5 gateway log joined with their decision lines and outcome.

    A request line and the lines about it share (``gateway.exchange_id``,
    ``jsonrpc.request.id``). From the decision (``gateway.decision``) come the engine's own
    inputs (tool key, touched assets, sensitivity, operation); from the request line, or
    else the decision line, the LOG-1 and ARG-1 fields (baseline key as the caller, zone,
    logical-call key, argument bytes). The outcome comes from the reply line with the same
    key, or from a bodiless reply's line in the same exchange. A request with no decision
    (unscored, a scoring error, a v1-v4 log) gives a message without the engine inputs, as
    v1-v4 read it. Lines up to ``JOIN_GRACE_S`` past the window are still read for its last
    requests' decisions and outcomes."""
    requests: list[tuple[tuple | None, dict]] = []
    decisions: dict[tuple, dict] = {}
    outcomes: dict[tuple, str] = {}
    exchange_outcomes: dict[object, str] = {}  # bodiless replies: every call of the exchange
    start = None
    for record in records:
        key = _join_key(record)
        if record.get(OUTCOME_FIELD):
            if key is not None:
                outcomes[key] = record[OUTCOME_FIELD]
            elif record.get(EXCHANGE_ID_FIELD) is not None:
                exchange_outcomes[record[EXCHANGE_ID_FIELD]] = record[OUTCOME_FIELD]
        direction = record.get("gateway.direction")
        if direction == FROM_GATEWAY and isinstance(record.get(DECISION_FIELD), dict):
            if key is not None:
                decisions[key] = record
            continue
        if direction != TO_SERVER:
            continue
        ts = record["ts"]
        start = ts if start is None else start
        if days is not None and ts - start > days * DAY_S:
            if ts - start > days * DAY_S + JOIN_GRACE_S:
                break
            continue
        requests.append((key, record))
    out = []
    for key, record in requests:
        outcome = outcomes.get(key) if key is not None else None
        if outcome is None:
            outcome = exchange_outcomes.get(record.get(EXCHANGE_ID_FIELD))
        out.append(_joined_message(record, decisions.get(key) if key else None, outcome))
    return out


def _join_key(record: dict) -> tuple | None:
    """(exchange id, request id), or None for a line that lacks either."""
    exchange, request = record.get(EXCHANGE_ID_FIELD), record.get(REQUEST_ID_FIELD)
    return None if exchange is None or request is None else (exchange, request)


def _joined_message(request: dict, decision_line: dict | None, outcome: str | None) -> Message:
    """One v5 message from a request line, its decision line (if any) and its outcome."""
    lines = (request, decision_line or {})
    decision = (decision_line or {}).get(DECISION_FIELD) or {}
    body = request.get("message") or {}

    def logged(name: str) -> object:
        return next((line[name] for line in lines if line.get(name) is not None), None)

    return Message(
        ts=request["ts"],
        agent=logged(BASELINE_KEY_FIELD)
        or request.get("gateway.agent_id")
        or request.get("gateway.agent")
        or GATEWAY_CALLER,
        method=request.get("mcp.method.name") or body.get("method") or "",
        session=request.get("mcp.session.id"),
        tool=decision.get(DECISION_TOOL) or request.get("gen_ai.tool.name"),
        asset=decision.get(DECISION_ASSET),
        more_assets=tuple(decision.get(DECISION_MORE_ASSETS) or ()),
        sensitivity=decision.get(DECISION_SENSITIVITY),
        operation=decision.get(DECISION_OPERATION),
        address=request.get("client.address"),
        client=request.get("gateway.client"),
        size=request.get("gateway.message_bytes", 0),
        zone=logged(ZONE_FIELD),
        arg_bytes=logged(ARG_BYTES_FIELD),
        logical_call=logged(LOGICAL_CALL_FIELD),
        outcome=outcome,
    )


def main() -> None:
    """Learn a route's behaviour policy from its gateway log and write it as JSON."""
    from mcp_security.gateway.log_file import read_log  # noqa: PLC0415 — CLI only

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--log", type=Path, required=True, help="the route's gateway log")
    parser.add_argument("--out", type=Path, required=True, help="where to write the policy")
    parser.add_argument("--days", type=float, default=None, help="learn from the first N days")
    parser.add_argument(  # v1-v4 (LEGACY_DESIGNS) keep the old procedure; v5 its own
        "--design", choices=DESIGNS, default=V4, help="the behaviour design the route runs"
    )
    args = parser.parse_args()
    messages = messages_from_log(read_log(args.log), args.days, design=args.design)
    policy = derive_policy(messages, base=BehaviourConfig(design=args.design))
    args.out.write_text(json.dumps(config_to_json(policy), indent=1), encoding="utf-8")
    if policy.design == V5:
        print(_summary_v5(messages, policy, args.out))
        return
    calls = sum(1 for m in messages if m.method == CALL_METHOD)
    print(
        f"{calls} tool calls -> {args.out}: design {policy.design}, "
        f"burst > {policy.burst_per_minute}/min, request > {policy.request_limit_bytes} B "
        f"({len(policy.request_limit_by_tool)} tools with their own limit), "
        f"{len(policy.requires_before)} tools with a required earlier step"
    )


def _summary_v5(messages: Sequence[Message], policy: BehaviourConfig, out: Path) -> str:
    """The CLI's one-line report of a learned v5 policy."""
    calls = learned_calls(messages, policy)
    days = agent_days(calls, policy)
    sweep = "off" if policy.many_assets_per_hour is None else policy.many_assets_per_hour
    return (
        f"{len(calls)} accepted scored calls on {len(days)} agent-days -> {out}: design v5, "
        f"burst > {policy.burst_per_minute}/min, sweep > {sweep} assets/h, "
        f"request > {policy.request_limit_bytes} B for new tools "
        f"({len(policy.request_limit_by_tool)} tool keys with their own line), "
        f"{len(policy.requires_before)} tools with a required earlier step "
        f"(lines need {MIN_LINE_DAYS} agent-days left once the top identity is out; below "
        "that the written defaults stay)"
    )


if __name__ == "__main__":
    main()
