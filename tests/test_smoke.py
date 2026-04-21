from unittest.mock import AsyncMock, patch

from mcp_security.main import main


def test_import_and_run() -> None:
    with patch("mcp_security.main.demo", new_callable=AsyncMock):
        main()
    assert True