"""Evaluate the embedding-based likelihood on the big-three sims and emit the formula files.

For each server (calendar, github, slack — the ``dyn_<server>_cbg`` sessions):

1. **Frozen eval** — fit every candidate architecture on the BENIGN calls in the first
   70% of the stream (chronological); score the entire held-out tail (benign + misuse +
   malicious). Report per-architecture AUC / separation / TPR-FPR; the single winner
   (best mean malicious-AUC across servers) is used for the output files.
2. **``<server>_test.csv``** — held-out calls only, scored by the frozen winner:
   the "calls the autoencoder never trained on" file.
3. **``<server>_stream.csv``** — honest prequential replay: row 1 is the genuinely first
   call ever seen (no history -> likelihood 1.0); the model refits every
   ``REFIT_EVERY`` calls on *all* previously seen calls (no labels — contamination is
   handled by the model's label-free self-trimming pass, ``trim_z=TRIM_Z`` (0.8x the ramp start)).

Every row carries the full v6 formula: ``final_risk = static_score x likelihood``, where
``static_score`` is the scanned (tool, asset) cell (worst-case fallback when a call does
not resolve) and ``likelihood`` comes from :mod:`mcp_security.dynamic.embedding`.

Outputs land in ``reports/dynamic_eval/embedding/``: six CSVs, ``metrics.json`` and the
``EMBEDDING_LIKELIHOOD.md`` report. Deterministic, no LLM, no network.

Usage::

    uv run python scripts/eval_embedding_likelihood.py
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_security.call_scoring.loader import Call, load_calls  # noqa: E402
from mcp_security.call_scoring.score import score_call  # noqa: E402
from mcp_security.call_scoring.tables import SCAN_DIR, StaticTable, load_scan  # noqa: E402
from mcp_security.dynamic.embedding import (  # noqa: E402
    SIGNALS,
    TRIM_Z,
    EmbeddingLikelihoodModel,
    likelihood_from_z,
)

SERVERS = ("calendar", "github", "slack")
SESSION_DIR = Path("logs/proxy/sessions")
OUT_DIR = Path("reports/dynamic_eval/embedding")
CANDIDATES = (*SIGNALS, "blend")
TRAIN_FRACTION = 0.7
REFIT_EVERY = 50
# Impact-aware reference filter: calls at/above the scan's *high* band never enter the
# demonstrated-normal reference, so a crown x destructive call cannot earn a likelihood
# discount through repetition (the insider-testbed failure mode). Design-time knowledge
# only — no labels, general to any scanned server. The threshold key is the scan's own
# band vocabulary; the value comes from each scan's band_thresholds.
IMPACT_FILTER_BAND = "high"

CSV_FIELDS = (
    "position", "index", "run_id", "persona", "category", "tool", "args",
    "asset", "static_score", "static_basis", "z", "likelihood", "final_risk",
)


@dataclass(frozen=True)
class StaticLookup:
    """A call's static v6 score with an honest basis label (never fabricated silently)."""

    asset: str
    score: float
    basis: str  # "cell" | "tool-worst-case" | "server-worst-case"


def static_lookup(call: Call, table: StaticTable) -> StaticLookup:
    """Resolve a call to its scanned cell score, falling back to explicit worst cases."""
    scored = score_call(call, table)
    if scored.scorable and scored.score is not None:
        return StaticLookup(asset=scored.asset or "", score=scored.score, basis="cell")
    if table.has_tool(call.tool):
        worst = max(row[call.tool] for row in table.cells.values() if call.tool in row)
        return StaticLookup(asset="(unresolved)", score=worst, basis="tool-worst-case")
    worst = max(score for row in table.cells.values() for score in row.values())
    return StaticLookup(asset="(invalid-tool)", score=worst, basis="server-worst-case")


def as_tuples(calls: list[Call]) -> list[tuple[str, dict]]:
    return [(c.tool, c.args) for c in calls]


def category_mask(calls: list[Call], category: str) -> np.ndarray:
    return np.array([c.category == category for c in calls])


def auc_or_nan(labels: np.ndarray, scores: np.ndarray) -> float:
    if labels.min() == labels.max():
        return float("nan")
    return float(roc_auc_score(labels, scores))


def reference_filter(calls: list[Call], table: StaticTable) -> list[Call]:
    """Drop calls at/above the scan's high band from a training reference.

    See :data:`IMPACT_FILTER_BAND` — high-impact calls must stay novel forever;
    they can be observed, but never demonstrated normal.
    """
    ceiling = table.band_thresholds.get(IMPACT_FILTER_BAND)
    if ceiling is None:
        return list(calls)
    return [c for c in calls if static_lookup(c, table).score < ceiling]


