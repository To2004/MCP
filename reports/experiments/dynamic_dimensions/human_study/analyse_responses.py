"""Analyse the "Bot Day Check" human study of the dynamic (behaviour) layer.

People judged one AI agent's day against that agent's own usual days, without ever seeing the
engine's score. Claude runs answer the same survey and are analysed as a separate group: they
never count toward the human majority. This script joins the answers with the private key (the
engine's day multiplier M, whether the day was on that day's top-4 review list, the stratum the
card was drawn from, the dimension that set the day's maximum) and writes a markdown report and
a JSON file for the paper.

The 16 scored cards are a purposive sample: strata were chosen to test where the engine is
right and where it is wrong, so the headline is descriptive, per stratum and per card, "for these
cards". Spearman's rho of M against people's answers depends on that mix and is secondary. Small
samples (10-20 people): the stratum shares carry a two-way bootstrap interval that resamples
raters AND cards (cards within their stratum) and state the number of people, cards and answers;
background groups and Claude runs get point values and n only. There are no p-values.
Agreement among people is Krippendorff's ordinal alpha (Fleiss' kappa beside it).

The attention rule is pre-registered: the plainly normal card passes with "normal for it"; the
wildly unusual card passes with "a bit" or "very unusual" AND "maybe" or "yes" to a check. A
person is kept after passing both. The report also shows the stratum shares with no attention
screen at all.

Run:
    uv run python reports/experiments/dynamic_dimensions/human_study/analyse_responses.py \\
        --responses responses.json \\
        --key reports/experiments/dynamic_dimensions/human_study/key.json \\
        --items reports/experiments/dynamic_dimensions/human_study/items.json \\
        --out results.md --json-out results.json
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from analysis_stats import (  # noqa: E402
    INTERVAL_LEVEL,
    NOMINAL,
    NOT_AVAILABLE,
    ORDINAL,
    Cells,
    agreement_words,
    average_ranks,
    bootstrap_interval,
    fleiss_kappa,
    krippendorff_alpha,
    pooled_share,
    quantile,
    spearman,
)

__all__ = ["average_ranks", "bootstrap_interval", "pooled_share", "quantile"]

# --- answers and raters ------------------------------------------------------------------------

ANSWER_LEVELS: tuple[int, ...] = (0, 1, 2)
UNUSUAL_WORDS = ("normal for it", "a bit unusual", "very unusual")
CHECK_WORDS = ("no", "maybe", "yes")
NORMAL_LEVEL = 0
FLAG_LEVEL = 1  # "a bit / very unusual", "maybe / yes, check it"
STRICT_LEVEL = 2  # "very unusual", "yes, check it"
CARD_FIELDS = ("unusual", "check")
QUESTION_WORDS: Mapping[str, str] = {"unusual": "how unusual", "check": "would check"}
ATTENTION_KINDS = ("normal", "wild")
#: the pre-registered pass rule, in words
ATTENTION_RULE_WORDS: Mapping[str, str] = {
    "normal": "'normal for it'",
    "wild": "'a bit' or 'very unusual', and 'maybe' or 'yes' to a check",
}
NOT_RECORDED = "not recorded"

HUMAN = "human"
CLAUDE = "claude"
RATER_KINDS = (HUMAN, CLAUDE)
DEFAULT_RATER_KIND = HUMAN
MISSING_PID_PREFIX = "no-pid-"
TECH_GROUPS: Mapping[str, str] = {
    "no": "Non-technical",
    "tech": "Technical",
    "security": "Security",
}
UNKNOWN_GROUP = "unknown"

# --- the design --------------------------------------------------------------------------------

STRATUM_WORDS: Mapping[str, str] = {
    "A": "listed gray (caught)",
    "B": "listed ordinary (false alarm)",
    "C": "gray not listed (missed)",
    "D": "benign life or company change",
    "E": "plain ordinary",
}
STRATA = tuple(STRATUM_WORDS)
LISTED_STRATA = ("A", "B")
#: "A", "A_caught", "A: listed gray" all mean stratum A; "benign" does not mean B.
STRATUM_PATTERN = re.compile(r"^([A-E])(?![A-Za-z0-9])")

# --- statistics --------------------------------------------------------------------------------

DEFAULT_DRAWS = 2_000
DEFAULT_SEED = 7
TOP_LISTED = 3  # rows and cards named in the "most ticked" columns
#: the reason measure uses only cards where the engine's strongest dimension means something
REASON_MIN_M = 2.0
#: a pair whose preferred card has M below this times the other's is "close" (a coin flip)
MIN_CLEAR_MARGIN = 1.25

# --- quality -----------------------------------------------------------------------------------

SPEEDER_MEDIAN_CARD_MS = 3_000  # flagged (not excluded) when a person's median card is faster
MS_PER_SECOND = 1_000
SECONDS_PER_MINUTE = 60
PERCENT = 100

EXCLUDE_KIND = "unknown rater kind"
EXCLUDE_VERSION = "different bank version"
EXCLUDE_DUPLICATE = "duplicate submission (the fuller one was kept)"
EXCLUDE_EMPTY = "no answers"
EXCLUDE_FAILED = "failed an attention check"
EXCLUDE_UNVERIFIED = "did not reach both attention checks"
#: Reasons counted per rater kind; EXCLUDE_KIND has no kind and is counted on its own.
EXCLUSION_ORDER = (
    EXCLUDE_VERSION,
    EXCLUDE_DUPLICATE,
    EXCLUDE_EMPTY,
    EXCLUDE_FAILED,
    EXCLUDE_UNVERIFIED,
)
ATTENTION_PASS = "pass"
ATTENTION_FAIL = "fail"
ATTENTION_MISSING = "missing"


class StudyInputError(ValueError):
    """The key, the item bank or the responses file is malformed or they do not match."""


# --- public data model -------------------------------------------------------------------------


@dataclass(frozen=True)
class CardKey:
    """What the private key says about one card."""

    card_id: str
    stratum: str | None
    attention: str | None
    multiplier: float | None
    listed: bool
    list_rank: int | None
    strongest: str | None
    expected_row: str | None
    gray_kind: str | None
    tags: tuple[str, ...]
    org_event: str | None
    latent_cause: str | None = None

    @property
    def is_scored(self) -> bool:
        """True for the 16 simulator cards, False for the two hand-built attention checks."""
        return self.attention is None


@dataclass(frozen=True)
class PairKey:
    """What the private key says about one daily choice."""

    pair_id: str
    pair_type: str
    card_ids: tuple[str, str]
    engine_prefers: str
    gray_card: str | None
    multipliers: Mapping[str, float]
    margin: float | None = None
    close: bool = False


@dataclass(frozen=True)
class Study:
    """The item bank joined with its private key."""

    bank_version: str
    engine: Mapping[str, object]
    row_ids: tuple[str, ...]
    row_labels: Mapping[str, str]
    row_dimensions: Mapping[str, tuple[str, ...]]
    cards: Mapping[str, CardKey]
    pairs: Mapping[str, PairKey]
    hidden_rows: frozenset[str] = frozenset()
    practice_ids: frozenset[str] = frozenset()
    context: Mapping[str, object] | None = None

    def cards_in(self, strata: Iterable[str]) -> list[str]:
        """Scored card ids in the given strata, in item-bank order."""
        wanted = set(strata)
        return [c.card_id for c in self.cards.values() if c.is_scored and c.stratum in wanted]

    def stratum_groups(self, strata: Iterable[str]) -> list[list[str]]:
        """One list of card ids per non-empty stratum: the units resampled within."""
        groups = [self.cards_in((stratum,)) for stratum in strata]
        return [group for group in groups if group]

    @property
    def scored_cards(self) -> list[str]:
        """All scored card ids, in item-bank order."""
        return self.cards_in(STRATA)

    @property
    def attention_cards(self) -> list[CardKey]:
        """The hand-built attention checks."""
        return [card for card in self.cards.values() if not card.is_scored]


@dataclass(frozen=True)
class CardAnswer:
    """One rater's answer to one card; a field the rater did not give is None."""

    unusual: int | None
    check: int | None
    stood_out: tuple[str, ...]
    ms: int | None
    order: int | None = None

    @property
    def is_complete(self) -> bool:
        """Both questions answered."""
        return self.unusual is not None and self.check is not None


@dataclass(frozen=True)
class PairAnswer:
    """One rater's choice in one pair."""

    chose: str
    top: str | None
    ms: int | None
    order: int | None = None


@dataclass(frozen=True)
class Rater:
    """One response document, parsed and validated."""

    pid: str
    kind: str
    bank_version: str | None
    tech: str
    ai_use: str
    started: datetime | None
    finished: datetime | None
    mobile: bool | None
    cards: Mapping[str, CardAnswer]
    pairs: Mapping[str, PairAnswer]
    model: str | None = None
    synthetic: bool = False  # the document says "synthetic": true (examples, tests)

    @property
    def key(self) -> str:
        """Unique id across rater kinds (a human and a Claude run may share a pid)."""
        return f"{self.kind}:{self.pid}"

    @property
    def answer_count(self) -> int:
        """Cards and pairs answered."""
        return len(self.cards) + len(self.pairs)


@dataclass(frozen=True)
class Screened:
    """A rater with the outcome of the quality screen."""

    rater: Rater
    complete: bool
    attention: Mapping[str, str]
    exclusion: str | None
    minutes: float | None
    median_card_seconds: float | None


@dataclass(frozen=True)
class Estimate:
    """A point estimate with its two-way bootstrap interval and its n."""

    value: float | None
    low: float | None
    high: float | None
    raters: int
    items: int
    answers: int
    draws: int


