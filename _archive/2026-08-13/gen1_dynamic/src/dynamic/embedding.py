"""Embedding-based likelihood for the dynamic scorer — the ``likelihood`` slot of the v6 formula.

The v6 static scan already computes ``asset_sensitivity * blast_radius * likelihood(1.0)
* tool_impact`` with likelihood pinned at 1.0. This module supplies that factor at
runtime: each call is embedded (hashing vectorizer over tool + arg tokens + structural
flags), scored for novelty against models fit on the server's *observed benign history
only*, calibrated into quantile-anchored z-scores ("sigmas above this server's normal"), and mapped
to a likelihood in ``[0.1, 1.0]``:

* a call indistinguishable from demonstrated-normal traffic (z <= 2) keeps the floor 0.1;
* a fully anomalous call (z >= 5) keeps the full static risk (likelihood 1.0);
* with *no* history at all, nothing has been demonstrated normal -> likelihood 1.0.

No LLM anywhere. Fitting is seconds per server (offline / periodic); scoring one call is
a hash + a few matrix products — sub-millisecond ("semi-runtime": refit periodically,
score live). Everything is deterministic under the fixed seed.

Callers choose what may serve as the demonstrated-normal reference. The pipeline applies
an **impact-aware reference filter** before fit(): calls at/above the scan's high band
never enter the reference, so a crown-asset destructive call cannot earn a likelihood
discount through repetition (see ``scripts/eval_embedding_likelihood.py`` —
``IMPACT_FILTER_BAND`` — and the insider-testbed section of the report). Design-time
knowledge only; no labels involved.

Novelty backends (all fit on the same training calls, never on attack labels):

* ``lin_ae``   linear autoencoder — TruncatedSVD reconstruction error in hashed space,
  computed sparsely via the projection identity ``||x - proj(x)||^2 = ||x||^2 - ||Vx||^2``;
* ``mlp_ae``   nonlinear autoencoder — small MLP reconstructing the SVD latent;
* ``knn``      mean distance to the nearest training calls in latent space;
* ``rareness`` frequency signal — how often this (tool, primary-asset) signature was seen;
* ``blend``    element-wise max of the calibrated ``lin_ae``/``knn``/``rareness`` z-scores.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.neural_network import MLPRegressor

HASH_DIM = 4096
LATENT_DIM = 24
KNN_NEIGHBORS = 5
SEED = 20260712
# Below this many training calls the model refuses to vouch for anything: likelihood 1.0.
MIN_FIT_CALLS = 20
# Robust-z anchors for the likelihood ramp: floor until Z_FLOOR sigmas, saturate at Z_CEIL.
# The 1.5x saturation ratio (Z_CEIL/Z_FLOOR) and the q99 anchor were tuned on the
# original corpus only and validated untouched on the insider corpus: equal TPR at
# roughly HALF the benign FPR versus the previous q98/2.5x setting. q99 is viable in
# unlabeled streams only because trimming happens BELOW the ramp start (see TRIM_Z) and
# the impact filter keeps high-band calls out of the reference.
Z_FLOOR = 2.0
Z_CEIL = 3.0
CALIBRATION_ANCHOR = 0.99
# Self-trim threshold for unlabeled streams: 0.8x the ramp start. Trimming below the
# ramp is what decouples contamination control from the alerting cutoff — the reference
# is cleaned aggressively while benign traffic still rarely crosses the (higher) ramp.
TRIM_Z = 0.8 * Z_FLOOR
# Max self-trim refinement rounds when trim_z is set (ITSR-style); loops exit early
# once a round trims nothing. Swept 1-3 on the prequential streams: 3 buys ~4 pts of
# malicious TPR and +0.1 mean malicious likelihood for ~1 pt of benign FPR.
TRIM_ROUNDS = 3
LIKELIHOOD_FLOOR = 0.1
SIGNALS = ("lin_ae", "mlp_ae", "knn", "rareness")
BLEND_SIGNALS = ("lin_ae", "knn", "rareness")

_B64 = re.compile(r"[A-Za-z0-9+/]{20,}={0,2}")
# Pure-hex strings (git SHAs, hex digests) match _B64 but are not opaque payloads. Real
# git traffic tripped has_b64_blob on 155/400 calls purely from commit SHAs; excluding
# hex keeps the flag meaning "unexpected encoded blob", not "long identifier".
_HEX = re.compile(r"[0-9a-fA-F]+")
_TOK = re.compile(r"[a-z0-9]+")
_NUM = re.compile(r"\d+")
_ASSET_KEYS = ("path", "repo", "channel", "calendar", "table_name", "file_name")

CallTuple = tuple[str, dict]


def tokenize_call(tool: str, args: dict) -> str:
    """One call -> bag-of-tokens 'document' for the hashing vectorizer.

    Emits the tool, each arg key, tokenized values (paths split on separators), cheap
    structural flags (nargs, content field, base64 blob, path depth), plus two features
    that each bought measurable held-out AUC:

    * magnitude buckets (``mag_<key>=<log10 bucket>``, ``listlen_<key>=...``) — an
      unusually large ``limit``/recipient list reads as novel even when every individual
      token was seen before;
    * the ``cell=<tool>|<asset>`` conjunction — bakes the (tool, asset) pairing into the
      embedding, so a known tool aimed at an asset it never benignly touches is far from
      every neighbor even though tool and asset tokens are each common.
    """
    toks = [f"tool={tool}", f"nargs={len(args)}"]
    for key, value in args.items():
        toks.append(f"key={key}")
        text = str(value)
        blob = _B64.search(text)
        if blob and not _HEX.fullmatch(blob.group()):
            toks.append("has_b64_blob")
        if key in ("content", "body", "message"):
            toks.append("has_content_field")
        toks.append(f"depth={min(text.count('/'), 6)}")
        toks += [f"val={t}" for t in _TOK.findall(text.lower())]
        if isinstance(value, (int, float)) or (isinstance(value, str) and _NUM.fullmatch(text)):
            magnitude = int(np.log10(max(abs(float(value)), 1.0)) + 1)
            toks.append(f"mag_{key}={min(magnitude, 6)}")
        if isinstance(value, list):
            magnitude = int(np.log10(max(len(value), 1)) + 1)
            toks.append(f"listlen_{key}={min(magnitude, 6)}")
    asset = next((str(args[k]) for k in _ASSET_KEYS if k in args), "")
    toks.append(f"cell={tool}|{asset}")
    return " ".join(toks)


def call_signature(tool: str, args: dict) -> str:
    """Coarse signature for the rareness signal: tool + primary asset argument."""
    asset = next((str(args[k]) for k in _ASSET_KEYS if k in args), "")
    return f"{tool}|{asset}"


def parse_args_json(raw: str) -> dict:
    """Best-effort parse of a raw JSON args string into a dict (never raises)."""
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def likelihood_from_z(z: np.ndarray | float) -> np.ndarray | float:
    """Map robust z-scores to the ``[LIKELIHOOD_FLOOR, 1.0]`` likelihood ramp.

    Monotone and interpretable in sigma units: at/below ``Z_FLOOR`` the call looks
    demonstrated-normal (floor); at/above ``Z_CEIL`` it is fully anomalous (1.0).
    """
    ramp = np.clip((np.asarray(z, dtype=float) - Z_FLOOR) / (Z_CEIL - Z_FLOOR), 0.0, 1.0)
    out = LIKELIHOOD_FLOOR + (1.0 - LIKELIHOOD_FLOOR) * ramp
    return float(out) if np.isscalar(z) else out


@dataclass(frozen=True)
class _QuantileCalibrator:
    """Quantile-anchored z-scoring: the training ``CALIBRATION_ANCHOR`` is pinned to ``Z_FLOOR``.

    ``z = Z_FLOOR * (score - q50) / (q_anchor - q50)`` — so by construction a fixed
    ~2% of in-distribution training traffic crosses the likelihood ramp, regardless of
    how skewed or zero-inflated the raw novelty scores are. (Median/MAD was tried first
    and is unstable here: most benign kNN distances are near-zero ties, so the MAD scale
    degenerates and the false-positive rate flips with the SVD seed.)
    """

    q50: float
    scale: float

    @classmethod
    def fit(cls, scores: np.ndarray) -> _QuantileCalibrator:
        q50, q_anchor = (float(q) for q in np.quantile(scores, [0.5, CALIBRATION_ANCHOR]))
        scale = (q_anchor - q50) / Z_FLOOR
        if scale < 1e-12:  # degenerate: nearly all training scores identical
            scale = (float(np.max(scores)) - q50) / Z_FLOOR
        return cls(q50=q50, scale=max(scale, 1e-9))

    def z(self, scores: np.ndarray) -> np.ndarray:
        return (scores - self.q50) / self.scale


@dataclass
class EmbeddingLikelihoodModel:
    """Per-server novelty -> likelihood model, fit on that server's observed history.

    ``signal`` selects which backend feeds :meth:`likelihoods`; every backend named in
    ``fit_signals`` is fit and remains queryable via ``z_scores(calls, signal=...)`` so
    an evaluation can compare architectures on one fitted model.
    """

    signal: str = "blend"
    fit_signals: tuple[str, ...] = SIGNALS
    # When set, fit() self-trims: score the training history with the freshly fit
    # model, drop calls whose z exceeds this, refit, and repeat (up to TRIM_ROUNDS or
    # until nothing more is trimmed) — the Iterative Training Set Refinement scheme from
    # the contaminated-training literature. Label-free contamination control for
    # UNLABELED streams (an attack repeated in the history would otherwise become its
    # own "normal"); leave None for curated benign training sets. Z_FLOOR is the
    # validated operating point.
    trim_z: float | None = None
    _vectorizer: HashingVectorizer = field(init=False, repr=False)
    _svd: TruncatedSVD | None = field(default=None, init=False, repr=False)
    _mlp: MLPRegressor | None = field(default=None, init=False, repr=False)
    _knn: NearestNeighbors | None = field(default=None, init=False, repr=False)
    _sig_freq: Counter = field(default_factory=Counter, init=False, repr=False)
    _calibrators: dict[str, _QuantileCalibrator] = field(default_factory=dict, init=False, repr=False)
    _n_fit: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        valid = set(SIGNALS) | {"blend"}
        if self.signal not in valid:
            raise ValueError(f"unknown signal {self.signal!r}; expected one of {sorted(valid)}")
        if self.signal == "blend":
            needed = set(BLEND_SIGNALS)
        else:
            needed = {self.signal}
        missing = needed - set(self.fit_signals)
        if missing:
            raise ValueError(f"signal {self.signal!r} needs fit_signals to include {sorted(missing)}")
        self._vectorizer = HashingVectorizer(n_features=HASH_DIM, alternate_sign=False, norm="l2")

    @property
    def is_fit(self) -> bool:
        """Whether enough history was seen to vouch for anything at all."""
        return self._n_fit >= MIN_FIT_CALLS

    def fit(self, calls: Sequence[CallTuple]) -> EmbeddingLikelihoodModel:
        """Fit every requested backend on ``calls`` (the observed history; no labels used).

        With ``trim_z`` set, follow-up passes drop the history calls the current model
        itself flags (z > trim_z) and refit on the remainder — see the field's comment.
        """
        self._fit_once(calls)
        kept = list(calls)
        for _ in range(TRIM_ROUNDS if self.trim_z is not None else 0):
            if not self.is_fit:
                break
            z_history = self.z_scores(kept)
            refined = [call for call, z in zip(kept, z_history) if z <= self.trim_z]
            if len(refined) < MIN_FIT_CALLS or len(refined) == len(kept):
                break
            kept = refined
            self._fit_once(kept)
        return self

    def _fit_once(self, calls: Sequence[CallTuple]) -> EmbeddingLikelihoodModel:
        self._n_fit = len(calls)
        if not self.is_fit:
            return self
        docs = [tokenize_call(t, a) for t, a in calls]
        x = self._vectorizer.transform(docs)

        n_components = max(2, min(LATENT_DIM, x.shape[0] - 1, x.shape[1] - 1))
        self._svd = TruncatedSVD(n_components=n_components, random_state=SEED)
        latent = self._svd.fit_transform(x)

        raw: dict[str, np.ndarray] = {}
        if "lin_ae" in self.fit_signals:
            raw["lin_ae"] = self._recon_error(x, latent)
        if "mlp_ae" in self.fit_signals:
            self._mlp = MLPRegressor(
                hidden_layer_sizes=(16, 6, 16), activation="tanh", solver="adam",
                max_iter=400, random_state=SEED,
            )
            self._mlp.fit(latent, latent)
            raw["mlp_ae"] = np.mean((latent - self._mlp.predict(latent)) ** 2, axis=1)
        if "knn" in self.fit_signals:
            self._knn = NearestNeighbors(n_neighbors=min(KNN_NEIGHBORS, len(calls))).fit(latent)
            # Calibration scores exclude each training call's own zero-distance match:
            # query k+1 neighbors and drop the nearest. With self included, every
            # training score carries a free zero in its mean, which silently tightens
            # the quantile anchor by ~(k-1)/k — an accident, not a knob.
            k_self = min(KNN_NEIGHBORS + 1, len(calls))
            raw["knn"] = self._knn.kneighbors(latent, n_neighbors=k_self)[0][:, 1:].mean(axis=1)
        if "rareness" in self.fit_signals:
            self._sig_freq = Counter(call_signature(t, a) for t, a in calls)
            raw["rareness"] = self._rareness(calls)

        self._calibrators = {name: _QuantileCalibrator.fit(scores) for name, scores in raw.items()}
        return self

    def z_scores(self, calls: Sequence[CallTuple], signal: str | None = None) -> np.ndarray:
        """Calibrated z-scores ("sigmas above this server's normal") for ``calls``.

        Returns ``+inf`` for every call when the model has insufficient history —
        the likelihood mapping then yields 1.0 (full static risk).
        """
        signal = signal or self.signal
        if not self.is_fit:
            return np.full(len(calls), np.inf)
        if signal == "blend":
            stacked = [self.z_scores(calls, s) for s in BLEND_SIGNALS]
            return np.max(np.vstack(stacked), axis=0)

        docs = [tokenize_call(t, a) for t, a in calls]
        x = self._vectorizer.transform(docs)
        latent = self._svd.transform(x)
        if signal == "lin_ae":
            raw = self._recon_error(x, latent)
        elif signal == "mlp_ae":
            raw = np.mean((latent - self._mlp.predict(latent)) ** 2, axis=1)
        elif signal == "knn":
            raw = self._knn.kneighbors(latent)[0].mean(axis=1)
        elif signal == "rareness":
            raw = self._rareness(calls)
        else:
            raise ValueError(f"unknown signal {signal!r}")
        return self._calibrators[signal].z(raw)

    def likelihoods(self, calls: Sequence[CallTuple]) -> np.ndarray:
        """Per-call likelihood in ``[0.1, 1.0]`` under the configured signal."""
        return likelihood_from_z(self.z_scores(calls))

    def _recon_error(self, x, latent: np.ndarray) -> np.ndarray:
        """SVD reconstruction error without densifying the hashed matrix.

        Components are orthonormal, so ``||x - x V^T V||^2 = ||x||^2 - ||x V^T||^2``.
        """
        row_norms = np.asarray(x.multiply(x).sum(axis=1)).ravel()
        residual = np.maximum(row_norms - np.sum(latent**2, axis=1), 0.0)
        return np.sqrt(residual)

    def _rareness(self, calls: Sequence[CallTuple]) -> np.ndarray:
        return np.array(
            [1.0 / (1.0 + self._sig_freq.get(call_signature(t, a), 0)) for t, a in calls]
        )
