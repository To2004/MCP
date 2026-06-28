"""Deterministic correctness verifier — re-checks that the pipeline actually works.

Where :mod:`.judge` asks the LLM whether the *design* is sound and :mod:`.advisor`
opines on the *results*, this module independently **re-derives** every published
artifact and asserts it is internally consistent. It uses no LLM, so it is fully
reproducible and catches the failure the other two cannot: a scan/rank that is
methodologically fine but numerically wrong (a band that does not match its score,
a ranked call that resolves to a cell the scan never produced, a leakage path).

Each check returns a :class:`Check`; a single ``fail`` means an artifact on disk
contradicts the code that claims to have produced it.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from mcp_security.param_scoring.combine import escalate

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAN_DIR = REPO_ROOT / "reports" / "scan"
TOOL_LISTS = REPO_ROOT / "reports" / "tool_lists"
RANKED_CSV = REPO_ROOT / "reports" / "ranked_calls.csv"

BANDS = ("low", "medium", "high", "critical")
# Ordinal used by the call ranker (corpus._rank_key); mirrors call_scoring.BAND_ORDER
# for the bands a scored call can carry. Higher = riskier = ranked first.
BAND_ORDER = {"critical": 5, "high": 4, "medium": 3, "low": 2}
# Source trees that must NEVER *read* the eval-only tables as scoring input. The
# scanner/scorers work from fresh scans; the committed tables only grade them.
# (static_scoring is the ground-truth *generator* — it legitimately writes them,
# so it is excluded here; the guard targets the live scoring path.)
SCORING_DIRS = ("scanner", "call_scoring", "param_scoring")
EVAL_ONLY = ("reports/samples", "reports/evaluation")
# A path literal is leakage only if the same line also *reads* it.
READ_TOKENS = ("open(", "read_text", "json.load", ".load(", "loads(", "read_bytes")
FORMULA_TOLERANCE = 1e-6


@dataclass(frozen=True)
class Check:
    """One verified invariant: ``ok`` with a human-readable ``detail``."""

    name: str
    ok: bool
    detail: str

    @property
    def mark(self) -> str:
        return "✅" if self.ok else "❌"


def _scan_files() -> list[Path]:
    """Published scans (excluding the ``*_params.json`` rubric side-files)."""
    return [p for p in sorted(SCAN_DIR.glob("*.json")) if not p.stem.endswith("_params")]


def _load(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def check_no_leakage_paths() -> Check:
    """No live scoring source *reads* the eval-only ground-truth tables.

    A docstring mention or a write-time ``--out`` default is fine; only a line that
    pairs an eval-only path with a read call (open/load/read_text) is leakage.
    """
    hits: list[str] = []
    for sub in SCORING_DIRS:
        root = REPO_ROOT / "src" / "mcp_security" / sub
        for py in root.rglob("*.py"):
            for lineno, line in enumerate(py.read_text("utf-8").splitlines(), 1):
                if not any(n in line for n in EVAL_ONLY):
                    continue
                if any(tok in line for tok in READ_TOKENS):
                    hits.append(f"{py.relative_to(REPO_ROOT)}:{lineno}")
    ok = not hits
    detail = "no live scoring source reads reports/samples or reports/evaluation" if ok \
        else "LEAKAGE (reads eval tables): " + "; ".join(hits)
    return Check("no_leakage_paths", ok, detail)


def check_scan_formula() -> Check:
    """Every scan cell equals sensitivity x blast_radius x tool_impact (the formula)."""
    bad: list[str] = []
    n = 0
    for path in _scan_files():
        d = _load(path)
        sens, impact, blast, cells = (
            d["asset_sensitivity"], d["tool_impact"], d["blast_radius"], d["cells"],
        )
        for asset, row in cells.items():
            for tool, score in row.items():
                bl = blast.get(f"{tool}|{asset}")
                if bl is None:
                    bad.append(f"{path.stem}: missing blast {tool}|{asset}")
                    continue
                expected = sens[asset] * bl * 1.0 * impact[tool]
                n += 1
                if abs(expected - score) > FORMULA_TOLERANCE:
                    bad.append(f"{path.stem}: {tool}x{asset} {score}!={expected}")
    ok = not bad
    return Check("scan_formula", ok,
                 f"{n} cells satisfy score=sensitivity*blast*impact" if ok
                 else "; ".join(bad[:8]))


def check_band_distribution() -> Check:
    """Each scan's published band_distribution recounts exactly from its band cells."""
    bad: list[str] = []
    for path in _scan_files():
        d = _load(path)
        counts = dict.fromkeys(BANDS, 0)
        for row in d["bands"].values():
            for band in row.values():
                if band not in BANDS:
                    bad.append(f"{path.stem}: invalid band '{band}'")
                    continue
                counts[band] += 1
        published = {k: v for k, v in d.get("band_distribution", {}).items() if v}
        recomputed = {k: v for k, v in counts.items() if v}
        if published != recomputed:
            bad.append(f"{path.stem}: dist {published} != recomputed {recomputed}")
    ok = not bad
    return Check("band_distribution", ok,
                 f"{len(_scan_files())} scans: band_distribution matches cells" if ok
                 else "; ".join(bad[:8]))


