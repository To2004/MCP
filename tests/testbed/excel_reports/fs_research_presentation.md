# Filesystem MCP Server — 5-Minute Presentation Script

Source: `fs_research_comparison.xlsx` (90 probes, 8 phases, 2 server versions)

## 1. The Question (≈30 sec)

The official Model Context Protocol filesystem server had a path-validation
bug somewhere between versions `v2025.3.28` and `v2025.7.29`. I wanted to
answer three things at once:

1. Can I **reproduce** the bug on the old version?
2. Did the new version **actually fix it**, or just rename the symptom?
3. What does the server's **behavioral surface** look like — where does it
   accept input, where does it refuse, and where do the two versions disagree?

The deliverable is a side-by-side spreadsheet so a reader can scan one row
and immediately see "old version did X, new version did Y."

## 2. Method (≈45 sec)

I built a single Python harness that boots both server versions against the
**same sandbox directory** and replays an identical, ordered list of 90 inputs
through each one. Every input is a deliberate probe — not random fuzzing.
Each row in the sheet records: my hypothesis *before* sending it, the raw
input, both responses, a `Differ?` flag, and a one-line observation *after*.

The 90 probes are grouped into 8 phases, ordered as a discovery story rather
than a feature checklist:

| Phase | Purpose | # probes |
|------:|---------|---------:|
| 1 | Fingerprint — what does "normal" look like? | 13 |
| 2 | Error mapping — how does it fail on legitimate misses? | 8 |
| 3 | Path normalization — slashes, dots, redundancy | 8 |
| 4 | Gibberish — total nonsense inputs | 14 |
| 5 | Almost valid — looks plausible, isn't | 14 |
| 6 | Creative attacker — prefix tricks, no traversal | 16 |
| 7 | Type confusion — wrong JSON types as `path` | 9 |
| 8 | Follow-up — exploit the finding from phase 6 | 8 |

The point of writing the hypothesis *first* is that it stops me from
back-rationalizing whatever the server happens to return.

## 3. What I Found (≈2 min — the core of the talk)

**Phases 1–4 (43 probes) were identical between versions.** Both servers
read normal files, both returned the same `ENOENT` strings, both normalized
`./././` and `////` the same way, both rejected gibberish with the same
"path outside allowed directories" error. That is the **boring half of the
sheet**, but it matters: it proves the harness is consistent and the patch
did **not** silently regress benign behavior — which is the first thing a
maintainer asks.

**The interesting half is phases 5–8, where 23 probes diverged.** They split
into three clean stories:

### Story A — The patch *worked* on classic tricks (phase 5)
Two probes flipped from "content returned" on the old version to "blocked"
on the new one: a Windows backslash separator and a null-byte injection. So
the patch genuinely closed two well-known path-validation gaps.

### Story B — The real vulnerability: **prefix bypass** (phases 6 + 8)
This is the headline finding. The old server allowed the sandbox `/tmp/mcp_sandbox`
but checked the path with a naive **string-prefix** match. So a sibling
directory called `/tmp/mcp_sandbox_escape` *also* started with the allowed
prefix and was accepted as "inside the sandbox." The old server happily
read files from a directory it was never supposed to touch.

Phase 6 confirmed the bypass with 6 variants. Phase 8 then leaned on it —
trailing slash, double slash, suffix mutations, dot-in-path — to see whether
the new version's fix was a one-liner or a real boundary check. In **every**
phase-8 variant the new version blocked and the old one leaked. That tells
me the patch is doing real path resolution, not just blacklisting one
spelling. **This is the actual exploitable bug, and the patch is sound.**

### Story C — Type confusion is still messy (phase 7)
8 of 9 type-confusion probes diverged: passing `42`, `null`, `true`, `[]`,
`{}` etc. as the `path` argument. Both versions reject these, but they
disagree on *how* — different error wording, different stack traces, sometimes
an unhandled exception vs. a clean error. Nothing exploitable, but it's a
**robustness gap** and a fingerprinting signal: a caller can tell the two
versions apart just by sending `path: 42`.

## 4. Why This Matters for the Thesis (≈45 sec)

This experiment is a miniature of the framework I'm building. The whole
thesis argues that an MCP server should **score the riskiness of an incoming
agent request** before executing it. This sheet is the empirical basis for
that scoring on one tool family:

- Phases 1–4 → the **low-risk baseline**: behavior is stable, deterministic,
  cheap to allow.
- Phase 5 → **known-bad patterns**: cheap signature checks, the kind of
  thing a static rule catches.
- Phase 6 → **semantic boundary violations**: this is where static rules
  fail and you need real path resolution. This is the cell my framework
  needs to score *high* even when the literal string looks innocent.
- Phase 7 → **schema-shape attacks**: a separate axis from path content,
  belongs in a different scoring dimension.
- Phase 8 → demonstrates the **follow-up loop** an attacker uses: find one
  weakness, mutate around it. The scorer has to catch the *family*, not
  the one spelling.

So the spreadsheet isn't just a bug report — it's a labeled dataset of
"what risky input looks like in practice for filesystem tools," which feeds
directly into the static-scoring rules.

## 5. What I'd Do Next (≈30 sec)

1. Run the same harness against the other 31 servers in the testbed and see
   which ones share the prefix-bypass class of bug.
2. Turn phases 5–8 into automated regression tests so future patches can be
   re-checked in seconds.
3. Use the labeled inputs to seed the static risk-scoring rules — phase 6
   and phase 8 rows are essentially ground-truth "high risk" examples.

## 30-Second Backup Version (if time runs out)

> I tested two versions of the MCP filesystem server with 90 ordered probes.
> The old version had a prefix-bypass bug: any directory starting with the
> sandbox name was treated as inside the sandbox. The new version fixes it
> properly — I confirmed with 8 follow-up mutations. I also found that type
> confusion is still inconsistent between versions, which is a fingerprinting
> risk but not exploitable. The spreadsheet is the labeled dataset I'll use
> to seed the static risk-scoring rules in the thesis framework.
