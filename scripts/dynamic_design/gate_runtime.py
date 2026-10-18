"""A gate-shaped wrapper around the dynamic_v2 scoring math.

``BreadthScorer`` in :mod:`dynamic_v2` keys history by *server kind*
(``"github"``, ``"slack"``, ...). That is correct for the eval corpora, where each
kind is exercised by exactly one org, but wrong for a real gate: two tenants
both running a GitHub MCP would pool their argument baselines, and one tenant
running two separate GitHub instances would pool those too.

This module fixes the key, changes nothing about the math. A ``Connection``
identifies *who* the history belongs to (``org_id``, ``server_id`` — the
specific upstream connection) separately from *which schema* applies
(``kind`` — which scan/spec table to read). History and tool-call counts are
keyed by the connection; the spec tables loaded by :func:`dynamic_v2.load_specs`
stay shared and read-only, keyed by kind, exactly as today — an org's tenancy
has no bearing on what a GitHub MCP's ``per_page`` argument means.

A background thread stands in for a Redis write-behind: :meth:`GateScorer.score`
never blocks on persistence. ``snapshot_async`` hands a connection's state to a
queue and returns immediately; a worker drains it to disk (a stand-in for
Redis) so a restarted or newly-owning replica can rehydrate instead of
starting fully cold.

    python3 scripts/dynamic_design/gate_runtime.py
"""

from __future__ import annotations

import bisect
import json
import queue
import sys
import threading
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dynamic_v2 import (  # noqa: E402
    B_MAX,
    B_MIN,
    BREADTH_WEIGHT,
    DEFAULT_BREADTH,
    ESCALATE_AT,
    L_ALPHA,
    L_MAX,
    L_MIN,
    MEASURABLE,
    MIN_HISTORY,
    NO_SIGNAL,
    load_specs,
    parse_quantity,
    span_of,
)

Scope = tuple[str, str]  # (org_id, server_id) -- the isolation unit for state


@dataclass(frozen=True)
class Connection:
    """Who a call belongs to (``scope``) and which schema applies (``kind``).

    Two different fields on purpose: tenancy and schema vary independently.
    An org's two GitHub instances share ``kind`` but not ``scope``; two orgs on
    the same GitHub MCP share neither.
    """

    org_id: str
    server_id: str
    kind: str

    @property
    def scope(self) -> Scope:
        return (self.org_id, self.server_id)


@dataclass(frozen=True)
class ToolProfile:
    """Everything about a (kind, tool) pair that no single call can change.

    Built once and cached. Measured cost of NOT caching this: recomputing the
    "which inputs are range-typed" filter from the raw spec dict on every call
    was 12.8% of total score() time on a 100k-call profile, entirely spent
    re-deriving a value that is fixed the moment the scan is loaded.
    """

    measurable: list[tuple[str, dict]]  # (name, spec) for gradeable inputs, spec order preserved
    range_names: list[str]              # input names whose kind is "range"


