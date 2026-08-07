"""Render a scan artifact (or static table) as human-readable markdown or CSV."""

from __future__ import annotations

import csv
import io

_BAND_MARK = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}

# Visualization colour by RAW SCORE, scaled to the table's own max (per experiment:
# baseline 75, five_level 125, cia 150). The cut points keep the 0-75 proportions
# (green <27%, yellow <53%, orange <80%, red above) so colours are comparable across
# experiments. Independent of the operational `band_label`.
_SCORE_MAX = 75
_SCORE_FRACTIONS = ((20 / 75, "🟢"), (40 / 75, "🟡"), (60 / 75, "🟠"))  # < frac*max -> mark


def _score_mark(score: float, score_max: float = _SCORE_MAX) -> str:
    """Heat-map glyph for a score, scaled to ``score_max`` (green→red at 27/53/80%)."""
    for frac, mark in _SCORE_FRACTIONS:
        if score < frac * score_max:
            return mark
    return "🔴"


# Column order for the tidy/long matrix export -- primitives before the product.
_CSV_FIELDS = ("asset", "tool", "sensitivity", "blast", "impact", "score", "band")


def matrix_rows(table: dict) -> list[dict]:
    """One tidy row per (asset, tool): the primitives and the score they multiply to.

    Deterministic view of ``table`` -- no LLM. Exposes ``sensitivity``, ``blast``
    and ``impact`` alongside the ``score`` so the ``s×b×i`` calculation behind each
    cell is machine-readable, not just visible in the rendered markdown.
    """
    cells = table.get("cells", {})
    bands = table.get("bands", {})
    sens = table.get("asset_sensitivity", {})
    blast = table.get("blast_radius", {})
    impact = table.get("tool_impact", {})
    rows: list[dict] = []
    for asset, row in cells.items():
        for tool, score in row.items():
            b = blast.get(f"{tool}|{asset}")
            rows.append(
                {
                    "asset": asset,
                    "tool": tool,
                    "sensitivity": sens.get(asset),
                    "blast": "N/A" if b is None else b,
                    "impact": impact.get(tool),
                    "score": "N/A" if score is None else f"{score:g}",
                    "band": bands.get(asset, {}).get(tool, ""),
                }
            )
    return rows


def matrix_csv(table: dict) -> str:
    """The risk matrix as tidy CSV (``asset,tool,sensitivity,blast,impact,score,band``)."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_CSV_FIELDS)
    writer.writeheader()
    writer.writerows(matrix_rows(table))
    return buf.getvalue()


def _matrix(table: dict) -> list[str]:
    cells = table.get("cells", {})
    if not cells:
        return ["_No cells._"]
    # Primitives behind each score, so the calculation is visible in place.
    sens = table.get("asset_sensitivity", {})
    blast = table.get("blast_radius", {})
    impact = table.get("tool_impact", {})
    score_max = table.get("score_max", _SCORE_MAX)
    mode = table.get("impact_mode", "baseline")
    tools = list(next(iter(cells.values())).keys())
    if table.get("sensitivity_scored") is False:
        calc_note = "`score (blast×impact)` — sensitivity is not scored in this mode"
    else:
        calc_note = "`score (sensitivity×blast×impact)`"
    lines = [
        f"_Each cell shows {calc_note}; impact_mode={mode}, "
        f"score ranges 0–{score_max:g}. Colour is by raw score, scaled to this "
        f"max: 🟢 low · 🟡 · 🟠 · 🔴 top ~20%. Likelihood is pinned to 1.0._",
        "",
        "| asset \\ tool | " + " | ".join(tools) + " |",
        "|" + " --- |" * (len(tools) + 1),
    ]
    for asset, row in cells.items():
        s = sens.get(asset)
        rendered = []
        for t in tools:
            score = row[t]
            if score is None:  # N/A — tool does not affect this asset
                rendered.append("N/A")
                continue
            mark = _score_mark(score, score_max)
            b, i = blast.get(f"{t}|{asset}"), impact.get(t)
            if s is None:  # sensitivity not scored -> show the two-factor calculation
                calc = f" ({b}×{i})" if None not in (b, i) else ""
            else:
                calc = f" ({s}×{b}×{i})" if None not in (s, b, i) else ""
            rendered.append(f"{score:g}{calc} {mark}".strip())
        lines.append(f"| `{asset}` | " + " | ".join(rendered) + " |")
    return lines


def _cia_section(table: dict) -> list[str]:
    """Per-tool CIA-triad breakdown (impact_mode='cia' only): base + violated facets."""
    cia = table.get("tool_cia")
    if not cia:
        return []
    lines = [
        "",
        "## Tool impact — CIA breakdown",
        "",
        "_impact = base(1-3) + one point per violated CIA facet. ✓ = the tool "
        "violates that objective (C disclose · I modify · A make-unavailable)._",
        "",
        "| tool | base | C | I | A | impact |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    mark = {True: "✓", False: "·"}
    for tool, v in cia.items():
        lines.append(
            f"| `{tool}` | {v.get('base', '')} | {mark[bool(v.get('C'))]} | "
            f"{mark[bool(v.get('I'))]} | {mark[bool(v.get('A'))]} | {v.get('impact', '')} |"
        )
    return lines


def scan_to_markdown(server: str, kind: str, table: dict) -> str:
    """A self-contained markdown view of one scan's risk matrix and primitives."""
    profile = table.get("inferred_profile", {})
    dist = table.get("band_distribution", {})
    lines = [
        f"# Scan — {server}",
        "",
        f"_kind={kind} · provenance={table.get('provenance', 'live-scan')} · "
        f"model_reviewed={table.get('model_reviewed', '')} · "
        f"impact_mode={table.get('impact_mode', 'baseline')} · bands={dist}_",
        "",
        "Risk derived live by the LLM from the scanned tools and assets — no "
        f"checked-in table was read. Matrix colour is by RAW SCORE "
        f"(0–{table.get('score_max', 75):g}), scaled to this max.",
        "",
        "## Inferred domain profile",
        "",
    ]
    # Profile-sensitivity (ult/pure) scans record their deterministic rule
    # manifest; surface it so the non-prompt half of the scoring is visible.
    rules = table.get("deterministic_rules") or []
    if rules:
        lines[-2:-2] = ["## Deterministic rules applied", ""] + [f"- {r}" for r in rules] + [""]
    for key in (
        "mcp_kind",
        "asset_meaning",
        "blast_radius_meaning",
        "dangerous_classes",
        "irreversible_actions",
        "worked_example",
    ):
        val = profile.get(key)
        if val:
            if isinstance(val, list):
                val = ", ".join(str(x) for x in val)
            lines.append(f"- **{key}**: {val}")
    lines += ["", "## Tool impact", "", "| tool | impact |", "| --- | --- |"]
    lines += [f"| `{t}` | {v} |" for t, v in table.get("tool_impact", {}).items()]
    lines += _cia_section(table)
    lines += _asset_sensitivity_section(table)
    lines += ["", "## Risk matrix (score · band)", ""]
    lines += _matrix(table)
    lines += _blast_matrix_section(table)
    lines += _atomic_ops_section(table)
    lines += _input_ranking_section(table)
    lines.append("")
    return "\n".join(lines)


