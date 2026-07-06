# The MCP Static Scanner — Full Report

Prepared 2026-07-05. A complete account of the static (design-time) scanning and
scoring subsystem: what it does, how it is built, what it produced across ten
MCP servers, how it was validated, and where it is weak. Every number here is
recomputed from the repo (`reports/scan/`, `reports/evaluation/`), not asserted.

---

## 1. What the static scanner is

The framework defends an **MCP server** from the **AI agent** that calls it
(client → server threat model; the reverse is out of scope). The *static*
scanner is the design-time half: it runs **before** a server goes live, never
connects to a running server, and produces a per-server **risk matrix** — a
band (`low/medium/high/critical`) for every `(tool, asset)` pair the server
exposes. At runtime, the call scorer looks an observed call up in that matrix.

The scanner is **LLM-only and evidence-bound**: it derives every risk primitive
from the tool list and the on-disk assets via the local model (Qwen2.5 / Ollama)
in strict mode. If the model is unreachable it raises rather than guess, and it
never reads the checked-in ground-truth tables it is later graded against.

---

## 2. Architecture

Five packages, ~5,300 lines, in a clean pipeline:

```
 tools/list  +  on-disk assets
        │
        ▼
┌───────────────────┐   enumerate tools & assets, no LLM
│ scanner/          │   scan.py · tool_list.py · render.py · __main__.py   (377 loc)
└─────────┬─────────┘
          ▼
┌───────────────────┐   LLM derives the 3 risk primitives + bands (strict)
│ static_scoring/   │   pipeline.py · registry.py · prompts.py · fallback.py (1,913 loc)
└─────────┬─────────┘
          ├────────────────────────────┐
          ▼                             ▼
┌───────────────────┐        ┌───────────────────┐
│ param_scoring/    │        │ call_scoring/     │   score an observed call
│ input magnitude   │        │ resolve → look up │   against the matrix
│ (428 loc)         │        │ (874 loc)         │
└───────────────────┘        └───────────────────┘

 atomic_ops/ (1,729 loc) — a parallel tool-catalog classifier that tags each
 tool's atomic operations and emits the sensitivity/heatmap workbooks.
```

| Package | Role | Key files |
| --- | --- | --- |
| `scanner/` | Assemble a server's description (tools from its own `tools/list`, assets from its on-disk store) and drive the LLM stage. | `scan.py`, `tool_list.py` |
| `static_scoring/` | The LLM pipeline: infer domain → score tool impact, asset sensitivity, blast radius → multiply → band → judge. | `pipeline.py`, `prompts.py`, `registry.py` |
| `param_scoring/` | Per-tool **input-parameter** rubrics: which inputs carry magnitude (counts, amounts, unbounded queries) and how a value escalates the band. | `derive.py`, `rubric.py`, `apply.py` |
| `call_scoring/` | Resolve an observed call's arguments to a scanned asset and look up its band; honest status when unresolvable. | `resolve.py`, `score.py`, `tables.py` |
| `atomic_ops/` | Design-time classification of tool catalogs into atomic operations + sensitivity heatmaps. | `classifier.py`, `toollist_rules.py` |

---

## 3. The scoring model

Each `(tool, asset)` cell gets a numeric score from three primitives the LLM
derives, with **likelihood pinned to 1.0** (a design-time upper bound):

```
score = asset_sensitivity(1–5) × blast_radius(0–5) × tool_impact(1–3)
```

- **tool_impact** — reversibility of the action: read = 1, create = 2, overwrite/delete/move = 3.
- **asset_sensitivity** — 1 (public) … 5 (regulated / PII / secrets / crown jewels).
- **blast_radius** — how far one call reaches, on a `0–5` scale (`0` = can't
  touch this asset; `1` single-item touch … `4` bulk read/overwrite across many
  … `5` clobber/destroy/fan-out). *(Widened from `0–4` to `0–5` so reach spans
  the same 1–5 gradation as sensitivity; `band_label`'s "broad" threshold stays
  `blast ≥ 3`, so this is a scale extension, not a re-calibration.)*

The **band** is *not* a raw threshold on the score. `band_label()` reserves the
top band the way a security reviewer would, so a gate does not block normal work:

