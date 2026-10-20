"""Scenario tests for the Velocity / Knowledge / Place baseline (vkp_engine.py).

The same simulated GitHub organisation as scenarios.py (50 agents, 90 days, real tools and static
impacts), the same scenarios from day 70, plus three that target dimensions the old set did not
have: a session left running all day, a tool nobody in the organisation uses, and a day with three
times the usual calls spread out (no bursts). For each scenario and each way of joining a family
(average, average of e, max, sum) it reports the strongest call, which dimensions fired, and
whether the agent-day is among the top 2 of its day (2 alerts a day, the same for every variant).

Run:  python vkp_scenarios.py      (writes results/vkp_scenarios.json)
"""
from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import scenarios as S
from vkp_engine import DIMENSIONS, VARIANTS, Engine

OUT = Path(__file__).with_name("results") / "vkp_scenarios.json"
BUDGET = 2
NEW = ["long_session", "org_rare_tool", "busy_day"]
SCENARIOS = [s for s in S.SCENARIOS if s not in ("new_hire_off_role_no_fill",)] + NEW


def build(name: str, rng: random.Random):
    if name not in NEW:
        return S.build(name, rng)
    agents = S.make_agents()
    by = {a.name: a for a in agents}
    rows = S.background(rng, agents)
    window = range(S.START, S.DAYS)
    if name == "long_session":                 # one session kept open from 9:00 to 17:30
        a = by["dev05"]
        tools = [t for _ in range(6) for t in S.developer_session(rng)][:22]
        rows += S.new_session(rng, a, S.START, 9.0, tools, S.OFFICE, a.client, 1400.0)
        return rows, ["dev05"], window, {}
    if name == "org_rare_tool":                # a tool no role in the organisation uses
        S.insert(rows, S.sessions(rows, "dev05", S.START)[0], "list_issues", ["create_repository"], 30.0)
        return rows, ["dev05"], window, {}
    if name == "busy_day":                     # three times the usual sessions, spread out
        a = by["tri03"]
        for k in range(10):
            rows += S.new_session(rng, a, S.START, 9 + 0.8 * k, S.triager_session(rng), S.OFFICE,
                                  a.client, 60.0)
        return rows, ["tri03"], window, {}
    raise ValueError(name)


def run(name: str, dims: tuple[str, ...] = DIMENSIONS) -> dict:
    rng = random.Random(S.SEED)
    rows, targets, days, _ = build(name, rng)
    rows.sort(key=lambda r: r.call.ts)
    impacts = {t["tool"]: t["impact"] for t in json.loads(S.SCAN.read_text())["tools"]}
    eng = Engine(n_tools=len(impacts), dims=dims)
    tset, peak, fired = set(targets), None, Counter()
    for r in rows:
        s = eng.score(r.call, impacts[r.call.tool])
        if r.tag == "scenario" and r.call.agent in tset:
            fired.update(d for d in s.fired() if d in dims)
            if peak is None or sum(s.x[d] for d in dims) > sum(peak.x[d] for d in dims):
                peak = s
    first = days[0]
    out = {"targets": len(targets), "scenario_calls_fired": dict(fired)}
    if peak is not None:
        out["peak"] = {"tool": peak.call.tool, "r_static": peak.r_static,
                       "fired": {d: round(peak.x[d], 1) for d in peak.fired() if d in dims},
                       "multiplier": {v: round(m, 2) for v, m in peak.multiplier.items()}}
    for v in VARIANTS:
        flags, ranks, _ = eng.daily_flags(BUDGET, v)
        alerts = defaultdict(int)
        for (_, d), f in flags.items():
            alerts[d] += f
        out[v] = {"first_day_flagged": any(flags.get((a, first), False) for a in targets),
                  "first_day_rank": min(ranks.get((a, first), 99) for a in targets),
                  "days_flagged": sorted({d for (a, d), f in flags.items() if f and a in tset
                                          and d in days}),
                  "targets_flagged_3d": sum(f for (a, d), f in flags.items() if f and a in tset
                                            and first <= d < first + 3)}
    return out


def main():
    res = {}
    for name in SCENARIOS:
        res[name] = r = run(name)
        p = r.get("peak", {})
        print(f"\n{name:<20} peak {p.get('tool')} fired {p.get('fired')}")
        print("   x: " + "  ".join(f"{v} {m}" for v, m in p.get("multiplier", {}).items()))
        print("   first-day rank: " + "  ".join(f"{v} #{r[v]['first_day_rank']}"
                                                f"{'*' if r[v]['first_day_flagged'] else ''}"
                                                for v in VARIANTS)
              + "   (* = flagged)")
        print("   days flagged: " + "  ".join(f"{v} {len(r[v]['days_flagged'])}" for v in VARIANTS)
              + "   targets flagged in 3 days: "
              + "  ".join(f"{v} {r[v]['targets_flagged_3d']}" for v in VARIANTS))
        top = sorted(r["scenario_calls_fired"].items(), key=lambda kv: -kv[1])[:6]
        print("   dimensions firing on scenario calls: " + ", ".join(f"{d} {n}" for d, n in top))
    OUT.write_text(json.dumps(res, indent=1))
    never = [d for d in DIMENSIONS if not any(res[n]["scenario_calls_fired"].get(d) for n in res)]
    print("\nnever fired on any scenario call:", never)


if __name__ == "__main__":
    main()
