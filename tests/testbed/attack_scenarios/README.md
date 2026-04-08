# Attack Scenarios

Multi-step scenarios exercise ordered sequences of MCP tool calls within a
shared session, letting later steps reference values captured from earlier
ones. They complement the single-shot attack templates by modeling realistic
multi-turn abuse patterns (session hijacking, privilege escalation chains, etc.).

## JSON Schema

Each scenario file is a JSON object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique scenario identifier (matches filename stem) |
| `category` | string | Attack category code (e.g. `C1`, `C3`, `C6`) |
| `description` | string | Human-readable description of the attack goal |
| `transport_support` | array of strings | Which transports to run on: `"stdio"`, `"http"` |
| `damage_indicator` | string or null | Regex applied to responses where `damage_check` is true |
| `steps` | array | Ordered list of step objects (see below) |

### Step object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `step` | integer | yes | Step number (used in result `payload_label` as `step_N`) |
| `tool` | string | yes | Glob pattern matched against available tool names (e.g. `read*`, `*admin*`) |
| `args` | object | yes | Arguments passed to the tool; values may contain `{var}` placeholders |
| `capture` | string | no | If present, stores `response_snippet[:300]` under this variable name for later steps |
| `damage_check` | boolean | no | If true, evaluates `damage_indicator` against this step's response (default: false) |

### Placeholder interpolation

String values in `args` may reference captured variables from prior steps:

```json
{"content": "prefix {captured_var} suffix"}
```

The runner replaces `{captured_var}` with the captured response snippet
before calling the tool.

## Running Scenarios

Run scenarios alongside regular attack templates:

```bash
python tests/testbed/harness/attack_runner.py --server <name> --scenarios --mode eval
```

Run with attack mode (no scoring) against all servers:

```bash
python tests/testbed/harness/attack_runner.py --all --scenarios --mode attack
```

## Adding a New Scenario

1. Create a new JSON file in this directory (use `snake_case.json`).
2. Follow the schema above. The `id` field should match the filename stem.
3. At least one step should have `"damage_check": true` to register findings.
4. The scenario is picked up automatically — no registration needed.
