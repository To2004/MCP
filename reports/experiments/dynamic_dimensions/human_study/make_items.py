"""Build the "Bot Day Check" item bank: items.json (public), key.json (private), cards.txt.

The human evaluation of the dynamic (behaviour) layer. The MCP server is the protected asset and
the AI agent is the threat: participants judge one agent's day against that agent's own usual
days, never seeing the engine's score. This builder:

1. builds the mostly-ordinary GitHub organisation (``normal_org_world.py``: main profile, 150
   agents, seed 7 by default);
2. scores it with the SHIPPED engine (``mcp_security.behaviour.engine``, design v4) in one stream
   in time order, with the limits ``policy.py`` learns from the first 30 days, as
   ``normal_org_sim.py --check-port`` runs it;
3. builds each day's review list (top 4 agent-days by M, then s2) over days 90-179;
4. picks 16 scored cards in five strata and 8 same-day pairs (``study_select.py``,
   ``study_pairs.py``), adds 2 practice and 2 attention cards (``study_text.py``), and renders
   every card in plain words (``study_facts.py``, ``study_notes.py``);
5. writes ``items.json`` (nothing from the key: no scores, strata, kinds, agent ids or day
   numbers; ids salted with a secret; shuffled; ``N_FORMS`` card orders for the page),
   ``key.json`` and ``cards.txt`` (from ``items.json`` only).

The id salt comes from ``$BOT_DAY_ID_SALT``, else from ``.id_salt`` next to this file (git
ignores it; one is made on the first run). It is stored in ``key.json`` only, so the code alone
does not map an id to an agent-day.

Run (about 6 minutes, most of it the engine):

    uv run python reports/experiments/dynamic_dimensions/human_study/make_items.py \\
        [--seed 7] [--agents 150] [--profile main] [--out-dir DIR] [--cache scores.pkl] \\
        [--require-clean]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import random
import secrets
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIM_DIR = HERE.parent
REPO = SIM_DIR.parents[2]
for path in (HERE, SIM_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from normal_org_sim import EVAL_FROM, day_labels  # noqa: E402
from normal_org_world import N_DAYS, PROFILES, build_world  # noqa: E402
from study_facts import (  # noqa: E402
    HIDDEN_ROWS,
    ROWS,
    DayFacts,
    card_rows,
    collect_facts,
    history_of,
)
from study_notes import (  # noqa: E402
    AgentProfile,
    agent_profiles,
    calendar_note,
    company_note,
    latent_cause,
    org_event_name,
    who_text,
)
from study_scores import (  # noqa: E402
    DESIGN,
    LIST_SIZE,
    DayScore,
    ListPlace,
    daily_list,
    score_world,
    shipped_config,
)
from study_pairs import MIN_MARGIN, PAIR_TYPES, Pair, select_pairs  # noqa: E402
from study_select import (  # noqa: E402
    CHANGE,
    GRAY,
    ORDINARY,
    STRATA,
    STRATUM_NAMES,
    AgentDay,
    Pick,
    Usage,
    opaque_id,
    select_cards,
    shuffle_apart,
)
from study_words import WEEKDAYS  # noqa: E402
from study_text import (  # noqa: E402
    ATTENTION_NAMES,
    BANK_VERSION,
    HAND_CARDS,
    PRACTICE_NAMES,
    bank_text,
    hand_card,
    render_text,
    shared_novelty,
)

DEFAULT_SEED, DEFAULT_AGENTS, DEFAULT_PROFILE = 7, 150, "main"
#: normal_org_world.repo_prefs orders repositories by Python's hash() of strings, which changes
#: from one process to the next unless PYTHONHASHSEED is fixed: the builder pins it
HASH_SEED = "0"
ATTENTION = "attention"
DIGITS = 4  # rounding of M, R, s2 and shares in the key
SALT_ENV = "BOT_DAY_ID_SALT"
SALT_FILE = HERE / ".id_salt"
SALT_BYTES = 16
#: card orders for the page (it picks one per participant); form 1 is the items.json order
N_FORMS = 6
FIRST_ATTENTION_POSITION = 3  # no attention check among the first 3 cards
MAX_FORM_TRIES = 10_000
ENGINE_FILES = (
    "src/mcp_security/behaviour/engine.py",
    "src/mcp_security/behaviour/memory.py",
    "src/mcp_security/behaviour/policy.py",
)
#: engine dimension -> the card row that shows it (risky order and the skipped hello have no
#: row of their own: they go to the closest one)
ROW_MAP: dict[str, str] = {
    "calls_last_hour": "actions",
    "burst": "actions",
    "session_length": "hours",
    "time_of_day": "hours",
    "same_call_10m": "repeats",
    "writes_last_hour": "changes",
    "sequence": "changes",
    "assets_last_hour": "projects",
    "asset": "projects",
    "many_assets": "projects",
    "tool": "kinds",
    "request_too_big": "upload",
    "network": "connection",
    "client": "connection",
    "protocol_skip": "connection",
}


# ── the engine's view ────────────────────────────────────────────────────────────────────
def load_or_score(
    world: dict[str, list[tuple]], meta: dict, cache: Path | None
) -> dict[tuple[str, int], DayScore]:
    """The shipped engine's day scores, from ``cache`` when it was made for the same world."""
    if cache and cache.exists():
        with cache.open("rb") as fh:
            saved = pickle.load(fh)  # our own scratch file, written below
        if all(saved.get(k) == v for k, v in meta.items()):
            return saved["scores"]
    scores = score_world(world, shipped_config(world, meta["design"]))
    if cache:
        with cache.open("wb") as fh:
            pickle.dump({**meta, "scores": scores}, fh)
    return scores


