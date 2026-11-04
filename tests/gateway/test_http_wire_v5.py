"""RPL-1 and GW-1 (``gateway/http_wire.py``): the reply tap reads the same messages as before
in linear time, counts raw bytes and skips parsing above a cap; a request body that cannot be
read gets a verdict. Every body here is synthetic.
"""

from __future__ import annotations

import gzip
import json
import random
import time
from collections.abc import Callable

import pytest

from mcp_security.gateway.http_wire import (
    ACCEPT_ENCODING_HEADER,
    IDENTITY_CODING,
    MAX_PARSED_REPLY_BYTES,
    UNPARSED_ENCODED,
    UNPARSED_ENCODED_STATUS,
    UNPARSED_JSON,
    UNPARSED_NOT_JSONRPC,
    UNPARSED_REFUSED_STATUS,
    Frame,
    MessageTap,
    body_problem,
    parse_messages,
    unparsed_verdict,
)

SSE, JSON_BODY = "text/event-stream", "application/json"
SEED = 20_261_026
MB = 1024 * 1024
SMALL_MB, LARGE_MB = 10, 50
CHUNK = 64 * 1024
#: Feeding 5x the bytes must cost less than this many times as long: linear is about 5, the
#: old quadratic buffer about 25.
LINEAR_RATIO_LIMIT = 12.0
#: And a 50 MB reply must be read well within this many seconds.
LARGE_REPLY_LIMIT_S = 10.0
REPEATS = 3


class _QuadraticTap:
    """The tap as it was before RPL-1, kept here as the reference its replacement must match."""

    def __init__(self, content_type: str) -> None:
        self._sse = content_type.startswith(SSE)
        self._buffer = b""

    def feed(self, chunk: bytes) -> list[dict]:
        self._buffer += chunk
        if not self._sse:
            return []
        self._buffer = self._buffer.replace(b"\r\n", b"\n")
        *frames, self._buffer = self._buffer.split(b"\n\n")
        return [message for frame in frames for message in _sse_messages(frame)]

    def close(self) -> list[dict]:
        rest, self._buffer = self._buffer, b""
        return _sse_messages(rest) if self._sse else parse_messages(rest)


def _sse_messages(frame: bytes) -> list[dict]:
    data = [line[5:].lstrip() for line in frame.split(b"\n") if line.startswith(b"data:")]
    return parse_messages(b"\n".join(data))


def _event(i: int, crlf: bool) -> bytes:
    end = b"\r\n" if crlf else b"\n"
    message = {"jsonrpc": "2.0", "id": i, "result": {"content": [{"text": "x" * (i % 37)}]}}
    lines = [b"event: message", b"data: " + json.dumps(message).encode()]
    if i % 5 == 0:
        lines.insert(0, b": keep-alive comment")
    return end.join(lines) + end + end


def _stream(events: int, rng: random.Random) -> bytes:
    return b"".join(_event(i, rng.random() < 0.5) for i in range(events))


def _chunks(raw: bytes, rng: random.Random) -> list[bytes]:
    cuts = sorted(rng.sample(range(1, len(raw)), min(len(raw) - 1, rng.randint(1, 60))))
    edges = [0, *cuts, len(raw)]
    return [raw[a:b] for a, b in zip(edges, edges[1:])]


def _read(tap: MessageTap | _QuadraticTap, chunks: list[bytes]) -> list[list[dict]]:
    """What the tap emits after each chunk, and at close."""
    return [tap.feed(chunk) for chunk in chunks] + [tap.close()]


@pytest.mark.parametrize("trial", range(40))
def test_the_linear_tap_reads_what_the_old_one_read(trial: int) -> None:
    rng = random.Random(SEED + trial)
    raw = _stream(rng.randint(1, 12), rng)
    if trial % 4 == 0:
        raw += b'data: {"jsonrpc": "2.0", "id": 99, "result": {}}'  # unterminated last
    chunks = _chunks(raw, rng)
    assert _read(MessageTap(SSE), chunks) == _read(_QuadraticTap(SSE), chunks)


