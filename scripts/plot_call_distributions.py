"""Draw the call-distribution figures from ``results.json`` (written by call_distributions.py).

Three PNGs next to the results: tool share by rank, the log-log tails of session length,
gap and reply size, and calls by hour of the week. Matplotlib is not a project dependency:

    uv run --with matplotlib python scripts/plot_call_distributions.py \
        --results reports/experiments/call_distributions/results.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
#: Fixed colour per corpus (validated categorical order); line style says where it came from
STYLE = {
    "MCPHunt (5 models)": ("#2a78d6", "-", "MCPHunt (outside agents)"),
    "PostHog": ("#eb6834", "none", "PostHog MCP server (published)"),
    "Normal org world (GitHub, 150 agents, 180 days)": ("#1baf7a", "--", "Our normal org world"),
    "World2 github (50 agents, 730 days)": ("#eda100", "--", "Our world2 GitHub"),
    "World2 slack (50 agents, 730 days)": ("#e87ba4", "--", "Our world2 Slack"),
    "Scripted real maverick_talon": ("#6250d6", ":", "Our scripted real calls (Maverick)"),
}
MAX_RANK = 30
BENCH_LABELS = {"mcpmark": "MCPMark", "adr_bench": "ADR-Bench"}
GAP_AXIS_FROM_S = 1e-4
CHARS_PER_TOKEN = 4  # rough English average, to set chars and bytes beside PostHog's tokens
DPI = 160


def _axes(ax: plt.Axes, title: str, xlabel: str, ylabel: str) -> None:
    """Recessive chrome: no top/right spines, light grid, muted ink."""
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", fontsize=11, color=INK)
    ax.set_xlabel(xlabel, color=MUTED)
    ax.set_ylabel(ylabel, color=MUTED)
    ax.grid(True, which="major", color=GRID, linewidth=0.8)
    ax.tick_params(colors=MUTED, labelsize=8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)


def _line(ax: plt.Axes, name: str, xs: list[float], ys: list[float]) -> None:
    """One corpus as a 2px line in its fixed colour and source style."""
    colour, style, label = STYLE[name]
    ax.plot(xs, ys, color=colour, linestyle=style, linewidth=2, label=label)


def plot_tool_mix(corpora: dict[str, dict], web: dict, out: Path) -> None:
    """Share of calls by tool rank, log scale: a straight line is a geometric fall-off."""
    fig, ax = plt.subplots(figsize=(7.5, 4.6), facecolor=SURFACE)
    for name in STYLE:
        if name in corpora:
            shares = corpora[name]["tool_mix"]["shares"][:MAX_RANK]
            _line(ax, name, list(range(1, len(shares) + 1)), shares)
    colour, _, label = STYLE["PostHog"]
    top = web["posthog"]["top_tool_shares"]
    ax.plot(
        range(1, len(top) + 1),
        top,
        "o",
        color=colour,
        markersize=8,
        label=label,
        markeredgecolor=SURFACE,
        markeredgewidth=2,
    )
    ax.set_yscale("log")
    _axes(ax, "Share of calls by tool rank", "Tool rank (1 = most called)", "Share of calls")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK)
    fig.tight_layout()
    fig.savefig(out, dpi=DPI, facecolor=SURFACE)
    plt.close(fig)


def _ccdf(ax: plt.Axes, corpora: dict[str, dict], key: str, scale: float = 1.0) -> None:
    """Every corpus that has ``key`` as a log-log P(X >= x) line."""
    for name in STYLE:
        if name in corpora and key in corpora[name]:
            points = corpora[name][key]["ccdf"]
            _line(ax, name, [x * scale for x, _ in points], [p for _, p in points])
    ax.set_xscale("log")
    ax.set_yscale("log")


def plot_tails(corpora: dict[str, dict], web: dict, out: Path) -> None:
    """Three log-log tails: calls per session, seconds between calls, reply size."""
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), facecolor=SURFACE)
    sessions, gaps, replies = axes
    _ccdf(sessions, corpora, "session_length")
    for bench, height in (("mcpmark", 3e-5), ("adr_bench", 1e-5)):
        mean = web[bench]["mean_calls_per_task"]
        sessions.axvline(mean, color=MUTED, linewidth=1, linestyle="-.")
        sessions.text(
            mean * 1.08, height, f"{BENCH_LABELS[bench]} mean {mean}", fontsize=7, color=MUTED
        )
    _axes(sessions, "Calls per session", "Calls (x)", "Share of sessions with ≥ x calls")
    _ccdf(gaps, corpora, "gap_s")
    gaps.set_xlim(left=GAP_AXIS_FROM_S)
    _axes(gaps, "Seconds between calls in a session", "Seconds (x)", "Share of gaps ≥ x")
    _ccdf(replies, corpora, "reply_size", scale=1 / CHARS_PER_TOKEN)
    colour, _, label = STYLE["PostHog"]
    quantiles = web["posthog"]["reply_tokens"]
    replies.plot(
        [quantiles["p50"], quantiles["p95"], quantiles["p99"]],
        [0.5, 0.05, 0.01],
        "o",
        color=colour,
        markersize=8,
        markeredgecolor=SURFACE,
        markeredgewidth=2,
        label=label,
    )
    _axes(
        replies,
        "Reply size per call",
        f"Tokens, about chars / {CHARS_PER_TOKEN} (x)",
        "Share of calls with reply ≥ x",
    )
    handles, labels = [], []
    for ax in axes:
        for handle, text in zip(*ax.get_legend_handles_labels(), strict=True):
            if text not in labels:
                handles.append(handle)
                labels.append(text)
    fig.legend(handles, labels, loc="lower center", ncol=len(labels), frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(out, dpi=DPI, facecolor=SURFACE)
    plt.close(fig)


def plot_week(corpora: dict[str, dict], out: Path) -> None:
    """Calls by hour of the week (UTC), one small panel per corpus that has real times."""
    names = [n for n in STYLE if n in corpora and "hour_of_week" in corpora[n]]
    fig, axes = plt.subplots(
        len(names), 1, figsize=(10, 1.9 * len(names)), sharex=True, facecolor=SURFACE, squeeze=False
    )
    for ax, name in zip(axes[:, 0], names, strict=True):
        week = [100 * s for s in corpora[name]["hour_of_week"]]
        colour, style, label = STYLE[name]
        ax.plot(range(len(week)), week, color=colour, linestyle=style, linewidth=2)
        weekend = corpora[name]["weekend_share"]
        _axes(ax, f"{label}: weekend {weekend:.0%} of calls", "", "% of calls")
        for day in range(1, 7):
            ax.axvline(day * 24, color=GRID, linewidth=1)
    axes[-1, 0].set_xticks(
        [d * 24 + 12 for d in range(7)], ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    )
    axes[-1, 0].set_xlabel("Hour of the week (UTC)", color=MUTED)
    fig.tight_layout()
    fig.savefig(out, dpi=DPI, facecolor=SURFACE)
    plt.close(fig)


def main() -> None:
    """Read ``results.json`` and write the three figures beside it."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.results.read_text())
    corpora = {c["name"]: c for c in data["corpora"]}
    folder = args.results.parent
    plot_tool_mix(corpora, data["web"], folder / "tool_mix.png")
    plot_tails(corpora, data["web"], folder / "tails.png")
    plot_week(corpora, folder / "time_of_week.png")
    print(f"figures -> {folder}")


if __name__ == "__main__":
    main()