def agent_days(
    scores: dict[tuple[str, int], DayScore],
    places: dict[tuple[str, int], ListPlace],
    labels: dict[tuple[str, int], tuple[set, set]],
    profiles: dict[str, AgentProfile],
    facts: dict[str, dict[int, DayFacts]],
) -> list[AgentDay]:
    """Every scored agent-day with its labels, list place and history length."""
    out = []
    for (agent, day), score in sorted(scores.items()):
        tags, grays = labels.get((agent, day), (set(), set()))
        place = places[(agent, day)]
        today = facts[agent].get(day, DayFacts())
        out.append(
            AgentDay(
                agent=agent,
                day=day,
                role=profiles[agent].role,
                multiplier=score.multiplier,
                risk=score.risk,
                strongest=score.strongest,
                second=score.second,
                above_ordinary=score.above_ordinary,
                rank=place.rank,
                chance=place.chance,
                tags=tuple(sorted(tags)),
                gray_kinds=tuple(sorted({g.split(":")[0] for g in grays})),
                history_days=len(history_of(facts[agent], day).days),
                org_event=org_event_name(day, tags),
                actions=today.calls,
                local_dates=tuple(sorted(today.local_dates)),
                latent_cause=latent_cause(profiles[agent], facts[agent], day, tags),
            )
        )
    return out


# ── cards ────────────────────────────────────────────────────────────────────────────────
def scored_card(
    day: AgentDay, card_id: str, profile: AgentProfile, facts: dict[int, DayFacts]
) -> dict:
    """The participant's card for one agent-day."""
    tags = set(day.tags)
    return {
        "id": card_id,
        "who": who_text(day.role),
        "day": WEEKDAYS[day.weekday],
        "calendar": calendar_note(profile, day.day, tags),
        "company": company_note(day.day, tags),
        "rows": card_rows(facts.get(day.day, DayFacts()), history_of(facts, day.day)),
    }


def key_entry(day: AgentDay, stratum: str | None) -> dict:
    """What the key keeps about a scored card."""
    return {
        "stratum": stratum,
        "gray_kind": day.gray_kind,
        "tags": list(day.tags),
        "org_event": day.org_event,
        "agent": day.agent,
        "role": day.role,
        "day": day.day,
        "weekday": WEEKDAYS[day.weekday],
        "M": round(day.multiplier, DIGITS),
        "R": round(day.risk, DIGITS),
        "strongest": day.strongest,
        "s2": round(day.second, DIGITS),
        "above_ordinary": list(day.above_ordinary),
        "listed": day.listed,
        "list_rank": day.rank,
        "list_chance": day.chance,
        "history_days": day.history_days,
        "latent_cause": day.latent_cause,
        "attention": None,
    }


