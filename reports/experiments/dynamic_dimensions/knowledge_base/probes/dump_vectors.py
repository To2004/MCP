"""Dump the v4 engine's per-call score vectors from the simulator's development worlds.

One row per tool call for every day 0-179 of a world, saved as a compressed npz with a JSON
sidecar that describes every column. The engine runs exactly as ``normal_org_sim.py`` runs its
``'v4'`` result: the simulation engine ``Variant`` with the ``V4`` switches and the limits that
``policy.derive_policy`` learns from the first 30 days (``normal_org_sim.py:212, 239-255,
1087``). The probe only wraps four ``Variant`` methods in this process (never in the repo) to
record the first-access floor, each red flag's raw value and raised days, and the org-discount
events. The wrappers return what the originals return, so ``M`` is unchanged.

Messages that are not tool calls (``initialize``, ``tools/list``) also enter the simulator's
day maximum (``normal_org_sim.py:421-435``), so they are saved in a small side table
(``msg_*`` arrays). The validation rebuilds the simulator's own inputs to ``analyse`` from the
saved npz and compares them with ``results/*.json`` ``'v4'``.

These worlds are DEVELOPMENT WORLDS: seeds 7, 11 and 21 were used to design v1-v4. No number
computed from them is a test result.

Run from the repo root (PYTHONHASHSEED is forced to 0; the script re-executes itself if needed):

    uv run python reports/experiments/dynamic_dimensions/knowledge_base/probes/dump_vectors.py \
        --world main_seed7 --world main_seed11 --world heavy_files_seed21 --workers 6
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import replace
from multiprocessing import get_context
from pathlib import Path

import numpy as np

REQUIRED_HASH_SEED = "0"  # normal_org_world.py:525 sorts repositories by a salted hash()
if os.environ.get("PYTHONHASHSEED") != REQUIRED_HASH_SEED:
    os.environ["PYTHONHASHSEED"] = REQUIRED_HASH_SEED
    os.execv(sys.executable, [sys.executable, *sys.argv])

HERE = Path(__file__).resolve().parent
SIM_DIR = HERE.parents[1]  # reports/experiments/dynamic_dimensions
REPO = HERE.parents[4]
sys.path.insert(0, str(SIM_DIR))

import normal_org_engines as engines  # noqa: E402
import normal_org_sim as sim  # noqa: E402
from mcp_security.behaviour.engine import (  # noqa: E402
    ASSET,
    ASSETS_LAST_HOUR,
    BURST,
    CALL_METHOD,
    CALLS_LAST_HOUR,
    CLIENT,
    DAY_S,
    MANY_ASSETS,
    MINUTE_S,
    NETWORK,
    PROTOCOL_SKIP,
    REQUEST_TOO_BIG,
    SAME_CALL_10M,
    SEQUENCE,
    SESSION_LENGTH,
    TIME_OF_DAY,
    TOOL,
    WRITES_LAST_HOUR,
)
from normal_org_world import BASE_DAY, CATALOG, DAY, PROFILES, build_world  # noqa: E402

DEFAULT_OUT = Path(
    "/tmp/claude-343913582/-home-ovadyat-MCP/d6821e4d-e280-4911-be08-63b780ec3aaa/"
    "scratchpad/v5_vectors"
)
MAX_WORKERS = 6
ENGINE = "v4"  # the normal_org_sim.VARIANTS entry this probe reproduces
EVAL_FROM = sim.EVAL_FROM  # 90: the simulator scores days 90-179
ALERT = sim.ALERT  # the x3 line

#: world name -> how normal_org_sim.py built it for its saved results file
WORLDS: dict[str, dict] = {
    "main_seed7": {"seed": 7, "profile": "main", "agents": 150, "results": "normal_org_sim"},
    "main_seed11": {
        "seed": 11,
        "profile": "main",
        "agents": 150,
        "results": "normal_org_sim_seed11",
    },
    "heavy_files_seed21": {
        "seed": 21,
        "profile": "heavy_files",
        "agents": 150,
        "results": "normal_org_git_heavy_files",
    },
    "smoke": {"seed": 7, "profile": "main", "agents": 30, "results": None},  # quick self-test
}
WORLD_CODES = {name: i for i, name in enumerate(WORLDS)}

#: (engine key, paper name, group): the 15 v4 dimensions (DIMENSION_FORMULAS.md, section Names)
DIMENSIONS: tuple[tuple[str, str, str], ...] = (
    (CALLS_LAST_HOUR, "Call rate", "Typical Cadence"),
    (WRITES_LAST_HOUR, "Write rate", "Typical Cadence"),
    (ASSETS_LAST_HOUR, "Breadth", "Typical Cadence"),
    (SAME_CALL_10M, "Repetition", "Typical Cadence"),
    (SESSION_LENGTH, "Session duration", "Typical Cadence"),
    (TIME_OF_DAY, "Hour of day", "Typical Cadence"),
    (TOOL, "Tool", "Typical Footprint"),
    (ASSET, "Asset", "Typical Footprint"),
    (NETWORK, "Network", "Typical Footprint"),
    (CLIENT, "Client", "Typical Footprint"),
    (BURST, "Burst", "Red Flags"),
    (MANY_ASSETS, "Sweep", "Red Flags"),
    (REQUEST_TOO_BIG, "Oversized request", "Red Flags"),
    (SEQUENCE, "Unsafe sequence", "Red Flags"),
    (PROTOCOL_SKIP, "Missing handshake", "Red Flags"),
)
DIM_KEYS = tuple(k for k, _, _ in DIMENSIONS)
DIM_INDEX = {k: i for i, k in enumerate(DIM_KEYS)}
FLAG_KEYS = (BURST, MANY_ASSETS, REQUEST_TOO_BIG, SEQUENCE, PROTOCOL_SKIP)
ORG_KINDS = ("network", "client", "tool", "asset")  # org-discount bit i = ORG_KINDS[i]
ROLES = ("ci_bot", "triage_bot", "report_bot", "dev", "lead", "sre", "pm")
BOT_ROLES = frozenset({"ci_bot", "triage_bot", "report_bot"})
TOOLS = tuple(CATALOG)
OPERATIONS = ("read", "write", "metadata")
METHODS = ("initialize", "tools/list")
LABEL_ORDINARY, LABEL_CHANGE, LABEL_GRAY = 0, 1, 2
NAN = float("nan")

CALL_COLUMNS: tuple[str, ...] = (
    "agent",
    "seq",
    "day",
    "ts",
    "label",
    "label_kind",
    "tag_mask",
    "episode",
    *(f"s_{k}" for k in DIM_KEYS),
    "n_dims",
    "s1",
    "dstar",
    "s2",
    "M",
    "A",
    "age",
    "warm",
    "floor",
    "asset_nofloor",
    *(f"raw_{f}" for f in FLAG_KEYS),
    *(f"k_{f}" for f in FLAG_KEYS),
    "org_mask",
    *(f"org_raw_{d}" for d in ORG_KINDS),
    "tool",
    "sens",
    "op",
    "static",
    "size",
    "size_limit",
    "minute_calls",
    "hour_assets",
)
MSG_COLUMNS: tuple[str, ...] = (
    "msg_agent",
    "msg_seq",
    "msg_day",
    "msg_ts",
    "msg_method",
    "msg_label_kind",
    "msg_tag_mask",
    "msg_episode",
    "msg_s_network",
    "msg_s_client",
    "msg_n_dims",
    "msg_s1",
    "msg_dstar",
    "msg_s2",
    "msg_M",
)
FLOAT32 = {
    *(f"s_{k}" for k in DIM_KEYS),
    "s1",
    "s2",
    "M",
    "floor",
    "asset_nofloor",
    *(f"raw_{f}" for f in FLAG_KEYS),
    *(f"org_raw_{d}" for d in ORG_KINDS),
    "msg_s_network",
    "msg_s_client",
    "msg_s1",
    "msg_s2",
    "msg_M",
}
INT_TYPES = {
    "agent": np.int16,
    "seq": np.int32,
    "day": np.int16,
    "label": np.int16,
    "label_kind": np.int8,
    "tag_mask": np.int32,
    "episode": np.int32,
    "n_dims": np.int8,
    "dstar": np.int8,
    "A": np.int16,
    "age": np.int16,
    "warm": np.uint8,
    **{f"k_{f}": np.int16 for f in FLAG_KEYS},
    "org_mask": np.int8,
    "tool": np.int8,
    "sens": np.int8,
    "op": np.int8,
    "static": np.int8,
    "size": np.int32,
    "size_limit": np.int32,
    "minute_calls": np.int16,
    "hour_assets": np.int16,
    "msg_agent": np.int16,
    "msg_seq": np.int32,
    "msg_day": np.int16,
    "msg_method": np.int8,
    "msg_label_kind": np.int8,
    "msg_tag_mask": np.int32,
    "msg_episode": np.int32,
    "msg_n_dims": np.int8,
    "msg_dstar": np.int8,
}
FLOAT64 = {"ts", "msg_ts"}

#: set in the parent before the pool forks, read by the workers
VOCAB: dict = {}


# ── instrumentation: wrappers around four Variant methods, in this process only ──────────────
_ORIGINAL = {
    name: getattr(engines.Variant, name)
    for name in ("_origin", "_sensitive_value", "_rule_value", "_org_started")
}


def _new_record() -> dict:
    return {"warm": None, "scores": None, "floor": NAN, "prefloor": NAN, "flags": {}, "org": {}}


def _origin(self, st, m, today, warm, scores):
    """Called first for every message: keep ``warm`` and the live ``scores`` dict."""
    rec = self._rec
    rec["warm"], rec["scores"] = warm, scores
    return _ORIGINAL["_origin"](self, st, m, today, warm, scores)


def _sensitive_value(self, sensitivity, tool):
    """Called only when the first-access floor applies (``normal_org_engines.py:475-485``)."""
    value = _ORIGINAL["_sensitive_value"](self, sensitivity, tool)
    rec = self._rec
    rec["floor"] = value  # v4 never org-discounts the floor (sensitive_org_discount=False)
    rec["prefloor"] = rec["scores"].get(ASSET, NAN)
    return value


def _rule_value(self, st, rule, value, today):
    """A raised red flag: keep its value before the habit discount and its raised days k."""
    out = _ORIGINAL["_rule_value"](self, st, rule, value, today)
    days = st.rule_days.get(rule) or ()
    window = self.config.history_days
    k = sum(1 for d in days if today - window < d < today)  # = ``broken`` at engines.py:538
    self._rec["flags"][rule] = (value, k)
    return out


def _org_started(self, kind, value, ts, agent):
    """An org-discount event: keep the score the dimension had before the cap at 0.5."""
    hit = _ORIGINAL["_org_started"](self, kind, value, ts, agent)
    if hit:
        cfg, st, today = self.config, self.agents[agent], int(ts // DAY_S)
        memory, ceiling = {
            "tool": (st.tools, cfg.tool_ceiling),
            "asset": (st.assets, 1.0),
            "network": (st.network_counts, cfg.origin_ceiling),
            "client": (st.client_counts, cfg.origin_ceiling),
        }[kind]
        e = memory.per_day((value,), True, None, today)  # pure: count_days is off in v4
        self._rec["org"][kind] = ceiling / (1 + cfg.tolerance * e)
    return hit


def install_probes() -> None:
    """Wrap the four methods on the class (this process and its forked workers only)."""
    flags = sim.V4
    if flags.sensitive_org_discount or not flags.sensitive_floor or flags.days:
        raise RuntimeError("the probe assumes V4: floor on, no org discount on it, calls counted")
    engines.Variant._origin = _origin
    engines.Variant._sensitive_value = _sensitive_value
    engines.Variant._rule_value = _rule_value
    engines.Variant._org_started = _org_started


# ── the world and its labels ─────────────────────────────────────────────────────────────────
def agent_index(aid: str) -> int:
    """The roster index of an agent id such as ``dev-021`` (unique per world)."""
    return int(aid.rsplit("-", 1)[1])


def label_of(legit: str, gray: str) -> tuple[str, int]:
    """The call's label code and kind, as the simulator ranks a day: gray, then change."""
    if gray:
        return f"gray:{gray.split(':')[0]}", LABEL_GRAY
    if legit:
        return f"change:{legit}", LABEL_CHANGE
    return "ordinary", LABEL_ORDINARY


