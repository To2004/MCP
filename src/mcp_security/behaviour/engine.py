"""The dynamic layer's behaviour multiplier: how strange is this call for this agent?

Each dimension compares the agent only with his own last 90 days and gives a score ``s``
between 0 and 1, where 0.5 is the edge of ordinary ("twice his usual"). The strangest
dimension sets the call's multiplier::

    M = 5   ** (2S - 1)    when S >= 0.5     (the edge of ordinary -> 1, the strangest -> 5)
    M = 0.7 ** (1 - 2S)    when S <  0.5     (familiar -> below 1, very familiar -> 0.7)

so ``M`` lies in [0.7, 5] by its shape alone (no clipping), and a static level of 1-5 times
``M`` lies in [0.7, 25]. Three kinds of score:

- **more than his usual** (counts and durations)::

      s = (v + u) / (v + u + 2 * (his average + u))      u = 1 call, 1 minute, 1 asset or 1 KB

- **rarer than his usual** (tool, asset, time of day; v4 also network and client app): how
  many times a day he does something this rare,
  ``e = (his calls on things at most this common + 1) / (active days + 1)``, then
  ``s = c / (1 + 2 * e)`` with ``c = 0.9`` for tools (and v4's network and app);
- **rules** (the paper's Red Flags group; earlier "Expected Conduct", then "Policy"): broken ->
  the rule's value (0.9 by default, x3.6; protocol skip 0.7, x1.9). The paper names each
  dimension differently from its key here (``many_assets`` is "sweep", ``protocol_skip`` is
  "missing handshake", ...): the mapping is in ``DIMENSION_FORMULAS.md``, section Names.

Four designs, chosen by ``BehaviourConfig.design`` (``reports/experiments/dynamic_dimensions/``
``DIMENSION_FORMULAS.md`` for v4, ``DIMENSION_FORMULAS_v1.md`` to ``_v3.md`` for the others):

- **v1**: the first design. Request size is also "more than his usual"; a first-time tool is
  rare through the tool dimension; history learns after every call; 5 warm-up calls.
- **v2**: request size only as a rule (over the limit); a tool not used in 90 days is a rule.
- **v3**: v2, plus same call in 10 minutes, writes and distinct assets in the last
  hour (counts), a "many assets in an hour" rule over a learned limit, a first look at a
  sensitive asset (0.9 for sensitivity 5, 0.8 for 4), request-size limits per tool; history
  updated once a day (a call is compared with his history up to yesterday), so the warm-up is
  his first day, during which only the rules that need none of his past fire; 14 days of
  onboarding before "starting something new" counts; weekends blended with all days; a habit
  rule (burst, risky order, many assets) counts less the more often he broke it; something new
  for him that 3 other agents also started in the last 7 days scores at most 0.5 (an org-wide
  change), except a first look at a sensitive asset.
- **v4** (default): v3 with every "new for him" check in Typical Footprint, none as a rule: the
  new network, new app and new tool rules are gone; network (/16) and client app are scored
  "rarer than his usual" like tool and asset, on every message; a tool not used in 90 days is
  scored by tool rarity; a first look at a sensitive asset is a floor on the asset's score
  (0.9 for sensitivity 5, 0.8 for 4, never org-discounted, and applied in the warm-up too).
- **v5** (``knowledge_base/v5-design-spec.md``; being built): v4's dimensions plus Read volume
  in Typical Cadence, priced by commonness and the record rank, with floors outside the
  statistic. So far (Batch 0) it has its interfaces: every config switch, the new message and
  verdict fields, :meth:`BehaviourEngine.score` / :meth:`BehaviourEngine.commit`, and the
  legacy fixes (E1, E2, RF9) under ``legacy_fixes``. With every v5 switch at its off value
  (:func:`v5_switches_off`) it gives exactly v4's verdicts.

Messages must reach :meth:`BehaviourEngine.observe` in arrival order; every request message
counts (``initialize`` and ``tools/list`` too: they carry the origin and the handshake).
"""

from __future__ import annotations

import math
import pickle
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from ipaddress import ip_address, ip_network

from mcp_security.behaviour.clock import (
    DAY_S,
    DAY_START_HOUR,
    DAYS_PER_WEEK,
    DEFAULT_ZONE,
    HOUR_S,
    WEEKEND_DAYS,
    check_day_start,
    zone,
)
from mcp_security.behaviour.memory import (
    DailyCounts,
    DailyMean,
    FirstUses,
    SlidingCounts,
    as_key,
    is_weekend,
)

MINUTE_S = 60.0  # DAY_S and HOUR_S come from clock.py: one source for the calendar
CALL_METHOD = "tools/call"
INIT_METHOD = "initialize"
RESOURCE_READ_METHOD = "resources/read"  # v5 scores these too (AI-10)
PROMPT_GET_METHOD = "prompts/get"
WRITE = "write"
READ = "read"
#: v5 message values: the protocol era (E3), whether the server accepted the call (ARG-1)
#: and how far an asset is exposed (EXP-1).
LEGACY_ERA, MODERN_ERA = "legacy", "modern"
ACCEPTED, REJECTED = "accepted", "rejected"
PUBLIC, INTERNAL, PRIVATE = "public", "internal", "private"

MAX_MULTIPLIER = 5.0
MIN_MULTIPLIER = 0.7  # v1-v4's bottom, and the base of the lower branch of the curve
V5_MIN_MULTIPLIER = 1.0  # PS8, decision D2: in v5 M never falls below 1
EDGE_OF_ORDINARY = 0.5
ALERT_LINE = 3.0  # v1-v4: a call at x3 or more is an alert (reporting only; PS6)
ALERT_ALPHA = 0.01  # v5: the deployed 1% line (CAL-5)
TOP_SENSITIVITY = 5  # the first-look rule is at its full value on these assets
SAME_CALL_WINDOW_S = 600.0  # "same call in 10 minutes"

V1, V2, V3, V4, V5 = "v1", "v2", "v3", "v4", "v5"
DESIGNS = (V1, V2, V3, V4, V5)
LEGACY_DESIGNS = (V1, V2, V3, V4)  # the designs v5 must leave bit-identical

#: Dimension names, as they appear in a verdict's ``scores`` and ``strongest``.
CALLS_LAST_HOUR = "calls_last_hour"
SESSION_LENGTH = "session_length"
REQUEST_SIZE = "request_size"  # v1
TOOL = "tool"
ASSET = "asset"
TIME_OF_DAY = "time_of_day"
ASSETS_LAST_HOUR = "assets_last_hour"  # v3
WRITES_LAST_HOUR = "writes_last_hour"  # v3
SAME_CALL_10M = "same_call_10m"  # v3
NETWORK = "network"  # v4: Typical Footprint
CLIENT = "client"  # v4: Typical Footprint, the client app
NEW_NETWORK = "new_network"  # v1-v3
NEW_CLIENT = "new_client"  # v1-v3
NEW_TOOL = "new_tool"  # v2, v3
BURST = "burst"
SEQUENCE = "sequence"
REQUEST_TOO_BIG = "request_too_big"
PROTOCOL_SKIP = "protocol_skip"
MANY_ASSETS = "many_assets"  # v3
SENSITIVE_FIRST_LOOK = "sensitive_first_look"  # v3; v4 folds it into ``asset``
READ_VOLUME = "read_volume"  # v5 (AI-8, decision D1): reply bytes in the last hour

#: v3: the rules that count less the more often he broke them (a habit can be benign)
HABIT_RULES = frozenset({BURST, SEQUENCE, MANY_ASSETS})
WINDOW_COUNTS = (ASSETS_LAST_HOUR, WRITES_LAST_HOUR, SAME_CALL_10M)

