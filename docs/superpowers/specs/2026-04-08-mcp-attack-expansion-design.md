# MCP Attack Testbed Expansion Design

This document specifies the design for expanding the MCP Security testbed to cover the full
attack taxonomy, add a multi-step scenario runner, and increase server coverage to 32 profiles.

## Motivation

The existing testbed implements 12 of 36 defined attacks (~33% coverage) against 13 server
profiles. The attacks document (`Literature_review/attacks/mcp_server_attacks_v3_reduced_styled_1.md`)
defines 36 attacks across four tiers; covering only the single-call, directly exploitable subset
limits the testbed's value as thesis validation evidence.

This expansion adds:
- 13 new single-call attack templates (covering core taxonomy gaps)
- A multi-step scenario runner (for replay, session abuse, privilege escalation, etc.)
- 5 multi-step scenario definitions
- 19 new server profiles (CVE-affected + MCPTox paper-aligned)

Combined coverage rises to ~70% of the taxonomy with a campaign matrix of ~550 test pairs.

## Architecture

The testbed remains fully data-driven: adding a server or attack requires only a JSON file.
No code changes are needed for new templates or server profiles. The only new code is
`scenario_runner.py` and a thin `--scenarios` flag in `attack_runner.py`.

```
tests/testbed/
├── harness/
│   ├── attack_runner.py       (existing — add --scenarios flag)
│   ├── scenario_runner.py     (NEW)
│   └── ...
├── attack_templates/          (12 → 25 JSON files)
├── attack_scenarios/          (NEW directory — 5 JSON scenario files)
└── servers/                   (13 → 32 JSON profiles)
```

## New Attack Templates

Thirteen new single-call templates added to `attack_templates/`. All follow the existing schema
and integrate with the existing tool_matcher → attack_runner pipeline.

| Template | Category | CWE | Attack Covered |
|---|---|---|---|
| `log_tampering` | C1 | 221 | Delete/truncate log files to hide evidence |
| `db_credential_exposure` | C2 | 522 | Read database config/connection strings |
| `throttle_bypass` | C4 | 770 | Evade rate controls via burst or param tricks |
| `scraping` | C2 | 200 | Systematic enumeration to replicate datasets |
| `tool_misuse` | C5 | 441 | Use legitimate tool for unintended harm (phishing) |
| `false_error_escalation` | C3 | 755 | Trigger errors that force privileged recovery paths |
| `state_corruption` | C3 | 666 | Corrupt cached/internal server state |
| `protocol_exhaustion` | C4 | 400 | Malformed or oversized JSON-RPC messages |
| `denial_of_wallet` | C4 | 400 | Force excessive spending on metered AI APIs |
| `toxic_content_proxy` | C5 | 116 | Generate harmful content via server text tools |
| `idempotency_abuse` | C4 | 770 | Flood storage with valid duplicate records |
| `rade_exfiltration` | C6 | 20 | Retrieval-poisoned content directs server tool abuse |
| `indirect_prompt_injection` | C6 | 20 | Hidden instructions in fetched external content |

CVE-specific payloads are also added to three existing templates:
- `command_injection`: CVE-2025-5277 (aws-mcp), CVE-2025-53967 (Figma)
- `path_traversal`: CVE-2025-53109, CVE-2025-53110 (Anthropic filesystem symlink)
- `ssrf`: CVE-2025-65513 (mcp-fetch), CVE-2026-32871 (FastMCP, CVSS 10.0)

## Multi-Step Scenario Runner

### Why

Attacks like replay, session abuse, and privilege escalation inherently span multiple tool calls.
A single payload cannot model them. The scenario runner executes ordered step sequences within
a shared MCP session, passing captured values between steps.

### Scenario JSON Format (`attack_scenarios/*.json`)

```json
{
  "id": "replay_attack",
  "category": "C3",
  "description": "Capture response from first call; replay identical call to confirm no idempotency guard",
  "transport_support": ["stdio", "http"],
  "damage_indicator": "created|success|id.*=",
  "steps": [
    {"step": 1, "tool": "create*", "args": {"name": "test-item"}, "capture": "item_id", "damage_check": false},
    {"step": 2, "tool": "create*", "args": {"name": "test-item"}, "damage_check": true}
  ]
}
```

