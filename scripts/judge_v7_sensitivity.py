"""Independent judge: did the scanner read each policy correctly?

The v7 arms disagree with the ``nacombo`` baseline on roughly half of all shared
assets. That number alone cannot distinguish two very different situations:

* **Justified divergence** — the ISO/NIST/CIS document genuinely describes the
  asset differently from the baseline document, so a different severity is the
  *correct* answer and the scanner did its job.
* **Scanner error** — the framework document says one thing and the scanner
  produced another. This is the failure that matters: a policy whose own words
  imply tier 3 scored as a 5.

Telling them apart needs a reading of the policy text that is independent of both
scanners. That is what this judge does.

METHOD — blind re-derivation, then arithmetic
---------------------------------------------
For every asset id that a v7 register and the baseline register share:

1. The judge is shown ONE policy section and ONE asset's register row, and asked
   to name the class that policy assigns and the 1-5 tier that class's own
   adverse-impact language implies. It must quote the policy sentence it relied
   on. It is shown **neither scanner's number**, and never both documents at
   once, so it cannot anchor or split the difference.
2. Step 1 runs twice per asset: once against the framework document, once against
   the baseline document. The baseline reading is cached across arms, since all
   three v7 arms compare to the same baseline text.
3. The verdict is then a deterministic function of four numbers — what each
   policy IMPLIES (judge) and what each scan PRODUCED — with no further model
   involvement:

   ``policy_divergence``  implied_v7 != implied_baseline
                          The two documents really do say different things.
   ``faithful``           scanner_v7 == implied_v7
                          The scanner read its own policy correctly.
   ``scanner_error``      scanner_v7 != implied_v7
                          The headline failure. Reported with its signed size, so
                          over-scoring and under-scoring are distinguishable.

   Baseline faithfulness (``scanner_baseline`` vs ``implied_baseline``) is
   reported too: a disagreement is not evidence against the v7 arm if the
   *baseline* is the one that misread its policy.

The judge shares ``render_asset_description`` with the scan driver, so the asset
text it reads is byte-identical to what the scanner read.

Writes ``JUDGE_SENSITIVITY.md``, ``judge_sensitivity.json`` and
``judge_sensitivity.csv`` into ``reports/experiments/v7/``.

Run (GPU):  python scripts/judge_v7_sensitivity.py
Smoke:      python scripts/judge_v7_sensitivity.py --limit 3
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mcp_security.llm.ollama_client import query_ollama  # noqa: E402
from mcp_security.static_scoring.server_policies import (  # noqa: E402
    parse_asset_register,
    policy_for,
    render_asset_description,
)

V7_DIR = REPO_ROOT / "reports" / "experiments" / "v7"
BASELINE_DIR = REPO_ROOT / "reports" / "experiments" / "v5" / "five_level_v2_policy_v5r_nacombo"
DOCS = REPO_ROOT / "docs" / "mcp-tools"

SERVERS = ("fs_corp_filesystem", "github_helios", "slack_vireo", "calendar_aurora")
ARMS = ("iso", "nist", "cis")
BASELINE = "nacombo"
DOC_FOR = {
    BASELINE: DOCS / "server-policies.md",
    "iso": DOCS / "server-policies-iso.md",
    "nist": DOCS / "server-policies-nist.md",
    "cis": DOCS / "server-policies-cis.md",
}

# The same 1-5 anchors every scoring arm maps onto. Restated here verbatim rather
# than imported from the scoring prompt: the judge must apply the same SCALE, but
# through its own reasoning, not by replaying the scanner's instructions.
TIER_ANCHORS = """  5  exposure alone is an emergency — exploitable or legally reportable the
     moment it leaks; OR a control plane, where losing it rewires what every
     other tool can reach.
  4  serious lasting harm one step removed: damages customers, staff or the
     organization's position, but is not instantly weaponizable.
  3  disruptive and embarrassing but recoverable; meant to stay in-org.
  2  low-value internal material; exposure is a shrug.
  1  already published or disposable — no confidentiality left to lose."""

JUDGE_PROMPT = """You are an independent reviewer auditing how a security scanner read an
organization's written policy. You are NOT the scanner. You are shown the
organization's policy for one server and ONE asset from its register, and you
decide for yourself what that policy says about this asset.

