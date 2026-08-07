# Architecture Diagrams

Input/output and dataflow of the whole scoring system — the static (design-time)
pipeline, the dynamic (runtime) pipeline, and how they compose. Every box maps
to a real module; arrows are actual data flows (verified against the code and
against the scan artifacts, not aspirational).

> ⚠️ [`architecture.dot`](architecture.dot) (render:
> `dot -Tsvg architecture.dot -o architecture.svg`) has **not** been updated to
> the current arm. It still labels the static subgraph `five_level_v2_ult` and
> does not mention the policy document at all, so it describes the superseded
> shape where sensitivity was read off the org's `| Asset | Sens. |` table. This
> Markdown file is the current source of truth.

Threat direction everywhere: **the MCP server is the protected asset; the agent
is the threat**. Static scoring prices what each (tool, asset) cell *could* do;
dynamic scoring prices what a specific session *is* doing.

## 1. Bird's-eye: static feeds dynamic

```mermaid
flowchart LR
    subgraph inputs["Design-time inputs"]
        TL["reports/tool_lists/*.json\n(captured tools/list)"]
        DEMO["demo/* stores\n(fs trees, sqlite DBs)"]
        POL["docs/mcp-tools/server-policies.md\n(org POLICY: classes + register,\nNO sensitivity numbers)"]
    end

    subgraph static["STATIC (design-time)"]
        SCAN["scanner\n+ static_scoring pipeline"]
        PARAM["param_scoring\n(input-magnitude rubrics)"]
    end

    PROF["docs/mcp-tools/server-profiles.md\n(per-asset Sens. tables)\nHELD OUT — never read by a scan"]
    EVAL["evaluate_policy_v5\nderived sens vs the org's own numbers"]

    SCANJSON[("reports/scan/&lt;server&gt;.json\ncells + bands + baselines")]
    PARAMJSON[("reports/scan/&lt;server&gt;_params.json")]

    subgraph runtime["DYNAMIC (runtime, per session)"]
        CS["call_scoring\nresolve asset → cell lookup"]
        DYN["dynamic\nbaseline + sequence + judge\n(escalate-only fusion)"]
        EMB["dynamic.embedding\nnovelty → likelihood ×\n(parallel track, scripts only)"]
    end

    SESS["logs/proxy/sessions/*/calls.csv\n(captured agent sessions)"]
    VERDICT["final band / final score\n→ gate · throttle · allow"]

    TL --> SCAN
    DEMO --> SCAN
    POL --> SCAN
    SCAN --> SCANJSON
    PARAM --> PARAMJSON
    SCANJSON --> CS
    PARAMJSON --> CS
    SESS --> CS
    CS -->|ScoredCall| DYN
    CS -->|ScoredCall history| EMB
    DYN --> VERDICT
    EMB -.->|static_score × likelihood| VERDICT

    SCANJSON --> EVAL
    PROF -->|ground truth, after the scan| EVAL

    REVIEW["review\nverify (deterministic) + judge/advisor (LLM)"]
    SCANJSON --> REVIEW
```

**The profile document is not a scanner input.** `server-profiles.md` hands over a
per-asset `Sens.` number; `server-policies.md` deliberately does not. Every policy
arm reads the policy and *derives* the number, and `policy_for()` raises
`PolicyNumbersError` if an `| Asset | Sens. |` table ever appears in a policy
section. The profile's numbers are the held-out ground truth
`scripts/evaluate_policy_v5.py` grades against afterwards — and only for the three
servers whose profile ids align (`calendar_real`, `github_real`, `slack_real`).

## 2. The three scanners and the severity matrix

The whole static side is three scanners, each producing exactly one primitive, and
one multiplication. Nothing else contributes to the score.

### 2a. At a glance

Two documents in, three scanners, one multiply. Colour and icon carry how each
number was decided: **⚙️ blue = deterministic rules**, **🤖 pink = LLM**,
**🔧 amber = rules first, LLM only where the rules have no verb**.

