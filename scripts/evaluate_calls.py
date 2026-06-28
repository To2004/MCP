"""Dynamic evaluation: does the request-time score separate risky calls from benign?

Reads the scored call corpus (``reports/ranked_calls.csv``) produced by the call
scorer and grades it against the calls' intent ``category`` (a *weak* label assigned
when the simulated sessions were authored, not an independent human/LLM judgment of
each call — we say so plainly and treat the result as diagnostic, not definitive).

We report what the strong defense papers report for runtime detection:

* **coverage** — what fraction of calls the static scorer can actually score vs.
  abstains on (``unresolved``) or hard-blocks as a forbidden tool (``invalid``);
* **AUC** of the risk band (1..4) against the binary risky label, on the calls the
  scorer can score (the honest separation question);
* **detection vs. false-positive** at the deny threshold (band ≥ high): TPR, FP rate
  on benign traffic, precision/recall/F1;
* **graduated vs. binary** — FP+FN at every single-threshold cut, showing no one
  binary line is good and the four-band gate routes mid-risk to log/escalate;
* **escalation-fires** — that the parameter dimension lifts bulk/destructive calls,
  and where the *static* band under-detects (read-only exfiltration), motivating a
  contextual LLM call scorer.

Run:  uv run python scripts/evaluate_calls.py
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import eval_metrics as m

REPO_ROOT = Path(__file__).resolve().parents[1]
RANKED = REPO_ROOT / "reports" / "ranked_calls.csv"
OUT_MD = REPO_ROOT / "reports" / "evaluation" / "dynamic_eval.md"
OUT_JSON = REPO_ROOT / "reports" / "evaluation" / "dynamic_eval.json"

# Weak intent labels grouped into a binary risky/benign split. MISUSE
# (in-scope tool, out-of-scope target) is access-control overreach whose correct
# verdict depends on a policy we do not encode here, so it is reported separately
# and excluded from the binary detection metrics.
RISKY = {"MALICIOUS", "BAD_PARAMS", "BAD_TOOL", "EDGE"}
BENIGN = {"DISCOVERY", "BENIGN", "VALID"}
SEPARATE = {"MISUSE"}

REAL_BANDS = {"low", "medium", "high", "critical"}
DENY_THRESHOLD = 3  # band >= high

CAT_ORDER = ["DISCOVERY", "BENIGN", "VALID", "MISUSE", "EDGE", "BAD_PARAMS", "BAD_TOOL", "MALICIOUS"]
BAND_ORDER = ["low", "medium", "high", "critical", "unresolved", "invalid"]


def _load() -> list[dict]:
    with RANKED.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _crosstab(rows: list[dict]) -> str:
    ct: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        ct[r["category"]][r["final_band"]] += 1
    lines = ["### Category × final band", "",
             "| category | " + " | ".join(BAND_ORDER) + " | total |",
             "| --- |" + " --- |" * (len(BAND_ORDER) + 1)]
    for c in CAT_ORDER:
        row = ct.get(c, Counter())
        total = sum(row.values())
        lines.append(f"| {c} | " + " | ".join(str(row.get(b, 0)) for b in BAND_ORDER)
                     + f" | {total} |")
    lines.append("")
    return "\n".join(lines)


def _coverage(rows: list[dict]) -> tuple[str, dict]:
    cov: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        status = ("scorable" if r["final_band"] in REAL_BANDS
                  else r["final_band"])  # unresolved | invalid
        cov[r["category"]][status] += 1
    lines = ["### Coverage (what the static scorer can score)", "",
             "| category | scorable | unresolved (abstain) | invalid (forbidden tool) |",
             "| --- | --- | --- | --- |"]
    summary = {}
    for c in CAT_ORDER:
        row = cov.get(c, Counter())
        lines.append(f"| {c} | {row.get('scorable', 0)} | {row.get('unresolved', 0)} "
                     f"| {row.get('invalid', 0)} |")
        summary[c] = dict(row)
    total = Counter()
    for row in cov.values():
        total.update(row)
    n = sum(total.values())
    lines.append(f"| **all** | {total.get('scorable', 0)} | {total.get('unresolved', 0)} "
                 f"| {total.get('invalid', 0)} |")
    lines += ["", f"Scorable coverage: **{total.get('scorable', 0)}/{n} "
              f"({100*total.get('scorable',0)/n:.0f}%)**. `unresolved` calls (enumeration / "
              "no-argument / unscanned target) are where the static scorer abstains — the "
              "gap a contextual LLM call scorer (future work) is meant to fill.", ""]
    return "\n".join(lines), summary


def _scored_subset(rows: list[dict]) -> tuple[list[float], list[int], list[dict]]:
    """Calls usable for binary detection: real band -> score; invalid -> deny (4).

    Returns (scores, labels, kept_rows). ``unresolved`` and MISUSE/SEPARATE are
    excluded (abstain / no binary truth). ``invalid`` (forbidden tool) is a hard
    detection and scored as deny.
    """
    scores: list[float] = []
    labels: list[int] = []
    kept: list[dict] = []
    for r in rows:
        cat = r["category"]
        if cat in SEPARATE:
            continue
        band = r["final_band"]
        if band in REAL_BANDS:
            score = float(m.BAND_RANK[band])
        elif band == "invalid":
            score = 4.0  # forbidden/unknown tool -> hard deny
        else:  # unresolved -> scorer abstains
            continue
        if cat in RISKY:
            label = 1
        elif cat in BENIGN:
            label = 0
        else:
            continue
        scores.append(score)
        labels.append(label)
        kept.append(r)
    return scores, labels, kept


def _escalation(rows: list[dict]) -> str:
    fired = [r for r in rows
             if r["param_band"] in REAL_BANDS and r["band"] in REAL_BANDS
             and m.BAND_RANK[r["final_band"]] > m.BAND_RANK[r["band"]]]
    by_cat = Counter(r["category"] for r in fired)
    # Static under-detection: scorable MALICIOUS calls that still land low/medium.
    under = [r for r in rows if r["category"] == "MALICIOUS"
             and r["final_band"] in ("low", "medium")]
    lines = ["### Parameter escalation & static under-detection", "",
             f"- parameter escalation lifted the band on **{len(fired)}** calls; "
             f"by category: {dict(by_cat)}",
             f"- scorable MALICIOUS calls still scored low/medium by the *static* cell: "
             f"**{len(under)}** — read-only exfiltration the inherent cell under-weights, "
             "the case a contextual request-time LLM scorer is designed to escalate.", ""]
    return "\n".join(lines)


def main() -> None:
    rows = _load()
    scores, labels, kept = _scored_subset(rows)

    auc = m.roc_auc(scores, labels)
    deny = m.binary_at_threshold(scores, labels, DENY_THRESHOLD)
    # Graduated vs. binary: errors at each possible single-threshold cut.
    thresholds = {2: "≥ medium", 3: "≥ high", 4: "≥ critical"}
    cuts = {t: m.binary_at_threshold(scores, labels, t) for t in thresholds}
    n = len(labels)
    npos, nneg = sum(labels), n - sum(labels)

    cov_block, cov_summary = _coverage(rows)

    out = [
        "# Dynamic evaluation: request-time risk vs. call intent", "",
        f"Scored calls: {len(rows)}. Binary detection is computed on the "
        f"**{n}** calls with a usable verdict ({npos} risky, {nneg} benign): a real band "
        "maps to its rank (low=1..critical=4), a forbidden-tool `invalid` maps to deny, "
        "`unresolved` abstentions and the access-control `MISUSE` class are excluded. "
        "Labels are the sessions' authored intent categories — a **weak** ground truth, "
        "so these numbers are diagnostic. We group "
        f"{sorted(RISKY)} as risky and {sorted(BENIGN)} as benign.", "",
        "## Separation", "",
        f"- **AUC** (risk band vs. risky label): **{auc:.2f}**"
        if auc is not None else "- AUC: undefined",
        f"- at the deny threshold (band ≥ high): detection/TPR **{100*deny['tpr']:.0f}%**, "
        f"false-positive rate on benign **{100*deny['fpr']:.0f}%**, "
        f"precision {100*deny['precision']:.0f}%, recall {100*deny['recall']:.0f}%, "
        f"F1 {100*deny['f1']:.0f}%", "",
        "## Graduated vs. a single binary threshold", "",
        "A binary gate must commit to one cut; the table shows the error count (FP+FN) at "
        "each. The four-band gate instead routes the middle to log/escalate rather than "
        "forcing allow or deny.", "",
        "| binary cut | TP | FP | TN | FN | FP+FN | TPR | FPR |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for t, name in thresholds.items():
        c = cuts[t]
        out.append(f"| {name} | {c['tp']} | {c['fp']} | {c['tn']} | {c['fn']} | "
                   f"**{c['errors']}** | {100*c['tpr']:.0f}% | {100*c['fpr']:.0f}% |")
    out += ["", _escalation(rows), cov_block, _crosstab(rows)]

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(out), encoding="utf-8")
    OUT_JSON.write_text(json.dumps({
        "n_scored_total": len(rows),
        "binary_n": n, "n_risky": npos, "n_benign": nneg,
        "auc": auc,
        "deny_threshold": dict(deny),
        "cuts": {thresholds[t]: dict(c) for t, c in cuts.items()},
        "coverage": cov_summary,
    }, indent=2), encoding="utf-8")
    print("\n".join(out))
    print(f"\nWrote {OUT_MD.relative_to(REPO_ROOT)} and {OUT_JSON.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