You are deliberately NOT told what any scanner scored. Do not guess at one.

THE ORGANIZATION'S POLICY
-------------------------
{policy}

THE ASSET YOU ARE JUDGING
-------------------------
asset id: {asset_id}
description: {description}
tools that can reach it: {tools}

YOUR TASK
---------
1. Find the class this organization's own classification scheme assigns to this
   asset. Use the scheme's named classes and its recognition rules. If the
   register or the scheme names a class for it, use that; otherwise apply the
   recognition rules, then the stated fail-closed default.
2. QUOTE the sentence or table row from the policy above that justifies your
   choice. Quote it verbatim. If nothing in the policy justifies a class, say so
   and use the default.
3. Map that class's own adverse-impact language onto this absolute scale:
{anchors}
   Judge the harm the POLICY describes, not how alarming the asset's name sounds.
   Data the organization says it has already published is 1, however sensitive
   its subject matter sounds.

Output ONLY valid JSON, no prose, no code fences:
{{"policy_class": "<the org's own class name>",
  "quote": "<verbatim sentence from the policy that justifies it>",
  "implied_tier": <integer 1-5>,
  "reasoning": "<one or two sentences>",
  "confidence": <0.0-1.0>}}"""


@dataclass
class Reading:
    """One blind re-derivation of a single asset against a single policy."""

    arm: str
    server: str
    asset_id: str
    policy_class: str
    quote: str
    implied_tier: int | None
    reasoning: str
    confidence: float


def load_scan(arm: str, server: str) -> dict:
    path = (
        BASELINE_DIR / f"{server}.json"
        if arm == BASELINE
        else V7_DIR / f"five_level_v2_policy_v7_{arm}" / f"{server}.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def register_rows(arm: str, server: str) -> dict:
    """``{asset_id: PolicyAssetRow}`` for one arm's register."""
    text = policy_for(server, doc=DOC_FOR[arm]).text
    return {row.asset_id: row for row in parse_asset_register(text)}


def judge_one(arm: str, server: str, asset_id: str, row, *, use_llm: bool = True) -> Reading:
    """One blind reading. The judge sees one policy and one asset, no numbers."""
    prompt = JUDGE_PROMPT.format(
        policy=policy_for(server, doc=DOC_FOR[arm]).text,
        asset_id=asset_id,
        description=render_asset_description(row),
        tools=", ".join(row.tools) or "(none)",
        anchors=TIER_ANCHORS,
    )
    result = query_ollama(prompt) if use_llm else None
    if not isinstance(result, dict) or "implied_tier" not in result:
        # A missing reading is recorded as such, never silently defaulted: an
        # unjudged asset must not be counted as agreement.
        return Reading(arm, server, asset_id, "", "", None, "judge returned no usable verdict", 0.0)
    try:
        tier = int(result["implied_tier"])
    except (TypeError, ValueError):
        tier = None
    if tier is not None and not 1 <= tier <= 5:
        tier = None
    return Reading(
        arm=arm,
        server=server,
        asset_id=asset_id,
        policy_class=str(result.get("policy_class", "")),
        quote=str(result.get("quote", "")),
        implied_tier=tier,
        reasoning=str(result.get("reasoning", "")),
        confidence=float(result.get("confidence", 0.0) or 0.0),
    )


def classify(implied_v7, implied_base, scan_v7, scan_base) -> dict:
    """The verdict — pure arithmetic on four numbers, no model involved."""
    if implied_v7 is None or implied_base is None:
        return {
            "verdict": "unjudged",
            "policy_divergence": None,
            "scanner_error": None,
            "error_size": None,
            "baseline_faithful": None,
        }
    faithful_v7 = scan_v7 == implied_v7
    faithful_base = scan_base == implied_base
    divergence = implied_v7 != implied_base
    if not faithful_v7:
        verdict = "scanner_error"
    elif divergence:
        verdict = "justified"
    else:
        verdict = "agrees"
    return {
        "verdict": verdict,
        "policy_divergence": divergence,
        "scanner_error": not faithful_v7,
        "error_size": scan_v7 - implied_v7,
        "baseline_faithful": faithful_base,
    }


