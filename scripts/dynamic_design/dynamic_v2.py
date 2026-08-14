"""The runtime layer: two independent factors over one call.

    R(c) = min(SCORE_MAX, cell(tool, asset) x B(c) x L(c))

    B  how far this call's ARGUMENTS depart from what this deployment asks for
       0.70 narrower than anything seen before ... 1.00 ordinary ... 1.30 far wider

    L  how unusual this TOOL is for this deployment
       0.85 called constantly ... 1.00 the median tool ... 1.30 never called

B reads only argument values and L only tool counts, so neither can double-count the
other and each can be evaluated on its own. Both are earned against the deployment's own
history: no absolute threshold appears anywhere, because "how big is too big" is a
property of an organization, not of a tool.

With no history at all both are exactly 1.0 and the static cell stands untouched. That is
the honest abstention -- inventing a runtime adjustment from no evidence is the one answer
that cannot be right.

Full walkthrough, with diagrams and worked examples:
docs/project/dynamic-layer-explained.md

The split of responsibility is the point:

* **design time** decides only *which arguments are quantities* — an array whose length
  is breadth, a number whose value is breadth, a pair of endpoints whose span is. The
  schema answers this where its types are honest; a local model answers it where they
  are not (a list encoded as a delimited string, a bound stated only in prose). Neither
  is ever asked for a threshold: "how big is too big" is a property of the organization,
  not of the tool.
* **runtime** builds the reference itself, from the values this deployment has actually
  passed for that argument — quartiles, not a cut-point, so calls on either side can
  still be ordered.

With too little history there is no reference, and D contributes 1.0 — the honest
abstention, not a guess.

Deliberately out of scope: anything needing state across calls (a burst of small
calls, a rate). Stated as a limitation, not hidden — the threat model is a
legitimate agent doing too much in one call, not an adversary spreading work to
evade a threshold.

    python3 scripts/dynamic_design/dynamic_v2.py
"""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import re
import time
from datetime import datetime
from collections import Counter, defaultdict, deque
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SPEC_DIR = REPO / "reports" / "experiments" / "breadth_spec"
ARM = REPO / "reports" / "experiments" / "v7" / "five_level_v2_policy_v7_iso"
CORPUS = REPO / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5r_nacombo"

#: The breadth factor B moves BOTH WAYS, against this deployment's own observed range.
#: It was a discount only, on the reasoning that the scan already rates blast radius for
#: the worst a single call can do. That confuses capability with practice: blast_radius is
#: judged from a schema and prices what the tool could reach, while the runtime alone knows
#: what this org actually asks for. Discount-only left 93.6% of calls on exactly 1.0.
B_MIN = 0.70
#: The escalation ceiling, symmetric with B_MIN about 1.0 and matching L_MAX. Reached at
#: the upper Tukey fence, where a value stops being a large ordinary one and becomes an
#: outlier against this deployment's own practice.
B_MAX = 1.30
#: The likelihood factor L moves both ways: a tool this deployment barely uses raises
#: risk, one it uses constantly lowers it. The discount side is deliberately tighter than
#: the escalation side — commonness exonerating is the failure mode with history behind
#: it (a symmetric likelihood measured net-negative on all three servers, and per-identity
#: conditioning collapsed misuse AUC 0.53 -> 0.30).
L_MIN, L_MAX = 0.85, 1.30
#: Smoothing on tool share, so a fresh deployment does not read as all-rare.
L_ALPHA = 30.0
#: Server key -> the catalog stem its scan was written under.
_CATALOG = {"github": "github_real", "slack": "slack_real", "calendar": "calendar_real",
            "filesystem": "filesystem", "sqlite": "sqlite",
            # The five no-credential finance servers (reports/scan_finance/README.md) —
            # live-captured the same way, but with no LLM cells/bands artifact behind
            # them yet, so `cell` stays unresolved for these and the run reports D alone.
            "yahoo_finance": "yahoo_finance", "finance_tools": "finance_tools",
            "sec_edgar": "sec_edgar", "maverick": "maverick", "openbb": "openbb"}
