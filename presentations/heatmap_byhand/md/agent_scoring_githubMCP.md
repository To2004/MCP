# Independent Scoring - GitHub MCP

## Approach

The GitHub MCP server is an API wrapper that fronts a Personal Access Token (PAT)
or OAuth token. Risk is modeled as **token-scope blast radius**: every tool call
inherits the token's authority, so the scoring asks "if the agent invokes this
tool on this asset, what is the irreversible or sensitive impact assuming the
token holds the realistic default `repo` + `workflow` + `read:org` scopes?"
This frames the MCP server as the protected asset (the gateway to GitHub
resources) and the agent as the threat actor whose requests must be gated.

Scoring is grounded in NIST SP 800-30 (likelihood-times-impact, conservative
worst-case) and FIPS 199 confidentiality/integrity/availability bands, with the
4-level CVSS v3.1-style banding (Critical/High/Medium/Low). The dominant
amplifiers in the GitHub setting are: (a) secrets exfiltration (Action Secrets,
Secret Scanning alerts) is irreversible once leaked; (b) writes to
`.github/workflows/*` or merges to protected branches are persistent supply-chain
compromise vectors; (c) public reads are low because the data is already public;
(d) "delete" operations are graded by reversibility (tags/branches are easy to
restore, history rewrites are not).

## Scoring rubric

| Level    | Score | Definition |
|----------|-------|------------|
| Critical | 4     | Irreversible, token-blast-radius-critical; secrets exfil, CI compromise, merge to protected branch |
| High     | 3     | Significant write or sensitive read; bulk private data exposure; non-trivial integrity damage |
| Medium   | 2     | Noticeable but reversible; moderate read sensitivity; non-trusted writes that reviewers catch |
| Low      | 1     | Read of low-sensitivity or public surface; metadata-only writes |
| N/A      | 0     | Tool genuinely does not apply to this asset |

## 1. Tool-Group Ranking (avg danger per tool across all applicable assets)

### Empty structure (user's scoring blank)

| Rank | Tool Group                  | Risk | Reasoning |
|------|-----------------------------|------|-----------|
| 1    | (blank)                     |      |           |
| 2    | (blank)                     |      |           |
| 3    | (blank)                     |      |           |
| 4    | (blank)                     |      |           |
| 5    | (blank)                     |      |           |
| 6    | (blank)                     |      |           |
| 7    | (blank)                     |      |           |
| 8    | (blank)                     |      |           |
| 9    | (blank)                     |      |           |
| 10   | (blank)                     |      |           |
| 11   | (blank)                     |      |           |
| 12   | (blank)                     |      |           |
| 13   | (blank)                     |      |           |

### Agent's independent scoring

| Rank | Tool Group                  | Risk     | Reasoning |
|------|-----------------------------|----------|-----------|
| 1    | Merge PR                    | Critical | A merge to a protected/default branch persistently lands attacker-controlled code into production with no further review gate. |
| 2    | Trigger Workflow            | Critical | Dispatching Actions runs executes arbitrary CI code against Action Secrets, enabling secret exfil and signed artifact tampering. |
| 3    | Write Code (create/update)  | Critical | Writing under `.github/workflows/` is equivalent to remote code execution in CI; ordinary code writes can backdoor releases. |
| 4    | Read Security Alerts        | High     | Secret Scanning alerts can leak the actual secret material; CodeQL/Dependabot disclose unpatched vulnerabilities to attackers. |
| 5    | Admin / Repo Create         | High     | Repo creation, visibility flips, and settings changes can publicly expose private code or weaken branch protection. |
| 6    | Delete Code                 | High     | Branch/tag/file deletion is recoverable in most cases, but history rewrites and release deletions are not. |
| 7    | Issue / PR Write            | Medium   | Comments and PR openings are reviewable and reversible, but enable social-engineering and review-bypass plays. |
| 8    | Gist Write                  | Medium   | Public gists can be used to exfiltrate any data the agent has read, including private code, with the user's identity attached. |
| 9    | Read Code                   | Medium   | Bulk read of private repos is a confidentiality breach; public code read is low; averaged to medium. |
| 10   | Search / Discovery          | Medium   | Indexed search over private repos surfaces sensitive content fast; public search is low; averaged to medium. |
| 11   | Read Issues & PRs           | Low      | Issue/PR text is rarely Crown-jewel sensitive, but can leak internal vulnerability discussions. |
| 12   | Read Notifications          | Low      | Notifications expose recent activity and review requests; useful for reconnaissance but not directly damaging. |
| 13   | Identity / Context          | Low      | Whoami-style calls disclose only the authenticated principal, which the agent's caller already knows. |

