"""EV-15 and EV-17: world pools, seed derivation and the held-out family ranges.

This file is the **range file** the freeze hashes (spec 6.3). It fixes:

- the three pools (spec 6.2-6.4): ``dev`` (5 new worlds per family W2-W8, seeds from a public
  salt, burnt once run), ``calibration`` (10 per family) and ``test`` (30 per family);
- the burnt development seeds {1, 2, 7, 11, 12, 21, 31, 41}, which no derived seed may equal;
- the seed rule, with the public beacon mixed in after the preregistration deposit::

      seed = int(SHA-256(f"{frozen_sha}|{beacon}|{family}|{pool}|{i}")) mod 2^31

  and, for the development pool, ``SHA-256(f"{salt}|{family}|dev|{i}")`` from a public salt.
  ``frozen_sha`` and ``beacon`` enter in one canonical spelling, so one commit and one pulse
  give one seed set (R2-12): trimmed, lower-case hex, the full 40-digit commit sha and a
  :data:`BEACON_HEX`-digit beacon; other lengths are refused (:func:`canonical_hex`).
  A value that is burnt or already used is re-drawn with ``|{attempt}`` appended, so no seed
  is burnt or used twice (:func:`derive_seed`, :func:`seed_plan`);
- each family's ranges (:data:`FAMILY_RANGES`), drawn per world from its seed
  (:func:`world_spec`);
- the sample-size rule n_f = max(30, ceil((1.96 SD_calib / h)^2)) (:func:`family_size`).

The beacon's source is UNVERIFIED (spec 6.3). The world generator reads a :class:`WorldSpec`;
which fields it honours is the simulator's side (EV-06-EV-14).
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

import numpy as np

# ── pools and families ───────────────────────────────────────────────────────────────────────
DEV, CALIBRATION, TEST = "dev", "calibration", "test"
POOLS = (DEV, CALIBRATION, TEST)
FAMILIES: dict[str, str] = {
    "W1": "replication of the 3 profiles, 150 agents",
    "W2": "varied organisations, 5-800 agents, with a 5-30-caller stratum",
    "W3": "modern era",
    "W4": "mixed era",
    "W5": "agent cadence",
    "W6": "365-day horizon",
    "W7": "two-route gateway, GitHub + Slack, with cross-route copies",
    "W8": "churn, 10-30% hires and leavers a year",
}
DEV_FAMILIES = ("W2", "W3", "W4", "W5", "W6", "W7", "W8")  # W1 replicates the burnt profiles
POOL_SIZES = {DEV: 5, CALIBRATION: 10, TEST: 30}  # per family; test and calibration are minima
BURNT_SEEDS = frozenset({1, 2, 7, 11, 12, 21, 31, 41})
SEED_MODULUS = 2**31
MAX_ATTEMPTS = 1_000  # re-draws before giving up (unreachable at 2^31 with a few hundred seeds)
FULL_SHA_HEX = 40  # the frozen commit: `git rev-parse HEAD` in full, never a short sha
# The beacon pulse: 512 bits as hex (for example a NIST Randomness Beacon 2.0 outputValue). The
# source is chosen in Batch 5 (UNVERIFIED); the length is frozen with this range file.
BEACON_HEX = 128
HEX_DIGITS = frozenset("0123456789abcdef")

# ── windows (spec 6.2), in deployment days: day 0 is the world's first day ───────────────────
N_DAYS = 180
LONG_HORIZON_DAYS = 365  # W6
EVAL_FROM_DAY = 90  # days 0-89 are the route warm-up stratum (EV-31)
FIT_WINDOW = (90, 134)  # thresholds, fitted unlabelled
SELECT_WINDOW = (135, 180)  # selection metrics on the new development worlds

# ── sample size (EV-15) ──────────────────────────────────────────────────────────────────────
MIN_TEST_WORLDS = 30
SIZE_Z = 1.96
H_BENIGN_X3_POINTS = 0.2  # half-width for the benign x3 rate, percentage points
H_LIST_CATCH_POINTS = 3.0  # half-width for credited list catch, percentage points

# ── family ranges (the range file proper) ────────────────────────────────────────────────────
PROFILES = ("main", "more_pastes", "heavy_files")  # normal_org_world.PROFILES
BASE_AGENTS = 150
ERAS = ("legacy", "modern", "mixed")
FAMILY_RANGES: dict[str, dict[str, object]] = {
    "common": {
        "calendar": "random",
        "inputs": "gateway",
        "plain_gray_share": 0.5,  # plain variants at 1:1
        "response_sizes": True,
        "public_repos": True,
        "toxic_flow": True,
        "n_days": N_DAYS,
        "eval_from": EVAL_FROM_DAY,
        "era": "legacy",
        "routes": ("github",),
        "agent_share": 0.0,
        "churn_per_year": 0.0,
    },
    "W1": {"n_agents": BASE_AGENTS, "profile_cycle": PROFILES},
    "W2": {
        "n_agents_log_uniform": (5, 800),
        "small_route_share": 0.3,  # worlds drawn in the 5-30-caller stratum
        "small_route_agents": (5, 30),
        "file_write_kb_log_uniform": (1.0, 16.0),
    },
    "W3": {"n_agents": BASE_AGENTS, "era": "modern"},
    "W4": {"n_agents": BASE_AGENTS, "era": "mixed", "modern_share_uniform": (0.2, 0.8)},
    "W5": {"n_agents": BASE_AGENTS, "agent_share_uniform": (0.3, 0.7)},
    "W6": {"n_agents": BASE_AGENTS, "n_days": LONG_HORIZON_DAYS},
    "W7": {"n_agents": BASE_AGENTS, "routes": ("github", "slack")},
    "W8": {"n_agents": BASE_AGENTS, "churn_per_year_uniform": (0.10, 0.30)},
}


@dataclass(frozen=True)
class WorldSpec:
    """One world to generate (EV-17's config fields)."""

    family: str
    pool: str
    index: int
    seed: int
    n_agents: int
    n_days: int
    eval_from: int
    era: str
    modern_share: float  # mixed era: share of modern traffic (1 modern, 0 legacy)
    calendar: str
    profile: str
    file_write_kb: float | None  # None: the profile's own
    agent_share: float  # share of agent-cadence callers (W5)
    churn_per_year: float  # hires and leavers a year (W8)
    routes: tuple[str, ...]
    plain_gray_share: float
    inputs: str
    response_sizes: bool
    public_repos: bool
    toxic_flow: bool


def _check(family: str, pool: str, index: int) -> None:
    if family not in FAMILIES:
        raise ValueError(f"family must be one of {tuple(FAMILIES)}, not {family!r}")
    if pool not in POOLS:
        raise ValueError(f"pool must be one of {POOLS}, not {pool!r}")
    if pool == DEV and family not in DEV_FAMILIES:
        raise ValueError(f"the dev pool draws only {DEV_FAMILIES}, not {family!r}")
    if index < 0:
        raise ValueError(f"index must be non-negative, not {index}")


def canonical_hex(value: str, digits: int, what: str) -> str:
    """``value`` trimmed and in lower case; ``ValueError`` unless it is then exactly ``digits``
    hex digits. Case and surrounding space cannot change a seed; a short or long spelling is
    refused rather than hashed."""
    text = value.strip().lower()
    if len(text) != digits or not set(text) <= HEX_DIGITS:
        raise ValueError(f"{what} must be exactly {digits} hex digits, not {value!r}")
    return text


def _message(root: str, family: str, pool: str, index: int, beacon: str | None) -> str:
    if pool == DEV:
        return f"{root}|{family}|{DEV}|{index}"
    return f"{root}|{beacon}|{family}|{pool}|{index}"


def derive_seed(
    root: str,
    family: str,
    pool: str,
    index: int,
    *,
    beacon: str | None = None,
    exclude: Iterable[int] = BURNT_SEEDS,
    modulus: int = SEED_MODULUS,
) -> int:
    """A world's seed: a pure function of its arguments that is never in ``exclude`` (the burnt
    seeds by default).

    ``root`` is the frozen commit's full sha for the calibration and test pools, which need the
    public ``beacon``; both are hashed in canonical spelling (:func:`canonical_hex`). For the
    dev pool ``root`` is the public salt, hashed as given, and ``beacon`` must be None.
    """
    _check(family, pool, index)
    if pool == DEV:
        if beacon is not None:
            raise ValueError("the dev pool is drawn from the public salt alone, without a beacon")
        if not root:
            raise ValueError("the dev pool needs a non-empty public salt")
    else:
        root = canonical_hex(root, FULL_SHA_HEX, "frozen_sha")
        if not beacon:
            raise ValueError("calibration and test seeds need the public beacon value")
        beacon = canonical_hex(beacon, BEACON_HEX, "beacon")
    if modulus < 2:
        raise ValueError(f"modulus must be at least 2, not {modulus}")
    banned = set(exclude)
    base = _message(root, family, pool, index, beacon)
    for attempt in range(MAX_ATTEMPTS):
        text = base if attempt == 0 else f"{base}|{attempt}"
        value = int.from_bytes(hashlib.sha256(text.encode()).digest(), "big") % modulus
        if value not in banned:
            return value
    raise RuntimeError(f"no free seed for {base!r} after {MAX_ATTEMPTS} attempts")


def dev_seeds(
    salt: str, n: int = POOL_SIZES[DEV], *, modulus: int = SEED_MODULUS
) -> dict[tuple[str, str], tuple[int, ...]]:
    """The development pool's seeds, n per family W2-W8, from the public salt."""
    return seed_plan(salt, None, {DEV: n}, families=DEV_FAMILIES, modulus=modulus)


def seed_plan(
    root: str,
    beacon: str | None,
    sizes: Mapping[str, int] | None = None,
    *,
    families: Iterable[str] = tuple(FAMILIES),
    used: Iterable[int] = (),
    modulus: int = SEED_MODULUS,
) -> dict[tuple[str, str], tuple[int, ...]]:
    """Seeds per (family, pool), unique across the whole plan, never burnt and never in
    ``used`` (pass the dev seeds when deriving the held-out pools). Deterministic: families in
    the order given, pools in :data:`POOLS` order, indices ascending."""
    want = (
        {CALIBRATION: POOL_SIZES[CALIBRATION], TEST: POOL_SIZES[TEST]} if sizes is None else sizes
    )
    taken = set(BURNT_SEEDS) | set(used)
    plan: dict[tuple[str, str], tuple[int, ...]] = {}
    for family in families:
        for pool in (p for p in POOLS if p in want):
            seeds = []
            for i in range(want[pool]):
                seed = derive_seed(
                    root, family, pool, i, beacon=beacon, exclude=taken, modulus=modulus
                )
                taken.add(seed)
                seeds.append(seed)
            plan[(family, pool)] = tuple(seeds)
    return plan


def _log_uniform(rng: np.random.Generator, lo: float, hi: float) -> float:
    return float(math.exp(rng.uniform(math.log(lo), math.log(hi))))


def world_spec(family: str, pool: str, index: int, seed: int) -> WorldSpec:
    """The world a seed stands for: the family's fixed fields, and its ranged fields drawn
    from ``numpy.random.default_rng(seed)`` (a pure function of the arguments)."""
    _check(family, pool, index)
    ranges = FAMILY_RANGES["common"] | FAMILY_RANGES[family]
    rng = np.random.default_rng(seed)
    n_agents = int(ranges.get("n_agents", BASE_AGENTS))
    file_write_kb = None
    if "n_agents_log_uniform" in ranges:
        small_lo, small_hi = ranges["small_route_agents"]
        _, top = ranges["n_agents_log_uniform"]
        small = rng.random() < ranges["small_route_share"]
        lo, hi = (small_lo, small_hi) if small else (small_hi + 1, top)
        n_agents = int(round(_log_uniform(rng, lo, hi)))
        file_write_kb = _log_uniform(rng, *ranges["file_write_kb_log_uniform"])
    profile = PROFILES[0]
    if "profile_cycle" in ranges:
        profile = ranges["profile_cycle"][index % len(ranges["profile_cycle"])]
    era = str(ranges["era"])
    modern_share = {"legacy": 0.0, "modern": 1.0}.get(era, 0.0)
    if "modern_share_uniform" in ranges:
        modern_share = float(rng.uniform(*ranges["modern_share_uniform"]))
    agent_share = float(ranges["agent_share"])
    if "agent_share_uniform" in ranges:
        agent_share = float(rng.uniform(*ranges["agent_share_uniform"]))
    churn = float(ranges["churn_per_year"])
    if "churn_per_year_uniform" in ranges:
        churn = float(rng.uniform(*ranges["churn_per_year_uniform"]))
    return WorldSpec(
        family=family,
        pool=pool,
        index=index,
        seed=seed,
        n_agents=n_agents,
        n_days=int(ranges["n_days"]),
        eval_from=int(ranges["eval_from"]),
        era=era,
        modern_share=modern_share,
        calendar=str(ranges["calendar"]),
        profile=profile,
        file_write_kb=file_write_kb,
        agent_share=agent_share,
        churn_per_year=churn,
        routes=tuple(ranges["routes"]),
        plain_gray_share=float(ranges["plain_gray_share"]),
        inputs=str(ranges["inputs"]),
        response_sizes=bool(ranges["response_sizes"]),
        public_repos=bool(ranges["public_repos"]),
        toxic_flow=bool(ranges["toxic_flow"]),
    )


def plan_worlds(plan: Mapping[tuple[str, str], Iterable[int]]) -> list[WorldSpec]:
    """Every world of a seed plan, in plan order."""
    return [
        world_spec(family, pool, i, seed)
        for (family, pool), seeds in plan.items()
        for i, seed in enumerate(seeds)
    ]


def family_size(sd_calibration: float, half_width: float, minimum: int = MIN_TEST_WORLDS) -> int:
    """Test worlds for a family: max(30, ceil((1.96 SD_calib / h)^2)), SD and h in the same
    units (h = 0.2 points for benign x3, 3 points for credited catch)."""
    if sd_calibration < 0 or half_width <= 0:
        raise ValueError("need sd_calibration >= 0 and half_width > 0")
    return max(minimum, math.ceil((SIZE_Z * sd_calibration / half_width) ** 2))
