"""RF5: the realised rate of every flag, floor and dimension against its nominal rate.

A route's :class:`FlagRates` counts agent-days, (caller, local day) pairs, over its trailing
``window_days`` days (30). The caller is the route's baseline key, the agent (spec 2.1, D5):
``Identity.id`` when it signs in, else its self-reported client family and address. For each
*item* it counts the agent-days on which the item fired and reports that realised rate, with a
Wilson interval, next to its ``nominal_rate``:

- ``flag:<key>``: a red flag raised, before any discount. The learned limits (Burst, Sweep,
  Oversized request) promise at most ``policy.LINE_ALPHA`` (0.5%) of agent-days (RF1, RF2).
  Unsafe sequence and Missing handshake have no nominal rate; they are reported only.
- ``floor:<name>``: an alert floor fired at the ALERT level, ``name`` being calibration.py's
  floor name (:data:`FIRST_ACCESS_FLOOR`, :data:`COPY_FLOOR`). Its nominal rate is its budget
  beta (``floor_budget``: 0.30% first access, 0.05% copy). ``floor:`` :data:`WATCH_FLOOR` is a
  first access at the WATCH level (sensitivity 4); it has no budget.
- ``dimension:<key>``: the dimension reached the alert line alone (q_d / w_d <= alpha), which
  is its spend, against w_d * alpha (spec 2.6, step 2). A watch-only dimension's is exactly 0.

**Floor demotion** (spec 2.4, CAL-4). At each fold an alert floor becomes a watch floor when
the upper Wilson bound of its realised rate exceeds its beta, counting only established
callers. Both the firings and the agent-days are those of callers established on that day, so
callers that are not established (Sybils: fresh keys, such as an unsigned agent that changes
its reported name or address) can neither force nor block a demotion. A floor whose bound
falls back to beta is restored. Each change is a :class:`DemotionEvent` to log.
:attr:`FlagRates.demoted_floors` is what ``calibration.apply_floors(demoted=...)`` takes.

The report also gives the rates per protocol era (R3-4), the path activity of every alerting
dimension and the dimensions whose cap condition fails (spec 2.3). The ``flag_surge`` line is
CAL-6's (``calibration.SurgeGuard.notice``); RF5 emits none. Nothing here changes a verdict
except :attr:`FlagRates.demoted_floors`.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field, fields, replace
from statistics import NormalDist
from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple

# calibration.py's floor names (FLOOR_ORDER), re-exported: RF5 counts floors under them
from mcp_security.behaviour.calibration import COPY_FLOOR as COPY_FLOOR
from mcp_security.behaviour.calibration import FIRST_ACCESS_FLOOR as FIRST_ACCESS_FLOOR
from mcp_security.behaviour.calibration import FLOOR_ORDER, floor_budgets, shares_for

if TYPE_CHECKING:  # engine.py imports this module (Batch 3): engine names are imported lazily
    from mcp_security.behaviour.engine import BehaviourConfig

SCHEMA = "flag-rates/1"
RATE_WINDOW_DAYS = 30  # RF5: realised rates over the trailing 30 days
CONFIDENCE = 0.95  # two-sided Wilson interval
HISTORY_DAYS = 90  # the record window: A_d + 1 <= 90 (the cap condition, spec 2.3)
LATE_DAYS = 2  # a caller's local day lags the route's by at most 2 (UTC-12 against UTC+14)
FLAG, FLOOR, DIMENSION = "flag", "floor", "dimension"
KINDS = (FLAG, FLOOR, DIMENSION)
SEPARATOR = ":"
#: The item of a first access at the WATCH level (sensitivity 4). calibration.py names that
#: firing FIRST_ACCESS_FLOOR too, so RF5 gives it its own item: it never counts toward the
#: alert floor's rate.
WATCH_FLOOR = "first_access_watch"
UNKNOWN_ERA = "unknown"  # a call with no protocol era
UPPER, LOWER = "upper", "lower"  # the Wilson bound that must exceed beta to demote
DEMOTE_RULES = (UPPER, LOWER)
OVER, WITHIN, UNCLEAR = "over", "within", "unclear"  # a realised rate against its nominal one
TOLERANCE = 1e-9  # float slack when 1 / (w_d alpha) or history x w_d x alpha is a whole number
PERCENT = 100
_MAPPINGS = ("nominal", "alert_floors", "shares")  # RateSettings' read-only mappings


def item_key(kind: str, name: str) -> str:
    """The item key ``kind:name``; ``ValueError`` for an unknown kind or an empty name."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}, not {kind!r}")
    if not isinstance(name, str) or not name:
        raise ValueError(f"an item needs a name, not {name!r}")
    return f"{kind}{SEPARATOR}{name}"


