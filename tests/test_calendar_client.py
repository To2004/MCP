import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_list_tools_initializes_session_and_returns_tools():
    mock_tool = MagicMock()
    mock_tool.name = "list-calendars"
    mock_session = AsyncMock()
    mock_session.list_tools.return_value = MagicMock(tools=[mock_tool])

    with patch("mcp_security.calendar_client.sse_client") as mock_sse, \
         patch("mcp_security.calendar_client.ClientSession") as mock_cls:
        mock_sse.return_value.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
        mock_sse.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        from mcp_security.calendar_client import list_tools
        tools = await list_tools("http://localhost:8080/sse")

    mock_session.initialize.assert_called_once()
    mock_session.list_tools.assert_called_once()
    assert tools == [mock_tool]


@pytest.mark.asyncio
async def test_call_tool_passes_name_and_arguments():
    mock_content = MagicMock()
    mock_result = MagicMock(content=[mock_content])
    mock_session = AsyncMock()
    mock_session.call_tool.return_value = mock_result

    with patch("mcp_security.calendar_client.sse_client") as mock_sse, \
         patch("mcp_security.calendar_client.ClientSession") as mock_cls:
        mock_sse.return_value.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
        mock_sse.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        from mcp_security.calendar_client import call_tool
        result = await call_tool("list-calendars", {}, "http://localhost:8080/sse")

    mock_session.initialize.assert_called_once()
    mock_session.call_tool.assert_called_once_with("list-calendars", {})
    assert result == mock_result


@pytest.mark.asyncio
async def test_call_tool_defaults_arguments_to_empty_dict():
    mock_session = AsyncMock()
    mock_session.call_tool.return_value = MagicMock(content=[])

    with patch("mcp_security.calendar_client.sse_client") as mock_sse, \
         patch("mcp_security.calendar_client.ClientSession") as mock_cls:
        mock_sse.return_value.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
        mock_sse.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        from mcp_security.calendar_client import call_tool
        await call_tool("get-current-time", url="http://localhost:8080/sse")

    mock_session.call_tool.assert_called_once_with("get-current-time", {})
