"""
One-shot Claude (claude-opus-4-7) baseline: security analyst (NIST/OWASP) risk scoring
for three MCP servers.  Produces the same three xlsx files as other methods.

Usage:
    ANTHROPIC_API_KEY=sk-ant-... python run_claude.py

Requires: pip install anthropic openpyxl
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow importing the shared xlsx filler from the parent folder
sys.path.insert(0, str(Path(__file__).parent.parent))
from _fill_xlsx_from_ai import fill_all_xlsx  # noqa: E402

import anthropic

SCRIPT_DIR = Path(__file__).parent
OUT_PATH   = SCRIPT_DIR / "claude_risks.json"

_DOCS_DIR = Path(__file__).parents[5] / "docs" / "mcp-tools"


def _readme(name: str) -> str:
    p = _DOCS_DIR / name
    return p.read_text(encoding="utf-8") if p.exists() else f"[{name} not found]"


_README_CONTEXT = (
    "Below are the official README documents for the three MCP servers you will score. "
    "Use them to understand exactly what each tool does before assigning risk levels.\n\n"
    "Note on tool name mapping used in the scoring JSON:\n"
    "  Filesystem: read_text_file/read_media_file/read_multiple_files → 'read_file'; "
    "create_directory → 'create_dir'; list_directory/directory_tree → 'list_dir'; "
    "search_files → 'search'\n\n"
    "=== Filesystem MCP Server README ===\n\n"
    + _readme("filesystem-mcp-readme.md")
    + "\n\n=== Slack MCP Server README ===\n\n"
    + _readme("slack-mcp-readme.md")
    + "\n\n=== SQLite MCP Server README ===\n\n"
    + _readme("sqlite-mcp-readme.md")
    + "\n\n=== END OF DOCUMENTATION ===\n\n"
)

SYSTEM_PROMPT = (
    "You are a senior security analyst performing risk assessments for AI-agent access "
    "to MCP (Model Context Protocol) servers. "
    "The MCP server is the protected asset; the AI agent is the threat source. "
    "Apply NIST SP 800-30 Rev.1 (Threat Likelihood × Adverse Impact) and reference "
    "OWASP LLM Top 10 for agent-specific threat categories. "
    "Risk scale (use EXACTLY these strings): Critical / High / Medium / Low."
)

# Identical scoring request to chatgpt/run_chatgpt.py for a fair comparison
_SCORING_REQUEST = """\
Score each tool and asset class for three MCP servers assuming worst-case enterprise
sensitivity. Use the risk scale: Critical / High / Medium / Low.

Return ONLY valid JSON matching this exact structure (no extra keys, no markdown):

