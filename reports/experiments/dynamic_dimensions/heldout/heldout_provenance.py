"""EV-02 provenance and the EV-15 freeze manifest for the v5 held-out evaluation.

Every result file carries a provenance block, so a number can be traced to the exact code,
config, policy and world that produced it (N25):

    config_digest = SHA-256(json.dumps(asdict(config), sort_keys=True))
    provenance    = {git_sha, dirty, sha256 per file, imported files,
                     config_digests and policy_digests per engine, engines, world_digest,
                     spec (family, pool, index, seed, calendar, ...),
                     PYTHONHASHSEED, python, numpy}

One result file holds several engines (v4 and v5) with different configs and policies, so
those digests are kept per engine. Two result files may be merged only when their provenance
agrees in everything but the engine list (:func:`check_mergeable`): per-engine digests must
agree on the engines both hold, file digests on the files both list, and every other field
exactly, so an ``--only`` run can add an engine. The simulator merged ``--only`` runs blindly
before (``normal_org_sim.py:1151-1153``, per Part A). :func:`merged_provenance` gives the
merged file's block.

The freeze (spec 6.3) hashes the engine and behaviour modules, every module that computes an
engine input or a score (binding, gateway, input rules, the gateway's runtime factor), the
dependency lock, the simulator files (hashed before selection, R2-6), this harness, the range
file (``heldout_world_spec.py``), the files later batches add (:data:`LATER_FILES`), the X1
scenario files and the X3 log digests, and stores the default ``BehaviourConfig`` with every
frozen constant: :func:`freeze_manifest`.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
DD = "reports/experiments/dynamic_dimensions"
#: Every module that computes a v5 engine input or a score: the behaviour engine; binding
#: (the touched asset and the floors' unique-match rule); the gateway (the scorer, the
#: per-agent baseline key of oauth.py, wire_log's logical calls and ARG-1 sizes, the protocol
#: era, the route config and the egress table); and the input rules the scorer applies.
SCORING_GLOBS = (
    "src/mcp_security/behaviour/*.py",
    "src/mcp_security/binding/*.py",
    "src/mcp_security/gateway/*.py",
    "src/mcp_security/gateway/egress/*.py",
    "src/mcp_security/gateway/egress/*.json",
    "src/mcp_security/input_rules/*.py",
)
GATEWAY_RUNTIME_FILES = (  # the runtime factor framework.gate_runtime() loads
    "scripts/dynamic_design/gate_runtime.py",
    "scripts/dynamic_design/dynamic_v2.py",
)
DEPENDENCY_FILES = ("pyproject.toml", "uv.lock")  # pin numpy, the SDK and the rest
SIMULATOR_FILES = (
    f"{DD}/normal_org_world.py",
    f"{DD}/normal_org_sim.py",
)
HARNESS_FILES = (
    f"{DD}/heldout/heldout_world_spec.py",
    f"{DD}/heldout/heldout_provenance.py",
    f"{DD}/heldout/select_v5.py",
    f"{DD}/heldout/heldout_metrics.py",
    f"{DD}/heldout/heldout_stats.py",
    f"{DD}/heldout/combiner_family.py",
    f"{DD}/heldout/outside_baselines.py",
)
#: The harness files later batches add (spec 6.3 counts them as the harness). The freeze
#: needs every one of them; before they land, ``freeze_files(allow_missing_later=True)``.
LATER_FILES = (
    f"{DD}/heldout_run_world.py",  # J5, Batch 2
    f"{DD}/gateway_replay_world.py",  # K2, Batch 3
    f"{DD}/adaptive_gray_kinds.py",  # K3, Batch 3
    f"{DD}/era_swap.py",  # K5, Batch 3
    "scripts/dynamic_design/heldout_array.sbatch",  # K4, Batch 3
)
LATER_GLOBS = (f"{DD}/catalogs/*",)  # J6, Batch 2: the Slack and other catalogs
RANGE_FILE = f"{DD}/heldout/heldout_world_spec.py"
#: Fields two mergeable runs may differ in: the engines, the time, and which files each
#: process happened to import (shared files are still compared through ``sha256``).
MERGE_IGNORED = frozenset({"engines", "created", "imported"})
PER_ENGINE_FIELDS = ("config_digests", "policy_digests")  # compared on the shared engines
PER_FILE_FIELD = "sha256"  # compared on the files both blocks list
NOT_DIGESTED = frozenset({"git", "runtime"})  # recorded in the manifest, left out of its digest
GIT_TIMEOUT_S = 30
READ_CHUNK = 1 << 20
NOT_SET = "unset"


class ProvenanceMismatch(ValueError):
    """Two result files cannot be merged: their provenance differs."""


# ── digests ──────────────────────────────────────────────────────────────────────────────────
def _encode(value: object) -> object:
    """JSON form of the values ``json`` does not know: dataclasses, sets, paths, numpy."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=repr)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"cannot encode {type(value).__name__} for a digest")


