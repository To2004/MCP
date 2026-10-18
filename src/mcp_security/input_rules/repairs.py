"""Design-time repairs the program makes to a model's rule before checking it (v13).

Each repair writes into the rule something the model should not have to decide:

- an asset-name (``register``) rule gets the policy's whole asset register,
  with each asset's scanned level, as its lookup table;
- a text (``keywords``) rule gets the secret words at level 5.

The repaired rule is the one stored, so the table a run writes can be read on
its own at run time.
"""

from __future__ import annotations

from mcp_security.input_rules.rules import CREDENTIAL_LEVEL, CREDENTIAL_WORDS, _is_level
#: Marks a group the program added, so a repeat repair replaces it rather than stacking.
ADDED_BY_PROGRAM = "program"


def with_credential_words(rule: dict) -> dict:
    """``rule`` with the credential words as a level-5 group, if it reads text.

    A path, a query, a body or a command can name or carry a credential, so
    every ``keywords`` rule rates them at 5. So does a ``register`` rule with no
    asset table (a server with no policy), which reads names only by their
    words. A rule whose groups are not a list is returned as is, for the check
    to report."""
    kind = rule.get("kind")
    groups = rule.get("groups")
    if kind not in ("keywords", "register") or rule.get("assets") or not isinstance(groups, list):
        return rule
    own = [g for g in groups if not (isinstance(g, dict) and g.get("added_by") == ADDED_BY_PROGRAM)]
    secret = {"contains": list(CREDENTIAL_WORDS), "level": CREDENTIAL_LEVEL,
              "added_by": ADDED_BY_PROGRAM}
    return {**rule, "groups": [*own, secret]}


def with_register_assets(rule: dict, assets: dict[str, int]) -> dict:
    """A ``register`` rule that looks names up in ``assets``, the policy's whole register.

    An input that names an asset can name any of the server's assets, whatever
    the tool, so the table is the server's, not the tool's. The scanned levels
    decide. A name word the model added is kept only at a level no listed asset
    reaches: elsewhere the policy says nothing about it, and the level already
    has an entry. With an empty ``assets`` (no policy) an override can name
    nothing, so it is dropped and the rest of the rule kept. Rules of other
    kinds come back as is."""
    if rule.get("kind") != "register":
        return rule
    if not assets:
        return {k: v for k, v in rule.items() if k != "overrides"} if "overrides" in rule else rule
    reached = set(assets.values())
    groups = rule.get("groups")
    kept = [g for g in groups if isinstance(g, dict) and _is_level(g.get("level"))
            and g["level"] not in reached] if isinstance(groups, list) else []
    return {**rule, "assets": dict(assets), "groups": kept}
