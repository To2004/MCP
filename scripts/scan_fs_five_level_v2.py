"""Scan ONLY the corp filesystem MCP (``fs:corp``) under the five_level_v2_na rubric.

The five_level_v2_na tool-impact ladder is the generalized action-type scale:
    1 = liveness / no-op    (ping/health -- no data effect)
    2 = metadata            (data ABOUT data: names, listing, sizes, schema)
    3 = read / observe      (see the CONTENTS, cannot change them)
    4 = write / modify      (create, edit, append, rename, MOVE -- recoverable)
    5 = delete / destroy    (remove, wipe, cancel, revoke -- irreversible)

Blast is COVERAGE of the asset (fraction of items AND of subjects one call
reaches); a call that exposes a whole-population asset (all PII / all secrets)
is blast 5 even if it is one file. The blast stage also marks (tool, asset)
pairs the tool does not act on as N/A, so those cells are not scored.

Assets are the ACTUAL files AND directories of the store (per-file + per-dir
scopes -- real names/paths, not extension buckets), and ``gen_assets`` homes
every tool on a concrete asset so no tool is left uncovered.

Unlike ``scan_real_catalogs.py`` (which always scans github/slack/calendar too),
this driver targets the single disk-backed filesystem server so the run stays
scoped to exactly one MCP. LLM-only (Qwen via Ollama) -> run on a GPU node.

Run (GPU):  python scripts/scan_fs_five_level_v2.py
Smoke:      python scripts/scan_fs_five_level_v2.py --no-llm
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from mcp_security.scanner.render import scan_to_markdown
from mcp_security.scanner.scan import scan_server, write_scan

REPO_ROOT = Path(__file__).resolve().parents[1]

KIND = "filesystem"
ROOT = REPO_ROOT / "demo" / "corp_filesystem"
SERVER = "fs:corp"
IMPACT_MODE = "five_level_v2_na"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-llm", action="store_true", help="offline baseline (smoke test only)")
    parser.add_argument("--version-tag", default=None, help="default: scan-fs-<impact-mode>")
    parser.add_argument(
        "--impact-mode", default=IMPACT_MODE,
        choices=["five_level_v2_na", "five_level_v2_ctx"],
        help="blast experiment: _na (coverage) or _ctx (per-tool understanding fed into blast)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "reports" / "experiments" / "five_level_v2_fs",
        help="where to write fs_corp.{json,md}",
    )
    args = parser.parse_args(argv)
    version_tag = args.version_tag or f"scan-fs-{args.impact_mode}"

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if not ROOT.exists():
        print(f"[FAIL] no filesystem store at {ROOT}")
        return 1

    try:
        result = scan_server(
            KIND,
            root=ROOT,
            server=SERVER,
            by_file=True,  # per-file + per-directory assets (real names/paths, not ext buckets)
            gen_assets=True,  # home every tool on a concrete asset so none is left uncovered
            use_llm=not args.no_llm,
            version=version_tag,
            impact_mode=args.impact_mode,
        )
    except Exception as exc:  # noqa: BLE001 -- report which server failed, then exit non-zero
        print(f"[FAIL] {SERVER}: {exc}")
        return 1

    path = write_scan(result, args.out_dir)
    (args.out_dir / f"{path.stem}.md").write_text(
        scan_to_markdown(result.server, result.kind, result.table), encoding="utf-8"
    )
    print(
        f"[ok] {result.server} ({args.impact_mode}): {result.n_tools} tools x "
        f"{result.n_assets} assets -> {path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
