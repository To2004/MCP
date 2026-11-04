"""EV-16: the development selection rule for the v5 configuration (spec 6.2, revision 2).

The rule is written and hashed before the first development run (:func:`rule_digest`). It is
applied to a table of candidates, each measured on the same development worlds over the
selection window (days 135-180 of the new development worlds; thresholds fitted on days 90-134).

**Objective:** the Hyp1 endpoint, the per-world credited pAUC over [0, 3%], averaged over the
development worlds.

**Admissible** means all of:

1. quiet: the realised rate on all benign agent-days at the deployed line has a one-sided upper
   95% world-bootstrap bound at most alpha + beta;
2. per-kind recall at the deployed line at least cfg0's minus delta_kind, for kinds with at
   least 20 episodes (pooled over the worlds);
3. credited list catch at least max(v4, cfg4) minus delta_list;
4. the cumulative cap: the benign agent-day rate at x3 at most cfg0's plus 0.5 points;
5. runtime at most 2x v4's, and every test passes.

**Argued switches** (B7, RF11, AI-8): cfg_k = cfg0 plus one switch is admitted when its objective
is at least cfg0's minus delta, its recall on every kind it targets improves on cfg0's by at
least delta_kind, and cfg_k is admissible. cfg4 is cfg0 plus every admitted switch, so at this
stage the list constraint is checked against v4 alone (cfg4 does not exist yet). A switch that
fails ships off, and no candidate that carries it can be chosen.

**Choice:** the eligible admissible candidate with the highest objective; candidates within delta
of it are tied, and a tie goes to fewer constants (then the higher objective, then the name).

**Margins:** delta, delta_kind and delta_list are 1.64 x the paired world-level bootstrap SE on
the development pool (spec 6.1), **fixed in the hashed rule** before the first development run.
Batch 5 runs :func:`derive_margins` (cfg0 against v4) on the L2 v5-engine development runs,
writes the numbers into the rule and only then hashes it (:func:`rule_digest`). A rule that
leaves a margin None is refused, unless it opts in with ``margins_from = "selection_table"``:
the opt-in is part of the hashed rule, the margins are then derived from the selection table
itself (data-dependent), and the result says so.

cfg9 (Footprint watch-only) is scored only if D3 = (c); the author chose D3 = (a), so a table
that holds cfg9 under any other D3 is refused.
"""

from __future__ import annotations

import dataclasses
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

try:  # imported as part of the heldout package (tests, other harness modules)
    from . import heldout_metrics as hm
    from . import heldout_provenance as hp
    from . import heldout_stats as hs
except ImportError:  # run as a script: the sibling modules are on sys.path
    import heldout_metrics as hm  # type: ignore[no-redef]
    import heldout_provenance as hp  # type: ignore[no-redef]
    import heldout_stats as hs  # type: ignore[no-redef]

# ── roles and frozen constants ───────────────────────────────────────────────────────────────
REFERENCE = "reference"  # v4
CORE = "core"  # cfg0
ARGUED = "argued"  # cfg1-cfg3: cfg0 plus one argued switch
COMBINED = "combined"  # cfg4: cfg0 plus every admitted switch
TUNE = "tune"  # cfg5-cfg8: cfg4 plus one tune candidate
WATCH_ONLY = "watch_only"  # cfg9: cfg4 with Footprint watch-only, scored only if D3 = (c)
ROLES = (REFERENCE, CORE, ARGUED, COMBINED, TUNE, WATCH_ONLY)
SINGLE_ROLES = (REFERENCE, CORE, COMBINED)  # exactly one candidate each
MARGIN_Z = 1.64  # delta = 1.64 x the world-level SE (spec 6.1)
MIN_KIND_EPISODES = 20
POINT = 0.01  # one percentage point, as a rate
X3_CAP = 0.5 * POINT  # the cumulative cap: cfg0's benign x3 rate plus 0.5 points
RUNTIME_FACTOR = 2.0
D3_DECIDED = "a"  # the author's decision (spec 8)
D3_LET_SELECTION_DECIDE = "c"
SELECTION_SEED = 20_261_029
DAYS_PER_MONTH = 30
AGENTS_PER_UNIT = 100
MARGINS_IN_RULE = "rule"  # every margin is a number in the hashed rule (spec 6.1)
MARGINS_FROM_TABLE = "selection_table"  # opt-in: margins left None come from the table
MARGIN_SOURCES = (MARGINS_IN_RULE, MARGINS_FROM_TABLE)
MAX_RECALL_SD = 0.5  # the largest SD of one recall indicator: a kind's no-spread fallback


