from unittest.mock import AsyncMock, patch

from mcp_security.main import main


def test_import_and_run() -> None:
    with patch("mcp_security.main.demo", new_callable=AsyncMock):
        main()
    assert True

def test_ollama_extract_json_salvages_trailing_prose():
    from mcp_security.llm.ollama_client import _extract_json
    # Trailing prose after a valid object ("Extra data") is salvaged.
    assert _extract_json('{"a": 1} and here is why...') == {"a": 1}
    # Leading chatter + fenced JSON.
    assert _extract_json('```json\n{"b": 2}\n```') == {"b": 2}
    # Nested braces and strings with braces inside.
    assert _extract_json('prefix {"k": "v{x}", "n": {"m": 3}} tail')["n"] == {"m": 3}
    # Unrecoverable -> None.
    assert _extract_json("no json here") is None