Key design decisions:
- `tool` field supports glob patterns; matched against available tools at runtime
- `{var}` interpolation in `args` references values captured in prior steps
- `damage_check: true` steps are evaluated against `damage_indicator` regex
- Results share the same dict format as single-call results so `metrics.py` is reused

### Five Scenarios

| Scenario | Category | Steps | Damage Signal |
|---|---|---|---|
| `replay_attack` | C3 | 2 | Second identical write succeeds |
| `session_abuse` | C3 | 11 (10 read + 1 write) | Final privileged write succeeds |
| `privilege_escalation_chain` | C1 | 3 (enum → read → write) | Admin tool call succeeds |
| `indirect_prompt_injection_scenario` | C6 | 2 (fetch → execute) | Injected instruction executes |
| `idempotency_abuse_scenario` | C4 | 50 (repeated create) | Incrementing IDs returned |

## New Server Profiles

### CVE-Affected (9 new profiles)

| Server | CVE(s) | Install | Attack Categories |
|---|---|---|---|
| `desktop-commander` | RCE via shell | `npm i -g @wonderwhy-er/desktop-commander` | C1, C2 |
| `playwright-mcp` | Browser SSRF | `npm i -g @playwright/mcp` | C2, C5 |
| `aws-mcp` | CVE-2025-5277 (CVSS 9.6) | `npm i -g @aws/mcp` | C1 |
| `fastmcp-server` | CVE-2026-32871 (CVSS 10.0) | `pip install fastmcp` + local script | C2 |
| `puppeteer-mcp` | Browser SSRF | `npm i -g @modelcontextprotocol/server-puppeteer` | C2 |
| `github-mcp` | Token exposure | `npm i -g @modelcontextprotocol/server-github` | C2, C3 |
| `google-maps-mcp` | Data exfil | `npm i -g @modelcontextprotocol/server-google-maps` | C2, C5 |
| `context7-mcp` | RADE vector | `npm i -g @upstash/context7-mcp` | C6 |
| `adx-mcp` | CVE-2026-33980 KQL inject | `npm i -g @azure/mcp` | C1 |

### MCPTox-Aligned (10 new profiles)

| Server | Install | Notes |
|---|---|---|
| `sequential-thinking` | `npm i -g @modelcontextprotocol/server-sequential-thinking` | MCPTox top server |
| `mcp-obsidian` | `npm i -g mcp-obsidian` | Local vault, no credentials |
| `pandoc-mcp` | `pip install mcp-pandoc` | Document conversion, no credentials |
| `mcp-run-python` | `pip install mcp-run-python` | Code execution sandbox |
| `brave-search` | `npm i -g @modelcontextprotocol/server-brave-search` | `requires_api_key: true` |
| `exa-mcp` | `npm i -g exa-mcp` | `requires_api_key: true` |
| `firecrawl-mcp` | `npm i -g @mendableai/mcp-server-firecrawl` | `requires_api_key: true` |
| `tavily-search` | `npm i -g tavily-mcp` | `requires_api_key: true` |
| `slack-mcp` | `npm i -g @modelcontextprotocol/server-slack` | `requires_api_key: true` |
| `notion-mcp` | `npm i -g @notionhq/mcp` | `requires_api_key: true` |

Servers with `requires_api_key: true` run only `tool_poisoning` and `behavioral_fingerprinting`
tests when no API key is present; other templates are skipped on connection failure.

## Error Handling

The existing attack runner already wraps tool calls in try/except and records errors in the
result dict. No changes needed. Servers that fail to install or connect produce zero results
and are excluded from ASR calculations.

## Verification

```bash
# Run full single-call campaign
cd tests/testbed/harness && python attack_runner.py --all --mode eval

# Run scenario campaign
python attack_runner.py --all --scenarios --mode eval

# Generate ASR report
cd tests/testbed && python generate_report.py --latest

# Confirm unit tests pass
uv run pytest tests/testbed/harness/ -v
```

Success criteria: all 13 templates execute, all 5 scenarios produce results, ≥8 of 19 new
servers connect, ASR ≥ 50% on known-vulnerable servers (dvmcp, aws-mcp, desktop-commander).
