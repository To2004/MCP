"""AI-3: the priced asset reads only the scan's target inputs, and nothing moves without them.

The scan is the simulated Helios Grid GitHub route
(``reports/experiments/gateway/github_remote``). ``matrix_golden.json`` pins the
``CallScore`` of 24 calls as ``MatrixScorer`` gave them before AI-3 (no ``tool_targets``).
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from mcp_security.binding.scoring import (
    ContainerSpec,
    MatrixScorer,
    TargetSpec,
    parse_tool_targets,
)

REPO = Path(__file__).resolve().parents[2]
GOLDEN = Path(__file__).with_name("matrix_golden.json")
OWNER = "helios"
SCADA, PUBLIC_SITE = "helios-scada-gateway", "helios-public-site"
#: Calls in the pin whose driver is not tied with another surviving asset.
UNTIED_CALLS = 20
#: The scan's target inputs for the tools used here (the scanner does not emit them yet).
TARGETS = {
    tool: ["owner", "repo"]
    for tool in ("get_file_contents", "push_files", "issue_write", "issue_read", "list_issues")
}


@pytest.fixture(scope="module")
def golden() -> dict:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def scan(golden: dict) -> dict:
    return json.loads((REPO / golden["scan"]).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def targeted(scan: dict) -> MatrixScorer:
    return MatrixScorer(scan["cells"], scan["bands"], targets=TARGETS)


def _as_dict(score) -> dict:
    out = dataclasses.asdict(score)
    out["assets"] = list(out["assets"])
    return out


def _tied(matrix: MatrixScorer, tool: str, expected: dict) -> set[str]:
    """The surviving assets whose cell equals the severity: any of them can be the driver.

    The v1-v4 path breaks a tie in set order, which varies with PYTHONHASHSEED (it did
    before AI-3), so the pin checks the driver exactly only when it is not tied."""
    cells = matrix.candidates(tool)
    return {a for a in expected["assets"] if cells.get(a) == expected["severity"]}


@pytest.mark.parametrize("targets_kw", [{}, {"targets": None}])
def test_without_tool_targets_every_call_scores_as_before(
    golden: dict, scan: dict, targets_kw: dict
) -> None:
    matrix = MatrixScorer(scan["cells"], scan["bands"], **targets_kw)
    assert not matrix.reads_targets_only
    untied = 0
    for row in golden["calls"]:
        got, expected = _as_dict(matrix.score(row["tool"], row["args"])), row["expected"]
        tied = _tied(matrix, row["tool"], expected)
        assert {k: v for k, v in got.items() if k != "driver"} == {
            k: v for k, v in expected.items() if k != "driver"
        }, row["tool"]
        if len(tied) > 1:
            assert got["driver"] in tied, row["tool"]
        else:
            assert got["driver"] == expected["driver"], row["tool"]
            untied += 1
    assert untied == UNTIED_CALLS  # the pin is not hollow: 4 of the 24 calls tie


def test_the_target_input_path_prefers_the_named_container_on_a_tie(scan: dict) -> None:
    """A driver-keyed history (asset_identity='driver') records the repository the call
    named, not the facet that ties with it and sorts first by id."""
    matrix = MatrixScorer(scan["cells"], scan["bands"], targets={"push_files": ["owner", "repo"]})
    score = matrix.score("push_files", {"owner": "helios", "repo": "helios-grid-infra-config"})
    assert set(score.assets) == {"branch-heads", "helios-grid-infra-config", "repository-contents"}
    assert score.severity == 64.0 and score.driver == "helios-grid-infra-config"  # all at 64


def test_the_target_input_path_breaks_other_ties_by_id() -> None:
    cells = {"alpha-store": {"read": 5.0}, "beta-store": {"read": 5.0}, "gamma": {"read": 1.0}}
    bands = {asset: {"read": "low"} for asset in cells}
    matrix = MatrixScorer(cells, bands, targets={"read": ["repo"]})
    assert matrix.score("read", {"repo": "nothing-like-it"}).driver == "alpha-store"
    named = matrix.score("read", {"repo": "beta-store"})  # alpha-store is a sibling: excluded
    assert (named.driver, named.assets) == ("beta-store", ("beta-store", "gamma"))
    # a facet tied with the named asset loses even though it sorts first
    tied = MatrixScorer(
        {"aa": {"read": 5.0}, "zz-repo": {"read": 5.0}}, {}, targets={"read": ["r"]}
    )
    assert tied.score("read", {"r": "zz-repo"}).driver == "zz-repo"


def test_the_golden_holds_the_decoy_failure_it_documents(golden: dict) -> None:
    """The pin records today's behaviour, failure included: a decoy path lowers the cell."""
    decoy = next(
        r
        for r in golden["calls"]
        if r["args"].get("path", "").endswith(".md") and "helios-public-site" in r["args"]["path"]
    )
    assert decoy["expected"]["severity"] == 48.0