def attention_entry(expected: str) -> dict:
    """The key of a hand-built attention card."""
    return {
        "stratum": ATTENTION,
        "gray_kind": None,
        "tags": [],
        "org_event": None,
        "agent": None,
        "role": None,
        "day": None,
        "weekday": None,
        "M": None,
        "R": None,
        "strongest": None,
        "s2": None,
        "above_ordinary": [],
        "listed": None,
        "list_rank": None,
        "list_chance": None,
        "history_days": None,
        "latent_cause": None,
        "attention": expected,
    }


def attention_placed(order: list[dict], attention_ids: set[str]) -> bool:
    """No attention check among the first cards, and one in the second half."""
    positions = [i for i, card in enumerate(order) if card["id"] in attention_ids]
    half = len(order) // 2
    return min(positions) >= FIRST_ATTENTION_POSITION and max(positions) >= half


def card_forms(
    cards: list[dict], groups: dict[str, str], attention_ids: set[str], rng: random.Random
) -> list[list[dict]]:
    """``N_FORMS`` different card orders, each with no two neighbours from one stratum and the
    attention checks placed by ``attention_placed``; the first is the items.json order."""
    forms: list[list[dict]] = []
    seen: set[tuple[str, ...]] = set()
    for _ in range(MAX_FORM_TRIES):
        order = shuffle_apart(cards, lambda c: groups[c["id"]], rng)
        ids = tuple(c["id"] for c in order)
        if ids in seen or not attention_placed(order, attention_ids):
            continue
        seen.add(ids)
        forms.append(order)
        if len(forms) == N_FORMS:
            return forms
    raise ValueError(f"only {len(forms)} of {N_FORMS} card orders found")


def pair_entry(pair: Pair, ids: dict[tuple[str, int], str], shown: list[AgentDay]) -> dict:
    """What the key keeps about a pair."""
    gray = pair.gray
    return {
        "type": pair.pair_type,
        "day": pair.preferred.day,
        "engine_prefers": ids[pair.preferred.key],
        "gray_card": ids[gray.key] if gray else None,
        "M": {ids[d.key]: round(d.multiplier, DIGITS) for d in shown},
        "margin": round(pair.margin, DIGITS),
        "tie_on_M": pair.tie_on_m,
        "close": pair.close,
        "min_margin": MIN_MARGIN,
        "cards": {ids[d.key]: key_entry(d, None) for d in shown},
    }


