# Static scan: mcphunt_git

Sensitivity of 7 assets, impact of 12 tools, blast radius of 84 tool–asset pairs. Each is its own level from 1 to 5; nothing in this report is multiplied, combined or ranked.

| Run | |
|---|---|
| Catalog | `/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/git/mcphunt_git.json` (sha256 `43fc262b4e37`) |
| Policy | `/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/git/mcphunt_git.md` (classification section sha256 `216b7f99cafc`) |
| Scanner prompts | scanner-v1, as in the research runs |
| Model | qwen2.5:32b (digest `9f13ba1299af`) |
| Finished | 2026-11-01T11:27:41+00:00 |

## For review

- 8 pair(s) the register does not list, rated by the model: `git_status` → `working-tree-changes` (2), `git_diff_staged` → `staging-index` (3), `git_add` → `working-tree-changes` (2), `git_reset` → `working-tree-changes` (5), `git_log` → `commit-history-contents` (5), `git_checkout` → `branch-directory` (2), `git_checkout` → `working-tree-status` (2), `git_branch` → `branch-heads` (2). Add them to the register, or confirm they are wrong.

## Asset sensitivity

| Asset | Level | Class | Reason |
|---|---|---|---|
| `commit-history-contents` | 4 | Restricted | The asset holds the full contents and diffs of past commits, including older environment files and configurations with keys never purged from history. According to the policy's data classification, this exposure opens production systems to… |
| `working-tree-changes` | 3 | Confidential | The asset holds uncommitted and staged changes to the workspace's files, shown as diffs. According to the policy, diffs and contents of source, deploy and infrastructure files are classified as Confidential. |
| `branch-heads` | 3 | Confidential | The asset 'branch-heads' holds information about where each branch points and which one is checked out. According to the policy, exposure hands over private code or its pending changes; a move of a branch changes what is built or deployed,… |
| `staging-index` | 3 | Internal | The staging index holds what is staged for the next commit, which is classified as 'Internal' according to the policy's asset register. |
| `commit-list` | 2 | Routine | The asset holds commit hashes, authors, dates and messages with no diffs, which is classified as Routine according to the organization's policy. |
| `branch-directory` | 2 | Routine | The asset holds branch names and refs with no contents, which is classified as Routine according to the policy's recognition rules. |
| `working-tree-status` | 2 | Routine | The asset holds metadata-only information about which files are modified, staged or untracked without any contents. According to the policy's classification, such metadata is categorized as Routine. |

## Tool impact

| Tool | Level | Operation | Decided by | Why |
|---|---|---|---|---|
| `git_status` | 2 | metadata | rules | metadata verbs: \bstatus\b |
| `git_diff_unstaged` | 3 | read | rules | read verbs: \bdiff\b |
| `git_diff_staged` | 3 | read | rules | read verbs: \bdiff\b |
| `git_diff` | 3 | read | rules | read verbs: \bdiff\b |
| `git_commit` | 4 | write (rules unsure) | model | The tool 'git_commit' records changes to the repository by writing a commit message and updating the repository state with those changes. This operation involves modifying the content of the repository, which aligns with an ordinary write … |
| `git_add` | 3 | write (rules unsure) | model | The tool 'git_add' adds file contents to the staging area in a Git repository. This operation modifies the state of the files by preparing them for commit but does not finalize the changes until a commit is made. The impact involves changi… |
| `git_reset` | 5 | remove | rules | remove verbs: \breset\b |
| `git_log` | 2 | read (rules unsure) | model | The tool 'git_log' only shows commit logs which are metadata about the commits such as timestamps and commit messages. It does not modify or remove any content. |
| `git_create_branch` | 4 | write (rules unsure) | model | The tool creates a new branch from an optional base branch in a repository. This operation involves writing to the repository by creating a new branch, which is considered an ordinary write operation. |
| `git_checkout` | 2 | write (rules unsure) | model | The tool 'git_checkout' switches branches in a git repository. This operation does not read or write content directly but changes the state of the working directory to reflect another branch, which is akin to changing metadata such as the … |
| `git_show` | 3 | read | rules | read verbs: \bshow\b, \bcontents?\b |
| `git_branch` | 2 | write (rules unsure) | model | The tool lists Git branches based on the provided parameters without modifying any content or metadata. It only returns information about the branches which falls under reading metadata. |

## Blast radius

One table per asset: the tools that reach it, and how far one call's consequences spread (1 one person or item, 2 one group, 3 several groups, 4 the whole organization, 5 beyond it). *Escape* is the reason the model gave for a 5.

