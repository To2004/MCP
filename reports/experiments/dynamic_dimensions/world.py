"""Synthetic two-year GitHub-MCP organisation, grounded in the repo's real live calls.

What is real:  the roles and their tool mixes (real_benign/github_helios_org.csv), the
argument templates (every real GitHub call in real_benign/ and real_warmup/), the tool
impact levels and asset sensitivity levels (v5 nacombo static scan of github_helios).
What is simulated: who the callers are, when they work, how the org changes over two years,
and the injected strange usage. Nothing here is an attack: every call uses a real tool of
the server with well-formed arguments.

Each call carries two labels:
  strange   kind of injected strange usage ('' for none)
  legit     kind of legitimate behaviour change in effect ('' for none) — the expected
            source of false alarms (new hire, role change, on-call incident at night, ...)

Run:  python world.py --days 730 --seed 1 --out world_seed1.csv.gz
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REAL_CALLS = [REPO_ROOT / "reports/experiments/real_benign/github_helios_org.csv",
              REPO_ROOT / "reports/experiments/real_benign/github_helios_real.csv",
              REPO_ROOT / "reports/experiments/real_warmup/github_helios_real.csv"]
START = datetime(2024, 10, 14, tzinfo=timezone.utc)
DAY = 86400.0

# Static impact level per tool (v5 nacombo github_helios matrix) and the tool's class,
# which is what the order dimension reasons over.
IMPACT = {"list_commits": 2, "list_issues": 2, "list_pull_requests": 2, "get_pull_request_files": 2,
          "get_pull_request_status": 2, "search_repositories": 3, "get_file_contents": 3,
          "add_issue_comment": 3, "search_code": 3, "search_issues": 3, "search_users": 3,
          "get_issue": 3, "get_pull_request": 3, "get_pull_request_comments": 3,
          "get_pull_request_reviews": 3, "create_or_update_file": 4, "create_repository": 4,
          "push_files": 4, "create_issue": 4, "create_pull_request": 4, "fork_repository": 4,
          "create_branch": 4, "update_issue": 4, "create_pull_request_review": 4,
          "merge_pull_request": 4, "update_pull_request_branch": 4}
TOOL_CLASS = {t: ("list" if t.startswith("list_") else "search" if t.startswith("search_")
                  else "read" if t.startswith("get_") else "comment" if t == "add_issue_comment"
                  else "review" if t == "create_pull_request_review" else "merge" if t == "merge_pull_request"
                  else "admin" if t in ("create_repository", "fork_repository") else "write") for t in IMPACT}

# Seed repositories: the five named helios repos keep their scanned sensitivity; the real
# repos seen in the live corpus become the platform/web teams' estate.
SEED_REPOS = {
    "grid": [("helios-grid-infra-config", 4), ("helios-scada-gateway", 5), ("helios-ot-runbooks", 4)],
    "market": [("helios-market-bidding-engine", 4), ("market-pricing-models", 3), ("market-reports", 3)],
    "web": [("helios-public-site", 1), ("workreddit", 2), ("nintendo-whatsapp-dashboard", 2)],
    "platform": [("RubicCube", 2), ("mcp-traffic-scratch", 2), ("mcp-attack-testbed", 2),
                 ("Dynamic-context-aware-severity-ranking-of-K8s-misconfigurations", 3)],
}
SHARED_REPOS = [("helios-public-site", 1)]

# Tools each role already uses for reading (so injected strange usage stays inside the role's
# own toolset and is not trivially caught as "new tool for this caller").
ROLE_READ = {"developer": ["get_file_contents", "list_commits", "search_code", "list_issues", "get_issue"],
             "reviewer": ["get_pull_request", "get_pull_request_files", "list_pull_requests", "list_commits"],
             "triager": ["list_issues", "get_issue", "search_issues"],
             "release_manager": ["list_pull_requests", "list_commits", "get_pull_request_status"],
             "ci_bot": ["get_pull_request_status", "get_pull_request_files", "get_file_contents", "list_commits"],
             "admin": ["search_repositories", "search_users"]}
ROLE_LIST = {r: [t for t in ts if TOOL_CLASS[t] in ("list", "search")] for r, ts in ROLE_READ.items()}

STRANGE_KINDS = ["loop", "page_walk", "over_fetch", "fan_out", "off_role_tool", "workflow_skip",
                 "off_hours", "burst", "dormant_wake", "sensitivity_escalation", "slow_creep",
                 "repeated_habit"]


def holidays(year: int) -> set[date]:
    """Generic holiday calendar: new year, a spring week, two single days, a late-September pair."""
    days = {date(year, 1, 1), date(year, 5, 1), date(year, 7, 4), date(year, 9, 23), date(year, 9, 24)}
    days |= {date(year, 4, 14) + timedelta(d) for d in range(5)}
    days |= {date(year, 12, 24) + timedelta(d) for d in range(8)}
    return days


HOLIDAYS = holidays(2024) | holidays(2025) | holidays(2026)


def day_factor(d: date) -> float:
    """Org-wide activity multiplier for a calendar day (seasonality)."""
    if d.weekday() >= 5 or d in HOLIDAYS:
        return 0.0
    f = 1.0
    if d.month == 8 and d.day <= 20:
        f *= 0.6                                         # summer dip
    if d.month in (3, 6, 9, 12) and d.day >= 17:
        f *= 1.5                                         # quarter-end crunch
    return f


def in_freeze(d: date) -> bool:
    return (d.month == 12 and d.day >= 15) or (d.month == 1 and d.day <= 5)


@dataclass
class Caller:
    cid: str
    role: str
    team: str
    kind: str                       # "bot" | "assistant"
    tz: int                         # hours offset from UTC
    rate: float                     # sessions per normal workday
    start: float                    # seconds since START
    end: float = math.inf
    pauses: list = field(default_factory=list)       # [(t0, t1)] vacations or abandonment
    extra_repos: list = field(default_factory=list)  # [(t_from, repo, legit_tag)]
    role_hist: list = field(default_factory=list)    # [(t_from, role)]
    team_hist: list = field(default_factory=list)    # [(t_from, team)]
    oncall: set = field(default_factory=set)         # ISO week numbers (year*100+week)

    def role_at(self, t):
        r = self.role
        for t0, rr in self.role_hist:
            if t >= t0:
                r = rr
        return r

    def team_at(self, t):
        tm = self.team
        for t0, tt in self.team_hist:
            if t >= t0:
                tm = tt
        return tm

    def active(self, t):
        return self.start <= t < self.end and not any(a <= t < b for a, b in self.pauses)


class World:
    def __init__(self, days: int, seed: int):
        self.rng = random.Random(seed)
        self.days = days
        self.templates = self._load_templates()
        self.repos: dict[str, dict] = {}            # name -> {team, sens, created, archived}
        for team, rs in SEED_REPOS.items():
            for name, s in rs:
                self.repos[name] = {"team": team, "sens": s, "created": 0.0, "archived": math.inf}
        self.teams = list(SEED_REPOS)
        self.callers: list[Caller] = []
        self.open_prs: dict[str, dict[int, dict]] = defaultdict(dict)   # repo -> pr -> {reviewed}
        self.pr_seq = defaultdict(lambda: 100)
        self.events: list[tuple] = []
        self.sid = 0
        self.legit_windows: dict[str, list] = defaultdict(list)          # cid -> [(t0, t1, tag)]
        self.creep: dict[str, list] = defaultdict(list)                  # cid -> [(t_from, repo)]
        self.habits: list[tuple] = []                                    # (cid, t0, t1)

    # ---------- grounding in real calls ----------
    def _load_templates(self):
        csv.field_size_limit(10**8)
        tpl = defaultdict(list)
        for path in REAL_CALLS:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for r in csv.DictReader(fh):
                    try:
                        a = json.loads(r["args"] or "{}")
                    except (json.JSONDecodeError, TypeError):
                        continue
                    if r["tool"] in IMPACT and isinstance(a, dict):
                        tpl[r["tool"]].append(a)
        tpl["fork_repository"].append({"owner": "helios-org", "repo": "x"})
        return tpl

    def args_for(self, tool, repo=None, **over):
        a = dict(self.rng.choice(self.templates[tool]))
        if "owner" in a:
            a["owner"] = "helios-org"
        if repo is not None and "repo" in a:
            a["repo"] = repo
        if "q" in a and repo is not None and tool in ("search_code", "search_issues"):
            a["q"] = f"repo:helios-org/{repo} " + str(a["q"]).split()[-1]
        for k in ("content", "files", "body", "message"):
            if k in a:
                a[k] = "<redacted>"
        if "_size" in over:                        # page size, under whichever key the tool uses
            over = dict(over)
            a["perPage" if "perPage" in a else "per_page"] = over.pop("_size")
        a.update(over)
        return a

    # ---------- org timeline ----------
    def build_org(self):
        rng = self.rng
        n = 0

        def add(role, team, kind, start, rate):
            nonlocal n
            n += 1
            c = Caller(f"{role}-{n:03d}", role, team, kind, rng.choice([0, 2, 2, 2, -5]), rate, start)
            self.callers.append(c)
            return c

        for team in self.teams:
            add("ci_bot", team, "bot", 0, 1.0)
            for _ in range(3):
                add("developer", team, "assistant", 0, rng.lognormvariate(math.log(6), 0.35))
            add("reviewer", team, "assistant", 0, rng.lognormvariate(math.log(5), 0.3))
            add("triager", team, "assistant", 0, rng.lognormvariate(math.log(5), 0.3))
        for _ in range(2):
            add("release_manager", "org", "assistant", 0, rng.lognormvariate(math.log(2.5), 0.3))
        add("admin", "org", "assistant", 0, 0.6)

        horizon = self.days * DAY
        # growth: a new hire most months, a new team in month 10
        t = 20 * DAY
        while t < horizon:
            if 300 * DAY <= t < 330 * DAY and "data" not in self.teams:
                self.teams.append("data")
                for name, s in [("data-lake-etl", 4), ("data-warehouse-models", 4), ("data-dashboards", 2)]:
                    self.repos[name] = {"team": "data", "sens": s, "created": t, "archived": math.inf}
                add("ci_bot", "data", "bot", t, 1.0)
                self._new_hire(add("developer", "data", "assistant", t, 5.5), t)
                self._new_hire(add("reviewer", "data", "assistant", t, 4.0), t)
            role = rng.choices(["developer", "reviewer", "triager"], [6, 2, 2])[0]
            team = rng.choice([x for x in self.teams])
            self._new_hire(add(role, team, "assistant", t, rng.lognormvariate(math.log(5), 0.35)), t)
            t += rng.uniform(22, 40) * DAY
        # departures
        for c in rng.sample([c for c in self.callers if c.kind == "assistant"], 5):
            c.end = rng.uniform(120, self.days - 30) * DAY
        # vacations: two per assistant-year, 1-3 weeks (legit dormancy, then a normal wake-up)
        for c in self.callers:
            if c.kind != "assistant":
                continue
            for y in range(math.ceil(self.days / 365)):
                for _ in range(2):
                    t0 = (y * 365 + rng.uniform(30, 330)) * DAY
                    t1 = t0 + rng.uniform(7, 21) * DAY
                    c.pauses.append((t0, t1))
                    self.legit_windows[c.cid].append((t1, t1 + 2 * DAY, "back_from_vacation"))
        # role changes and team transfers (legit behaviour changes)
        devs = [c for c in self.callers if c.role == "developer" and c.start == 0]
        for c, new in zip(rng.sample(devs, 4), ["reviewer", "release_manager", "reviewer", "triager"]):
            t0 = rng.uniform(150, self.days - 60) * DAY
            c.role_hist.append((t0, new))
            self.legit_windows[c.cid].append((t0, t0 + 30 * DAY, "role_change"))
        for c in rng.sample([c for c in self.callers if c.kind == "assistant" and c.team != "org"], 4):
            t0 = rng.uniform(150, self.days - 60) * DAY
            new = rng.choice([x for x in SEED_REPOS if x != c.team])
            c.team_hist.append((t0, new))
            self.legit_windows[c.cid].append((t0, t0 + 30 * DAY, "team_transfer"))
        # legitimate seniority drift: some developers slowly pick up a cross-team repo
        for c in rng.sample(devs, max(1, len(devs) // 3)):
            t0 = rng.uniform(60, 200) * DAY
            while t0 < horizon:
                other = rng.choice([r for r, m in self.repos.items() if m["team"] != c.team and m["sens"] <= 3])
                c.extra_repos.append((t0, other, "legit_drift"))
                t0 += rng.uniform(50, 90) * DAY
        # on-call rotation for grid/platform developers
        for team in ("grid", "platform"):
            rota = [c for c in self.callers if c.team == team and c.role == "developer"]
            for w in range(self.days // 7 + 1):
                d = (START + timedelta(weeks=w)).isocalendar()
                rota[w % len(rota)].oncall.add(d[0] * 100 + d[1])
        # new repositories every ~3 weeks
        t = 30 * DAY
        k = 0
        while t < horizon:
            k += 1
            team = rng.choice(self.teams)
            s = rng.choices([2, 3, 4, 5], [50, 30, 15, 5])[0]
            self.repos[f"{team}-svc-{k:02d}"] = {"team": team, "sens": s, "created": t, "archived": math.inf}
            t += rng.uniform(14, 30) * DAY
        for name in rng.sample([r for r in self.repos if self.repos[r]["created"] == 0], 2):
            self.repos[name]["archived"] = rng.uniform(200, 500) * DAY

    def _new_hire(self, c, t):
        self.legit_windows[c.cid].append((t, t + 30 * DAY, "new_hire"))

    def team_repos(self, team, t):
        return [r for r, m in self.repos.items()
                if m["team"] == team and m["created"] <= t < m["archived"]]

    def caller_repos(self, c, t):
        team = c.team_at(t)
        rs = self.team_repos(team, t) if team != "org" else [r for r, m in self.repos.items() if m["created"] <= t < m["archived"]]
        rs = rs + [r for t0, r, _ in c.extra_repos if t0 <= t and self.repos[r]["archived"] > t]
        return rs or ["helios-public-site"]

    # ---------- emitting calls ----------
    def emit(self, t, c, tool, args, strange="", sid=None, episode=""):
        legit = next((tag for a, b, tag in self.legit_windows[c.cid] if a <= t < b), "")
        repo = args.get("repo", "")
        if not legit and repo:
            legit = next((tag for t0, r, tag in c.extra_repos if r == repo and t0 <= t < t0 + 30 * DAY), "")
            if not legit and t - self.repos.get(repo, {}).get("created", -1e18) < 14 * DAY:
                legit = "new_repo"
        self.events.append((round(t, 3), c.cid, c.role_at(t), c.team_at(t), sid if sid is not None else self.sid,
                            tool, json.dumps(args, sort_keys=True), repo,
                            self.repos.get(repo, {}).get("sens", 0), strange, legit,
                            episode or (f"{strange}:{self.sid}" if strange else "")))

    def session(self, t, c, strange="", repo=None, gap=8.0, forced=None, episode="", mark_only=False):
        """One task episode for caller c starting at t, following its role's workflow."""
        rng = self.rng
        self.sid += 1
        role = c.role_at(t)
        rs = self.caller_repos(c, t)
        # creeping callers drift into the extra repos they picked up
        creep = [r for t0, r, t1 in self.creep.get(c.cid, []) if t0 <= t < t1]
        if creep and not strange and rng.random() < 0.15:
            repo, strange = rng.choice(creep), "slow_creep"
            episode = f"slow_creep:{c.cid}:{repo}"
        repo = repo or (rng.choice(rs) if rng.random() > 0.06 else rng.choice(list(self.repos)))
        if self.repos.get(repo, {}).get("created", 0) > t:
            repo = rng.choice(rs)
        plan = forced or self.workflow(role, repo, t)
        for tool, over in plan:
            if tool == "merge_pull_request" and over.get("_skip") is None and in_freeze((START + timedelta(seconds=t)).date()):
                continue
            marked = not mark_only or bool(over.get("_mark"))
            lab, ep = (strange, episode) if marked else ("", "")
            over = {k: v for k, v in over.items() if not k.startswith("_") or k == "_size"}
            self.emit(t, c, tool, self.args_for(tool, repo, **over), lab, episode=ep)
            if rng.random() < 0.04:                     # benign client retry of the same call
                t += rng.uniform(0.5, 3)
                self.emit(t, c, tool, self.args_for(tool, repo, **over), lab, episode=ep)
            t += rng.lognormvariate(math.log(gap), 0.8)
        return t

    def _pr(self, repo, want_reviewed=None):
        prs = self.open_prs[repo]
        cands = [p for p, m in prs.items() if want_reviewed is None or m["reviewed"] == want_reviewed]
        return self.rng.choice(cands) if cands else None

    def workflow(self, role, repo, t):
        rng = self.rng
        R = lambda lo, hi: rng.randint(lo, hi)
        if role == "developer":
            w = rng.choices(["fix", "investigate", "issues"], [3, 4, 3])[0]
            if w == "fix":
                pr = self.pr_seq[repo] = self.pr_seq[repo] + 1
                self.open_prs[repo][pr] = {"reviewed": False}
                return ([("list_issues", {}), ("get_issue", {})] + [("get_file_contents", {})] * R(1, 4)
                        + [("create_branch", {"branch": f"feature/{pr}"}),
                           ("push_files", {"branch": f"feature/{pr}"}),
                           ("create_pull_request", {"head": f"feature/{pr}", "base": "main"})])
            if w == "investigate":
                return [("search_code", {})] + [("get_file_contents", {})] * R(1, 5) + [("list_commits", {})]
            return [("search_issues", {})] + [("get_issue", {})] * R(1, 3) + ([("add_issue_comment", {})] if rng.random() < .4 else [])
        if role == "reviewer":
            pr = self._pr(repo, False) or self._pr(repo)
            if pr is None:
                return [("list_pull_requests", {}), ("list_commits", {})]
            self.open_prs[repo][pr]["reviewed"] = True
            p = {"pull_number": pr}
            return [("list_pull_requests", {}), ("get_pull_request", p), ("get_pull_request_files", p),
                    ("get_pull_request_comments", p), ("get_pull_request_reviews", p),
                    ("create_pull_request_review", p)] + ([("update_pull_request_branch", p)] if rng.random() < .15 else [])
        if role == "triager":
            return ([("list_issues", {}) if rng.random() < .6 else ("search_issues", {})] + [("get_issue", {})] * R(1, 4)
                    + [rng.choice([("update_issue", {}), ("add_issue_comment", {}), ("create_issue", {})])])
        if role == "release_manager":
            pr = self._pr(repo, True)
            out = [("list_pull_requests", {}), ("list_commits", {})]
            if pr is not None:
                p = {"pull_number": pr}
                out += [("get_pull_request_status", p), ("get_pull_request_reviews", p), ("merge_pull_request", p)]
                del self.open_prs[repo][pr]
            if rng.random() < .2:
                out.append(("create_branch", {"branch": f"release/{int(t // DAY)}"}))
            return out
        if role == "ci_bot":
            out = []
            for _ in range(R(1, 3)):
                pr = self._pr(repo)
                if pr is None:
                    break
                p = {"pull_number": pr}
                out += [("get_pull_request_status", p), ("get_pull_request_files", p)] + [("get_file_contents", {})] * R(0, 2)
            return out + [("list_commits", {})]
        if role == "admin":
            return rng.choice([[("search_users", {})], [("search_repositories", {})],
                               [("search_repositories", {}), ("search_users", {})]])
        return [("list_issues", {})]

    def schedule(self):
        """Benign traffic for every caller, day by day."""
        rng = self.rng
        for day in range(self.days):
            d = (START + timedelta(days=day)).date()
            f = day_factor(d)
            iso = d.isocalendar()
            for c in self.callers:
                t_day = day * DAY
                if not c.active(t_day + 12 * 3600):
                    continue
                if c.kind == "bot":
                    # CI runs around the clock, denser in working hours, follows the org's PR flow
                    t = t_day
                    while t < t_day + DAY:
                        h = ((t - t_day) / 3600 + c.tz) % 24
                        busy = f > 0 and 7 <= h < 20
                        t = self.session(t, c, gap=2.0) + rng.expovariate(1 / ((40 if busy else 150) * 60))
                    continue
                oncall = (iso[0] * 100 + iso[1]) in c.oncall
                if oncall and rng.random() < 0.7 / 7:          # incident: any hour, broad and fast
                    t = t_day + rng.uniform(0, DAY)
                    self.legit_windows[c.cid].append((t, t + 3 * 3600, "oncall_incident"))
                    for r in rng.sample(self.caller_repos(c, t), min(4, len(self.caller_repos(c, t)))):
                        t = self.session(t, c, repo=r, gap=3.0, forced=[("list_commits", {}), ("search_code", {})]
                                         + [("get_file_contents", {})] * rng.randint(2, 6))
                n = 0
                if f > 0:
                    n = sum(1 for _ in range(int(c.rate * f * 2)) if rng.random() < 0.5)
                elif rng.random() < 0.04:
                    n = 1                                          # occasional weekend/holiday session
                for _ in range(n):
                    h = rng.gauss(13.0, 2.6) if rng.random() > 0.05 else rng.uniform(18, 22)
                    t = t_day + ((h - c.tz) % 24) * 3600 + rng.uniform(0, 600)
                    self.session(t, c)

    # ---------- injected strange usage ----------
    def inject(self, per_kind: int):
        rng = self.rng
        horizon = self.days * DAY
        assistants = lambda t: [c for c in self.callers if c.kind == "assistant" and c.active(t)]
        anyone = lambda t: [c for c in self.callers if c.active(t)]
        # abandoned agents for dormant_wake: stop for >= 60 days, then come back strange
        for c in rng.sample([c for c in self.callers if c.kind == "assistant" and c.start == 0], per_kind // 2):
            t0 = rng.uniform(40, self.days - 120) * DAY
            c.pauses.append((t0, t0 + rng.uniform(60, 110) * DAY))
        for kind in STRANGE_KINDS:
            for i in range(per_kind):
                t = rng.uniform(14, self.days - 14) * DAY
                pool = assistants(t) if kind in ("off_hours", "dormant_wake", "slow_creep", "repeated_habit") else anyone(t)
                if kind in ("fan_out", "sensitivity_escalation", "over_fetch", "page_walk", "repeated_habit"):
                    pool = [c for c in pool if c.role_at(t) != "admin"]
                if kind == "workflow_skip":
                    pool = [c for c in pool if c.role_at(t) in ("developer", "release_manager")]
                if kind == "dormant_wake":
                    woke = [(c, b) for c in self.callers for a, b in c.pauses if b - a >= 59 * DAY and b < horizon - DAY]
                    if i >= len(woke):
                        break
                    c, tw = woke[i]
                    self.session(self.normal_time(c, tw), c, strange=kind)
                    continue
                if not pool:
                    continue
                c = rng.choice(pool)
                if kind != "off_hours":
                    t = self.normal_time(c, t)        # strange usage happens when the caller normally works
                if not c.active(t):
                    continue
                rs = self.caller_repos(c, t)
                repo = rng.choice(rs)
                role = c.role_at(t)
                ep = f"{kind}:{c.cid}:{i}"
                plan = list(self.workflow(role, repo, t)) or [("list_commits", {})]
                if kind == "loop":
                    k = rng.choice([5, 10, 30, 100])
                    j = rng.randrange(len(plan))
                    tool, over = plan[j]
                    plan[j + 1:j + 1] = [(tool, {**over, "_mark": 1}) for _ in range(k)]
                    self.session(t, c, strange=kind, repo=repo, forced=plan, episode=ep, mark_only=True, gap=3.0)
                elif kind == "page_walk":
                    tool = next((tl for tl, _ in plan if tl in ROLE_LIST[role]), rng.choice(ROLE_LIST[role]))
                    walk = [(tool, {"page": p, "_mark": 1}) for p in range(1, rng.choice([10, 25, 60]) + 1)]
                    j = next((n for n, (tl, _) in enumerate(plan) if tl == tool), len(plan))
                    plan[j:j + 1] = walk
                    self.session(t, c, strange=kind, repo=repo, forced=plan, episode=ep, mark_only=True, gap=3.0)
                elif kind == "over_fetch":
                    for j in range(rng.randint(3, 6)):
                        p2 = list(self.workflow(role, repo, t)) or []
                        p2 = [(tl, {**o, "_size": 100, "_mark": 1}) if tl in ROLE_LIST[role] else (tl, o) for tl, o in p2]
                        if not any(o.get("_mark") for _, o in p2):
                            p2.append((rng.choice(ROLE_LIST[role]), {"_size": 100, "_mark": 1}))
                        self.session(t + j * rng.uniform(1800, 5400), c, strange=kind, repo=repo, forced=p2,
                                     episode=ep, mark_only=True)
                elif kind == "fan_out":
                    k = rng.choice([5, 10, 20])
                    targets = rng.sample(list(self.repos), min(k, len(self.repos)))
                    reads = [x for x in ROLE_READ[role] if x not in ("search_repositories", "search_users")] or ["list_commits"]
                    self.sid += 1
                    for j, r in enumerate(targets):
                        tool = reads[j % len(reads)]
                        self.emit(t + j * rng.uniform(4, 15), c, tool, self.args_for(tool, r), kind, episode=ep)
                elif kind == "off_role_tool":
                    odd = {"ci_bot": ["push_files", "merge_pull_request", "create_issue"],
                           "triager": ["merge_pull_request", "push_files", "create_branch"],
                           "reviewer": ["create_repository", "push_files"],
                           "developer": ["create_repository", "fork_repository", "merge_pull_request"],
                           "release_manager": ["create_repository", "update_issue"],
                           "admin": ["push_files", "merge_pull_request"]}[role]
                    tool = rng.choice(odd)
                    over = {"pull_number": self._pr(repo) or 1} if tool == "merge_pull_request" else {}
                    plan.insert(rng.randrange(len(plan) + 1), (tool, {**over, "_mark": 1, "_skip": 1}))
                    self.session(t, c, strange=kind, repo=repo, forced=plan, episode=ep, mark_only=True)
                elif kind == "workflow_skip":
                    pr = self._pr(repo, False)
                    if pr is not None and role == "release_manager":
                        del self.open_prs[repo][pr]
                        plan = [("list_pull_requests", {}), ("list_commits", {}),
                                ("merge_pull_request", {"pull_number": pr, "_skip": 1, "_mark": 1})]
                    else:
                        plan = [(tl, {**o, "branch": "main", "_mark": 1}) if tl == "push_files" else (tl, o)
                                for tl, o in plan if tl != "create_pull_request"]
                        if not any(o.get("_mark") for _, o in plan):
                            plan.append(("push_files", {"branch": "main", "_mark": 1}))
                    self.session(t, c, strange=kind, repo=repo, forced=plan, episode=ep, mark_only=True)
                elif kind == "off_hours":
                    d = int(t // DAY)
                    local_h = rng.uniform(1, 5)
                    self.session(d * DAY + ((local_h - c.tz) % 24) * 3600, c, strange=kind, repo=repo, episode=ep)
                elif kind == "burst":
                    k = rng.choice([5, 10, 20])
                    for j in range(k):
                        self.session(t + j * rng.uniform(60, 3600 / k), c, strange=kind, gap=3.0, episode=ep)
                elif kind == "sensitivity_escalation":
                    hot = [r for r, m in self.repos.items() if m["sens"] >= 4 and m["team"] != c.team_at(t)
                           and m["created"] <= t]
                    r = rng.choice(hot)
                    self.session(t, c, strange=kind, repo=r, episode=ep)      # its normal workflow, foreign repo
                elif kind == "slow_creep":
                    others = [r for r, m in self.repos.items() if m["team"] != c.team_at(t) and m["created"] <= t]
                    if i >= per_kind // 2:
                        break
                    picks = rng.sample(others, min(6, len(others)))
                    for w, r in enumerate(picks):
                        self.creep[c.cid].append((t + w * 7 * DAY, r, t + (len(picks) + 12) * 7 * DAY))
                elif kind == "repeated_habit":
                    if i >= per_kind // 2:
                        break
                    weeks = rng.randint(8, 20)
                    tool = rng.choice(ROLE_LIST[role])
                    for w in range(weeks):
                        tw = t + w * 7 * DAY
                        if not c.active(tw):
                            continue
                        self.sid += 1
                        for p in range(1, 21):
                            self.emit(tw + p * 2.0, c, tool, self.args_for(tool, repo, page=p), kind,
                                      episode=f"repeated_habit:{c.cid}:{i}")

    def normal_time(self, c, t):
        """A moment on or after day(t) when this caller normally works (bots: any hour)."""
        d = int(t // DAY)
        if c.kind == "bot":
            return d * DAY + self.rng.uniform(0, DAY)
        for _ in range(10):
            if day_factor((START + timedelta(days=d)).date()) > 0:
                break
            d += 1
        h = min(19.0, max(8.0, self.rng.gauss(13.0, 2.6)))
        return d * DAY + ((h - c.tz) % 24) * 3600 + self.rng.uniform(0, 600)

    def run(self, per_kind):
        self.build_org()
        self.inject(per_kind)          # sets creep schedules and abandonment before traffic
        self.schedule()
        self.events.sort(key=lambda e: e[0])
        return self.events


COLUMNS = ["ts", "caller", "role", "team", "session", "tool", "args", "repo", "sens", "strange", "legit",
           "episode"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=730)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--per-kind", type=int, default=40)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    w = World(a.days, a.seed)
    ev = w.run(a.per_kind)
    with gzip.open(a.out, "wt", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(COLUMNS)
        wr.writerows(ev)
    callers = {e[1] for e in ev}
    n_str = sum(1 for e in ev if e[9])
    print(f"{len(ev):,} calls, {len(callers)} callers, {len(w.repos)} repos, "
          f"strange calls {n_str:,} ({n_str / len(ev):.2%}) -> {a.out}")


if __name__ == "__main__":
    main()