def check_cell_coverage() -> Check:
    """Every tool/asset appearing in cells is declared in tool_impact/asset_sensitivity."""
    bad: list[str] = []
    for path in _scan_files():
        d = _load(path)
        for asset, row in d["cells"].items():
            if asset not in d["asset_sensitivity"]:
                bad.append(f"{path.stem}: asset '{asset}' not in asset_sensitivity")
            for tool in row:
                if tool not in d["tool_impact"]:
                    bad.append(f"{path.stem}: tool '{tool}' not in tool_impact")
    ok = not bad
    return Check("cell_coverage", ok,
                 "every cell's tool & asset is declared" if ok else "; ".join(bad[:8]))


def _advertised_tools(kind: str) -> set[str] | None:
    """The server's advertised tool set for ``kind``: from the saved tools/list for
    disk-backed kinds, from the registry for declarative kinds (slack/calendar/
    github). None when the kind is unknown / has no source."""
    disk = TOOL_LISTS / f"{kind}.json"
    if disk.exists():
        return {t["name"] for t in _load(disk).get("tools", [])}
    from mcp_security.static_scoring import registry as reg
    loaders = {
        "slack": reg.load_slack_registry,
        "calendar": reg.load_calendar_registry,
        "github": reg.load_github_registry,
    }
    loader = loaders.get(kind)
    return {t.name for t in loader().tools} if loader else None


def check_tools_match_tool_list() -> Check:
    """Scan tool sets equal the server's own advertised tools (no invented tools).

    Disk-backed kinds (filesystem, sqlite) are checked against the saved
    ``tools/list``; declarative kinds (slack, calendar, github) against the
    registry's declared tool set. Dispatch uses the authoritative ``server_kind``.
    """
    bad: list[str] = []
    if not TOOL_LISTS.exists():
        return Check("tools_match_tool_list", False, "reports/tool_lists missing")
    for path in _scan_files():
        d = _load(path)
        kind = d.get("server_kind") or ("filesystem" if d.get("mcp_kind") == "filesystem"
                                        else "sqlite")
        want = _advertised_tools(kind)
        if want is None:
            bad.append(f"{path.stem}: no advertised tool set for kind '{kind}'")
            continue
        got = set(d["tool_impact"])
        if got != want:
            extra, missing = got - want, want - got
            bad.append(f"{path.stem}: extra={sorted(extra)} missing={sorted(missing)}")
    ok = not bad
    return Check("tools_match_tool_list", ok,
                 "scan tools equal the advertised tool set for every server" if ok
                 else "; ".join(bad[:8]))


def check_param_rubrics() -> Check:
    """Param rubrics target real scan tools and have strictly increasing cutoffs."""
    bad: list[str] = []
    n = 0
    for path in sorted(SCAN_DIR.glob("*_params.json")):
        scan = SCAN_DIR / path.name.replace("_params.json", ".json")
        tools = set(_load(scan)["tool_impact"]) if scan.exists() else set()
        for tool, rub in _load(path).get("rubrics", {}).items():
            if tools and tool not in tools:
                bad.append(f"{path.stem}: rubric tool '{tool}' absent from scan")
            for param in rub.get("parameters", []):
                if param.get("base_rank") not in BANDS:
                    bad.append(f"{path.stem}:{tool}.{param.get('name')} bad base_rank")
                mins = [c["min"] for c in param.get("cutoffs", [])]
                if mins != sorted(mins) or len(mins) != len(set(mins)):
                    bad.append(f"{path.stem}:{tool}.{param.get('name')} cutoffs not increasing")
                n += 1
    ok = not bad
    return Check("param_rubrics", ok,
                 f"{n} parameters: valid base_rank & monotonic cutoffs" if ok
                 else "; ".join(bad[:8]))


