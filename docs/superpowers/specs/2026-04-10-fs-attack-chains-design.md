# Filesystem MCP Attack Chains — Design Spec

Date: 2026-04-10
Target: `@modelcontextprotocol/server-filesystem` — two versions side-by-side
Output: `tests/testbed/excel_reports/fs_attack_chains.xlsx`

## 1. Goal

Run an aggressive, research-driven attack campaign against **both** the pinned
filesystem MCP server (v2025.3.28, known-vulnerable to CVE-2025-53109 and
CVE-2025-53110) and the latest version (v2025.7.29, patched). The campaign
uses only `read_file` and `list_directory`. The mission is to find real
bugs — with a primary bias toward finding bugs in the **patched** version,
where blind CVE replays are already dead and progress requires understanding
the patch.

Unlike the existing `generate_fs_research.py` probe sweep (which catalogs
how servers respond), this campaign is a white-hat pentest engagement:
multi-step attack chains driven by hypotheses about where patches typically
miss.

## 2. Scope

### In scope

- Tools: `read_file`, `list_directory` only.
- Targets: both server versions running against dedicated sandbox roots.
- Attack surface: path parsing, allow-list check, `realpath`/`normalize`
  ordering, symlink resolution, hardlink handling, Unicode normalization,
  null-byte / control-char handling, type confusion at the JSON-RPC layer,
  TOCTOU races, procfs pivots, resource exhaustion.
- Output: single multi-sheet Excel report plus a raw JSONL audit log plus
  a source-analysis notes file.

### Out of scope

- Other tools (`write_file`, `edit_file`, `move_file`, etc.) — excluded by
  user direction.
- Any write, delete, or mutation against real host state outside `/tmp`.
- Network-based attacks.
- Any attack surface outside the two tools above.

## 3. Methodology

The campaign is organized as six phases, each feeding the next.

### Phase 0 — Source analysis

Read `index.js` of both versions directly. Extract and document:

- Path validation function(s) and their call sequence.
- Where and how `realpath` is invoked.
- Where and how `normalize` is invoked (before or after `realpath`).
- Allow-list check — exact-match vs prefix-match vs `startsWith`.
- Symlink handling.
- Error message construction (what gets echoed back to the client).

Deliverable: `fs_attack_chains.source_notes.md` — a short gap analysis per
version. Every later payload is aimed at a specific gap identified here.

### Phase 1 — Recon and fingerprinting

Roughly ten legitimate-looking requests whose *errors* leak information:

- Node version, runtime identifiers.
- Canonical sandbox path (e.g. `/tmp` vs `/private/tmp`, or trailing-slash
  variants).
- Allow-list contents if leaked in errors.
- Error-message shape and which fields echo the input.

Leaked values are captured and used as input for later phases.

### Phase 2 — Primitive discovery

Roughly fifteen atomic, single-question probes. Each one answers exactly
one question and is a building block for later chains:

- Does the server follow an externally-planted symlink?
- Is the allow-list check `startsWith` without a trailing-slash?
- Does `normalize` run before or after `realpath`?
- Does the server open hardlinks?
- Does path handling truncate at `\0`?
- Does the server honor NFC vs NFD normalization?
- Is `realpath` cached across calls?
- Are relative paths normalized against the allowed dir or against cwd?

### Phase 3 — Attack chains

Ten to fifteen multi-step attack chains. Each chain is a narrative: set up
filesystem state with shell operations, call the server tool(s), observe,
potentially set up more state, call again. Planned chains:

