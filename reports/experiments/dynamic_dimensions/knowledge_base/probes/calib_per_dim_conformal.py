"""Per-dimension conformal rates + weighted Bonferroni (a v5 calibration arm), offline.

Design: knowledge_base/04-score-aggregation-and-calibration.md sections 5-6.3. Every number this
script prints is from a DEVELOPMENT WORLD (seeds 7, 11 and 21 were used to design v1-v4), never a
test result. It reads the v4 per-call vectors written by dump_vectors.py and scores them with the
shared evaluator calib_eval.py (the only source of headline numbers).

Stage 1, per dimension d (his history = his last 90 days up to yesterday: days t-89 .. t-1, the
window the A column uses; checked on smoke):
- Typical Cadence (call rate .. hour of day): q_d = (1 + N_d) / (A + 1), N_d = his past calls
  whose logged s_d is at least today's (rank of today's unit among his past units; 04 s5.2).
- Typical Footprint (tool, asset, network, client): q_d = e, the design's own per-day rate,
  recovered from s = c / (1 + 2e) (c = 0.9 for tool, network, client; 1 for asset). e is
  lambda_hat x p_split, i.e. the same rank against his past units (04 s1.2, s5.2).
- Red Flags burst, sweep, unsafe sequence: q_d = (k + 1) / (A + 1), k = his raised days (the
  habit discount 0.9 / (1 + 2 q) is this rate). Oversized request and missing handshake: an
  org rate, (1 + org agent-days at least this far over the limit) / (org agent-days + 1).
- Record rank (stage-1 org pooling): when no past unit was as strange (N_d = 0 or k = 0), the
  floor 1/(A+1) is split by the org: q_d = c_d / (A + 1), c_d = (1 + org record-days on d at
  least this strong) / (org record-days + 1). Valid when today's record is exchangeable with the
  org's records (the atom at the floor is broken by an org rank instead of a coin).
- Org discount: q_d >= 0.5 when 3+ other agents adopted the value this week (04 s6.4).
Stage 2: q = min_d q_d / w_d (weighted Bonferroni), d* = argmin, q2 = runner-up.
Stage 3 (options): personal q3 (04 s6.3), or the org day rank P = share of the org's agent-days
of the same stratum (A band, optionally x machine identity) in the last 90 days whose strangest
row had q at most this one.
Policy overrides outside the statistic: the first-access floor (04 s6.4).
Hour of day (option "hour_gap"): the unit score is the gap, in minutes of the day, between this call
and the nearest time of day he called in the window (past calls: nearest other call), ranked the
same way; a record is ranked by its gap among the org's hour-of-day records.
RECOMMENDED arm: stages 1-2 with group weights and the record rank, no stage 3, hour of day from
the logged score. The org day rank arm was declared main before the full worlds ran and lost to
its own ablation on all three; the hour-gap option failed its adoption rule. All arms are kept.
M = g(1 / (1 + 2 P)) with the design's curve g (engine.py:184-188).

Run from the repo root (numpy only, one process):

    python3 reports/experiments/dynamic_dimensions/knowledge_base/probes/calib_per_dim_conformal.py \
        --vectors <dir with the npz files> --world smoke --out <dir>
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import calib_eval as ce  # noqa: E402  (the shared evaluator sits next to this file)

# ── constants ────────────────────────────────────────────────────────────────────────────────
HISTORY_DAYS = 89  # past days in "his last 90 days, up to yesterday" (A = active days in them)
N_DAYS = 182  # simulation days 0-179 plus the UTC spill-over day 180, plus one spare
S_BINS = 4096  # bins on s in [0, 1]; a tied bin counts as ">=" (conservative, 04 s5.2)
Q_LOG_LO, Q_LOG_STEP, Q_BINS = -8.0, 0.002, 6500  # log10 q bins for the day rank, -8 .. +5
MAG_STEP, MAG_BINS = 0.005, 4000  # log2 of "times over the limit"; bin 0 = not raised
ORG_DISCOUNT_Q = 0.5  # 04 s6.4: an org-wide new value gets q_d >= 1/2 (s <= 1/2 in v4)
MIN_STRATUM_DAYS = 200  # a stratum with fewer agent-days in its window borrows the next band's
ALPHAS = (0.01, 0.025, 0.05)
BAND_EDGES = (15, 45)  # the evaluator's history bands (calib_eval.py:59)
BURST_LIMIT, SWEEP_LIMIT = 64, 90  # policy_learned_for_v4 in the sidecar (calls/min, assets/h)

CADENCE = (0, 1, 2, 3, 4, 5)  # call rate, write rate, breadth, repetition, session, hour of day
RARITY_CEILING = {6: 0.9, 7: 1.0, 8: 0.9, 9: 0.9}  # tool, asset, network, client (engine.py:20)
ORG_BIT = {8: 0, 9: 1, 6: 2, 7: 3}  # org_mask bit of each Footprint dimension (sidecar)
HABIT_FLAGS = (10, 11, 13)  # burst, sweep, unsafe sequence (engine HABIT_RULES)
ORG_FLAGS = (12, 14)  # oversized request, missing handshake (no habit discount in v4)
FLOOR_REASON = 15  # d* index for the first-access floor (a policy reason, not a dimension)
N_DIMS = 15

GROUP_OF = ("cadence",) * 6 + ("footprint",) * 4 + ("flags",) * 5
WEIGHTS = {
    # each group a third of the budget, split equally inside the group
    "group": np.array([1 / 18] * 6 + [1 / 12] * 4 + [1 / 15] * 5),
    "equal": np.full(N_DIMS, 1 / 15),
}


@dataclass(frozen=True)
class ArmSpec:
    """One variant of the arm."""

    name: str
    weights: str = "group"  # key into WEIGHTS
    record_rank: bool = True  # stage-1 org pooling at the personal floor
    stage3: str = "org"  # "none", "personal" or "org"
    strata: str = "band"  # for stage3 == "org": "band" or "band_id" (band x machine identity)
    hour_gap: bool = False  # hour of day scored by the time-of-day gap, not by the logged s


ARMS = (
    ArmSpec("S1+2 equal w, no record rank", "equal", False, "none"),
    ArmSpec("S1+2 group w + record rank (RECOMMENDED)", "group", True, "none"),
    ArmSpec("S1+2 group w + record rank + hour gap (option)", "group", True, "none", hour_gap=True),
    ArmSpec("S1+2 group w, no record rank", "group", False, "none"),
    ArmSpec("S1+2 equal w + record rank", "equal", True, "none"),
    ArmSpec("S1+2+3 personal", "group", True, "personal"),
    ArmSpec("S1+2+3 org day rank (pre-declared main)", "group", True, "org", "band"),
    ArmSpec("S1+2+3 org day rank, no record rank", "group", False, "org", "band"),
    ArmSpec("S1+2+3 org day rank, band x identity", "group", True, "org", "band_id"),
)
# The org day rank arm was declared the main arm before the full worlds were run. On all three
# development worlds its own ablation without stage 3 did better, so the recommendation moved.
# The hour-gap option was added after the first full run showed off_hours_batch lost, under a
# rule written before its run: adopt it if, at the x3 line, the benign rate rises by at most 0.2
# points and gray recall falls in no world. It failed the rule (+0.27 to +0.57 points at x3,
# with +1 to +3 episodes), so it stays an option. Held-out worlds must confirm every choice.
RECOMMENDED = ARMS[1].name
HOUR_GAP = ARMS[2].name
PRE_DECLARED = ARMS[6].name
EQUAL_NO_RR, GROUP_NO_RR = ARMS[0].name, ARMS[3].name


# ── small helpers ────────────────────────────────────────────────────────────────────────────
def multiplier_from_q(q: np.ndarray) -> np.ndarray:
    """The design's curve on s = 1/(1+2q): 5^(2s-1) above s = 1/2, 0.7^(1-2s) below."""
    s = 1.0 / (1.0 + 2.0 * np.asarray(q, dtype=np.float64))
    return np.where(s >= 0.5, 5.0 ** (2 * s - 1), 0.7 ** (1 - 2 * s))


