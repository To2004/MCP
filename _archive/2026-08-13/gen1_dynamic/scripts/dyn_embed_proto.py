"""Prototype: embedding + autoencoder novelty for the dynamic MCP scorer.

Question under test: for a given MCP call (esp. a `create`), how *different* is it
from what this server has seen benignly, and how *rare* is its signature — and is
there a distance CUTOFF that cleanly splits benign from malicious (misuse)?

Approach (fast, offline, deterministic; no torch, no network):
  1. Embed each call with a hashing vectorizer over tool + arg-keys + tokenized
     arg-values + a few structural tokens (nargs, has-content, base64 blob, depth).
  2. Reduce to a dense latent with TruncatedSVD fit on BENIGN calls only (the
     learned "embedding", LSA-style).
  3. Score novelty, all trained on BENIGN-ONLY (never on attack labels):
       - lin_ae   linear autoencoder = SVD reconstruction error in hashed space
       - mlp_ae   nonlinear autoencoder on the latent, recon MSE
       - knn      distance to nearest benign call in latent space
       - rareness FREQUENCY signal = how often this (tool, asset) signature is benign
  4. CUTOFF is picked from BENIGN scores only (no label leakage). We show it two ways:
       - a single GLOBAL cutoff (benign 99th pct of the pooled raw score)
       - a PER-SERVER calibrated cutoff: judge each call against ITS server's benign
         distribution (z-score), then one global "Nσ above benign" rule.
  5. Break it out per create-tool: benign vs malicious mean distance + AUC.

Runtime cost: fit is a few seconds per server (offline); scoring one new call is a
hash + one SVD transform + one forward/kNN query = sub-millisecond ("semi-runtime").
"""
from __future__ import annotations

import glob
import json
import re
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import NearestNeighbors
from sklearn.neural_network import MLPRegressor

HASH_DIM = 4096
LATENT_DIM = 24
BENIGN_CUTOFF_PCT = 99.0
Z_CUT = 3.0  # per-server rule: flag at 3 std devs above that server's benign mean
RNG = 20260706
SIGNALS = ["lin_ae", "mlp_ae", "knn", "rareness"]

_B64 = re.compile(r"[A-Za-z0-9+/]{20,}={0,2}")
_TOK = re.compile(r"[a-z0-9]+")
_ASSET_KEYS = ("path", "repo", "channel", "calendar", "table_name", "file_name")


def tokenize_call(tool: str, args: dict) -> str:
    """One call -> bag-of-tokens 'document' for the hashing vectorizer.

    Emits the tool, each arg key, tokenized values (paths split on separators),
    and cheap structural flags (nargs, content field, base64 blob, path depth).
    """
    toks = [f"tool={tool}", f"nargs={len(args)}"]
    for k, v in args.items():
        toks.append(f"key={k}")
        s = str(v)
        if _B64.search(s):
            toks.append("has_b64_blob")
        if k in ("content", "body", "message"):
            toks.append("has_content_field")
        toks.append(f"depth={min(s.count('/'), 6)}")
        toks += [f"val={t}" for t in _TOK.findall(s.lower())]
    return " ".join(toks)


def signature(tool: str, args: dict) -> str:
    """Coarse signature for the 'how often' frequency signal: tool + primary asset."""
    asset = next((str(args[k]) for k in _ASSET_KEYS if k in args), "")
    return f"{tool}|{asset}"


def load_all() -> pd.DataFrame:
    frames = []
    for f in sorted(glob.glob("logs/proxy/sessions/dyn_*/calls.csv")):
        d = pd.read_csv(f)
        d["server"] = f.split("/")[-2][4:]
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df["argd"] = df["args"].apply(lambda a: json.loads(a) if isinstance(a, str) else {})
    df["doc"] = [tokenize_call(t, a) for t, a in zip(df.tool, df.argd)]
    df["sig"] = [signature(t, a) for t, a in zip(df.tool, df.argd)]
    df["is_mal"] = (df.category == "MALICIOUS").astype(int)
    return df


