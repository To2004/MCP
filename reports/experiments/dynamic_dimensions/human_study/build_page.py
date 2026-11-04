"""Build the Bot Day Check web page: embed the public item bank into the page template.

Only ``items.json`` goes into the page. ``key.json`` (scores, strata, labels) never does, and the
build fails if any key-only field name appears in the bank.

Run from the repository root::

    uv run python reports/experiments/dynamic_dimensions/human_study/build_page.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ITEMS = HERE / "items.json"
DEFAULT_TEMPLATE = HERE / "web" / "index.template.html"
DEFAULT_OUT = HERE / "web" / "index.html"
PLACEHOLDER = "__BANK_JSON__"
#: field names that exist only in key.json; seeing one in the bank means the key leaked
KEY_ONLY_FIELDS = ("stratum", "gray_kind", "strongest", "listed", "list_rank", "attention")


def bank_json(items: dict) -> str:
    """Serialise the bank for a ``<script type="application/json">`` block.

    ``</`` is escaped so no string inside the bank can close the script element.
    """
    text = json.dumps(items, ensure_ascii=False, separators=(",", ":"))
    return text.replace("</", "<\\/")


def leaked_fields(items: dict) -> list[str]:
    """Return every key-only field name found anywhere in the bank."""
    found: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in KEY_ONLY_FIELDS:
                    found.add(key)
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(items)
    return sorted(found)


def build_page(items: dict, template: str) -> str:
    """Return the page with the bank embedded; raise if the bank or template is wrong."""
    leaked = leaked_fields(items)
    if leaked:
        raise ValueError(f"items.json carries key-only fields: {', '.join(leaked)}")
    if template.count(PLACEHOLDER) != 1:
        raise ValueError(f"the template must contain {PLACEHOLDER} exactly once")
    return template.replace(PLACEHOLDER, bank_json(items))


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description="Embed items.json into the Bot Day Check page.")
    ap.add_argument("--items", type=Path, default=DEFAULT_ITEMS)
    ap.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    items = json.loads(args.items.read_text(encoding="utf-8"))
    page = build_page(items, args.template.read_text(encoding="utf-8"))
    args.out.write_text(page, encoding="utf-8")
    print(f"wrote {args.out} ({len(page):,} bytes, bank {items.get('bank_version')})")


if __name__ == "__main__":
    main()