def q_from_multiplier(m: float) -> float:
    """Inverse of multiplier_from_q above x1 (used for the x3 line)."""
    s = (math.log(m) / math.log(5.0) + 1) / 2
    return (1 / s - 1) / 2


def window_count(
    ref_day: np.ndarray,
    ref_bin: np.ndarray,
    q_day: np.ndarray,
    q_bin: np.ndarray,
    n_bins: int,
    *,
    at_least: bool,
) -> np.ndarray:
    """For each query, the reference units on days [t-89, t-1] whose bin is >= (or <=) its bin."""
    h = np.bincount(ref_day * n_bins + ref_bin, minlength=N_DAYS * n_bins).reshape(N_DAYS, n_bins)
    tail = np.cumsum(h[:, ::-1], axis=1)[:, ::-1] if at_least else np.cumsum(h, axis=1)
    cum = np.zeros((N_DAYS + 1, n_bins), dtype=np.int64)
    np.cumsum(tail, axis=0, out=cum[1:])
    lo = np.maximum(q_day - HISTORY_DAYS, 0)
    return cum[q_day, q_bin] - cum[lo, q_bin]


def window_units(ref_day: np.ndarray, q_day: np.ndarray) -> np.ndarray:
    """For each query day, the number of reference units on days [t-89, t-1]."""
    cum = np.r_[0, np.cumsum(np.bincount(ref_day, minlength=N_DAYS))]
    return cum[q_day] - cum[np.maximum(q_day - HISTORY_DAYS, 0)]


def s_bin(s: np.ndarray) -> np.ndarray:
    """Bin of a score in [0, 1]."""
    return np.clip((s * S_BINS).astype(np.int64), 0, S_BINS - 1)


def q_bin(q: np.ndarray) -> np.ndarray:
    """Bin of log10 q (q = inf goes to the top bin)."""
    with np.errstate(divide="ignore"):
        x = (np.log10(q) - Q_LOG_LO) / Q_LOG_STEP
    x = np.where(np.isfinite(x), x, Q_BINS - 1)
    return np.clip(np.floor(x), 0, Q_BINS - 1).astype(np.int64)


def mag_bin(m: np.ndarray) -> np.ndarray:
    """Bin of a magnitude >= 1 (times over the limit); NaN (not raised) goes to bin 0."""
    with np.errstate(invalid="ignore", divide="ignore"):
        x = np.floor(np.log2(np.maximum(m, 1.0)) / MAG_STEP) + 1
    return np.where(np.isfinite(m), np.clip(x, 1, MAG_BINS - 1), 0).astype(np.int64)


