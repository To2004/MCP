"""The framework for one route: static artifacts loaded once, then one call scored at a time.

This connects the existing pieces and adds no risk logic of its own:

- **static** — the scan's cells: ``binding.scoring.MatrixScorer`` resolves a call's
  arguments to an asset and returns that cell, with the three levels behind it;
- **dynamic** — the runtime factor ``B × L``: ``gate_runtime.GateScorer``, which learns
  from every call it scores, so calls must reach it in arrival order;
- **input rules** — stage 2: ``input_rules.evaluate_call``, the call's input level 1–5,
  reported beside the risk (how the two combine is not decided);
- **behaviour** — the dynamic layer's behaviour multiplier ×0.7–5:
  ``behaviour.BehaviourEngine``, which compares each caller with his own last 90 days
  (Typical Cadence: call rate, write rate, breadth, repetition, session duration, hour of day;
  Typical Footprint: tool, asset, network, client; Red Flags: the rules) without reading the
  arguments;
  design v4 by default, v1-v3 with ``"design"`` in the route's behaviour policy. It sees
  every request message, not only tool calls, so ``observe`` and ``session_initialized``
  must be called in arrival order too. Reported as
  ``behaviour`` and ``dynamic_risk`` = static level (1–5) × behaviour (0.7–25).

The gateway calls ``RouteScorer.score`` live, before forwarding; ``score.py`` calls it over
a saved log. Same object, same order, same numbers. Every result carries the digests of the
artifacts it came from, so a score can always be traced to the exact scan that produced it.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Protocol

from mcp_security.behaviour import BehaviourConfig, BehaviourEngine, Message, Verdict
from mcp_security.behaviour.policy import load_policy
from mcp_security.binding.scoring import MatrixScorer
from mcp_security.gateway.config import Upstream
from mcp_security.gateway.pseudonym import Pseudonymizer
from mcp_security.input_rules import CallLevel, evaluate_call

REPO_ROOT = Path(__file__).resolve().parents[3]
DYNAMIC_DIR = REPO_ROOT / "scripts" / "dynamic_design"
DEFAULT_SCORE_MAX = 125.0
GATEWAY_ORG = "gateway"
DIGEST_CHARS = 12
MICROSECONDS = 1_000_000
NO_CELLS = "no-cells"
CALL_METHOD = "tools/call"
WRITE_IMPACT = 4  # the scan's impact ladder: 4 = write, 5 = remove, 3 and below = read
STATE_VERSION = 2  # saved state: {"version", "gate", "behaviour"}; older files are gate-only

Rules = dict[str, tuple[list[dict], dict[str, int]]]


@dataclass(frozen=True)
class Artifacts:
    """Everything the static side produced for one route, and where it came from."""

    scan: dict
    specs: dict[str, dict]  # {kind: {tool: {input: breadth spec}}}
    rules: Rules | None
    kind: str
    digests: dict[str, str]  # artifact name -> sha256 of the file read
    behaviour: BehaviourConfig | None = None  # the behaviour layer's policy; None = defaults

    @property
    def scanned_catalog(self) -> str | None:
        """SHA-256 of the tool list the scan was run on, when the scan recorded it."""
        return (self.scan.get("catalog") or {}).get("sha256")


def load_artifacts(
    route: str,
    scan: str | None,
    breadth: str | None,
    rules: str | None,
    kind: str | None,
    behaviour_policy: str | None = None,
) -> Artifacts | None:
    """The route's static artifacts from its config paths; None for a route with no scan."""
    if not scan:
        return None
    kind = kind or route
    digests = {"scan": _digest(scan)}
    if breadth:
        specs = {kind: load_breadth(Path(breadth))}
        digests["breadth"] = _digest(breadth)
    else:
        specs = gate_runtime().load_gate_specs()
    if rules:
        digests["rules"] = _digest(rules)
    if behaviour_policy:
        digests["behaviour_policy"] = _digest(behaviour_policy)
    return Artifacts(
        scan=json.loads(Path(scan).read_text(encoding="utf-8")),
        specs=specs,
        rules=load_rules(Path(rules)) if rules else None,
        kind=kind,
        digests=digests,
        behaviour=load_policy(behaviour_policy) if behaviour_policy else None,
    )