def build_vocab(world: dict, roles: dict) -> dict:
    """Tag, label, episode and agent vocabularies, from every message of the world."""
    tags, labels, episodes = set(), {"ordinary"}, set()
    for rows in world.values():
        for r in rows:
            if r[11]:
                tags.update(r[11].split("|"))
            if r[12]:
                episodes.add(r[12])
            if r[1] == CALL_METHOD:
                labels.add(label_of(r[11], r[12])[0])
    tag_list = sorted(tags)
    if len(tag_list) > 31:
        raise ValueError(f"{len(tag_list)} tags do not fit an int32 mask")
    label_list = ["ordinary", *sorted(labels - {"ordinary"})]
    episode_list = sorted(episodes)
    agents = sorted(world, key=agent_index)
    return {
        "tags": tag_list,
        "tag_bit": {t: 1 << i for i, t in enumerate(tag_list)},
        "labels": label_list,
        "label_index": {s: i for i, s in enumerate(label_list)},
        "episodes": episode_list,
        "episode_index": {e: i for i, e in enumerate(episode_list)},
        "agents": agents,
        "roles": {aid: roles[aid] for aid in agents},
    }


def tag_mask(legit: str) -> int:
    bits = VOCAB["tag_bit"]
    return sum(bits[t] for t in set(legit.split("|"))) if legit else 0