@pytest.mark.parametrize("trial", range(10))
def test_a_json_body_is_read_as_before_and_its_bytes_counted(trial: int) -> None:
    rng = random.Random(SEED - trial)
    body = json.dumps({"jsonrpc": "2.0", "id": trial, "result": {"content": ["y" * 999]}})
    chunks = _chunks(body.encode(), rng)
    tap = MessageTap(JSON_BODY)
    assert _read(tap, chunks) == _read(_QuadraticTap(JSON_BODY), chunks)
    assert tap.wire_bytes == len(body.encode())


#: Pieces of an SSE stream with bare CRs, which SSE allows as line ends and neither tap reads so.
BARE_CR_PIECES = [b"\r", b"\n", b"\r\n", b'data: {"id": 1}', b'data: {"id": 2}', b"x"]


def _whole(raw: bytes) -> list[dict]:
    """The old tap reading the stream in one chunk: the frames of the whole stream."""
    tap = _QuadraticTap(SSE)
    return tap.feed(raw) + tap.close()


@pytest.mark.parametrize("trial", range(300))
def test_any_chunking_reads_what_the_old_tap_read_whole(trial: int) -> None:
    """Bare CRs: the old tap's frames depended on where the chunks fell; the new tap's do not,
    and are those the old tap read from the whole stream (the docstring's v4 guarantee)."""
    rng = random.Random(SEED * 7 + trial)
    raw = b"".join(rng.choice(BARE_CR_PIECES) for _ in range(rng.randint(1, 25)))
    tap = MessageTap(SSE)
    read = [m for chunk in _chunks(raw, rng) for m in tap.feed(chunk)] + tap.close()
    assert read == _whole(raw)


def test_the_frame_ends_split_across_chunks_are_found() -> None:
    raw = b'data: {"id": 1}\r\n\r\ndata: {"id": 2}\n\r\ndata: {"id": 3}\r\n\n'
    for cut in range(1, len(raw)):
        tap = MessageTap(SSE)
        got = tap.feed(raw[:cut]) + tap.feed(raw[cut:]) + tap.close()
        assert [m["id"] for m in got] == [1, 2, 3], cut


def test_raw_bytes_are_counted_per_frame_and_in_total() -> None:
    first, second = b'data: {"id": 1}\r\n\r\n', b'data: {"id": 2}\n\n'
    tap = MessageTap(SSE)
    frames = tap.feed_frames(first + second[:5]) + tap.feed_frames(second[5:])
    assert [f.wire_bytes for f in frames] == [len(first), len(second)]
    assert tap.wire_bytes == len(first) + len(second)
    assert tap.close_frames() == []


def test_a_json_body_over_the_cap_is_counted_not_parsed() -> None:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"content": ["z" * 5_000]}}).encode()
    tap = MessageTap(JSON_BODY, max_parse_bytes=1_000)
    for start in range(0, len(body), 700):
        assert tap.feed_frames(body[start : start + 700]) == []
    assert tap.close_frames() == [Frame([], len(body), parsed=False)]
    assert (tap.unparsed, tap.wire_bytes) == (1, len(body))
    under = MessageTap(JSON_BODY, max_parse_bytes=len(body))
    under.feed(body)
    assert under.close() == parse_messages(body) and under.unparsed == 0


def test_an_sse_frame_over_the_cap_is_skipped_and_the_next_ones_read() -> None:
    small = b'data: {"id": 1}\n\n'
    big = b"data: " + json.dumps({"id": 2, "pad": "p" * 4_000}).encode() + b"\r\n\r\n"
    tail = b'data: {"id": 3}\n\n'
    raw = small + big + tail
    tap = MessageTap(SSE, max_parse_bytes=1_000)
    frames = [f for i in range(0, len(raw), 300) for f in tap.feed_frames(raw[i : i + 300])]
    frames += tap.close_frames()
    assert [f.parsed for f in frames] == [True, False, True]
    assert [m["id"] for f in frames for m in f.messages] == [1, 3]
    assert [f.wire_bytes for f in frames] == [len(small), len(big), len(tail)]
    assert tap.unparsed == 1 and tap.wire_bytes == len(raw)


def test_a_complete_frame_over_the_cap_in_one_chunk_is_skipped() -> None:
    big = b"data: " + json.dumps({"id": 2, "pad": "p" * 4_000}).encode() + b"\n\n"
    tap = MessageTap(SSE, max_parse_bytes=1_000)
    assert tap.feed_frames(big) == [Frame([], len(big), parsed=False)]


