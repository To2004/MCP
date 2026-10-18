# github — every tool input, explained

Run `run4`. One table per tool. **Declared** is what the tool's
own schema says — the only evidence the model had. **Class** is what the
model returned and why. **At run time** is what that classification asks
the dynamic layer to do with the value.

Classes: `RANGE` compares by magnitude · `POLICY` resolves which entity
was named against policy · `IGNORE` is not evaluated · `UNKNOWN` is
undecided.

**RANGE** 34 · **POLICY** 61 · **IGNORE** 40 · **UNKNOWN** 0 · 130 declared across 26 tool(s).

Prompt `4fae213c99a4` · job `20629011` · catalog `reports/live_run/github_real_toollist.json` (@modelcontextprotocol/server-github, captured 2026-07-06).

### `add_issue_comment`

4 argument(s), one model call, 12s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` | **POLICY** | The owner identifies which repository the comment is added to, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` | **POLICY** | The repo name specifies which repository the comment is added to, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `issue_number` | `number` | **RANGE** / count | The issue number is a count and has no inherent policy implications. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `body` | `string` | **IGNORE** | The body of the comment is free text that does not have an order or identity relevant to policy. | Not evaluated by this component. |

### `create_branch`

4 argument(s), one model call, 16s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository (and thus, which entity) the operation acts on. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies a particular repository within an owner's scope, thus it is policy-relevant. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `branch` | `string` — Name for the new branch | **IGNORE** | Branch names are free text and do not have inherent order or policy implications beyond the context of the repository itself. | Not evaluated by this component. |
| `from_branch` | `string` — Optional: source branch to create from (defaults to the repository's default branch) | **IGNORE** | The source branch is a reference point for creating a new branch, but it does not change which entity or resource the operation acts on beyond the context of the repository. | Not evaluated by this component. |

### `create_issue`

7 argument(s), one model call, 16s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` | **POLICY** | The owner identifies which GitHub user or organization the repository belongs to, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` | **POLICY** | The repo name specifies which specific repository within an owner's account the issue should be created in, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `title` | `string` | **IGNORE** | The title of the issue is free text that does not have a meaningful order or identity that a policy would speak to. | Not evaluated by this component. |
| `body` | `string` | **IGNORE** | The body of the issue is free text and its content does not affect which resource or context the call acts on, only how it is presented. | Not evaluated by this component. |
| `assignees` | `array` | **RANGE** / count | The number of assignees can be counted, and each assignee is a policy concern as it determines which user(s) the issue will be assigned to. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. Each item is **POLICY** — user, so the members are checked as well as the count. |
| `milestone` | `number` | **RANGE** / other | The milestone number does not have an inherent order or policy concern, but it is a numeric value that can be compared. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `labels[].items` | `array` | **POLICY** | Labels are identifiers for categorizing issues and each label represents a specific category or context, which is a policy concern. | Resolve “label” against the organisation's policy: may this caller act on the one it named? |

### `create_or_update_file`

7 argument(s), one model call, 188s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner argument refers to the entity (user or organization) that owns the repository, which is a policy concept. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo argument refers to the name of the repository, which is a policy concept as it identifies the specific resource. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `path` | `string` — Path where to create/update the file | **IGNORE** | The path argument specifies where in the repository the file should be created or updated. It does not have an inherent order and is not a policy concept. | Not evaluated by this component. |
| `content` | `string` — Content of the file | **IGNORE** | The content of the file is free text that a person reads, which is typically classified as IGNORE. | Not evaluated by this component. |
| `message` | `string` — Commit message | **IGNORE** | Commit messages are free text and do not have an inherent order or policy significance. | Not evaluated by this component. |
| `branch` | `string` — Branch to create/update the file in | **POLICY** | The branch argument refers to the specific branch in which changes are made, which is a policy concept as it identifies the context of the operation. | Resolve “repository_branch” against the organisation's policy: may this caller act on the one it named? |
| `sha` | `string` — SHA of the file being replaced (required when updating existing files) | **POLICY** | The sha argument refers to the specific version (SHA) of a file, which is a policy concept as it identifies the exact resource being updated. | Resolve “file_sha” against the organisation's policy: may this caller act on the one it named? |

### `create_pull_request`

8 argument(s), one model call, 17s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner argument refers to the entity (user or organization) that owns the repository, which is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo argument refers to the specific repository name, which is a policy concern as it identifies the resource being acted upon. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `title` | `string` — Pull request title | **IGNORE** | The title of the pull request is free text and does not have an inherent order or identity that would be subject to policy checks. | Not evaluated by this component. |
| `body` | `string` — Pull request body/description | **IGNORE** | The body/description of the pull request is free text and does not have an inherent order or identity that would be subject to policy checks. | Not evaluated by this component. |
| `head` | `string` — The name of the branch where your changes are implemented | **POLICY** | The head argument refers to the branch name where changes are implemented, which is a policy concern as it identifies the specific context of the operation. | Resolve “branch_name” against the organisation's policy: may this caller act on the one it named? |
| `base` | `string` — The name of the branch you want the changes pulled into | **POLICY** | The base argument refers to the branch name into which changes are pulled, which is a policy concern as it identifies the specific context of the operation. | Resolve “branch_name” against the organisation's policy: may this caller act on the one it named? |
| `draft` | `boolean` — Whether to create the pull request as a draft | **IGNORE** | Whether the pull request is created as a draft does not have an inherent order or identity that would be subject to policy checks; it's more about presentation and operational state. | Not evaluated by this component. |
| `maintainer_can_modify` | `boolean` — Whether maintainers can modify the pull request | **IGNORE** | Whether maintainers can modify the pull request is an operational switch rather than a value that would be subject to policy checks. | Not evaluated by this component. |

### `create_pull_request_review`

10 argument(s), one model call, 18s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The repository owner is a policy concept as it determines which repository the action is performed on. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repository name is a policy concept as it determines which repository the action is performed on. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / count | Pull request number is an identifier but can be considered a count in this context, as it represents the sequence of pull requests. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `commit_id` | `string` — The SHA of the commit that needs a review | **POLICY** | The commit SHA is an identifier that determines which specific commit in a repository needs to be reviewed, making it a policy concept. | Resolve “commit_sha” against the organisation's policy: may this caller act on the one it named? |
| `body` | `string` — The body text of the review | **IGNORE** | The body text of the review is free-form text and does not have an inherent order or identity that would make it a policy concept. | Not evaluated by this component. |
| `event` | `string` · enum=["APPROVE", "REQUEST_CHANGES", "COMMENT"] — The review action to perform | **POLICY** | The event determines the type of action to be performed on the pull request, which is a policy decision. | Resolve “review_action” against the organisation's policy: may this caller act on the one it named? |
| `comments[].path` | `array` — Comments to post as part of the review (specify either position or line, not both) | **POLICY** | The relative path to the file being commented on determines which specific file in the repository is acted upon, making it a policy concept. | Resolve “file_path” against the organisation's policy: may this caller act on the one it named? |
| `comments[].position` | `array` — Comments to post as part of the review (specify either position or line, not both) | **RANGE** / count | The position in the diff where you want to add a review comment is an identifier but can be considered a count as it represents a specific location. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `comments[].line` | `array` — Comments to post as part of the review (specify either position or line, not both) | **RANGE** / count | The line number in the file where you want to add a review comment is an identifier but can be considered a count as it represents a specific location. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `comments[].body` | `array` — Comments to post as part of the review (specify either position or line, not both) | **IGNORE** | The text of the review comment is free-form text and does not have an inherent order or identity that would make it a policy concept. | Not evaluated by this component. |

### `create_repository`

4 argument(s), one model call, 12s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `name` | `string` — Repository name | **POLICY** | The repository name is a unique identifier for the resource and must be evaluated against policy. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `description` | `string` — Repository description | **IGNORE** | The description is free text that does not affect the scope or identity of the resource. | Not evaluated by this component. |
| `private` | `boolean` — Whether the repository should be private | **IGNORE** | This boolean only changes how the repository is rendered (public vs private) and doesn't change which resource it acts on. | Not evaluated by this component. |
| `autoInit` | `boolean` — Initialize with README.md | **IGNORE** | The auto initialization with README.md does not affect the scope or identity of the repository, only its initial content. | Not evaluated by this component. |

### `fork_repository`

3 argument(s), one model call, 10s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner argument specifies which entity owns the repository, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo argument identifies the specific repository to be forked, which is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `organization` | `string` — Optional: organization to fork to (defaults to your personal account) | **POLICY** | The organization argument specifies where the repository should be forked to, and this is a policy concern. | Resolve “target_organization” against the organisation's policy: may this caller act on the one it named? |

### `get_file_contents`

4 argument(s), one model call, 21s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository is accessed, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies the exact repository to access, which is subject to policy. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `path` | `string` — Path to the file or directory | **POLICY** | The path determines which file or directory content is accessed within the repository, and this can be subject to policy. | Resolve “file_or_directory_path” against the organisation's policy: may this caller act on the one it named? |
| `branch` | `string` — Branch to get contents from | **POLICY** | The branch specifies which version of the file or directory content is accessed, and this can be subject to policy. | Resolve “repository_branch” against the organisation's policy: may this caller act on the one it named? |

### `get_issue`

3 argument(s), one model call, 12s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` | **POLICY** | The owner identifies which GitHub user or organization the repository belongs to, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` | **POLICY** | The repo name specifies which specific repository within an owner's account the operation targets, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `issue_number` | `number` | **RANGE** / count | The issue number is a count that identifies the specific issue within a repository. It has an order but does not inherently relate to policy. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `get_pull_request`

3 argument(s), one model call, 6s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner argument specifies which repository owner (username or organization) the call acts on, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo argument specifies which repository name the call acts on, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / count | The pull_number argument is a number that represents the pull request number, which has an order but does not specify a policy concern. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `get_pull_request_comments`

3 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner argument specifies which repository owner (username or organization) the call acts on, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo argument specifies which repository name the call acts on, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / other | The pull_number argument is a number that represents the pull request number, which has an order but does not fit into any specific subtype like count or duration. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `get_pull_request_files`

3 argument(s), one model call, 7s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository's pull request files are being accessed, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies the exact repository within an owner's account, which is also a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / other | The pull request number is a numerical identifier but does not inherently imply an order or magnitude relevant to the tool's operation. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `get_pull_request_reviews`

3 argument(s), one model call, 6s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner argument specifies which repository owner (username or organization) the call acts on, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo argument specifies which repository name the call acts on, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / other | The pull_number argument is a number that represents the pull request number, which has an order but does not fit into any specific subtype like count or duration. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `get_pull_request_status`

3 argument(s), one model call, 6s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository the call acts on, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies which specific repository within an owner's scope the call acts on, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / other | The pull request number has a meaningful order (higher numbers are later requests), but it does not represent a quantity, duration or other common RANGE subtypes. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `list_commits`

5 argument(s), one model call, 42s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` | **POLICY** | The owner identifies which GitHub user or organization the repository belongs to, and this is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` | **POLICY** | The repo name specifies which specific repository within an owner's account the operation targets, and this is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `sha` | `string` | **POLICY** | The SHA identifies which branch or specific commit to list commits for, and this is a policy concern. | Resolve “branch_or_commit_identifier” against the organisation's policy: may this caller act on the one it named? |
| `page` | `number` | **RANGE** / count | The page number is a count of which page of results to return, and it has a meaningful order. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `perPage` | `number` | **RANGE** / count | The perPage argument is a count of how many results to return per page, and it has a meaningful order. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `list_issues`

9 argument(s), one model call, 26s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` | **POLICY** | The value identifies the GitHub user or organization owning the repository. | Resolve “GitHub repository owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` | **POLICY** | The value identifies the specific repository within an owner's account. | Resolve “GitHub repository name” against the organisation's policy: may this caller act on the one it named? |
| `direction` | `string` · enum=["asc", "desc"] | **IGNORE** | This argument only changes how results are ordered, not which issues are retrieved. | Not evaluated by this component. |
| `labels[]` | `array` | **POLICY** | Labels identify specific categories or tags for issues, which can be policy-relevant. | Resolve “labels” against the organisation's policy: may this caller act on the one it named? Each item is **POLICY** — GitHub issue label, so the members are checked as well as the count. |
| `page` | `number` | **RANGE** / count | The page number is a count of the result set pages. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `per_page` | `number` | **RANGE** / count | The number of items per page is a count. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `since` | `string` | **RANGE** / temporal | The value represents a date or timestamp, which is used to filter issues. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `sort` | `string` · enum=["created", "updated", "comments"] | **IGNORE** | This argument only changes how results are ordered, not which issues are retrieved. | Not evaluated by this component. |
| `state` | `string` · enum=["open", "closed", "all"] | **POLICY** | The value identifies the state of the issues (open, closed), which can be policy-relevant. | Resolve “GitHub issue state” against the organisation's policy: may this caller act on the one it named? |

### `list_pull_requests`

9 argument(s), one model call, 16s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner argument specifies which repository owner (username or organization) the call acts on. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo argument specifies which repository name the call acts on. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `state` | `string` · enum=["open", "closed", "all"] — State of the pull requests to return | **IGNORE** | The state argument changes only how results are filtered, not which specific resource or context is acted upon. | Not evaluated by this component. |
| `head` | `string` — Filter by head user or head organization and branch name | **POLICY** | The head argument filters by a branch name or user, which can be considered as selecting a specific resource. | Resolve “branch_name_or_user” against the organisation's policy: may this caller act on the one it named? |
| `base` | `string` — Filter by base branch name | **POLICY** | The base argument filters by a base branch name, which is a specific resource or context. | Resolve “branch_name” against the organisation's policy: may this caller act on the one it named? |
| `sort` | `string` · enum=["created", "updated", "popularity", "long-running"] — What to sort results by | **IGNORE** | The sort argument changes only how results are sorted, not the resources acted upon. | Not evaluated by this component. |
| `direction` | `string` · enum=["asc", "desc"] — The direction of the sort | **IGNORE** | The direction argument changes only how results are ordered, not which specific resource or context is acted upon. | Not evaluated by this component. |
| `per_page` | `number` — Results per page (max 100) | **RANGE** / count | The per_page argument specifies the number of results per page, which is a count. | Band the value: **low** — · **medium** — · **high** —. Boundaries come from limits stated in the description. |
| `page` | `number` — Page number of the results | **RANGE** / count | The page argument specifies the page number of the results, which is a count. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |

### `merge_pull_request`

6 argument(s), one model call, 10s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository (and thus, which entity or organization) the pull request belongs to. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies a particular repository within an owner's account, which is relevant for policy decisions. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / other | The pull request number is a unique identifier but can be considered as part of an ordered sequence. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `commit_title` | `string` — Title for the automatic commit message | **IGNORE** | This argument specifies the title for the commit message, which does not affect policy or have any meaningful order. | Not evaluated by this component. |
| `commit_message` | `string` — Extra detail to append to automatic commit message | **IGNORE** | The extra detail to append to the automatic commit message is free text and does not influence policy decisions. | Not evaluated by this component. |
| `merge_method` | `string` · enum=["merge", "squash", "rebase"] — Merge method to use | **POLICY** | The merge method can have significant implications for the repository's history and thus is subject to organizational policy. | Resolve “merge_strategy” against the organisation's policy: may this caller act on the one it named? |

### `push_files`

7 argument(s), one model call, 20s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner argument refers to the entity (user or organization) that owns the repository, which is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo argument refers to the specific repository name, which is a policy concern as it determines which repository will be acted upon. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `branch` | `string` — Branch to push to (e.g., 'main' or 'master') | **POLICY** | The branch argument refers to the specific branch within a repository, which is a policy concern as it determines which branch will be acted upon. | Resolve “repository_branch” against the organisation's policy: may this caller act on the one it named? |
| `files` | `array` — Array of files to push | **RANGE** / count | The files argument is an array, and its length (number of files) can be compared. The content within each file does not have a meaningful order or policy significance. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. Each item is **IGNORE**, so the members are checked as well as the count. |
| `files[].path` | `array` — Array of files to push | **IGNORE** | The path argument inside the files array is a string representing the file's path, which is operational and does not have a meaningful order or policy significance. | Not evaluated by this component. |
| `files[].content` | `array` — Array of files to push | **IGNORE** | The content argument inside the files array is free text that represents the file's contents, which is operational and does not have a meaningful order or policy significance. | Not evaluated by this component. |
| `message` | `string` — Commit message | **IGNORE** | The message argument is a string representing the commit message, which is free text that does not have a meaningful order or policy significance. | Not evaluated by this component. |

### `search_code`

4 argument(s), one model call, 16s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `q` | `string` | **IGNORE** | The query string is free text and does not have a meaningful order or policy context. | Not evaluated by this component. |
| `order` | `string` · enum=["asc", "desc"] | **IGNORE** | The order argument changes only the presentation of results and does not have a meaningful order or policy context. | Not evaluated by this component. |
| `page` | `number` · minimum=1 | **RANGE** / count | The page argument represents a count and has a minimum value defined in the schema. | Band the value: **low** — · **medium** — · **high** —. Boundaries come from the schema's declared minimum/maximum. |
| `per_page` | `number` · minimum=1 · maximum=100 | **RANGE** / count | The per_page argument represents a count and has both minimum and maximum values defined in the schema. | Band the value: **low** — · **medium** — · **high** —. Boundaries come from the schema's declared minimum/maximum. |

### `search_issues`

5 argument(s), one model call, 21s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `q` | `string` | **IGNORE** | The query string is free text and does not have a meaningful order or policy context. | Not evaluated by this component. |
| `order` | `string` · enum=["asc", "desc"] | **IGNORE** | The order argument changes only the presentation of results and does not affect which resources are acted upon. | Not evaluated by this component. |
| `page` | `number` · minimum=1 | **RANGE** / count | The page argument represents a count of pages, which has a meaningful order. | Band the value: **low** — · **medium** — · **high** —. Boundaries come from the schema's declared minimum/maximum. |
| `per_page` | `number` · minimum=1 · maximum=100 | **RANGE** / count | The per_page argument represents a count of items per page, which has a meaningful order and defined bounds. | Band the value: **low** — · **medium** — · **high** —. Boundaries come from the schema's declared minimum/maximum. |
| `sort` | `string` · enum=["comments", "reactions", "reactions-+1", "reactions--1", "reactions-smile", "reactions-thinking_face", "reactions-heart", "reactions-tada", "interactions", "created", "updated"] | **IGNORE** | The sort argument changes only the presentation of results and does not affect which resources are acted upon. | Not evaluated by this component. |

### `search_repositories`

3 argument(s), one model call, 18s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `query` | `string` — Search query (see GitHub search syntax) | **IGNORE** | The query is free text that a person reads and interprets, not a value with an inherent order or policy context. | Not evaluated by this component. |
| `page` | `number` — Page number for pagination (default: 1) | **RANGE** / count | The page number is a count that has an inherent order, indicating the sequence of pages. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `perPage` | `number` — Number of results per page (default: 30, max: 100) | **RANGE** / count | The number of results per page is a count with an upper bound, indicating the size of each result set. | Band the value: **low** — · **medium** — · **high** —. Boundaries come from limits stated in the description. |

### `search_users`

5 argument(s), one model call, 18s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `q` | `string` | **IGNORE** | The query string is free text and does not have a meaningful order or policy context. | Not evaluated by this component. |
| `order` | `string` · enum=["asc", "desc"] | **IGNORE** | The order argument changes only the presentation of results and does not affect which resources are acted upon. | Not evaluated by this component. |
| `page` | `number` · minimum=1 | **RANGE** / count | The page argument represents a count of pages, which has a meaningful order. | Band the value: **low** — · **medium** — · **high** —. Boundaries come from the schema's declared minimum/maximum. |
| `per_page` | `number` · minimum=1 · maximum=100 | **RANGE** / count | The per_page argument represents a count of items per page, which has a meaningful order. | Band the value: **low** — · **medium** — · **high** —. Boundaries come from the schema's declared minimum/maximum. |
| `sort` | `string` · enum=["followers", "repositories", "joined"] | **IGNORE** | The sort argument changes only the presentation of results and does not affect which resources are acted upon. | Not evaluated by this component. |

### `update_issue`

9 argument(s), one model call, 21s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` | **POLICY** | The owner identifies the entity that owns the repository, which is a policy concern. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` | **POLICY** | The repo name specifies the specific repository to act on, which is a policy concern. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `issue_number` | `number` | **RANGE** / count | Issue numbers are sequential and have an order, but they do not represent a quantity or duration. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `title` | `string` | **IGNORE** | The title is free text that does not affect the policy context of the call. | Not evaluated by this component. |
| `body` | `string` | **IGNORE** | The body is free text and its content does not change the policy context or operational behavior. | Not evaluated by this component. |
| `assignees[]` | `array` | **RANGE** / count | The number of assignees is a count, and each assignee's identity is a policy concern. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. Each item is **POLICY** — user, so the members are checked as well as the count. |
| `milestone` | `number` | **RANGE** / count | Milestone numbers are sequential and have an order but do not represent a quantity or duration. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `labels[]` | `array` | **RANGE** / count | The number of labels is a count, and each label's identity can be a policy concern. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. Each item is **POLICY** — label, so the members are checked as well as the count. |
| `state` | `string` · enum=["open", "closed"] | **IGNORE** | State changes the presentation or status but does not change which resource or context the call acts on. | Not evaluated by this component. |

### `update_pull_request_branch`

4 argument(s), one model call, 8s.

| input | declared | class | why the model said so | at run time |
|---|---|---|---|---|
| `owner` | `string` — Repository owner (username or organization) | **POLICY** | The owner identifies which repository (and thus, which entity or organization) the operation acts on. | Resolve “repository_owner” against the organisation's policy: may this caller act on the one it named? |
| `repo` | `string` — Repository name | **POLICY** | The repo name specifies which specific repository within an owner's scope is being acted upon, making it a policy concept. | Resolve “repository_name” against the organisation's policy: may this caller act on the one it named? |
| `pull_number` | `number` — Pull request number | **RANGE** / other | The pull number is a numerical identifier but does not inherently imply an order or quantity beyond its use as an index. | Band the value: **low** — · **medium** — · **high** —. Boundaries were placed from ordinary practice, so traffic should correct them. |
| `expected_head_sha` | `string` — The expected SHA of the pull request's HEAD ref | **IGNORE** | This value is expected to be copied from the current state of the pull request and does not represent a policy concept or have inherent ordering. | Not evaluated by this component. |
