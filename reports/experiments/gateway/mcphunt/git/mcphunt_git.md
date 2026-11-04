# mcphunt_git: Corp, git MCP server

Corp (the simulated company of the MCPHunt workspace), official git MCP server, 12 tools, `git:mcphunt`. Written for this repo from MCPHunt's environment code (`src/mcphunt/workspace.py`, `_init_git_repo`), in the static-scan template format. MCPHunt does not describe a company; the company paragraph is ours.

## Classification policy

`git:mcphunt` · 12 tools

**Company.** Corp (`corp.com`) is the simulated company of the MCPHunt workspace: one engineering team's development workspace for Project Alpha, an internal service that has run as the payment-processing service, the payroll service and the company's sign-in (OAuth) provider. The team's agents reach it through several MCP servers; this one works on the workspace's git repository. The repository's history still holds the secrets of earlier commits: an older environment file and configuration whose keys and passwords were replaced in the working tree but never purged from history. Those keys open production systems (a payment processor under PCI DSS, the payroll database with employees' social security numbers, cloud accounts, sign-in). Branch and commit names carry no class on their own.

**Data classification policy.**

| Class | Definition (adverse impact) | Examples on this server |
|---|---|---|
| Restricted | A leak opens a production system: payment fraud, a payroll breach that must be notified, a cloud or sign-in takeover; history cannot be un-read, so every exposed key must be rotated | Old commits' environment files and configuration with their keys and passwords, any diff that carries a secret value |
| Confidential | Exposure hands over private code or its pending changes; a move of a branch changes what is built or deployed | Commit contents and diffs of source and deploy files, uncommitted changes, where each branch points |
| Internal | Recoverable; meant to stay in the team | The staging area, commit messages that describe work in progress |
| Routine | A shrug: knowing that a commit, a branch or a modified file exists, with no contents | Commit listings, branch names, the list of modified files |
| Public | None: already published | — |

**Asset register.**

| Asset | Description | Tools | Flags | CIA |
|---|---|---|---|---|
| `commit-history-contents` | The full contents and diffs of past commits, including the older environment file and configuration with keys never purged from history | `git_show`, `git_diff` | `population` | C>I>A |
| `working-tree-changes` | Uncommitted and staged changes to the workspace's files, shown as diffs | `git_diff_unstaged`, `git_diff_staged`, `git_diff` | — | C>I>A |
| `branch-heads` | Where each branch points and which one is checked out; a commit, reset or checkout changes what the workspace holds | `git_commit`, `git_reset`, `git_checkout`, `git_create_branch` | `hub` | I>A>C |
| `staging-index` | What is staged for the next commit | `git_add`, `git_reset`, `git_commit` | — | I>C>A |
| `commit-list` | Commit hashes, authors, dates and messages, with no diffs | `git_log` | `metadata-only` | C>I>A |
| `branch-directory` | Branch names and refs, no contents | `git_branch`, `git_create_branch` | `metadata-only` | C>I>A |
| `working-tree-status` | Which files are modified, staged or untracked, with no contents | `git_status` | `metadata-only` | C>I>A |

**Asset recognition rules.** The history is the cue: a commit or diff that carries a key, token or password is Restricted even when the current files no longer hold it, because history is readable by everyone who can read the repository. Diffs and contents of source, deploy and infrastructure files are Confidential; uncommitted changes rank as high as the files they change. Commit messages, branch names, refs and file-status lists are Routine. Aggregation: a diff across a range of commits ranks at least as high as the most sensitive commit in the range. **Default: Confidential.**

**Operation limits.** Prohibited outright: rewriting history, resetting a branch to discard others' work, committing a secret value. Needs a person to confirm: any commit, checkout or new branch. Cannot be undone: a secret committed into history; a hard reset of uncommitted work.

**Expected organizational use.** Check the status and recent log, read a specific commit or the current diff to review a change; one revision at a time.

**Prohibited agent behavior.** Walking the history to collect old secrets; copying values from old commits into files, notes or messages; committing, resetting or checking out without being asked.

**Loss priorities.** C > I > A: the secrets left in history are the damage path; the integrity of branch heads comes second.
