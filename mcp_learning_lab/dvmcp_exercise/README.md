# DVMCP Attack Demo Exercise

A single end-to-end attack demo against **Damn Vulnerable MCP (DVMCP)**,
a deliberately insecure MCP server. The goal is *not* to build anything
reusable — it is to make one agent→server attack concrete before scoping
the thesis evaluation chapter.

## Why This Exercise

Four decisions about the thesis hinge on knowing what a real MCP attack
actually looks like:

| Decision | What this exercise reveals |
|----------|----------------------------|
| How many attack demos to include (3–5 vs. skip) | Real effort cost of one demo |
| What the dynamic scoring model can observe | Which server-side signals exist during an attack |
| How to ground the taxonomy's Bypass/Abuse tiers | A concrete JSON-RPC example per category |
| Protocol fluency (async + JSON-RPC) | Watching real traffic, not reading specs |

## Deliverable

**One page** in [`attack_demo.md`](attack_demo.md) — the attack name,
the JSON-RPC request, the server response, observations, and a mapping
back to the thesis taxonomy. That page becomes a figure in the
evaluation chapter.

## What's Here

| File | Role |
|------|------|
| `README.md` | This file — why and what |
| `setup_notes.md` | Running log of install/run steps (append-only) |
| `attack_demo.md` | One-page writeup template for the attack |

## Suggested Flow

1. Locate DVMCP (GitHub) and read its README.
2. Install and run it locally — log each step in `setup_notes.md`.
3. Pick **one** documented vulnerability. Start with the simplest.
4. Connect with MCP Inspector or a small Python client.
5. Trigger the vulnerability. Capture the raw JSON-RPC request/response.
6. Fill in `attack_demo.md`.

## Out of Scope

- Building a custom vulnerable server (use DVMCP as-is).
- Automating multiple attacks.
- Writing detection logic (that comes later, in the scoring model).
- Any change to the main `src/mcp_security/` code.

## Safety

DVMCP is designed to be exploited in an isolated local environment.
Do **not** expose it on a public network. Run it on `localhost` only.
