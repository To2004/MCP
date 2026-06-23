"""Thin client for the project's local LLM: Qwen2.5:32b via Ollama.

This is the single place that talks to a model. There is **no cloud fallback**
by design — every model call in the framework goes through the user's local
Ollama instance. Callers handle ``None`` (Ollama down / bad response) by
degrading gracefully rather than substituting another provider.

Extracted from ``local_llm/rank_with_llm.py`` so both that script and
``mcp_security.scanner`` share one implementation.
"""

from __future__ import annotations

import json
import logging
import os

import requests

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_MODEL = "qwen2.5:32b"
# Local 32b generation is slow; mirror the script's generous ceiling.
DEFAULT_TIMEOUT = 1200
# Greedy, fixed-seed decoding so the same prompt yields the same answer every
# run — risk tables must be reproducible. Callers can override via ``options``.
DEFAULT_OPTIONS = {"temperature": 0, "seed": 0, "top_p": 1.0}


def _strip_fences(text: str) -> str:
    """Remove a leading ```json/``` fence and trailing ``` from a response."""
    return text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()


def query_ollama(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    timeout: int = DEFAULT_TIMEOUT,
    host: str = OLLAMA_HOST,
    options: dict | None = None,
) -> dict | None:
    """Send a prompt to the local model and parse a JSON object from the reply.

    Decoding is greedy and fixed-seed by default (:data:`DEFAULT_OPTIONS`) so a
    given prompt is reproducible; pass ``options`` to override. Returns the
    decoded ``dict`` on success, or ``None`` if the request fails, the model is
    unreachable, or the response is not valid JSON. Never raises for these
    expected failure modes — callers degrade gracefully.
    """
    try:
        resp = requests.post(
            f"{host}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": DEFAULT_OPTIONS if options is None else options,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        raw = _strip_fences(resp.json().get("response", ""))
        parsed = json.loads(raw)
    except requests.RequestException as exc:
        logger.warning("Ollama request failed: %s", exc)
        return None
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Ollama returned non-JSON response: %s", exc)
        return None

    if not isinstance(parsed, dict):
        logger.warning("Ollama returned %s, expected object", type(parsed).__name__)
        return None
    return parsed
