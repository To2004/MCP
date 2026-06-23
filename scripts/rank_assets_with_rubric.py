"""Rank discovered assets with the local LLM using the asset-ranking rubric.

Reads ``reports/discovered_assets.json`` (produced by ``discover_assets.py``)
and, for each server, asks Qwen2.5 (local Ollama) to assign every asset a
Risk Level + Sensitivity (1-5) + Reasoning, following
``docs/standards/asset-ranking-guidelines.md`` verbatim. Writes a markdown
report. Designed to run on a SLURM GPU node where Ollama is serving the model.

Env:
  OLLAMA_HOST   Ollama base URL (default http://127.0.0.1:11434)
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp_security.llm.ollama_client import query_ollama

REPO = Path(__file__).resolve().parent.parent
RUBRIC = REPO / "docs/standards/asset-ranking-guidelines.md"
ASSETS = REPO / "reports" / "discovered_assets.json"
OUT = REPO / "reports" / "asset_ranking_rubric.md"

RISK_BY_SENS = {5: "Critical", 4: "High", 3: "Medium", 2: "Low", 1: "Minimal"}
CHUNK = 12  # assets per LLM call — keeps the prompt within the 8192 ctx cap


def _build_prompt(rubric: str, server: str, kind: str, context: str, assets: list[dict]) -> str:
    payload = [{"name": a["name"], "tags": a["tags"]} for a in assets]
    ctx = f"\nServer self-description (what it exposes):\n{context}\n" if context.strip() else ""
    return (
        "You are a security architect ranking the assets an MCP server exposes. "
        "The MCP server is the protected asset; the AI agent making requests is the threat.\n"
        "Follow this rubric EXACTLY when scoring — apply FIPS 199, MITRE ATT&CK, OWASP, "
        "and the kill-chain role steps it describes:\n\n"
        "================ RUBRIC ================\n"
        f"{rubric}\n"
        "================ END RUBRIC ================\n\n"
        f"Server: {server} (kind={kind}). Each asset below is one asset class.{ctx}\n"
        "For EVERY asset assign:\n"
        "  - risk_level: one of Critical, High, Medium, Low, Minimal\n"
        "  - sensitivity: integer 1-5 (must agree with risk_level per the rubric)\n"
        "  - reasoning: <= 20 words, citing at least one framework anchor "
        "(a MITRE T-code, a FIPS C/I/A rating, or an OWASP factor)\n"
        "Reply with JSON only, no prose.\n"
        f"Assets: {json.dumps(payload)}\n"
        'Return exactly: {"rows":[{"name":"<name>","risk_level":"<band>",'
        '"sensitivity":<1-5>,"reasoning":"<text>"}]}'
    )


def _coerce(row: dict) -> dict | None:
    name = row.get("name")
    if not name:
        return None
    try:
        sens = int(row.get("sensitivity", 0))
    except (TypeError, ValueError):
        sens = 0
    sens = max(1, min(5, sens)) if sens else 2
    risk = str(row.get("risk_level", "")).strip().capitalize()
    if risk not in RISK_BY_SENS.values():
        risk = RISK_BY_SENS[sens]
    return {
        "name": str(name),
        "risk_level": risk,
        "sensitivity": sens,
        "reasoning": str(row.get("reasoning", "")).strip() or "unknown — pending review",
    }


def _rank_server(rubric: str, server: dict) -> list[dict]:
    assets = server["assets"]
    ranked: dict[str, dict] = {}
    for i in range(0, len(assets), CHUNK):
        chunk = assets[i : i + CHUNK]
        prompt = _build_prompt(rubric, server["server"], server["kind"], server.get("context", ""), chunk)
        resp = query_ollama(prompt)
        rows = (resp or {}).get("rows", []) if isinstance(resp, dict) else []
        for row in rows:
            if isinstance(row, dict):
                clean = _coerce(row)
                if clean:
                    ranked[clean["name"]] = clean
        # Any asset the model skipped: record as pending so nothing is dropped.
        for a in chunk:
            ranked.setdefault(
                a["name"],
                {"name": a["name"], "risk_level": "Low", "sensitivity": 2,
                 "reasoning": "unknown — pending review (LLM omitted)"},
            )
    return sorted(ranked.values(), key=lambda r: (-r["sensitivity"], r["name"]))


def main() -> None:
    rubric = RUBRIC.read_text(encoding="utf-8")
    servers = json.loads(ASSETS.read_text(encoding="utf-8"))

    blocks = ["# Asset Ranking — rubric-scored by local LLM (Qwen2.5)\n",
              "Scored per `docs/standards/asset-ranking-guidelines.md` "
              "(FIPS 199 · MITRE ATT&CK · OWASP · kill-chain).\n"]
    for server in servers:
        rows = _rank_server(rubric, server)
        blocks.append(f"## {server['server']}  _(kind={server['kind']})_\n")
        blocks.append("| Asset class | Risk Level | Sensitivity | Reasoning |")
        blocks.append("|---|---|---|---|")
        for r in rows:
            blocks.append(
                f"| `{r['name']}` | {r['risk_level']} | {r['sensitivity']} | {r['reasoning']} |"
            )
        blocks.append("")
        print(f"ranked {server['server']}: {len(rows)} assets")

    OUT.write_text("\n".join(blocks) + "\n", encoding="utf-8")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
