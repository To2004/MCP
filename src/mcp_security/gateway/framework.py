"""The framework for one route: static artifacts loaded once, then one call scored at a time.

This connects the existing pieces and adds no risk logic of its own:

- **static** — the scan's cells: ``binding.scoring.MatrixScorer`` resolves a call's
  arguments to an asset and returns that cell, with the three levels behind it;
- **dynamic** — the runtime factor ``B × L``: ``gate_runtime.GateScorer``, which learns
  from every call it scores, so calls must reach it in arrival order;
- **input rules** — stage 2: ``input_rules.evaluate_call``, the call's input level 1–5,
  reported beside the risk (how the two combine is not decided).

The gateway calls ``RouteScorer.score`` live, before forwarding; ``score.py`` calls it over
a saved log. Same object, same order, same numbers. Every result carries the digests of the
artifacts it came from, so a score can always be traced to the exact scan that produced it.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

from mcp_security.binding.scoring import MatrixScorer
from mcp_security.input_rules import CallLevel, evaluate_call

REPO_ROOT = Path(__file__).resolve().parents[3]
DYNAMIC_DIR = REPO_ROOT / "scripts" / "dynamic_design"
DEFAULT_SCORE_MAX = 125.0
GATEWAY_ORG = "gateway"
DIGEST_CHARS = 12
MICROSECONDS = 1_000_000
NO_CELLS = "no-cells"

Rules = dict[str, tuple[list[dict], dict[str, int]]]


@dataclass(frozen=True)
class Artifacts:
    """Everything the static side produced for one route, and where it came from."""

    scan: dict
    specs: dict[str, dict]  # {kind: {tool: {input: breadth spec}}}
    rules: Rules | None
    kind: str
    digests: dict[str, str]  # artifact name -> sha256 of the file read

    @property
    def scanned_catalog(self) -> str | None:
        """SHA-256 of the tool list the scan was run on, when the scan recorded it."""
        return (self.scan.get("catalog") or {}).get("sha256")


def load_artifacts(
    route: str, scan: str | None, breadth: str | None, rules: str | None, kind: str | None
) -> Artifacts | None:
    """The route's static artifacts from its config paths; None for a route with no scan."""
    if not scan:
        return None
    kind = kind or route
    digests = {"scan": _digest(scan)}
    if breadth:
        specs = {kind: load_breadth(Path(breadth))}
        digests["breadth"] = _digest(breadth)
    else:
        specs = gate_runtime().load_gate_specs()
    if rules:
        digests["rules"] = _digest(rules)
    return Artifacts(
        scan=json.loads(Path(scan).read_text(encoding="utf-8")),
        specs=specs,
        rules=load_rules(Path(rules)) if rules else None,
        kind=kind,
        digests=digests,
    )


class RouteScorer:
    """Scores one route's calls in arrival order, with state carried from call to call."""

    def __init__(self, route: str, artifacts: Artifacts) -> None:
        runtime = gate_runtime()
        self.artifacts = artifacts
        self._matrix = MatrixScorer(artifacts.scan["cells"], artifacts.scan["bands"])
        self._gate = runtime.GateScorer(artifacts.specs)
        self._connection = runtime.Connection(
            org_id=GATEWAY_ORG, server_id=route, kind=artifacts.kind
        )
        self._score_max = float(artifacts.scan.get("score_max", DEFAULT_SCORE_MAX))

    def score(self, tool: str, args: dict, ts: float) -> dict:
        """Static cell, runtime factor, risk and input level for one call; learns from it."""
        started = time.perf_counter()
        cell = self._matrix.score(tool, args)
        factor, reasons = self._gate.score(self._connection, tool, args)
        level = self._input_level(tool, args, ts)
        elapsed = time.perf_counter() - started
        scan = self.artifacts.scan
        known = cell.basis != NO_CELLS
        result = {
            "asset": cell.driver,
            "basis": cell.basis,
            "cell": cell.severity if known else None,
            "factor": round(factor, 3),
            "risk": round(min(self._score_max, cell.severity * factor), 3) if known else None,
            "input_level": level.level if level else None,
            "input_set_by": ",".join(level.set_by) if level else None,
            "score_us": round(elapsed * MICROSECONDS),
            "reasons": "; ".join(reasons) if known else "tool not in scan",
        }
        if known:
            result |= {
                "band": scan["bands"].get(cell.driver, {}).get(tool),
                "sensitivity": scan.get("asset_sensitivity", {}).get(cell.driver),
                "impact": scan.get("tool_impact", {}).get(tool),
                "blast": scan.get("blast_radius", {}).get(f"{tool}|{cell.driver}"),
            }
        return result

    def _input_level(self, tool: str, args: dict, ts: float) -> CallLevel | None:
        rules = self.artifacts.rules
        if not rules or tool not in rules:
            return None
        rows, assets = rules[tool]
        # The call's own time, not the clock: live and offline must agree.
        return evaluate_call(
            rows, args, assets=assets, now=datetime.fromtimestamp(ts, timezone.utc)
        )


def load_rules(path: Path) -> Rules:
    """Tool -> (its stage-2 rule rows, its reachable assets with their scanned level)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    rules = {}
    for tool in data["tools"]:
        rows = [arg for arg in tool["arguments"] if isinstance(arg.get("rule"), dict)]
        reach = (tool.get("policy_slice") or {}).get("assets_this_tool_can_reach", [])
        assets = {
            a["asset"]: a["scanned_level"] for a in reach if isinstance(a.get("scanned_level"), int)
        }
        rules[tool["tool_name"]] = (rows, assets)
    return rules


def load_breadth(path: Path) -> dict[str, dict]:
    """``{tool: {input: spec}}`` from one breadth-spec file (``scripts/scan_breadth.py``)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        tool: {entry["name"]: dict(entry) for entry in block["inputs"]}
        for tool, block in data["tools"].items()
    }


def gate_runtime() -> ModuleType:
    """The runtime factor lives in ``scripts/dynamic_design`` (stdlib-only scripts)."""
    if str(DYNAMIC_DIR) not in sys.path:
        sys.path.insert(0, str(DYNAMIC_DIR))
    import gate_runtime as module  # noqa: PLC0415 — path is only valid after the insert above

    return module


def _digest(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:DIGEST_CHARS]