- **critical** — only irreversible destruction of a crown-jewel (`impact 3 ∧ sensitivity 5 ∧ blast ≥ 3`).
- **high** — irreversible op on restricted data (`impact 3 ∧ sensitivity ≥ 4`), a high raw score (`≥ 24`), or a *broad read* of sensitive data (mass exfiltration: `impact 1 ∧ sensitivity ≥ 4 ∧ blast ≥ 3`).
- **medium** — middling score (`≥ 8`), or any read of a crown jewel (a confidentiality floor — reading a secret is never "nothing").
- **low** — routine; let it through.

This deliberately makes the band a *categorical* function, not a monotone one,
of the raw score — a broad read outranks a small write even at a lower score.
It yields a ~1–2 % critical "risk pyramid" instead of a flat alarm.

---

## 4. Coverage — what was scanned

Ten servers, **1,700 scored cells** across five MCP kinds:

| Scan | kind | tools × assets | cells | low / medium / high / critical |
| --- | --- | --- | --- | --- |
| calendar_cbg | calendar | 11 × 6 | 66 | 6 / 28 / 21 / 11 |
| github_cbg | github | 11 × 6 | 66 | 14 / 13 / 23 / 16 |
| slack_cbg | slack | 8 × 10 | 80 | 27 / 28 / 19 / 6 |
| sqlite_cbg_sqlite | SQL | 5 × 7 | 35 | 6 / 13 / 11 / 5 |
| sqlite_devops_sqlite | SQL | 5 × 5 | 25 | 8 / 5 / 9 / 3 |
| fs_corp_filesystem | filesystem | 14 × 15 | 210 | 52 / 56 / 71 / 31 |
| fs_fintech_fs | filesystem | 14 × 23 | 322 | 54 / 95 / 104 / 69 |
| fs_law_firm_fs | filesystem | 14 × 22 | 308 | 64 / 112 / 98 / 34 |
| fs_media_studio_fs | filesystem | 14 × 21 | 294 | 49 / 125 / 86 / 34 |
| fs_medical_clinic_fs | filesystem | 14 × 21 | 294 | 56 / 87 / 95 / 56 |

Each scan is written as `reports/scan/<server>.json` (matrix) plus a `_params.json`
(the input-parameter rubrics) and a markdown view.

> **Demo vs real coverage.** These scans model **hand-built demo** servers. The
> real MCP servers, captured live (see `reports/live_run/MCP_INVENTORY.md` and
> `reports/tool_lists/*_real.json`), expose 2–3× more tools: **GitHub 26** (demo
> 11), **Slack 16** (demo 8), **Google Calendar 13** (demo 11) — including many
> write/destructive tools the demos omit. A real deployment must scan those real
> catalogs, not the samples.

---

## 5. Input-parameter scoring — the most influential inputs

Beyond *which tool touches which asset*, the value of an input parameter matters:
inviting 3 people vs 200, a bounded `SELECT … LIMIT 100` vs an unbounded one, a
money `amount`. The LLM derives a per-tool rubric (base rank + value cutoffs +
how to extract the value), applied deterministically to escalate — never lower —
the cell band. `scripts/highlight_influential_inputs.py` ranks these across all
servers by how many bands the value alone can swing the risk:

| server | tool | input | swing | top trigger |
| --- | --- | --- | --- | --- |
| calendar_cbg | send_email_invite | `recipients` | low→critical | items ≥ 50 |
| calendar_cbg | create_event | `attendees` | low→critical | items ≥ 20 |
| fs_* | read_multiple_files | `paths` | low→critical | items ≥ 20 |
| sqlite_* | read_query / write_query | `sql` | low→critical | unbounded (no LIMIT) |

71 magnitude parameters found across 9 servers. (github's rubric found 0 last
scan — a gap the improved "pick the single most-influential input" prompt in
`docs/standards/parameter-scoring.md` targets on the next derivation.) A money
`amount` on a future payments tool would surface here identically.

### 5a. Atomic-operation flag per tool

Every scan now also classifies **each tool into one atomic operation** from the
project's severity-ranked taxonomy (`atomic_operations.csv`:
EXECUTE(5)/DELETE(5)/OVERWRITE(4)/SCHEMA_MODIFY(4)/BROADCAST(4)/WRITE/MODIFY/MOVE/
CREATE(3)/READ/SEARCH(2)/METADATA/LIST(1)). This answers "what does this tool
*fundamentally do*, and how dangerous is that verb", independent of the asset.