class NoAdmissibleCandidate(ValueError):
    """No eligible candidate passes the admissibility constraints."""


# ── the table ────────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class WorldMetrics:
    """One candidate's numbers on one development world, selection window."""

    world: str
    pauc: float  # Hyp1 endpoint on this world
    benign_days: int  # every benign agent-day (ordinary and change)
    benign_alerts: int  # ... alerting at the deployed line
    benign_alerts_x3: int  # ... at x3 (the cumulative benign cost)
    kind_episodes: Mapping[str, int]
    kind_caught: Mapping[str, int]  # credited, at the deployed line
    list_episodes: int
    list_caught: float  # credited list catch (expected count)
    runtime_s: float


@dataclass(frozen=True)
class Candidate:
    """One configuration and its development numbers (``worlds`` empty before the runs)."""

    name: str
    role: str
    n_constants: int
    switches: tuple[str, ...] = ()  # argued and tune switches on beyond the core
    targets: tuple[str, ...] = ()  # gray kinds an argued switch targets
    tests_pass: bool = True
    worlds: tuple[WorldMetrics, ...] = ()

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise ValueError(f"{self.name}: role must be one of {ROLES}, not {self.role!r}")
        if self.role == ARGUED and (len(self.switches) != 1 or not self.targets):
            raise ValueError(f"{self.name}: an argued candidate has one switch and its targets")
        if self.n_constants < 0:
            raise ValueError(f"{self.name}: n_constants must be non-negative")


@dataclass(frozen=True)
class SelectionRule:
    """The hashed rule. Every margin is a number fixed in it, unless ``margins_from`` opts in
    to deriving the ones left None from the selection table (hashed with the rule)."""

    delta: float | None = None
    delta_kind: float | Mapping[str, float] | None = None
    delta_list: float | None = None
    alpha: float = hm.ALPHA_DEPLOYED
    beta: float = hm.FLOOR_BUDGET
    min_kind_episodes: int = MIN_KIND_EPISODES
    x3_cap: float = X3_CAP
    runtime_factor: float = RUNTIME_FACTOR
    level: float = hs.CONFIDENCE
    b: int = hs.BOOTSTRAP_B
    seed: int = SELECTION_SEED
    d3: str = D3_DECIDED
    margins_from: str = MARGINS_IN_RULE

    def __post_init__(self) -> None:
        if self.margins_from not in MARGIN_SOURCES:
            raise ValueError(
                f"margins_from must be one of {MARGIN_SOURCES}, not {self.margins_from!r}"
            )
        missing = [
            name for name in ("delta", "delta_kind", "delta_list") if getattr(self, name) is None
        ]
        if missing and self.margins_from == MARGINS_IN_RULE:
            raise ValueError(
                f"the rule leaves {missing} None, but margins are fixed in the hashed rule "
                "(spec 6.1): run derive_margins on the L2 v5-engine development runs and "
                "write the numbers into the rule before hashing it, or opt in with "
                f"margins_from={MARGINS_FROM_TABLE!r}"
            )


@dataclass(frozen=True)
class Margins:
    """delta, delta_kind (per kind) and delta_list, and where they came from.
    ``fallback_kinds`` got the no-spread fallback (seen in fewer than two worlds)."""

    delta: float
    delta_kind: Mapping[str, float]
    delta_list: float
    source: str
    fallback_kinds: tuple[str, ...] = ()


