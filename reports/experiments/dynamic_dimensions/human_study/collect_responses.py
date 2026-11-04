"""Gather Bot Day Check answers into the one JSON list that ``analyse_responses.py`` reads.

Answers arrive three ways:

- the web page's shared store: an export of the ``responses`` collection, where each viewer's
  document holds ``{"runs": {pid: response document}, "updated": ...}`` (one viewer can hold
  several runs when the study is run in person on one device);
- answer codes: people who cannot write to the store copy a code from the last screen and send
  it by email or message. A code is ``BDC1-`` + base64url(UTF-8 JSON of the response document)
  + ``.``; line breaks inside a pasted code are ignored;
- Claude raters: runs answered from ``cards.txt``, where card n is ``items.json`` ``cards[n-1]``
  and, in pair n, Agent A is ``pairs[n-1].cards[0]`` and Agent B is ``cards[1]``.

Run from the repository root::

    uv run python reports/experiments/dynamic_dimensions/human_study/collect_responses.py \\
        --store store_export.json --codes codes.txt \\
        --claude reports/experiments/dynamic_dimensions/human_study/claude_ratings.json \\
        --out responses.json
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import TypeGuard

HERE = Path(__file__).resolve().parent
DEFAULT_ITEMS = HERE / "items.json"
CODE_PREFIX = "BDC1-"
CODE_END = "."
BASE64URL = re.compile(r"[A-Za-z0-9_-]")
CLAUDE = "claude"
#: a response document always carries these fields
DOCUMENT_FIELDS = ("pid", "cards")


class CollectError(ValueError):
    """An input that cannot be turned into response documents."""


# --- answer codes ------------------------------------------------------------------------------


def encode_answer_code(document: Mapping) -> str:
    """Return the answer code the web page shows for ``document`` (used by tests)."""
    raw = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return CODE_PREFIX + body + CODE_END


def decode_answer_code(code: str) -> dict:
    """Decode one answer code into its response document.

    Whitespace inside the code (a line break added by an email program) is ignored, and the
    closing ``.`` may be missing.

    Raises:
        CollectError: If the code is not ``BDC1-`` + base64url JSON of a response document.
    """
    text = "".join(code.split())
    if not text.startswith(CODE_PREFIX):
        raise CollectError(f"an answer code starts with {CODE_PREFIX}")
    body = text[len(CODE_PREFIX) :].removesuffix(CODE_END)
    try:
        raw = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
        document = json.loads(raw.decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CollectError(f"unreadable answer code ({error})") from error
    if not is_response_document(document):
        raise CollectError("the answer code does not hold a response document")
    return document


def find_answer_codes(text: str) -> list[str]:
    """Return every answer code in a block of pasted text, in order.

    A code runs from ``BDC1-`` to its closing ``.``; whitespace inside it is skipped, so a code
    an email program wrapped over several lines is still found whole. A code with no closing
    ``.`` ends at the first character that is neither base64url nor whitespace.
    """
    codes = []
    for chunk in text.split(CODE_PREFIX)[1:]:
        body = []
        for char in chunk:
            if char.isspace():
                continue
            if not BASE64URL.fullmatch(char):
                break
            body.append(char)
        if body:
            codes.append(CODE_PREFIX + "".join(body) + CODE_END)
    return codes


# --- shared-store exports ----------------------------------------------------------------------


def is_response_document(node: object) -> TypeGuard[dict]:
    """True when ``node`` looks like one participant's response document."""
    return isinstance(node, dict) and all(field in node for field in DOCUMENT_FIELDS)