def score_server(sub: pd.DataFrame) -> pd.DataFrame:
    """Fit benign-only novelty models for one server; return per-call raw scores."""
    vec = HashingVectorizer(n_features=HASH_DIM, alternate_sign=False, norm="l2")
    X = vec.transform(sub.doc)
    benign = sub.is_mal.values == 0
    Xb = X[benign]
    n_lat = min(LATENT_DIM, Xb.shape[0] - 1, Xb.shape[1] - 1)

    svd = TruncatedSVD(n_components=n_lat, random_state=RNG)
    Zb = svd.fit_transform(Xb)
    Z = svd.transform(X)
    lin_ae = np.linalg.norm(np.asarray(X.todense()) - svd.inverse_transform(Z), axis=1)

    mlp = MLPRegressor(hidden_layer_sizes=(16, 6, 16), activation="tanh",
                       solver="adam", max_iter=400, random_state=RNG)
    mlp.fit(Zb, Zb)
    mlp_ae = np.mean((Z - mlp.predict(Z)) ** 2, axis=1)

    nn = NearestNeighbors(n_neighbors=min(5, Zb.shape[0])).fit(Zb)
    knn = nn.kneighbors(Z)[0].mean(axis=1)

    freq = Counter(sub.sig[benign])
    rareness = np.array([1.0 / (1.0 + freq.get(s, 0)) for s in sub.sig])

    out = sub[["server", "tool", "category", "is_mal", "sig"]].copy()
    out["lin_ae"], out["mlp_ae"], out["knn"], out["rareness"] = lin_ae, mlp_ae, knn, rareness
    out["_benign"] = benign
    return out


def calibrate_per_server(scored: pd.DataFrame) -> pd.DataFrame:
    """Add a `<signal>_z`: each score as std-devs above ITS server's benign mean."""
    scored = scored.copy()
    for s in SIGNALS:
        for _, g in scored.groupby("server"):
            b = g[g._benign][s]
            scored.loc[g.index, f"{s}_z"] = (g[s] - b.mean()) / (b.std() + 1e-9)
    return scored


def _row(name: str, y: np.ndarray, v: np.ndarray, cut: float) -> None:
    flag = v >= cut
    print(f"{name:<12}{roc_auc_score(y, v):>7.3f}{cut:>10.3f}"
          f"{flag[y == 1].mean():>11.1%}{flag[y == 0].mean():>11.1%}")


def report(df: pd.DataFrame) -> None:
    scored = calibrate_per_server(
        pd.concat([score_server(g) for _, g in df.groupby("server")], ignore_index=True)
    )
    y = scored.is_mal.values
    benign = scored._benign.values

    print("\n" + "=" * 74 + "\nRAW score, single GLOBAL cutoff (benign 99th pct)\n" + "=" * 74)
    print(f"{'signal':<12}{'AUC':>7}{'cutoff':>10}{'TPR(mal)':>11}{'FPR(ben)':>11}")
    for s in SIGNALS:
        v = scored[s].values
        _row(s, y, v, np.percentile(v[benign], BENIGN_CUTOFF_PCT))

    print("\n" + "=" * 74 +
          f"\nPER-SERVER calibrated: flag at {Z_CUT}σ above each server's benign mean\n" + "=" * 74)
    print(f"{'signal':<12}{'AUC':>7}{'cutoff':>10}{'TPR(mal)':>11}{'FPR(ben)':>11}")
    for s in SIGNALS:
        _row(f"{s}_z", y, scored[f"{s}_z"].values, Z_CUT)

    print("\n" + "=" * 74 +
          "\nCREATE tools — calibrated MLP-autoencoder distance (z above benign)\n" + "=" * 74)
    print(f"{'tool':<22}{'nB':>5}{'nM':>5}{'benign µz':>11}{'mal µz':>10}{'AUC':>7}")
    create = scored[scored.tool.str.contains("create")]
    for tool, g in create.groupby("tool"):
        b, m = g[g.is_mal == 0].mlp_ae_z, g[g.is_mal == 1].mlp_ae_z
        auc = roc_auc_score(g.is_mal, g.mlp_ae) if g.is_mal.nunique() > 1 else float("nan")
        print(f"{tool:<22}{len(b):>5}{len(m):>5}{b.mean():>11.2f}{m.mean():>10.2f}{auc:>7.3f}")

    scored.to_csv("dyn_embed_scores.csv", index=False)
    print("\nper-call scores -> dyn_embed_scores.csv")


if __name__ == "__main__":
    report(load_all())