@dataclass(frozen=True)
class Check:
    """One candidate against the rule."""

    name: str
    role: str
    objective: float
    quiet_upper: float
    admissible: bool
    eligible: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class SwitchDecision:
    """An argued switch: admitted or not, and why."""

    candidate: str
    switch: str
    admitted: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class Selection:
    """The rule's outcome."""

    chosen: str
    tied: tuple[str, ...]
    margins: Margins
    checks: Mapping[str, Check]
    switches: Mapping[str, SwitchDecision]
    admitted: tuple[str, ...]
    rule_digest: str
    notes: tuple[str, ...] = field(default_factory=tuple)


# ── pooled statistics ────────────────────────────────────────────────────────────────────────
def _worlds(c: Candidate) -> list[WorldMetrics]:
    if not c.worlds:
        raise ValueError(f"{c.name} has no development numbers")
    return sorted(c.worlds, key=lambda w: w.world)


def objective(c: Candidate) -> float:
    """The mean of the per-world pAUC over the development worlds."""
    return float(np.mean([w.pauc for w in _worlds(c)]))


def kind_recall(c: Candidate, kind: str) -> tuple[float, int]:
    """Pooled credited recall at the deployed line on one kind, and its episodes."""
    ws = _worlds(c)
    n = sum(w.kind_episodes.get(kind, 0) for w in ws)
    k = sum(w.kind_caught.get(kind, 0) for w in ws)
    return (k / n if n else float("nan")), n


def list_recall(c: Candidate) -> float:
    """Pooled credited list catch over the list's episodes."""
    ws = _worlds(c)
    n = sum(w.list_episodes for w in ws)
    if n == 0:
        raise ValueError(f"{c.name}: no list episodes")
    return sum(w.list_caught for w in ws) / n


def x3_rate(c: Candidate) -> float:
    """Pooled benign agent-day rate at x3."""
    ws = _worlds(c)
    return sum(w.benign_alerts_x3 for w in ws) / sum(w.benign_days for w in ws)


def runtime(c: Candidate) -> float:
    """Total runtime over the development worlds, seconds."""
    return float(sum(w.runtime_s for w in _worlds(c)))


def quiet_upper(c: Candidate, rule: SelectionRule) -> float:
    """One-sided upper world-bootstrap bound of the benign rate at the deployed line."""
    ws = _worlds(c)
    interval = hs.world_bootstrap(
        [w.benign_alerts for w in ws],
        [w.benign_days for w in ws],
        b=rule.b,
        seed=rule.seed,
        level=rule.level,
    )
    return interval.upper_one_sided


def _kinds(c: Candidate) -> list[str]:
    return sorted({k for w in _worlds(c) for k in w.kind_episodes})


# ── margins ──────────────────────────────────────────────────────────────────────────────────
def margin(se: float, z: float = MARGIN_Z) -> float:
    """A margin from a world-level SE: z x SE."""
    if se < 0:
        raise ValueError(f"an SE is non-negative, not {se}")
    return z * se


