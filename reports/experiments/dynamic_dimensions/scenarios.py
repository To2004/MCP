"""Scenario tests for the dynamic engine (dynamic_engine.py).

One simulated GitHub organisation: 90 days, 50 agents (reviewers, developers, triagers, merge
bots), real tool names and static impacts from the mcp-static-scan reference scan. Each scenario
changes the traffic of one agent, or of everyone, from day 70. The engine scores the whole stream
and the report shows what the formula says on the scenario's calls and days: the base formula,
idea A (crowd), idea B (settling), and both. Alerts use a budget of 2 agent-days per day with
the threshold taken from the previous 30 days, as a deployment would.

Run:  python scenarios.py      (writes results/scenarios.json)
"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path

from dynamic_engine import DAY, VARIANTS, Call, Engine

SCAN = Path.home() / "mcp-static-scan/examples/github-helios/reference/github-helios.scan.json"
OUT = Path(__file__).with_name("results") / "scenarios.json"
DAYS, START, BUDGET, SEED = 90, 70, 2.0, 7
FLOOR = 4.0                                   # bits: never flag a day below this, whatever the budget
ROLE_COUNTS = {"reviewer": 16, "developer": 16, "triager": 8, "bot": 10}
OFFICE, BOT_NET = "10.1", "10.9"
CREEP_TOOLS = ["create_branch", "create_or_update_file", "push_files", "update_pull_request_branch",
               "merge_pull_request", "create_issue", "update_issue", "fork_repository"]


def reviewer_session(rng: random.Random) -> list[str]:
    s = ["list_pull_requests", "get_pull_request", "get_pull_request_files"]
    s += ["get_file_contents"] * rng.randint(1, 3)
    if rng.random() < 0.3:
        s += ["search_code", "get_file_contents"]
    s += ["get_pull_request_comments", "create_pull_request_review"]
    return s + (["add_issue_comment"] if rng.random() < 0.2 else [])


def developer_session(rng: random.Random) -> list[str]:
    r = rng.random()
    if r < 0.5:
        return (["list_issues", "get_issue", "create_branch"] + ["get_file_contents"] * rng.randint(1, 4)
                + ["create_or_update_file"] * rng.randint(1, 2) + ["create_pull_request"])
    if r < 0.8:
        return ["search_code"] + ["get_file_contents"] * rng.randint(1, 3)
    return ["list_commits", "get_file_contents"]


def triager_session(rng: random.Random) -> list[str]:
    s = ["list_issues"] + ["get_issue"] * rng.randint(1, 3)
    s += [rng.choice(["add_issue_comment", "update_issue"])]
    return s + (["search_issues"] if rng.random() < 0.3 else [])


def bot_session(rng: random.Random) -> list[str]:
    s = ["list_pull_requests", "get_pull_request_status", "get_pull_request_reviews"]
    return s + (["merge_pull_request"] if rng.random() < 0.1 else [])


SCRIPTS = {"reviewer": reviewer_session, "developer": developer_session,
           "triager": triager_session, "bot": bot_session}


@dataclass
class Agent:
    name: str
    role: str
    home: int
    client: str
    start_day: int = 0


@dataclass
class Row:
    call: Call
    tag: str = ""


def make_agents() -> list[Agent]:
    agents, i = [], 0
    for role, n in ROLE_COUNTS.items():
        for k in range(n):
            client = "mcp-python-sdk/1.2.0" if role == "bot" else \
                ("claude-desktop/0.9.4" if k % 2 else "cursor/1.4.2")
            agents.append(Agent(f"{role[:3]}{k:02d}", role, 64 + i, client))
            i += 1
    return agents


def host(rng: random.Random) -> str:
    return f"{rng.randrange(256)}.{rng.randrange(1, 255)}"


def agent_day(rng: random.Random, a: Agent, day: int, role: str | None = None) -> list[Row]:
    """One agent's normal calls for one day."""
    role = role or a.role
    rows: list[Row] = []
    if role == "bot":
        for h in range(24):
            ts = day * DAY + h * 3600 + rng.uniform(0, 300)
            for j, tool in enumerate(bot_session(rng)):
                rows.append(Row(Call(ts + 2 * j, a.name, a.role, f"{a.name}-{day}-{h}", tool,
                                     f"{BOT_NET}.{host(rng)}", a.client)))
        return rows
    weekday = day % 7 < 5
    n_sessions = rng.randint(3, 6) if weekday else int(rng.random() < 0.1)
    net = OFFICE if rng.random() < 0.7 else f"100.{a.home}"
    starts = sorted(rng.uniform(9, 17) for _ in range(n_sessions))
    for k, start in enumerate(starts):
        ts = day * DAY + start * 3600
        for tool in SCRIPTS[role](rng):
            rows.append(Row(Call(ts, a.name, a.role, f"{a.name}-{day}-{k}", tool,
                                 f"{net}.{host(rng)}", a.client)))
            ts += rng.uniform(20, 90)
    return rows