```mermaid
flowchart TB
    classDef io    fill:#eceff1,stroke:#546e7a,color:#263238
    classDef rules fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1
    classDef llm   fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#880e4f
    classDef mix   fill:#fff8e1,stroke:#ef6c00,stroke-width:2px,color:#e65100
    classDef out   fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px,color:#1b5e20

    TC["🗂️ Tool Catalog"]:::io
    OP["📜 Org Policy"]:::io

    subgraph SCAN["Three Scanners"]
        direction LR
        TS["🔧 <b>Tool Scanner</b><br/>⚙️ rules → 🤖 on gaps<br/><i>impact</i> · per tool"]:::mix
        AS["🏷️ <b>Asset Scanner</b><br/>🤖 LLM<br/><i>sensitivity</i> · per asset"]:::llm
        BS["💥 <b>Blast Scanner</b><br/>🤖 LLM<br/><i>blast</i> · per tool × asset"]:::llm
    end

    SM["⚙️ <b>SEVERITY MATRIX</b><br/>sensitivity × blast × impact<br/>1 – 125"]:::out

    TC --> TS
    TC --> BS
    OP --> AS
    OP --> BS
    TS -->|impact| SM
    AS -->|sensitivity| SM
    BS -->|blast| SM
```

Three things this view is meant to make obvious, and everything else is detail:

1. **Only two documents go in.** No file tree, no per-asset number.
2. **Each scanner owns one primitive**, and only blast is indexed by both tool
   and asset — which is why the matrix has structure at all.
3. **Most of the pipeline is arithmetic, not judgement.** The model is consulted
   in three places; the multiply and the banding are reproducible.

### 2b. In detail

```mermaid
flowchart TB
    subgraph src["Two documents in — nothing else"]
        CAT["tool catalog\nreports/tool_lists/*.json (tools/list)"]
        POL["org POLICY section\nserver-policies.md\nclasses · asset register · recognition rules"]
    end

    subgraph scanners["Three scanners — one primitive each"]
        direction TB
        subgraph tool["TOOL SCANNER · stage 1 — STATIC FIRST, LLM ONLY ON ABSTAIN"]
            direction LR
            L1["static_impact.classify\noperation-type ladder\nliveness · metadata · read · write · destroy"]
            L2{"did a tier verb\nactually match?"}
            L3["RULES ANSWER\nsource = static_ladder\nconfidence 1.0 — deterministic"]
            L4["LLM FALLBACK\nv4 impact prompt, tool JSON alone\nsource = llm_fallback"]
            L1 --> L2
            L2 -->|"yes · confidence ≥ 0.5"| L3
            L2 -->|"no · confidence 0.35"| L4
        end
        AS["ASSET SCANNER · stage 2\nWHAT THE DATA IS WORTH\nsensitivity a = 1-5\nclassify vs the policy's classes, then map\n▶ a VECTOR over A assets"]
        BS["BLAST SCANNER · stage 3\nHOW FAR ONE CALL REACHES\nblast t,a = 1-5 or N/A\nscope ladder: one item → beyond the org\n▶ a T×A MATRIX"]
    end

    CAT --> L1
    POL --> AS
    CAT --> BS
    POL --> BS
    TS["impact t = 1-5\n▶ a VECTOR over T tools"]
    L3 --> TS
    L4 --> TS

    ASM2["deterministic assembly\nbulk twins · alias twins\nno floors · no roof"]
    BS --> ASM2

    MUL["SEVERITY MATRIX\nscore t,a = sensitivity a × blast t,a × impact t\n1 … 125   ·   N/A wherever blast is N/A"]
    TS --> MUL
    AS --> MUL
    ASM2 --> MUL

    BAND["band_label_v5 — pure thresholds on the score\nlow &lt;17 · medium 17-49 · high 50-99 · critical ≥100"]
    MUL --> BAND
    BAND --> OUT[("&lt;server&gt;_matrix.csv\nasset,tool,sensitivity,blast,impact,score,band")]
```

**Yes — they multiply, and the shapes are what make the matrix interesting.**
Sensitivity is indexed by *asset* only and impact by *tool* only, so on their own
`sensitivity ⊗ impact` is a rank-1 outer product — every row would be a scaled copy
of every other. Blast is the only primitive indexed by *both*, so it is what makes
each cell genuinely its own number, and it is also the only one that can say **N/A**
(this tool does not touch this asset), which knocks the cell out of the matrix
entirely.

