"""Real MCP filesystem server.

Exposes tools to read files, list directories, and get file metadata.
This is a real server — it performs actual filesystem operations.

IMPORTANT: stdout is reserved for JSON-RPC protocol messages.
All logging goes to stderr. Never use print() in this file.
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SERVER_NAME = "filesystem-server"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Logging — must go to stderr, stdout is for JSON-RPC only
# ---------------------------------------------------------------------------

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(SERVER_NAME)

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(SERVER_NAME)


def _resolve_safe_path(path_str: str) -> Path:
    """Resolve a path and ensure it stays within the project root.

    Raises:
        ValueError: If the resolved path escapes the project root.
    """
    resolved = (PROJECT_ROOT / path_str).resolve()
    if not str(resolved).startswith(str(PROJECT_ROOT)):
        raise ValueError(f"Access denied: path '{path_str}' is outside the project root")
    return resolved


@mcp.tool()
def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: Relative path from the project root (e.g. "pyproject.toml").
    """
    logger.info(f"read_file called with path={path!r}")
    file_path = _resolve_safe_path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Not a file: {path}")
    return file_path.read_text(encoding="utf-8")


@mcp.tool()
def list_directory(path: str) -> str:
    """List the contents of a directory.

    Args:
        path: Relative path from the project root (e.g. "src/mcp_security").
    """
    logger.info(f"list_directory called with path={path!r}")
    dir_path = _resolve_safe_path(path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")

    entries: list[str] = []
    for entry in sorted(dir_path.iterdir()):
        kind = "[DIR] " if entry.is_dir() else "[FILE]"
        entries.append(f"  {kind} {entry.name}")
    return "\n".join(entries) if entries else "(empty directory)"


@mcp.tool()
def get_file_info(path: str) -> str:
    """Get metadata about a file (size, last modified).

    Args:
        path: Relative path from the project root (e.g. "README.md").
    """
    logger.info(f"get_file_info called with path={path!r}")
    file_path = _resolve_safe_path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    stat = file_path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
    kind = "directory" if file_path.is_dir() else "file"

    return (
        f"name: {file_path.name}\n"
        f"type: {kind}\n"
        f"size: {stat.st_size} bytes\n"
        f"modified: {modified:%Y-%m-%d %H:%M:%S UTC}"
    )


# ---------------------------------------------------------------------------
# Entry point — run with: uv run python mcp_learning_lab/filesystem_server.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info(f"Starting {SERVER_NAME}, project root: {PROJECT_ROOT}")
    mcp.run(transport="stdio")
