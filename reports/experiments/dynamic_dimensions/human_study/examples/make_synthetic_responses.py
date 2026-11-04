"""Write SYNTHETIC response documents for the committed item bank, to show the analysis path.

Nothing here is data from a person. Every document says ``"synthetic": true`` and every pid
starts with ``synthetic-``, so the analysis prints a banner on the report. The answers are
random (seeded), apart from a few made-up behaviours that exercise the quality screen: most
raters answer the attention checks as the rule expects, one fails the wild check, one stops
early, and two "Claude" runs answer as a separate group. Card order comes from one of the
bank's card orders (``forms``); each pair's shown order is shuffled.

Run:
    uv run python reports/experiments/dynamic_dimensions/human_study/examples/\\
make_synthetic_responses.py [--out FILE] [--seed 3]
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
DEFAULT_OUT = HERE / "synthetic_responses.json"
DEFAULT_SEED = 3
N_PEOPLE = 10
N_CLAUDE = 2
LEVELS = (0, 1, 2)
TECH = ("no", "tech", "security")
AI_USE = ("never", "sometimes", "often")
EXPECTED = {"normal": (0, 0), "wild": (2, 2)}  # attention card -> (unusual, check)
FAIL_WILD = (0, 0)  # one synthetic rater calls the wild card normal
TICKS = 2  # rows a rater ticks when a card is unusual
CARD_MS = (15_000, 70_000)
PAIR_MS = (30_000, 120_000)
STOP_AFTER = 7  # the rater who stops early answers this many cards
START = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
CLAUDE_MODEL = "synthetic-claude-run"


def card_answer(
    rng: random.Random, expected: tuple[int, int] | None, shown: list[str], order: int
) -> dict:
    """One card answer; an attention card gets ``expected``, any other a random one."""
    unusual, check = expected or (rng.choice(LEVELS), rng.choice(LEVELS))
    return {
        "unusual": unusual,
        "check": check,
        "stood_out": rng.sample(shown, TICKS) if unusual else [],
        "ms": rng.randint(*CARD_MS),
        "order": order,
    }


def document(
    pid: str,
    items: dict,
    key: dict,
    rng: random.Random,
    rater: str = "human",
    fail_wild: bool = False,
    stop_after: int | None = None,
) -> dict:
    """One synthetic response document in the documented format."""
    form = rng.choice(items["forms"])
    shown = [row["id"] for row in items["rows"] if row["shown"]]
    cards = {}
    for order, card_id in enumerate(form["cards"]):
        if stop_after is not None and order >= stop_after:
            break
        kind = key["cards"][card_id]["attention"]
        expected = FAIL_WILD if fail_wild and kind == "wild" else EXPECTED.get(kind)
        cards[card_id] = card_answer(rng, expected, shown, order)
    pairs = {}
    if stop_after is None:
        for order, pair in enumerate(rng.sample(items["pairs"], len(items["pairs"]))):
            ids = [card["id"] for card in pair["cards"]]
            pairs[pair["id"]] = {
                "chose": rng.choice(ids),
                "top": rng.choice(ids),
                "ms": rng.randint(*PAIR_MS),
                "order": order,
            }
    started = START + timedelta(hours=rng.randint(0, 200))
    minutes = sum(a["ms"] for a in cards.values()) + sum(a["ms"] for a in pairs.values())
    finished = started + timedelta(milliseconds=minutes) if stop_after is None else None
    doc = {
        "pid": pid,
        "synthetic": True,
        "bank_version": items["bank_version"],
        "form": form["id"],
        "started": started.isoformat(),
        "finished": finished.isoformat() if finished else None,
        "background": {"tech": rng.choice(TECH), "ai_use": rng.choice(AI_USE)},
        "cards": cards,
        "pairs": pairs,
        "mobile": rng.random() < 0.3,
        "rater": rater,
    }
    if rater == "claude":
        doc["model"] = CLAUDE_MODEL
    return doc


def synthetic_documents(items: dict, key: dict, seed: int) -> list[dict]:
    """``N_PEOPLE`` people (one fails the wild check, one stops early) and ``N_CLAUDE`` runs."""
    rng = random.Random(seed)
    docs = [document(f"synthetic-h{i:02d}", items, key, rng) for i in range(N_PEOPLE)]
    docs.append(document("synthetic-fails-wild", items, key, rng, fail_wild=True))
    docs.append(document("synthetic-stopped", items, key, rng, stop_after=STOP_AFTER))
    docs += [
        document(f"synthetic-claude-{i}", items, key, rng, rater="claude") for i in range(N_CLAUDE)
    ]
    return docs


def main(argv: list[str] | None = None) -> None:
    """Read the committed items.json and key.json; write the synthetic responses."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args(argv)
    items = json.loads((STUDY / "items.json").read_text())
    key = json.loads((STUDY / "key.json").read_text())
    docs = synthetic_documents(items, key, args.seed)
    args.out.write_text(json.dumps(docs, indent=1) + "\n")
    print(f"wrote {len(docs)} synthetic documents to {args.out}")


if __name__ == "__main__":
    main()