Four real rows from
`five_level_v2_policy_v5r_nacombo/fs_corp_filesystem_matrix.csv`:

| asset | tool | sensitivity | blast | impact | score | band |
|---|---|---:|---:|---:|---:|---|
| `security-keys` | `write_file` | 5 | 5 | 4 | **100** | critical |
| `security-keys` | `read_file` | 5 | 5 | 3 | 75 | high |
| `security-keys` | `get_file_info` | 5 | N/A | 2 | N/A | na |
| `public-overview` | `read_file` | 1 | 2 | 3 | 6 | low |

Same asset in the first three rows: sensitivity is pinned at 5 and only the verb
and the reach move. `get_file_info` drops out not because it is safe but because the
blast scanner ruled it does not reach that asset — metadata about a key file is not
the key.

### The tool scanner's static-first hand-off, and why it is auditable

The ladder does not "try and fail" — it reports a confidence, and
`confidence < STATIC_IMPACT_MIN_CONFIDENCE` (0.5) means one specific thing: **no
tier verb matched at all**, so the ladder would have had to fall back on its own
default rather than on evidence. `static_impact.classify` emits exactly `0.35` in
that case, so the gate is really "did a verb fire, yes or no".

When it hands off, the artifact keeps what the ladder *would* have said, so the
hand-off can be second-guessed later. Both abstentions on `fs_corp_filesystem`:

| tool | ladder would have said | LLM said | outcome |
|---|---:|---:|---|
| `create_directory` | 4 | **4** | model agreed with the ladder's default |
| `move_file` | 4 | **2** | model overruled it by two tiers |

`move_file` is the case the fallback exists for: no verb in the ladder's vocabulary
fires on "move", the default would have priced it as a write (4), and the model
priced it as a rename that neither reads nor destroys content (2). Every such record
carries `abstained: true`, `static_would_have_said`, and the reason string
*"no tier verb matched, so the ladder would have used its default"*.

Coverage is per server and visible in `tool_impact_source`: 12/14 rules on
`fs_corp_filesystem`, 13/16 on `slack_vireo`, 9/13 on `calendar_aurora`, and only
15/26 on `github_helios` — the GitHub catalog carries the most verbs the ladder has
no rule for.

### What is *not* in the severity matrix

`param_scoring` is the third risk dimension and it is **not** a factor here. It
prices how much a call's *argument values* ask for, which cannot be known at design
time — `read_file(head=10)` and `read_file(head=100000)` are the same cell. Its
design-time half derives a per-tool rubric; its runtime half applies that rubric to
concrete arguments and combines the result with this matrix's band. See the note
below on inputs.

## 3. Static pipeline in detail — the final static arm, `five_level_v2_v5r_nacombo`

This is the arm the v5r experiments converged on and the reference every later arm
is compared against
([`reports/experiments/v5/five_level_v2_policy_v5r_nacombo/`](../../reports/experiments/v5/five_level_v2_policy_v5r_nacombo/)).
Two facts distinguish it from the older `ult` shape the previous version of this
diagram described: **sensitivity is derived, not looked up**, and **tool impact is
decided by rules, not by the model** except where the rules abstain.