@dataclass(frozen=True)
class ShareMetric:
    """A share of answers over the cards of some strata."""

    name: str
    label: str
    field_name: str
    strata: tuple[str, ...]
    predicate: str


def _is_normal(value: int) -> bool:
    return value == NORMAL_LEVEL


def _is_flagged(value: int) -> bool:
    return value >= FLAG_LEVEL


def _is_strict(value: int) -> bool:
    return value >= STRICT_LEVEL


def _is_one(value: int) -> bool:
    return value == 1


PREDICATES: Mapping[str, Callable[[int], bool]] = {
    "normal": _is_normal,
    "flagged": _is_flagged,
    "strict": _is_strict,
    "chosen": _is_one,
}

UNUSUAL_SHARES = tuple(
    ShareMetric(
        f"unusual_{s}",
        f"{STRATUM_WORDS[s]} ({s}): said 'a bit' or 'very unusual'",
        "unusual",
        (s,),
        "flagged",
    )
    for s in STRATA
)
CHECK_SHARES = tuple(
    ShareMetric(
        f"check_{s}",
        f"{STRATUM_WORDS[s]} ({s}): would ask for a check"
        + (" (human noise floor)" if s == "E" else ""),
        "check",
        (s,),
        "flagged",
    )
    for s in STRATA
)
NORMAL_B = ShareMetric(
    "normal_B", "False alarms (B): said 'normal for it'", "unusual", ("B",), "normal"
)
STRICT_SHARES = tuple(
    ShareMetric(
        f"check_yes_{s}", f"{STRATUM_WORDS[s]} ({s}): answered 'yes'", "check", (s,), "strict"
    )
    for s in STRATA
)
DIFFERENCE_NAME = "check_A_minus_B"
DIFFERENCE_LABEL = "Caught gray (A) minus false alarms (B), 'check' share"
RHO_LABELS: Mapping[str, str] = {
    "unusual": "Spearman: engine's M vs mean 'how unusual' (depends on the card mix)",
    "check": "Spearman: engine's M vs mean 'would check' (depends on the card mix)",
}


# --- loading -----------------------------------------------------------------------------------


def _stratum_letter(raw: object, card_id: str) -> str:
    match = STRATUM_PATTERN.match(str(raw or "").strip())
    if match is None:
        raise StudyInputError(f"card {card_id}: stratum {raw!r} is not one of {', '.join(STRATA)}")
    return match.group(1)


def _card_key(card_id: str, raw: Mapping, row_map: Mapping[str, str | None]) -> CardKey:
    attention = raw.get("attention")
    if attention is not None and attention not in ATTENTION_KINDS:
        raise StudyInputError(f"card {card_id}: attention {attention!r} is not normal/wild")
    multiplier = raw.get("M")
    if attention is None and not isinstance(multiplier, (int, float)):
        raise StudyInputError(f"card {card_id}: a scored card needs a numeric M")
    strongest = raw.get("strongest") or None
    list_rank = raw.get("list_rank")
    return CardKey(
        card_id=card_id,
        stratum=None if attention is not None else _stratum_letter(raw.get("stratum"), card_id),
        attention=attention,
        multiplier=None if multiplier is None else float(multiplier),
        listed=bool(raw.get("listed")),
        list_rank=list_rank if isinstance(list_rank, int) else None,
        strongest=strongest,
        expected_row=row_map.get(strongest) if strongest else None,
        gray_kind=raw.get("gray_kind") or None,
        tags=tuple(str(tag) for tag in raw.get("tags") or ()),
        org_event=raw.get("org_event") or None,
        latent_cause=raw.get("latent_cause") or None,
    )


def _pair_key(pair_id: str, raw: Mapping, item_pair: Mapping) -> PairKey:
    card_ids = tuple(str(card.get("id")) for card in item_pair.get("cards") or ())
    if len(card_ids) != 2 or card_ids[0] == card_ids[1]:
        raise StudyInputError(f"pair {pair_id}: needs exactly two different cards")
    prefers = raw.get("engine_prefers")
    if prefers not in card_ids:
        raise StudyInputError(f"pair {pair_id}: engine_prefers {prefers!r} is not in the pair")
    gray = raw.get("gray_card")
    if gray is not None and gray not in card_ids:
        raise StudyInputError(f"pair {pair_id}: gray_card {gray!r} is not in the pair")
    raw_m = raw.get("M") or {}
    multipliers = {cid: float(raw_m[cid]) for cid in card_ids if cid in raw_m}
    margin = raw.get("margin")
    if not isinstance(margin, (int, float)) and len(multipliers) == len(card_ids):
        other = next(cid for cid in card_ids if cid != prefers)
        low = multipliers[other]
        margin = multipliers[prefers] / low if low > 0 else None
    margin = float(margin) if isinstance(margin, (int, float)) else None
    close = raw.get("close")
    if not isinstance(close, bool):
        close = margin is not None and margin < MIN_CLEAR_MARGIN
    return PairKey(
        pair_id=pair_id,
        pair_type=str(raw.get("type") or UNKNOWN_GROUP),
        card_ids=(card_ids[0], card_ids[1]),
        engine_prefers=prefers,
        gray_card=gray,
        multipliers=multipliers,
        margin=margin,
        close=close,
    )


def _same_ids(name: str, bank_ids: list[str], key_ids: Iterable[str]) -> None:
    if len(bank_ids) != len(set(bank_ids)) or set(bank_ids) != set(key_ids):
        raise StudyInputError(f"the item bank and the key list different {name}")


def hidden_rows(items: Mapping, key: Mapping) -> frozenset[str]:
    """Rows people never see: marked not shown, listed by the key, or "not recorded" on every
    card that has rows. Ticks on them are noise, never a blind spot."""
    rows = items.get("rows") or []
    hidden = {str(row["id"]) for row in rows if row.get("shown") is False}
    hidden |= {str(row) for row in key.get("hidden_rows") or ()}
    cards = [card for card in items.get("cards") or () if card.get("rows")]
    for row in rows:
        values = [value for card in cards for value in card["rows"] if value.get("id") == row["id"]]
        if values and all(v.get("usual") == v.get("today") == NOT_RECORDED for v in values):
            hidden.add(str(row["id"]))
    return frozenset(hidden)


def load_study(key: Mapping, items: Mapping) -> Study:
    """Join items.json with key.json and check that they describe the same study.

    Args:
        key: The parsed private key.
        items: The parsed public item bank.

    Returns:
        The joined study, cards and pairs in item-bank order.

    Raises:
        StudyInputError: If versions, ids, strata or pair choices do not line up.
    """
    version = items.get("bank_version")
    if not version or key.get("bank_version") != version:
        raise StudyInputError(
            f"bank_version differs: key {key.get('bank_version')!r}, items {version!r}"
        )
    rows = items.get("rows") or []
    row_ids = tuple(str(row["id"]) for row in rows)
    row_map: Mapping[str, str | None] = key.get("row_map") or {}
    stray = sorted(str(row) for row in row_map.values() if row is not None and row not in row_ids)
    if stray:
        raise StudyInputError(f"row_map points at rows that are not in the bank: {stray}")
    bank_cards = [str(card["id"]) for card in items.get("cards") or ()]
    key_cards = key.get("cards") or {}
    _same_ids("cards", bank_cards, key_cards)
    bank_pairs = {str(pair["id"]): pair for pair in items.get("pairs") or ()}
    key_pairs = key.get("pairs") or {}
    _same_ids("pairs", [str(pair["id"]) for pair in items.get("pairs") or ()], key_pairs)
    context = key.get("context")
    return Study(
        bank_version=str(version),
        engine=dict(key.get("engine") or {}),
        row_ids=row_ids,
        row_labels={str(row["id"]): str(row.get("label", row["id"])) for row in rows},
        row_dimensions={
            row: tuple(sorted(dim for dim, mapped in row_map.items() if mapped == row))
            for row in row_ids
        },
        cards={cid: _card_key(cid, key_cards[cid], row_map) for cid in bank_cards},
        pairs={pid: _pair_key(pid, key_pairs[pid], bank_pairs[pid]) for pid in bank_pairs},
        hidden_rows=hidden_rows(items, key),
        practice_ids=frozenset(str(card["id"]) for card in items.get("practice") or ()),
        context=dict(context) if isinstance(context, Mapping) else None,
    )


def unwrap_documents(raw: object) -> list[dict]:
    """Return the response documents of an export from the shared store.

    Accepts a JSON list of documents (the documented format), a list of store rows that hold the
    document under "data", a single document, or a {doc id: document} mapping.

    Raises:
        StudyInputError: If the export has any other shape.
    """
    if isinstance(raw, dict):
        documents = [raw] if "pid" in raw else list(raw.values())
    elif isinstance(raw, list):
        documents = raw
    else:
        raise StudyInputError("responses must be a JSON list of response documents")
    unwrapped = []
    for document in documents:
        if isinstance(document, dict) and "pid" not in document:
            document = document.get("data", document)
        if not isinstance(document, dict):
            raise StudyInputError("every response must be a JSON object")
        unwrapped.append(document)
    return unwrapped


def _parse_level(value: object, name: str, issues: Counter) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value not in ANSWER_LEVELS:
        issues[f"invalid '{name}' answer (dropped)"] += 1
        return None
    return value


