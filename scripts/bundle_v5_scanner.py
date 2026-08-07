"""Package the static scanner plus every input it needs into one self-contained zip.

The zip is written into the arm's own results folder and, once unpacked, reads
**nothing outside itself**. Every path a bundled file resolves points back into
the bundle: the package modules already derive their root from
``Path(__file__).resolve().parents[3]``, so preserving ``src/mcp_security/...``
inside the bundle is enough for those, and the handful of constants that pointed
at awkward repo locations (``reports/tool_lists``, the finance catalogs under
``reports/experiments/static_scanner/inputs``, the default output directory) are
rewritten to a flat ``inputs/`` and ``results/`` layout.

Those rewrites happen **only in the copies placed inside the zip** -- the repo's
own sources are never touched.

The module list is not hand-maintained: it is the transitive import closure of
the driver, so a new import cannot silently leave a file out of the bundle.

The organization's inventory-grade profile (``server-profiles.md``) is the
held-out answer key. It travels under ``inputs/ground_truth/`` -- deliberately
*not* at the path ``server_profiles.PROFILE_DOC`` would look in, so a bundled run
cannot read it even by accident.

Run:  uv run python scripts/bundle_v5_scanner.py
      uv run python scripts/bundle_v5_scanner.py --arm senscis --verify
"""

from __future__ import annotations

import argparse
import ast
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
DRIVER = REPO_ROOT / "scripts" / "scan_policy_v5.py"
V5 = REPO_ROOT / "reports" / "experiments" / "v5"

# Path constants rewritten in the bundled copies so the bundle is self-contained.
# (file relative to repo root, exact source text, replacement text)
PATH_REWRITES: tuple[tuple[str, str, str], ...] = (
    (
        "scripts/scan_policy_v5.py",
        'TOOL_LISTS = REPO_ROOT / "reports" / "tool_lists"',
        'TOOL_LISTS = REPO_ROOT / "inputs" / "tool_catalogs"',
    ),
    (
        "scripts/scan_policy_v5.py",
        'FINANCE_CATALOGS = REPO_ROOT / "reports" / "experiments" / "static_scanner" / "inputs"',
        'FINANCE_CATALOGS = REPO_ROOT / "inputs" / "finance_catalogs"',
    ),
    (
        "scripts/scan_policy_v5.py",
        'DEFAULT_OUT = REPO_ROOT / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5"',
        'DEFAULT_OUT = REPO_ROOT / "results"',
    ),
    (
        "src/mcp_security/scanner/tool_list.py",
        'TOOL_LIST_DIR = REPO_ROOT / "reports" / "tool_lists"',
        'TOOL_LIST_DIR = REPO_ROOT / "inputs" / "tool_catalogs"',
    ),
    (
        "src/mcp_security/atomic_ops/classifier.py",
        'DEFAULT_TAXONOMY = (\n    REPO_ROOT\n    / "presentations"\n    / "heatmap_byhand"'
        '\n    / "csv"\n    / "atomic_operations.csv"\n)',
        'DEFAULT_TAXONOMY = REPO_ROOT / "inputs" / "atomic_operations.csv"',
    ),
)

# Data files the code reads that live outside any package directory.
# (source relative to repo root, destination relative to the bundle root)
EXTRA_DATA: tuple[tuple[str, str], ...] = (
    (
        "presentations/heatmap_byhand/csv/atomic_operations.csv",
        "inputs/atomic_operations.csv",
    ),
)

# The driver's MODES dict sends every arm to a repo path spelled inline; inside
# the bundle every arm writes under results/<arm>/ instead.
MODES_REWRITE = ('REPO_ROOT / "reports/experiments/v5/', 'REPO_ROOT / "results/')


