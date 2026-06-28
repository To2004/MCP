"""Load external, third-party MCP attack benchmarks into a uniform call list.

Replaces the team's own hand-authored heatmaps with independent ground truth.
Reads the vendored benchmark task files under the attack testbed:

    mcp-attack-testbed/benchmarks/{mcpsecbench,mcp_safetybench,msb}/tasks/*.json

Each task file is ``{"server": ..., "calls": [{category, tool, args, attack_class?}]}``
with the SAME threat model as this framework (the MCP server is the protected asset;
calls flow client -> server). ``category`` values:

* ``ATTACK``     -> a hostile call (with an ``attack_class`` in the ATT-1..17 taxonomy)
* ``VALID``      -> a benign, well-formed call
* ``BAD_TOOL``   -> a call to a non-existent / forbidden tool (a misconfiguration the
                    gate should still flag; our scorer reports these ``invalid``)
* ``BAD_PARAMS`` -> a malformed-argument call (also flag-worthy)
* ``EDGE``       -> a gray-zone malformed/odd call

We expose two detection labels so the benchmark can be scored two ways:

* ``label_attack``  — positive = ATTACK only; negatives = VALID. (cleanest separation
  question: does the scorer rank genuine attacks above benign traffic?)
* ``label_flag``    — positive = ATTACK | BAD_TOOL | BAD_PARAMS; negative = VALID.
  (operational gate question: does it flag everything a gate should stop?)
EDGE is excluded from both (ambiguous).

MSB's args are a single natural-language ``task`` string rather than structured MCP
arguments, so MSB calls are marked ``structured_args=False`` and are meant for the
LLM-judge / binary comparison, not the (tool, asset) structured scorer.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_BENCH_DIR = Path(
    os.environ.get("MCP_BENCH_DIR", Path.home() / "mcp-attack-testbed" / "benchmarks")
)
BENCHES = ("mcpsecbench", "mcp_safetybench", "msb")

# category -> coarse class
_BENIGN = "VALID"
_ATTACK = "ATTACK"
_MISCONFIG = {"BAD_TOOL", "BAD_PARAMS"}
_EDGE = "EDGE"


@dataclass(frozen=True)
class BenchCall:
    """One labeled tool call from an external benchmark."""

    bench: str
    server: str
    tool: str
    args: dict
    category: str
    attack_class: str | None
    structured_args: bool
    idx: int

    @property
    def label_attack(self) -> int | None:
        """1 for ATTACK, 0 for VALID, None to exclude (misconfig/edge)."""
        if self.category == _ATTACK:
            return 1
        if self.category == _BENIGN:
            return 0
        return None

    @property
    def label_flag(self) -> int | None:
        """1 for anything a gate should stop, 0 for VALID, None for EDGE."""
        if self.category == _ATTACK or self.category in _MISCONFIG:
            return 1
        if self.category == _BENIGN:
            return 0
        return None

    @property
    def args_text(self) -> str:
        """Flat string of the arguments, for content heuristics / the LLM judge."""
        return json.dumps(self.args, ensure_ascii=False)


def _is_structured(bench: str, args: dict) -> bool:
    """MSB encodes the whole call as a natural-language ``task`` string."""
    if bench == "msb":
        return False
    return not (set(args.keys()) == {"task"})


def load_benchcalls(
    benches: tuple[str, ...] = BENCHES, bench_dir: Path = DEFAULT_BENCH_DIR
) -> list[BenchCall]:
    """Every labeled call across the requested benchmarks, in file order."""
    calls: list[BenchCall] = []
    idx = 0
    for bench in benches:
        tasks = sorted((bench_dir / bench / "tasks").glob("*.json"))
        for path in tasks:
            data = json.loads(path.read_text(encoding="utf-8"))
            server = data.get("server", path.stem)
            for c in data.get("calls", []):
                args = c.get("args", {}) or {}
                calls.append(
                    BenchCall(
                        bench=bench,
                        server=server,
                        tool=c.get("tool", ""),
                        args=args,
                        category=c["category"],
                        attack_class=c.get("attack_class"),
                        structured_args=_is_structured(bench, args),
                        idx=idx,
                    )
                )
                idx += 1
    return calls


@dataclass
class BenchSummary:
    by_bench_category: Counter = field(default_factory=Counter)
    attack_classes: Counter = field(default_factory=Counter)
    structured: Counter = field(default_factory=Counter)


def summarize(calls: list[BenchCall]) -> BenchSummary:
    s = BenchSummary()
    for c in calls:
        s.by_bench_category[(c.bench, c.category)] += 1
        if c.category == _ATTACK:
            s.attack_classes[c.attack_class or "?"] += 1
        s.structured[(c.bench, c.structured_args)] += 1
    return s


def main() -> None:
    calls = load_benchcalls()
    s = summarize(calls)
    print(f"Loaded {len(calls)} labeled calls from {DEFAULT_BENCH_DIR}\n")
    print("Per-bench x category:")
    for (b, cat), n in sorted(s.by_bench_category.items()):
        print(f"  {b:18} {cat:11} {n}")
    n_attack = sum(1 for c in calls if c.label_attack == 1)
    n_benign = sum(1 for c in calls if c.label_attack == 0)
    n_struct = sum(1 for c in calls if c.structured_args)
    print(f"\nlabel_attack: {n_attack} attack vs {n_benign} VALID "
          f"(misconfig/edge excluded)")
    print(f"structured-arg calls (usable by the (tool,asset) scorer): {n_struct}/{len(calls)}")
    print(f"distinct attack classes: {len(s.attack_classes)} -> "
          f"{dict(sorted(s.attack_classes.items()))}")


if __name__ == "__main__":
    main()
