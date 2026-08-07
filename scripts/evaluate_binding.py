#!/usr/bin/env python3
"""Measure runtime asset binding against the labelled live call corpus.

Every call in the corpus carries the asset a human said it touched. Nothing in
the resolver reads that column, and nothing about any server is configured: the
register supplies the candidates, and the container key, the enumerating tool
and the organization's own domains are all discovered from the traffic. So the
numbers below measure a method that transfers, not three tuned configurations.

Reported per server and per ablation level:

``recall``      the labelled asset is somewhere in the predicted set
``top1``        the resolver's single best answer IS the labelled asset
``mean set``    how many assets it predicts — the cost of that recall
``exact``       predicted exactly one asset and it was right
``empty``       predicted nothing at all
``fanout``      the call named no container, so it reaches every one

Usage::

    uv run python scripts/evaluate_binding.py
    uv run python scripts/evaluate_binding.py --corpus <dir> --json out.json
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mcp_security.binding import AssetResolver, Level, discover, worst_severity  # noqa: E402
from mcp_security.binding.discovery import Discovery  # noqa: E402
from mcp_security.binding.catalog import catalog_for  # noqa: E402
from mcp_security.binding.discovery import _args_of, _scalar_values  # noqa: E402
from mcp_security.binding.identifiers import (  # noqa: E402
    canonical_id,
    normalize_key,
    token_similarity,
)
from mcp_security.static_scoring.server_policies import (  # noqa: E402
    parse_asset_register,
    policy_for,
)

#: The nacombo arm is the reference deployment: its register wrote the asset ids
#: the corpus labels use, and its scan recorded the operation ladder.
DEFAULT_CORPUS = REPO_ROOT / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5r_nacombo"

#: Corpus servers. The kind is recorded for reporting only — no code branches on
#: it, and nothing about a server is configured anywhere in the resolver.
SERVER_KINDS = {
    "calendar_aurora": "calendar",
    "github_helios": "github",
    "slack_vireo": "slack",
}

#: Where the v8 experiment writes its artifacts.
V8_DIR = REPO_ROOT / "reports" / "experiments" / "v8"

LEVEL_NAMES = {
    Level.TOOL_ONLY: "L0 tool-only",
    Level.CATALOG: "L1 +catalog",
    Level.OPERATION: "L2 +operation",
    Level.EGRESS: "L3 +egress",
}


@dataclass
class LevelScore:
    """Aggregated outcome of one ablation level on one server."""

    calls: int = 0
    recall: int = 0
    alias_recall: int = 0
    #: Severity a gate would assign (worst over the resolved set) minus the
    #: severity of the asset actually touched. Never negative when recall is 1.
    over_severity: list[int] = None  # type: ignore[assignment]
    assigned_severity: list[int] = None  # type: ignore[assignment]
    top1: int = 0
    exact: int = 0
    empty: int = 0
    fanout: int = 0
    set_sizes: list[int] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.set_sizes is None:
            self.set_sizes = []
        if self.over_severity is None:
            self.over_severity = []
        if self.assigned_severity is None:
            self.assigned_severity = []

    def as_row(self) -> dict[str, float]:
        n = max(self.calls, 1)
        return {
            "calls": self.calls,
            "recall": self.recall / n,
            "alias_recall": self.alias_recall / n,
            "top1": self.top1 / n,
            "exact": self.exact / n,
            "empty": self.empty / n,
            "fanout": self.fanout / n,
            "mean_set": statistics.mean(self.set_sizes) if self.set_sizes else 0.0,
            "mean_assigned_severity": (
                statistics.mean(self.assigned_severity) if self.assigned_severity else 0.0
            ),
            "mean_over_severity": (
                statistics.mean(self.over_severity) if self.over_severity else 0.0
            ),
            "exact_severity": (
                sum(1 for d in self.over_severity if d == 0) / max(len(self.over_severity), 1)
            ),
            "under_severity": (
                sum(1 for d in self.over_severity if d < 0) / max(len(self.over_severity), 1)
            ),
        }


def load_calls(corpus: Path, server: str) -> list[dict]:
    """Every captured call for one server, newest run wins on duplicate index."""
    path = corpus / f"live_scale_{server}.csv"
    if not path.exists():
        raise FileNotFoundError(f"no corpus for {server}: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_operations(corpus: Path, server: str) -> dict[str, list[str]]:
    """The scanner's per-tool atomic operations, used by the OPERATION level.

    The full list, not ``primary_op``: a creating verb is recorded as
    ``primary_op="WRITE"`` with ``atomic_ops=["CREATE", "WRITE"]``, so reading
    the primary operation alone hides every container-creating verb.
    """
    path = corpus / f"{server}.json"
    if not path.exists():
        return {}
    artifact = json.loads(path.read_text(encoding="utf-8"))
    return {
        tool: list(entry.get("atomic_ops") or [entry.get("primary_op", "")])
        for tool, entry in (artifact.get("tool_atomic_ops") or {}).items()
    }


def parse_args_cell(raw: str) -> dict:
    try:
        parsed = json.loads(raw or "{}")
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def evaluate_server(corpus: Path, server: str, kind: str, *, stateless: bool = False) -> dict:
    """Run every ablation level over one server's calls."""
    calls = load_calls(corpus, server)
    rows = parse_asset_register(policy_for(server).text)
    operations = load_operations(corpus, server)
    artifact_path = corpus / f"{server}.json"
    sensitivity = (
        json.loads(artifact_path.read_text(encoding="utf-8")).get("asset_sensitivity") or {}
        if artifact_path.exists()
        else {}
    )

    # Stateless mode retains nothing: no observed traffic, no learned
    # identifier-to-asset table, no memory between calls. A decision is a pure
    # function of the call, the register and the tool schemas.
    found = Discovery((), (), (), {}) if stateless else discover(calls, rows)
    resolver = AssetResolver(rows, None if stateless else found, operations, catalog_for(server))

    # Two ceilings no resolver can exceed, reported so the numbers below are read
    # against what is actually reachable rather than against 1.0.
    register_ids = {row.asset_id for row in rows}
    labelled = [call["asset"] for call in calls]
    in_register = sum(label in register_ids for label in labelled) / max(len(labelled), 1)
    reachable = sum(
        call["asset"] in set(resolver.candidates(call["tool"])) for call in calls
    ) / max(len(calls), 1)

    # Binding accuracy: for each container the traffic actually addressed, does
    # the discovered link agree with the asset the corpus labelled those calls?
    # This measures the catalog on its own, before any resolution logic.
    observed: dict[str, Counter[str]] = defaultdict(Counter)
    for call in calls:
        for key, value in _args_of(call).items():
            if normalize_key(key) not in found.container_keys:
                continue
            for raw in _scalar_values(value):
                observed[canonical_id(raw)][call["asset"]] += 1
    binding_hits, binding_total, binding_detail = 0, 0, []
    for container_id, counts in sorted(observed.items()):
        binding = found.bindings.get(container_id)
        modal = counts.most_common(1)[0][0]
        binding_total += 1
        predicted = binding.asset_id if binding else None
        agrees = bool(predicted) and (
            predicted == modal or token_similarity(predicted, modal) >= 0.8
        )
        binding_hits += agrees
        binding_detail.append({
            "container": container_id, "bound_to": predicted, "modal_label": modal,
            "route": binding.route if binding else None, "agrees": agrees,
        })

    # Some corpus labels name a container by its bare name while the register ids
    # it with the organization prefix ("eng-platform" vs "vireo-eng-platform").
    # Alias-tolerant recall reports what the method found under that spelling gap.
    aliases: dict[str, str] = {}
    for label in set(labelled):
        if label in register_ids:
            continue
        near = [(token_similarity(label, rid), rid) for rid in register_ids]
        score, rid = max(near) if near else (0.0, "")
        if score >= 0.8:
            aliases[label] = rid

    scores: dict[str, LevelScore] = {name: LevelScore() for name in LEVEL_NAMES.values()}
    by_category: dict[str, LevelScore] = defaultdict(LevelScore)
    misses: Counter[tuple[str, str]] = Counter()

    for call in calls:
        label = call["asset"]
        args = parse_args_cell(call["args"])
        for level, name in LEVEL_NAMES.items():
            resolution = resolver.resolve(call["tool"], args, level)
            predicted = resolution.asset_ids
            score = scores[name]
            score.calls += 1
            score.set_sizes.append(len(predicted))
            hit = label in predicted
            score.recall += hit
            score.alias_recall += hit or aliases.get(label, "") in predicted
            score.top1 += resolution.primary == label
            score.exact += hit and len(predicted) == 1
            score.empty += not predicted
            score.fanout += resolution.fanout
            # What a gate would actually act on: the worst severity it cannot
            # rule out, against the severity of the asset really touched.
            assigned, _ = worst_severity(resolution, sensitivity)
            truth = sensitivity.get(label) or sensitivity.get(aliases.get(label, ""), 0)
            if truth:
                score.assigned_severity.append(assigned)
                score.over_severity.append(assigned - truth)
            if level == Level.EGRESS:
                bucket = by_category[call["category"]]
                bucket.calls += 1
                bucket.recall += hit
                bucket.alias_recall += hit or aliases.get(label, "") in predicted
                bucket.top1 += resolution.primary == label
                bucket.set_sizes.append(len(predicted))
                if not hit:
                    misses[(call["tool"], label)] += 1

    return {
        "server": server,
        "kind": kind,
        "calls": len(calls),
        "register_rows": len(rows),
        "binding": {
            "containers_addressed": binding_total,
            "bound_correctly": binding_hits,
            "accuracy": binding_hits / max(binding_total, 1),
            "detail": binding_detail,
        },
        "ceilings": {
            "label_in_register": in_register,
            "label_reachable_by_tool": reachable,
            "aliases": aliases,
        },
        "discovery": {
            "container_keys": list(found.container_keys),
            "listing_tools": list(found.listing_tools),
            "org_domains": list(found.org_domains),
            "rejected_keys": [{"key": k, "why": why} for k, why in found.rejected],
            "bindings": {
                cid: {"asset": b.asset_id, "route": b.route, "basis": b.basis,
                      "score": round(b.score, 3)}
                for cid, b in sorted(found.bindings.items())
            },
        },
        "levels": {name: score.as_row() for name, score in scores.items()},
        "by_category": {name: score.as_row() for name, score in sorted(by_category.items())},
        "top_misses": [
            {"tool": tool, "label": label, "count": n} for (tool, label), n in misses.most_common(8)
        ],
    }


