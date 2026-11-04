"""Shape of MCP call traffic: tool mix, session length, gaps, reply size and time of week.

Measures outside traffic (MCPHunt's recorded agents), our simulated organisations (the
mostly-ordinary GitHub world and the world2 GitHub / Slack / Calendar worlds) and our earlier
tool-mix corpora, fits each distribution's shape, and sets them beside the published numbers
(PostHog's MCP server, MCPMark, ADR-Bench). Writes ``results.json`` (summaries, fits and the
curves the plot script draws) and ``results.md``.

Run:
    uv run python scripts/call_distributions.py --out reports/experiments/call_distributions
    uv run --with matplotlib python scripts/plot_call_distributions.py \
        --results reports/experiments/call_distributions/results.json
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
DYNAMIC_DIR = REPO / "reports" / "experiments" / "dynamic_dimensions"
MCPHUNT_TRACES = REPO / "external" / "mcphunt" / "traces"
MCPHUNT_CATALOGS = REPO / "reports" / "experiments" / "gateway" / "mcphunt"
WORLD2_START = datetime(2024, 10, 14, tzinfo=timezone.utc)  # world2.py START
NORMAL_WORLD_AGENTS, NORMAL_WORLD_SEED = 150, 7  # normal_org_sim.py defaults
UNKNOWN_SERVER = "unknown"
CALL_METHOD = "tools/call"
FAILED_STATUS_PREFIXES = ("error", "exc", "timeout")
UNLABELLED_STATUSES = ("synthetic",)

SAMPLE_CAP = 100_000  # values per shape fit (fits are slow on millions)
TAIL_FRACTION = 0.05  # Hill tail index over the top 5% of values
BURST_GAP_S = 0.1  # gaps shorter than this are calls sent together (one model turn)
TOP_SHARES = (0.005, 0.01)  # share of all reply bytes carried by the top 0.5% / 1% of calls
CCDF_POINTS = 60
SEED = 20261104
HOURS_PER_WEEK = 168
SHAPES = ("lognorm", "expon", "weibull_min", "gamma")

#: Published numbers, checked on 2026-11-04 (see README for the quotes)
WEB_REFERENCE = {
    "posthog": {
        "source": "https://posthog.com/blog/how-ai-agents-behave",
        "what": "PostHog's MCP server, 63M tool calls from about 130,000 people over 90 days",
        "top_tool_shares": [0.25, 0.07],  # running SQL, reading the schema
        "reply_tokens": {"p50": 440, "p95": 7800, "p99": 16000},
        "failure_rate_by_client": {
            "Codex": 0.02,
            "Cursor": 0.035,
            "Cowork": 0.053,
            "Claude Code": 0.057,
        },
        "same_tool_after_error": 0.39,
        "one_tool_group_token_share": {"calls": 0.005, "tokens": 0.18},
    },
    "mcpmark": {"source": "https://arxiv.org/abs/2509.24002", "mean_calls_per_task": 17.4},
    "adr_bench": {"source": "https://arxiv.org/html/2605.17380", "mean_calls_per_task": 28.5},
}


@dataclass
class Corpus:
    """One call corpus, reduced to what the distributions need."""

    name: str
    kind: str  # outside agents | simulated org | persona corpus | scripted real calls
    tool_counts: Counter = field(default_factory=Counter)
    catalog_size: int | None = None
    session_lengths: np.ndarray = field(default_factory=lambda: np.array([]))
    gaps_s: np.ndarray = field(default_factory=lambda: np.array([]))
    reply_sizes: np.ndarray = field(default_factory=lambda: np.array([]))
    reply_unit: str = ""
    hour_of_week: np.ndarray = field(default_factory=lambda: np.array([]))
    failures: int | None = None
    labelled_calls: int | None = None  # calls with a known success/failure
    session_groups: dict[str, np.ndarray] = field(default_factory=dict)


# ---------------------------------------------------------------- statistics


def rank_shares(counts: Counter) -> np.ndarray:
    """Each tool's share of calls, largest first."""
    if not counts:
        raise ValueError("no tool counts")
    values = np.array(sorted(counts.values(), reverse=True), dtype=float)
    return values / values.sum()


