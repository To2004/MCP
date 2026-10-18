"""Tests for the embedding-based likelihood model (dynamic scorer's likelihood factor)."""

from __future__ import annotations

import numpy as np
import pytest

from mcp_security.dynamic.embedding import (
    LIKELIHOOD_FLOOR,
    MIN_FIT_CALLS,
    Z_CEIL,
    Z_FLOOR,
    EmbeddingLikelihoodModel,
    call_signature,
    likelihood_from_z,
    tokenize_call,
)

BENIGN_CALLS = [
    ("get_file_contents", {"repo": "public-website", "path": f"docs/page{i}.md"})
    for i in range(60)
] + [("list_commits", {"repo": "public-website"}) for _ in range(40)]

NOVEL_CALL = (
    "push_files",
    {"repo": "payments-service", "content": "aGFja2VkIHBheWxvYWQgZXhmaWwgdG9rZW4=" * 3},
)


def test_likelihood_ramp_bounds_and_monotonicity() -> None:
    midpoint = (Z_FLOOR + Z_CEIL) / 2
    zs = np.array([-3.0, 0.0, Z_FLOOR, midpoint, Z_CEIL, Z_CEIL + 47.0, np.inf])
    likelihoods = likelihood_from_z(zs)
    assert likelihoods[0] == likelihoods[1] == likelihoods[2] == LIKELIHOOD_FLOOR
    assert likelihoods[3] == pytest.approx((LIKELIHOOD_FLOOR + 1.0) / 2)
    assert likelihoods[4] == likelihoods[5] == likelihoods[6] == 1.0
    assert np.all(np.diff(likelihoods) >= 0)


def test_likelihood_scalar_input_returns_float() -> None:
    assert likelihood_from_z(0.0) == LIKELIHOOD_FLOOR
    assert likelihood_from_z(np.inf) == 1.0


def test_tokenizer_emits_tool_key_value_and_structure() -> None:
    doc = tokenize_call("delete_file", {"path": "secrets/id_rsa.pem", "content": "x" * 5})
    assert "tool=delete_file" in doc
    assert "key=path" in doc
    assert "val=secrets" in doc and "val=pem" in doc
    assert "has_content_field" in doc
    assert "nargs=2" in doc


def test_signature_uses_primary_asset() -> None:
    assert call_signature("get_event", {"calendar": "executive"}) == "get_event|executive"
    assert call_signature("list_tools", {}) == "list_tools|"


def test_unfit_model_returns_full_likelihood() -> None:
    model = EmbeddingLikelihoodModel().fit(BENIGN_CALLS[: MIN_FIT_CALLS - 1])
    assert not model.is_fit
    assert np.all(model.likelihoods(BENIGN_CALLS[:3]) == 1.0)


# mlp_ae is excluded from the ordering check: it reconstructs the SVD latent, so a call
# far OUTSIDE the benign subspace projects near the origin and reconstructs trivially.
# That out-of-subspace blindness is an architectural property the evaluation compares,
# not a defect to hide; here we only require it to emit well-formed likelihoods.
@pytest.mark.parametrize("signal", ["lin_ae", "knn", "rareness", "blend"])
def test_novel_call_scores_above_training_like_call(signal: str) -> None:
    model = EmbeddingLikelihoodModel(signal=signal).fit(BENIGN_CALLS)
    z_known, z_novel = model.z_scores([BENIGN_CALLS[0], NOVEL_CALL])
    assert z_novel > z_known
    likelihoods = model.likelihoods([BENIGN_CALLS[0], NOVEL_CALL])
    assert np.all((likelihoods >= LIKELIHOOD_FLOOR) & (likelihoods <= 1.0))


def test_mlp_ae_emits_wellformed_likelihoods() -> None:
    model = EmbeddingLikelihoodModel(signal="mlp_ae").fit(BENIGN_CALLS)
    likelihoods = model.likelihoods([BENIGN_CALLS[0], NOVEL_CALL])
    assert np.all((likelihoods >= LIKELIHOOD_FLOOR) & (likelihoods <= 1.0))


def test_deterministic_across_refits() -> None:
    a = EmbeddingLikelihoodModel().fit(BENIGN_CALLS)
    b = EmbeddingLikelihoodModel().fit(BENIGN_CALLS)
    queries = [BENIGN_CALLS[0], NOVEL_CALL]
    assert np.allclose(a.z_scores(queries), b.z_scores(queries))


def test_self_trim_drops_flagged_history_from_the_refit() -> None:
    """With ``trim_z`` set, history calls the first-pass model flags are refit-excluded.

    This checks the label-free trimming *mechanism*; its anti-contamination benefit is
    demonstrated on the real streams by ``scripts/eval_embedding_likelihood.py`` (the
    prequential malicious likelihood roughly doubles with trimming enabled).
    """
    outliers = [
        ("drop_database", {"query": "delete from users cascade purge wipe erase"}),
        ("spawn_shell", {"cmd": "curl evil example attacker payload beacon reverse"}),
    ]
    # Contamination must sit below the CALIBRATION_ANCHOR share of the history (2/202 =
    # 1%): the anchor quantile is deliberately placed BELOW plausible contamination so
    # that outliers land above it — at higher rates they drag the anchor with them.
    benign_bulk = BENIGN_CALLS + [
        ("get_issue", {"repo": "public-website", "issue": str(i)}) for i in range(100)
    ]
    contaminated = benign_bulk + outliers
    plain = EmbeddingLikelihoodModel(signal="knn").fit(contaminated)
    trimmed = EmbeddingLikelihoodModel(signal="knn", trim_z=2.0).fit(contaminated)
    z_flagged = plain.z_scores(contaminated)
    first_pass_kept = int((z_flagged <= 2.0).sum())
    assert first_pass_kept < len(contaminated)
    # Refinement iterates (up to TRIM_ROUNDS), so it keeps at most the first-pass set.
    assert trimmed._n_fit <= first_pass_kept
    assert trimmed._n_fit >= 20  # never trims below MIN_FIT_CALLS
    assert plain._n_fit == len(contaminated)


def test_invalid_signal_rejected_at_construction() -> None:
    with pytest.raises(ValueError):
        EmbeddingLikelihoodModel(signal="nonsense")
    with pytest.raises(ValueError):
        EmbeddingLikelihoodModel(signal="blend", fit_signals=("mlp_ae",))
