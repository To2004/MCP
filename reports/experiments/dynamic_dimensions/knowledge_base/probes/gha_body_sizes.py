"""Feasibility probe for the real-data ladder step 1: request-body sizes in GH Archive.

Reads GH Archive JSON lines (one hourly file, decompressed) from stdin and reports, per event
type that maps to a GitHub MCP write tool, whether the payload carries the text the MCP request
would carry (issue, comment, pull-request and review bodies) and its UTF-8 size quantiles. It
also reports how many events have an ``org`` and how many actors end in ``[bot]``.

Nothing is written to disk and no actor login is printed: only counts and quantiles. Stream the
file straight in, so no downloaded file sits next to code:

    curl -s https://data.gharchive.org/2025-06-10-12.json.gz | gzip -dc | \
        python3 -I reports/experiments/dynamic_dimensions/knowledge_base/probes/gha_body_sizes.py

Mapping to MCP tools (the GitHub MCP server's tool names, as in ``normal_org_world.TOOLS``):
IssuesEvent opened -> create_issue; IssuesEvent edited -> update_issue; IssueCommentEvent
created -> add_issue_comment; PullRequestEvent opened -> create_pull_request;
PullRequestReviewEvent created -> create_pull_request_review. PushEvent carries no file
contents, so push_files and create_or_update_file are out of reach of this step.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict

#: (event type, action or None for any) -> (MCP tool, payload object holding the text)
MAPPING: dict[tuple[str, str | None], tuple[str, str]] = {
    ("IssuesEvent", "opened"): ("create_issue", "issue"),
    ("IssuesEvent", "edited"): ("update_issue", "issue"),
    ("IssueCommentEvent", "created"): ("add_issue_comment", "comment"),
    ("PullRequestEvent", "opened"): ("create_pull_request", "pull_request"),
    ("PullRequestReviewEvent", "created"): ("create_pull_request_review", "review"),
}
QUANTILES = (0.5, 0.9, 0.99, 0.995, 0.999)
TEXT_FIELDS = ("title", "body")


def text_bytes(obj: dict) -> int | None:
    """UTF-8 bytes of the title and body the MCP request would carry; None if neither field
    is present in the payload (the archive trimmed it)."""
    present = [f for f in TEXT_FIELDS if f in obj]
    if not present:
        return None
    return sum(len((obj.get(f) or "").encode("utf-8")) for f in present)


def quantiles(values: list[int]) -> dict[str, int]:
    """Nearest-rank quantiles of ``values`` (already sorted)."""
    if not values:
        return {}
    n = len(values)
    return {f"q{q}": values[min(n - 1, int(q * n))] for q in QUANTILES} | {"max": values[-1]}


def main() -> None:
    """Read events from stdin and print one JSON summary."""
    started = time.time()
    events, with_org, bot_events, parse_errors = 0, 0, 0, 0
    by_type: Counter = Counter()
    sizes: dict[str, list[int]] = defaultdict(list)
    missing: Counter = Counter()
    fields_seen: dict[str, Counter] = defaultdict(Counter)
    for line in sys.stdin:
        try:
            event = json.loads(line)
        except ValueError:
            parse_errors += 1
            continue
        events += 1
        kind = event.get("type")
        by_type[kind] += 1
        with_org += bool(event.get("org"))
        bot_events += (event.get("actor") or {}).get("login", "").endswith("[bot]")
        payload = event.get("payload") or {}
        action = payload.get("action")
        target = MAPPING.get((kind, action)) or MAPPING.get((kind, None))
        if target is None:
            continue
        tool, holder = target
        obj = payload.get(holder) or {}
        fields_seen[tool].update(k for k in TEXT_FIELDS if k in obj)
        size = text_bytes(obj)
        if size is None:
            missing[tool] += 1
        else:
            sizes[tool].append(size)
    report = {
        "events": events,
        "parse_errors": parse_errors,
        "share_with_org": round(with_org / max(1, events), 4),
        "share_bot_suffix": round(bot_events / max(1, events), 4),
        "top_event_types": by_type.most_common(8),
        "tools": {
            tool: {
                "n_with_text": len(v),
                "n_text_missing": missing[tool],
                "fields_seen": dict(fields_seen[tool]),
                "text_bytes": quantiles(sorted(v)),
            }
            for tool, v in sorted(sizes.items())
        }
        | {
            tool: {"n_with_text": 0, "n_text_missing": n, "fields_seen": dict(fields_seen[tool])}
            for tool, n in missing.items()
            if tool not in sizes
        },
        "seconds": round(time.time() - started, 1),
    }
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
