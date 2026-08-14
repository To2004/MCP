"""Three label-free evaluations of the runtime layer.

Each answers a question that does not need a misuse corpus, which is why they come first:
building a misuse set is the step where a security evaluation most easily goes wrong, and
if these three come back badly there is nothing worth building one for.

``ablation``    Does each factor earn its place? Ranking agreement between the full score
                and each reduced variant, plus two trivial baselines. If dropping a factor
                does not move the ranking, that factor is decorative.

``sensitivity`` What can the layer see at all? For each way a call can deviate, sweep the
                magnitude and find where the score change first clears the noise floor.
                The anomaly-injection method used where labels do not exist.

``poisoning``   What does evasion cost? Both factors learn from traffic the adversary
                controls, so an agent can widen its own baseline until the call it wanted
                is ordinary. The cost is bounded and therefore computable.

References: Arp et al., Dos and Don'ts of ML in Computer Security (USENIX Sec 2022) for
the baseline requirement; Sommer and Paxson (IEEE S&P 2010) for the anomalous-vs-malicious
gap these are trying to measure rather than assume.
"""

from __future__ import annotations

import argparse
import copy
import csv
import itertools
import json
import random
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dynamic_v2 import (  # noqa: E402
    MAX_HISTORY,
    MIN_HISTORY,
    BreadthScorer,
    load_specs,
)
from org_traffic import write_tools  # noqa: E402

REPO = Path("/home/ovadyat/MCP")
#: Warm on this fraction of the corpus before anything is scored.
WARM_FRACTION = 0.5
#: Calls sampled for the ranking comparisons. Kendall tau is quadratic in this.
RANK_SAMPLE = 1200
#: Breadth level used by the "no rubric" control, the midpoint of the 1-5 scale.
FLAT_BREADTH = 3
#: How far past a deployment's 90th percentile the control pushes each argument.
WIDEN_FACTOR = 100


def _args(row: dict) -> dict:
    try:
        parsed = json.loads(row["args"] or "{}")
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _load(path: Path) -> list[dict]:
    with path.open() as handle:
        return list(csv.DictReader(handle))


def _kendall(left: list[float], right: list[float]) -> tuple[float, float]:
    """Kendall tau-b between two scorings of the same calls, with the tied-pair fraction.

    tau-b, not the concordant/discordant ratio: B sits at exactly 1.0 on ~93% of calls and
    a write/read flag is binary, so most pairs are tied. Dividing by concordant+discordant
    alone silently restricts the statistic to the few untied pairs and reports agreement
    of 0.97 for a variable that is constant almost everywhere. The tie fraction is
    returned alongside so a high tau on a nearly constant variable is visible rather than
    flattering.
    """
    concordant = discordant = tied_left = tied_right = 0
    for (a1, b1), (a2, b2) in itertools.combinations(zip(left, right), 2):
        da, db = a1 - a2, b1 - b2
        if da == 0 and db == 0:
            continue
        if da == 0:
            tied_left += 1
        elif db == 0:
            tied_right += 1
        elif da * db > 0:
            concordant += 1
        else:
            discordant += 1
    pairs = concordant + discordant + tied_left + tied_right
    denominator = ((concordant + discordant + tied_left)
                   * (concordant + discordant + tied_right)) ** 0.5
    tau = (concordant - discordant) / denominator if denominator else float("nan")
    return tau, (tied_left + tied_right) / pairs if pairs else 0.0


def _warm(rows: list[dict], server: str) -> tuple[BreadthScorer, list[dict]]:
    scorer = BreadthScorer(load_specs())
    split = int(len(rows) * WARM_FRACTION)
    for row in rows[:split]:
        scorer.observe(server, row["tool"], _args(row))
    return scorer, rows[split:]


# --------------------------------------------------------------------------- ablation


def ablation(rows: list[dict], server: str) -> None:
    """Whether each factor changes the ranking, and whether a trivial rule matches it."""
    scorer, rest = _warm(rows, server)
    sample = rest[:RANK_SAMPLE]
    writes = write_tools(server)

    full, only_b, only_l, freq, is_write = [], [], [], [], []
    for row in sample:
        args = _args(row)
        b, _ = scorer.breadth_factor(server, row["tool"], args)
        lk, _ = scorer.likelihood_factor(server, row["tool"])
        scorer.observe(server, row["tool"], args)
        full.append(b * lk)
        only_b.append(b)
        only_l.append(lk)
        # Trivial baseline 1: rank by how rare the tool is, nothing else.
        freq.append(-scorer.tool_calls[server][row["tool"]])
        # Trivial baseline 2: a one-line rule any engineer would write first.
        is_write.append(1.0 if row["tool"] in writes else 0.0)

    print(f"\nablation on {len(sample)} scored calls "
          f"({len({r['tool'] for r in sample})} tools)\n")
    print(f"  {'':38} {'tau-b':>7} {'tied pairs':>11}")
    print("  ranking agreement with the full score D = B x L")
    for label, column in (("D vs L alone (is B decorative?)", only_l),
                          ("D vs B alone (is L decorative?)", only_b)):
        tau, ties = _kendall(full, column)
        print(f"    {label:36} {tau:+7.3f} {ties:>10.0%}")
    print("\n  ranking agreement with trivial baselines")
    for label, column in (("D vs 'rank by tool rarity'", freq),
                          ("D vs 'flag every write'", is_write)):
        tau, ties = _kendall(full, column)
        print(f"    {label:36} {tau:+7.3f} {ties:>10.0%}")
    moved_b = sum(abs(v - 1.0) > 1e-9 for v in only_b)
    print(f"\n  B moved on {moved_b}/{len(sample)} calls "
          f"({moved_b / len(sample):.1%}); its median is {st.median(only_b):.4f}")


