"""The gateway's log files: append-only JSONL, one per route, each line chained to the last.

Every line carries ``gateway.prev_sha256``, the SHA-256 of the line before it in the same
file, so editing, inserting or deleting a line in the middle breaks the chain where it
happened (OWASP: "build in tamper detection"). A restart continues the chain from the
file's last line.

What the chain cannot show on its own: lines cut from the very start or end of a file, or
a file rewritten whole with a new chain. Copy the files (or just their last line's digest)
to storage the gateway cannot rewrite to close that gap. One process per log directory —
two writers on one file would interleave lines and break the chain.

    uv run python -m mcp_security.gateway.log_file verify runs/gateway/live/github.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import TextIO

CHAIN_FIELD = "gateway.prev_sha256"
TAIL_CHUNK = 65_536  # bytes read at a time when looking for a file's last line
NEWLINE = b"\n"


def line_digest(line: bytes) -> str:
    """The digest the next line records: SHA-256 of the line's bytes, newline excluded."""
    return hashlib.sha256(line).hexdigest()


class MessageLog:
    """Append-only JSONL, one file per route. A write failure is reported, never raised:
    the log must not be able to break the agent's session.

    Each route's file stays open, and every line is flushed to the OS as it is written —
    the same durability as opening per line, without an open, close and mkdir per message
    (8% of a call's time, measured).
    """

    def __init__(self, log_dir: Path) -> None:
        self._dir = log_dir
        self._files: dict[str, TextIO] = {}
        self._last: dict[str, str | None] = {}

    def write(self, route: str, record: dict) -> None:
        try:
            handle = self._files.get(route) or self._open(route)
            previous = self._last.get(route)
            chained = {**record, CHAIN_FIELD: previous} if previous else record
            line = json.dumps(chained, ensure_ascii=False)
            handle.write(line + "\n")
            handle.flush()
            self._last[route] = line_digest(line.encode())
        except OSError as exc:
            print(f"gateway: log write failed for {route}: {exc}", file=sys.stderr)
            self._files.pop(route, None)  # reopen on the next write, re-reading the tail

    def close(self) -> None:
        for handle in self._files.values():
            handle.close()
        self._files.clear()

    def _open(self, route: str) -> TextIO:
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._dir / f"{route}.jsonl"
        last, complete = last_line(path)
        self._last[route] = line_digest(last) if last is not None else None
        handle = path.open("a", encoding="utf-8")
        if not complete:
            handle.write("\n")  # a torn last line stays a line of its own, chained as it is
        self._files[route] = handle
        return handle


def last_line(path: Path) -> tuple[bytes | None, bool]:
    """A file's last line (None: empty or missing) and whether it ends with a newline."""
    if not path.exists() or path.stat().st_size == 0:
        return None, True
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        position = handle.tell()
        handle.seek(position - 1)
        complete = handle.read(1) == NEWLINE
        tail = b""
        while position > 0:
            step = min(TAIL_CHUNK, position)
            position -= step
            handle.seek(position)
            tail = handle.read(step) + tail
            body = tail.rstrip(NEWLINE)
            if NEWLINE in body:
                return body.rsplit(NEWLINE, 1)[1], complete
        return tail.rstrip(NEWLINE) or None, complete


def verify_chain(path: Path) -> list[int]:
    """Line numbers (from 1) where the chain is broken: a line that is not a JSON object,
    one whose ``prev`` is not the digest of the line before it, or one with no ``prev``
    after the chain began. Lines from before the chain (older logs) are accepted."""
    broken: list[int] = []
    previous: bytes | None = None
    chained = False
    with path.open("rb") as handle:
        for number, raw in enumerate(handle, start=1):
            line = raw.rstrip(b"\r\n")
            if not line:
                continue
            claimed = _claimed_prev(line)
            if claimed is False or (claimed is None and chained):
                broken.append(number)
            elif claimed and previous is not None and claimed != line_digest(previous):
                broken.append(number)
            chained = chained or bool(claimed)
            previous = line
    return broken


#: v1 lines (before ``schema``) used these keys; readers rename them so old logs still score.
V1_KEYS = {
    "route": "gateway.route",
    "agent": "gateway.agent",
    "session": "mcp.session.id",
    "direction": "gateway.direction",
    "http": "http.request.method",
    "status": "http.response.status_code",
}


def read_log(path: Path) -> list[dict]:
    """Every record in a gateway log, in write order, with v1 keys renamed.

    A line that is not a JSON object (a write cut short by a crash) is skipped with a
    warning, so one torn line does not make the whole log unreadable; ``verify_chain``
    reports where it is.
    """
    records, torn = [], 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                record = None
            if isinstance(record, dict):
                records.append(record)
            else:
                torn += 1
    if torn:
        print(f"gateway: {path}: skipped {torn} line(s) that are not JSON objects", file=sys.stderr)
    return [
        record if "schema" in record else {V1_KEYS.get(k, k): v for k, v in record.items()}
        for record in records
    ]


def _claimed_prev(line: bytes) -> str | None | bool:
    """The line's ``prev`` digest; None if it has none; False if it is not a JSON object."""
    try:
        record = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False
    return record.get(CHAIN_FIELD) if isinstance(record, dict) else False


def main() -> None:
    """``verify <log.jsonl>...``: exit 1 if any file's chain is broken."""
    parser = argparse.ArgumentParser(description="Check gateway log hash chains.")
    parser.add_argument("command", choices=["verify"])
    parser.add_argument("paths", type=Path, nargs="+")
    args = parser.parse_args()
    failed = False
    for path in args.paths:
        broken = verify_chain(path)
        failed = failed or bool(broken)
        shown = ", ".join(map(str, broken[:20])) + (" …" if len(broken) > 20 else "")
        print(f"{path}: " + (f"BROKEN at line(s) {shown}" if broken else "chain intact"))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