def frozen_eval(
    calls: list[Call], table: StaticTable
) -> tuple[EmbeddingLikelihoodModel, list[Call], dict]:
    """Fit all candidates on the benign head; score the held-out tail; return metrics."""
    boundary = int(len(calls) * TRAIN_FRACTION)
    train = reference_filter(
        [c for c in calls[:boundary] if c.category == "BENIGN"], table
    )
    test = calls[boundary:]

    t0 = time.perf_counter()
    model = EmbeddingLikelihoodModel(signal="blend").fit(as_tuples(train))
    fit_seconds = time.perf_counter() - t0

    benign = category_mask(test, "BENIGN")
    malicious = category_mask(test, "MALICIOUS")
    misuse = category_mask(test, "MISUSE")

    per_signal: dict[str, dict] = {}
    for signal in CANDIDATES:
        t0 = time.perf_counter()
        z = model.z_scores(as_tuples(test), signal=signal)
        score_ms_per_call = (time.perf_counter() - t0) * 1000 / len(test)
        likelihood = likelihood_from_z(z)
        mask_bm = benign | malicious
        per_signal[signal] = {
            "auc_malicious": auc_or_nan(malicious[mask_bm].astype(int), z[mask_bm]),
            "auc_misuse": auc_or_nan(
                misuse[benign | misuse].astype(int), z[benign | misuse]
            ),
            "mean_likelihood": {
                "BENIGN": float(likelihood[benign].mean()),
                "MISUSE": float(likelihood[misuse].mean()),
                "MALICIOUS": float(likelihood[malicious].mean()),
            },
            "tpr_malicious": float((likelihood[malicious] > 0.1).mean()),
            "fpr_benign": float((likelihood[benign] > 0.1).mean()),
            "score_ms_per_call": score_ms_per_call,
        }

    metrics = {
        "n_train_benign": len(train),
        "n_test": len(test),
        "n_test_by_category": {
            "BENIGN": int(benign.sum()), "MISUSE": int(misuse.sum()),
            "MALICIOUS": int(malicious.sum()),
        },
        "fit_seconds": fit_seconds,
        "signals": per_signal,
    }
    return model, test, metrics


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def formula_rows(
    calls: list[Call], zs: np.ndarray, table: StaticTable, start_position: int = 1
) -> list[dict]:
    """Materialize the full-formula rows: static x likelihood = final risk, per call."""
    likelihoods = likelihood_from_z(zs)
    rows = []
    for offset, (call, z, likelihood) in enumerate(zip(calls, zs, likelihoods)):
        static = static_lookup(call, table)
        rows.append({
            "position": start_position + offset,
            "index": call.index,
            "run_id": call.run_id,
            "persona": call.persona,
            "category": call.category,
            "tool": call.tool,
            "args": call.args_raw,
            "asset": static.asset,
            "static_score": static.score,
            "static_basis": static.basis,
            "z": "inf" if np.isinf(z) else round(float(z), 3),
            "likelihood": round(float(likelihood), 3),
            "final_risk": round(static.score * float(likelihood), 2),
        })
    return rows