```mermaid
flowchart TB
    subgraph in["Inputs — exactly two documents per server"]
        TOOLS["tool catalog\nreports/tool_lists/*.json (tools/list)"]
        ORG["org POLICY section\nserver-policies.md:\nclassification table · asset register\n(Asset·Description·Tools·Flags·CIA)\nrecognition rules · fail-closed default\nNO 1-5 anywhere"]
    end

    REG["ServerRegistry\nbuild_policy_registry()\nDescription → asset description\nTools → tool:&lt;name&gt; tags (the tool×asset homing)\nFlags → flag:&lt;name&gt; tags"]
    TOOLS --> REG
    ORG --> REG
    REG -->|asset_flags = none:\nflag tags STRIPPED| REGN["registry as the stages see it\n(no flags reach model or arithmetic)"]

    subgraph rules["Deterministic (no model call)"]
        LADDER["1a · tool impact — RULES FIRST\nstatic_impact.classify\noperation-type ladder 1-5\nliveness · metadata · read · write · destroy"]
    end

    subgraph llm["LLM stages (Qwen via ollama_client, strict = never fabricate)"]
        DOM["0 · domain inference\nmcp_kind · content_unit · contents_definition\n(three-field stage in v5r)"]
        IMPF["1b · tool impact FALLBACK\nv4 impact prompt, only where the\nladder's confidence &lt; 0.5"]
        SENS["2 · asset sensitivity 1-5\nCLASSIFY vs the policy's own classes,\nTHEN map class → 1-5\nsensitivity_source = llm_policy_class"]
        BLAST["3 · blast radius 1-5 or N/A\nv5r SCOPE rubric (1 item → beyond the org)\nrelevance = combo: register homing +\nthe prompt's own reachability question"]
    end

    REGN --> DOM
    REGN --> LADDER
    LADDER -->|confidence ≥ 0.5\n58-86% of tools, per server| ASM
    LADDER -.->|abstains| IMPF
    IMPF --> ASM
    DOM -->|domain profile| BLAST
    ORG -.->|policy rides in every prompt| SENS
    ORG -.-> BLAST
    REGN --> SENS
    SENS -->|sensitivity primitive| ASM
    BLAST -->|blast_radius_raw| ASM

    subgraph det["Deterministic assembly (v5r)"]
        ASM["bulk twins: impact(bulk) ≥ impact(singular)\nalias twins (DEPRECATED → canonical): max blast\nbulk twin blast: blast(bulk) &gt; blast(singular), cap 5\nNO floors — floors = none\nNO roof — a cap can only under-score\nscore = sens × blast × impact (likelihood pinned 1.0)\nmax 125"]
        BAND["band_label_v5 — PURE score thresholds\nlow &lt;17 · medium 17-49 · high 50-99 · critical ≥100\nno categorical overrides"]
    end
    ASM --> BAND

    ENR["enrich_scan\natomic-op flags + per-input risk ranking"]
    BAND --> ENR
    ENR --> OUT[("scan JSON\ncells · bands · blast_radius_raw ·\nasset_sensitivity · tool_impact_source ·\nbulk_fixups · alias_fixups ·\nregister_flags_declared · description_source")]

    NOBASE["4 · behavioral baselines\nSKIPPED (no_baselines) — baselines = {}"]
```

### What this arm actually does, verified against the artifacts

| Stage | Where the number comes from | Evidence in the scan JSON |
|---|---|---|
| tool impact | deterministic ladder first; model only on abstention | `tool_impact_source` — 12/14 static on `fs_corp_filesystem`, 15/26 on `github_helios`, 13/16 on `slack_vireo`, 9/13 on `calendar_aurora` |
| asset sensitivity | LLM classifies against the policy's classes, then maps | `sensitivity_source: "llm_policy_class"` |
| blast radius | LLM, v5r scope rubric, may return N/A | `blast_radius_raw`, `null` cells → band `na` |
| floors | **none** | `blast_floor: {floors: {}, impact_floors: {}, raised_cells: 0}` |
| roof | **removed** | `blast_roof: {}` |
| flags | **none reach the model or the arithmetic** | `asset_flag_policy: "none"`; what the register declared is kept for audit only, in `register_flags_declared` |
| baselines | not run | `baselines: {}` |

The `register_flags_declared` field is the honest part of the flag removal: the
register still states `hub` / `population` / `self-sufficient`, and the artifact
records them, but no stage reads them. That is why removing the `Flags` column
outright in the v7 documents changed nothing arithmetically.

## 4. The two asset sources, and the parameter rubric

Three inputs in section 1 are easy to confuse. They answer different questions.

### `demo/*` stores — what physically exists

Real on-disk artifacts: `demo/corp_filesystem/` is an actual file tree
(`sensitive/`, `source_code/`, `projects/`, `onboarding/`), `demo/*_sqlite/` are
actual SQLite databases. Generated deterministically by
`scripts/build_corp_demo.py`. `scanner.scan.build_registry(kind, root=…)` **walks
them** — `reg.filesystem_assets(store)` enumerates the tree, `reg.sqlite_assets(store)`
reads the schema — so assets are *discovered from real structure*. Declarative kinds
(slack, calendar, github) front no local disk, so their assets come from code
registries instead.