def test_a_decoy_path_cannot_lower_the_priced_asset(targeted: MatrixScorer) -> None:
    args = {"owner": OWNER, "repo": "website", "path": f"docs/{PUBLIC_SITE}.md"}
    score = targeted.score("get_file_contents", args)
    assert (score.driver, score.severity, score.basis) == (SCADA, 75.0, "unresolved")
    assert score.worst_case


def test_free_text_naming_a_sensitive_asset_does_not_raise_the_priced_asset(
    scan: dict, targeted: MatrixScorer
) -> None:
    args = {
        "owner": OWNER,
        "repo": PUBLIC_SITE,
        "branch": "main",
        "message": "sync",
        "files": [{"path": "a.md", "content": f"copied from {SCADA}"}],
    }
    untargeted = MatrixScorer(scan["cells"], scan["bands"]).score("push_files", args)
    score = targeted.score("push_files", args)
    assert untargeted.driver == SCADA  # today: the file body names SCADA and prices it
    assert SCADA not in score.assets and PUBLIC_SITE in score.assets
    assert score.basis == "named" and score.severity < untargeted.severity


def test_the_named_target_narrows_and_keeps_facets(targeted: MatrixScorer) -> None:
    score = targeted.score("get_file_contents", {"owner": OWNER, "repo": PUBLIC_SITE})
    assert score.basis == "named"
    # repository-contents is a facet: no target value resembles it, so it is never excluded
    assert set(score.assets) == {PUBLIC_SITE, "repository-contents"}


def test_a_tool_with_no_declared_target_is_priced_at_the_worst_case(
    targeted: MatrixScorer,
) -> None:
    score = targeted.score("search_code", {"query": f"repo:{OWNER}/{PUBLIC_SITE} footer"})
    assert score.basis == "unresolved" and score.driver == SCADA and score.severity == 75.0


def test_an_empty_tool_targets_field_reads_no_argument(scan: dict) -> None:
    matrix = MatrixScorer(scan["cells"], scan["bands"], targets={})
    assert matrix.reads_targets_only
    score = matrix.score("get_file_contents", {"owner": OWNER, "repo": PUBLIC_SITE})
    assert score.basis == "unresolved"


def test_single_candidate_and_unknown_tools_are_unchanged(
    scan: dict, targeted: MatrixScorer
) -> None:
    plain = MatrixScorer(scan["cells"], scan["bands"])
    for tool, args in (("search_users", {"query": "a"}), ("no_such_tool", {"repo": SCADA})):
        assert targeted.score(tool, args) == plain.score(tool, args)


def test_the_match_key_holds_only_target_values(scan: dict, targeted: MatrixScorer) -> None:
    args = {
        "owner": OWNER,
        "repo": "website",
        "method": "create",
        "title": "bug",
        "body": "the private key is in the runbook",
    }
    assert targeted.match_key("issue_write", args) == json.dumps([OWNER, "website"])
    assert "private key" not in targeted.match_key("issue_write", args)
    plain = MatrixScorer(scan["cells"], scan["bands"])
    assert plain.match_key("issue_write", args) == json.dumps(args, sort_keys=True, default=str)


def test_list_valued_target_inputs_are_all_read(targeted: MatrixScorer) -> None:
    values = targeted.match_values("issue_read", {"owner": OWNER, "repo": [SCADA, PUBLIC_SITE]})
    assert values == [OWNER, SCADA, PUBLIC_SITE]


def test_parse_tool_targets_shapes() -> None:
    parsed = parse_tool_targets(
        {
            "get": ["owner", "repo"],
            "send": ["channel"],
            "fork": [["owner", "repo"], {"inputs": ["organization"], "owner": "organization"}],
            "mix": [["owner", "repo"], "organization"],
        }
    )
    assert parsed["get"] == TargetSpec((ContainerSpec(("owner", "repo"), "owner"),))
    assert parsed["send"] == TargetSpec((ContainerSpec(("channel",), None),))
    assert parsed["fork"].containers[1] == ContainerSpec(("organization",), "organization")
    assert parsed["mix"].inputs == ("owner", "repo", "organization")
    assert parse_tool_targets(None) is None


@pytest.mark.parametrize(
    "raw",
    [
        ["owner"],
        {"get": "owner"},
        {"get": []},
        {"get": [{"inputs": "owner"}]},
        {"get": [{"inputs": ["repo"], "owner": "owner"}]},
        {"get": [["owner", 3]]},
        {"get": [7]},
        {"": ["repo"]},
    ],
)
def test_parse_tool_targets_rejects_malformed_fields(raw: object) -> None:
    with pytest.raises(ValueError):
        parse_tool_targets(raw)
