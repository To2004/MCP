# github — every tool input, explained

Run `run5`. One table per tool. **Declared** is what the tool's
own schema says — the only evidence the model had. **Class** is what the
model returned and why. **At run time** is what that classification asks
the dynamic layer to do with the value.

Classes: `RANGE` compares by magnitude · `POLICY` resolves which entity
was named against policy · `IGNORE` is not evaluated · `UNKNOWN` is
undecided.

**RANGE** 31 · **POLICY** 64 · **IGNORE** 41 · **UNKNOWN** 0 · 130 declared across 26 tool(s).

Prompt `b14d66ebf28b` · job `20673504` · catalog `reports/live_run/github_real_toollist.json` (@modelcontextprotocol/server-github, captured 2026-07-06).

### `add_issue_comment`

4 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` | **POLICY** | The owner identifies which repository the comment is added to, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` | **POLICY** | The repo name specifies the exact repository where the issue comment will be added, which is subject to policy. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `issue_number` | `number` | **POLICY** | The issue number identifies a specific issue within the repository and thus changes which resource the call acts on. | Resolve “issue_identifier” against the organisation's policy: may this caller act on the one it named? |
| `body` | `string` | **IGNORE** | The body of the comment is free text that does not have an inherent order or policy significance, it's content to be read by a person. | Not evaluated by this component. |

### `create_branch`

