"""How the remote GitHub MCP differs from the npx server our corpus and policy were written for.

The remote server (``api.githubcopilot.com/mcp/``) merged several npx tools into one tool
with a ``method`` argument and renamed some arguments. This table is used twice: to replay
an npx-era corpus against the remote server, and to rewrite the org policy's asset
register so it names the tools the remote catalog actually has (``static-scan`` refuses a
register that names a tool the catalog lacks).

    uv run python -m mcp_security.gateway.github_remote \
        --policy ~/mcp-static-scan/policies/examples/github_helios.md --out remote.md
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

#: npx tool name -> (remote tool name, fixed arguments added to the call).
RENAMED_TOOLS: dict[str, tuple[str, dict]] = {
    "get_issue": ("issue_read", {"method": "get"}),
    "create_issue": ("issue_write", {"method": "create"}),
    "update_issue": ("issue_write", {"method": "update"}),
    "get_pull_request": ("pull_request_read", {"method": "get"}),
    "get_pull_request_status": ("pull_request_read", {"method": "get_status"}),
    "get_pull_request_files": ("pull_request_read", {"method": "get_files"}),
    "get_pull_request_comments": ("pull_request_read", {"method": "get_review_comments"}),
    "get_pull_request_reviews": ("pull_request_read", {"method": "get_reviews"}),
    "create_pull_request_review": ("pull_request_review_write", {"method": "create"}),
}
RENAMED_ARGS = {"pull_number": "pullNumber", "per_page": "perPage", "q": "query"}
#: The remote list_issues pages by cursor and only knows OPEN / CLOSED.
LIST_ISSUES_STATES = {"open": "OPEN", "closed": "CLOSED"}
_TICKED_NAME = re.compile(r"`([a-z_]+)`")
#: Both register tables (classification and Table 2) start with these columns.
REGISTER_HEADER = re.compile(r"^\|\s*Asset\s*\|\s*Description\s*\|\s*Tools\s*\|")
REGISTER_TOOLS_COLUMN = 3  # "| `asset` | description | tools |".split("|")[3]


def translate_call(tool: str, args: dict) -> tuple[str, dict]:
    """The remote server's tool name and arguments for one npx-catalog call."""
    remote, fixed = RENAMED_TOOLS.get(tool, (tool, {}))
    out = {RENAMED_ARGS.get(key, key): value for key, value in args.items()}
    if tool == "list_issues":
        out.pop("page", None)
        state = LIST_ISSUES_STATES.get(str(out.pop("state", "")).lower())
        if state:
            out["state"] = state
    return remote, {**fixed, **out}


def rename_register_tools(tools_cell: str) -> str:
    """One register ``Tools`` cell with npx names replaced by remote ones, duplicates dropped."""
    names = _TICKED_NAME.findall(tools_cell)
    if not names:
        return tools_cell
    renamed = dict.fromkeys(_remote_name(name) for name in names)
    return " " + ", ".join(f"`{name}`" for name in renamed) + " "


def remote_policy(text: str) -> str:
    """The org policy, naming the remote server's tools and arguments.

    Only names change; the org's wording is kept. In both asset registers a merged tool is
    listed once; elsewhere (input rules, input baseline, prose) each ticked tool or
    argument name is replaced where it stands.
    """
    lines, in_register = [], False
    for line in text.split("\n"):
        if REGISTER_HEADER.match(line):
            in_register = True
        elif not line.startswith("|"):
            in_register = False
        cells = line.split("|")
        if in_register and len(cells) > REGISTER_TOOLS_COLUMN:
            cells[REGISTER_TOOLS_COLUMN] = rename_register_tools(cells[REGISTER_TOOLS_COLUMN])
            lines.append("|".join(cells))
        else:
            lines.append(_TICKED_NAME.sub(lambda m: f"`{_remote_name(m.group(1))}`", line))
    return "\n".join(lines)


def _remote_name(name: str) -> str:
    """The remote name of a ticked tool or argument; anything else unchanged."""
    return RENAMED_TOOLS.get(name, (RENAMED_ARGS.get(name, name), {}))[0]


def main() -> None:
    """Write the remote-catalog version of an org policy: ``--policy in.md --out out.md``."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(remote_policy(args.policy.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"{args.policy} -> {args.out}")


if __name__ == "__main__":
    main()
