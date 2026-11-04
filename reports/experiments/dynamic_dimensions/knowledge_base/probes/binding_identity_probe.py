"""Reproduce the measured binding failures (C5, N1) and prototype the v5 asset-identity split.

Two arms on the same calls, against the real remote GitHub scan
(``reports/experiments/gateway/github_remote/github_remote.cells.json``):

- ``live``: the gateway as it is. ``RouteScorer.score`` hands the engine the worst surviving
  register driver (``framework.py:186-191``; ``binding/scoring.py:106-123``).
- ``handle``: a prototype written here only (nothing in ``src/`` changes). The binding matches
  only the tool's *target inputs* (``owner``, ``repo``) for R_static, and the engine gets a
  container handle: the register id when the repository is a registered container, else a
  pseudonym of ``owner/repo`` with no sensitivity. It feeds ``BehaviourEngine`` (design v4)
  directly, so the difference between the arms is the asset identity alone.

The scenarios are synthetic calls, not a development world; no number here is a test result.

    uv run python reports/experiments/dynamic_dimensions/knowledge_base/probes/binding_identity_probe.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mcp_security.behaviour import BehaviourConfig, BehaviourEngine, Message
from mcp_security.binding.identifiers import canonical_id, describes_call_target, name_coverage
from mcp_security.binding.scoring import NAME_MATCH_FLOOR, MatrixScorer
from mcp_security.gateway.framework import RouteScorer, load_artifacts

REPO = Path(__file__).resolve().parents[5]
SCAN = REPO / "reports/experiments/gateway/github_remote/github_remote.cells.json"
BREADTH = REPO / "reports/experiments/breadth_spec/github_remote_scan.json"
CATALOG = REPO / "reports/experiments/gateway/github_remote/github_remote.json"
REGISTER = REPO / "reports/experiments/gateway/github_remote/github_helios_remote.md"
DAY, HOUR = 86_400.0, 3_600.0
BASE_DAY = 20_000  # a weekday (memory.is_weekend)
OWNER = "helios"
SELECTOR = "method"
WRITE_IMPACT = 4


def ts(day: int, hour: float) -> float:
    return (BASE_DAY + day) * DAY + hour * HOUR


def target_inputs() -> dict[str, tuple[str, ...]]:
    """Prototype of the scan's target inputs: every tool whose schema has owner and repo."""
    tools = json.loads(CATALOG.read_text())["tools"]
    out = {}
    for tool in tools:
        props = (tool.get("inputSchema") or {}).get("properties") or {}
        if "owner" in props and "repo" in props:
            out[tool["name"]] = ("owner", "repo")
    return out


def register_containers() -> set[str]:
    """Register rows that are standing containers, not call targets ("What a ... reaches")."""
    out = set()
    for line in REGISTER.read_text().splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 3 and cells[1].startswith("`") and cells[1].endswith("`"):
            if not describes_call_target(cells[2]):
                out.add(cells[1].strip("`"))
    return out


class HandleArm:
    """The prototype: typed matching for R_static, a container handle for the engine."""

    def __init__(self, scan: dict, design: str = "v4") -> None:
        self.scan = scan
        self.matrix = MatrixScorer(scan["cells"], scan["bands"])
        self.targets = target_inputs()
        self.containers = register_containers() & set(scan["asset_sensitivity"])
        self.engine = BehaviourEngine(BehaviourConfig(design=design))

    def identity(self, tool: str, args: dict) -> tuple[str | None, int | None, str]:
        names = self.targets.get(tool)
        values = [args.get(n) for n in names] if names else []
        if not names or not all(isinstance(v, str) and v.strip() for v in values):
            return None, None, "no-target"
        repo = values[-1]
        named = [
            a
            for a in self.containers
            if name_coverage(repo, a) >= NAME_MATCH_FLOOR
        ]
        if len(named) == 1:
            return named[0], self.scan["asset_sensitivity"].get(named[0]), "named"
        container = "/".join(canonical_id(v) for v in values)
        return "c:" + hashlib.sha256(container.encode()).hexdigest()[:12], None, "unregistered"

    def r_static(self, tool: str, args: dict):
        names = self.targets.get(tool, ())
        return self.matrix.score(tool, {n: args[n] for n in names if n in args})

    def score(self, tool: str, args: dict, t: float, agent: str, session: str) -> dict:
        asset, sens, basis = self.identity(tool, args)
        impact = self.scan["tool_impact"].get(tool)
        op = None if impact is None else ("write" if impact >= WRITE_IMPACT else "read")
        key = f"{tool}:{args[SELECTOR]}" if SELECTOR in args else tool
        v = self.engine.observe(Message(t, agent, "tools/call", session, tool=key, asset=asset,
                                        sensitivity=sens, operation=op))
        cell = self.r_static(tool, args)
        return {"M": round(v.multiplier, 3), "d*": v.strongest, "asset": asset, "basis": basis,
                "driver": cell.driver, "cell": cell.severity, "scores": v.scores}


class LiveArm:
    def __init__(self) -> None:
        artifacts = load_artifacts("github", str(SCAN), str(BREADTH), None, "github_remote")
        self.route = RouteScorer("github", artifacts)

    def score(self, tool: str, args: dict, t: float, agent: str, session: str) -> dict:
        d = self.route.score(tool, args, t, agent, session=session)
        v = self.route.behaviour
        return {"M": d["behaviour"], "d*": d["behaviour_reason"], "asset": d["asset"],
                "basis": d["basis"], "driver": d["asset"], "cell": d["cell"],
                "assets_known": len(v.agents[agent].assets.counts)}


