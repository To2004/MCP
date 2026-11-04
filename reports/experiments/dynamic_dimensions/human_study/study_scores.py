"""Score the simulated organisation with the shipped dynamic-layer engine, one agent-day at a time.

The shipped ``BehaviourEngine`` (design v4 by default) is fed every agent's messages in one stream
in time order, as ``normal_org_sim.py --check-port`` does, so its org discount sees all agents at
once. Its limits are the ones ``policy.py`` learns from the first 30 days. For each scored
agent-day (days 90-179) we keep what the daily review list needs: the day's largest multiplier
``M``, the dimension that set it, that call's second score ``s2`` and the day's largest
``static x M``. The daily list is the top 4 agent-days by ``(M, s2)``, ties at the cut broken at
random, exactly as ``normal_org_sim.analyse`` ranks "M, then second score".
"""

from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

SIM_DIR = Path(__file__).resolve().parent.parent
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from mcp_security.behaviour.engine import BehaviourConfig, BehaviourEngine  # noqa: E402
from normal_org_sim import (  # noqa: E402
    CONFIG,
    EVAL_FROM,
    learned_config,
    message,
    topk_probability,
)
from normal_org_world import BASE_DAY, DAY  # noqa: E402

DESIGN = "v4"
LIST_SIZE = 4  # the daily review list: top 4 agent-days of the organisation
SCORE_DIGITS = 9  # rounding of (M, s2) before ranking, as normal_org_sim does
STATIC_COLUMN = 10  # the row tuple's static level (normal_org_world.ROW)


@dataclass(frozen=True)
class DayScore:
    """What the engine said about one agent-day."""

    multiplier: float  # the day's largest M
    risk: float  # the day's largest static x M
    strongest: str | None  # the dimension that set the day's M
    second: float  # s2 of the call that set the day's M
    above_ordinary: tuple[str, ...]  # that call's dimensions past 0.5, strongest first


@dataclass(frozen=True)
class ListPlace:
    """Where an agent-day stands on its day's review list."""

    rank: int  # 1 + agent-days of that day with a strictly higher (M, s2)
    chance: float  # chance it is on the top-4 list when ties at the cut are broken at random


def shipped_config(world: dict[str, list[tuple]], design: str = DESIGN) -> BehaviourConfig:
    """The documented limits plus what ``policy.py`` learns from the first 30 days."""
    return learned_config(world, replace(CONFIG, design=design))


def score_world(
    world: dict[str, list[tuple]], config: BehaviourConfig
) -> dict[tuple[str, int], DayScore]:
    """Run the shipped engine over every message in time order; one record per scored agent-day."""
    engine = BehaviourEngine(config)
    stream = sorted((r[0], aid, i) for aid, rows in world.items() for i, r in enumerate(rows))
    days: dict[tuple[str, int], list] = {}
    for ts, aid, i in stream:
        row = world[aid][i]
        verdict = engine.observe(message(aid, row))
        day = int(ts // DAY) - BASE_DAY
        if day < EVAL_FROM:
            continue
        record = days.get((aid, day))
        if record is None:
            record = days[(aid, day)] = [0.0, 0.0, None, 0.0, ()]
        if verdict.multiplier > record[0]:
            ordered = sorted(verdict.scores.values(), reverse=True)
            record[0], record[2] = verdict.multiplier, verdict.strongest
            record[3] = ordered[1] if len(ordered) > 1 else 0.0
            record[4] = tuple(verdict.above_ordinary)
        record[1] = max(record[1], row[STATIC_COLUMN] * verdict.multiplier)
    return {
        key: DayScore(rec[0], rec[1], rec[2], rec[3], rec[4]) for key, rec in sorted(days.items())
    }


def rank_key(score: DayScore) -> tuple[float, float]:
    """The review list's order: M, then that call's s2."""
    return (round(score.multiplier, SCORE_DIGITS), round(score.second, SCORE_DIGITS))


def daily_list(
    scores: dict[tuple[str, int], DayScore], list_size: int = LIST_SIZE
) -> dict[tuple[str, int], ListPlace]:
    """Each agent-day's rank on its day and its chance of being on the top-``list_size`` list."""
    keys = sorted(scores)
    ranking = [rank_key(scores[k]) for k in keys]
    day = np.array([k[1] for k in keys])
    chance, _ = topk_probability(ranking, day, list_size)
    by_day: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for k, r in zip(keys, ranking):
        by_day[k[1]].append(r)
    places = {}
    for i, k in enumerate(keys):
        higher = sum(1 for other in by_day[k[1]] if other > ranking[i])
        places[k] = ListPlace(1 + higher, float(chance[i]))
    return places