def derive_margins(
    core: Candidate,
    reference: Candidate,
    *,
    b: int = hs.BOOTSTRAP_B,
    seed: int = SELECTION_SEED,
    z: float = MARGIN_Z,
) -> Margins:
    """delta, delta_kind and delta_list as z x the paired (core - reference) world-bootstrap
    SE of the objective, each kind's pooled recall and the pooled list catch.

    Batch 5 runs it on the L2 v5-engine development runs and writes the result into the rule
    before hashing it. A kind with episodes in fewer than two worlds has no world-level spread;
    it gets the stated fallback z x 0.5 x sqrt(1/n_core + 1/n_reference), n its pooled
    episodes: the binomial SE of a recall difference at its largest (p = 1/2), and it is listed
    in ``fallback_kinds``.
    """
    a, r = _worlds(core), _worlds(reference)
    if [w.world for w in a] != [w.world for w in r]:
        raise ValueError("core and reference must be measured on the same worlds")
    counts = hs.bootstrap_counts(len(a), b, seed)

    def se(
        num_a: Sequence[float],
        num_r: Sequence[float],
        den_a: Sequence[float] | None = None,
        den_r: Sequence[float] | None = None,
    ) -> float:
        return hs.paired_world_bootstrap(num_a, num_r, den_a, den_r, counts=counts).se

    delta = margin(se([w.pauc for w in a], [w.pauc for w in r]), z)
    delta_kind = {}
    fallback = []
    for kind in _kinds(core):
        den_a = [w.kind_episodes.get(kind, 0) for w in a]
        den_r = [w.kind_episodes.get(kind, 0) for w in r]
        if sum(den_a) == 0 or sum(den_r) == 0:
            continue  # never checked: no episode of the kind
        if sum(d > 0 for d in den_a) < hs.MIN_BOOTSTRAP_WORLDS:
            delta_kind[kind] = z * MAX_RECALL_SD * math.sqrt(1 / sum(den_a) + 1 / sum(den_r))
            fallback.append(kind)
            continue
        num_a = [w.kind_caught.get(kind, 0) for w in a]
        num_r = [w.kind_caught.get(kind, 0) for w in r]
        delta_kind[kind] = margin(se(num_a, num_r, den_a, den_r), z)
    delta_list = margin(
        se(
            [w.list_caught for w in a],
            [w.list_caught for w in r],
            [w.list_episodes for w in a],
            [w.list_episodes for w in r],
        ),
        z,
    )
    source = f"{z} x paired SE, {core.name} - {reference.name}"
    if fallback:
        source += f"; no-spread fallback for {sorted(fallback)}"
    return Margins(delta, delta_kind, delta_list, source, tuple(sorted(fallback)))


def _resolve_margins(rule: SelectionRule, core: Candidate, reference: Candidate) -> Margins:
    given = (rule.delta, rule.delta_kind, rule.delta_list)
    if all(m is not None for m in given):
        kinds = rule.delta_kind
        per_kind = dict(kinds) if isinstance(kinds, Mapping) else {k: kinds for k in _kinds(core)}
        return Margins(float(rule.delta), per_kind, float(rule.delta_list), "fixed in the rule")
    if rule.margins_from != MARGINS_FROM_TABLE:  # SelectionRule refuses this; kept as a guard
        raise ValueError("a margin is None and the rule does not opt in to deriving it")
    derived = derive_margins(core, reference, b=rule.b, seed=rule.seed)
    kinds = rule.delta_kind
    if kinds is None:
        per_kind = dict(derived.delta_kind)
    elif isinstance(kinds, Mapping):
        per_kind = dict(kinds)
    else:
        per_kind = {k: float(kinds) for k in _kinds(core)}
    return Margins(
        delta=derived.delta if rule.delta is None else float(rule.delta),
        delta_kind=per_kind,
        delta_list=derived.delta_list if rule.delta_list is None else float(rule.delta_list),
        source=f"derived from the selection table where the rule left None ({derived.source})",
        fallback_kinds=derived.fallback_kinds if kinds is None else (),
    )


def _kind_margin(margins: Margins, kind: str) -> float:
    if kind not in margins.delta_kind:
        raise ValueError(f"no delta_kind for kind {kind!r}; fix it in the rule")
    return margins.delta_kind[kind]


