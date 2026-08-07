"""Download the real-world data-classification policies used as disclosure-grade examples.

Three documents published by one organization (The University of Iowa) that describe the
same subject -- how institutional data is classified and where it may live -- at three very
different levels of asset concreteness. They are the real-world counterpart to the synthetic
registers in `docs/mcp-tools/server-policies*.md`.

Each source is saved under `docs/mcp-tools/real-policy-examples/<rung>-<slug>/` as the raw
`source.html`, a `<slug>.md` text extraction, and a `provenance.json` recording the URL,
retrieval timestamp and SHA-256 of the bytes that were converted.

Usage:
    uv run python scripts/fetch_real_policy_examples.py [--out DIR] [--offline]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests
from lxml import html as lxml_html

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "docs" / "mcp-tools" / "real-policy-examples"

# Iowa's Drupal theme renders the permission matrix as Font Awesome glyphs with no text, so a
# plain text extraction loses every cell. These are the only three verdicts the legend defines.
ICON_VERDICTS = {
    "fa-check": "permitted",
    "fa-question": "consultation required",
    "fa-xmark": "not permitted",
}

REQUEST_TIMEOUT_SECONDS = 60
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

BLOCK_TAGS = {"p", "div", "section", "article", "br", "tr", "blockquote"}
HEADING_TAGS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}


@dataclass(frozen=True)
class PolicySource:
    """One published policy document and the rung of the concreteness ladder it illustrates."""

    rung: str
    slug: str
    title: str
    url: str
    why: str


SOURCES: tuple[PolicySource, ...] = (
    PolicySource(
        rung="bad",
        slug="uiowa-it19-institutional-data-policy",
        title="Institutional Data Policy (IT-19) — The University of Iowa",
        url="https://itsecurity.uiowa.edu/policies-standards-guidelines/institutional-data-policy",
        why="Four abstract classes and generic data examples. No system, owner or operation named.",
    ),
    PolicySource(
        rung="medium",
        slug="uiowa-data-classification-guidelines",
        title="Data classification guidelines — The University of Iowa",
        url="https://itsecurity.uiowa.edu/it-policies/it-guidelines/data-classification-guidelines",
        why="Adds the CIA derivation matrix and five worked examples; one names a real system.",
    ),
    PolicySource(
        rung="good",
        slug="uiowa-data-classification-guide-to-it-services",
        title="Data Classification Guide to IT Services — The University of Iowa",
        url="https://its.uiowa.edu/services/protecting-sensitive-data/data-classification-guide-it-services",
        why="A register of 41 real named services x 4 classes, each cell an explicit authorization.",
    ),
)


def fetch(url: str) -> bytes:
    """GET `url` with a browser user agent, raising on any non-200 response."""
    response = requests.get(
        url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS
    )
    response.raise_for_status()
    return response.content


def cell_text(cell: lxml_html.HtmlElement) -> str:
    """Text of one table cell, substituting the legend verdict for a bare Font Awesome glyph."""
    text = " ".join(cell.itertext()).strip()
    text = re.sub(r"\s+", " ", text)
    if text:
        return text
    classes = " ".join(cell.xpath(".//span/@class"))
    for icon, verdict in ICON_VERDICTS.items():
        if icon in classes:
            return verdict
    return ""


def table_to_markdown(table: lxml_html.HtmlElement) -> str:
    """Render an HTML table as a GitHub-flavored Markdown table."""
    rows: list[list[str]] = []
    for row in table.xpath(".//tr"):
        cells = [cell_text(c) for c in row.xpath("./th|./td")]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    header, *body = rows
    lines = [
        "| " + " | ".join(c.replace("|", "\\|") for c in header) + " |",
        "|" + "|".join(["---"] * width) + "|",
    ]
    lines += ["| " + " | ".join(c.replace("|", "\\|") for c in r) + " |" for r in body]
    return "\n".join(lines)


def element_to_markdown(node: lxml_html.HtmlElement, out: list[str]) -> None:
    """Walk `node` depth-first, appending Markdown fragments to `out`."""
    tag = str(node.tag).lower() if isinstance(node.tag, str) else ""
    if tag in {"script", "style", "nav", "form", "noscript"}:
        return
    if tag == "table":
        out.append("\n\n" + table_to_markdown(node) + "\n\n")
        return
    if tag in HEADING_TAGS:
        text = re.sub(r"\s+", " ", " ".join(node.itertext())).strip()
        if text:
            out.append(f"\n\n{HEADING_TAGS[tag]} {text}\n\n")
        return
    if tag == "li":
        text = re.sub(r"\s+", " ", " ".join(node.itertext())).strip()
        if text:
            out.append(f"\n- {text}")
        return
    if node.text:
        out.append(node.text)
    for child in node:
        element_to_markdown(child, out)
        if child.tail:
            out.append(child.tail)
    if tag in BLOCK_TAGS:
        out.append("\n\n")


def html_to_markdown(raw: bytes) -> str:
    """Extract the <main> region of a Drupal page as Markdown."""
    root = lxml_html.fromstring(raw)
    mains = root.xpath("//main")
    target = mains[0] if mains else root
    fragments: list[str] = []
    element_to_markdown(target, fragments)
    text = "".join(fragments)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def write_source(source: PolicySource, out_dir: Path, offline: bool) -> dict[str, object]:
    """Download one source, write html + markdown + provenance, and return the provenance."""
    target = out_dir / f"{source.rung}-{source.slug}"
    target.mkdir(parents=True, exist_ok=True)
    html_path = target / "source.html"

    if offline:
        if not html_path.exists():
            raise FileNotFoundError(f"--offline but no cached {html_path}")
        raw = html_path.read_bytes()
        retrieved = "(cached)"
    else:
        raw = fetch(source.url)
        html_path.write_bytes(raw)
        retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")

    body = html_to_markdown(raw)
    header = (
        f"# {source.title}\n\n"
        f"> Verbatim text extraction of a **publicly published** policy page, kept as a\n"
        f"> real-world reference example. Copyright remains with the publisher.\n"
        f">\n"
        f"> - Source: <{source.url}>\n"
        f"> - Retrieved: {retrieved}\n"
        f"> - Ladder rung: **{source.rung}** — {source.why}\n\n"
        f"---\n\n"
    )
    (target / f"{source.slug}.md").write_text(header + body, encoding="utf-8")

    provenance = {
        "rung": source.rung,
        "title": source.title,
        "url": source.url,
        "retrieved_utc": retrieved,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "markdown_chars": len(body),
    }
    (target / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", "utf-8")
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory")
    parser.add_argument(
        "--offline", action="store_true", help="re-extract from cached source.html only"
    )
    args = parser.parse_args()

    for source in SOURCES:
        provenance = write_source(source, args.out, args.offline)
        print(
            f"[{provenance['rung']:>6}] {provenance['bytes']:>7} B html -> "
            f"{provenance['markdown_chars']:>6} chars md  {source.slug}"
        )
    print(f"\nwrote {len(SOURCES)} sources -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