def import_closure(entry: Path) -> set[Path]:
    """Every ``mcp_security`` module reachable from ``entry``, plus package inits."""

    def to_path(module: str) -> Path | None:
        for candidate in (
            SRC / (module.replace(".", "/") + ".py"),
            SRC / module.replace(".", "/") / "__init__.py",
        ):
            if candidate.exists():
                return candidate
        return None

    def package_of(path: Path) -> str:
        parts = list(path.relative_to(SRC).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
            return ".".join(parts)
        return ".".join(parts[:-1])

    found: set[Path] = {entry}
    pending, seen = [entry], set()

    def add(path: Path) -> None:
        """Queue a module, and every package ``__init__`` importing it will run."""
        if path not in found:
            found.add(path)
            pending.append(path)
        # Importing a submodule executes its packages' __init__ first, so those
        # inits -- and whatever *they* import -- are part of the closure too.
        if not path.is_relative_to(SRC):
            return
        parent = path.parent
        while parent != SRC:
            init = parent / "__init__.py"
            if init.exists() and init not in found:
                found.add(init)
                pending.append(init)
            parent = parent.parent

    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        base = package_of(current) if current.is_relative_to(SRC) else ""
        for node in ast.walk(ast.parse(current.read_text(encoding="utf-8"))):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    root = base
                    for _ in range(node.level - 1):
                        root = root.rsplit(".", 1)[0] if "." in root else ""
                    prefix = f"{root}.{node.module}" if node.module else root
                else:
                    prefix = node.module or ""
                if not prefix:
                    continue
                names = [prefix] + [f"{prefix}.{alias.name}" for alias in node.names]
            for name in names:
                if not name.startswith("mcp_security"):
                    continue
                path = to_path(name)
                if path:
                    add(path)
    return found


def rewrite(text: str, rel: str) -> str:
    """Apply this file's path rewrites, failing loudly if an anchor is gone."""
    for target, old, new in PATH_REWRITES:
        if target != rel:
            continue
        if old not in text:
            raise SystemExit(f"[FAIL] {rel}: rewrite anchor not found:\n  {old}")
        text = text.replace(old, new)
    if rel == "scripts/scan_policy_v5.py":
        old, new = MODES_REWRITE
        if old not in text:
            raise SystemExit(f"[FAIL] {rel}: MODES anchor not found: {old}")
        text = text.replace(old, new)
    return text


def stage(bundle: Path, arm: str) -> None:
    """Lay the whole self-contained tree out under ``bundle``."""
    arm_dir = V5 / f"five_level_v2_policy_v5r_{arm}"

    # 1. Code: the driver plus its transitive import closure, path-rewritten.
    for path in sorted(import_closure(DRIVER)):
        rel = path.relative_to(REPO_ROOT).as_posix()
        out = bundle / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rewrite(path.read_text(encoding="utf-8"), rel), encoding="utf-8")

    # 2. Data files that live inside the package (rule tables, vendored catalogs).
    for data_dir in SRC.rglob("data"):
        if not data_dir.is_dir():
            continue
        shutil.copytree(data_dir, bundle / data_dir.relative_to(REPO_ROOT), dirs_exist_ok=True)

    # 3. The organization's policy -- the only org input the scanner reads.
    for doc in (REPO_ROOT / "docs" / "mcp-tools").glob("*.md"):
        if doc.name == "server-profiles.md":
            continue  # the held-out answer key; staged out of reach below
        out = bundle / "docs" / "mcp-tools" / doc.name
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(doc, out)
    spec = REPO_ROOT / "docs" / "standards" / "mcp-policy-spec.md"
    if spec.exists():
        (bundle / "docs" / "standards").mkdir(parents=True, exist_ok=True)
        shutil.copy2(spec, bundle / "docs" / "standards" / spec.name)

    # 4. Tool catalogs, flattened to inputs/.
    catalogs = bundle / "inputs" / "tool_catalogs"
    catalogs.mkdir(parents=True, exist_ok=True)
    for path in (REPO_ROOT / "reports" / "tool_lists").glob("*.json"):
        shutil.copy2(path, catalogs / path.name)
    finance = bundle / "inputs" / "finance_catalogs"
    finance.mkdir(parents=True, exist_ok=True)
    for path in (REPO_ROOT / "reports" / "experiments" / "static_scanner" / "inputs").glob(
        "*.json"
    ):
        shutil.copy2(path, finance / path.name)

    # 4b. Data files the code reads from outside any package directory.
    for source, destination in EXTRA_DATA:
        origin = REPO_ROOT / source
        if not origin.exists():
            raise SystemExit(f"[FAIL] missing data file the scanner needs: {source}")
        out = bundle / destination
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, out)

    # 5. The held-out answer key, deliberately not where the code looks for it.
    truth = REPO_ROOT / "docs" / "mcp-tools" / "server-profiles.md"
    if truth.exists():
        (bundle / "inputs" / "ground_truth").mkdir(parents=True, exist_ok=True)
        shutil.copy2(truth, bundle / "inputs" / "ground_truth" / truth.name)

    # 6. This arm's results and the prompts exactly as it ran them.
    results = bundle / "results" / f"five_level_v2_policy_v5r_{arm}"
    results.mkdir(parents=True, exist_ok=True)
    for path in sorted(arm_dir.iterdir()):
        if path.is_file() and path.suffix in {".json", ".md", ".csv"}:
            shutil.copy2(path, results / path.name)