#: Each design's dimensions by group, in the order of its design document. v5 is v4 plus
#: Read volume in Typical Cadence (decision D1): 16 dimensions, Cadence shares 1/21 each.
TYPICAL_CADENCE, TYPICAL_FOOTPRINT, RED_FLAGS = "Typical Cadence", "Typical Footprint", "Red Flags"
_CADENCE_V4 = (
    CALLS_LAST_HOUR,
    WRITES_LAST_HOUR,
    ASSETS_LAST_HOUR,
    SAME_CALL_10M,
    SESSION_LENGTH,
    TIME_OF_DAY,
)
_FOOTPRINT_V4 = (TOOL, ASSET, NETWORK, CLIENT)
_RED_FLAGS_V4 = (BURST, MANY_ASSETS, REQUEST_TOO_BIG, SEQUENCE, PROTOCOL_SKIP)
DIMENSION_GROUPS: dict[str, dict[str, tuple[str, ...]]] = {
    V1: {
        "Timing": (CALLS_LAST_HOUR, SESSION_LENGTH, TIME_OF_DAY, BURST, SEQUENCE),
        "Footprint": (TOOL, ASSET),
        "Origin": (NEW_NETWORK, NEW_CLIENT),
        "Request": (REQUEST_SIZE, REQUEST_TOO_BIG, PROTOCOL_SKIP),
    },
    V2: {
        TYPICAL_CADENCE: (CALLS_LAST_HOUR, SESSION_LENGTH, TIME_OF_DAY),
        TYPICAL_FOOTPRINT: (TOOL, ASSET),
        "Policy": (
            BURST,
            SEQUENCE,
            NEW_NETWORK,
            NEW_CLIENT,
            NEW_TOOL,
            REQUEST_TOO_BIG,
            PROTOCOL_SKIP,
        ),
    },
    V3: {
        TYPICAL_CADENCE: (
            CALLS_LAST_HOUR,
            SESSION_LENGTH,
            TIME_OF_DAY,
            SAME_CALL_10M,
            WRITES_LAST_HOUR,
            ASSETS_LAST_HOUR,
        ),
        TYPICAL_FOOTPRINT: (TOOL, ASSET),
        "Policy": (
            BURST,
            SEQUENCE,
            MANY_ASSETS,
            NEW_NETWORK,
            NEW_CLIENT,
            NEW_TOOL,
            REQUEST_TOO_BIG,
            SENSITIVE_FIRST_LOOK,
            PROTOCOL_SKIP,
        ),
    },
    V4: {TYPICAL_CADENCE: _CADENCE_V4, TYPICAL_FOOTPRINT: _FOOTPRINT_V4, RED_FLAGS: _RED_FLAGS_V4},
    V5: {
        TYPICAL_CADENCE: (*_CADENCE_V4, READ_VOLUME),
        TYPICAL_FOOTPRINT: _FOOTPRINT_V4,
        RED_FLAGS: _RED_FLAGS_V4,
    },
}


def dimension_groups(design: str) -> dict[str, tuple[str, ...]]:
    """``design``'s dimensions by group (engine keys); ``ValueError`` for an unknown design."""
    if design not in DIMENSION_GROUPS:
        raise ValueError(f"design must be one of {DESIGNS}, not {design!r}")
    return DIMENSION_GROUPS[design]


class DesignDefault:
    """What a v5 config field holds when it was not given: ``BehaviourConfig.__post_init__``
    replaces it with the field's value for the config's design (:data:`DESIGN_VALUES`). One
    instance only, so copies and pickles stay the same marker."""

    _instance: DesignDefault | None = None

    def __new__(cls) -> DesignDefault:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "DESIGN_DEFAULT"

    def __copy__(self) -> DesignDefault:
        return self

    def __deepcopy__(self, memo: dict) -> DesignDefault:
        return self


DESIGN_DEFAULT = DesignDefault()
DERIVED = "derived"  # a v5 default computed from other fields (alert_line, alert_floor_rate)
_THIRD = 1 / 3
WATCH_CAP = 2 / 15  # CAL-3: a watch-only term's q/w never falls below this
WATCH_FLOOR_RATE = 0.125  # CAL-4: the watch floor's q (x2.63)
FLOOR_BUDGET = (0.003, 0.0005)  # CAL-4: beta for first access and for the copy floor
ROUTE_WARMUP_DAYS = 14  # CAL-4: alert floors act as watch floors until the route has these
SURGE_MIN = 5  # CAL-6: distinct callers' record agent-days that make a surge, at least
SURGE_FACTOR = 3.0  # CAL-6: ... and this many times the window's daily mean
UTC_DAY_START_HOUR = 0.0  # v1-v4: a day starts at midnight UTC
SEQUENCE_WINDOW_S = 10 * MINUTE_S  # E5: read-then-write within 10 minutes
REQUIRES_WINDOW_S = DAY_S  # E5: a required earlier step within 24 hours
IDLE_GAP_S = 30 * MINUTE_S  # E4: a caller's run of calls ends after 30 idle minutes
MAX_SESSIONS_PER_CALLER = 64  # E8: legacy sessions remembered per caller
SESSION_TTL_S = 7 * DAY_S  # E8: a legacy session is forgotten after 7 idle days
ORG_NEW_DAYS = 30  # RF7: a value is new to the organisation if unseen this long
ORG_DISCOUNT_MAX_STATIC = 3  # RF7: the org discount applies only up to this static level
ESTABLISHED_DAYS = 20  # RF7, RF11, floors: active days before a caller is established
MAX_HISTORY_DAYS = 365  # B5
USUAL_QUANTILE = 0.75  # B7: the robust usual
MAX_VALUES_PER_KIND = 4_096  # DEP-7: distinct values kept per kind before the overflow
SCORE_BUDGET_MS = 5.0  # DEP-7: scoring time per call before it is marked unscored
REPLY_UNIT_BYTES = 100_000  # AI-8: Read volume's unit u
REPLY_WINDOW_S = HOUR_S  # AI-8: Read volume counts the last hour's reply bytes
MIN_STATIC_LEVEL, MAX_STATIC_LEVEL = 1, 5  # R_static's range (PS7)
#: v5 (AI-10): the methods scored as calls; v1-v4 score tool calls only
V5_SCORED_METHODS = (CALL_METHOD, RESOURCE_READ_METHOD, PROMPT_GET_METHOD)
#: B2: where the client value comes from. v1-v4: the client's self-reported ``clientInfo``;
#: v5: the pair (authenticated app, ``clientInfo`` family or ``(none)``).
CLIENT_INFO, APP_CLIENT = "client_info", "app"

