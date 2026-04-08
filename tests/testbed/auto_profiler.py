"""Auto-generate server profile JSONs from npm or PyPI package names.

Usage:
    python tests/testbed/auto_profiler.py --npm @modelcontextprotocol/server-brave-search
    python tests/testbed/auto_profiler.py --pip mcp-server-time
    python tests/testbed/auto_profiler.py --npm-search "mcp-server" --limit 20
    python tests/testbed/auto_profiler.py --list awesome-mcp-servers  # parses punkpeye list
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import requests

SERVERS_DIR = Path(__file__).parent / "servers"

# Keywords that suggest a server needs credentials and may hang on start
CREDENTIAL_SIGNALS = [
    "aws", "azure", "gcp", "google", "slack", "github", "jira", "atlassian",
    "stripe", "twilio", "sendgrid", "openai", "anthropic", "notion", "linear",
    "figma", "shopify", "salesforce", "hubspot",
]


def _needs_credentials(name: str, description: str) -> bool:
    """Heuristic: does this server likely need an API key to start?"""
    text = (name + " " + description).lower()
    return any(sig in text for sig in CREDENTIAL_SIGNALS)


def _infer_categories(name: str, description: str) -> list[str]:
    """Guess likely attack categories based on package name/description."""
    text = (name + " " + description).lower()
    categories = []
    if any(w in text for w in ["file", "filesystem", "path", "directory", "read", "write"]):
        categories.append("C2")
    if any(w in text for w in ["exec", "command", "shell", "run", "process", "script"]):
        categories.append("C1")
    if any(w in text for w in ["fetch", "http", "url", "web", "request", "browser"]):
        categories.append("C2")
    if any(w in text for w in ["sql", "database", "db", "query", "postgres", "sqlite", "mysql"]):
        categories.append("C1")
    if any(w in text for w in ["git", "repo", "github", "version"]):
        categories.append("C1")
    return sorted(set(categories)) or ["C2"]


def profile_from_npm(package_name: str) -> dict[str, Any] | None:
    """Fetch npm registry metadata and generate a server profile.

    Args:
        package_name: npm package name (e.g. ``@modelcontextprotocol/server-filesystem``).

    Returns:
        Profile dict, or None if the package was not found.
    """
    encoded = package_name.replace("/", "%2F")
    resp = requests.get(f"https://registry.npmjs.org/{encoded}", timeout=10)
    if resp.status_code != 200:
        print(f"[npm] Not found: {package_name} (HTTP {resp.status_code})", file=sys.stderr)
        return None

    data = resp.json()
    latest_version = data.get("dist-tags", {}).get("latest", "")
    description = data.get("description", "")
    stem = package_name.split("/")[-1].replace("server-", "").replace("-", "_")

    profile = {
        "name": stem,
        "description": description or package_name,
        "cve": [],
        "tier": "unknown",
        "transport": "stdio",
        "install": f"npm install -g {package_name}@{latest_version}" if latest_version else f"npm install -g {package_name}",
        "start_cmd": ["npx", "-y", package_name],
        "expected_attack_categories": _infer_categories(package_name, description),
        "_needs_credentials": _needs_credentials(package_name, description),
        "_latest_version": latest_version,
        "_source": "npm",
    }
    return profile


def profile_from_pypi(package_name: str) -> dict[str, Any] | None:
    """Fetch PyPI metadata and generate a server profile.

    Args:
        package_name: PyPI package name (e.g. ``mcp-server-fetch``).

    Returns:
        Profile dict, or None if the package was not found.
    """
    resp = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=10)
    if resp.status_code != 200:
        print(f"[pypi] Not found: {package_name} (HTTP {resp.status_code})", file=sys.stderr)
        return None

    data = resp.json()
    info = data.get("info", {})
    version = info.get("version", "")
    description = info.get("summary", "")
    stem = package_name.replace("mcp-server-", "").replace("-", "_")

    profile = {
        "name": stem,
        "description": description or package_name,
        "cve": [],
        "tier": "unknown",
        "transport": "stdio",
        "install": f"pip install {package_name}=={version}" if version else f"pip install {package_name}",
        "start_cmd": ["uvx", package_name],
        "expected_attack_categories": _infer_categories(package_name, description),
        "_needs_credentials": _needs_credentials(package_name, description),
        "_latest_version": version,
        "_source": "pypi",
    }
    return profile


def search_npm(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search npm for MCP servers matching a query.

    Args:
        query: Search terms (e.g. ``"mcp-server"``).
        limit: Maximum results to return.

    Returns:
        List of profile dicts (not yet saved).
    """
    resp = requests.get(
        "https://registry.npmjs.org/-/v1/search",
        params={"text": query, "size": min(limit, 250)},
        timeout=15,
    )
    resp.raise_for_status()
    objects = resp.json().get("objects", [])
    profiles = []
    for obj in objects:
        pkg = obj.get("package", {})
        name = pkg.get("name", "")
        if not name:
            continue
        profile = profile_from_npm(name)
        if profile:
            profiles.append(profile)
    return profiles


def save_profile(profile: dict[str, Any], overwrite: bool = False) -> Path:
    """Write a profile dict to servers/<name>.json.

    Args:
        profile: Profile dict with a ``name`` key.
        overwrite: If False, skip saving if the file already exists.

    Returns:
        Path to the saved file.
    """
    SERVERS_DIR.mkdir(parents=True, exist_ok=True)
    path = SERVERS_DIR / f"{profile['name']}.json"
    if path.exists() and not overwrite:
        print(f"[skip] {path.name} already exists (use --overwrite to replace)")
        return path
    path.write_text(json.dumps(profile, indent=2))
    cred_warning = " ⚠ likely needs credentials" if profile.get("_needs_credentials") else ""
    print(f"[saved] {path.name}  ({profile['_source']}, tier={profile['tier']}){cred_warning}")
    return path


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Auto-generate MCP server profiles")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--npm", metavar="PACKAGE", help="Profile a single npm package")
    group.add_argument("--pip", metavar="PACKAGE", help="Profile a single PyPI package")
    group.add_argument("--npm-search", metavar="QUERY", help="Search npm and profile results")
    parser.add_argument("--limit", type=int, default=20, help="Max results for --npm-search")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing profiles")
    parser.add_argument("--dry-run", action="store_true", help="Print profiles without saving")
    args = parser.parse_args()

    profiles: list[dict[str, Any]] = []

    if args.npm:
        p = profile_from_npm(args.npm)
        if p:
            profiles.append(p)
    elif args.pip:
        p = profile_from_pypi(args.pip)
        if p:
            profiles.append(p)
    elif args.npm_search:
        profiles = search_npm(args.npm_search, args.limit)

    if not profiles:
        print("No profiles generated.", file=sys.stderr)
        sys.exit(1)

    for profile in profiles:
        if args.dry_run:
            print(json.dumps(profile, indent=2))
        else:
            save_profile(profile, overwrite=args.overwrite)

    print(f"\n{len(profiles)} profile(s) processed.")
    needs_creds = [p["name"] for p in profiles if p.get("_needs_credentials")]
    if needs_creds:
        print("⚠  These likely need credentials (add env_vars to profile before running):")
        for name in needs_creds:
            print(f"   {name}")


if __name__ == "__main__":
    main()
