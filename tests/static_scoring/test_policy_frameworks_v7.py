"""Tests for the v7 framework-native policy documents and their parser support.

Three organizations' policy documents — ISO/IEC 27001:2022, NIST FIPS 199 /
SP 800-60, and CIS Controls v8.1 Control 3 — describe the same four deployments
the ``nacombo`` baseline covers, but in each framework's own register shape. The
register carries native columns (an ISO owner, a NIST information type, a CIS
data category and segment), an authorization column stating which of the tools
that REACH an asset the organization actually SANCTIONS, and no flag column.

What these tests protect:

* the framework registers parse, and their tool homing is total (a tool with no
  register row silently scores nothing, which is the failure that matters);
* the authorization column is read as a subset of the reachable tools, so an
  authorization cell can never invent reach the register did not grant;
* no framework document leaks a per-asset sensitivity number, which would turn
  the derivation experiment back into a lookup;
* the baseline document is unaffected by the parser changes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_security.static_scoring.server_policies import (
    PolicyNumbersError,
    assert_no_sensitivity_numbers,
    parse_asset_register,
    policy_for,
    unknown_register_tools,
    unmapped_tools,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "docs" / "mcp-tools"
TOOL_LISTS = REPO_ROOT / "reports" / "tool_lists"

FRAMEWORKS = ("iso", "nist", "cis")
# The four organizations the v7 experiment covers, and the catalog each is scanned
# against. Same catalogs the baseline arm uses, so a register difference is the
# only difference between arms.
SERVERS = {
    "fs_corp_filesystem": "filesystem",
    "github_helios": "github_real",
    "slack_vireo": "slack_real",
    "calendar_aurora": "calendar_real",
}
# `get-current-time` reaches no organizational asset on the calendar catalog, which
# every calendar policy states in prose. A legitimate gap, not a missing homing.
KNOWN_UNMAPPED = {"calendar_aurora": {"get-current-time"}}

CASES = [(fw, server) for fw in FRAMEWORKS for server in SERVERS]


def framework_doc(framework: str) -> Path:
    return DOCS / f"server-policies-{framework}.md"


def catalog_tools(server: str) -> list[str]:
    raw = json.loads((TOOL_LISTS / f"{SERVERS[server]}.json").read_text(encoding="utf-8"))
    return [tool["name"] for tool in (raw["tools"] if isinstance(raw, dict) else raw)]


@pytest.mark.parametrize("framework", FRAMEWORKS)
def test_framework_document_exists(framework: str):
    assert framework_doc(framework).is_file(), f"missing {framework} policy document"


@pytest.mark.parametrize(("framework", "server"), CASES)
def test_register_parses_and_homes_every_tool(framework: str, server: str):
    """Total tool coverage: a tool with no register row scores nothing, silently."""
    rows = parse_asset_register(policy_for(server, doc=framework_doc(framework)).text)
    assert rows, f"{framework}/{server}: empty register"

    tools = catalog_tools(server)
    assert unknown_register_tools(rows, tools) == [], (
        f"{framework}/{server}: register names tools the server does not advertise"
    )
    unmapped = set(unmapped_tools(rows, tools))
    assert unmapped <= KNOWN_UNMAPPED.get(server, set()), (
        f"{framework}/{server}: tools with no register row: {sorted(unmapped)}"
    )


@pytest.mark.parametrize(("framework", "server"), CASES)
def test_asset_ids_are_unique_and_nonempty(framework: str, server: str):
    rows = parse_asset_register(policy_for(server, doc=framework_doc(framework)).text)
    ids = [row.asset_id for row in rows]
    assert all(ids), f"{framework}/{server}: an asset id is empty"
    assert len(ids) == len(set(ids)), f"{framework}/{server}: duplicate asset id"


@pytest.mark.parametrize(("framework", "server"), CASES)
def test_authorization_is_a_subset_of_reach(framework: str, server: str):
    """An authorization cell may narrow reach; it may never widen it.

    The ``Tools`` column is the tool×asset homing the blast stage scores. If an
    authorization cell could introduce a tool the register never granted, the
    two columns would disagree about what the surface can do and the homing would
    be the one that loses.
    """
    rows = parse_asset_register(policy_for(server, doc=framework_doc(framework)).text)
    stated = [row for row in rows if row.authorized_stated]
    assert stated, f"{framework}/{server}: no row states an authorization column"
    for row in rows:
        assert set(row.authorized) <= set(row.tools), (
            f"{framework}/{server}/{row.asset_id}: authorizes tools it does not reach: "
            f"{sorted(set(row.authorized) - set(row.tools))}"
        )


@pytest.mark.parametrize(("framework", "server"), CASES)
def test_registers_carry_no_flags_and_do_carry_native_columns(framework: str, server: str):
    """v7 drops the flag column and replaces it with framework-native ones."""
    rows = parse_asset_register(policy_for(server, doc=framework_doc(framework)).text)
    assert all(row.flags == () for row in rows), f"{framework}/{server}: a row still carries flags"
    assert any(row.extra for row in rows), (
        f"{framework}/{server}: no row carries a framework-native column"
    )


@pytest.mark.parametrize(("framework", "server"), CASES)
def test_no_sensitivity_numbers_leak(framework: str, server: str):
    """The organization states classes and consequences; the scanner supplies 1-5."""
    assert_no_sensitivity_numbers(
        policy_for(server, doc=framework_doc(framework)).text, server=server
    )


@pytest.mark.parametrize("framework", FRAMEWORKS)
def test_document_rejects_a_leaked_sensitivity_table(framework: str):
    """The guard is live on these documents too, not only on the baseline."""
    leaked = framework_doc(framework).read_text(encoding="utf-8") + (
        "\n| Asset | Sens. |\n|---|---|\n| `security-keys` | 5 |\n"
    )
    with pytest.raises(PolicyNumbersError):
        assert_no_sensitivity_numbers(leaked, server="fs_corp_filesystem")


def test_register_shapes_diverge_as_designed():
    """ISO keeps the baseline's rows, NIST splits, CIS merges.

    The divergence is the experiment: if every framework produced the same
    register, the arms would differ only in prose and there would be nothing to
    measure.
    """
    for server in SERVERS:
        counts = {
            framework: len(
                parse_asset_register(policy_for(server, doc=framework_doc(framework)).text)
            )
            for framework in FRAMEWORKS
        }
        baseline = len(parse_asset_register(policy_for(server).text))
        assert counts["iso"] == baseline, f"{server}: ISO should keep the baseline's rows"
        assert counts["nist"] > baseline, f"{server}: NIST should split at least one row"
        assert counts["cis"] < baseline, f"{server}: CIS should merge into coarse entries"


def test_baseline_register_is_unchanged_by_the_parser_extension():
    """The baseline document still parses exactly as it did: flags, no authorization."""
    rows = parse_asset_register(policy_for("fs_corp_filesystem").text)
    assert len(rows) == 16
    keys = next(row for row in rows if row.asset_id == "security-keys")
    assert keys.flags == ("self-sufficient", "hub")
    assert keys.cia == "C>I>A"
    assert keys.authorized == () and not keys.authorized_stated
    assert keys.extra == ()