def canonical_json(value: object) -> str:
    """``json.dumps(value, sort_keys=True)`` with dataclasses, sets, paths and numpy encoded:
    the text every digest here is taken over."""
    return json.dumps(value, sort_keys=True, default=_encode)


def digest(value: object) -> str:
    """SHA-256 hex digest of :func:`canonical_json`."""
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def config_digest(config: object) -> str:
    """EV-02: SHA-256(json.dumps(asdict(config), sort_keys=True)); a mapping is taken as is."""
    if dataclasses.is_dataclass(config) and not isinstance(config, type):
        return digest(dataclasses.asdict(config))
    if isinstance(config, Mapping):
        return digest(dict(config))
    raise TypeError(
        f"config must be a dataclass instance or a mapping, not {type(config).__name__}"
    )


def file_sha256(path: str | Path) -> str:
    """SHA-256 hex digest of a file's bytes."""
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(READ_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def code_hashes(paths: Iterable[str | Path], root: Path = REPO) -> dict[str, str]:
    """SHA-256 of each file, keyed by its path relative to ``root``. A missing file raises
    ``FileNotFoundError``: a frozen file list never skips a file."""
    out = {}
    for p in paths:
        path = Path(p) if Path(p).is_absolute() else root / p
        if not path.is_file():
            raise FileNotFoundError(f"cannot hash {path}: no such file")
        out[_relative(path, root)] = file_sha256(path)
    return dict(sorted(out.items()))


def _relative(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(root.resolve()))
    except ValueError:
        return str(resolved)


# ── the running process ──────────────────────────────────────────────────────────────────────
def git_state(repo: Path = REPO) -> dict[str, object]:
    """The repository head and whether the tree is dirty; ``git_sha`` None when git cannot be
    run (the per-file digests then identify the code)."""
    try:
        head = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT_S,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT_S,
        ).stdout
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return {"git_sha": None, "dirty": None, "git_error": type(exc).__name__}
    return {"git_sha": head, "dirty": bool(status.strip())}


def imported_files(root: Path = REPO) -> list[str]:
    """Every source file under ``root`` that the running process has imported, relative."""
    base = root.resolve()
    found = set()
    for module in list(sys.modules.values()):
        name = getattr(module, "__file__", None)
        if not name:
            continue
        path = Path(name).resolve()
        if path.is_file() and path.is_relative_to(base):
            found.add(str(path.relative_to(base)))
    return sorted(found)


def runtime() -> dict[str, str]:
    """Interpreter, numpy and hash-seed facts."""
    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED", NOT_SET),
    }


# ── provenance blocks ────────────────────────────────────────────────────────────────────────
def provenance(
    *,
    configs: Mapping[str, object] | None = None,
    policies: Mapping[str, object] | None = None,
    world_digest: str | None = None,
    spec: object | None = None,
    files: Sequence[str | Path] | None = None,
    root: Path = REPO,
) -> dict[str, object]:
    """One result's provenance block (EV-02).

    ``configs`` maps each engine scored (``"v4"``, ``"v5"``) to its config; their digests are
    stored per engine, and the engine list is their keys. ``policies`` maps engines to their
    learned policy (a mapping, or a path whose bytes are hashed). ``world_digest`` is the digest
    of the world's rows, ``spec`` the world's :class:`heldout_world_spec.WorldSpec` (its fields
    are stored: family, pool, index, seed, calendar, ...). ``files`` defaults to every
    repository file the process imported.
    """
    engine_configs = dict(configs or {})
    engine_policies = dict(policies or {})
    unknown = sorted(set(engine_policies) - set(engine_configs))
    if unknown:
        raise ValueError(f"policies for engines without a config: {unknown}")
    paths = imported_files(root) if files is None else list(files)
    block: dict[str, object] = dict(git_state(root))
    block["sha256"] = code_hashes(paths, root)
    block["imported"] = imported_files(root)
    block["config_digests"] = {e: config_digest(c) for e, c in sorted(engine_configs.items())}
    block["policy_digests"] = {e: _policy_digest(p) for e, p in sorted(engine_policies.items())}
    block["world_digest"] = world_digest
    block["spec"] = None if spec is None else json.loads(canonical_json(spec))
    block["engines"] = sorted(engine_configs)
    block.update(runtime())
    return block


def _policy_digest(policy: object) -> str:
    if isinstance(policy, (str, Path)):
        return file_sha256(policy)
    return digest(policy)


def _shared_differ(saved: object, new: object) -> list[str]:
    """Keys both mappings hold with different values (a non-mapping side differs whole)."""
    if not isinstance(saved, Mapping) or not isinstance(new, Mapping):
        return [] if saved == new else ["(whole field)"]
    return sorted(str(k) for k in set(saved) & set(new) if saved[k] != new[k])


