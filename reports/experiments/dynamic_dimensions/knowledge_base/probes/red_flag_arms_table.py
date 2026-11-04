"""Print the red_flag_arms.py results of several development worlds side by side.

    python3 red_flag_arms_table.py OUT1.json OUT2.json ...

Every number is from a burnt development world, not a test result.
"""

from __future__ import annotations

import json
import sys

TAGS = ("new_hire", "org_tool_rollout", "org_vpn_change", "org_repo_migration", "new_project")


def main() -> None:
    runs = [json.load(open(p, encoding="utf-8")) for p in sys.argv[1:]]
    names = [f"{r['world']['seed']}/{r['world']['agents']}/{r['world']['profile']}" for r in runs]
    print("development worlds:", ", ".join(names))
    for r, n in zip(runs, names):
        print(f"  {n}: v4 flag raise rates on ordinary agent-days {r['flag_raise_rate_ordinary_v4']}")
        print(f"     sequence firings {r['sequence_firings_ordinary']['agent_days_by_branch_flow']}"
              f" newsrc-days {r['sequence_firings_ordinary'].get('agent_days_newsrc')}"
              f" down5-days {r['sequence_firings_ordinary'].get('agent_days_down5')}")
    arms = list(runs[0]["arms"])
    print(f"\n{'arm':58s} " + " | ".join(f"{n:>34s}" for n in names))
    print(f"{'':58s} " + " | ".join(f"{'ordx3 ppl  bots  M1.9 gray list':>34s}" for _ in names))
    for arm in arms:
        cells = []
        for r in runs:
            a = r["arms"][arm]
            cells.append(
                f"{100 * a['ordinary_x3']:5.2f} {100 * a['ordinary_x3_people']:5.2f} "
                f"{100 * a['ordinary_x3_bots']:4.2f} {100 * a['ordinary_M_ge_1.9']:5.1f} "
                f"{a['gray_caught_x3_all']:.3f} {a['gray_on_list_top4']:.3f}"
            )
        print(f"{arm:58s} " + " | ".join(f"{c:>34s}" for c in cells))
    print("\ncross copy caught at x3 / changes at x3 (tags)")
    for arm in arms:
        cc = [r["arms"][arm]["gray_caught_x3"].get("cross_copy", "-") for r in runs]
        tg = []
        for r in runs:
            ch = r["arms"][arm]["changes_x3"]
            tg.append(" ".join(ch.get(t, "-") for t in TAGS))
        print(f"{arm:58s} cc={' '.join(cc):24s} tags[{' '.join(TAGS)}]: {' || '.join(tg)}")
    print("\nordinary x3 causes")
    for arm in arms:
        print(f"{arm:58s} " + " || ".join(str(r["arms"][arm]["ordinary_x3_causes"][:4]) for r in runs))


if __name__ == "__main__":
    main()
