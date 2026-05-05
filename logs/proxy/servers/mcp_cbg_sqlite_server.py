"""CBG research-lab SQLite MCP server — FastMCP over Streamable HTTP.

Accepts the DB path as sys.argv[1] (defaults to demo/cbg_sqlite/cbg.db).
Tools:
  list_tables     — discover available tables
  describe_table  — column names and types for one table
  read_query      — run a SELECT statement (read-only enforced)
  write_query     — run INSERT / UPDATE / DELETE (DDL blocked)
  insert_row      — structured insert via a JSON dict
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DB_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("demo/cbg_sqlite/cbg.db")

mcp = FastMCP("cbg-sqlite", port=8097)


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@mcp.tool()
def list_tables() -> list[str]:
    """List all tables available in the CBG database."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    return [r["name"] for r in rows]


@mcp.tool()
def describe_table(table: str) -> list[dict]:
    """Return column names and types for a given table."""
    with _conn() as conn:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()  # noqa: S608
    if not rows:
        return [{"error": f"Table '{table}' not found"}]
    return [{"column": r["name"], "type": r["type"], "not_null": bool(r["notnull"]), "pk": bool(r["pk"])} for r in rows]


@mcp.tool()
def read_query(sql: str) -> list[dict] | dict:
    """Run a read-only SELECT query against the CBG database. Returns up to 100 rows."""
    stripped = sql.strip().upper()
    if not stripped.startswith("SELECT"):
        return {"error": "Only SELECT statements are allowed in read_query."}
    try:
        with _conn() as conn:
            rows = conn.execute(sql).fetchmany(100)
        return [dict(r) for r in rows]
    except sqlite3.Error as e:
        return {"error": str(e)}


@mcp.tool()
def write_query(sql: str) -> dict:
    """Run an INSERT, UPDATE, or DELETE query. DDL statements (DROP, ALTER, CREATE) are blocked."""
    stripped = sql.strip().upper()
    for blocked in ("DROP", "ALTER", "CREATE", "TRUNCATE", "PRAGMA"):
        if stripped.startswith(blocked):
            return {"error": f"DDL statement '{blocked}' is not permitted."}
    if not any(stripped.startswith(kw) for kw in ("INSERT", "UPDATE", "DELETE")):
        return {"error": "Only INSERT, UPDATE, or DELETE statements are allowed in write_query."}
    try:
        with _conn() as conn:
            cur = conn.execute(sql)
            conn.commit()
        return {"rows_affected": cur.rowcount, "status": "ok"}
    except sqlite3.Error as e:
        return {"error": str(e)}


@mcp.tool()
def insert_row(table: str, values: str) -> dict:
    """Insert a row into a table. Pass values as a JSON object string, e.g. '{"col": "val"}'."""
    try:
        data: dict = json.loads(values)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"  # noqa: S608
    try:
        with _conn() as conn:
            cur = conn.execute(sql, list(data.values()))
            conn.commit()
        return {"inserted_id": cur.lastrowid, "status": "ok"}
    except sqlite3.Error as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