class GateScorer:
    """Per-call ``B x L``, isolated per :class:`Connection`, spec tables shared per kind."""

    def __init__(self, specs: dict[str, dict]) -> None:
        self.specs = specs  # {kind: {tool: {arg: spec}}} -- shared, read-only
        self.history: dict[tuple, list[float]] = defaultdict(list)
        self.arrival: dict[tuple, deque] = defaultdict(deque)
        self.tool_calls: dict[Scope, Counter] = defaultdict(Counter)
        self.max_history = 4000
        # Derived from `specs` alone -- never invalidated at runtime, since specs
        # never change after load. Populated lazily, on first use of each (kind, tool).
        self._tool_profile_cache: dict[tuple[str, str], ToolProfile | None] = {}
        self._widest_reach_cache: dict[tuple[str, str], int] = {}
        # Incremental mirror of `tool_calls`, so `likelihood_factor` never re-sorts
        # the whole per-scope distribution. See `_record_tool_call`.
        self._tool_count_sorted: dict[Scope, list[int]] = defaultdict(list)
        self._tool_count_total: dict[Scope, int] = defaultdict(int)

    def _tool_profile(self, kind: str, tool: str) -> ToolProfile | None:
        cache_key = (kind, tool)
        if cache_key in self._tool_profile_cache:
            return self._tool_profile_cache[cache_key]
        by_arg = self.specs.get(kind, {}).get(tool)
        profile = None
        if by_arg:
            measurable = [(name, spec) for name, spec in by_arg.items()
                          if spec.get("kind", "none") not in ("none", "unresolved", "range")]
            range_names = [n for n, sp in by_arg.items() if sp.get("kind") == "range"]
            profile = ToolProfile(measurable, range_names)
        self._tool_profile_cache[cache_key] = profile
        return profile

    def quantities(self, conn: Connection, tool: str, args: dict):
        profile = self._tool_profile(conn.kind, tool)
        if profile is None:
            return
        for name, spec in profile.measurable:
            if name in args:
                quantity = parse_quantity(args[name], spec["kind"], spec.get("parse"))
                yield name, quantity, spec, "value" if quantity is not None else "unreadable"
                continue
            declared = spec.get("default")
            if declared is not None:
                quantity = parse_quantity(declared, spec["kind"], spec.get("parse"))
                if quantity is not None:
                    yield name, quantity, spec, "default"
                continue
            yield name, None, spec, "omitted"

        if profile.range_names:
            present = [n for n in profile.range_names if n in args]
            span = span_of(args, present)
            if span is not None:
                yield "<span:days>", span, {"kind": "range", "ceiling": None}, "value"
            elif not present:
                yield "<span:days>", None, {"kind": "range", "ceiling": None}, "omitted"

    def _remember(self, key: tuple, quantity: float) -> None:
        seen, order = self.history[key], self.arrival[key]
        bisect.insort(seen, quantity)
        order.append(quantity)
        if len(order) > self.max_history:
            oldest = order.popleft()
            index = bisect.bisect_left(seen, oldest)
            if index < len(seen) and seen[index] == oldest:
                del seen[index]

    def deviation(self, key: tuple, quantity: float | None) -> tuple[float, str]:
        seen = self.history[key]
        if len(seen) < MIN_HISTORY:
            return 1.0, "no history"
        n = len(seen)
        q1 = seen[n // 4]
        if quantity is None:
            q3 = seen[(3 * n) // 4 - (1 if (3 * n) % 4 == 0 else 0)]
            quantity = q3
        edge = seen[min(len(seen) - 1, (ESCALATE_AT * len(seen)) // 100)]
        fence = edge * 2.5
        if quantity > edge:
            reach = min((quantity - edge) / (fence - edge), 1.0) if fence > edge else 1.0
            return 1.0 + (B_MAX - 1.0) * reach, "wide"
        if q1 <= seen[0]:
            return 1.0, "no floor"
        if quantity >= q1:
            return 1.0, "ordinary"
        floor = seen[0]
        position = min(max((quantity - floor) / (q1 - floor), 0.0), 1.0) if q1 > floor else 1.0
        return B_MIN + (1.0 - B_MIN) * position, "narrow"

    def widest_reach(self, conn: Connection, tool: str) -> int:
        """A pure function of (kind, tool) -- cached, since specs never change at runtime.

        Measured cost of NOT caching this: recomputing it from the raw spec dict on
        every gradeable argument of every call was 5.2% of total score() time, all of
        it re-deriving the same answer for the same (kind, tool) every time.
        """
        cache_key = (conn.kind, tool)
        cached = self._widest_reach_cache.get(cache_key)
        if cached is not None:
            return cached
        by_arg = self.specs.get(conn.kind, {}).get(tool) or {}
        levels = [spec.get("breadth") or DEFAULT_BREADTH for spec in by_arg.values()
                  if spec.get("kind") in MEASURABLE]
        if not levels:
            levels = [spec.get("breadth") or DEFAULT_BREADTH for spec in by_arg.values()]
        result = max(levels) if levels else DEFAULT_BREADTH
        self._widest_reach_cache[cache_key] = result
        return result

    def _relative_weight(self, conn: Connection, tool: str, spec: dict) -> float:
        level = spec.get("breadth") or DEFAULT_BREADTH
        most_central = BREADTH_WEIGHT.get(self.widest_reach(conn, tool), 0.0)
        if most_central <= 0:
            return 0.0
        return min(BREADTH_WEIGHT.get(level, 0.0) / most_central, 1.0)

    def breadth_factor(self, conn: Connection, tool: str, args: dict) -> tuple[float, list[str]]:
        discounts, reasons, pending = [], [], []
        for name, quantity, spec, source in self.quantities(conn, tool, args):
            key = (conn.scope, tool, name)
            b, decided = self.deviation(key, quantity)
            if decided not in NO_SIGNAL:
                weight = self._relative_weight(conn, tool, spec)
                discounts.append(1.0 - weight * (1.0 - b))
                shown = source if quantity is None else f"{quantity:g}"
                tag = "" if source == "value" else f",{source}"
                reasons.append(f"{name}={shown}->{b:.2f}"
                               f"(b{spec.get('breadth') or '?'},w{weight:.2f},{decided}{tag})")
            if source in ("value", "default"):
                pending.append((key, quantity))
        for key, quantity in pending:
            self._remember(key, quantity)
        return (max(discounts) if discounts else 1.0), reasons

    def likelihood_factor(self, conn: Connection, tool: str) -> tuple[float, str]:
        """Identical formula to ``dynamic_v2``; reads the incremental mirror, not a resort.

        ``used`` is ``sorted(c for c in counts.values() if c)`` recomputed from scratch
        by the reference implementation. Measured cost of that: 32.5% of total score()
        time on a 100k-call profile, entirely spent re-sorting a distribution that only
        ever changes by one counter moving by one, one call at a time.
        """
        used = self._tool_count_sorted.get(conn.scope)
        if not used:
            return 1.0, "no history"
        total = self._tool_count_total[conn.scope]
        reference = used[len(used) // 2] / total
        share = (self.tool_calls[conn.scope][tool] + L_ALPHA * reference) / (total + L_ALPHA)
        ratio = share / reference if reference else 1.0
        if ratio < 1.0:
            raw = 1.0 + (L_MAX - 1.0) * (1.0 - ratio)
        else:
            raw = 1.0 - (1.0 - L_MIN) * (1.0 - 1.0 / ratio)
        exposed = len(self.specs.get(conn.kind) or self.tool_calls[conn.scope]) or 1
        confidence = total / (total + MIN_HISTORY * exposed)
        factor = 1.0 + (raw - 1.0) * confidence
        if confidence < 0.5:
            return factor, (f"{ratio:.2f}x the median tool, held back to "
                            f"{confidence:.0%} on {total} calls")
        return factor, f"{ratio:.2f}x the median tool"

    def _record_tool_call(self, conn: Connection, tool: str) -> None:
        """Increment the call count and keep ``_tool_count_sorted`` in step with it.

        Bisect insert/evict on a list capped at the number of tools this connection's
        kind exposes (tens, not thousands) -- the same trade already made for argument
        history, applied to the one other place a full resort was happening per call.
        """
        counts = self.tool_calls[conn.scope]
        old = counts[tool]
        counts[tool] = old + 1
        sorted_counts = self._tool_count_sorted[conn.scope]
        if old:
            index = bisect.bisect_left(sorted_counts, old)
            if index < len(sorted_counts) and sorted_counts[index] == old:
                del sorted_counts[index]
        bisect.insort(sorted_counts, old + 1)
        self._tool_count_total[conn.scope] += 1

    def score(self, conn: Connection, tool: str, args: dict) -> tuple[float, list[str]]:
        b, reasons = self.breadth_factor(conn, tool, args)
        lik, why = self.likelihood_factor(conn, tool)
        self._record_tool_call(conn, tool)
        reasons.append(f"L={lik:.2f}({why})")
        return b * lik, reasons

    # -- persistence: one connection's numeric state, nothing schema-related --

    def snapshot(self, conn: Connection) -> dict:
        """Everything needed to rehydrate one connection. No spec data — that's shared."""
        prefix = conn.scope
        hist = {f"{tool}\x1f{arg}": self.history[k]
                for k, tool, arg in self._keys_for(prefix)
                for k in [(prefix, tool, arg)]}
        arr = {f"{tool}\x1f{arg}": list(self.arrival[k])
               for k, tool, arg in self._keys_for(prefix)
               for k in [(prefix, tool, arg)]}
        return {"history": hist, "arrival": arr,
                "tool_calls": dict(self.tool_calls[prefix])}

    def _keys_for(self, scope: Scope):
        for k in list(self.history):
            if k[0] == scope:
                yield k, k[1], k[2]

    def rehydrate(self, conn: Connection, payload: dict) -> None:
        for combo, values in payload.get("history", {}).items():
            tool, arg = combo.split("\x1f")
            self.history[(conn.scope, tool, arg)] = list(values)
        for combo, values in payload.get("arrival", {}).items():
            tool, arg = combo.split("\x1f")
            self.arrival[(conn.scope, tool, arg)] = deque(values)
        counts = Counter(payload.get("tool_calls", {}))
        self.tool_calls[conn.scope] = counts
        # `_tool_count_sorted`/`_tool_count_total` are a mirror of `tool_calls`, not
        # snapshotted state -- rebuilt once here rather than carried in the payload, the
        # same one-time cost `likelihood_factor` no longer pays on every call.
        self._tool_count_sorted[conn.scope] = sorted(c for c in counts.values() if c)
        self._tool_count_total[conn.scope] = sum(counts.values())


class SnapshotStore:
    """Background write-behind so persistence never sits in the score() path.

    A real deployment would push these onto Redis/a queue; a local JSON file per
    connection is the same shape without standing up infrastructure to prove the
    pattern. The queue hand-off is the only cost score() ever pays for this.
    """

    def __init__(self, directory: Path) -> None:
        self.dir = directory
        self.dir.mkdir(parents=True, exist_ok=True)
        self._q: queue.Queue = queue.Queue()
        self._writes = 0
        self._thread = threading.Thread(target=self._drain, daemon=True)
        self._thread.start()

    def enqueue(self, conn: Connection, payload: dict) -> float:
        """Hand off a snapshot; returns the caller-side cost in seconds."""
        t0 = time.perf_counter()
        self._q.put((conn.org_id, conn.server_id, payload))
        return time.perf_counter() - t0

    def _drain(self) -> None:
        while True:
            org_id, server_id, payload = self._q.get()
            path = self.dir / f"{org_id}__{server_id}.json"
            path.write_text(json.dumps(payload))
            self._writes += 1
            self._q.task_done()

    def wait_idle(self) -> None:
        self._q.join()


def load_gate_specs() -> dict[str, dict]:
    """Same shared spec tables dynamic_v2 uses, keyed by server kind."""
    return load_specs()
