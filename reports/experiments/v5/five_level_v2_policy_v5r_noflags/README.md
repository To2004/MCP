# v5r · no-flags arm — package for review

Static, design-time risk scoring for three MCP servers. The scanner sees **two
documents per server and nothing else**: the captured tool catalog (`tools/list`)
and the organization's written policy. The policy contains **no risk numbers** —
the scanner derives all of them.

Every score is `sensitivity × blast × impact`, max 125.

| primitive | 1–5 | who decides it |
|---|---|---|
| **tool impact** | what one call *does* — read / write / remove | deterministic rules; the model only where the rules abstain |
| **asset sensitivity** | how bad if this asset is lost | the model, classifying each asset against the org's own policy classes |
| **blast radius** | how far the consequences *propagate* — who and what is different afterwards | the model |

## The three organizations

| server | organization | domain | catalog |
|---|---|---|---|
| `calendar_aurora` | Aurora Airways | commercial aviation | real Google Calendar, 13 tools |
| `github_helios` | Helios Grid | electricity transmission (NERC CIP) | real GitHub, 26 tools |
| `slack_vireo` | Vireo Bio | biopharmaceutical R&D | real Slack, 16 tools |

All three policies were written against a **live deployment that was probed**, not
assumed — so their operation limits record what the platform actually does and
does not enforce (e.g. on Helios, a PR with zero reviews merged on the first
attempt and no branch protection intervened).

## What is in here

| path | what it is |
|---|---|
| `<server>.md` | the readable scan report — all three primitives and the scored matrix |
| `<server>_matrix.csv` | the tool × asset grid, one score per cell |
| `<server>_EXPLAINED.md` | **start here.** Every asset and every tool explained, the scan's number beside an independently expected one, and the cells worth arguing about |
| `<server>.json` | the full artifact, including the model's raw answers before any deterministic adjustment |
| `policies/<server>.policy.md` | the organization's policy — the *only* org input the scanner received |
| `scoring-prompts-AS-RUN.md` | every prompt sent to the model, verbatim |
| `code/` | the source that produced this run, with a `.md` explaining each file |

## What "no flags" means, and why this arm exists

The policy's asset register has an optional `Flags` column where an organization
can label an asset `hub`, `population` or `self-sufficient`. Those labels gated the
top blast tier: without one, the model was told it could not award a 5.

We ran the same scan three ways — all flags, only the three that mattered, and
**none** — because a flag is the organization asserting a *conclusion* (`hub` =
reaching this reaches other systems) where the rest of the register states
*facts*, and that conclusion is the question blast is supposed to derive. An
organization may also simply not provide one.

**This arm uses no flags.** Tier 5 has to be argued from the asset's own
description, and the model states its reason in free text so a reviewer can check
it against the register.

## Known limitations — please read before judging the numbers

1. **Blast is the noisy stage.** Earlier generations measured 23–35 cells of
   run-to-run movement per server with the prompt held fixed. Single-run
   differences of that size are not findings.
2. **Blast correlates with sensitivity at +0.57.** The model is told the asset's
   sensitivity as a decided fact so it can apply the organization's floors, and it
   partly re-prices value as a result. On ~47 % of cells it returns the
   sensitivity number as the blast number. This is a known defect, not a feature.
3. **Sensitivity is calibrated, blast is not.** On three *other* servers where the
   organization's own per-asset numbers exist and were held out, the derived
   sensitivity matched them at 50 % vs 48 % of assets at ≥4, mean identical to two
   decimals. There is no equivalent ground truth for blast.
4. **The formula is ours.** `sens × blast × impact` on three ordinal 1–5 scales is
   not a published method — CVSS uses a fitted equation, FAIR uses distributions.
   The individual primitives are grounded (HTTP PATCH/PUT and CVSS integrity for
   the impact ladder, MITRE ATT&CK for metadata-vs-content, FIPS 199 / SP 800-60
   for classify-then-map sensitivity); the *combination* is not.
5. **`n = 3` servers, one run each.**

## Questions we would most value feedback on

- Is deriving asset sensitivity from a written policy — with no numbers supplied —
  a defensible substitute for an organization-supplied severity inventory?
- Is blast radius as *propagation* (who and what is different afterwards) the
  right primitive, or should coverage and consequence be separated?
- Does multiplying three ordinal scales overstate what the numbers can support?
- Should the top blast tier require an organization-supplied label at all?