def build_bank(
    picks: list[Pick],
    pairs: list[Pair],
    profiles: dict[str, AgentProfile],
    facts: dict[str, dict[int, DayFacts]],
    rng: random.Random,
    id_parts: tuple,
) -> tuple[dict, dict]:
    """``(items, key)`` minus the key's engine block. ``id_parts`` (with the secret salt) only
    feed the ids; ``rng`` sets every order."""
    taken: set[str] = set()

    def new_id(prefix: str, *parts: object) -> str:
        return opaque_id(prefix, (*id_parts, *parts), taken)

    practice, practice_key = [], {}
    for name in PRACTICE_NAMES:
        card = hand_card(name, new_id("c", "hand", name))
        practice.append(card)
        practice_key[card["id"]] = {"name": name, "feedback": card["feedback"]}
    cards, groups, card_key, attention_ids = [], {}, {}, set()
    for pick in picks:
        d = pick.day
        card = scored_card(d, new_id("c", d.agent, d.day), profiles[d.agent], facts[d.agent])
        cards.append(card)
        groups[card["id"]] = pick.stratum
        card_key[card["id"]] = key_entry(d, pick.stratum)
    for name in ATTENTION_NAMES:
        card = hand_card(name, new_id("c", "hand", name))
        cards.append(card)
        groups[card["id"]] = ATTENTION  # the two checks are never neighbours either
        attention_ids.add(card["id"])
        card_key[card["id"]] = attention_entry(HAND_CARDS[name]["expected"])
    forms = card_forms(cards, groups, attention_ids, rng)
    cards = forms[0]
    card_key = {c["id"]: card_key[c["id"]] for c in cards}
    pair_items, pair_key = [], {}
    for pair in pairs:
        shown = [pair.preferred, pair.other]
        rng.shuffle(shown)
        ids = {d.key: new_id("c", d.agent, d.day) for d in shown}
        pair_id = new_id("p", *(ids[d.key] for d in shown))
        pair_cards = [scored_card(d, ids[d.key], profiles[d.agent], facts[d.agent]) for d in shown]
        pair_items.append({"id": pair_id, "cards": pair_cards})
        pair_key[pair_id] = pair_entry(pair, ids, shown)
    rng.shuffle(pair_items)
    pair_key = {p["id"]: pair_key[p["id"]] for p in pair_items}
    hand = [*practice, *(c for c in cards if c["id"] in attention_ids)]
    real = [c for c in cards if c["id"] not in attention_ids]
    shared = shared_novelty(hand, real + [c for p in pair_items for c in p["cards"]])
    if shared:
        raise ValueError(f"hand-built cards share phrases with simulator cards: {sorted(shared)}")
    items = {
        "bank_version": BANK_VERSION,
        "rows": [
            {"id": row_id, "label": label, "shown": row_id not in HIDDEN_ROWS}
            for row_id, label in ROWS
        ],
        "text": bank_text(),
        "practice": practice,
        "cards": cards,
        "forms": [
            {"id": f"f{n}", "cards": [c["id"] for c in form]}
            for n, form in enumerate(forms, start=1)
        ],
        "pairs": pair_items,
    }
    key = {
        "bank_version": BANK_VERSION,
        "row_map": ROW_MAP,
        "hidden_rows": sorted(HIDDEN_ROWS),
        "strata": {s: {"name": STRATUM_NAMES[s], "count": n} for s, n in STRATA.items()},
        "pair_types": PAIR_TYPES,
        "cards": card_key,
        "pairs": pair_key,
        "practice": practice_key,
    }
    return items, key


def list_context(days: list[AgentDay]) -> dict:
    """What the real daily list holds (the cards are a purposive sample, not this mix): the
    share of listed agent-days by category, and how often the engine lists each gray kind."""
    listed: Counter = Counter()
    for d in days:
        listed[d.category] += d.chance
    total = sum(listed.values())
    by_kind: dict[str, list[float]] = defaultdict(list)
    for d in days:
        if d.category == GRAY:
            by_kind[d.gray_kind or ""].append(d.chance)
    return {
        "listed_agent_days": round(total, DIGITS),
        "list_composition": {
            c: round(listed[c] / total, DIGITS) if total else None for c in (GRAY, CHANGE, ORDINARY)
        },
        "gray_kind_listed_share": {
            kind: round(sum(v) / len(v), DIGITS) for kind, v in sorted(by_kind.items())
        },
        "gray_kind_days": {kind: len(v) for kind, v in sorted(by_kind.items())},
    }


def id_salt() -> str:
    """The secret that salts the ids: ``$BOT_DAY_ID_SALT``, else ``SALT_FILE`` (made once)."""
    salt = os.environ.get(SALT_ENV)
    if salt:
        return salt
    if SALT_FILE.exists():
        return SALT_FILE.read_text().strip()
    salt = secrets.token_hex(SALT_BYTES)
    SALT_FILE.write_text(salt + "\n")
    print(f"made a new id salt in {SALT_FILE} (keep it; key.json holds a copy)", flush=True)
    return salt


# ── provenance ───────────────────────────────────────────────────────────────────────────
def git_sha() -> str | None:
    """HEAD of the repository, or ``None`` outside git."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def engine_uncommitted() -> bool | None:
    """Whether the engine files differ from HEAD (the git sha alone does not pin them)."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--", *ENGINE_FILES],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return bool(result.stdout.strip())


