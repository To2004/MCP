"""The log files: append-only, every line chained to the one before it, torn lines survived."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from mcp_security.gateway import log_file
from mcp_security.gateway.log_file import (
    CHAIN_FIELD,
    MessageLog,
    line_digest,
    read_log,
    verify_chain,
)

ROUTE = "github"


def _write(log_dir: Path, *values: int) -> Path:
    log = MessageLog(log_dir)
    for value in values:
        log.write(ROUTE, {"n": value})
    log.close()
    return log_dir / f"{ROUTE}.jsonl"


def _lines(path: Path) -> list[bytes]:
    return path.read_bytes().splitlines()


def test_each_line_records_the_digest_of_the_line_before(tmp_path: Path) -> None:
    path = _write(tmp_path, 1, 2, 3)
    lines = _lines(path)

    assert CHAIN_FIELD not in json.loads(lines[0])  # a new file starts the chain
    assert json.loads(lines[1])[CHAIN_FIELD] == line_digest(lines[0])
    assert json.loads(lines[2])[CHAIN_FIELD] == line_digest(lines[1])
    assert verify_chain(path) == []


@pytest.mark.parametrize(
    ("change", "broken"),
    [
        (lambda lines: [lines[0], lines[1].replace(b'"n": 2', b'"n": 7'), lines[2]], [3]),
        (lambda lines: [lines[0], lines[2]], [2]),  # a line deleted
        (lambda lines: [lines[0], b'{"n": 9}', lines[1], lines[2]], [3]),  # one inserted
    ],
)
def test_editing_deleting_or_inserting_a_line_breaks_the_chain_there(
    tmp_path: Path, change, broken: list[int]
) -> None:
    path = _write(tmp_path, 1, 2, 3)
    path.write_bytes(b"\n".join(change(_lines(path))) + b"\n")

    assert verify_chain(path) == broken


def test_a_restart_continues_the_chain_from_the_last_line(tmp_path: Path) -> None:
    path = _write(tmp_path, 1, 2)
    last = _lines(path)[-1]
    _write(tmp_path, 3)  # a new process, a new MessageLog

    assert json.loads(_lines(path)[2])[CHAIN_FIELD] == line_digest(last)
    assert verify_chain(path) == []


def test_a_torn_last_line_stays_its_own_line_and_is_the_only_one_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _write(tmp_path, 1)
    with path.open("ab") as handle:
        handle.write(b'{"n": 2, "cut sho')  # the process died mid-write
    _write(tmp_path, 3)

    assert verify_chain(path) == [2]
    assert [r["n"] for r in read_log(path)] == [1, 3]
    assert "skipped 1 line" in capsys.readouterr().err


def test_lines_from_before_the_chain_are_accepted(tmp_path: Path) -> None:
    path = tmp_path / f"{ROUTE}.jsonl"
    path.write_text('{"schema": "gateway-log/2"}\n{"schema": "gateway-log/2"}\n')
    _write(tmp_path, 1)

    assert verify_chain(path) == []


def test_a_chain_field_removed_after_the_chain_began_is_reported(tmp_path: Path) -> None:
    path = _write(tmp_path, 1, 2, 3)
    lines = _lines(path)
    record = json.loads(lines[2])
    del record[CHAIN_FIELD]
    path.write_bytes(b"\n".join([*lines[:2], json.dumps(record).encode()]) + b"\n")

    assert verify_chain(path) == [3]


def test_verify_command_exits_nonzero_on_a_broken_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _write(tmp_path, 1, 2)
    path.write_bytes(path.read_bytes().replace(b'"n": 1', b'"n": 5'))
    monkeypatch.setattr(sys, "argv", ["log_file", "verify", str(path)])

    with pytest.raises(SystemExit) as exit_info:
        log_file.main()

    assert exit_info.value.code == 1
    assert "BROKEN at line(s) 2" in capsys.readouterr().out
