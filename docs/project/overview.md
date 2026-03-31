# Project Overview

## What Is MCP Security?

MCP Security is a defense-oriented risk scoring framework where the
**MCP server is the protected asset** and **AI agents are the threat source**.
The framework sits in front of the MCP server, scores incoming agent requests,
and enables the server to gate, throttle, or deny dangerous interactions
before they execute.

Existing risk frameworks were built for static software and human-driven
workflows. They don't account for the unique threats that autonomous AI agents
pose to MCP servers — agents that dynamically invoke tools, reuse context,
and trigger real-world actions. This project fills that gap by placing the
server's safety first.

## Threat Model

> **The server is always the victim; the agent is always the threat.**

All attacks in this project flow **client → server**: a malicious or
compromised AI agent (or the user behind it) sends harmful requests through
the MCP protocol to damage, exfiltrate from, or disrupt the server and its
resources.

The inverse scenario — a malicious server attacking the agent (e.g., tool
poisoning that tricks the agent) — is **out of scope**. When tool poisoning
is discussed, it is only to the extent that a poisoned agent subsequently
becomes a threat *to the server*.

## What the Framework Does

The framework produces a risk score for MCP tool interactions that incorporates
factors such as:

- **Agent autonomy level** — how independently the agent operates
- **Tool privilege scope and side effects** — what the tool can access or modify
- **Context persistence and reuse** — whether sensitive context carries across
  calls
- **Trust boundaries** — boundaries between agents and servers
- **Execution frequency and criticality** — how often and how critically the
  tool is invoked
- **Downstream blast radius** — how far damage can propagate from a single
  interaction

## Static vs. Dynamic Scoring

The score can be computed in two modes:

- **Static** — evaluated at design time, based on the tool's general properties
  (e.g., "file_write is inherently riskier than file_read")
- **Dynamic** — evaluated at runtime, based on the specific request/input. Two
  agents calling the same tool with different inputs may receive different risk
  scores (e.g., `rm -rf /` vs. `ls /tmp`)

## Key Design Decisions

- The framework is **not anomaly detection** — it does not flag deviations from
  known-good behavior. It defines what *makes* an interaction risky based on
  concrete factors.
- **Open question:** how much access to agent logs and request context is
  available at runtime, as this directly affects the richness of the dynamic
  score.

## Deliverables

- A threat model for MCP tool interactions
- A formal risk scoring model
- A proof-of-concept implementation
- An evaluation against representative MCP deployment scenarios

## Guiding Principles

- **Modular** — each component is a self-contained module with a clear public
  API
- **Testable** — all logic has corresponding tests; no untestable code
- **Readable** — code is written for humans first, optimized second
- **Minimal dependencies** — only add what is truly needed
- **Security-first** — the tools we build enforce good security practices, and
  so does our own code

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
