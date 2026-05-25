"""
Re-generate xlsx and markdown notes from existing chatgpt_risks_*.json files.
No API calls — reads saved JSON and re-fills using the current _fill_xlsx_from_ai.py.

Usage:
    python refill_from_json.py
    # or with uv:
    uv run --with openpyxl python refill_from_json.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from _fill_xlsx_from_ai import fill_all_xlsx  # noqa: E402

SCRIPT_DIR = Path(__file__).parent

_VARIANTS = [
    {
        "json_file":    "chatgpt_risks_plain.json",
        "label":        "chatgpt_plain",
        "variant_desc": "ChatGPT (gpt-4o) — plain, no system prompt",
    },
    {
        "json_file":    "chatgpt_risks_security.json",
        "label":        "chatgpt_security",
        "variant_desc": "ChatGPT (gpt-4o) — security analyst, NIST SP 800-30 + OWASP LLM Top 10",
    },
]


def main() -> None:
    for v in _VARIANTS:
        json_path = SCRIPT_DIR / v["json_file"]
        if not json_path.exists():
            print(f"  SKIP (not found): {json_path.name}")
            continue
        print(f"\n=== {v['label']} ===")
        data = json.loads(json_path.read_text(encoding="utf-8"))
        ai_scores = data["risks"]
        fill_all_xlsx(ai_scores, SCRIPT_DIR, label=v["label"], variant_desc=v["variant_desc"])

    print("\nDone.")


if __name__ == "__main__":
    main()
