"""INF-3: re-scoring the recorded synthetic gateway log with v4 gives the pinned CSV, and
re-recording it gives the same lines.

``golden/github.jsonl`` was written by the gateway itself (``golden_log.py``); one test runs
``score.py``'s CLI over it with the route's v4 behaviour policy and compares the CSV with
``golden/github_scored.csv``, every column but the timing (``score_us``). Another records
the same traffic again through the live gateway and compares every line, start and stop
lines included, so a change to the live path of a v4 route shows too.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from mcp_security.gateway.config import digest_view
from mcp_security.gateway.log_file import verify_chain
from tests.gateway.golden_log import (
    CSV_NAME,
    GOLDEN_DIR,
    LOG_NAME,
    TOKEN_SUBJECTS,
    record_log,
    rescore,
    route,
)
from tests.gateway.tokens import ISSUER

TIMING_COLUMNS = ("score_us",)  # wall-clock time of one score: never the same twice
DECISION = "gateway.decision"
CHAIN = "gateway.prev_sha256"  # the hash chain covers score_us, so it moves with it
#: The route's config digest covers the artifacts' paths, so it depends on the folder the log
#: was recorded in; it is checked on its own below.
CONFIG_DIGEST = "gateway.config_sha256"
STARTED, STOPPED = "gateway_started", "gateway_stopped"
DIGEST_CHARS = 12


@pytest.fixture(scope="module")
def golden_lines() -> list[dict]:
    return _lines(GOLDEN_DIR / LOG_NAME)


def _lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _comparable(record: dict) -> dict:
    """A log line without what may differ between two recordings of the same traffic."""
    out = {k: v for k, v in record.items() if k not in (CHAIN, CONFIG_DIGEST)}
    if isinstance(out.get(DECISION), dict):
        out[DECISION] = {k: v for k, v in out[DECISION].items() if k not in TIMING_COLUMNS}
    return out


def _pre_v5_digest(where: Path) -> str:
    """The config digest the pre-v5 gateway gave the golden route recorded in ``where``."""
    canonical = json.dumps(digest_view(route(where)), sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:DIGEST_CHARS]


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            {k: v for k, v in row.items() if k not in TIMING_COLUMNS}
            for row in csv.DictReader(handle)
        ]


def test_the_golden_log_is_synthetic_and_intact(golden_lines: list[dict]) -> None:
    calls = [r for r in golden_lines if "gateway.notice" not in r]
    assert {r.get("gateway.issuer") for r in calls} == {ISSUER}
    assert {r.get("user.id") for r in calls} == {sub for sub, _ in TOKEN_SUBJECTS.values()}
    assert verify_chain(GOLDEN_DIR / LOG_NAME) == []


def test_the_golden_log_has_its_start_and_stop_lines(golden_lines: list[dict]) -> None:
    first, last = golden_lines[0], golden_lines[-1]
    assert (first.get("gateway.notice"), last.get("gateway.notice")) == (STARTED, STOPPED)
    assert first[CONFIG_DIGEST] == last[CONFIG_DIGEST]


def test_rerecording_the_golden_log_gives_the_same_lines(
    tmp_path: Path, golden_lines: list[dict]
) -> None:
    again = _lines(record_log(tmp_path))
    assert len(again) == len(golden_lines)
    for index, (now, then) in enumerate(zip(again, golden_lines, strict=True)):
        assert _comparable(now) == _comparable(then), f"log line {index} changed"
    assert verify_chain(tmp_path / LOG_NAME) == []


def test_a_v4_routes_start_line_keeps_its_pre_v5_config_digest(tmp_path: Path) -> None:
    again = _lines(record_log(tmp_path))
    assert {again[0][CONFIG_DIGEST], again[-1][CONFIG_DIGEST]} == {_pre_v5_digest(tmp_path)}


def test_rescoring_the_golden_log_with_v4_gives_the_pinned_csv(tmp_path: Path) -> None:
    pinned = _rows(GOLDEN_DIR / CSV_NAME)
    got = _rows(rescore(GOLDEN_DIR, tmp_path))
    assert len(got) == len(pinned)
    for index, (now, then) in enumerate(zip(got, pinned)):
        assert now == then, f"scored call {index} changed"
