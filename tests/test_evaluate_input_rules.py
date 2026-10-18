"""The separation measure used to grade input rules against labelled calls."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evaluate_input_rules import load_aliases, separation  # noqa: E402


def test_separation_is_an_auc_with_ties_counted_half():
    assert separation([5, 5], [1, 1]) == 1.0
    assert separation([1], [5]) == 0.0
    assert separation([3, 3], [3, 3]) == 0.5
    assert separation([4, 2], [3]) == 0.5
    assert separation([], [1]) is None


def test_aliases_cover_real_channel_and_calendar_ids():
    aliases = load_aliases()
    assert aliases  # the provisioning records exist and carry ids
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in aliases.items())