#: Every config field v5 adds: (its value for v1-v4, its v5 default), in resolution order.
#: A field not given takes the value for its design. The v1-v4 value keeps today's behaviour
#: and is also the switch's "off" value on v5 (spec section 4.4); the spec's other candidate
#: values, where they differ from the v1-v4 one, are in :data:`SPEC_ALTERNATIVES`.
DESIGN_VALUES: dict[str, tuple[object, object]] = {
    "legacy_fixes": (False, True),  # E1, E2, RF9 (section 4.1); on v4 it makes "v4.1"
    "max_multiplier": (MAX_MULTIPLIER, MAX_MULTIPLIER),  # EV-21
    "min_multiplier": (MIN_MULTIPLIER, V5_MIN_MULTIPLIER),  # EV-21, PS8 (D2)
    "alert_alpha": (None, ALERT_ALPHA),  # CAL-5
    "alert_line": (ALERT_LINE, DERIVED),  # PS6; v5: the multiplier at alert_alpha (x4.69)
    "calibration": ("max", "commonness"),  # CAL-1
    "record_rank": (False, True),  # CAL-2
    "budget_shares": (None, (_THIRD, _THIRD, _THIRD)),  # CAL-3: Cadence, Footprint, Red Flags
    "watch_cap": (None, WATCH_CAP),  # CAL-3
    "alert_floor_rate": (None, DERIVED),  # CAL-4: the deployed alpha
    "watch_floor_rate": (None, WATCH_FLOOR_RATE),  # CAL-4
    "floor_budget": (None, FLOOR_BUDGET),  # CAL-4
    "route_warmup_days": (None, ROUTE_WARMUP_DAYS),  # CAL-4
    "surge_min": (None, SURGE_MIN),  # CAL-6
    "surge_factor": (None, SURGE_FACTOR),  # CAL-6
    "route_zone": (DEFAULT_ZONE, DEFAULT_ZONE),  # CAL-7, B9
    "day_start_hour": (UTC_DAY_START_HOUR, DAY_START_HOUR),  # CAL-7, B9
    "footprint_alerts": (True, True),  # FP-1, decision D3 = (a)
    "record_hold_days": (None, None),  # tune HOLD
    "leave_top_identity_out": (False, False),  # tune TOP
    "record_reference": ("all", "all"),  # tune EST
    "reference_scope": ("route", "route"),  # tune GWR
    "sequence_record": (False, True),  # SEQ-1
    "copy_floor": (False, True),  # SEQ-2
    "sequence_window_s": (None, SEQUENCE_WINDOW_S),  # E5: read-then-write
    "requires_window_s": (None, REQUIRES_WINDOW_S),  # E5: a required earlier step
    "requires_same_asset": (False, True),  # E5: ... on the same asset
    "idle_gap_s": (None, IDLE_GAP_S),  # E4
    "handshake_legacy_sessionless": (False, True),  # E6
    "max_sessions_per_caller": (None, MAX_SESSIONS_PER_CALLER),  # E8
    "session_ttl_s": (None, SESSION_TTL_S),  # E8
    "origin_from_calls_only": (False, True),  # E12
    "missing_client_counts": (False, True),  # E11: a missing client name is "(none)"
    "client_source": (CLIENT_INFO, APP_CLIENT),  # B2
    "request_limit_pooled": (False, True),  # RF1: one limit on argument bytes, org-ranked
    "org_new_days": (None, ORG_NEW_DAYS),  # RF7
    "org_discount_reads_only": (False, True),  # RF7
    "org_discount_max_static": (None, ORG_DISCOUNT_MAX_STATIC),  # RF7
    "established_days": (None, ESTABLISHED_DAYS),  # RF7, RF11, floors (with onboarding_days)
    "habit_after_established": (False, True),  # RF11
    "max_history_days": (None, MAX_HISTORY_DAYS),  # B5
    "usual_quantile": (None, USUAL_QUANTILE),  # B7
    "local_day": (False, True),  # B9
    "weekend_days": (WEEKEND_DAYS, WEEKEND_DAYS),  # B9
    "shared_networks": ((), ()),  # B10: (label, CIDR) pairs counted as one platform network
    "max_values_per_kind": (None, MAX_VALUES_PER_KIND),  # DEP-7
    "score_budget_ms": (None, SCORE_BUDGET_MS),  # DEP-7
    "asset_identity": ("driver", "target"),  # AI-2
    "tool_key": ("name", "operation"),  # AI-7
    "multi_asset_breadth": (False, True),  # AI-12: each container a call names adds to Breadth
    "reply_volume": (False, True),  # AI-8 (D1): Read volume, the 16th dimension
    "reply_unit_bytes": (REPLY_UNIT_BYTES, REPLY_UNIT_BYTES),  # AI-8
    "reply_window_s": (REPLY_WINDOW_S, REPLY_WINDOW_S),  # AI-8
    "scored_methods": ((CALL_METHOD,), V5_SCORED_METHODS),  # AI-10
}
#: The v5 fields whose v5 default is computed from ``alert_alpha`` and the multiplier bounds.
DERIVED_FIELDS = frozenset(n for n, (_, modern) in DESIGN_VALUES.items() if modern == DERIVED)
#: v5 fields any design may set away from its v1-v4 value (the rest are v5-only switches).
#: B10's platform networks are design-independent: a v4 route may list them too.
ALL_DESIGN_FIELDS = frozenset(
    {"legacy_fixes", "max_multiplier", "min_multiplier", "alert_line", "shared_networks"}
)
#: The spec's other candidate value of a switch (section 4.4, in parentheses) where it
#: differs from the v1-v4 value: D3's preregistered fallback (b) and the tune candidates.
#: :func:`v5_switches_off` never reaches these; an ablation arm sets them explicitly.
SPEC_ALTERNATIVES: dict[str, object] = {
    "footprint_alerts": False,  # FP-1, D3 (b): Footprint watch-only
    "record_hold_days": 30,  # HOLD
    "leave_top_identity_out": True,  # TOP
    "record_reference": "established",  # EST
    "reference_scope": "gateway",  # GWR
}
CHOICES = {
    "calibration": ("max", "commonness"),
    "record_reference": ("all", "established"),
    "reference_scope": ("route", "gateway"),
    "asset_identity": ("driver", "target"),
    "tool_key": ("name", "operation"),
    "client_source": (CLIENT_INFO, APP_CLIENT),
}
#: Range checks of the v5 fields that are not choices, applied when the value is not None.
POSITIVE_INTS = (
    "route_warmup_days",
    "surge_min",
    "record_hold_days",
    "max_sessions_per_caller",
    "org_new_days",
    "established_days",
    "max_history_days",
    "max_values_per_kind",
    "reply_unit_bytes",
)
POSITIVE_DURATIONS = (
    "sequence_window_s",
    "requires_window_s",
    "idle_gap_s",
    "session_ttl_s",
    "reply_window_s",
    "score_budget_ms",
)
OPEN_UNIT_RATES = ("usual_quantile", "watch_floor_rate", "alert_floor_rate")  # in (0, 1)
SWITCHES = tuple(n for n, (legacy, _) in DESIGN_VALUES.items() if isinstance(legacy, bool))
SHARE_GROUPS = 3
FLOOR_KINDS = 2
SHARE_TOLERANCE = 1e-9
ALERT_LINE_TOLERANCE = 1e-12  # an explicit alert line must equal its derivation this closely
CIDR_PAIR = 2  # a shared network is a (label, CIDR) pair