## 2. Asset Category Ranking

### Empty structure (user's scoring blank)

| Rank | Asset Category     | Risk | Reasoning |
|------|--------------------|------|-----------|
| 1    | (blank)            |      |           |
| 2    | (blank)            |      |           |
| 3    | (blank)            |      |           |
| 4    | (blank)            |      |           |
| 5    | (blank)            |      |           |
| 6    | (blank)            |      |           |
| 7    | (blank)            |      |           |
| 8    | (blank)            |      |           |

### Agent's independent scoring

| Rank | Asset Category     | Risk     | Reasoning |
|------|--------------------|----------|-----------|
| 1    | Credentials        | Critical | Action Secrets are raw cleartext on extraction and grant downstream cloud/registry access; one read is game-over. |
| 2    | CI/CD              | Critical | Actions runs and job logs may echo secrets; dispatching runs equals arbitrary CI execution with full scope. |
| 3    | Security Findings  | High     | Secret Scanning alerts expose the secret itself; CodeQL/Dependabot reveal unpatched exploit paths. |
| 4    | Code               | High     | Private code is confidentiality-critical; workflow files are integrity-critical; public code is low - category averages high. |
| 5    | Governance         | High     | Repo admin can flip visibility (private->public leaks code) and disable branch protection (enables silent merges). |
| 6    | Collaboration      | Medium   | Issues/PRs/Discussions are reviewable and mostly textual; abuse is reputational and social rather than technical. |
| 7    | Personal           | Medium   | Gists can exfiltrate arbitrary data under the user's name; notifications are mostly recon-grade. |
| 8    | Identity           | Low      | User/org/team metadata is largely already-known or low-sensitivity directory information. |

## 3. Asset Ranking (16 individual assets)

### Empty structure (user's scoring blank)

| Rank | Asset                                | Risk | Reasoning |
|------|--------------------------------------|------|-----------|
| 1    | (blank)                              |      |           |
| 2    | (blank)                              |      |           |
| 3    | (blank)                              |      |           |
| 4    | (blank)                              |      |           |
| 5    | (blank)                              |      |           |
| 6    | (blank)                              |      |           |
| 7    | (blank)                              |      |           |
| 8    | (blank)                              |      |           |
| 9    | (blank)                              |      |           |
| 10   | (blank)                              |      |           |
| 11   | (blank)                              |      |           |
| 12   | (blank)                              |      |           |
| 13   | (blank)                              |      |           |
| 14   | (blank)                              |      |           |
| 15   | (blank)                              |      |           |
| 16   | (blank)                              |      |           |

### Agent's independent scoring

