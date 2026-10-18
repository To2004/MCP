"""Fused dynamic likelihood: embedding ⊕ sequence ⊕ baseline, escalate-only.

The embedding likelihood is near its content ceiling; its characterized misses are
(a) attack preambles — normal *content*, abnormal *order* — and (b) misuse — normal
content, abnormal *volume/actor*. Those are exactly the sequence and baseline signals'
jobs. This evaluation maps all three onto the same ``[0.1, 1.0]`` scale and fuses

    L_final = max(L_embed, L_sequence, L_baseline)      (escalation only)
    final_risk = static_score x L_final

Escalation-only is deliberate: a signal can flag what the embedding vouched for, but
nothing can *lower* the embedding's suspicion — the failure mode proved in the
per-user-conditioning experiment (repeated misuse vouching for itself) cannot leak in.

Leakage discipline matches the embedding protocol:

* frozen — baselines built from the (unlabeled) first 70% of the stream; sequence is
  stateless; embedding trained on the filtered benign head as before.
* stream — baselines rebuilt every ``REFIT_EVERY`` calls from calls seen so far;
  sequence verdicts are causal (each call's verdict looks only backward in its run);
  session size for burst detection is the size *so far*, never the final size.

Usage::

    uv run python scripts/eval_fused_likelihood.py                 # original corpus
    uv run python scripts/eval_fused_likelihood.py --variant ins   # insider corpus
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_embedding_likelihood import (  # noqa: E402
    REFIT_EVERY,
    SESSION_DIR,
    as_tuples,
    auc_or_nan,
    frozen_eval,
    static_lookup,
)
from mcp_security.call_scoring.loader import load_calls  # noqa: E402
from mcp_security.call_scoring.score import ScoredCall, score_call  # noqa: E402
from mcp_security.call_scoring.tables import SCAN_DIR, load_scan  # noqa: E402
from mcp_security.dynamic.baseline import build_baselines, score_deviation  # noqa: E402
from mcp_security.dynamic.embedding import (  # noqa: E402
    TRIM_Z,
    EmbeddingLikelihoodModel,
    likelihood_from_z,
)
from mcp_security.dynamic.sequence import score_sequence  # noqa: E402

SERVERS = ("calendar", "github", "slack")
OUT_DIR = Path("reports/dynamic_eval/fused")
# Band -> likelihood scale shared by all escalating signals. "low" is the honest
# no-signal answer and maps to the same floor the embedding uses.
BAND_LIKELIHOOD = {"low": 0.1, "medium": 0.4, "high": 0.7, "critical": 1.0}


def sequence_likelihoods(scored: list[ScoredCall]) -> np.ndarray:
    """Per-call sequence likelihood; verdicts are causal within each run."""
    by_run: dict[str, list[int]] = defaultdict(list)
    for i, call in enumerate(scored):
        by_run[call.run_id].append(i)
    out = np.full(len(scored), BAND_LIKELIHOOD["low"])
    for indices in by_run.values():
        verdicts = score_sequence([scored[i] for i in indices])
        for i, verdict in zip(indices, verdicts):
            out[i] = BAND_LIKELIHOOD.get(verdict.band, 0.1)
    return out


def baseline_likelihoods(
    scored: list[ScoredCall], history: list[ScoredCall]
) -> np.ndarray:
    """Per-call baseline likelihood against baselines built from ``history``.

    Session size passed to burst detection is the count of the run's calls *within
    the scored slice up to that call* — causal by construction.
    """
    baselines = build_baselines(history)
    seen_in_run: dict[str, int] = defaultdict(int)
    out = np.empty(len(scored))
    for i, call in enumerate(scored):
        seen_in_run[call.run_id] += 1
        band, _ = score_deviation(
            call,
            baselines.get(f"{call.persona}@{call.server}"),
            session_size=seen_in_run[call.run_id],
        )
        out[i] = BAND_LIKELIHOOD.get(band, 0.1)
    return out


def metric_block(L: np.ndarray, cat: np.ndarray, statics: np.ndarray, z_rank: np.ndarray) -> dict:
    ben, mis, mal = cat == "BENIGN", cat == "MISUSE", cat == "MALICIOUS"
    risk = statics * L
    mask = ben | mal
    return {
        "auc_malicious": auc_or_nan(mal[mask].astype(int), z_rank[mask]),
        "auc_misuse": auc_or_nan(mis[ben | mis].astype(int), z_rank[ben | mis]),
        "tpr_malicious": float((L[mal] > 0.1).mean()) if mal.any() else float("nan"),
        "tpr_misuse": float((L[mis] > 0.1).mean()) if mis.any() else float("nan"),
        "fpr_benign": float((L[ben] > 0.1).mean()),
        "mean_likelihood": {
            "BENIGN": float(L[ben].mean()),
            "MISUSE": float(L[mis].mean()) if mis.any() else float("nan"),
            "MALICIOUS": float(L[mal].mean()) if mal.any() else float("nan"),
        },
        "risk_separation": float(risk[mal].mean() / max(risk[ben].mean(), 1e-9))
        if mal.any() else float("nan"),
    }


def evaluate_server(server: str, variant: str) -> dict:
    calls = [c for c in load_calls(SESSION_DIR / f"dyn_{server}_{variant}" / "calls.csv") if c.tool]
    calls.sort(key=lambda c: int(c.index))
    table = load_scan(SCAN_DIR / f"{server}_cbg.json")
    scored = [score_call(c, table) for c in calls]
    statics = np.array([static_lookup(c, table).score for c in calls])
    cat = np.array([c.category for c in calls])
    boundary = int(len(calls) * 0.7)

    # ---- frozen ----
    model, test, _ = frozen_eval(calls, table)
    z_embed = model.z_scores(as_tuples(test), signal="knn")
    L_embed = np.asarray(likelihood_from_z(z_embed))
    L_seq_all = sequence_likelihoods(scored)  # causal; slicing the tail is safe
    L_seq = L_seq_all[boundary:]
    L_base = baseline_likelihoods(scored[boundary:], scored[:boundary])
    L_fused = np.max(np.vstack([L_embed, L_seq, L_base]), axis=0)
    frozen = {
        "embed_only": metric_block(L_embed, cat[boundary:], statics[boundary:],
                                   np.where(np.isinf(z_embed), 1e9, z_embed)),
        "fused": metric_block(L_fused, cat[boundary:], statics[boundary:], L_fused),
    }

    # ---- prequential stream ----
    tuples = as_tuples(calls)
    ceiling = table.band_thresholds.get("high")
    ok = [ceiling is None or s < ceiling for s in statics]
    z_stream = np.full(len(calls), np.inf)
    L_base_stream = np.full(len(calls), 1.0)  # cold start: nothing demonstrated normal
    emb = EmbeddingLikelihoodModel(signal="knn", trim_z=TRIM_Z).fit([])
    baselines_history: list[ScoredCall] = []
    seen_in_run: dict[str, int] = defaultdict(int)
    for start in range(0, len(calls), REFIT_EVERY):
        stop = min(start + REFIT_EVERY, len(calls))
        z_stream[start:stop] = emb.z_scores(tuples[start:stop])
        if baselines_history:
            baselines = build_baselines(baselines_history)
            for i in range(start, stop):
                seen_in_run[scored[i].run_id] += 1
                band, _ = score_deviation(
                    scored[i],
                    baselines.get(f"{scored[i].persona}@{scored[i].server}"),
                    session_size=seen_in_run[scored[i].run_id],
                )
                L_base_stream[i] = BAND_LIKELIHOOD.get(band, 0.1)
        else:
            for i in range(start, stop):
                seen_in_run[scored[i].run_id] += 1
        reference = [t for t, keep in zip(tuples[:stop], ok[:stop]) if keep]
        emb = EmbeddingLikelihoodModel(signal="knn", trim_z=TRIM_Z).fit(reference)
        baselines_history = scored[:stop]
    L_embed_stream = np.asarray(likelihood_from_z(z_stream))
    L_fused_stream = np.max(np.vstack([L_embed_stream, L_seq_all, L_base_stream]), axis=0)

    half = len(calls) // 2
    stream = {}
    for name, L, rank in (
        ("embed_only", L_embed_stream, np.where(np.isinf(z_stream), 1e9, z_stream)),
        ("fused", L_fused_stream, L_fused_stream),
    ):
        stream[name] = {
            "full": metric_block(L, cat, statics, rank),
            "mature_half": metric_block(L[half:], cat[half:], statics[half:], rank[half:]),
        }

    # runs rollup precision (fused, full stream)
    risk = statics * L_fused_stream
    per_run: dict[str, dict] = {}
    for i, c in enumerate(calls):
        r = per_run.setdefault(c.run_id, {"category": c.category, "max_risk": 0.0})
        r["max_risk"] = max(r["max_risk"], float(risk[i]))
    ranked = sorted(per_run.values(), key=lambda r: -r["max_risk"])
    top20 = sum(1 for r in ranked[:20] if r["category"] != "BENIGN")
    base_rate = sum(1 for r in ranked if r["category"] != "BENIGN") / len(ranked)

    return {
        "frozen": frozen,
        "stream": stream,
        "runs": {"top20_attacks": top20, "n_runs": len(ranked), "attack_base_rate": base_rate},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--variant", default="cbg")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    summary = {}
    for server in SERVERS:
        summary[server] = evaluate_server(server, args.variant)
        s = summary[server]
        for mode in ("embed_only", "fused"):
            m = s["stream"][mode]["mature_half"]
            print(f"[{server}] {mode:<10} mature stream: auc={m['auc_malicious']:.3f} "
                  f"TPRmal={m['tpr_malicious']:.0%} TPRmis={m['tpr_misuse']:.0%} "
                  f"FPR={m['fpr_benign']:.1%} sep=x{m['risk_separation']:.0f}")
        print(f"[{server}] fused top-20 runs: {s['runs']['top20_attacks']}/20 attacks "
              f"(base {s['runs']['attack_base_rate']:.0%})")
    out_path = args.out / f"metrics_{args.variant}.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"metrics -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
