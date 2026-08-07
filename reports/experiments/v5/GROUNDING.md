# What follows a published standard, and what does not

An audit of every load-bearing decision in the v5r scoring path, split into what
has a citable source and what is ours. Written because the rules documents cite
standards next to some rules and not others, which makes the unsourced ones look
sourced by association.

**Summary: 9 decisions are grounded, 13 are ours, and 1 borrows half a
definition while contradicting the other half.**

---

## Grounded — a source says this

| Decision | Source | What the source actually says |
|---|---|---|
| **Tier 3/4 — limited vs ordinary write** | HTTP `PATCH` (RFC 5789) vs `PUT` (RFC 9110) | PATCH "applies partial modifications … leaves unmentioned fields untouched"; PUT sends "the complete representation" and replaces the resource |
| **Tier 3/4 — the same line again** | CVSS v4.0 integrity | `VI:L` = "modification of data is possible, but … the amount of modification is limited"; `VI:H` = "a total loss of integrity" |
| **Tier 2/3 — metadata vs content** | MITRE ATT&CK | Discovery (TA0007) is "knowledge about the system"; Collection (TA0009) is "gathering data of interest". Two separate tactics — enumeration is not exfiltration |
| **Tier 5 — irreversibility as the top** | CSA *NIST AI RMF Agentic Profile*; the four-tier agent-action frameworks | tool risk classification includes "reversibility — whether the effects can be undone, and at what cost"; irreversible + serious consequence is the top tier |
| **Annotations are hints, never bounds** | MCP spec; MCP blog *Tool Annotations as Risk Vocabulary* | clients "must treat them as untrusted unless they come from a trusted server"; "a server can claim `readOnlyHint: true` and delete your files anyway" |
| **Blast 4 vs 5 — contained vs escapes** | CVSS v4.0 | the Vulnerable System / Subsequent System split; VC/VI/VA vs SC/SI/SA |
| **Blast measured as PROPAGATION, not item count** | the industry definition of blast radius | "how far an attacker's impact can spread once they gain a foothold"; "which users are affected, which dependent services degrade, and how far the failure propagates". Reachability decides: "a CVE in a library you've imported but never call has a blast radius of zero" |
| **Sensitivity by classify-then-map** | FIPS 199; NIST SP 800-60; Stanford risk classifications; UC Berkeley P1–P4 | the org defines classes by adverse effect, the categorizer assigns the level |
| **Aggregation raises sensitivity** | SP 800-60 adjustment step; FIPS 199 high-water mark | "sensitivity is greater in context than in isolation"; a container takes the level of the most sensitive thing it holds |

## Half-grounded — and this one is a real tension

**Excluding breadth from tool impact.** The framework's central claim is
orthogonality: impact is the verb, sensitivity the noun, blast the quantifier. So
impact reads no breadth vocabulary at all.

But the CVSS definition cited for the tier 3/4 line **folds the amount into the
impact metric itself**: `VI:L` is "modification of data is possible, but … *the
amount of modification is limited*", and `VI:H` is "able to modify *any/all*
files". CVSS has no separate coverage axis — scope lives inside Integrity Impact.

So the 3/4 boundary borrows CVSS's *wording* while rejecting its *structure*. The
HTTP half of the citation is clean (PATCH vs PUT is genuinely about one resource's
representation, not about how many resources). The CVSS half is not. Two honest
options: stop citing CVSS for that line, or accept that "amount" belongs partly in
impact after all.

---

### A rubric that used to be ungrounded and now is not

Until this revision the blast tiers counted **items** — "one item among many",
"most of the asset", "essentially everything this asset holds". No published
definition of blast radius works that way. Every one of them measures how far a
consequence *propagates*: which users are affected, which dependent services
degrade, how far it travels before containment. Counting rows is a proxy that
fails exactly where it matters — reading one credential file touches one item and
reaches every system that credential opens.

The rubric now says "COUNT SUBJECTS AND SYSTEMS, NOT ITEMS" and anchors the normal
case at tier 3, which brings it in line with the term's ordinary meaning. The
reachability point lands too: the relevance gate (`affects_asset=false` → N/A) is
the same idea as an imported-but-never-called dependency scoring zero.

## Ours — no source, and they should be read as design choices

### Structural

| Decision | Why there is no source |
|---|---|
| **`score = sensitivity × blast × impact`** | No standard endorses multiplying three ordinal 1–5 scales. CVSS uses a fitted, empirically-calibrated equation over categorical metrics; FAIR uses probability distributions; both deliberately avoid multiplying ordinals, because the product implies interval spacing the scales do not have. **This is the largest unsourced choice in the framework.** |
| **Five tiers** | CVSS uses three (None/Low/High). ATT&CK has no severity tiers. The agentic frameworks use four. Five is ours. |
| **Tier 1 "no effect"** | No risk taxonomy carries a liveness-probe tier. It exists so `get-current-time` has somewhere to go. Harmless, but invented. |
| **Bands: low <17, medium 17–49, high 50–99, critical ≥100** | Arbitrary cutoffs on the 0–125 product. Chosen to spread the corpus, not derived. |

