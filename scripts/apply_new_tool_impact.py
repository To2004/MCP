"""Apply the new Tool Impact ladder to calls_userid_scored_v2_full.csv
in-place. Backup already created as _backup.csv.

New ladder:
  x3 — state-changing: write/delete/shell/chmod/edit/move/copy
  x2 — multi-asset reach: list_*/directory_tree/search/multi-read
  x1 — single-asset read or metadata: single read/info/create_dir/list_allowed
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

V2 = Path("C:/Users/user/Downloads/calls_userid_scored_v2_full.csv")

TOOL_IMPACT = {
    # x3 — state-changing
    "write_file": 3, "delete_file": 3, "execute_shell": 3, "chmod": 3,
    "edit_file": 3, "move_file": 3, "copy_file": 3,
    # x2 — multi-asset reach
    "list_directory": 2, "list_directory_with_sizes": 2,
    "directory_tree": 2, "search_files": 2,
    "read_multiple_files": 2,
    # x1 — single-asset / metadata
    "read_text_file": 1, "read_media_file": 1,
    "get_file_info": 1, "create_directory": 1,
    "list_allowed_directories": 1,
}


def band(score: float) -> str:
    if score >= 27:
        return "Critical"
    if score >= 13:
        return "High"
    if score >= 7:
        return "Medium"
    return "Low"


def main() -> None:
    with V2.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        rows = list(reader)

    changed = 0
    for r in rows:
        tool = r["tool"]
        new_ti = TOOL_IMPACT.get(tool, 1)
        old_ti = int(r["tool_impact"])
        if new_ti == old_ti:
            continue
        sens = int(r["sens"])
        blast = int(r["blast"])
        ai = float(r["asset_impact"])  # unchanged: sens x blast
        ll = float(r["likelihood"])    # unchanged: base_dev x anomaly x expo
        new_misuse = round(max(ai * ll * new_ti, 1.0), 2)
        r["tool_impact"] = new_ti
        r["misuse"] = new_misuse
        r["band"] = band(new_misuse)
        # Update the x-notation in why_likelihood (single occurrence per row)
        r["why_likelihood"] = re.sub(
            rf"\u00d7{old_ti}\b", f"\u00d7{new_ti}", r["why_likelihood"],
        )
        changed += 1

    with V2.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    print(f"Updated {changed} of {len(rows)} rows in {V2.name}")


if __name__ == "__main__":
    main()
