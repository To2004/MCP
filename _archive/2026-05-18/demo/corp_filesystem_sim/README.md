# Demo Corporate Filesystem

A small fake corporate file tree, served by the official Anthropic filesystem
MCP server. Used as a target for misuse cases (recon, exfil, tampering) in
later phases of the risk-scoring framework.

**Everything in this tree is fake.** No real organization names, no real
product names, no real credentials. PDFs and DOCX files are stub bytes —
they are not valid documents and are only there to exercise file-extension
handling.

## Layout

```
sensitive/         # high-tier (folder name is a human hint, not a score)
  contracts/
  financials/
  security/
source_code/       # high — stub code with placeholder API keys
projects/          # mid
onboarding/        # low
public/            # low
```

Folder names hint at sensitivity for human readers. They are NOT consumed by
any scoring code in this phase. Severity scoring is a follow-up.

## Run the MCP server

Direct stdio (e.g., for Claude Desktop):

```bash
npx -y @modelcontextprotocol/server-filesystem ./demo/corp_filesystem
```

Behind the existing `mcp-proxy` (matches the calendar pattern; logs flow to
`logs/proxy/`):

```bash
mcp-proxy --port 8080 -- npx -y @modelcontextprotocol/server-filesystem ./demo/corp_filesystem
```

The positional directory argument is the **only** path the server allows
operations against — calls outside it return an "outside allowed directory"
error.

Full runbook: [../../docs/guides/run-corp-filesystem-demo.md](../../docs/guides/run-corp-filesystem-demo.md).

## Regenerate the tree

```bash
python scripts/build_corp_demo.py
```

Idempotent. Source of truth is the `FILES` dict in that script. Fourteen
small files spanning `.c`, `.exe`, `.pdf`, `.docx`, `.xlsx`, `.png`, `.csv`,
`.sql`, `.pem`, and `.txt` — at most two files per folder, kept minimal so
the tree is easy to scan.

## Smoke-test the server

```bash
python scripts/smoke_corp_demo.py
```

Spawns the MCP server, runs `initialize` + `tools/list` + `list_directory`,
and prints the result. Use this to confirm `npx`, the package, and the
sandbox argument are all working before connecting a real client.
