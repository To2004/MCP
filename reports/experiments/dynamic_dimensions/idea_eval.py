"""Two new ideas on top of the e formula (FORMULA.md), tested on the 9 simulated organisations.

Base (FORMULA.md): per call, each family's excess surprise X = max over its dimensions of
max(0, u - B); per agent-day, each family keeps its strongest call; day score = sum of families.

Idea A, crowd ("one agent, or everyone?"). When several agents were clearly above normal
(X >= CROWD_MIN_X) on the same thing, it is an organisation change, not one agent misbehaving. The
daily check runs at the end of the day, so it counts c = other such agents from the window start to
the end of that day:
    Path: the same step (previous tool -> tool), window 7 days
    Pace: the same tool in the same clock hour
    fold    (the proposal) c + 1 >= ORG_NOTICE_AGENTS: the thing becomes one organisation notice
            and stops counting for each agent (X = 0)
    graded  (tried first)  X / (1 + c / CROWD_HALF)
(Place needs the network and client values, which the score files do not keep: scenario test only.)

Idea B, settling ("changed, or misbehaving?"). A step this agent made on at least SETTLE_DAYS
different days of the last 7 is a new habit, not a surprise: its Path excess is 0.

Also tried and reported: persistence (yesterday's balance fades into today, rho = 0.5), and a
floor on the daily check (never flag a day below FLOOR bits, whatever the budget).
Alerts are also split by the legitimate change running on that agent-day (new hire, role change,
team transfer, client upgrade, network move, vacation return).

Run:  python idea_eval.py
"""
from __future__ import annotations

import json
from multiprocessing import Pool

import numpy as np

from family_formula import CAL_DAYS, HERE, NAMES, SETS, alerts, load_org, signals

FAMILIES = SETS["core4"]
DIMS = [c for v in FAMILIES.values() for c in v]
DAY = 86400.0
CROWD_HALF, ORG_NOTICE_AGENTS, CROWD_MIN_X = 3.0, 5, 3.0
FLOOR = 4.0
PATH_WINDOW = 7 * DAY
SETTLE_DAYS, SETTLE_WINDOW = 3, 7
RHO = 0.5
LOADS = (2.0, 4.0)
VARIANTS = ("base", "graded", "fold", "settle", "fold+settle", "persist")


def previous_tool(session: np.ndarray, ts: np.ndarray, tool: np.ndarray) -> np.ndarray:
    """The previous tool call in the same session ('<start>' for the first)."""
    order = np.lexsort((ts, session))
    prev = np.full(len(tool), "<start>", dtype=object)
    s, t = session[order], tool[order]
    same = np.r_[False, s[1:] == s[:-1]]
    prev[order[same]] = t[np.flatnonzero(same) - 1]
    return prev.astype(str)