| Rank | Asset                                | Risk     | Reasoning |
|------|--------------------------------------|----------|-----------|
| 1    | Action Secrets (env-level)           | Critical | Secrets are cleartext credentials to cloud, registries, and signing keys; any read or write is irreversible. |
| 2    | Workflow / CI Files (.github)        | Critical | Any write here becomes remote code execution inside CI with full secret access on the next trigger. |
| 3    | Secret Scanning alerts               | Critical | Alert payloads include the leaked secret value itself; reading them equals exfiltrating live credentials. |
| 4    | GitHub Actions runs & job logs       | High     | Logs frequently leak partial secrets; rerun/dispatch primitives provide a foothold for CI compromise. |
| 5    | Private Repository Code              | High     | Bulk read of private code is a confidentiality breach; writes can introduce backdoors into shipping software. |
| 6    | Releases & Tags                      | High     | Releases are the supply-chain artifact consumers trust; tag/release manipulation can ship malicious binaries. |
| 7    | Code Scanning alerts (CodeQL)        | High     | Disclose locations of unpatched vulnerabilities (zero-day-grade intel for an attacker). |
| 8    | Dependabot alerts                    | High     | Map unpatched dependencies with known CVEs to specific repos; targeted exploitation enabler. |
| 9    | Repo admin (forks, stars, create)    | High     | Visibility flips expose private code; protection toggles enable silent malicious merges. |
| 10   | Pull Requests & Reviews              | Medium   | PRs are reviewable; merge is the dangerous step (scored separately), but PR write can dismiss reviews. |
| 11   | Gists (public & secret)              | Medium   | Public gist creation is a built-in data exfiltration channel; secret gists leak if URL is shared. |
| 12   | Issues & Comments                    | Medium   | Mostly social-impact; can leak internal vuln discussions and host phishing/instruction-injection content. |
| 13   | Discussions                          | Low      | Community-facing text; minimal write impact, low-sensitivity read. |
| 14   | Public Repository Code               | Low      | Already public by definition; read is free intel, write requires push rights and lands on the public repo. |
| 15   | User notifications                   | Low      | Recon value (what is the user working on) but no direct integrity or confidentiality damage. |
| 16   | User / Org / Team metadata           | Low      | Org charts and team rosters are low-sensitivity directory information. |

## 4. Tool x Asset cube - illustrative subset

Focused on the high-signal intersections: Credentials, Security Findings,
Workflow/CI Files, Merge PR, Trigger Workflow.

### Empty structure (user's scoring blank)

| #  | Tool Group                  | Asset                                | Risk |
|----|-----------------------------|--------------------------------------|------|
| 1  | Read Security Alerts        | Action Secrets (env-level)           |      |
| 2  | Read Security Alerts        | Secret Scanning alerts               |      |
| 3  | Read Security Alerts        | Code Scanning alerts (CodeQL)        |      |
| 4  | Read Security Alerts        | Dependabot alerts                    |      |
| 5  | Read Code                   | Action Secrets (env-level)           |      |
| 6  | Write Code (create/update)  | Workflow / CI Files (.github)        |      |
| 7  | Write Code (create/update)  | Public Repository Code               |      |
| 8  | Write Code (create/update)  | Private Repository Code              |      |
| 9  | Write Code (create/update)  | Releases & Tags                      |      |
| 10 | Delete Code                 | Workflow / CI Files (.github)        |      |
| 11 | Delete Code                 | Releases & Tags                      |      |
| 12 | Merge PR                    | Private Repository Code              |      |
| 13 | Merge PR                    | Workflow / CI Files (.github)        |      |
| 14 | Merge PR                    | Public Repository Code               |      |
| 15 | Trigger Workflow            | GitHub Actions runs & job logs       |      |
| 16 | Trigger Workflow            | Action Secrets (env-level)           |      |
| 17 | Admin / Repo Create         | Repo admin (forks, stars, create)    |      |
| 18 | Admin / Repo Create         | Private Repository Code              |      |
| 19 | Gist Write                  | Gists (public & secret)              |      |
| 20 | Issue / PR Write            | Pull Requests & Reviews              |      |

### Agent's independent scoring