def flag_item(name: str) -> str:
    """The item of a red flag raised (``name`` is its engine key, e.g. ``burst``)."""
    return item_key(FLAG, name)


def floor_item(name: str) -> str:
    """The item of a floor fired (``name`` is :data:`FIRST_ACCESS_FLOOR`, :data:`COPY_FLOOR`
    at the ALERT level, or :data:`WATCH_FLOOR`)."""
    return item_key(FLOOR, name)


def floor_firings(alert: Iterable[str] = (), watch: Iterable[str] = ()) -> tuple[str, ...]:
    """The items of the floors one call fired, from the floor names the engine passes as
    ``alert`` and ``watch`` to ``calibration.apply_floors``: each alert floor's own item, and
    :data:`WATCH_FLOOR`'s for a first access at the WATCH level. ``ValueError`` for a name that
    is not calibration.py's (an alert name outside ``FLOOR_ORDER``, a watch name other than
    :data:`FIRST_ACCESS_FLOOR`) or a bare string, so a renamed floor fails here and does not
    silently escape demotion."""
    if isinstance(alert, str) or isinstance(watch, str):
        raise ValueError("alert and watch are iterables of floor names, not a string")
    items = []
    for name in alert:
        if name not in FLOOR_ORDER:
            raise ValueError(f"an alert floor is one of {FLOOR_ORDER}, not {name!r}")
        items.append(floor_item(name))
    for name in watch:
        if name != FIRST_ACCESS_FLOOR:
            raise ValueError(f"only {FIRST_ACCESS_FLOOR!r} has a watch level, not {name!r}")
        items.append(floor_item(WATCH_FLOOR))
    return tuple(dict.fromkeys(items))


def dimension_item(name: str) -> str:
    """The item of a dimension that reached the alert line alone (its engine key)."""
    return item_key(DIMENSION, name)


def split_item(key: str) -> tuple[str, str]:
    """(kind, name) of an item key; ``ValueError`` unless it is ``kind:name``."""
    if not isinstance(key, str) or SEPARATOR not in key:
        raise ValueError(f"an item key is kind{SEPARATOR}name, not {key!r}")
    kind, _, name = key.partition(SEPARATOR)
    item_key(kind, name)
    return kind, name


class Interval(NamedTuple):
    """A confidence interval for a rate."""

    lower: float
    upper: float


def wilson_interval(raised: int, days: int, confidence: float = CONFIDENCE) -> Interval:
    """The Wilson score interval of ``raised`` agent-days out of ``days``:
    (k + z^2/2) / (n + z^2) +/- z sqrt(k (n - k) / n + z^2 / 4) / (n + z^2), with z the
    two-sided normal quantile. With no agent-days it is (0, 1). ``ValueError`` unless
    0 <= raised <= days are integers and 0 < confidence < 1."""
    _check_count(raised, days)
    _check_open_unit(confidence, "confidence")
    if days == 0:
        return Interval(0.0, 1.0)
    z = NormalDist().inv_cdf(0.5 + confidence / 2)
    z2 = z * z
    centre = (raised + z2 / 2) / (days + z2)
    half = z * math.sqrt(raised * (days - raised) / days + z2 / 4) / (days + z2)
    lower = 0.0 if raised == 0 else max(0.0, centre - half)
    upper = 1.0 if raised == days else min(1.0, centre + half)
    return Interval(lower, upper)


def rate_status(interval: Interval, nominal: float | None, raised: int | None = None) -> str | None:
    """:data:`OVER` when the interval lies above ``nominal``, :data:`WITHIN` when its upper
    bound does not exceed it, else :data:`UNCLEAR`; None without a nominal rate. A nominal
    rate of 0 (a watch-only dimension) is exact: OVER if anything was ``raised`` (when not
    given, if the lower bound is above 0), else WITHIN."""
    if nominal is None:
        return None
    if nominal == 0:
        fired = interval.lower > 0 if raised is None else raised > 0
        return OVER if fired else WITHIN
    if interval.lower > nominal:
        return OVER
    return WITHIN if interval.upper <= nominal else UNCLEAR


