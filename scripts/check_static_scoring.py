"""Static-scoring sanity check on a fresh org the scanner never saw.

Invents a new organization ("NovaCorp") with new personas and a small,
hand-authored set of calls for the three big MCPs (github, slack, calendar),
then scores them with **static scoring only** — the design-time (tool, asset)
band from the scan, escalated by the input-parameter rubric. No dynamic signal
(baseline / sequence / LLM) is used here.

The point is to check the static scorer is **general, not hardcoded or overfit**:

* every score comes from the scanned risk matrix (``reports/scan/<server>.json``),
  never from a value baked into the scorer;
* a call to an asset the scan never enumerated returns an honest ``unresolved``
  status, and a call to a tool the server never advertised returns ``invalid`` —
  the scorer refuses to fabricate a number it cannot justify;
* the same tool on a more sensitive asset, or with a bigger input parameter,
  scores strictly higher — the ordering the framework claims.

Deterministic and offline; writes ``reports/static_check/SUMMARY.md`` and
``static_scores.csv`` for you to take.

Run::

    uv run python scripts/check_static_scoring.py
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from mcp_security.call_scoring.score import score_call
from mcp_security.call_scoring.loader import Call
from mcp_security.call_scoring.tables import load_scan, load_param_rubrics, SCAN_DIR

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "reports" / "static_check"

# A brand-new org + personas the scanner has never seen. The scanner scored
# tools and asset *classes* (repos/channels/calendars), not people or orgs, so a
# new org's calls must score purely from those class-level judgements.
ORG = "NovaCorp"


@dataclass(frozen=True)
class FreshCall:
    server: str          # scan stem
    persona: str
    intent: str          # benign | malicious — for the reader only, NOT used in scoring
    tool: str
    args: dict
    note: str            # what this call is meant to demonstrate


# Hand-authored calls. Deliberately a mix of: ordinary work on low-sensitivity
# assets, misuse of crown-jewel assets, big-parameter blasts, and two calls the
# scan cannot resolve (unknown asset / unknown tool) to prove no fabrication.
FRESH_CALLS = [
    # --- GitHub -----------------------------------------------------------
    FreshCall("github_cbg", "Dana (PM)", "benign", "get_file_contents",
              {"repo": "public-website", "path": "README.md"},
              "read a public repo — should be low"),
    FreshCall("github_cbg", "Raj (SRE)", "benign", "list_commits",
              {"repo": "internal-docs"}, "read internal docs — modest"),
    FreshCall("github_cbg", "Raj (SRE)", "malicious", "get_file_contents",
              {"repo": "infra-config", "path": ".env"},
              "read the crown-jewel infra repo (sens 5) — should be high+"),
    FreshCall("github_cbg", "Attacker (Nyx)", "malicious", "delete_file",
              {"repo": "payments-service", "path": "auth.js"},
              "destructive op on a sensitive repo — should be high/critical"),
    FreshCall("github_cbg", "Attacker (Nyx)", "malicious", "push_files",
              {"repo": "unknown-shadow-repo", "path": "x"},
              "UNKNOWN repo — must be UNRESOLVED, not a fabricated score"),
    FreshCall("github_cbg", "Attacker (Nyx)", "malicious", "run_arbitrary_code",
              {"repo": "backend-api"},
              "UNKNOWN tool — must be INVALID, not scored"),
    # --- Slack ------------------------------------------------------------
    FreshCall("slack_cbg", "Dana (PM)", "benign", "slack_get_channel_history",
              {"channel": "general"}, "read the open channel — low"),
    FreshCall("slack_cbg", "Mara (HR)", "benign", "slack_post_message",
              {"channel": "announcements"}, "post to announcements — modest"),
    FreshCall("slack_cbg", "Attacker (Nyx)", "malicious", "slack_get_channel_history",
              {"channel": "exec-private"},
              "read a private exec channel (sens 4) — should be high+"),
    FreshCall("slack_cbg", "Attacker (Nyx)", "malicious", "slack_post_message",
              {"channel": "incident-response"},
              "post into incident-response (sens 4) — should be high+"),
    FreshCall("slack_cbg", "Attacker (Nyx)", "malicious", "slack_get_channel_history",
              {"channel": "novacorp-secret"},
              "UNKNOWN channel — must be UNRESOLVED"),
    # --- Calendar ---------------------------------------------------------
    FreshCall("calendar_cbg", "Dana (PM)", "benign", "list_events",
              {"calendar": "team"}, "read the team calendar — baseline"),
    FreshCall("calendar_cbg", "Dana (PM)", "benign", "create_event",
              {"calendar": "team", "attendees": ["a", "b", "c"]},
              "small team event (3 attendees) — low param magnitude"),
    FreshCall("calendar_cbg", "Attacker (Nyx)", "malicious", "create_event",
              {"calendar": "executive", "attendees": [f"p{i}" for i in range(60)]},
              "60-attendee event on the exec calendar — big param should escalate"),
    FreshCall("calendar_cbg", "Attacker (Nyx)", "malicious", "send_email_invite",
              {"calendar": "recruiting", "recipients": [f"e{i}" for i in range(120)]},
              "120-recipient blast — big param should escalate"),
    FreshCall("calendar_cbg", "Attacker (Nyx)", "malicious", "delete_all_events",
              {"calendar": "executive"},
              "wipe the exec calendar — destructive, should be high/critical"),
]


@dataclass
class Scored:
    fresh: FreshCall
    resolved_asset: str | None
    tool_impact: int | None
    sensitivity: int | None
    score: float | None
    band: str
    param_band: str | None
    final_band: str
    scorable: bool
    reason: str


def score_fresh(calls: list[FreshCall]) -> list[Scored]:
    """Score each fresh call with static-only call scoring (band + param escalation)."""
    scans: dict[str, object] = {}
    rubrics = load_param_rubrics(SCAN_DIR)
    results: list[Scored] = []
    for fc in calls:
        if fc.server not in scans:
            scans[fc.server] = load_scan(SCAN_DIR / f"{fc.server}.json")
        table = scans[fc.server]
        rubric = rubrics.get(fc.server, {}).get(fc.tool)
        call = Call(source=fc.server, index="", tool=fc.tool, args=fc.args, persona=fc.persona)
        sc = score_call(call, table, rubric)
        results.append(
            Scored(
                fresh=fc,
                resolved_asset=sc.asset,
                tool_impact=sc.tool_impact,
                sensitivity=sc.sensitivity,
                score=sc.score,
                band=sc.band,
                param_band=sc.param_band,
                final_band=sc.final_band,
                scorable=sc.scorable,
                reason=sc.reason,
            )
        )
    return results


def _audit(results: list[Scored]) -> list[str]:
    """Turn the results into pass/fail checks that the scorer is honest, not hardcoded."""
    checks: list[str] = []

    def find(note_substr: str) -> Scored | None:
        return next((r for r in results if note_substr in r.fresh.note), None)

    unknown_asset = find("UNKNOWN repo")
    checks.append(
        f"- Unknown asset is NOT fabricated: `push_files` on a repo the scan never "
        f"enumerated → **{unknown_asset.final_band}** "
        f"({'PASS' if unknown_asset and not unknown_asset.scorable else 'FAIL'})"
    )
    unknown_tool = find("UNKNOWN tool")
    checks.append(
        f"- Unknown tool is NOT fabricated: `run_arbitrary_code` (not advertised) → "
        f"**{unknown_tool.final_band}** "
        f"({'PASS' if unknown_tool and unknown_tool.band == 'invalid' else 'FAIL'})"
    )
    # Ordering: same tool, more sensitive asset scores higher.
    pub = next((r for r in results if r.fresh.tool == "get_file_contents"
                and r.fresh.args.get("repo") == "public-website"), None)
    infra = next((r for r in results if r.fresh.tool == "get_file_contents"
                  and r.fresh.args.get("repo") == "infra-config"), None)
    if pub and infra and pub.score is not None and infra.score is not None:
        ok = infra.score > pub.score
        checks.append(
            f"- Sensitivity ordering holds: same `get_file_contents`, public-website "
            f"(sens {pub.sensitivity}, score {pub.score:g}) < infra-config "
            f"(sens {infra.sensitivity}, score {infra.score:g}) ({'PASS' if ok else 'FAIL'})"
        )
    # Parameter magnitude escalates: big attendee list raises the band.
    small = next((r for r in results if r.fresh.tool == "create_event"
                  and len(r.fresh.args.get("attendees", [])) == 3), None)
    big = next((r for r in results if r.fresh.tool == "create_event"
                and len(r.fresh.args.get("attendees", [])) == 60), None)
    if small and big:
        ok = _rank(big.final_band) >= _rank(small.final_band) and big.param_band is not None
        checks.append(
            f"- Input magnitude escalates: create_event 3 attendees → "
            f"**{small.final_band}** vs 60 attendees → **{big.final_band}** "
            f"(param_band {big.param_band}) ({'PASS' if ok else 'FAIL'})"
        )
    return checks


_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def _rank(band: str) -> int:
    return _ORDER.get(band, 0)


# Servers whose full scan matrices we audit for score↔band consistency.
_AUDIT_SERVERS = ("github_cbg", "slack_cbg", "calendar_cbg")


def _monotonicity_audit() -> list[str]:
    """Check each scan's bands are a consistent (monotone) function of its own scores.

    The scanner assigns each cell's band by a separate per-cell LLM judgement,
    not by thresholding the numeric score (see ``call_scoring.tables.cell``), so
    the two can disagree. This surfaces where they do — a calibration issue in
    the *scan*, independent of the (faithful) scorer.
    """
    lines: list[str] = []
    for stem in _AUDIT_SERVERS:
        path = SCAN_DIR / f"{stem}.json"
        if not path.exists():
            continue
        import json

        raw = json.loads(path.read_text(encoding="utf-8"))
        cells: list[tuple[float, str, str]] = []  # (score, band, "asset/tool")
        for asset, row in raw.get("cells", {}).items():
            for tool, score in row.items():
                band = raw.get("bands", {}).get(asset, {}).get(tool)
                if band in _ORDER:
                    cells.append((float(score), band, f"{asset}/{tool}"))

        # Same score, more than one band.
        by_score: dict[float, set[str]] = {}
        for score, band, _cell in cells:
            by_score.setdefault(score, set()).add(band)
        ambiguous = {s: b for s, b in by_score.items() if len(b) > 1}

        # Rank inversion: a cell with a LOWER score carries a HIGHER band than a
        # cell with a HIGHER score. Each tuple is (low_score, low_band, low_cell,
        # high_score, high_band, high_cell) with low_score < high_score.
        inversions = []
        for i, (s_a, b_a, c_a) in enumerate(cells):
            for s_b, b_b, c_b in cells[i + 1:]:
                if s_a < s_b and _rank(b_a) > _rank(b_b):
                    inversions.append((s_a, b_a, c_a, s_b, b_b, c_b))
                elif s_b < s_a and _rank(b_b) > _rank(b_a):
                    inversions.append((s_b, b_b, c_b, s_a, b_a, c_a))

        status = "PASS" if not ambiguous and not inversions else "PROBLEM"
        lines.append(
            f"- **{stem}** ({len(cells)} cells): {len(ambiguous)} scores map to "
            f"multiple bands, {len(inversions)} score↔band rank inversions (pairwise) "
            f"({status})"
        )
        for s_lo, b_lo, c_lo, s_hi, b_hi, c_hi in inversions[:2]:
            lines.append(
                f"    - inversion: lower score {s_lo:g} → **{b_lo}** ({c_lo}) yet "
                f"higher score {s_hi:g} → **{b_hi}** ({c_hi})"
            )
    return lines


def _render(results: list[Scored]) -> str:
    lines = [
        f"# Static-scoring check — fresh org “{ORG}”",
        "",
        "A new organization and new personas the scanner never saw, scored with",
        "**static scoring only** (the design-time (tool, asset) band from the scan,",
        "escalated by the input-parameter rubric — no dynamic/behavioral signal).",
        "Intent labels are for the reader; they are **not** inputs to the score.",
        "",
        "## Honesty / no-overfit checks (the scorer)",
        "",
        "These confirm the *scorer* is faithful: it never invents a number, and it",
        "orders risk by asset sensitivity and input magnitude.",
        "",
    ]
    lines += _audit(results)
    lines += [
        "",
        "## Scan calibration audit (the scan matrix itself)",
        "",
        "Separately, this checks whether each **scan's** band labels are a consistent",
        "function of its own risk scores. They are assigned by a per-cell LLM",
        "judgement, not by thresholding the score, so they can disagree — a quality",
        "issue in the *scan*, not the scorer:",
        "",
    ]
    lines += _monotonicity_audit()
    lines += [
        "",
        "## Every scored call",
        "",
        "| server | persona | intent | tool | target | resolved asset | sens | score | band | param | final | why |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in results:
        fc = r.fresh
        target = fc.args.get("repo") or fc.args.get("channel") or fc.args.get("calendar") or "—"
        n_param = ""
        for k in ("attendees", "recipients"):
            if isinstance(fc.args.get(k), list):
                n_param = f" ({len(fc.args[k])} {k})"
        score = f"{r.score:g}" if r.score is not None else "—"
        lines.append(
            f"| {fc.server} | {fc.persona} | {fc.intent} | `{fc.tool}` | {target}{n_param} | "
            f"{r.resolved_asset or '—'} | {r.sensitivity if r.sensitivity is not None else '—'} | "
            f"{score} | {r.band} | {r.param_band or '—'} | **{r.final_band}** | {fc.note} |"
        )
    lines.append("")
    return "\n".join(lines)


def _write_csv(results: list[Scored], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        w = csv.writer(handle)
        w.writerow(["server", "persona", "intent", "tool", "target", "resolved_asset",
                    "tool_impact", "sensitivity", "score", "band", "param_band",
                    "final_band", "scorable", "reason"])
        for r in results:
            fc = r.fresh
            target = fc.args.get("repo") or fc.args.get("channel") or fc.args.get("calendar") or ""
            w.writerow([fc.server, fc.persona, fc.intent, fc.tool, target, r.resolved_asset or "",
                        r.tool_impact if r.tool_impact is not None else "",
                        r.sensitivity if r.sensitivity is not None else "",
                        r.score if r.score is not None else "", r.band, r.param_band or "",
                        r.final_band, r.scorable, r.reason])


def main() -> int:
    results = score_fresh(FRESH_CALLS)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = _render(results)
    (OUT_DIR / "SUMMARY.md").write_text(summary, encoding="utf-8")
    _write_csv(results, OUT_DIR / "static_scores.csv")
    print(summary)
    print(f"\nWritten to {OUT_DIR}/SUMMARY.md and static_scores.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
