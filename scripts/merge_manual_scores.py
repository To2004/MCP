"""Merge the original calls_userid.csv columns with the manually-scored
columns from calls_userid_scored_manual.csv. Joins on `index`. No scoring
happens here -- this only re-attaches the original log fields.
"""

from __future__ import annotations

import csv
from pathlib import Path

DOWNLOADS = Path("C:/Users/user/Downloads")
SRC = DOWNLOADS / "calls_userid.csv"
MANUAL = DOWNLOADS / "calls_userid_scored_manual.csv"
OUT = DOWNLOADS / "calls_userid_scored_manual_full.csv"


def main() -> None:
    with SRC.open(encoding="utf-8", newline="") as f:
        orig = {row["index"]: row for row in csv.DictReader(f)}

    with MANUAL.open(encoding="utf-8", newline="") as f:
        manual_reader = csv.DictReader(f)
        manual_rows = list(manual_reader)
        manual_fields = manual_reader.fieldnames or []

    # Original columns to re-attach (everything except the ones the manual
    # version already has in some form -- we still keep the original `args`).
    orig_cols = [
        "timestamp", "user_id", "session_id", "jsonrpc_id",
        "status", "args", "http_status", "elapsed_s",
        "content_count", "error_code", "result",
    ]

    # Final column order: index, category, tool, target (manual summary),
    # original log fields, then scoring fields.
    score_cols = [
        "sens", "blast", "ctx", "irrev", "base_dev", "anomaly", "expo",
        "impact", "likelihood", "misuse", "band",
        "why_impact", "why_likelihood",
    ]
    headers = ["index", "category", "tool", "target", *orig_cols, *score_cols]

    written = 0
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for row in manual_rows:
            idx = row["index"]
            o = orig.get(idx, {})
            merged = {
                "index": idx,
                "category": row["category"],
                "tool": row["tool"],
                "target": row["target"],
                **{c: o.get(c, "") for c in orig_cols},
                **{c: row[c] for c in score_cols},
            }
            w.writerow(merged)
            written += 1

    print(f"Wrote {OUT} ({written} rows, {len(headers)} columns)")


if __name__ == "__main__":
    main()