def cap_condition_holds(share: float, alpha: float, history_days: int = HISTORY_DAYS) -> bool:
    """Spec 2.3: the personal part 1 / (A_d + 1) of a record's commonness cannot reach the
    line ``alpha`` when history_days x w_d x alpha < 1, since A_d + 1 <= history_days."""
    return history_days * share * alpha < 1 - TOLERANCE


def broken_caps(
    shares: Mapping[str, float | None], alpha: float, history_days: int = HISTORY_DAYS
) -> tuple[str, ...]:
    """The alerting dimensions in ``shares`` whose cap condition fails at line ``alpha``."""
    _check_open_unit(alpha, "alpha")
    return tuple(
        dim
        for dim, share in shares.items()
        if _alerting(share) and not cap_condition_holds(share, alpha, history_days)
    )


@dataclass(frozen=True)
class PathActivity:
    """Whether a dimension's record path can reach the line ``alpha`` on this route: only if
    N_d + 1 >= 1 / (w_d alpha), N_d being the route's agent-days in the record window on
    which the dimension took part (spec 2.3)."""

    dimension: str
    share: float  # w_d
    alpha: float
    agent_days: int  # N_d
    needed: int  # the least N_d + 1 that lets the path reach alpha: ceil(1 / (w_d alpha))
    active: bool
    cap_holds: bool  # see cap_condition_holds

    @property
    def message(self) -> str:
        """``"<dimension>: path inactive at the 1% line (...)"``, or that it is active."""
        line = f"the {self.alpha * PERCENT:g}% line"
        if self.active:
            return f"{self.dimension}: path active at {line}"
        return (
            f"{self.dimension}: path inactive at {line} "
            f"(N_d + 1 = {self.agent_days + 1} < {self.needed})"
        )


def path_activity(
    agent_days: Mapping[str, int],
    shares: Mapping[str, float | None],
    alpha: float,
    history_days: int = HISTORY_DAYS,
) -> tuple[PathActivity, ...]:
    """The path activity of every dimension in ``shares`` that can alert (a share above 0,
    not None), in ``shares``' order. A dimension missing from ``agent_days`` has N_d = 0."""
    _check_open_unit(alpha, "alpha")
    out = []
    for dimension, share in shares.items():
        if not _alerting(share):
            continue
        n = agent_days.get(dimension, 0)
        _check_count(n, n)
        needed = math.ceil(1 / (share * alpha) - TOLERANCE)
        cap = cap_condition_holds(share, alpha, history_days)
        out.append(PathActivity(dimension, share, alpha, n, needed, n + 1 >= needed, cap))
    return tuple(out)


@dataclass(frozen=True)
class ItemRate:
    """One item's realised rate over the window: over every caller, and over established
    callers only (the demotion's count), with Wilson bounds and the status against its
    nominal rate (over every caller)."""

    item: str
    nominal_rate: float | None
    raised: int
    agent_days: int
    lower: float
    upper: float
    established_raised: int
    established_days: int
    established_lower: float
    established_upper: float
    status: str | None

    @property
    def rate(self) -> float | None:
        """raised / agent_days; None with no agent-days."""
        return self.raised / self.agent_days if self.agent_days else None


@dataclass(frozen=True)
class EraRate:
    """One item's realised rate among the agent-days with a call in one protocol era."""

    era: str
    item: str
    raised: int
    agent_days: int
    lower: float
    upper: float

    @property
    def rate(self) -> float | None:
        """raised / agent_days; None with no agent-days."""
        return self.raised / self.agent_days if self.agent_days else None


@dataclass(frozen=True)
class DemotionEvent:
    """An alert floor demoted to a watch floor (``demoted``) or restored, at a fold."""

    floor: str
    day: int  # the route day folded
    demoted: bool
    raised: int  # established callers' agent-days with the floor fired, in the window
    agent_days: int  # established callers' agent-days in the window
    bound: float  # the Wilson bound compared with beta
    beta: float
    rule: str  # UPPER or LOWER: which bound

    def fields(self) -> dict:
        """The fields of its log line."""
        return asdict(self)


@dataclass(frozen=True)
class RateReport:
    """Every item's realised rate over the days [day - window_days, day - 1]."""

    day: int
    window_days: int
    agent_days: int
    established_days: int
    rates: tuple[ItemRate, ...]
    eras: tuple[EraRate, ...]
    paths: tuple[PathActivity, ...]  # empty unless the route's N_d were given
    demoted: tuple[str, ...]  # the alert floors demoted after this report
    demotions: tuple[DemotionEvent, ...] = ()  # the changes this fold made
    broken_caps: tuple[str, ...] = ()  # alerting dimensions whose cap condition fails

    @property
    def inactive_paths(self) -> tuple[PathActivity, ...]:
        """The dimensions whose path cannot reach the line on this route."""
        return tuple(p for p in self.paths if not p.active)

    def to_json(self) -> dict:
        """The report as plain JSON values (for the ``behaviour_fold`` line or a file)."""
        out = asdict(self)
        out["paths"] = [asdict(p) | {"message": p.message} for p in self.paths]
        return out


