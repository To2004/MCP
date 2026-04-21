import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

PROXY_URL = "http://localhost:8080/sse"


async def list_tools(url: str = PROXY_URL) -> list:
    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return result.tools


async def call_tool(name: str, arguments: dict | None = None, url: str = PROXY_URL):
    if arguments is None:
        arguments = {}
    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(name, arguments)


async def demo(url: str = PROXY_URL) -> None:
    print(f"Connecting to {url} ...")

    tools = await list_tools(url)
    print(f"\nAvailable tools ({len(tools)}):")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")

    print("\nCalling list-calendars ...")
    result = await call_tool("list-calendars", url=url)
    for item in result.content:
        print(f"  {item}")

    print("\nCalling get-current-time ...")
    result = await call_tool("get-current-time", url=url)
    for item in result.content:
        print(f"  {item}")