def write_entrypoints(bundle: Path, arm: str, mode: str) -> None:
    """A local runner and a SLURM runner, both free of absolute paths."""
    (bundle / "run_scan.sh").write_text(
        f"""#!/bin/bash
# Reproduce the {arm} scan from inside this bundle. No path here points outside it.
#
#   ./run_scan.sh                 # every server in the corpus
#   ./run_scan.sh sqlite_cbg_sqlite
#   NO_LLM=1 ./run_scan.sh calendar_real   # smoke test, no model needed
set -euo pipefail
BUNDLE="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
export PYTHONPATH="$BUNDLE/src"
export OLLAMA_HOST="${{OLLAMA_HOST:-http://127.0.0.1:11434}}"
ARGS=(--impact-mode {mode} --overwrite)
[ -n "${{1:-}}" ] && ARGS+=(--only "$1")
[ -n "${{NO_LLM:-}}" ] && ARGS+=(--no-llm)
exec python "$BUNDLE/scripts/scan_policy_v5.py" "${{ARGS[@]}}"
""",
        encoding="utf-8",
    )
    (bundle / "run_scan.sh").chmod(0o755)

    (bundle / "run_scan.sbatch").write_text(
        f"""#!/bin/bash
#SBATCH --job-name=mcprisk-{arm}
#SBATCH --partition=gpu
#SBATCH --gres=gpu:rtx_4090:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=scan-%x-%j.out

# Reproduce the {arm} scan on a SLURM cluster, serving the model locally.
# Set OLLAMA_BIN and OLLAMA_MODELS for your site; everything else is relative
# to this bundle.
#
#   sbatch run_scan.sbatch [server_stem]
set -u
BUNDLE="$(cd "$(dirname "$0")" && pwd)"
OLLAMA_BIN="${{OLLAMA_BIN:-ollama}}"
PORT=$((11900 + RANDOM % 300))

export PYTHONPATH="$BUNDLE/src"
export OLLAMA_KEEP_ALIVE=10m
export OLLAMA_CONTEXT_LENGTH=16384
# Large catalogs can abort the CUDA flash-attention kernel; leave this off for
# servers with many tools (see BUNDLE_README.md).
export OLLAMA_FLASH_ATTENTION="${{OLLAMA_FLASH_ATTENTION:-1}}"

OLLAMA_HOST=127.0.0.1:$PORT "$OLLAMA_BIN" serve > "$BUNDLE/ollama-${{SLURM_JOB_ID}}.log" 2>&1 &
SERVE_PID=$!
for _ in $(seq 1 120); do
  curl -s "http://127.0.0.1:$PORT/api/tags" >/dev/null 2>&1 && break
  sleep 1
done

ARGS=(--impact-mode {mode} --overwrite)
[ -n "${{1:-}}" ] && ARGS+=(--only "$1")
OLLAMA_HOST=http://127.0.0.1:$PORT python "$BUNDLE/scripts/scan_policy_v5.py" "${{ARGS[@]}}"
RC=$?
kill "$SERVE_PID" 2>/dev/null; wait "$SERVE_PID" 2>/dev/null
exit $RC
""",
        encoding="utf-8",
    )
    (bundle / "requirements.txt").write_text("requests>=2.31\n", encoding="utf-8")


