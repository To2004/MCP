"""Stress test of the bounded per-dimension formula (DIMENSION_FORMULAS.md) on all 9 simulated
organisations (GitHub, Calendar, Slack) and on hand-made edge cases.

Per call, each dimension gives s in [0, 1):
  more than usual    s = (v + c) / (v + c + 2 x (his average + c))      c = 1 call (calls in hour),
                                                                         1 minute (session length),
                                                                         1 KB (request size)
  rarer than usual   share = (n + 1) / (N + K), K = values he used + 1
                     s = c / (1 + 2 x K x share)                         tool (c = 0.9), asset, time (c = 1)
  policy rule        broken -> its value: 0.9 by default, protocol skip 0.7 (only for an agent who
                     normally sends initialize, so stateless clients do not fire)
S = max s;  M = 5^(2S-1) if S >= 0.5 else 0.7^(1-2S);  warm-up: M = 1 for the first 5 tool calls.
Every message is scored (origin and protocol rules also apply to initialize / tools/list).

Design changes in this version (user, 2026-10-19): "same tool in 10 minutes" removed; the fixed
"session over 10 minutes" rule replaced by session length against his own usual; a never-used tool
tops out near x3.6; IP cut to /16; protocol skip lowered to 0.7 (x1.9) and learned; smoothing in
natural units (1 call, 1 minute, 1 KB) so tiny absolute changes do not count.
The variant "with_repeat" adds "same tool in 10 minutes" back, to show what removing it costs.

Run:  python bounded_stress.py            (writes results/bounded_stress.json)
"""
from __future__ import annotations

import csv
import gzip
import json
import math
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from vkp_eval import CAL_DAYS, alerts

HERE = Path(__file__).parent
NAMES = ["github_M", "github_S", "github_bots", "calendar_M", "calendar_M2", "calendar_L", "slack_M",
         "slack_M2", "slack_churn"]
DAY, W = 86400.0, 90
MAX_M, MIN_M = 5.0, 0.7
SENSITIVE, READ_MEMORY_DAYS = 4, 7
REVIEW_TOOLS = {"get_pull_request", "get_pull_request_reviews", "get_pull_request_status"}
WRITE_OPS = {"write", "remove", "delete"}
DIMS = ["calls_1h", "repeat_10m", "session_length", "request_size", "tool_share", "asset_share",
        "time_of_day", "first_ip", "first_client", "burst", "sequence", "request_big", "protocol_skip"]


@dataclass(frozen=True)
class Config:
    tolerance: float = 2.0
    warmup: int = 5
    burst_per_min: int = 20
    request_limit: int = 10_000
    ip_prefix: int = 2             # /16
    rule: float = 0.9              # x3.6
    protocol_skip: float = 0.7     # x1.9
    tool_ceiling: float = 0.9      # a never-used tool tops out near x3.6
    with_repeat: bool = False      # "same tool in 10 minutes" (removed in this version)
    asset_novelty: bool = False    # a never-touched asset is judged by how often he touches new assets
    per_day: bool = False          # tool / asset / time: how many times a day he does something this rare


DESIGN = Config()
WITH_REPEAT = Config(with_repeat=True)
ASSET_NOVELTY = Config(asset_novelty=True)
PER_DAY = Config(per_day=True)


def multiplier(S: float) -> float:
    return MAX_M ** (2 * S - 1) if S >= 0.5 else MIN_M ** (1 - 2 * S)


class RunningMean:
    """His average over the last 90 days (read before adding the current value)."""

    def __init__(self):
        self.log, self.total = deque(), 0.0

    def mean_then_add(self, value: float, day: int):
        while self.log and self.log[0][0] <= day - W:
            self.total -= self.log.popleft()[1]
        mean = self.total / len(self.log) if self.log else None
        self.log.append((day, value))
        self.total += value
        return mean