def concentration(shares: np.ndarray, catalog_size: int | None) -> dict:
    """Top-1 and top-3 share, tools needed for 80% of calls, and how much of the catalog is used."""
    cumulative = np.cumsum(shares)
    entropy = -float(np.sum(shares * np.log(shares)))
    return {
        "tools_used": int(len(shares)),
        "catalog_size": catalog_size,
        "top1": float(cumulative[0]),
        "top3": float(cumulative[min(2, len(shares) - 1)]),
        "tools_for_80pct": int(np.searchsorted(cumulative, 0.8) + 1),
        "entropy_ratio": entropy / math.log(len(shares)) if len(shares) > 1 else 0.0,
    }


def _r_squared(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Slope and R² of a least-squares line y = a + b·x."""
    slope, intercept = np.polyfit(x, y, 1)
    residual = y - (intercept + slope * x)
    total = y - y.mean()
    return float(slope), float(1 - residual @ residual / (total @ total))


def fit_rank_curve(shares: np.ndarray) -> dict:
    """Compare a Zipf curve (log share linear in log rank) with a geometric one (linear in rank)."""
    if len(shares) < 3:
        raise ValueError("need at least three tools to fit a rank curve")
    ranks = np.arange(1, len(shares) + 1, dtype=float)
    log_shares = np.log(shares)
    zipf_slope, zipf_r2 = _r_squared(np.log(ranks), log_shares)
    geo_slope, geo_r2 = _r_squared(ranks, log_shares)
    return {
        "zipf_exponent": -zipf_slope,
        "zipf_r2": zipf_r2,
        "geometric_ratio": math.exp(geo_slope),
        "geometric_r2": geo_r2,
        "better": "zipf" if zipf_r2 >= geo_r2 else "geometric",
    }


def summarise(values: np.ndarray) -> dict:
    """Count, mean and the 50th / 90th / 99th percentiles and maximum."""
    if len(values) == 0:
        raise ValueError("no values")
    p50, p90, p99 = np.percentile(values, [50, 90, 99])
    return {
        "n": int(len(values)),
        "mean": float(values.mean()),
        "p50": float(p50),
        "p90": float(p90),
        "p99": float(p99),
        "max": float(values.max()),
    }


def _sample(values: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """At most ``SAMPLE_CAP`` positive values, drawn without replacement."""
    positive = values[values > 0]
    if len(positive) > SAMPLE_CAP:
        positive = rng.choice(positive, SAMPLE_CAP, replace=False)
    return positive


def fit_shapes(values: np.ndarray, rng: np.random.Generator) -> dict:
    """Fit each candidate shape by maximum likelihood (location fixed at 0); best by AIC."""
    sample = _sample(values, rng)
    if len(sample) < 10:
        raise ValueError("need at least ten positive values to fit a shape")
    fits = {}
    for name in SHAPES:
        distribution = getattr(stats, name)
        params = distribution.fit(sample, floc=0)
        log_likelihood = float(np.sum(distribution.logpdf(sample, *params)))
        free = len(params) - 1  # location is fixed
        ks = float(stats.kstest(sample, name, args=params).statistic)
        fits[name] = {
            "aic": 2 * free - 2 * log_likelihood,
            "ks": ks,
            "params": [float(p) for p in params],
        }
    best = min(fits, key=lambda n: fits[n]["aic"])
    return {"best": best, "fits": fits, "tail_index": hill_tail_index(sample)}


def hill_tail_index(values: np.ndarray, tail_fraction: float = TAIL_FRACTION) -> float:
    """Hill estimate of the power-law exponent of the largest values (lower = heavier tail)."""
    ordered = np.sort(values[values > 0])[::-1]
    k = max(int(len(ordered) * tail_fraction), 2)
    threshold = ordered[k]
    logs = np.log(ordered[:k] / threshold)
    if logs.sum() == 0:
        return math.inf
    return float(k / logs.sum())


def ccdf_points(values: np.ndarray, n_points: int = CCDF_POINTS) -> list[list[float]]:
    """``[x, P(X >= x)]`` at log-spaced x, for a log-log plot."""
    positive = np.sort(values[values > 0])
    if len(positive) == 0:
        raise ValueError("no positive values")
    xs = np.unique(np.geomspace(positive[0], positive[-1], n_points))
    above = 1 - np.searchsorted(positive, xs, side="left") / len(positive)
    return [[float(x), float(p)] for x, p in zip(xs, above, strict=True)]


def top_share(values: np.ndarray, fraction: float) -> float:
    """Share of the total carried by the largest ``fraction`` of values."""
    ordered = np.sort(values)[::-1]
    k = max(int(len(ordered) * fraction), 1)
    return float(ordered[:k].sum() / ordered.sum())


def hour_of_week_counts(epoch_seconds: np.ndarray) -> np.ndarray:
    """Calls per hour of the week (Monday 00:00 UTC = 0), from Unix times."""
    days = np.floor(epoch_seconds / 86400).astype(int)
    weekday = (days + 3) % 7  # 1970-01-01 was a Thursday
    hour = np.floor((epoch_seconds % 86400) / 3600).astype(int)
    return np.bincount(weekday * 24 + hour, minlength=HOURS_PER_WEEK).astype(float)


def session_gaps(times_by_session: dict) -> np.ndarray:
    """Seconds between consecutive calls inside each session."""
    gaps = [np.diff(np.sort(np.asarray(t))) for t in times_by_session.values() if len(t) > 1]
    return np.concatenate(gaps) if gaps else np.array([])


# ---------------------------------------------------------------- loaders


def _catalog_size(catalog_dir: Path) -> int:
    """Number of tools across every server catalog captured for MCPHunt."""
    catalogs = [
        p
        for p in sorted(catalog_dir.glob("*/mcphunt_*.json"))
        if p.name == f"mcphunt_{p.parent.name}.json"
    ]  # not the .cells.json files
    return sum(len(json.loads(p.read_text())["tools"]) for p in catalogs)


def load_mcphunt(traces_dir: Path, catalog_dir: Path) -> Corpus:
    """MCPHunt: each run is one session; times are each call's recorded end time."""
    corpus = Corpus(
        "MCPHunt (5 models)",
        "outside agents",
        catalog_size=_catalog_size(catalog_dir),
        reply_unit="chars",
    )
    lengths, times, replies, epochs = [], defaultdict(list), [], []
    failures = 0
    by_model: dict[str, list[int]] = defaultdict(list)
    for path in sorted(traces_dir.glob("*.json")):
        for trace in json.loads(path.read_text(encoding="utf-8"))["traces"]:
            events = [e for e in trace["events"] if e.get("server") != UNKNOWN_SERVER]
            lengths.append(len(events))
            by_model[path.stem].append(len(events))
            for event in events:
                corpus.tool_counts[f"{event['server']}/{event['tool']}"] += 1
                stamp = float(event["timestamp"])
                times[(path.stem, trace["trace_id"])].append(stamp)  # ids repeat per model
                epochs.append(stamp)
                replies.append(float(event["result_chars"]))
                failures += str(event["success"]) != "True"
    corpus.session_lengths = np.array(lengths, dtype=float)
    corpus.gaps_s = session_gaps(times)
    corpus.reply_sizes = np.array(replies)
    corpus.hour_of_week = hour_of_week_counts(np.array(epochs))
    corpus.failures, corpus.labelled_calls = failures, len(replies)
    corpus.session_groups = {m: np.array(v, dtype=float) for m, v in by_model.items()}
    return corpus


def load_normal_world(agents: int, seed: int) -> Corpus:
    """The mostly-ordinary GitHub organisation (``normal_org_world``, v5 rows with reply bytes)."""
    sys.path.insert(0, str(DYNAMIC_DIR))
    from normal_org_world import CATALOG, ROW_V5, build_world  # noqa: PLC0415

    world, _, _ = build_world(agents, seed, world_version="v5")
    col = {name: i for i, name in enumerate(ROW_V5)}
    corpus = Corpus(
        f"Normal org world (GitHub, {agents} agents, 180 days)",
        "simulated org",
        catalog_size=len(CATALOG),
        reply_unit="bytes",
    )
    times, replies = defaultdict(list), []
    for agent, rows in world.items():
        for row in rows:
            if row[col["method"]] != CALL_METHOD:
                continue
            corpus.tool_counts[row[col["tool"]]] += 1
            times[(agent, row[col["session"]])].append(row[col["ts"]])
            replies.append(float(row[col["resp"]]))
    corpus.session_lengths = np.array([len(t) for t in times.values()], dtype=float)
    corpus.gaps_s = session_gaps(times)
    corpus.reply_sizes = np.array(replies)
    corpus.hour_of_week = hour_of_week_counts(
        np.concatenate([np.asarray(t) for t in times.values()])
    )
    return corpus


def load_world2(path: Path, server: str) -> Corpus:
    """A world2 corpus: agent->server messages only, ``ts`` in seconds from ``WORLD2_START``."""
    csv.field_size_limit(sys.maxsize)
    corpus = Corpus(f"World2 {server} (50 agents, 730 days)", "simulated org")
    times = defaultdict(list)
    with gzip.open(path, "rt", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["method"] != CALL_METHOD:
                continue
            corpus.tool_counts[row["tool"]] += 1
            times[(row["agent"], row["session"])].append(float(row["ts"]))
    corpus.session_lengths = np.array([len(t) for t in times.values()], dtype=float)
    corpus.gaps_s = session_gaps(times)
    offsets = np.concatenate([np.asarray(t) for t in times.values()])
    corpus.hour_of_week = hour_of_week_counts(offsets + WORLD2_START.timestamp())
    return corpus


def load_tool_mix(path: Path, name: str, kind: str) -> Corpus:
    """A corpus with no time or session columns: tool counts and failures only."""
    csv.field_size_limit(sys.maxsize)
    corpus = Corpus(name, kind)
    failures = labelled = 0
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            corpus.tool_counts[row["tool"]] += 1
            status = row["status"].lower()
            if status.startswith(UNLABELLED_STATUSES) or status.startswith("skipped"):
                continue
            labelled += 1
            failures += status.startswith(FAILED_STATUS_PREFIXES)
    if labelled:
        corpus.failures, corpus.labelled_calls = failures, labelled
    return corpus


def default_corpora() -> list[Corpus]:
    """Every corpus this repo holds that says something about call shape."""
    benign = REPO / "reports" / "experiments" / "real_benign"
    finance = REPO / "reports" / "experiments" / "real_benign_finance"
    corpora = [
        load_mcphunt(MCPHUNT_TRACES, MCPHUNT_CATALOGS),
        load_normal_world(NORMAL_WORLD_AGENTS, NORMAL_WORLD_SEED),
    ]
    corpora += [
        load_world2(DYNAMIC_DIR / "w2" / f"{s}_M.csv.gz", s)
        for s in ("github", "slack", "calendar")
    ]
    for org, server in (
        ("github_helios", "GitHub"),
        ("slack_vireo", "Slack"),
        ("calendar_aurora", "Calendar"),
    ):
        corpora.append(
            load_tool_mix(
                benign / f"{org}_org_100k.csv", f"Persona corpus {server} (100k)", "persona corpus"
            )
        )
        corpora.append(
            load_tool_mix(
                benign / f"{org}_real.csv", f"Scripted real {server} (1k)", "scripted real calls"
            )
        )
    for path in sorted(finance.glob("*_real.csv")):
        corpora.append(
            load_tool_mix(
                path, f"Scripted real {path.stem.removesuffix('_real')}", "scripted real calls"
            )
        )
    return corpora


# ---------------------------------------------------------------- report


def distribution(values: np.ndarray, rng: np.random.Generator) -> dict:
    """Summary, shape fits and log-log curve of one distribution."""
    return {**summarise(values), **fit_shapes(values, rng), "ccdf": ccdf_points(values)}


def describe(corpus: Corpus, rng: np.random.Generator) -> dict:
    """Every summary, fit and curve for one corpus."""
    shares = rank_shares(corpus.tool_counts)
    result: dict[str, object] = {
        "name": corpus.name,
        "kind": corpus.kind,
        "calls": int(sum(corpus.tool_counts.values())),
        "tool_mix": {
            **concentration(shares, corpus.catalog_size),
            **fit_rank_curve(shares),
            "shares": [float(s) for s in shares],
        },
    }
    if corpus.labelled_calls and corpus.failures is not None:
        result["failure_rate"] = corpus.failures / corpus.labelled_calls
    if len(corpus.session_lengths):
        sessions = distribution(corpus.session_lengths, rng)
        if corpus.session_groups:
            sessions["by_group"] = {
                g: summarise(v) for g, v in sorted(corpus.session_groups.items())
            }
        result["session_length"] = sessions
    if len(corpus.gaps_s):
        result["gap_s"] = {
            **distribution(corpus.gaps_s, rng),
            "burst_share": float(np.mean(corpus.gaps_s < BURST_GAP_S)),
        }
    if len(corpus.reply_sizes):
        result["reply_size"] = {
            **distribution(corpus.reply_sizes, rng),
            "unit": corpus.reply_unit,
            **{f"top_{f}_share": top_share(corpus.reply_sizes, f) for f in TOP_SHARES},
        }
    if len(corpus.hour_of_week):
        week = corpus.hour_of_week / corpus.hour_of_week.sum()
        result["hour_of_week"] = [float(s) for s in week]
        result["weekend_share"] = float(week[5 * 24 :].sum())
    return result


def _cell(value: object, digits: int = 2) -> str:
    """A table cell: numbers rounded, missing values as a dash."""
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.{digits}f}" if abs(value) < 1000 else f"{value:,.0f}"
    return f"{value:,}" if isinstance(value, int) else str(value)


def _distribution_table(results: list[dict], key: str, title: str) -> list[str]:
    """One markdown table of a distribution's summary and best-fitting shape."""
    lines = [
        f"## {title}",
        "",
        "| Corpus | n | Mean | Median | p90 | p99 | Max | Best fit (AIC) "
        "| KS of best | Tail index |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        if key not in r:
            continue
        d = r[key]
        lines.append(
            " | ".join(
                [
                    "",
                    r["name"],
                    _cell(d["n"]),
                    _cell(d["mean"]),
                    _cell(d["p50"]),
                    _cell(d["p90"]),
                    _cell(d["p99"]),
                    _cell(d["max"]),
                    d["best"],
                    _cell(d["fits"][d["best"]]["ks"], 3),
                    _cell(d["tail_index"]),
                    "",
                ]
            ).strip()
        )
    return [*lines, ""]


def to_markdown(results: list[dict]) -> str:
    """The generated tables (the README holds the reading of them)."""
    lines = [
        "# Call distributions: generated tables",
        "",
        "Written by `scripts/call_distributions.py`; see [README.md](README.md) for what "
        "they mean.",
        "",
        "## Tool mix",
        "",
        "| Corpus | Kind | Calls | Tools used / catalog | Top-1 | Top-3 | Tools for 80% "
        "| Zipf R² | Geometric R² | Shape | Failure rate |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        t = r["tool_mix"]
        used = f"{t['tools_used']} / {_cell(t['catalog_size'])}"
        lines.append(
            " | ".join(
                [
                    "",
                    r["name"],
                    r["kind"],
                    _cell(r["calls"]),
                    used,
                    _cell(t["top1"], 3),
                    _cell(t["top3"], 3),
                    _cell(t["tools_for_80pct"]),
                    _cell(t["zipf_r2"], 3),
                    _cell(t["geometric_r2"], 3),
                    t["better"],
                    _cell(r.get("failure_rate"), 3),
                    "",
                ]
            ).strip()
        )
    lines.append("")
    lines += _distribution_table(results, "session_length", "Calls per session")
    lines += _distribution_table(results, "gap_s", "Seconds between calls in a session")
    lines += [
        f"Share of gaps under {BURST_GAP_S} s (calls sent together): "
        + "; ".join(
            f"{r['name']} {r['gap_s']['burst_share']:.3f}" for r in results if "gap_s" in r
        ),
        "",
    ]
    lines += _distribution_table(results, "reply_size", "Reply size per call")
    lines += [
        "| Corpus | Unit | Top 0.5% of calls carry | Top 1% carry | Weekend share |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        if "reply_size" in r or "weekend_share" in r:
            reply = r.get("reply_size", {})
            lines.append(
                " | ".join(
                    [
                        "",
                        r["name"],
                        reply.get("unit", "—"),
                        _cell(reply.get("top_0.005_share"), 3),
                        _cell(reply.get("top_0.01_share"), 3),
                        _cell(r.get("weekend_share"), 3),
                        "",
                    ]
                ).strip()
            )
    return "\n".join([*lines, ""])


def main() -> None:
    """Measure every corpus and write ``results.json`` and ``results.md``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--out", type=Path, required=True, help="folder for results.json / .md")
    args = parser.parse_args()
    rng = np.random.default_rng(SEED)
    results = [describe(corpus, rng) for corpus in default_corpora()]
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "results.json").write_text(
        json.dumps({"corpora": results, "web": WEB_REFERENCE}, indent=1)
    )
    (args.out / "results.md").write_text(to_markdown(results))
    print(f"{len(results)} corpora -> {args.out}")


if __name__ == "__main__":
    main()