def format_report(report: RateReport) -> str:
    """A plain-text table of the report, for the offline re-score to print."""
    lines = [
        f"realised rates, days {report.day - report.window_days}..{report.day - 1}: "
        f"{report.agent_days} agent-days ({report.established_days} established)"
    ]
    for r in report.rates:
        nominal = "-" if r.nominal_rate is None else f"{r.nominal_rate:.4%}"
        rate = "-" if r.rate is None else f"{r.rate:.4%}"
        lines.append(
            f"  {r.item:32} {r.raised:>7}/{r.agent_days:<8} {rate:>9} "
            f"[{r.lower:.4%}, {r.upper:.4%}] nominal {nominal:>8} {r.status or ''}"
        )
    lines += [f"  {p.message}" for p in report.inactive_paths]
    lines += [
        f"  {dim}: cap condition broken (the personal part can reach the line)"
        for dim in report.broken_caps
    ]
    lines += [f"  demoted to a watch floor: {floor}" for floor in report.demoted]
    return "\n".join(lines)


def config_shares(config: BehaviourConfig) -> dict[str, float | None]:
    """Every dimension the config scores, with its budget share w_d, in design order
    (``calibration.shares_for``); empty without budget shares (v1-v4). A watch-only
    dimension's share is None, and so is a share of 0 (its group's budget switched off),
    which ``calibration.combine`` treats as watch-only too."""
    if config.budget_shares is None:
        return {}
    return {dim: share if _alerting(share) else None for dim, share in shares_for(config).items()}


def nominal_rates(config: BehaviourConfig) -> dict[str, float | None]:
    """Each item's nominal rate for a config: the design's red flags (``policy.LINE_ALPHA``
    for learned limits, None for the rest), then, with an alert line, each dimension's
    w_d x alpha (0 for watch-only), then, with floor budgets, the floors."""
    from mcp_security.behaviour import engine, policy  # lazily: engine imports this module

    learned = (engine.BURST, engine.MANY_ASSETS, engine.REQUEST_TOO_BIG)
    flags = (*learned, engine.SEQUENCE, engine.PROTOCOL_SKIP)
    scored = {d for dims in engine.dimension_groups(config.design).values() for d in dims}
    out: dict[str, float | None] = {
        flag_item(f): policy.LINE_ALPHA if f in learned else None for f in flags if f in scored
    }
    if config.alert_alpha is not None:
        for dim, share in config_shares(config).items():
            out[dimension_item(dim)] = 0.0 if share is None else share * config.alert_alpha
    out |= {floor_item(name): beta for name, beta in _alert_floors(config).items()}
    if config.floor_budget is not None:
        out[floor_item(WATCH_FLOOR)] = None
    return out


def _alert_floors(config: BehaviourConfig) -> dict[str, float]:
    """The config's alert floors and their budgets beta, by calibration.py's floor names
    (none without ``floor_budget``; no copy floor without ``copy_floor``)."""
    if config.floor_budget is None:
        return {}
    floors = floor_budgets(config.floor_budget)
    if not config.copy_floor:
        del floors[COPY_FLOOR]
    return floors


