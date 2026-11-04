"""Probe for the v5 baselines-and-identity design: raw-traffic facts behind its parameter choices.

Builds one simulator world (``normal_org_world.build_world``) and measures, without changing any
engine or simulator file:

1. **N7 (rarity not monotone at novelty).** For every warm tool call on days 90-179 whose asset
   (or tool, or /16 network) is unseen for the caller, the v4 rarity count of a never-seen value
   is ``nu`` (new starts after onboarding, ``memory.py:98-99``); a value seen once would count
   ``f1 + 1`` (the singletons, plus itself). The call is an inversion when ``nu > f1 + 1``: the
   never-seen value scores *lower* than it would after one use. The real ``DailyCounts`` from
   ``src/mcp_security/behaviour/memory.py`` is used with ``daily=True`` and the engine's warm-up
   and onboarding rules (``engine.py:288-290, 437-441``).
2. **Per-day caps (N5).** Share of (agent, day, value) cells, and of calls, that a cap of c per
   value per day would trim, for tools and assets, c in {1, 2, 3, 5, 10}.
3. **Bucketed usual (N5).** Per agent over days 0-89: the v4 call-weighted usual of the trailing
   hour count (``engine.py:374-378``) against the median and 90th percentile of calls per active
   clock hour.
4. **UTC days (N27).** Per time-zone group, the share of a person's local working days whose calls
   fall on two UTC dates, and on two "04:00 local" dates; the ratio of UTC active days to local
   active days.
5. **Absence gaps (N10).** Gaps between consecutive active days: the share of gaps of at least 7,
   14, 21 and 30 days, people and bots.
6. **Novelty arms (N7).** The asset score at x3 under v4 and three monotone rules (min, max
   envelope, Good-Turing), with new starts counted per call or per day; then the proposed rule
   under per-day caps c in {1, 2, 3, 5, 10, none}.

DEVELOPMENT WORLD: seed 7 was used to design v1-v4. No number here is a test result.

Run from the repo root:

    PYTHONHASHSEED=0 uv run python \
        reports/experiments/dynamic_dimensions/knowledge_base/probes/baselines_identity_probe.py \
        --out /tmp/.../scratchpad/v5_vectors/baselines_identity_seed7.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
SIM_DIR = HERE.parents[1]
REPO = HERE.parents[4]
sys.path.insert(0, str(SIM_DIR))
sys.path.insert(0, str(REPO / "src"))

import normal_org_world as W  # noqa: E402  (path set above)

from mcp_security.behaviour.memory import DailyCounts  # noqa: E402

DAY_S, HOUR_S = 86_400.0, 3_600.0
HISTORY_DAYS, WARMUP_CALLS, ONBOARDING_DAYS = 90, 5, 14  # engine defaults (engine.py:115-137)
SCORED_FROM = 90
CAPS = (1, 2, 3, 5, 10)
GAP_LINES = (7, 14, 21, 30)
ROLLOVER_H = 4.0
TOLERANCE, ASSET_CEILING, ORIGIN_CEILING = 2.0, 1.0, 0.9


def network16(address: str | None) -> str | None:
    if not address:
        return None
    a, b, *_ = address.split(".")
    return f"{a}.{b}"


def person_tz(spec: W.Spec, seed: int, profile: W.Profile) -> float:
    """The person's home UTC offset, re-drawn exactly as ``gen_person`` draws it."""
    rng = random.Random(seed * 1_000_003 + spec.idx)
    return W.make_person(spec, rng, profile).tz


def singletons(counts: DailyCounts) -> int:
    return sum(1 for c in counts.counts.values() if c == 1)