# ------------------------------------------------------------------------ sensitivity


#: Each deviation is a transformation of a REAL call, not a freshly sampled one: an
#: evaluation whose benign and misuse sets come from the same generator recovers the
#: generator, not the scorer.
def _deviations(server: str) -> dict:
    if server == "github":
        return {
            "widen page size": ("list_issues",
                                {"owner": "To2004", "repo": "RubicCube", "state": "open",
                                 "per_page": 30, "page": 1},
                                "per_page", [30, 100, 1_000, 10_000, 1_000_000]),
            "deepen paging": ("list_commits",
                              {"owner": "To2004", "repo": "RubicCube", "perPage": 30,
                               "page": 1},
                              "page", [1, 10, 100, 1_000, 100_000]),
            "fan out a batch": ("push_files",
                                {"owner": "To2004", "repo": "mcp-traffic-scratch",
                                 "branch": "main", "message": "m",
                                 "files": [{"path": "a", "content": "c"}]},
                                "files", [1, 5, 50, 500, 5_000]),
        }
    if server == "slack":
        return {
            "widen history limit": ("conversations_history",
                                    {"channel_id": "C0BLK6CPECA", "limit": 100},
                                    "limit", [100, 500, 5_000, 50_000, 1_000_000]),
            "widen channel sweep": ("conversations_unreads",
                                    {"channel_types": "public_channel", "max_channels": 50,
                                     "max_messages_per_channel": 10},
                                    "max_channels", [50, 200, 2_000, 20_000, 200_000]),
        }
    return {
        "widen the window": ("list-events",
                             {"calendarId": ["primary"], "timeMin": "2026-08-14T00:00:00Z",
                              "timeMax": "2026-08-21T00:00:00Z"},
                             "timeMax", ["2026-08-21T00:00:00Z", "2026-11-14T00:00:00Z",
                                         "2027-08-14T00:00:00Z", "2036-08-14T00:00:00Z",
                                         "2126-08-14T00:00:00Z"]),
        "fan out calendars": ("list-events",
                              {"calendarId": ["primary"], "timeMin": "2026-08-14T00:00:00Z",
                               "timeMax": "2026-08-21T00:00:00Z"},
                              "calendarId", [1, 5, 50, 500, 5_000]),
    }


def sensitivity(rows: list[dict], server: str, floor: float) -> None:
    """Sweep each deviation and report where the score first clears the noise floor."""
    scorer, _ = _warm(rows, server)
    print(f"\nsensitivity: one real call, one argument swept, noise floor {floor:.3f}\n")
    for label, (tool, base, name, values) in _deviations(server).items():
        print(f"  {label}  ({tool}.{name})")
        baseline = None
        detected = None
        for value in values:
            probe = copy.deepcopy(base)
            if name == "files":
                probe[name] = [{"path": f"p{i}", "content": "c"} for i in range(value)]
            elif name == "calendarId":
                probe[name] = [f"cal{i}" for i in range(value)]
            else:
                probe[name] = value
            # Score without letting the probe teach the model the very value being probed.
            shadow = copy.deepcopy(scorer)
            score, _ = shadow.score(server, tool, probe)
            if baseline is None:
                baseline = score
            delta = score - baseline
            shown = value if not isinstance(value, str) else value[:10]
            mark = ""
            if abs(delta) > floor and detected is None:
                detected, mark = value, "  <- first detected"
            print(f"    {str(shown):>12}  D={score:.4f}  delta={delta:+.4f}{mark}")
        verdict = f"detected at {detected}" if detected is not None else "NEVER detected"
        print(f"    -> {verdict}\n")


# --------------------------------------------------------------------------- poisoning