@dataclass(frozen=True)
class BehaviourConfig:
    """Every knob of the behaviour multiplier; the defaults are the simulated design.

    The fields after ``requires_before`` were added for v5. Each starts as
    :data:`DESIGN_DEFAULT` and ``__post_init__`` sets it to its design's value
    (:data:`DESIGN_VALUES`): for v1-v4 the value that keeps today's behaviour, for v5 the
    spec's default. After construction every field holds a plain value. A v5-only switch
    given a value other than its v1-v4 one on a v1-v4 config is an error.

    On v5, ``alert_line`` and ``alert_floor_rate`` follow ``alert_alpha`` (CAL-5: an alert,
    q <= alpha, is the same event as M >= M_alpha). Given explicitly they must equal that
    derivation, so ``dataclasses.replace(config, alert_alpha=...)`` fails fast instead of
    keeping a stale line: change alpha or the multiplier bounds with :func:`replace_config`
    (or :func:`with_alert_alpha`), which derives both again. Note also that
    ``dataclasses.replace(config, design="v5")`` keeps ``config``'s resolved values: build a
    v5 config with ``BehaviourConfig(design="v5", ...)``.
    """

    design: str = V4
    history_days: int = 90
    warmup_calls: int = 5  # until an agent has made this many tool calls, M = 1
    tolerance: float = 2.0  # up to twice his usual (or every other day) is ordinary
    call_unit: float = 1.0
    minute_unit: float = 1.0
    byte_unit: float = 1_000.0  # v1: requests under ~1 KB never matter
    tool_ceiling: float = 0.9  # a rare tool tops out near x3.6
    origin_ceiling: float = 0.9  # v4: so does a rare network or client app
    rule_score: float = 0.9  # x3.6
    protocol_skip_score: float = 0.7  # x1.9
    burst_per_minute: int = 20
    request_limit_bytes: int = 10_000
    #: v3: tool -> its own request limit (learned); other tools use ``request_limit_bytes``
    request_limit_by_tool: dict[str, int] = field(default_factory=dict)
    many_assets_per_hour: int | None = None  # v3: more distinct assets in an hour is a rule
    same_call_window_s: float = SAME_CALL_WINDOW_S  # v3
    ipv4_prefix: int = 16  # a "new network" is a new /16, not a new address
    ipv6_prefix: int = 48
    sensitive_level: int = 4  # asset sensitivity at or above which reads and writes are watched
    sensitive_step: float = 0.1  # v3: a first look scores 0.1 less per sensitivity level below 5
    read_memory_days: int = 7  # a write to a sensitive asset not read in this long is blind
    normally_initializes_after: int = 3  # sessions seen before "he normally initializes" counts
    onboarding_days: int = 14  # v3: first uses in his first days are not "something new"
    org_discount_agents: int = 3  # v3: this many others starting the same thing: org-wide
    org_discount_days: int = 7
    weekend_prior_days: float = 4.0  # v3: a weekend borrows this many days of his all-days profile
    max_sessions: int = 50_000  # open sessions remembered across all agents (oldest dropped)
    #: tool -> tools one of which must come earlier in the session (e.g. merge after a review)
    requires_before: dict[str, frozenset[str]] = field(default_factory=dict)
    # ── v5 (spec 4.1, 4.4); the values are in DESIGN_VALUES ──────────────────────────────
    legacy_fixes: bool = DESIGN_DEFAULT  # E1, E2, RF9
    max_multiplier: float = DESIGN_DEFAULT  # EV-21: the top of M
    min_multiplier: float = DESIGN_DEFAULT  # EV-21, PS8: the bottom of M
    alert_alpha: float | None = DESIGN_DEFAULT  # CAL-5: the alert line as a commonness
    alert_line: float = DESIGN_DEFAULT  # PS6: an alert is M at or above this (reporting only)
    calibration: str = DESIGN_DEFAULT  # CAL-1: "max" (v4) or "commonness"
    record_rank: bool = DESIGN_DEFAULT  # CAL-2
    budget_shares: tuple[float, float, float] | None = DESIGN_DEFAULT  # CAL-3
    watch_cap: float | None = DESIGN_DEFAULT  # CAL-3
    alert_floor_rate: float | None = DESIGN_DEFAULT  # CAL-4
    watch_floor_rate: float | None = DESIGN_DEFAULT  # CAL-4
    floor_budget: tuple[float, float] | None = DESIGN_DEFAULT  # CAL-4
    route_warmup_days: int | None = DESIGN_DEFAULT  # CAL-4
    surge_min: int | None = DESIGN_DEFAULT  # CAL-6
    surge_factor: float | None = DESIGN_DEFAULT  # CAL-6
    #: CAL-7, B9: the IANA zone of the route clock. A route's ``Upstream.route_zone`` (the
    #: routes file), when set, overrides it: the route's scorer applies it with
    #: :func:`replace_config`.
    route_zone: str = DESIGN_DEFAULT
    day_start_hour: float = DESIGN_DEFAULT  # CAL-7, B9: local hour a day starts
    footprint_alerts: bool = DESIGN_DEFAULT  # FP-1 (D3)
    record_hold_days: int | None = DESIGN_DEFAULT  # tune HOLD
    leave_top_identity_out: bool = DESIGN_DEFAULT  # tune TOP
    record_reference: str = DESIGN_DEFAULT  # tune EST: "all" or "established"
    reference_scope: str = DESIGN_DEFAULT  # tune GWR: "route" or "gateway"
    sequence_record: bool = DESIGN_DEFAULT  # SEQ-1
    copy_floor: bool = DESIGN_DEFAULT  # SEQ-2
    sequence_window_s: float | None = DESIGN_DEFAULT  # E5
    requires_window_s: float | None = DESIGN_DEFAULT  # E5
    requires_same_asset: bool = DESIGN_DEFAULT  # E5
    idle_gap_s: float | None = DESIGN_DEFAULT  # E4
    handshake_legacy_sessionless: bool = DESIGN_DEFAULT  # E6
    max_sessions_per_caller: int | None = DESIGN_DEFAULT  # E8
    session_ttl_s: float | None = DESIGN_DEFAULT  # E8
    origin_from_calls_only: bool = DESIGN_DEFAULT  # E12
    missing_client_counts: bool = DESIGN_DEFAULT  # E11
    client_source: str = DESIGN_DEFAULT  # B2: CLIENT_INFO or APP_CLIENT
    request_limit_pooled: bool = DESIGN_DEFAULT  # RF1
    org_new_days: int | None = DESIGN_DEFAULT  # RF7
    org_discount_reads_only: bool = DESIGN_DEFAULT  # RF7
    org_discount_max_static: int | None = DESIGN_DEFAULT  # RF7
    established_days: int | None = DESIGN_DEFAULT  # RF7, RF11
    habit_after_established: bool = DESIGN_DEFAULT  # RF11
    max_history_days: int | None = DESIGN_DEFAULT  # B5
    usual_quantile: float | None = DESIGN_DEFAULT  # B7
    local_day: bool = DESIGN_DEFAULT  # B9
    weekend_days: tuple[int, ...] = DESIGN_DEFAULT  # B9: Monday = 0
    shared_networks: tuple[tuple[str, str], ...] = DESIGN_DEFAULT  # B10: (label, CIDR) pairs
    max_values_per_kind: int | None = DESIGN_DEFAULT  # DEP-7
    score_budget_ms: float | None = DESIGN_DEFAULT  # DEP-7
    asset_identity: str = DESIGN_DEFAULT  # AI-2: "driver" or "target"
    tool_key: str = DESIGN_DEFAULT  # AI-7: "name" or "operation"
    multi_asset_breadth: bool = DESIGN_DEFAULT  # AI-12
    reply_volume: bool = DESIGN_DEFAULT  # AI-8: Read volume
    reply_unit_bytes: int = DESIGN_DEFAULT  # AI-8
    reply_window_s: float = DESIGN_DEFAULT  # AI-8
    scored_methods: tuple[str, ...] = DESIGN_DEFAULT  # AI-10

    def __post_init__(self) -> None:
        if self.design not in DESIGNS:
            raise ValueError(f"design must be one of {DESIGNS}, not {self.design!r}")
        v5 = self.design == V5
        given: set[str] = set()  # the v5 fields given explicitly
        for name, (legacy, modern) in DESIGN_VALUES.items():
            value = getattr(self, name)
            if value is DESIGN_DEFAULT:
                value = (self._derived(name) if modern == DERIVED else modern) if v5 else legacy
            else:
                given.add(name)
                if isinstance(value, list):  # read back from JSON
                    value = _tuples(value)
            object.__setattr__(self, name, value)
            if not v5 and name not in ALL_DESIGN_FIELDS and value != legacy:
                raise ValueError(
                    f"{name} is a v5 switch: design {self.design} keeps {legacy!r}, not {value!r}"
                )
        if v5:
            self._check_derived(given & DERIVED_FIELDS)
        self._check_v5_fields()

    def _derived(self, name: str) -> float | None:
        """A v5 default computed from fields resolved before it."""
        if name == "alert_floor_rate":
            return self.alert_alpha
        if self.alert_alpha is None:  # alert_line with no alpha: v4's line
            return ALERT_LINE
        if not 0 < self.alert_alpha < 1:
            raise ValueError(f"alert_alpha must be in (0, 1), not {self.alert_alpha!r}")
        return alert_multiplier(self.alert_alpha, self.max_multiplier, self.min_multiplier)

    def derived_value(self, name: str) -> float | None:
        """What a derived field (:data:`DERIVED_FIELDS`) holds when not given explicitly."""
        if name not in DERIVED_FIELDS:
            raise ValueError(f"{name} is not a derived field: {sorted(DERIVED_FIELDS)}")
        return self._derived(name)

    def _check_derived(self, given: set[str]) -> None:
        """v5: an explicit alert line or alert floor rate must equal its derivation from
        ``alert_alpha`` (free only when there is no alpha)."""
        if self.alert_alpha is None:
            return
        for name in sorted(given):
            value, derived = getattr(self, name), self._derived(name)
            if value is None or not math.isclose(
                value, derived, rel_tol=0.0, abs_tol=ALERT_LINE_TOLERANCE
            ):
                raise ValueError(
                    f"{name} follows alert_alpha={self.alert_alpha!r} on v5 ({derived!r}), "
                    f"not {value!r}: change alpha or the bounds with replace_config"
                )

    def _check_v5_fields(self) -> None:
        """Fail fast on a v5 field outside its range (a field at None is switched off)."""
        for name, allowed in CHOICES.items():
            if getattr(self, name) not in allowed:
                raise ValueError(f"{name} must be one of {allowed}, not {getattr(self, name)!r}")
        for name in SWITCHES:
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"{name} must be True or False, not {getattr(self, name)!r}")
        for name in POSITIVE_INTS:
            value = getattr(self, name)
            if value is not None and (_not_int(value) or value <= 0):
                raise ValueError(f"{name} must be a positive integer or None, not {value!r}")
        for name in POSITIVE_DURATIONS:
            value = getattr(self, name)
            if value is not None and not (_is_number(value) and value > 0):
                raise ValueError(f"{name} must be positive or None, not {value!r}")
        for name in OPEN_UNIT_RATES:
            value = getattr(self, name)
            if value is not None and not (_is_number(value) and 0 < value < 1):
                raise ValueError(f"{name} must be in (0, 1) or None, not {value!r}")
        if not 0 < self.min_multiplier <= 1 <= self.max_multiplier:
            raise ValueError("multiplier bounds need 0 < min_multiplier <= 1 <= max_multiplier")
        if self.alert_alpha is not None and not 0 < self.alert_alpha < 1:
            raise ValueError(f"alert_alpha must be in (0, 1), not {self.alert_alpha!r}")
        if not (_is_number(self.alert_line) and self.alert_line >= self.min_multiplier):
            raise ValueError(f"alert_line must be at least min_multiplier: {self.alert_line!r}")
        if self.watch_cap is not None and not 0 < self.watch_cap <= 1:
            raise ValueError(f"watch_cap must be in (0, 1], not {self.watch_cap!r}")
        if self.surge_factor is not None and not self.surge_factor >= 1:
            raise ValueError(f"surge_factor must be at least 1, not {self.surge_factor!r}")
        static = self.org_discount_max_static
        if static is not None and not MIN_STATIC_LEVEL <= static <= MAX_STATIC_LEVEL:
            raise ValueError(f"org_discount_max_static must be a static level 1-5: {static!r}")
        shares = self.budget_shares
        if shares is not None and (
            len(shares) != SHARE_GROUPS or min(shares) < 0 or sum(shares) > 1 + SHARE_TOLERANCE
        ):
            raise ValueError(f"budget_shares must be 3 shares summing to at most 1: {shares!r}")
        if self.floor_budget is not None and (
            len(self.floor_budget) != FLOOR_KINDS
            or not all(0 < rate < 1 for rate in self.floor_budget)
        ):
            raise ValueError(f"floor_budget must be 2 rates in (0, 1): {self.floor_budget!r}")
        if not set(self.weekend_days) <= set(range(DAYS_PER_WEEK)):
            raise ValueError(f"weekend_days must be weekdays 0-6: {self.weekend_days!r}")
        if not self.scored_methods or not set(self.scored_methods) <= set(V5_SCORED_METHODS):
            raise ValueError(
                f"scored_methods must be some of {V5_SCORED_METHODS}: {self.scored_methods!r}"
            )
        _check_shared_networks(self.shared_networks)
        check_day_start(self.day_start_hour)
        # v1-v4 never read the zone (pinned to UTC): looking it up there would make every
        # config need the IANA database, which a minimal host may lack
        if self.design == V5 or self.route_zone != DEFAULT_ZONE:
            zone(self.route_zone)  # ValueError for an unknown zone


def _tuples(value: object) -> object:
    """A JSON list, nested lists included, back to the tuples it was saved from."""
    return tuple(_tuples(v) for v in value) if isinstance(value, list) else value


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _not_int(value: object) -> bool:
    return not isinstance(value, int) or isinstance(value, bool)


