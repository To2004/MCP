import asyncio
from mcp_security.calendar_client import demo


def main() -> None:
    asyncio.run(demo())


if __name__ == "__main__":
    main()
