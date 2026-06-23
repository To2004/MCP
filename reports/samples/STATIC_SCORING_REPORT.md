# MCP Static (Design-Time) Misuse Scoring — Work Report

This report explains what was built, the calibration journey, the results, and an
honest assessment of what is and isn't trustworthy.

## 1. What it is

A **static (design-time) risk-scoring** module for MCP servers. It scores every
`(tool × asset)` combination a server exposes — *before any request is seen* — so
a gateway can pre-rank which operations are dangerous. This is the "static" half
of the two-mode model in `docs/project/overview.md`; the runtime "dynamic" half
(per-request likelihood) is future work (see §7).

The output JSON matches the shape of the reference `payment_static_table.json`.
Risk formula (from `docs/standards/scoring-reference.md`):

```
score = asset_sensitivity (1-5) × blast_radius (0-4) × likelihood(1.0) × tool_impact (1-3)
```

`likelihood` is pinned to 1.0 because static mode is an **upper-bound ceiling**.

## 2. The pipeline (6 stages)

```
registry → 0 infer domain → 1 tool impact → 2 asset sensitivity
         → 3 blast radius → 4 baselines → 5 judge (independent review)
         → cells = S×B×L×I → operational bands
```

Each stage calls the local LLM (Qwen2.5:32b via Ollama) using the templates in
`prompts.py`, anchored to an inferred domain profile. If the model is
unreachable, deterministic heuristics in `fallback.py` produce a complete table
flagged `model_reviewed=false`. **Stage 5 (judge)** re-derives every primitive
independently and overrides the proposer on disagreement — a real second opinion,
not a confidence count. Decoding is greedy + fixed-seed, so runs are reproducible
(verified byte-identical across two independent GPU jobs).

## 3. Servers scored (the "simulations")

Seven demo servers, built from the project's own simulation/demo data, run in
parallel (one GPU each):

| Server(s) | Kind | Assets from |
|-----------|------|-------------|
| corp / law-firm / medical-clinic / media-studio | filesystem | files under each `demo/*` tree |
| cbg / corp | sqlite | live db schema (tables + columns) |
| slack | slack | `demo/slack_mcp` channels (a different kind: messaging) |

Combined results: `all_static_tables.json` (take1) and
`all_static_tables_take2.json` (take2).

## 4. take1 → take2: filesystem asset granularity

- **take1** groups files by **extension** (`.txt`, `.pem`). It discards the
  *path*, so `patients/alice/medical_history.txt` is seen only as "a `.txt`".
  Medical/legal stores were badly **under-scored** (0 critical despite holding
  PHI / privileged files).
- **take2** (`--take2`) makes each **file a full-path asset**
  (`patients/alice_johnson/medical_history.txt`), so the model sees what each
  file *is*. Medical/legal records now score correctly.

| Server | take1 worst/crit | take2 worst/crit |
|--------|------------------|------------------|
| law_firm_fs | high / 0 | critical (PHI/privilege surfaced) |
| medical_clinic_fs | high / 0 | critical |
| media_studio_fs | high / 0 | critical |

## 5. Band policy — a usable gate, not a flat alarm

A gate that flags too much halts the work it protects. Bands are assigned the way
a security reviewer would (rules grounded in `scoring-reference.md`):

- **critical** — irreversible (impact 3) destruction of a **crown-jewel**
  (sensitivity 5 = regulated/PII/financial/secrets) at departmental+ reach
  (blast ≥ 3). The ~1–2% you hard-gate.
- **high** — irreversible op on restricted data (sensitivity ≥ 4), a high raw
  score, **or a broad read of sensitive data** (mass exfiltration).
- **medium** — a middling score, **or any read of a crown-jewel**
  (confidentiality floor: reading a secret / PII record is never just "low").
- **low** — routine reads of ordinary/internal data. Work flows.

### Resulting distribution (take2, model-reviewed)

| low | medium | high | critical |
|-----|--------|------|----------|
| ~68% | ~15% | ~16% | ~2% |

The ~13 critical cells fleet-wide are exactly: `api_keys` / `private_key.pem`
destruction, and patient-record / invoice destruction — the operations a human
should approve. Reading those secrets is medium-to-high (not low); routine work
stays low.

## 6. Two calibration fixes found by review

1. **Over-flagging:** raw banding made ~10% of cells critical → a gate would block
   legitimate work. Reserving critical for crown-jewel destruction → ~2%.
2. **Confidentiality blind spot:** reading `api_keys` (the actual secrets) was
   banded `low`. Added a floor so reads of crown-jewels are medium (narrow) /
   high (broad). No sensitivity-5 read sits in `low` anymore.

## 7. Honest assessment — what is and isn't trustworthy

**Good (proof-of-concept quality):** the mechanics are sound (real judge,
deterministic, schema-faithful); the calibration is defensible and grounded in
the project's own scoring reference; the obvious flaws above are fixed; 219 tests
pass.

**Not yet production-trustworthy:**
- **No ground-truth validation** — calibrated to plausibility, not verified by a
  security expert.
- **Static can't separate routine from anomalous reads** — reading a patient
  record is `medium` statically, but routine for a clinician and exfiltration for
  an outsider. That distinction is the **dynamic/likelihood layer**'s job (the
  other half of the design), which is not built here.
- **Sensitive to model-assigned sensitivities** at the 4-vs-5 line (employees,
  legal files): these swing whole servers between "0 critical" and "many".

**Highest-value next step:** wire the dynamic layer — apply the
Baseline-Deviation / Access-Anomaly / Exposure likelihood (from
`scoring-reference.md`) to these static ceilings using the per-app baselines the
pipeline already generates. That turns "a defensible table" into "a gate that
lets work through and catches abuse."

## 8. How to reproduce

```bash
# Offline / deterministic (no GPU)
python -m mcp_security.static_scoring --all --no-llm            # take1
python -m mcp_security.static_scoring --all --no-llm --take2    # take2

# Model-reviewed on GPUs (one job per server), then combine + re-band
sbatch scripts/static_score_one.sbatch <server> take2          # ×7
python -m mcp_security.static_scoring --combine reports/samples/parts_take2/*.json
python -m mcp_security.static_scoring --reband reports/samples/all_static_tables_take2.json
```

## 9. Files in this bundle

- `code/` — the `static_scoring` Python module (pipeline, registries, fallback, CLI)
- `prompts/` — the LLM prompt templates for every stage (`prompts.py`)
- `results/` — the combined result tables (take1 + take2) and per-server parts
- `scoring-reference.md` — the project's scoring model these bands are grounded in
- this report
