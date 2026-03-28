# Project Overview

## What Is MCP Security?

MCP Security is a Python project focused on evaluating and ranking the severity
of AI agents that request access to Model Context Protocol (MCP) servers. The
goal is to build a risk scoring system that analyzes agent access requests and
classifies them by severity level, helping determine whether an agent should be
allowed, restricted, or denied access to MCP resources. The project is designed
to be clean, modular, and testable, and can be used standalone or integrated
into larger workflows.

## Guiding Principles

- **Modular** — each tool is a self-contained module with a clear public API
- **Testable** — all logic has corresponding tests; no untestable code
- **Readable** — code is written for humans first, optimized second
- **Minimal dependencies** — only add what is truly needed
- **Security-first** — the tools we build enforce good security practices, and so does our own code

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.12+ | Language |
| uv | Dependency management and virtual environments |
| pytest | Testing framework |
| Ruff | Linting and formatting |

## Repository Layout

```
src/mcp_security/     Main application code (installed as a package)
tests/                Automated tests (mirrors src/ structure)
docs/                 Documentation (you are here)
.claude/commands/     Reusable Claude Code command prompts
```

## Current Status

The project is in early development. The package skeleton is in place with a
stub entry point and a smoke test. See [Roadmap](roadmap.md) for what's planned.