SCORE_MAX = 125.0
# Below this many observations there are no meaningful quartiles.
#: Verdicts meaning the argument could not have signalled narrowness whatever its value.
#: They are excluded from B rather than scored 1.0, because B takes the least discount any
#: argument justifies: counted, one such argument pins the whole call to 1.0 and silently
#: disables the factor. Real traffic produces them constantly.
NO_SIGNAL = frozenset({"no history", "no floor"})

MIN_HISTORY = 20
# Bounded per-argument history: keeps memory constant on long streams. The window is
# the most recent MAX_HISTORY values, so the reference tracks what the deployment does
# now rather than what it did a year ago. Eviction must be by ARRIVAL order — evicting
# from the sorted list instead drops the smallest value every time, which walks Q1 and
# Q3 upward forever and quietly stops routine calls earning the discount.
MAX_HISTORY = 4000
TUKEY_K = 1.5
#: Percentile above which a value stops being a large ordinary one for this deployment.
#: A percentile rather than a quartile-derived fence because a dominant default collapses
#: the interquartile range, and a rule that switches on that flips real calls back and
#: forth between verdicts.
ESCALATE_AT = 90
#: How central a parameter is to the asset, as the scan graded it: 5 it names the asset
#: (or several), 4 an important part, 3 an unimportant part, 2 indirect, 1 not at all.
#: The scale applies to every parameter — an identifier is graded on what it names, not on
#: whether a number can be read from it.
BREADTH_WEIGHT = {5: 1.00, 4: 0.75, 3: 0.50, 2: 0.25, 1: 0.0}
#: Used when the scan gave no level, so an unlabelled quantity is neither silenced nor
#: treated as the widest thing on its tool.
DEFAULT_BREADTH = 3
#: Kinds a quantity can actually be read from. Only these can carry a deviation, so only
#: these can set the reference the relative weighting is measured against.
MEASURABLE = frozenset({"count", "magnitude", "range"})

ORG_TO_SERVER = {"calendar_aurora": "calendar", "github_helios": "github",
                 "slack_vireo": "slack",
                 "yahoo_finance_kestrel": "yahoo_finance", "finance_tools_orbit": "finance_tools",
                 "sec_edgar_ledger": "sec_edgar", "maverick_talon": "maverick",
                 "openbb_atlas": "openbb"}
_NUM_UNIT = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([a-zA-Z]*)\s*$")
_UNIT_DAYS = {"d": 1, "w": 7, "m": 30, "y": 365, "h": 1 / 24}

csv.field_size_limit(10 ** 7)


def parse_quantity(value, kind: str, parse: str | None) -> float | None:
    """The numeric quantity a value carries, or None if it carries none.

    ``kind`` decides only *whether* to look; the value's own shape decides *how* to
    read it. That split is deliberate. Measured on real traffic, the classifiers
    disagree about whether a paged `perPage` is a "count" or a "magnitude" — and under
    a label-driven parser that disagreement silently dropped 100% of one server's
    quantities, because a count parser demands a list and `perPage` is an integer.
    The distinction is real to a taxonomist and irrelevant here: both produce a number.

    ``range`` yields nothing on its own — a single endpoint is not a quantity. Spans
    are computed per call by :func:`span_of`, which needs the pair.
    """
    if kind in ("none", "range"):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, list):
        return float(len(value))
    if isinstance(value, dict):
        return float(len(value))
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if parse == "split:," and "," in text:
            return float(len([p for p in text.split(",") if p.strip()]))
        match = _NUM_UNIT.match(text)
        if match:
            number, unit = float(match.group(1)), match.group(2).lower()
            return number * _UNIT_DAYS.get(unit, 1) if unit else number
        # A single value where a collection was expected is a collection of one.
        return 1.0 if kind == "count" else None
    return None