def _parse_ms(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        return None
    return int(value)


def _parse_time(value: object, issues: Counter) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        issues["unreadable start or finish time"] += 1
        return None


def _parse_card(raw: object, study: Study, issues: Counter) -> CardAnswer | None:
    if not isinstance(raw, dict):
        issues["card answer is not an object (dropped)"] += 1
        return None
    unusual = _parse_level(raw.get("unusual"), "unusual", issues)
    check = _parse_level(raw.get("check"), "check", issues)
    if unusual is None and check is None:
        return None
    ticked = raw.get("stood_out") or []
    if not isinstance(ticked, list):
        ticked = []
    stray = [row for row in ticked if row not in study.row_ids]
    if stray:
        issues["ticked a row that is not in the bank (ignored)"] += len(stray)
    stood_out = tuple(dict.fromkeys(row for row in ticked if row in study.row_ids))
    return CardAnswer(
        unusual, check, stood_out, _parse_ms(raw.get("ms")), _parse_order(raw.get("order"))
    )


def _parse_order(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _parse_pair(raw: object, pair: PairKey, issues: Counter) -> PairAnswer | None:
    if not isinstance(raw, dict) or raw.get("chose") not in pair.card_ids:
        issues["pair choice is not one of the pair's cards (dropped)"] += 1
        return None
    top = raw.get("top") if raw.get("top") in pair.card_ids else None
    return PairAnswer(
        str(raw["chose"]), top, _parse_ms(raw.get("ms")), _parse_order(raw.get("order"))
    )


def parse_rater(document: Mapping, index: int, study: Study, issues: Counter) -> Rater:
    """Parse one response document; invalid answers are dropped and counted in ``issues``."""
    pid = document.get("pid")
    if not isinstance(pid, str) or not pid.strip():
        issues["response without a pid (numbered by position)"] += 1
        pid = f"{MISSING_PID_PREFIX}{index}"
    kind = document.get("rater")
    if kind is None:
        issues[f"response without 'rater' (taken as {DEFAULT_RATER_KIND})"] += 1
        kind = DEFAULT_RATER_KIND
    background = document.get("background")
    background = background if isinstance(background, dict) else {}
    tech = background.get("tech")
    raw_cards = document.get("cards") if isinstance(document.get("cards"), dict) else {}
    raw_pairs = document.get("pairs") if isinstance(document.get("pairs"), dict) else {}
    cards: dict[str, CardAnswer] = {}
    for card_id, raw in raw_cards.items():
        if card_id in study.practice_ids:
            continue  # a practice answer: never analysed, never an issue
        if card_id not in study.cards:
            issues["answer for a card that is not in the bank (ignored)"] += 1
            continue
        answer = _parse_card(raw, study, issues)
        if answer is not None:
            cards[card_id] = answer
    pairs: dict[str, PairAnswer] = {}
    for pair_id, raw in raw_pairs.items():
        if pair_id not in study.pairs:
            issues["answer for a pair that is not in the bank (ignored)"] += 1
            continue
        choice = _parse_pair(raw, study.pairs[pair_id], issues)
        if choice is not None:
            pairs[pair_id] = choice
    mobile = document.get("mobile")
    model = document.get("model")
    return Rater(
        pid=pid.strip(),
        kind=str(kind),
        bank_version=document.get("bank_version"),
        tech=tech if tech in TECH_GROUPS else UNKNOWN_GROUP,
        ai_use=str(background.get("ai_use") or UNKNOWN_GROUP),
        started=_parse_time(document.get("started"), issues),
        finished=_parse_time(document.get("finished"), issues),
        mobile=mobile if isinstance(mobile, bool) else None,
        cards=cards,
        pairs=pairs,
        model=model if isinstance(model, str) and model else None,
        synthetic=document.get("synthetic") is True,
    )


# --- 1. quality --------------------------------------------------------------------------------


def _minutes(rater: Rater) -> float | None:
    start, end = rater.started, rater.finished
    if start is None or end is None or (start.tzinfo is None) != (end.tzinfo is None):
        return None
    seconds = (end - start).total_seconds()
    return seconds / SECONDS_PER_MINUTE if seconds >= 0 else None


def _median_card_seconds(rater: Rater) -> float | None:
    times = [answer.ms for answer in rater.cards.values() if answer.ms is not None]
    return statistics.median(times) / MS_PER_SECOND if times else None


def attention_outcome(kind: str, answer: CardAnswer | None) -> str:
    """The pre-registered rule: the normal card passes with 'normal for it'; the wild card passes
    with 'a bit' or 'very unusual' and 'maybe' or 'yes' to a check."""
    if answer is None or answer.unusual is None:
        return ATTENTION_MISSING
    if kind == "normal":
        return ATTENTION_PASS if answer.unusual == NORMAL_LEVEL else ATTENTION_FAIL
    if answer.unusual < FLAG_LEVEL or (answer.check is not None and answer.check < FLAG_LEVEL):
        return ATTENTION_FAIL
    return ATTENTION_MISSING if answer.check is None else ATTENTION_PASS


def attention_results(rater: Rater, study: Study) -> dict[str, str]:
    """Pass, fail or missing for each attention card (see ``attention_outcome``)."""
    return {
        card.card_id: attention_outcome(card.attention or "", rater.cards.get(card.card_id))
        for card in study.attention_cards
    }


def _is_eligible(rater: Rater, study: Study) -> bool:
    return rater.kind in RATER_KINDS and rater.bank_version == study.bank_version


def _exclusion(
    rater: Rater, attention: Mapping[str, str], study: Study, is_duplicate: bool
) -> str | None:
    if rater.kind not in RATER_KINDS:
        return EXCLUDE_KIND
    if rater.bank_version != study.bank_version:
        return EXCLUDE_VERSION
    if is_duplicate:
        return EXCLUDE_DUPLICATE
    if not rater.answer_count:
        return EXCLUDE_EMPTY
    if ATTENTION_FAIL in attention.values():
        return EXCLUDE_FAILED
    if ATTENTION_MISSING in attention.values():
        return EXCLUDE_UNVERIFIED
    return None


def _fuller_first(rater: Rater) -> tuple:
    return (rater.answer_count, rater.finished is not None, str(rater.finished or rater.started))


def is_complete(rater: Rater, study: Study) -> bool:
    """Finished, with both questions on every card and a choice in every pair."""
    cards_done = all(cid in rater.cards and rater.cards[cid].is_complete for cid in study.cards)
    return rater.finished is not None and cards_done and set(rater.pairs) == set(study.pairs)


def screen_raters(raters: Sequence[Rater], study: Study) -> list[Screened]:
    """Apply the quality screen: duplicates, bank version, empty, attention checks.

    A rater is kept only after passing BOTH attention checks; a partial rater who passed both is
    kept with the answers given. Of several documents on this bank version with the same pid and
    kind, the one with the most answers is kept.
    """
    best: dict[str, Rater] = {}
    for rater in raters:
        if not _is_eligible(rater, study):
            continue
        if rater.key not in best or _fuller_first(rater) > _fuller_first(best[rater.key]):
            best[rater.key] = rater
    screened = []
    for rater in raters:
        attention = attention_results(rater, study)
        is_duplicate = _is_eligible(rater, study) and best[rater.key] is not rater
        screened.append(
            Screened(
                rater=rater,
                complete=is_complete(rater, study),
                attention=attention,
                exclusion=_exclusion(rater, attention, study, is_duplicate),
                minutes=_minutes(rater),
                median_card_seconds=_median_card_seconds(rater),
            )
        )
    return screened


def _median(values: Iterable[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return statistics.median(present) if present else None


def quality_summary(screened: Sequence[Screened], study: Study, issues: Counter) -> dict:
    """Counts for the 'who took part and who was kept' table, per rater kind."""
    by_kind: dict[str, dict] = {}
    for kind in RATER_KINDS:
        group = [s for s in screened if s.rater.kind == kind]
        kept = [s for s in group if s.exclusion is None]
        counted = [s for s in group if s.exclusion not in (EXCLUDE_DUPLICATE, EXCLUDE_VERSION)]
        attention = {}
        for check_name in ATTENTION_KINDS:
            seen = [
                s.attention[card.card_id]
                for s in counted
                for card in study.attention_cards
                if card.attention == check_name and s.attention[card.card_id] != ATTENTION_MISSING
            ]
            attention[check_name] = {"passed": seen.count(ATTENTION_PASS), "answered": len(seen)}
        speeders = [
            s
            for s in kept
            if s.median_card_seconds is not None
            and s.median_card_seconds * MS_PER_SECOND < SPEEDER_MEDIAN_CARD_MS
        ]
        phones = [s.rater.mobile for s in kept if s.rater.mobile is not None]
        by_kind[kind] = {
            "received": len(group),
            "finished": sum(s.rater.finished is not None for s in group),
            "complete": sum(s.complete for s in group),
            "excluded": {
                reason: sum(s.exclusion == reason for s in group) for reason in EXCLUSION_ORDER
            },
            "kept": len(kept),
            "kept_partial": sum(not s.complete for s in kept),
            "median_minutes": _median(s.minutes for s in kept),
            "median_card_seconds": _median(s.median_card_seconds for s in kept),
            "fast_raters_flagged": len(speeders) if kind == HUMAN else None,
            "on_a_phone": sum(phones) if phones else None,
            "attention": attention,
            "models": dict(Counter(s.rater.model for s in kept if s.rater.model)),
        }
    others = [s for s in screened if s.rater.kind not in RATER_KINDS]
    kept_humans = [s.rater for s in screened if s.exclusion is None and s.rater.kind == HUMAN]
    return {
        "by_kind": by_kind,
        "synthetic": sum(s.rater.synthetic for s in screened),
        "received": len(screened),
        "unknown_kind": len(others),
        "background": dict(Counter(rater.tech for rater in kept_humans)),
        "ai_use": dict(Counter(rater.ai_use for rater in kept_humans)),
        "issues": dict(issues),
        "raters": [
            {
                "pid": s.rater.pid,
                "rater": s.rater.kind,
                "tech": s.rater.tech,
                "cards": len(s.rater.cards),
                "pairs": len(s.rater.pairs),
                "complete": s.complete,
                "minutes": s.minutes,
                "attention": dict(s.attention),
                "excluded": s.exclusion,
            }
            for s in screened
        ],
    }


# --- statistics helpers ------------------------------------------------------------------------


def _active(cells: Cells, raters: Sequence[str], items: Sequence[str]) -> list[str]:
    return [rater for rater in raters if any(item in cells.get(rater, {}) for item in items)]


def _estimate(
    cells: Cells,
    raters: Sequence[str],
    item_groups: Sequence[Sequence[str]],
    statistic: Callable[[Sequence[str], Sequence[str]], float | None],
    draws: int,
    seed_text: str,
) -> Estimate:
    items = [item for group in item_groups for item in group]
    active = _active(cells, raters, items)
    low, high, valid = bootstrap_interval(statistic, active, item_groups, draws, seed_text)
    answered_items = {item for rater in active for item in items if item in cells[rater]}
    return Estimate(
        value=statistic(active, items) if active else None,
        low=low,
        high=high,
        raters=len(active),
        items=len(answered_items),
        answers=sum(item in cells[rater] for rater in active for item in items),
        draws=valid,
    )


def share_estimate(
    cells: Cells,
    raters: Sequence[str],
    item_groups: Sequence[Sequence[str]],
    predicate: Callable[[int], bool],
    draws: int,
    seed_text: str,
) -> Estimate:
    """Pooled share of answers meeting ``predicate``, with a two-way bootstrap interval."""

    def statistic(sample_raters: Sequence[str], sample_items: Sequence[str]) -> float | None:
        return pooled_share(cells, sample_raters, sample_items, predicate)

    return _estimate(cells, raters, item_groups, statistic, draws, seed_text)


def difference_estimate(
    cells: Cells,
    raters: Sequence[str],
    groups_a: Sequence[Sequence[str]],
    groups_b: Sequence[Sequence[str]],
    predicate: Callable[[int], bool],
    draws: int,
    seed_text: str,
) -> Estimate:
    """Share on the ``groups_a`` items minus share on the ``groups_b`` items (same raters)."""
    in_a = {item for group in groups_a for item in group}

    def statistic(sample_raters: Sequence[str], sample_items: Sequence[str]) -> float | None:
        share_a = pooled_share(
            cells, sample_raters, [i for i in sample_items if i in in_a], predicate
        )
        share_b = pooled_share(
            cells, sample_raters, [i for i in sample_items if i not in in_a], predicate
        )
        return None if share_a is None or share_b is None else share_a - share_b

    return _estimate(cells, raters, [*groups_a, *groups_b], statistic, draws, seed_text)


def rank_estimate(
    cells: Cells,
    raters: Sequence[str],
    item_groups: Sequence[Sequence[str]],
    multipliers: Mapping[str, float],
    draws: int,
    seed_text: str,
) -> Estimate:
    """Spearman between each card's M and the raters' mean answer on it."""

    def statistic(sample_raters: Sequence[str], sample_items: Sequence[str]) -> float | None:
        xs, ys = [], []
        for item in sample_items:
            answers = [cells[r][item] for r in sample_raters if item in cells.get(r, {})]
            if answers:
                xs.append(multipliers[item])
                ys.append(statistics.fmean(answers))
        return spearman(xs, ys)

    return _estimate(cells, raters, item_groups, statistic, draws, seed_text)


def answer_cells(raters: Sequence[Rater], field_name: str) -> dict[str, dict[str, int]]:
    """rater key -> card id -> the answer to one question."""
    cells: dict[str, dict[str, int]] = {}
    for rater in raters:
        row = {}
        for card_id, answer in rater.cards.items():
            value = getattr(answer, field_name)
            if value is not None:
                row[card_id] = value
        cells[rater.key] = row
    return cells


def choice_cells(
    raters: Sequence[Rater], study: Study, target: Callable[[PairKey], str | None]
) -> dict[str, dict[str, int]]:
    """rater key -> pair id -> 1 if the rater chose ``target(pair)``, else 0."""
    cells: dict[str, dict[str, int]] = {}
    for rater in raters:
        row = {}
        for pair_id, choice in rater.pairs.items():
            wanted = target(study.pairs[pair_id])
            if wanted is not None:
                row[pair_id] = int(choice.chose == wanted)
        cells[rater.key] = row
    return cells


def _metric(name: str, label: str, kind: str, estimate: Estimate) -> dict:
    return {"name": name, "label": label, "kind": kind, **asdict(estimate)}


# --- 3. headline metrics -----------------------------------------------------------------------


def _share_metric(
    metric: ShareMetric,
    cells: Mapping[str, Cells],
    keys: Sequence[str],
    study: Study,
    draws: int,
    seed: str,
) -> dict:
    estimate = share_estimate(
        cells[metric.field_name],
        keys,
        study.stratum_groups(metric.strata),
        PREDICATES[metric.predicate],
        draws,
        f"{seed}|{metric.name}",
    )
    return _metric(metric.name, metric.label, "share", estimate)


def headline_metrics(raters: Sequence[Rater], study: Study, draws: int, seed: str) -> dict:
    """The paper's headline numbers for one group of raters: per-stratum shares for these cards
    (with an interval and n when ``draws`` > 0), the A-B difference, and Spearman's rho as a
    secondary number that depends on the card mix."""
    keys = [rater.key for rater in raters]
    cells = {name: answer_cells(raters, name) for name in CARD_FIELDS}
    multipliers = {
        cid: card.multiplier
        for cid, card in study.cards.items()
        if card.is_scored and card.multiplier is not None
    }

    def share(metric: ShareMetric) -> dict:
        return _share_metric(metric, cells, keys, study, draws, seed)

    strata = [
        {
            "stratum": s,
            "name": STRATUM_WORDS[s],
            "cards": len(study.cards_in((s,))),
            "unusual": share(unusual),
            "check": share(check),
            "check_yes": share(yes),
        }
        for s, unusual, check, yes in zip(
            STRATA, UNUSUAL_SHARES, CHECK_SHARES, STRICT_SHARES, strict=True
        )
        if study.cards_in((s,))
    ]
    rows = [entry["check"] for entry in strata]
    rows.append(share(NORMAL_B))
    difference = difference_estimate(
        cells["check"],
        keys,
        study.stratum_groups(("A",)),
        study.stratum_groups(("B",)),
        PREDICATES["flagged"],
        draws,
        f"{seed}|{DIFFERENCE_NAME}",
    )
    rows.append(_metric(DIFFERENCE_NAME, DIFFERENCE_LABEL, "difference", difference))
    all_strata = study.stratum_groups(STRATA)
    secondary = [
        _metric(
            f"rho_m_{name}",
            RHO_LABELS[name],
            "rho",
            rank_estimate(cells[name], keys, all_strata, multipliers, draws, f"{seed}|rho|{name}"),
        )
        for name in CARD_FIELDS
    ]
    return {
        "raters": len(raters),
        "intervals": draws > 0,
        "strata": strata,
        "headline": rows,
        "strict": [entry["check_yes"] for entry in strata],
        "secondary": secondary,
    }


# --- 2. per card -------------------------------------------------------------------------------


def _share(values: Sequence[int], predicate: Callable[[int], bool]) -> float | None:
    return sum(map(predicate, values)) / len(values) if values else None


def _mean(values: Sequence[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _field_values(raters: Sequence[Rater], card_id: str, field_name: str) -> list[int]:
    values = []
    for rater in raters:
        answer = rater.cards.get(card_id)
        value = None if answer is None else getattr(answer, field_name)
        if value is not None:
            values.append(value)
    return values


def card_table(humans: Sequence[Rater], claudes: Sequence[Rater], study: Study) -> list[dict]:
    """One row per card: people's answers next to the key (M, listed, stratum)."""
    rows = []
    for card in study.cards.values():
        unusual = _field_values(humans, card.card_id, "unusual")
        check = _field_values(humans, card.card_id, "check")
        rows.append(
            {
                "card": card.card_id,
                "stratum": card.stratum,
                "attention": card.attention,
                "gray_kind": card.gray_kind,
                "tags": list(card.tags),
                "org_event": card.org_event,
                "latent_cause": card.latent_cause,
                "M": card.multiplier,
                "listed": card.listed,
                "list_rank": card.list_rank,
                "strongest": card.strongest,
                "strongest_row": card.expected_row,
                "n": len(unusual),
                "share_unusual": _share(unusual, PREDICATES["flagged"]),
                "share_normal": _share(unusual, PREDICATES["normal"]),
                "share_check": _share(check, PREDICATES["flagged"]),
                "mean_unusual": _mean(unusual),
                "mean_check": _mean(check),
                "claude_n": len(_field_values(claudes, card.card_id, "unusual")),
                "claude_mean_unusual": _mean(_field_values(claudes, card.card_id, "unusual")),
                "claude_mean_check": _mean(_field_values(claudes, card.card_id, "check")),
            }
        )
    return rows


# --- 4. pairs ----------------------------------------------------------------------------------


def _pair_types(study: Study) -> list[str]:
    return list(dict.fromkeys(pair.pair_type for pair in study.pairs.values()))


def pair_metrics(raters: Sequence[Rater], study: Study, draws: int, seed: str) -> dict:
    """Agreement with the engine's preferred card, gray-card choice and first-shown bias."""
    keys = [rater.key for rater in raters]
    agree = choice_cells(raters, study, lambda pair: pair.engine_prefers)
    gray = choice_cells(raters, study, lambda pair: pair.gray_card)
    first = {
        rater.key: {pid: int(c.chose == c.top) for pid, c in rater.pairs.items() if c.top}
        for rater in raters
    }
    chosen = PREDICATES["chosen"]
    clear_ids = [p.pair_id for p in study.pairs.values() if not p.close]
    close_ids = [p.pair_id for p in study.pairs.values() if p.close]
    by_type, type_groups, gray_groups = [], [], []
    for pair_type in _pair_types(study):
        ids = [p.pair_id for p in study.pairs.values() if p.pair_type == pair_type]
        gray_ids = [pid for pid in ids if study.pairs[pid].gray_card is not None]
        type_groups.append(ids)
        gray_groups.append(gray_ids)
        by_type.append(
            {
                "type": pair_type,
                "pairs": len(ids),
                "agree": asdict(
                    share_estimate(agree, keys, [ids], chosen, draws, f"{seed}|agree|{pair_type}")
                ),
                "gray": asdict(
                    share_estimate(
                        gray, keys, [gray_ids], chosen, draws, f"{seed}|gray|{pair_type}"
                    )
                )
                if gray_ids
                else None,
            }
        )
    per_pair = []
    for pair in study.pairs.values():
        answers = [r.pairs[pair.pair_id] for r in raters if pair.pair_id in r.pairs]
        per_pair.append(
            {
                "pair": pair.pair_id,
                "type": pair.pair_type,
                "engine_prefers": pair.engine_prefers,
                "gray_card": pair.gray_card,
                "M": dict(pair.multipliers),
                "margin": pair.margin,
                "close": pair.close,
                "n": len(answers),
                "agree": _share([int(a.chose == pair.engine_prefers) for a in answers], chosen),
                "gray": _share([int(a.chose == pair.gray_card) for a in answers], chosen)
                if pair.gray_card
                else None,
            }
        )
    return {
        "by_type": by_type,
        "agree_all": asdict(
            share_estimate(agree, keys, type_groups, chosen, draws, f"{seed}|agree|all")
        ),
        "agree_clear": asdict(
            share_estimate(agree, keys, [clear_ids], chosen, draws, f"{seed}|agree|clear")
        ),
        "agree_close": asdict(
            share_estimate(agree, keys, [close_ids], chosen, draws, f"{seed}|agree|close")
        ),
        "close_pairs": close_ids,
        "gray_all": asdict(
            share_estimate(
                gray, keys, [g for g in gray_groups if g], chosen, draws, f"{seed}|gray|all"
            )
        ),
        "first_shown": asdict(
            share_estimate(first, keys, type_groups, chosen, draws, f"{seed}|first")
        ),
        "per_pair": per_pair,
    }


# --- 5. reasons --------------------------------------------------------------------------------


def _group_then_m(card: CardKey) -> tuple[str, float]:
    return (card.stratum or "", -(card.multiplier or 0.0))


def reason_summary(raters: Sequence[Rater], study: Study, draws: int, seed: str) -> dict:
    """Did the rows people ticked include the row of the engine's strongest dimension?

    Only cards with M of at least ``REASON_MIN_M`` count: below it the strongest dimension is
    noise. Rows people never see (``Study.hidden_rows``) are never a blind spot; ticks on them
    are reported as noise.
    """
    scored = [study.cards[cid] for cid in study.scored_cards]
    eligible = [
        card
        for card in scored
        if card.expected_row is not None and (card.multiplier or 0.0) >= REASON_MIN_M
    ]
    eligible_ids = {card.card_id for card in eligible}
    hits: dict[str, dict[str, int]] = {}
    row_ticks: Counter = Counter()
    ticks_by_row: dict[str, Counter] = {row: Counter() for row in study.row_ids}
    flagged_answers = ticking_answers = 0
    for rater in raters:
        row = {}
        for card_id, answer in rater.cards.items():
            card = study.cards[card_id]
            if not card.is_scored or answer.unusual is None or answer.unusual < FLAG_LEVEL:
                continue
            flagged_answers += 1
            if not answer.stood_out:
                continue
            ticking_answers += 1
            row_ticks.update(answer.stood_out)
            for ticked in answer.stood_out:
                ticks_by_row[ticked][card_id] += 1
            if card_id in eligible_ids:
                row[card_id] = int(card.expected_row in answer.stood_out)
        hits[rater.key] = row
    groups = [
        [cid for cid in group if cid in eligible_ids] for group in study.stratum_groups(STRATA)
    ]
    pooled = share_estimate(
        hits,
        [r.key for r in raters],
        [g for g in groups if g],
        PREDICATES["chosen"],
        draws,
        f"{seed}|reason",
    )
    per_card = []
    for card in sorted(eligible, key=_group_then_m):
        answers = [hits[r.key][card.card_id] for r in raters if card.card_id in hits[r.key]]
        per_card.append(
            {
                "card": card.card_id,
                "stratum": card.stratum,
                "M": card.multiplier,
                "strongest": card.strongest,
                "strongest_row": card.expected_row,
                "ticked": len(answers),
                "share_with_row": _share(answers, PREDICATES["chosen"]),
                "most_ticked": [row for row, _ in _most_ticked(card.card_id, ticks_by_row)],
            }
        )
    rows = [
        {
            "row": row,
            "label": study.row_labels[row],
            "shown": row not in study.hidden_rows,
            "dimensions": list(study.row_dimensions[row]),
            "ticks": row_ticks[row],
            "share_of_ticking_answers": row_ticks[row] / ticking_answers
            if ticking_answers
            else None,
            "blind_spot": not study.row_dimensions[row] and row not in study.hidden_rows,
            "top_cards": [cid for cid, _ in ticks_by_row[row].most_common(TOP_LISTED)],
        }
        for row in study.row_ids
    ]
    skipped = []
    for card in scored:
        if card.expected_row is None:
            skipped.append({"card": card.card_id, "strongest": card.strongest, "why": "no row"})
        elif (card.multiplier or 0.0) < REASON_MIN_M:
            skipped.append({"card": card.card_id, "strongest": card.strongest, "why": "low M"})
    return {
        "pooled": asdict(pooled),
        "min_m": REASON_MIN_M,
        "flagged_answers": flagged_answers,
        "ticking_answers": ticking_answers,
        "per_card": per_card,
        "skipped_cards": skipped,
        "rows": rows,
        "blind_spot_ticks": sum(r["ticks"] for r in rows if r["blind_spot"]),
        "hidden_row_ticks": sum(r["ticks"] for r in rows if not r["shown"]),
    }


def _most_ticked(card_id: str, ticks_by_row: Mapping[str, Counter]) -> list[tuple[str, int]]:
    """The rows ticked most often on one card, most first (ties keep bank order)."""
    counts = [(row, ticks[card_id]) for row, ticks in ticks_by_row.items() if ticks[card_id]]
    return sorted(counts, key=lambda pair: -pair[1])[:TOP_LISTED]


# --- 7. agreement with the human majority ------------------------------------------------------


def majority_credit(answer: int | str, others: Sequence[int | str]) -> float:
    """1 if ``answer`` is the others' most common answer; 1/k if it ties with k-1 others; else 0."""
    counts = Counter(others)
    top = max(counts.values())
    modes = [value for value, count in counts.items() if count == top]
    return 1 / len(modes) if answer in modes else 0.0


def _card_value(rater: Rater, card_id: str, field_name: str) -> int | None:
    answer = rater.cards.get(card_id)
    return None if answer is None else getattr(answer, field_name)


def agreement_with_majority(rater: Rater, humans: Sequence[Rater], study: Study) -> dict:
    """Agreement of one rater with the majority of the OTHER kept humans, per question."""
    others = [human for human in humans if human.key != rater.key]
    result = {}
    for field_name in CARD_FIELDS:
        credits = []
        for card_id in study.scored_cards:
            value = _card_value(rater, card_id, field_name)
            peers = [v for o in others if (v := _card_value(o, card_id, field_name)) is not None]
            if value is not None and peers:
                credits.append(majority_credit(value, peers))
        result[field_name] = {"share": _mean(credits), "n": len(credits)}
    credits = []
    for pair_id, choice in rater.pairs.items():
        peers = [o.pairs[pair_id].chose for o in others if pair_id in o.pairs]
        if peers:
            credits.append(majority_credit(choice.chose, peers))
    result["pairs"] = {"share": _mean(credits), "n": len(credits)}
    return result


def placement(value: float | None, human_values: Sequence[float]) -> float | None:
    """Share of humans below ``value`` (ties count half): 0.5 means in the middle of people."""
    if value is None or not human_values:
        return None
    below = sum(other < value for other in human_values)
    tied = sum(other == value for other in human_values)
    return (below + tied / 2) / len(human_values)


def agreement_summary(humans: Sequence[Rater], claudes: Sequence[Rater], study: Study) -> dict:
    """Each human's and each Claude run's agreement with the human majority, and Claude's place."""
    human_rows = [
        {"pid": h.pid, "rater": HUMAN, **agreement_with_majority(h, humans, study)} for h in humans
    ]
    claude_rows = [
        {"pid": c.pid, "rater": CLAUDE, **agreement_with_majority(c, humans, study)}
        for c in claudes
    ]
    spread = {}
    for name in (*CARD_FIELDS, "pairs"):
        values = [row[name]["share"] for row in human_rows if row[name]["share"] is not None]
        spread[name] = {
            "humans": len(values),
            "median": _median(values),
            "min": min(values) if values else None,
            "max": max(values) if values else None,
        }
        for row in claude_rows:
            row[name]["place_among_humans"] = placement(row[name]["share"], values)
    return {"humans": human_rows, "claude": claude_rows, "human_spread": spread}


# --- 8. agreement among raters ----------------------------------------------------------------


def agreement_table(raters: Sequence[Rater], study: Study, field_name: str) -> list[list[int]]:
    """Scored cards x answer levels: how many raters gave each answer."""
    table = []
    for card_id in study.scored_cards:
        counts = Counter(_field_values(raters, card_id, field_name))
        table.append([counts[level] for level in ANSWER_LEVELS])
    return table


def kappa_summary(raters: Sequence[Rater], study: Study) -> dict:
    """Krippendorff's ordinal alpha (headline) and Fleiss' kappa (unordered, beside it) on 'how
    unusual' and 'would check' over the scored cards. Descriptive only."""
    result = {}
    for field_name in CARD_FIELDS:
        table = agreement_table(raters, study, field_name)
        alpha = krippendorff_alpha(table, ORDINAL)
        kappa = fleiss_kappa(table)
        result[field_name] = {
            "alpha": alpha,
            "alpha_words": agreement_words(alpha),
            "alpha_nominal": krippendorff_alpha(table, NOMINAL),
            "kappa": kappa,
            "words": agreement_words(kappa),
            "raters": len(raters),
            "cards": sum(sum(row) >= 2 for row in table),
        }
    return result


def kappa_words(kappa: float | None) -> str:
    """Landis and Koch's plain-word band (kept for callers of the older name)."""
    return agreement_words(kappa)


# --- 9. position in the survey -------------------------------------------------------------


def position_summary(raters: Sequence[Rater], study: Study) -> dict:
    """'Would check' share and seconds per card on scored cards seen in the first half of a
    rater's own card order against the second half (fatigue or drift). Needs 'order'."""
    half = len(study.cards) // 2
    halves = {"first": [], "second": []}
    seconds = {"first": [], "second": []}
    with_order = 0
    for rater in raters:
        ordered = sorted(
            ((a.order, cid) for cid, a in rater.cards.items() if a.order is not None),
        )
        if not ordered:
            continue
        with_order += 1
        for position, (_, card_id) in enumerate(ordered):
            answer = rater.cards[card_id]
            which = "first" if position < half else "second"
            if study.cards[card_id].is_scored and answer.check is not None:
                halves[which].append(answer.check)
            if answer.ms is not None:
                seconds[which].append(answer.ms / MS_PER_SECOND)
    return {
        "raters_with_order": with_order,
        "half": half,
        **{
            f"check_{which}": _share(values, PREDICATES["flagged"])
            for which, values in halves.items()
        },
        **{f"answers_{which}": len(values) for which, values in halves.items()},
        **{f"median_seconds_{which}": _median(values) for which, values in seconds.items()},
    }


# --- the whole analysis ------------------------------------------------------------------------


def group_summary(raters: Sequence[Rater], study: Study, draws: int, seed: str) -> dict:
    """Headline, pair and reason metrics for one group of raters (no intervals if draws is 0)."""
    return {
        **headline_metrics(raters, study, draws, seed),
        "pairs": pair_metrics(raters, study, draws, seed),
        "reason": reason_summary(raters, study, draws, seed),
    }


def unscreened(screened: Sequence[Screened]) -> list[Rater]:
    """People kept with no attention screen: right bank, kind and copy, with answers."""
    passes = (None, EXCLUDE_FAILED, EXCLUDE_UNVERIFIED)
    return [s.rater for s in screened if s.rater.kind == HUMAN and s.exclusion in passes]


def analyse(
    documents: Sequence[Mapping],
    study: Study,
    draws: int = DEFAULT_DRAWS,
    seed: int = DEFAULT_SEED,
) -> dict:
    """Run every step of the analysis and return a JSON-ready result.

    Args:
        documents: Response documents (humans and Claude runs together).
        study: The joined item bank and key.
        draws: Bootstrap draws per interval (people only; groups and Claude get none).
        seed: Seed for the bootstrap; the same seed gives the same intervals.
    """
    issues: Counter = Counter()
    raters = [parse_rater(doc, index, study, issues) for index, doc in enumerate(documents)]
    screened = screen_raters(raters, study)
    kept = [s.rater for s in screened if s.exclusion is None]
    humans = [rater for rater in kept if rater.kind == HUMAN]
    claudes = [rater for rater in kept if rater.kind == CLAUDE]
    background_groups = {
        tech: [h for h in humans if h.tech == tech]
        for tech in (*TECH_GROUPS, UNKNOWN_GROUP)
        if any(h.tech == tech for h in humans)
    }
    everyone = unscreened(screened)
    return {
        "bank_version": study.bank_version,
        "engine": dict(study.engine),
        "context": dict(study.context) if study.context else None,
        "settings": {
            "draws": draws,
            "seed": seed,
            "interval": INTERVAL_LEVEL,
            "check_counts_from": CHECK_WORDS[FLAG_LEVEL],
            "attention_rule": dict(ATTENTION_RULE_WORDS),
            "reason_min_m": REASON_MIN_M,
            "min_clear_margin": MIN_CLEAR_MARGIN,
        },
        "quality": quality_summary(screened, study, issues),
        "cards": card_table(humans, claudes, study),
        "humans": group_summary(humans, study, draws, f"{seed}|humans"),
        "no_attention_screen": headline_metrics(everyone, study, 0, f"{seed}|everyone"),
        "groups": {
            tech: group_summary(group, study, 0, f"{seed}|{tech}")
            for tech, group in background_groups.items()
        },
        "claude": group_summary(claudes, study, 0, f"{seed}|claude") if claudes else None,
        "agreement": agreement_summary(humans, claudes, study),
        "kappa": {
            "humans": kappa_summary(humans, study),
            "claude": kappa_summary(claudes, study) if len(claudes) >= 2 else None,
        },
        "positions": position_summary(humans, study),
    }


# --- markdown ----------------------------------------------------------------------------------


def _pct(value: float | None) -> str:
    return NOT_AVAILABLE if value is None else f"{PERCENT * value:.0f}%"


def _num(value: float | None, digits: int = 2) -> str:
    return NOT_AVAILABLE if value is None else f"{value:.{digits}f}"


def format_estimate(metric: Mapping) -> str:
    """'62% [45-78%]', '0.71 [0.40, 0.88]' or '+35 pts [+10, +58]' (n/a when undefined)."""
    value, low, high = metric["value"], metric["low"], metric["high"]
    if value is None:
        return NOT_AVAILABLE
    kind = metric.get("kind", "share")
    if kind == "rho":
        interval = "" if low is None else f" [{low:.2f}, {high:.2f}]"
        return f"{value:.2f}{interval}"
    if kind == "difference":
        interval = "" if low is None else f" [{PERCENT * low:+.0f}, {PERCENT * high:+.0f}]"
        return f"{PERCENT * value:+.0f} pts{interval}"
    interval = "" if low is None else f" [{PERCENT * low:.0f}-{PERCENT * high:.0f}%]"
    return f"{PERCENT * value:.0f}%{interval}"


def _table(header: Sequence[str], rows: Iterable[Sequence[object]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return lines + [""]


HOW_TO_READ = """\
- **What people saw.** Each card is one AI agent's day next to that same agent's usual days. \
People answered two questions: how unusual is today for it (normal for it / a bit unusual / \
very unusual), and would you ask someone to check it today (no / maybe / yes). They never saw \
the engine's score. On unusual cards they could tick the lines that stood out.
- **What the engine said.** The engine gives each day a multiplier **M**, from x0.7 (calmer \
than its usual) to x5 (far outside its habits). Each day the 4 highest agent-days go on a \
review list; **listed** means the card's day was on that list.
- **Where the cards came from.** A: gray-area days the engine listed (caught). B: ordinary \
days it listed (false alarms). C: gray-area days it did not list (missed). D: harmless days \
with a life or company change (a new secure link, back from vacation). E: plain ordinary days.
- **These cards were chosen on purpose**, to test where the engine is right and where it is \
wrong; they are not a sample of the real list. Read every number as "for these cards". The \
headline is the table by group (A-E) and the card-by-card table; Spearman's rho depends on the \
mix of cards and is secondary. No precision, recall or population-level agreement can be read \
from this study.
- **What good looks like.** People ask for a check on A and C, and not on B, D and E. E is \
the human noise floor: how often people ask for a check on a plain day anyway. If B looks as \
'normal' to people as E does, the false alarms are real false alarms.
- **Brackets.** '62% [45-78%]' means our best guess is 62%, and with other similar people \
and other similar cards of the same groups it would likely land between 45% and 78% (a 95% \
bootstrap interval that resamples both the people and the cards). With 10-20 people and 3-4 \
cards a group the brackets are wide: only differences of about 30-40 points or more stand out \
from zero. There are no p-values, on purpose. Background groups and Claude runs show the value \
and n only, without brackets.
- **'Would check'** counts both 'maybe' and 'yes'; a stricter table counts 'yes' only.
- **n.** People = raters with at least one answer in that measure; Cards = cards answered; \
Answers = person-card answers.
- **Claude** answered the same survey as a separate group. It is never part of the human \
majority it is compared against."""


def _settings_line(result: Mapping) -> str:
    engine = result["engine"]
    parts = [
        f"{name} {engine[name]}"
        for name in ("design", "profile", "agents", "seed", "git_sha")
        if name in engine
    ]
    settings = result["settings"]
    return (
        f"Bank `{result['bank_version']}`; engine {', '.join(parts) or NOT_AVAILABLE}. "
        f"Intervals: {PERCENT * settings['interval']:.0f}% two-way bootstrap (raters and cards), "
        f"{settings['draws']} draws, seed {settings['seed']}."
    )


def _context_lines(context: Mapping | None) -> list[str]:
    """What the engine's real daily list holds, next to the chosen cards."""
    if not context or not context.get("list_composition"):
        return []
    mix = context["list_composition"]
    words = {"gray": "gray-area days", "change": "benign change days", "ordinary": "ordinary days"}
    parts = [f"{_pct(mix.get(name))} {word}" for name, word in words.items()]
    return [
        f"On the engine's real daily list ({_num(context.get('listed_agent_days'), 0)} listed "
        f"agent-days), {', '.join(parts)}. The cards here over-represent gray days on purpose.",
        "",
    ]


def _quality_section(quality: Mapping) -> list[str]:
    kinds = quality["by_kind"]
    header = ["", "People", "Claude runs"]

    def row(label: str, getter: Callable[[Mapping], object]) -> list[object]:
        return [label, *(getter(kinds[kind]) for kind in RATER_KINDS)]

    rows = [
        row("Responses received", lambda k: k["received"]),
        row("Pressed the last button", lambda k: k["finished"]),
        row("Answered every card and pair", lambda k: k["complete"]),
        *(
            row(f"Dropped: {reason}", lambda k, r=reason: k["excluded"][r])
            for reason in EXCLUSION_ORDER
        ),
        row("**Kept**", lambda k: f"**{k['kept']}**"),
        row("Kept, but stopped early (answers used)", lambda k: k["kept_partial"]),
        row("Median minutes (kept)", lambda k: _num(k["median_minutes"], 1)),
        row("Median seconds per card (kept)", lambda k: _num(k["median_card_seconds"], 1)),
        row(
            f"Median card under {SPEEDER_MEDIAN_CARD_MS / MS_PER_SECOND:.0f} s (flagged only)",
            lambda k: (
                NOT_AVAILABLE if k["fast_raters_flagged"] is None else k["fast_raters_flagged"]
            ),
        ),
        row(
            "On a phone (kept)",
            lambda k: NOT_AVAILABLE if k["on_a_phone"] is None else k["on_a_phone"],
        ),
    ]
    for check_name, expected in ATTENTION_RULE_WORDS.items():
        rows.append(
            row(
                f"Attention card '{check_name}' passed (expects {expected})",
                lambda k, c=check_name: (
                    f"{k['attention'][c]['passed']}/{k['attention'][c]['answered']}"
                    if c in k["attention"]
                    else NOT_AVAILABLE
                ),
            )
        )
    lines = ["## 1. Who took part and who was kept", ""]
    lines += [
        "A person is kept only after passing both hidden attention checks, by the "
        "pre-registered rule: the plainly normal card answered 'normal for it'; the wildly "
        "unusual card answered 'a bit' or 'very unusual' and 'maybe' or 'yes' to a check. "
        "People who stopped early but passed both are kept with the answers they gave.",
        "",
    ]
    lines += _table(header, rows)
    models = quality["by_kind"][CLAUDE].get("models") or {}
    if models:
        named = ", ".join(f"{name} ({count})" for name, count in sorted(models.items()))
        lines += [f"Claude runs kept, by model: {named}.", ""]
    background = quality["background"]
    if background:
        words = [f"{TECH_GROUPS.get(k, k)} {v}" for k, v in sorted(background.items())]
        lines += [
            f"Kept people by background: {', '.join(words)}. "
            f"AI use: {', '.join(f'{k} {v}' for k, v in sorted(quality['ai_use'].items()))}.",
            "",
        ]
    if quality["unknown_kind"]:
        lines += [f"Responses with an unknown rater kind (dropped): {quality['unknown_kind']}.", ""]
    if quality["issues"]:
        lines += ["Data issues found while reading the responses:", ""]
        lines += [f"- {issue}: {count}" for issue, count in sorted(quality["issues"].items())]
        lines.append("")
    return lines


def _listed_text(card: Mapping) -> str:
    if not card["listed"]:
        return "no"
    return f"yes (#{card['list_rank']})" if card["list_rank"] else "yes"


def _note_text(card: Mapping) -> str:
    latent = card.get("latent_cause")
    notes = [
        card["gray_kind"] or "",
        *card["tags"],
        card["org_event"] or "",
        f"latent: {latent}" if latent else "",
    ]
    return ", ".join(note for note in notes if note) or "-"


def _cards_section(cards: Sequence[Mapping], has_claude: bool) -> list[str]:
    scored = sorted(
        (card for card in cards if card["attention"] is None),
        key=lambda card: (card["stratum"], -(card["M"] or 0)),
    )
    header = [
        "Card",
        "Group",
        "M",
        "Listed",
        "Strongest (row)",
        "Gray kind / notes",
        "n",
        "Unusual",
        "Check",
        "Mean unusual",
        "Mean check",
    ]
    if has_claude:
        header += ["Claude unusual", "Claude check"]
    rows = []
    for card in scored:
        row = [
            card["card"],
            card["stratum"],
            f"x{card['M']:.2f}",
            _listed_text(card),
            f"{card['strongest'] or '-'} ({card['strongest_row'] or '-'})",
            _note_text(card),
            card["n"],
            _pct(card["share_unusual"]),
            _pct(card["share_check"]),
            _num(card["mean_unusual"]),
            _num(card["mean_check"]),
        ]
        if has_claude:
            row += [_num(card["claude_mean_unusual"]), _num(card["claude_mean_check"])]
        rows.append(row)
    lines = ["## 2. Card by card (people)", ""]
    lines += [
        "Unusual = share answering 'a bit' or 'very unusual'; Check = share answering 'maybe' "
        "or 'yes'. Means are on 0-2. Sorted by group, then by M.",
        "",
    ]
    return lines + _table(header, rows)


def _metric_rows(metrics: Sequence[Mapping]) -> list[list[object]]:
    return [
        [
            metric["label"],
            format_estimate(metric),
            metric["raters"],
            metric["items"],
            metric["answers"],
        ]
        for metric in metrics
    ]


def _strata_rows(group: Mapping) -> list[list[object]]:
    return [
        [
            f"{entry['stratum']}: {entry['name']}",
            entry["cards"],
            entry["check"]["raters"],
            entry["check"]["answers"],
            format_estimate(entry["unusual"]),
            format_estimate(entry["check"]),
            format_estimate(entry["check_yes"]),
        ]
        for entry in group["strata"]
    ]


STRATA_HEADER = (
    "Group",
    "Cards",
    "People",
    "Answers",
    "Said unusual",
    "Would check",
    "Said 'yes', check",
)


def _headline_section(humans: Mapping, everyone: Mapping) -> list[str]:
    lines = ["## 3. Headline: by group, for these cards (people)", ""]
    lines += [
        "Said unusual = 'a bit' or 'very unusual'; would check = 'maybe' or 'yes'. Each share "
        "is pooled over the group's cards and people.",
        "",
    ]
    lines += _table(STRATA_HEADER, _strata_rows(humans))
    others = [m for m in humans["headline"] if m["name"] in ("normal_B", DIFFERENCE_NAME)]
    header = ["Measure", "Result [95% interval]", "People", "Cards", "Answers"]
    lines += _table(header, _metric_rows(others))
    lines += [
        "Secondary, and only a description of this card mix (the cards were chosen to include "
        "the engine's mistakes, so rho mixes design and agreement):",
        "",
    ]
    lines += _table(header, _metric_rows(humans["secondary"]))
    lines += ["### With no attention screen", ""]
    lines += [
        f"The same table for everyone who answered this bank ({everyone['raters']} people), "
        "whether or not they passed the attention checks. Values only.",
        "",
    ]
    return lines + _table(STRATA_HEADER, _strata_rows(everyone))


def _pairs_section(pairs: Mapping) -> list[str]:
    lines = ["## 4. Daily choices (pairs)", ""]
    lines += [
        "Each pair is two agent-days from the same day; people picked the one to check first. "
        "'Agrees with engine' = picked the card ranked higher on that day's list.",
        "",
    ]
    rows = [
        [
            entry["type"],
            entry["pairs"],
            format_estimate(entry["agree"]),
            format_estimate(entry["gray"]) if entry["gray"] else "-",
            entry["agree"]["answers"],
        ]
        for entry in pairs["by_type"]
    ]
    rows.append(
        [
            "**all pairs**",
            sum(e["pairs"] for e in pairs["by_type"]),
            format_estimate(pairs["agree_all"]),
            format_estimate(pairs["gray_all"]),
            pairs["agree_all"]["answers"],
        ]
    )
    lines += _table(
        ["Pair type", "Pairs", "Agrees with engine", "Chose the gray card", "Answers"], rows
    )
    close = pairs.get("close_pairs") or []
    lines += [
        f"Pairs where the engine clearly prefers one card (M at least x{MIN_CLEAR_MARGIN:g} the "
        f"other's): agrees {format_estimate(pairs['agree_clear'])}. Close pairs "
        f"({len(close)}: {', '.join(close) or 'none'}), where agreeing is close to a coin "
        f"flip: agrees {format_estimate(pairs['agree_close'])}.",
        "",
        f"Chose the card shown first: {format_estimate(pairs['first_shown'])} "
        "(50% means no position bias).",
        "",
    ]
    per_pair = [
        [
            p["pair"],
            p["type"],
            p["engine_prefers"],
            p["gray_card"] or "-",
            ", ".join(f"{cid} x{m:.2f}" for cid, m in p["M"].items()) or "-",
            f"x{_num(p['margin'])}" + (" (close)" if p["close"] else ""),
            p["n"],
            _pct(p["agree"]),
            _pct(p["gray"]),
        ]
        for p in pairs["per_pair"]
    ]
    lines += _table(
        ["Pair", "Type", "Engine prefers", "Gray card", "M", "Margin", "n", "Agree", "Chose gray"],
        per_pair,
    )
    return lines


def _reason_section(reason: Mapping, claude_reason: Mapping | None) -> list[str]:
    lines = ["## 5. Why it stood out", ""]
    pooled = reason["pooled"] | {"kind": "share"}
    lines += [
        f"On cards people found unusual, they ticked at least one row in "
        f"{reason['ticking_answers']} of {reason['flagged_answers']} answers. On cards where "
        f"the engine's M is at least x{reason['min_m']:g} (below it the strongest dimension "
        f"is noise), the rows ticked included the row of the engine's strongest dimension in "
        f"{format_estimate(pooled)} (people {pooled['raters']}, cards {pooled['items']}, "
        f"answers {pooled['answers']}). Read the per-card table more than this pooled number.",
        "",
    ]
    if claude_reason is not None:
        claude_pooled = claude_reason["pooled"] | {"kind": "share"}
        lines += [
            f"Claude runs: {format_estimate(claude_pooled)} (answers {claude_pooled['answers']}).",
            "",
        ]
    if reason["skipped_cards"]:
        skipped = ", ".join(
            f"{c['card']} ({c['strongest'] or 'none'}, {c['why']})" for c in reason["skipped_cards"]
        )
        lines += [f"Cards left out: {skipped}.", ""]
    lines += _table(
        ["Card", "Group", "Strongest (row)", "Ticked", "Ticked that row", "Most ticked"],
        [
            [
                c["card"],
                c["stratum"],
                f"{c['strongest']} ({c['strongest_row']})",
                c["ticked"],
                _pct(c["share_with_row"]),
                ", ".join(c["most_ticked"]) or "-",
            ]
            for c in reason["per_card"]
        ],
    )
    lines += [
        "Rows ticked over all scored cards. A **blind spot** is a row people see and use that "
        "no engine dimension maps to. A row people never see cannot be a blind spot; ticks on "
        f"it are noise ({reason['hidden_row_ticks']} here).",
        "",
    ]
    lines += _table(
        [
            "Row",
            "Engine dimensions",
            "Ticks",
            "Share of ticking answers",
            "Blind spot",
            "Top cards",
        ],
        [
            [
                f"{r['label']} (`{r['row']}`)",
                ", ".join(r["dimensions"]) or "-",
                r["ticks"],
                _pct(r["share_of_ticking_answers"]),
                "yes" if r["blind_spot"] else ("not shown" if not r["shown"] else ""),
                ", ".join(r["top_cards"]) or "-",
            ]
            for r in reason["rows"]
        ],
    )
    return lines


def _groups_section(result: Mapping) -> list[str]:
    columns = [("All people", result["humans"])]
    columns += [(TECH_GROUPS.get(t, t.capitalize()), g) for t, g in result["groups"].items()]
    if result["claude"]:
        columns.append(("Claude runs", result["claude"]))
    by_name = [{m["name"]: m for m in group["headline"]} for _, group in columns]
    rows = [["Raters", *(group["raters"] for _, group in columns)]]
    for metric in result["humans"]["headline"]:
        name = metric["name"]
        rows.append([metric["label"], *(format_estimate(group[name]) for group in by_name)])
    rows.append(
        [
            "Pairs: agrees with engine",
            *(format_estimate(group["pairs"]["agree_all"]) for _, group in columns),
        ]
    )
    rows.append(
        [
            "Pairs: chose the gray card",
            *(format_estimate(group["pairs"]["gray_all"]) for _, group in columns),
        ]
    )
    rows.append(
        [
            "Ticked the strongest dimension's row",
            *(format_estimate(group["reason"]["pooled"]) for _, group in columns),
        ]
    )
    lines = ["## 6. By background (and Claude)", ""]
    lines += [
        "Groups of 2-7 people: values and n only, no brackets (only 'All people' has them). "
        "Read this as a description, not as a comparison of groups.",
        "",
    ]
    return lines + _table(["Measure", *(name for name, _ in columns)], rows)


def _agreement_section(agreement: Mapping) -> list[str]:
    lines = ["## 7. Claude next to people: agreement with the human majority", ""]
    lines += [
        "For each card, the majority answer of the other kept people (the rater being scored "
        "is left out; Claude is never in it). A tie between k answers gives 1/k credit to "
        "each of them. 'Place' is the share of people Claude beats (ties half): 50% is the "
        "middle of the people.",
        "",
    ]
    spread = agreement["human_spread"]
    rows = [
        [
            "People: median (range)",
            *(
                f"{_pct(spread[n]['median'])} ({_pct(spread[n]['min'])}-{_pct(spread[n]['max'])})"
                for n in (*CARD_FIELDS, "pairs")
            ),
        ]
    ]
    for run in agreement["claude"]:
        rows.append(
            [
                f"Claude `{run['pid']}`",
                *(
                    f"{_pct(run[n]['share'])} (place {_pct(run[n]['place_among_humans'])})"
                    for n in (*CARD_FIELDS, "pairs")
                ),
            ]
        )
    lines += _table(["", "How unusual", "Would check", "Pair choice"], rows)
    people = [
        [
            run["pid"],
            *(f"{_pct(run[n]['share'])} (n={run[n]['n']})" for n in (*CARD_FIELDS, "pairs")),
        ]
        for run in agreement["humans"]
    ]
    lines += ["Each person against the others:", ""]
    return lines + _table(["Person", "How unusual", "Would check", "Pair choice"], people)


def _kappa_section(kappa: Mapping) -> list[str]:
    lines = ["## 8. How much people agree with each other (descriptive)", ""]
    lines += [
        "Krippendorff's alpha with the answers in order (normal < a bit < very; no < maybe < "
        "yes) is the headline; Fleiss' kappa, which ignores the order, is beside it. 0 = no "
        "more agreement than chance, 1 = full agreement. Scored cards only.",
        "",
    ]
    rows = []
    for group_name, group in (("People", kappa["humans"]), ("Claude runs", kappa["claude"])):
        if group is None:
            continue
        for name in CARD_FIELDS:
            entry = group[name]
            rows.append(
                [
                    group_name,
                    QUESTION_WORDS[name],
                    _num(entry["alpha"]),
                    entry["alpha_words"],
                    _num(entry["kappa"]),
                    entry["raters"],
                    entry["cards"],
                ]
            )
    header = ["Group", "Question", "Alpha (ordinal)", "In words", "Fleiss' kappa", "Raters"]
    return lines + _table([*header, "Cards"], rows)


def _positions_section(positions: Mapping) -> list[str]:
    lines = ["## 9. Position in the survey", ""]
    if not positions["raters_with_order"]:
        return [*lines, f"No card order was recorded ({NOT_AVAILABLE}).", ""]
    lines += [
        f"Each person's cards split at card {positions['half']} of their own order "
        f"({positions['raters_with_order']} people). A large gap suggests tiredness or drift.",
        "",
    ]
    rows = [
        [
            label,
            _pct(positions[f"check_{which}"]),
            positions[f"answers_{which}"],
            _num(positions[f"median_seconds_{which}"], 1),
        ]
        for label, which in (("First half", "first"), ("Second half", "second"))
    ]
    return lines + _table(["Cards seen", "Would check", "Answers", "Median seconds"], rows)


def render_markdown(result: Mapping) -> str:
    """The full markdown report for one analysis result."""
    lines = ["# Bot Day Check: results of the human study", ""]
    quality = result["quality"]
    if quality.get("synthetic"):
        lines += [
            f"> **Synthetic data.** {quality['synthetic']} of the {quality['received']} "
            "responses are marked synthetic: this report shows the analysis path, not results "
            "of the study.",
            "",
        ]
    lines += [
        "People judged single AI-agent days against that agent's own usual days; this report "
        "sets their answers next to the dynamic layer's verdicts. " + _settings_line(result),
        "",
        *_context_lines(result.get("context")),
        "## How to read this",
        "",
        HOW_TO_READ,
        "",
    ]
    lines += _quality_section(result["quality"])
    lines += _cards_section(result["cards"], result["claude"] is not None)
    lines += _headline_section(result["humans"], result["no_attention_screen"])
    lines += _pairs_section(result["humans"]["pairs"])
    claude_reason = result["claude"]["reason"] if result["claude"] else None
    lines += _reason_section(result["humans"]["reason"], claude_reason)
    lines += _groups_section(result)
    lines += _agreement_section(result["agreement"])
    lines += _kappa_section(result["kappa"])
    lines += _positions_section(result["positions"])
    return "\n".join(lines).rstrip() + "\n"


# --- command line ------------------------------------------------------------------------------


def _read_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: Sequence[str] | None = None) -> int:
    """Read responses, key and items; write the markdown report and the JSON result."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--responses",
        type=Path,
        required=True,
        help="JSON list of response documents (humans and Claude runs)",
    )
    parser.add_argument("--key", type=Path, required=True, help="the private key.json")
    parser.add_argument("--items", type=Path, required=True, help="the public items.json")
    parser.add_argument("--out", type=Path, required=True, help="markdown report to write")
    parser.add_argument("--json-out", type=Path, help="JSON result (default: --out as .json)")
    parser.add_argument("--draws", type=int, default=DEFAULT_DRAWS, help="bootstrap draws")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="bootstrap seed")
    args = parser.parse_args(argv)
    if args.draws < 0:
        parser.error("--draws must be zero or more")
    study = load_study(_read_json(args.key), _read_json(args.items))
    documents = unwrap_documents(_read_json(args.responses))
    result = analyse(documents, study, draws=args.draws, seed=args.seed)
    json_out = args.json_out or args.out.with_suffix(".json")
    for path in (args.out, json_out):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_markdown(result), encoding="utf-8")
    json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    kept = result["quality"]["by_kind"]
    print(
        f"kept {kept[HUMAN]['kept']} people and {kept[CLAUDE]['kept']} Claude runs; "
        f"wrote {args.out} and {json_out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
