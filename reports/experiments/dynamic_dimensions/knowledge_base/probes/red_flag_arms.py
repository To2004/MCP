"""Design-phase probe (development world only): v5 red-flag mechanics arms, one engine pass.

The shipped v4 engine runs once over a simulated organisation. M feeds nothing back into engine
state, so each arm is recomputed per call from the v4 verdict by replacing a few entries:

- habit arms: the unsafe-sequence value under other habit keys (per branch, per source, per
  source and target) and with a down-flow exemption; optional floors;
- org arms: the org discount with established subjects only, a threshold relative to org size,
  "new to the organisation", and no discount for write or static >= 4 tools (tool kind only);
- limit arms: oversized request under the agent-day max-ratio procedure (bots and people apart,
  optional leave-one-identity-out, fallback by operation class).

Every number it prints is from a burnt development world (seeds 7 and 11, the five existing
organisations). None of it is a test result.

    PYTHONHASHSEED=0 uv run python reports/experiments/dynamic_dimensions/knowledge_base/probes/\\
        red_flag_arms.py SEED AGENTS PROFILE OUT.json [pass1|pass2|pass3]

Pass 1 compares habit keys, org-discount hardenings and learned-limit procedures; pass 2 adds the
burst line, explicit floors and the first-access exemption; pass 3 is the recommended default.
"""

from __future__ import annotations

import json
import math
import random
import sys
import time
from collections import Counter, defaultdict, deque
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HERE))

import normal_org_world as W  # noqa: E402

from mcp_security.behaviour import engine as E  # noqa: E402
from mcp_security.behaviour.engine import (  # noqa: E402
    DAY_S,
    BehaviourConfig,
    BehaviourEngine,
    Message,
    multiplier,
)
from mcp_security.behaviour.memory import FirstUses  # noqa: E402
from mcp_security.behaviour.policy import derive_policy  # noqa: E402

ALERT = 3.0
EVAL_FROM = 90
LEARN_DAYS = 30
ALPHA = 0.005
KB = 1_000
TOP_K = 4
ORG_NEW_DAYS = 30
OPS = {t: v[0] for t, v in W.CATALOG.items()}
STATIC = {t: v[1] for t, v in W.CATALOG.items()}
CONTENT = {
    "create_issue",
    "add_issue_comment",
    "create_pull_request_review",
    "create_pull_request",
    "create_release",
    "create_or_update_file",
    "push_files",
}
HABIT_MODES = (
    "none",
    "branch",
    "branch90",
    "branch90est+down5",
    "src",
    "pair",
    "branch+down5",
    "branch+newsrc",
    "branch+newsrc+down5",
    "branch90+down5",
    "v4+down",
    "v4+down5",
    "v4+fa7",
    "v4+down5+fa7",
)
ORG_MODES = ("none", "est", "est+rel2", "est+orgnew", "est+orgnew+nowrite", "oracle+nowrite")
LIMIT_MODES = ("p4_apart", "p4_apart_loo", "p4_pooled", "p1_apart")
#: arm -> (habit mode, floor, org mode, limit mode, floors explicit, burst mode)
_PASS1_HABIT = ("none", "branch", "branch90", "src", "pair", "branch+down5", "branch+newsrc",
                "branch+newsrc+down5", "branch90+down5", "v4+down", "v4+down5")
