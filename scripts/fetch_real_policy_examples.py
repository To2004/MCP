"""Download the real-world data-classification policies used as disclosure-grade examples.

Two sets of sources, both real-world counterparts to the synthetic registers in
`docs/mcp-tools/server-policies*.md`:

- The concreteness ladder: three documents published by one organization (The University of
  Iowa) that describe the same subject -- how institutional data is classified and where it
  may live -- at three very different levels of asset concreteness.
- The framework set: three documents from three different organizations, each publicly citing
  one of the frameworks the v7 arms write in natively -- ISO/IEC 27002, NIST FIPS 199 / SP
  800-60, and CIS Controls -- by name or control number. Unlike the ladder, these are not one
  organization's controlled comparison; they answer a narrower question: when a real org
  discloses that it follows framework X, what does the resulting document actually say?

Each source is saved under `docs/mcp-tools/real-policy-examples/<rung>-<slug>/` as the raw
downloaded file (`source.html` or `source.pdf`), a `<slug>.md` text extraction, and a
`provenance.json` recording the URL, retrieval timestamp and SHA-256 of the bytes that were
converted. For the framework set, `rung` holds the framework name (iso/nist/cis) rather than a
concreteness rung.

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
from io import BytesIO
from pathlib import Path

import requests
from lxml import html as lxml_html
from pypdf import PdfReader

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


FRAMEWORK_RUNGS = frozenset({"iso", "nist", "cis"})

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
    # Framework set: real orgs that publicly cite the framework each v7 arm writes in natively.
    # `rung` holds the framework name here, not a concreteness rung -- see module docstring.
    PolicySource(
        rung="iso",
        slug="leedsbeckett-information-classification-scheme",
        title="Information Classification Scheme — Leeds Beckett University",
        url=(
            "https://www.leedsbeckett.ac.uk/-/media/files/policies/information-governance/"
            "upig_information_classification.pdf"
        ),
        why=(
            "Cites BS ISO/IEC 27002:2013 Section 8.2 by name and names controls A.8.1.1/"
            "A.8.2.1/A.8.2.2/A.8.2.3 (the 2013-numbering predecessors of A.5.9/A.5.12/A.8.3). "
            "Three classes with a worked matrix of concrete data examples (staff names, exam "
            "papers, server-room details, passwords)."
        ),
    ),
    PolicySource(
        rung="nist",
        slug="ucdenver-data-classification-and-system-security-categorization",
        title="Process for Data Classification and System Security Categorization — "
        "University of Colorado Denver",
        url="https://clas.ucdenver.edu/it-support/sites/default/files/attached-files/cudataclassification.pdf",
        why=(
            "Cites FIPS 199 and NIST SP 800-60 by name, reproduces the {C,I,A} security-"
            "category triple and the high-water-mark rule, and works a full example (Funds "
            "Control) straight from the NIST 800-60 catalog."
        ),
    ),
    PolicySource(
        rung="cis",
        slug="nevada-statewide-data-classification-policy",
        title="Statewide Policy for Data Classification — State of Nevada Governor's "
        "Technology Office",
        url=(
            "https://www.it.nv.gov/siteassets/itnew.nv.gov/content/governance/"
            "statewide-policy-for-data-classifications---signed_020220206-12.pdf"
        ),
        why=(
            "Lists 'CIS Controls v8' as a named federal reference alongside NIST SP 800-53/"
            "800-60, directs its own technical-control policies to be built on 'NIST and CIS "
            "Control frameworks', and defines CIS in its glossary as the Center for Internet "
            "Security. A four-tier scheme with named regulatory sub-categories (CJIS, FTI, "
            "CUI) rather than a per-system register."
        ),
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


def pdf_to_markdown(raw: bytes) -> str:
    """Extract text from a PDF, page by page, as plain-paragraph Markdown."""
    reader = PdfReader(BytesIO(raw))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(page.strip() for page in pages if page.strip())
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def write_source(source: PolicySource, out_dir: Path, offline: bool) -> dict[str, object]:
    """Download one source, write the raw file + markdown + provenance, return the provenance."""
    target = out_dir / f"{source.rung}-{source.slug}"
    target.mkdir(parents=True, exist_ok=True)
    is_pdf = source.url.lower().endswith(".pdf")
    raw_path = target / ("source.pdf" if is_pdf else "source.html")

    if offline:
        if not raw_path.exists():
            raise FileNotFoundError(f"--offline but no cached {raw_path}")
        raw = raw_path.read_bytes()
        retrieved = "(cached)"
    else:
        raw = fetch(source.url)
        raw_path.write_bytes(raw)
        retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")

    body = pdf_to_markdown(raw) if is_pdf else html_to_markdown(raw)
    label = "Framework" if source.rung in FRAMEWORK_RUNGS else "Ladder rung"
    header = (
        f"# {source.title}\n\n"
        f"> Verbatim text extraction of a **publicly published** policy document, kept as a\n"
        f"> real-world reference example. Copyright remains with the publisher.\n"
        f">\n"
        f"> - Source: <{source.url}>\n"
        f"> - Retrieved: {retrieved}\n"
        f"> - {label}: **{source.rung}** — {source.why}\n\n"
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
        "--offline", action="store_true", help="re-extract from cached source files only"
    )
    args = parser.parse_args()

    for source in SOURCES:
        provenance = write_source(source, args.out, args.offline)
        raw_kind = "pdf" if source.url.lower().endswith(".pdf") else "html"
        print(
            f"[{provenance['rung']:>6}] {provenance['bytes']:>7} B {raw_kind} -> "
            f"{provenance['markdown_chars']:>6} chars md  {source.slug}"
        )
    print(f"\nwrote {len(SOURCES)} sources -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
