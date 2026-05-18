"""Render a categorical risk heatmap: cbg.db tables x SQLite MCP tools.

Rows  : 7 tables in demo/cbg_sqlite/cbg.db (api_keys, employees, ... publications),
        ordered by sensitivity tier.
Cols  : 6 tools from the reference SQLite MCP server (mcp-server-sqlite):
        read_query, write_query, create_table, list_tables, describe_table,
        append_insight.
Cells : categorical risk tier - High / Medium / Low.

Tier rationale (asset side):
  - api_keys, employees, grants : credentials / PII+salary / financial -> High.
  - datasets, experiments, projects : research IP and operational data -> Medium.
  - publications : largely public output -> Low.

Tier rationale (action side):
  - read_query / write_query : full disclosure or direct tamper of the asset.
  - create_table : structural; not asset-targeted -> Low everywhere.
  - list_tables / describe_table : schema recon, scaled by asset sensitivity.
  - append_insight : writes to a memo resource, not the tables -> Low everywhere.

Output: presentations/cbg_sqlite_risk_heatmap.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "presentations" / "cbg_sqlite_risk_heatmap.png"

ASSETS = [
    "api_keys",
    "employees",
    "grants",
    "datasets",
    "experiments",
    "projects",
    "publications",
]

TOOLS = [
    "read_query",
    "write_query",
    "create_table",
    "list_tables",
    "describe_table",
    "append_insight",
]

L, M, H = 0, 1, 2
LABELS = {L: "Low", M: "Medium", H: "High"}

# Rows in ASSETS order, cols in TOOLS order.
RISK: list[list[int]] = [
    # read  write  create  list  desc  insight
    [   H,    H,    L,     M,    M,    L  ],  # api_keys
    [   H,    H,    L,     M,    M,    L  ],  # employees
    [   H,    H,    L,     M,    M,    L  ],  # grants
    [   M,    M,    L,     L,    L,    L  ],  # datasets
    [   M,    M,    L,     L,    L,    L  ],  # experiments
    [   M,    M,    L,     L,    L,    L  ],  # projects
    [   L,    L,    L,     L,    L,    L  ],  # publications
]


def render(matrix: np.ndarray, out_path: Path) -> None:
    """Render the categorical heatmap to `out_path` as PNG."""
    cmap = ListedColormap(["#1a9850", "#fee08b", "#d73027"])  # Low, Medium, High

    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    ax.imshow(matrix, cmap=cmap, vmin=-0.5, vmax=2.5, aspect="auto")

    ax.set_xticks(np.arange(len(TOOLS)))
    ax.set_yticks(np.arange(len(ASSETS)))
    ax.set_xticklabels(TOOLS, rotation=30, ha="right", fontsize=10)
    ax.set_yticklabels(ASSETS, fontsize=11, family="monospace")

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            tier = LABELS[int(matrix[i, j])]
            color = "white" if matrix[i, j] != M else "black"
            ax.text(j, i, tier, ha="center", va="center",
                    color=color, fontsize=10, fontweight="bold")

    ax.set_xticks(np.arange(-0.5, len(TOOLS), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(ASSETS), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)

    ax.set_title(
        "Risk heatmap: demo/cbg_sqlite tables x SQLite MCP tools",
        fontsize=13,
        pad=12,
    )
    ax.set_xlabel("SQLite MCP tool", fontsize=11)
    ax.set_ylabel("Table (asset)", fontsize=11)

    legend = [
        Patch(facecolor="#d73027", label="High"),
        Patch(facecolor="#fee08b", label="Medium"),
        Patch(facecolor="#1a9850", label="Low"),
    ]
    ax.legend(handles=legend, loc="center left", bbox_to_anchor=(1.01, 0.5),
              frameon=False, fontsize=10, title="Risk tier")

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    matrix = np.array(RISK, dtype=int)
    render(matrix, OUT_PATH)
    print(f"wrote {OUT_PATH} ({matrix.shape[0]} tables x {matrix.shape[1]} tools)")


if __name__ == "__main__":
    main()