def run(limit: int | None = None, *, use_llm: bool = True) -> dict:
    base_cache: dict[tuple[str, str], Reading] = {}
    records: list[dict] = []
    for arm in ARMS:
        for server in SERVERS:
            v7_rows = register_rows(arm, server)
            base_rows = register_rows(BASELINE, server)
            v7_scan = load_scan(arm, server)["asset_sensitivity"]
            base_scan = load_scan(BASELINE, server)["asset_sensitivity"]
            shared = sorted(set(v7_rows) & set(base_rows) & set(v7_scan) & set(base_scan))
            if limit:
                shared = shared[:limit]
            for asset in shared:
                key = (server, asset)
                if key not in base_cache:
                    base_cache[key] = judge_one(
                        BASELINE, server, asset, base_rows[asset], use_llm=use_llm
                    )
                base_read = base_cache[key]
                v7_read = judge_one(arm, server, asset, v7_rows[asset], use_llm=use_llm)
                verdict = classify(
                    v7_read.implied_tier, base_read.implied_tier, v7_scan[asset], base_scan[asset]
                )
                records.append(
                    {
                        "arm": arm,
                        "server": server,
                        "asset": asset,
                        "scanner_v7": v7_scan[asset],
                        "scanner_baseline": base_scan[asset],
                        "implied_v7": v7_read.implied_tier,
                        "implied_baseline": base_read.implied_tier,
                        **verdict,
                        "class_v7": v7_read.policy_class,
                        "class_baseline": base_read.policy_class,
                        "quote_v7": v7_read.quote,
                        "reasoning_v7": v7_read.reasoning,
                        "confidence_v7": v7_read.confidence,
                    }
                )
                print(
                    f"[judge] {arm:4s} {server:20s} {asset:28s} "
                    f"policy→{v7_read.implied_tier} scan→{v7_scan[asset]} "
                    f"{verdict['verdict']}",
                    flush=True,
                )
    return {"records": records, "readings_cached": len(base_cache)}


def summarize(records: list[dict]) -> dict:
    out: dict = {}
    for arm in ARMS:
        rows = [r for r in records if r["arm"] == arm and r["verdict"] != "unjudged"]
        if not rows:
            out[arm] = {"n": 0}
            continue
        counts = Counter(r["verdict"] for r in rows)
        errors = [r for r in rows if r["verdict"] == "scanner_error"]
        over = [r for r in errors if r["error_size"] > 0]
        under = [r for r in errors if r["error_size"] < 0]
        out[arm] = {
            "n": len(rows),
            "faithful": len(rows) - len(errors),
            "faithful_rate": round((len(rows) - len(errors)) / len(rows), 3),
            "scanner_error": len(errors),
            "scanner_error_rate": round(len(errors) / len(rows), 3),
            "over_scored": len(over),
            "under_scored": len(under),
            "mean_error_size": (
                round(statistics.fmean(r["error_size"] for r in errors), 2) if errors else 0.0
            ),
            "big_errors": sum(1 for r in errors if abs(r["error_size"]) >= 2),
            "justified": counts.get("justified", 0),
            "agrees": counts.get("agrees", 0),
            "policy_divergence": sum(1 for r in rows if r["policy_divergence"]),
            "baseline_unfaithful": sum(1 for r in rows if r["baseline_faithful"] is False),
        }
    return out