def _as_epoch(value) -> float | None:
    """Seconds since epoch for an ISO-8601-ish timestamp, else None."""
    if not isinstance(value, str):
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def span_of(args: dict, range_args: list[str]) -> float | None:
    """The width in days between the widest pair of ``range`` endpoints in one call.

    A `timeMin` alone says nothing about breadth; `timeMin` with `timeMax` says how
    much calendar the call sweeps. Measured on real traffic this is the single largest
    class of quantity arguments, and a per-argument parser drops all of it.
    """
    stamps = [t for t in (_as_epoch(args.get(name)) for name in range_args) if t is not None]
    if len(stamps) < 2:
        return None
    return (max(stamps) - min(stamps)) / 86400.0


BANDS = (("critical", 100.0), ("high", 50.0), ("medium", 17.0), ("low", 0.0))


def band(score: float) -> str:
    """The scan's band for a score. A label over the number, not a decision."""
    for name, lower in BANDS:
        if score >= lower:
            return name
    return "low"


def fences(sorted_values: list[float]) -> tuple[float, float]:
    """Tukey's lower and upper fences for an already-sorted sample."""
    n = len(sorted_values)
    q1 = sorted_values[n // 4]
    q3 = sorted_values[(3 * n) // 4 - (1 if (3 * n) % 4 == 0 else 0)]
    iqr = q3 - q1
    return q1 - TUKEY_K * iqr, q3 + TUKEY_K * iqr


class BreadthScorer:
    """Per-call D, with the organization's own argument history as the reference."""

    def __init__(self, specs: dict[str, dict]) -> None:
        # {server: {tool: {arg: spec}}}
        self.specs = specs
        # Two views of the same window: `history` sorted for quartiles, `arrival` in
        # order so eviction removes the oldest value rather than the smallest.
        self.history: dict[tuple, list[float]] = defaultdict(list)
        self.arrival: dict[tuple, deque] = defaultdict(deque)
        #: Per-server tool call counts, the only input to the likelihood factor.
        self.tool_calls: dict[str, Counter] = defaultdict(Counter)
        self.sources: Counter = Counter()

    def quantities(self, server: str, tool: str, args: dict):
        """Yield ``(name, quantity, spec, source)`` for every breadth-carrying argument.

        An argument the caller omitted is not absent data — the call still happened, and
        something was still in force. Which thing depends on the server's own schema:

        * **the declared default.** When the schema states one, that value applies, so
          the call really did request it. Substituting it is fact, not imputation.
        * **nothing.** When no default is declared, the caller bounded nothing at all,
          and the honest reading is that this is at least as broad as the usual upper
          end. The value is imputed at Q3 and marked, so it can never be mistaken for
          an observation — imputed values are scored but never remembered, or the
          reference would end up learning from its own assumptions.
        """
        by_arg = self.specs.get(server, {}).get(tool)
        if not by_arg:
            return
        for name, spec in by_arg.items():
            if spec.get("kind", "none") in ("none", "unresolved", "range"):
                continue
            if name in args:
                quantity = parse_quantity(args[name], spec["kind"], spec.get("parse"))
                # A value the parser cannot read is not evidence of narrowness. Rather
                # than add a rule for whatever shape it turned out to be, it is imputed
                # like an omission and marked, so the gap stays visible in the reasons.
                yield name, quantity, spec, "value" if quantity is not None else "unreadable"
                continue
            declared = spec.get("default")
            if declared is not None:
                quantity = parse_quantity(declared, spec["kind"], spec.get("parse"))
                if quantity is not None:
                    yield name, quantity, spec, "default"
                continue
            yield name, None, spec, "omitted"

        declared_range = [n for n, sp in by_arg.items() if sp.get("kind") == "range"]
        if declared_range:
            span = span_of(args, [n for n in declared_range if n in args])
            if span is not None:
                yield "<span:days>", span, {"kind": "range", "ceiling": None}, "value"
            elif not any(n in args for n in declared_range):
                # The tool takes a time window and the caller gave none. That is not a
                # missing measurement, it is a request over all of time — the widest
                # window the tool offers. Imputed like any other omission.
                yield "<span:days>", None, {"kind": "range", "ceiling": None}, "omitted"

    def observe(self, server: str, tool: str, args: dict) -> None:
        """Fold a call's quantities into the history without scoring it (warm-up).

        Response status is deliberately ignored: the reference answers "what breadth does
        this organization ask for", not "what succeeded". Imputed values never enter —
        only what the caller actually sent, or the default the server actually applied.
        """
        for name, quantity, _spec, source in self.quantities(server, tool, args):
            if source in ("value", "default"):
                self._remember((server, tool, name), quantity)
        self.tool_calls[server][tool] += 1

    def widest_reach(self, server: str, tool: str) -> int:
        """The highest breadth level among this tool's *measurable* parameters.

        Counting every parameter, including ones no quantity can be read from, sounded
        principled -- the argument naming the asset sets how central everything else is by
        comparison -- but it degenerates in practice. The most central input is breadth 5
        on 17 of 17 GitHub tools and 9 of 9 Calendar tools, because every tool names its
        asset, and that input is always an identifier with no readable quantity. The most
        central *measurable* input is breadth 3 on most tools. So the ratio was a constant
        0.50 almost everywhere: not a discriminating weight, just a halving of every signal
        the runtime can actually read.

        Measured effect: with the old denominator a widening deviation moved the score by a
        median +0.227 on GitHub, against +0.348 for a flat rubric -- the weighting was
        costing a third of the signal it was meant to shape.
        """
        by_arg = self.specs.get(server, {}).get(tool) or {}
        levels = [spec.get("breadth") or DEFAULT_BREADTH for spec in by_arg.values()
                  if spec.get("kind") in MEASURABLE]
        if not levels:      # nothing readable on this tool; the weight cannot matter
            levels = [spec.get("breadth") or DEFAULT_BREADTH for spec in by_arg.values()]
        return max(levels) if levels else DEFAULT_BREADTH

    def _relative_weight(self, server: str, tool: str, spec: dict) -> float:
        """How much this quantity's deviation counts, against the tool's most central
        argument that a quantity can actually be read from.

        Absolute weighting would say a row limit counts the same everywhere. It does not:
        on a tool whose most central argument IS that limit, the limit is the call's reach
        and deserves full influence; on a tool that also takes a page of results, it
        governs a corner of what the call touches.

        The reference deliberately excludes arguments no quantity can be read from -- see
        :meth:`widest_reach` for why counting them collapsed this to a constant 0.50.
        """
        level = spec.get("breadth") or DEFAULT_BREADTH
        most_central = BREADTH_WEIGHT.get(self.widest_reach(server, tool), 0.0)
        if most_central <= 0:
            return 0.0
        return min(BREADTH_WEIGHT.get(level, 0.0) / most_central, 1.0)

    def _remember(self, key: tuple, quantity: float) -> None:
        """Add one observation to the rolling window, evicting the oldest if full."""
        seen, order = self.history[key], self.arrival[key]
        bisect.insort(seen, quantity)
        order.append(quantity)
        if len(order) > MAX_HISTORY:
            oldest = order.popleft()
            index = bisect.bisect_left(seen, oldest)
            if index < len(seen) and seen[index] == oldest:
                del seen[index]

    def deviation(self, key: tuple, quantity: float | None) -> tuple[float, str]:
        """How far one quantity departs from what this deployment actually asks for.

        ``B_MIN`` at the narrowest value ever observed, 1.0 anywhere between the quartiles,
        ``B_MAX`` at the upper Tukey fence and beyond. Both directions are earned against
        this deployment's own history, never against an absolute threshold.

        The factor was one-sided until the sensitivity sweep showed what that cost: gated
        at Q1 and capped at 1.0, it left 93.6% of real calls on exactly 1.0, so an ordinary
        page size and a request for a million records were indistinguishable and every
        widening deviation measured +0.0000 on all three servers.

        The original reasoning -- ``blast_radius`` already prices the worst one call can do,
        so the runtime may only discount -- confuses two different facts. ``blast_radius``
        is judged at design time from a schema and prices what the tool COULD reach. What a
        deployment actually asks for is not in it, and cannot be: the scan never sees
        traffic. A call exceeding observed practice is therefore new information rather
        than reach counted twice.

        A value is graded only against values this deployment actually passed. With too
        little history there is nothing to grade against and nothing is earned.
        """
        seen = self.history[key]
        if len(seen) < MIN_HISTORY:
            self.sources["no history"] += 1
            return 1.0, "no history"

        n = len(seen)
        q1 = seen[n // 4]
        q3 = seen[(3 * n) // 4 - (1 if (3 * n) % 4 == 0 else 0)]
        # The only thing that disqualifies an argument is having no room below Q1: no
        # value it could carry would be narrow, so it can say nothing about narrowness.
        # Counting it as "ordinary" instead would be wrong in a way that is silent and
        # total, because the combination below takes the LEAST discount any argument
        # justifies -- one such argument pins B to 1.0 for every call on the tool, however
        # narrow the others are. Real traffic produces them constantly: a page number is 1
        # in four calls out of five.
        #
        # Above Q3 the call exceeds what this deployment does, and that is information the
        # static cell cannot contain: blast_radius is judged at design time from a schema,
        # so it prices what the tool COULD reach, never what this org actually asks for.
        # Escalating here is not counting reach twice -- the cell counts capability, this
        # counts departure from observed practice. Without it the factor saturated: 93.6%
        # of real calls landed on exactly 1.0, so per_page=30 and per_page=1000000 were
        # indistinguishable and every widening deviation measured +0.0000.
        #
        # The upper Tukey fence is the right anchor here even though the lower one was not.
        # These quantities are positive and right-skewed, which pushes the lower fence
        # below zero and out of reach, but leaves the upper fence both reachable and
        # meaningful: it is the standard boundary between a large ordinary value and an
        # outlier.
        #
        # Q3 is deliberately not consulted for the DISCOUNT side. An earlier test rejected
        # the argument when
        # Q3 <= Q1, meaning to catch a sample with no variation, but that is not what it
        # detects: with a dominant default -- per_page is 30 in 58% of calls -- the whole
        # interquartile range collapses onto one value while the sample still spans 1..100.
        # The argument then flipped between disqualified and active as Q3 crossed, and
        # identical calls scored 0.771 or 0.908 depending only on when they arrived.
        if quantity is None:           # omitted, and the deployment does use this argument
            quantity = q3              # treat as the high end of normal: nothing earned

        # The escalation edge is a single high percentile, always -- never a rule that
        # switches on whether the IQR is degenerate. An earlier version used Q3 when the
        # IQR was positive and a fallback anchor when it was zero, and real traffic
        # oscillates across that boundary: per_page=100 flipped between "ordinary" and
        # "wide" as Q3 crossed, which drove the noise floor from 0.009 to 0.130. One
        # continuous rule cannot flip.
        #
        # A percentile also degrades gracefully where the quartiles do not. per_page is 30
        # in 58% of calls, which collapses Q1 and Q3 onto the same value while the sample
        # still spans 1..100; the ninetieth percentile stays meaningful throughout.
        edge = seen[min(len(seen) - 1, (ESCALATE_AT * len(seen)) // 100)]
        fence = edge * (1.0 + TUKEY_K)   # multiplicative: these quantities are positive
        if quantity > edge:
            reach = min((quantity - edge) / (fence - edge), 1.0) if fence > edge else 1.0
            self.sources["wide"] += 1
            return 1.0 + (B_MAX - 1.0) * reach, "wide"

        # An argument whose lower quartile sits on its own minimum can never be below Q1,
        # so it can say nothing about narrowness -- but it can still be wide, which is why
        # this is checked only after the escalation branch.
        if q1 <= seen[0]:
            self.sources["no floor"] += 1
            return 1.0, "no floor"

        if quantity >= q1:
            self.sources["ordinary"] += 1
            return 1.0, "ordinary"     # between the quartiles is this deployment's normal

        # Below Q1 only, ramped against the narrowest value this deployment has ever
        # used. Tukey's lower fence is the wrong anchor here: these quantities are
        # positive and right-skewed, so Q1 5 with Q3 75 puts the fence at -100 and no
        # real call can approach it. The smallest observed value is always reachable and
        # means something concrete — as narrow as this deployment has ever gone.
        floor = seen[0]
        position = min(max((quantity - floor) / (q1 - floor), 0.0), 1.0) if q1 > floor else 1.0
        self.sources["narrow"] += 1
        return B_MIN + (1.0 - B_MIN) * position, "narrow"

    def breadth_factor(self, server: str, tool: str, args: dict) -> tuple[float, list[str]]:
        """``B`` for one call: how far its arguments depart from this deployment's range.

        Each argument's deviation is scaled by how much that argument can reach, relative
        to the most central input on its tool — an unusual value on a minor argument counts
        for little either way.

        The call then takes the **most alarming** verdict any argument justifies. In the
        discount direction that means the least discount, because a call wide in any one
        dimension is not a narrow call; in the escalation direction it means the widest
        argument decides, because one runaway quantity is enough. ``max`` expresses both.
        """
        discounts, reasons, pending = [], [], []
        for name, quantity, spec, source in self.quantities(server, tool, args):
            key = (server, tool, name)
            b, decided = self.deviation(key, quantity)
            if decided not in NO_SIGNAL:
                weight = self._relative_weight(server, tool, spec)
                discounts.append(1.0 - weight * (1.0 - b))
                shown = source if quantity is None else f"{quantity:g}"
                tag = "" if source == "value" else f",{source}"
                reasons.append(f"{name}={shown}->{b:.2f}"
                               f"(b{spec.get('breadth') or '?'},w{weight:.2f},{decided}{tag})")
            if source in ("value", "default"):
                pending.append((key, quantity))

        for key, quantity in pending:  # causal: history updates only after scoring
            self._remember(key, quantity)

        return (max(discounts) if discounts else 1.0), reasons

    def likelihood_factor(self, server: str, tool: str) -> tuple[float, str]:
        """``L`` for one call: how usual this tool is for this deployment.

        The neutral point is the MEDIAN tool this deployment actually calls. No absolute
        threshold is chosen: "rare" means rare relative to how this deployment spreads its
        own traffic. Anchoring instead on an even split over the whole exposed catalog put
        every tool a deployment really uses above "even", so every call was discounted and
        nothing could sit at 1.0.

        Unlike ``B`` this moves both ways, but asymmetrically. A tool nobody calls raises
        risk to ``L_MAX``; one called constantly lowers it only to ``L_MIN``. Commonness
        exonerating is the failure mode with history behind it, so the discount side is
        deliberately the smaller one.

        The whole factor is then shrunk toward 1.0 in proportion to how much history the
        deployment actually has. ``B`` refuses to grade an argument until it has seen
        ``MIN_HISTORY`` values of it; without the same guard here a fresh deployment
        claimed a tool was "0.79x the median" and escalated 6.4% on the evidence of nine
        calls. Rarity is a statement about a distribution, and there is no distribution
        yet.
        """
        counts = self.tool_calls[server]
        used = sorted(c for c in counts.values() if c)
        if not used:
            return 1.0, "no history"
        total = sum(counts.values())
        # Neutral point is the MEDIAN tool this deployment calls, not an even split over
        # the whole catalog. Anchoring on the catalog made every tool a deployment
        # actually uses look common — six tools out of thirteen exposed put all six above
        # "even", so every call was discounted and nothing could sit at 1.0.
        reference = used[len(used) // 2] / total
        share = (counts[tool] + L_ALPHA * reference) / (total + L_ALPHA)
        ratio = share / reference if reference else 1.0
        if ratio < 1.0:
            raw = 1.0 + (L_MAX - 1.0) * (1.0 - ratio)
        else:
            raw = 1.0 - (1.0 - L_MIN) * (1.0 - 1.0 / ratio)

        # Confidence: a share is only estimable once there are enough calls per tool to
        # estimate one. MIN_HISTORY is reused as that per-tool requirement, so B and L
        # demand evidence of the same order before either is allowed to move the score.
        exposed = len(self.specs.get(server) or counts) or 1
        confidence = total / (total + MIN_HISTORY * exposed)
        factor = 1.0 + (raw - 1.0) * confidence
        if confidence < 0.5:
            return factor, (f"{ratio:.2f}x the median tool, held back to "
                            f"{confidence:.0%} on {total} calls")
        return factor, f"{ratio:.2f}x the median tool"

    def score(self, server: str, tool: str, args: dict) -> tuple[float, list[str]]:
        """``(B x L, reasons)`` for one call, then fold it into the history.

        Two independent factors. ``B`` never looks at how often a tool is called and ``L``
        never looks at argument values, so neither can double-count the other and each can
        be evaluated on its own.
        """
        b, reasons = self.breadth_factor(server, tool, args)
        lik, why = self.likelihood_factor(server, tool)
        self.tool_calls[server][tool] += 1
        reasons.append(f"L={lik:.2f}({why})")
        return b * lik, reasons


def load_specs() -> dict[str, dict]:
    """``{server: {tool: {arg: spec}}}`` from the scanner's ``tool_breadth`` output.

    The scan answers two things per input, neither of them a threshold: whether a quantity
    can be read from it and in what form (``kind``), and how central it is to the asset the
    call acts on (``breadth``, 1-5). The numbers -- how large is large *here* -- are built
    at runtime from traffic, never at scan time.
    """
    specs: dict[str, dict] = {}
    for server, stem in _CATALOG.items():
        path = SPEC_DIR / f"{stem}_scan.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        specs[server] = {
            tool: {entry["name"]: dict(entry) for entry in block["inputs"]}
            for tool, block in data["tools"].items()
        }
    return specs


def resolve_asset(cells: dict, org: str, asset: str) -> str:
    """Corpora sometimes drop the org prefix the scan uses."""
    if asset in cells:
        return asset
    prefix = org.split("_")[1]
    return f"{prefix}-{asset}" if f"{prefix}-{asset}" in cells else asset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CORPUS / "live_scale_all.csv")
    parser.add_argument(
        "--split", type=float, default=None,
        help="fraction of --corpus to use as warm-up before scoring the remainder "
             "(e.g. 0.5). Warm-up and test then come from the same distribution, which "
             "is the only way to tell a cold-start artefact from a real outlier.",
    )
    parser.add_argument("--emit", type=Path, default=None,
                        help="write one row per scored call to this CSV")
    parser.add_argument(
        "--warmup", type=Path, nargs="*", default=None,
        help="corpora to fold into the history BEFORE scoring, without scoring them. "
             "Real traffic here means the fences are set by observed practice rather "
             "than by the first few calls of the corpus under test.",
    )
    args_ns = parser.parse_args(argv)

    specs = load_specs()
    # Only github/slack/calendar have an LLM-scanned cells/bands artifact (ARM). The
    # finance servers have no such matrix yet (reports/scan_finance/README.md) — `cell`
    # stays unresolved for them rather than crashing the run, and `final`/`final_band`
    # are left blank in the emitted CSV, same as they already are for the real corpora
    # of the three servers that DO have one (see dynamic_layer/v2/README.md).
    artifacts = {}
    for org in ORG_TO_SERVER:
        path = ARM / f"{org}.json"
        if path.exists():
            artifacts[org] = json.loads(path.read_text())
    scorer = BreadthScorer(specs)

    if args_ns.warmup:
        warmed = 0
        for path in args_ns.warmup:
            for row in csv.DictReader(path.open()):
                server = ORG_TO_SERVER.get(row.get("org", ""))
                if not server:
                    continue
                try:
                    warm_args = json.loads(row.get("args") or "{}")
                except json.JSONDecodeError:
                    continue
                if isinstance(warm_args, dict):
                    scorer.observe(server, row["tool"], warm_args)
                    warmed += 1
        ready = sum(1 for v in scorer.history.values() if len(v) >= MIN_HISTORY)
        print(f"warm-up: {warmed} calls -> {len(scorer.history)} tracked quantities, "
              f"{ready} with enough history to judge\n")

    rows = list(csv.DictReader(args_ns.corpus.open()))
    if args_ns.split:
        cut = int(len(rows) * args_ns.split)
        for row in rows[:cut]:
            server = ORG_TO_SERVER.get(row.get("org", ""))
            if not server:
                continue
            try:
                split_args = json.loads(row.get("args") or "{}")
            except json.JSONDecodeError:
                continue
            if isinstance(split_args, dict):
                scorer.observe(server, row["tool"], split_args)
        ready = sum(1 for v in scorer.history.values() if len(v) >= MIN_HISTORY)
        print(f"split warm-up: first {cut} of {len(rows)} rows -> {len(scorer.history)} "
              f"tracked quantities, {ready} judgeable; scoring the remaining {len(rows) - cut}\n")
        rows = rows[cut:]

    emit = None
    if args_ns.emit:
        args_ns.emit.parent.mkdir(parents=True, exist_ok=True)
        emit = csv.writer(args_ns.emit.open("w", newline=""))
        emit.writerow(["index", "org", "server", "tool", "asset", "cell", "band",
                       "D", "final", "final_band", "quantities", "why"])

    scores: list[float] = []
    per_server: dict[str, list[float]] = defaultdict(list)
    scored = 0
    examples: list[str] = []

    started = time.perf_counter()
    for row in rows:
        org = row.get("org", "")
        server = ORG_TO_SERVER.get(org)
        if not server:
            continue
        try:
            call_args = json.loads(row.get("args") or "{}")
        except json.JSONDecodeError:
            call_args = {}
        if not isinstance(call_args, dict):
            call_args = {}

        d, reasons = scorer.score(server, row["tool"], call_args)
        scores.append(d)
        per_server[server].append(d)

        cells = artifacts.get(org, {}).get("cells", {})
        asset = resolve_asset(cells, org, row.get("asset", ""))
        cell = cells.get(asset, {}).get(row["tool"])
        final_v = min(SCORE_MAX, cell * d) if cell is not None else None
        if emit is not None:
            emit.writerow([row.get("index", ""), org, server, row["tool"], asset,
                           cell if cell is not None else "",
                           band(cell) if cell is not None else "",
                           f"{d:.4f}", f"{final_v:.2f}" if final_v is not None else "",
                           band(final_v) if final_v is not None else "",
                           len(reasons), "; ".join(reasons)])
        if cell is not None:
            scored += 1
            if len(examples) < 5 and d > 1.05:
                examples.append(f"{row['tool']}: cell {cell} x {d:.2f} = {final_v:.1f}  "
                                f"[{'; '.join(reasons)}]")
    elapsed = time.perf_counter() - started

    total = len(scores)
    ordered = sorted(scores)
    print(f"corpus: {args_ns.corpus.name}  rows scored: {total}  (cell resolved: {scored})\n")
    print(f"{'':<12}{'n':>7}{'min':>7}{'p25':>7}{'median':>8}{'p75':>7}{'max':>7}"
          f"{'<1.0':>8}{'>1.0':>8}")

    def summarise(label: str, values: list[float]) -> None:
        if not values:
            return
        v = sorted(values)
        n = len(v)
        print(f"{label:<12}{n:>7}{v[0]:>7.2f}{v[n // 4]:>7.2f}{v[n // 2]:>8.2f}"
              f"{v[3 * n // 4]:>7.2f}{v[-1]:>7.2f}"
              f"{sum(1 for x in v if x < 0.999) / n:>7.0%}"
              f"{sum(1 for x in v if x > 1.001) / n:>7.0%}")

    summarise("all", ordered)
    for server, values in sorted(per_server.items()):
        summarise(server, values)
    print(f"\ndistinct scores: {len({round(x, 4) for x in scores})}")

    print("\nwhat decided each quantity:")
    for source, count in scorer.sources.most_common():
        print(f"  {source:<20}{count:>8}")

    if examples:
        print("\nexamples where D = 1.3:")
        for line in examples:
            print(f"  {line}")

    rate = total / elapsed if elapsed else float("inf")
    print(f"\nspeed: {total} calls in {elapsed * 1000:.1f} ms "
          f"= {rate:,.0f} calls/sec ({elapsed / max(total, 1) * 1e6:.1f} us/call)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