### `server-policies.md` — what the organization calls an asset, and why it matters

Not a directory listing but a *statement*: a classification table defining classes
by adverse impact, an asset register, recognition rules, a fail-closed default.
`build_policy_registry()` takes asset ids, descriptions and the tool×asset homing
straight from the register rows.

**The policy arms never read the demo store.** Every v5 / v5r / nacombo / v7 scan
records `registry_source: "tool_catalog+org_policy_only"`. You can see it in the
asset ids: the disk-backed path yields path-shaped assets
(`sensitive/security/private_key.pem`), the policy path yields concept-shaped ones
(`security-keys`). Section 1 draws `demo/*` into the scanner because the
**older** `python -m mcp_security.scanner --kind filesystem --root demo/corp_filesystem`
entry point does use it, writing `reports/scan/<server>.json`. That is a different
driver from `scripts/scan_policy_v5.py`.

| | `demo/*` store | `server-policies.md` | `server-profiles.md` |
|---|---|---|---|
| Answers | what files/tables exist | what asset classes matter, and why | what each asset is worth (1–5) |
| Asset shape | paths, schemas | concepts | paths |
| Read by the policy arms? | **no** | **yes** | **no** — held-out ground truth |
| Supplies a number? | no | **no, by design** | yes |

### `param_scoring` — the input-magnitude rubric

The third risk dimension, orthogonal to (tool, asset): **how much does a call's
parameter values ask for?** Rules live in `docs/standards/parameter-scoring.md`,
which doubles as the LLM prompt.

- **Design time** — `param_scoring.derive` produces one rubric per tool into
  `reports/scan/<server>_params.json` (14 rubrics for the filesystem server). Each
  names the magnitude-bearing parameters, a `base_rank`, an extractor
  (`number` · `list_length` · `parsed_limit` · `boolean`) and ascending cutoffs.
  Real entry for `read_file`: parameters `head` and `tail`, `base_rank: medium`,
  `extract: number`, cutoffs `≥10 → low`, `≥50 → medium`, `≥100 → high`.
- **Run time** — `param_scoring.apply.score_call_params` applies that rubric
  deterministically to actual arguments, and `param_scoring.combine` merges the
  result with the cell's band (`escalate` or `combine_avg`).

So the rubric is derived statically but *cannot* enter the severity matrix: it needs
argument values, and a design-time cell has none. Do not confuse it with
`tool_input_ranking`, which `enrich_scan` attaches to the scan JSON — that is a
per-parameter risk annotation (1–5 plus a `critical_trigger`), documentation rather
than an applyable rubric.

## 5. Dynamic (runtime) pipeline in detail

```mermaid
flowchart TB
    SCANJSON[("scan JSON\n(static cells + bands)")]
    RUBRICS[("_params.json\nper-tool input rubrics")]
    CALLS["session calls.csv\n(tool, args, persona, run_id)"]
    CORPUS["history corpus\nlogs/proxy/sessions/*"]

    RESOLVE["call_scoring.resolve\nargs → scanned asset"]
    SCORE["call_scoring.score\ncell (score, band) verbatim\n× param multiplier"]
    CALLS --> RESOLVE
    SCANJSON --> RESOLVE
    RESOLVE --> SCORE
    RUBRICS --> SCORE

    SC["ScoredCall\nstatic band = the floor"]
    SCORE --> SC

    subgraph signals["Dynamic signals (escalate-only, never lower)"]
        BL["baseline.score_deviation\nunseen tool / sensitivity jump /\nsession burst vs persona history"]
        SEQ["sequence.score_sequence\nsensitive read → outbound\nwithin 5 calls = critical"]
        JDG["judge.judge_call (optional LLM)\ndecodes base64/hex/shell args"]
    end

    CORPUS -->|build_baselines| BL
    SC --> BL
    SC --> SEQ
    SC --> JDG

    FUSE["combine.score_session\nfinal = escalate(static, baseline,\nsequence, judge)"]
    BL --> FUSE
    SEQ --> FUSE
    JDG --> FUSE
    FUSE --> OUT["DynamicVerdict per call\n(final_band + every signal kept)"]
```

