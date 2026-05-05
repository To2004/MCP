# Filesystem Simulation Design

Simulate 20 realistic filesystem operations from 6 org personas against a copy of `demo/corp_filesystem`, captured via the existing MITM proxy logging stack.

## Goal

Produce a logged session (`sessions/filesystem_sim/`) that shows normal day-to-day employee file access through the MCP filesystem server — reads, writes, directory listings, searches, moves — using the same wire-level capture format as all other proxy sessions.

## Architecture

```
run_filesystem_sim.py
  → mcp-proxy:8094  (npx @modelcontextprotocol/server-filesystem ./demo/corp_filesystem_sim)
  → mitmdump:9094   (reverse proxy, -s mitm_capture.py)
  → captured.jsonl  → calls.csv + calls_report.txt + raw_log.txt
```

Same pattern as POC A (`run_mitm_two_servers.py`). No new logging infrastructure needed — `mitm_capture.py` and `write_report()` are reused as-is.

## Filesystem Copy

- **Original (read-only):** `demo/corp_filesystem/` — never touched
- **Simulation working copy:** `demo/corp_filesystem_sim/` — created by the script on first run via `shutil.copytree`; overwritten each run so results are reproducible

## Personas and Calls

All 20 calls are category `VALID`. The server has real files to operate on, so all should return `OK`.

| # | Persona | Tool | Arguments |
|---|---------|------|-----------|
| 01 | Alice (HR) | `list_directory` | `onboarding/` |
| 02 | Alice (HR) | `read_file` | `onboarding/policies.pdf` |
| 03 | Alice (HR) | `get_file_info` | `onboarding/org_chart.png` |
| 04 | Bob (Dev) | `list_directory` | `source_code/` |
| 05 | Bob (Dev) | `read_file` | `source_code/core.c` |
| 06 | Bob (Dev) | `write_file` | `source_code/notes.txt` ← new file with sprint notes |
| 07 | Carol (Finance) | `list_directory` | `sensitive/financials/` |
| 08 | Carol (Finance) | `read_file` | `sensitive/financials/budget_2026.xlsx` |
| 09 | Carol (Finance) | `read_file` | `sensitive/financials/payslips_q1.csv` |
| 10 | Dave (Manager) | `read_file` | `projects/known_defects.csv` |
| 11 | Dave (Manager) | `search_files` | path=`.`, pattern=`*.pdf` |
| 12 | Dave (Manager) | `get_file_info` | `public/whitepaper.pdf` |
| 13 | Eve (Security) | `list_directory` | `sensitive/security/` |
| 14 | Eve (Security) | `read_file` | `sensitive/security/audit_log.txt` |
| 15 | Eve (Security) | `read_file` | `sensitive/contracts/nda_template.docx` |
| 16 | Frank (New hire) | `read_file` | `README.md` |
| 17 | Frank (New hire) | `list_directory` | `public/` |
| 18 | Frank (New hire) | `read_file` | `public/whitepaper.pdf` |
| 19 | Bob (Dev) | `create_directory` | `source_code/feature_branch/` |
| 20 | Bob (Dev) | `move_file` | `source_code/notes.txt` → `source_code/feature_branch/notes.txt` |

## Output

Session folder: `logs/proxy/sessions/filesystem_sim/`

| File | Contents |
|------|----------|
| `captured.jsonl` | Raw wire flows (one JSON per HTTP exchange) |
| `calls.csv` | Structured per-call log (timestamp, tool, args, status, elapsed) |
| `calls_report.txt` | Human-readable block report with summary table |
| `raw_log.txt` | Full pretty-printed HTTP flows |
| `mitmdump.log` | mitmdump process output |
| `wire.log` | mcp-proxy process output |

## New Files

| Path | Purpose |
|------|---------|
| `logs/proxy/scripts/run_filesystem_sim.py` | Simulation runner script |
| `demo/corp_filesystem_sim/` | Working copy of the org filesystem (gitignored) |
| `logs/proxy/sessions/filesystem_sim/` | Session output |

## Ports

| Service | Port |
|---------|------|
| mcp-proxy (filesystem server) | 8094 |
| mitmdump (capture) | 9094 |

Ports chosen to not collide with existing sessions (local=8092/9092, calendar=8093/9093).
