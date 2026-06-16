"""Tests for reading connected MCP servers from ~/.claude.json."""

import json

from mcp_security.scanner.config_reader import (
    ConnectionSpec,
    infer_kind,
    read_configured_servers,
    spec_from_root,
)


def _write_claude_json(tmp_path, data):
    path = tmp_path / ".claude.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_reads_global_and_project_servers(tmp_path):
    cfg = _write_claude_json(
        tmp_path,
        {
            "mcpServers": {
                "fs": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/data/corp"],
                }
            },
            "projects": {
                "/home/u/proj": {
                    "mcpServers": {
                        "slurm": {"command": "python", "args": ["/x/server.py"]}
                    }
                }
            },
        },
    )
    specs = read_configured_servers(claude_json=cfg)
    by_name = {s.name: s for s in specs}
    assert set(by_name) == {"fs", "slurm"}
    assert by_name["fs"].scope == "global"
    assert by_name["slurm"].scope == "/home/u/proj"


def test_filesystem_roots_extracted_from_args(tmp_path):
    cfg = _write_claude_json(
        tmp_path,
        {
            "mcpServers": {
                "fs": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/data/a", "/data/b"],
                }
            }
        },
    )
    (spec,) = read_configured_servers(claude_json=cfg)
    assert spec.kind == "filesystem"
    assert spec.roots == ("/data/a", "/data/b")


def test_env_values_redacted_to_key_names(tmp_path):
    cfg = _write_claude_json(
        tmp_path,
        {
            "mcpServers": {
                "gh": {
                    "command": "docker",
                    "args": ["run", "ghcr.io/github/github-mcp-server"],
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "secret-value-123"},
                }
            }
        },
    )
    (spec,) = read_configured_servers(claude_json=cfg)
    assert spec.env_keys == ("GITHUB_PERSONAL_ACCESS_TOKEN",)
    # The secret value must appear nowhere on the spec.
    assert "secret-value-123" not in repr(spec)


def test_transport_inferred_for_url_server(tmp_path):
    cfg = _write_claude_json(
        tmp_path,
        {"mcpServers": {"remote": {"url": "https://example.com/sse"}}},
    )
    (spec,) = read_configured_servers(claude_json=cfg)
    assert spec.transport in {"sse", "http"}
    assert spec.url == "https://example.com/sse"


def test_missing_file_returns_empty(tmp_path):
    assert read_configured_servers(claude_json=tmp_path / "nope.json") == []


def test_infer_kind_matrix():
    assert infer_kind("@modelcontextprotocol/server-filesystem", ()) == "filesystem"
    assert infer_kind("mcp-server-sqlite", ()) == "sqlite"
    assert infer_kind("@modelcontextprotocol/server-slack", ()) == "slack"
    assert infer_kind("github/github-mcp-server", ()) == "github"
    assert infer_kind("some-random-thing", ()) == "other"


def test_spec_from_root_is_filesystem():
    spec = spec_from_root("/tmp/store")
    assert isinstance(spec, ConnectionSpec)
    assert spec.kind == "filesystem"
    assert spec.roots == ("/tmp/store",)
    assert spec.scope == "cli"
