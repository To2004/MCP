"""Tests for the Bot Day Check web page build and the answer collector.

The page embeds the public ``items.json`` only; the collector turns store exports, pasted
answer codes and Claude runs into the response documents ``analyse_responses.py`` reads.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reports.experiments.dynamic_dimensions.human_study import analyse_responses as ar
from reports.experiments.dynamic_dimensions.human_study import build_page as bp
from reports.experiments.dynamic_dimensions.human_study import collect_responses as cr

STUDY_DIR = (
    Path(__file__).resolve().parents[1] / "reports/experiments/dynamic_dimensions/human_study"
)
TEMPLATE = '<p>page</p><script type="application/json" id="bank">__BANK_JSON__</script>'


def _load(name: str) -> dict:
    return json.loads((STUDY_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def items() -> dict:
    return _load("items.json")


@pytest.fixture(scope="module")
def key() -> dict:
    return _load("key.json")


def _document(pid: str = "p1", cards: int = 1) -> dict:
    return {
        "pid": pid,
        "bank_version": "dyn-human-v1",
        "cards": {
            f"c{i}": {"unusual": 1, "check": 0, "stood_out": ["hours"]} for i in range(cards)
        },
        "pairs": {},
        "rater": "human",
    }


# --- build_page --------------------------------------------------------------------------------


def test_build_refuses_a_bank_with_key_fields():
    with pytest.raises(ValueError, match="stratum"):
        bp.build_page({"cards": [{"id": "c1", "stratum": "A"}]}, TEMPLATE)


def test_build_needs_exactly_one_placeholder():
    with pytest.raises(ValueError, match="exactly once"):
        bp.build_page({"cards": []}, "<p>no placeholder</p>")
    with pytest.raises(ValueError, match="exactly once"):
        bp.build_page({"cards": []}, TEMPLATE + TEMPLATE)


def test_bank_text_cannot_close_the_script_element():
    page = bp.build_page({"text": "a </script><b>x</b>"}, TEMPLATE)
    assert "</script><b>" not in page
    embedded = page.split('id="bank">', 1)[1].rsplit("</script>", 1)[0]
    assert json.loads(embedded) == {"text": "a </script><b>x</b>"}


def test_real_page_holds_the_bank_and_nothing_from_the_key(items, key):
    template = (STUDY_DIR / "web" / "index.template.html").read_text(encoding="utf-8")
    page = bp.build_page(items, template)
    embedded = page.split('id="bank">', 1)[1].split("</script>", 1)[0]
    assert json.loads(embedded.replace("<\\/", "</")) == items
    agents = [card["agent"] for card in key["cards"].values() if card["agent"]]
    assert agents, "the key names the simulated agents"
    for agent in agents:
        assert agent not in page
    assert key["id_salt"] not in page


def test_committed_page_is_up_to_date(items):
    template = (STUDY_DIR / "web" / "index.template.html").read_text(encoding="utf-8")
    built = (STUDY_DIR / "web" / "index.html").read_text(encoding="utf-8")
    assert built == bp.build_page(items, template), "rerun build_page.py"


# --- answer codes ------------------------------------------------------------------------------


def test_answer_code_round_trip():
    document = _document(cards=3)
    code = cr.encode_answer_code(document)
    assert code.startswith(cr.CODE_PREFIX) and code.endswith(cr.CODE_END)
    assert cr.decode_answer_code(code) == document


def test_codes_survive_line_breaks_and_surrounding_text():
    first, second = cr.encode_answer_code(_document("p1")), cr.encode_answer_code(_document("p2"))
    wrapped = first[:40] + "\n  " + first[40:]
    text = f"Hi,\nhere it is: {wrapped}\nThanks!\n\nanother one {second}"
    found = cr.find_answer_codes(text)
    assert [cr.decode_answer_code(code)["pid"] for code in found] == ["p1", "p2"]


def test_code_without_closing_stop_still_decodes():
    code = cr.encode_answer_code(_document()).removesuffix(cr.CODE_END)
    assert cr.decode_answer_code(code)["pid"] == "p1"


@pytest.mark.parametrize(
    "bad",
    ["hello", "BDC1-!!!.", cr.CODE_PREFIX + "eyJhIjogMX0."],  # the last one is {"a": 1}
)
def test_bad_codes_raise(bad):
    with pytest.raises(cr.CollectError):
        cr.decode_answer_code(bad)


# --- store exports and merging -----------------------------------------------------------------


def test_documents_found_inside_any_store_export_shape():
    export = {
        "documents": [
            {"id": "u1", "data": {"runs": {"p1": _document("p1")}, "updated": "t"}},
            {"id": "u2", "data": {"runs": {"p2": _document("p2"), "p3": _document("p3")}}},
        ]
    }
    assert sorted(d["pid"] for d in cr.documents_in(export)) == ["p1", "p2", "p3"]
    assert cr.documents_in([_document("p4")])[0]["pid"] == "p4"


def test_merge_keeps_the_fuller_copy_of_a_run():
    partial, full = _document("p1", cards=2), _document("p1", cards=5)
    merged = cr.merge_documents([partial, full, _document("p2")])
    assert {d["pid"]: len(d["cards"]) for d in merged} == {"p1": 5, "p2": 1}


# --- Claude runs -------------------------------------------------------------------------------


def test_claude_run_maps_cards_txt_numbers_to_bank_ids(items):
    run = {
        "finished": "2026-10-25T08:26:34+00:00",
        "cards": [
            {"id": "Card 2", "unusual": 1, "check": 0, "stood_out": ["Quick repeats"]},
            {"id": "3", "unusual": 0, "check": 0, "stood_out": []},
        ],
        "pairs": [{"id": "Pair 1", "chose": "B"}, {"id": "Pair 2", "chose": "Agent A"}],
    }
    document = cr.claude_document(run, 1, items, "model-x")
    assert document["rater"] == "claude" and document["model"] == "model-x"
    second = items["cards"][1]["id"]
    assert document["cards"][second] == {
        "unusual": 1,
        "check": 0,
        "stood_out": ["repeats"],
        "order": 1,
    }
    assert items["cards"][2]["id"] in document["cards"]
    pair_one, pair_two = items["pairs"][0], items["pairs"][1]
    assert document["pairs"][pair_one["id"]]["chose"] == pair_one["cards"][1]["id"]
    assert document["pairs"][pair_one["id"]]["top"] == pair_one["cards"][0]["id"]
    assert document["pairs"][pair_two["id"]]["chose"] == pair_two["cards"][0]["id"]


@pytest.mark.parametrize(
    "run, message",
    [
        ({"cards": [{"id": "Card 99", "unusual": 0, "check": 0}], "pairs": []}, "not in the bank"),
        ({"cards": [{"id": "x", "unusual": 0, "check": 0}], "pairs": []}, "no number"),
        (
            {"cards": [{"id": "1", "unusual": 1, "check": 0, "stood_out": ["Mood"]}], "pairs": []},
            "unknown line",
        ),
        ({"cards": [], "pairs": [{"id": "Pair 1", "chose": "C"}]}, "not A or B"),
    ],
)
def test_bad_claude_runs_raise(items, run, message):
    with pytest.raises(cr.CollectError, match=message):
        cr.claude_document(run, 1, items, "model-x")


def test_committed_claude_runs_are_complete_and_kept(items, key):
    documents = cr.collect([], [], [STUDY_DIR / "claude_ratings.json"], items)
    assert len(documents) == 5
    assert all(d["rater"] == "claude" and d["finished"] for d in documents)
    assert all(len(d["cards"]) == len(items["cards"]) for d in documents)
    assert all(len(d["pairs"]) == len(items["pairs"]) for d in documents)
    result = ar.analyse(documents, ar.load_study(key, items), draws=0)
    claude = result["quality"]["by_kind"]["claude"]
    assert claude["kept"] == 5 and claude["complete"] == 5
