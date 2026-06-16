"""Tests for the web/theorise resolver for unreachable servers."""

import mcp_security.scanner.resolver as resolver_mod
from mcp_security.scanner.config_reader import ConnectionSpec
from mcp_security.scanner.resolver import resolve, resolve_via_web, theorise


def _spec():
    return ConnectionSpec(
        name="slack",
        kind="slack",
        transport="stdio",
        command="npx",
        args=("-y", "@modelcontextprotocol/server-slack"),
    )


def test_web_hit_yields_source_web(monkeypatch):
    monkeypatch.setattr(
        resolver_mod, "query_ollama", lambda *a, **k: {"assets": ["#general", "#private"]}
    )
    inv = resolve_via_web(_spec(), fetcher=lambda ident: "README: lists channels and users")
    assert inv.source == "web"
    assert {a.name for a in inv.assets} == {"#general", "#private"}


def test_web_empty_doc_returns_no_assets(monkeypatch):
    monkeypatch.setattr(resolver_mod, "query_ollama", lambda *a, **k: {"assets": ["x"]})
    inv = resolve_via_web(_spec(), fetcher=lambda ident: None)
    assert inv.source == "web"
    assert inv.is_empty


def test_theorise_yields_source_theorised(monkeypatch):
    monkeypatch.setattr(resolver_mod, "query_ollama", lambda *a, **k: {"assets": ["channels"]})
    inv = theorise(_spec())
    assert inv.source == "theorised"
    assert [a.name for a in inv.assets] == ["channels"]


def test_resolve_falls_through_web_to_theorise(monkeypatch):
    calls = {"web": 0, "theorise": 0}

    def fake_llm(prompt, *a, **k):
        if "THEORISE" in prompt:
            calls["theorise"] += 1
            return {"assets": ["guessed"]}
        calls["web"] += 1
        return {"assets": []}  # web finds nothing

    monkeypatch.setattr(resolver_mod, "query_ollama", fake_llm)
    inv = resolve(_spec(), fetcher=lambda ident: "some doc")
    assert inv.source == "theorised"
    assert [a.name for a in inv.assets] == ["guessed"]


def test_fetcher_exception_does_not_raise(monkeypatch):
    monkeypatch.setattr(resolver_mod, "query_ollama", lambda *a, **k: {"assets": ["t"]})

    def boom(ident):
        raise RuntimeError("network down")

    inv = resolve_via_web(_spec(), fetcher=boom)
    assert inv.is_empty  # degraded, no crash