def engine_digest() -> str:
    """sha256 of the engine files as they ran."""
    digest = hashlib.sha256()
    for name in ENGINE_FILES:
        digest.update((REPO / name).read_bytes())
    return digest.hexdigest()


def pin_hash_seed(argv: list[str]) -> None:
    """Re-run this script under ``PYTHONHASHSEED=HASH_SEED`` unless it already runs under it."""
    if os.environ.get("PYTHONHASHSEED") == HASH_SEED:
        return
    env = {**os.environ, "PYTHONHASHSEED": HASH_SEED}
    os.execve(sys.executable, [sys.executable, str(Path(__file__).resolve()), *argv], env)


# ── main ─────────────────────────────────────────────────────────────────────────────────
def write_outputs(out_dir: Path, items: dict, key: dict) -> None:
    """items.json, key.json and cards.txt (rendered from items.json alone)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "items.json").write_text(json.dumps(items, indent=1, ensure_ascii=False) + "\n")
    (out_dir / "key.json").write_text(json.dumps(key, indent=1, ensure_ascii=False) + "\n")
    (out_dir / "cards.txt").write_text(render_text(items))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="world seed")
    parser.add_argument("--agents", type=int, default=DEFAULT_AGENTS)
    parser.add_argument("--profile", default=DEFAULT_PROFILE, choices=sorted(PROFILES))
    parser.add_argument("--out-dir", type=Path, default=HERE)
    parser.add_argument(
        "--cache",
        type=Path,
        default=None,
        help="scratch pickle of the engine's day scores (reused when made for the same world "
        "and the same engine files)",
    )
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="stop unless the engine files match git HEAD (use for the bank people will answer)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Build the world, score it, pick the cards and pairs, and write the three files."""
    argv = sys.argv[1:] if argv is None else argv
    pin_hash_seed(argv)
    args = parse_args(argv)
    if args.require_clean and engine_uncommitted() is not False:
        raise SystemExit("the engine files differ from git HEAD: commit them first")
    t0 = time.time()
    world, _roles, _org = build_world(args.agents, args.seed, PROFILES[args.profile])
    print(f"world: {len(world)} agents ({time.time() - t0:.0f}s)", flush=True)
    meta = {
        "seed": args.seed,
        "agents": args.agents,
        "profile": args.profile,
        "design": DESIGN,
        "hash_seed": HASH_SEED,
        "engine_files_sha256": engine_digest(),
    }
    scores = load_or_score(world, meta, args.cache)
    print(f"scored {len(scores):,} agent-days ({time.time() - t0:.0f}s)", flush=True)
    places = daily_list(scores, LIST_SIZE)
    labels = day_labels(world)
    profiles = agent_profiles(args.agents, args.seed, PROFILES[args.profile])
    facts = {aid: collect_facts(rows, profiles[aid].tz) for aid, rows in world.items()}
    days = agent_days(scores, places, labels, profiles, facts)
    order_parts = (BANK_VERSION, args.seed, args.profile, args.agents)
    rng = random.Random("|".join(str(p) for p in order_parts))
    salt = id_salt()
    usage = Usage()
    picks = select_cards(days, rng, usage)
    pairs = select_pairs(days, rng, usage)
    items, key = build_bank(picks, pairs, profiles, facts, rng, (salt, *order_parts))
    key["id_salt"] = salt
    key["context"] = list_context(days)
    key["engine"] = {
        "design": DESIGN,
        "git_sha": git_sha(),
        "engine_uncommitted": engine_uncommitted(),
        "engine_files_sha256": engine_digest(),
        "profile": args.profile,
        "agents": args.agents,
        "seed": args.seed,
        "python_hash_seed": HASH_SEED,
        "scored_days": [EVAL_FROM, N_DAYS - 1],
        "list_size": LIST_SIZE,
        "ranking": "M, then s2; ties at the cut broken at random (only sure picks used)",
        "usable_day": "all actions on the owner's own calendar date of the server's day",
    }
    key = {"bank_version": key.pop("bank_version"), "engine": key.pop("engine"), **key}
    write_outputs(args.out_dir, items, key)
    print(f"wrote {args.out_dir} ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
