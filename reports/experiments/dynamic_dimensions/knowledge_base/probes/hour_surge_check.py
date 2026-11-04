"""Which benign agent-days drive Hour-of-day spend under the org-level record rank (DEVELOPMENT
WORLD only; v4 score vectors, arm O1 of org_record_rank_probe.py).

Prints, at the 1% line and at x3, how many benign agent-days alert through Hour of day alone,
split ordinary / change, the busiest days and the change tags behind them. Used for review
finding R3-4 (common-mode shifts): one org-wide event can spend a dimension's whole share.

    python3 hour_surge_check.py <npz>
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import calib_per_dim_conformal as pdm  # noqa: E402  (sibling probe, path set above)
import calib_v5_synthesis as syn  # noqa: E402
import org_record_rank_probe as orp  # noqa: E402

HOUR_OF_DAY = 5
N_BUSIEST = 8


def main(npz: Path) -> None:
    """Print the Hour-of-day breakdown for one world."""
    pdm.hour_gap_rate = lambda v, a1: np.full(len(v.agent), np.inf)  # option not used here
    v = pdm.load_vectors(npz)
    st1 = pdm.stage1(v)
    arms, _ = orp.build_arms(v, st1, syn.stage1_variant(v, st1, "days"))
    q_o1, w5 = arms["O1"]
    w, _ = syn.day_groups(npz)
    d = HOUR_OF_DAY
    day_q = syn.day_min(w, np.r_[q_o1[:, d] / w5[d], np.full(w.n_msgs, np.inf)])
    benign = (w.label != 2) & (w.day >= 90)
    tag_names = w.meta.get("tags") or w.meta.get("tag_names") or []
    for line in (0.01, syn.STATED[3]):
        hot = benign & (day_q <= line)
        days, cnt = np.unique(w.day[hot], return_counts=True)
        top = np.argsort(-cnt)[:N_BUSIEST]
        print(
            f"line q<={line:.4f}: {int(hot.sum())} of {int(benign.sum())} benign agent-days; "
            f"ordinary {int((hot & (w.label == 0)).sum())}, "
            f"change {int((hot & (w.label == 1)).sum())}"
        )
        print("  busiest days:", [(int(days[i]), int(cnt[i])) for i in top])
        tags: dict[str, int] = {}
        for x in w.tags[hot & (w.label == 1)]:
            for b, name in enumerate(tag_names):
                if int(x) >> b & 1:
                    tags[name] = tags.get(name, 0) + 1
        print("  change tags:", dict(sorted(tags.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
