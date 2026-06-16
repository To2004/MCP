"""Tests for ranking an asset inventory into the CBG table."""

import mcp_security.scanner.ranker as ranker_mod
from mcp_security.scanner.enumerator import AssetGroup, AssetInventory
from mcp_security.scanner.ranker import rank_inventory


def _fs_inventory(names):
    return AssetInventory(
        server="fs",
        kind="filesystem",
        assets=[AssetGroup(name=n, count=1) for n in names],
        source="enumerated",
    )


def test_known_extensions_reproduce_taxonomy_without_llm():
    inv = _fs_inventory([".sys", ".sql", ".txt", ".png"])
    rows = {r.name: r for r in rank_inventory(inv, use_llm=False)}
    assert rows[".sys"].risk_level == "Critical"
    assert rows[".sql"].risk_level == "High"
    assert rows[".txt"].risk_level == "Low"
    assert rows[".png"].risk_level == "Low"


def test_ranking_is_sorted_and_numbered():
    inv = _fs_inventory([".txt", ".sys", ".sql"])
    rows = rank_inventory(inv, use_llm=False)
    assert [r.name for r in rows] == [".sys", ".sql", ".txt"]
    assert [r.rank for r in rows] == [1, 2, 3]


def test_unanchored_extension_uses_llm(monkeypatch):
    # .pem is not in the taxonomy → must be ranked by the (mocked) local LLM.
    def fake_llm(kind, assets, context=""):
        return {a.name: {"risk": "Critical", "reason": "private key material"} for a in assets}

    monkeypatch.setattr(ranker_mod, "_llm_rank", fake_llm)
    inv = _fs_inventory([".pem"])
    (row,) = rank_inventory(inv, use_llm=True)
    assert row.name == ".pem"
    assert row.risk_level == "Critical"
    assert "private key" in row.reasoning


def test_llm_may_raise_but_not_lower_anchored(monkeypatch):
    # Anchor says .sql=High; LLM says Critical → raised. LLM says .sys=Low → kept Critical.
    def fake_llm(kind, assets, context=""):
        out = {}
        for a in assets:
            if a.name == ".sql":
                out[a.name] = {"risk": "Critical", "reason": "raised"}
            elif a.name == ".sys":
                out[a.name] = {"risk": "Low", "reason": "downgrade attempt"}
        return out

    monkeypatch.setattr(ranker_mod, "_llm_rank", fake_llm)
    rows = {r.name: r for r in rank_inventory(_fs_inventory([".sql", ".sys"]), use_llm=True)}
    assert rows[".sql"].risk_level == "Critical"  # raised
    assert rows[".sys"].risk_level == "Critical"  # not lowered


def test_sqlite_pii_column_anchor():
    inv = AssetInventory(
        server="db",
        kind="sqlite",
        assets=[
            AssetGroup(name="customers", tags=("column:email",)),
            AssetGroup(name="logins", tags=("column:password",)),
        ],
        source="enumerated",
    )
    rows = {r.name: r for r in rank_inventory(inv, use_llm=False)}
    assert rows["logins"].risk_level == "Critical"  # password → Critical
    assert rows["customers"].risk_level == "High"  # email → High


def test_generic_kind_anchors_via_extension_without_per_kind_code():
    # An unknown server kind: assets that reveal a filetype (by name or ext: tag)
    # are still anchored by the shared taxonomy; the rest fall to the LLM.
    inv = AssetInventory(
        server="mystery",
        kind="some-brand-new-kind",
        assets=[
            AssetGroup(name="report.pdf"),
            AssetGroup(name="dump.sql"),
            AssetGroup(name="notes", tags=("ext:txt",)),
        ],
        source="enumerated",
    )
    rows = {r.name: r for r in rank_inventory(inv, use_llm=False)}
    assert rows["dump.sql"].risk_level == "High"
    assert rows["report.pdf"].risk_level == "Medium"
    assert rows["notes"].risk_level == "Low"


def test_unknown_server_is_understood_from_context(monkeypatch):
    # A brand-new kind with no anchors: the understanding agent must receive the
    # server's self-description so it can rate assets it has never seen.
    seen = {}

    def fake_llm(kind, assets, context=""):
        seen["context"] = context
        return {a.name: {"risk": "High", "reason": "internal planning data"} for a in assets}

    monkeypatch.setattr(ranker_mod, "_llm_rank", fake_llm)
    inv = AssetInventory(
        server="jira",
        kind="other",
        assets=[AssetGroup(name="sprint-board"), AssetGroup(name="backlog")],
        source="enumerated",
        context="- list_issues: list all tracked issues\n- get_sprint: read sprint planning",
    )
    rows = {r.name: r for r in rank_inventory(inv, use_llm=True)}
    assert rows["sprint-board"].risk_level == "High"
    assert "get_sprint" in seen["context"]  # context threaded to the agent


def test_llm_down_falls_back_to_templated_reason(monkeypatch):
    monkeypatch.setattr(ranker_mod, "query_ollama", lambda *a, **k: None)
    inv = _fs_inventory([".pem"])
    (row,) = rank_inventory(inv, use_llm=True)
    assert row.risk_level == "Medium"
    assert "unranked" in row.reasoning
