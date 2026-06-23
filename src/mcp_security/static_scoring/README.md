# static_scoring

Static (design-time) misuse scoring for MCP servers. Builds a per-server risk
table from the server's tool registry and asset classes **alone** — before any
request is seen — so a gateway can pre-rank which (tool, asset) combinations are
dangerous on this server.

This is the **static** half of the framework's two scoring modes (see
`docs/project/overview.md`); the runtime/**dynamic** score lives elsewhere and
adjusts these baselines per actual request.

## What it produces

One JSON table per server (same shape as
`reports/samples/payment_static_table.json`):

| Key | Meaning |
|-----|---------|
| `inferred_profile` | Domain inferred from the registry (what assets/reach mean here) |
| `tool_impact` | Per tool: 1 read-only · 2 recoverable · 3 destructive/irreversible |
| `asset_sensitivity` | Per asset class: 1–5 criticality |
| `blast_radius` | Per `tool|asset` pair: 0–4 reach |
| `cells` | `sensitivity × blast × likelihood(1.0) × impact` per (asset, tool) |
| `bands` | Each cell mapped to low/medium/high/critical (operational policy below) |
| `band_distribution` | Count of cells per band — the gate workload / risk pyramid |
| `baselines` | Expected behaviour per consuming app |
| `crosscheck_summary` | Judge pass: records scored, records flagged for review |

## Band policy — a gate calibration, not a raw threshold

The static score pins `likelihood = 1.0` (the design-time *upper bound* from
`docs/standards/scoring-reference.md`), so it's a **worst-case ceiling**. Banding
on the raw number alone makes ~10% of cells critical — and a gate that blocks all
of those would halt legitimate work. So bands are assigned the way a reviewer
would, to keep `critical` rare and actionable:

- **critical** — *only* the catastrophes you hard-gate: an irreversible action
  (impact 3 / Irreversibility ×3) destroying a **crown-jewel** asset
  (sensitivity 5 = regulated / PII / financial / secrets) at departmental-or-wider
  reach (blast ≥ 3). Cannot be reconstituted. ~1–2% of cells.
- **high** — serious but recoverable or sub-crown-jewel (any irreversible op on
  restricted business data, sensitivity ≥ 4). Watch/throttle, don't block.
- **medium / low** — routine; let through. **Confidentiality floor:** a read
  can't *destroy* anything, but reading a crown-jewel still leaks it — so a
  *narrow* read of a sensitivity-5 asset (a secret / PII / financial record) is
  **medium**, never low, and a *broad* read of sensitive data is **high** (mass
  exfiltration). Narrow reads of ordinary/internal data stay low, so normal work
  still flows. Reads never reach critical (they don't change state).

Result across the 7 demos: ~68% low, ~15% medium, ~16% high, **~1–2% critical**.
The critical cells are exactly `api_keys`/`.pem` destruction and patient-record /
invoice destruction; reading those secrets is medium-to-high, not low.

## Pipeline

```
registry → 0 infer domain ─┐
           1 tool impact    ├─ LLM (Qwen2.5/Ollama) per stage,
           2 asset sens.    │   each anchored to the inferred profile,
           3 blast radius    │   falling back to deterministic heuristics
           4 baselines      │   when the model is unreachable
           5 judge xcheck ──┘
                 │
              cells = sensitivity × blast × likelihood × impact → bands
```

The prompt templates are in `prompts.py`; the offline heuristics (tool
annotations + the shared `mcp_security.sensitivity` anchors, plus crown-jewel
name escalation) are in `fallback.py`. Any table built with a fallback in play
is flagged `model_reviewed=false` / `needs_human_review=true`.

**Stage 5 is a real independent reviewer.** The judge re-derives every primitive
from the same domain profile via the `JUDGE_*` prompts, and on disagreement its
value *overrides* the proposer's before the cells are computed. Every override is
recorded in `crosscheck_summary.disagreements`. Offline (no model) the judge
cannot run, so `judge_ran=false` and low-confidence proposals are flagged
instead. Model decoding is greedy + fixed-seed (`temperature=0`), so a given
registry produces a byte-identical table every run.

## take1 vs take2 — filesystem asset granularity

How a filesystem server's *assets* (the rows of its table) are defined:

- **take1 (default)** — assets are **file types** (`.txt`, `.pem`, `.sql`). Small
  and fast, and fine when the extension carries the risk (`.pem`, `.sql`). But it
  **discards the path**, so `patients/alice/medical_history.txt` is seen only as
  "`.txt`" — a patient record and a grocery list become the same asset. Medical/
  legal stores get under-scored.
- **take2 (`--take2`)** — assets are **individual files, identified by full path**
  (`patients/alice_johnson/medical_history.txt`). The model and the offline
  keyword fallback can see what each file *is* from its directory and name, so PHI
  and privileged files score correctly. Bigger matrix (every file × every tool).

sqlite and slack are already name-based (table / channel names), so `--take2`
only changes the filesystem demos.

## Usage

```bash
# Offline / deterministic (no GPU needed) — runs anywhere
python -m mcp_security.static_scoring --kind cbg_sqlite --no-llm
python -m mcp_security.static_scoring --kind medical_clinic_fs --take2 --no-llm

# Every demo server → one combined results file
python -m mcp_security.static_scoring --all --no-llm         # take1, offline
python -m mcp_security.static_scoring --all                  # take1, model-reviewed
python -m mcp_security.static_scoring --all --take2          # take2, model-reviewed
sbatch scripts/static_score_on_gpu.sbatch                    # --all on a GPU node

# Arbitrary server from a registry JSON file
python -m mcp_security.static_scoring --registry path/to/registry.json
```

Single-server output defaults to `reports/samples/<kind>[_take2]_static_table.json`;
the combined run writes `reports/samples/all_static_tables[_take2].json`. The
`version` field is tagged `static-take1-*` / `static-take2-*`.

## Registries

`registry.py` builds every registry from the project's own demo/simulation data,
so the tables reflect real servers rather than hand-typed input. `--all` scores
the full `DEMO_SERVERS` set:

| Demo | Kind | Assets from |
|------|------|-------------|
| `corp_filesystem`, `law_firm_fs`, `medical_clinic_fs`, `media_studio_fs` | filesystem | file types under each `demo/*` tree (one shared tool registry) |
| `cbg_sqlite`, `corp_sqlite` | sqlite | live db schema (tables + columns), read-only |
| `slack` | slack | `demo/slack_mcp` channels (privacy + category); **no destructive tools** |

The original two canonical servers:

- **filesystem** — tools from the captured proxy registry
  (`logs/proxy/parsed/tools_catalog.csv`, `secure-filesystem-server`), asset
  classes from the file types in `demo/corp_filesystem`.
- **sqlite** — the five tools of `logs/proxy/servers/mcp_cbg_sqlite_server.py`,
  asset classes from the live `demo/cbg_sqlite/cbg.db` schema (read-only).
