"""
mitmproxy addon — captures every HTTP request/response that flows through
mitmdump and writes one JSON object per flow to a JSONL file.

Usage:
    mitmdump --mode reverse:http://localhost:8090 -p 9090 -s mitm_capture.py

Environment:
    MITM_OUT  override output file (default logs/proxy/sessions/mitm_everything/captured.jsonl)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from mitmproxy import http

OUT = Path(os.environ.get("MITM_OUT", "logs/proxy/sessions/mitm_everything/captured.jsonl"))


def _extract_body(raw: str) -> str:
    """If raw is SSE-formatted (event:/data: lines), extract and return the JSON payload."""
    if not raw or (not raw.startswith("event:") and not raw.startswith("data:")):
        return raw
    parts = []
    for line in raw.splitlines():
        if line.startswith("data: "):
            parts.append(line[6:])
    return parts[0] if len(parts) == 1 else "\n".join(parts)


class JsonlLogger:
    def __init__(self) -> None:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text("", encoding="utf-8")  # truncate previous run

    def response(self, flow: http.HTTPFlow) -> None:
        try:
            req_body = flow.request.get_text(strict=False) if flow.request.content else ""
        except Exception:
            req_body = "<binary>"
        try:
            raw = flow.response.get_text(strict=False) if flow.response.content else ""
            resp_body = _extract_body(raw)
        except Exception:
            resp_body = "<binary>"

        record = {
            "ts_request":  flow.request.timestamp_start,
            "ts_response": flow.response.timestamp_end or flow.response.timestamp_start,
            "duration_s":  (flow.response.timestamp_end or 0) - flow.request.timestamp_start,
            "method":      flow.request.method,
            "url":         flow.request.url,
            "path":        flow.request.path,
            "status":      flow.response.status_code,
            "req_headers": dict(flow.request.headers),
            "req_body":    req_body,
            "resp_headers": dict(flow.response.headers),
            "resp_body":   resp_body,
        }
        with OUT.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


addons = [JsonlLogger()]