#: arm -> (habit mode, floor, org mode, limit mode, floors explicit, burst mode)
ARM_SETS = {
    "pass1": {
        "v4": ("v4", None, "v4", "v4", False, "v4"),
        **{f"H {h}": (h, None, "v4", "v4", False, "v4") for h in _PASS1_HABIT},
        "H branch+down5 floor0.7": ("branch+down5", 0.7, "v4", "v4", False, "v4"),
        "H branch+down5 floor0.5": ("branch+down5", 0.5, "v4", "v4", False, "v4"),
        **{f"O {o}": ("v4", None, o, "v4", False, "v4") for o in ORG_MODES},
        **{f"L {lm}": ("v4", None, "v4", lm, False, "v4") for lm in LIMIT_MODES},
        "V5a branch+down5 / est+orgnew+nowrite / p4_apart_loo": (
            "branch+down5", 0.5, "est+orgnew+nowrite", "p4_apart_loo", False, "v4"),
        "V5b v4 habit / est+orgnew+nowrite / p4_apart_loo": (
            "v4", None, "est+orgnew+nowrite", "p4_apart_loo", False, "v4"),
        "V5c branch90+down5 / est+orgnew+nowrite / p4_apart_loo": (
            "branch90+down5", 0.5, "est+orgnew+nowrite", "p4_apart_loo", False, "v4"),
    },
    "pass2": {
        "v4": ("v4", None, "v4", "v4", False, "v4"),
        **{f"H {h}": (h, None, "v4", "v4", False, "v4") for h in (
            "none", "branch", "branch90est+down5", "v4+down5", "v4+fa7", "v4+down5+fa7")},
        **{f"O {o}": ("v4", None, o, "v4", False, "v4") for o in (
            "none", "est", "est+rel2", "est+orgnew", "est+orgnew+nowrite")},
        "L p4_apart": ("v4", None, "v4", "p4_apart", False, "v4"),
        "L p4_apart_loo": ("v4", None, "v4", "p4_apart_loo", False, "v4"),
        "B apart_loo": ("v4", None, "v4", "v4", False, "apart_loo"),
        "F floors explicit": ("v4", None, "v4", "v4", True, "v4"),
        "V5 down5 / est+orgnew+nowrite / p4_apart_loo / burst apart / floors": (
            "v4+down5", 0.5, "est+orgnew+nowrite", "p4_apart_loo", True, "apart_loo"),
        "V5 down5+fa7 / est+orgnew+nowrite / p4_apart_loo / burst apart / floors": (
            "v4+down5+fa7", 0.5, "est+orgnew+nowrite", "p4_apart_loo", True, "apart_loo"),
        "V5 down5 / est+orgnew / p4_apart_loo / burst apart / floors": (
            "v4+down5", 0.5, "est+orgnew", "p4_apart_loo", True, "apart_loo"),
    },
    "pass3": {
        "v4": ("v4", None, "v4", "v4", False, "v4"),
        "V5 default: copy5 / est+orgnew+nowrite / p4_apart_loo / floors": (
            "v4+down5", 0.5, "est+orgnew+nowrite", "p4_apart_loo", True, "v4"),
        "V5 default, pooled lines: copy5 / est+orgnew+nowrite / p4_pooled / floors": (
            "v4+down5", 0.5, "est+orgnew+nowrite", "p4_pooled", True, "v4"),
        "V5 default without copy5: v4 habit / est+orgnew+nowrite / p4_apart_loo / floors": (
            "v4", None, "est+orgnew+nowrite", "p4_apart_loo", True, "v4"),
    },
}
ARMS = ARM_SETS[sys.argv[5] if len(sys.argv) > 5 else "pass3"]


def whole_kb(x: float) -> int:
    return math.ceil(x / KB) * KB


def conformal(vals: list[float], q: float) -> float | None:
    """The split-conformal order statistic: smallest value with exceedance <= 1 - q."""
    vals = sorted(vals)
    k = math.ceil(q * (len(vals) + 1))
    return None if k > len(vals) else vals[k - 1]


def cls_of(tool: str) -> tuple[str, bool]:
    return OPS.get(tool, "write"), tool in CONTENT


