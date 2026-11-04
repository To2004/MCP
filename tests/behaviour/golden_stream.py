"""INF-1: a seeded synthetic message stream and the golden verdicts of designs v1-v4 on it.

The stream is built here, from a fixed seed, so the pin never depends on the simulator or on
a log. It covers what the v5 legacy fixes and the v5 interfaces touch:

- seven callers over 30 days (one of them a bot, one a newcomer from day 15, and one who comes
  back on day 97, after his first days have left the 90-day memory), so warm-up, onboarding,
  habits and the 90-day memory all take part;
- read and write tools on assets of sensitivity 1-5, one asset with no sensitivity, and calls
  the binding could not resolve (no asset);
- sessions opened with ``initialize`` (both the direct form and the gateway's form: a request
  with no session id, then the server's session), a session that never initialized, and
  sessionless calls, including sessionless calls to ``merge_pr``, which ``requires_before``
  guards (E1 and E2 act on these);
- a first use of one asset recorded twice for the same caller (a clock step back across
  midnight), followed by two other callers' first uses of it within 7 days (RF9);
- a network change, a client change, a burst, a sweep, oversized requests, a read-then-write
  and a blind write to a sensitivity-5 asset;
- what later v5 batches rewrite: ``resources/read`` and ``prompts/get`` requests (AI-10),
  IPv6 addresses in two /48 networks and an address that is not an IP (B10's ``network_of``),
  and clients that are capitalised, padded, version-less or empty (B2/E11's
  ``client_family``).

Each golden file pins, for one design: every verdict, floats rounded to 1e-9 (portable, and
per message, for diagnosis); the SHA-256 of every verdict's exact floats (``float.hex``),
checked on the platform it was recorded on; the SHA-256 of the engine's snapshot at the end;
and every verdict after a snapshot -> JSON -> restore into a fresh engine at day 15 (open
sessions are not saved, so this pins what a restart forgets).

Regenerate the golden files only when a change to v1-v4 output is intended, and name it:

    uv run python -m tests.behaviour.golden_stream --reason "E1: <why v4 output changes>"

which rewrites ``golden/engine_v*.json.gz`` and appends that line to ``golden/CHANGELOG.md``.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import platform
import random
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from mcp_security.behaviour import BehaviourConfig, BehaviourEngine, Message, Verdict

SEED = 20_261_026
DAY_S = 86_400.0
HOUR_S = 3_600.0
MINUTE_S = 60.0
START = datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp()  # a Monday, 00:00 UTC
DAYS = 30
RESTORE_DAY = 15  # the restart: snapshot, JSON, restore into a fresh engine
SATURDAY, SUNDAY = 5, 6
ROUND_DIGITS = 9
GOLDEN_DIR = Path(__file__).parent / "golden"
CHANGELOG = GOLDEN_DIR / "CHANGELOG.md"
PINNED_DESIGNS = ("v1", "v2", "v3", "v4")
GZIP_LEVEL = 9

CALL, INIT, LIST = "tools/call", "initialize", "tools/list"
RESOURCE_READ, PROMPT_GET = "resources/read", "prompts/get"  # scored by v5 only (AI-10)
IPV6_ADDRESSES = ("2001:db8:1::5", "2001:db8:2::5")  # two /48 networks
NOT_AN_IP = "unix-socket"
ODD_CLIENTS = ("Cursor/0.9", " claude-code /2", "")  # capitalised, padded, empty
VERSIONLESS_CLIENT = "claude-desktop"
READ, WRITE = "read", "write"
TOOLS = {
    "get_file": READ,
    "list_issues": READ,
    "search_code": READ,
    "review_pr": READ,
    "create_issue": WRITE,
    "write_file": WRITE,
    "merge_pr": WRITE,
}
SENSITIVITY: dict[str, int | None] = {
    "repo-public": 1,
    "repo-docs": 2,
    "repo-app": 3,
    "repo-infra": 4,
    "repo-secrets": 5,
    "repo-vault": 5,  # never read: a write to it is blind
    "repo-shared": 2,  # the RF9 asset
    "repo-unregistered": None,  # resolved, but not in the register
}
SWEEP_ASSETS = tuple(f"repo-x{i:02d}" for i in range(16))
SENSITIVITY.update({a: 1 + i % 3 for i, a in enumerate(SWEEP_ASSETS)})

#: The policy every pinned design runs with: written limits and a required earlier step.
POLICY = {
    "burst_per_minute": 12,
    "request_limit_bytes": 8_000,
    "request_limit_by_tool": {"write_file": 40_000},
    "many_assets_per_hour": 8,
    "requires_before": {"merge_pr": frozenset({"review_pr"})},
}

#: Fields a message had before v5: the stream digest reads only these, so adding fields to
#: ``Message`` never changes it.
STREAM_FIELDS = (
    "ts",
    "agent",
    "method",
    "session",
    "tool",
    "asset",
    "sensitivity",
    "operation",
    "address",
    "client",
    "size",
)


def golden_config(design: str) -> BehaviourConfig:
    """The pinned policy for ``design``."""
    return BehaviourConfig(design=design, **POLICY)


@dataclass(frozen=True)
class Caller:
    """One person's working pattern in the stream."""

    name: str
    hours: tuple[float, float]  # first and last hour a session may start (UTC)
    network: str  # the /16 his addresses fall in, as "a.b"
    client: str  # his client, "name/version"
    days: tuple[int, ...]
    calls: int  # calls per session
    sessions: int  # sessions per working day
    sessionless: int  # extra sessionless calls per working day
    tools: tuple[str, ...]
    assets: tuple[str, ...]
    gateway_init: bool = False  # initialize as the gateway sees it: no session id, then one