def check_mergeable(
    saved: Mapping[str, object],
    new: Mapping[str, object],
    ignored: Iterable[str] = MERGE_IGNORED,
) -> None:
    """Refuse a merge of two result files whose provenance differs in anything but the engine
    list: ``ProvenanceMismatch`` names every differing field.

    Per-engine digests (:data:`PER_ENGINE_FIELDS`) must agree on the engines both blocks
    hold, file digests on the files both list; every other field must be equal.
    """
    skip = set(ignored)
    differ = []
    for key in sorted((set(saved) | set(new)) - skip):
        if key in PER_ENGINE_FIELDS or key == PER_FILE_FIELD:
            bad = _shared_differ(saved.get(key, {}), new.get(key, {}))
            differ += [f"{key}[{k}]" for k in bad]
        elif saved.get(key) != new.get(key):
            differ.append(key)
    if differ:
        raise ProvenanceMismatch(f"provenance differs in {differ}; refusing to merge")


def merged_provenance(saved: Mapping[str, object], new: Mapping[str, object]) -> dict[str, object]:
    """The block of a merged result file: :func:`check_mergeable`, then the union of the
    engines, the per-engine digests, the file digests and the imported files."""
    check_mergeable(saved, new)
    out = dict(saved)
    for key in (*PER_ENGINE_FIELDS, PER_FILE_FIELD):
        merged = {**dict(saved.get(key) or {}), **dict(new.get(key) or {})}
        out[key] = dict(sorted(merged.items()))
    for key in ("engines", "imported"):
        out[key] = sorted(set(saved.get(key) or ()) | set(new.get(key) or ()))
    return out


# ── the freeze (EV-15, spec 6.3) ─────────────────────────────────────────────────────────────
def freeze_files(
    root: Path = REPO,
    *,
    imported: Iterable[str | Path] = (),
    allow_missing_later: bool = False,
) -> list[Path]:
    """The files the freeze hashes.

    - every module of :data:`SCORING_GLOBS`, the gateway's runtime factor and the dependency
      lock;
    - the simulator files, the harness and the range file;
    - the files later batches add (:data:`LATER_FILES`, :data:`LATER_GLOBS`);
    - ``imported``: pass :func:`imported_files` after a real scoring run in the same process,
      so every module the run imported is pinned too.

    A named file that is missing raises ``FileNotFoundError``. The later files may be missing
    only with ``allow_missing_later``, for a preview before they land; the freeze needs them.
    """
    named = [*GATEWAY_RUNTIME_FILES, *DEPENDENCY_FILES, *SIMULATOR_FILES, *HARNESS_FILES]
    paths = [p for pattern in SCORING_GLOBS for p in root.glob(pattern)]
    paths += [root / p for p in named]
    paths += [Path(p) if Path(p).is_absolute() else root / p for p in imported]
    missing = [str(p) for p in paths if not p.is_file()]
    later = [root / p for p in LATER_FILES]
    later += [p for pattern in LATER_GLOBS for p in root.glob(pattern) if p.is_file()]
    missing_later = [str(p) for p in later if not p.is_file()]
    missing_later += [
        f"{root / pattern} (no file)" for pattern in LATER_GLOBS if not any(root.glob(pattern))
    ]
    if missing_later and not allow_missing_later:
        missing += missing_later
    if missing:
        raise FileNotFoundError(f"freeze files missing: {missing}")
    return sorted({p for p in paths + later if p.is_file()})


def freeze_manifest(
    config: object,
    constants: Mapping[str, object],
    *,
    files: Sequence[str | Path] | None = None,
    x1_scenarios: Sequence[str | Path] = (),
    x3_log_digests: Mapping[str, str] | None = None,
    root: Path = REPO,
) -> dict[str, object]:
    """The freeze record: SHA-256 of every frozen file and X1 scenario file, the X3 log
    digests, the default config and its digest, and every frozen constant (shares, floor
    prices and budgets, RF1 constants, surge constants, value cap, idle gap, windows, the
    alert line and the list rule). Its own digest goes into the preregistration.

    The digest covers the code, the lock file, the inputs and the constants only. The git
    state and the runtime (python, numpy, ``PYTHONHASHSEED``) are recorded beside it but left
    out, so anyone can re-derive the digest from the frozen files on any machine; the
    dependency versions are pinned through ``uv.lock`` among the files.
    """
    paths = freeze_files(root) if files is None else list(files)
    record: dict[str, object] = {
        "git": git_state(root),
        "sha256": code_hashes(paths, root),
        "x1_scenarios": code_hashes(x1_scenarios, root),
        "x3_log_digests": dict(sorted((x3_log_digests or {}).items())),
        "config": json.loads(canonical_json(config)),
        "config_digest": config_digest(config),
        "constants": json.loads(canonical_json(dict(constants))),
        "runtime": runtime(),
    }
    record["manifest_digest"] = digest({k: v for k, v in record.items() if k not in NOT_DIGESTED})
    return record