| ID  | Name                        | Hypothesis                                                                                  |
| --- | --------------------------- | ------------------------------------------------------------------------------------------- |
| C1  | Prefix confusion            | If allow-list uses `startsWith` without trailing slash, `/tmp/mcp_attack_328_evil/*` passes. |
| C2  | Symlink plant → read        | Baseline: `sandbox/link -> canary`. Does server follow it?                                  |
| C3  | Symlink chain               | A→B→C→canary. Does realpath walk the whole chain?                                           |
| C4  | Symlink loop DoS            | A→B→A. Hang or ELOOP?                                                                       |
| C5  | Dangling symlink info leak  | Broken symlink; does error echo the target?                                                 |
| C6  | Dir-symlink nested read     | `sandbox/etc -> /tmp/victim_328` then `read_file(sandbox/etc/passwd_canary)`.               |
| C7  | Parent-dir symlink          | Sandbox parent contains a symlink; does the server realpath the parent dir?                 |
| C8  | **Hardlink escape**         | Plant a hardlink inside the sandbox to a canary in `/tmp`. Realpath cannot detect hardlinks. |
| C9  | TOCTOU race                 | Rename-swap file↔symlink while hammering `read_file` from multiple threads.                 |
| C10 | Procfs pivot                | `/proc/self/root/...`, `/proc/self/cwd/...`, `/proc/1/root/...`.                           |
| C11 | Unicode normalization       | Plant a file with NFD filename; query with NFC (and vice versa).                            |
| C12 | Null-byte truncation        | `sandbox/ok.txt\x00/tmp/victim_328/passwd_canary`.                                          |
| C13 | CVE-53110 mutation family   | `....//`, `.....///`, `....\/`, `%2e%2e%2e%2e//`.                                           |
| C14 | Type confusion / JSON-RPC   | `path` as array/object/number/null, prototype-pollution keys, duplicate keys, 1 MB string.  |
| C15 | Resource exhaustion         | `/dev/zero` read (capped at 10 MB), FIFO read, symlink loop list, PATH_MAX-length path.     |

C8 is the chain most likely to find a real bug in v2025.7.29: the CVE-53109
patch addresses symlink resolution, but `realpath` returns the input path
unchanged for a hardlink (hardlinks have no separate target to resolve), so
a hardlink inside the sandbox to a file elsewhere on the same filesystem
should escape a realpath-only check.

### Phase 4 — Differential diff

Every input across every phase is sent to both versions. Any behavioral
divergence (error text, error code, success/failure flip, output size class)
becomes a row on the Diff sheet. Regressions in either direction are
interesting.

### Phase 5 — PoC hardening

For each confirmed Critical or High hit, the campaign distills a minimal
reproducible PoC entry: chain id, exact tool call, expected vs actual
output, and CVE reference if applicable.

## 4. Safety rules

The campaign runs on the user's actual development machine. It must not
touch anything outside `/tmp`.

- Two dedicated sandbox roots are created for this campaign:
  `/tmp/mcp_attack_328` and `/tmp/mcp_attack_729`. The existing
  `/tmp/mcp_sandbox` used by the old report is not touched.
- Escape targets are script-created canaries under `/tmp/victim_328`
  and `/tmp/victim_729`. The canary file contains the literal string
  `ATTACKER_CANARY_12345`; the hit scorer uses this string as the
  "escape succeeded" signal.
- Real system files (`/etc/passwd`, `/etc/shadow`, `~/.ssh/*`) are probed
  read-only for realism, but the win condition is always the canary — the
  campaign never depends on sensitive host content.
- No writes to `/etc`, `/root`, `/var`, `/home`, or the user's profile.
- No network activity.
- Fixture planting uses Python `os` calls (`os.symlink`, `os.link`,
  `os.mkfifo`, raw `bytes` filenames) — never a shell string.
- TOCTOU race (C9) is bounded by a 30-second hard ceiling with a
  `ThreadPoolExecutor` that is hard-killed at teardown.
- `/dev/zero` reads in C15 are capped client-side at 10 MB; beyond that
  the response is truncated and the row is flagged as High-severity DoS.
- Each server subprocess is spawned per-phase and killed in a `finally:`
  block. Total runtime budget: about 5 minutes per version, 10 minutes
  total. Per-request hard timeout: 15 seconds.

## 5. Code layout

New script: `tests/testbed/attack_fs_chains.py`, sibling of the existing
`generate_fs_research.py` and following the same style.

Top-to-bottom structure inside the single file:

1. Constants: server paths, sandbox roots, victim roots, output paths.
2. Source-analysis data: list of dicts hardcoded after reading `index.js`
   manually during Phase 0.
3. Fixture builder: functions that wipe and rebuild each sandbox with the
   exact state a given chain needs (files, symlinks of every variety,
   hardlinks, NFD-named files, FIFOs, null-byte-named files).
4. MCP client helper: spawns one stdio subprocess per version, sends
   `tools/call`, returns `{status, stdout, stderr, elapsed_ms}`. Reuses
   the pattern already established in `generate_fs_research.py`.
5. Hit scorer: pure function `(input, pinned_resp, latest_resp) ->
   (severity, reason, is_regression)`.
6. Chain definitions: 15 functions `c01_prefix_confusion()` through
   `c15_resource_dos()`, each returning a list of step dicts.