WEEKDAYS = tuple(d for d in range(DAYS) if d % 7 not in (SATURDAY, SUNDAY))
CALLERS = (
    Caller(
        "alice",
        (8.5, 15.5),
        "10.1",
        "claude-desktop/1.0",
        WEEKDAYS,
        8,
        2,
        2,
        ("get_file", "list_issues", "search_code", "create_issue", "write_file"),
        ("repo-docs", "repo-app", "repo-public", "repo-unregistered"),
        gateway_init=True,
    ),
    Caller(
        "bob",
        (13.0, 20.0),
        "10.2",
        "claude-code/1.0",
        WEEKDAYS,
        7,
        2,
        0,
        ("get_file", "search_code", "list_issues", "create_issue"),
        ("repo-app", "repo-docs", "repo-infra"),
        gateway_init=True,
    ),
    Caller(
        "carol",
        (8.0, 14.0),
        "10.3",
        "cursor/0.9",
        WEEKDAYS,
        6,
        2,
        1,
        ("review_pr", "get_file", "list_issues"),
        ("repo-app", "repo-docs", "repo-public"),
    ),
    Caller(
        "dave",
        (7.0, 13.0),
        "10.4",
        "claude-code/1.0",
        (*WEEKDAYS, 26),
        6,
        2,
        1,
        ("get_file", "write_file", "list_issues"),
        ("repo-infra", "repo-secrets", "repo-app"),
    ),
    Caller(
        "erin",
        (9.0, 16.0),
        "10.5",
        "claude-desktop/1.0",
        tuple(d for d in WEEKDAYS if d >= 15),
        6,
        2,
        0,
        ("get_file", "list_issues", "search_code", "create_issue"),
        ("repo-docs", "repo-public", "repo-app"),
    ),
    Caller(
        "frank",
        (10.0, 15.0),
        "10.6",
        "claude-desktop/1.0",
        (0, 1, 2, 3, 4, 97, 98, 99),
        6,
        1,
        0,
        ("get_file", "list_issues", "create_issue"),
        ("repo-docs", "repo-app"),
    ),
)
BOT = "ci-bot"
BOT_ADDRESS, BOT_CLIENT = "10.9.0.5", "ci-runner/3.2"


class _Stream:
    """Collects messages with their arrival position, then puts them in arrival order."""

    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)
        self.items: list[tuple[float, int, Message]] = []
        self.late: list[tuple[int, Message]] = []  # (index of the message it follows, message)

    def add(self, message: Message) -> None:
        self.items.append((message.ts, len(self.items), message))

    def call(
        self,
        ts: float,
        agent: str,
        tool: str,
        asset: str | None,
        session: str | None,
        address: str,
        client: str,
        size: int | None = None,
    ) -> Message:
        operation = TOOLS[tool]
        if size is None:
            low, high = (150, 600) if operation == READ else (400, 3_000)
            size = self.rng.randint(low, high)
        message = Message(
            ts,
            agent,
            CALL,
            session,
            tool=tool,
            asset=asset,
            sensitivity=SENSITIVITY.get(asset) if asset else None,
            operation=operation,
            address=address,
            client=client,
            size=size,
        )
        self.add(message)
        return message

    def ordered(self) -> list[Message]:
        out = [m for _, _, m in sorted(self.items, key=lambda item: (item[0], item[1]))]
        for after, message in self.late:  # arrival order, not time order: inserted after
            out.insert(out.index(after) + 1, message)
        return out


