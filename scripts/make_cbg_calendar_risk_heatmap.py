"""Render a categorical risk heatmap: CBG project-manager calendar assets x Google Calendar MCP tools.

Perspective: a project manager at the CBG research lab whose Google account is
exposed to an MCP agent through the google-calendar MCP server.

Rows  : 7 event-category assets the PM owns or attends. Tiered by sensitivity.
Cols  : 13 tools observed from the google-calendar MCP server tool catalog
        (logs/proxy/sessions/calendar/parsed/tools_catalog.csv).
Cells : categorical risk tier - High / Medium / Low.

Asset tier rationale:
  - PI 1:1s, Sponsor/grant meetings, Hiring & personnel, Embargoed project mtgs:
    confidential strategy, financial commitments, HR data, or under-embargo
    research -> High-sensitivity events.
  - Internal team syncs, External collaborator meetings: operational, mid value.
  - Public seminars / lab events: announced publicly anyway -> Low.

Tool tier rationale:
  - list-events / search-events / get-event : full or targeted disclosure of
    event content (titles, attendees, description, attachments) -> scales with
    asset sensitivity.
  - update-event / delete-event : direct tamper or DoS of a known event ->
    High on sensitive assets.
  - create-event / create-events : poisoning / social-engineering vector;
    Medium for sensitive categories where a fake invite is plausible.
  - respond-to-event : reply on behalf of the PM; mostly Medium for sensitive
    contexts (false acceptance can be misleading).
  - list-calendars / get-freebusy : low-content recon; freebusy reveals only
    busy/free, not titles -> Low.
  - list-colors / get-current-time : not asset-bearing -> Low.
  - manage-accounts : auth-level admin (add/remove Google accounts); not tied
    to a single asset but could enable broader access -> uniform Medium.

Output: presentations/cbg_calendar_risk_heatmap.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "presentations" / "cbg_calendar_risk_heatmap.png"

ASSETS = [
    "PI 1:1s",
    "Sponsor / grant meetings",
    "Hiring & personnel",
    "Embargoed project mtgs",
    "Internal team syncs",
    "External collaborator mtgs",
    "Public seminars / lab events",
]

TOOLS = [
    "list-events",
    "search-events",
    "get-event",
    "list-calendars",
    "get-freebusy",
    "create-event",
    "create-events",
    "update-event",
    "delete-event",
    "respond-to-event",
    "list-colors",
    "get-current-time",
    "manage-accounts",
]

L, M, H = 0, 1, 2
LABELS = {L: "Low", M: "Medium", H: "High"}

# Rows in ASSETS order, cols in TOOLS order.
RISK: list[list[int]] = [
    # list-evt search-evt get-evt list-cal freebusy create-evt create-evts upd-evt del-evt respond colors curtime accounts
    [   H,      H,         H,      M,       L,       M,          M,          H,       H,       M,      L,     L,      M  ],  # PI 1:1s
    [   H,      H,         H,      M,       L,       M,          M,          H,       H,       M,      L,     L,      M  ],  # Sponsor / grant
    [   H,      H,         H,      M,       L,       M,          M,          H,       H,       M,      L,     L,      M  ],  # Hiring
    [   H,      H,         H,      M,       L,       M,          M,          H,       H,       M,      L,     L,      M  ],  # Embargoed
    [   M,      M,         M,      L,       L,       L,          L,          M,       M,       L,      L,     L,      M  ],  # Internal syncs
    [   M,      M,         M,      L,       L,       L,          L,          M,       M,       L,      L,     L,      M  ],  # External collab
    [   L,      L,         L,      L,       L,       L,          L,          L,       L,       L,      L,     L,      M  ],  # Public seminars
]


def render(matrix: np.ndarray, out_path: Path) -> None:
    """Render the categorical heatmap to `out_path` as PNG."""
    cmap = ListedColormap(["#1a9850", "#fee08b", "#d73027"])  # Low, Medium, High

    fig, ax = plt.subplots(figsize=(15.5, 5.8))
    ax.imshow(matrix, cmap=cmap, vmin=-0.5, vmax=2.5, aspect="auto")

    ax.set_xticks(np.arange(len(TOOLS)))
    ax.set_yticks(np.arange(len(ASSETS)))
    ax.set_xticklabels(TOOLS, rotation=35, ha="right", fontsize=9)
    ax.set_yticklabels(ASSETS, fontsize=10)

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            tier = LABELS[int(matrix[i, j])]
            color = "white" if matrix[i, j] != M else "black"
            ax.text(j, i, tier, ha="center", va="center",
                    color=color, fontsize=8.5, fontweight="bold")

    ax.set_xticks(np.arange(-0.5, len(TOOLS), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(ASSETS), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)

    ax.set_title(
        "Risk heatmap: CBG project-manager calendar assets x Google Calendar MCP tools",
        fontsize=13,
        pad=12,
    )
    ax.set_xlabel("Google Calendar MCP tool", fontsize=11)
    ax.set_ylabel("Calendar asset (event category)", fontsize=11)

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
    print(f"wrote {OUT_PATH} ({matrix.shape[0]} assets x {matrix.shape[1]} tools)")


if __name__ == "__main__":
    main()