### `commit-history-contents`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `git_diff` | 3 | yes | Q2: “the older environment file and configuration with keys never purged from history” | The tool git_diff is listed in the organization's register as reaching this asset, and it can indeed show differences between branches or commits which includes accessing past commit contents. |
| `git_log` | 5 | no | Q2: “Old commits' environment files and configuration with their keys and passwords, any diff that carries a secret value” | The tool git_log can access the commit history, which includes the full contents and diffs of past commits as described in the asset description. |
| `git_show` | 4 | yes | Q2: “an older environment file and configuration whose keys and passwords were replaced in the working tree but never purged from history. Those keys open production systems (a payment processor under PCI DSS, the payroll database with emp… | The tool 'git_show' is listed in the organization's register as reaching this asset, and its description matches the asset's contents. |

Not reached: `git_status`, `git_diff_unstaged`, `git_diff_staged`, `git_commit`, `git_add`, `git_reset`, `git_create_branch`, `git_checkout`, `git_branch`

### `working-tree-changes`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `git_status` | 2 | no | none | The tool 'git_status' does not directly list the asset 'working-tree-changes', but it shows the status of uncommitted and staged changes, which are part of this asset. |
| `git_diff_unstaged` | 3 | yes | Q2: “Exposure hands over private code or its pending changes; a move of a branch changes what is built or deployed” | The tool 'git_diff_unstaged' is listed in the organization's register as reaching this asset, and its description matches the asset's description of uncommitted changes. |
| `git_diff_staged` | 3 | yes | Q2: “Uncommitted and staged changes to the workspace's files, shown as diffs (loss axis: C>I>A)” | The tool 'git_diff_staged' is listed in the organization's register as reaching this asset, and its description matches the asset's description of showing staged changes. |
| `git_diff` | 3 | yes | Q2: “Uncommitted and staged changes to the workspace's files, shown as diffs (loss axis: C>I>A)” | The tool is listed in the organization's register as reaching this asset. |
| `git_add` | 2 | no | none | The tool 'git_add' adds file contents to the staging area, which is part of the working tree changes asset. |
| `git_reset` | 5 | no | Q2: “Uncommitted and staged changes to the workspace's files, shown as diffs (loss axis: C>I>A)” | The tool git_reset unstages all staged changes, which directly affects the working-tree-changes asset. |

Not reached: `git_commit`, `git_log`, `git_create_branch`, `git_checkout`, `git_show`, `git_branch`

### `branch-heads`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `git_commit` | 4 | yes | Q2: “a commit, reset or checkout changes what the workspace holds (loss axis: I>A>C)” | The organization's register lists this tool as reaching the asset. |
| `git_reset` | 5 | yes | Q2: “a commit, reset or checkout changes what the workspace holds (loss axis: I>A>C)” | The organization's register lists this tool as reaching the asset. |
| `git_create_branch` | 4 | yes | none | The tool 'git_create_branch' is listed in the organization's register as reaching this asset, and it directly affects where branches point. |
| `git_checkout` | 2 | yes | none | The tool 'git_checkout' is listed in the organization's register as reaching this asset, and its description matches the asset's description of changing what the workspace holds. |
| `git_branch` | 2 | no | none | The tool 'git_branch' lists branches, which are part of the asset 'branch-heads'. Although it is not listed in the organization's register, it still affects this asset by providing information about branch heads. |

Not reached: `git_status`, `git_diff_unstaged`, `git_diff_staged`, `git_diff`, `git_add`, `git_log`, `git_show`

### `staging-index`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `git_diff_staged` | 3 | no | Q2 | The tool 'git_diff_staged' is relevant to the asset 'staging-index', as it shows changes that are staged for commit, which directly relates to what is staged in the staging index. |
| `git_commit` | 4 | yes | Q2: “Exposure hands over private code or its pending changes; a move of a branch changes what is built or deployed” | The organization's register lists this tool as reaching the asset. |
| `git_add` | 2 | yes | none | The tool 'git_add' is listed in the organization's register as reaching this asset, and its description matches the function of adding file contents to the staging area. |
| `git_reset` | 5 | yes | Q2: “Uncommitted and staged changes to the workspace's files, shown as diffs” | The organization's register lists this tool as reaching the asset. |

Not reached: `git_status`, `git_diff_unstaged`, `git_diff`, `git_log`, `git_create_branch`, `git_checkout`, `git_show`, `git_branch`

### `commit-list`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `git_log` | 4 | yes | Q2: “Exposure hands over private code or its pending changes; a move of a branch changes what is built or deployed (Commit contents and diffs of source and deploy files, uncommitted changes, where each branch points)” | The tool git_log is listed in the organization's register as reaching this asset, and it directly shows commit logs which include hashes, authors, dates, and messages. |

Not reached: `git_status`, `git_diff_unstaged`, `git_diff_staged`, `git_diff`, `git_commit`, `git_add`, `git_reset`, `git_create_branch`, `git_checkout`, `git_show`, `git_branch`

### `branch-directory`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `git_create_branch` | 2 | yes | none | The tool 'git_create_branch' is listed in the organization's register as reaching this asset, and it directly manipulates branch names which are part of the 'branch-directory'. |
| `git_checkout` | 2 | no | none | The tool 'git_checkout' can affect the branch directory by switching branches, which is a relevant operation according to the organization's register. |
| `git_branch` | 2 | yes | none | The tool 'git_branch' is listed in the organization's register as reaching this asset, and its parameters allow listing branches which are part of the branch directory. |

Not reached: `git_status`, `git_diff_unstaged`, `git_diff_staged`, `git_diff`, `git_commit`, `git_add`, `git_reset`, `git_log`, `git_show`

### `working-tree-status`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `git_status` | 2 | yes | none | The tool 'git_status' is listed in the organization's register as reaching this asset, and its description matches the asset's description. |
| `git_checkout` | 2 | no | none | The tool 'git_checkout' can affect the working tree status by switching branches, which changes what files are modified, staged or untracked. |

Not reached: `git_diff_unstaged`, `git_diff_staged`, `git_diff`, `git_commit`, `git_add`, `git_reset`, `git_log`, `git_create_branch`, `git_show`, `git_branch`