def _check_shared_networks(pairs: tuple[tuple[str, str], ...]) -> None:
    """B10: each shared network is a (platform label, CIDR) pair; ``ValueError`` if not."""
    for pair in pairs:
        if not (
            isinstance(pair, tuple)
            and len(pair) == CIDR_PAIR
            and all(isinstance(part, str) and part for part in pair)
        ):
            raise ValueError(f"shared_networks holds (label, CIDR) pairs, not {pair!r}")
        try:
            ip_network(pair[1])
        except ValueError as exc:
            raise ValueError(f"shared network {pair[0]!r}: bad CIDR {pair[1]!r}") from exc


def replace_config(config: BehaviourConfig, **changes: object) -> BehaviourConfig:
    """``dataclasses.replace`` for a behaviour config: on v5 the derived fields
    (``alert_line``, ``alert_floor_rate``) are derived again from the new ``alert_alpha`` and
    bounds, unless ``changes`` sets them. Use it for sweeps (EV-21) and for a route's zone."""
    if config.design == V5:
        changes = {name: DESIGN_DEFAULT for name in DERIVED_FIELDS} | changes
    return replace(config, **changes)


def with_alert_alpha(config: BehaviourConfig, alpha: float | None) -> BehaviourConfig:
    """``config`` (v5) at another alert line: alpha, the alert multiplier and the alert floor's
    rate move together (2.5% -> x4.29, 5% -> x3.73)."""
    return replace_config(config, alert_alpha=alpha)


def v5_switches_off(**overrides: object) -> BehaviourConfig:
    """Design v5 with every v5 field at its v1-v4 value (its "off" value): the start of an
    ablation. Until the v5 bodies exist it gives exactly v4's verdicts. The derived fields
    are left to follow ``alert_alpha`` (off: None, so v4's x3 line and no floor rate), and
    the spec's other candidate values (:data:`SPEC_ALTERNATIVES`) are never set here."""
    values = {name: legacy for name, (legacy, modern) in DESIGN_VALUES.items() if modern != DERIVED}
    return BehaviourConfig(design=V5, **(values | overrides))


#: CAL-3: the dimensions that only order the list and can never alert alone (E6).
WATCH_ONLY = frozenset({PROTOCOL_SKIP})


def alerting_dimensions(config: BehaviourConfig) -> dict[str, tuple[str, ...]]:
    """The config's dimensions that can alert, by group (CAL-3): its design's groups without
    the watch-only ones (:data:`WATCH_ONLY`), without Read volume when ``reply_volume`` is
    off, and with Typical Footprint empty when ``footprint_alerts`` is off (FP-1, D3 (b))."""
    out = {}
    for group, dims in dimension_groups(config.design).items():
        kept = tuple(
            d for d in dims if d not in WATCH_ONLY and (d != READ_VOLUME or config.reply_volume)
        )
        out[group] = () if group == TYPICAL_FOOTPRINT and not config.footprint_alerts else kept
    return out


def budget_share(config: BehaviourConfig, dimension: str) -> float | None:
    """A dimension's budget share w_d (CAL-3): its group's share split equally among the
    group's alerting dimensions (v5 defaults: 1/21 Cadence, 1/12 Footprint and Red Flags).
    None for a dimension that takes part but cannot alert (watch-only). ``ValueError`` for a
    config without budget shares, or a dimension the config does not score."""
    if config.budget_shares is None:
        raise ValueError(f"design {config.design} with budget_shares=None has no shares (CAL-3)")
    groups = dimension_groups(config.design)
    for index, (group, dims) in enumerate(groups.items()):
        if dimension not in dims or (dimension == READ_VOLUME and not config.reply_volume):
            continue
        alerting = alerting_dimensions(config)[group]
        if dimension not in alerting:
            return None
        return config.budget_shares[index] / len(alerting)
    raise ValueError(f"design {config.design} does not score {dimension!r} with this config")


@dataclass(frozen=True)
class Message:
    """What the gateway knows about one request message, without reading its arguments."""

    ts: float
    agent: str
    method: str
    session: str | None = None
    tool: str | None = None
    asset: str | None = None  # the asset the call resolves to (the static side's binding)
    sensitivity: int | None = None  # that asset's sensitivity 1-5 (static scan)
    operation: str | None = None  # "read" or "write" (static scan)
    address: str | None = None
    client: str | None = None  # "name/version" from initialize or _meta
    size: int = 0  # bytes of the message
    # ── v5 inputs (spec 2.1); v1-v4 never read them ─────────────────────────────────────
    era: str | None = None  # E3: LEGACY_ERA or MODERN_ERA
    app: str | None = None  # B2: the authenticated application (the token's client)
    client_family: str | None = None  # B2, E11: clientInfo's name, or "(none)"
    zone: str | None = None  # B9: the caller's IANA zone; None = the route's
    more_assets: tuple[str, ...] = ()  # AI-12: further containers the call names
    exposure: str | None = None  # EXP-1: PUBLIC, INTERNAL or PRIVATE
    static: float | None = None  # RF7: the call's static level R_static, 1-5
    arg_bytes: int | None = None  # ARG-1: bytes of params.arguments (era-free)
    logical_call: str | None = None  # ARG-1: continuations and retries share this key
    outcome: str | None = None  # ARG-1: ACCEPTED or REJECTED by the server
    owner: str | None = None  # EXP-1, SEQ-2: the asset's owner (pseudonymised); None: unknown


@dataclass(frozen=True)
class Verdict:
    """The behaviour multiplier for one message, and why.

    The first five fields are every design's. ``alert``, ``runner_up`` and
    ``runner_up_dimension`` (PS6) are set for every design: an alert is ``multiplier`` at or
    above the config's ``alert_line``; the runner-up is the second-largest score and its
    dimension (None when fewer than two took part). The rest are v5's (spec 2.4) and stay
    empty for v1-v4: the commonness ``rate`` (q) and per-dimension ``rates``, the runner-up's
    rate, the ``floors`` that fired, the dimensions that set a ``records``, and ``notes``
    such as a surge or an unscored call.
    """

    multiplier: float
    strongest: str | None  # the dimension that set it; None when nothing took part
    score: float | None  # that dimension's score (S)
    scores: dict[str, float]  # every dimension that took part
    learning: bool  # still in warm-up: only rules that need none of his past take part
    alert: bool = False  # PS6
    runner_up: float | None = None  # PS6: s2
    runner_up_dimension: str | None = None  # PS6
    floors: tuple[str, ...] = ()  # v5: CAL-4, SEQ-2
    rate: float | None = None  # v5: q
    rates: dict[str, float] = field(default_factory=dict)  # v5: q_d
    runner_up_rate: float | None = None  # v5: q2
    records: tuple[str, ...] = ()  # v5: CAL-2
    notes: tuple[str, ...] = ()  # v5: e.g. flag_surge, unscored

    @property
    def above_ordinary(self) -> list[str]:
        """Dimensions past the edge of ordinary, strongest first (a tie-breaker for ranking)."""
        hot = [(s, d) for d, s in self.scores.items() if s > EDGE_OF_ORDINARY]
        return [d for _, d in sorted(hot, reverse=True)]


@dataclass(frozen=True)
class Reply:
    """What the gateway knows about one reply to a scored call (AI-8, Read volume)."""

    ts: float
    agent: str
    method: str | None = None  # the method of the request it answers
    tool: str | None = None
    size: int = 0  # bytes of result.content (ARG-1)


#: Called once with each request message and its verdict once the engine has learned from
#: it, and once with each reply and its reply verdict (EV-03).
Trace = Callable[[Message | Reply, Verdict], None]


def multiplier(score: float, top: float = MAX_MULTIPLIER, bottom: float = MIN_MULTIPLIER) -> float:
    """The curve from a score in [0, 1] to a multiplier in [bottom, top]; exactly 1 at 0.5.
    The defaults are v1-v4's [0.7, 5] (EV-21 moves the bounds into the config)."""
    if score >= EDGE_OF_ORDINARY:
        return top ** (2 * score - 1)
    return bottom ** (1 - 2 * score)


def alert_multiplier(
    alpha: float, top: float = MAX_MULTIPLIER, bottom: float = V5_MIN_MULTIPLIER
) -> float:
    """v5's alert line as a multiplier, M_alpha = max(bottom, g(1 / (1 + 2 alpha))), so an
    alert (commonness q <= alpha) is the same event as M >= M_alpha: x4.69 at 1% (CAL-5)."""
    return max(bottom, multiplier(1 / (1 + 2 * alpha), top, MIN_MULTIPLIER))


def network_of(address: str | None, config: BehaviourConfig) -> str | None:
    """The address's network (IPv4 /16, IPv6 /48 by default); the raw text if not an IP."""
    if not address:
        return None
    try:
        ip = ip_address(address)
    except ValueError:
        return address
    bits = config.ipv4_prefix if ip.version == 4 else config.ipv6_prefix
    width = 32 if ip.version == 4 else 128
    masked = int(ip) >> (width - bits) << (width - bits)
    return f"{type(ip)(masked)}/{bits}"