HISTORY_SCOPES = ("route", "caller")
#: The asset lookup is a pure function of (tool, arguments) and 85% of a call's cost
#: (measured: ~180 us of ~210 us); repeated calls are common, so it is cached, bounded.
CELL_CACHE_SIZE = 65_536
#: ARG-1 (v5): scored calls waiting for the server's answer before they are committed, by
#: logical-call key. A call whose answer never comes is dropped oldest first past this bound.
MAX_PENDING_CALLS = 65_536

#: One remembered sensitive read (E14): (ts, route, asset, sensitivity, owner or None).
LedgerRead = tuple[float, str, str, int, str | None]


class ReadLedger(Protocol):
    """E14 (v5): the sensitive reads of every route whose callers share an issuer, so a read
    on one route and a write on another can make an unsafe sequence. The gateway creates one
    and gives it to each ``RouteScorer`` (Batch 2); until then no scorer uses it."""

    def note_read(
        self,
        caller: str,
        route: str,
        asset: str,
        sensitivity: int,
        ts: float,
        owner: str | None = None,
    ) -> None:
        """Remember that ``caller`` read ``asset`` (sensitivity 1-5, owned by ``owner`` when
        known: SEQ-2's foreign-owner clause) on ``route`` at ``ts``."""

    def reads_since(self, caller: str, since: float) -> list[LedgerRead]:
        """``caller``'s remembered reads at or after ``since``: (ts, route, asset,
        sensitivity, owner), oldest first."""