@dataclass(frozen=True)
class RateSettings:
    """What a route's :class:`FlagRates` counts against. ``alert_floors`` maps each alert
    floor's name to its beta; its item's nominal rate is beta (added when ``nominal`` lacks
    it). ``demote_on`` names the Wilson bound that must exceed beta: :data:`UPPER` (the spec)
    or :data:`LOWER`. The mappings are stored read-only."""

    nominal: Mapping[str, float | None] = field(default_factory=dict)
    alert_floors: Mapping[str, float] = field(default_factory=dict)
    shares: Mapping[str, float | None] = field(default_factory=dict)
    alpha: float | None = None
    history_days: int = HISTORY_DAYS
    window_days: int = RATE_WINDOW_DAYS
    confidence: float = CONFIDENCE
    demote_on: str = UPPER

    def __post_init__(self) -> None:
        nominal = dict(self.nominal)
        for key, rate in nominal.items():
            split_item(key)
            if rate is not None and not 0 <= rate <= 1:
                raise ValueError(f"the nominal rate of {key} must be in [0, 1], not {rate!r}")
        floors = dict(self.alert_floors)
        for name, beta in floors.items():
            _check_open_unit(beta, f"beta of {name}")
            if nominal.setdefault(floor_item(name), beta) != beta:
                raise ValueError(f"{floor_item(name)}'s nominal rate must be its beta {beta!r}")
        shares = dict(self.shares)
        for dim, share in shares.items():
            if share is not None and not 0 < share <= 1:
                raise ValueError(f"the share of {dim} must be in (0, 1], not {share!r}")
        if self.alpha is not None:
            _check_open_unit(self.alpha, "alpha")
        _check_positive_int(self.history_days, "history_days")
        _check_positive_int(self.window_days, "window_days")
        _check_open_unit(self.confidence, "confidence")
        if self.demote_on not in DEMOTE_RULES:
            raise ValueError(f"demote_on must be one of {DEMOTE_RULES}, not {self.demote_on!r}")
        object.__setattr__(self, "nominal", MappingProxyType(nominal))
        object.__setattr__(self, "alert_floors", MappingProxyType(floors))
        object.__setattr__(self, "shares", MappingProxyType(shares))

    @classmethod
    def from_config(cls, config: BehaviourConfig, **overrides: object) -> RateSettings:
        """The settings of a route scored with ``config``; ``overrides`` replace fields. The
        alert floors' nominal rows follow ``alert_floors``, the config's or an override."""
        config_floors = {floor_item(name) for name in _alert_floors(config)}
        values = {
            "nominal": {k: v for k, v in nominal_rates(config).items() if k not in config_floors},
            "alert_floors": _alert_floors(config),
            "shares": config_shares(config),
            "alpha": config.alert_alpha,
            "history_days": config.history_days,
        }
        return cls(**(values | overrides))

    def to_json(self) -> dict:
        """JSON values; the mappings as [key, value] pairs, so their order survives."""
        out = {f.name: getattr(self, f.name) for f in fields(self)}
        for name in _MAPPINGS:
            out[name] = [[key, value] for key, value in out[name].items()]
        return out

    @classmethod
    def from_json(cls, data: dict) -> RateSettings:
        """The settings :meth:`to_json` wrote."""
        mappings = {name: dict(data[name]) for name in _MAPPINGS}
        return cls(**(data | mappings))


