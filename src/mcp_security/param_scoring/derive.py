"""Derive per-tool parameter rubrics with the LLM, using the markdown as prompt.

``docs/standards/parameter-scoring.md`` is both the human spec and the LLM prompt:
it is sent verbatim as context, then the tool's definition is appended and the model
returns the rubric JSON. Nothing is hardcoded per server — the model decides which
parameters carry magnitude and what the cutoffs are, from the tool itself.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from mcp_security.llm.ollama_client import query_ollama
from mcp_security.static_scoring.registry import ToolSpec

from .rubric import ToolRubric

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPT_PATH = REPO_ROOT / "docs" / "standards" / "parameter-scoring.md"

_INSTRUCTION = (
    "\n\n---\nUsing the rubric above, derive the parameter rubric for this tool. "
    "Output ONLY the JSON object described in the 'LLM prompt' section, no prose, "
    "no fences.\n\nTool:\n{tool_json}\n"
)


def _prompt_for(tool: ToolSpec) -> str:
    rubric_md = PROMPT_PATH.read_text(encoding="utf-8")
    return rubric_md + _INSTRUCTION.format(tool_json=json.dumps(tool.to_prompt_json()))


def derive_tool_rubric(tool: ToolSpec, *, strict: bool = False) -> ToolRubric:
    """Derive one tool's parameter rubric from the model.

    In ``strict`` mode an unreachable/garbage model raises; otherwise the tool gets
    an empty rubric (no magnitude parameters) so scoring simply falls back to the
    (tool, asset) band for that tool.
    """
    result = query_ollama(_prompt_for(tool))
    if not isinstance(result, dict) or "parameters" not in result:
        if strict:
            from mcp_security.static_scoring.pipeline import LLMUnavailableError

            raise LLMUnavailableError(
                f"no usable parameter rubric for tool {tool.name!r}; "
                "strict mode forbids a fabricated rubric"
            )
        logger.warning("no rubric for %s; treating as no magnitude parameters", tool.name)
        return ToolRubric(tool_name=tool.name, parameters=())
    result.setdefault("tool_name", tool.name)
    return ToolRubric.from_dict(result)


def derive_rubrics(tools: list[ToolSpec], *, strict: bool = False) -> dict[str, ToolRubric]:
    """Derive parameter rubrics for every tool, keyed by tool name."""
    return {t.name: derive_tool_rubric(t, strict=strict) for t in tools}
