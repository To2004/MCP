"""Copy the v5 arm's exact scanner inputs into the experiment folder.

A v5 scan reads two documents per server and nothing else. This writes both into
``reports/experiments/v5/five_level_v2_policy_v5/inputs/`` so the experiment is
readable without the repo's docs tree, plus the parsed asset register as CSV —
the machine view of what the org actually disclosed.

Per server:

* ``<stem>.policy.md``    the policy section verbatim, with its sha256
* ``<stem>.tools.json``   the captured tool catalog, with its sha256
* ``<stem>.register.csv`` asset · description · tools · flags · CIA

Run:  uv run python scripts/export_v5_inputs.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mcp_security.static_scoring.server_policies import (  # noqa: E402
    parse_asset_register,
    policy_for,
)

sys.path.insert(0, str(REPO_ROOT))
from scripts.scan_policy_v5 import DEFAULT_OUT, TARGETS  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    inputs_dir = args.out_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    for target in TARGETS:
        policy = policy_for(target.server)
        rows = parse_asset_register(policy.text)
        policy_path = inputs_dir / f"{target.stem}.policy.md"
        policy_path.write_text(policy.text, encoding="utf-8")
        catalog = json.loads(target.catalog.read_text(encoding="utf-8"))
        (inputs_dir / f"{target.stem}.tools.json").write_text(
            json.dumps(catalog, indent=2), encoding="utf-8"
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["asset", "description", "tools", "flags", "cia"])
        for row in rows:
            writer.writerow(
                [row.asset_id, row.description, " ".join(row.tools), " ".join(row.flags), row.cia]
            )
        (inputs_dir / f"{target.stem}.register.csv").write_text(
            buffer.getvalue(), encoding="utf-8"
        )
        manifest.append(
            {
                "stem": target.stem,
                "server": target.server,
                "policy_sha256": hashlib.sha256(policy.text.encode("utf-8")).hexdigest(),
                "catalog_sha256": hashlib.sha256(target.catalog.read_bytes()).hexdigest(),
                "n_register_rows": len(rows),
                "n_tools": len(catalog["tools"] if isinstance(catalog, dict) else catalog),
            }
        )
        print(f"[ok] {target.stem}: {len(rows)} register rows -> {inputs_dir}")

    (inputs_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