class FlagRates:
    """One route's realised rates and floor demotions (RF5).

    Feed it with :meth:`add` for every scored call whose agent-day should count (``raised``
    empty when nothing fired), and :meth:`fold` it at each route rollover (CAL-7). Days are
    the callers' local days (B9). Snapshot with :meth:`to_json`.

    **What the engine (K1) adds as ``raised``.** :func:`floor_firings` of the same ``alert``
    and ``watch`` names it passes to ``calibration.apply_floors``. So every floor that fired at
    the ALERT level counts, whether it acted or not: firings during route warm-up and while RF5
    has the floor demoted count. Not ``Decision.alert_floors``: a demoted floor never acts, so
    its rate would fall to 0 and the floor would flap. Not ``Decision.floors`` either: it names
    a first access at the WATCH level (sensitivity 4) FIRST_ACCESS_FLOOR too, which must be
    ``floor_item(WATCH_FLOOR)``, never the alert floor's item. Then ``flag_item(key)`` for each
    red flag raised, before any discount, and ``dimension_item(key)`` when a dimension alone
    reached the line.

    **Days.** A fold at route day t reports and decides on the local-day buckets
    [t - window_days, t - 1]. At the rollover, callers west of the route's zone are still in
    local day t - 1 (or t - 2), so the newest buckets can be partial; CAL-7's sweep folds
    only ended local days, so the two can differ slightly on those days. Adds are accepted
    for days from t - :data:`LATE_DAYS` on; older days are kept only as counts.

    **Demotion caveats** (for the author; spec rule kept). Under the UPPER rule, keeping a
    floor needs at least z^2 (1 - beta) / beta established agent-days with no firing: 1,277
    at beta = 0.30%, 7,680 at 0.05%, about 43 and 256 a day over 30 days. A route with few or
    no established callers (every new route) demotes both floors at its first fold, with
    ``agent_days`` 0 and ``bound`` 1.0, and keeps them demoted until it has that many: the copy
    floor stays demoted on a 150-agent route that never fires it, and a route too small for an
    active record path (spec 2.3: "a smaller route alerts only through its floors") has no
    alert path left. A single established caller firing often can demote a floor for the whole
    route. :data:`LOWER` is selectable. Restoring a floor goes beyond the spec, and demotion and
    restoration share one bound with no hysteresis, so a route whose bound sits near beta can
    flap at consecutive folds, logging each change.
    """

    def __init__(self, settings: RateSettings | None = None) -> None:
        self.settings = settings if settings is not None else RateSettings()
        self._open: dict[int, _Day] = {}  # days that can still take adds: caller sets
        self._closed: dict[int, _Counts] = {}  # older days kept in the window: counts only
        self._folded: int | None = None  # the last route day folded
        self._demoted: dict[str, int] = {}  # alert floor -> the fold day that demoted it

    @classmethod
    def from_config(cls, config: BehaviourConfig, **overrides: object) -> FlagRates:
        """A route's rates for ``config`` (see :meth:`RateSettings.from_config`)."""
        return cls(RateSettings.from_config(config, **overrides))

    def add(
        self,
        day: int,
        caller: str,
        raised: Iterable[str] = (),
        *,
        established: bool = False,
        era: str | None = None,
    ) -> None:
        """Count one call's agent-day and the items it ``raised`` (item keys). A caller
        counts as established on a day if any of that day's calls says so. ``ValueError``
        for a malformed input or a day before the last fold's t - :data:`LATE_DAYS`."""
        _check_day(day)
        if not isinstance(caller, str) or not caller:
            raise ValueError(f"caller must be a non-empty string, not {caller!r}")
        if not isinstance(established, bool):
            raise ValueError(f"established must be a bool, not {established!r}")
        if isinstance(raised, str):
            raise ValueError(f"raised is an iterable of item keys, not the string {raised!r}")
        items = list(raised)
        for key in items:
            split_item(key)
        first = self._first_open_day()
        if first is not None and day < first:
            raise ValueError(f"day {day} is closed: adds start at day {first} after the fold")
        bucket = self._open.setdefault(day, _Day())
        bucket.callers[caller] = bucket.callers.get(caller, False) or established
        era_key = UNKNOWN_ERA if era is None else era
        bucket.eras.setdefault(era_key, set()).add(caller)
        era_items = bucket.era_raised.setdefault(era_key, {})
        for key in items:
            bucket.raised.setdefault(key, set()).add(caller)
            era_items.setdefault(key, set()).add(caller)

    def demoted(self, floor: str) -> bool:
        """Whether the alert floor ``floor`` acts as a watch floor after the last fold."""
        return floor in self._demoted

    @property
    def demoted_floors(self) -> tuple[str, ...]:
        """The alert floors demoted after the last fold (``apply_floors(demoted=...)``)."""
        return tuple(sorted(self._demoted))

    def report(self, day: int, agent_days: Mapping[str, int] | None = None) -> RateReport:
        """The rates over [day - window_days, day - 1], changing nothing. ``agent_days``
        (N_d per dimension, from the record reference) adds the path activity."""
        _check_day(day)
        return self._report(day, agent_days)

    def fold(self, day: int, agent_days: Mapping[str, int] | None = None) -> RateReport:
        """At the route's rollover to ``day``: report the window, demote or restore each
        alert floor, keep days older than ``day`` - :data:`LATE_DAYS` as counts and forget
        days before the window. Its ``demotions`` are the changes to log. ``ValueError`` for
        a day before the last fold."""
        _check_day(day)
        if self._folded is not None and day < self._folded:
            raise ValueError(f"folds go forward: day {day} is before {self._folded}")
        base = self._report(day, agent_days)
        rows = {r.item: r for r in base.rates}
        events = []
        rule = self.settings.demote_on
        for floor, beta in sorted(self.settings.alert_floors.items()):
            row = rows[floor_item(floor)]
            bound = row.established_upper if rule == UPPER else row.established_lower
            over = bound > beta
            if over == self.demoted(floor):
                continue
            if over:
                self._demoted[floor] = day
            else:
                del self._demoted[floor]
            events.append(
                DemotionEvent(
                    floor,
                    day,
                    over,
                    row.established_raised,
                    row.established_days,
                    bound,
                    beta,
                    rule,
                )
            )
        self._folded = day
        self._compact(day)
        return replace(base, demoted=self.demoted_floors, demotions=tuple(events))

    def to_json(self) -> dict:
        """A snapshot that :meth:`from_json` restores exactly."""
        return {
            "schema": SCHEMA,
            "settings": self.settings.to_json(),
            "folded": self._folded,
            "demoted": dict(sorted(self._demoted.items())),
            "open": {str(d): self._open[d].to_json() for d in sorted(self._open)},
            "closed": {str(d): self._closed[d].to_json() for d in sorted(self._closed)},
        }

    @classmethod
    def from_json(cls, data: dict) -> FlagRates:
        """The rates :meth:`to_json` saved; ``ValueError`` for another schema."""
        if data.get("schema") != SCHEMA:
            raise ValueError(f"not a {SCHEMA} snapshot: {data.get('schema')!r}")
        rates = cls(RateSettings.from_json(data["settings"]))
        rates._folded = data["folded"]
        rates._demoted = {floor: int(day) for floor, day in data["demoted"].items()}
        rates._open = {int(d): _Day.from_json(b) for d, b in data["open"].items()}
        rates._closed = {int(d): _Counts.from_json(c) for d, c in data["closed"].items()}
        return rates

    # ── implementation ───────────────────────────────────────────────────────────────────
    def _first_open_day(self) -> int | None:
        """The first day that still takes adds (None before the first fold)."""
        return None if self._folded is None else self._folded - LATE_DAYS

    def _compact(self, day: int) -> None:
        """After the fold at ``day``: days before ``day`` - LATE_DAYS become counts, and
        days before the window [day - window_days, day - 1] are forgotten."""
        first_open, oldest = day - LATE_DAYS, day - self.settings.window_days
        for d in [d for d in self._open if d < first_open]:
            self._closed[d] = self._open.pop(d).counts()
        self._open = {d: b for d, b in self._open.items() if d >= oldest}
        self._closed = {d: c for d, c in self._closed.items() if d >= oldest}

    def _window(self, day: int) -> _Counts:
        """The summed counts of the kept days in [day - window_days, day - 1]."""
        total = _Counts()
        for d in range(day - self.settings.window_days, day):
            if d in self._closed:
                total.merge(self._closed[d])
            elif d in self._open:
                total.merge(self._open[d].counts())
        return total

    def _report(self, day: int, agent_days: Mapping[str, int] | None) -> RateReport:
        """The report over the window before ``day``, with the current demotions."""
        s = self.settings
        c = self._window(day)
        keys = sorted(set(s.nominal) | set(c.raised))
        rates = tuple(
            _item_rate(
                key,
                s.nominal.get(key),
                c.raised[key],
                c.agent_days,
                c.raised_est[key],
                c.established,
                s,
            )
            for key in keys
        )
        eras = tuple(
            EraRate(
                era,
                key,
                c.era_raised[era, key],
                c.era_days[era],
                *_interval(c.era_raised[era, key], c.era_days[era], s),
            )
            for era in sorted(c.era_days)
            for key in keys
        )
        paths, caps = (), ()
        if s.alpha is not None:
            caps = broken_caps(s.shares, s.alpha, s.history_days)
            if agent_days is not None:
                paths = path_activity(agent_days, s.shares, s.alpha, s.history_days)
        return RateReport(
            day,
            s.window_days,
            c.agent_days,
            c.established,
            rates,
            eras,
            paths,
            self.demoted_floors,
            broken_caps=caps,
        )