def agent_slices(agent: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous row ranges of each agent (rows are in agent, stream order)."""
    if np.any(np.diff(agent) < 0):
        raise ValueError("rows are not grouped by agent")
    cut = np.flatnonzero(np.diff(agent)) + 1
    starts, ends = np.r_[0, cut], np.r_[cut, len(agent)]
    return list(zip(starts.tolist(), ends.tolist()))


def day_max_units(
    agent: np.ndarray, day: np.ndarray, value: np.ndarray, mask: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """(day, max value) of every agent-day that has a masked row."""
    idx = np.flatnonzero(mask)
    if len(idx) == 0:
        return np.zeros(0, np.int64), np.zeros(0)
    key = agent[idx] * N_DAYS + day[idx]
    order = np.lexsort((-value[idx], key))
    first = np.r_[True, key[order][1:] != key[order][:-1]]
    pick = idx[order][first]
    return day[pick], value[pick]


# ── the world ───────────────────────────────────────────────────────────────────────────────
@dataclass
class Vectors:
    """The columns this arm reads (calls and non-call messages)."""

    agent: np.ndarray
    day: np.ndarray
    a: np.ndarray
    s: np.ndarray  # (n_calls, 15) logged v4 scores, NaN when the dimension took no part
    floor: np.ndarray
    asset_nofloor: np.ndarray
    raw: dict[int, np.ndarray]
    k: dict[int, np.ndarray]
    org_mask: np.ndarray
    org_raw: dict[int, np.ndarray]
    magnitude: dict[int, np.ndarray]  # times over the limit, NaN when not raised
    is_bot: np.ndarray
    minute: np.ndarray  # UTC minute of the day of each call
    msg_agent: np.ndarray
    msg_day: np.ndarray
    msg_a: np.ndarray
    msg_s: dict[int, np.ndarray]  # network, client
    meta: dict


def load_vectors(npz: Path) -> Vectors:
    """Read the npz columns this arm needs and derive A for the non-call messages."""
    meta = json.loads(npz.with_suffix(".json").read_text())
    keys = [d["key"] for d in meta["dimensions"]]
    with np.load(npz) as z:
        agent = z["agent"].astype(np.int64)
        day = z["day"].astype(np.int64)
        s = np.stack([z[f"s_{k}"].astype(np.float64) for k in keys], axis=1)
        flags = {i: keys[i] for i in HABIT_FLAGS + ORG_FLAGS}
        raw = {i: z[f"raw_{f}"].astype(np.float64) for i, f in flags.items()}
        kk = {i: z[f"k_{f}"].astype(np.int64) for i, f in flags.items()}
        org_raw = {i: z[f"org_raw_{keys[i]}"].astype(np.float64) for i in ORG_BIT}
        size, limit = z["size"].astype(np.float64), z["size_limit"].astype(np.float64)
        mag = {
            10: z["minute_calls"] / BURST_LIMIT,
            11: z["hour_assets"] / SWEEP_LIMIT,
            12: size / np.maximum(limit, 1.0),
            13: np.ones(len(agent)),
            14: np.ones(len(agent)),
        }
        mag = {
            i: np.where(np.isfinite(raw[i]), m.astype(np.float64), np.nan) for i, m in mag.items()
        }
        v = Vectors(
            agent=agent,
            day=day,
            a=z["A"].astype(np.int64),
            s=s,
            floor=z["floor"].astype(np.float64),
            asset_nofloor=z["asset_nofloor"].astype(np.float64),
            raw=raw,
            k=kk,
            org_mask=z["org_mask"].astype(np.int64),
            org_raw=org_raw,
            magnitude=mag,
            is_bot=z["is_bot"].astype(bool),
            minute=((z["ts"] % 86400) // 60).astype(np.int64),
            msg_agent=z["msg_agent"].astype(np.int64),
            msg_day=z["msg_day"].astype(np.int64),
            msg_a=np.zeros(len(z["msg_agent"]), np.int64),
            msg_s={
                8: z["msg_s_network"].astype(np.float64),
                9: z["msg_s_client"].astype(np.float64),
            },
            meta=meta,
        )
    v.msg_a = active_days_at(v.agent, v.day, v.msg_agent, v.msg_day)
    check = active_days_at(v.agent, v.day, v.agent, v.day)
    if not np.array_equal(check, v.a):
        raise ValueError("A does not match active days on [t-89, t-1]")
    return v


def active_days_at(
    agent: np.ndarray, day: np.ndarray, q_agent: np.ndarray, q_day: np.ndarray
) -> np.ndarray:
    """His days with a tool call on [t-89, t-1] for each (agent, day) query."""
    n_agents = int(max(agent.max(), q_agent.max())) + 1
    act = np.zeros((n_agents, N_DAYS), dtype=np.int64)
    act[agent, day] = 1
    cum = np.zeros((n_agents, N_DAYS + 1), dtype=np.int64)
    np.cumsum(act, axis=1, out=cum[:, 1:])
    return cum[q_agent, q_day] - cum[q_agent, np.maximum(q_day - HISTORY_DAYS, 0)]


# ── stage 1 ─────────────────────────────────────────────────────────────────────────────────
@dataclass
class Stage1:
    """Per-dimension rates q_d (inf when the dimension took no part)."""

    q: np.ndarray  # (n_calls, 15)
    q_rr: np.ndarray  # (n_calls, 15) the same with the record rank at the personal floor
    msg_q: np.ndarray  # (n_msgs, 15), only network and client can be finite
    hour_gap_q: np.ndarray  # (n_calls,) hour of day by the time-of-day gap, record-ranked
    record: np.ndarray  # (n_calls, 15) bool, a personal record (N_d = 0 or k = 0)


def cadence_counts(v: Vectors) -> np.ndarray:
    """N_d for the Cadence dimensions: his past calls with s_d at least today's (binned)."""
    n = np.full((len(v.agent), len(CADENCE)), -1, dtype=np.int64)
    for lo, hi in agent_slices(v.agent):
        day = v.day[lo:hi]
        for j, d in enumerate(CADENCE):
            sd = v.s[lo:hi, d]
            ok = np.flatnonzero(np.isfinite(sd))
            if len(ok) == 0:
                continue
            b = s_bin(sd[ok])
            n[lo + ok, j] = window_count(day[ok], b, day[ok], b, S_BINS, at_least=True)
    return n


def footprint_rate(v: Vectors, d: int) -> np.ndarray:
    """q_d = e for a Footprint dimension, from the score before the org cap and the floor."""
    s = v.asset_nofloor.copy() if d == 7 else v.s[:, d].copy()
    fired = ((v.org_mask >> ORG_BIT[d]) & 1).astype(bool) & np.isfinite(v.org_raw[d])
    s[fired] = v.org_raw[d][fired]
    with np.errstate(divide="ignore", invalid="ignore"):
        e = (RARITY_CEILING[d] / s - 1.0) / 2.0
    e = np.where(np.isfinite(s), np.maximum(e, 0.0), np.inf)
    return np.where(fired, np.maximum(e, ORG_DISCOUNT_Q), e)


def org_flag_rate(v: Vectors, d: int) -> np.ndarray:
    """q_d for an org-calibrated flag: share of org agent-days at least this far over the limit."""
    m = v.magnitude[d]
    raised = np.isfinite(m)
    out = np.full(len(m), np.inf)
    if not raised.any():
        return out
    ref_day, ref_mag = day_max_units(v.agent, v.day, m, raised)
    q_d, q_b = v.day[raised], mag_bin(m[raised])
    ge = window_count(ref_day, mag_bin(ref_mag), q_d, q_b, MAG_BINS, at_least=True)
    days_d, _ = day_max_units(v.agent, v.day, np.zeros(len(m)), np.ones(len(m), bool))
    out[raised] = (1.0 + ge) / (window_units(days_d, q_d) + 1.0)
    return out


def record_rank(
    v: Vectors, record: np.ndarray, strength: np.ndarray, n_bins: int, bins
) -> np.ndarray:
    """c_d: share of the org's record-days on d in the window at least as strong (add-one)."""
    out = np.ones(len(record))
    if not record.any():
        return out
    ref_day, ref_val = day_max_units(v.agent, v.day, strength, record)
    qd, qb = v.day[record], bins(strength[record])
    ge = window_count(ref_day, bins(ref_val), qd, qb, n_bins, at_least=True)
    out[record] = (1.0 + ge) / (window_units(ref_day, qd) + 1.0)
    return out


MINUTES = 1440
MAX_GAP = MINUTES // 2  # the largest circular gap in minutes


def circular_gaps(occupied: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per row: minutes to the previous and to the next occupied minute, strictly (circular)."""
    idx = np.arange(3 * MINUTES)
    occ3 = np.tile(occupied, (1, 3))
    last = np.where(occ3, idx, -10 * MINUTES)
    prev = np.maximum.accumulate(last, axis=1)
    nxt = np.minimum.accumulate(np.where(occ3, idx, 20 * MINUTES)[:, ::-1], axis=1)[:, ::-1]
    mid = np.arange(MINUTES, 2 * MINUTES)
    prev_strict = mid - prev[:, mid - 1]
    next_strict = nxt[:, mid + 1] - mid
    return prev_strict, next_strict


def hour_gap_rate(v: Vectors, a1: np.ndarray) -> np.ndarray:
    """Hour of day as a gap: q = (1 + past calls whose gap >= this one's) / (A + 1).

    The gap of a call is the circular distance, in minutes of the day, to the nearest time of
    day he called in [t-89, t-1] (for a past call: to the nearest other past call). A record
    (no past call with a gap this large) is ranked by its gap among the org's records.
    """
    takes_part = np.isfinite(v.s[:, 5])
    n = np.full(len(v.agent), -1, dtype=np.int64)
    gap = np.zeros(len(v.agent), dtype=np.int64)
    for lo, hi in agent_slices(v.agent):
        day, minute = v.day[lo:hi], v.minute[lo:hi]
        h = np.bincount(day * MINUTES + minute, minlength=N_DAYS * MINUTES).reshape(N_DAYS, -1)
        cum = np.zeros((N_DAYS + 1, MINUTES), dtype=np.int64)
        np.cumsum(h, axis=0, out=cum[1:])
        days = np.unique(day)
        w = cum[days] - cum[np.maximum(days - HISTORY_DAYS, 0)]  # window counts per minute
        has = w.sum(axis=1) > 0
        prev_s, next_s = circular_gaps(w > 0)
        near = np.minimum(np.minimum(prev_s, next_s), MAX_GAP)
        today_gap = np.where(w > 0, 0, near)  # a new call at minute m
        past_gap = np.where(w >= 2, 0, near)  # a past call at m, from the nearest other call
        hist = np.zeros((len(days), MAX_GAP + 1), dtype=np.int64)
        rows = np.repeat(np.arange(len(days)), MINUTES)
        np.add.at(hist, (rows, past_gap.ravel()), w.ravel())
        tail = np.cumsum(hist[:, ::-1], axis=1)[:, ::-1]
        di = np.searchsorted(days, day)
        g = today_gap[di, minute]
        ok = takes_part[lo:hi] & has[di]
        n[lo:hi] = np.where(ok, tail[di, g], -1)
        gap[lo:hi] = g
    q = np.where(n >= 0, (1.0 + n) / a1, np.inf)
    record = n == 0
    rr = record_rank(
        v,
        record,
        gap.astype(np.float64),
        MAX_GAP + 1,
        lambda x: np.clip(x, 0, MAX_GAP).astype(np.int64),
    )
    return np.where(record, q * rr, q)


def stage1(v: Vectors) -> Stage1:
    """Every dimension's per-day rate q_d, with and without the record rank."""
    n_calls = len(v.agent)
    a1 = v.a.astype(np.float64) + 1.0
    q = np.full((n_calls, N_DIMS), np.inf)
    rr = np.ones((n_calls, N_DIMS))
    record = np.zeros((n_calls, N_DIMS), dtype=bool)
    counts = cadence_counts(v)
    for j, d in enumerate(CADENCE):
        ok = counts[:, j] >= 0
        q[ok, d] = (1.0 + counts[ok, j]) / a1[ok]
        record[:, d] = counts[:, j] == 0
        rr[:, d] = record_rank(v, record[:, d], v.s[:, d], S_BINS, s_bin)
    for d in RARITY_CEILING:
        q[:, d] = footprint_rate(v, d)
    for d in HABIT_FLAGS:
        raised = np.isfinite(v.raw[d])
        q[raised, d] = (v.k[d][raised] + 1.0) / a1[raised]
        record[:, d] = raised & (v.k[d] == 0)
        if d != 13:  # unsafe sequence has no strength to rank by
            rr[:, d] = record_rank(v, record[:, d], v.magnitude[d], MAG_BINS, mag_bin)
    for d in ORG_FLAGS:
        q[:, d] = org_flag_rate(v, d)
    msg_q = np.full((len(v.msg_agent), N_DIMS), np.inf)
    for d, s in v.msg_s.items():
        with np.errstate(divide="ignore", invalid="ignore"):
            e = (RARITY_CEILING[d] / s - 1.0) / 2.0
        msg_q[:, d] = np.where(np.isfinite(s), np.maximum(e, 0.0), np.inf)
    return Stage1(
        q=q,
        q_rr=np.where(record, q * rr, q),
        msg_q=msg_q,
        record=record,
        hour_gap_q=hour_gap_rate(v, a1),
    )


# ── stage 2 ─────────────────────────────────────────────────────────────────────────────────
def stage2(qd: np.ndarray, w: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Weighted Bonferroni: q = min_d q_d / w_d, the reason d* and the runner-up q2."""
    x = qd / w[None, :]
    order = np.argsort(x, axis=1, kind="stable")[:, :2]
    rows = np.arange(len(x))
    q, q2 = x[rows, order[:, 0]], x[rows, order[:, 1]]
    dstar = np.where(np.isfinite(q), order[:, 0], -1)
    return q, dstar.astype(np.int64), q2


# ── stage 3 ─────────────────────────────────────────────────────────────────────────────────
def stage3_personal(agent, day, a, q) -> np.ndarray:
    """q3 = (1 + his past rows with q(u) <= q(c)) / (A + 1) (04 s6.3)."""
    out = np.empty(len(q))
    order = np.lexsort((day, agent))
    ag, dy, qq = agent[order], day[order], q[order]
    for lo, hi in agent_slices(ag):
        b = q_bin(qq[lo:hi])
        out[order[lo:hi]] = 1.0 + window_count(dy[lo:hi], b, dy[lo:hi], b, Q_BINS, at_least=False)
    return out / (a + 1.0)


def band_of(a: np.ndarray) -> np.ndarray:
    """History band: 0 for A < 15, 1 for 15-44, 2 for A >= 45."""
    return np.digitize(a, BAND_EDGES)


def stage3_org(agent, day, a, q, ident, strata: str) -> np.ndarray:
    """P = (1 + org agent-days in the stratum's window with day-min q <= q(c)) / (N + 1).

    A stratum is a history band (x machine identity for "band_id"). A band whose window holds
    fewer than MIN_STRATUM_DAYS agent-days also uses the next band's agent-days (fixed rule).
    """
    key = agent * N_DAYS + day
    order = np.lexsort((q, key))
    first = np.r_[True, key[order][1:] != key[order][:-1]]
    top = order[first]  # each agent-day's strangest row
    d_day, d_q, d_band = day[top], q[top], band_of(a[top])
    d_id = ident[top] if strata == "band_id" else np.zeros(len(top), np.int64)
    r_band, r_id = band_of(a), ident if strata == "band_id" else np.zeros(len(q), np.int64)
    out = np.ones(len(q))
    qb = q_bin(q)
    for g in np.unique(r_id):
        for b in range(3):
            rows = np.flatnonzero((r_band == b) & (r_id == g))
            if len(rows) == 0:
                continue
            ref = np.flatnonzero((d_band == b) & (d_id == g))
            n_ref = window_units(d_day[ref], day[rows])
            wide = np.flatnonzero((d_band >= b) & (d_id == g))
            n_wide = window_units(d_day[wide], day[rows])
            le = window_count(
                d_day[ref], q_bin(d_q[ref]), day[rows], qb[rows], Q_BINS, at_least=False
            )
            le_w = window_count(
                d_day[wide], q_bin(d_q[wide]), day[rows], qb[rows], Q_BINS, at_least=False
            )
            small = n_ref < MIN_STRATUM_DAYS
            num = np.where(small, le_w, le) + 1.0
            den = np.where(small, n_wide, n_ref) + 1.0
            out[rows] = num / den
    return out


# ── one arm ─────────────────────────────────────────────────────────────────────────────────
@dataclass
class ArmOut:
    """Per-row outputs of one arm (calls, then messages)."""

    p_final: np.ndarray  # the per-day rate after stage 3 and the overrides
    q2: np.ndarray
    dstar: np.ndarray
    msg_p: np.ndarray
    msg_q2: np.ndarray
    msg_dstar: np.ndarray
    q_stage2: np.ndarray  # before stage 3 (calls then messages)


def run_arm(v: Vectors, st1: Stage1, spec: ArmSpec) -> ArmOut:
    """Stages 2 and 3 and the first-access floor for one arm."""
    w = WEIGHTS[spec.weights]
    qd = st1.q_rr if spec.record_rank else st1.q
    if spec.hour_gap:
        qd = qd.copy()
        qd[:, 5] = st1.hour_gap_q
    q, dstar, q2 = stage2(qd, w)
    mq, mdstar, mq2 = stage2(st1.msg_q, w)
    agent = np.r_[v.agent, v.msg_agent]
    day = np.r_[v.day, v.msg_day]
    a = np.r_[v.a, v.msg_a]
    qall = np.r_[q, mq]
    if spec.stage3 == "personal":
        p = stage3_personal(agent, day, a, qall)
    elif spec.stage3 == "org":
        bots = v.is_bot.astype(np.int64)
        bot_of = np.zeros(int(agent.max()) + 1, np.int64)
        bot_of[v.agent] = bots
        p = stage3_org(agent, day, a, qall, bot_of[agent], spec.strata)
    else:
        p = qall.copy()
    n = len(v.agent)
    floor_q = np.where(np.isfinite(v.floor), (1.0 / v.floor - 1.0) / 2.0, np.inf)
    pc = p[:n].copy()
    use_floor = floor_q < pc
    pc[use_floor] = floor_q[use_floor]
    dstar = np.where(use_floor, FLOOR_REASON, dstar)
    q2 = np.where(use_floor, p[:n], q2)  # under the floor, the runner-up is the statistic
    return ArmOut(pc, q2, dstar, p[n:], mq2, mdstar, qall)


def neglog(x: np.ndarray) -> np.ndarray:
    """-log10 of a rate (higher = stranger); inf rate -> a large negative finite value."""
    with np.errstate(divide="ignore"):
        y = -np.log10(x)
    return np.where(np.isfinite(y), y, -12.0)


def evaluate_arm(npz: Path, v: Vectors, out: ArmOut, name: str) -> dict:
    """The shared evaluator on one arm, with the stated lines as fixed lines."""
    names = [d["paper_name"] for d in v.meta["dimensions"]] + ["First-access floor (policy)"]
    lines = {f"P<={100 * a:g}%": float(-np.log10(a)) for a in ALPHAS}
    lines["x3 (P<=9.43%)"] = float(-np.log10(q_from_multiplier(3.0)))
    return ce.evaluate(
        npz,
        neglog(out.p_final),
        neglog(out.q2),
        out.dstar,
        name,
        msg_primary=neglog(out.msg_p),
        msg_secondary=neglog(out.msg_q2),
        msg_dstar=out.msg_dstar,
        dstar_names=names,
        fixed_lines=lines,
    )


# ── diagnostics (not headline numbers) ──────────────────────────────────────────────────────
def day_min(agent, day, x) -> dict[int, float]:
    """Minimum of x per agent-day key (agent * N_DAYS + day)."""
    key = agent * N_DAYS + day
    order = np.lexsort((x, key))
    first = np.r_[True, key[order][1:] != key[order][:-1]]
    return dict(zip(key[order][first].tolist(), x[order][first].tolist()))


def label_days(v: Vectors, npz: Path) -> dict[int, int]:
    """Day label (0 ordinary, 1 change, 2 gray) for every agent-day key on days 90+."""
    w = ce.load_world(npz)
    with np.load(npz) as z:
        ag = np.r_[z["agent"], z["msg_agent"]].astype(np.int64)
    agent_of_group = ag[w.rows[w.starts]]
    keys = agent_of_group * N_DAYS + w.day
    return dict(zip(keys.tolist(), w.label.tolist()))


def calibration_diagnostics(v: Vectors, st1: Stage1, outs: dict[str, ArmOut], npz: Path) -> dict:
    """Realised versus stated rates on ordinary agent-days, days 90-134 and 135-180."""
    labels = label_days(v, npz)
    agent = np.r_[v.agent, v.msg_agent]
    day = np.r_[v.day, v.msg_day]
    a = np.r_[v.a, v.msg_a]
    res: dict = {"note": "DEVELOPMENT WORLD diagnostics; ordinary agent-days only unless named"}

    def rates(x: np.ndarray, ts) -> dict:
        dm = day_min(agent, day, x)
        out = {}
        for half, (lo, hi) in (("fit 90-134", (90, 134)), ("report 135-180", (135, 180))):
            for cls_name, cls in (("ordinary", (0,)), ("all", (0, 1, 2))):
                vals = np.array(
                    [m for kk, m in dm.items() if lo <= kk % N_DAYS <= hi and labels.get(kk) in cls]
                )
                out[f"{half} {cls_name} (n={len(vals)})"] = {
                    f"t={t:g}": float((vals <= t).mean()) for t in ts
                }
        return out

    ts = (0.01, 0.025, 0.05, 0.1, 0.2, 0.5)
    for name, o in outs.items():
        res[name] = rates(np.r_[o.p_final, o.msg_p], ts)
        res[name + " [stage 2 q]"] = rates(o.q_stage2, ts)
    per_dim = {}
    for d in range(N_DIMS):
        x = np.r_[st1.q_rr[:, d], st1.msg_q[:, d]]
        if not np.isfinite(x).any():
            continue
        per_dim[v.meta["dimensions"][d]["paper_name"]] = rates(x, (0.01, 0.05, 0.1, 0.5))
    res["per dimension q_d (with record rank)"] = per_dim
    # resolution limit: the smallest stage-2 q a day can reach without stage 3
    floor_eq = 1.0 / ((a + 1.0) * WEIGHTS["equal"].max())
    floor_grp = 1.0 / ((a + 1.0) * WEIGHTS["group"].max())
    res["resolution"] = {
        "max M from personal dimensions, equal weights, A=89": float(multiplier_from_q(15 / 90.0)),
        "max M, group weights (best personal w = 1/12), A=89": float(multiplier_from_q(12 / 90.0)),
        "max M, group weights, A=14": float(multiplier_from_q(12 / 15.0)),
        "x3 needs q <=": q_from_multiplier(3.0),
        "share of rows at the equal-weight personal floor or below": float(
            (outs[EQUAL_NO_RR].q_stage2 <= floor_eq * (1 + 1e-9)).mean()
        ),
        "share of rows at the group-weight floor or below (no record rank)": float(
            (outs[GROUP_NO_RR].q_stage2 <= floor_grp * (1 + 1e-9)).mean()
        ),
    }
    return res


def episode_view(v: Vectors, outs: dict[str, ArmOut], kinds: list[str], npz: Path) -> dict:
    """For the named gray kinds: each episode's strangest report-window call per arm and v4."""
    with np.load(npz) as z:
        ep, ep_kind = z["episode"].astype(np.int64), z["ep_kind"].astype(np.int64)
        m4, d4 = z["M"].astype(np.float64), z["dstar"].astype(np.int64)
    names = [d["paper_name"] for d in v.meta["dimensions"]] + ["First-access floor"]

    def best(o: ArmOut, r: np.ndarray) -> dict:
        i = r[np.argmin(o.p_final[r])]
        return {
            "M": round(float(multiplier_from_q(o.p_final[i])), 3),
            "P": float(o.p_final[i]),
            "dstar": names[o.dstar[i]] if o.dstar[i] >= 0 else "none",
            "A": int(v.a[i]),
        }

    res = {}
    for kind in kinds:
        if kind not in v.meta["kinds"]:
            continue
        rows_out = []
        for e in np.flatnonzero(ep_kind == v.meta["kinds"].index(kind)):
            r = np.flatnonzero((ep == e) & (v.day >= 135))
            if len(r) == 0:
                continue
            j = r[np.argmax(m4[r])]
            rows_out.append(
                {
                    "episode": v.meta["episodes"][e],
                    "v4": {
                        "M": round(float(m4[j]), 3),
                        "dstar": names[d4[j]] if d4[j] >= 0 else "-",
                    },
                    "recommended": best(outs[RECOMMENDED], r),
                    "hour_gap_option": best(outs[HOUR_GAP], r),
                    "pre_declared": best(outs[PRE_DECLARED], r),
                }
            )
        res[kind] = rows_out
    return res


# ── markdown from the evaluator's results (no metric is computed here) ─────────────────────
def _pct(x) -> str:
    return "-" if x is None else f"{100 * x:.2f}%"


def _point(res: dict, label: str) -> dict | None:
    for p in res["operating_points"]:
        if p["label"] == label:
            return p
    return None


def _gray_cell(g: dict) -> str:
    ci = g.get("wilson95") or [0.0, 1.0]
    return f"{g['caught']}/{g['episodes']} [{100 * ci[0]:.0f}-{100 * ci[1]:.0f}%]"


def _row(res: dict, p: dict) -> str:
    m, f = p["metrics"], p["fit"]
    lab = m["by_day_label"]
    fit = f"{_pct(f.get('fit_rate'))} ({_pct(f.get('fit_rate_next_value'))})"
    return (
        f"| {res['name']} | {p['label']} | {fit} | {_pct(lab['ordinary']['rate'])}"
        f" | {_pct(lab['change']['rate'])} | {_pct(lab['benign']['rate'])}"
        f" | {_gray_cell(m['gray']['overall'])} | {_pct(m['precision']['credited'])}"
        f" | {m['alerts_per_1000_agent_days']['all']:.1f} |"
    )


def _reasons_line(res: dict, label: str) -> str:
    r = _point(res, label)["metrics"]["benign_alert_reasons"]
    parts = []
    for cls in ("ordinary", "change"):
        top = ", ".join(f"{k} {100 * v:.0f}%" for k, v in list(r[cls]["share"].items())[:4])
        parts.append(f"{cls} n={r[cls]['alerts']}: {top}")
    return f"- {res['name']}, {label}: " + "; ".join(parts)


def compact_tables(world: str, results: list[dict]) -> str:
    """Compact tables of the evaluator's numbers (formatting only; no metric is computed here)."""
    by = {r["name"]: r for r in results}
    focus = [results[0], by[RECOMMENDED], by[PRE_DECLARED]]
    head = (
        "| Arm | Point | Fit rate (one value lower) | Ordinary | Change | Benign |"
        " Gray recall [Wilson 95] | Credited precision | Alerts / 1000 agent-days |"
    )
    lines = [
        f"### {world}: DEVELOPMENT WORLD",
        "",
        "Operating points, report window"
        " (days 135-180; the last rows are the fixed lines on days 90-180):",
        "",
        head,
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for res in focus:
        lines += [_row(res, p) for p in res["operating_points"]]
    tb = "alpha 2.5%, ties by secondary"
    lines += [
        "",
        f"Ablations at '{tb}' and at the x3 line (report window):",
        "",
        "| Arm | Benign at 2.5% | Gray at 2.5% | Benign at x3 | Gray at x3 | Top-4 credited |",
        "|---|---|---|---|---|---|",
    ]
    for res in results:
        p, x = (
            _point(res, tb)["metrics"],
            _point(res, "x3 fixed") or _point(res, "x3 (P<=9.43%) fixed"),
        )
        x = x["metrics"]
        top4 = res["review_list"][0]["credited"]["all"]["recall_exact"]
        lines.append(
            f"| {res['name']} | {_pct(p['by_day_label']['benign']['rate'])}"
            f" | {_gray_cell(p['gray']['overall'])} | {_pct(x['by_day_label']['benign']['rate'])}"
            f" | {_gray_cell(x['gray']['overall'])} | {_pct(top4)} |"
        )
    lines += [
        "",
        "Review list (days 90-180): credited recall (exact) / random / lift:",
        "",
        "| Arm | k=4 | k=8 |",
        "|---|---|---|",
    ]
    for res in results:
        cells = []
        for rl in res["review_list"]:
            c = rl["credited"]["all"]
            cells.append(f"{_pct(c['recall_exact'])} / {_pct(c['random'])} / {c['lift']:.2f}x")
        lines.append(f"| {res['name']} | " + " | ".join(cells) + " |")
    kinds = sorted(_point(results[0], tb)["metrics"]["gray"]["by_kind"])
    lines += [
        "",
        "Gray recall by kind [Wilson 95], report window:",
        "",
        "| Arm | Point | " + " | ".join(kinds) + " |",
        "|---|---|" + "---|" * len(kinds),
    ]
    for res in results:
        labels = [f"alpha {100 * a:g}%, ties by secondary" for a in ALPHAS]
        labels = labels if res in focus[:2] else [tb]
        for lab in labels:
            bk = _point(res, lab)["metrics"]["gray"]["by_kind"]
            cells = [_gray_cell(bk[k]) if bk.get(k) and bk[k]["episodes"] else "-" for k in kinds]
            lines.append(f"| {res['name']} | {lab.split(',')[0]} | " + " | ".join(cells) + " |")
    lines += ["", "Benign alert reasons (share of alerted agent-days by the top row's d*):", ""]
    for res in focus:
        lines.append(_reasons_line(res, tb))
    lines += [
        "",
        f"Strata at '{tb}': benign alert rate (n benign agent-days; gray caught):",
        "",
        "| Arm | People | Bots | A < 15 | 15-44 | A >= 45 |",
        "|---|---|---|---|---|---|",
    ]
    for res in focus:
        st = _point(res, tb)["metrics"]["strata"]
        cells = []
        for grp, key in (
            ("is_bot", "people"),
            ("is_bot", "bots"),
            ("history", "A < 15"),
            ("history", "15 <= A < 45"),
            ("history", "A >= 45"),
        ):
            row, g = st[grp][key], st[grp][key]["gray"]
            cells.append(
                f"{_pct(row['benign']['rate'])} (n={row['benign']['days']}; "
                f"{g.get('caught', 0)}/{g.get('episodes', 0)})"
            )
        lines.append(f"| {res['name']} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


# ── main ────────────────────────────────────────────────────────────────────────────────────
def run_world(npz: Path, arms: tuple[ArmSpec, ...]) -> tuple[list[dict], dict, dict]:
    """Every arm on one world, plus the v4 reference and the diagnostics."""
    t0 = time.time()
    v = load_vectors(npz)
    st1 = stage1(v)
    outs = {spec.name: run_arm(v, st1, spec) for spec in arms}
    print(f"{npz.stem}: stages in {time.time() - t0:.1f}s", flush=True)
    results = [ce.v4_reference(npz, check=False)]
    results += [evaluate_arm(npz, v, outs[spec.name], spec.name) for spec in arms]
    diag = calibration_diagnostics(v, st1, outs, npz)
    diag["episodes"] = episode_view(
        v, outs, ["cross_copy", "overfetch", "bulk_export", "scope_creep", "sensitive_peek"], npz
    )
    diag["record_share_of_ordinary_rows"] = {
        v.meta["dimensions"][d]["paper_name"]: float(st1.record[:, d].mean()) for d in range(N_DIMS)
    }
    print(f"{npz.stem}: done in {time.time() - t0:.1f}s", flush=True)
    return results, diag, outs


def main() -> None:
    """CLI: run the arms on the named worlds and write JSON and markdown to --out."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--vectors", required=True, type=Path)
    ap.add_argument("--world", action="append", required=True)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    md = ["Every table below is a DEVELOPMENT WORLD (burnt seeds), not a test result.", ""]
    for world in args.world:
        npz = args.vectors / f"{world}.npz"
        results, diag, _ = run_world(npz, ARMS)
        md.append(compact_tables(world, results))
        (args.out / f"pdc_{world}.json").write_text(
            json.dumps({"results": results, "diagnostics": diag}, default=ce._jsonable)
        )
        (args.out / f"pdc_{world}_diag.json").write_text(json.dumps(diag, indent=1))
    (args.out / "pdc_tables.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