def _address(stream: _Stream, network: str) -> str:
    return f"{network}.{stream.rng.randint(0, 9)}.{stream.rng.randint(2, 250)}"


def _session(stream: _Stream, who: Caller, day: int, index: int) -> None:
    """``initialize``, ``tools/list`` and ``who.calls`` calls, a few minutes apart."""
    rng = stream.rng
    t0 = START + day * DAY_S + rng.uniform(*who.hours) * HOUR_S
    sid = f"{who.name}-{day}-{index}"
    network = "172.16" if who.name == "bob" and day >= 12 else who.network  # network change
    client = "cursor/0.9" if who.name == "alice" and day >= 18 else who.client  # client change
    address = _address(stream, network)
    if who.gateway_init:  # the request carries no session; the server's reply opens one
        stream.add(Message(t0 - 2, who.name, INIT, None, address=address, client=client, size=180))
        stream.add(Message(t0 - 1, who.name, INIT, sid))
    else:
        stream.add(Message(t0 - 1, who.name, INIT, sid, address=address, client=client, size=180))
    stream.add(Message(t0, who.name, LIST, sid, address=address, client=client, size=60))
    ts = t0
    for _ in range(who.calls):
        ts += rng.uniform(20.0, 400.0)
        tool = rng.choice(who.tools)
        asset = rng.choice(who.assets)
        if tool == "search_code" and rng.random() < 0.5:
            asset = None  # the binding could not tell which repository
        if tool == "review_pr" and who.name == "carol":  # a review, then the merge it allows
            stream.call(ts, who.name, "review_pr", asset, sid, address, client)
            ts += rng.uniform(30.0, 120.0)
            tool = "merge_pr"
        if who.name == "dave" and tool == "write_file" and rng.random() < 0.5:
            stream.call(ts, who.name, "get_file", "repo-secrets", sid, address, client)
            ts += rng.uniform(10.0, 60.0)  # read one sensitive asset, write another
            asset = "repo-infra"
        stream.call(ts, who.name, tool, asset, sid, address, client)


def _sessionless(stream: _Stream, who: Caller, day: int) -> None:
    rng = stream.rng
    for _ in range(who.sessionless):
        ts = START + day * DAY_S + rng.uniform(*who.hours) * HOUR_S
        address = _address(stream, who.network)
        stream.call(
            ts,
            who.name,
            rng.choice(who.tools),
            rng.choice(who.assets),
            None,
            address,
            f"{who.name}-cli/2.0",
        )


def _bot(stream: _Stream) -> None:
    """A CI bot, every day: a nightly batch (a burst and a sweep, ending in a sessionless
    merge, which its policy guards) and a file read every two hours."""
    for day in range(DAYS):
        t0 = START + day * DAY_S + 2 * HOUR_S
        for i, asset in enumerate(SWEEP_ASSETS[:10]):
            stream.call(t0 + 3.0 * i, BOT, "get_file", asset, None, BOT_ADDRESS, BOT_CLIENT)
        for i in range(5):
            stream.call(
                t0 + 30.0 + i, BOT, "list_issues", "repo-app", None, BOT_ADDRESS, BOT_CLIENT
            )
        stream.call(t0 + 40.0, BOT, "merge_pr", "repo-app", None, BOT_ADDRESS, BOT_CLIENT)
        for hour in range(4, 24, 2):
            ts = START + day * DAY_S + hour * HOUR_S + stream.rng.uniform(0.0, 300.0)
            stream.call(ts, BOT, "get_file", "repo-app", None, BOT_ADDRESS, BOT_CLIENT)


