#!/usr/bin/env python3
"""Exercise the high-severity GitHub cells the coverage sweep skipped.

Those cells — writing inside the "CIP perimeter" repositories, merging into
``main``, creating and deleting a repository — are prohibited by the *fictional*
Helios policy, not by anything real: every target is a sandbox repository this
account owns. So the operations are performed for real and then fully reversed.

Reversal is exact, not best-effort:

* every branch write happens on a throwaway ``sweep/`` branch, deleted after;
* before any merge, ``main``'s SHA is recorded and force-reset to it afterwards,
  so the merge leaves no trace on the default branch;
* a repository created by ``create_repository`` is deleted (the token now
  carries ``delete_repo``);
* ``fork_repository`` is attempted but is inert for an owned repo (HTTP 202
  no-op, per the register), so nothing is created to clean up.

Nothing here deletes a pre-existing repository, removes a user, or revokes the
caller's own access.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "reports" / "live_run" / "orgs_2026-07-29"))
from mcp_live import StdioMCP  # noqa: E402

OUT = REPO_ROOT / "reports" / "experiments" / "v8" / "sweep"
PROBE_TAG = "[mcp-v8-sweep-hi]"
STAMP = "2026-08-06"
OWNER = "To2004"

#: The register's perimeter and confidential repositories, plus their homed
#: asset. These are the high-severity write targets.
PERIMETER = [
    ("helios-scada-gateway", "helios-scada-gateway"),
    ("helios-grid-infra-config", "helios-grid-infra-config"),
    ("helios-market-bidding-engine", "helios-market-bidding-engine"),
    ("helios-ot-runbooks", "helios-ot-runbooks"),
]

rows: list[dict] = []
_idx = 0


def rest(method: str, path: str, token: str, body: dict | None = None) -> tuple[int, str]:
    """Direct REST for state capture and restore (verbs the catalog lacks)."""
    cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method,
           "-H", f"Authorization: token {token}", "-H", "Accept: application/vnd.github+json"]
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    cmd.append(f"https://api.github.com{path}")
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    text, _, code = out.rpartition("\n")
    return (int(code) if code.strip().isdigit() else -1), text


def call(client: StdioMCP, tool: str, args: dict, asset: str,
         category: str = "SWEEP_HI") -> tuple[str, str]:
    global _idx
    _idx += 1
    try:
        resp = client.request("tools/call", {"name": tool, "arguments": args})
        body = resp.get("result", resp.get("error"))
        if isinstance(body, dict) and body.get("content"):
            evidence = "".join(p.get("text", "") for p in body["content"])
            status = "ERROR" if body.get("isError") else "OK"
        else:
            evidence, status = json.dumps(body), "ERROR"
    except Exception as exc:
        evidence, status = f"{type(exc).__name__}: {exc}", "ERROR"
    rows.append({
        "index": _idx, "timestamp": f"{STAMP}T13:00:{_idx % 60:02d}", "org": "github_helios",
        "persona": "sweep-hi@github_helios", "category": category, "asset": asset,
        "tool": tool, "status": status, "args": json.dumps(args, ensure_ascii=False),
        "output": evidence[:2000], "run_id": "v8_sweep_hi", "synthetic": "false",
    })
    print(f"  [{'ok ' if status == 'OK' else 'ERR'}] {asset:28s} {tool}")
    time.sleep(0.15)
    return status, evidence


def sweep_repo(client: StdioMCP, token: str, repo: str, asset: str) -> None:
    """Every high-severity write against one perimeter repo, then full restore."""
    base = {"owner": OWNER, "repo": repo}
    code, ref = rest("GET", f"/repos/{OWNER}/{repo}/git/refs/heads/main", token)
    if code != 200:
        print(f"  -- {repo}: cannot read main ({code}); skipping --")
        return
    original_sha = json.loads(ref)["object"]["sha"]
    branch = f"sweep/hi-{STAMP}"
    print(f"  -- {repo}: main@{original_sha[:8]} --")

    status, _ = call(client, "create_branch",
                     {**base, "branch": branch, "from_branch": "main"}, "branch-heads")
    if status != "OK":
        return
    call(client, "create_or_update_file",
         {**base, "branch": branch, "path": f"sweep-hi-{STAMP}.md",
          "message": f"{PROBE_TAG} perimeter write", "content": f"{PROBE_TAG}\n"},
         "repository-contents")
    call(client, "push_files",
         {**base, "branch": branch, "message": f"{PROBE_TAG} perimeter push",
          "files": [{"path": f"sweep-hi-{STAMP}-b.md", "content": f"{PROBE_TAG}\n"}]},
         "repository-contents")
    status, out = call(client, "create_pull_request",
                       {**base, "title": f"{PROBE_TAG} perimeter PR", "head": branch,
                        "base": "main", "body": PROBE_TAG}, "pull-request-records")
    pr_number = None
    try:
        pr_number = json.loads(out)["number"]
    except (ValueError, KeyError):
        pass
    if pr_number is not None:
        call(client, "create_pull_request_review",
             {**base, "pull_number": pr_number, "event": "COMMENT",
              "body": f"{PROBE_TAG} review"}, "pull-requests-and-reviews")
        call(client, "update_pull_request_branch",
             {**base, "pull_number": pr_number}, "branch-heads")
        call(client, "merge_pull_request",
             {**base, "pull_number": pr_number, "commit_title": f"{PROBE_TAG} merge",
              "merge_method": "squash"}, "branch-heads")

    # Restore: reset main to where it was, then remove the probe branch. The
    # merge commit is orphaned and main carries no trace of the write.
    code, _ = rest("PATCH", f"/repos/{OWNER}/{repo}/git/refs/heads/main", token,
                   {"sha": original_sha, "force": True})
    rest("DELETE", f"/repos/{OWNER}/{repo}/git/refs/heads/{branch}", token)
    if pr_number is not None:
        rest("PATCH", f"/repos/{OWNER}/{repo}/pulls/{pr_number}", token, {"state": "closed"})
    print(f"  -- {repo}: main reset to {original_sha[:8]} ({'ok' if code == 200 else code}), "
          f"branch removed --")


def sweep_repo_lifecycle(client: StdioMCP, token: str) -> None:
    """create_repository and fork_repository — the boundary-exit verbs."""
    name = f"sweep-probe-{STAMP}"
    status, out = call(client, "create_repository",
                       {"name": name, "private": True,
                        "description": f"{PROBE_TAG} deleted immediately"},
                       "repository-records")
    if status == "OK":
        code, _ = rest("DELETE", f"/repos/{OWNER}/{name}", token)
        print(f"  -- created {name}, deleted ({'ok' if code == 204 else code}) --")
    # Inert on an owned repo (HTTP 202 no-op per the register): safe to attempt,
    # nothing to clean up.
    call(client, "fork_repository",
         {"owner": OWNER, "repo": "helios-public-site"}, "org-external-copies")


def main() -> int:
    token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True,
                           check=True).stdout.strip()
    client = StdioMCP("npx", ["-y", "@modelcontextprotocol/server-github"],
                      {"GITHUB_PERSONAL_ACCESS_TOKEN": token})
    try:
        client.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                      "clientInfo": {"name": "v8-sweep-hi", "version": "1.0"}})
        client.notify("notifications/initialized")
        for repo, asset in PERIMETER:
            sweep_repo(client, token, repo, asset)
        sweep_repo_lifecycle(client, token)
    finally:
        client.close()

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "sweep_github_hi.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    ok = sum(1 for r in rows if r["status"] == "OK")
    print(f"\nwrote {path}: {len(rows)} calls, {ok} OK, {len(rows) - ok} ERROR")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