def stream_eval(calls: list[Call], table: StaticTable, winner: str) -> tuple[list[dict], dict]:
    """Honest prequential replay: score each call with a model fit only on earlier calls."""
    tuples = as_tuples(calls)
    # Precompute which calls may serve as reference (below the impact-filter ceiling).
    ceiling = table.band_thresholds.get(IMPACT_FILTER_BAND)
    ok = [
        ceiling is None or static_lookup(c, table).score < ceiling
        for c in calls
    ]
    zs = np.empty(len(calls))
    refits = 0
    t0 = time.perf_counter()
    model = EmbeddingLikelihoodModel(signal=winner, trim_z=TRIM_Z).fit([])
    for start in range(0, len(calls), REFIT_EVERY):
        block = slice(start, min(start + REFIT_EVERY, len(calls)))
        zs[block] = model.z_scores(tuples[block])
        reference = [t for t, keep in zip(tuples[: block.stop], ok[: block.stop]) if keep]
        model = EmbeddingLikelihoodModel(signal=winner, trim_z=TRIM_Z).fit(reference)
        refits += 1
    elapsed = time.perf_counter() - t0

    likelihood = likelihood_from_z(zs)
    malicious = category_mask(calls, "MALICIOUS")
    benign = category_mask(calls, "BENIGN")
    mask = benign | malicious
    # Steady-state view: second half of the stream, past the designed cold-start
    # (early calls carry likelihood 1.0 on purpose — full-stream TPR/FPR mix that in).
    mature = np.zeros(len(calls), dtype=bool)
    mature[len(calls) // 2:] = True
    mm = mask & mature
    metrics = {
        "auc_malicious_prequential": auc_or_nan(
            malicious[mask].astype(int), np.where(np.isinf(zs[mask]), 1e9, zs[mask])
        ),
        "mean_likelihood": {
            "BENIGN": float(likelihood[benign].mean()),
            "MALICIOUS": float(likelihood[malicious].mean()),
        },
        "tpr_malicious": float((likelihood[malicious] > 0.1).mean()),
        "fpr_benign": float((likelihood[benign] > 0.1).mean()),
        "mature_half": {
            "auc_malicious": auc_or_nan(
                malicious[mm].astype(int), np.where(np.isinf(zs[mm]), 1e9, zs[mm])
            ),
            "tpr_malicious": float((likelihood[malicious & mature] > 0.1).mean()),
            "fpr_benign": float((likelihood[benign & mature] > 0.1).mean()),
            "mean_likelihood_malicious": float(likelihood[malicious & mature].mean()),
        },
        "refits": refits,
        "replay_seconds": elapsed,
    }
    return formula_rows(calls, zs, table), metrics


def write_runs_rollup(path: Path, rows: list[dict]) -> None:
    """Aggregate stream rows to one scored line per run (session)."""
    runs: dict[str, list[dict]] = {}
    for row in rows:
        runs.setdefault(row["run_id"], []).append(row)
    out = []
    for run_id, calls in runs.items():
        likelihoods = [float(c["likelihood"]) for c in calls]
        risks = [float(c["final_risk"]) for c in calls]
        peak = max(calls, key=lambda c: float(c["final_risk"]))
        out.append({
            "run_id": run_id,
            "category": calls[0]["category"],
            "persona": calls[0]["persona"],
            "n_calls": len(calls),
            "first_position": min(int(c["position"]) for c in calls),
            "mean_likelihood": round(sum(likelihoods) / len(likelihoods), 3),
            "max_likelihood": round(max(likelihoods), 3),
            "max_final_risk": round(max(risks), 2),
            "sum_final_risk": round(sum(risks), 2),
            "riskiest_call": f"{peak['tool']}->{peak['asset']}",
        })
    out.sort(key=lambda r: -r["max_final_risk"])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--servers", nargs="+", default=list(SERVERS))
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument(
        "--variant", default="cbg",
        help="Session-dir suffix: dyn_<server>_<variant>/calls.csv (default: cbg; "
             "'ins' = the insider testbed from make_insider_testbed.py).",
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    data: dict[str, dict] = {}
    for server in args.servers:
        session = SESSION_DIR / f"dyn_{server}_{args.variant}" / "calls.csv"
        calls = [c for c in load_calls(session) if c.tool]
        calls.sort(key=lambda c: int(c.index))
        table = load_scan(SCAN_DIR / f"{server}_cbg.json")
        model, test, metrics = frozen_eval(calls, table)
        data[server] = {
            "calls": calls, "table": table, "model": model, "test": test, "metrics": metrics,
        }
        print(f"[{server}] frozen eval done: {metrics['n_train_benign']} train benign, "
              f"{metrics['n_test']} test, fit {metrics['fit_seconds']:.2f}s")

    # The deployed architecture is FIXED a priori (kNN, selected once on the original
    # corpus and validated across seeds) — re-picking a winner per corpus from held-out
    # labels would be model selection on the test set. The per-signal AUCs are still
    # computed and reported for transparency.
    winner = "knn"
    mean_auc = {
        s: float(np.nanmean([data[srv]["metrics"]["signals"][s]["auc_malicious"]
                             for srv in args.servers]))
        for s in CANDIDATES
    }
    print(f"architecture (fixed a priori): {winner} "
          f"(observed: {', '.join(f'{s}={v:.3f}' for s, v in sorted(mean_auc.items()))})")

    summary: dict[str, dict] = {"winner": winner, "mean_auc_malicious": mean_auc, "servers": {}}
    for server in args.servers:
        d = data[server]
        boundary = len(d["calls"]) - len(d["test"])
        z_test = d["model"].z_scores(as_tuples(d["test"]), signal=winner)
        write_rows(
            args.out / f"{server}_test.csv",
            formula_rows(d["test"], z_test, d["table"], start_position=boundary + 1),
        )
        stream_rows, stream_metrics = stream_eval(d["calls"], d["table"], winner)
        write_rows(args.out / f"{server}_stream.csv", stream_rows)
        write_runs_rollup(args.out / f"{server}_runs.csv", stream_rows)
        summary["servers"][server] = {"frozen": d["metrics"], "stream": stream_metrics}
        print(f"[{server}] stream replay: {stream_metrics['refits']} refits in "
              f"{stream_metrics['replay_seconds']:.1f}s, "
              f"prequential AUC {stream_metrics['auc_malicious_prequential']:.3f}")

    (args.out / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"metrics -> {args.out / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
