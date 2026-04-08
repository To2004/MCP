"""Minimal FastMCP test server for CVE-2026-32871 SSRF testing (port 8765)."""

from fastmcp import FastMCP

mcp = FastMCP("fastmcp-test-server")


@mcp.tool()
def fetch_url(url: str) -> str:
    """Fetch the content of a URL. Vulnerable to SSRF (CVE-2026-32871)."""
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.read(4096).decode("utf-8", errors="replace")
    except Exception as exc:
        return f"Error fetching {url}: {exc}"


@mcp.tool()
def read_file(path: str) -> str:
    """Read a file from the server filesystem."""
    try:
        with open(path) as f:
            return f.read(4096)
    except Exception as exc:
        return f"Error reading {path}: {exc}"


@mcp.tool()
def echo(message: str) -> str:
    """Echo a message back."""
    return message


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8765)
