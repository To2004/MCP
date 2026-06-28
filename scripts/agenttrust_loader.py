"""Load the AgentTrust severity benchmark as external ground truth.

Unlike the attack benchmarks, AgentTrust grades each agent tool action on a
graded severity scale---``none < low < medium < high < critical``---over a
benign→misuse spectrum of routine operations (read a README, write to a project
file, delete a system file, POST data to an external host, ...). That is exactly
the target a *risk-scoring* framework should be measured against: not "is this an
attack?" but "how risky is this action, on a scale?", the same question CVSS / NIST
/ DREAD answer.

Each scenario carries the concrete action (``action_type``, ``tool_name``,
``parameters``, ``raw_content``) plus the ground-truth ``expected_risk`` and
``expected_verdict``. We map ``expected_risk`` to an ordinal 0--4 so every scorer
can be graded against it by agreement, rank correlation, and error.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
_EXT = Path(os.environ.get("AGENTTRUST_DIR", REPO_ROOT / "external"))
DEFAULT_DIR = _EXT / "agenttrust" / "scenarios"

# Severity-graded benchmark sources, all sharing the AgentTrust scenario schema
# (``action.action_type``/``raw_content`` + ``expected_risk``). Three are external
# (AgentTrust); ``mcp_native`` is an author-created MCP-specific set (secondary).
SOURCES: dict[str, Path] = {
    "agenttrust_internal": _EXT / "agenttrust" / "scenarios",          # 300, external
    "agenttrust_independent": _EXT / "agenttrust" / "extra" / "independent_test.yaml",  # 30
    "agenttrust_realworld": _EXT / "agenttrust" / "extra" / "real_world_100.yaml",      # 100
    "mcp_native": _EXT / "mcp_severity",                               # author-created
}
EXTERNAL_SOURCES = ("agenttrust_internal", "agenttrust_independent", "agenttrust_realworld")

# Ground-truth severity scale (ordinal). none=0 .. critical=4.
SEVERITY = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
SEVERITY_NAME = {v: k for k, v in SEVERITY.items()}


@dataclass(frozen=True)
class Scenario:
    """One graded scenario from a severity benchmark."""

    id: str
    source: str
    category: str
    action_type: str
    tool_name: str
    description: str
    parameters: dict
    raw_content: str
    severity: int  # 0..4 ground truth
    verdict: str  # allow/warn/block/review
    difficulty: str

    @property
    def text(self) -> str:
        """All free-text of the action, for content heuristics / the LLM judge."""
        parts = [self.description, self.raw_content, str(self.parameters)]
        return " ".join(p for p in parts if p)


def _parse(items: list, source: str, default_cat: str) -> list[Scenario]:
    out: list[Scenario] = []
    for it in items or []:
        action = it.get("action", {}) or {}
        risk = str(it.get("expected_risk", "none")).lower()
        out.append(Scenario(
            id=it.get("id", ""),
            source=source,
            category=it.get("category", default_cat),
            action_type=action.get("action_type", ""),
            tool_name=action.get("tool_name", ""),
            description=action.get("description", "") or it.get("description", ""),
            parameters=action.get("parameters", {}) or {},
            raw_content=action.get("raw_content", "") or "",
            severity=SEVERITY.get(risk, 0),
            verdict=str(it.get("expected_verdict", "")).lower(),
            difficulty=str(it.get("difficulty", "")).lower(),
        ))
    return out


def load_source(name: str) -> list[Scenario]:
    """Load one named benchmark source (a directory of YAMLs, or a single YAML)."""
    path = SOURCES[name]
    files = sorted(path.glob("*.yaml")) if path.is_dir() else [path]
    out: list[Scenario] = []
    for f in files:
        if f.exists():
            out += _parse(yaml.safe_load(f.read_text(encoding="utf-8")), name, f.stem)
    return out


def load_scenarios(scenario_dir: Path = DEFAULT_DIR) -> list[Scenario]:
    """Backward-compatible: the AgentTrust internal 300."""
    out: list[Scenario] = []
    for path in sorted(scenario_dir.glob("*.yaml")):
        out += _parse(yaml.safe_load(path.read_text(encoding="utf-8")),
                      "agenttrust_internal", path.stem)
    return out


def load_all() -> list[Scenario]:
    """Every scenario from every available source (skips missing ones)."""
    out: list[Scenario] = []
    for name in SOURCES:
        out += load_source(name)
    return out


def main() -> None:
    from collections import Counter

    scen = load_scenarios()
    print(f"Loaded {len(scen)} AgentTrust scenarios from {DEFAULT_DIR}\n")
    by_cat = Counter(s.category for s in scen)
    by_sev = Counter(s.severity for s in scen)
    by_act = Counter(s.action_type for s in scen)
    print("Per category:")
    for c, n in sorted(by_cat.items()):
        print(f"  {c:20} {n}")
    print("\nSeverity ground truth (0 none .. 4 critical):")
    for s in range(5):
        print(f"  {s} {SEVERITY_NAME[s]:9} {by_sev.get(s, 0)}")
    print(f"\n{len(by_act)} distinct action types; e.g. "
          f"{dict(sorted(by_act.items(), key=lambda kv: -kv[1])[:8])}")


if __name__ == "__main__":
    main()