{
  "filesystem_mcp": {
    "tool_rankings": [
      {"tool": "read_file",     "risk_level": "?", "reasoning": "one sentence"},
      {"tool": "write_file",    "risk_level": "?", "reasoning": "..."},
      {"tool": "edit_file",     "risk_level": "?", "reasoning": "..."},
      {"tool": "create_dir",    "risk_level": "?", "reasoning": "..."},
      {"tool": "list_dir",      "risk_level": "?", "reasoning": "..."},
      {"tool": "move_file",     "risk_level": "?", "reasoning": "..."},
      {"tool": "search",        "risk_level": "?", "reasoning": "..."},
      {"tool": "get_file_info", "risk_level": "?", "reasoning": "..."}
    ],
    "filetype_rankings": [
      {"filetype": ".sys",  "risk_level": "?", "reasoning": "..."},
      {"filetype": ".exe",  "risk_level": "?", "reasoning": "..."},
      {"filetype": ".bash", "risk_level": "?", "reasoning": "..."},
      {"filetype": ".code", "risk_level": "?", "reasoning": "..."},
      {"filetype": ".sql",  "risk_level": "?", "reasoning": "..."},
      {"filetype": ".xlsx", "risk_level": "?", "reasoning": "..."},
      {"filetype": ".docx", "risk_level": "?", "reasoning": "..."},
      {"filetype": ".pdf",  "risk_level": "?", "reasoning": "..."},
      {"filetype": ".csv",  "risk_level": "?", "reasoning": "..."},
      {"filetype": ".md",   "risk_level": "?", "reasoning": "..."},
      {"filetype": ".png",  "risk_level": "?", "reasoning": "..."},
      {"filetype": ".txt",  "risk_level": "?", "reasoning": "..."}
    ],
    "folder_rankings": [
      {"folder": "Sensitive Docs",    "risk_level": "?", "reasoning": "..."},
      {"folder": "Security Evidence", "risk_level": "?", "reasoning": "..."},
      {"folder": "Source Code",       "risk_level": "?", "reasoning": "..."},
      {"folder": "QA Test Plans",     "risk_level": "?", "reasoning": "..."},
      {"folder": "Shared Proj Dir",   "risk_level": "?", "reasoning": "..."},
      {"folder": "Eval Data",         "risk_level": "?", "reasoning": "..."},
      {"folder": "Onboarding",        "risk_level": "?", "reasoning": "..."},
      {"folder": "Public",            "risk_level": "?", "reasoning": "..."}
    ]
  },
  "slack_mcp": {
    "tool_rankings": [
      {"tool": "slack_get_channel_history", "risk_level": "?", "reasoning": "..."},
      {"tool": "slack_get_thread_replies",  "risk_level": "?", "reasoning": "..."},
      {"tool": "slack_get_user_profile",    "risk_level": "?", "reasoning": "..."},
      {"tool": "slack_post_message",        "risk_level": "?", "reasoning": "..."},
      {"tool": "slack_reply_to_thread",     "risk_level": "?", "reasoning": "..."},
      {"tool": "slack_get_users",           "risk_level": "?", "reasoning": "..."},
      {"tool": "slack_list_channels",       "risk_level": "?", "reasoning": "..."},
      {"tool": "slack_add_reaction",        "risk_level": "?", "reasoning": "..."}
    ],
    "channel_category_rankings": [
      {"category": "Management", "risk_level": "?", "reasoning": "..."},
      {"category": "HR",         "risk_level": "?", "reasoning": "..."},
      {"category": "Supervisor", "risk_level": "?", "reasoning": "..."},
      {"category": "Researcher", "risk_level": "?", "reasoning": "..."},
      {"category": "Technical",  "risk_level": "?", "reasoning": "..."},
      {"category": "Public",     "risk_level": "?", "reasoning": "..."}
    ],
    "asset_rankings": [
      {"asset": "User PII (emails, phones, titles)", "risk_level": "?", "reasoning": "..."},
      {"asset": "Private Channel Messages",          "risk_level": "?", "reasoning": "..."},
      {"asset": "Public Channel Messages",           "risk_level": "?", "reasoning": "..."},
      {"asset": "Team Metadata",                     "risk_level": "?", "reasoning": "..."}
    ]
  },
  "sqlite_mcp": {
    "tool_rankings": [
      {"tool": "list_tables",    "risk_level": "?", "reasoning": "..."},
      {"tool": "describe_table", "risk_level": "?", "reasoning": "..."},
      {"tool": "read_query",     "risk_level": "?", "reasoning": "..."},
      {"tool": "write_query",    "risk_level": "?", "reasoning": "..."},
      {"tool": "create_table",   "risk_level": "?", "reasoning": "..."},
      {"tool": "append_insight", "risk_level": "?", "reasoning": "..."}
    ],
    "data_type_rankings": [
      {"data_type": "PII",                      "risk_level": "?", "reasoning": "..."},
      {"data_type": "Financial",                "risk_level": "?", "reasoning": "..."},
      {"data_type": "Credentials / API Keys",   "risk_level": "?", "reasoning": "..."},
      {"data_type": "Restricted Research Data", "risk_level": "?", "reasoning": "..."},
      {"data_type": "Public Research Data",     "risk_level": "?", "reasoning": "..."},
      {"data_type": "Org / Role Metadata",      "risk_level": "?", "reasoning": "..."},
      {"data_type": "Lifecycle / Timestamps",   "risk_level": "?", "reasoning": "..."}
    ],
    "table_rankings": [
      {"table": "employees",    "risk_level": "?", "reasoning": "..."},
      {"table": "projects",     "risk_level": "?", "reasoning": "..."},
      {"table": "datasets",     "risk_level": "?", "reasoning": "..."},
      {"table": "experiments",  "risk_level": "?", "reasoning": "..."},
      {"table": "publications", "risk_level": "?", "reasoning": "..."},
      {"table": "grants",       "risk_level": "?", "reasoning": "..."},
      {"table": "api_keys",     "risk_level": "?", "reasoning": "..."}
    ]
  }
}"""

USER_PROMPT = _README_CONTEXT + _SCORING_REQUEST


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0]
    return text.strip()


def main() -> None:
    client = anthropic.Anthropic()

    print("Calling claude-opus-4-7 — one-shot MCP risk assessment...")
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": USER_PROMPT}],
    )

    raw = next(b.text for b in response.content if b.type == "text")
    ai_scores = json.loads(_strip_fences(raw))

    # Persist raw AI output
    OUT_PATH.write_text(
        json.dumps({
            "filled_by": "claude",
            "model":     "claude-opus-4-7",
            "filled_at": datetime.now(timezone.utc).isoformat(),
            "status":    "filled",
            "risks":     ai_scores,
        }, indent=2),
        encoding="utf-8",
    )
    print(f"JSON saved: {OUT_PATH.name}")

    # Fill xlsx files
    print("Filling xlsx files...")
    fill_all_xlsx(ai_scores, SCRIPT_DIR)
    print("Done.")


if __name__ == "__main__":
    main()