def client_family(client: str | None) -> str | None:
    """The client program's name without its version: ``cursor/1.4.2`` -> ``cursor``."""
    if not client:
        return None
    family = client.split("/")[0].strip().lower()
    return family or None


@dataclass
class AgentState:
    """One agent's memory: what the dimensions compare him with."""

    calls_last_hour: DailyMean
    session_minutes: DailyMean
    tools: DailyCounts
    assets: DailyCounts
    hours: DailyCounts  # (weekend, hour of day)
    first_day: int = 0  # the day of his first message
    tool_calls: int = 0
    recent: deque = field(default_factory=deque)  # his tool-call times, last hour
    sizes: dict[str, DailyMean] = field(default_factory=dict)  # v1: per tool
    networks: dict[str, int] = field(default_factory=dict)  # value -> last day seen
    clients: dict[str, int] = field(default_factory=dict)
    last_read: dict[str, int] = field(default_factory=dict)  # sensitive asset -> day read
    sessions_seen: int = 0
    sessions_initialized: int = 0
    # v3
    fresh: dict[tuple, int] = field(default_factory=dict)  # new network/client -> day: new all day
    rule_days: dict[str, deque] = field(default_factory=dict)  # habit rule -> days he broke it
    assets_hour: SlidingCounts = field(default_factory=lambda: SlidingCounts(HOUR_S))
    writes_hour: SlidingCounts = field(default_factory=lambda: SlidingCounts(HOUR_S))
    same_calls: SlidingCounts = field(default_factory=lambda: SlidingCounts(SAME_CALL_WINDOW_S))
    window_means: dict[str, DailyMean] = field(default_factory=dict)  # his usual of the windows
    # v4: networks and client apps per day, like tools and assets
    network_counts: DailyCounts = field(default_factory=lambda: DailyCounts(0))
    client_counts: DailyCounts = field(default_factory=lambda: DailyCounts(0))

    @classmethod
    def new(cls, config: BehaviourConfig, first_day: int, daily: bool = False) -> AgentState:
        days = config.history_days
        return cls(
            DailyMean(days, daily),
            DailyMean(days, daily),
            DailyCounts(days, daily),
            DailyCounts(days, daily),
            DailyCounts(days, daily),
            first_day=first_day,
            same_calls=SlidingCounts(config.same_call_window_s),
            network_counts=DailyCounts(days, daily),
            client_counts=DailyCounts(days, daily),
        )


@dataclass
class SessionState:
    start: float
    initialized: bool = False
    counted: bool = False
    tools: set = field(default_factory=set)
    read_sensitive: set = field(default_factory=set)