### The blast floors

```
asset sensitivity 5  →  blast ≥ 4
asset sensitivity 4  →  blast ≥ 3
tool impact       5  →  blast ≥ 3
```

These are **the analyst's own rules**, stated as policy. There is no standard for
them, and the closest published idea points the other way: CVSS scores each metric
independently and lets the equation combine them, rather than letting one metric
set a floor under another. They encode a defensible judgement — reaching a
crown-jewel asset is never pinpoint — but they are a judgement, not a derivation.

### The rules' mechanics

| Decision | Status |
|---|---|
| **281 verb patterns** across five operation classes | Hand-built from six domain vocabularies (fs, db, VCS, messaging, infra, payments). No source. Coverage of an unlisted domain degrades to the default. |
| **119 ambiguous words matched in the tool NAME only** | A pure NLP heuristic, ours. It is the single most effective rule in the file, and it is unsourced. |
| **10 generic read verbs** (`get`, `search`, `query`…) | Ours. |
| **Longest match wins** | Grounded in lexical analysis (maximal-munch tokenisation), not in any security standard. Cited honestly as a language principle. |
| **Liveness probe must be NAMED one** | Ours. |
| **Parameters never move the tier** | Ours — a design stance that runtime facts belong to the dynamic stage. Contradicts the over-privilege literature, which does treat unconstrained parameters as a design-time property. |
| **Confidence 0.35 / 0.8, hand-off at < 0.5** | Arbitrary values. They encode "the rules defaulted" vs "the rules had evidence", which is meaningful; the numbers themselves are not. |
| **Tier-5 blast requires an org-sanctioned flag** | The *idea* echoes CVSS subsequent-system; the flag mechanism (`hub` / `population` / `self-sufficient` in the register) is ours. |
| **Bulk-twin and alias-twin dominance** | Ours. Consistency rules, chosen to stop incoherent orderings. |

---

## What this means for the write-up

Three statements are safe to make: the ladder's read/write/remove spine matches
how ATT&CK, HTTP and CVSS each carve the same space; the annotation stance follows
the protocol's own guidance; and the sensitivity stage follows FIPS 199 / SP
800-60 practice directly.

One statement is not safe: that the *scoring formula* is standards-based. It is
not. `sens × blast × impact` on ordinal scales is the framework's own construction
and its band thresholds are chosen, not derived — which is exactly why
`scripts/formula_sensitivity.py` exists, and why the honest claim is "the primitives
are grounded, the combination is ours".

## Sources

- RFC 5789, *PATCH Method for HTTP* — <https://datatracker.ietf.org/doc/html/rfc5789>
- MDN, *PATCH request method* — <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/PATCH>
- CVSS v4.0 Specification — <https://www.first.org/cvss/v4.0/specification-document>
- MITRE ATT&CK, *Discovery (TA0007)* — <https://attack.mitre.org/tactics/TA0007/>
- MITRE ATT&CK, *Collection (TA0009)* — <https://attack.mitre.org/tactics/TA0009/>
- MCP blog, *Tool Annotations as Risk Vocabulary* — <https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/>
- CSA, *NIST AI RMF Agentic Profile* — <https://labs.cloudsecurityalliance.org/agentic/agentic-nist-ai-rmf-profile-v1/>
- MindStudio, *Classify AI Agent Actions by Risk* — <https://www.mindstudio.ai/blog/classify-ai-agent-actions-by-risk>
- Endor Labs, *Vulnerability Blast Radius: How to Measure and Reduce Impact* — <https://www.endorlabs.com/learn/vulnerability-blast-radius-how-to-measure-and-reduce-impact>
- Traversal, *What is Blast Radius?* — <https://www.traversal.com/glossary/blast-radius>
- Securview, *Network Blast Radius: Definition and Key Concepts* — <https://www.securview.com/ai-security-essentials/network-blast-radius>
- OX Security, *Scoping the Blast Radius* — <https://www.ox.security/blog/responding-to-a-supply-chain-breach-a-guide-to-key-rotation-version-pinning-and-scoping-the-blast-radius/>
- NIST FIPS 199; NIST SP 800-60 Vol. I/II — <https://csrc.nist.gov/pubs/sp/800/60/r2/iwd>
- Stanford, *Risk Classifications* — <https://uit.stanford.edu/guide/riskclassifications>
- UC Berkeley, *Data Classification Standard* — <https://security.berkeley.edu/data-classification-standard>