def test_an_unterminated_frame_over_the_cap_is_skipped_at_close() -> None:
    raw = b"data: " + b"q" * 5_000
    tap = MessageTap(SSE, max_parse_bytes=1_000)
    assert tap.feed_frames(raw) == []
    assert tap.close_frames() == [Frame([], len(raw), parsed=False)]


@pytest.mark.parametrize("cap", [0, 1, 2, 3, 4])
def test_a_tiny_cap_still_counts_every_byte(cap: int) -> None:
    """Below the longest frame end (4 bytes) nothing is dropped twice or left uncounted."""
    tap = MessageTap(SSE, max_parse_bytes=cap)
    frames = tap.feed_frames(b"d") + tap.feed_frames(b"ata: {}\n\n") + tap.close_frames()
    assert [(f.wire_bytes, f.parsed) for f in frames] == [(10, False)]
    assert tap.wire_bytes == 10 and tap.unparsed == 1


@pytest.mark.parametrize("trial", range(200))
def test_every_byte_lands_in_one_frame_whatever_the_cap(trial: int) -> None:
    """The frames' raw bytes add up to the stream, and a frame under the cap reads as without
    one, for any cap and chunking."""
    rng = random.Random(SEED + 1_000 + trial)
    raw = _stream(rng.randint(1, 8), rng) + rng.choice([b"", b'data: {"id": 77}'])
    chunks = _chunks(raw, rng)
    capped, free = MessageTap(SSE, max_parse_bytes=rng.randint(0, 120)), MessageTap(SSE)
    got = [f for chunk in chunks for f in capped.feed_frames(chunk)] + capped.close_frames()
    want = [f for chunk in chunks for f in free.feed_frames(chunk)] + free.close_frames()
    assert sum(f.wire_bytes for f in got) == capped.wire_bytes == len(raw)
    assert [f.wire_bytes for f in got] == [f.wire_bytes for f in want]
    assert [f.messages for f in got if f.parsed] == [
        w.messages for f, w in zip(got, want, strict=True) if f.parsed
    ]


def test_a_bad_cap_fails_loudly() -> None:
    with pytest.raises(ValueError):
        MessageTap(JSON_BODY, max_parse_bytes=-1)
    assert MAX_PARSED_REPLY_BYTES > LARGE_MB * MB / 4  # well above an ordinary reply


def _json_reply(megabytes: int) -> bytes:
    pad = "a" * (megabytes * MB)
    return json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"content": [pad]}}).encode()


def _sse_reply(megabytes: int) -> bytes:
    """One SSE event of ``megabytes``: the old tap re-scanned it whole on every chunk."""
    return b"data: " + _json_reply(megabytes) + b"\n\n"


def _seconds(raw: bytes, content_type: str, cap: int | None) -> tuple[float, int]:
    """The fastest of REPEATS reads of ``raw`` in CHUNK pieces, and the messages read."""
    best, read = float("inf"), 0
    for _ in range(REPEATS):
        tap = MessageTap(content_type, max_parse_bytes=cap)
        started = time.perf_counter()
        read = sum(len(tap.feed(raw[i : i + CHUNK])) for i in range(0, len(raw), CHUNK))
        read += len(tap.close())
        best = min(best, time.perf_counter() - started)
        assert tap.wire_bytes == len(raw)
    return best, read


@pytest.mark.parametrize(
    ("make", "content_type", "cap", "messages"),
    [
        (_json_reply, JSON_BODY, None, 1),
        (_sse_reply, SSE, None, 1),
        (_json_reply, JSON_BODY, MAX_PARSED_REPLY_BYTES, 0),
        (_sse_reply, SSE, MAX_PARSED_REPLY_BYTES, 0),
    ],
    ids=["json", "sse", "json-capped", "sse-capped"],
)
def test_a_50_mb_reply_takes_linear_time(
    make: Callable[[int], bytes], content_type: str, cap: int | None, messages: int
) -> None:
    small, _ = _seconds(make(SMALL_MB), content_type, cap)
    large, read = _seconds(make(LARGE_MB), content_type, cap)
    assert read == messages  # parsed without a cap, only counted above it
    assert large < LARGE_REPLY_LIMIT_S
    assert large / max(small, 1e-6) < LINEAR_RATIO_LIMIT


