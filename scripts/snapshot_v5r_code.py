"""Snapshot the source that produced a v5r run into the experiment folder.

A scan artifact is only reproducible if you can see the code that made it. The
repo moves; the run does not. This copies every module the v5r scan path actually
executes into ``<results>/code/``, preserving its repo-relative path, and records
a sha256 per file so a result can be tied to the exact source that produced it.

Only the files on the path are copied — not the whole package. What is included
and why is listed in ``FILES`` below, and each one has a companion ``.md`` in the
same folder explaining what it does.

Run:  uv run python scripts/snapshot_v5r_code.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5r" / "code"

# Every module the v5r scan executes, with its role in one line. Order is the
# order the scan touches them.
FILES: tuple[tuple[str, str], ...] = (
    ("scripts/scan_v5.sbatch", "SLURM wrapper: starts the local model, then calls the driver"),
    ("scripts/scan_policy_v5.py", "the driver: builds the registry from two documents, writes artifacts"),
    ("src/mcp_security/scanner/tool_list.py", "loads the captured tools/list catalog into ToolSpec objects"),
    ("src/mcp_security/static_scoring/server_profiles.py", "splits the policy document into per-server sections"),
    ("src/mcp_security/static_scoring/server_policies.py", "parses the asset register and refuses a policy carrying numbers"),
    ("src/mcp_security/static_scoring/registry.py", "the data model: ToolSpec, AssetSpec, ServerRegistry"),
    ("src/mcp_security/static_scoring/static_impact.py", "the deterministic tool-impact rules (stage 1)"),
    ("src/mcp_security/static_scoring/prompts.py", "every prompt template the scan sends"),
    ("src/mcp_security/llm/ollama_client.py", "the model transport: one request per scoring decision"),
    ("src/mcp_security/static_scoring/pipeline.py", "orchestration, the four stages, and the deterministic assembly"),
    ("src/mcp_security/static_scoring/fallback.py", "offline heuristics; never reached in a strict scan"),
    ("src/mcp_security/scanner/atomic_flags.py", "post-scan enrichment: atomic ops and input ranking"),
    ("src/mcp_security/scanner/render.py", "renders the artifact as markdown and the matrix CSV"),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    manifest = []
    for rel, role in FILES:
        source = REPO_ROOT / rel
        if not source.exists():
            print(f"[FAIL] missing {rel}")
            return 1
        target = args.out_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        body = source.read_bytes()
        manifest.append(
            {
                "path": rel,
                "role": role,
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
                "lines": body.decode("utf-8", "replace").count("\n") + 1,
            }
        )
        print(f"[ok] {rel} ({manifest[-1]['lines']} lines)")

    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    total = sum(entry["lines"] for entry in manifest)
    print(f"\n{len(manifest)} files, {total} lines -> {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