def gfc(repo: str, path: str = "README.md") -> dict:
    return {"owner": OWNER, "repo": repo, "path": path}


def warm(arm, agent: str, repo: str, days: int, per_day: int = 6) -> None:
    """``days`` office days of routine reads on one repository."""
    for d in range(days):
        for k in range(per_day):
            arm.score("get_file_contents", gfc(repo, f"src/f{k}.py"), ts(d, 9 + k), agent,
                      f"{agent}-{d}")


def main() -> None:
    scan = json.loads(SCAN.read_text())
    out: dict = {}

    # S1: steering by a decoy path (C5). R_static driver and cell, both arms.
    live, handle = LiveArm(), HandleArm(scan)
    rows = []
    for path in ("README.md", "docs/helios-public-site.md"):
        a = gfc("website", path)
        cell = live.route._matrix.score("get_file_contents", a)
        typed = handle.r_static("get_file_contents", a)
        rows.append({"path": path, "live": [cell.driver, cell.severity, cell.basis],
                     "typed": [typed.driver, typed.severity, typed.basis]})
    out["S1_decoy_path"] = rows

    # S2: one public repository through five tools: drivers (live) vs one handle.
    calls = [
        ("get_file_contents", gfc("helios-public-site")),
        ("list_issues", {"owner": OWNER, "repo": "helios-public-site"}),
        ("issue_read", {"owner": OWNER, "repo": "helios-public-site", "method": "get",
                        "issue_number": 3}),
        ("push_files", {"owner": OWNER, "repo": "helios-public-site", "branch": "main",
                        "files": [{"path": "a.md", "content": "x"}], "message": "m"}),
        ("pull_request_read", {"owner": OWNER, "repo": "helios-public-site", "method": "get",
                               "pullNumber": 1}),
    ]
    out["S2_one_repo_five_tools"] = [
        {"tool": t, "live_driver": live.route._matrix.score(t, a).driver,
         "live_sens": scan["asset_sensitivity"].get(live.route._matrix.score(t, a).driver),
         "handle": handle.identity(t, a)}
        for t, a in calls
    ]

    # S2b: after 20 days on the public repo, each of those tools once on day 20 (M per call).
    for name, arm in (("live", LiveArm()), ("handle", HandleArm(scan))):
        warm(arm, "dev", "helios-public-site", 20)
        out[f"S2b_{name}"] = [
            {k: arm.score(t, a, ts(20, 10 + i * 0.1), "dev", "dev-20")[k] for k in ("M", "d*")}
            for i, (t, a) in enumerate(calls)
        ]

    # S3: 30 unregistered repositories in one hour: distinct assets each arm records.
    for name, arm in (("live", LiveArm()), ("handle", HandleArm(scan))):
        warm(arm, "lead", "helios-public-site", 20)
        last = None
        for i in range(30):
            last = arm.score("get_file_contents", gfc(f"team-repo-{i}"), ts(20, 10 + i / 60),
                             "lead", "lead-20")
        engine = arm.route.behaviour if name == "live" else arm.engine
        out[f"S3_{name}"] = {"distinct_assets_last_hour": engine.agents["lead"].assets_hour
                             .distinct(), "last_M": last["M"], "last_d*": last["d*"]}

    # S4: 30 days on an unregistered repository, then the first real SCADA read.
    for name, arm in (("live", LiveArm()), ("handle", HandleArm(scan))):
        warm(arm, "dev", "website", 30)
        r = arm.score("get_file_contents", gfc("helios-scada-gateway"), ts(30, 11), "dev",
                      "dev-30")
        out[f"S4_{name}"] = {k: r[k] for k in ("M", "d*", "asset", "basis")}

    # S5: read a file then file an issue, both on an unregistered repository (day 20).
    for name, arm in (("live", LiveArm()), ("handle", HandleArm(scan))):
        warm(arm, "dev", "helios-public-site", 20)
        arm.score("get_file_contents", gfc("website"), ts(20, 10), "dev", "dev-20")
        r = arm.score("issue_write", {"owner": OWNER, "repo": "website", "method": "create",
                                      "title": "bug", "body": "see README"},
                      ts(20, 10.1), "dev", "dev-20")
        out[f"S5_{name}"] = {k: r[k] for k in ("M", "d*", "asset", "basis")}

    # S6: a focused developer's first read of an unregistered repository (day 20).
    for name, arm in (("live", LiveArm()), ("handle", HandleArm(scan))):
        warm(arm, "dev", "helios-public-site", 20)
        r = arm.score("get_file_contents", gfc("website"), ts(20, 10), "dev", "dev-20")
        out[f"S6_{name}"] = {k: r[k] for k in ("M", "d*", "asset", "basis")}

    # Coverage of the prototype's target inputs on the remote catalog.
    targets = target_inputs()
    cells = MatrixScorer(scan["cells"], scan["bands"])
    multi = [t for t in scan["tool_impact"] if len(cells.candidates(t)) >= 2]
    out["register_containers"] = sorted(register_containers())
    out["coverage"] = {
        "tools": len(scan["tool_impact"]),
        "multi_candidate": len(multi),
        "multi_candidate_with_owner_repo": sum(1 for t in multi if t in targets),
        "multi_candidate_without": sorted(t for t in multi if t not in targets),
    }
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
