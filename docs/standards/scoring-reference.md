# Scoring Reference

This document defines the scoring model used to rank MCP server-side threats. A risk score combines four components:

```
Risk = Impact × Likelihood × Irreversibility
```

Where **Impact** is derived from two scales (Sensitivity and Blast Radius), **Likelihood** is an aggregate of three behavioral sub-factors, and **Irreversibility** is a multiplier reflecting how recoverable the action is.

---

## 1. Impact

Impact captures *how bad the outcome is if the attack succeeds*. It has two independent scales: what kind of asset is touched (Sensitivity), and how much of the system is affected (Blast Radius).

### 1.1 Sensitivity scale (1–5)

Reflects the confidentiality/value of the data or resource being acted on.

| Score | Asset class | Examples |
|-------|-------------|----------|
| **1** | Public / non-sensitive | Public config, non-sensitive logs |
| **2** | Low-sensitivity infrastructure | File system, external API endpoints |
| **3** | Internal operational data | Internal DB, system config, QA plans |
| **4** | Restricted business data | Audit logs, source code, email |
| **5** | Regulated / PII | Financial records, PII, payslip data |

### 1.2 Blast Radius scale (1–5)

Reflects how far the effect of a single successful action propagates.

| Score | Scope | Examples |
|-------|-------|----------|
| **1** | Local | Single record, isolated operation |
| **3** | Departmental | Full table or departmental scope |
| **5** | Systemic | Entire system, all users / all agents |

> Scores 2 and 4 are reserved as interpolation points between the anchored levels.

---

## 2. Likelihood

Likelihood estimates how anomalous — and therefore how plausibly malicious — a given action is at runtime. It is composed of three independent sub-factors, each scored against observed behavior of the agent/user.

### 2.1 Baseline Deviation (0.0–1.0)

How unusual is this action relative to the historical baseline for this principal?

| Value | Meaning |
|-------|---------|
| **0.0** | Performs this regularly (known behavior) |
| **0.5** | Occasionally, seen in history |
| **1.0** | Never done in system history |

### 2.2 Access Anomaly (0.0–0.9)

Does the *manner* of access look anomalous in time and volume?

| Value | Meaning |
|-------|---------|
| **0.0** | Normal hours, normal volume |
| **0.5** | Time or volume outlier |
| **0.9** | Off-hours, bulk, new target |

### 2.3 Exposure (0.0–0.9)

How much untrusted external content has entered the context window before the action — i.e. how much attack surface for prompt injection or indirect manipulation?

| Value | Meaning |
|-------|---------|
| **0.0** | Internal data only |
| **0.5** | External data in LLM context |
| **0.9** | Reads emails, PDFs, web, DBs |

> The three sub-factors are combined into a single Likelihood term. Capping Access Anomaly and Exposure at 0.9 (vs 1.0 for Baseline Deviation) reflects that history is the strongest single signal — no other factor alone should saturate likelihood.

---

## 3. Irreversibility Multiplier

Applied as a multiplier on the Impact × Likelihood base score. Reflects the cost of undoing the action if it turns out to be malicious or mistaken.

### 3.1 ×1 — Recoverable

Action can be rolled back or re-derived with no lasting effect.

- Transaction rollback available
- `read_file`, `list_directory`
- `search_files`, `get_file_info`

### 3.2 ×2 — Difficult to recover

Action damages state in a way that requires effort, backups, or out-of-band reconstruction.

- `write_file` — overwrites, no backup
- `move_file` — backup trail breaks
- Config change without audit entry

### 3.3 ×3 — Permanent

Action destroys evidence or assets that cannot be reconstituted, including the records that would let us detect the attack itself.

- `edit_file` on audit / regulatory logs
- Financial record destruction
- Cryptographic key rotation / delete

> Read-only operations stay at ×1 regardless of sensitivity — they don't change state. The multiplier escalates sharply for actions that destroy the forensic trail itself (×3), because they break the ability to score *future* events accurately.

---

## Putting it together

For any candidate attack, the score is:

```
Risk = (Sensitivity × Blast Radius) × (Baseline Deviation + Access Anomaly + Exposure) × Irreversibility
```

This produces a comparable numeric risk across heterogeneous attack types and supports both:

- **Static mode** — score the attack class at design time using upper-bound assumptions.
- **Dynamic mode** — score a specific runtime call using observed Likelihood values.
