"""Assemble evidence excerpts for the reviewers from the repo's own files.

Keeping excerpts small and targeted lets the local LLM audit one claim at a time
within its context window, instead of being handed the whole codebase at once.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def read_file(rel: str, *, max_chars: int = 6000) -> str:
    """Return a repo file's text (truncated), labelled for the prompt."""
    path = REPO_ROOT / rel
    if not path.exists():
        return f"# {rel}\n(missing)"
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n... (truncated, {len(text)} chars total)"
    return f"# {rel}\n{text}"


def bundle(rels: list[str], *, per_file_chars: int = 16000) -> str:
    """Concatenate several repo files into one labelled evidence blob.

    The default budget is large enough to show a whole scoring module (e.g. the
    ~16 KB of pipeline.py that holds both the LLM band path ``score_bands`` and the
    strict-mode ``_strict_fail`` guard) — truncating before them is what made an
    earlier audit misread the deprecated ``band_label`` fallback as the live policy.
    """
    return "\n\n".join(read_file(rel, max_chars=per_file_chars) for rel in rels)