class BehaviourEngine:
    """Scores messages one at a time, in arrival order, learning from each.

    :meth:`observe` scores a message and learns from it. :meth:`score` gives the same verdict
    without learning, and :meth:`commit` learns from a scored message: v5's gateway scores a
    call before forwarding it and commits it once the server accepted it (ARG-1). For v1-v4
    ``observe`` keeps its own code path, which is exactly ``score`` then ``commit``.

    ``trace`` (EV-03), when given, sees every request and every reply once: each message
    with its verdict after the engine learned from it, and each reply with its reply
    verdict. It never changes a verdict.
    """

    def __init__(self, config: BehaviourConfig | None = None, trace: Trace | None = None) -> None:
        self.config = config or BehaviourConfig()
        design = self.config.design
        self.v2 = design in (V2, V3, V4, V5)  # request size only a rule
        self.v3 = design in (V3, V4, V5)  # everything v3 added; v4 and v5 keep it
        self.v4 = design in (V4, V5)  # "new for him" only in Typical Footprint
        self.v5 = design == V5
        self.trace = trace
        self.agents: dict[str, AgentState] = {}
        self.sessions: OrderedDict[str, SessionState] = OrderedDict()
        self.first_uses = FirstUses(self.config.org_discount_days * DAY_S)

    # ── scoring ──────────────────────────────────────────────────────────────────────────
    def observe(self, message: Message) -> Verdict:
        """The behaviour verdict for one request message; then remember it."""
        if self.v5:
            verdict = self.score(message)
            self.commit(message, verdict)
            return verdict
        verdict = self._observe(message)
        if self.trace is not None:
            self.trace(message, verdict)
        return verdict

    def score(self, message: Message) -> Verdict:
        """The verdict :meth:`observe` would give ``message``, leaving the engine's state as
        it was. Batch 0 scores a private copy of what the message can read or change: its
        caller's history, its session and the org discount's first uses of its values."""
        return self._scratch(message)._observe(message)

    def commit(self, message: Message, verdict: Verdict | None = None) -> None:
        """Learn from ``message``, as :meth:`observe` would after scoring it. ``verdict`` is
        the one :meth:`score` gave; it goes to the trace (v5 will also keep its records).
        Without it the trace gets the verdict the engine computed while learning, which is
        the same one: the message is traced once either way."""
        learned = self._observe(message)
        if self.trace is not None:
            self.trace(message, verdict if verdict is not None else learned)

    def reply(self, reply: Reply) -> Verdict:
        """A reply's bytes, for Read volume (AI-8). Until v5's Read volume is built (Batch 2)
        this learns nothing and gives a neutral verdict for every design. It never raises,
        so the gateway may call it on its live path. The trace sees the reply once."""
        verdict = Verdict(1.0, None, None, {}, learning=False)
        if self.trace is not None:
            self.trace(reply, verdict)
        return verdict

    def fold(self, ts: float) -> dict | None:
        """CAL-7: fold the route's closed days into its references on the route clock, and
        return what the gateway logs as the ``behaviour_fold`` line ({"digests": ...}), or
        None when nothing was folded. Nothing is folded before Batch 3 (K1), and never for
        v1-v4: None."""
        return None

    def _observe(self, message: Message) -> Verdict:
        """Score ``message`` against the state and update the state: v1-v4's ``observe``."""
        today = int(message.ts // DAY_S)
        st = self._agent(message.agent, today)
        session = self._session(message)
        if message.method == INIT_METHOD and session:
            session.initialized = True
        warm = st.tool_calls >= self.config.warmup_calls
        if self.v3:  # learning once a day: nothing to compare with before his first day ends
            warm = warm and today > st.first_day
        scores: dict[str, float] = {}
        self._origin(st, message, today, warm, scores)
        if message.method == CALL_METHOD:
            self._call(st, session, message, today, warm, scores)
        return self._verdict(scores, warm)

    def _verdict(self, scores: dict[str, float], warm: bool) -> Verdict:
        """The strongest dimension sets M; PS6 adds the alert and the runner-up."""
        line = self.config.alert_line
        if not scores:
            return Verdict(1.0, None, None, {}, learning=not warm, alert=1.0 >= line)
        strongest = max(scores, key=lambda d: scores[d])
        top = scores[strongest]
        value = self._multiplier(top)
        second = max((d for d in scores if d != strongest), key=lambda d: scores[d], default=None)
        return Verdict(
            value,
            strongest,
            top,
            scores,
            learning=not warm,
            alert=value >= line,
            runner_up=None if second is None else scores[second],
            runner_up_dimension=second,
        )

    def _multiplier(self, score: float) -> float:
        """M for the strongest score, within the config's bounds (EV-21). v5 keeps the
        curve's 0.7 lower branch and lifts it to ``min_multiplier`` (CAL-5, PS8)."""
        cfg = self.config
        if self.v5:
            return max(cfg.min_multiplier, multiplier(score, cfg.max_multiplier, MIN_MULTIPLIER))
        return multiplier(score, cfg.max_multiplier, cfg.min_multiplier)

    def _scratch(self, m: Message) -> BehaviourEngine:
        """An engine holding copies of the state ``m`` can read or change, for :meth:`score`."""
        scratch = BehaviourEngine(self.config)
        st = self.agents.get(m.agent)
        if st is not None:
            scratch.agents[m.agent] = _private_copy(st)
        key = _session_key(m)
        if key is not None and key in self.sessions:
            scratch.sessions[key] = _private_copy(self.sessions[key])
        scratch.first_uses = self.first_uses.subset(self._first_use_keys(m))
        return scratch

    def _first_use_keys(self, m: Message) -> list[tuple]:
        """The org-discount values ``m`` can add or ask about: its network, client, tool and
        asset."""
        values = (
            ("network", network_of(m.address, self.config)),
            ("client", client_family(m.client)),
            ("tool", m.tool or ""),
            ("asset", m.asset),
        )
        return [(kind, value) for kind, value in values if value is not None]

    def _origin(
        self, st: AgentState, m: Message, today: int, warm: bool, scores: dict[str, float]
    ) -> None:
        """New network (/16) and new client program: rules, on every message (v1-v3)."""
        if self.v4:
            self._origin_footprint(st, m, today, warm, scores)
            return
        cfg = self.config
        for name, kind, value, seen in (
            (NEW_NETWORK, "network", network_of(m.address, cfg), st.networks),
            (NEW_CLIENT, "client", client_family(m.client), st.clients),
        ):
            if value is None:
                continue
            last = seen.get(value)
            new = last is None or last <= today - cfg.history_days
            if self.v3:
                if new:
                    self.first_uses.add((kind, value), m.ts, m.agent)
                    if warm:
                        st.fresh[(kind, value)] = today
                elif st.fresh.get((kind, value)) == today:
                    new = True  # learning once a day: new stays new all day
            if warm and new:
                score = cfg.rule_score
                if self._org_wide(kind, value, m):
                    score = min(score, EDGE_OF_ORDINARY)
                scores[name] = score
            seen[value] = today
        for seen in (st.networks, st.clients):  # forget what has not been seen in 90 days
            if len(seen) > 64:
                for value in [v for v, d in seen.items() if d <= today - cfg.history_days]:
                    del seen[value]
        if len(st.fresh) > 16:
            st.fresh = {k: d for k, d in st.fresh.items() if d == today}

    def _origin_footprint(
        self, st: AgentState, m: Message, today: int, warm: bool, scores: dict[str, float]
    ) -> None:
        """v4: network (/16) and client app in Typical Footprint, rarer than his usual, on
        every message. A dimension takes part once its own history has a day in it (a snapshot
        saved before v4 kept none)."""
        cfg = self.config
        onboarded = today - st.first_day >= cfg.onboarding_days
        for name, kind, value, counts in (
            (NETWORK, "network", network_of(m.address, cfg), st.network_counts),
            (CLIENT, "client", client_family(m.client), st.client_counts),
        ):
            if value is None:
                continue
            counts.expire(today)
            if counts.is_new(value, today):
                self.first_uses.add((kind, value), m.ts, m.agent)
            if warm and counts.active_days(today=today):
                e = counts.per_day([value], True, today=today)
                score = cfg.origin_ceiling / (1 + cfg.tolerance * e)
                if not counts.known(value) and self._org_wide(kind, value, m):
                    score = min(score, EDGE_OF_ORDINARY)
                scores[name] = score
            counts.add(today, value, count_as_new=warm and onboarded)

    def _call(
        self,
        st: AgentState,
        session: SessionState | None,
        m: Message,
        today: int,
        warm: bool,
        scores: dict[str, float],
    ) -> None:
        cfg = self.config
        tool = m.tool or ""
        # counts and sizes: more than his usual
        recent = st.recent
        recent.append(m.ts)
        while recent and recent[0] <= m.ts - HOUR_S:
            recent.popleft()
        usual_hour = st.calls_last_hour.mean_then_add(today, len(recent))
        minutes = (m.ts - session.start) / MINUTE_S if session else 0.0
        usual_session = None
        if session or not cfg.legacy_fixes:  # E2: a sessionless call is no 0-minute session
            usual_session = st.session_minutes.mean_then_add(today, minutes)
        usual_size = None
        if not self.v2:
            sizes = st.sizes.setdefault(tool, DailyMean(cfg.history_days))
            usual_size = sizes.mean_then_add(today, float(m.size))
        for counts in (st.tools, st.assets, st.hours):
            counts.expire(today)
        weekend = is_weekend(today)
        hour = int((m.ts % DAY_S) // HOUR_S)
        around = [(weekend, (hour + k) % 24) for k in (-1, 0, 1)]
        normally_initializes = (
            st.sessions_seen >= cfg.normally_initializes_after
            and 2 * st.sessions_initialized >= st.sessions_seen
        )
        windows: dict[str, tuple[float, float | None]] = {}
        breadth = 0
        if self.v3:
            windows, breadth = self._windows(st, m, tool, today)
            self._note_first_uses(st, m, tool, today)
        if warm:
            for name, (value, usual) in windows.items():
                self._more(scores, name, value, usual, cfg.call_unit)
            self._more(scores, CALLS_LAST_HOUR, len(recent), usual_hour, cfg.call_unit)
            if session:
                self._more(scores, SESSION_LENGTH, minutes, usual_session, cfg.minute_unit)
            if not self.v2:
                self._more(scores, REQUEST_SIZE, m.size, usual_size, cfg.byte_unit)
            if self.v2 and not self.v4 and not st.tools.known(tool):
                score = cfg.rule_score
                if self._org_wide("tool", tool, m):
                    score = min(score, EDGE_OF_ORDINARY)
                scores[NEW_TOOL] = score
            else:  # v4: a tool new for him too, priced by how often he starts new tools
                e = st.tools.per_day([tool], True, today=today)
                score = cfg.tool_ceiling / (1 + cfg.tolerance * e)
                if not st.tools.known(tool) and self._org_wide("tool", tool, m):
                    score = min(score, EDGE_OF_ORDINARY)
                scores[TOOL] = score
            if m.asset:
                e = st.assets.per_day([m.asset], True, today=today)
                score = 1 / (1 + cfg.tolerance * e)
                if not st.assets.known(m.asset) and self._org_wide("asset", m.asset, m):
                    score = min(score, EDGE_OF_ORDINARY)
                scores[ASSET] = score
            e = self._time_of_day(st, around, weekend, today)
            scores[TIME_OF_DAY] = 1 / (1 + cfg.tolerance * e)
        fired: list[tuple[str, float]] = []
        if warm or self.v3:  # v3's warm-up: only the rules that need none of his past
            fired = self._rules(st, session, m, tool, today, warm, breadth, normally_initializes)
            look = self._first_look(st, m)
            if look is not None and self.v4:  # Typical Footprint: a floor on the asset's score
                scores[ASSET] = max(scores.get(ASSET, 0.0), look)
            elif look is not None:
                fired.insert(0, (SENSITIVE_FIRST_LOOK, look))
            for rule, value in fired:
                scores[rule] = self._habit(st, rule, value, today)
        # remember
        onboarded = not self.v3 or today - st.first_day >= cfg.onboarding_days
        st.tools.add(today, tool, count_as_new=warm and onboarded)
        st.hours.add(today, (weekend, hour), count_as_new=False)
        if m.asset:
            st.assets.add(today, m.asset, count_as_new=warm and onboarded)
            if m.operation == READ and (m.sensitivity or 0) >= cfg.sensitive_level:
                st.last_read[m.asset] = today
                if session:
                    session.read_sensitive.add(m.asset)
        if session:
            if not session.counted:
                session.counted = True
                st.sessions_seen += 1
                st.sessions_initialized += int(session.initialized)
            session.tools.add(tool)
        st.tool_calls += 1
        for rule, _ in fired:
            if self.v3 and rule in HABIT_RULES:
                days = st.rule_days.setdefault(rule, deque())
                if not days or days[-1] != today:
                    days.append(today)

    def _rules(
        self,
        st: AgentState,
        session: SessionState | None,
        m: Message,
        tool: str,
        today: int,
        warm: bool,
        breadth: int,
        normally_initializes: bool,
    ) -> list[tuple[str, float]]:
        """The rules this call broke (the Red Flags group), with their values, in a fixed
        order."""
        cfg = self.config
        fired: list[tuple[str, float]] = []
        if self.v3 and cfg.many_assets_per_hour is not None and breadth > cfg.many_assets_per_hour:
            fired.append((MANY_ASSETS, cfg.rule_score))
        if sum(1 for t in st.recent if t > m.ts - MINUTE_S) > cfg.burst_per_minute:
            fired.append((BURST, cfg.rule_score))
        limit = cfg.request_limit_bytes
        if self.v3:
            limit = cfg.request_limit_by_tool.get(tool, limit)
        if m.size > limit:
            fired.append((REQUEST_TOO_BIG, cfg.rule_score))
        if warm and session and not session.initialized and normally_initializes:
            fired.append((PROTOCOL_SKIP, cfg.protocol_skip_score))
        if self._problematic_sequence(st, session, m, tool, today):
            fired.append((SEQUENCE, cfg.rule_score))
        return fired

    def _first_look(self, st: AgentState, m: Message) -> float | None:
        """v3+: a sensitive asset (4-5) he has not touched in 90 days -> 0.9 for sensitivity 5,
        0.1 less a level below; never org-discounted. Needs none of his past."""
        cfg = self.config
        sensitivity = m.sensitivity or 0
        if not (
            self.v3
            and m.asset
            and sensitivity >= cfg.sensitive_level
            and not st.assets.known(m.asset)
        ):
            return None
        value = cfg.rule_score - cfg.sensitive_step * (TOP_SENSITIVITY - sensitivity)
        return min(1.0, value)

    def _habit(self, st: AgentState, rule: str, value: float, today: int) -> float:
        """v3: a habit rule's value, lowered by how often he broke it in 90 days (not today)."""
        if not (self.v3 and rule in HABIT_RULES):
            return value
        days = st.rule_days.get(rule)
        if not days:
            return value
        while days and days[0] <= today - self.config.history_days:
            days.popleft()
        broken = len(days) - int(bool(days) and days[-1] == today)
        e = broken / (st.tools.active_days(today=today) + 1)
        return value / (1 + self.config.tolerance * e)

    def _windows(
        self, st: AgentState, m: Message, tool: str, today: int
    ) -> tuple[dict[str, tuple[float, float | None]], int]:
        """v3: distinct assets and writes in the last hour, the same call in the last 10
        minutes: ``({dimension: (value now, his usual)}, distinct assets now)``."""
        if m.asset:
            st.assets_hour.add(m.ts, m.asset)
        st.assets_hour.expire(m.ts)
        if m.operation == WRITE:
            st.writes_hour.add(m.ts, WRITE)
        st.writes_hour.expire(m.ts)
        key = (tool, m.asset)
        st.same_calls.add(m.ts, key)
        st.same_calls.expire(m.ts)
        now = {
            ASSETS_LAST_HOUR: st.assets_hour.distinct(),
            WRITES_LAST_HOUR: st.writes_hour.total(),
            SAME_CALL_10M: st.same_calls.count(key),
        }
        out = {}
        for name in WINDOW_COUNTS:
            means = st.window_means.get(name)
            if means is None:
                means = st.window_means[name] = DailyMean(self.config.history_days, daily=True)
            out[name] = (now[name], means.mean_then_add(today, now[name]))
        return out, now[ASSETS_LAST_HOUR]

    def _note_first_uses(self, st: AgentState, m: Message, tool: str, today: int) -> None:
        """v3: a tool or asset new for him in 90 days counts toward the org discount."""
        if st.tools.is_new(tool, today):
            self.first_uses.add(("tool", tool), m.ts, m.agent)
        if m.asset and st.assets.is_new(m.asset, today):
            self.first_uses.add(("asset", m.asset), m.ts, m.agent)

    def _org_wide(self, kind: str, value: str, m: Message) -> bool:
        """v3: enough other agents also started this in the last days (an org-wide change)."""
        if not self.v3:
            return False
        cfg = self.config
        # RF9 (legacy_fixes): each other agent counts once, however often his use was recorded
        others = self.first_uses.others((kind, value), m.ts, m.agent, distinct=cfg.legacy_fixes)
        return others >= cfg.org_discount_agents

    def _time_of_day(self, st: AgentState, around: list, weekend: bool, today: int) -> float:
        """``e`` for time of day: v1 and v2 compare a weekend call with his weekend days only;
        v3 blends them with ``weekend_prior_days`` days' worth of his all-days profile."""
        hours = st.hours
        if not self.v3:
            return hours.per_day(around, False, weekend)
        prior = self.config.weekend_prior_days
        pooled = around + [(not weekend, h) for _, h in around]
        e_all = hours.per_day(pooled, False, None, today)
        return (hours.count(around) + prior * e_all) / (hours.active_days(weekend, today) + prior)

    def _problematic_sequence(
        self, st: AgentState, session: SessionState | None, m: Message, tool: str, today: int
    ) -> bool:
        cfg = self.config
        needed = cfg.requires_before.get(tool)
        # E1 (legacy_fixes): with no session the required step cannot be checked, so a
        # sessionless call is "not evaluable" here rather than raised
        evaluable = session is not None or not cfg.legacy_fixes
        if needed and evaluable and not (session and session.tools & needed):
            return True  # e.g. a merge with no review earlier in the session
        if m.operation != WRITE or not m.asset:
            return False
        if session and session.read_sensitive - {m.asset}:
            return True  # a write after reading a different sensitive asset
        sensitive = (m.sensitivity or 0) >= cfg.sensitive_level
        last = st.last_read.get(m.asset)
        return sensitive and (last is None or last < today - cfg.read_memory_days)

    def _more(
        self, scores: dict[str, float], name: str, value: float, usual: float | None, unit: float
    ) -> None:
        if usual is None:
            return  # no history for this yet: the dimension does not take part
        scores[name] = (value + unit) / (value + unit + self.config.tolerance * (usual + unit))

    def _agent(self, agent: str, today: int) -> AgentState:
        st = self.agents.get(agent)
        if st is None:
            st = self.agents[agent] = AgentState.new(self.config, today, daily=self.v3)
        return st

    def _session(self, m: Message) -> SessionState | None:
        key = _session_key(m)
        if key is None:
            return None
        session = self.sessions.get(key)
        if session is None:
            session = self.sessions[key] = SessionState(start=m.ts)
            if len(self.sessions) > self.config.max_sessions:
                self.sessions.popitem(last=False)
        else:
            self.sessions.move_to_end(key)
        return session

    # ── state that survives a restart ───────────────────────────────────────────────────
    def snapshot(self) -> dict:
        """Everything the engine has learned, as JSON-safe data (open sessions excluded)."""
        return {
            "design": self.config.design,
            "agents": {a: _agent_json(st) for a, st in self.agents.items()},
            "first_uses": self.first_uses.to_json(),
        }

    def restore(self, data: dict) -> None:
        """Load :meth:`snapshot` output, so a restart continues where it stopped. A snapshot
        of another design loads too: its per-day history is the same data."""
        days, daily = self.config.history_days, self.v3
        for agent, d in data.get("agents", {}).items():
            st = AgentState(
                tool_calls=d["tool_calls"],
                recent=deque(d["recent"]),
                calls_last_hour=DailyMean.from_json(days, d["calls_last_hour"], daily),
                session_minutes=DailyMean.from_json(days, d["session_minutes"], daily),
                sizes={t: DailyMean.from_json(days, v) for t, v in d.get("sizes", {}).items()},
                tools=DailyCounts.from_json(days, d["tools"], daily),
                assets=DailyCounts.from_json(days, d["assets"], daily),
                hours=DailyCounts.from_json(days, d["hours"], daily),
                networks=dict(d["networks"]),
                clients=dict(d["clients"]),
                last_read=dict(d["last_read"]),
                sessions_seen=d["sessions_seen"],
                sessions_initialized=d["sessions_initialized"],
                fresh={as_key(k): v for k, v in d.get("fresh", [])},
                rule_days={r: deque(v) for r, v in d.get("rule_days", {}).items()},
                assets_hour=SlidingCounts.from_json(HOUR_S, d.get("assets_hour", [])),
                writes_hour=SlidingCounts.from_json(HOUR_S, d.get("writes_hour", [])),
                same_calls=SlidingCounts.from_json(
                    self.config.same_call_window_s, d.get("same_calls", [])
                ),
                window_means={
                    n: DailyMean.from_json(days, v, daily=True)
                    for n, v in d.get("window_means", {}).items()
                },
                first_day=d["first_day"] if "first_day" in d else _first_day(d),
                network_counts=_counts(days, d.get("network_counts"), daily),
                client_counts=_counts(days, d.get("client_counts"), daily),
            )
            self.agents[agent] = st
        self.first_uses = FirstUses.from_json(
            self.config.org_discount_days * DAY_S, data.get("first_uses", [])
        )


def _private_copy[T](state: T) -> T:
    """A deep copy of the engine's own in-memory state. A pickle round trip copies these
    plain containers exactly, at a third of ``copy.deepcopy``'s cost; nothing outside the
    process is ever unpickled here."""
    return pickle.loads(pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL))


def _session_key(m: Message) -> str | None:
    """Where an open session is kept: one per (agent, session id); None without a session."""
    if not m.session:
        return None
    return f"{m.agent}\x1f{m.session}"


def _counts(days: int, saved: dict | None, daily: bool) -> DailyCounts:
    """Saved per-day counts back; empty when the snapshot kept none (saved before v4)."""
    if saved is None:
        return DailyCounts(days, daily)
    return DailyCounts.from_json(days, saved, daily)


def _first_day(saved: dict) -> int:
    """An agent saved before v3 kept no first day: the earliest day in what he saved."""
    days = [d for d, *_ in saved["calls_last_hour"]] + list(saved["networks"].values())
    return min(days, default=0)


def _agent_json(st: AgentState) -> dict:
    return {
        "tool_calls": st.tool_calls,
        "first_day": st.first_day,
        "recent": list(st.recent),
        "calls_last_hour": st.calls_last_hour.to_json(),
        "session_minutes": st.session_minutes.to_json(),
        "sizes": {t: m.to_json() for t, m in st.sizes.items()},
        "tools": st.tools.to_json(),
        "assets": st.assets.to_json(),
        "hours": st.hours.to_json(),
        "networks": st.networks,
        "clients": st.clients,
        "last_read": st.last_read,
        "sessions_seen": st.sessions_seen,
        "sessions_initialized": st.sessions_initialized,
        "fresh": [[list(k), d] for k, d in st.fresh.items()],
        "rule_days": {r: list(days) for r, days in st.rule_days.items()},
        "assets_hour": st.assets_hour.to_json(),
        "writes_hour": st.writes_hour.to_json(),
        "same_calls": st.same_calls.to_json(),
        "window_means": {n: m.to_json() for n, m in st.window_means.items()},
        "network_counts": st.network_counts.to_json(),
        "client_counts": st.client_counts.to_json(),
    }