| #  | Tool Group                  | Asset                                | Risk     | Reasoning |
|----|-----------------------------|--------------------------------------|----------|-----------|
| 1  | Read Security Alerts        | Action Secrets (env-level)           | N/A      | Read-alerts API does not return secret values directly; secrets surface via Secret Scanning, not this asset. |
| 2  | Read Security Alerts        | Secret Scanning alerts               | Critical | Alert body contains the actual leaked secret; one call equals credential exfil. |
| 3  | Read Security Alerts        | Code Scanning alerts (CodeQL)        | High     | Discloses exact file/line of unpatched vulns - zero-day-grade reconnaissance. |
| 4  | Read Security Alerts        | Dependabot alerts                    | High     | Reveals unpatched CVE-laden dependencies per repo; targets exploitation. |
| 5  | Read Code                   | Action Secrets (env-level)           | N/A      | Secrets are not stored in repo content; read-code does not reach this asset. |
| 6  | Write Code (create/update)  | Workflow / CI Files (.github)        | Critical | Writing a workflow file is remote code execution in CI on next trigger, with full secret scope. |
| 7  | Write Code (create/update)  | Public Repository Code               | High     | Public writes are visible but can still ship malicious code that downstream consumers pull. |
| 8  | Write Code (create/update)  | Private Repository Code              | High     | Backdoors land in shipping internal software; harder to detect than public writes. |
| 9  | Write Code (create/update)  | Releases & Tags                      | High     | Editing release assets ships tampered binaries to every downstream consumer. |
| 10 | Delete Code                 | Workflow / CI Files (.github)        | High     | Removing a workflow can disable security scanning or required CI, weakening defenses silently. |
| 11 | Delete Code                 | Releases & Tags                      | High     | Release deletion is not always reversible and breaks dependent consumers' integrity assumptions. |
| 12 | Merge PR                    | Private Repository Code              | Critical | A merged PR persistently lands attacker-controlled code into the trusted history of private software. |
| 13 | Merge PR                    | Workflow / CI Files (.github)        | Critical | Merging a workflow change is the canonical supply-chain compromise vector for GitHub. |
| 14 | Merge PR                    | Public Repository Code               | High     | Merge is persistent; public visibility makes detection more likely but does not undo shipped code. |
| 15 | Trigger Workflow            | GitHub Actions runs & job logs       | Critical | Dispatching arbitrary workflows executes attacker-chosen code with full secrets context. |
| 16 | Trigger Workflow            | Action Secrets (env-level)           | Critical | Triggering a malicious workflow is the standard primitive for exfiltrating Action Secrets. |
| 17 | Admin / Repo Create         | Repo admin (forks, stars, create)    | High     | Visibility flips and protection changes are persistent governance failures. |
| 18 | Admin / Repo Create         | Private Repository Code              | High     | Flipping a private repo to public exposes the entire codebase irreversibly (history persists in forks). |
| 19 | Gist Write                  | Gists (public & secret)              | Medium   | Built-in exfiltration channel under the user's identity; impact bounded by what the agent can already read. |
| 20 | Issue / PR Write            | Pull Requests & Reviews              | Medium   | Comments and dismiss-review actions can pressure or bypass human reviewers without directly landing code. |

## Notes

**Where the GitHub token-scope model bites differently than filesystem.**
Filesystem MCP servers map cleanly onto path/permission trees - the asset is
the file. For GitHub, the relevant blast radius is the token's *scope set*
(`repo`, `workflow`, `read:org`, etc.), and a single high-scope token cuts
across every repo the principal can reach. That means "Read Code" on Private
Repository Code is not bounded to a directory the user opted in to; it spans
everything the token sees. Static scoring therefore conservatively assumes the
worst-case private surface for any tool that authenticates with a `repo`-scope
token.

**CodeQL vs Secret Scanning severity distinction.**
Both live under "Read Security Alerts," but their data-sensitivity profiles
differ sharply. **Secret Scanning** alert bodies routinely embed the literal
secret string (e.g. `AKIA...`, `ghp_...`); reading the alert is functionally
equivalent to exfiltrating the credential, hence Critical. **CodeQL** alerts
reveal the location and shape of an unpatched vulnerability but do not hand
over a working credential - they are reconnaissance gold (High) rather than
ready-to-use loot. **Dependabot** alerts sit alongside CodeQL: they enumerate
known-vulnerable dependencies per repo, which is high-value targeting data but
again not directly exploitative on its own.

**Ambiguous cells.**

- *Trigger Workflow x Public Repository Code*: marked High in absentia
  because triggering a workflow that touches only public code still consumes
  scoped tokens and produces logs that may leak. Scored conservatively.
- *Issue / PR Write x Workflow / CI Files*: opening a PR that *modifies* a
  workflow is reviewable and bounded - the danger is when **Merge PR** acts on
  it, so the write tool itself is graded Medium and the merge is Critical.
- *Read Code x Workflow / CI Files*: arguably High because workflow files can
  reveal CI structure and self-hosted runner names useful for targeting. Kept
  at the same band as private code read (High in the per-asset roll-up).