class Shares:
    """90-day counts of values; share = (n + 1) / (N + K), K = distinct values used + 1."""

    def __init__(self):
        self.counts, self.total, self.log = Counter(), 0, deque()
        self.days, self.new_uses = Counter(), 0

    def expire(self, day: int) -> None:
        while self.log and self.log[0][0] <= day - W:
            d, k, new = self.log.popleft()
            self.counts[k] -= 1
            if not self.counts[k]:
                del self.counts[k]
            self.days[d] -= 1
            if not self.days[d]:
                del self.days[d]
            self.new_uses -= new
            self.total -= 1

    def per_day(self, keys, tail: bool, weekend: int | None = None) -> float:
        """How many times a day he does something this rare: (calls + 1) / (active days + 1).
        tail: count his calls on every value at most this common (never used: his first uses).
        weekend: count only active days of the same kind (0 weekday, 1 weekend)."""
        n = sum(self.counts.get(k, 0) for k in keys)
        if not tail:
            rare = n
        elif n == 0:
            rare = self.new_uses
        else:
            rare = sum(c for c in self.counts.values() if c <= n)
        days = len(self.days) if weekend is None else sum(1 for d in self.days if int(d % 7 >= 5) == weekend)
        return (rare + 1) / (days + 1)

    def score(self, keys, tolerance: float, ceiling: float = 1.0) -> float:
        k = len(self.counts) + 1
        share = (sum(self.counts.get(x, 0) for x in keys) + 1) / (self.total + k)
        return ceiling / (1 + tolerance * k * share)

    def add(self, key, day: int, count_new: bool = True) -> None:
        new = int(key not in self.counts and count_new)
        self.counts[key] += 1
        self.days[day] += 1
        self.new_uses += new
        self.total += 1
        self.log.append((day, key, new))


@dataclass
class AgentState:
    tool_calls: int = 0
    calls: deque = field(default_factory=deque)
    recent: deque = field(default_factory=deque)
    mean_1h: RunningMean = field(default_factory=RunningMean)
    mean_rep: RunningMean = field(default_factory=RunningMean)
    mean_sess: RunningMean = field(default_factory=RunningMean)
    mean_size: dict = field(default_factory=lambda: defaultdict(RunningMean))
    sessions: int = 0
    sessions_init: int = 0
    new_assets: deque = field(default_factory=deque)
    tools: Shares = field(default_factory=Shares)
    assets: Shares = field(default_factory=Shares)
    hours: Shares = field(default_factory=Shares)
    seen_ip: set = field(default_factory=set)
    seen_client: set = field(default_factory=set)
    last_read: dict = field(default_factory=dict)


