# Dynamic scoring — embedding / autoencoder novelty (prototype)

An embedding-based *"how different and how often"* signal for the dynamic scorer,
built and measured on the existing 16.6k-call synthetic testbed
(`logs/proxy/sessions/dyn_*/calls.csv`, 14.4k benign / 2.2k malicious).

Prototype: [`dyn_embed_proto.py`](../../dyn_embed_proto.py) ·
plot: [`embed_separation.png`](embed_separation.png)

## Method

Per call → a bag-of-tokens document (tool, arg keys, tokenized arg values, and
structural flags: `nargs`, `has_content_field`, `has_b64_blob`, path `depth`) →
`HashingVectorizer` (4096-d, no fit) → `TruncatedSVD` latent **fit on BENIGN
calls only** (the learned embedding). Novelty is then scored four ways, all
benign-only trained (never on attack labels):

| signal | what it measures | model |
| --- | --- | --- |
| `lin_ae` | reconstruction error in hashed space | linear autoencoder = SVD invert |
| `mlp_ae` | reconstruction error on the latent | nonlinear autoencoder (MLP) |
| `knn` | distance to nearest benign call | kNN in latent space |
| `rareness` | *how often* this (tool, asset) is benign | frequency, `1/(1+count)` |

**Cutoff has no label leakage**: it is read off the *benign* score distribution
only. The honest runtime form is **per-server calibration** — judge a call
against *its own* server's benign scores (z-score), then apply one global rule
"flag at Nσ above benign".

Fit is a few seconds/server (offline); scoring one new call is a hash + one SVD
transform + one kNN/forward pass ≈ sub-millisecond → "semi-runtime".

## Results (per-server calibrated, flag at 3σ above benign)

| signal | AUC | TPR (malicious) | FPR (benign) |
| --- | --- | --- | --- |
| `lin_ae_z` (linear AE) | **0.932** | **84.4%** | **0.0%** |
| `knn_z` | 0.920 | 84.4% | 0.0% |
| `rareness_z` (frequency) | 0.924 | 84.4% | 4.2% |
| `mlp_ae_z` (nonlinear AE) | 0.616 | 31.7% | 1.7% |
| blended `max(lin_ae,knn,rareness)` | 0.919 | 84.4% @ 3σ / 84.4% @ 5σ | 4.2% / **0.5%** |

## The `create` breakdown (the asked-for case)

MLP-autoencoder reconstruction distance, z above each server's benign mean:

| create tool | nB | nM | benign µ | malicious µ | AUC |
| --- | --- | --- | --- | --- | --- |
| create_event | 42 | 19 | 2.6σ | 4.7σ | **1.000** |
| create_issue | 18 | 8 | 3.7σ | 9.9σ | **1.000** |
| create_or_update_file | 29 | 13 | 2.3σ | 8.6σ | **1.000** |
| create_pull_request | 28 | 16 | 2.6σ | 9.9σ | **1.000** |
| create_directory | 58 | 36 | (MLP inverts, 0.26) | — | **1.000** via lin_ae/knn/rareness |

Benign `create`s land ~2–3σ from the benign centroid; malicious `create`s land
4–10σ out — driven by the asset (crown-jewel vs `README.md`/`public-website`),
the extra `content` field, and the base64 exfil blob. **A cutoff of ~3.5–4σ
splits them cleanly** for every create tool.

## Two findings worth keeping

1. **Calibrate per server, not globally.** Raw MLP reconstruction error is not
   comparable across servers (pooled AUC 0.61) yet is *perfect per tool*
   (AUC 1.0). Z-scoring against each server's benign distribution fixes this and
   gives one meaningful "Nσ" cutoff. The linear AE and kNN are already
   scale-robust and don't strictly need it, but it drives their benign FPR to 0.

2. **~84% is the correct per-call ceiling, not a miss.** The malicious calls
   below the cutoff are the benign-looking *preamble reads* inside attack
   sessions (`get_file_contents`, `list_allowed_directories`, rareness ≈ 0.015)
   — individually indistinguishable from benign, and correctly left to the
   existing read-then-send **sequence** signal to catch in context.

## Suggested integration

Add `mcp_security/dynamic/embedding.py` producing a `band` from a per-server
benign-calibrated novelty z-score (`low <2σ, medium 2–3σ, high 3–5σ, critical
>5σ`), fused via the existing `escalate()` alongside `baseline`/`sequence`.
Use the **blended `max(lin_ae, knn, rareness)`** as the score — it covers the one
case (`create_directory`) where the nonlinear AE inverts. Fit artifacts (SVD +
benign score stats) are tiny and cache to disk, so runtime scoring stays offline
and sub-ms — no torch, no network (matches the SLURM-offline constraint).