def _call_body(value: bytes) -> bytes:
    """A tools/call body whose one argument is the JSON text ``value``."""
    head = b'{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "t", '
    return head + b'"arguments": {"q": ' + value + b"}}}"


#: GW-1: (body, Content-Encoding) -> why it cannot be read.
PROBLEMS = [
    (
        gzip.compress(b'{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'),
        "gzip",
        UNPARSED_ENCODED,
    ),
    (b'{"jsonrpc": "2.0", "id": 1}', "identity, br", UNPARSED_ENCODED),
    (b'{"jsonrpc": "2.0", "id": 1, ', None, UNPARSED_JSON),
    (b"\xff\xfe\x00garbage", None, UNPARSED_JSON),
    (b"[" * 100_000 + b"]" * 100_000, None, UNPARSED_JSON),  # too deep to read
    (_call_body(b"1" * 5_000), None, UNPARSED_JSON),  # an integer longer than Python reads
    (_call_body(b'"\\ud800"'), None, UNPARSED_JSON),  # an escaped lone surrogate
    (_call_body(b'"\xed\xa0\x80"'), None, UNPARSED_JSON),  # its raw bytes
    (_call_body(b'"\\udfff and \\ud83d"'), None, UNPARSED_JSON),  # two halves, wrong order
    (b'"tools/call"', None, UNPARSED_NOT_JSONRPC),
    (b"[]", None, UNPARSED_NOT_JSONRPC),
    (b'[{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, 42]', None, UNPARSED_NOT_JSONRPC),
]


@pytest.mark.parametrize(
    ("raw", "encoding", "reason"),
    PROBLEMS,
    ids=[
        "gzip",
        "br",
        "truncated",
        "not-utf8",
        "too-deep",
        "long-int",
        "surrogate-escape",
        "surrogate-bytes",
        "surrogate-halves",
        "scalar",
        "empty-batch",
        "non-object",
    ],
)
def test_a_body_the_gateway_cannot_read_says_why(
    raw: bytes, encoding: str | None, reason: str
) -> None:
    assert body_problem(raw, encoding) == reason


@pytest.mark.parametrize(
    ("raw", "encoding"),
    [
        (b'{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}', None),
        (b'{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}', "Identity"),
        (b'[{"jsonrpc": "2.0", "method": "notifications/initialized"}]', ""),
        (b"", "gzip"),  # a bodiless GET or DELETE
        (b"  \n", None),
        (_call_body(b'"\\ud83d\\ude00"'), None),  # an escaped surrogate pair: one character
        (_call_body('"שלום"'.encode()), None),  # UTF-8 text with no escape
    ],
)
def test_a_readable_or_empty_body_has_no_problem(raw: bytes, encoding: str | None) -> None:
    assert body_problem(raw, encoding) is None
    assert unparsed_verdict(raw, encoding, fail_closed=True) is None


def test_the_verdict_refuses_an_unreadable_body_only_on_a_fail_closed_route() -> None:
    raw = b"{not json"
    forwarded = unparsed_verdict(raw, None, fail_closed=False)
    refused = unparsed_verdict(raw, None, fail_closed=True)
    assert forwarded is not None and refused is not None
    assert (forwarded.reason, forwarded.refused, forwarded.status) == (UNPARSED_JSON, False, None)
    assert (refused.refused, refused.status, refused.headers) == (
        True,
        UNPARSED_REFUSED_STATUS,
        {},
    )


@pytest.mark.parametrize("fail_closed", [False, True])
def test_an_encoded_body_is_refused_on_every_route(fail_closed: bool) -> None:
    """A server that inflates request bodies (``express.json()`` does by default) would run a
    gzip-compressed call the gateway never read, so an encoded body is never forwarded; the
    answer says which coding is taken (RFC 9110 15.5.16)."""
    call = b'{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "t"}}'
    verdict = unparsed_verdict(gzip.compress(call), "gzip", fail_closed=fail_closed)
    assert verdict is not None
    assert (verdict.reason, verdict.refused, verdict.status) == (
        UNPARSED_ENCODED,
        True,
        UNPARSED_ENCODED_STATUS,
    )
    assert verdict.headers == {ACCEPT_ENCODING_HEADER: IDENTITY_CODING}