7. Phase runners: `recon_phase()`, `primitives_phase()`, `chains_phase()`,
   `diff_phase()`, `poc_phase()`.
8. Excel writer: openpyxl, one function per sheet, with red/yellow/blue
   severity fills.
9. `main()`: wipes fixtures, runs phases in order, writes workbook, prints
   a one-screen summary to stdout.

## 6. Excel layout

Single workbook: `tests/testbed/excel_reports/fs_attack_chains.xlsx`.

| Sheet              | Purpose                         | Key columns                                                                                                                                                                             |
| ------------------ | ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 01_Summary         | Executive summary               | chain_id, chain_name, hypothesis, result (PASS/FAIL/PARTIAL), severity, verdict, steps_count, hits_count                                                                                |
| 02_Source_Analysis | Phase 0 output                  | version, function, code_snippet, gap_identified, attack_idea                                                                                                                            |
| 03_Recon           | Phase 1 findings                | probe_id, input, pinned_output, latest_output, leaked_info, used_in_chain                                                                                                               |
| 04_Primitives      | Phase 2 atoms                   | primitive_id, question, input, pinned_answer, latest_answer, implication                                                                                                                |
| 05_Chain_Steps     | Main attack sheet               | step_id, chain_id, step_num, pre_setup, tool, input, pinned_status, pinned_output, latest_status, latest_output, hit?, severity, reason, is_regression                                  |
| 06_Diff            | Differential findings           | row_id, input, pinned_behavior, latest_behavior, diff_type (new_block / new_allow / error_change), severity                                                                             |
| 07_PoCs            | Minimal reproducible exploits   | poc_id, chain_id, version_affected, steps, expected_output, actual_output, cve_reference                                                                                                |
| 08_Raw             | Full audit trail                | one row per request/response, untrimmed                                                                                                                                                 |

Severity color fills: Critical red, High orange, Medium yellow, Low blue,
Info none.

## 7. Hit detection rules

Run on each step immediately after the response comes back:

| Rule                                                                                                                   | Severity |
| ---------------------------------------------------------------------------------------------------------------------- | -------- |
| Response contains the literal canary string `ATTACKER_CANARY_12345`                                                    | CRITICAL |
| Response contains `root:x:` (classic `/etc/passwd` marker)                                                             | CRITICAL |
| Response contains `ssh-rsa`, `BEGIN OPENSSH`, or `BEGIN RSA`                                                           | CRITICAL |
| Response contains `AWS_SECRET`, `API_KEY`, or `PASSWORD=`                                                              | CRITICAL |
| The path the server *actually read* — verified by the script calling `os.path.realpath` on the host — resolves outside `/tmp/mcp_attack_*` | CRITICAL |
| `list_directory` returned entries for a path that resolves outside sandbox                                             | CRITICAL |
| Connection closed, stderr contains stack trace, or response timeout exceeds 10 seconds                                 | HIGH     |
| Response larger than 5 MB (candidate `/dev/zero`-style DoS)                                                            | HIGH     |
| Error message contains an absolute host path that is not a substring of the input                                     | MEDIUM   |
| Error message contains Node version, internal function names, or `node_modules` path                                  | MEDIUM   |
| Pinned blocks but latest allows, or vice versa                                                                         | LOW (regression) |
| Clean result, no flags                                                                                                 | INFO     |

Higher severities win over lower ones if multiple rules match.

## 8. Outputs

- `tests/testbed/excel_reports/fs_attack_chains.xlsx` — the main report.
- `tests/testbed/excel_reports/fs_attack_chains.raw.jsonl` — one JSON
  object per request/response, for post-hoc audit.
- `tests/testbed/excel_reports/fs_attack_chains.source_notes.md` — Phase
  0 gap analysis.

## 9. Acceptance criteria

- Script runs end-to-end in under 10 minutes on the user's machine.
- Excel opens cleanly in Excel/LibreOffice with all eight sheets populated.
- At least one Critical or High hit is demonstrated on the pinned version
  (sanity check that the hit detector works, since the pinned version has
  documented CVEs).
- Every chain in Phase 3 has a verdict on the Summary sheet, even if the
  verdict is "no bug found".
- Raw JSONL audit log contains one line per actual MCP request issued.
- No file has been written outside `/tmp` during the run.
- No process from the campaign is still running after `main()` exits.