# ── one worker: a shard of agents ────────────────────────────────────────────────────────────
def _top_and_second(scores: dict) -> tuple[float, int, float]:
    """(s1, d* index, s2) as the simulator takes them (normal_org_engines.py:348, sim.py:432)."""
    if not scores:
        return NAN, -1, 0.0
    strongest = max(scores, key=lambda d: scores[d])
    ordered = sorted(scores.values(), reverse=True)
    return scores[strongest], DIM_INDEX[strongest], ordered[1] if len(ordered) > 1 else 0.0


def _minute_calls(recent, ts: float) -> int:
    """Tool calls in the last minute, this one included (the burst count)."""
    n = 0
    for t in reversed(recent):
        if t <= ts - MINUTE_S:
            break
        n += 1
    return n


def dump_shard(aids: list[str]) -> dict:
    """Run the v4 observer over ``aids`` (each agent's messages in order); typed columns."""
    observe = sim.make_observer(ENGINE)
    variant = observe.__self__
    cfg, window = variant.config, variant.config.history_days
    tolerance = cfg.tolerance
    habit = variant.flags.rarity_rules if variant.flags.rule_rarity else frozenset()
    calls, msgs = [], []
    habit_check = 0.0
    unknown: set = set()
    for aid in aids:
        a_idx, cached_day, cached = agent_index(aid), None, (0, 0)
        for seq, r in enumerate(sim.WORLD[aid]):
            rec = variant._rec = _new_record()
            M, _, scores = observe(sim.message(aid, r))
            unknown.update(k for k in scores if k not in DIM_INDEX)
            day = int(r[0] // DAY)
            sim_day = day - BASE_DAY
            ts_rel = r[0] - BASE_DAY * DAY
            legit, gray = r[11], r[12]
            kind = label_of(legit, gray)[1]
            ep = VOCAB["episode_index"][gray] if gray else -1
            s1, dstar, s2 = _top_and_second(scores)
            if r[1] != CALL_METHOD:
                msgs.append(
                    (
                        a_idx,
                        seq,
                        sim_day,
                        ts_rel,
                        METHODS.index(r[1]) if r[1] in METHODS else len(METHODS),
                        kind,
                        tag_mask(legit),
                        ep,
                        scores.get(NETWORK, NAN),
                        scores.get(CLIENT, NAN),
                        len(scores),
                        s1,
                        dstar,
                        s2,
                        M,
                    )
                )
                continue
            st = variant.agents[aid]
            if cached_day != day:  # constant within the day: history updates once a day
                active = sum(1 for d in st.tools.by_day if day - window < d < day)
                cached_day, cached = day, (active, day - st.first_day)
            active, age = cached
            floor = rec["floor"]
            s_asset = scores.get(ASSET, NAN)
            asset_nofloor = rec["prefloor"] if not math.isnan(floor) else s_asset
            raws, ks = [], []
            for f in FLAG_KEYS:
                raw, k = rec["flags"].get(f, (NAN, -1))
                raws.append(raw)
                ks.append(k)
                if f in habit and k >= 0:
                    expected = raw / (1 + tolerance * k / (active + 1))
                    habit_check = max(habit_check, abs(expected - scores[f]))
            org_mask = sum(1 << i for i, d in enumerate(ORG_KINDS) if d in rec["org"])
            tool = r[3]
            calls.append(
                (
                    a_idx,
                    seq,
                    sim_day,
                    ts_rel,
                    VOCAB["label_index"][label_of(legit, gray)[0]],
                    kind,
                    tag_mask(legit),
                    ep,
                    *(scores.get(k, NAN) for k in DIM_KEYS),
                    len(scores),
                    s1,
                    dstar,
                    s2,
                    M,
                    active,
                    age,
                    int(bool(rec["warm"])),
                    floor,
                    asset_nofloor,
                    *raws,
                    *ks,
                    org_mask,
                    *(rec["org"].get(d, NAN) for d in ORG_KINDS),
                    TOOLS.index(tool),
                    r[5] if r[5] is not None else -1,
                    OPERATIONS.index(r[6]),
                    r[10],
                    r[9],
                    variant.size_limits.get(tool, cfg.request_limit_bytes),
                    _minute_calls(st.recent, r[0]),
                    len(st.hour_asset_counts),
                )
            )
    return {
        "calls": _typed(calls, CALL_COLUMNS),
        "msgs": _typed(msgs, MSG_COLUMNS),
        "habit_check": habit_check,
        "unknown_dimensions": sorted(unknown),
    }


def _typed(rows: list[tuple], columns: tuple[str, ...]) -> dict[str, np.ndarray]:
    """Rows of numbers -> one typed array per column (ts and M also kept in float64)."""
    table = np.array(rows, dtype=np.float64).reshape(len(rows), len(columns))
    out = {}
    for i, name in enumerate(columns):
        col = table[:, i]
        if name in FLOAT64:
            out[name] = col.copy()
        elif name in FLOAT32:
            out[name] = col.astype(np.float32)
        else:
            out[name] = col.astype(INT_TYPES[name])
        if name in ("M", "msg_M"):
            out[f"{name}__f64"] = col.copy()  # for the float32 check; not saved
    return out


# ── assemble, save, describe ─────────────────────────────────────────────────────────────────
def assemble(parts: list[dict], prefix: str, key: str, seq: str) -> dict[str, np.ndarray]:
    """Concatenate shards and sort rows by (agent, message order)."""
    merged = {name: np.concatenate([p[key][name] for p in parts]) for name in parts[0][key]}
    order = np.lexsort((merged[seq], merged[f"{prefix}agent"]))
    return {name: col[order] for name, col in merged.items()}


def episode_table(calls: dict) -> dict[str, np.ndarray]:
    """Per episode: kind, agent, first and last day, and number of tool calls."""
    episodes = VOCAB["episodes"]
    kinds = sorted({e.split(":")[0] for e in episodes})
    ep = calls["episode"]
    rows = np.flatnonzero(ep >= 0)
    n = len(episodes)
    first = np.full(n, 10_000, dtype=np.int64)
    last = np.full(n, -1, dtype=np.int64)
    np.minimum.at(first, ep[rows], calls["day"][rows])
    np.maximum.at(last, ep[rows], calls["day"][rows])
    return {
        "ep_kind": np.array([kinds.index(e.split(":")[0]) for e in episodes], dtype=np.int8),
        "ep_agent": np.array([agent_index(e.split(":")[1]) for e in episodes], dtype=np.int16),
        "ep_first_day": first.astype(np.int16),
        "ep_last_day": last.astype(np.int16),
        "ep_calls": np.bincount(ep[rows], minlength=n).astype(np.int32),
    }, kinds


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def provenance() -> dict:
    files = [
        SIM_DIR / "normal_org_world.py",
        SIM_DIR / "normal_org_engines.py",
        SIM_DIR / "normal_org_sim.py",
        REPO / "src/mcp_security/behaviour/engine.py",
        REPO / "src/mcp_security/behaviour/memory.py",
        REPO / "src/mcp_security/behaviour/policy.py",
        Path(__file__).resolve(),
    ]
    head = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    return {
        "git_head": head,
        "note": "the simulator files are untracked and engine.py/policy.py have uncommitted "
        "edits, so the sha256 digests below, not the git head, identify the code",
        "sha256": {str(p.relative_to(REPO)): file_digest(p) for p in files},
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "PYTHONHASHSEED": os.environ["PYTHONHASHSEED"],
    }


def column_docs(kinds: list[str]) -> dict[str, str]:
    """One sentence per saved array."""
    dims = ", ".join(f"{i}={k}" for i, k in enumerate(DIM_KEYS))
    docs = {
        "world": f"world code: {WORLD_CODES}",
        "agent": "agent roster index (agents[i] in the sidecar is its id)",
        "role": f"role code: {dict(enumerate(ROLES))}",
        "is_bot": "1 for ci_bot, triage_bot and report_bot",
        "seq": "position of this message in the agent's message stream (calls and non-calls)",
        "day": "simulation day 0-179 = UTC day of ts (the simulator's day, normal_org_sim.py:424)",
        "ts": "seconds since simulation day 0 00:00 UTC (float64; BASE_DAY in meta)",
        "label": "index into labels: ordinary | change:<legit tags joined by |> | gray:<kind>",
        "label_kind": "0 ordinary (no tag, no episode), 1 change (tagged, no episode), 2 gray",
        "tag_mask": "bit i set when tags[i] is on this call (also on gray calls; scope creep)",
        "episode": "index into episodes, -1 if the call is not part of a gray episode",
        "n_dims": "number of dimensions that took part (len(scores))",
        "s1": "top score: the largest s_d (NaN when no dimension took part; M is then 1)",
        "dstar": f"reason d*: index of the dimension that set s1 (-1 if none); {dims}",
        "s2": "runner-up: second-largest s_d (0.0 when fewer than 2 took part, as the simulator)",
        "M": "behaviour multiplier g(s1) in [0.7, 5] (1.0 when nothing took part)",
        "A": "his active days: days with a tool call in the last 90, up to yesterday "
        "(st.tools.active_days, the habit discount's denominator minus 1)",
        "age": "days since his first message",
        "warm": "1 when past the warm-up (5 tool calls and past his first UTC day)",
        "floor": "first-access floor value (0.9 sensitivity 5, 0.8 sensitivity 4) when it "
        "applied (never-touched sensitive asset), else NaN",
        "asset_nofloor": "the asset score without the floor (NaN if the asset took no part "
        "without it, e.g. in the warm-up)",
        "org_mask": "bit i set when the org discount fired on ORG_KINDS[i] = "
        f"{dict(enumerate(ORG_KINDS))} (cap at 0.5 applied)",
        "tool": "index into tools",
        "sens": "asset sensitivity 2-5, -1 if no asset",
        "op": f"operation code: {dict(enumerate(OPERATIONS))}",
        "static": "the tool's static level (2 metadata, 3 read, 4 write), the simulator's static",
        "size": "request bytes",
        "size_limit": "the oversized-request limit for this tool (learned per tool or global)",
        "minute_calls": "tool calls in the last 60 s, this one included (the burst count)",
        "hour_assets": "distinct assets in the last hour, this one included (breadth and sweep)",
        "ep_kind": f"per episode: kind code into kinds = {kinds}",
        "ep_agent": "per episode: agent roster index",
        "ep_first_day": "per episode: first day with a tool call of the episode",
        "ep_last_day": "per episode: last day with a tool call of the episode",
        "ep_calls": "per episode: number of tool calls",
    }
    for k, paper, group in DIMENSIONS:
        docs[f"s_{k}"] = f"score of {paper} ({group}, engine key {k}); NaN when it took no part"
    for f in FLAG_KEYS:
        docs[f"raw_{f}"] = f"{f}: value when raised, before the habit discount (NaN if not raised)"
        docs[f"k_{f}"] = f"{f}: raised days in the last 90, up to yesterday (-1 if not raised)"
    for d in ORG_KINDS:
        docs[f"org_raw_{d}"] = f"{d}: score before the org-discount cap (NaN if no event)"
    docs.update(
        {
            "msg_agent": "non-call message: agent roster index",
            "msg_seq": "non-call message: position in the agent's stream",
            "msg_day": "non-call message: simulation day",
            "msg_ts": "non-call message: seconds since day 0",
            "msg_method": f"non-call message: {dict(enumerate(METHODS))}, {len(METHODS)} other",
            "msg_label_kind": "non-call message: 0 ordinary, 1 change, 2 gray",
            "msg_tag_mask": "non-call message: tag bits",
            "msg_episode": "non-call message: episode index or -1",
            "msg_s_network": "non-call message: network score",
            "msg_s_client": "non-call message: client score",
            "msg_n_dims": "non-call message: dimensions that took part",
            "msg_s1": "non-call message: s1",
            "msg_dstar": "non-call message: d* index",
            "msg_s2": "non-call message: s2",
            "msg_M": "non-call message: M (these enter the simulator's day maximum)",
        }
    )
    return docs


def dump_world(name: str, out_dir: Path, workers: int) -> dict:
    """Build one world, run v4 over it in ``workers`` processes, save npz + sidecar."""
    spec = WORLDS[name]
    t0 = time.time()
    world, roles, _ = build_world(spec["agents"], spec["seed"], PROFILES[spec["profile"]])
    sim.WORLD.clear()
    sim.WORLD.update(world)
    sim.FIRST_USES.clear()
    sim.FIRST_USES.update(sim.first_uses(world))
    policy = sim.learned_config(world, replace(sim.CONFIG, design="v3"))  # sim.py:1087
    sim.CONFIGS["policy.py"] = policy
    learned = sim.learned_config(world, replace(sim.CONFIG, requires_before={}))  # sim.py:1085
    VOCAB.clear()
    VOCAB.update(build_vocab(world, roles))
    t_world = time.time() - t0
    print(f"[{name}] world built and policy learned ({t_world:.0f}s)", flush=True)
    aids = sorted(world, key=lambda a: -len(world[a]))  # as normal_org_sim.py:1119-1120
    shards = [aids[i::workers] for i in range(workers)]
    with get_context("fork").Pool(workers) as pool:
        parts = pool.map(dump_shard, shards)
    t_score = time.time() - t0 - t_world
    print(f"[{name}] scored ({t_score:.0f}s)", flush=True)
    unknown = sorted({d for p in parts for d in p["unknown_dimensions"]})
    if unknown:
        raise RuntimeError(f"dimensions outside the 15 of v4: {unknown}")
    calls = assemble(parts, "", "calls", "seq")
    msgs = assemble(parts, "msg_", "msgs", "msg_seq")
    flips = {
        name: int(np.sum((c[f"{name}__f64"] >= ALERT) != (c[name] >= ALERT)))
        for name, c in (("M", calls), ("msg_M", msgs))
    }
    for c, key in ((calls, "M"), (msgs, "msg_M")):
        del c[f"{key}__f64"]
    role_of = [VOCAB["roles"][a] for a in VOCAB["agents"]]
    by_index = {agent_index(a): ROLES.index(r) for a, r in zip(VOCAB["agents"], role_of)}
    role = np.array([by_index[a] for a in calls["agent"]], dtype=np.int8)
    arrays = {
        "world": np.full(len(calls["agent"]), WORLD_CODES[name], dtype=np.int8),
        "role": role,
        "is_bot": np.isin(role, [ROLES.index(r) for r in BOT_ROLES]).astype(np.uint8),
        **calls,
        **msgs,
    }
    eps, kinds = episode_table(calls)
    arrays.update(eps)
    out_dir.mkdir(parents=True, exist_ok=True)
    npz_path = out_dir / f"{name}.npz"
    np.savez_compressed(npz_path, **arrays)
    t_total = time.time() - t0
    docs = column_docs(kinds)
    sidecar = {
        "world": name,
        "caveat": "DEVELOPMENT WORLD: seeds 7, 11 and 21 and these profiles were used to "
        "design v1-v4. Every number from this file is a development-world number, never a "
        "test result.",
        "spec": spec,
        "engine": f"normal_org_sim.VARIANTS[{ENGINE!r}] = (V4 switches, policy.py limits)",
        "rows": {"tool_calls": int(len(calls["agent"])), "non_call_messages": int(len(msgs["msg_agent"]))},
        "messages": int(sum(len(v) for v in world.values())),
        "agents": [
            {"index": agent_index(a), "id": a, "role": VOCAB["roles"][a]} for a in VOCAB["agents"]
        ],
        "dimensions": [
            {"index": i, "key": k, "paper_name": p, "group": g}
            for i, (k, p, g) in enumerate(DIMENSIONS)
        ],
        "flags": list(FLAG_KEYS),
        "habit_discounted_flags": sorted(sim.V4.rarity_rules),
        "org_kinds": list(ORG_KINDS),
        "roles": list(ROLES),
        "tools": list(TOOLS),
        "operations": list(OPERATIONS),
        "tags": VOCAB["tags"],
        "labels": VOCAB["labels"],
        "episodes": VOCAB["episodes"],
        "kinds": kinds,
        "columns": {
            k: {"dtype": str(v.dtype), "length": int(len(v)), "doc": docs.get(k, "")}
            for k, v in arrays.items()
        },
        "constants": {
            "BASE_DAY": BASE_DAY,
            "eval_from_day": EVAL_FROM,
            "alert_line": ALERT,
            "history_days": policy.history_days,
            "tolerance": policy.tolerance,
            "warmup_calls": policy.warmup_calls,
            "rule_score": policy.rule_score,
            "protocol_skip_score": policy.protocol_skip_score,
            "tool_ceiling": policy.tool_ceiling,
            "origin_ceiling": policy.origin_ceiling,
        },
        "policy_learned_for_v4": {
            "burst_per_minute": policy.burst_per_minute,
            "request_limit_bytes": policy.request_limit_bytes,
            "request_limit_by_tool": dict(sorted(policy.request_limit_by_tool.items())),
            "many_assets_per_hour": policy.many_assets_per_hour,
            "requires_before": {t: sorted(b) for t, b in policy.requires_before.items()},
        },
        "learned_limits_as_in_results_meta": {
            "burst_per_minute": learned.burst_per_minute,
            "request_limit_bytes": learned.request_limit_bytes,
            "requires_before": {t: sorted(b) for t, b in learned.requires_before.items()},
        },
        "checks": {
            "float32_flips_at_x3": flips,
            "habit_discount_max_abs_error": max(p["habit_check"] for p in parts),
        },
        "workers": workers,
        "runtime_seconds": {
            "world_and_policy": round(t_world, 1),
            "scoring": round(t_score, 1),
            "total_with_save": round(t_total, 1),
        },
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "provenance": provenance(),
    }
    (out_dir / f"{name}.json").write_text(json.dumps(sidecar, indent=1))
    print(f"[{name}] saved {npz_path} ({npz_path.stat().st_size / 1e6:.0f} MB, {t_total:.0f}s)")
    return sidecar


# ── validation against the simulator's saved 'v4' result ─────────────────────────────────────
def simulator_inputs(npz_path: Path, with_messages: bool = True) -> tuple:
    """Rebuild ``normal_org_sim.analyse``'s inputs (days, labels, gray_calls, ordinary, roles)
    from a saved npz, exactly as ``score_shard`` and ``day_labels`` build them."""
    meta = json.loads(npz_path.with_suffix(".json").read_text())
    z = np.load(npz_path)
    ids = {a["index"]: a["id"] for a in meta["agents"]}
    roles = {a["id"]: a["role"] for a in meta["agents"]}
    tags, episodes = meta["tags"], meta["episodes"]
    n_call = len(z["agent"])
    parts = {
        "agent": [z["agent"]],
        "seq": [z["seq"]],
        "day": [z["day"]],
        "M": [z["M"].astype(np.float64)],
        "s2": [z["s2"].astype(np.float64)],
        "dstar": [z["dstar"]],
        "static": [z["static"].astype(np.float64)],
        "tag_mask": [z["tag_mask"]],
        "episode": [z["episode"]],
    }
    strange = np.zeros(n_call, dtype=np.int64)
    for i, (k, _, _) in enumerate(DIMENSIONS):
        strange |= (np.nan_to_num(z[f"s_{k}"], nan=0.0) > 0.5).astype(np.int64) << i
    parts["strange"] = [strange]
    if with_messages:
        n_msg = len(z["msg_agent"])
        ms = np.zeros(n_msg, dtype=np.int64)
        for i, key in ((DIM_INDEX[NETWORK], "msg_s_network"), (DIM_INDEX[CLIENT], "msg_s_client")):
            ms |= (np.nan_to_num(z[key], nan=0.0) > 0.5).astype(np.int64) << i
        for col, src in (
            ("agent", "msg_agent"),
            ("seq", "msg_seq"),
            ("day", "msg_day"),
            ("dstar", "msg_dstar"),
            ("tag_mask", "msg_tag_mask"),
            ("episode", "msg_episode"),
        ):
            parts[col].append(z[src])
        parts["M"].append(z["msg_M"].astype(np.float64))
        parts["s2"].append(z["msg_s2"].astype(np.float64))
        parts["static"].append(np.ones(n_msg))
        parts["strange"].append(ms)
    cols = {k: np.concatenate(v) for k, v in parts.items()}
    order = np.lexsort((cols["seq"], cols["agent"]))
    cols = {k: v[order] for k, v in cols.items()}
    keep = cols["day"] >= EVAL_FROM
    cols = {k: v[keep] for k, v in cols.items()}
    key = cols["agent"].astype(np.int64) * 1000 + cols["day"]
    starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    lengths = np.diff(np.r_[starts, len(key)])
    gmax = np.maximum.reduceat(cols["M"], starts)
    is_max = cols["M"] == np.repeat(gmax, lengths)
    idx = np.arange(len(key))
    first = np.minimum.reduceat(np.where(is_max, idx, len(key)), starts)  # strict ">": first
    R = np.maximum.reduceat(cols["static"] * cols["M"], starts)
    strange_or = np.bitwise_or.reduceat(cols["strange"], starts)
    tag_or = np.bitwise_or.reduceat(cols["tag_mask"].astype(np.int64), starts)
    days, labels = {}, {}
    for g, s in enumerate(starts):
        k = (ids[int(cols["agent"][s])], int(cols["day"][s]))
        top = int(cols["dstar"][first[g]])
        days[k] = (
            float(gmax[g]),
            float(R[g]),
            DIM_KEYS[top] if top >= 0 else None,
            int(strange_or[g]).bit_count(),
            float(cols["s2"][first[g]]),
        )
        labels[k] = ({t for i, t in enumerate(tags) if tag_or[g] >> i & 1}, set())
    for i in np.flatnonzero(cols["episode"] >= 0):
        labels[(ids[int(cols["agent"][i])], int(cols["day"][i]))][1].add(
            episodes[int(cols["episode"][i])]
        )
    gray_calls: dict[str, list] = defaultdict(list)
    ordinary: Counter = Counter()
    call_day = z["day"] >= EVAL_FROM
    M_call = z["M"].astype(np.float64)
    for i in np.flatnonzero(call_day & (z["episode"] >= 0)):
        gray_calls[episodes[int(z["episode"][i])]].append(float(M_call[i]))
    plain = call_day & (z["label_kind"] == LABEL_ORDINARY)
    ordinary["calls"] = int(plain.sum())
    ordinary["calls_x2"] = int((M_call[plain] >= 2).sum())
    ordinary["calls_x3"] = int((M_call[plain] >= ALERT).sum())
    return days, labels, dict(gray_calls), ordinary, roles


def _flat(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(_flat(v, f"{prefix}{k}."))
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out[f"{prefix}{k}"] = v
    return out


VALIDATED_KEYS = (
    "agent_days",
    "ordinary_days_x3",
    "ordinary_days_x2",
    "ordinary_days_x3_people",
    "ordinary_days_x3_bots",
    "ordinary_calls_x3",
    "alerts_per_day.ordinary",
    "alerts_per_day.change",
    "alerts_per_day.gray",
    "gray_episodes",
    "gray_caught_x3",
    "review.top 4 | M, then second score.gray_caught",
    "review.top 8 | M, then second score.gray_caught",
    "review.top 4 | M, then second score.days_cut_in_a_tie",
)


def validate(name: str, out_dir: Path) -> dict:
    """Compare the rebuilt ``analyse`` output with the saved ``'v4'`` result of this world."""
    spec = WORLDS[name]
    npz_path = out_dir / f"{name}.npz"
    meta = json.loads(npz_path.with_suffix(".json").read_text())
    report: dict = {"world": name, "results_file": spec["results"]}
    rebuilt = {
        "all messages": sim.analyse(*simulator_inputs(npz_path, with_messages=True)),
        "tool calls only": sim.analyse(*simulator_inputs(npz_path, with_messages=False)),
    }
    if spec["results"] is None:
        report["rebuilt"] = {k: _flat(v) for k, v in rebuilt.items()}
        return report
    saved_all = json.loads((SIM_DIR / "results" / f"{spec['results']}.json").read_text())
    saved, saved_meta = saved_all["results"][ENGINE], saved_all["meta"]
    flat_saved = _flat(saved)
    rows = []
    for key in VALIDATED_KEYS:
        row = {"metric": key, "saved": flat_saved.get(key)}
        for label, res in rebuilt.items():
            row[label] = _flat(res).get(key)
        rows.append(row)
    kinds = sorted(saved["gray"])
    gray_rows = []
    for kind in kinds:
        row = {"kind": kind, "episodes": saved["gray"][kind]["episodes"]}
        row["saved"] = saved["gray"][kind]["caught_x3"]
        row["rebuilt"] = rebuilt["all messages"]["gray"].get(kind, {}).get("caught_x3")
        gray_rows.append(row)
    learned_meta = saved_meta.get("learned_limits", {})
    learned_now = meta["learned_limits_as_in_results_meta"]
    report.update(
        {
            "metrics": rows,
            "gray_by_kind": gray_rows,
            "causes_saved": saved["ordinary_x3_causes"],
            "causes_rebuilt": rebuilt["all messages"]["ordinary_x3_causes"],
            "meta": {
                "messages": {"saved": saved_meta["messages"], "now": meta["messages"]},
                "gray_episodes": {
                    "saved": saved_meta["gray_episodes"],
                    "now": len(meta["episodes"]),
                },
                "learned_limits_equal": learned_meta == learned_now,
                "learned_limits_saved": learned_meta,
                "learned_limits_now": learned_now,
            },
        }
    )
    return report


def _num(x) -> str:
    return f"{x:10.5f}" if isinstance(x, (int, float)) else f"{'-':>10s}"


def print_validation(report: dict) -> None:
    print(f"\nvalidation: {report['world']} vs results/{report['results_file']}.json 'v4'")
    if "metrics" not in report:
        print(json.dumps(report.get("rebuilt"), indent=1)[:2000])
        return
    print(f"{'metric':55s} {'saved':>10s} {'rebuilt':>10s} {'calls only':>10s}")
    for r in report["metrics"]:
        print(
            f"{r['metric']:55s} {_num(r['saved'])} {_num(r['all messages'])} "
            f"{_num(r['tool calls only'])}"
        )
    for r in report["gray_by_kind"]:
        print(f"  gray {r['kind']:20s} n={r['episodes']:3d} saved {_num(r['saved'])} "
              f"now {_num(r['rebuilt'])}")
    print("meta:", json.dumps(report["meta"]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--world", action="append", choices=sorted(WORLDS), required=True)
    ap.add_argument("--workers", type=int, default=MAX_WORKERS)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--validate-only", action="store_true", help="re-validate saved npz files")
    args = ap.parse_args()
    if not 1 <= args.workers <= MAX_WORKERS:
        raise SystemExit(f"--workers must be 1-{MAX_WORKERS}")
    install_probes()
    print(f"PYTHONHASHSEED={os.environ['PYTHONHASHSEED']}, workers={args.workers}", flush=True)
    for name in args.world:  # one world after another, so the machine is not overloaded
        if not args.validate_only:
            dump_world(name, args.out_dir, args.workers)
        report = validate(name, args.out_dir)
        (args.out_dir / f"{name}.validation.json").write_text(json.dumps(report, indent=1))
        print_validation(report)


if __name__ == "__main__":
    main()
