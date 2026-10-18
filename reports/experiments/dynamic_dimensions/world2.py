"""Multi-server, multi-scenario synthetic MCP traffic with gateway-log/2 wire fields.

Grounded in the repo's real calls and the static scan, for three servers (github, calendar,
slack):
  roles + tool mixes      real personas in reports/experiments/real_benign/<org>_org.csv
  call order              tool-to-tool transitions from real ordered sessions (live_scale runs)
  argument values         real argument templates per tool (every real benign corpus)
  input effects           ~/mcp-static-scan reference importance (which/how_much/who/when/action/carried)
  tool operation/impact   ~/mcp-static-scan reference scan; asset sensitivity from its register
Simulated: who the agents are, when they work, how the org changes, the wire (address, client
software, user agent, protocol handshakes, request bytes) and labelled strange usage.

Every record is one message an agent sends (agent->server only; nothing from the server):
initialize, notifications/initialized, tools/list, tools/call, ping, notifications/cancelled.
Strange usage comes in 21 kinds at intensity 1 (mild), 2 (medium) or 3 (strong); legitimate
behaviour changes carry a `legit` tag so false alarms can be attributed.

Run:  python world2.py --server calendar --days 730 --agents 50 --seed 1 --out w2_calendar_M_s1.csv.gz
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

csv.field_size_limit(10**9)
REPO = Path(__file__).resolve().parents[3]
STATIC = Path.home() / "mcp-static-scan" / "examples"
SERVERS = {
    "github": ("github_helios", "github-helios"),
    "calendar": ("calendar_aurora", "calendar-aurora"),
    "slack": ("slack_vireo", "slack-vireo"),
}
START = datetime(2024, 10, 14, tzinfo=timezone.utc)
DAY = 86400.0
PAGE_KEYS = ("page", "cursor", "offset")
CLIENTS = [("claude-code", "python-httpx/0.28"), ("langchain-mcp-adapters", "python-httpx/0.27"),
           ("mcp", "python-httpx/0.28.1"), ("cursor", "node-fetch/3.3"), ("openai-agents", "python-httpx/0.27"),
           ("vscode-copilot", "undici/6.19")]
SCRIPT_CLIENT = ("python-requests-script", "python-requests/2.32")
KINDS = ["loop", "burst", "page_walk", "over_fetch", "long_span", "recipient_blast", "content_dump",
         "mode_switch", "fan_out", "sensitivity_escalation", "slow_creep", "off_role_tool", "workflow_skip",
         "off_hours", "dormant_wake", "repeated_habit", "shared_credential", "client_switch", "new_origin",
         "protocol_skip", "cancel_storm"]
HOLIDAYS = set()
for _y in (2024, 2025, 2026):
    HOLIDAYS |= {datetime(_y, 1, 1).date(), datetime(_y, 5, 1).date(), datetime(_y, 7, 4).date()}
    HOLIDAYS |= {(datetime(_y, 12, 24) + timedelta(d)).date() for d in range(8)}
    HOLIDAYS |= {(datetime(_y, 4, 14) + timedelta(d)).date() for d in range(5)}


def workday_factor(d) -> float:
    if d.weekday() >= 5 or d in HOLIDAYS:
        return 0.0
    f = 0.6 if (d.month == 8 and d.day <= 20) else 1.0
    return f * (1.5 if d.month in (3, 6, 9, 12) and d.day >= 17 else 1.0)


def base_key(path: str) -> str:
    return path.split("[")[0].split(".")[0]


# ---------------------------------------------------------------- server profile (real data)
class Profile:
    def __init__(self, server: str):
        org, stem = SERVERS[server]
        scan = json.load(open(STATIC / stem / "reference" / f"{stem}.scan.json"))
        imp = json.load(open(STATIC / stem / "reference" / f"{stem}.importance.json"))
        self.server = server
        self.op = {t["tool"]: t.get("operation") or "read" for t in scan["tools"]}
        self.impact = {t["tool"]: int(t.get("impact") or 3) for t in scan["tools"]}
        self.effects: dict[str, dict[str, str]] = defaultdict(dict)
        for t in imp["tools"]:
            for a in t["arguments"]:
                if a.get("important") and a.get("effect") not in (None, "none"):
                    self.effects[t["tool_name"]].setdefault(base_key(a["path"]), a["effect"])
        reg_sens = {a["asset"]: int(a.get("sensitivity") or 3) for a in scan["assets"]}
        rows = self._real_rows(org)
        self.templates: dict[str, list[dict]] = defaultdict(list)
        label_of: dict[str, Counter] = defaultdict(Counter)
        for r in rows:
            try:
                a = json.loads(r["args"] or "{}")
            except (json.JSONDecodeError, TypeError):
                continue
            if r["tool"] in self.op and isinstance(a, dict):
                self.templates[r["tool"]].append(a)
                w = self.which_value(r["tool"], a)
                if w and r.get("asset"):
                    label_of[w][r["asset"]] += 1
        self.tools = [t for t in self.op if self.templates.get(t)]
        # assets = values of each tool's main `which` input seen in real calls
        self.asset_sens: dict[str, int] = {}
        for t in self.tools:
            for a in self.templates[t]:
                w = self.which_value(t, a)
                if w and w not in self.asset_sens:
                    lab = label_of[w].most_common(1)[0][0] if label_of[w] else ""
                    self.asset_sens[w] = next((s for name, s in reg_sens.items()
                                               if lab and (name == lab or name.endswith(lab) or lab.endswith(name))), 3)
        # roles = real personas with their tool mixes
        self.roles: dict[str, Counter] = defaultdict(Counter)
        for r in rows:
            if r.get("_src") == "org" and r["tool"] in self.tools:
                self.roles[r["persona"]][r["tool"]] += 1
        # tool-to-tool transitions from real ordered sessions
        self.trans: dict[str, Counter] = defaultdict(Counter)
        for seq in self._sequences(org):
            for a, b in zip(["<start>"] + seq, seq):
                if b in self.tools:
                    self.trans[a][b] += 1

    def _real_rows(self, org):
        base = REPO / "reports" / "experiments"
        out = []
        for path, src in ((base / "real_benign" / f"{org}_org.csv", "org"),
                          (base / "real_benign" / f"{org}_real.csv", "real"),
                          (base / "real_warmup" / f"{org}_real.csv", "real")):
            if path.exists():
                with open(path, encoding="utf-8", errors="replace") as fh:
                    for r in csv.DictReader(fh):
                        r["_src"] = src
                        out.append(r)
        ls = base / "v5" / "five_level_v2_policy_v5r_nacombo" / "live_scale_all.csv"
        with open(ls, encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh):
                if r["org"] == org and r["category"] == "BENIGN":
                    r["_src"] = "ls"
                    out.append(r)
        return out

    def _sequences(self, org):
        ls = REPO / "reports/experiments/v5/five_level_v2_policy_v5r_nacombo/live_scale_all.csv"
        runs = defaultdict(list)
        with open(ls, encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh):
                if r["org"] == org and r["category"] == "BENIGN":
                    runs[r["run_id"]].append(r["tool"])
        return list(runs.values())

    def keys(self, tool, effect):
        return [k for k, e in self.effects.get(tool, {}).items() if e == effect]

    def which_value(self, tool, args):
        for k in self.keys(tool, "which"):
            if k in args and k not in ("owner", "account"):
                v = args[k]
                if isinstance(v, list):                 # a list of assets: the first one names the call
                    v = v[0] if v else None
                    if isinstance(v, dict):
                        v = v.get("id") or json.dumps(v, sort_keys=True)
                return json.dumps(v, sort_keys=True) if v is not None else None
        return None

    def next_tool(self, rng, prev, mix: Counter):
        """Real transition probabilities, restricted to the role's own tools (a real role does not
        drift into every tool); a rare legitimate exploration call may use any tool."""
        if rng.random() < 0.0005:
            return rng.choice(self.tools)
        tr = self.trans.get(prev) or self.trans["<start>"]
        tot_mix = sum(mix.values()) or 1
        allowed = [t for t in self.tools if mix.get(t, 0) > 0] or self.tools
        w = {t: (tr.get(t, 0) + 0.3) ** 0.6 * (mix.get(t, 0) / tot_mix) for t in allowed}
        r, acc = rng.random() * sum(w.values()), 0.0
        for t, x in w.items():
            acc += x
            if acc >= r:
                return t
        return t


# ---------------------------------------------------------------- agents
@dataclass
class Agent:
    aid: str
    role: str
    team: int
    bot: bool
    tz: int
    rate: float
    start: float
    end: float = math.inf
    pauses: list = field(default_factory=list)
    addresses: list = field(default_factory=list)       # [(t_from, [addr, ...])]
    clients: list = field(default_factory=list)         # [(t_from, (name, version, ua))]
    team_hist: list = field(default_factory=list)
    role_hist: list = field(default_factory=list)
    extra_assets: list = field(default_factory=list)    # [(t_from, asset)]

    def at(self, hist, t, default):
        v = default
        for t0, x in hist:
            if t >= t0:
                v = x
        return v

    def active(self, t):
        return self.start <= t < self.end and not any(a <= t < b for a, b in self.pauses)


class World:
    def __init__(self, server, days, n_agents, seed, bot_share=0.35, churn=1.0, per_kind=24):
        self.p = Profile(server)
        self.rng = random.Random(seed)
        self.days, self.n_agents, self.bot_share, self.churn, self.per_kind = days, n_agents, bot_share, churn, per_kind
        self.events = []
        self.sid = 0
        self.legit = defaultdict(list)
        self.creep = defaultdict(list)
        self.assets = dict(self.p.asset_sens)
        self.asset_created = {a: 0.0 for a in self.assets}
        self.team_assets = defaultdict(list)
        self.shared = []

    # ---- organisation
    def build(self):
        rng, p = self.rng, self.p
        names = sorted(self.assets, key=lambda a: rng.random())
        n_teams = max(2, min(6, self.n_agents // 8))
        self.n_teams = n_teams
        k_shared = max(1, len(names) // 5)
        self.shared = names[:k_shared]
        for i, a in enumerate(names[k_shared:]):
            self.team_assets[i % n_teams].append(a)
        roles = list(p.roles)
        weights = [sum(p.roles[r].values()) for r in roles]
        for i in range(self.n_agents):
            self._add_agent(rng.choices(roles, weights)[0], i % n_teams, 0.0)
        horizon = self.days * DAY
        t = 25 * DAY
        while t < horizon:                                       # hires, leavers
            self._add_agent(rng.choices(roles, weights)[0], rng.randrange(n_teams), t, legit="new_hire")
            t += rng.uniform(20, 45) * DAY / self.churn
        for a in rng.sample(self.agents, max(1, int(len(self.agents) * 0.08 * self.churn))):
            a.end = rng.uniform(90, self.days - 20) * DAY
        for a in self.agents:
            if not a.bot:                                        # vacations
                for y in range(math.ceil(self.days / 365)):
                    for _ in range(2):
                        t0 = (y * 365 + rng.uniform(20, 340)) * DAY
                        a.pauses.append((t0, t0 + rng.uniform(7, 21) * DAY))
                        self.legit[a.aid].append((t0 + 14 * DAY, t0 + 25 * DAY, "back_from_vacation"))
            # client upgrades and address changes (legitimate wire changes)
            t1 = a.start + rng.uniform(40, 90) * DAY
            name, ver, ua = a.clients[0][1]
            while t1 < horizon:
                ver = ver[:-1] + str((int(ver[-1]) + 1) % 10)
                a.clients.append((t1, (name, ver, ua)))
                self.legit[a.aid].append((t1, t1 + 3 * DAY, "client_upgrade"))
                t1 += rng.uniform(50, 110) * DAY / self.churn
            t2 = a.start + rng.uniform(60, 200) * DAY
            while t2 < horizon:
                if a.bot:
                    a.addresses.append((t2, [f"10.{a.team}.{rng.randrange(255)}.{rng.randrange(255)}"]))
                    tag = "redeploy"
                else:
                    home = a.addresses[-1][1]
                    a.addresses.append((t2, home[:1] + [f"100.{rng.randrange(64, 127)}.{rng.randrange(255)}.{rng.randrange(255)}"]))
                    tag = "new_network"
                self.legit[a.aid].append((t2, t2 + 5 * DAY, tag))
                t2 += rng.uniform(90, 240) * DAY / self.churn
        humans_all = [a for a in self.agents if not a.bot]
        human_roles = [r for r in p.roles if "bot" not in r] or list(p.roles)
        for a in rng.sample(humans_all, min(len(humans_all), max(1, int(len(self.agents) * 0.05 * self.churn)))):
            t0 = rng.uniform(120, self.days - 60) * DAY
            new_role = rng.choice([r for r in human_roles if r != a.role] or human_roles)
            a.role_hist.append((t0, new_role))
            self.legit[a.aid].append((t0, t0 + 30 * DAY, "role_change"))
        movers = rng.sample(humans_all, min(len(humans_all), max(1, int(len(self.agents) * 0.06 * self.churn))))
        for a in movers:
            t0 = rng.uniform(120, self.days - 60) * DAY
            a.team_hist.append((t0, (a.team + 1) % n_teams))
            self.legit[a.aid].append((t0, t0 + 30 * DAY, "team_transfer"))
        for a in rng.sample(humans_all, min(len(humans_all), max(1, len(self.agents) // 6))):
            t0 = rng.uniform(60, 200) * DAY                       # legitimate slow widening
            while t0 < horizon:
                a.extra_assets.append((t0, rng.choice(names)))
                t0 += rng.uniform(45, 90) * DAY
        t = 30 * DAY                                              # new assets appear
        k = 0
        while t < horizon:
            k += 1
            src = json.loads(rng.choice(names))
            base = src if isinstance(src, str) else "asset"
            new = json.dumps(f"{base}-n{k}")
            self.assets[new] = rng.choices([1, 2, 3, 4, 5], [10, 25, 35, 20, 10])[0]
            self.asset_created[new] = t
            self.team_assets[rng.randrange(n_teams)].append(new)
            t += rng.uniform(10, 30) * DAY

    agents: list = []

    def _add_agent(self, role, team, t, legit=""):
        rng = self.rng
        if not hasattr(self, "_agents"):
            self._agents = []
            self.agents = self._agents
        bot = "bot" in role or rng.random() < self.bot_share * 0.3
        name, ua = rng.choice(CLIENTS)
        a = Agent(f"{role}-{len(self.agents):03d}", role, team, bot, rng.choice([0, 2, 2, -5]),
                  rng.lognormvariate(math.log(4 if not bot else 1), 0.4), t)
        a.clients.append((t, (name, f"1.{rng.randrange(9)}.{rng.randrange(9)}", ua)))
        a.addresses.append((t, [f"10.{team}.{rng.randrange(255)}.{rng.randrange(255)}"] if bot else
                            [f"172.16.{rng.randrange(255)}.{rng.randrange(255)}", f"192.168.{rng.randrange(255)}.{rng.randrange(255)}"]))
        self.agents.append(a)
        if legit:
            self.legit[a.aid].append((t, t + 30 * DAY, legit))
        return a

    def assets_for(self, a, t):
        team = a.at(a.team_hist, t, a.team)
        own = [x for x in self.team_assets[team] if self.asset_created.get(x, 0) <= t]
        return own, [x for x in self.shared] + [x for t0, x in a.extra_assets if t0 <= t]

    # ---- emitting
    def emit(self, t, a, session, seq, method, tool=None, args=None, strange="", episode="", intensity=0,
             address=None, client=None):
        legit = next((tag for x, y, tag in self.legit[a.aid] if x <= t < y), "")
        cname, cver, ua = client or a.at(a.clients, t, a.clients[0][1])
        addr = address or self.rng.choice(a.at(a.addresses, t, a.addresses[0][1]))
        msg = {"jsonrpc": "2.0", "method": method}
        if method == "tools/call":
            msg.update(id=seq, params={"name": tool, "arguments": args})
        elif method == "initialize":
            msg.update(id=seq, params={"protocolVersion": "2025-11-25", "clientInfo": {"name": cname, "version": cver}})
        elif method in ("tools/list", "ping"):
            msg["id"] = seq
        which = self.p.which_value(tool, args) if tool else None
        if tool and which is None and args:
            which = None
        self.events.append((round(t, 3), a.aid, a.at(a.role_hist, t, a.role), a.at(a.team_hist, t, a.team),
                            session, seq, method, tool or "", json.dumps(args, sort_keys=True) if args else "",
                            which or "", self.assets.get(which, 0) if which else 0,
                            self.p.op.get(tool, "") if tool else "", addr, f"{cname}/{cver}", ua,
                            len(json.dumps(msg)), strange, legit, episode, intensity))

    def args_for(self, tool, asset=None):
        a = dict(self.rng.choice(self.p.templates[tool]))
        keys = [k for k in self.p.keys(tool, "which") if k not in ("owner", "account") and k in a]
        if asset is not None and keys:
            v = json.loads(asset)
            cur = a[keys[0]]
            if isinstance(cur, list) and cur and isinstance(cur[0], dict):
                a[keys[0]] = [{**cur[0], "id": v}]
            elif isinstance(cur, list):
                a[keys[0]] = [v]
            else:
                a[keys[0]] = v
        return a

    def session(self, t, a, plan=None, n=None, asset=None, gap=None, strange="", episode="", intensity=0,
                protocol=True, address=None, client=None, mark=None):
        """One session: handshake, then tool calls following real transitions for the role."""
        rng = self.rng
        self.sid += 1
        sid = f"s{self.sid}"
        role = a.at(a.role_hist, t, a.role)
        mix = self.p.roles.get(role) or Counter(self.p.tools)
        gap = gap or (2.0 if a.bot else 9.0)
        seq = 0
        lab = lambda i: (strange, episode, intensity) if (mark is None or i in mark) else ("", "", 0)
        kw = dict(address=address, client=client)
        if protocol:
            for m in ("initialize", "notifications/initialized"):
                seq += 1
                self.emit(t, a, sid, seq, m, strange=strange if mark is None else "", episode=episode if mark is None else "",
                          intensity=intensity if mark is None else 0, **kw)
                t += rng.uniform(0.05, 0.4)
            if rng.random() < (0.6 if a.bot else 0.92):
                seq += 1
                self.emit(t, a, sid, seq, "tools/list", strange=strange if mark is None else "",
                          episode=episode if mark is None else "", intensity=intensity if mark is None else 0, **kw)
                t += rng.uniform(0.1, 0.6)
        if plan is None:
            own, extra = self.assets_for(a, t)
            creep = [x for t0, x, t1 in self.creep.get(a.aid, []) if t0 <= t < t1]
            if creep and not strange and rng.random() < 0.15:
                asset, strange, episode, intensity = rng.choice(creep), "slow_creep", f"slow_creep:{a.aid}", 2
                mark = None
                lab = lambda i: (strange, episode, intensity)
            if asset is None:
                pool = own if (own and rng.random() < 0.75) else (extra or own or list(self.assets))
                asset = rng.choice(pool)
            n = n or max(1, int(rng.lognormvariate(math.log(3 if a.bot else 5), 0.5)))
            plan, prev = [], "<start>"
            for _ in range(n):
                tool = self.p.next_tool(rng, prev, mix)
                plan.append((tool, None))
                prev = tool
        for i, (tool, args) in enumerate(plan):
            if args is None:
                args = self.args_for(tool, asset)
            seq += 1
            s, e, k = lab(i)
            self.emit(t, a, sid, seq, "tools/call", tool, args, s, e, k, **kw)
            if rng.random() < 0.04:                                # benign client retry
                t += rng.uniform(0.5, 3)
                seq += 1
                self.emit(t, a, sid, seq, "tools/call", tool, args, s, e, k, **kw)
            if rng.random() < 0.01:
                seq += 1
                self.emit(t + 1, a, sid, seq, "notifications/cancelled", s and "" or "", **kw)
            t += rng.lognormvariate(math.log(gap), 0.8)
        return t, plan

    def normal_time(self, a, t):
        d = int(t // DAY)
        if a.bot:
            return d * DAY + self.rng.uniform(0, DAY)
        for _ in range(10):
            if workday_factor((START + timedelta(days=d)).date()) > 0:
                break
            d += 1
        h = min(19.0, max(8.0, self.rng.gauss(13.0, 2.6)))
        return d * DAY + ((h - a.tz) % 24) * 3600 + self.rng.uniform(0, 600)

    # ---- benign traffic
    def schedule(self):
        rng = self.rng
        for day in range(self.days):
            d = (START + timedelta(days=day)).date()
            f = workday_factor(d)
            for a in self.agents:
                t0 = day * DAY
                if not a.active(t0 + 12 * 3600):
                    continue
                if a.bot:
                    t = t0 + rng.uniform(0, 1800)
                    while t < t0 + DAY:
                        h = ((t - t0) / 3600 + a.tz) % 24
                        busy = f > 0 and 7 <= h < 20
                        t, _ = self.session(t, a)
                        t += rng.expovariate(1 / ((45 if busy else 160) * 60 / max(a.rate, 0.3)))
                    continue
                if rng.random() < 0.02 and f > 0:                   # on-call style night work (legit)
                    t = t0 + ((rng.uniform(0, 5) - a.tz) % 24) * 3600
                    self.legit[a.aid].append((t, t + 3 * 3600, "night_work"))
                    for _ in range(rng.randint(2, 4)):
                        t, _ = self.session(t, a, gap=4.0)
                n = sum(1 for _ in range(int(a.rate * f * 2)) if rng.random() < 0.5) if f > 0 else int(rng.random() < 0.04)
                for _ in range(n):
                    h = rng.gauss(13.0, 2.6) if rng.random() > 0.05 else rng.uniform(18, 22)
                    self.session(t0 + ((h - a.tz) % 24) * 3600 + rng.uniform(0, 600), a)

    # ---- strange usage
    def inject(self):
        rng, p = self.rng, self.p
        horizon = self.days * DAY
        humans = [a for a in self.agents if not a.bot and a.start == 0]
        for a in rng.sample(humans, min(len(humans), max(2, self.per_kind // 3))):
            t0 = rng.uniform(40, self.days - 120) * DAY
            a.pauses.append((t0, t0 + rng.uniform(60, 110) * DAY))
        tools_with = lambda eff: [t for t in p.tools if p.keys(t, eff)]
        for kind in KINDS:
            for i in range(self.per_kind):
                k = 1 + i % 3                                          # intensity 1..3
                t = rng.uniform(20, self.days - 20) * DAY
                pool = [a for a in self.agents if a.active(t)]
                if kind in ("off_hours", "dormant_wake", "slow_creep", "repeated_habit", "client_switch"):
                    pool = [a for a in pool if not a.bot]
                if not pool:
                    continue
                a = rng.choice(pool)
                ep = f"{kind}:{a.aid}:{i}"
                if kind == "dormant_wake":
                    woke = [(x, b) for x in self.agents for q, b in x.pauses if b - q >= 59 * DAY and b < horizon - DAY]
                    if i >= len(woke):
                        continue
                    a, b = woke[i]
                    self.session(self.normal_time(a, b), a, strange=kind, episode=f"{kind}:{a.aid}:{i}", intensity=2)
                    continue
                if kind != "off_hours":
                    t = self.normal_time(a, t)
                if not a.active(t):
                    continue
                own, extra = self.assets_for(a, t)
                asset = rng.choice(own or extra or list(self.assets))
                role = a.at(a.role_hist, t, a.role)
                mix = p.roles.get(role) or Counter(p.tools)
                usual = [x for x, _ in mix.most_common()] or p.tools
                common = dict(strange=kind, episode=ep, intensity=k)
                if kind == "loop":
                    tool = rng.choice(usual[:5])
                    args = self.args_for(tool, asset)
                    self.session(t, a, plan=[(tool, args)] * [5, 20, 100][k - 1], gap=2.0, **common)
                elif kind == "burst":
                    for j in range([3, 10, 30][k - 1]):
                        self.session(t + j * rng.uniform(30, 3600 / [3, 10, 30][k - 1]), a, gap=2.0, **common)
                elif kind == "page_walk":
                    cand = [x for x in usual if any(pk in tpl for tpl in p.templates[x][:50] for pk in PAGE_KEYS)] or \
                           [x for x in p.tools if any(pk in tpl for tpl in p.templates[x][:50] for pk in PAGE_KEYS)]
                    if not cand:
                        continue
                    tool = cand[0]
                    pk = next(pk for pk in PAGE_KEYS if any(pk in tpl for tpl in p.templates[tool][:50]))
                    plan = []
                    for n in range(1, [10, 30, 100][k - 1] + 1):
                        x = self.args_for(tool, asset)
                        x[pk] = n if pk == "page" else f"c{n}"
                        plan.append((tool, x))
                    self.session(t, a, plan=plan, gap=2.0, **common)
                elif kind in ("over_fetch", "long_span", "recipient_blast", "content_dump", "mode_switch"):
                    eff = {"over_fetch": "how_much", "long_span": "when", "recipient_blast": "who",
                           "content_dump": "carried", "mode_switch": "action"}[kind]
                    cand = [x for x in usual if x in tools_with(eff)] or tools_with(eff)
                    if not cand:
                        continue
                    # a normal session for this agent, with only the calls that carry the effect changed
                    seq_tools, prev = [], "<start>"
                    for _ in range(rng.randint(3, 8)):
                        prev = p.next_tool(rng, prev, mix)
                        seq_tools.append(prev)
                    pos = [j for j, x in enumerate(seq_tools) if x in cand]
                    if not pos:
                        j = rng.randrange(len(seq_tools) + 1)
                        seq_tools.insert(j, rng.choice(cand[:4]))
                        pos = [j]
                    pos = rng.sample(pos, min(len(pos), rng.randint(1, 3)))
                    plan = []
                    for j, x in enumerate(seq_tools):
                        if j in pos:
                            args = self.args_for(x, asset)
                            self._mutate(x, args, eff, k)
                            plan.append((x, args))
                        else:
                            plan.append((x, None))
                    self.session(t, a, plan=plan, asset=asset, mark=set(pos), **common)
                elif kind == "fan_out":
                    targets = rng.sample(list(self.assets), min([5, 12, 30][k - 1], len(self.assets)))
                    tools = [x for x in usual if p.keys(x, "which")] or [x for x in p.tools if p.keys(x, "which")]
                    plan = [(tools[j % min(3, len(tools))], self.args_for(tools[j % min(3, len(tools))], g))
                            for j, g in enumerate(targets)]
                    self.session(t, a, plan=plan, gap=4.0, **common)
                elif kind == "sensitivity_escalation":
                    team = a.at(a.team_hist, t, a.team)
                    hot = [x for x, s in self.assets.items() if s >= 4 and x not in self.team_assets[team]
                           and self.asset_created.get(x, 0) <= t] or list(self.assets)
                    self.session(t, a, asset=rng.choice(hot), **common)
                elif kind == "slow_creep":
                    team = a.at(a.team_hist, t, a.team)
                    others = [x for x in self.assets if x not in self.team_assets[team]]
                    picks = rng.sample(others, min([2, 4, 8][k - 1], len(others)))
                    for w, x in enumerate(picks):
                        self.creep[a.aid].append((t + w * 7 * DAY, x, t + (len(picks) + 12) * 7 * DAY))
                elif kind == "off_role_tool":
                    rare = [x for x in p.tools if mix.get(x, 0) == 0] or p.tools
                    rare.sort(key=lambda x: -p.impact.get(x, 3))
                    tool = rng.choice(rare[: [8, 4, 2][k - 1]])
                    _, plan = self.session(t, a, n=rng.randint(2, 5), asset=asset, strange="", episode="")
                    self.session(t + 60, a, plan=[(x, None) for x, _ in plan[:2]] + [(tool, None)], asset=asset,
                                 mark={len(plan[:2])}, **common)
                elif kind == "workflow_skip":
                    writes = [x for x in usual if p.op.get(x) in ("write", "remove")] or \
                             [x for x in p.tools if p.op.get(x) in ("write", "remove")]
                    self.session(t, a, plan=[(rng.choice(writes), None)] * [1, 2, 4][k - 1], asset=asset, **common)
                elif kind == "off_hours":
                    d = int(t // DAY)
                    self.session(d * DAY + ((rng.uniform(1, 5) - a.tz) % 24) * 3600, a, **common)
                elif kind == "repeated_habit":
                    tool = rng.choice([x for x in usual if p.keys(x, "how_much")] or usual)
                    for w in range([4, 8, 16][k - 1]):
                        tw = t + w * 7 * DAY
                        if a.active(tw):
                            plan = [(tool, self.args_for(tool, rng.choice(list(self.assets)))) for _ in range(15)]
                            self.session(tw, a, plan=plan, gap=2.0, **common)
                elif kind == "shared_credential":
                    other_client = rng.choice([c for c in CLIENTS if c[0] != a.at(a.clients, t, a.clients[0][1])[0]])
                    addr = f"203.0.{rng.randrange(255)}.{rng.randrange(255)}"
                    for j in range([2, 5, 12][k - 1]):
                        self.session(t + j * rng.uniform(300, 2400), a, address=addr,
                                     client=(other_client[0], "0.9.1", other_client[1]), **common)
                elif kind == "client_switch":
                    for j in range([2, 6, 15][k - 1]):
                        self.session(t + j * rng.uniform(600, 7200), a, client=(SCRIPT_CLIENT[0], "2.32", SCRIPT_CLIENT[1]), **common)
                elif kind == "new_origin":
                    addr = f"35.{rng.randrange(255)}.{rng.randrange(255)}.{rng.randrange(255)}"
                    for j in range([1, 4, 10][k - 1]):
                        self.session(t + j * rng.uniform(600, 7200), a, address=addr, **common)
                elif kind == "protocol_skip":
                    for j in range([2, 6, 20][k - 1]):
                        self.session(t + j * rng.uniform(60, 900), a, protocol=(k == 3 and j % 2 == 0), **common) \
                            if k == 3 else self.session(t + j * rng.uniform(60, 900), a, protocol=False, **common)
                elif kind == "cancel_storm":
                    tool = rng.choice(usual[:5])
                    args = self.args_for(tool, asset)
                    self.sid += 1
                    sid, seq, tt = f"s{self.sid}", 0, t
                    for m in ("initialize", "notifications/initialized", "tools/list"):
                        seq += 1
                        self.emit(tt, a, sid, seq, m, **common)
                    for _ in range([4, 12, 40][k - 1]):
                        seq += 1
                        self.emit(tt, a, sid, seq, "tools/call", tool, args, **common)
                        seq += 1
                        self.emit(tt + rng.uniform(5, 30), a, sid, seq, "notifications/cancelled", **common)
                        tt += rng.uniform(6, 40)

    def _mutate(self, tool, x, eff, k):
        rng, p = self.rng, self.p
        for key in p.keys(tool, eff):
            if eff == "how_much":
                v = x.get(key)
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    x[key] = int(max(v, 1) * [3, 10, 50][k - 1])
                elif v is None:
                    x[key] = [100, 500, 5000][k - 1]
            elif eff == "when":
                span = [60, 400, 3000][k - 1]
                if key.lower().endswith(("min", "after", "start")):
                    x[key] = (START - timedelta(days=span)).strftime("%Y-%m-%dT00:00:00Z")
                elif key.lower().endswith(("max", "before", "end")):
                    x[key] = (START + timedelta(days=span)).strftime("%Y-%m-%dT00:00:00Z")
            elif eff == "who":
                n = [6, 30, 150][k - 1]
                x[key] = [{"email": f"user{j}@ext{rng.randrange(9)}.example"} for j in range(n)] \
                    if key in ("attendees",) else [f"U{rng.randrange(10**6):06d}" for _ in range(n)]
            elif eff == "carried":
                x[key] = "x" * (200 * [5, 40, 300][k - 1])
            elif eff == "action":
                pool = [tpl[key] for tpl in p.templates[tool] if key in tpl]
                vals = Counter(json.dumps(v) for v in pool)
                rare = [json.loads(v) for v, c in vals.items() if c <= max(1, len(pool) // 50)]
                x[key] = rng.choice(rare) if rare else {"sendUpdates": "all", "visibility": "public"}.get(key, "ALL")

    def run(self):
        self.build()
        self.inject()
        self.schedule()
        self.events.sort(key=lambda e: (e[0], e[5]))
        return self.events


COLUMNS = ["ts", "agent", "role", "team", "session", "seq", "method", "tool", "args", "which", "sens", "op",
           "address", "client", "ua", "bytes", "strange", "legit", "episode", "intensity"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", choices=list(SERVERS), required=True)
    ap.add_argument("--days", type=int, default=730)
    ap.add_argument("--agents", type=int, default=50)
    ap.add_argument("--bot-share", type=float, default=0.35)
    ap.add_argument("--churn", type=float, default=1.0)
    ap.add_argument("--per-kind", type=int, default=24)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    w = World(a.server, a.days, a.agents, a.seed, a.bot_share, a.churn, a.per_kind)
    ev = w.run()
    with gzip.open(a.out, "wt", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(COLUMNS)
        wr.writerows(ev)
    calls = sum(1 for e in ev if e[6] == "tools/call")
    st = sum(1 for e in ev if e[16])
    print(f"{a.out.name}: {len(ev):,} messages ({calls:,} tool calls), {len(w.agents)} agents, "
          f"{len(w.assets)} assets, strange {st:,} ({st / len(ev):.2%}), episodes "
          f"{len({e[18] for e in ev if e[18]})}")


if __name__ == "__main__":
    main()