- *Gist Write* is scored Medium overall, but in a setting where the agent
  has already exfiltrated private code, gist creation becomes a Critical
  channel - this is a dynamic-context concern, not static.

**Why "Merge PR" outranks "Write Code" at the tool-group level.**
Both can land malicious code, but `Write Code` typically creates a branch or
commit that still has to pass review and CI before becoming part of the
trusted history. `Merge PR` is the *gating step*: a single tool call collapses
the review gate and commits attacker code to the default branch, where it
flows immediately into release pipelines, CI caches, and downstream consumers.
In a typical agent setup the merge primitive is also the most under-monitored
because reviewers expect humans to press the button.

**Delete operations - why High and not Critical.**
GitHub retains a 90-day reflog for deleted branches and tags, and the API
supports restoration; deleted issues/PRs can be recovered by support. Release
deletion and force-pushed history rewrites are the genuinely irreversible
sub-cases, but they are not the default behavior of a "delete" primitive.
Averaging across the realistic delete surface lands at High, with Critical
reserved for the irreversible specialisations that occur in the dynamic layer
(e.g. `force=true`, `prune=true`).

**Token-scope assumption baked into this matrix.**
This scoring assumes the realistic worst-case PAT scope for an "all-purpose
GitHub agent": `repo` (full read/write across private and public repos), 
`workflow` (modify workflow files), and `read:org`. Fine-grained tokens or
GitHub App installations with narrower permission sets would compress several
High cells to Medium - but at design time the server must score for the
broadest token its clients are likely to present. This conservative posture
matches NIST SP 800-30's worst-case impact convention.

**Ambiguous cells.**

- *Trigger Workflow x Public Repository Code*: marked High in absentia
  because triggering a workflow that touches only public code still consumes
  scoped tokens and produces logs that may leak. Scored conservatively.
- *Issue / PR Write x Workflow / CI Files*: opening a PR that *modifies* a
  workflow is reviewable and bounded - the danger is when **Merge PR** acts on
  it, so the write tool itself is graded Medium and the merge is Critical.
- *Read Code x Workflow / CI Files*: arguably High because workflow files can
  reveal CI structure and self-hosted runner names useful for targeting. Kept
  at the same band as private code read (High in the per-asset roll-up).
- *Gist Write* is scored Medium overall, but in a setting where the agent
  has already exfiltrated private code, gist creation becomes a Critical
  channel - this is a dynamic-context concern, not static.
- *Search / Discovery x Private Repository Code*: code-search across private
  repos can surface secrets in code (hardcoded keys, `.env` files committed by
  accident); a Critical case if it lands a hit, but on average High because
  most search hits are non-sensitive.
- *Read Notifications*: notifications themselves are low-impact, but their
  aggregate exposes the user's review queue and active investigations, which
  is medium-value reconnaissance for a patient attacker. Kept at Low for
  static scoring because no single call provides actionable damage.

**Calibration against the filesystem baseline.**
On the filesystem MCP server, the highest-risk static cell is typically
"Write" or "Execute" against system config paths. The GitHub equivalent is
not the file-content write but rather the *workflow trigger and merge*
operations, because GitHub's compute fabric (Actions) is where the agent's
write becomes execution. A defender porting filesystem heuristics to GitHub
should mentally remap `Write x /etc` to `Write x .github/workflows` and
`Execute x bin/` to `Trigger Workflow` and `Merge PR`.

**Out of scope for static scoring.**
Per the framework's threat model, the inverse direction (malicious GitHub
server -> agent) is not scored here. Runtime context (which repo, which branch,
which user, whether the target branch has protection, whether secrets are
present, whether the agent has already exfiltrated data this session) is
reserved for the dynamic layer of the scoring framework; this matrix captures
the design-time worst-case per (tool, asset) pair. The dynamic layer is
expected to multiplicatively adjust these static bands - for example, a Merge
PR call against an unprotected fork's branch may drop from Critical to
Medium, while a Read Code call that hits a `.env` file may escalate from
Medium to Critical.