def crowd_to_day_end(keys: np.ndarray, agent: np.ndarray, ts: np.ndarray, active: np.ndarray,
                     window: float) -> np.ndarray:
    """For each active call: distinct OTHER active agents on the same key, ts-window .. day end."""
    c = np.zeros(len(keys), np.float32)
    idx = np.flatnonzero(active)
    order = idx[np.lexsort((ts[idx], keys[idx]))]
    k = keys[order]
    bounds = np.flatnonzero(np.r_[True, k[1:] != k[:-1], True])
    for lo, hi in zip(bounds[:-1], bounds[1:]):
        rows = order[lo:hi]
        if len(rows) < 2:
            continue
        t, a = ts[rows], agent[rows]
        end = (t // DAY + 1) * DAY
        inside: dict[str, int] = {}
        left = right = 0
        for j in range(len(rows)):                       # both window edges only move forward
            while right < len(rows) and t[right] < end[j]:
                inside[a[right]] = inside.get(a[right], 0) + 1
                right += 1
            while t[left] < t[j] - window:
                inside[a[left]] -= 1
                if not inside[a[left]]:
                    del inside[a[left]]
                left += 1
            c[rows[j]] = len(inside) - (a[j] in inside)
    return c


def settled(agent: np.ndarray, key: np.ndarray, day: np.ndarray, active: np.ndarray) -> np.ndarray:
    """For active calls: did this agent make this step on >= SETTLE_DAYS of the previous 7 days?"""
    out = np.zeros(len(key), bool)
    ak = np.char.add(np.char.add(agent, "|"), key)
    pairs = np.unique(np.char.add(np.char.add(ak, "#"), day.astype(str)))
    days_of: dict[str, list[int]] = {}
    for p in pairs:
        a, d = p.rsplit("#", 1)
        days_of.setdefault(a, []).append(int(d))
    days_of = {a: np.sort(v) for a, v in days_of.items()}
    for i in np.flatnonzero(active):
        ds = days_of[ak[i]]
        n = np.searchsorted(ds, day[i], "left") - np.searchsorted(ds, day[i] - SETTLE_WINDOW, "left")
        out[i] = n >= SETTLE_DAYS
    return out


def evaluate(name: str) -> dict:
    z, cols, X = load_org(name)
    jj = [cols.index(c) for c in DIMS]
    ts = z["ts"].astype(float)
    day = (ts // DAY).astype(int)
    sig = signals(X[:, jj], day)
    exc, event = sig["exc"], sig["cal"] > 0
    agent, tool = z["agent"].astype(str), z["tool"].astype(str)
    strange, legit = z["strange"].astype(str), z["legit"].astype(str)
    fam = {f: exc[:, [DIMS.index(c) for c in ds]].max(1) for f, ds in FAMILIES.items()}
    prev = previous_tool(z["session"].astype(str), ts, tool)
    path_key = np.char.add(np.char.add(prev, ">"), tool)
    pace_key = np.char.add(np.char.add(tool, "@"), (ts // 3600).astype(int).astype(str))
    strong = {f: fam[f] >= CROWD_MIN_X for f in ("path", "pace")}
    crowd = {"path": crowd_to_day_end(path_key, agent, ts, strong["path"], PATH_WINDOW),
             "pace": crowd_to_day_end(pace_key, agent, ts, strong["pace"], 3600.0)}
    notice_days = set()
    for f, key in (("path", path_key), ("pace", pace_key)):
        for i in np.flatnonzero(strong[f] & (crowd[f] + 1 >= ORG_NOTICE_AGENTS)):
            notice_days.add((f, key[i], int(day[i])))
    settle = settled(agent, path_key, day, fam["path"] > 0)
    keys = np.char.add(np.char.add(agent, "|"), day.astype(str))
    _, inv = np.unique(keys, return_inverse=True)
    nk = inv.max() + 1
    kday, kagent = np.zeros(nk, int), np.empty(nk, dtype=object)
    kday[inv], kagent[inv] = day, agent
    n_eval_days = max(1, day.max() + 1 - CAL_DAYS)
    k_strange = np.zeros(nk, bool)
    np.logical_or.at(k_strange, inv, strange != "")
    k_legit = np.full(nk, "", dtype=object)
    ben = (legit != "") & (strange == "")
    k_legit[inv[ben]] = legit[ben]
    episode = z["episode"].astype(str)
    eps: dict[str, list[int]] = {}
    for i in np.flatnonzero(strange != ""):
        eps.setdefault(episode[i], []).append(i)
    ep = [(np.unique(inv[ix]), strange[ix[0]], day[ix[0]] >= CAL_DAYS, event[ix].any())
          for ix in map(np.array, eps.values())]
    order = np.lexsort((kday, kagent.astype(str)))

    def day_score(crowd_mode: str, use_settle: bool) -> np.ndarray:
        total = np.zeros(nk, np.float32)
        for f, x in fam.items():
            if use_settle and f == "path":
                x = np.where(settle, 0.0, x)
            if crowd_mode == "fold" and f in crowd:
                x = np.where(strong[f] & (crowd[f] + 1 >= ORG_NOTICE_AGENTS), 0.0, x)
            if crowd_mode == "graded" and f in crowd:
                x = np.where(strong[f], x / (1 + crowd[f] / CROWD_HALF), x)
            m = np.zeros(nk, np.float32)
            np.maximum.at(m, inv, x)
            total += m
        return total

    def persist(score: np.ndarray) -> np.ndarray:
        out = score.copy()
        for a, b in zip(order[:-1], order[1:]):
            if kagent[a] == kagent[b]:
                out[b] = score[b] + RHO ** (kday[b] - kday[a]) * out[a]
        return out

    scores = {"base": day_score("", False), "graded": day_score("graded", False),
              "fold": day_score("fold", False), "settle": day_score("", True),
              "fold+settle": day_score("fold", True)}
    scores["persist"] = persist(scores["base"])
    out = {"notices_per_day": len({(f, k, d) for f, k, d in notice_days if d >= CAL_DAYS})
           / n_eval_days,
           "settled_share_of_path_events": float(settle[fam["path"] > 0].mean()),
           "crowd_share_of_events": {f: float((c[strong[f]] > 0).mean()) for f, c in crowd.items()}}
    runs = [(v, s, 0.0) for v, s in scores.items()]
    runs += [(v + "+floor", scores[v], FLOOR) for v in ("base", "fold+settle")]
    for v, s, floor in runs:
        for load in LOADS:
            al = alerts(s, kday, n_eval_days, load, False) & (s >= floor)
            per: dict[str, list[bool]] = {}
            for cds, kind, after, has_event in ep:
                if after:
                    per.setdefault(kind, []).append(bool(al[cds].any() and has_event))
            ev_al = al & (kday >= CAL_DAYS)
            tags, counts = np.unique(k_legit[ev_al].astype(str), return_counts=True)
            out[f"{v}|{load:g}"] = {
                "per_kind": {k: float(np.mean(x)) for k, x in per.items()},
                "alerts": int(ev_al.sum()), "alerts_per_day": float(ev_al.sum() / n_eval_days),
                "legit_alerts": {t: int(n) for t, n in zip(tags, counts) if t}}
    print(f"done {name}", flush=True)
    return out


def main():
    with Pool(3) as pool:
        res = dict(zip(NAMES, pool.map(evaluate, NAMES)))
    (HERE / "results" / "idea_eval.json").write_text(json.dumps(res, indent=1))
    for v in VARIANTS + ("base+floor", "fold+settle+floor"):
        for load in LOADS:
            key = f"{v}|{load:g}"
            kinds: dict[str, list[float]] = {}
            legit_share, role, per_day = [], [], []
            for n in NAMES:
                r = res[n][key]
                for k, x in r["per_kind"].items():
                    kinds.setdefault(k, []).append(x)
                legit_share.append(sum(r["legit_alerts"].values()) / max(1, r["alerts"]))
                role.append(r["legit_alerts"].get("role_change", 0) / max(1, r["alerts"]))
                per_day.append(r["alerts_per_day"])
            m = np.mean([np.mean(x) for x in kinds.values()])
            print(f"{key:<22} detection {m:.1%} | alerts/day {np.mean(per_day):.2f} | on legit-change"
                  f" days {np.mean(legit_share):.1%} (role change {np.mean(role):.1%})")
    for n in NAMES:
        print(n, {k: res[n][k] for k in ("notices_per_day", "settled_share_of_path_events",
                                         "crowd_share_of_events")})


if __name__ == "__main__":
    main()