4 argument(s), one model call, 8s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository the operation acts on, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies which specific repository within an owner's account the operation acts on, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `branch` | `string` — Name for the new branch | **POLICY** | The branch name specifies which specific branch within a repository the operation acts on, and this is a policy concern. | Resolve “branch_name” against the organisation's policy: may this caller act on the one it named? |
| `from_branch` | `string` — Optional: source branch to create from (defaults to the repository's default branch) | **POLICY** | The from_branch specifies which specific branch to create the new branch from, and this is a policy concern. | Resolve “source_branch_name” against the organisation's policy: may this caller act on the one it named? |

### `create_issue`

7 argument(s), one model call, 14s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` | **POLICY** | The owner identifies which GitHub entity the issue is created under, and this is a policy concern. | Resolve “GitHub organization or user account” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` | **POLICY** | The repo argument specifies in which repository the issue will be created, affecting which resources and permissions are involved. | Resolve “GitHub repository” against the organisation's policy: may this caller act on the one it named? |
| `title` | `string` | **IGNORE** | The title is free text that does not have a meaningful order or policy implication beyond its content. | Not evaluated by this component. |
| `body` | `string` | **IGNORE** | The body of the issue is free text and does not carry any inherent ordering or policy implications beyond its content. | Not evaluated by this component. |
| `assignees[]` | `array` | **POLICY** | Assignees are identifiers of GitHub users, and the policy concerns who can be assigned to an issue. | Resolve “assignees” against the organisation's policy: may this caller act on the one it named? Each item is **POLICY** — GitHub user, so the members are checked as well as the count. |
| `milestone` | `number` | **RANGE** / other | The milestone number can be considered a range, but its meaning is not clearly defined by the schema or description. The ranges are based on typical usage. | Band the value: **low** <5 · **medium** 5-20 · **high** >20. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `labels[]` | `array` | **POLICY** | Labels are identifiers that can have policy implications, as they categorize the issue and may affect workflow or visibility. | Resolve “labels” against the organisation's policy: may this caller act on the one it named? Each item is **POLICY** — GitHub label, so the members are checked as well as the count. |

### `create_or_update_file`

7 argument(s), one model call, 54s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner argument identifies the repository owner, which is a policy concept. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo argument identifies the specific repository within an organization or user account, which is a policy concept. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `path` | `string` — Path where to create/update the file | **IGNORE** | The path argument specifies where to create/update the file but does not have inherent order or policy significance. | Not evaluated by this component. |
| `content` | `string` — Content of the file | **IGNORE** | The content of a file is free text and does not inherently carry an order or policy significance. | Not evaluated by this component. |
| `message` | `string` — Commit message | **IGNORE** | A commit message is free text that describes the changes made, but it doesn't have inherent order or policy significance. | Not evaluated by this component. |
| `branch` | `string` — Branch to create/update the file in | **POLICY** | The branch argument identifies which branch of the repository to operate on, which is a policy concept. | Resolve “repository_branch” against the organisation's policy: may this caller act on the one it named? |
| `sha` | `string` — SHA of the file being replaced (required when updating existing files) | **IGNORE** | SHA is used for identifying specific versions of files but does not have inherent order or policy significance in this context. | Not evaluated by this component. |

### `create_pull_request`

8 argument(s), one model call, 14s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner argument selects which repository owner the pull request is created for, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo argument selects which specific repository within the owner's account the pull request is created for, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `title` | `string` — Pull request title | **IGNORE** | The title of the pull request does not have an inherent order or identity that would be relevant to policy decisions; it's free text for human consumption. | Not evaluated by this component. |
| `body` | `string` — Pull request body/description | **IGNORE** | Similar to 'title', the body of the pull request is free text and does not have an inherent order or identity that would be relevant to policy decisions. | Not evaluated by this component. |
| `head` | `string` — The name of the branch where your changes are implemented | **POLICY** | The head argument specifies the branch where changes are implemented, which is a specific resource within the repository and thus relevant to policy. | Resolve “branch_name” against the organisation's policy: may this caller act on the one it named? |
| `base` | `string` — The name of the branch you want the changes pulled into | **POLICY** | The base argument specifies the branch into which changes are pulled, which is a specific resource within the repository and thus relevant to policy. | Resolve “branch_name” against the organisation's policy: may this caller act on the one it named? |
| `draft` | `boolean` — Whether to create the pull request as a draft | **IGNORE** | This boolean indicates whether the pull request should be created as a draft or not; it does not have an inherent order or identity that would be relevant to policy decisions. | Not evaluated by this component. |
| `maintainer_can_modify` | `boolean` — Whether maintainers can modify the pull request | **IGNORE** | This boolean indicates whether maintainers can modify the pull request, which is a setting rather than an order or identity that would be relevant to policy decisions. | Not evaluated by this component. |

### `create_pull_request_review`

11 argument(s), one model call, 22s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The repository owner is a policy concept as it identifies the entity owning the repository. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repository name is a policy concept as it identifies which specific repository the action applies to. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / count | The pull request number is a count and can be classified as RANGE. The boundaries are based on typical usage. | Band the value: **low** <5 · **medium** 5-20 · **high** >20. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `commit_id` | `string` — The SHA of the commit that needs a review | **POLICY** | The commit ID is a policy concept as it identifies the specific commit that needs review. | Resolve “commit_sha” against the organisation's policy: may this caller act on the one it named? |
| `body` | `string` — The body text of the review | **IGNORE** | The body text of the review is free text and does not have an inherent order or policy significance. | Not evaluated by this component. |
| `event` | `string` · enum=["APPROVE", "REQUEST_CHANGES", "COMMENT"] — The review action to perform | **POLICY** | The event determines which action to perform on the pull request, and this is a policy concept as it changes the nature of the operation. | Resolve “review_action” against the organisation's policy: may this caller act on the one it named? |
| `comments` | `array` — Comments to post as part of the review (specify either position or line, not both) | **RANGE** / count | The number of comments is a count and can be classified as RANGE. The boundaries are based on typical usage. | Band the value: **low** <2 · **medium** 2-5 · **high** >5. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `comments[].path` | `array` — Comments to post as part of the review (specify either position or line, not both) | **POLICY** | The path to the file being commented on is a policy concept as it identifies which specific file in the repository is affected. | Resolve “file_path” against the organisation's policy: may this caller act on the one it named? |
| `comments[].position` | `array` — Comments to post as part of the review (specify either position or line, not both) | **RANGE** / count | The position in the diff is a count and can be classified as RANGE. The boundaries are based on typical usage. | Band the value: **low** <5 · **medium** 5-20 · **high** >20. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `comments[].line` | `array` — Comments to post as part of the review (specify either position or line, not both) | **RANGE** / count | The line number in the file is a count and can be classified as RANGE. The boundaries are based on typical usage. | Band the value: **low** <5 · **medium** 5-20 · **high** >20. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `comments[].body` | `array` — Comments to post as part of the review (specify either position or line, not both) | **IGNORE** | The body text of each comment is free text and does not have an inherent order or policy significance. | Not evaluated by this component. |

### `create_repository`

4 argument(s), one model call, 6s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `name` | `string` — Repository name | **POLICY** | The repository name is a unique identifier for the resource. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `description` | `string` — Repository description | **IGNORE** | The description is free text and does not affect the policy or scale of the operation. | Not evaluated by this component. |
| `private` | `boolean` — Whether the repository should be private | **IGNORE** | This boolean only changes how the repository is accessed, not its identity or scale. | Not evaluated by this component. |
| `autoInit` | `boolean` — Initialize with README.md | **IGNORE** | The auto initialization with README.md does not affect the policy or scale of the operation. | Not evaluated by this component. |

### `fork_repository`

3 argument(s), one model call, 6s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner argument specifies which user or organization owns the repository, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo argument specifies the name of the repository to be forked, which is also a policy concern as it identifies the specific resource. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `organization` | `string` — Optional: organization to fork to (defaults to your personal account) | **POLICY** | The organization argument specifies where to fork the repository, which is a policy concern as it identifies the target organizational unit. | Resolve “target_organization” against the organisation's policy: may this caller act on the one it named? |

### `get_file_contents`

4 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository is accessed, and this can be controlled by policy. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies the exact repository to access, which is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `path` | `string` — Path to the file or directory | **POLICY** | The path determines which file or directory content is retrieved, and this can be controlled by policy. | Resolve “file_or_directory_path” against the organisation's policy: may this caller act on the one it named? |
| `branch` | `string` — Branch to get contents from | **POLICY** | Branch selection changes the context of which version of the file or directory is accessed, and this can be controlled by policy. | Resolve “repository_branch” against the organisation's policy: may this caller act on the one it named? |

### `get_issue`

3 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` | **POLICY** | The owner identifies which GitHub user or organization the repository belongs to, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` | **POLICY** | The repo name specifies which specific repository within an owner's account the operation acts on, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `issue_number` | `number` | **RANGE** / count | The issue number is a count that can be compared, but the specific ranges are based on typical usage patterns. | Band the value: **low** <50 · **medium** 50-200 · **high** >200. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `get_pull_request`

3 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository the pull request belongs to, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies which specific repository within an owner's account the pull request belongs to, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / count | The pull request number is a count that can be compared, but the specific ranges are based on typical usage patterns. | Band the value: **low** <50 · **medium** 50-200 · **high** >200. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `get_pull_request_comments`

3 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository's comments are retrieved, making it a policy concept. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies the exact repository to retrieve pull request comments from, which is subject-specific and thus a policy concept. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / count | The pull request number is a count that can be compared, but the specific numbers are not defined by policy or schema. | Band the value: **low** <50 · **medium** 50-200 · **high** >200. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `get_pull_request_files`

3 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository and its associated policies are being accessed. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies the exact repository, which is a policy concept as it determines the context of operation. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / count | The pull number is a count that can be compared, but the specific ranges are based on typical usage patterns. | Band the value: **low** <50 · **medium** 50-200 · **high** >200. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `get_pull_request_reviews`

3 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository the call acts on, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies which specific repository within an owner's scope the call acts on, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / count | The pull request number is a count, and while it doesn't have an inherent order in terms of importance, the scale can be divided into ranges based on typical usage. | Band the value: **low** <50 · **medium** 50-200 · **high** >200. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `get_pull_request_status`

3 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository the call acts on, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies which specific repository within an owner's scope the call acts on, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / count | The pull number is a count and can be compared to understand the scale of operations, but these boundaries are based on typical usage patterns. | Band the value: **low** <50 · **medium** 50-200 · **high** >200. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `list_commits`

5 argument(s), one model call, 10s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` | **POLICY** | The value identifies the GitHub user or organization owning the repository, which is a policy concern. | Resolve “GitHub repository owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` | **POLICY** | The value identifies the specific repository within an owner's account, which is a policy concern. | Resolve “Repository name” against the organisation's policy: may this caller act on the one it named? |
| `sha` | `string` | **IGNORE** | SHA (Secure Hash Algorithm) values are unique identifiers for commits and do not have a meaningful order or represent a quantity that changes the nature of the call. | Not evaluated by this component. |
| `page` | `number` | **RANGE** / count | The page number is a count of pages, and the ranges are based on typical pagination practices. | Band the value: **low** <5 · **medium** 5-20 · **high** >20. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `perPage` | `number` | **RANGE** / count | The number of items per page is a count, and the ranges are based on typical pagination practices. | Band the value: **low** <5 · **medium** 5-20 · **high** >20. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `list_issues`

9 argument(s), one model call, 18s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` | **POLICY** | The value identifies the GitHub user or organization owning the repository. | Resolve “GitHub repository owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` | **POLICY** | The value identifies the specific repository within an owner's account. | Resolve “GitHub repository name” against the organisation's policy: may this caller act on the one it named? |
| `direction` | `string` · enum=["asc", "desc"] | **IGNORE** | This argument only changes how results are ordered, not which issues are selected or acted upon. | Not evaluated by this component. |
| `labels[]` | `array` | **POLICY** | Labels are used to categorize issues, which can be a policy concern. | Resolve “GitHub issue labels” against the organisation's policy: may this caller act on the one it named? Each item is **POLICY** — GitHub issue label, so the members are checked as well as the count. |
| `page` | `number` | **RANGE** / count | The page number is a count of pages, and the ranges are based on typical pagination behavior. | Band the value: **low** <5 · **medium** 5-20 · **high** >20. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `per_page` | `number` | **RANGE** / count | The number of items per page is a count, and the ranges are based on typical pagination behavior. | Band the value: **low** <5 · **medium** 5-20 · **high** >20. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `since` | `string` | **RANGE** / temporal | The 'since' argument is a temporal value used to filter issues based on their creation or update time. | Band the value: **low** <24 hours ago · **medium** 24-72 hours ago · **high** >72 hours ago. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `sort` | `string` · enum=["created", "updated", "comments"] | **IGNORE** | This argument only changes how results are sorted, not which issues are selected or acted upon. | Not evaluated by this component. |
| `state` | `string` · enum=["open", "closed", "all"] | **POLICY** | The state of an issue (open/closed/all) can be a policy concern, as it affects which issues are visible or actionable. | Resolve “GitHub issue state” against the organisation's policy: may this caller act on the one it named? |

### `list_pull_requests`

9 argument(s), one model call, 17s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner argument selects which repository owner (username or organization) the call acts on. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo argument selects which specific repository name the call acts on. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `state` | `string` · enum=["open", "closed", "all"] — State of the pull requests to return | **IGNORE** | The state argument changes only how results are filtered, not which resource or context is acted upon. | Not evaluated by this component. |
| `head` | `string` — Filter by head user or head organization and branch name | **POLICY** | The head argument filters by a specific branch name or user, which changes the context of the call. | Resolve “branch_name_or_user” against the organisation's policy: may this caller act on the one it named? |
| `base` | `string` — Filter by base branch name | **POLICY** | The base argument filters by a specific base branch name, changing the context of the call. | Resolve “branch_name” against the organisation's policy: may this caller act on the one it named? |
| `sort` | `string` · enum=["created", "updated", "popularity", "long-running"] — What to sort results by | **IGNORE** | The sort argument changes only how results are sorted, not which resource or context is acted upon. | Not evaluated by this component. |
| `direction` | `string` · enum=["asc", "desc"] — The direction of the sort | **IGNORE** | The direction argument changes only the order of sorting, not which resource or context is acted upon. | Not evaluated by this component. |
| `per_page` | `number` — Results per page (max 100) | **RANGE** / count | The per_page argument is a count of results per page, with documented maximum. | Band the value: **low** < 25 · **medium** 25-75 · **high** > 75. Boundaries come from limits stated in the description. |
| `page` | `number` — Page number of the results | **RANGE** / count | The page argument is a count of the page number, with no documented maximum. | Band the value: **low** < 5 · **medium** 5-20 · **high** > 20. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `merge_pull_request`

6 argument(s), one model call, 10s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository the operation acts on. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies which repository the operation acts on. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / count | The pull request number is a count, but its value does not inherently imply risk or severity. | Band the value: **low** <5 · **medium** 5-20 · **high** >20. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `commit_title` | `string` — Title for the automatic commit message | **IGNORE** | Commit title is free text that changes the content of the commit message without affecting the operation's scope or impact. | Not evaluated by this component. |
| `commit_message` | `string` — Extra detail to append to automatic commit message | **IGNORE** | Extra detail for the commit message does not change the operation's scope or impact, only its documentation. | Not evaluated by this component. |
| `merge_method` | `string` · enum=["merge", "squash", "rebase"] — Merge method to use | **IGNORE** | The merge method changes how the pull request is merged but does not affect which resources are acted upon. | Not evaluated by this component. |

### `push_files`

7 argument(s), one model call, 13s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner argument selects which repository owner the operation acts on. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo argument selects which specific repository within an owner's account is acted upon. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `branch` | `string` — Branch to push to (e.g., 'main' or 'master') | **POLICY** | The branch argument specifies the exact branch to push files into, which can be sensitive based on policy. | Resolve “branch_name” against the organisation's policy: may this caller act on the one it named? |
| `files` | `array` — Array of files to push | **RANGE** / count | The files argument is an array, and its length can be considered a count. The content of each file does not have a meaningful order or policy relevance. | Band the value: **low** <5 · **medium** 5-20 · **high** >20. Boundaries were placed from ordinary practice, so traffic should correct them. Each item is **IGNORE**, so the members are checked as well as the count. |
| `files[].path` | `array` — Array of files to push | **IGNORE** | The path argument within the files array is an identifier for where to place the file, but it doesn't change which resource is acted upon in a policy-relevant way. | Not evaluated by this component. |
| `files[].content` | `array` — Array of files to push | **IGNORE** | The content argument within the files array holds the actual data of the file, but it's not relevant to dynamic analysis as it doesn't change which resource is acted upon. | Not evaluated by this component. |
| `message` | `string` — Commit message | **IGNORE** | The commit message does not affect the operation in a way that changes its policy relevance or has a meaningful order. | Not evaluated by this component. |

### `search_code`

4 argument(s), one model call, 14s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `q` | `string` | **IGNORE** | The query string is free text and does not have a meaningful order or policy context. | Not evaluated by this component. |
| `order` | `string` · enum=["asc", "desc"] | **IGNORE** | The order argument changes only the presentation of results and does not have a meaningful order or policy context. | Not evaluated by this component. |
| `page` | `number` · minimum=1 | **RANGE** / count | The page number is a count and has a meaningful order. The ranges are based on typical pagination behavior. | Band the value: **low** < 5 · **medium** 5-20 · **high** > 20. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `per_page` | `number` · minimum=1 · maximum=100 | **RANGE** / count | The per_page argument is a count and has a meaningful order. The ranges are based on the declared minimum and maximum values. | Band the value: **low** < 10 · **medium** 10-50 · **high** > 50. Boundaries come from the schema's declared minimum/maximum. |

### `search_issues`

5 argument(s), one model call, 16s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `q` | `string` | **IGNORE** | The query string is free text and does not have a meaningful order or policy context. | Not evaluated by this component. |
| `order` | `string` · enum=["asc", "desc"] | **IGNORE** | The order argument changes only the presentation of results and does not have a meaningful order or policy context. | Not evaluated by this component. |
| `page` | `number` · minimum=1 | **RANGE** / count | The page argument represents a count of pages, which has a meaningful order. | Band the value: **low** < 5 · **medium** 5-20 · **high** > 20. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `per_page` | `number` · minimum=1 · maximum=100 | **RANGE** / count | The per_page argument represents a count of items per page, which has a meaningful order and is bounded by the schema. | Band the value: **low** < 25 · **medium** 25-75 · **high** > 75. Boundaries come from the schema's declared minimum/maximum. |
| `sort` | `string` · enum=["comments", "reactions", "reactions-+1", "reactions--1", "reactions-smile", "reactions-thinking_face", "reactions-heart", "reactions-tada", "interactions", "created", "updated"] | **IGNORE** | The sort argument changes only the presentation of results and does not have a meaningful order or policy context. | Not evaluated by this component. |

### `search_repositories`

3 argument(s), one model call, 11s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `query` | `string` — Search query (see GitHub search syntax) | **IGNORE** | The query is free text and does not have a meaningful order or identity that a policy would speak to. | Not evaluated by this component. |
| `page` | `number` — Page number for pagination (default: 1) | **RANGE** / count | The page number is a count and has a meaningful order. | Band the value: **low** < 5 · **medium** 5-20 · **high** > 20. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `perPage` | `number` — Number of results per page (default: 30, max: 100) | **RANGE** / count | The number of results per page is a count and has a meaningful order, with the maximum defined in the schema. | Band the value: **low** < 30 · **medium** 30-75 · **high** > 75. Boundaries come from the schema's declared minimum/maximum. |

### `search_users`

5 argument(s), one model call, 16s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `q` | `string` | **IGNORE** | The query string is free text and does not have a meaningful order or policy context. | Not evaluated by this component. |
| `order` | `string` · enum=["asc", "desc"] | **IGNORE** | The order argument changes only the presentation of results and does not have a meaningful order or policy context. | Not evaluated by this component. |
| `page` | `number` · minimum=1 | **RANGE** / count | The page argument represents a count of pages, and the boundaries are based on typical pagination behavior. | Band the value: **low** < 5 · **medium** 5-20 · **high** > 20. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `per_page` | `number` · minimum=1 · maximum=100 | **RANGE** / count | The per_page argument represents a count of items per page, and the boundaries are based on the declared minimum and maximum. | Band the value: **low** < 25 · **medium** 25-75 · **high** > 75. Boundaries come from the schema's declared minimum/maximum. |
| `sort` | `string` · enum=["followers", "repositories", "joined"] | **IGNORE** | The sort argument changes only the presentation of results and does not have a meaningful order or policy context. | Not evaluated by this component. |

### `update_issue`

9 argument(s), one model call, 18s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` | **POLICY** | The owner identifies which GitHub user or organization the repository belongs to, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` | **POLICY** | The repo name specifies which specific repository within an owner's account the operation targets, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `issue_number` | `number` | **POLICY** | The issue number identifies which specific issue within a repository the operation targets, and this is a policy concern. | Resolve “issue_identifier” against the organisation's policy: may this caller act on the one it named? |
| `title` | `string` | **IGNORE** | The title of an issue does not have a meaningful order or identity that a policy would speak to; it's free text content. | Not evaluated by this component. |
| `body` | `string` | **IGNORE** | The body of an issue is free text and does not have a meaningful order or identity that a policy would speak to. | Not evaluated by this component. |
| `assignees` | `array` | **RANGE** / count | The number of assignees can be counted, and each assignee is a policy concern as it identifies specific users. | Band the value: **low** <2 · **medium** 2-5 · **high** >5. Boundaries were placed from ordinary practice, so traffic should correct them. Each item is **POLICY** — user_identifier, so the members are checked as well as the count. |
| `milestone` | `number` | **POLICY** | The milestone number or identifier specifies which milestone the issue is associated with, and this can be a policy concern. | Resolve “milestone_identifier” against the organisation's policy: may this caller act on the one it named? |
| `labels` | `array` | **RANGE** / count | The number of labels can be counted, and each label is a policy concern as it categorizes the issue. | Band the value: **low** <2 · **medium** 2-5 · **high** >5. Boundaries were placed from ordinary practice, so traffic should correct them. Each item is **POLICY** — label_identifier, so the members are checked as well as the count. |
| `state` | `string` · enum=["open", "closed"] | **IGNORE** | The state (open or closed) does not have an order that conveys more or less of something, and changing this value only changes the status of the issue. | Not evaluated by this component. |

### `update_pull_request_branch`

4 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository and its associated permissions are being acted upon. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies the exact repository to act on, which is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / count | The pull request number is a count, but its value does not inherently imply risk or policy concern. | Band the value: **low** <50 · **medium** 50-200 · **high** >200. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `expected_head_sha` | `string` — The expected SHA of the pull request's HEAD ref | **IGNORE** | SHA values are unique identifiers and do not have an inherent order or policy implication beyond identifying a specific commit. | Not evaluated by this component. |