def to_markdown(summary: dict, records: list[dict]) -> str:
    lines = [
        "# Did the scanner read each policy correctly?",
        "",
        "Half of all v7 assets score differently from the `nacombo` baseline. That",
        "number cannot by itself tell a *justified* difference (the framework",
        "document genuinely says something else) from a *scanner error* (the",
        "document says one thing and the scanner produced another).",
        "",
        "This judge separates them. For every shared asset it re-derives the tier",
        "from the policy text alone — shown one document and one asset, and told",
        "neither scanner's number — then the verdict is arithmetic on four values:",
        "what each policy IMPLIES and what each scan PRODUCED.",
        "",
        "| verdict | meaning |",
        "|---|---|",
        "| `faithful` | scanner matches what its own policy implies |",
        "| `justified` | faithful **and** the two documents genuinely differ |",
        "| `agrees` | faithful, and both documents imply the same tier |",
        "| `scanner_error` | **the failure that matters** — policy implies X, scanner said Y |",
        "",
        "## Per arm",
        "",
        "| arm | judged | faithful | **scanner error** | over | under | ≥2 tiers | mean signed error |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ARMS:
        s = summary.get(arm, {})
        if not s.get("n"):
            lines.append(f"| `{arm}` | 0 | — | — | — | — | — | not judged |")
            continue
        lines.append(
            f"| `{arm}` | {s['n']} | {s['faithful_rate']:.0%} | **{s['scanner_error_rate']:.0%}** "
            f"| {s['over_scored']} | {s['under_scored']} | {s['big_errors']} "
            f"| {s['mean_error_size']:+.2f} |"
        )

    lines += [
        "",
        "## Is a difference from the baseline explained by the documents?",
        "",
        "`policy divergence` counts assets where the judge read the two documents as",
        "implying *different* tiers — a difference that is supposed to happen.",
        "`baseline unfaithful` counts assets where the **baseline** scanner, not the",
        "v7 one, departed from its own policy.",
        "",
        "| arm | policy divergence | justified | agrees | baseline unfaithful |",
        "|---|---:|---:|---:|---:|",
    ]
    for arm in ARMS:
        s = summary.get(arm, {})
        if not s.get("n"):
            lines.append(f"| `{arm}` | — | — | — | not judged |")
            continue
        lines.append(
            f"| `{arm}` | {s['policy_divergence']} | {s['justified']} | {s['agrees']} "
            f"| {s['baseline_unfaithful']} |"
        )

    errors = sorted(
        (r for r in records if r["verdict"] == "scanner_error"),
        key=lambda r: -abs(r["error_size"]),
    )
    if errors:
        lines += [
            "",
            "## Every scanner error, worst first",
            "",
            "`policy` is the tier the judge derived from that arm's own document;",
            "`scan` is what the arm produced. The quote is the policy sentence the",
            "judge relied on.",
            "",
            "| arm | server | asset | policy | scan | Δ | class the policy assigns |",
            "|---|---|---|---:|---:|---:|---|",
        ]
        for r in errors[:40]:
            lines.append(
                f"| `{r['arm']}` | `{r['server']}` | `{r['asset']}` | {r['implied_v7']} "
                f"| {r['scanner_v7']} | {r['error_size']:+d} | {r['class_v7']} |"
            )
        lines += ["", "### The three largest, with the policy's own words", ""]
        for r in errors[:3]:
            lines += [
                f"**`{r['arm']}` · `{r['server']}` · `{r['asset']}` — "
                f"policy implies {r['implied_v7']}, scanner said {r['scanner_v7']}**",
                "",
                f"> {r['quote_v7']}",
                "",
                f"Judge: {r['reasoning_v7']}",
                "",
            ]
    else:
        lines += [
            "",
            "## Scanner errors",
            "",
            "None: every judged asset matched what its own policy implies.",
            "",
        ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="assets per (arm, server)")
    parser.add_argument("--no-llm", action="store_true", help="plumbing smoke test only")
    parser.add_argument("--out-dir", type=Path, default=V7_DIR)
    args = parser.parse_args(argv)

    result = run(limit=args.limit, use_llm=not args.no_llm)
    records = result["records"]
    summary = summarize(records)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "judge_sensitivity.json").write_text(
        json.dumps({"summary": summary, "records": records}, indent=2), encoding="utf-8"
    )
    (args.out_dir / "JUDGE_SENSITIVITY.md").write_text(
        to_markdown(summary, records), encoding="utf-8"
    )
    if records:
        with (args.out_dir / "judge_sensitivity.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)

    for arm in ARMS:
        s = summary.get(arm, {})
        if s.get("n"):
            print(
                f"[judge] {arm}: {s['n']} judged | faithful {s['faithful_rate']:.0%} "
                f"| scanner errors {s['scanner_error']} "
                f"(over {s['over_scored']} / under {s['under_scored']})"
            )
    print(f"[judge] wrote JUDGE_SENSITIVITY.md and friends to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