# ── checks ───────────────────────────────────────────────────────────────────────────────────
def _admissibility(
    c: Candidate,
    core: Candidate,
    reference: Candidate,
    list_bar: float,
    rule: SelectionRule,
    margins: Margins,
) -> tuple[float, list[str]]:
    reasons = []
    upper = quiet_upper(c, rule)
    if upper > rule.alpha + rule.beta:
        reasons.append(
            f"quiet: upper bound {upper:.5f} > alpha + beta {rule.alpha + rule.beta:.5f}"
        )
    for kind in _kinds(core):
        base, n = kind_recall(core, kind)
        if n < rule.min_kind_episodes:
            continue
        rec, _ = kind_recall(c, kind)
        bar = base - _kind_margin(margins, kind)
        if rec < bar:
            reasons.append(f"kind {kind}: recall {rec:.4f} < {core.name}'s {base:.4f} - delta_kind")
    rec = list_recall(c)
    if rec < list_bar - margins.delta_list:
        reasons.append(f"list: catch {rec:.4f} < {list_bar:.4f} - delta_list")
    if x3_rate(c) > x3_rate(core) + rule.x3_cap:
        reasons.append(
            f"x3: benign rate {x3_rate(c):.5f} > {core.name}'s {x3_rate(core):.5f} + cap"
        )
    if runtime(c) > rule.runtime_factor * runtime(reference):
        reasons.append(f"runtime: {runtime(c):.1f} s > {rule.runtime_factor} x v4's")
    if not c.tests_pass:
        reasons.append("tests fail")
    return upper, reasons


def _decide_switch(
    c: Candidate,
    core: Candidate,
    reference: Candidate,
    rule: SelectionRule,
    margins: Margins,
) -> SwitchDecision:
    reasons = []
    if objective(c) < objective(core) - margins.delta:
        reasons.append(
            f"objective {objective(c):.4f} < {core.name}'s {objective(core):.4f} - delta"
        )
    for kind in c.targets:
        rec, _ = kind_recall(c, kind)
        base, _ = kind_recall(core, kind)
        if not rec - base >= _kind_margin(margins, kind):
            reasons.append(f"target {kind}: gain {rec - base:.4f} < delta_kind")
    _, admissible = _admissibility(c, core, reference, list_recall(reference), rule, margins)
    reasons += [f"not admissible: {r}" for r in admissible]
    return SwitchDecision(c.name, c.switches[0], not reasons, tuple(reasons))


def _validate(candidates: Sequence[Candidate], rule: SelectionRule) -> dict[str, Candidate]:
    by_name = {c.name: c for c in candidates}
    if len(by_name) != len(candidates):
        raise ValueError("candidate names must be unique")
    for role in SINGLE_ROLES:
        n = sum(c.role == role for c in candidates)
        if n != 1:
            raise ValueError(f"the table needs exactly one {role} candidate, not {n}")
    if any(c.role == WATCH_ONLY for c in candidates) and rule.d3 != D3_LET_SELECTION_DECIDE:
        raise ValueError(f"cfg9 (Footprint watch-only) is scored only if D3 = (c), not {rule.d3}")
    worlds = {tuple(w.world for w in _worlds(c)) for c in candidates}
    if len(worlds) != 1:
        raise ValueError("every candidate must be measured on the same development worlds")
    episodes = {
        tuple(
            (w.world, tuple(sorted(w.kind_episodes.items())), w.list_episodes) for w in _worlds(c)
        )
        for c in candidates
    }
    if len(episodes) != 1:
        raise ValueError(
            "every candidate must see the same episodes per world (kind_episodes and "
            "list_episodes are properties of a world, not of a configuration)"
        )
    kinds = set(_kinds(candidates[0]))
    for c in candidates:
        unknown = sorted(set(c.targets) - kinds)
        if unknown:
            raise ValueError(f"{c.name} targets kinds the table does not hold: {unknown}")
    return by_name


def _one(candidates: Sequence[Candidate], role: str) -> Candidate:
    return next(c for c in candidates if c.role == role)