def background(rng: random.Random, agents: list[Agent], role_override=None) -> list[Row]:
    rows = []
    for day in range(DAYS):
        for a in agents:
            if day >= a.start_day:
                role = role_override(a, day) if role_override else None
                rows.extend(agent_day(rng, a, day, role))
    return rows


def sessions(rows: list[Row], agent: str, day: int) -> list[str]:
    seen: dict[str, float] = {}
    for r in rows:
        c = r.call
        if c.agent == agent and int(c.ts // DAY) == day:
            seen.setdefault(c.session, c.ts)
    return sorted(seen, key=lambda s: seen[s])


def insert(rows: list[Row], session: str, after_tool: str | None, tools: list[str], gap: float,
           **changes) -> None:
    """Insert tools into a session after the first call of after_tool (or the first call)."""
    idx = [i for i, r in enumerate(rows) if r.call.session == session]
    if not idx:
        return
    pos = next((i for i in idx if after_tool is None or rows[i].call.tool == after_tool), idx[0])
    base = rows[pos].call
    shift = gap * len(tools)
    for i in idx:
        if rows[i].call.ts > base.ts:
            rows[i] = Row(replace(rows[i].call, ts=rows[i].call.ts + shift), rows[i].tag)
    new = [Row(replace(base, ts=base.ts + gap * (k + 1), tool=t, **changes), "scenario")
           for k, t in enumerate(tools)]
    rows[pos + 1:pos + 1] = new


def mark(rows: list[Row], agent: str, days: range) -> None:
    for i, r in enumerate(rows):
        if r.call.agent == agent and int(r.call.ts // DAY) in days:
            rows[i] = Row(r.call, "scenario")


def new_session(rng: random.Random, agent: Agent, day: int, hour: float, tools: list[str],
                net: str, client: str, gap: float, tag: str = "scenario") -> list[Row]:
    ts = day * DAY + hour * 3600
    sid = f"{agent.name}-{day}-x{hour:.2f}"
    return [Row(Call(ts + gap * j, agent.name, agent.role, sid, t, f"{net}.{host(rng)}", client), tag)
            for j, t in enumerate(tools)]


# ---------------------------------------------------------------- scenarios
def build(name: str, rng: random.Random):
    """(rows, targets, days of interest, engine options) for one scenario."""
    agents = make_agents()
    by = {a.name: a for a in agents}
    window = range(START, DAYS)
    opts = {"team_fill": True}
    if name == "role_change":
        rows = background(rng, agents, lambda a, d: "developer" if a.name == "rev03" and d >= START
                          else None)
        mark(rows, "rev03", window)
        return rows, ["rev03"], window, opts
    if name.startswith("new_hire"):
        hire = Agent("dev99", "developer", 200, "cursor/1.4.2", start_day=START)
        rows = background(rng, agents + [hire])
        mark(rows, "dev99", window)
        if "off_role" in name:                               # a new hire merges on its first day
            insert(rows, sessions(rows, "dev99", START)[0], "get_issue", ["merge_pull_request"], 30.0)
        opts["team_fill"] = not name.endswith("no_fill")
        return rows, ["dev99"], window, opts
    rows = background(rng, agents)
    if name == "control":
        mark(rows, "rev03", range(START, START + 1))
        return rows, ["rev03"], window, opts
    if name == "over_fetch":
        mark(rows, "dev05", range(START, START + 1))       # same calls; only the inputs would differ
        return rows, ["dev05"], window, opts
    if name == "loop":
        s = sessions(rows, "dev05", START)[0]
        insert(rows, s, None, ["get_file_contents"] * 40, 12.0)
        return rows, ["dev05"], window, opts
    if name == "off_role":
        insert(rows, sessions(rows, "rev03", START)[0], "get_pull_request", ["merge_pull_request"], 30.0)
        return rows, ["rev03"], window, opts
    if name == "off_role_new_place":
        s = sessions(rows, "rev03", START)[0]
        for i, r in enumerate(rows):
            if r.call.session == s:
                rows[i] = Row(replace(r.call, address=f"203.0.{host(rng)}"), "scenario")
        insert(rows, s, "get_pull_request", ["merge_pull_request"], 30.0, address="203.0.113.7")
        return rows, ["rev03"], window, opts
    if name == "shared_credential":
        a = by["rev03"]
        for k, net in enumerate(["203.0", "198.51", "192.0"]):
            rows += new_session(rng, a, START, 15 + k * 0.3, reviewer_session(rng), net,
                                "python-httpx/0.27.0", 15.0)
        return rows, ["rev03"], window, opts
    if name == "slow_creep":
        for d, tool in zip(range(START, START + 10), CREEP_TOOLS + CREEP_TOOLS):
            ss = sessions(rows, "rev03", d)
            if ss:
                insert(rows, ss[0], "get_pull_request_files", [tool], 30.0)
        return rows, ["rev03"], window, opts
    if name == "daily_off_role":
        for d in range(START, START + 10):
            ss = sessions(rows, "rev03", d)
            if ss:
                insert(rows, ss[0], "get_pull_request", ["merge_pull_request"], 30.0)
        return rows, ["rev03"], window, opts
    if name == "nagging_loop":
        for d in range(START, START + 7):
            ss = sessions(rows, "dev05", d)
            if ss:
                insert(rows, ss[0], None, ["list_commits"] * 12, 20.0)
        return rows, ["dev05"], window, opts
    if name == "org_client_rollout":
        humans = [a for a in agents if a.role != "bot"]
        switch = {a.name: (START + rng.randrange(3)) * DAY + rng.uniform(9, 17) * 3600 for a in humans}
        for i, r in enumerate(rows):
            t = switch.get(r.call.agent)
            if t is not None and r.call.ts >= t:
                rows[i] = Row(replace(r.call, client="claude-code/1.0.3"),
                              "scenario" if r.call.ts < t + 3 * DAY else "")
        return rows, [a.name for a in humans], range(START, START + 3), opts
    if name == "org_retry_storm":
        humans = [a for a in agents if a.role != "bot"]
        for a in humans:
            rows += new_session(rng, a, START, 14 + rng.uniform(0, 0.8), ["get_file_contents"] * 8,
                                OFFICE, a.client, 10.0)
        return rows, [a.name for a in humans], range(START, START + 1), opts
    raise ValueError(name)


SCENARIOS = ["control", "loop", "off_role", "shared_credential", "off_role_new_place", "slow_creep",
             "daily_off_role", "nagging_loop", "role_change", "new_hire", "new_hire_off_role",
             "new_hire_off_role_no_fill", "org_client_rollout", "org_retry_storm", "over_fetch"]


def run(name: str) -> dict:
    rng = random.Random(SEED)
    rows, targets, days, opts = build(name, rng)
    rows.sort(key=lambda r: r.call.ts)
    impacts = {t["tool"]: t["impact"] for t in json.loads(SCAN.read_text())["tools"]}
    eng = Engine(n_tools=len(impacts), **opts)
    peak = None
    for r in rows:
        s = eng.score(r.call, impacts[r.call.tool])
        if r.tag == "scenario" and r.call.agent in targets:
            if peak is None or s.multiplier["base"] > peak.multiplier["base"]:
                peak = s
    out: dict = {"targets": len(targets), "peak": None}
    if peak is not None:
        out["peak"] = {"tool": peak.call.tool, "day": int(peak.call.ts // DAY),
                       "r_static": peak.r_static,
                       "family": {f: round(v, 1) for f, v in peak.family.items()},
                       "crowd_so_far": peak.crowd, "settled": peak.settled,
                       "multiplier": {v: round(m, 2) for v, m in peak.multiplier.items()},
                       "risk": {v: round(peak.risk(v), 1) for v in VARIANTS}}
    tset = set(targets)
    first3 = range(days[0], days[0] + 3)
    for v in VARIANTS:
        out[v] = {}
        for tag, floor in (("", 0.0), ("_floor", FLOOR)):
            flags, thr, scores = eng.daily_flags(BUDGET, v, floor)
            alerts_by_day = defaultdict(int)
            for (_, d), f in flags.items():
                alerts_by_day[d] += f
            out[v].update({
                "target_days_flagged" + tag: sorted({d for (a, d), f in flags.items()
                                                     if f and a in tset and d in days}),
                "threshold_first_day" + tag: round(thr.get(days[0], float("nan")), 1),
                "target_alerts_3d" + tag: sum(f for (a, d), f in flags.items() if f and a in tset
                                              and d in first3),
                "org_alerts_3d" + tag: sum(alerts_by_day[d] for d in first3)})
            out[v]["first_day_score"] = round(max(scores.get((a, days[0]), 0.0) for a in targets), 1)
    out["org_notices"] = [n for n in eng.org_notices() if n[0] in first3][:6]
    return out


def main():
    res = {}
    for name in SCENARIOS:
        res[name] = r = run(name)
        p = r["peak"] or {}
        print(f"{name:<26} peak {p.get('tool')} day {p.get('day')} x{p.get('multiplier')} "
              f"R {p.get('risk')} fam {p.get('family')} crowd {p.get('crowd_so_far')} "
              f"settled {p.get('settled')}")
        for v in VARIANTS:
            print(f"    {v:<7} flagged days {r[v]['target_days_flagged']} | day score "
                  f"{r[v]['first_day_score']} vs threshold {r[v]['threshold_first_day']} | "
                  f"target alerts (3 d) {r[v]['target_alerts_3d']} of org {r[v]['org_alerts_3d']}"
                  f" || floor {FLOOR:g}: days {r[v]['target_days_flagged_floor']}, org alerts "
                  f"{r[v]['org_alerts_3d_floor']}")
        if r["org_notices"]:
            print("    org notices:", r["org_notices"])
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
