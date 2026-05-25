"""Tests for the shared rule base types and atomic-op identifiers."""

from mcp_security.atomic_ops.rules_base import ATOMIC_OPS, Confidence, RuleHit


def test_atomic_ops_contains_all_thirteen():
    expected = {
        "EXECUTE",
        "DELETE",
        "OVERWRITE",
        "SCHEMA_MODIFY",
        "BROADCAST",
        "WRITE",
        "MODIFY",
        "MOVE",
        "CREATE",
        "READ",
        "SEARCH",
        "METADATA",
        "LIST",
    }
    assert expected.issubset(ATOMIC_OPS)


def test_rulehit_holds_required_fields():
    hit = RuleHit(
        rule_id="readme.execute.shell_keyword",
        atomic_op="EXECUTE",
        confidence=Confidence.HIGH,
        matched_on="execute shell command",
    )
    assert hit.atomic_op == "EXECUTE"
    assert hit.confidence is Confidence.HIGH
    assert "shell" in hit.matched_on


def test_confidence_values():
    assert Confidence.HIGH.value == "high"
    assert Confidence.MEDIUM.value == "medium"
    assert Confidence.LOW.value == "low"