def novelty_probe(rows: list[tuple]) -> dict:
    """N7 for asset, tool and network on one agent, in arrival order, as the v4 engine keeps
    its counts (learning once a day)."""
    kinds = {k: DailyCounts(HISTORY_DAYS, daily=True) for k in ("asset", "tool", "network")}
    first_day, tool_calls = None, 0
    out = {k: Counter() for k in kinds}
    gaps = {k: [] for k in kinds}
    for r in rows:
        ts, method = r[0], r[1]
        today = int(ts // DAY_S)
        if first_day is None:
            first_day = today
        warm = tool_calls >= WARMUP_CALLS and today > first_day
        onboarded = today - first_day >= ONBOARDING_DAYS
        values = {"network": network16(r[7])}
        if method == "tools/call":
            values |= {"tool": r[3] or "", "asset": r[4]}
        for kind, value in values.items():
            if value is None:
                continue
            counts = kinds[kind]
            counts.expire(today)
            scored = warm and today - (W.BASE_DAY) >= SCORED_FROM
            if scored and not counts.known(value) and counts.active_days(today=today):
                a = counts.active_days(today=today)
                nu = counts.new_uses - counts.new_by_day.get(today, 0)
                f1 = singletons(counts)
                c = ASSET_CEILING if kind == "asset" else ORIGIN_CEILING
                s0 = c / (1 + TOLERANCE * (nu + 1) / (a + 1))
                s1 = c / (1 + TOLERANCE * (f1 + 2) / (a + 1))
                out[kind]["unseen"] += 1
                if nu > f1 + 1:
                    out[kind]["inverted"] += 1
                    gaps[kind].append(s1 - s0)
            counts.add(today, value, count_as_new=warm and onboarded)
        if method == "tools/call":
            tool_calls += 1
    return {
        k: {
            "unseen_calls": out[k]["unseen"],
            "inverted_calls": out[k]["inverted"],
            "score_gap": gaps[k],
        }
        for k in kinds
    }


S_STAR = 0.8413  # s1 at which M = x3 (06, "The alert lines")
NOVELTY_ARMS = (
    "v4",
    "min_new_starts",
    "max_envelope",
    "good_turing",
    "start_days",
    "start_days_min",
    "start_days_max",
)


def novelty_arms(rows: list[tuple]) -> dict:
    """Asset rarity score (no floor, no org discount) under four novelty rules, on warm scored
    calls to assets of sensitivity <= 3: how many calls and agent-days reach x3.

    - v4: N(0) = nu (new starts), N(n) = tail(n).
    - min_new_starts: N(0) = min(nu, f1 + 1); N(n) = tail(n).
    - max_envelope: N(0) = nu; N(n) = max(nu, tail(n)) for n >= 1.
    - good_turing: N(0) = f1 (things used once); N(n) = tail(n).
    - start_days*: the same three with nu replaced by the number of days on which he started
      something new (a daily cap of 1 on new starts).
    """
    counts = DailyCounts(HISTORY_DAYS, daily=True)
    first_day, tool_calls = None, 0
    hot = {a: Counter() for a in NOVELTY_ARMS}
    hot_days = {a: {"ordinary": set(), "gray": set()} for a in NOVELTY_ARMS}
    cache: dict = {}
    for r in rows:
        ts, method = r[0], r[1]
        today = int(ts // DAY_S)
        if first_day is None:
            first_day = today
        if method != "tools/call":
            continue
        warm = tool_calls >= WARMUP_CALLS and today > first_day
        onboarded = today - first_day >= ONBOARDING_DAYS
        asset, sens = r[4], r[5] or 0
        tool_calls += 1
        if asset is None:
            continue
        counts.expire(today)
        if warm and today - W.BASE_DAY >= SCORED_FROM and sens <= 3 and counts.active_days(
            today=today
        ):
            a = counts.active_days(today=today)
            n = counts.counts.get(asset, 0)
            key = (today, n)
            if key not in cache:
                if len(cache) > 512:
                    cache.clear()
                nu = counts.new_uses - counts.new_by_day.get(today, 0)
                f1 = singletons(counts)
                tail = sum(c for c in counts.counts.values() if c <= n) if n else 0
                nd = sum(1 for d, k in counts.new_by_day.items() if k > 0 and d != today)
                big_n = {
                    "start_days": nd if n == 0 else tail,
                    "start_days_min": min(nd, f1 + 1) if n == 0 else tail,
                    "start_days_max": nd if n == 0 else max(nd, tail),
                    "v4": nu if n == 0 else tail,
                    "min_new_starts": min(nu, f1 + 1) if n == 0 else tail,
                    "max_envelope": nu if n == 0 else max(nu, tail),
                    "good_turing": f1 if n == 0 else tail,
                }
                cache[key] = {
                    arm: ASSET_CEILING / (1 + TOLERANCE * (v + 1) / (a + 1))
                    for arm, v in big_n.items()
                }
            label = "gray" if r[12] else "ordinary"
            for arm, s_val in cache[key].items():
                if s_val >= S_STAR:
                    hot[arm][label] += 1
                    hot[arm][label + ("_unseen" if n == 0 else "_seen")] += 1
                    hot_days[arm][label].add(today)
            hot["v4"]["scored_" + label] += 1
        counts.add(today, asset, count_as_new=warm and onboarded)
    return {
        "calls": {a: dict(c) for a, c in hot.items()},
        "days": {a: {k: len(v) for k, v in d.items()} for a, d in hot_days.items()},
    }


CAP_ARMS = (1, 2, 3, 5, 10, None)


class CappedCounts:
    """``DailyCounts(daily=True)`` with each value's day folded in as min(count, cap), and new
    starts counted as days with a new start (the v5 proposal)."""

    def __init__(self, days: int, cap: int | None) -> None:
        self.days, self.cap = days, cap
        self.by_day: dict[int, Counter] = {}
        self.order: deque = deque()
        self.counts: Counter = Counter()
        self.start_days: set = set()
        self.folded: set = set()

    def _w(self, n: int) -> int:
        return n if self.cap is None else min(n, self.cap)

    def expire(self, today: int) -> None:
        for day in list(self.order):
            if day < today and day not in self.folded:
                self.counts.update({v: self._w(n) for v, n in self.by_day[day].items()})
                self.folded.add(day)
        while self.order and self.order[0] <= today - self.days:
            day = self.order.popleft()
            if day in self.folded:
                self.counts.subtract({v: self._w(n) for v, n in self.by_day[day].items()})
                self.counts += Counter()
                self.folded.discard(day)
            self.by_day.pop(day)
            self.start_days.discard(day)

    def active_days(self, today: int) -> int:
        return sum(1 for d in self.order if d != today)

    def add(self, today: int, value, count_as_new: bool) -> None:
        if today not in self.by_day:
            self.by_day[today] = Counter()
            self.order.append(today)
        if count_as_new and value not in self.counts and value not in self.by_day[today]:
            self.start_days.add(today)
        self.by_day[today][value] += 1


def cap_arms(rows: list[tuple]) -> dict:
    """Asset score (sensitivity <= 3, no floor or org discount) with the v5 novelty rule (new
    starts counted in days, max envelope) under per-day caps: calls and agent-days at x3."""
    out = {}
    for cap in CAP_ARMS:
        counts = CappedCounts(HISTORY_DAYS, cap)
        first_day, tool_calls = None, 0
        hot, days = Counter(), {"ordinary": set(), "gray": set()}
        cache: dict = {}
        for r in rows:
            ts = r[0]
            today = int(ts // DAY_S)
            if first_day is None:
                first_day = today
            if r[1] != "tools/call":
                continue
            warm = tool_calls >= WARMUP_CALLS and today > first_day
            onboarded = today - first_day >= ONBOARDING_DAYS
            tool_calls += 1
            asset, sens = r[4], r[5] or 0
            if asset is None:
                continue
            counts.expire(today)
            a = counts.active_days(today)
            if warm and today - W.BASE_DAY >= SCORED_FROM and sens <= 3 and a:
                n = counts.counts.get(asset, 0)
                key = (today, n)
                if key not in cache:
                    if len(cache) > 512:
                        cache.clear()
                    nd = len(counts.start_days - {today})
                    tail = sum(c for c in counts.counts.values() if c <= n) if n else 0
                    big_n = nd if n == 0 else max(nd, tail)
                    cache[key] = ASSET_CEILING / (1 + TOLERANCE * (big_n + 1) / (a + 1))
                label = "gray" if r[12] else "ordinary"
                if cache[key] >= S_STAR:
                    hot[label] += 1
                    days[label].add(today)
            counts.add(today, asset, count_as_new=warm and onboarded)
        out[str(cap)] = {"calls": dict(hot), "days": {k: len(v) for k, v in days.items()}}
    return out


def cap_probe(rows: list[tuple]) -> dict:
    """Cells and calls a per-day cap would trim, for tools and assets."""
    cells = {"tool": Counter(), "asset": Counter()}
    for r in rows:
        if r[1] != "tools/call":
            continue
        day = int(r[0] // DAY_S)
        cells["tool"][(day, r[3])] += 1
        if r[4]:
            cells["asset"][(day, r[4])] += 1
    out = {}
    for kind, cnt in cells.items():
        total_calls = sum(cnt.values())
        out[kind] = {
            "cells": len(cnt),
            "calls": total_calls,
            **{
                f"cap{c}": {
                    "cells_over": sum(1 for v in cnt.values() if v > c),
                    "calls_trimmed": sum(v - c for v in cnt.values() if v > c),
                }
                for c in CAPS
            },
        }
    return out


def usual_probe(rows: list[tuple]) -> dict | None:
    """v4's call-weighted usual of the trailing hour count, against per-active-hour quantiles,
    over the agent's first 90 days."""
    recent: deque = deque()
    weighted, n_calls = 0.0, 0
    per_hour: Counter = Counter()
    for r in rows:
        if r[1] != "tools/call":
            continue
        ts = r[0]
        if int(ts // DAY_S) - W.BASE_DAY >= SCORED_FROM:
            break
        recent.append(ts)
        while recent and recent[0] <= ts - HOUR_S:
            recent.popleft()
        weighted += len(recent)
        n_calls += 1
        per_hour[int(ts // HOUR_S)] += 1
    if n_calls < 50:
        return None
    hourly = sorted(per_hour.values())

    def quant(p: float) -> int:
        return hourly[min(len(hourly) - 1, int(p * len(hourly)))]

    return {
        "call_weighted_usual": weighted / n_calls,
        "hour_median": median(hourly),
        "hour_p75": quant(0.75),
        "hour_p80": quant(0.8),
        "hour_p90": quant(0.9),
        "active_hours": len(hourly),
    }


def utc_probe(rows: list[tuple], tz: float) -> dict:
    """Local working days whose calls fall on two UTC dates, or two 04:00-local dates."""
    by_local: dict[int, set] = defaultdict(set)
    by_shift: dict[int, set] = defaultdict(set)
    utc_days, shift_days = set(), set()
    for r in rows:
        if r[1] != "tools/call":
            continue
        ts = r[0]
        local = ts + tz * HOUR_S
        local_day = int(local // DAY_S)
        utc_day = int(ts // DAY_S)
        shifted = int((local - ROLLOVER_H * HOUR_S) // DAY_S)
        by_local[local_day].add(utc_day)
        by_shift[local_day].add(shifted)
        utc_days.add(utc_day)
        shift_days.add(shifted)
    return {
        "local_days": len(by_local),
        "split_utc": sum(1 for v in by_local.values() if len(v) > 1),
        "split_0400_local": sum(1 for v in by_shift.values() if len(v) > 1),
        "utc_active_days": len(utc_days),
        "rollover_active_days": len(shift_days),
    }


def gap_probe(rows: list[tuple]) -> list[int]:
    days = sorted({int(r[0] // DAY_S) for r in rows if r[1] == "tools/call"})
    return [b - a for a, b in zip(days, days[1:])]


def summarise(per_agent: dict, roles: dict, tzs: dict) -> dict:
    nov = {k: Counter() for k in ("asset", "tool", "network")}
    nov_gaps = {k: [] for k in nov}
    caps = {k: Counter() for k in ("tool", "asset")}
    usual_ratio = {"people": [], "bots": []}
    utc = defaultdict(Counter)
    gaps = {"people": [], "bots": []}
    for agent, res in per_agent.items():
        group = "bots" if "bot" in roles[agent] else "people"
        for k, v in res["novelty"].items():
            nov[k]["unseen"] += v["unseen_calls"]
            nov[k]["inverted"] += v["inverted_calls"]
            nov_gaps[k] += v["score_gap"]
        for k, v in res["caps"].items():
            caps[k]["calls"] += v["calls"]
            caps[k]["cells"] += v["cells"]
            for c in CAPS:
                caps[k][f"cap{c}_cells_over"] += v[f"cap{c}"]["cells_over"]
                caps[k][f"cap{c}_calls_trimmed"] += v[f"cap{c}"]["calls_trimmed"]
        if res["usual"]:
            u = res["usual"]
            usual_ratio[group].append(
                {
                    "p90_over_cw": u["hour_p90"] / u["call_weighted_usual"],
                    "p75_over_cw": u["hour_p75"] / u["call_weighted_usual"],
                    "p80_over_cw": u["hour_p80"] / u["call_weighted_usual"],
                    "median_over_cw": u["hour_median"] / u["call_weighted_usual"],
                }
            )
        if group == "people":
            for key, val in res["utc"].items():
                utc[str(tzs[agent])][key] += val
        gaps[group] += res["gaps"]

    def q(xs: list[float], p: float) -> float | None:
        xs = sorted(xs)
        return round(xs[min(len(xs) - 1, int(p * len(xs)))], 3) if xs else None

    return {
        "novelty": {
            k: {
                "unseen_calls": nov[k]["unseen"],
                "inverted_calls": nov[k]["inverted"],
                "inverted_share": round(nov[k]["inverted"] / max(1, nov[k]["unseen"]), 4),
                "score_gap_median": q(nov_gaps[k], 0.5),
                "score_gap_p90": q(nov_gaps[k], 0.9),
            }
            for k in nov
        },
        "caps": {
            k: {
                "cells": caps[k]["cells"],
                "calls": caps[k]["calls"],
                **{
                    f"cap{c}": {
                        "cells_over_share": round(
                            caps[k][f"cap{c}_cells_over"] / max(1, caps[k]["cells"]), 4
                        ),
                        "calls_trimmed_share": round(
                            caps[k][f"cap{c}_calls_trimmed"] / max(1, caps[k]["calls"]), 4
                        ),
                    }
                    for c in CAPS
                },
            }
            for k in caps
        },
        "usual": {
            g: {
                "agents": len(v),
                "p90_over_call_weighted_median": q([x["p90_over_cw"] for x in v], 0.5),
                "p90_over_call_weighted_p10": q([x["p90_over_cw"] for x in v], 0.1),
                "p90_over_call_weighted_p90": q([x["p90_over_cw"] for x in v], 0.9),
                "median_over_call_weighted_median": q([x["median_over_cw"] for x in v], 0.5),
                "p75_over_call_weighted_median": q([x["p75_over_cw"] for x in v], 0.5),
                "p80_over_call_weighted_median": q([x["p80_over_cw"] for x in v], 0.5),
            }
            for g, v in usual_ratio.items()
        },
        "utc_by_tz": {
            tz: {
                "local_days": c["local_days"],
                "split_utc_share": round(c["split_utc"] / max(1, c["local_days"]), 4),
                "split_0400_local_share": round(
                    c["split_0400_local"] / max(1, c["local_days"]), 4
                ),
                "utc_over_rollover_active_days": round(
                    c["utc_active_days"] / max(1, c["rollover_active_days"]), 4
                ),
            }
            for tz, c in sorted(utc.items())
        },
        "gaps": {
            g: {
                "gaps": len(v),
                **{f"share_ge_{d}": round(sum(1 for x in v if x >= d) / max(1, len(v)), 5)
                   for d in GAP_LINES},
                "max": max(v, default=0),
            }
            for g, v in gaps.items()
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--agents", type=int, default=150)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--profile", default="main", choices=sorted(W.PROFILES))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    profile = W.PROFILES[args.profile]
    world, roles, _ = W.build_world(args.agents, args.seed, profile)
    specs = {s.aid: s for s in W.roster(args.agents, args.seed)}
    tzs = {
        a: (person_tz(specs[a], args.seed, profile) if "bot" not in roles[a] else 0.0)
        for a in world
    }
    per_agent = {}
    for agent, rows in world.items():
        per_agent[agent] = {
            "novelty": novelty_probe(rows),
            "novelty_arms": novelty_arms(rows),
            "cap_arms": cap_arms(rows),
            "caps": cap_probe(rows),
            "usual": usual_probe(rows),
            "utc": utc_probe(rows, tzs[agent]),
            "gaps": gap_probe(rows),
        }
    arms_calls = {a: Counter() for a in NOVELTY_ARMS}
    arms_days = {a: Counter() for a in NOVELTY_ARMS}
    for res in per_agent.values():
        for arm in NOVELTY_ARMS:
            arms_calls[arm].update(res["novelty_arms"]["calls"][arm])
            arms_days[arm].update(res["novelty_arms"]["days"][arm])
    summary_arms = {
        arm: {"calls_at_x3": dict(arms_calls[arm]), "agent_days_at_x3": dict(arms_days[arm])}
        for arm in NOVELTY_ARMS
    }
    cap_calls = {str(c): Counter() for c in CAP_ARMS}
    cap_days = {str(c): Counter() for c in CAP_ARMS}
    for res in per_agent.values():
        for c, v in res["cap_arms"].items():
            cap_calls[c].update(v["calls"])
            cap_days[c].update(v["days"])
    summary = {
        "world": f"{args.profile}_seed{args.seed}",
        "asset_novelty_arms_sens_le_3": summary_arms,
        "asset_cap_arms_v5_novelty_sens_le_3": {
            c: {"calls_at_x3": dict(cap_calls[c]), "agent_days_at_x3": dict(cap_days[c])}
            for c in cap_calls
        },
        "label": "DEVELOPMENT WORLD (seed used to design v1-v4); not a test result",
        **summarise(per_agent, roles, tzs),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
