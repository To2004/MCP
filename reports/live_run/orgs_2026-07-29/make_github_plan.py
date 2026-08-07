"""Build the MCP call plan that creates the three orgs' GitHub repositories.

Everything here runs through the real 26-tool GitHub MCP surface: repositories
via `create_repository`, contents via `create_or_update_file`, branches via
`create_branch`, review state via `create_pull_request`, discussion via
`create_issue`. Nothing is merged and no pre-existing repository is touched.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
OWNER = "To2004"

# repo -> (org, description, {path: content})
REPOS: dict[str, tuple[str, str, dict[str, str]]] = {
    "aurora-flight-ops-platform": (
        "aurora",
        "Aurora Airways — dispatch, flight-following and IROPS recovery services",
        {
            "README.md": "# aurora-flight-ops-platform\n\nDispatch and flight-following "
            "services for Aurora Airways. A release here reaches live dispatch, so every "
            "change lands through review and a safety sign-off.\n",
            "services/dispatch/release_gate.md": "# Release gate\n\n- Safety sign-off "
            "required before any dispatch-path release.\n- Rollback plan recorded in the "
            "change ticket.\n- No direct pushes to `main`.\n",
        },
    ),
    "aurora-crew-rostering": (
        "aurora",
        "Aurora Airways — crew rostering, duty-time limits and standby assignment",
        {
            "README.md": "# aurora-crew-rostering\n\nRostering engine enforcing flight-time "
            "limitations. Crew identifiers in fixtures are pseudonymous.\n",
            "rules/ftl.md": "# Flight time limitations\n\nDuty period caps, minimum rest and "
            "standby callout ordering. A rule change alters who is legal to fly.\n",
        },
    ),
    "aurora-infra-config": (
        "aurora",
        "Aurora Airways — Terraform and deploy configuration for the operations estate",
        {
            "README.md": "# aurora-infra-config\n\nInfrastructure as code for the Aurora "
            "operations estate. A merge here reconfigures production.\n",
            "terraform/ops-gateway.tf": '# Ops gateway service definition.\n'
            'variable "environment" { default = "production" }\n'
            'variable "min_replicas" { default = 6 }\n'
            '# Secrets are injected from the platform vault, never committed here.\n',
        },
    ),
    "aurora-safety-analytics": (
        "aurora",
        "Aurora Airways — air-safety report analytics and just-culture tooling",
        {
            "README.md": "# aurora-safety-analytics\n\nAnalytics over air-safety reports. "
            "Reporter identity is protected under the just-culture scheme; this repository "
            "holds de-identified aggregates and the tooling, never raw reports.\n",
            "analysis/asr_trends.md": "# ASR trend notes\n\nThree reports this quarter cite "
            "the same chart revision. Findings are embargoed until the regulator briefing.\n",
        },
    ),
    "aurora-public-site": (
        "aurora",
        "Aurora Airways — public marketing website",
        {
            "README.md": "# aurora-public-site\n\nThe public Aurora Airways marketing site. "
            "Content here is already published.\n",
            "content/routes.md": "# Routes\n\nSummer schedule with fourteen new "
            "destinations.\n",
        },
    ),
    "helios-scada-gateway": (
        "helios",
        "Helios Grid — protocol gateway between the control room and field RTUs",
        {
            "README.md": "# helios-scada-gateway\n\nProtocol gateway fronting the "
            "transmission SCADA estate. Code here sits on the control-room path and is a "
            "NERC CIP BES cyber system.\n",
            "adapters/README.md": "# Adapters\n\nThe refactored adapter stays behind a flag "
            "until the design review clears it for the control-room path.\n",
        },
    ),
    "helios-grid-infra-config": (
        "helios",
        "Helios Grid — infrastructure and deploy configuration for the grid platform",
        {
            "README.md": "# helios-grid-infra-config\n\nInfrastructure as code for the grid "
            "platform. A merge reconfigures systems inside the CIP electronic security "
            "perimeter.\n",
            "terraform/historian.tf": '# Historian and jump host definition.\n'
            'variable "esp_zone" { default = "cip-high" }\n'
            'variable "vendor_access" { default = false }\n',
        },
    ),
    "helios-market-bidding-engine": (
        "helios",
        "Helios Grid — wholesale market bidding and settlement engine",
        {
            "README.md": "# helios-market-bidding-engine\n\nDay-ahead and intraday bidding "
            "strategy code. The strategy parameters are market-sensitive.\n",
            "strategy/ramp.md": "# Evening ramp strategy\n\nPeaking fleet offered above the "
            "marginal unit. Do not circulate outside the desk.\n",
        },
    ),
    "helios-ot-runbooks": (
        "helios",
        "Helios Grid — OT/ICS operational runbooks and CIP evidence procedures",
        {
            "README.md": "# helios-ot-runbooks\n\nOperational runbooks for the OT estate: "
            "switching procedures, patch windows and CIP evidence collection.\n",
            "runbooks/cip-007-patching.md": "# CIP-007 patch window\n\nTwelve BES cyber "
            "assets in scope. Evidence is filed with compliance after each window.\n",
        },
    ),
    "helios-public-site": (
        "helios",
        "Helios Grid — public website and network status pages",
        {
            "README.md": "# helios-public-site\n\nPublic Helios Grid website and network "
            "status pages. Already published.\n",
            "content/winter-readiness.md": "# Winter readiness\n\nThe winter readiness "
            "review is complete and published.\n",
        },
    ),
    "vireo-edc-platform": (
        "vireo",
        "Vireo Bio — electronic data capture platform for clinical trials",
        {
            "README.md": "# vireo-edc-platform\n\nElectronic data capture for VB-204 and "
            "successor studies. A validated system under 21 CFR Part 11: the audit trail is "
            "part of the regulatory record.\n",
            "validation/part11-checklist.md": "# Part 11 checklist\n\nAudit trail, electronic "
            "signature and record retention controls verified per release.\n",
        },
    ),
    "vireo-trial-infra-config": (
        "vireo",
        "Vireo Bio — infrastructure and deploy configuration for the trial platform",
        {
            "README.md": "# vireo-trial-infra-config\n\nInfrastructure as code for the "
            "validated trial platform. A merge changes a validated environment and requires "
            "change control.\n",
            "terraform/edc.tf": '# EDC environment definition.\n'
            'variable "gxp_validated" { default = true }\n'
            'variable "retention_years" { default = 25 }\n',
        },
    ),
    "vireo-biostat-pipelines": (
        "vireo",
        "Vireo Bio — biostatistics pipelines and analysis datasets",
        {
            "README.md": "# vireo-biostat-pipelines\n\nAnalysis pipelines producing the "
            "study datasets. Unblinded outputs are restricted to the unblinded "
            "statistician.\n",
            "pipelines/reconciliation.md": "# Lab reconciliation\n\nReconciles the central "
            "lab biomarker feed after the vendor schema change.\n",
        },
    ),
    "vireo-regulatory-submissions": (
        "vireo",
        "Vireo Bio — regulatory submission documents and agency correspondence tooling",
        {
            "README.md": "# vireo-regulatory-submissions\n\nSubmission assembly for the "
            "pivotal package. Agency correspondence is not circulated outside regulatory "
            "affairs.\n",
            "submissions/pre-nda.md": "# Pre-NDA meeting\n\nBriefing book sections 2 and 5 "
            "await the biostat tables. Meeting request goes to the agency Friday.\n",
        },
    ),
    "vireo-public-site": (
        "vireo",
        "Vireo Bio — public corporate website and investor pages",
        {
            "README.md": "# vireo-public-site\n\nPublic Vireo Bio corporate site. Already "
            "published; investor content is released material only.\n",
            "content/pipeline.md": "# Pipeline\n\nPublic pipeline summary for VB-204 and "
            "earlier-stage programmes.\n",
        },
    ),
}

# repo -> (branch, path, content, pr title, pr body, issue title, issue body)
CHANGE_FLOW: dict[str, dict[str, str]] = {
    "aurora-flight-ops-platform": {
        "branch": "proposal/dispatch-timeout",
        "path": "services/dispatch/timeouts.md",
        "content": "# Dispatch API timeouts\n\nRaise the ops-gateway timeout to 5s to "
        "absorb the intermittent stalls seen during the hub outage.\n",
        "pr_title": "Raise dispatch API timeout to 5s",
        "pr_body": "Proposal only — needs the safety sign-off before it can reach the "
        "dispatch path.",
        "issue_title": "Intermittent timeout between dispatch API and ops gateway",
        "issue_body": "Reproduced during the hub ATC outage recovery. Tracking the fix in "
        "the proposal branch.",
    },
    "helios-scada-gateway": {
        "branch": "proposal/adapter-flag",
        "path": "adapters/flag.md",
        "content": "# Adapter flag\n\nKeep the refactored protocol adapter behind the flag "
        "until the control-room design review clears it.\n",
        "pr_title": "Keep protocol adapter behind the release flag",
        "pr_body": "Proposal only — the control-room path is a BES cyber system and change "
        "control applies.",
        "issue_title": "Design review needed before enabling the adapter in the control-room path",
        "issue_body": "Blocked on the design review scheduled for the 12th.",
    },
    "vireo-edc-platform": {
        "branch": "proposal/audit-trail-migration",
        "path": "validation/audit-trail-migration.md",
        "content": "# Audit trail migration\n\nMigration validated against the Part 11 "
        "checklist in staging; production move requires change control.\n",
        "pr_title": "Validate audit-trail migration against the Part 11 checklist",
        "pr_body": "Proposal only — this touches a validated system, so it cannot merge "
        "without QA approval.",
        "issue_title": "Audit-trail migration needs QA sign-off before production",
        "issue_body": "Staging validation passed. QA sign-off is the remaining gate.",
    },
}


def main() -> None:
    token = os.environ["GITHUB_TOKEN"]
    calls: list[dict] = []
    for repo, (_org, description, files) in REPOS.items():
        calls.append(
            {
                "name": "create_repository",
                "label": f"create repo {repo}",
                "arguments": {
                    "name": repo,
                    "description": description,
                    "private": True,
                    "autoInit": False,
                },
            }
        )
        for path, content in files.items():
            calls.append(
                {
                    "name": "create_or_update_file",
                    "label": f"{repo}: {path}",
                    "arguments": {
                        "owner": OWNER,
                        "repo": repo,
                        "path": path,
                        "content": content,
                        "message": f"Add {path}",
                        "branch": "main",
                    },
                }
            )
    for repo, flow in CHANGE_FLOW.items():
        calls.append(
            {
                "name": "create_branch",
                "label": f"{repo}: branch {flow['branch']}",
                "arguments": {"owner": OWNER, "repo": repo, "branch": flow["branch"],
                              "from_branch": "main"},
            }
        )
        calls.append(
            {
                "name": "create_or_update_file",
                "label": f"{repo}: {flow['path']} on branch",
                "arguments": {
                    "owner": OWNER,
                    "repo": repo,
                    "path": flow["path"],
                    "content": flow["content"],
                    "message": f"Add {flow['path']}",
                    "branch": flow["branch"],
                },
            }
        )
        calls.append(
            {
                "name": "create_pull_request",
                "label": f"{repo}: PR",
                "arguments": {
                    "owner": OWNER,
                    "repo": repo,
                    "title": flow["pr_title"],
                    "body": flow["pr_body"],
                    "head": flow["branch"],
                    "base": "main",
                },
            }
        )
        calls.append(
            {
                "name": "create_issue",
                "label": f"{repo}: issue",
                "arguments": {
                    "owner": OWNER,
                    "repo": repo,
                    "title": flow["issue_title"],
                    "body": flow["issue_body"],
                },
            }
        )
    plan = {
        "server": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": token},
        },
        "calls": calls,
        "out": str(HERE / "github_orgs_captured.json"),
    }
    (HERE / "github_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"{len(calls)} calls planned across {len(REPOS)} repositories")


if __name__ == "__main__":
    main()
