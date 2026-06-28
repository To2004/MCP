"""Run AgentTrust's OWN published rule-based risk scorer on our scenarios.

This is a true apples-to-apples head-to-head: AgentTrust's ``TrustInterceptor``
emits an ``overall_risk`` on the same none..critical scale as our ground truth and
our scorer, and its rule path runs CPU-only (the LLM judge is off by default — the
paper's headline numbers are "rule-core, Judge OFF"). We run it per scenario and
write its severities to ``reports/evaluation/sev_scores/agenttrust.json`` so
``evaluate_severity.py`` grades it alongside ours / CVSS / NIST / DREAD / OWASP.

Needs the AgentTrust repo checked out (github.com/chenglin1112/AgentTrust); point
``AGENTTRUST_SRC`` at its ``src`` dir. Deps: pydantic, pyyaml, rich, httpx, jinja2.

Run:  AGENTTRUST_SRC=/path/to/AgentTrust/src uv run --with pydantic --with rich \
        --with httpx --with jinja2 python scripts/run_agenttrust_scorer.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

AT_SRC = Path(os.environ.get(
    "AGENTTRUST_SRC",
    Path.home() / ".." / "ovadyat" / "scratchpad" / "AgentTrust" / "src",
))
# Fallback to the session scratchpad clone if the env var isn't set.
if not AT_SRC.exists():
    for cand in Path("/tmp").glob("claude-*/**/scratchpad/AgentTrust/src"):
        AT_SRC = cand
        break
sys.path.insert(0, str(AT_SRC))

from agent_trust.benchmarks.runner import _ACTION_TYPE_ALIASES  # noqa: E402
from agent_trust.core.interceptor import TrustInterceptor  # noqa: E402
from agent_trust.core.types import Action, ActionType  # noqa: E402

from agenttrust_loader import SEVERITY, load_all  # noqa: E402

OUT = REPO_ROOT / "reports" / "evaluation" / "sev_scores" / "agenttrust.json"

# Extend AgentTrust's own alias map for the few MCP action types it doesn't list.
_ALIASES = {
    **_ACTION_TYPE_ALIASES,
    "db_read": ActionType.DATABASE_QUERY,
    "db_write": ActionType.DATABASE_QUERY,
    "list_dir": ActionType.FILE_READ,
    "directory_tree": ActionType.FILE_READ,
}


def _coerce(raw: str) -> ActionType:
    try:
        return ActionType(raw)
    except ValueError:
        return _ALIASES.get(raw, ActionType.UNKNOWN)


def main() -> None:
    scen = load_all()
    scores: list[int] = []
    for s in scen:
        action = Action(
            action_type=_coerce(s.action_type),
            tool_name=s.tool_name,
            description=s.description,
            parameters=s.parameters,
            raw_content=s.raw_content,
        )
        # Fresh interceptor per scenario -> pure per-action risk, no cross-scenario
        # chain contamination (each item scored statelessly, like the other scorers).
        report = TrustInterceptor().verify(action)
        scores.append(SEVERITY.get(report.overall_risk.value, 0))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(scores), encoding="utf-8")
    from collections import Counter
    print(f"AgentTrust scorer ran on {len(scores)} scenarios "
          f"(src: {AT_SRC}).\n  severity dist: {dict(sorted(Counter(scores).items()))}")
    print(f"Wrote {OUT.relative_to(REPO_ROOT)} -> evaluate_severity.py will grade it.")


if __name__ == "__main__":
    main()
