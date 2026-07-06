"""Highlight the input parameters that most influence a call's risk.

The scanner's parameter rubrics (``reports/scan/<server>_params.json``, derived
by the LLM per ``docs/standards/parameter-scoring.md``) say which inputs carry
magnitude and how their *value* maps to a risk band. This report ranks those
inputs by **influence** — how many bands the value alone can swing the call's
risk — and surfaces, for each, the threshold value that trips the top band
(e.g. "attendees ≥ 20 → critical", or a money "amount ≥ N → critical" once such
a tool is scanned).

It is deterministic and reads only existing rubrics — no LLM. Run after a scan
(``python -m mcp_security.param_scoring``):

    uv run python scripts/highlight_influential_inputs.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from mcp_security.param_scoring.combine import BAND_RANK, BANDS
from mcp_security.param_scoring.rubric import ParamRubric, ToolRubric

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_DIR = REPO_ROOT / "reports" / "scan"
OUT_DIR = REPO_ROOT / "reports" / "influential_inputs"

# A parsed_limit parameter with no LIMIT is unbounded — the widest reach, which
# the rubric spec bands as critical even when the cutoffs stop lower.
_UNBOUNDED_BAND = "critical"


@dataclass(frozen=True)
class InputInfluence:
    server: str
    tool: str
    param: str
    extract: str
    base_rank: str
    min_band: str
    top_band: str
    swing: int          # top_rank - min_rank: how many bands the value can move risk
    top_trigger: str    # human description of the value that reaches top_band
    reasoning: str
    llm_picked: bool = False  # the scanner's own "most_influential" pick for this tool


def _reachable_bands(param: ParamRubric) -> list[str]:
    """Every risk band the parameter's value can produce."""
    bands = {param.base_rank}
    for cutoff in param.cutoffs:
        bands.add(cutoff.band)
    if param.extract == "parsed_limit":
        bands.add(_UNBOUNDED_BAND)  # unbounded query/command -> critical reach
    if param.when_true:  # boolean flag
        bands.add(param.when_true)
        bands.add("low")  # false -> effectively low
    if not param.cutoffs and not param.when_true and param.extract != "parsed_limit":
        bands.add("low")  # value-less magnitude still starts at low
    return [b for b in bands if b in BAND_RANK]


def _top_trigger(param: ParamRubric, top_band: str) -> str:
    """Describe the value that first reaches ``top_band``."""
    if param.extract == "parsed_limit" and top_band == _UNBOUNDED_BAND:
        return "unbounded (no LIMIT / no cap)"
    if param.when_true and top_band == param.when_true:
        return "flag set to true"
    triggers = [c.min for c in param.cutoffs if c.band == top_band]
    if triggers:
        unit = {"list_length": "items", "number": "value", "parsed_limit": "rows"}.get(
            param.extract, "value"
        )
        return f"{unit} ≥ {min(triggers):g}"
    return "top cutoff"


def _influence(server: str, tool: str, param: ParamRubric, *, llm_picked: bool = False) -> InputInfluence:
    bands = _reachable_bands(param)
    ranks = [BAND_RANK[b] for b in bands]
    min_rank, top_rank = min(ranks), max(ranks)
    top_band = BANDS[top_rank - 1]
    return InputInfluence(
        server=server,
        tool=tool,
        param=param.name,
        extract=param.extract,
        base_rank=param.base_rank,
        min_band=BANDS[min_rank - 1],
        top_band=top_band,
        swing=top_rank - min_rank,
        top_trigger=_top_trigger(param, top_band),
        reasoning=param.reasoning,
        llm_picked=llm_picked,
    )


def collect_influences(scan_dir: Path = SCAN_DIR) -> list[InputInfluence]:
    """Every magnitude parameter across all scanned servers, scored for influence."""
    influences: list[InputInfluence] = []
    for path in sorted(scan_dir.glob("*_params.json")):
        server = path.stem[: -len("_params")]
        raw = json.loads(path.read_text(encoding="utf-8"))
        for tool_name, rubric_raw in raw.get("rubrics", {}).items():
            rubric = ToolRubric.from_dict(rubric_raw)
            for param in rubric.parameters:
                influences.append(
                    _influence(server, tool_name, param, llm_picked=param.name == rubric.most_influential)
                )
    return influences


def _render(influences: list[InputInfluence]) -> str:
    # Most influential first: biggest value-driven swing, then highest top band.
    ranked = sorted(
        influences,
        key=lambda i: (i.swing, BAND_RANK[i.top_band]),
        reverse=True,
    )
    lines = [
        "# Most influential MCP inputs",
        "",
        "Which **input parameter values** move a call's risk the most. Ranked by",
        "*swing* — how many bands the value alone can shift the call's risk (from",
        "its smallest to its largest reachable band) — then by the top band it can",
        "reach. `top trigger` is the value that trips that top band: the number,",
        "list length, or unbounded query that makes the call as dangerous as the",
        "input can make it (e.g. a money `amount ≥ N` once such a tool is scanned).",
        "A ⭐ marks the input the scanner itself named as the tool's *most",
        "influential* (`most_influential` in the rubric).",
        "",
        f"Scanned rubrics: {len({i.server for i in influences})} servers, "
        f"{len(influences)} magnitude parameters, "
        f"{sum(1 for i in influences if i.llm_picked)} flagged most-influential by the scanner.",
        "",
        "## Top influential inputs",
        "",
        "| rank | server | tool | input | swing | reaches | top trigger | why |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for n, inf in enumerate(ranked[:25], 1):
        swing = f"{inf.min_band}→{inf.top_band} (+{inf.swing})"
        why = (inf.reasoning[:70] + "…") if len(inf.reasoning) > 71 else inf.reasoning
        star = " ⭐" if inf.llm_picked else ""
        lines.append(
            f"| {n} | {inf.server} | {inf.tool} | `{inf.param}`{star} | {swing} | "
            f"**{inf.top_band}** | {inf.top_trigger} | {why} |"
        )
    lines += ["", "## By server", ""]
    by_server: dict[str, list[InputInfluence]] = {}
    for inf in ranked:
        by_server.setdefault(inf.server, []).append(inf)
    for server in sorted(by_server):
        rows = by_server[server]
        lines.append(f"### {server} ({len(rows)} magnitude inputs)")
        lines.append("")
        if not rows:
            lines += ["_No magnitude inputs found by the scanner._", ""]
            continue
        lines.append("| tool | input | reaches | top trigger |")
        lines.append("| --- | --- | --- | --- |")
        for inf in rows:
            lines.append(
                f"| {inf.tool} | `{inf.param}` | {inf.top_band} | {inf.top_trigger} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    influences = collect_influences()
    if not influences:
        print("No parameter rubrics found. Run `python -m mcp_security.param_scoring` first.")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "influential_inputs.json").write_text(
        json.dumps([i.__dict__ for i in influences], indent=2), encoding="utf-8"
    )
    summary = _render(influences)
    (OUT_DIR / "SUMMARY.md").write_text(summary, encoding="utf-8")
    print(summary)
    print(f"\nWritten to {OUT_DIR}/SUMMARY.md and influential_inputs.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
