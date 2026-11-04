# Shared egress table

This folder holds the per-platform egress table (change B10 of the v5 dynamic layer). A route
names it with `shared_egress` in the routes file. Every address inside one platform's ranges then
counts as one network, `platform:<label>`, instead of its /16.

## Why

Hosted agent platforms send every tenant's MCP calls from a few published ranges. Without the
table, all of a platform's callers share one /16. The org discount then waves a new caller from it
through after three others. A platform label stays in the caller's own Footprint (he has never used
the platform before: new), and it never takes part in the org discount.

## Files

| File | What it holds |
|------|---------------|
| `platform_egress.json` | The shipped table: one entry per platform, each marked `verified` or `UNVERIFIED` |
| `table.py` | The loader and its checks: `load_egress_table`, `EgressTable.shared_networks` |
| `__init__.py` | Makes the folder a package; no code |

## Format

```json
{
  "version": 1,
  "use_unverified": false,
  "platforms": [
    {"label": "anthropic", "status": "verified", "cidrs": ["160.79.104.0/21"],
     "source": "https://...", "checked": "2026-10-26", "note": "..."}
  ]
}
```

- `verified`: someone opened `source` on `checked` and copied `cidrs` from it. A verified entry
  must have ranges, an http(s) source and an ISO date.
- `UNVERIFIED`: a placeholder with no ranges, or a range nobody has checked. Its ranges are used only
  when `use_unverified` is `true`.
- Ranges are strict CIDRs (no host bits set). Ranges in use may not overlap across platforms.
- Any other key, at the top level or in an entry, is refused (a typo such as `use_unverifed`
  would otherwise be ignored).
- The loaded table carries `digest`, the SHA-256 of the file read. On a route that logs raw
  addresses, an offline re-score recomputes network values from this file, so the route pins
  the digest with its other artifacts (`route_egress_table` in [../config.py](../config.py)).

## Rules

- Never invent a range. Copy it from the platform's own published list, and record the page and
  the date.
- Re-check a verified entry when its platform announces a change, and update `checked`.

## References

- Loader and checks: [table.py](table.py); a route's pairs: `route_shared_networks` in
  [../config.py](../config.py).
- Design: change B10 in the v5 design spec,
  `reports/experiments/dynamic_dimensions/knowledge_base/v5-design-spec.md` (section 4.3).
