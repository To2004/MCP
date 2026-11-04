"""Does the dynamic layer stay quiet on a mostly-ordinary organisation, and does it surface gray risk?

The world (``normal_org_world.py``): 150 agents, 180 days, the real GitHub MCP tools; almost all
calls ordinary, ordinary life changes and three org-wide changes labelled, plus rare gray
episodes (risky but not attacks). The first 90 days are history; days 90-179 are scored.

Engines (``normal_org_engines.py``): the shipped engine (v1), the documented v2, v2 with each
proposed fix alone and all together, the v3 candidates, ``v3 (decided)`` (DIMENSION_FORMULAS_v3.md)
and ``v4`` (DIMENSION_FORMULAS.md: every "new for him" check in Typical Footprint), with v4's two
partial switches. Before anything else, ``Variant(Flags())`` must reproduce the shipped engine
exactly on a sample of agents; ``--check-port`` checks the shipped v3 and v4 on every message.

Measures, per engine:
- false alarms: ordinary agent-days at x3 or more, and what caused them;
- ordinary life changes and org-wide changes at x3 or more;
- the daily review list (top 4 or 8 agent-days of 150): ties at the cut, the share of gray
  episodes it catches (ties broken at random, by the number of strange dimensions, or by
  static x M), and what fills it;
- gray episodes: caught at x3 at all, and the share of their calls at x3 (gating, call by call);
- hand-made scenarios for single problems (calls vs days, training, onboarding, new tool, a
  fresh identity, cloud runner networks).

Run:  uv run python reports/experiments/dynamic_dimensions/normal_org_sim.py [--agents 150]
Writes results/normal_org_sim.json and results/normal_org_sim.md.
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import random
import sys
import time
from collections import Counter, defaultdict
from dataclasses import replace
from multiprocessing import get_context
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from mcp_security.behaviour.engine import (  # noqa: E402
    BURST,
    SEQUENCE,
    BehaviourConfig,
    BehaviourEngine,
    Message,
    client_family,
    network_of,
)
from mcp_security.behaviour.policy import derive_policy  # noqa: E402
from normal_org_engines import MANY_ASSETS, Flags, Variant  # noqa: E402
from normal_org_world import (  # noqa: E402
    BASE_DAY,
    CATALOG,
    DAY,
    HOUR,
    PROFILES,
    REVIEW_TOOLS,
    build_world,
)

HERE = Path(__file__).parent
SCRATCH = Path(os.environ.get("NORMAL_ORG_SCORES", "/tmp/normal_org_scores.pkl"))
EVAL_FROM = 90
BUDGETS = (4, 8)
ALERT = 3.0
#: the documented limits; the shipped engine runs design v1 under it, as it did before v3
CONFIG = BehaviourConfig(design="v1", requires_before={"merge_pull_request": REVIEW_TOOLS})
LEARN_DAYS = (
    30  # "learned limits": policy.derive_policy on the first 30 days, as a deployment would
)
ALL_FIXES = Flags(
    v2=True,
    days=True,
    daily=True,
    tiebreak=0.3,
    rule_rarity=True,
    org_discount=3,
    novelty_warmup_days=14,
)
#: what the misses called for: breadth, writes and repetition per hour, sensitive first looks,
#: weekend fallback, a size limit per tool
NEW_DETECTORS = Flags(
    v2=True, extra_dims=True, sensitive_this_only=True, tod_fallback=4, per_tool_size=True
)
#: the new detectors plus the fixes that helped; rule rarity only for the habit rules whose
#: habit is benign (burst, risky order), not for request size
RECOMMENDED = replace(
    NEW_DETECTORS,
    daily=True,
    tiebreak=0.3,
    rule_rarity=True,
    rarity_rules=frozenset({BURST, SEQUENCE}),
    org_discount=3,
    novelty_warmup_days=14,
)
#: the v3 candidate (2026-10-20 decisions): same call in 10 minutes and writes per hour in
#: Typical Cadence; distinct assets per hour as a count; a first look at a sensitive asset as a
#: Policy rule; size limits per tool, learned; history updated once a day; 14 days of
#: onboarding; weekends blended with all days; M stays the max (ties are broken when ranking)
V3 = Flags(
    v2=True,
    daily=True,
    rule_rarity=True,
    rarity_rules=frozenset({BURST, SEQUENCE, MANY_ASSETS}),
    org_discount=3,
    novelty_warmup_days=14,
    same_call_10m=True,
    writes_per_hour=True,
    assets_per_hour="count",
    sensitive_rule=True,
    weekend="blend",
    per_tool_size=True,
)
#: v3 as decided (2026-10-20, second round): distinct assets per hour as a count with the
#: learned rule as a backstop; M is only the max; the first-look rule graded by the asset's
#: sensitivity (0.1 a level below 5) and the tool's static level (0.05 a level below a write).
#: With history updated once a day, the warm-up is his first day, and the rules that need none
#: of his past still fire during it.
V3_FINAL = replace(
    V3,
    assets_per_hour="both",
    sensitive_steps=(0.1, 0.05),
    first_day_warmup=True,
    warmup_rules=True,
)
#: v3 as written into DIMENSION_FORMULAS.md: the first-look rule graded by the asset only
#: (sensitivity 5 -> 0.9, 4 -> 0.8; grading by the tool too gained nothing in the five
#: organisations), not capped by the org discount (in the large organisation it hid peeks at
#: secrets that 3 other agents had also started reading that week), with request-size limits
#: learned per agent-day
V3_DECIDED = replace(V3_FINAL, sensitive_steps=(0.1, 0.0), sensitive_org_discount=False)
#: v4 (2026-10-21): every "new for him" check in Typical Footprint, none as a rule. Network and
#: client app are rarity dimensions; a first-time tool goes through tool rarity; the first look
#: at a sensitive asset is a floor on the asset's score. The rest is v3 (decided).
V4 = replace(V3_DECIDED, origin_rarity=True, tool_rarity_first_use=True, sensitive_floor=True)
SIZE_QUANTILE, SIZE_MIN_CALLS = 0.999, 200
SIZE_DAY_QUANTILE, SIZE_MIN_DAYS = 0.995, 50  # per agent-day, as policy.py learns its one limit
BREADTH_QUANTILE = 0.995  # the "many assets" rule: like policy.py, at most 0.5% of agent-days
#: engine name -> (switches, or None for the shipped engine; "doc" limits or "learned" limits)
VARIANTS: dict[str, tuple[Flags | None, str]] = {
    "v1 (shipped)": (None, "doc"),
    "v2": (Flags(v2=True), "doc"),
    "v2 + days": (Flags(v2=True, days=True), "doc"),
    "v2 + daily update": (Flags(v2=True, daily=True), "doc"),
    "v2 + tie-break": (Flags(v2=True, tiebreak=0.3), "doc"),
    "v2 + rule rarity": (Flags(v2=True, rule_rarity=True), "doc"),
    "v2 + org discount": (Flags(v2=True, org_discount=3), "doc"),
    "v2 + 14-day onboarding": (Flags(v2=True, novelty_warmup_days=14), "doc"),
    "v2 + all fixes": (ALL_FIXES, "doc"),
    "v1, learned limits": (None, "learned"),
    "v2, learned limits": (Flags(v2=True), "learned"),
    "v2 + all fixes, learned limits": (ALL_FIXES, "learned"),
    "v2 + new detectors, learned limits": (NEW_DETECTORS, "learned"),
    "v2 + recommended, learned limits": (RECOMMENDED, "learned"),
    "v2 + recommended + days, learned limits": (replace(RECOMMENDED, days=True), "learned"),
    "v2 + recommended (first look only), learned limits": (
        replace(RECOMMENDED, sensitive_first_look=True),
        "learned",
    ),
    "v3": (V3, "learned"),
    "v3, assets/hour as a rule": (replace(V3, assets_per_hour="rule"), "learned"),
    "v3, weekend split": (replace(V3, weekend="split"), "learned"),
    "v3, weekend fallback": (replace(V3, weekend="fallback"), "learned"),
    "v3, weekend flag": (replace(V3, weekend="flag"), "learned"),
    "v3 without writes/hour": (replace(V3, writes_per_hour=False), "learned"),
    "v3 + tie-break formula": (replace(V3, tiebreak=0.3), "learned"),
    "v3 final": (V3_FINAL, "learned"),
    "v3 final, 5-call warm-up": (
        replace(V3_FINAL, first_day_warmup=False, warmup_rules=False),
        "learned",
    ),
    "v3 final, first-day warm-up without rules": (
        replace(V3_FINAL, warmup_rules=False),
        "learned",
    ),
    "v3 final, flat first-look rule": (replace(V3_FINAL, sensitive_steps=(0.0, 0.0)), "learned"),
    "v3 final, first look by asset only": (
        replace(V3_FINAL, sensitive_steps=(0.1, 0.0)),
        "learned",
    ),
    "v3 final, first look anchored at a read": (
        replace(V3_FINAL, sensitive_anchor=3),
        "learned",
    ),
    "v3 final, first look tool step 0.1": (
        replace(V3_FINAL, sensitive_steps=(0.1, 0.1)),
        "learned",
    ),
    "v3 final, size limits per agent-day": (V3_FINAL, "learned per day"),
    "v3 final, read anchor, sizes per agent-day": (
        replace(V3_FINAL, sensitive_anchor=3),
        "learned per day",
    ),
    "v3 (decided)": (V3_DECIDED, "policy.py"),
    "v3 (decided), org discount on first looks": (
        replace(V3_DECIDED, sensitive_org_discount=True),
        "learned per day",
    ),
    "v3 (decided), network and app in Footprint": (
        replace(V3_DECIDED, origin_rarity=True),
        "policy.py",
    ),
    "v3 (decided), new tool through tool rarity": (
        replace(V3_DECIDED, tool_rarity_first_use=True),
        "policy.py",
    ),
    "v4": (V4, "policy.py"),
}
CONFIGS: dict[str, BehaviourConfig] = {"doc": CONFIG}
SIZE_LIMITS: dict[str, dict[str, int]] = {}  # limits name -> tool -> bytes
#: tool -> static level (2 metadata, 3 read, 4 write), as the gateway reads it from the scan
TOOL_LEVELS = {tool: level for tool, (_, level) in CATALOG.items()}
BREADTH: dict[str, int] = {}  # {"limit": n}, learned
WORLD: dict[str, list] = {}
FIRST_USES: dict = {}


def message(aid: str, r: tuple) -> Message:
    return Message(r[0], aid, r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9])


def make_observer(name: str):
    """``observe(message) -> (M, strongest, scores)`` for one engine."""
    flags, limits = VARIANTS[name]
    config = CONFIGS[limits]
    if flags is None:
        engine = BehaviourEngine(config)

        def observe(m: Message):
            v = engine.observe(m)
            return v.multiplier, v.strongest, v.scores

        return observe
    if limits == "policy.py":  # everything from the shipped policy learner
        return v3_variant(flags, config).observe
    return Variant(
        flags, config, FIRST_USES, SIZE_LIMITS.get(limits), BREADTH.get("limit"), TOOL_LEVELS
    ).observe


def v3_variant(flags: Flags, config: BehaviourConfig) -> Variant:
    """The simulation engine with the limits ``policy.py`` learned (per tool, many assets)."""
    return Variant(
        flags,
        config,
        FIRST_USES,
        config.request_limit_by_tool,
        config.many_assets_per_hour,
        TOOL_LEVELS,
    )


def learned_config(world: dict, base: BehaviourConfig) -> BehaviourConfig:
    """The limits and required steps a deployment would learn from its first days."""
    cutoff = (BASE_DAY + LEARN_DAYS) * DAY
    msgs = [message(aid, r) for aid, rows in world.items() for r in rows if r[0] < cutoff]
    return derive_policy(msgs, base=base)


def learned_size_limits(world: dict) -> dict[str, int]:
    """Per tool, the request size only 0.1% of its calls exceed in the first days (whole KB)."""
    cutoff = (BASE_DAY + LEARN_DAYS) * DAY
    sizes: dict[str, list[int]] = defaultdict(list)
    for rows in world.values():
        for r in rows:
            if r[0] < cutoff and r[1] == "tools/call":
                sizes[r[3]].append(r[9])
    limits = {}
    for tool, values in sizes.items():
        if len(values) >= SIZE_MIN_CALLS:
            values.sort()
            q = values[min(len(values) - 1, int(SIZE_QUANTILE * len(values)))]
            limits[tool] = -(-q // 1000) * 1000
    return limits


def learned_size_limits_per_day(world: dict) -> dict[str, int]:
    """Per tool, the agent-day's largest request that only 0.5% of agent-days exceed in the
    first days (whole KB): the way policy.py learns its one org-wide limit."""
    cutoff = (BASE_DAY + LEARN_DAYS) * DAY
    biggest: dict[str, dict[tuple, int]] = defaultdict(dict)
    for aid, rows in world.items():
        for r in rows:
            if r[0] < cutoff and r[1] == "tools/call":
                days, key = biggest[r[3]], (aid, int(r[0] // DAY))
                days[key] = max(days.get(key, 0), r[9])
    limits = {}
    for tool, days in biggest.items():
        if len(days) >= SIZE_MIN_DAYS:
            values = sorted(days.values())
            q = values[min(len(values) - 1, int(SIZE_DAY_QUANTILE * len(values)))]
            limits[tool] = -(-q // 1000) * 1000
    return limits


def learned_breadth_limit(world: dict) -> int:
    """Org-wide: distinct assets in an agent's busiest hour, at the quantile of agent-days."""
    cutoff = (BASE_DAY + LEARN_DAYS) * DAY
    busiest: dict[tuple, int] = defaultdict(int)
    for aid, rows in world.items():
        window: list = []
        counts: Counter = Counter()
        start = 0
        for r in rows:
            if r[0] >= cutoff:
                break
            if r[1] != "tools/call" or not r[4]:
                continue
            window.append((r[0], r[4]))
            counts[r[4]] += 1
            while window[start][0] <= r[0] - HOUR:
                counts[window[start][1]] -= 1
                if not counts[window[start][1]]:
                    del counts[window[start][1]]
                start += 1
            key = (aid, int(r[0] // DAY))
            busiest[key] = max(busiest[key], len(counts))
    values = sorted(busiest.values())
    return values[min(len(values) - 1, int(BREADTH_QUANTILE * len(values)))]


def first_uses(world: dict) -> dict:
    """(kind, value) -> (times, agents) of each agent's first use in 90 days, in time order: a
    value he had not used in the 90 days before, once a day, as the shipped engine counts them
    for its org discount. (Results before ``v3 (decided)`` counted first uses ever.)"""
    first: dict[tuple, list] = defaultdict(list)
    window = CONFIG.history_days
    for aid, rows in world.items():
        last: dict[tuple, int] = {}
        for r in rows:
            day = int(r[0] // DAY)
            items = [("network", network_of(r[7], CONFIG)), ("client", client_family(r[8]))]
            if r[1] == "tools/call":
                items += [("tool", r[3]), ("asset", r[4])]
            for kind, value in items:
                if value is None:
                    continue
                seen = last.get((kind, value))
                if seen is None or seen <= day - window:
                    first[(kind, value)].append((r[0], aid))
                last[(kind, value)] = day
    out = {}
    for key, uses in first.items():
        uses.sort()
        out[key] = ([t for t, _ in uses], [a for _, a in uses])
    return out


def check_equivalence(aids: list[str], design: str = "v1") -> int:
    """The shipped engine's design v1 (v2) must give the multiplier of the simulation engine
    with no switches (with ``v2``) on every message of ``aids``."""
    flags = Flags() if design == "v1" else Flags(v2=True)
    n = 0
    for aid in aids:
        shipped = BehaviourEngine(replace(CONFIG, design=design))
        mirror = Variant(flags, CONFIG)
        for r in WORLD[aid]:
            m = message(aid, r)
            a, b = shipped.observe(m).multiplier, mirror.observe(m)[0]
            if abs(a - b) > 1e-12:
                raise AssertionError(f"{design} differs from the simulation: {aid} {r} {a} {b}")
            n += 1
    return n


PORTED = {"v3": V3_DECIDED, "v4": V4}  # the shipped engine's design -> its simulation switches


def variant_shard(job: tuple[str, list[str]]) -> dict[str, tuple[np.ndarray, list]]:
    """A ported design in the simulation engine, per agent: (M, strongest) of every message."""
    design, aids = job
    out = {}
    for aid in aids:
        observe = v3_variant(PORTED[design], CONFIGS["policy.py"]).observe
        results = [observe(message(aid, r))[:2] for r in WORLD[aid]]
        out[aid] = (np.array([m for m, _ in results]), [top for _, top in results])
    return out


def check_port(workers: int, design: str = "v3") -> dict:
    """Design v3 or v4: the shipped engine, fed every agent's messages in one stream in time
    order (its org discount sees all agents at once), must give the simulation engine's
    multiplier and strongest dimension on every message."""
    aids = sorted(WORLD, key=lambda a: -len(WORLD[a]))
    expected: dict = {}
    jobs = [(design, aids[i::workers]) for i in range(workers)]
    with get_context("fork").Pool(workers) as pool:
        for part in pool.imap_unordered(variant_shard, jobs):
            expected.update(part)
    stream = sorted((r[0], aid, i) for aid, rows in WORLD.items() for i, r in enumerate(rows))
    engine = BehaviourEngine(replace(CONFIGS["policy.py"], design=design))
    t0, differ, examples = time.time(), 0, []
    for _, aid, i in stream:
        verdict = engine.observe(message(aid, WORLD[aid][i]))
        m_sim, top_sim = expected[aid][0][i], expected[aid][1][i]
        if abs(verdict.multiplier - m_sim) > 1e-12 or verdict.strongest != top_sim:
            differ += 1
            if len(examples) < 5:
                examples.append((aid, i, verdict.multiplier, m_sim, verdict.strongest, top_sim))
    seconds = time.time() - t0
    return {
        "messages": len(stream),
        "differ": differ,
        "examples": examples,
        "shipped_seconds": round(seconds, 1),
        "messages_per_second": round(len(stream) / seconds),
    }


def score_shard(job: tuple[str, list[str]]):
    name, aids = job
    observe = make_observer(name)
    days: dict[tuple, list] = {}
    gray_calls: dict[str, list] = defaultdict(list)
    ordinary = Counter()
    for aid in aids:
        for r in WORLD[aid]:
            M, top, scores = observe(message(aid, r))
            d = int(r[0] // DAY) - BASE_DAY
            if d < EVAL_FROM:
                continue
            rec = days.get((aid, d))
            if rec is None:
                rec = days[(aid, d)] = [0.0, 0.0, None, set(), 0, 0.0]
            if M > rec[0]:
                rec[0], rec[2] = M, top
                ordered = sorted(scores.values(), reverse=True)
                rec[5] = ordered[1] if len(ordered) > 1 else 0.0
            rec[1] = max(rec[1], r[10] * M)
            rec[3].update(k for k, s in scores.items() if s > 0.5)
            if r[1] == "tools/call":
                rec[4] += 1
                if r[12]:
                    gray_calls[r[12]].append(M)
                elif not r[11]:
                    ordinary["calls"] += 1
                    ordinary["calls_x2"] += M >= 2
                    ordinary["calls_x3"] += M >= ALERT
    return (
        name,
        {k: (v[0], v[1], v[2], len(v[3]), v[5]) for k, v in days.items()},
        dict(gray_calls),
        ordinary,
    )


def day_labels(world: dict) -> dict:
    labels: dict[tuple, tuple[set, set]] = {}
    for aid, rows in world.items():
        for r in rows:
            d = int(r[0] // DAY) - BASE_DAY
            if d < EVAL_FROM:
                continue
            tags, grays = labels.setdefault((aid, d), (set(), set()))
            if r[11]:
                tags.update(r[11].split("|"))
            if r[12]:
                grays.add(r[12])
    return labels


# ── the daily review list ──────────────────────────────────────────────────────────────────
def topk_probability(keys: list[tuple], day: np.ndarray, k: int) -> tuple[np.ndarray, dict]:
    """Chance each agent-day is on its day's top-k list when ties are broken at random, plus
    how often the cut falls inside a tie."""
    p = np.zeros(len(keys))
    tied_days, tie_sizes, n_days = 0, [], 0
    for d in np.unique(day):
        ix = np.flatnonzero(day == d)
        groups: dict[tuple, list[int]] = defaultdict(list)
        for i in ix:
            groups[keys[i]].append(i)
        above = 0
        n_days += 1
        for key in sorted(groups, reverse=True):
            members = groups[key]
            t = len(members)
            if above >= k:
                break
            if above + t <= k:
                p[members] = 1.0
            else:
                p[members] = (k - above) / t
                tied_days += 1
                tie_sizes.append(t)
            above += t
    return p, {
        "days_cut_in_a_tie": tied_days / max(1, n_days),
        "median_tie_size_at_cut": float(np.median(tie_sizes)) if tie_sizes else 0.0,
    }


def analyse(days: dict, labels: dict, gray_calls: dict, ordinary: Counter, roles: dict) -> dict:
    keys = list(days)
    M = np.array([days[k][0] for k in keys])
    R = np.array([days[k][1] for k in keys])
    top = [days[k][2] for k in keys]
    breadth = np.array([days[k][3] for k in keys])
    second = np.array([days[k][4] for k in keys])
    day = np.array([k[1] for k in keys])
    bot = np.array(["bot" in roles[k[0]] for k in keys])
    cat = np.array(
        ["gray" if labels[k][1] else "change" if labels[k][0] else "ordinary" for k in keys]
    )
    hot = M >= ALERT
    out: dict = {"agent_days": len(keys)}
    ordinary_mask = cat == "ordinary"
    out["ordinary_days_x3"] = float(hot[ordinary_mask].mean())
    out["ordinary_days_x2"] = float((M[ordinary_mask] >= 2).mean())
    out["ordinary_days_x3_people"] = float(hot[ordinary_mask & ~bot].mean())
    out["ordinary_days_x3_bots"] = float(hot[ordinary_mask & bot].mean())
    causes = Counter(top[i] for i in np.flatnonzero(ordinary_mask & hot))
    total = max(1, sum(causes.values()))
    out["ordinary_x3_causes"] = {c: round(v / total, 3) for c, v in causes.most_common(8)}
    out["ordinary_calls_x3"] = ordinary["calls_x3"] / max(1, ordinary["calls"])
    tags: dict[str, list[int]] = defaultdict(list)
    for i, k in enumerate(keys):
        if cat[i] == "change":
            for t in labels[k][0]:
                tags[t].append(i)
    out["changes_x3"] = {
        t: {
            "days": len(ix),
            "x3": round(float(hot[ix].mean()), 3),
            "cause": Counter(top[i] for i in ix if hot[i]).most_common(1)[0][0]
            if hot[ix].any()
            else "-",
        }
        for t, ix in sorted(tags.items())
    }
    n_days = len(np.unique(day))
    out["alerts_per_day"] = {
        c: float(hot[cat == c].sum() / n_days) for c in ("ordinary", "change", "gray")
    }
    episodes: dict[str, list[int]] = defaultdict(list)
    for i, k in enumerate(keys):
        for ep in labels[k][1]:
            episodes[ep].append(i)
    rankings = {
        "M, ties at random": [(round(float(m), 9),) for m in M],
        "M, then strange dimensions": [(round(float(m), 9), int(b)) for m, b in zip(M, breadth)],
        "M, then second score": [
            (round(float(m), 9), round(float(s), 9)) for m, s in zip(M, second)
        ],
        "static x M": [(round(float(r), 9),) for r in R],
    }
    out["review"] = {}
    for k in BUDGETS:
        for rank_name, rank_keys in rankings.items():
            p, ties = topk_probability(rank_keys, day, k)
            caught = [1 - np.prod(1 - p[ix]) for ix in episodes.values()]
            fill = {
                c: float(p[cat == c].sum() / (k * n_days)) for c in ("ordinary", "change", "gray")
            }
            out["review"][f"top {k} | {rank_name}"] = {
                "gray_caught": float(np.mean(caught)) if caught else None,
                "fill": fill,
                **ties,
            }
    kinds: dict[str, list] = defaultdict(list)
    for ep, ms in gray_calls.items():
        kinds[ep.split(":")[0]].append(ms)
    out["gray"] = {
        kind: {
            "episodes": len(v),
            "caught_x3": float(np.mean([max(ms) >= ALERT for ms in v])),
            "median_max_M": float(np.median([max(ms) for ms in v])),
            "calls_x3": float(np.mean([np.mean(np.array(ms) >= ALERT) for ms in v])),
        }
        for kind, v in sorted(kinds.items())
    }
    out["gray_episodes"] = len(gray_calls)
    out["gray_caught_x3"] = float(np.mean([max(ms) >= ALERT for ms in gray_calls.values()]))
    return out


# ── hand-made scenarios ────────────────────────────────────────────────────────────────────
REPOS5 = ("t0-svc0", "t0-svc1", "t0-svc2", "t0-svc3", "t0-svc4")
TOOLS4 = ("get_file_contents", "list_issues", "get_issue", "search_code")


def mk(
    day: int,
    hour: float,
    agent: str = "a",
    tool: str = "get_file_contents",
    asset: str | None = "t0-svc0",
    sens: int = 2,
    op: str = "read",
    method: str = "tools/call",
    session: str | None = None,
    address: str = "203.0.1.1",
    client: str = "claude-code/1.0",
    size: int = 200,
) -> Message:
    call = method == "tools/call"
    return Message(
        (BASE_DAY + day) * DAY + hour * HOUR,
        agent,
        method,
        session or f"{agent}-{day}-{int(hour)}",
        tool if call else None,
        asset if call else None,
        sens if call else None,
        op if call else None,
        address,
        client,
        size,
    )


def work(
    day: int,
    agent: str = "a",
    n: int = 20,
    start: float = 9.0,
    end: float = 17.0,
    repos=REPOS5,
    tools=TOOLS4,
    **kw,
) -> list[Message]:
    sid = f"{agent}-{day}"
    out = [mk(day, start - 0.01, agent, method="initialize", session=sid, **kw)]
    for i in range(n):
        out.append(
            mk(
                day,
                start + (end - start) * i / n,
                agent,
                tools[i % len(tools)],
                repos[i % len(repos)],
                session=sid,
                **kw,
            )
        )
    return out


def weekdays(first: int, last: int) -> list[int]:
    return [d for d in range(first, last) if d % 7 < 5]


def with_init(msgs: list[Message], seen: set) -> list[Message]:
    """Start every new session with ``initialize``, as an ordinary client does."""
    out = []
    for m in msgs:
        if m.session not in seen:
            seen.add(m.session)
            if m.method != "initialize":
                out.append(
                    Message(
                        m.ts - 0.5,
                        m.agent,
                        "initialize",
                        m.session,
                        address=m.address,
                        client=m.client,
                        size=170,
                    )
                )
        out.append(m)
    return out


def run(name: str | Flags, history: list[Message], test: list[Message]) -> list[tuple]:
    """Feed ``history``, then score ``test``; the results of its tool calls, in order.
    ``name``: an engine of VARIANTS, or switches run with the doc's limits."""
    if isinstance(name, str):
        observe = make_observer(name)
    else:
        observe = Variant(name, CONFIG, tool_levels=TOOL_LEVELS).observe
    seen: set = set()
    for m in with_init(history, seen):
        observe(m)
    results = []
    for m in with_init(test, seen):
        r = observe(m)
        if m.method == "tools/call":
            results.append(r)
    return results


def worst(results: list[tuple]) -> str:
    M, top, _ = max(results, key=lambda r: r[0])
    return f"x{M:.2f} ({top})"


def scenarios() -> list[dict]:
    rows = []

    def add(case: str, what: str, values: dict) -> None:
        rows.append({"case": case, "what": what, **values})

    names = ("v1 (shipped)", "v2", "v2 + days", "v2 + daily update", "v2 + 14-day onboarding")
    base = [m for d in weekdays(0, 60) for m in work(d)]

    # 1. calls vs days: one busy night makes 3 a.m. look ordinary for 90 days
    night = [mk(10, 3 + i / 60, session="a-10-night") for i in range(30)]
    history = sorted(base + night, key=lambda m: m.ts)
    probe = [mk(45, 3.0 + i / 30, session="a-45-night") for i in range(3)]
    add(
        "One night of 30 calls at 3 a.m. (day 10); a 3 a.m. call on day 45",
        "max M of the 3 a.m. calls",
        {n: worst(run(n, history, probe)) for n in names[:3]}
        | {"control (no earlier night), v2": worst(run("v2", base, probe))},
    )

    # 2. training a new asset within one day
    q4 = [mk(62, 10 + i / 30, asset="q4-plan", session="a-62") for i in range(12)]
    for n in ("v2", "v2 + daily update"):
        res = run(n, base, q4)
        add(
            "New folder q4-plan, 12 calls on its first day",
            f"M per call, {n}",
            {"sequence": " ".join(f"{r[0]:.1f}" for r in res)},
        )

    # 3. onboarding exploration hides later first touches
    explore = [
        mk(
            d,
            9 + i / 3,
            agent="b",
            asset=f"t{(3 * d + i) % 10}-svc{(3 * d + i) // 10 % 6}",
            session=f"b-{d}",
        )
        for d in weekdays(0, 14)
        for i in range(20)
    ]
    later = [m for d in weekdays(14, 73) for m in work(d, agent="b")]
    peek = [mk(73, 11, agent="b", asset="payroll-service", sens=5, session="b-73")]
    add(
        "New hire explores ~30 repos in 2 weeks; first look at payroll on day 73",
        "M of the payroll call",
        {
            n: worst(run(n, explore + later, peek))
            for n in ("v1 (shipped)", "v2", "v2 + 14-day onboarding")
        }
        | {
            "control (no exploration), v2": worst(
                run("v2", [m for d in weekdays(0, 73) for m in work(d, agent="b")], peek)
            )
        },
    )

    # 4. a never-used tool: habitual, tool explorer, new hire on day 2
    first_tool = [mk(62, 11, tool="create_release", op="write", session="a-62")]
    explorer = list(base)
    for w, d in enumerate(range(3, 60, 7)):
        explorer.append(mk(d, 12, tool=f"rare_tool_{w}", session=f"a-{d}-x"))
    explorer.sort(key=lambda m: m.ts)
    hire = work(0, agent="h", n=8, tools=("get_file_contents",))
    hire_day1 = [mk(1, 10, agent="h", tool="list_pull_requests", op="metadata", session="h-1")]
    add(
        "First use of a tool he never used",
        "M",
        {
            "habitual agent, v1": worst(run("v1 (shipped)", base, first_tool)),
            "habitual agent, v2": worst(run("v2", base, first_tool)),
            "tries a new tool every week, v1": worst(run("v1 (shipped)", explorer, first_tool)),
            "tries a new tool every week, v2": worst(run("v2", explorer, first_tool)),
            "new hire on day 2, v1": worst(run("v1 (shipped)", hire, hire_day1)),
            "new hire on day 2, v2": worst(run("v2", hire, hire_day1)),
        },
    )

    # 5. a fresh identity explores on day 1, then touches something sensitive on day 2
    fresh = [mk(0, 9 + i / 60, agent="c", asset="t0-svc0", session="c-0") for i in range(5)]
    fresh += [
        mk(0, 10 + i / 30, agent="c", asset=f"t{i % 10}-svc{i // 10}", session="c-0")
        for i in range(20)
    ]
    day1 = [mk(0, 11, agent="c", asset="payroll-service", sens=5, session="c-0b")]
    day2 = [mk(1, 11, agent="c", asset="customer-data-pipeline", sens=5, session="c-1")]
    add(
        "Fresh identity: 5 warm-up calls, 20 repos on day 1",
        "M",
        {
            "payroll on day 1, v2": worst(run("v2", fresh, day1)),
            "customer data on day 2, v2": worst(run("v2", fresh + day1, day2)),
            "same agent with 60 quiet days first, customer data, v2": worst(
                run(
                    "v2",
                    [m for d in weekdays(0, 60) for m in work(d, agent="c")],
                    [mk(62, 11, agent="c", asset="customer-data-pipeline", sens=5, session="c-62")],
                )
            ),
        },
    )

    # 7. a day worker's first weekend work ever, at 2 a.m. (day 68 is a Saturday)
    saturday = [mk(68, 2.0 + i / 30, session="a-68-sat") for i in range(5)]
    add(
        "Day worker who never worked a weekend: Saturday 2 a.m.",
        "max M",
        {
            "v2": worst(run("v2", base, saturday)),
            "v2 + weekend falls back to all days": worst(
                run(replace(Flags(v2=True), tod_fallback=4), base, saturday)
            ),
            "same hour on a weekday (day 66), v2": worst(
                run("v2", base, [mk(66, 2.0 + i / 30, session="a-66-n") for i in range(5)])
            ),
        },
    )

    # 8. an explorer (a new repo every other weekday) looks at payroll for the first time
    roaming = sorted(
        base
        + [
            mk(d, 13, asset=f"t{1 + k % 9}-svc{k % 6}", session=f"a-{d}-r")
            for k, d in enumerate(weekdays(0, 60)[::2])
        ],
        key=lambda m: m.ts,
    )
    payroll = [mk(63, 11, asset="payroll-service", sens=5, session="a-63-p")]
    add(
        "Explorer (a new repo every other weekday): first look at payroll",
        "M",
        {
            "v2": worst(run("v2", roaming, payroll)),
            "v2 + sensitive assets also scored on this thing only": worst(
                run(replace(Flags(v2=True), sensitive_this_only=True), roaming, payroll)
            ),
            "focused agent (no exploring), v2": worst(run("v2", base, payroll)),
        },
    )

    # 10. the first-look rule, flat or graded by the asset's sensitivity and the tool's level,
    # where the rule decides: an explorer, a new hire on day 3 (both know the probe tools)
    variants = (
        replace(V3_FINAL, sensitive_steps=(0.0, 0.0)),
        V3_DECIDED,
        V3_FINAL,
        replace(V3_FINAL, sensitive_anchor=3),
    )
    look_tools = (*TOOLS4, "create_or_update_file", "list_commits")
    looks = {
        "payroll (5), read file": ("payroll-service", 5, "get_file_contents", "read"),
        "payroll (5), list commits": ("payroll-service", 5, "list_commits", "metadata"),
        "payroll (5), write file": ("payroll-service", 5, "create_or_update_file", "write"),
        "team deploy repo (4), read file": ("t1-deploy", 4, "get_file_contents", "read"),
        "team deploy repo (4), list commits": ("t1-deploy", 4, "list_commits", "metadata"),
        "team deploy repo (4), write file": ("t1-deploy", 4, "create_or_update_file", "write"),
    }
    explorer = sorted(
        [m for d in weekdays(0, 60) for m in work(d, tools=look_tools)]
        + [
            mk(d, 13, asset=f"t{1 + k % 9}-svc{k % 6}", session=f"a-{d}-r")
            for k, d in enumerate(weekdays(0, 60)[::2])
        ],
        key=lambda m: m.ts,
    )
    hire = [m for d in weekdays(0, 3) for m in work(d, "h", repos=REPOS5[:3], tools=look_tools)]
    who = {"explorer": (explorer, "a", 63), "new hire, day 3": (hire, "h", 3)}
    for label, (history, agent, day) in who.items():
        cells = {}
        for case, (asset, sens, tool, op) in looks.items():
            probe = [mk(day, 11, agent, tool, asset, sens, op, session=f"{agent}-{day}-look")]
            cells[case] = " -> ".join(worst(run(v, history, probe)) for v in variants)
        add(
            f"First look at a sensitive asset: {label}",
            "M: flat 0.9 -> by asset (v3) -> by asset and tool, anchored at a write -> at a read",
            cells,
        )

    # 11. a fresh identity's first day, under each warm-up (history updated once a day)
    warmups = {
        "5 calls": replace(V3_DECIDED, first_day_warmup=False, warmup_rules=False),
        "first day": replace(V3_DECIDED, warmup_rules=False),
        "first day, rules on": V3_DECIDED,
    }
    probes = {
        "an ordinary call with a tool new today": mk(0, 12, "c", "list_issues", "t0-svc1"),
        "payroll (5), read file": day1[0],
        "payroll (5), write file": mk(
            0, 11, "c", "create_or_update_file", "payroll-service", 5, "write"
        ),
        "team deploy repo (4), read file": mk(0, 11, "c", asset="t0-deploy", sens=4),
        "team deploy repo (4), list commits": mk(
            0, 11, "c", "list_commits", "t0-deploy", 4, "metadata"
        ),
    }
    add(
        "Fresh identity: 25 calls on day 1, then one more call that day",
        "M under the warm-up: " + " / ".join(warmups),
        {
            case: " / ".join(worst(run(f, fresh, [probe])) for f in warmups.values())
            for case, probe in probes.items()
        },
    )

    # 9. the four weekend modes on four cases (days 68 and 75 are Saturdays)
    saturday_worker = sorted(
        base + [m for d in range(5, 68, 7) for m in work(d, n=10, start=10, end=14)],
        key=lambda m: m.ts,
    )
    cases = {
        "day worker, first Saturday ever, 2 a.m.": (base, 2.0),
        "day worker, first Saturday ever, 10 a.m.": (base, 10.0),
        "works every Saturday 10-14, Saturday 2 a.m.": (saturday_worker, 2.0),
        "works every Saturday 10-14, Saturday 10 a.m.": (saturday_worker, 10.0),
    }
    for mode in ("split", "fallback", "blend", "flag"):
        cells = {}
        for case, (history, hour) in cases.items():
            probe = [mk(68, hour + i / 30, session=f"a-68-{hour}") for i in range(5)]
            cells[case] = worst(run(replace(Flags(v2=True), weekend=mode), history, probe))
        add(f"Weekend mode: {mode}", "max M", cells)

    # 6. cloud runners: a new /16 from a large pool
    pool_rows = {}
    for size in (40, 400, 1500):
        rng = random.Random(size)
        pool = [(20 + i // 256, i % 256) for i in range(size)]
        msgs = []
        for d in range(150):
            for j in range(30):
                net = rng.choice(pool)
                msgs.append(
                    mk(
                        d,
                        j * 0.75,
                        agent="ci",
                        tool="get_pull_request_status",
                        op="metadata",
                        session=f"ci-{d}-{j}",
                        address=f"{net[0]}.{net[1]}.1.1",
                    )
                )
        observe = make_observer("v2")
        fired = set()
        for m in msgs:
            M, top, scores = observe(m)
            d = int(m.ts // DAY) - BASE_DAY
            if d >= 90 and scores.get("new_network"):
                fired.add(d)
        pool_rows[f"{size} /16s"] = f"{len(fired) / 60:.0%} of days"
    add(
        "CI bot, 30 jobs a day, each from a random /16 of its cloud pool",
        "days with a new network (x3.6)",
        pool_rows,
    )
    return rows


# ── report ─────────────────────────────────────────────────────────────────────────────────
def pct(x) -> str:
    return "-" if x is None else f"{100 * x:.1f}%"


def markdown(meta: dict, results: dict, scen: list[dict]) -> str:
    lines = [
        "# Mostly-ordinary organisation: results",
        "",
        f"{meta['agents']} agents, {meta['days']} days (scored: days {EVAL_FROM}-"
        f"{meta['days'] - 1}), {meta['messages']:,} messages, {meta['gray_episodes']} gray "
        f"episodes. Shipped-engine mirror checked on {meta['equivalence_messages']:,} messages.",
        "",
        f"Doc limits: burst > 20 a minute, request > 10 KB. Learned limits (policy.py, first "
        f"{LEARN_DAYS} days): {meta.get('learned_limits')}.",
        "",
        "## False alarms and gray episodes",
        "",
        "| Engine | Ordinary days ≥x3 | people | bots | ordinary calls ≥x3 | alerts/day "
        "(ordinary · change · gray) | gray caught ≥x3 | top causes on ordinary days |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, r in results.items():
        a = r["alerts_per_day"]
        causes = ", ".join(
            f"{c} {100 * v:.0f}%" for c, v in list(r["ordinary_x3_causes"].items())[:3]
        )
        lines.append(
            f"| {name} | {pct(r['ordinary_days_x3'])} | {pct(r['ordinary_days_x3_people'])} | "
            f"{pct(r['ordinary_days_x3_bots'])} | {pct(r['ordinary_calls_x3'])} | "
            f"{a['ordinary']:.1f} · {a['change']:.1f} · {a['gray']:.1f} | "
            f"{pct(r['gray_caught_x3'])} | {causes} |"
        )
    lines += [
        "",
        "## Daily review list",
        "",
        f"Gray episodes caught when someone reviews the top-k agent-days each day ({meta['agents']} agents).",
        "",
        "| Engine | list | gray caught | cut in a tie | list filled by ordinary · change · gray |",
        "|---|---|---|---|---|",
    ]
    for name, r in results.items():
        for key, v in r["review"].items():
            f = v["fill"]
            lines.append(
                f"| {name} | {key} | {pct(v['gray_caught'])} | {pct(v['days_cut_in_a_tie'])}"
                f" | {pct(f['ordinary'])} · {pct(f['change'])} · {pct(f['gray'])} |"
            )
    lines += ["", "## Ordinary life and org-wide changes at x3 or more", ""]
    tags = sorted({t for r in results.values() for t in r["changes_x3"]})
    names = list(results)
    lines += ["| Change | days | " + " | ".join(names) + " |", "|---|---|" + "---|" * len(names)]
    for t in tags:
        days = next(r["changes_x3"][t]["days"] for r in results.values() if t in r["changes_x3"])
        cells = [
            f"{pct(r['changes_x3'][t]['x3'])} ({r['changes_x3'][t]['cause']})"
            if t in r["changes_x3"]
            else "-"
            for r in results.values()
        ]
        lines.append(f"| {t} | {days} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Gray episodes by kind",
        "",
        "| Kind | episodes | " + " | ".join(f"{n}: caught · calls ≥x3" for n in names) + " |",
        "|---|---|" + "---|" * len(names),
    ]
    kinds = sorted({k for r in results.values() for k in r["gray"]})
    for k in kinds:
        n_eps = next(r["gray"][k]["episodes"] for r in results.values() if k in r["gray"])
        cells = [
            f"{pct(r['gray'][k]['caught_x3'])} · {pct(r['gray'][k]['calls_x3'])}"
            if k in r["gray"]
            else "-"
            for r in results.values()
        ]
        lines.append(f"| {k} | {n_eps} | " + " | ".join(cells) + " |")
    lines += ["", "## Hand-made scenarios", ""]
    for s in scen:
        lines.append(f"**{s['case']}** ({s['what']})")
        lines.append("")
        for k, v in s.items():
            if k not in ("case", "what"):
                lines.append(f"- {k}: {v}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", type=int, default=150)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--profile", default="main", choices=sorted(PROFILES))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument(
        "--scenarios-only",
        action="store_true",
        help="rerun the hand-made scenarios and rewrite the report from saved results",
    )
    ap.add_argument("--name", default="normal_org_sim", help="results file name (no extension)")
    ap.add_argument(
        "--check-port",
        action="store_true",
        help="check the shipped engine's designs v1-v4 against the simulation, then stop",
    )
    ap.add_argument(
        "--only",
        default="",
        help="engines to score and merge into the saved results, separated by |",
    )
    args = ap.parse_args()
    out = HERE / "results"
    if args.scenarios_only:
        saved = json.loads((out / f"{args.name}.json").read_text())
        scen = scenarios()
        saved["scenarios"] = scen
        (out / f"{args.name}.json").write_text(json.dumps(saved, indent=1, default=str))
        (out / f"{args.name}.md").write_text(markdown(saved["meta"], saved["results"], scen))
        print(markdown(saved["meta"], saved["results"], scen))
        return
    t0 = time.time()
    world, roles, _ = build_world(args.agents, args.seed, PROFILES[args.profile])
    WORLD.update(world)
    FIRST_USES.update(first_uses(world))
    n_msgs = sum(len(v) for v in world.values())
    print(f"world: {len(world)} agents, {n_msgs:,} messages ({time.time() - t0:.0f}s)", flush=True)
    sample = [a for a in world if "bot" in a][:2] + [a for a in world if "bot" not in a][:4]
    n_eq = check_equivalence(sample)
    print(f"mirror of the shipped engine: identical on {n_eq:,} messages", flush=True)
    # the engines before v3 learned with policy.py dropping the written steps (merge after a
    # review); keep that for them, so their saved results stay reproducible
    learned = learned_config(world, replace(CONFIG, requires_before={}))
    CONFIGS["learned"] = CONFIGS["learned per day"] = learned
    CONFIGS["policy.py"] = policy = learned_config(world, replace(CONFIG, design="v3"))
    print(
        f"policy.py: size limits per tool {policy.request_limit_by_tool}, many assets > "
        f"{policy.many_assets_per_hour}, required steps {dict(policy.requires_before)}",
        flush=True,
    )
    if args.check_port:
        n_v2 = check_equivalence(sample, "v2")
        print(f"design v2: identical on {n_v2:,} messages", flush=True)
        port = check_port(args.workers) | {"v1_messages": n_eq, "v2_messages": n_v2}
        print(f"design v3 (one stream, all agents): {port}", flush=True)
        port["v4"] = check_port(args.workers, "v4")
        print(f"design v4 (one stream, all agents): {port['v4']}", flush=True)
        path = out / "normal_org_port_check.json"
        saved = json.loads(path.read_text()) if path.exists() else {}
        saved[args.name] = port
        path.write_text(json.dumps(saved, indent=1, default=str))
        return
    learned_limits = {
        "burst_per_minute": learned.burst_per_minute,
        "request_limit_bytes": learned.request_limit_bytes,
        "requires_before": {t: sorted(b) for t, b in learned.requires_before.items()},
    }
    print(f"learned limits: {learned_limits}", flush=True)
    SIZE_LIMITS["learned"] = learned_size_limits(world)
    SIZE_LIMITS["learned per day"] = learned_size_limits_per_day(world)
    BREADTH["limit"] = learned_breadth_limit(world)
    print(f"learned many-assets limit: > {BREADTH['limit']} distinct assets an hour", flush=True)
    print(f"learned size limits per tool (calls): {SIZE_LIMITS['learned']}", flush=True)
    print(f"learned size limits per tool (agent-days): {SIZE_LIMITS['learned per day']}")
    names = [n.strip() for n in args.only.split("|") if n.strip()] or list(VARIANTS)
    labels = day_labels(world)
    aids = sorted(world, key=lambda a: -len(world[a]))
    shards = [aids[i :: args.workers] for i in range(args.workers)]
    jobs = [(name, shard) for name in names for shard in shards]
    merged: dict[str, list] = {name: [{}, {}, Counter()] for name in names}
    # fork, so workers share the world built above (3.14 defaults to forkserver)
    with get_context("fork").Pool(args.workers) as pool:
        for name, days, gray, ordinary in pool.imap_unordered(score_shard, jobs):
            merged[name][0].update(days)
            merged[name][1].update(gray)
            merged[name][2].update(ordinary)
    print(f"scored {len(names)} engines ({time.time() - t0:.0f}s)", flush=True)
    with open(SCRATCH, "wb") as fh:  # keep the scores, so the analysis can be rerun alone
        pickle.dump(
            {
                "merged": merged,
                "labels": labels,
                "roles": roles,
                "messages": n_msgs,
                "equivalence": n_eq,
            },
            fh,
        )
    results = {
        name: analyse(
            days=merged[name][0],
            gray_calls=merged[name][1],
            ordinary=merged[name][2],
            labels=labels,
            roles=roles,
        )
        for name in names
    }
    if args.only and (out / f"{args.name}.json").exists():  # merge into the saved run
        saved = json.loads((out / f"{args.name}.json").read_text())
        results = saved["results"] | results
    scen = scenarios()
    meta = {
        "agents": len(world),
        "days": 180,
        "messages": n_msgs,
        "seed": args.seed,
        "gray_episodes": next(iter(results.values()))["gray_episodes"],
        "equivalence_messages": n_eq,
        "roles": Counter(roles.values()),
        "learned_limits": learned_limits,
        "learned_size_limits": SIZE_LIMITS["learned"],
        "learned_size_limits_per_day": SIZE_LIMITS["learned per day"],
        "learned_breadth_limit": BREADTH["limit"],
        "profile": args.profile,
    }
    (out / f"{args.name}.json").write_text(
        json.dumps({"meta": meta, "results": results, "scenarios": scen}, indent=1, default=str)
    )
    (out / f"{args.name}.md").write_text(markdown(meta, results, scen))
    print(markdown(meta, results, scen))
    print(f"done ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