def write_readme(bundle: Path, arm: str, mode: str) -> None:
    """The bundle's own README: what is here, how to run it, what it proves."""
    n_py = len(list(bundle.rglob("*.py")))
    n_cat = len(list((bundle / "inputs").rglob("*.json")))
    (bundle / "BUNDLE_README.md").write_text(
        f"""# McpRisk v5r — `{arm}` arm, self-contained scanner bundle

Everything needed to reproduce the `{arm}` static scan. **Nothing here reads a
path outside this folder.** Unpack it anywhere.

## Run it

```bash
pip install -r requirements.txt          # requests, nothing else
./run_scan.sh                            # the whole corpus
./run_scan.sh sqlite_cbg_sqlite          # one server
NO_LLM=1 ./run_scan.sh calendar_real     # smoke test, no model needed
```

`run_scan.sh` expects an Ollama-compatible endpoint at `$OLLAMA_HOST`
(default `http://127.0.0.1:11434`). `run_scan.sbatch` starts one itself on a
SLURM node — set `OLLAMA_BIN` and `OLLAMA_MODELS` for your site.

Results land in `results/five_level_v2_policy_v5r_{arm}/`, alongside the copies
of the original run already there.

## What is in here

| Path | What it is |
|---|---|
| `scripts/scan_policy_v5.py` | the driver: one scan per server |
| `src/mcp_security/` | the scanner ({n_py} Python files — the driver's full import closure) |
| `docs/mcp-tools/server-policies.md` | **the only org input the scanner reads** — classification classes, asset registers, recognition rules, and no risk numbers anywhere |
| `docs/standards/mcp-policy-spec.md` | what a conforming policy section must contain |
| `inputs/tool_catalogs/` | captured `tools/list` output per server |
| `inputs/finance_catalogs/` | the same, for the third-party finance servers ({n_cat} catalogs in total) |
| `inputs/ground_truth/server-profiles.md` | the org's own per-asset numbers — **held out**, see below |
| `results/` | the artifacts this arm produced: `.json`, `.md`, `.csv` per server |
| `results/.../scoring-prompts-AS-RUN.md` | every prompt the run sent, rendered |

## The two inputs, and the one thing that is held out

The scanner sees exactly two documents per server: the **tool catalog** and the
**organization's policy**. The policy states what classes of data the
organization recognises and what happens if each is lost — it never states a
number from 1 to 5. Every number in `results/` is derived.

`inputs/ground_truth/server-profiles.md` is the organization's own per-asset
sensitivity inventory. It is the answer key the derived numbers are scored
against, and the scan must never see it. It is stored here **deliberately not at
the path the code would look for it**, so a run in this bundle cannot read it
even by accident.

## How a score is built

Every cell is `sensitivity × blast × impact`, each 1–5, so 1–125.

| primitive | what it asks | who decides |
|---|---|---|
| **tool impact** | what one call *does* — read, write, remove | a deterministic ladder; the model only where the ladder abstains |
| **asset sensitivity** | how bad if this asset is lost | the model, classifying the asset against the org's own policy classes |
| **blast radius** | how far the consequences *propagate* | the model |

Each artifact records which of those two answered every tool
(`tool_impact_source`), the reasoning behind each number, and the SHA-256 of both
inputs (`catalog_sha256`, `profile_sha256`) so a rerun can be checked against it.

## Note on large catalogs

Servers with many tools (`maverick`, 119) can abort the CUDA flash-attention
kernel on some driver/model combinations — `ggml_abort` in `launch_fattn`, or
`CUDA error: an illegal memory access`. It is a kernel fault, not a scanner one.
Set `OLLAMA_FLASH_ATTENTION=0` for those runs.
""",
        encoding="utf-8",
    )


def verify(bundle: Path, mode: str, stem: str) -> None:
    """Prove the staged tree runs standalone, from a copy outside the repo."""
    import subprocess

    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "bundle"
        shutil.copytree(bundle, target)
        result = subprocess.run(
            [
                sys.executable,
                str(target / "scripts" / "scan_policy_v5.py"),
                "--impact-mode",
                mode,
                "--only",
                stem,
                "--no-llm",
                "--overwrite",
            ],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(target / "src"), "PATH": "/usr/bin:/bin", "HOME": tmp},
            cwd=tmp,
        )
        tail = (result.stdout + result.stderr).strip().splitlines()[-6:]
        print("\n".join(f"    {line}" for line in tail))
        if result.returncode != 0:
            raise SystemExit(f"[FAIL] bundle does not run standalone (rc={result.returncode})")
        produced = target / "results" / "five_level_v2_policy_v5r_nacombo" / f"{stem}.json"
        alt = list((target / "results").rglob(f"{stem}.json"))
        if not produced.exists() and not alt:
            raise SystemExit("[FAIL] bundle ran but wrote no artifact")
        print(
            f"[ok] bundle runs standalone and wrote {(produced if produced.exists() else alt[0]).name}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", default="nacombo", help="which v5r arm to package")
    parser.add_argument("--verify", action="store_true", help="run the bundle standalone first")
    parser.add_argument("--verify-stem", default="calendar_real")
    args = parser.parse_args(argv)

    arm_dir = V5 / f"five_level_v2_policy_v5r_{args.arm}"
    if not arm_dir.is_dir():
        raise SystemExit(f"[FAIL] no such arm folder: {arm_dir}")
    mode = f"five_level_v2_v5r_{args.arm}"

    with tempfile.TemporaryDirectory() as tmp:
        bundle = Path(tmp) / f"mcprisk-v5r-{args.arm}"
        bundle.mkdir()
        stage(bundle, args.arm)
        write_entrypoints(bundle, args.arm, mode)
        write_readme(bundle, args.arm, mode)

        if args.verify:
            print("verifying the bundle runs with nothing but itself...")
            verify(bundle, mode, args.verify_stem)
            # Drop anything the verification run wrote.
            for path in bundle.rglob("*.log"):
                path.unlink()

        zip_path = arm_dir / f"mcprisk-v5r-{args.arm}-scanner.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(bundle.rglob("*")):
                if path.is_file():
                    archive.write(path, Path(bundle.name) / path.relative_to(bundle))

    size_mb = zip_path.stat().st_size / 1e6
    with zipfile.ZipFile(zip_path) as archive:
        members = archive.namelist()
    print(f"\n[ok] {zip_path.relative_to(REPO_ROOT)}  ({size_mb:.1f} MB, {len(members)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