def check_ranked_calls() -> Check:
    """Every ranked row is faithful to the scans: scored rows resolve to a real cell
    with the cell's exact score/band, final_band is the param escalation of that band,
    and unscored rows carry no fabricated number. Ranking order is non-increasing."""
    if not RANKED_CSV.exists():
        return Check("ranked_calls", False, "reports/ranked_calls.csv missing")
    scans = {p.stem: _load(p) for p in _scan_files()}
    rows = list(csv.DictReader(RANKED_CSV.open(encoding="utf-8")))
    bad: list[str] = []
    scored = 0
    for r in rows:
        ident = f"{r['server']}/{r['tool']}/{r['asset']}"
        if r["scorable"] == "True":
            scored += 1
            scan = scans.get(r["server"])
            if scan is None:
                bad.append(f"{ident}: server has no scan")
                continue
            cell = scan["bands"].get(r["asset"], {}).get(r["tool"])
            if cell is None:
                bad.append(f"{ident}: not a scanned cell")
                continue
            if cell != r["band"]:
                bad.append(f"{ident}: band {r['band']}!=scan {cell}")
            expected_final = escalate(r["band"], r["param_band"]) if r["param_band"] else r["band"]
            if r["final_band"] != expected_final:
                bad.append(f"{ident}: final {r['final_band']}!=escalate {expected_final}")
        else:
            if r["score"] or r["band"] in BANDS:
                bad.append(f"{ident}: unscored row carries score/band ({r['band']})")
    # Ranking key mirrors corpus._rank_key: scored-first, then final_band, then score.
    def _key(r: dict) -> tuple[int, int, float]:
        scored = 1 if r["score"] else 0
        return (scored, BAND_ORDER.get(r["final_band"], -1), float(r["score"] or 0.0))

    keys = [_key(r) for r in rows]
    if keys != sorted(keys, reverse=True):
        bad.append("rows not ordered by (scored, final_band, score) descending")
    ok = not bad
    return Check("ranked_calls", ok,
                 f"{len(rows)} rows ({scored} scored) faithful to scans & ordered" if ok
                 else "; ".join(bad[:8]))


def check_determinism_config() -> Check:
    """The Ollama client pins greedy decoding (temperature 0) and a fixed seed."""
    client = REPO_ROOT / "src" / "mcp_security" / "llm" / "ollama_client.py"
    text = client.read_text("utf-8") if client.exists() else ""
    has_temp = '"temperature": 0' in text or "'temperature': 0" in text
    has_seed = '"seed"' in text or "'seed'" in text
    ok = has_temp and has_seed
    return Check("determinism_config", ok,
                 "ollama client uses temperature 0 + fixed seed" if ok
                 else f"temperature0={has_temp} seed={has_seed}")


CHECKS = (
    check_no_leakage_paths,
    check_scan_formula,
    check_band_distribution,
    check_cell_coverage,
    check_tools_match_tool_list,
    check_param_rubrics,
    check_ranked_calls,
    check_determinism_config,
)


def run_verification() -> list[Check]:
    """Run every deterministic check and return the results."""
    return [check() for check in CHECKS]


def to_markdown(checks: list[Check]) -> str:
    """Render the verification results as a markdown report."""
    n_ok = sum(c.ok for c in checks)
    lines = [
        "# Pipeline correctness verification (deterministic)",
        "",
        "Independent re-derivation of every published artifact — no LLM, fully "
        "reproducible. A ❌ means an on-disk artifact contradicts the code that "
        "produced it.",
        "",
        f"**{n_ok}/{len(checks)} checks pass.**",
        "",
        "| Check | Result | Detail |",
        "| --- | --- | --- |",
    ]
    for c in checks:
        lines.append(f"| `{c.name}` | {c.mark} | {c.detail} |")
    lines.append("")
    return "\n".join(lines)
