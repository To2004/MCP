"""Tests for the human-study analysis of the dynamic layer (Bot Day Check).

Most inputs are synthetic: a small key and item bank in the documented formats, and response
documents from perfect, random, careless and partial raters, plus Claude runs. One test runs the
analysis on the committed key.json and items.json with synthetic responses in the documented
format.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from reports.experiments.dynamic_dimensions.human_study import analyse_responses as ar

BANK = "dyn-human-test"
DRAWS = 200
STUDY_DIR = (
    Path(__file__).resolve().parents[1] / "reports/experiments/dynamic_dimensions/human_study"
)
PRACTICE_ID = "cP01"
CLOSE_PAIR = "p08"
ROW_IDS = (
    "hours",
    "actions",
    "projects",
    "changes",
    "kinds",
    "upload",
    "downloads",
    "repeats",
    "connection",
)
BLIND_ROW = "downloads"  # no engine dimension maps to it
ROW_MAP = {
    "time_of_day": "hours",
    "session_length": "hours",
    "calls_last_hour": "actions",
    "asset": "projects",
    "writes_last_hour": "changes",
    "tool": "kinds",
    "request_too_big": "upload",
    "same_call_10m": "repeats",
    "network": "connection",
    "client": "connection",
    "sequence": None,
}
#: (card id, stratum, M, listed, list rank, strongest dimension)
SCORED = (
    ("cA01", "A", 4.6, True, 1, "asset"),
    ("cA02", "A", 4.1, True, 2, "same_call_10m"),
    ("cA03", "A", 3.6, True, 3, "writes_last_hour"),
    ("cA04", "A", 3.2, True, 4, "request_too_big"),
    ("cB01", "B_false_alarm", 3.4, True, 1, "network"),
    ("cB02", "B", 3.0, True, 2, "time_of_day"),
    ("cB03", "B", 2.7, True, 4, "tool"),
    ("cC01", "C", 1.8, False, None, "calls_last_hour"),
    ("cC02", "C", 1.5, False, None, "writes_last_hour"),
    ("cC03", "C", 1.3, False, None, "asset"),
    ("cD01", "D", 3.3, False, None, "network"),
    ("cD02", "D", 1.2, False, None, "client"),
    ("cD03", "D", 0.9, False, None, "session_length"),
    ("cE01", "E", 1.0, False, None, "calls_last_hour"),
    ("cE02", "E", 0.9, False, None, "tool"),
    ("cE03", "E", 0.8, False, None, None),
)
ATTENTION = (("cN01", "normal"), ("cW01", "wild"))
#: (pair id, type, card ids, engine prefers, gray card)
PAIRS = (
    ("p01", "gray_over_ordinary", ("q01", "q02"), "q01", "q01"),
    ("p02", "gray_over_ordinary", ("q03", "q04"), "q04", "q04"),
    ("p03", "gray_over_ordinary", ("q05", "q06"), "q05", "q05"),
    ("p04", "false_alarm_over_gray", ("q07", "q08"), "q07", "q08"),
    ("p05", "false_alarm_over_gray", ("q09", "q10"), "q10", "q09"),
    ("p06", "false_alarm_over_gray", ("q11", "q12"), "q11", "q12"),
    ("p07", "both_listed", ("q13", "q14"), "q13", None),
    ("p08", "both_listed", ("q15", "q16"), "q16", "q15"),
)
ALL_CARDS = [spec[0] for spec in SCORED] + [cid for cid, _ in ATTENTION]


def make_items(hide: tuple[str, ...] = ()) -> dict:
    rows = [{"id": row, "label": row.title(), "shown": row not in hide} for row in ROW_IDS]
    order = random.Random(3).sample(ALL_CARDS, len(ALL_CARDS))
    cards = [
        {
            "id": cid,
            "who": "An agent",
            "day": "Monday",
            "calendar": None,
            "company": None,
            "rows": [],
        }
        for cid in order
    ]
    pairs = [{"id": pid, "cards": [{"id": a}, {"id": b}]} for pid, _, (a, b), _, _ in PAIRS]
    practice = [{"id": PRACTICE_ID, "rows": [], "feedback": {"unusual": 0, "check": 0}}]
    return {
        "bank_version": BANK,
        "rows": rows,
        "practice": practice,
        "cards": cards,
        "pairs": pairs,
    }


def make_key() -> dict:
    cards = {
        cid: {
            "stratum": stratum,
            "gray_kind": "scope_creep" if stratum[0] in "AC" else None,
            "tags": ["vacation"] if stratum == "D" else [],
            "org_event": None,
            "agent": "a001",
            "day": 120,
            "M": m,
            "R": m,
            "strongest": strongest,
            "s2": None,
            "listed": listed,
            "list_rank": rank,
            "attention": None,
        }
        for cid, stratum, m, listed, rank, strongest in SCORED
    }
    for cid, check in ATTENTION:
        cards[cid] = {
            "stratum": None,
            "gray_kind": None,
            "tags": [],
            "org_event": None,
            "M": None,
            "listed": False,
            "list_rank": None,
            "strongest": None,
            "attention": check,
        }
    pairs = {}
    for pid, kind, (a, b), prefers, gray in PAIRS:
        other = b if prefers == a else a
        low = 2.9 if pid == CLOSE_PAIR else 1.5  # one close pair: x3.0 against x2.9
        pairs[pid] = {
            "type": kind,
            "engine_prefers": prefers,
            "gray_card": gray,
            "M": {prefers: 3.0, other: low},
        }
    return {
        "bank_version": BANK,
        "engine": {
            "design": "v4",
            "git_sha": "abc1234",
            "profile": "main",
            "agents": 150,
            "seed": 7,
        },
        "row_map": ROW_MAP,
        "cards": cards,
        "pairs": pairs,
        "practice": {},
    }


@pytest.fixture
def study() -> ar.Study:
    return ar.load_study(make_key(), make_items())


def engine_like_unusual(m: float) -> int:
    if m >= 3.0:
        return 2
    return 1 if m >= 1.25 else 0


def attention_answers(normal: int = 0, wild: int = 2) -> dict:
    return {
        "cN01": {"unusual": normal, "check": 0, "stood_out": [], "ms": 6000, "order": 16},
        "cW01": {"unusual": wild, "check": 2, "stood_out": ["upload"], "ms": 6000, "order": 17},
    }


def perfect_cards() -> dict:
    """Answers that follow the engine: unusual by M, check exactly on listed cards."""
    cards = attention_answers()
    for order, (cid, _, m, listed, _, strongest) in enumerate(SCORED):
        unusual = engine_like_unusual(m)
        row = ROW_MAP.get(strongest) if strongest else None
        cards[cid] = {
            "unusual": unusual,
            "check": 2 if listed else 0,
            "stood_out": [row] if unusual and row else [],
            "ms": 9000,
            "order": order,
        }
    return cards


def perfect_pairs() -> dict:
    return {
        pid: {"chose": prefers, "top": a, "ms": 7000, "order": i}
        for i, (pid, _, (a, _b), prefers, _) in enumerate(PAIRS)
    }


def random_cards(rng: random.Random) -> dict:
    cards = attention_answers()
    for order, (cid, *_rest) in enumerate(SCORED):
        unusual = rng.choice(ar.ANSWER_LEVELS)
        ticked = rng.sample(ROW_IDS, 2) if unusual else []
        cards[cid] = {
            "unusual": unusual,
            "check": rng.choice(ar.ANSWER_LEVELS),
            "stood_out": ticked,
            "ms": 8000,
            "order": order,
        }
    return cards


def random_pairs(rng: random.Random) -> dict:
    return {
        pid: {"chose": rng.choice(ids), "top": ids[0], "ms": 5000, "order": i}
        for i, (pid, _, ids, _, _) in enumerate(PAIRS)
    }


def response(
    pid: str,
    cards: dict,
    pairs: dict,
    rater: str = "human",
    tech: str = "no",
    finished: str | None = "2026-10-20T10:15:00+00:00",
    version: str = BANK,
) -> dict:
    return {
        "pid": pid,
        "bank_version": version,
        "started": "2026-10-20T10:00:00+00:00",
        "finished": finished,
        "background": {"tech": tech, "ai_use": "sometimes"},
        "cards": cards,
        "pairs": pairs,
        "mobile": False,
        "rater": rater,
    }


def perfect_panel(count: int, tech: str = "no") -> list[dict]:
    return [
        response(f"h{i:02d}", perfect_cards(), perfect_pairs(), tech=tech) for i in range(count)
    ]


def metric(group: dict, name: str) -> dict:
    found = group["headline"] + group["strict"] + group["secondary"]
    return next(m for m in found if m["name"] == name)


# --- loading -----------------------------------------------------------------------------------


def test_load_study_joins_items_and_key(study: ar.Study) -> None:
    assert study.row_ids == ROW_IDS
    assert len(study.scored_cards) == len(SCORED)
    assert {card.attention for card in study.attention_cards} == {"normal", "wild"}
    assert study.cards["cB01"].stratum == "B"  # "B_false_alarm" reads as B
    assert study.cards["cA02"].expected_row == "repeats"
    assert study.cards["cE03"].expected_row is None
    assert study.row_dimensions[BLIND_ROW] == ()
    assert study.row_dimensions["connection"] == ("client", "network")
    assert list(study.cards) == [card["id"] for card in make_items()["cards"]]
    assert study.practice_ids == {PRACTICE_ID} and study.hidden_rows == frozenset()
    assert study.pairs[CLOSE_PAIR].close and not study.pairs["p01"].close
    assert study.pairs["p01"].margin == pytest.approx(2.0)


def test_load_study_rejects_a_different_bank_version() -> None:
    key = make_key() | {"bank_version": "other"}
    with pytest.raises(ar.StudyInputError, match="bank_version"):
        ar.load_study(key, make_items())


def test_load_study_rejects_cards_missing_from_the_key() -> None:
    key = make_key()
    del key["cards"]["cA01"]
    with pytest.raises(ar.StudyInputError, match="cards"):
        ar.load_study(key, make_items())


def test_load_study_rejects_a_word_that_only_starts_with_a_stratum_letter() -> None:
    key = make_key()
    key["cards"]["cD01"]["stratum"] = "benign_change"
    with pytest.raises(ar.StudyInputError, match="stratum"):
        ar.load_study(key, make_items())


def test_load_study_rejects_a_pair_choice_outside_the_pair() -> None:
    key = make_key()
    key["pairs"]["p01"]["engine_prefers"] = "q99"
    with pytest.raises(ar.StudyInputError, match="engine_prefers"):
        ar.load_study(key, make_items())


def test_unwrap_documents_accepts_list_store_rows_and_mapping() -> None:
    doc = response("h1", {}, {})
    assert ar.unwrap_documents([doc]) == [doc]
    assert ar.unwrap_documents([{"id": "x", "data": doc}]) == [doc]
    assert ar.unwrap_documents({"x": doc}) == [doc]
    assert ar.unwrap_documents(doc) == [doc]
    with pytest.raises(ar.StudyInputError):
        ar.unwrap_documents("not a list")


# --- statistics helpers ------------------------------------------------------------------------


def test_spearman_handles_order_ties_and_no_spread() -> None:
    assert ar.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert ar.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert ar.average_ranks([5, 1, 5, 3]) == [3.5, 1.0, 3.5, 2.0]
    assert ar.spearman([1, 2, 3], [1, 1, 1]) is None
    assert ar.spearman([1, 2], [1, 2]) is None


def test_fleiss_kappa_matches_the_textbook_example() -> None:
    # Fleiss (1971) style worked example: 10 items, 14 raters, 5 categories -> 0.210.
    table = [
        [0, 0, 0, 0, 14],
        [0, 2, 6, 4, 2],
        [0, 0, 3, 5, 6],
        [0, 3, 9, 2, 0],
        [2, 2, 8, 1, 1],
        [7, 7, 0, 0, 0],
        [3, 2, 6, 3, 0],
        [2, 5, 3, 2, 2],
        [6, 5, 2, 1, 0],
        [0, 2, 2, 3, 7],
    ]
    assert ar.fleiss_kappa(table) == pytest.approx(0.210, abs=0.001)
    assert ar.fleiss_kappa([[3, 0, 0], [0, 3, 0], [0, 0, 3]]) == pytest.approx(1.0)
    assert ar.fleiss_kappa([[1, 0, 0]]) is None  # one rater per item: nothing to compare
    assert ar.kappa_words(0.15) == "slight"
    assert ar.kappa_words(-0.1) == "less than chance"
    assert ar.kappa_words(0.95) == "almost perfect"


def test_krippendorff_alpha_matches_the_published_example() -> None:
    # Krippendorff (2011), "Computing Krippendorff's alpha-reliability": 4 coders, 12 units.
    coders = (
        "1 2 3 3 2 1 4 1 2 . . .",
        "1 2 3 3 2 2 4 1 2 5 . 3",
        ". 3 3 3 2 3 4 2 2 5 1 .",
        "1 2 3 3 2 4 4 1 2 5 1 .",
    )
    values = [line.split() for line in coders]
    table = []
    for unit in range(12):
        row = [0] * 5
        for coder in values:
            if coder[unit] != ".":
                row[int(coder[unit]) - 1] += 1
        table.append(row)
    assert ar.krippendorff_alpha(table, ar.NOMINAL) == pytest.approx(0.743, abs=0.001)
    assert ar.krippendorff_alpha(table, ar.ORDINAL) == pytest.approx(0.815, abs=0.001)
    assert ar.krippendorff_alpha([[3, 0, 0], [0, 3, 0], [0, 0, 3]]) == pytest.approx(1.0)
    assert ar.krippendorff_alpha([[1, 0, 0]]) is None


def test_majority_credit_splits_ties_and_placement_counts_ties_half() -> None:
    assert ar.majority_credit(1, [1, 1, 0]) == 1.0
    assert ar.majority_credit(0, [1, 1, 0]) == 0.0
    assert ar.majority_credit(1, [0, 1]) == 0.5
    assert ar.placement(0.6, [0.4, 0.6, 0.8, 0.9]) == pytest.approx(0.375)
    assert ar.placement(None, [0.5]) is None


def test_bootstrap_is_deterministic_and_brackets_the_estimate() -> None:
    cells = {f"r{i}": {f"i{j}": (i + j) % 3 for j in range(6)} for i in range(8)}
    raters = list(cells)
    groups = [["i0", "i1", "i2"], ["i3", "i4", "i5"]]
    first = ar.share_estimate(cells, raters, groups, ar.PREDICATES["flagged"], DRAWS, "s")
    again = ar.share_estimate(cells, raters, groups, ar.PREDICATES["flagged"], DRAWS, "s")
    assert first == again
    assert first.low <= first.value <= first.high
    assert (first.raters, first.items, first.answers, first.draws) == (8, 6, 48, DRAWS)


# --- perfect raters ----------------------------------------------------------------------------


def test_perfect_raters_track_the_engine(study: ar.Study) -> None:
    result = ar.analyse(perfect_panel(8), study, draws=DRAWS)
    humans = result["humans"]
    rho = metric(humans, "rho_m_unusual")
    assert rho["value"] > 0.85 and -1 <= rho["low"] <= rho["value"] <= rho["high"] <= 1
    assert (rho["raters"], rho["items"]) == (8, len(SCORED))
    assert metric(humans, "check_A")["value"] == 1.0
    assert metric(humans, "check_B")["value"] == 1.0
    assert metric(humans, "normal_B")["value"] == 0.0
    assert metric(humans, "check_C")["value"] == 0.0
    assert metric(humans, "check_E")["value"] == 0.0
    assert metric(humans, "check_A_minus_B")["value"] == 0.0
    assert humans["pairs"]["agree_all"]["value"] == 1.0
    assert humans["pairs"]["agree_clear"]["items"] == len(PAIRS) - 1
    assert humans["pairs"]["agree_close"]["items"] == 1
    assert humans["pairs"]["close_pairs"] == [CLOSE_PAIR]
    assert humans["pairs"]["first_shown"]["answers"] == 8 * len(PAIRS)
    assert result["kappa"]["humans"]["unusual"]["kappa"] == pytest.approx(1.0)
    assert result["kappa"]["humans"]["unusual"]["alpha"] == pytest.approx(1.0)
    assert [entry["stratum"] for entry in humans["strata"]] == list("ABCDE")
    assert all(m["name"] != "check_listed" for m in humans["headline"])
    assert all(row["unusual"]["share"] == 1.0 for row in result["agreement"]["humans"])


def test_perfect_raters_tick_the_strongest_row_and_never_the_blind_spot(
    study: ar.Study,
) -> None:
    reason = ar.analyse(perfect_panel(5), study, draws=DRAWS)["humans"]["reason"]
    assert reason["pooled"]["value"] == 1.0
    assert reason["blind_spot_ticks"] == 0
    blind = next(row for row in reason["rows"] if row["row"] == BLIND_ROW)
    assert blind["blind_spot"] and blind["ticks"] == 0
    skipped = {card["card"]: card["why"] for card in reason["skipped_cards"]}
    assert skipped["cE03"] == "no row"
    low = {cid for cid, _, m, *_ in SCORED if m < ar.REASON_MIN_M} - {"cE03"}
    assert {cid for cid, why in skipped.items() if why == "low M"} == low
    assert all(card["M"] >= ar.REASON_MIN_M for card in reason["per_card"])


def test_raters_who_tick_an_unmapped_row_show_a_blind_spot(study: ar.Study) -> None:
    cards = perfect_cards()
    cards["cB03"]["stood_out"] = [BLIND_ROW]
    reason = ar.analyse([response("h1", cards, perfect_pairs())], study, draws=DRAWS)
    blind = next(r for r in reason["humans"]["reason"]["rows"] if r["row"] == BLIND_ROW)
    assert blind["ticks"] == 1 and blind["top_cards"] == ["cB03"] and blind["blind_spot"]
    per_card = {c["card"]: c for c in reason["humans"]["reason"]["per_card"]}
    assert per_card["cB03"]["share_with_row"] == 0.0


def test_ticks_on_a_row_people_never_see_are_noise_not_a_blind_spot() -> None:
    hidden = ar.load_study(make_key(), make_items(hide=(BLIND_ROW,)))
    assert hidden.hidden_rows == {BLIND_ROW}
    cards = perfect_cards()
    cards["cB03"]["stood_out"] = [BLIND_ROW]
    reason = ar.analyse([response("h1", cards, perfect_pairs())], hidden, draws=DRAWS)
    reason = reason["humans"]["reason"]
    row = next(r for r in reason["rows"] if r["row"] == BLIND_ROW)
    assert not row["blind_spot"] and not row["shown"]
    assert reason["blind_spot_ticks"] == 0 and reason["hidden_row_ticks"] == 1


def test_a_row_not_recorded_on_every_card_counts_as_hidden() -> None:
    items = make_items()
    for card in items["cards"]:
        card["rows"] = [{"id": BLIND_ROW, "usual": "not recorded", "today": "not recorded"}]
    assert ar.load_study(make_key(), items).hidden_rows == {BLIND_ROW}


def test_people_who_reject_false_alarms_give_a_positive_difference(study: ar.Study) -> None:
    cards = perfect_cards()
    for cid in ("cB01", "cB02", "cB03"):
        cards[cid] = {"unusual": 0, "check": 0, "stood_out": [], "ms": 9000, "order": 1}
    result = ar.analyse(
        [response(f"h{i}", cards, perfect_pairs()) for i in range(4)], study, draws=DRAWS
    )
    assert metric(result["humans"], "check_A_minus_B")["value"] == 1.0
    assert metric(result["humans"], "normal_B")["value"] == 1.0


# --- random raters -----------------------------------------------------------------------------


def test_random_raters_show_a_weak_link_and_chance_agreement(study: ar.Study) -> None:
    rng = random.Random(11)
    docs = [response(f"r{i:02d}", random_cards(rng), random_pairs(rng)) for i in range(40)]
    result = ar.analyse(docs, study, draws=DRAWS)
    rho = metric(result["humans"], "rho_m_unusual")
    assert rho["low"] < 0 < rho["high"]
    assert abs(result["kappa"]["humans"]["unusual"]["kappa"]) < 0.1
    assert abs(result["kappa"]["humans"]["check"]["kappa"]) < 0.1
    assert abs(result["kappa"]["humans"]["unusual"]["alpha"]) < 0.1
    assert 0.3 < result["humans"]["pairs"]["agree_all"]["value"] < 0.7
    perfect = metric(ar.analyse(perfect_panel(40), study, draws=DRAWS)["humans"], "rho_m_unusual")
    assert perfect["value"] > rho["value"]


# --- quality screen ----------------------------------------------------------------------------


def test_attention_failures_and_unverified_raters_are_excluded(study: ar.Study) -> None:
    failed_normal = perfect_cards() | attention_answers(normal=2)
    failed_wild = perfect_cards() | attention_answers(wild=0)
    stopped_early = {
        cid: answer for cid, answer in perfect_cards().items() if cid not in ("cN01", "cW01")
    }
    docs = [
        *perfect_panel(3),
        response("bad1", failed_normal, perfect_pairs()),
        response("bad2", failed_wild, perfect_pairs()),
        response("gone", stopped_early, {}, finished=None),
    ]
    result = ar.analyse(docs, study, draws=DRAWS)
    humans = result["quality"]["by_kind"]["human"]
    assert humans["received"] == 6 and humans["kept"] == 3
    assert humans["excluded"][ar.EXCLUDE_FAILED] == 2
    assert humans["excluded"][ar.EXCLUDE_UNVERIFIED] == 1
    assert humans["attention"]["normal"] == {"passed": 4, "answered": 5}
    assert humans["attention"]["wild"] == {"passed": 4, "answered": 5}
    assert metric(result["humans"], "check_A")["raters"] == 3
    assert result["no_attention_screen"]["raters"] == 6


def test_the_wild_attention_card_passes_with_a_bit_unusual_and_maybe() -> None:
    wild = "wild"
    assert ar.attention_outcome(wild, ar.CardAnswer(1, 1, (), None)) == ar.ATTENTION_PASS
    assert ar.attention_outcome(wild, ar.CardAnswer(2, 0, (), None)) == ar.ATTENTION_FAIL
    assert ar.attention_outcome(wild, ar.CardAnswer(0, 2, (), None)) == ar.ATTENTION_FAIL
    assert ar.attention_outcome(wild, ar.CardAnswer(2, None, (), None)) == ar.ATTENTION_MISSING
    assert ar.attention_outcome("normal", ar.CardAnswer(1, 0, (), None)) == ar.ATTENTION_FAIL
    assert ar.attention_outcome("normal", None) == ar.ATTENTION_MISSING


def test_practice_answers_are_skipped_without_an_issue(study: ar.Study) -> None:
    cards = perfect_cards() | {PRACTICE_ID: {"unusual": 0, "check": 0, "ms": 4000, "order": 0}}
    result = ar.analyse([response("h1", cards, perfect_pairs())], study, draws=DRAWS)
    assert result["quality"]["issues"] == {}
    assert result["quality"]["by_kind"]["human"]["kept"] == 1


def test_partial_response_that_passed_both_checks_is_kept(study: ar.Study) -> None:
    some = {
        cid: answer
        for cid, answer in perfect_cards().items()
        if cid in ("cN01", "cW01", "cA01", "cB01", "cE01")
    }
    docs = [*perfect_panel(2), response("part", some, {}, finished=None)]
    result = ar.analyse(docs, study, draws=DRAWS)
    humans = result["quality"]["by_kind"]["human"]
    assert humans["kept"] == 3 and humans["kept_partial"] == 1 and humans["complete"] == 2
    assert metric(result["humans"], "check_A")["answers"] == 2 * 4 + 1
    assert metric(result["humans"], "check_C")["raters"] == 2
    assert result["humans"]["pairs"]["agree_all"]["raters"] == 2
    cards = {row["card"]: row for row in result["cards"]}
    assert cards["cA01"]["n"] == 3 and cards["cA02"]["n"] == 2


def test_duplicate_version_and_invalid_answers_are_handled(study: ar.Study) -> None:
    short = {cid: a for cid, a in perfect_cards().items() if cid in ("cN01", "cW01", "cA01")}
    broken = perfect_cards()
    broken["cA02"] = {"unusual": 7, "check": 1, "stood_out": ["nope"], "ms": 1, "order": 1}
    broken["cA03"] = {"unusual": 1, "check": True, "stood_out": [], "ms": 1, "order": 2}
    docs = [
        response("dup", short, {}),
        response("dup", perfect_cards(), perfect_pairs()),
        response("old", perfect_cards(), perfect_pairs(), version="dyn-human-v0"),
        response("brk", broken, perfect_pairs()),
        {"bank_version": BANK, "cards": {}, "pairs": {}},
    ]
    result = ar.analyse(docs, study, draws=DRAWS)
    quality = result["quality"]
    humans = quality["by_kind"]["human"]
    assert humans["excluded"][ar.EXCLUDE_DUPLICATE] == 1
    assert humans["excluded"][ar.EXCLUDE_VERSION] == 1
    assert humans["excluded"][ar.EXCLUDE_EMPTY] == 1
    assert humans["kept"] == 2
    kept_dup = next(r for r in quality["raters"] if r["pid"] == "dup" and not r["excluded"])
    assert kept_dup["cards"] == len(ALL_CARDS)
    assert quality["issues"]["invalid 'unusual' answer (dropped)"] == 1
    assert quality["issues"]["invalid 'check' answer (dropped)"] == 1
    assert quality["issues"]["ticked a row that is not in the bank (ignored)"] == 1
    assert quality["issues"]["response without a pid (numbered by position)"] == 1
    assert {row["card"]: row["n"] for row in result["cards"]}["cA02"] == 1


def test_a_fuller_copy_on_an_old_bank_does_not_push_out_the_current_one(
    study: ar.Study,
) -> None:
    short = {cid: a for cid, a in perfect_cards().items() if cid in ("cN01", "cW01", "cA01")}
    docs = [
        response("same", perfect_cards(), perfect_pairs(), version="dyn-human-v0"),
        response("same", short, {}),
        {**response("odd", perfect_cards(), perfect_pairs()), "rater": "robot"},
    ]
    result = ar.analyse(docs, study, draws=DRAWS)
    humans = result["quality"]["by_kind"]["human"]
    assert humans["kept"] == 1
    assert humans["excluded"][ar.EXCLUDE_VERSION] == 1
    assert humans["excluded"][ar.EXCLUDE_DUPLICATE] == 0
    assert result["quality"]["unknown_kind"] == 1


# --- groups and Claude -------------------------------------------------------------------------


def test_background_groups_are_reported_separately(study: ar.Study) -> None:
    rng = random.Random(5)
    docs = [
        *perfect_panel(3, tech="security"),
        *(response(f"n{i}", random_cards(rng), random_pairs(rng), tech="no") for i in range(4)),
    ]
    result = ar.analyse(docs, study, draws=DRAWS)
    assert set(result["groups"]) == {"security", "no"}
    assert result["groups"]["security"]["raters"] == 3
    assert result["groups"]["no"]["raters"] == 4
    assert result["quality"]["background"] == {"security": 3, "no": 4}
    assert result["groups"]["security"]["pairs"]["agree_all"]["value"] == 1.0
    for group in result["groups"].values():
        assert not group["intervals"]
        assert all(m["low"] is None and m["high"] is None for m in group["headline"])
    assert result["humans"]["intervals"]


def opposite_cards() -> dict:
    cards = attention_answers()
    for order, (cid, _, m, listed, _, _) in enumerate(SCORED):
        cards[cid] = {
            "unusual": 2 - engine_like_unusual(m),
            "check": 0 if listed else 2,
            "stood_out": [],
            "ms": 0,
            "order": order,
        }
    return cards


def test_claude_runs_are_their_own_group_and_never_in_the_human_majority(
    study: ar.Study,
) -> None:
    claude_runs = [
        response(f"claude-{i}", opposite_cards(), perfect_pairs(), rater="claude") for i in range(2)
    ]
    result = ar.analyse([*perfect_panel(4), *claude_runs], study, draws=DRAWS)
    assert result["quality"]["by_kind"]["claude"]["kept"] == 2
    assert result["humans"]["raters"] == 4 and result["claude"]["raters"] == 2
    assert metric(result["claude"], "check_A")["value"] == 0.0
    assert metric(result["humans"], "check_A")["value"] == 1.0
    agreement = result["agreement"]
    assert all(row["check"]["share"] == 1.0 for row in agreement["humans"])
    for run in agreement["claude"]:
        assert run["check"]["share"] == 0.0
        assert run["check"]["place_among_humans"] == 0.0
        assert run["pairs"]["share"] == 1.0
        assert run["pairs"]["place_among_humans"] == 0.5
    assert result["kappa"]["claude"]["check"]["raters"] == 2
    cards = {row["card"]: row for row in result["cards"]}
    assert cards["cA01"]["claude_mean_check"] == 0.0 and cards["cA01"]["n"] == 4


def test_claude_runs_with_failed_attention_are_dropped_too(study: ar.Study) -> None:
    bad = response(
        "claude-x", perfect_cards() | attention_answers(normal=1), perfect_pairs(), rater="claude"
    )
    result = ar.analyse([*perfect_panel(2), bad], study, draws=DRAWS)
    assert result["quality"]["by_kind"]["claude"]["excluded"][ar.EXCLUDE_FAILED] == 1
    assert result["claude"] is None


# --- report ------------------------------------------------------------------------------------


def test_markdown_renders_every_section_even_with_nobody_kept(study: ar.Study) -> None:
    failed = response("bad", perfect_cards() | attention_answers(normal=2), {})
    markdown = ar.render_markdown(ar.analyse([failed], study, draws=DRAWS))
    assert "## How to read this" in markdown
    assert markdown.count("\n## ") >= 9
    assert ar.NOT_AVAILABLE in markdown


def test_position_check_splits_each_persons_own_order(study: ar.Study) -> None:
    cards = perfect_cards()
    for cid, answer in cards.items():
        if cid not in dict(ATTENTION):
            answer["check"] = 2 if answer["order"] < len(ALL_CARDS) // 2 else 0
    result = ar.analyse([response("h1", cards, perfect_pairs())], study, draws=DRAWS)
    positions = result["positions"]
    assert positions["raters_with_order"] == 1 and positions["half"] == len(ALL_CARDS) // 2
    assert positions["check_first"] == 1.0 and positions["check_second"] == 0.0


def test_format_estimate_by_kind() -> None:
    share = {"value": 0.62, "low": 0.45, "high": 0.78, "kind": "share"}
    rho = {"value": 0.71, "low": 0.4, "high": 0.88, "kind": "rho"}
    difference = {"value": 0.35, "low": 0.1, "high": 0.58, "kind": "difference"}
    assert ar.format_estimate(share) == "62% [45-78%]"
    assert ar.format_estimate(rho) == "0.71 [0.40, 0.88]"
    assert ar.format_estimate(difference) == "+35 pts [+10, +58]"
    assert ar.format_estimate({"value": None, "low": None, "high": None}) == ar.NOT_AVAILABLE


def test_main_writes_markdown_and_json(tmp_path: Path) -> None:
    rng = random.Random(2)
    docs = [
        *perfect_panel(3, tech="tech"),
        response("r1", random_cards(rng), random_pairs(rng)),
        response("claude-1", perfect_cards(), perfect_pairs(), rater="claude"),
    ]
    paths = {name: tmp_path / f"{name}.json" for name in ("responses", "key", "items")}
    paths["responses"].write_text(json.dumps(docs))
    paths["key"].write_text(json.dumps(make_key()))
    paths["items"].write_text(json.dumps(make_items()))
    out = tmp_path / "report" / "results.md"
    exit_code = ar.main(
        [
            "--responses",
            str(paths["responses"]),
            "--key",
            str(paths["key"]),
            "--items",
            str(paths["items"]),
            "--out",
            str(out),
            "--draws",
            "50",
        ]
    )
    assert exit_code == 0
    markdown = out.read_text()
    assert markdown.startswith("# Bot Day Check")
    assert "Claude runs" in markdown and "Fleiss" in markdown
    result = json.loads(out.with_suffix(".json").read_text())
    assert result["settings"]["draws"] == 50
    assert result["quality"]["by_kind"]["human"]["kept"] == 4
    assert result["claude"]["raters"] == 1


# --- the committed bank ------------------------------------------------------------------------


def committed_response(pid: str, items: dict, rng: random.Random, key: dict) -> dict:
    """A response in the documented format to the committed bank: random answers, attention
    checks answered as the rule expects, order from a card form."""
    form = items["forms"][rng.randrange(len(items["forms"]))]["cards"]
    shown = [row["id"] for row in items["rows"] if row["shown"]]
    cards = {}
    for order, card_id in enumerate(form):
        expected = key["cards"][card_id]["attention"]
        unusual = {"normal": 0, "wild": 2}.get(expected, rng.choice(ar.ANSWER_LEVELS))
        check = {"normal": 0, "wild": 2}.get(expected, rng.choice(ar.ANSWER_LEVELS))
        cards[card_id] = {
            "unusual": unusual,
            "check": check,
            "stood_out": rng.sample(shown, 2) if unusual else [],
            "ms": rng.randint(20_000, 70_000),
            "order": order,
        }
    pairs = {}
    for order, pair in enumerate(items["pairs"]):
        ids = [card["id"] for card in pair["cards"]]
        top = rng.choice(ids)
        pairs[pair["id"]] = {"chose": rng.choice(ids), "top": top, "ms": 60_000, "order": order}
    return response(pid, cards, pairs, version=items["bank_version"])


def test_the_analysis_runs_on_the_committed_key_and_items() -> None:
    items = json.loads((STUDY_DIR / "items.json").read_text())
    key = json.loads((STUDY_DIR / "key.json").read_text())
    study = ar.load_study(key, items)
    assert study.hidden_rows == {"downloads"}
    assert len(study.scored_cards) == 16 and len(study.attention_cards) == 2
    rng = random.Random(4)
    docs = [committed_response(f"h{i:02d}", items, rng, key) for i in range(6)]
    result = ar.analyse(docs, study, draws=50)
    assert result["quality"]["issues"] == {}
    assert result["quality"]["by_kind"]["human"]["kept"] == 6
    assert len(result["cards"]) == len(items["cards"])
    assert len(result["humans"]["pairs"]["per_pair"]) == len(items["pairs"])
    assert result["humans"]["reason"]["hidden_row_ticks"] == 0
    assert result["context"]["list_composition"]
    markdown = ar.render_markdown(result)
    assert "## 9. Position in the survey" in markdown
    assert "Synthetic data" not in markdown
    marked = [doc | {"synthetic": True} for doc in docs]
    flagged = ar.render_markdown(ar.analyse(marked, study, draws=0))
    assert "> **Synthetic data.** 6 of the 6 responses" in flagged