def _events(stream: _Stream) -> None:
    """The one-off events each v5 change or dimension needs to see at least once."""
    day = START + 0 * DAY_S
    at = lambda d, hour: day + d * DAY_S + hour * HOUR_S  # noqa: E731 — local shorthand
    alice_addr, dave_addr, bob_addr = "10.1.3.3", "10.4.3.3", "172.16.4.4"
    # oversized requests: over write_file's own limit, and over the default limit
    stream.call(
        at(9, 10.0),
        "alice",
        "write_file",
        "repo-app",
        None,
        alice_addr,
        "claude-desktop/1.0",
        size=60_000,
    )
    stream.call(
        at(9, 10.1),
        "alice",
        "create_issue",
        "repo-docs",
        None,
        alice_addr,
        "claude-desktop/1.0",
        size=20_000,
    )
    # a session that never sent initialize, for a caller who normally does
    for i in range(5):
        stream.call(
            at(24, 11.0) + 60.0 * i,
            "alice",
            "get_file",
            "repo-docs",
            "alice-noinit-24",
            alice_addr,
            "cursor/0.9",
        )
    # a burst: 25 calls, 2 s apart
    for i in range(25):
        stream.call(
            at(20, 11.0) + 2.0 * i,
            "dave",
            "get_file",
            "repo-app",
            "dave-burst-20",
            dave_addr,
            "claude-code/1.0",
        )
    # a sweep: 15 distinct assets in half an hour
    for i, asset in enumerate(SWEEP_ASSETS[:15]):
        stream.call(
            at(22, 15.0) + 120.0 * i,
            "bob",
            "get_file",
            asset,
            "bob-sweep-22",
            bob_addr,
            "claude-code/1.0",
        )
    # a blind write: a sensitivity-5 asset he has never read
    stream.call(
        at(21, 12.0),
        "dave",
        "write_file",
        "repo-vault",
        "dave-blind-21",
        dave_addr,
        "claude-code/1.0",
    )
    # sessionless merges (E1): with no review, and after a sessionless review
    stream.call(at(10, 9.5), "carol", "merge_pr", "repo-app", None, "10.3.1.1", "carol-cli/2.0")
    stream.call(at(11, 9.5), "carol", "merge_pr", "repo-docs", None, "10.3.1.1", "carol-cli/2.0")
    stream.call(at(25, 9.0), "carol", "review_pr", "repo-app", None, "10.3.1.1", "carol-cli/2.0")
    stream.call(at(25, 9.1), "carol", "merge_pr", "repo-app", None, "10.3.1.1", "carol-cli/2.0")
    # RF9: dave's first use of repo-shared is recorded twice (a late message, stamped before
    # midnight, arrives after his first call of the next day); carol and alice follow.
    stream.call(at(16, 23.8), "dave", "get_file", "repo-app", None, dave_addr, "claude-code/1.0")
    first = stream.call(
        at(17, 0.003), "dave", "get_file", "repo-shared", None, dave_addr, "claude-code/1.0"
    )
    late = Message(
        at(17, 0.0) - 5.0,
        "dave",
        CALL,
        None,
        tool="get_file",
        asset="repo-shared",
        sensitivity=SENSITIVITY["repo-shared"],
        operation=READ,
        address=dave_addr,
        client="claude-code/1.0",
        size=210,
    )
    stream.late.append((first, late))
    stream.call(at(17, 8.5), "carol", "get_file", "repo-shared", None, "10.3.1.1", "carol-cli/2.0")
    stream.call(at(18, 10.0), "alice", "get_file", "repo-shared", None, alice_addr, "cursor/0.9")
    _later_inputs(stream, at)


def _later_inputs(stream: _Stream, at: Callable[[int, float], float]) -> None:
    """Inputs whose code later v5 batches rewrite: non-tool requests v5 scores (AI-10), IPv6
    and non-IP addresses (B10), and odd client values (B2, E11). Explicit sizes, so these
    draw nothing from the generator and every earlier message stays as it was."""
    alice_addr, erin_addr = "10.1.3.3", "10.5.2.2"
    for day, method, agent, session, address, client in (
        (11, RESOURCE_READ, "alice", "alice-11-0", alice_addr, "claude-desktop/1.0"),
        (13, PROMPT_GET, "carol", None, "10.3.1.1", "carol-cli/2.0"),
        (19, RESOURCE_READ, "erin", None, erin_addr, "claude-desktop/1.0"),
        (23, PROMPT_GET, "bob", "bob-23-0", "172.16.4.4", "claude-code/1.0"),
    ):
        stream.add(
            Message(at(day, 14.2), agent, method, session, address=address, client=client, size=140)
        )
    for day, address in zip((19, 23), IPV6_ADDRESSES, strict=True):
        stream.call(
            at(day, 12.5), "alice", "get_file", "repo-docs", None, address, "cursor/0.9", size=300
        )
    stream.call(
        at(24, 9.5), "carol", "list_issues", "repo-app", None, NOT_AN_IP, "carol-cli/2.0", size=250
    )
    for day, client in zip((20, 22, 26), ODD_CLIENTS, strict=True):
        stream.call(
            at(day, 10.5), "erin", "list_issues", "repo-public", None, erin_addr, client, size=260
        )
    stream.call(
        at(27, 10.5), "erin", "get_file", "repo-docs", None, erin_addr, VERSIONLESS_CLIENT, size=270
    )


def build_stream(seed: int = SEED) -> list[Message]:
    """The INF-1 stream, in arrival order."""
    stream = _Stream(seed)
    for who in CALLERS:
        for day in who.days:
            for index in range(who.sessions):
                _session(stream, who, day, index)
            _sessionless(stream, who, day)
    _bot(stream)
    _events(stream)
    return stream.ordered()