def print_report(results: list[dict]) -> None:
    for result in results:
        print(f"\n{'=' * 78}\n{result['server']}  ({result['kind']}, "
              f"{result['calls']} calls, {result['register_rows']} register rows)\n{'=' * 78}")
        found = result["discovery"]
        print(f"discovered container keys : {found['container_keys']}")
        print(f"discovered listing tools  : {found['listing_tools']}")
        print(f"discovered org domains    : {found['org_domains']}")
        if found["rejected_keys"]:
            rejected = ", ".join(f"{r['key']} ({r['why']})" for r in found["rejected_keys"][:6])
            print(f"rejected candidate keys   : {rejected}")
        print(f"bindings: {len(found['bindings'])}")
        for cid, entry in found["bindings"].items():
            print(f"    {cid[:34]:36s} -> {entry['asset']:28s} [{entry['route']}] "
                  f"{entry['score']:.2f}  {entry['basis'][:44]}")
        b = result["binding"]
        print(f"binding accuracy: {b['bound_correctly']}/{b['containers_addressed']} "
              f"containers ({b['accuracy']:.3f})")
        for row in b["detail"]:
            mark = "ok  " if row["agrees"] else "MISS"
            print(f"  {mark} {str(row['container'])[:30]:32s} -> "
                  f"{str(row['bound_to']):28s} label={row['modal_label']} [{row['route']}]")
        ceil = result["ceilings"]
        print(f"\nceilings: label is a register id {ceil['label_in_register']:.3f}; "
              f"label reachable by its tool {ceil['label_reachable_by_tool']:.3f}")
        if ceil["aliases"]:
            print(f"label aliases: {ceil['aliases']}")
        header = (
            f"{'level':16s} {'recall':>8s} {'alias':>8s} {'top1':>8s} {'mean set':>9s} "
            f"{'severity':>9s} {'over':>7s} {'exact sv':>9s} {'under':>7s}"
        )
        print(f"\n{header}\n{'-' * len(header)}")
        for name, row in result["levels"].items():
            print(f"{name:16s} {row['recall']:8.3f} {row['alias_recall']:8.3f} "
                  f"{row['top1']:8.3f} {row['mean_set']:9.2f} "
                  f"{row['mean_assigned_severity']:9.2f} {row['mean_over_severity']:7.2f} "
                  f"{row['exact_severity']:9.3f} {row['under_severity']:7.3f}")
        print("\nby call category (at L3):")
        for name, row in result["by_category"].items():
            print(f"  {name:10s} n={row['calls']:5d}  recall={row['recall']:.3f}  "
                  f"top1={row['top1']:.3f}  mean set={row['mean_set']:.2f}")
        if result["top_misses"]:
            print("\nunrecalled (tool, label):")
            for miss in result["top_misses"]:
                print(f"  {miss['tool']:30s} {miss['label']:28s} {miss['count']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--only", action="append", help="restrict to one server (repeatable)")
    parser.add_argument("--stateless", action="store_true",
                        help="retain nothing: no key table, no observed traffic")
    parser.add_argument("--json", type=Path, default=V8_DIR / "binding_results.json",
                        help="write the full result here (default: the v8 experiment folder)")
    options = parser.parse_args()

    wanted = options.only or list(SERVER_KINDS)
    results = [
        evaluate_server(options.corpus, server, SERVER_KINDS[server],
                        stateless=options.stateless)
        for server in wanted
        if server in SERVER_KINDS
    ]
    print_report(results)
    if options.json:
        options.json.parent.mkdir(parents=True, exist_ok=True)
        options.json.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nwrote {options.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
