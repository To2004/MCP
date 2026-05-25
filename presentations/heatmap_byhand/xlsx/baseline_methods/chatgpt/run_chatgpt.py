"""
Two-shot ChatGPT (gpt-4o) baseline for three MCP servers.

Run 1 — plain:    no system prompt, bare scoring question.
Run 2 — security: system prompt = senior security analyst (NIST SP 800-30 + OWASP LLM Top 10).

Produces 6 xlsx files + 2 JSON files in this folder.

Usage:
    OPENAI_API_KEY=sk-... python run_chatgpt.py

Requires: pip install openai openpyxl
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from _fill_xlsx_from_ai import fill_all_xlsx  # noqa: E402

from openai import OpenAI

SCRIPT_DIR = Path(__file__).parent
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

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PLAIN = None  # no system prompt — bare model

SYSTEM_SECURITY = (
    "You are a senior security analyst performing risk assessments for AI-agent access "
    "to MCP (Model Context Protocol) servers. "
    "The MCP server is the protected asset; the AI agent is the threat source. "
    "Apply NIST SP 800-30 Rev.1 (Threat Likelihood × Adverse Impact) and reference "
    "OWASP LLM Top 10 for agent-specific threat categories. "
    "Risk scale (use EXACTLY these strings): Critical / High / Medium / Low."
)

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _call(client: OpenAI, system: str | None) -> dict:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": USER_PROMPT})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def _save_json(ai_scores: dict, label: str, variant: str) -> None:
    path = SCRIPT_DIR / f"chatgpt_risks_{label}.json"
    path.write_text(
        json.dumps({
            "filled_by": "chatgpt",
            "model":     "gpt-4o",
            "variant":   variant,
            "filled_at": datetime.now(timezone.utc).isoformat(),
            "status":    "filled",
            "risks":     ai_scores,
        }, indent=2),
        encoding="utf-8",
    )
    print(f"  JSON: {path.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    client = OpenAI()

    # -- Run 1: plain (no system prompt) ------------------------------------
    print("=== Run 1: plain (no system prompt) ===")
    scores_plain = _call(client, SYSTEM_PLAIN)
    _save_json(scores_plain, "plain", "plain — no system prompt")
    fill_all_xlsx(scores_plain, SCRIPT_DIR, label="chatgpt_plain",
                  variant_desc="ChatGPT (gpt-4o) — plain, no system prompt")

    # -- Run 2: security expert context (NIST/OWASP) ------------------------
    print("\n=== Run 2: security expert (NIST SP 800-30 + OWASP LLM Top 10) ===")
    scores_security = _call(client, SYSTEM_SECURITY)
    _save_json(scores_security, "security", "security analyst — NIST SP 800-30 + OWASP LLM Top 10")
    fill_all_xlsx(scores_security, SCRIPT_DIR, label="chatgpt_security",
                  variant_desc="ChatGPT (gpt-4o) — security analyst, NIST SP 800-30 + OWASP LLM Top 10")

    print("\nDone — 6 xlsx files written.")


if __name__ == "__main__":
    main()