def stream_digest(messages: list[Message]) -> str:
    """SHA-256 of the stream's pre-v5 fields: changes only when the fixture itself does."""
    rows = [[getattr(m, name) for name in STREAM_FIELDS] for m in messages]
    return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()


def _rounded(value: float | None) -> float | None:
    return None if value is None else round(value, ROUND_DIGITS)


def _hex(value: float | None) -> str | None:
    return None if value is None else float(value).hex()


def verdict_row(verdict: Verdict) -> list:
    """What the pin records of one verdict, floats rounded to 1e-9."""
    return [
        _rounded(verdict.multiplier),
        verdict.strongest,
        _rounded(verdict.score),
        {d: _rounded(s) for d, s in verdict.scores.items()},
        verdict.learning,
    ]


def exact_digest(verdicts: list[Verdict]) -> str:
    """SHA-256 of the verdicts' exact floats (``float.hex``): equal only if bit-identical."""
    rows = [
        [
            _hex(v.multiplier),
            v.strongest,
            _hex(v.score),
            sorted((d, _hex(s)) for d, s in v.scores.items()),
            v.learning,
        ]
        for v in verdicts
    ]
    return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()


def snapshot_digest(engine: BehaviourEngine) -> str:
    """SHA-256 of everything the engine learned, as its snapshot (JSON, keys sorted)."""
    data = json.dumps(engine.snapshot(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode()).hexdigest()


def this_platform() -> dict[str, str]:
    """Where exact digests were recorded: the transcendental functions (``pow``) may differ
    in the last bit on another machine or C library, so exact digests are compared only on
    the same one."""
    return {"machine": platform.machine(), "platform": sys.platform}


def verdicts(config: BehaviourConfig, messages: list[Message]) -> tuple[list[Verdict], str]:
    """Every verdict of a fresh engine over ``messages``, and its snapshot digest after."""
    engine = BehaviourEngine(config)
    out = [engine.observe(m) for m in messages]
    return out, snapshot_digest(engine)


def restore_index(messages: list[Message]) -> int:
    """The first message on or after :data:`RESTORE_DAY`: where the restart happens."""
    return next(i for i, m in enumerate(messages) if m.ts >= START + RESTORE_DAY * DAY_S)


def restarted(config: BehaviourConfig, messages: list[Message]) -> list[Verdict]:
    """The verdicts from :func:`restore_index` on, when the engine is saved there (snapshot,
    JSON text) and restored into a fresh engine, as a gateway restart does."""
    at = restore_index(messages)
    engine = BehaviourEngine(config)
    for message in messages[:at]:
        engine.observe(message)
    fresh = BehaviourEngine(config)
    fresh.restore(json.loads(json.dumps(engine.snapshot())))
    return [fresh.observe(m) for m in messages[at:]]


def golden_path(design: str) -> Path:
    return GOLDEN_DIR / f"engine_{design}.json.gz"


def load_golden(design: str) -> dict:
    """A pinned design's recorded verdicts and the stream digest they were recorded on."""
    with gzip.open(golden_path(design), "rt", encoding="utf-8") as handle:
        return json.load(handle)


def write_golden(design: str, messages: list[Message]) -> None:
    """Record ``design``'s verdicts on ``messages`` (byte-stable gzip: no name, mtime 0)."""
    config = golden_config(design)
    observed, snapshot = verdicts(config, messages)
    after = restarted(config, messages)
    payload = {
        "design": design,
        "seed": SEED,
        "stream_sha256": stream_digest(messages),
        "messages": len(messages),
        "verdicts": [verdict_row(v) for v in observed],
        "exact_sha256": exact_digest(observed),
        "recorded_on": this_platform(),
        "snapshot_sha256": snapshot,
        "restore": {
            "at": restore_index(messages),
            "verdicts": [verdict_row(v) for v in after],
            "exact_sha256": exact_digest(after),
        },
    }
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    with golden_path(design).open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=GZIP_LEVEL, mtime=0) as gz:
            gz.write(data)


def main() -> None:
    """Rewrite the v1-v4 golden files and append the reason to the changelog."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reason", required=True, help="the change that moves v1-v4 output")
    args = parser.parse_args()
    messages = build_stream()
    for design in PINNED_DESIGNS:
        write_golden(design, messages)
    with CHANGELOG.open("a", encoding="utf-8") as log:
        log.write(f"- {date.today().isoformat()}: regenerated engine_v1-v4. {args.reason}\n")
    print(f"{len(messages)} messages; golden files rewritten in {GOLDEN_DIR}")


if __name__ == "__main__":
    main()