def _asset_sensitivity_section(table: dict) -> list[str]:
    """The per-asset sensitivity table, or a note when the mode does not score it."""
    sens = table.get("asset_sensitivity") or {}
    if not sens and table.get("sensitivity_scored") is False:
        assets = table.get("asset_ids") or list(table.get("cells", {}))
        return [
            "",
            "## Asset sensitivity",
            "",
            f"_Not scored in `impact_mode={table.get('impact_mode', '')}`: the "
            "organization's written description of this server states how severe "
            "each asset is, so no separate 1–5 sensitivity primitive is derived. "
            f"The {len(assets)} assets below still form the matrix axis; the score "
            "is `blast × impact`._",
            "",
            "| asset | sensitivity |",
            "| --- | --- |",
            *[f"| `{a}` | — |" for a in assets],
        ]
    return [
        "",
        "## Asset sensitivity",
        "",
        "| asset | sensitivity |",
        "| --- | --- |",
        *[f"| `{a}` | {v} |" for a, v in sens.items()],
    ]


def _blast_matrix_section(table: dict) -> list[str]:
    """A standalone blast-radius (coverage · 1-5) matrix.

    Same asset×tool orientation as the risk matrix, so each COLUMN is one tool
    across every asset. Blast is the model's coverage judgment — what fraction of
    the asset one call reaches.
    """
    blast = table.get("blast_radius", {})
    if not blast:
        return []
    cells = table.get("cells", {})
    tools = list(next(iter(cells.values())).keys()) if cells else []
    if not tools:
        return []
    assets = list(cells.keys())
    lines = [
        "",
        "## Blast radius (coverage · 1–5)",
        "",
        "_What fraction of the asset ONE call of the tool reaches (1 = tiny/metadata, "
        "4 = essentially all, 5 = all + destructive) — coverage, not severity._",
        "",
        "| asset \\ tool | " + " | ".join(tools) + " |",
        "|" + " --- |" * (len(tools) + 1),
    ]
    for asset in assets:
        row = []
        for t in tools:
            v = blast.get(f"{t}|{asset}")
            row.append("N/A" if v is None else str(v))
        lines.append(f"| `{asset}` | " + " | ".join(row) + " |")
    return lines


def _atomic_ops_section(table: dict) -> list[str]:
    ao = table.get("tool_atomic_ops")
    if not ao:
        return []
    lines = [
        "",
        "## Tool atomic operations",
        "",
        "_Independent verb-based taxonomy (severity 1–5), NOT the risk score and NOT "
        "the tool impact. It is a coarse lexical prior shown for reference; the "
        "domain-grounded **tool impact** (1–3) above supersedes it when they differ "
        "(e.g. a single-event delete is impact 2 there even though the DELETE verb is "
        "severity 5 here)._",
        "",
        "| tool | atomic op | severity | all ops | source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for tool, v in ao.items():
        ops = ", ".join(v.get("atomic_ops", []))
        lines.append(
            f"| `{tool}` | **{v.get('primary_op', '')}** | "
            f"{v.get('severity', '')} ({v.get('severity_label', '')}) | {ops} | {v.get('source', '')} |"
        )
    return lines


def _input_ranking_section(table: dict) -> list[str]:
    ir = table.get("tool_input_ranking")
    if not ir:
        return []
    lines = [
        "",
        "## Tool input ranking (risk 1–5 + critical trigger)",
        "",
        "| tool | input | risk | critical trigger | why |",
        "| --- | --- | --- | --- | --- |",
    ]
    for tool, v in ir.items():
        for r in v.get("inputs", []):
            trig = r.get("critical_trigger") or "—"
            why = (r.get("reason") or "")[:60]
            lines.append(
                f"| `{tool}` | `{r.get('name', '')}` | {r.get('risk', '')} | {trig} | {why} |"
            )
    return lines
