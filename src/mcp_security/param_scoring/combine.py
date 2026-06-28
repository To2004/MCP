"""Band arithmetic for parameter scoring.

Bands rank ``low=1 · medium=2 · high=3 · critical=4`` (see
``docs/standards/parameter-scoring.md``). Two operations are used:

* :func:`combine_avg` — average two bands, rounded half-up. The user's rule:
  a ``medium`` base parameter whose value lands ``critical`` ⇒ avg(2, 4) = 3 =
  ``high``.
* :func:`escalate` — take the more severe band. A risky parameter escalates the
  inherent (tool, asset) band, never lowers it.
"""

from __future__ import annotations

import math

BANDS = ("low", "medium", "high", "critical")
BAND_RANK = {band: i + 1 for i, band in enumerate(BANDS)}
RANK_BAND = {i + 1: band for i, band in enumerate(BANDS)}


def _rank(band: str) -> int:
    return BAND_RANK.get(band, 1)


def combine_avg(band_a: str, band_b: str) -> str:
    """Average two bands, rounding half-up (so avg of medium+critical is high)."""
    avg = (_rank(band_a) + _rank(band_b)) / 2
    rank = int(math.floor(avg + 0.5))
    return RANK_BAND[max(1, min(len(BANDS), rank))]


def escalate(band_a: str, band_b: str) -> str:
    """Return the more severe of two bands (parameter escalates inherent risk)."""
    return RANK_BAND[max(_rank(band_a), _rank(band_b))]