def poisoning(rows: list[dict], server: str) -> None:
    """What evasion costs, for each factor the adversary can feed.

    Both factors learn from traffic the adversary controls. B is discount-only and blind
    to widening, so poisoning it buys nothing -- it is measured for completeness. L is the
    layer's only real signal, so the cost of normalising a rare tool is the number that
    matters.
    """
    scorer, _ = _warm(rows, server)
    counts = scorer.tool_calls[server]
    used = sorted(c for c in counts.values() if c)
    if not used:
        print("\npoisoning: no history\n")
        return
    median_calls = used[len(used) // 2]
    rare = min((t for t, c in counts.items() if c), key=lambda t: counts[t])

    print(f"\npoisoning L: normalising the rarest tool, {rare}")
    print(f"  it has {counts[rare]} calls; the median tool has {median_calls}\n")
    print(f"  {'cover calls sent':>17} {'L':>8}   verdict")
    sent = 0
    probe = {"owner": "x", "repo": "y"} if server == "github" else {}
    for target in (0, 250, 500, 1_000, 2_000):
        while sent < target:
            scorer.observe(server, rare, probe)
            sent += 1
        factor, _ = scorer.likelihood_factor(server, rare)
        verdict = "escalated" if factor > 1.05 else (
            "ORDINARY" if factor >= 1.0 else "DISCOUNTED - better than average")
        print(f"  {sent:>17,} {factor:>8.4f}   {verdict}")
    print(f"\n  cost of hiding a rare tool ~ the median tool's volume ({median_calls} calls).")
    print("  Past that the tool is scored BELOW 1.0: the attacker ends up better placed")
    print("  than an ordinary caller, because commonness is treated as evidence.")

    print(f"\npoisoning B: MAX_HISTORY={MAX_HISTORY} bounds how long any argument remembers,")
    print("  so an argument's quartiles can be owned outright with that many calls. It buys")
    print("  nothing here only because B cannot escalate in the first place.")


# ---------------------------------------------------------------------------- controls


def _variants(specs: dict, server: str) -> dict:
    """The scan's breadth labels, and two ways of destroying them."""
    rng = random.Random(0)
    randomised = copy.deepcopy(specs)
    constant = copy.deepcopy(specs)
    for tool in specs.get(server, {}):
        for name in specs[server][tool]:
            randomised[server][tool][name]["breadth"] = rng.choice([1, 2, 3, 4, 5])
            constant[server][tool][name]["breadth"] = FLAT_BREADTH
    return {"scan labels (as built)": specs,
            "randomised": randomised,
            "constant (no rubric)": constant}


def controls(rows: list[dict], server: str, floor: float) -> None:
    """Does the LLM breadth rubric earn its place, measured against what it drives?

    A component that can be replaced by noise without changing the result was not
    contributing. Breadth weights B, so it is controlled against B's own job -- detecting a
    widened argument -- and not against the write/read separation, which L drives and which
    breadth cannot affect either way.

    Every argument the runtime can read a quantity from is swept, rather than one chosen
    example: a single case cannot distinguish a rubric that helps from one that happens to
    help there.
    """
    specs = load_specs()
    print(f"\ncontrols: widening every measurable argument to {WIDEN_FACTOR}x its p90\n")
    print(f"  {'breadth labels':24} {'args':>5} {'detected':>9} {'median delta':>13}")
    for label, variant in _variants(specs, server).items():
        scorer, rest = _warm(rows, server)
        scorer.specs = variant
        example: dict[str, dict] = {}
        for row in rest:
            example.setdefault(row["tool"], _args(row))

        deltas = []
        for tool, base in example.items():
            for name, quantity, spec, source in list(scorer.quantities(server, tool, base)):
                key = (server, tool, name)
                history = scorer.history[key]
                if len(history) < MIN_HISTORY or source != "value" or name not in base:
                    continue
                p90 = history[min(len(history) - 1, (90 * len(history)) // 100)]
                probe = dict(base)
                probe[name] = ([probe[name][0]] * int(p90 * WIDEN_FACTOR)
                               if isinstance(probe[name], list) and probe[name]
                               else p90 * WIDEN_FACTOR)
                before, _ = copy.deepcopy(scorer).score(server, tool, base)
                after, _ = copy.deepcopy(scorer).score(server, tool, probe)
                deltas.append(after - before)
        if not deltas:
            print(f"  {label:24} {'-':>5} {'-':>9} {'-':>13}")
            continue
        found = sum(d > floor for d in deltas)
        print(f"  {label:24} {len(deltas):>5} {found / len(deltas):>8.0%} "
              f"{st.median(deltas):>+13.3f}")
    print("\n  If randomising the labels changes nothing, the rubric is inert. If the")
    print("  constant beats the scan labels, the rubric is costing sensitivity.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--server", default="github")
    parser.add_argument("--floor", type=float, default=0.009,
                        help="noise floor from report_org_run.py for this corpus")
    parser.add_argument("--only", choices=("ablation", "sensitivity", "poisoning",
                                           "controls"))
    args = parser.parse_args(argv)

    rows = _load(args.corpus)
    print("=" * 78)
    print(f"{args.corpus.name}   server={args.server}   n={len(rows):,}")
    print("=" * 78)
    if args.only in (None, "ablation"):
        ablation(rows, args.server)
    if args.only in (None, "sensitivity"):
        sensitivity(rows, args.server, args.floor)
    if args.only in (None, "poisoning"):
        poisoning(rows, args.server)
    if args.only in (None, "controls"):
        controls(rows, args.server, args.floor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