## 6. Where each experiment changed the static pipeline

```mermaid
flowchart TB
    BASELINE["five_level_v2_na\ncoverage blast, LLM sens"]
    CTX["ctx: per-tool understanding\ninjected into blast prompts"]
    FLOOR["floor: post-hoc sens-keyed\nblast minimums (plain/gated)"]
    ROWFIX["rowfix: per-asset row audit,\nguardrailed repairs"]
    DESC["desc: org prose replaces the\nsens primitive (blast × impact)"]
    ULT["ult: org TABLE = sens primitive\n+ gated floor + alias pass\n+ band_label_v5"]

    BASELINE --> CTX
    BASELINE --> FLOOR
    BASELINE --> ROWFIX
    BASELINE --> DESC
    FLOOR -->|gated variant| ULT
    DESC -->|description + band floor| ULT

    V5["v5: org POLICY replaces the table\nsensitivity DERIVED (classify → map)\n+ deterministic impact ladder"]
    V5R["v5r: rewritten prompts and rules\noperation-type impact ladder\nfloors ungated, then roof removed"]
    ULT --> V5 --> V5R

    subgraph abl["v5r ablations — one lever each"]
        A1["_noflags · _keyflags · _selfassess"]
        A2["_scope · _naregister · _naprompt · _nona"]
        A3["_lowfloor · _twostage"]
    end
    V5R --> abl

    NACOMBO["five_level_v2_v5r_nacombo\nTHE FINAL STATIC ARM\nasset_flags none · blast scope ·\nfloors none · relevance combo"]
    abl -->|the combination that won| NACOMBO

    SENS["v5r sens* arms: the PROMPT speaks\nISO / NIST / CIS at the same document"]
    V7["v7: the DOCUMENT is written in the\nframework's own shape — A.5.9 inventory,\nSP 800-60 types, Safeguard 3.2 inventory\n+ an authorization column, no flags"]
    NACOMBO --> SENS
    NACOMBO --> V7
    SENS -.->|same three standards,\nprompt-side vs document-side| V7
```

The two right-hand branches are the same three standards applied at different
layers, which is what makes them a pair: `sensiso` / `sensnist` / `senscis` change
only the sensitivity **prompt** while the organization keeps our register shape;
the v7 arms change the **document** the organization publishes and give each a
matching prompt. See
[`reports/experiments/v7/README.md`](../../reports/experiments/v7/README.md).

## Notes

- The two runtime composition tracks are separate by design
  (`docs/project/dynamic-scoring-design.md`): the **band track** (escalate-only,
  what `python -m mcp_security.dynamic` runs) and the **likelihood track**
  (`static_score × embedding likelihood`, wired into `scripts/eval_*` only).
- All LLM calls go through one chokepoint, `llm/ollama_client.query_ollama`
  (qwen2.5:32b, temperature 0, seed 0, no cloud fallback — callers degrade
  gracefully or, in strict scans, abort).
- `review/` re-derives every artifact deterministically (`verify`) and audits
  methodology with an LLM (`judge`, `advisor`) — assurance, not scoring.
- **Section 2 describes `five_level_v2_v5r_nacombo` specifically.** Earlier arms
  differ in exactly the levers section 4 names; the arm registry
  (`static_scoring/pipeline.py::_ULT_VARIANT_OPTIONS`) is the authority, and every
  scan records the arm it ran under in `impact_mode` plus the full lever set in
  `ult_variant_options`.
- `profile_sha256` in a scan artifact is a **legacy field name**. It hashes
  whatever organizational text the scan actually used, which for every policy arm
  is the policy section — not `server-profiles.md`.
- The score formula string in the artifact reads
  `asset_sensitivity * blast_radius * likelihood(1.0) * tool_impact`. Likelihood is
  pinned to 1.0 at design time by construction: a static cell prices what a call
  *could* do, so the static score is an upper bound. Likelihood is what the dynamic
  side supplies.