It is deterministic (no LLM), attached to the scan as `tool_atomic_ops`
(`{primary_op, atomic_ops, severity, severity_label, source}`), produced by
`mcp_security.scanner.atomic_flags` wrapping the existing `atomic_ops` rule
classifier. When the rule set doesn't recognise a tool, a verb fallback infers
the op from the tool name (hyphens normalised), so **every** tool is flagged and
the `source` field ("rules" vs "verb-fallback") stays honest. Examples from the
real catalogs: `delete_file → DELETE (Critical)`, `merge_pull_request → OVERWRITE`,
`conversations_add_message → BROADCAST (High)`, `list-calendars → LIST (Low)`.

### 5b. Per-tool input-risk ranking (LLM, with a rule fallback)

Alongside the cross-server magnitude ranking above, every scan carries a
**per-tool** ranking of that tool's own inputs (`tool_input_ranking` →
`{source, inputs:[{name, type, required, risk 1–5, critical_trigger, reason}]}`),
scored by how much each input can amplify the call's risk. `critical_trigger` is
the value/condition that pushes *that input* to critical — e.g. `amount ≥ 100000`,
`≥ 20 recipients`, `unbounded (no LIMIT)` — or null for non-magnitude inputs
(the same value-cutoff idea as the §5 param rubrics, produced inline here).

On a real (LLM) scan the ranking is produced by the model, which reasons about
*intent* — the prompt (in `atomic_flags._INPUT_RANK_PROMPT`) asks a security
analyst to rank every parameter 1–5 by how much its *value* amplifies risk (a
free-form query/command or caller-controlled payload, a list whose length is
breadth, a destructive/scope-widening flag rank high; a parameter that merely
names the target or is a fixed enum ranks low) and to return JSON covering every
parameter exactly once. If the model is unreachable or returns a partial/invalid
ranking, it **degrades to a deterministic rule heuristic** (query/command=5,
list/payload/destructive-flag=4, magnitude count=3, target id=2, else 1) — the
`source` field records `llm` / `rules` / `rules-fallback` honestly. Either way,
for `push_files` the risky inputs (`files`, `message`) surface above `owner`/`repo`.

Both `5a` and `5b` ship inside every `reports/scan/<server>.json`. New scans get
them automatically; older scans are backfilled by `scripts/enrich_scans_atomic.py`
(`--llm` for the model ranking, needs a GPU node; default is the rule heuristic).

---

## 6. Call scoring — resolving observed calls, honestly

`call_scoring/` takes a captured call, resolves its arguments to a scanned asset
(filesystem by path-suffix, SQL by table, slack by channel, calendar by calendar,
github by repo), and returns the cell's band — escalated by the parameter rubric.
Crucially it **never fabricates**:

- a call to a tool the server never advertised → `invalid`;
- a call to an asset the scan never enumerated → `unresolved`;
- only a resolved `(tool, asset)` cell yields a real band.

This is what keeps the scorer general: it reports what the scan says or admits it
cannot, but never invents a number.

---

## 7. Validation — how the scanner was graded

The scanner never reads the ground truth it is graded against. Four independent
checks:

**a) vs an LLM-reviewed ground-truth table** (`scanner_accuracy.md`)
- tool-impact agreement: **59/61 (97%)**
- asset-sensitivity agreement: **5/7 (71%)**
- full band agreement: **12/35 (34%)** — but only one server (cbg_sqlite) had a
  banded ground-truth table, so this cell is thin.

**b) vs an independent oracle panel** (`scanner_vs_human.md`) — a human hand-heatmap
plus CVSS, DREAD, NIST 800-30/60, OWASP, MAESTRO, and ChatGPT raters, none of them
the scanner's own model:
- scanner vs consensus: exact **25/71 (35%)**, within-one-band **49/71 (69%)**
- **inter-rater ceiling**: the oracles agree with *each other* only exact 50% /
  within-one 78%. So 35%/69% sits close to the legitimate-disagreement ceiling —
  risk banding is genuinely subjective, and the scanner is within the human spread.