def select(candidates: Sequence[Candidate], rule: SelectionRule) -> Selection:
    """Apply the rule. ``NoAdmissibleCandidate`` when nothing eligible is admissible;
    ``ValueError`` when cfg4 was not run with exactly the admitted switches."""
    _validate(candidates, rule)
    reference, core, combined = (_one(candidates, r) for r in (REFERENCE, CORE, COMBINED))
    margins = _resolve_margins(rule, core, reference)
    decisions = {
        c.switches[0]: _decide_switch(c, core, reference, rule, margins)
        for c in candidates
        if c.role == ARGUED
    }
    admitted = tuple(sorted(s for s, d in decisions.items() if d.admitted))
    if set(combined.switches) != set(admitted):
        raise ValueError(
            f"{combined.name} was run with {sorted(combined.switches)}, but the admitted "
            f"switches are {list(admitted)}: re-run it"
        )
    list_bar = max(list_recall(reference), list_recall(combined))
    checks = {}
    for c in candidates:
        if c.role == REFERENCE:
            continue
        upper, reasons = _admissibility(c, core, reference, list_bar, rule, margins)
        admissible = not reasons
        eligible = all(s in admitted or s not in decisions for s in c.switches)
        if not eligible:
            reasons.append("not eligible: carries a switch that was not admitted")
        checks[c.name] = Check(
            name=c.name,
            role=c.role,
            objective=objective(c),
            quiet_upper=upper,
            admissible=admissible,
            eligible=eligible,
            reasons=tuple(reasons),
        )
    passing = [ck for ck in checks.values() if ck.admissible and ck.eligible]
    if not passing:
        raise NoAdmissibleCandidate(
            "; ".join(f"{ck.name}: {', '.join(ck.reasons)}" for ck in checks.values())
        )
    best = max(ck.objective for ck in passing)
    tied = [ck for ck in passing if ck.objective >= best - margins.delta]
    constants = {c.name: c.n_constants for c in candidates}
    chosen = min(tied, key=lambda ck: (constants[ck.name], -ck.objective, ck.name))
    return Selection(
        chosen=chosen.name,
        tied=tuple(sorted(ck.name for ck in tied)),
        margins=margins,
        checks=checks,
        switches=decisions,
        admitted=admitted,
        rule_digest=rule_digest(rule),
        notes=(f"margins: {margins.source}",),
    )


# ── the hashed files ─────────────────────────────────────────────────────────────────────────
def rule_digest(rule: SelectionRule) -> str:
    """SHA-256 of the rule's canonical JSON (recorded before any development run)."""
    return hp.digest(dataclasses.asdict(rule))


def _world(obj: Mapping[str, object]) -> WorldMetrics:
    return WorldMetrics(**obj)  # type: ignore[arg-type]


def candidates_from_json(obj: Mapping[str, object]) -> tuple[SelectionRule, list[Candidate]]:
    """Read ``{"rule": {...}, "candidates": [{name, role, n_constants, switches, targets,
    tests_pass, worlds?}, ...]}`` (``heldout/v5_candidates.json``, written in Batch 5)."""
    rule = SelectionRule(**obj.get("rule", {}))  # type: ignore[arg-type]
    out = []
    for c in obj["candidates"]:  # type: ignore[union-attr]
        out.append(
            Candidate(
                name=c["name"],
                role=c["role"],
                n_constants=int(c["n_constants"]),
                switches=tuple(c.get("switches", ())),
                targets=tuple(c.get("targets", ())),
                tests_pass=bool(c.get("tests_pass", True)),
                worlds=tuple(_world(w) for w in c.get("worlds", ())),
            )
        )
    return rule, out


def load_candidates(path: str | Path) -> tuple[SelectionRule, list[Candidate]]:
    """Read a candidates file (see :func:`candidates_from_json`)."""
    return candidates_from_json(json.loads(Path(path).read_text()))


def catches_per_100_agent_months(
    delta_recall: float, episodes: int, agent_calendar_days: float
) -> float:
    """A recall margin in operational units (spec 6.1): analyst catches per 100 agents per
    month, given the episodes it applies to and the agents x days they came from."""
    if agent_calendar_days <= 0:
        raise ValueError("agent_calendar_days must be positive")
    return delta_recall * episodes * AGENTS_PER_UNIT * DAYS_PER_MONTH / agent_calendar_days
