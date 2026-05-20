"""
Run both AI baselines (ChatGPT + Claude) and write a metadata.json
recording which model filled which file and when.

Usage:
    OPENAI_API_KEY=... ANTHROPIC_API_KEY=... python run_all.py

Requires:
    pip install openai anthropic
"""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
META_PATH = SCRIPT_DIR / "metadata.json"


def _run_script(script_path: Path) -> None:
    spec = importlib.util.spec_from_file_location("_module", script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()


def _read_fill_info(json_path: Path) -> dict:
    if not json_path.exists():
        return {"status": "missing"}
    data = json.loads(json_path.read_text(encoding="utf-8"))
    return {
        "status": data.get("status"),
        "filled_by": data.get("filled_by"),
        "model": data.get("model"),
        "filled_at": data.get("filled_at"),
        "path": str(json_path.relative_to(SCRIPT_DIR)),
    }


def main() -> None:
    chatgpt_script = SCRIPT_DIR / "chatgpt" / "run_chatgpt.py"
    claude_script = SCRIPT_DIR / "claude" / "run_claude.py"

    print("=== Running ChatGPT baseline ===")
    _run_script(chatgpt_script)

    print("\n=== Running Claude baseline ===")
    _run_script(claude_script)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": {
            "chatgpt/chatgpt_risks.json": _read_fill_info(
                SCRIPT_DIR / "chatgpt" / "chatgpt_risks.json"
            ),
            "claude/claude_risks.json": _read_fill_info(
                SCRIPT_DIR / "claude" / "claude_risks.json"
            ),
        },
    }

    META_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"\nMetadata saved: {META_PATH}")
    print("\nSummary:")
    for fname, info in metadata["files"].items():
        print(f"  {fname}  →  filled_by={info['filled_by']}  model={info['model']}")


if __name__ == "__main__":
    main()