def p4_limits(days: list, ref_q=0.99, min_ref=100, loo=False):
    """Agent-day max-ratio procedure: per-tool reference at ref_q, one shared multiple k set
    so the agent-day's largest size/reference ratio exceeds k on <= ALPHA of learning days."""
    per_tool = defaultdict(list)
    for _, tools in days:
        for t, s in tools.items():
            per_tool[t].append(s)
    ref = {}
    if not any(len(v) >= min_ref for v in per_tool.values()):
        min_ref = 20  # tiny smoke-test worlds only
    for t, v in per_tool.items():
        if len(v) >= min_ref:
            v = sorted(v)
            ref[t] = v[min(len(v) - 1, math.ceil(ref_q * (len(v) + 1)) - 1)]
    by = defaultdict(list)
    for t, r in ref.items():
        by[cls_of(t)].append(r)
    cmed = {c: sorted(v)[len(v) // 2] for c, v in by.items()}
    top = max(ref.values())

    def reff(t):
        return ref.get(t) or cmed.get(cls_of(t)) or top

    ratios = [(a, max(s / reff(t) for t, s in tools.items())) for a, tools in days]
    if loo:
        ids = {a for a, _ in ratios}
        loo_k = [conformal([r for a2, r in ratios if a2 != a], 1 - ALPHA) for a in ids]
        k = min((x for x in loo_k if x is not None), default=max(r for _, r in ratios))
    else:
        k = conformal([r for _, r in ratios], 1 - ALPHA) or max(r for _, r in ratios)
    lim = {t: whole_kb(k * r) for t, r in ref.items()}
    return k, lim, (lambda t: whole_kb(k * reff(t)))


def p1_limits(days: list):
    """Per-tool conformal 99.5% quantile (needs >= 199 agent-days), fallback class max."""
    per_tool = defaultdict(list)
    for _, tools in days:
        for t, s in tools.items():
            per_tool[t].append(s)
    lim = {t: whole_kb(c) for t, v in per_tool.items() if (c := conformal(v, 1 - ALPHA))}
    by = defaultdict(list)
    for t, v in lim.items():
        by[cls_of(t)].append(v)
    cmax = {c: max(v) for c, v in by.items()}
    top = max(lim.values())
    return None, lim, (lambda t: lim.get(t) or cmax.get(cls_of(t)) or top)


class FirstUsesX(FirstUses):
    """v4's FirstUses, plus a record of whether each first user was established then."""

    def __init__(self, eng: Probe, seconds: float) -> None:
        super().__init__(seconds)
        self.eng = eng
        self.ext: dict[tuple, deque] = defaultdict(deque)

    def add(self, key, ts, agent):
        super().add(key, ts, agent)
        self.ext[key].append((ts, agent, self.eng.established(agent, int(ts // DAY_S))))

    def distinct_established(self, key, ts, agent) -> int:
        uses = self.ext.get(key)
        if not uses:
            return 0
        while uses and uses[0][0] < ts - self.seconds:
            uses.popleft()
        return len({a for t, a, est in uses if t < ts and a != agent and est})


class Probe(BehaviourEngine):
    def __init__(self, config, limits, isbot):
        super().__init__(config)
        self.first_uses = FirstUsesX(self, config.org_discount_days * DAY_S)
        self.limits = limits  # mode -> {"bot"|"person": (lim, fb)}
        self.isbot = isbot
        self.sens_of: dict = {}
        self.keys = {k: defaultdict(deque) for k in ("branch", "src", "pair", "branch_est")}
        self.org_first: dict = {}
        self.org_last: dict = {}
        self.last_active: dict = {}
        self.firings: list = []
        self.cur_gray = ""
        self.first_access: dict = {}  # (agent, asset) -> day the first-access floor fired
        self.burst_days: dict = defaultdict(deque)  # agent -> days the arm's burst line fired

    # ── helpers ──
    def established(self, agent, today):
        st = self.agents.get(agent)
        return (
            st is not None
            and st.tool_calls >= self.config.warmup_calls
            and today - st.first_day >= self.config.onboarding_days
        )

    def org_new(self, kind, value, today):
        first = self.org_first.get((kind, value))
        return first is None or first >= today - ORG_NEW_DAYS

    def _note_org(self, m, today):
        for kv in (
            ("tool", m.tool),
            ("asset", m.asset),
            ("network", E.network_of(m.address, self.config)),
            ("client", E.client_family(m.client)),
        ):
            if kv[1] is None or (kv[0] == "tool" and m.method != E.CALL_METHOD):
                continue
            last = self.org_last.get(kv)
            if last is None or last < today - self.config.history_days:
                self.org_first[kv] = today
            self.org_last[kv] = today

    # ── one message ──
    def observe(self, m: Message):
        self.cur_m = m
        self.cur_seq = None
        self.cur_habit = None
        self.cur_org = []
        if m.asset and m.sensitivity is not None:
            self.sens_of[m.asset] = m.sensitivity
        v = super().observe(m)
        today = int(m.ts // DAY_S)
        if m.method == E.CALL_METHOD and m.asset and m.agent in self.agents:
            if self._first_look(self.agents[m.agent], m) is not None:
                self.first_access[(m.agent, m.asset)] = today
        self._note_org(m, today)
        self.last_active[m.agent] = today
        return v

    def _problematic_sequence(self, st, session, m, tool, today):
        cfg = self.config
        needed = cfg.requires_before.get(tool)
        if needed and not (session and session.tools & needed):
            self.cur_seq = dict(branch="unrev", srcs=[], ss=0, dst=m.asset, ds=m.sensitivity or 0)
            return True
        if m.operation != E.WRITE or not m.asset:
            return False
        if session and session.read_sensitive - {m.asset}:
            srcs = sorted(session.read_sensitive - {m.asset})
            self.cur_seq = dict(
                branch="copy", srcs=srcs, ss=max(self.sens_of.get(a, 0) for a in srcs),
                dst=m.asset, ds=m.sensitivity or 0,
            )
            return True
        sensitive = (m.sensitivity or 0) >= cfg.sensitive_level
        last = st.last_read.get(m.asset)
        if sensitive and (last is None or last < today - cfg.read_memory_days):
            self.cur_seq = dict(branch="blind", srcs=[], ss=0, dst=m.asset, ds=m.sensitivity or 0)
            return True
        return False

    def _habit(self, st, rule, value, today):
        out = super()._habit(st, rule, value, today)
        if rule != E.SEQUENCE or self.cur_seq is None:
            return out
        info = self.cur_seq
        b, agent, tool = info["branch"], self.cur_m.agent, self.cur_m.tool
        hist = self.config.history_days

        def prior_of(kt, key):
            days = self.keys[kt][key]
            while days and days[0] <= today - hist:
                days.popleft()
            return len(days) - int(bool(days) and days[-1] == today)

        if b == "copy":
            src_keys = [(agent, b, a) for a in info["srcs"]]
            pair_keys = [(agent, b, a, info["dst"]) for a in info["srcs"]]
        else:
            one = info["dst"] if b == "blind" else tool
            src_keys = pair_keys = [(agent, b, one)]
        pb = prior_of("branch", (agent, b))
        pbe = prior_of("branch_est", (agent, b))
        if self.established(agent, today):  # habit days count only once he is established
            days = self.keys["branch_est"][(agent, b)]
            if not days or days[-1] != today:
                days.append(today)
        ps = min(prior_of("src", k) for k in src_keys)  # the least habitual source governs
        pp = min(prior_of("pair", k) for k in pair_keys)
        for kt, keys in (("branch", [(agent, b)]), ("src", src_keys), ("pair", pair_keys)):
            for key in keys:
                days = self.keys[kt][key]
                if not days or days[-1] != today:
                    days.append(today)
        active = st.tools.active_days(today=today)
        tol = self.config.tolerance

        def val(p, denom):
            return value / (1 + tol * p / (denom + 1))

        down = b == "copy" and info["ss"] > info["ds"]
        down5 = b == "copy" and info["ss"] >= 5 and info["ds"] < 5
        newsrc = b == "copy" and ps == 0
        fa7 = b == "copy" and any(
            self.first_access.get((agent, a_), -10**9) >= today - self.config.read_memory_days
            for a_ in info["srcs"]
        )
        vb, vb90 = val(pb, active), val(pb, max(active, hist))
        self.cur_habit = {
            "none": value,
            "branch": vb,
            "branch90": vb90,
            "src": val(ps, active),
            "pair": val(pp, active),
            "branch+down5": value if down5 else vb,
            "branch+newsrc": value if newsrc else vb,
            "branch+newsrc+down5": value if (newsrc or down5) else vb,
            "branch90+down5": value if down5 else vb90,
            "branch90est+down5": value if down5 else val(pbe, max(active, hist)),
            "v4+down": value if down else out,
            "v4+down5": value if down5 else out,
            "v4+fa7": value if fa7 else out,
            "v4+down5+fa7": value if (down5 or fa7) else out,
        }
        self.firings.append(
            (agent, today - W.BASE_DAY, b, info["ss"], info["ds"], round(out, 4), pb, ps, pp,
             self.cur_gray.split(":")[0], int(self.isbot[agent]), int(newsrc), active)
        )
        return out

    def _org_wide(self, kind, value, m):
        dec = super()._org_wide(kind, value, m)
        cfg, today = self.config, int(m.ts // DAY_S)
        st = self.agents[m.agent]
        counts, ceiling, dim = {
            "tool": (st.tools, cfg.tool_ceiling, E.TOOL),
            "asset": (st.assets, 1.0, E.ASSET),
            "network": (st.network_counts, cfg.origin_ceiling, E.NETWORK),
            "client": (st.client_counts, cfg.origin_ceiling, E.CLIENT),
        }[kind]
        raw = ceiling / (1 + cfg.tolerance * counts.per_day([value], True, today=today))
        est = self.first_uses.distinct_established((kind, value), m.ts, m.agent)
        active_est = sum(
            1 for a, d in self.last_active.items() if d >= today - 7 and self.established(a, today)
        )
        need_rel = max(cfg.org_discount_agents, math.ceil(0.02 * active_est))
        risky_tool = kind == "tool" and (OPS.get(value) == "write" or STATIC.get(value, 0) >= 4)
        orgnew = self.org_new(kind, value, today)
        oracle = _oracle_event(kind, value, today - W.BASE_DAY)
        n = cfg.org_discount_agents
        decs = {
            "none": False,
            "est": est >= n,
            "est+rel2": est >= need_rel,
            "est+orgnew": est >= n and orgnew,
            "est+orgnew+nowrite": est >= n and orgnew and not risky_tool,
            "oracle+nowrite": est >= n and oracle and not risky_tool,
        }
        self.cur_org.append((dim, raw, dec, decs))
        return dec


VPN_NET = f"{W.VPN_NEW[0]}.{W.VPN_NEW[1]}.0.0/16"


def _oracle_event(kind, value, d):
    if kind == "tool":
        return value in W.NEW_TOOLS and W.ROLLOUT_DAY <= d < W.ROLLOUT_DAY + 30
    if kind == "asset":
        return str(value).startswith("platform/") and W.MIGRATION_DAY <= d < W.MIGRATION_DAY + 30
    if kind == "network":
        return value == VPN_NET and W.VPN_CHANGE_DAY <= d < W.VPN_CHANGE_DAY + 30
    return False


def top_two(scores: dict):
    best, bd, second = -1.0, None, 0.0
    for d, s in scores.items():
        if s > best:
            second, best, bd = max(second, best), s, d
        elif s > second:
            second = s
    return best, bd, max(second, 0.0)


def topk_prob(keys, day, k):
    p = [0.0] * len(keys)
    by_day = defaultdict(list)
    for i, d in enumerate(day):
        by_day[d].append(i)
    for ix in by_day.values():
        groups = defaultdict(list)
        for i in ix:
            groups[keys[i]].append(i)
        above = 0
        for key in sorted(groups, reverse=True):
            mem = groups[key]
            if above >= k:
                break
            share = 1.0 if above + len(mem) <= k else (k - above) / len(mem)
            for i in mem:
                p[i] = share
            above += len(mem)
    return p


def main() -> None:
    seed, n, prof, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
    t0 = time.time()
    world, roles, _ = W.build_world(n, seed, W.PROFILES[prof])
    isbot = {a: "bot" in roles[a] for a in world}

    def msg(a, r):
        return Message(r[0], a, r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9])

    cut = (W.BASE_DAY + LEARN_DAYS) * DAY_S
    base = BehaviourConfig(design="v3", requires_before={"merge_pull_request": W.REVIEW_TOOLS})
    policy = replace(
        derive_policy([msg(a, r) for a, rows in world.items() for r in rows if r[0] < cut], base),
        design="v4",
    )
    learn = {}
    for a, rows in world.items():
        for r in rows:
            if r[0] < cut and r[1] == "tools/call":
                d = learn.setdefault((a, int(r[0] // DAY_S)), {})
                d[r[3]] = max(d.get(r[3], 0), r[9])
    days_of = {
        "all": [(k[0], t) for k, t in learn.items()],
        "bot": [(k[0], t) for k, t in learn.items() if isbot[k[0]]],
        "person": [(k[0], t) for k, t in learn.items() if not isbot[k[0]]],
    }
    limits, kvals = {}, {}
    for mode in LIMIT_MODES:
        if mode == "p1_apart":
            limits[mode] = {g: p1_limits(days_of[g])[1:] for g in ("bot", "person")}
            continue
        loo = mode.endswith("loo")
        if mode == "p4_pooled":
            k, lim, fb = p4_limits(days_of["all"], loo=loo)
            limits[mode] = {"bot": (lim, fb), "person": (lim, fb)}
            kvals[mode] = round(k, 3)
        else:
            res = {g: p4_limits(days_of[g], loo=loo) for g in ("bot", "person")}
            limits[mode] = {g: r[1:] for g, r in res.items()}
            kvals[mode] = {g: round(r[0], 3) for g, r in res.items()}
    busiest = {}
    for a, rows in world.items():
        q = deque()
        for r in rows:
            if r[0] >= cut or r[1] != "tools/call":
                continue
            q.append(r[0])
            while q and q[0] <= r[0] - 60:
                q.popleft()
            k_ = (a, int(r[0] // DAY_S))
            busiest[k_] = max(busiest.get(k_, 0), len(q))
    burst_lines = {}
    for g, is_b in (("bot", True), ("person", False)):
        pts = [(k_[0], v_) for k_, v_ in busiest.items() if isbot[k_[0]] == is_b]
        ids = {a_ for a_, _ in pts}
        loo = [conformal([v_ for a2, v_ in pts if a2 != a_], 1 - ALPHA) for a_ in ids]
        burst_lines[g] = min((x for x in loo if x is not None), default=max(v_ for _, v_ in pts))
    kvals["burst_lines"] = burst_lines
    print(f"[{time.time() - t0:.0f}s] world and limits ready: k={kvals}", flush=True)

    eng = Probe(policy, limits, isbot)
    stream = sorted((r[0], a, i) for a, rows in world.items() for i, r in enumerate(rows))
    per_arm = {arm: {} for arm in ARMS}  # (aid, d) -> [M, top, s2]
    gray_max = {arm: defaultdict(float) for arm in ARMS}
    flag_days = defaultdict(set)  # flag -> agent-days it was raised (v4, before discount)
    labels = {}
    for _, a, i in stream:
        r = world[a][i]
        eng.cur_gray = r[12] or ""
        m = msg(a, r)
        v = eng.observe(m)
        today_abs = int(r[0] // DAY_S)
        d = today_abs - W.BASE_DAY
        if d < EVAL_FROM:
            if m.method == E.CALL_METHOD and burst_lines is not None:
                st_ = eng.agents[a]  # keep the arm's burst habit days in the history too
                if sum(1 for t in st_.recent if t > m.ts - E.MINUTE_S) > burst_lines[
                        "bot" if isbot[a] else "person"]:
                    days = eng.burst_days[a]
                    if not days or days[-1] != today_abs:
                        days.append(today_abs)
            continue
        key = (a, d)
        lab = labels.setdefault(key, [set(), set()])
        if r[11]:
            lab[0].update(r[11].split("|"))
        if r[12]:
            lab[1].add(r[12])
        for f in (E.BURST, E.MANY_ASSETS, E.REQUEST_TOO_BIG, E.SEQUENCE, E.PROTOCOL_SKIP):
            if f in v.scores:
                flag_days[f].add(key)
        base_scores = v.scores
        group = "bot" if isbot[a] else "person"
        v4_big = None
        if m.method == E.CALL_METHOD:
            lim = policy.request_limit_by_tool.get(m.tool, policy.request_limit_bytes)
            v4_big = m.size > lim
        b_top = None
        burst_arm = None
        if m.method == E.CALL_METHOD:  # the arm's burst line, its own habit days
            st_ = eng.agents[a]
            n1 = sum(1 for t in st_.recent if t > m.ts - E.MINUTE_S)
            if n1 > burst_lines[group]:
                days = eng.burst_days[a]
                while days and days[0] <= today_abs - policy.history_days:
                    days.popleft()
                k_ = len(days) - int(bool(days) and days[-1] == today_abs)
                burst_arm = policy.rule_score / (
                    1 + policy.tolerance * k_ / (st_.tools.active_days(today=today_abs) + 1))
                if not days or days[-1] != today_abs:
                    days.append(today_abs)
        for arm, spec in ARMS.items():
            hm, floor, om, lm, fx, bm = spec
            changed = False
            sc = base_scores
            if hm != "v4" and eng.cur_habit is not None and E.SEQUENCE in sc:
                val = eng.cur_habit[hm]
                if floor is not None:
                    val = max(floor, val)
                if val != sc[E.SEQUENCE]:
                    sc = dict(sc) if not changed else sc
                    changed = True
                    sc[E.SEQUENCE] = val
            if om != "v4" and eng.cur_org:
                for dim, raw, dec, decs in eng.cur_org:
                    if decs[om] == dec:
                        continue
                    new = min(raw, 0.5) if decs[om] else raw
                    if dim == E.ASSET:
                        look = eng._first_look(eng.agents[a], m)
                        if look is not None:
                            new = max(new, look)
                    if not changed:
                        sc, changed = dict(sc), True
                    sc[dim] = new
            if bm != "v4" and m.method == E.CALL_METHOD:
                cur = sc.get(E.BURST)
                if burst_arm != cur:
                    if not changed:
                        sc, changed = dict(sc), True
                    if burst_arm is None:
                        sc.pop(E.BURST, None)
                    else:
                        sc[E.BURST] = max(floor, burst_arm) if floor is not None else burst_arm
            if fx and m.method == E.CALL_METHOD and m.asset:
                look = eng._first_look(eng.agents[a], m)
                if look is not None:  # the first-access floor as its own entry
                    if not changed:
                        sc, changed = dict(sc), True
                    ent = [x for x in eng.cur_org if x[0] == E.ASSET]
                    if ent:
                        _, raw, dec, decs = ent[0]
                        disc = decs[om] if om != "v4" else dec
                        sc[E.ASSET] = min(raw, 0.5) if disc else raw
                    else:
                        sc.pop(E.ASSET, None)
                    sc[E.SENSITIVE_FIRST_LOOK] = look
            if lm != "v4" and v4_big is not None:
                lim, fb = limits[lm][group]
                big = m.size > lim.get(m.tool, fb(m.tool))
                if big != v4_big:
                    if not changed:
                        sc, changed = dict(sc), True
                    if big:
                        sc[E.REQUEST_TOO_BIG] = policy.rule_score
                    else:
                        sc.pop(E.REQUEST_TOO_BIG, None)
            if changed:
                s1, top, s2 = top_two(sc) if sc else (None, None, 0.0)
                M = multiplier(s1) if sc else 1.0
            else:
                if b_top is None:
                    b_top = top_two(base_scores) if base_scores else (None, None, 0.0)
                M, top, s2 = v.multiplier, v.strongest, b_top[2]
            rec = per_arm[arm].get(key)
            if rec is None or M > rec[0]:
                per_arm[arm][key] = [M, top, s2]
            if r[12] and r[1] == "tools/call":
                g = gray_max[arm]
                g[r[12]] = max(g[r[12]], M)
    print(f"[{time.time() - t0:.0f}s] scored", flush=True)

    keys = list(labels)
    cat = {k: "gray" if labels[k][1] else "change" if labels[k][0] else "ordinary" for k in keys}
    ordinary = [k for k in keys if cat[k] == "ordinary"]
    result = {
        "world": dict(seed=seed, agents=n, profile=prof, label="development world"),
        "learned": dict(
            burst=policy.burst_per_minute,
            sweep=policy.many_assets_per_hour,
            by_tool=policy.request_limit_by_tool,
            fallback=policy.request_limit_bytes,
            k=kvals,
            p4_apart_loo_person={t: limits["p4_apart_loo"]["person"][0].get(t) for t in CONTENT},
        ),
        "flag_raise_rate_ordinary_v4": {
            f: round(len(s & set(ordinary)) / len(ordinary), 5) for f, s in flag_days.items()
        },
        "n_ordinary": len(ordinary),
        "arms": {},
    }
    episodes = defaultdict(list)
    for k in keys:
        for ep in labels[k][1]:
            episodes[ep].append(k)
    for arm in ARMS:
        rec = per_arm[arm]
        M = {k: rec.get(k, [1.0, None, 0.0])[0] for k in keys}
        hot = {k for k in keys if M[k] >= ALERT}
        people = [k for k in ordinary if not isbot[k[0]]]
        bots = [k for k in ordinary if isbot[k[0]]]
        causes = Counter(rec[k][1] for k in ordinary if k in hot)
        tags = defaultdict(lambda: [0, 0])
        for k in keys:
            if cat[k] == "change":
                for t in labels[k][0]:
                    tags[t][0] += 1
                    tags[t][1] += k in hot
        kinds = defaultdict(lambda: [0, 0])
        for ep, mx in gray_max[arm].items():
            kinds[ep.split(":")[0]][0] += 1
            kinds[ep.split(":")[0]][1] += mx >= ALERT
        rk = [(round(rec.get(k, [1.0])[0], 9), round(rec.get(k, [1, None, 0.0])[2], 9))
              for k in keys]
        p = topk_prob(rk, [k[1] for k in keys], TOP_K)
        idx = {k: i for i, k in enumerate(keys)}
        on_list = defaultdict(list)
        for ep, ks in episodes.items():
            on_list[ep.split(":")[0]].append(1 - math.prod(1 - p[idx[k]] for k in ks))
        all_list = [x for v in on_list.values() for x in v]
        result["arms"][arm] = {
            "ordinary_x3": round(len(hot & set(ordinary)) / len(ordinary), 5),
            "ordinary_x3_people": round(sum(k in hot for k in people) / max(1, len(people)), 5),
            "ordinary_x3_bots": round(sum(k in hot for k in bots) / max(1, len(bots)), 5),
            "ordinary_M_ge_1.9": round(sum(M[k] >= 1.9 for k in ordinary) / len(ordinary), 5),
            "ordinary_x3_causes": causes.most_common(6),
            "changes_x3": {t: f"{h}/{n_}" for t, (n_, h) in sorted(tags.items())},
            "gray_caught_x3": {t: f"{h}/{n_}" for t, (n_, h) in sorted(kinds.items())},
            "gray_caught_x3_all": round(
                sum(h for _, h in kinds.values()) / max(1, sum(n_ for n_, _ in kinds.values())), 4
            ),
            "gray_on_list_top4": round(sum(all_list) / max(1, len(all_list)), 4),
            "cross_copy_on_list_top4": round(
                sum(on_list["cross_copy"]) / max(1, len(on_list["cross_copy"])), 4
            ),
        }
    fir_ord = [f for f in eng.firings if f[1] >= EVAL_FROM and cat.get((f[0], f[1])) == "ordinary"]
    by = Counter()
    for f in fir_ord:
        flow = "down" if f[3] > f[4] else "level" if f[3] == f[4] else "up"
        by[(f[2], flow if f[2] == "copy" else "-", f[3] if f[2] == "copy" else "-")] += 1
    days_by = defaultdict(set)
    for f in fir_ord:
        flow = "down" if f[3] > f[4] else "level" if f[3] == f[4] else "up"
        days_by[(f[2], flow if f[2] == "copy" else "-")].add((f[0], f[1]))
    result["sequence_firings_ordinary"] = {
        "calls_by_branch_flow_srcsens": {str(k): v for k, v in by.most_common()},
        "agent_days_by_branch_flow": {
            str(k): round(len(v) / len(ordinary), 5) for k, v in days_by.items()
        },
    }
    copy_ord = [f for f in fir_ord if f[2] == "copy"]
    result["sequence_firings_ordinary"]["copy_calls_newsrc_share"] = round(
        sum(f[11] for f in copy_ord) / max(1, len(copy_ord)), 4)
    result["sequence_firings_ordinary"]["copy_calls_down5_share"] = round(
        sum(f[3] >= 5 and f[4] < 5 for f in copy_ord) / max(1, len(copy_ord)), 4)
    nd = defaultdict(set)
    for f in fir_ord:
        if f[2] == "copy" and f[11]:
            nd["newsrc"].add((f[0], f[1]))
        if f[2] == "copy" and f[3] >= 5 and f[4] < 5:
            nd["down5"].add((f[0], f[1]))
    result["sequence_firings_ordinary"]["agent_days_newsrc"] = round(len(nd["newsrc"]) / len(ordinary), 5)
    result["sequence_firings_ordinary"]["agent_days_down5"] = round(len(nd["down5"]) / len(ordinary), 5)
    result["cross_copy_firings"] = [f for f in eng.firings if f[9] == "cross_copy"]
    out.write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    print(f"[{time.time() - t0:.0f}s] wrote {out}", flush=True)


if __name__ == "__main__":
    random.seed(0)
    main()
