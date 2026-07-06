"""Tests for the influential-input highlight report's scoring logic."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_security.param_scoring.rubric import Cutoff, ParamRubric
from scripts.highlight_influential_inputs import _influence, _reachable_bands


def _param(**kw) -> ParamRubric:
    base = dict(name="amount", base_rank="low", extract="number", cutoffs=(), when_true=None, reasoning="")
    base.update(kw)
    return ParamRubric(**base)


def test_value_param_swings_low_to_critical():
    p = _param(cutoffs=(Cutoff(100, "low"), Cutoff(1000, "medium"), Cutoff(10000, "critical")))
    inf = _influence("payments", "transfer_funds", p)
    assert inf.top_band == "critical"
    assert inf.swing == 3
    assert inf.top_trigger == "value ≥ 10000"


def test_parsed_limit_unbounded_reaches_critical():
    p = _param(name="sql", extract="parsed_limit", cutoffs=(Cutoff(1000, "medium"),))
    inf = _influence("db", "read_query", p)
    assert inf.top_band == "critical"
    assert "unbounded" in inf.top_trigger


def test_list_length_trigger_uses_items_unit():
    p = _param(name="recipients", extract="list_length", cutoffs=(Cutoff(50, "critical"),))
    inf = _influence("cal", "send_email_invite", p)
    assert inf.top_trigger == "items ≥ 50"


def test_boolean_flag_reaches_when_true_band():
    p = _param(name="recursive", extract="boolean", when_true="high")
    bands = _reachable_bands(p)
    assert "high" in bands and "low" in bands
    inf = _influence("fs", "delete", p)
    assert inf.top_band == "high"
    assert inf.top_trigger == "flag set to true"
