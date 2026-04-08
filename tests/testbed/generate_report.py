"""Generate a markdown attack report from testbed result files."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from tests.testbed.harness.metrics import compute_all, format_report

RESULTS_DIR = Path(__file__).parent / "results"


def load_results() -> list[dict[str, Any]]:
    """Load all JSON result files from the results/ directory."""
    all_results = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text())
            if isinstance(data, list):
                all_results.extend(data)
        except (json.JSONDecodeError, OSError):
            pass
    return all_results


def load_scanner_reports() -> dict[str, str]:
    """Load all MCPSafetyScanner markdown reports keyed by server name."""
    reports = {}
    for path in sorted(RESULTS_DIR.glob("scanner_*.md")):
        # filename: scanner_<server>_<timestamp>.md
        parts = path.stem.split("_", 2)
        if len(parts) >= 2:
            server = parts[1]
            reports[server] = path.read_text()
    return reports


def per_server_table(results: list[dict[str, Any]]) -> str:
    """Build a per-server markdown section."""
    by_server: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in results:
        by_server[r.get("server", "unknown")].append(r)

    sections = []
    for server, rows in sorted(by_server.items()):
        malicious = [r for r in rows if r.get("payload_type") == "malicious"]
        damaged = [r for r in malicious if r.get("damage_detected")]
        asr = len(damaged) / len(malicious) if malicious else 0.0
        sections.append(
            f"\n### {server}  (ASR: {asr:.0%}, {len(damaged)}/{len(malicious)} attacks succeeded)\n"
        )
        sections.append("| Template | Tool | Payload | Damage | Error |")
        sections.append("|---|---|---|---|---|")
        for r in rows[:30]:  # cap to avoid huge tables
            dmg = "[DAMAGE]" if r.get("damage_detected") else "no"
            err = (r.get("error") or "")[:40]
            snip = r.get("response_snippet", "")[:60].replace("\n", " ")
            sections.append(
                f"| {r.get('template_id', '')} | {r.get('tool', '')} "
                f"| {r.get('payload_label', '')} | {dmg} | {err or snip} |"
            )
    return "\n".join(sections)


def notable_findings(results: list[dict[str, Any]]) -> str:
    """Return top 5 most impactful confirmed exploits."""
    hits = [r for r in results if r.get("damage_detected") and r.get("payload_type") == "malicious"]
    hits.sort(key=lambda r: len(r.get("response_snippet", "")), reverse=True)
    lines = ["### Top Confirmed Exploits\n"]
    for i, r in enumerate(hits[:5], 1):
        lines.append(
            f"{i}. **{r.get('server')} / {r.get('template_id')}** — "
            f"`{r.get('tool')}({r.get('payload_label')})` -> "
            f"`{r.get('response_snippet', '')[:100]}`"
        )
    return "\n".join(lines) if len(lines) > 1 else "_No damage confirmed yet — run attacks first._"


def generate(output_path: Path | None = None) -> Path:
    """Load results, compute metrics, write markdown report."""
    results = load_results()
    scanner_reports = load_scanner_reports()

    metrics = compute_all(results) if results else {}
    ascii_table = format_report(metrics) if metrics else "_No results loaded yet._"

    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    n_servers = len({r.get("server") for r in results}) if results else 0

    lat = (
        f"{metrics.get('latency_p95_ms', 0):.1f} ms"
        if metrics.get("latency_p95_ms")
        else "N/A"
    )

    lines = [
        "# MCP Attack Testbed Report",
        f"\n_Generated: {ts}_\n",
        "## Summary\n",
        "| Metric | Value |",
        "|---|---|",
        f"| Servers tested | {n_servers} |",
        f"| Total results | {metrics.get('total_results', 0)} |",
        f"| Malicious payloads | {metrics.get('malicious_count', 0)} |",
        f"| Benign payloads | {metrics.get('benign_count', 0)} |",
        f"| Overall ASR | {metrics.get('asr', {}).get('overall', 0):.1%} |",
        f"| Scorer TPR | {metrics.get('tpr_fpr', {}).get('tpr') or 'N/A (stub)'} |",
        f"| Scorer FPR | {metrics.get('tpr_fpr', {}).get('fpr') or 'N/A (stub)'} |",
        f"| Latency p95 | {lat} |",
        "\n## ASR Metrics\n",
        f"```\n{ascii_table}\n```",
        "\n## Per-Server Results\n",
        per_server_table(results) if results else "_No results yet._",
        "\n## Notable Findings\n",
        notable_findings(results),
    ]

    if scanner_reports:
        lines.append("\n## MCPSafetyScanner Findings (LLM-based)\n")
        for server, report in sorted(scanner_reports.items()):
            lines.append(f"\n### {server}\n")
            # Include first 1000 chars of scanner report
            lines.append(report[:1000] + ("…" if len(report) > 1000 else ""))

    content = "\n".join(lines)

    RESULTS_DIR.mkdir(exist_ok=True)
    if output_path is None:
        ts_file = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        output_path = RESULTS_DIR / f"report_{ts_file}.md"
    output_path.write_text(content, encoding="utf-8")
    print(f"Report written to: {output_path}")
    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate MCP testbed attack report")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    generate(args.output)