def documents_in(node: object) -> list[dict]:
    """Return every response document inside an export, whatever wraps it.

    Store exports nest documents under row objects, ``data`` fields and ``runs`` maps; rather
    than tie this to one export shape, the walk keeps every object that has a ``pid`` and
    ``cards`` and does not descend into it.
    """
    if is_response_document(node):
        return [node]
    found: list[dict] = []
    if isinstance(node, Mapping):
        for value in node.values():
            found.extend(documents_in(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(documents_in(value))
    return found


# --- Claude raters -----------------------------------------------------------------------------


def _position(raw_id: object, kind: str, count: int) -> int:
    """Turn "Card 7" / "7" into the 0-based index 6, checked against ``count``."""
    match = re.search(r"\d+", str(raw_id))
    if not match:
        raise CollectError(f"{kind} id {raw_id!r} has no number")
    index = int(match.group()) - 1
    if not 0 <= index < count:
        raise CollectError(f"{kind} {index + 1} is not in the bank (1-{count})")
    return index


def _row_ids(stood_out: Iterable[str], label_to_id: Mapping[str, str]) -> list[str]:
    ids = []
    for label in stood_out:
        row_id = label_to_id.get(label.strip().lower())
        if row_id is None:
            raise CollectError(f"unknown line {label!r} in stood_out")
        ids.append(row_id)
    return list(dict.fromkeys(ids))


def claude_document(run: Mapping, number: int, items: Mapping, model: str) -> dict:
    """Turn one Claude run answered from ``cards.txt`` into a response document.

    ``run`` is ``{"started", "finished", "cards": [{"id": "Card n", "unusual", "check",
    "stood_out": [labels]}], "pairs": [{"id": "Pair n", "chose": "A" | "B"}]}``; a run with no
    ``finished`` time counts as stopped early. Cards are numbered as in ``cards.txt``
    (which is ``items.json`` order); every pair shows Agent A first.
    """
    cards = items["cards"]
    pairs = items["pairs"]
    label_to_id = {}
    for row in items["rows"]:
        label_to_id[row["label"].lower()] = row["id"]
        label_to_id[row["id"].lower()] = row["id"]
    card_answers = {}
    for answer in run["cards"]:
        index = _position(answer["id"], "card", len(cards))
        card_answers[cards[index]["id"]] = {
            "unusual": answer["unusual"],
            "check": answer["check"],
            "stood_out": _row_ids(answer.get("stood_out") or (), label_to_id),
            "order": index,
        }
    pair_answers = {}
    for answer in run["pairs"]:
        index = _position(answer["id"], "pair", len(pairs))
        agent_a, agent_b = (card["id"] for card in pairs[index]["cards"])
        chose = str(answer["chose"]).strip().upper().removeprefix("AGENT ").strip()
        if chose not in ("A", "B"):
            raise CollectError(f"pair {index + 1}: choice {answer['chose']!r} is not A or B")
        pair_answers[pairs[index]["id"]] = {
            "chose": agent_a if chose == "A" else agent_b,
            "top": agent_a,
            "order": index,
        }
    return {
        "pid": f"claude-run-{number}",
        "bank_version": items["bank_version"],
        "started": run.get("started"),
        "finished": run.get("finished"),
        "background": {},
        "cards": card_answers,
        "pairs": pair_answers,
        "mobile": None,
        "rater": CLAUDE,
        "model": model,
    }


# --- merge -------------------------------------------------------------------------------------


def _answered(document: Mapping) -> int:
    return len(document.get("cards") or {}) + len(document.get("pairs") or {})


def merge_documents(documents: Iterable[dict]) -> list[dict]:
    """Keep one document per pid: the most answered one (a code can repeat a stored run)."""
    best: dict[str, dict] = {}
    for document in documents:
        pid = str(document.get("pid"))
        if pid not in best or _answered(document) > _answered(best[pid]):
            best[pid] = document
    return list(best.values())


def _read_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def collect(
    stores: Sequence[Path], codes: Sequence[Path], claude: Sequence[Path], items: Mapping
) -> list[dict]:
    """Read every input and return the merged response documents."""
    documents: list[dict] = []
    for path in stores:
        documents.extend(documents_in(_read_json(path)))
    for path in codes:
        text = path.read_text(encoding="utf-8")
        documents.extend(decode_answer_code(code) for code in find_answer_codes(text))
    for path in claude:
        saved = _read_json(path)
        if not isinstance(saved, Mapping) or "runs" not in saved:
            raise CollectError(f"{path}: expected {{'model': ..., 'runs': [...]}}")
        model = str(saved.get("model") or "")
        for number, run in enumerate(saved["runs"], start=1):
            documents.append(claude_document(run, number, items, model))
    return merge_documents(documents)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Gather Bot Day Check answers into one list.")
    parser.add_argument(
        "--store",
        type=Path,
        action="append",
        default=[],
        help="an export of the page's responses collection (repeatable)",
    )
    parser.add_argument(
        "--codes",
        type=Path,
        action="append",
        default=[],
        help="a text file of pasted answer codes (repeatable)",
    )
    parser.add_argument(
        "--claude",
        type=Path,
        action="append",
        default=[],
        help="saved Claude runs, {'model', 'runs'} (repeatable)",
    )
    parser.add_argument("--items", type=Path, default=DEFAULT_ITEMS)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if not (args.store or args.codes or args.claude):
        parser.error("give at least one of --store, --codes or --claude")
    items = _read_json(args.items)
    if not isinstance(items, Mapping):
        parser.error("--items must be the items.json object")
    documents = collect(args.store, args.codes, args.claude, items)
    args.out.write_text(json.dumps(documents, indent=1, ensure_ascii=False) + "\n", "utf-8")
    kinds = {kind: sum(d.get("rater") == kind for d in documents) for kind in ("human", CLAUDE)}
    print(f"wrote {args.out}: {kinds['human']} people, {kinds[CLAUDE]} Claude runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