class RouteScorer:
    """Scores one route's calls in arrival order, with state carried from call to call.

    ``history`` says whose past the runtime factor compares a call with: ``route`` keeps
    one history for everyone on the route; ``caller`` keeps one per caller, using the
    dynamic layer's own isolation unit (its ``Connection`` scope), so no logic changes.

    v5's interfaces (Batch 0; their bodies come in Batch 2): ``pseudonymizer`` is the
    gateway's keyed pseudonym function, for touched assets the register does not name
    (AI-2); ``ledger`` is the cross-route sensitive-read ledger (E14); ``upstream`` is the
    route's entry in the routes file, whose v5 fields the scorer reads (B9d ``route_zone``
    and ``zone_map``, B10 ``shared_egress``, B1 ``baseline_key``: per agent by default, D5).
    The v5 keyword arguments of :meth:`observe`,
    :meth:`session_initialized`, :meth:`score` and :meth:`score_read` (era, app, client
    family, zone, argument bytes, logical-call key, owner) are accepted and ignored for now.
    :meth:`reply`, :meth:`score_read`, :meth:`commit` and :meth:`apply_notice` do nothing
    yet, for every design.
    """

    def __init__(
        self,
        route: str,
        artifacts: Artifacts,
        history: str = "route",
        pseudonymizer: Pseudonymizer | None = None,
        ledger: ReadLedger | None = None,
        upstream: Upstream | None = None,
    ) -> None:
        if history not in HISTORY_SCOPES:
            raise ValueError(f"history must be one of {HISTORY_SCOPES}, not {history!r}")
        self._runtime = gate_runtime()
        self.artifacts = artifacts
        self.route = route
        self.history = history
        self.pseudonymizer = pseudonymizer
        self.ledger = ledger
        self.upstream = upstream
        #: ARG-1: logical-call key -> (message, verdict) scored and not yet committed. v5
        #: fills it from Batch 2 on; v1-v4 learn in :meth:`score` and never use it.
        self._pending: OrderedDict[str, tuple[Message, Verdict]] = OrderedDict()
        self._matrix = MatrixScorer(artifacts.scan["cells"], artifacts.scan["bands"])
        self._gate = self._runtime.GateScorer(artifacts.specs)
        self._connections: dict[str, object] = {}
        self._cells: OrderedDict[tuple[str, str], object] = OrderedDict()
        self._score_max = float(artifacts.scan.get("score_max", DEFAULT_SCORE_MAX))
        self.behaviour = BehaviourEngine(artifacts.behaviour)

    def connection(self, caller: str | None):  # -> gate_runtime.Connection
        """The dynamic layer's scope for this call: the route, or the caller on it."""
        owner = caller if self.history == "caller" and caller else GATEWAY_ORG
        if owner not in self._connections:
            self._connections[owner] = self._runtime.Connection(
                org_id=owner, server_id=self.route, kind=self.artifacts.kind
            )
        return self._connections[owner]

    def observe(
        self,
        method: str | None,
        ts: float,
        caller: str | None = None,
        session: str | None = None,
        address: str | None = None,
        client: str | None = None,
        size: int = 0,
        *,
        era: str | None = None,
        app: str | None = None,
        client_family: str | None = None,
        zone: str | None = None,
        arg_bytes: int | None = None,
        logical_call: str | None = None,
    ) -> None:
        """A request message that is not a tool call (initialize, tools/list, ...): the
        behaviour layer learns the caller's origin and handshake from it.

        The keyword-only arguments are v5's engine inputs (spec 2.1), ignored until Batch 2.
        They are the keys ``behaviour_fields`` will add from the LOG-1 fields, so the
        gateway and ``score.py`` can pass its output to this method and to :meth:`score`."""
        self.behaviour.observe(
            Message(ts, caller or GATEWAY_ORG, method or "", session, address=address,
                    client=client, size=size)
        )

    def session_initialized(
        self,
        caller: str | None,
        session: str,
        ts: float,
        *,
        era: str | None = None,
        app: str | None = None,
        zone: str | None = None,
    ) -> None:
        """The server assigned ``session`` in its reply to ``initialize``: the session started
        properly (the request itself carried no session id yet). The keyword-only arguments
        are v5's inputs, ignored until Batch 2."""
        self.behaviour.observe(Message(ts, caller or GATEWAY_ORG, "initialize", session))

    def score(
        self,
        tool: str,
        args: dict,
        ts: float,
        caller: str | None = None,
        *,
        session: str | None = None,
        address: str | None = None,
        client: str | None = None,
        size: int = 0,
        era: str | None = None,
        app: str | None = None,
        client_family: str | None = None,
        zone: str | None = None,
        arg_bytes: int | None = None,
        logical_call: str | None = None,
        owner: str | None = None,
    ) -> dict:
        """Static cell, runtime factor, risk, input level and behaviour for one call; learns
        from it.

        ``era`` to ``owner`` are v5's engine inputs (spec 2.1: E3, B2, E11, B9d, ARG-1,
        EXP-1), ignored until Batch 2. ``logical_call`` is also the key :meth:`commit` takes
        for this call; ``owner`` is the touched asset's owner when the caller already knows
        it (otherwise the binding reads it)."""
        started = time.perf_counter()
        cell = self._cell(tool, args)
        factor, reasons = self._gate.score(self.connection(caller), tool, args)
        level = self._input_level(tool, args, ts)
        scan = self.artifacts.scan
        known = cell.basis != NO_CELLS
        impact = scan.get("tool_impact", {}).get(tool)
        verdict = self.behaviour.observe(Message(
            ts, caller or GATEWAY_ORG, CALL_METHOD, session, tool=tool,
            asset=cell.driver if known else None,
            sensitivity=scan.get("asset_sensitivity", {}).get(cell.driver) if known else None,
            operation=None if impact is None else ("write" if impact >= WRITE_IMPACT else "read"),
            address=address, client=client, size=size,
        ))
        elapsed = time.perf_counter() - started
        static_level = cell.severity ** (1 / 3) if known and cell.severity else None
        result = {
            "asset": cell.driver,
            "basis": cell.basis,
            "cell": cell.severity if known else None,
            "factor": round(factor, 3),
            "risk": round(min(self._score_max, cell.severity * factor), 3) if known else None,
            "input_level": level.level if level else None,
            "input_set_by": ",".join(level.set_by) if level else None,
            "behaviour": round(verdict.multiplier, 3),
            "behaviour_reason": _behaviour_reason(verdict),
            "static_level": round(static_level, 3) if static_level else None,
            "dynamic_risk": round(static_level * verdict.multiplier, 3) if static_level else None,
            "score_us": round(elapsed * MICROSECONDS),
            "reasons": "; ".join(reasons) if known else "tool not in scan",
        }
        if known:
            result |= {
                "band": scan["bands"].get(cell.driver, {}).get(tool),
                "sensitivity": scan.get("asset_sensitivity", {}).get(cell.driver),
                "impact": scan.get("tool_impact", {}).get(tool),
                "blast": scan.get("blast_radius", {}).get(f"{tool}|{cell.driver}"),
            }
        return result

    def reply(
        self, caller: str | None, method: str | None, tool: str | None, ts: float, size: int
    ) -> dict | None:
        """A reply to a scored request, for Read volume (AI-8): the reply's behaviour fields
        for its log line. Nothing yet (Batch 2), and never for v1-v4: None."""
        return None

    def score_read(
        self,
        method: str,
        name: str,
        args: dict,
        ts: float,
        caller: str | None = None,
        *,
        session: str | None = None,
        address: str | None = None,
        client: str | None = None,
        size: int = 0,
        era: str | None = None,
        app: str | None = None,
        client_family: str | None = None,
        zone: str | None = None,
        arg_bytes: int | None = None,
        logical_call: str | None = None,
        owner: str | None = None,
    ) -> dict | None:
        """A ``resources/read`` or ``prompts/get`` scored as a call (AI-10): its decision.
        Not yet (Batch 2), and never for v1-v4: None, and the request is only observed.
        The keyword-only arguments are those of :meth:`score`."""
        return None

    def commit(self, logical_call: str | None, outcome: str | None = None) -> None:
        """Learn from the call scored under ``logical_call`` once the server answered it
        (ARG-1: only an accepted call is learned; a rejected one is dropped).

        :meth:`score` keeps each v5 call it scores under its ``logical_call`` key, at most
        :data:`MAX_PENDING_CALLS` of them (oldest dropped); this pops the entry. An unknown
        or None key does nothing. Every design learns in :meth:`score` for now, so nothing
        is pending yet; v5 moves its learning here in Batch 2."""
        if logical_call is None:
            return
        self._pending.pop(logical_call, None)

    def apply_notice(self, record: dict) -> None:
        """Replay a logged ``behaviour_fold`` or ``policy_switched`` line (spec 2.9: offline
        replay folds and switches at the same point the live gateway did). Nothing yet
        (Batch 2, J3), for every design."""

    def snapshot_all(self) -> dict[str, dict]:
        """Every history owner's state, in ``GateScorer.snapshot`` format, in one pass.

        ``GateScorer.snapshot`` rescans all keys for each owner, so saving N callers that
        way costs N × keys (11.5 s at 1,000 callers, measured); this walks the state once.
        """
        gate = self._gate
        owner_of = {conn.scope: owner for owner, conn in self._connections.items()}
        out = {
            owner: {"history": {}, "arrival": {}, "tool_calls": dict(gate.tool_calls[conn.scope])}
            for owner, conn in self._connections.items()
        }
        for key, values in gate.history.items():
            scope, tool, arg = key
            if scope in owner_of:
                payload, combo = out[owner_of[scope]], f"{tool}\x1f{arg}"
                payload["history"][combo] = list(values)
                # .get, not [], so saving never adds empty entries to the live state
                payload["arrival"][combo] = list(gate.arrival.get(key, ()))
        return out

    def restore_all(self, snapshots: dict[str, dict]) -> None:
        """Load ``snapshot_all`` output back, so a restart continues where it stopped."""
        for owner, payload in snapshots.items():
            caller = None if owner == GATEWAY_ORG else owner
            self._gate.rehydrate(self.connection(caller), payload)

    def state(self) -> dict:
        """Everything learned on this route: the runtime factor's history and the behaviour
        layer's, as the gateway saves it to the route's ``state_file``."""
        return {"version": STATE_VERSION, "gate": self.snapshot_all(),
                "behaviour": self.behaviour.snapshot()}

    def load_state(self, data: dict) -> None:
        """Load ``state`` output; a file saved before the behaviour layer is gate-only."""
        if data.get("version") == STATE_VERSION:
            self.restore_all(data["gate"])
            self.behaviour.restore(data["behaviour"])
        else:
            self.restore_all(data)

    def _cell(self, tool: str, args: dict):  # -> binding.scoring result
        """The matrix lookup, memoised: same (tool, arguments), same answer."""
        key = (tool, json.dumps(args, sort_keys=True, default=str))
        hit = self._cells.get(key)
        if hit is not None:
            self._cells.move_to_end(key)
            return hit
        cell = self._cells[key] = self._matrix.score(tool, args)
        if len(self._cells) > CELL_CACHE_SIZE:
            self._cells.popitem(last=False)
        return cell

    def _input_level(self, tool: str, args: dict, ts: float) -> CallLevel | None:
        rules = self.artifacts.rules
        if not rules or tool not in rules:
            return None
        rows, assets = rules[tool]
        # The call's own time, not the clock: live and offline must agree.
        return evaluate_call(
            rows, args, assets=assets, now=datetime.fromtimestamp(ts, timezone.utc)
        )


