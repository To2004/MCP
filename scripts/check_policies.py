"""Validate ``docs/mcp-tools/server-policies.md`` against the policy spec.

The ``--check-policies`` validator the spec
(``docs/standards/mcp-policy-spec.md``) asks for, mirroring the profile checker.
Per section it enforces:

* the ``### <stem>`` heading and the ``**Tier: X** · `server-id` `` fact line parse;
* **no** ``| Asset | Sens. |`` table and no numeric sensitivity column anywhere —
  the judgement number is exactly what a policy withholds;
* the asset register parses, ids are unique, and every ``Flags`` value is one of
  the six known flags;
* at P1+ the register's ``Tools`` cells reference only tools the server actually
  advertises;
* at P2 every advertised tool appears in some row's ``Tools`` cell, and a
  ``Default:`` recognition rule exists.

Exit code 0 when every section conforms at its declared level, 1 otherwise.

Run:  uv run python scripts/check_policies.py [--server calendar_real]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mcp_security.static_scoring import registry as reg  # noqa: E402
from mcp_security.static_scoring.server_policies import (  # noqa: E402
    POLICY_DOC,
    POLICY_FLAGS,
    parse_asset_register,
    unknown_register_tools,
    unmapped_tools,
)
from mcp_security.static_scoring.server_profiles import load_profiles  # noqa: E402

TOOL_LISTS = REPO_ROOT / "reports" / "tool_lists"
FINANCE_CATALOGS = REPO_ROOT / "reports" / "experiments" / "static_scanner" / "inputs"

# Where each section's advertised tool list comes from, and the conformance level
# the document claims for it. "captured" reads a tools/list JSON; "declarative"
# builds the demo registry in code.
SECTIONS: dict[str, tuple[str, str, str]] = {
    # stem: (source kind, source key, claimed conformance)
    "fs_fintech_fs": ("captured", "filesystem.json", "P2"),
    "fs_medical_clinic_fs": ("captured", "filesystem.json", "P2"),
    "fs_corp_filesystem": ("captured", "filesystem.json", "P2"),
    "fs_law_firm_fs": ("captured", "filesystem.json", "P2"),
    "fs_media_studio_fs": ("captured", "filesystem.json", "P2"),
    "github_real": ("captured", "github_real.json", "P2"),
    "github_cbg": ("declarative", "github", "P2"),
    "slack_real": ("captured", "slack_real.json", "P2"),
    "slack_cbg": ("declarative", "slack", "P2"),
    "calendar_real": ("captured", "calendar_real.json", "P2"),
    "calendar_cbg": ("declarative", "calendar", "P2"),
    "sqlite_cbg_sqlite": ("captured", "sqlite.json", "P2"),
    "maverick": ("finance", "maverick.json", "P2"),
    "finance_tools": ("finance", "finance_tools.json", "P2"),
    "openbb": ("finance", "openbb.json", "P1"),
    "sec_edgar": ("finance", "sec_edgar.json", "P1"),
    "yahoo_finance": ("finance", "yahoo_finance.json", "P1"),
    # Live-provisioned organizations — one org per real vendor catalog, three
    # domains. Assets in these registers exist; see reports/live_run/orgs_2026-07-29/.
    "github_helios": ("captured", "github_real.json", "P2"),
    "slack_vireo": ("captured", "slack_real.json", "P2"),
    "calendar_aurora": ("captured", "calendar_real.json", "P2"),
}

_DECLARATIVE_LOADERS = {
    "github": reg.load_github_registry,
    "slack": reg.load_slack_registry,
    "calendar": reg.load_calendar_registry,
}
_SENS_TABLE_RE = re.compile(r"^\|\s*Asset\s*\|\s*Sens\.?\s*\|", re.IGNORECASE)
_DEFAULT_RULE_RE = re.compile(r"\*\*Default:\s*[A-Za-z]", re.IGNORECASE)


def advertised_tools(source_kind: str, key: str) -> list[str]:
    """The tool names the server actually advertises, per its catalog source."""
    if source_kind == "declarative":
        return [tool.name for tool in _DECLARATIVE_LOADERS[key]().tools]
    path = (TOOL_LISTS if source_kind == "captured" else FINANCE_CATALOGS) / key
    payload = json.loads(path.read_text(encoding="utf-8"))
    tools = payload["tools"] if isinstance(payload, dict) and "tools" in payload else payload
    return [tool["name"] for tool in tools]


def check_section(text: str, tools: list[str], level: str) -> tuple[list[str], int]:
    """Every conformance problem in one section, plus the register row count."""
    problems: list[str] = []
    if any(_SENS_TABLE_RE.match(line.strip()) for line in text.splitlines()):
        problems.append("carries an '| Asset | Sens. |' table — a policy states no numbers")
    try:
        rows = parse_asset_register(text)
    except Exception as exc:  # noqa: BLE001 -- surface the parse error as a finding
        return [*problems, f"register does not parse: {exc}"], 0

    stray = unknown_register_tools(rows, tools)
    if stray:
        problems.append(
            f"register names {len(stray)} tool(s) the server does not advertise: {stray}"
        )
    if not _DEFAULT_RULE_RE.search(text):
        problems.append("no '**Default: <class>**' recognition rule (fail-closed default required)")
    if level == "P2":
        unmapped = unmapped_tools(rows, tools)
        # A tool that genuinely touches no asset is legitimate when the section
        # says so in prose ("`get-current-time` touches no organizational asset").
        undeclared = [tool for tool in unmapped if f"`{tool}` touches no" not in text]
        if undeclared:
            problems.append(
                f"P2 requires total tool coverage; {len(undeclared)} tool(s) appear in no "
                f"register row and are not declared asset-free: {undeclared}"
            )
    for row in rows:
        bad = [flag for flag in row.flags if flag not in POLICY_FLAGS]
        if bad:
            problems.append(f"asset {row.asset_id!r}: unknown flag(s) {bad}")
    return problems, len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc", type=Path, default=POLICY_DOC)
    parser.add_argument("--server", default=None, help="check one section stem only")
    parser.add_argument(
        "--only-present",
        action="store_true",
        help=(
            "check the sections the document actually carries, instead of requiring "
            "every registered server. For a document that covers a subset by design "
            "— the v7 framework-native policies cover four organizations — a missing "
            "section is the point, not a failure. A section the document DOES carry "
            "is still checked in full."
        ),
    )
    args = parser.parse_args(argv)
    # A relative --doc is a natural invocation; the summary line prints the
    # path relative to the repo, which needs an absolute one.
    args.doc = args.doc.resolve()

    sections = load_profiles(args.doc)
    by_stem = {name: section for name, section in sections.items()}
    if args.server:
        wanted = {args.server}
    elif args.only_present:
        wanted = set(by_stem) & set(SECTIONS)
        skipped = sorted(set(by_stem) - set(SECTIONS))
        if skipped:
            print(f"[warn] {args.doc.name}: section(s) not registered in SECTIONS: {skipped}")
        if not wanted:
            print(f"[FAIL] {args.doc.name} carries no section registered in SECTIONS")
            return 1
    else:
        wanted = set(SECTIONS)

    missing = sorted(wanted - set(by_stem))
    if missing:
        print(f"[FAIL] {args.doc.name} has no section(s): {missing}")
        return 1

    rc = 0
    for stem in sorted(wanted):
        if stem not in SECTIONS:
            print(f"[FAIL] {stem}: not registered in SECTIONS; add its catalog source")
            rc = 1
            continue
        source_kind, key, level = SECTIONS[stem]
        tools = advertised_tools(source_kind, key)
        problems, n_assets = check_section(by_stem[stem].text, tools, level)
        if problems:
            rc = 1
            print(f"[FAIL] {stem} ({level}, {len(tools)} tools):")
            for problem in problems:
                print(f"        - {problem}")
        else:
            print(f"[ok]   {stem} ({level}): {len(tools)} tools, {n_assets} register rows")
    print(f"\n{len(wanted)} section(s) checked in {args.doc.relative_to(REPO_ROOT)}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