class BoundedEngine:
    def __init__(self, cfg: Config = DESIGN):
        self.cfg = cfg
        self.agents: dict[str, AgentState] = defaultdict(AgentState)
        self.sessions: dict[str, dict] = {}

    def _more(self, value: float, mean, unit: float = 1.0) -> float:
        if mean is None:
            return 0.0
        return (value + unit) / (value + unit + self.cfg.tolerance * (mean + unit))

    def score(self, ts: float, agent: str, session: str, method: str, tool: str = "", asset: str = "",
              sens: int = 0, op: str = "", address: str = "", client: str = "", size: float = 0.0):
        """Returns (M, {dimension: s}) for one message."""
        cfg, st = self.cfg, self.agents[agent]
        day = int(ts // DAY)
        sess = self.sessions.setdefault(session, {"start": ts, "init": False, "read_sens": set(),
                                                  "review": False})
        if method == "initialize":
            sess["init"] = True
        warm = st.tool_calls >= cfg.warmup
        s: dict[str, float] = {}
        ip = ".".join(address.split(".")[:cfg.ip_prefix])
        fam = client.split("/")[0].strip().lower()
        if warm and ip and ip not in st.seen_ip:
            s["first_ip"] = cfg.rule
        if warm and fam and fam not in st.seen_client:
            s["first_client"] = cfg.rule
        st.seen_ip.add(ip)
        st.seen_client.add(fam)
        if method == "tools/call":
            if not sess.get("counted"):
                sess["counted"] = True
                normally_init = st.sessions >= 3 and st.sessions_init >= 0.5 * st.sessions
                st.sessions += 1
                st.sessions_init += int(sess["init"])
            else:
                normally_init = st.sessions >= 3 and st.sessions_init >= 0.5 * st.sessions
            q = st.calls
            q.append(ts)
            while q[0] < ts - 3600:
                q.popleft()
            m_1h = st.mean_1h.mean_then_add(len(q), day)
            rq = st.recent
            rq.append((ts, tool))
            while rq[0][0] < ts - 600:
                rq.popleft()
            rep = sum(1 for _, t in rq if t == tool)
            m_rep = st.mean_rep.mean_then_add(rep, day)
            age = (ts - sess["start"]) / 60
            m_sess = st.mean_sess.mean_then_add(age, day)
            m_size = st.mean_size[tool].mean_then_add(size, day)
            for sh in (st.tools, st.assets, st.hours):
                sh.expire(day)
            daytype, hour = int(day % 7 >= 5), int((ts % DAY) // 3600)
            near = [(daytype, (hour + k) % 24) for k in (-1, 0, 1)]
            if warm:
                s["calls_1h"] = self._more(len(q), m_1h)
                if cfg.with_repeat:
                    s["repeat_10m"] = self._more(rep, m_rep)
                s["session_length"] = self._more(age, m_sess)
                s["request_size"] = self._more(size, m_size, unit=1000.0)
                if cfg.per_day:
                    s["tool_share"] = cfg.tool_ceiling / (1 + cfg.tolerance * st.tools.per_day([tool], True))
                    s["time_of_day"] = 1 / (1 + cfg.tolerance * st.hours.per_day(near, False, daytype))
                else:
                    s["tool_share"] = st.tools.score([tool], cfg.tolerance, cfg.tool_ceiling)
                    s["time_of_day"] = st.hours.score(near, cfg.tolerance)
                if asset:
                    is_new = asset not in st.assets.counts
                    if cfg.per_day:
                        s["asset_share"] = 1 / (1 + cfg.tolerance * st.assets.per_day([asset], True))
                    elif cfg.asset_novelty and is_new:
                        log = st.new_assets
                        nu = (sum(x for _, x in log) + 1) / (len(log) + 2)
                        s["asset_share"] = 1 / (1 + cfg.tolerance * 2 * nu)
                    else:
                        s["asset_share"] = st.assets.score([asset], cfg.tolerance)
                if sum(1 for t in q if t >= ts - 60) > cfg.burst_per_min:
                    s["burst"] = cfg.rule
                if size > cfg.request_limit:
                    s["request_big"] = cfg.rule
                if not sess["init"] and normally_init:
                    s["protocol_skip"] = cfg.protocol_skip
                blind = op in WRITE_OPS and asset and sens >= SENSITIVE and \
                    st.last_read.get(asset, -10**6) < day - READ_MEMORY_DAYS
                if (op in WRITE_OPS and sess["read_sens"] - {asset}) or blind or \
                        (tool == "merge_pull_request" and not sess["review"]):
                    s["sequence"] = cfg.rule
            st.tools.add(tool, day, count_new=warm)
            st.hours.add((daytype, hour), day)
            if asset:
                st.new_assets.append((day, int(asset not in st.assets.counts)))
                while st.new_assets and st.new_assets[0][0] <= day - W:
                    st.new_assets.popleft()
                st.assets.add(asset, day, count_new=warm)
                if op in ("read", "metadata"):
                    st.last_read[asset] = day
                    if sens >= SENSITIVE:
                        sess["read_sens"].add(asset)
            if tool in REVIEW_TOOLS:
                sess["review"] = True
            st.tool_calls += 1
        if not s:
            return 1.0, s
        return multiplier(max(s.values())), s


# ── the 9 simulated organisations ──────────────────────────────────────────────────────────
def run_org(job: tuple[str, str]) -> dict:
    name, cfg_name = job
    eng = BoundedEngine({"with_repeat": WITH_REPEAT, "asset_novelty": ASSET_NOVELTY,
                         "per_day": PER_DAY}.get(cfg_name, DESIGN))
    csv.field_size_limit(10**9)
    M, top, ts_l, ag_l, st_l, lg_l, ep_l, bot_l = [], [], [], [], [], [], [], []
    with gzip.open(HERE / "w2" / f"{name}.csv.gz", "rt") as fh:
        for r in csv.DictReader(fh):
            asset = r["which"] if r["which"] not in ("", "null") else ""
            m, s = eng.score(float(r["ts"]), r["agent"], r["session"], r["method"], r["tool"], asset,
                             int(r["sens"] or 0), r["op"], r["address"], r["client"], float(r["bytes"] or 0))
            M.append(m)
            top.append(DIMS.index(max(s, key=lambda k: s[k])) if s and m > 1 else -1)
            ts_l.append(float(r["ts"]))
            ag_l.append(r["agent"])
            st_l.append(r["strange"])
            lg_l.append(r["legit"])
            ep_l.append(r["episode"])
            bot_l.append("bot" in r["role"])
    M, top = np.array(M, np.float32), np.array(top, np.int8)
    day = (np.array(ts_l) // DAY).astype(int)
    agent, strange, legit, episode = np.array(ag_l), np.array(st_l), np.array(lg_l), np.array(ep_l)
    bot = np.array(bot_l)
    _, ident = np.unique(agent, return_inverse=True)
    _, inv = np.unique(ident.astype(np.int64) * 100000 + day, return_inverse=True)
    nk = inv.max() + 1
    dmax = np.zeros(nk, np.float32)
    np.maximum.at(dmax, inv, M)
    kday, kbot = np.zeros(nk, int), np.zeros(nk, bool)
    kday[inv], kbot[inv] = day, bot
    k_strange = np.zeros(nk, bool)
    np.logical_or.at(k_strange, inv, strange != "")
    k_legit = np.full(nk, "", dtype=object)
    ben = (legit != "") & (strange == "")
    k_legit[inv[ben]] = legit[ben]
    after = kday >= CAL_DAYS
    ordinary_day = after & ~k_strange & (k_legit == "")
    first = np.full(nk, -1)
    seen = np.zeros(nk, bool)
    for i in np.argsort(-M, kind="stable"):
        k = inv[i]
        if not seen[k]:
            seen[k], first[k] = True, top[i]
    hot = ordinary_day & (dmax >= 3)
    causes = Counter(DIMS[c] for c in first[hot] if c >= 0)
    ordinary_calls = (strange == "") & (legit == "")

    def rate(mask):
        return float((dmax[mask] >= 3).mean()) if mask.any() else None

    out = {"range": [float(M.min()), float(M.max())], "nan": int(np.isnan(M).sum()),
           "ordinary_calls_M>1.5": float((M[ordinary_calls] > 1.5).mean()),
           "ordinary_days_M>=2": float((dmax[ordinary_day] >= 2).mean()),
           "ordinary_days_M>=3": rate(ordinary_day),
           "ordinary_days_M>=3_bots": rate(ordinary_day & kbot),
           "ordinary_days_M>=3_people": rate(ordinary_day & ~kbot),
           "ordinary_causes": {k: v / max(1, int(hot.sum())) for k, v in causes.most_common()},
           "legit_days_M>=3": {t: rate(after & (k_legit == t)) for t in set(k_legit[after]) if t}}
    eps: dict[str, list[int]] = {}
    for i in np.flatnonzero(strange != ""):
        eps.setdefault(episode[i], []).append(i)
    per_kind: dict[str, list[float]] = defaultdict(list)
    ep_cds = []
    for ix in map(np.array, eps.values()):
        if day[ix[0]] >= CAL_DAYS:
            per_kind[strange[ix[0]]].append(float(M[ix].max()))
            ep_cds.append((strange[ix[0]], np.unique(inv[ix]), bool((M[ix] > 1).any())))
    out["episode_max_M"] = {k: {"n": len(v), ">=2": float(np.mean(np.array(v) >= 2)),
                                ">=3": float(np.mean(np.array(v) >= 3)), "median": float(np.median(v))}
                            for k, v in per_kind.items()}
    n_eval = max(1, day.max() + 1 - CAL_DAYS)
    for load in (2.0, 4.0):
        al = alerts(dmax - 1, kday, n_eval, load)
        det: dict[str, list[bool]] = defaultdict(list)
        for kind, cds, has in ep_cds:
            det[kind].append(bool(al[cds].any() and has))
        out[f"detect_{load:g}"] = {k: float(np.mean(v)) for k, v in det.items()}
    print(f"done {name} {cfg_name}", flush=True)
    return out


# ── hand-made edge cases ────────────────────────────────────────────────────────────────────
def call(ts, agent="a", session=None, method="tools/call", tool="read", asset="", sens=0, op="read",
         address="10.0.0.1", client="claude-desktop/1.0", size=200.0):
    return dict(ts=ts, agent=agent, session=session or f"{agent}-{int(ts // DAY)}", method=method,
                tool=tool, asset=asset, sens=sens, op=op, address=address, client=client, size=size)


def session(t0, agent="a", sid=None, tools=("read", "list", "search"), n=10, gap=30.0, init=True,
            assets=5, **kw):
    """One session: initialize, then n calls gap seconds apart, cycling through tools and assets."""
    sid = sid or f"{agent}-{t0:.0f}"
    head = {k: v for k, v in kw.items() if k in ("address", "client")}
    out = [call(t0 - 1, agent, sid, "initialize", **head)] if init else []
    for i in range(n):
        out.append(call(t0 + i * gap, agent, sid, tool=tools[i % len(tools)],
                        asset=f"repo{i % assets}" if assets else "", sens=2, **kw))
    return out


def workday(day, agent="a", sessions=4, start_h=9, hours=8, one_session=False, **kw):
    """A working day: short sessions spread over the working hours, or one session all day."""
    if one_session:
        return session(day * DAY + start_h * 3600, agent, f"{agent}-{day}", n=sessions * 10,
                       gap=hours * 3600 / (sessions * 10), **kw)
    return [c for k in range(sessions)
            for c in session(day * DAY + (start_h + k * hours / sessions) * 3600, agent, **kw)]


def history(days=60, **kw):
    return [c for d in range(days) if d % 7 < 5 for c in workday(d, **kw)]


def edge_cases(cfg: Config) -> list[dict]:
    rows = []

    def run(name, expect, warm, test, note=""):
        e = BoundedEngine(cfg)
        try:
            for c in warm:
                e.score(**c)
            res = [e.score(**c) for c in test]
        except ZeroDivisionError:
            rows.append({"case": name, "expect": expect, "max_M": "division by zero", "top_dim": "-",
                         "out_of_range": 1, "note": note})
            return
        ms = [m for m, _ in res]
        worst = max(res, key=lambda x: x[0])
        top = max(worst[1], key=lambda k: worst[1][k]) if worst[1] else "-"
        rows.append({"case": name, "expect": expect, "max_M": round(max(ms), 2), "top_dim": top,
                     "out_of_range": sum(1 for m in ms if not MIN_M <= m <= MAX_M or math.isnan(m)),
                     "note": note})

    base = history()
    t = 63 * DAY
    run("Ordinary day", "≤ 1", base, workday(63))
    run("Night-shift worker, ordinary night", "≤ 1", history(start_h=22), workday(63, start_h=22))
    run("Brand-new agent, first 12 calls", "1, then mild", [], workday(0, sessions=2)[:14])
    run("Desktop client: one session open all day, ordinary", "≤ 1", history(one_session=True),
        workday(63, one_session=True))
    run("Stuck session: usual 5 minutes, this one open 3 hours", "flares", base,
        session(t + 9 * 3600, n=40, gap=270))
    run("New exact IP on every call, same /16 (mobile, NAT, cloud)", "≤ 1",
        [dict(c, address=f"100.64.{i % 256}.{i % 250 + 1}") for i, c in enumerate(base)],
        [dict(c, address=f"100.64.{(i * 7) % 256}.{(i * 3) % 250 + 1}") for i, c in enumerate(workday(63))])
    run("A new /16 network", "flares", base, workday(63, address="203.0.113.5"))
    run("Requests always 0 bytes", "≤ 1, no crash", history(size=0.0), workday(63, size=0.0))
    run("Requests always 0 bytes, then one of 50 bytes", "mild", history(size=0.0),
        session(t + 10 * 3600, n=1, size=50.0))
    run("A 20 KB request (usually 200 B)", "flares", base, session(t + 10 * 3600, n=1, size=20_000))
    run("A 1 GB request", "close to 5, never above", base, session(t + 10 * 3600, n=1, size=1e9))
    run("Travel: same work 8 hours earlier, first day", "flares", base, workday(63, start_h=1))
    travel = [c for d in range(63, 70) if d % 7 < 5 for c in workday(d, start_h=1)]
    run("Travel: same work 8 hours earlier, second day", "lower", base + travel[:44], travel[44:88])
    run("Travel: same work 8 hours earlier, fifth day", "settles", base + travel[:-44], travel[-44:])
    bot = [c for d in range(30) for k in range(24)
           for c in session(d * DAY + k * 3600, "bot", tools=("poll",), n=100, gap=36, assets=0)]
    run("Bot, 100 calls an hour, ordinary", "≤ 1", bot,
        [c for k in range(5) for c in session(30 * DAY + k * 3600, "bot", tools=("poll",), n=100, gap=36,
                                              assets=0)])
    run("Bot, +20%", "≤ 1", bot,
        [c for k in range(5) for c in session(30 * DAY + k * 3600, "bot", tools=("poll",), n=120, gap=30,
                                              assets=0)])
    run("Bot, 5x (500 an hour)", "flares", bot,
        session(30 * DAY, "bot", tools=("poll",), n=500, gap=7.2, assets=0))
    rare = [c for d in range(60) for c in session(d * DAY + 10 * 3600, "rare", n=1)]
    run("Low-volume agent (1 call a day), ordinary call", "≤ 1", rare,
        session(61 * DAY + 10 * 3600, "rare", n=1))
    run("Same low-volume agent back after 120 days", "mild", rare, session(181 * DAY + 10 * 3600, "rare", n=2))
    run("First-time tool (after 60 days of history)", "about x3.6", base,
        session(t + 10 * 3600, tools=("delete_repo",), n=1))
    run("Tool he used once in 60 days", "below x3.6",
        base + session(5 * DAY + 10 * 3600, tools=("rare_tool",), n=1),
        session(t + 10 * 3600, tools=("rare_tool",), n=1))
    run("Single-tool agent uses a second tool", "about x3.6", history(tools=("read",)),
        session(t + 10 * 3600, tools=("read", "write"), n=2))
    tools26 = tuple(f"t{i}" for i in range(26))
    run("Agent using 26 tools evenly, ordinary day", "≤ 1", history(tools=tools26), workday(63, tools=tools26))
    rot = [dict(c, asset=f"ch{i % 300}") for i, c in enumerate(history(sessions=6))]
    run("Bot posting to 300 channels in rotation, ordinary", "≤ 1", rot,
        [dict(c, asset=f"ch{(len(rot) + i) % 300}") for i, c in enumerate(workday(63, sessions=6))])
    run("A never-touched asset", "flares", base,
        [call(t + 10 * 3600 - 1, method="initialize"), call(t + 10 * 3600, asset="new-repo", sens=2)])
    run("Legit pagination: 60 page reads in one minute", "?", base,
        session(t + 11 * 3600, tools=("list",), n=60, gap=1.0), "burst cannot tell pagination from a loop")
    run("Runaway loop: 300 identical calls in 5 minutes", "flares", base,
        session(t + 11 * 3600, tools=("read",), n=300, gap=1.0))
    run("Slow loop: same tool 40 times in 10 minutes", "flares", base,
        session(t + 11 * 3600, tools=("read",), n=40, gap=15.0), "this is what 'same tool in 10 min' caught")
    run("Write to a sensitive asset never read", "flares", base,
        [call(t + 11 * 3600 - 1, method="initialize"),
         call(t + 11 * 3600, tool="update", asset="secrets", sens=5, op="write")])
    run("Tool call without initialize", "about x1.9", base, session(t + 10 * 3600, n=3, init=False))
    run("Stateless HTTP client (never sends initialize)", "≤ 1 ideally", history(init=False),
        workday(63, init=False), "every call looks like a protocol skip")
    run("Same work from a new client program", "flares", base, workday(63, client="python-httpx/0.27"))
    skew = workday(63)
    skew[5]["ts"], skew[6]["ts"] = skew[6]["ts"], skew[5]["ts"]
    run("Two calls arrive out of order", "≤ 1, no crash", base, skew)
    return rows


def main():
    edge = edge_cases(DESIGN)
    print("EDGE CASES (current design)")
    for r in edge:
        print(f"  {r['case']:<58} max M {r['max_M']!s:<6} {r['top_dim']:<15} expect {r['expect']:<22} "
              f"{'OUT OF RANGE' if r['out_of_range'] else ''} {r['note']}")
    jobs = [(n, c) for c in ("design", "with_repeat") for n in NAMES]
    with Pool(3) as pool:
        res = pool.map(run_org, jobs)
    orgs = {f"{n}|{c}": r for (n, c), r in zip(jobs, res)}
    (HERE / "results" / "bounded_stress.json").write_text(json.dumps({"orgs": orgs, "edge": edge},
                                                                     indent=1, default=str))
    print("\nORGANISATIONS (current design)")
    for n in NAMES:
        o = orgs[f"{n}|design"]
        print(f"  {n:<12} M {o['range'][0]:.2f}-{o['range'][1]:.2f} nan {o['nan']} | ordinary calls M>1.5 "
              f"{o['ordinary_calls_M>1.5']:.2%} | ordinary days M>=2 {o['ordinary_days_M>=2']:.1%}, M>=3 "
              f"{o['ordinary_days_M>=3']:.1%} (bots {o['ordinary_days_M>=3_bots']}, people "
              f"{o['ordinary_days_M>=3_people']})")
        print("      causes of ordinary M>=3:", {k: f"{v:.0%}" for k, v in list(o["ordinary_causes"].items())[:5]})
        print("      legit days M>=3:", {k: f"{v:.0%}" for k, v in sorted(o["legit_days_M>=3"].items())})
    for cfg_name in ("design", "with_repeat"):
        kinds: dict[str, list] = defaultdict(list)
        for n in NAMES:
            for k, v in orgs[f"{n}|{cfg_name}"]["episode_max_M"].items():
                kinds[k].append(v)
        print(f"\nSTRANGE EPISODES ({cfg_name}): share with max M >= 2 / >= 3, median max M")
        for k, vs in sorted(kinds.items(), key=lambda kv: -np.mean([v[">=3"] for v in kv[1]])):
            print(f"  {k:<24} {np.mean([v['>=2'] for v in vs]):.0%} / {np.mean([v['>=3'] for v in vs]):.0%}"
                  f"   median {np.median([v['median'] for v in vs]):.2f}")
        for load in ("2", "4"):
            det = [np.mean(list(orgs[f"{n}|{cfg_name}"][f"detect_{load}"].values())) for n in NAMES]
            print(f"  daily list <= {load} a day: " + " ".join(f"{n} {d:.0%}" for n, d in zip(NAMES, det))
                  + f" | mean {np.mean(det):.0%}")


if __name__ == "__main__":
    main()