@dataclass
class _Counts:
    """A day's (or a window's) counts, all a report reads: agent-days and established ones,
    and the agent-days per item raised, per era and per (era, item) raised."""

    agent_days: int = 0
    established: int = 0
    raised: Counter[str] = field(default_factory=Counter)
    raised_est: Counter[str] = field(default_factory=Counter)  # established callers only
    era_days: Counter[str] = field(default_factory=Counter)
    era_raised: Counter[tuple[str, str]] = field(default_factory=Counter)

    def merge(self, other: _Counts) -> None:
        """Add ``other``'s counts to these."""
        self.agent_days += other.agent_days
        self.established += other.established
        self.raised.update(other.raised)
        self.raised_est.update(other.raised_est)
        self.era_days.update(other.era_days)
        self.era_raised.update(other.era_raised)

    def to_json(self) -> dict:
        """Sorted JSON values; (era, item) counts nested as era -> item -> count."""
        nested: dict[str, dict[str, int]] = {}
        for (era, key), n in sorted(self.era_raised.items()):
            nested.setdefault(era, {})[key] = n
        return {
            "agent_days": self.agent_days,
            "established": self.established,
            "raised": dict(sorted(self.raised.items())),
            "raised_est": dict(sorted(self.raised_est.items())),
            "era_days": dict(sorted(self.era_days.items())),
            "era_raised": nested,
        }

    @classmethod
    def from_json(cls, data: dict) -> _Counts:
        """The counts :meth:`to_json` wrote."""
        return cls(
            data["agent_days"],
            data["established"],
            Counter(data["raised"]),
            Counter(data["raised_est"]),
            Counter(data["era_days"]),
            Counter(
                {
                    (era, key): n
                    for era, items in data["era_raised"].items()
                    for key, n in items.items()
                }
            ),
        )