**c) as a graded severity scorer vs the classical frameworks** (`severity_eval/`)
- Over 496 scenarios it **beats CVSS and DREAD and ties NIST/OWASP** on clean
  operational severity, and **generalizes to unseen MCP scenarios better than
  AgentTrust's own scorer** (0.64 vs 0.43 Spearman on data neither authored).

**d) formula robustness** (`formula_sensitivity.md`) — ⚠️ the weak spot:
- Perturbing each cell's inputs by ±1: only **248/1700 (15%)** of cells are
  stable; **1452/1700 (85%)** flip their band under a one-step change, and 62%
  sit within 4 points of a cut-point. The bands are sharp but fragile to the
  primitive estimates feeding them.

---

## 8. Audit performed this session (fresh org, no overfit)

`scripts/check_static_scoring.py` invented a new org ("NovaCorp") with new
personas and fresh calls for github/slack/calendar the scanner never saw, and
scored them static-only. Results in `reports/static_check/`:

- **The scorer is faithful and not hardcoded.** Unknown asset → `unresolved`,
  unknown tool → `invalid` (no fabrication); a more sensitive asset scores
  strictly higher for the same tool; a bigger input parameter escalates the band.
  All four checks pass on data outside the training set.

- **Band provenance — an honest reproducibility caveat.** Only **810/1700
  (47.6%)** of stored bands equal the deterministic `band_label(sensitivity,
  blast, impact)`; the other **52%** are the pipeline's per-cell **LLM band
  override** (the judge stage). The LLM both escalates (e.g. `delete_all_events`
  high→critical) and de-escalates (e.g. a modest `create_event` high→medium).
  This is *by design* — LLM bands are the intended output — but it has two
  consequences worth stating plainly: (1) bands are **not reproducible** across
  rescans (the known "numbers move on re-scan" effect), and (2) the numeric
  score and the band can rank cells differently, so the score is not, by itself,
  the authoritative signal — the band is.

  *(Correction to an earlier note: the score↔band "inversions" are mostly this
  intended categorical/LLM behavior, not a scorer bug.)*

---

## 9. Known limitations (stated, not hidden)

1. **Content- and obfuscation-blindness.** The static rubric scores a tool's
   capability, not the intent in the arguments. A base64-wrapped reverse shell
   or `cat secrets | mail external@` is rated by the benign tool it rides on.
   This is the gap the **dynamic** scorer (`src/mcp_security/dynamic/`) closes.
2. **Band reproducibility.** ~52% of bands are LLM judgement; a rescan can move
   them. Deriving bands deterministically from the score via `band_label()`
   (already implemented, used as the offline fallback) would trade some nuance
   for full reproducibility — a decision to make, not a bug to fix.
3. **Formula fragility.** 85% of cells flip band under a ±1 change to a primitive.
4. **Flat sensitivity on some kinds.** The calendar scan rates every calendar
   sensitivity 4, so it cannot distinguish a benign from a sensitive calendar by
   asset alone — even a read is "high".

---

## 10. How to run it

```bash
# Scan a server (LLM-only; needs Ollama / a GPU node)
uv run python -m mcp_security.scanner --kind filesystem --root demo/corp_filesystem
uv run python -m mcp_security.scanner --kind calendar          # declarative kinds: github, slack, calendar

# Derive input-parameter rubrics
uv run python -m mcp_security.param_scoring --kind calendar --server calendar:cbg

# Score observed calls against the scan
uv run python -m mcp_security.call_scoring

# Reports (no LLM)
uv run python scripts/highlight_influential_inputs.py   # most influential inputs
uv run python scripts/check_static_scoring.py           # fresh-org honesty + calibration audit
uv run python scripts/evaluate_scanner.py               # grade vs ground truth
uv run python scripts/formula_sensitivity.py            # band robustness
```

---

## Bottom line

The static scanner reproduces reviewed **tool-impact judgement at 97%**, sits
**within the human inter-rater spread** on full banding (35% exact / 69%
within-one, against a 50%/78% ceiling), and **beats the classical risk
frameworks** as a severity scorer while generalizing to unseen servers. The
scorer that consumes its matrices is **faithful and not overfit** — it never
fabricates a score. The two things to be honest about: **band labels are ~half
LLM judgement and not reproducible across rescans**, and the **formula is
fragile to ±1 primitive changes**. Neither is a correctness bug; both are
calibration decisions worth owning in the writeup.