def behaviour_fields(record: dict) -> dict:
    """Who sent a request, from where, with what, and how big — read from its log line, so
    the live gateway and an offline re-score of the log feed the behaviour layer exactly the
    same values. From Batch 2 on it also returns v5's inputs from the LOG-1 fields, under the
    keyword names :meth:`RouteScorer.score` and :meth:`RouteScorer.observe` take (``era``,
    ``app``, ``client_family``, ``zone``, ``arg_bytes``, ``logical_call``)."""
    return {
        "caller": record.get("gateway.agent_id") or record.get("gateway.agent"),
        "session": record.get("mcp.session.id"),
        "address": record.get("client.address"),
        "client": record.get("gateway.client"),
        "size": record.get("gateway.message_bytes", 0),
    }


def _behaviour_reason(verdict) -> str | None:  # -> behaviour.Verdict
    """Why the behaviour multiplier is what it is: the dimension that set it, and the others
    past the edge of ordinary (ties at the top of a review list break on those)."""
    if verdict.strongest is None:
        return "learning (warm-up)" if verdict.learning else None
    hot = [d for d in verdict.above_ordinary if d != verdict.strongest]
    text = f"{verdict.strongest} {verdict.score:.2f}"
    if verdict.learning:  # v3+: a check that needs none of his past fired in warm-up
        text += " (warm-up)"
    return f"{text}; also {', '.join(hot)}" if hot else text


def load_rules(path: Path) -> Rules:
    """Tool -> (its stage-2 rule rows, its reachable assets with their scanned level)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    rules = {}
    for tool in data["tools"]:
        rows = [arg for arg in tool["arguments"] if isinstance(arg.get("rule"), dict)]
        reach = (tool.get("policy_slice") or {}).get("assets_this_tool_can_reach", [])
        assets = {
            a["asset"]: a["scanned_level"] for a in reach if isinstance(a.get("scanned_level"), int)
        }
        rules[tool["tool_name"]] = (rows, assets)
    return rules


def load_breadth(path: Path) -> dict[str, dict]:
    """``{tool: {input: spec}}`` from one breadth-spec file (``scripts/scan_breadth.py``)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        tool: {entry["name"]: dict(entry) for entry in block["inputs"]}
        for tool, block in data["tools"].items()
    }


def gate_runtime() -> ModuleType:
    """The runtime factor lives in ``scripts/dynamic_design`` (stdlib-only scripts)."""
    if str(DYNAMIC_DIR) not in sys.path:
        sys.path.insert(0, str(DYNAMIC_DIR))
    import gate_runtime as module  # noqa: PLC0415 — path is only valid after the insert above

    return module


def _digest(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:DIGEST_CHARS]