class _Day:
    """An open day's agent-days: who was active (and established), in which era, and who
    raised each item (also per era). Caller sets, so a repeat call counts once."""

    __slots__ = ("callers", "eras", "raised", "era_raised")

    def __init__(self) -> None:
        self.callers: dict[str, bool] = {}  # caller -> established that day
        self.eras: dict[str, set[str]] = {}  # era -> callers
        self.raised: dict[str, set[str]] = {}  # item -> callers
        self.era_raised: dict[str, dict[str, set[str]]] = {}  # era -> item -> callers

    def counts(self) -> _Counts:
        """The day's counts (what it compacts to at a fold)."""
        out = _Counts(len(self.callers), sum(self.callers.values()))
        for key, who in self.raised.items():
            out.raised[key] = len(who)
            established = sum(self.callers[c] for c in who)
            if established:
                out.raised_est[key] = established
        for era, who in self.eras.items():
            out.era_days[era] = len(who)
        for era, items in self.era_raised.items():
            for key, who in items.items():
                out.era_raised[era, key] = len(who)
        return out

    def to_json(self) -> dict:
        """Sorted JSON values, so a snapshot is deterministic."""
        return {
            "callers": dict(sorted(self.callers.items())),
            "eras": {e: sorted(who) for e, who in sorted(self.eras.items())},
            "raised": {k: sorted(who) for k, who in sorted(self.raised.items())},
            "era_raised": {
                e: {k: sorted(who) for k, who in sorted(items.items())}
                for e, items in sorted(self.era_raised.items())
            },
        }

    @classmethod
    def from_json(cls, data: dict) -> _Day:
        """The day :meth:`to_json` wrote."""
        day = cls()
        day.callers = {c: bool(est) for c, est in data["callers"].items()}
        day.eras = {e: set(who) for e, who in data["eras"].items()}
        day.raised = {k: set(who) for k, who in data["raised"].items()}
        day.era_raised = {
            e: {k: set(who) for k, who in items.items()} for e, items in data["era_raised"].items()
        }
        return day


def _alerting(share: float | None) -> bool:
    """Whether a budget share lets its dimension alert: a share above 0, as
    ``calibration.combine`` reads it (None or 0 is watch-only)."""
    return share is not None and share > 0


def _interval(raised: int, days: int, settings: RateSettings) -> Interval:
    """The Wilson interval at the settings' confidence."""
    return wilson_interval(raised, days, settings.confidence)


def _item_rate(
    key: str,
    nominal: float | None,
    raised: int,
    days: int,
    raised_est: int,
    days_est: int,
    settings: RateSettings,
) -> ItemRate:
    """One report row."""
    every = _interval(raised, days, settings)
    est = _interval(raised_est, days_est, settings)
    status = rate_status(every, nominal, raised)
    return ItemRate(key, nominal, raised, days, *every, raised_est, days_est, *est, status)


def _check_count(raised: int, days: int) -> None:
    """``ValueError`` unless 0 <= raised <= days are integers (not bools)."""
    for value in (raised, days):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"counts must be integers, not {value!r}")
    if not 0 <= raised <= days:
        raise ValueError(f"need 0 <= raised <= days, not {raised} of {days}")


def _check_day(day: int) -> None:
    """``ValueError`` unless ``day`` is an integer day number."""
    if not isinstance(day, int) or isinstance(day, bool):
        raise ValueError(f"day must be an integer day number, not {day!r}")


def _check_positive_int(value: int, name: str) -> None:
    """``ValueError`` unless ``value`` is an integer >= 1."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{name} must be a positive integer, not {value!r}")


def _check_open_unit(value: float, name: str) -> None:
    """``ValueError`` unless ``value`` is a number in (0, 1)."""
    if isinstance(value, bool) or not isinstance(value, int | float) or not 0 < value < 1:
        raise ValueError(f"{name} must be in (0, 1), not {value!r}")
