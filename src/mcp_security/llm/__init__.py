"""Local-LLM helpers (Ollama / Qwen2.5)."""

from .ollama_client import DEFAULT_MODEL, OLLAMA_HOST, query_ollama

__all__ = ["DEFAULT_MODEL", "OLLAMA_HOST", "query_ollama"]
