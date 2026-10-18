"""Measure how much `blast_radius` depends on the order peer_tools/peer_assets ride in.

`score_blast` (mcp_security.static_scoring.pipeline.StaticScorer.score_blast) embeds
`peer_tools`/`peer_assets` -- the server's OTHER tools/assets, straight off
`registry.tools`/`registry.assets` iteration order, UNSORTED -- into every single-cell
blast prompt whenever an arm sets `blast_peers: True` (v4, v5, v5r, v7 -- every
production mode, including `nacombo`, the one actually scanning github_real/slack_real).
The rubric then tells the model: "the sibling lists below are the SAME server... must
not differ by more than one tier without a reason." That is a comparative instruction
riding on an unsorted list -- structurally the same mechanism `check_rank_stability.py`
found unstable for the old listwise `rank` field (mean Kendall's tau 0.538 under
reversal), just never measured for blast.

Unlike breadth's per-tool input list, blast is scored ONE (tool, asset) CELL PER MODEL
CALL -- there is no in-reply ordering to bias a single cell's own answer. What can move
is the CONTEXT: reverse `registry.tools`/`registry.assets` and every cell's peer_tools/
peer_assets list arrives in the opposite order, changing what a real re-scan (e.g. a
catalog fetched with the API returning tools in a different order) could show for the
identical (tool, asset) pair.

asset_sensitivity and tool_impact are NOT re-tested here: sensitivity is scored one
asset at a time with no peer list in the prompt at all, and nacombo's tool_impact is a
deterministic ladder (`static_impact.classify_by_operation`, no LLM call) -- both are
order-invariant by construction, so they are computed ONCE (forward order) and held
fixed for both blast passes. That isolates the one axis actually in question.

Full matrices are too large to run twice (github_real: 26 tools x 20 assets = 520
cells; slack_real: 16 x 20 = 320): a sample of pairs is drawn instead, spread across
both tools and assets (not a block of either), so a tool-level or asset-level effect
can't hide by only landing in the untested half.

    sbatch scripts/check_blast_stability.sbatch
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# Run directly (``python scripts/check_blast_stability.py``), sys.path[0] is
# ``scripts/`` itself, not the repo root -- ``scripts`` isn't importable as a
# package without this. Must precede the ``scripts.scan_policy_v5`` import below.
sys.path.insert(0, str(REPO))

from mcp_security.static_scoring import fallback, prompts
from mcp_security.static_scoring.pipeline import _clamp, _ULT_VARIANT_OPTIONS, StaticScorer
from scripts.scan_policy_v5 import TARGETS, build_policy_registry
from mcp_security.scanner.tool_list import load_tool_list
from mcp_security.static_scoring.server_policies import POLICY_DOC, policy_for

OUT = REPO / "reports" / "experiments" / "breadth_spec" / "blast_stability.json"
MODE = "five_level_v2_v5r_nacombo"
STEMS = ("github_real", "slack_real")


class PairScorer(StaticScorer):
    """`score_blast`, restricted to a sampled list of (tool, asset) pairs.

    Reproduces only the `nacombo` branch of `score_blast` (asserted below) -- this
    measures ONE arm on purpose, the production one, not the full branch matrix.
    """

    def score_blast_pairs(
        self, sensitivity: dict[str, int], impacts: dict[str, int], pairs: list[tuple[str, str]]
    ) -> dict[str, dict]:
        assert self.impact_mode == MODE, f"only wired for {MODE!r}"
        blast_task = prompts.BLAST_TASK_V5R_SCOPE_NACOMBO
        blast_user = prompts.BLAST_USER_V5R_SCOPE_NACOMBO
        declared = {
            asset.asset_id: {t.split(":", 1)[1] for t in asset.tags if t.startswith("tool:")}
            for asset in self.registry.assets
        }
        tools_by_name = {t.name: t for t in self.registry.tools}
        assets_by_id = {a.asset_id: a for a in self.registry.assets}
        out: dict[str, dict] = {}
        for tool_name, asset_id in pairs:
            tool, asset = tools_by_name[tool_name], assets_by_id[asset_id]
            fb_sens = sensitivity.get(asset.asset_id, 3)
            fb_blast, _ = fallback.blast_radius(tool, asset, fb_sens)
            listed = sorted(declared.get(asset.asset_id, ()))
            fmt = {
                "tool_json": json.dumps(tool.to_prompt_json()),
                "asset_json": json.dumps(asset.to_prompt_json()),
                "register_tools": ", ".join(listed) if listed else "none",
                "tool_impact": str(impacts.get(tool.name, "unknown")),
                "asset_sensitivity": str(sensitivity.get(asset.asset_id, "unknown")),
                # The one thing this script varies: registry order, unsorted, exactly
                # as score_blast builds it (pipeline.py's blast_peers branch).
                "peer_tools": json.dumps([t.name for t in self.registry.tools if t.name != tool.name]),
                "peer_assets": json.dumps(
                    [a.asset_id for a in self.registry.assets if a.asset_id != asset.asset_id]
                ),
            }
            result = self._ask(self._proposer_prompt(blast_task, blast_user.format(**fmt)))
            key = f"{tool.name}|{asset.asset_id}"
            if isinstance(result, dict) and result.get("blast_radius") is not None:
                value = _clamp(result["blast_radius"], 1, 5, fb_blast)
                fell_back = False
            elif isinstance(result, dict) and result.get("affects_asset") is False:
                value, fell_back = None, False
            else:
                value, fell_back = fb_blast, True
            out[key] = {
                "blast_radius": value,
                "affects_asset": result.get("affects_asset") if isinstance(result, dict) else None,
                "escape": result.get("escape", "none") if isinstance(result, dict) else "none",
                "fell_back": fell_back,
            }
        return out


def sample_pairs(tools: list[str], assets: list[str], n: int, seed: int) -> list[tuple[str, str]]:
    """`n` (tool, asset) pairs spread across both axes, not a block of either."""
    rng = random.Random(seed)
    all_pairs = [(t, a) for t in tools for a in assets]
    return rng.sample(all_pairs, min(n, len(all_pairs)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs-per-server", type=int, default=24)
    parser.add_argument("--stems", default=",".join(STEMS))
    parser.add_argument("--seed", type=int, default=20260815)
    args = parser.parse_args(argv)

    targets = {t.stem: t for t in TARGETS}
    stems = [s.strip() for s in args.stems.split(",")]

    results: list[dict] = []
    print(f"{'server':<14}{'pairs':>7}{'blast agree':>13}{'affects agree':>15}{'escape agree':>14}",
          flush=True)
    for stem in stems:
        target = targets[stem]
        policy = policy_for(target.server, doc=POLICY_DOC)
        tools = load_tool_list(target.kind, path=target.catalog)
        # Match production nacombo exactly: asset_flags="none" -> no register flags
        # reach the model (see scan_policy_v5.scan_one's identical lookup).
        flag_policy = _ULT_VARIANT_OPTIONS[MODE].get("asset_flags", "all")
        registry_fwd, _ = build_policy_registry(
            target.server, target.kind, policy.text, tools, flag_policy=flag_policy
        )

        # domain_profile/sensitivity/impact are order-invariant on their own (domain
        # inference aside -- see below), so each is computed ONCE and held fixed
        # for both blast passes. That isolates blast's peer-list effect as the only
        # thing that differs between the forward and reversed call.
        fwd = PairScorer(registry_fwd, use_llm=True, strict=False, impact_mode=MODE)
        domain_profile = fwd.infer_domain()  # itself reads the full tool list --
        # order-sensitive in principle, which is why it is NOT re-run on the
        # reversed registry below; the reversed scorer is handed this same result.
        impacts = fwd.score_tools()
        sensitivity = fwd.score_assets()

        pairs = sample_pairs(
            [t.name for t in registry_fwd.tools],
            [a.asset_id for a in registry_fwd.assets],
            args.pairs_per_server,
            args.seed,
        )

        registry_rev = dataclasses.replace(
            registry_fwd,
            tools=list(reversed(registry_fwd.tools)),
            assets=list(reversed(registry_fwd.assets)),
        )
        rev = PairScorer(registry_rev, use_llm=True, strict=False, impact_mode=MODE)
        rev.domain_profile = domain_profile
        rev._domain_confidence = fwd._domain_confidence

        forward = fwd.score_blast_pairs(sensitivity, impacts, pairs)
        backward = rev.score_blast_pairs(sensitivity, impacts, pairs)

        cells = []
        for tool_name, asset_id in pairs:
            key = f"{tool_name}|{asset_id}"
            f, b = forward[key], backward[key]
            if f["fell_back"] or b["fell_back"]:
                continue
            cells.append({
                "tool": tool_name, "asset": asset_id,
                "forward": f, "backward": b,
                "blast_match": f["blast_radius"] == b["blast_radius"],
                "blast_delta": (
                    None if f["blast_radius"] is None or b["blast_radius"] is None
                    else abs(f["blast_radius"] - b["blast_radius"])
                ),
                "affects_match": f["affects_asset"] == b["affects_asset"],
                "escape_match": f["escape"] == b["escape"],
            })

        blast_rate = statistics.fmean(c["blast_match"] for c in cells) if cells else None
        affects_rate = statistics.fmean(c["affects_match"] for c in cells) if cells else None
        escape_rate = statistics.fmean(c["escape_match"] for c in cells) if cells else None
        deltas = [c["blast_delta"] for c in cells if c["blast_delta"]]
        print(f"{stem:<14}{len(cells):>7}"
              f"{'n/a' if blast_rate is None else f'{blast_rate:.2f}':>13}"
              f"{'n/a' if affects_rate is None else f'{affects_rate:.2f}':>15}"
              f"{'n/a' if escape_rate is None else f'{escape_rate:.2f}':>14}", flush=True)
        results.append({
            "server": stem, "cells_scored": len(cells),
            "blast_agree": round(blast_rate, 3) if blast_rate is not None else None,
            "affects_agree": round(affects_rate, 3) if affects_rate is not None else None,
            "escape_agree": round(escape_rate, 3) if escape_rate is not None else None,
            "identical": sum(1 for c in cells if c["blast_match"]),
            "mean_blast_delta_when_disagreeing": (
                round(statistics.fmean(deltas), 3) if deltas else None
            ),
            "cells": cells,
        })

    all_cells = [c for r in results for c in r["cells"]]
    overall_blast = statistics.fmean(c["blast_match"] for c in all_cells) if all_cells else None
    summary = {
        "mode": MODE,
        "servers": results,
        "overall_cells": len(all_cells),
        "overall_blast_agree": round(overall_blast, 3) if overall_blast is not None else None,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=1))
    print(f"\n{len(all_cells)} cells  overall blast agree {summary['overall_blast_agree']}",
          flush=True)
    print(f"written to {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
