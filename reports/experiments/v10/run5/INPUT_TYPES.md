# Tool Arguments: how each value is evaluated at run time

Run `run5` — prompt in `prompt-AS-RUN.md` beside this file.
Qwen2.5:32b, greedy, seed 0.

`RANGE` values are compared by magnitude; `POLICY` values are resolved
against the organisation's policy; `IGNORE` values this component does not
evaluate; `UNKNOWN` means the definition did not say enough.

## github

Full explanation, tool by tool: [`github.md`](github.md)

| tool | argument | class | low / medium / high | policy concept / items | conf | why |
|---|---|---|---|---|---|---|
| `add_issue_comment` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository the comment is added to, and this is a policy concern. |
| `add_issue_comment` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies the exact repository where the issue comment will be added, which is subject to policy. |
| `add_issue_comment` | `issue_number` | **POLICY** | — | issue_identifier | 1.0 | The issue number identifies a specific issue within the repository and thus changes which resource the call acts on. |
| `add_issue_comment` | `body` | **IGNORE** | — | — | 1.0 | The body of the comment is free text that does not have an inherent order or policy significance, it's content to be read by a person. |
| `create_branch` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository the operation acts on, and this is a policy concern. |
| `create_branch` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies which specific repository within an owner's account the operation acts on, and this is a policy concern. |
| `create_branch` | `branch` | **POLICY** | — | branch_name | 1.0 | The branch name specifies which specific branch within a repository the operation acts on, and this is a policy concern. |
| `create_branch` | `from_branch` | **POLICY** | — | source_branch_name | 1.0 | The from_branch specifies which specific branch to create the new branch from, and this is a policy concern. |
| `create_issue` | `owner` | **POLICY** | — | GitHub organization or user account | 1.0 | The owner identifies which GitHub entity the issue is created under, and this is a policy concern. |
| `create_issue` | `repo` | **POLICY** | — | GitHub repository | 1.0 | The repo argument specifies in which repository the issue will be created, affecting which resources and permissions are involved. |
| `create_issue` | `title` | **IGNORE** | — | — | 1.0 | The title is free text that does not have a meaningful order or policy implication beyond its content. |
| `create_issue` | `body` | **IGNORE** | — | — | 1.0 | The body of the issue is free text and does not carry any inherent ordering or policy implications beyond its content. |
| `create_issue` | `assignees[]` | **POLICY** | — | items: POLICY | 1.0 | Assignees are identifiers of GitHub users, and the policy concerns who can be assigned to an issue. |
| `create_issue` | `milestone` | **RANGE** / other | L <5 · M 5-20 · H >20 (none) | — | 1.0 | The milestone number can be considered a range, but its meaning is not clearly defined by the schema or description. The ranges are based on typical usage. |
| `create_issue` | `labels[]` | **POLICY** | — | items: POLICY | 1.0 | Labels are identifiers that can have policy implications, as they categorize the issue and may affect workflow or visibility. |
| `create_or_update_file` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner argument identifies the repository owner, which is a policy concept. |
| `create_or_update_file` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo argument identifies the specific repository within an organization or user account, which is a policy concept. |
| `create_or_update_file` | `path` | **IGNORE** | — | — | 1.0 | The path argument specifies where to create/update the file but does not have inherent order or policy significance. |
| `create_or_update_file` | `content` | **IGNORE** | — | — | 1.0 | The content of a file is free text and does not inherently carry an order or policy significance. |
| `create_or_update_file` | `message` | **IGNORE** | — | — | 1.0 | A commit message is free text that describes the changes made, but it doesn't have inherent order or policy significance. |
| `create_or_update_file` | `branch` | **POLICY** | — | repository_branch | 1.0 | The branch argument identifies which branch of the repository to operate on, which is a policy concept. |
| `create_or_update_file` | `sha` | **IGNORE** | — | — | 1.0 | SHA is used for identifying specific versions of files but does not have inherent order or policy significance in this context. |
| `create_pull_request` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner argument selects which repository owner the pull request is created for, and this is a policy concern. |
| `create_pull_request` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo argument selects which specific repository within the owner's account the pull request is created for, and this is a policy concern. |
| `create_pull_request` | `title` | **IGNORE** | — | — | 1.0 | The title of the pull request does not have an inherent order or identity that would be relevant to policy decisions; it's free text for human consumption. |
| `create_pull_request` | `body` | **IGNORE** | — | — | 1.0 | Similar to 'title', the body of the pull request is free text and does not have an inherent order or identity that would be relevant to policy decisions. |
| `create_pull_request` | `head` | **POLICY** | — | branch_name | 1.0 | The head argument specifies the branch where changes are implemented, which is a specific resource within the repository and thus relevant to policy. |
| `create_pull_request` | `base` | **POLICY** | — | branch_name | 1.0 | The base argument specifies the branch into which changes are pulled, which is a specific resource within the repository and thus relevant to policy. |
| `create_pull_request` | `draft` | **IGNORE** | — | — | 1.0 | This boolean indicates whether the pull request should be created as a draft or not; it does not have an inherent order or identity that would be relevant to policy decisions. |
| `create_pull_request` | `maintainer_can_modify` | **IGNORE** | — | — | 1.0 | This boolean indicates whether maintainers can modify the pull request, which is a setting rather than an order or identity that would be relevant to policy decisions. |
| `create_pull_request_review` | `owner` | **POLICY** | — | repository_owner | 1.0 | The repository owner is a policy concept as it identifies the entity owning the repository. |
| `create_pull_request_review` | `repo` | **POLICY** | — | repository_name | 1.0 | The repository name is a policy concept as it identifies which specific repository the action applies to. |
| `create_pull_request_review` | `pull_number` | **RANGE** / count | L <5 · M 5-20 · H >20 (none) | — | 1.0 | The pull request number is a count and can be classified as RANGE. The boundaries are based on typical usage. |
| `create_pull_request_review` | `commit_id` | **POLICY** | — | commit_sha | 1.0 | The commit ID is a policy concept as it identifies the specific commit that needs review. |
| `create_pull_request_review` | `body` | **IGNORE** | — | — | 1.0 | The body text of the review is free text and does not have an inherent order or policy significance. |
| `create_pull_request_review` | `event` | **POLICY** | — | review_action | 1.0 | The event determines which action to perform on the pull request, and this is a policy concept as it changes the nature of the operation. |
| `create_pull_request_review` | `comments` | **RANGE** / count | L <2 · M 2-5 · H >5 (none) | — | 1.0 | The number of comments is a count and can be classified as RANGE. The boundaries are based on typical usage. |
| `create_pull_request_review` | `comments[].path` | **POLICY** | — | file_path | 1.0 | The path to the file being commented on is a policy concept as it identifies which specific file in the repository is affected. |
| `create_pull_request_review` | `comments[].position` | **RANGE** / count | L <5 · M 5-20 · H >20 (none) | — | 1.0 | The position in the diff is a count and can be classified as RANGE. The boundaries are based on typical usage. |
| `create_pull_request_review` | `comments[].line` | **RANGE** / count | L <5 · M 5-20 · H >20 (none) | — | 1.0 | The line number in the file is a count and can be classified as RANGE. The boundaries are based on typical usage. |
| `create_pull_request_review` | `comments[].body` | **IGNORE** | — | — | 1.0 | The body text of each comment is free text and does not have an inherent order or policy significance. |
| `create_repository` | `name` | **POLICY** | — | repository_name | 1.0 | The repository name is a unique identifier for the resource. |
| `create_repository` | `description` | **IGNORE** | — | — | 1.0 | The description is free text and does not affect the policy or scale of the operation. |
| `create_repository` | `private` | **IGNORE** | — | — | 1.0 | This boolean only changes how the repository is accessed, not its identity or scale. |
| `create_repository` | `autoInit` | **IGNORE** | — | — | 1.0 | The auto initialization with README.md does not affect the policy or scale of the operation. |
| `fork_repository` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner argument specifies which user or organization owns the repository, and this is a policy concern. |
| `fork_repository` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo argument specifies the name of the repository to be forked, which is also a policy concern as it identifies the specific resource. |
| `fork_repository` | `organization` | **POLICY** | — | target_organization | 1.0 | The organization argument specifies where to fork the repository, which is a policy concern as it identifies the target organizational unit. |
| `get_file_contents` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository is accessed, and this can be controlled by policy. |
| `get_file_contents` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies the exact repository to access, which is a policy concern. |
| `get_file_contents` | `path` | **POLICY** | — | file_or_directory_path | 1.0 | The path determines which file or directory content is retrieved, and this can be controlled by policy. |
| `get_file_contents` | `branch` | **POLICY** | — | repository_branch | 1.0 | Branch selection changes the context of which version of the file or directory is accessed, and this can be controlled by policy. |
| `get_issue` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which GitHub user or organization the repository belongs to, and this is a policy concern. |
| `get_issue` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies which specific repository within an owner's account the operation acts on, and this is a policy concern. |
| `get_issue` | `issue_number` | **RANGE** / count | L <50 · M 50-200 · H >200 (none) | — | 1.0 | The issue number is a count that can be compared, but the specific ranges are based on typical usage patterns. |
| `get_pull_request` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository the pull request belongs to, and this is a policy concern. |
| `get_pull_request` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies which specific repository within an owner's account the pull request belongs to, and this is a policy concern. |
| `get_pull_request` | `pull_number` | **RANGE** / count | L <50 · M 50-200 · H >200 (none) | — | 1.0 | The pull request number is a count that can be compared, but the specific ranges are based on typical usage patterns. |
| `get_pull_request_comments` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository's comments are retrieved, making it a policy concept. |
| `get_pull_request_comments` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies the exact repository to retrieve pull request comments from, which is subject-specific and thus a policy concept. |
| `get_pull_request_comments` | `pull_number` | **RANGE** / count | L <50 · M 50-200 · H >200 (none) | — | 1.0 | The pull request number is a count that can be compared, but the specific numbers are not defined by policy or schema. |
| `get_pull_request_files` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository and its associated policies are being accessed. |
| `get_pull_request_files` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies the exact repository, which is a policy concept as it determines the context of operation. |
| `get_pull_request_files` | `pull_number` | **RANGE** / count | L <50 · M 50-200 · H >200 (none) | — | 1.0 | The pull number is a count that can be compared, but the specific ranges are based on typical usage patterns. |
| `get_pull_request_reviews` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository the call acts on, and this is a policy concern. |
| `get_pull_request_reviews` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies which specific repository within an owner's scope the call acts on, and this is a policy concern. |
| `get_pull_request_reviews` | `pull_number` | **RANGE** / count | L <50 · M 50-200 · H >200 (none) | — | 1.0 | The pull request number is a count, and while it doesn't have an inherent order in terms of importance, the scale can be divided into ranges based on typical usage. |
| `get_pull_request_status` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository the call acts on, and this is a policy concern. |
| `get_pull_request_status` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies which specific repository within an owner's scope the call acts on, and this is a policy concern. |
| `get_pull_request_status` | `pull_number` | **RANGE** / count | L <50 · M 50-200 · H >200 (none) | — | 1.0 | The pull number is a count and can be compared to understand the scale of operations, but these boundaries are based on typical usage patterns. |
| `list_commits` | `owner` | **POLICY** | — | GitHub repository owner | 1.0 | The value identifies the GitHub user or organization owning the repository, which is a policy concern. |
| `list_commits` | `repo` | **POLICY** | — | Repository name | 1.0 | The value identifies the specific repository within an owner's account, which is a policy concern. |
| `list_commits` | `sha` | **IGNORE** | — | — | 1.0 | SHA (Secure Hash Algorithm) values are unique identifiers for commits and do not have a meaningful order or represent a quantity that changes the nature of the call. |
| `list_commits` | `page` | **RANGE** / count | L <5 · M 5-20 · H >20 (none) | — | 1.0 | The page number is a count of pages, and the ranges are based on typical pagination practices. |
| `list_commits` | `perPage` | **RANGE** / count | L <5 · M 5-20 · H >20 (none) | — | 1.0 | The number of items per page is a count, and the ranges are based on typical pagination practices. |
| `list_issues` | `owner` | **POLICY** | — | GitHub repository owner | 1.0 | The value identifies the GitHub user or organization owning the repository. |
| `list_issues` | `repo` | **POLICY** | — | GitHub repository name | 1.0 | The value identifies the specific repository within an owner's account. |
| `list_issues` | `direction` | **IGNORE** | — | — | 1.0 | This argument only changes how results are ordered, not which issues are selected or acted upon. |
| `list_issues` | `labels[]` | **POLICY** | — | GitHub issue labels | 1.0 | Labels are used to categorize issues, which can be a policy concern. |
| `list_issues` | `page` | **RANGE** / count | L <5 · M 5-20 · H >20 (none) | — | 1.0 | The page number is a count of pages, and the ranges are based on typical pagination behavior. |
| `list_issues` | `per_page` | **RANGE** / count | L <5 · M 5-20 · H >20 (none) | — | 1.0 | The number of items per page is a count, and the ranges are based on typical pagination behavior. |
| `list_issues` | `since` | **RANGE** / temporal | L <24 hours ago · M 24-72 hours ago · H >72 hours ago (none) | — | 1.0 | The 'since' argument is a temporal value used to filter issues based on their creation or update time. |
| `list_issues` | `sort` | **IGNORE** | — | — | 1.0 | This argument only changes how results are sorted, not which issues are selected or acted upon. |
| `list_issues` | `state` | **POLICY** | — | GitHub issue state | 1.0 | The state of an issue (open/closed/all) can be a policy concern, as it affects which issues are visible or actionable. |
| `list_pull_requests` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner argument selects which repository owner (username or organization) the call acts on. |
| `list_pull_requests` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo argument selects which specific repository name the call acts on. |
| `list_pull_requests` | `state` | **IGNORE** | — | — | 1.0 | The state argument changes only how results are filtered, not which resource or context is acted upon. |
| `list_pull_requests` | `head` | **POLICY** | — | branch_name_or_user | 1.0 | The head argument filters by a specific branch name or user, which changes the context of the call. |
| `list_pull_requests` | `base` | **POLICY** | — | branch_name | 1.0 | The base argument filters by a specific base branch name, changing the context of the call. |
| `list_pull_requests` | `sort` | **IGNORE** | — | — | 1.0 | The sort argument changes only how results are sorted, not which resource or context is acted upon. |
| `list_pull_requests` | `direction` | **IGNORE** | — | — | 1.0 | The direction argument changes only the order of sorting, not which resource or context is acted upon. |
| `list_pull_requests` | `per_page` | **RANGE** / count | L < 25 · M 25-75 · H > 75 (documented) | — | 1.0 | The per_page argument is a count of results per page, with documented maximum. |
| `list_pull_requests` | `page` | **RANGE** / count | L < 5 · M 5-20 · H > 20 (none) | — | 1.0 | The page argument is a count of the page number, with no documented maximum. |
| `merge_pull_request` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository the operation acts on. |
| `merge_pull_request` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies which repository the operation acts on. |
| `merge_pull_request` | `pull_number` | **RANGE** / count | L <5 · M 5-20 · H >20 (none) | — | 1.0 | The pull request number is a count, but its value does not inherently imply risk or severity. |
| `merge_pull_request` | `commit_title` | **IGNORE** | — | — | 1.0 | Commit title is free text that changes the content of the commit message without affecting the operation's scope or impact. |
| `merge_pull_request` | `commit_message` | **IGNORE** | — | — | 1.0 | Extra detail for the commit message does not change the operation's scope or impact, only its documentation. |
| `merge_pull_request` | `merge_method` | **IGNORE** | — | — | 1.0 | The merge method changes how the pull request is merged but does not affect which resources are acted upon. |
| `push_files` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner argument selects which repository owner the operation acts on. |
| `push_files` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo argument selects which specific repository within an owner's account is acted upon. |
| `push_files` | `branch` | **POLICY** | — | branch_name | 1.0 | The branch argument specifies the exact branch to push files into, which can be sensitive based on policy. |
| `push_files` | `files` | **RANGE** / count | L <5 · M 5-20 · H >20 (none) | items: IGNORE | 1.0 | The files argument is an array, and its length can be considered a count. The content of each file does not have a meaningful order or policy relevance. |
| `push_files` | `files[].path` | **IGNORE** | — | — | 1.0 | The path argument within the files array is an identifier for where to place the file, but it doesn't change which resource is acted upon in a policy-relevant way. |
| `push_files` | `files[].content` | **IGNORE** | — | — | 1.0 | The content argument within the files array holds the actual data of the file, but it's not relevant to dynamic analysis as it doesn't change which resource is acted upon. |
| `push_files` | `message` | **IGNORE** | — | — | 1.0 | The commit message does not affect the operation in a way that changes its policy relevance or has a meaningful order. |
| `search_code` | `q` | **IGNORE** | — | — | 1.0 | The query string is free text and does not have a meaningful order or policy context. |
| `search_code` | `order` | **IGNORE** | — | — | 1.0 | The order argument changes only the presentation of results and does not have a meaningful order or policy context. |
| `search_code` | `page` | **RANGE** / count | L < 5 · M 5-20 · H > 20 (none) | — | 0.9 | The page number is a count and has a meaningful order. The ranges are based on typical pagination behavior. |
| `search_code` | `per_page` | **RANGE** / count | L < 10 · M 10-50 · H > 50 (schema) | — | 1.0 | The per_page argument is a count and has a meaningful order. The ranges are based on the declared minimum and maximum values. |
| `search_issues` | `q` | **IGNORE** | — | — | 1.0 | The query string is free text and does not have a meaningful order or policy context. |
| `search_issues` | `order` | **IGNORE** | — | — | 1.0 | The order argument changes only the presentation of results and does not have a meaningful order or policy context. |
| `search_issues` | `page` | **RANGE** / count | L < 5 · M 5-20 · H > 20 (none) | — | 1.0 | The page argument represents a count of pages, which has a meaningful order. |
| `search_issues` | `per_page` | **RANGE** / count | L < 25 · M 25-75 · H > 75 (schema) | — | 1.0 | The per_page argument represents a count of items per page, which has a meaningful order and is bounded by the schema. |
| `search_issues` | `sort` | **IGNORE** | — | — | 1.0 | The sort argument changes only the presentation of results and does not have a meaningful order or policy context. |
| `search_repositories` | `query` | **IGNORE** | — | — | 1.0 | The query is free text and does not have a meaningful order or identity that a policy would speak to. |
| `search_repositories` | `page` | **RANGE** / count | L < 5 · M 5-20 · H > 20 (none) | — | 1.0 | The page number is a count and has a meaningful order. |
| `search_repositories` | `perPage` | **RANGE** / count | L < 30 · M 30-75 · H > 75 (schema) | — | 1.0 | The number of results per page is a count and has a meaningful order, with the maximum defined in the schema. |
| `search_users` | `q` | **IGNORE** | — | — | 1.0 | The query string is free text and does not have a meaningful order or policy context. |
| `search_users` | `order` | **IGNORE** | — | — | 1.0 | The order argument changes only the presentation of results and does not have a meaningful order or policy context. |
| `search_users` | `page` | **RANGE** / count | L < 5 · M 5-20 · H > 20 (none) | — | 0.9 | The page argument represents a count of pages, and the boundaries are based on typical pagination behavior. |
| `search_users` | `per_page` | **RANGE** / count | L < 25 · M 25-75 · H > 75 (schema) | — | 1.0 | The per_page argument represents a count of items per page, and the boundaries are based on the declared minimum and maximum. |
| `search_users` | `sort` | **IGNORE** | — | — | 1.0 | The sort argument changes only the presentation of results and does not have a meaningful order or policy context. |
| `update_issue` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which GitHub user or organization the repository belongs to, and this is a policy concern. |
| `update_issue` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies which specific repository within an owner's account the operation targets, and this is a policy concern. |
| `update_issue` | `issue_number` | **POLICY** | — | issue_identifier | 1.0 | The issue number identifies which specific issue within a repository the operation targets, and this is a policy concern. |
| `update_issue` | `title` | **IGNORE** | — | — | 1.0 | The title of an issue does not have a meaningful order or identity that a policy would speak to; it's free text content. |
| `update_issue` | `body` | **IGNORE** | — | — | 1.0 | The body of an issue is free text and does not have a meaningful order or identity that a policy would speak to. |
| `update_issue` | `assignees` | **RANGE** / count | L <2 · M 2-5 · H >5 (none) | items: POLICY | 1.0 | The number of assignees can be counted, and each assignee is a policy concern as it identifies specific users. |
| `update_issue` | `milestone` | **POLICY** | — | milestone_identifier | 1.0 | The milestone number or identifier specifies which milestone the issue is associated with, and this can be a policy concern. |
| `update_issue` | `labels` | **RANGE** / count | L <2 · M 2-5 · H >5 (none) | items: POLICY | 1.0 | The number of labels can be counted, and each label is a policy concern as it categorizes the issue. |
| `update_issue` | `state` | **IGNORE** | — | — | 1.0 | The state (open or closed) does not have an order that conveys more or less of something, and changing this value only changes the status of the issue. |
| `update_pull_request_branch` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository and its associated permissions are being acted upon. |
| `update_pull_request_branch` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies the exact repository to act on, which is a policy concern. |
| `update_pull_request_branch` | `pull_number` | **RANGE** / count | L <50 · M 50-200 · H >200 (none) | — | 1.0 | The pull request number is a count, but its value does not inherently imply risk or policy concern. |
| `update_pull_request_branch` | `expected_head_sha` | **IGNORE** | — | — | 1.0 | SHA values are unique identifiers and do not have an inherent order or policy implication beyond identifying a specific commit. |

**RANGE** 31 · **POLICY** 64 · **IGNORE** 41 · **UNKNOWN** 0 · 130 declared · 0 tool(s) declare none · failed: none.

## calendar

Full explanation, tool by tool: [`calendar.md`](calendar.md)

| tool | argument | class | low / medium / high | policy concept / items | conf | why |
|---|---|---|---|---|---|---|
| `create-event` | `account` | **POLICY** | — | calendar_account | 1.0 | The account nickname selects which calendar account the event is created in. |
| `create-event` | `calendarId` | **POLICY** | — | calendar_id | 1.0 | The ID of the calendar determines which specific calendar the event will be added to. |
| `create-event` | `eventId` | **IGNORE** | — | — | 1.0 | This is an optional custom identifier for the event, not a policy concept or meaningful order. |
| `create-event` | `summary` | **IGNORE** | — | — | 1.0 | The title of the event is free text and does not have a meaningful order or policy context. |
| `create-event` | `description` | **IGNORE** | — | — | 1.0 | Event description is free text and does not have a meaningful order or policy context. |
| `create-event` | `start` | **RANGE** / temporal | L < 24 hours from now · M 24-72 hours from now · H > 72 hours from now (none) | — | 1.0 | The start time of the event is a temporal value with meaningful order. |
| `create-event` | `end` | **RANGE** / temporal | L < 24 hours from now · M 24-72 hours from now · H > 72 hours from now (none) | — | 1.0 | The end time of the event is a temporal value with meaningful order. |
| `create-event` | `timeZone` | **POLICY** | — | timezone | 1.0 | Timezone selection affects which timezone the event times are interpreted in, impacting policy and compliance. |
| `create-event` | `location` | **IGNORE** | — | — | 1.0 | The location of the event is free text and does not have a meaningful order or policy context. |
| `create-event` | `attendees[]` | **RANGE** / count | L < 5 attendees · M 5-20 attendees · H > 20 attendees (none) | items: None | 1.0 | The number of attendees is a count with meaningful order. |
| `create-event` | `colorId` | **IGNORE** | — | — | 1.0 | Color ID for the event does not have a meaningful order or policy context. |
| `create-event` | `reminders.useDefault` | **IGNORE** | — | — | 1.0 | Boolean flag indicating whether to use default reminders, which is an operational switch. |
| `create-event` | `reminders.overrides[]` | **RANGE** / count | L < 2 overrides · M 2-5 overrides · H > 5 overrides (none) | items: None | 1.0 | The number of custom reminders is a count with meaningful order. |
| `create-event` | `recurrence[]` | **RANGE** / count | L < 2 rules · M 2-5 rules · H > 5 rules (none) | items: POLICY | 1.0 | The number of recurrence rules is a count with meaningful order. |
| `create-event` | `transparency` | **IGNORE** | — | — | 1.0 | Transparency setting does not have a meaningful order or policy context. |
| `create-event` | `visibility` | **POLICY** | — | event_visibility | 1.0 | Visibility determines who can see the event, which is a policy concept. |
| `create-event` | `guestsCanInviteOthers` | **IGNORE** | — | — | 1.0 | Boolean flag indicating whether guests can invite others, which is an operational switch. |
| `create-event` | `guestsCanModify` | **IGNORE** | — | — | 1.0 | Boolean flag indicating whether guests can modify the event, which is an operational switch. |
| `create-event` | `guestsCanSeeOtherGuests` | **IGNORE** | — | — | 1.0 | Boolean flag indicating whether guests can see other attendees, which is an operational switch. |
| `create-event` | `anyoneCanAddSelf` | **IGNORE** | — | — | 1.0 | Boolean flag indicating whether anyone can add themselves to the event, which is an operational switch. |
| `create-event` | `sendUpdates` | **POLICY** | — | event_notification_policy | 1.0 | Determines who receives notifications about the event creation, impacting policy and compliance. |
| `create-event` | `conferenceData.createRequest.requestId` | **IGNORE** | — | — | 1.0 | Client-generated unique ID for ensuring idempotency is not a policy concept or meaningful order. |
| `create-event` | `conferenceData.createRequest.conferenceSolutionKey.type` | **POLICY** | — | conference_solution_type | 1.0 | The type of conference solution selected is a policy concept. |
| `create-event` | `extendedProperties.private[]` | **RANGE** / count | L < 5 properties · M 5-20 properties · H > 20 properties (none) | items: IGNORE | 1.0 | The number of private extended properties is a count with meaningful order. |
| `create-event` | `extendedProperties.shared[]` | **RANGE** / count | L < 5 properties · M 5-20 properties · H > 20 properties (none) | items: IGNORE | 1.0 | The number of shared extended properties is a count with meaningful order. |
| `create-event` | `attachments[]` | **RANGE** / count | L < 2 attachments · M 2-5 attachments · H > 5 attachments (none) | items: None | 1.0 | The number of file attachments is a count with meaningful order. |
| `create-event` | `source.url` | **IGNORE** | — | — | 1.0 | URL of the source is free text and does not have a meaningful order or policy context. |
| `create-event` | `source.title` | **IGNORE** | — | — | 1.0 | Title of the source is free text and does not have a meaningful order or policy context. |
| `create-event` | `calendarsToCheck[]` | **RANGE** / count | L < 2 calendars · M 2-5 calendars · H > 5 calendars (none) | items: POLICY | 1.0 | The number of calendar IDs to check for conflicts is a count with meaningful order. |
| `create-event` | `duplicateSimilarityThreshold` | **RANGE** / percentage | L < 0.5 · M 0.5-0.7 · H > 0.7 (schema) | — | 1.0 | The threshold for duplicate detection is a percentage with meaningful order. |
| `create-event` | `allowDuplicates` | **IGNORE** | — | — | 1.0 | Boolean flag indicating whether to allow duplicates, which is an operational switch. |
| `create-event` | `eventType` | **POLICY** | — | event_type | 1.0 | The type of event determines the nature and compliance requirements for the event. |
| `create-event` | `focusTimeProperties.autoDeclineMode` | **IGNORE** | — | — | 1.0 | Auto-decline mode is an operational switch, not a policy concept or meaningful order. |
| `create-event` | `focusTimeProperties.chatStatus` | **IGNORE** | — | — | 1.0 | Chat status during focus time is an operational setting, not a policy concept or meaningful order. |
| `create-event` | `focusTimeProperties.declineMessage` | **IGNORE** | — | — | 1.0 | Decline message text is free text and does not have a meaningful order or policy context. |
| `create-event` | `outOfOfficeProperties.autoDeclineMode` | **IGNORE** | — | — | 1.0 | Auto-decline mode for out of office events is an operational switch, not a policy concept or meaningful order. |
| `create-event` | `outOfOfficeProperties.declineMessage` | **IGNORE** | — | — | 1.0 | Decline message text for out of office events is free text and does not have a meaningful order or policy context. |
| `create-event` | `workingLocationProperties.type` | **POLICY** | — | working_location_type | 1.0 | The type of working location is a policy concept, impacting compliance and access. |
| `create-event` | `workingLocationProperties.officeLocation.label` | **IGNORE** | — | — | 1.0 | Label for the office location is free text and does not have a meaningful order or policy context. |
| `create-event` | `workingLocationProperties.officeLocation.buildingId` | **POLICY** | — | building_id | 1.0 | Building identifier is a policy concept, impacting compliance and access. |
| `create-event` | `workingLocationProperties.officeLocation.floorId` | **POLICY** | — | floor_id | 1.0 | Floor identifier is a policy concept, impacting compliance and access. |
| `create-event` | `workingLocationProperties.officeLocation.floorSectionId` | **POLICY** | — | floor_section_id | 1.0 | Floor section identifier is a policy concept, impacting compliance and access. |
| `create-event` | `workingLocationProperties.officeLocation.deskId` | **POLICY** | — | desk_id | 1.0 | Desk identifier is a policy concept, impacting compliance and access. |
| `create-event` | `workingLocationProperties.customLocation.label` | **IGNORE** | — | — | 1.0 | Label for custom location is free text and does not have a meaningful order or policy context. |
| `create-events` | `account` | **POLICY** | — | user_account |  | Identifies the account for all events, which is a policy concern. |
| `create-events` | `calendarId` | **POLICY** | — | calendar_resource |  | Identifies the calendar resource where events are created, which is a policy concern. |
| `create-events` | `timeZone` | **IGNORE** | — | — |  | Specifies the timezone for all events but does not have an inherent order or identity that would be subject to policy. |
| `create-events` | `sendUpdates` | **IGNORE** | — | — |  | Determines notification settings, which affects presentation and behavior but is not a policy concern. |
| `create-events` | `events[].summary` | **IGNORE** | — | — |  | The title of the event is free text that does not have an inherent order or identity subject to policy. |
| `create-events` | `events[].start` | **RANGE** / temporal | L < 1 hour from now · M 1-24 hours from now · H > 24 hours from now (none) | — |  | The start time of the event is a temporal value that can be compared. |
| `create-events` | `events[].end` | **RANGE** / temporal | L < 1 hour from now · M 1-24 hours from now · H > 24 hours from now (none) | — |  | The end time of the event is a temporal value that can be compared. |
| `create-events` | `events[].calendarId` | **POLICY** | — | calendar_resource |  | Overrides the calendar resource for individual events, which is a policy concern. |
| `create-events` | `events[].account` | **POLICY** | — | user_account |  | Overrides the account for individual events, which is a policy concern. |
| `create-events` | `events[].timeZone` | **IGNORE** | — | — |  | Specifies the timezone for individual events but does not have an inherent order or identity that would be subject to policy. |
| `create-events` | `events[].description` | **IGNORE** | — | — |  | The description of the event is free text that does not have an inherent order or identity subject to policy. |
| `create-events` | `events[].location` | **POLICY** | — | event_location |  | Identifies the location where the event takes place, which can be a policy concern. |
| `create-events` | `events[].attendees[]` | **RANGE** / count | L < 5 attendees · M 5-10 attendees · H > 10 attendees (none) | — |  | The number of attendees can be compared. |
| `create-events` | `events[].attendees[].email` | **POLICY** | — | user_email |  | Identifies the email address of an attendee, which is a policy concern. |
| `create-events` | `events[].attendees[].displayName` | **IGNORE** | — | — |  | The display name of an attendee does not have an inherent order or identity that would be subject to policy. |
| `create-events` | `events[].attendees[].optional` | **IGNORE** | — | — |  | Determines if the attendee is optional, which affects behavior but is not a policy concern. |
| `create-events` | `events[].attendees[].responseStatus` | **IGNORE** | — | — |  | The response status of an attendee does not have an inherent order or identity that would be subject to policy. |
| `create-events` | `events[].colorId` | **IGNORE** | — | — |  | Color ID for the event is a presentation detail and does not have an inherent order or identity that would be subject to policy. |
| `create-events` | `events[].reminders.useDefault` | **IGNORE** | — | — |  | Determines if default reminders are used, which affects behavior but is not a policy concern. |
| `create-events` | `events[].reminders.overrides[]` | **RANGE** / count | L < 2 overrides · M 2-5 overrides · H > 5 overrides (none) | — |  | The number of custom reminders can be compared. |
| `create-events` | `events[].reminders.overrides[].method` | **IGNORE** | — | — |  | Determines the method for a reminder, which affects behavior but is not a policy concern. |
| `create-events` | `events[].reminders.overrides[].minutes` | **RANGE** / duration | L < 15 minutes before event · M 15-60 minutes before event · H > 60 minutes before event (none) | — |  | The duration before the event to trigger a reminder can be compared. |
| `create-events` | `events[].recurrence[]` | **RANGE** / count | L < 2 recurrence rules · M 2-5 recurrence rules · H > 5 recurrence rules (none) | — |  | The number of recurrence rules can be compared. |
| `create-events` | `events[].transparency` | **IGNORE** | — | — |  | Determines if the event blocks time, which affects behavior but is not a policy concern. |
| `create-events` | `events[].visibility` | **POLICY** | — | event_visibility |  | Identifies who can see the event, which is a policy concern. |
| `create-events` | `events[].guestsCanInviteOthers` | **IGNORE** | — | — |  | Determines if guests can invite others, which affects behavior but is not a policy concern. |
| `create-events` | `events[].guestsCanModify` | **IGNORE** | — | — |  | Determines if guests can modify the event, which affects behavior but is not a policy concern. |
| `create-events` | `events[].guestsCanSeeOtherGuests` | **IGNORE** | — | — |  | Determines if guests can see other attendees, which affects behavior but is not a policy concern. |
| `create-events` | `events[].anyoneCanAddSelf` | **IGNORE** | — | — |  | Determines if anyone can add themselves to the event, which affects behavior but is not a policy concern. |
| `create-events` | `events[].sendUpdates` | **IGNORE** | — | — |  | Overrides notification settings for individual events, which affects presentation and behavior but is not a policy concern. |
| `create-events` | `events[].conferenceData.createRequest.requestId` | **IGNORE** | — | — |  | A client-generated unique ID to ensure idempotency, which does not have an inherent order or identity that would be subject to policy. |
| `create-events` | `events[].conferenceData.createRequest.conferenceSolutionKey.type` | **POLICY** | — | conference_solution_type |  | Identifies the type of conference solution, which can be a policy concern. |
| `delete-event` | `account` | **POLICY** | — | Account nickname | 1.0 | The account nickname selects which account the operation acts on. |
| `delete-event` | `calendarId` | **POLICY** | — | Calendar ID | 1.0 | The calendar ID selects which calendar the operation acts on. |
| `delete-event` | `eventId` | **POLICY** | — | Event ID | 1.0 | The event ID selects which specific event to delete, and thus changes the subject of the call. |
| `delete-event` | `sendUpdates` | **IGNORE** | — | — | 1.0 | This argument only affects how notifications are sent out; it does not change the subject or resource acted upon. |
| `get-current-time` | `account` | **POLICY** | — | account_nickname | 1.0 | The account nickname selects which account the call acts on, and this is a policy decision. |
| `get-current-time` | `timeZone` | **POLICY** | — | timezone | 1.0 | The timezone value selects which time zone the call acts on, and this can be subject to policy constraints. |
| `get-event` | `account` | **POLICY** | — | Account nickname | 1.0 | The account nickname selects which account the call acts on. |
| `get-event` | `calendarId` | **POLICY** | — | Calendar ID | 1.0 | The calendar ID selects which calendar the call acts on. |
| `get-event` | `eventId` | **POLICY** | — | Event ID | 1.0 | The event ID selects which specific event the call retrieves. |
| `get-event` | `fields` | **RANGE** / count | L < 5 items · M 5-10 items · H > 10 items items (none) | items: IGNORE | 1.0 | The number of fields requested can be considered a count, and the ranges are based on typical usage. |
| `get-freebusy` | `account` | **POLICY** | — | Account nickname(s) | 1.0 | The account argument selects which accounts to query, and this is a policy decision. |
| `get-freebusy` | `calendars[].id` | **POLICY** | — | Calendar ID | 1.0 | The id of the calendar is an identifier that selects which calendars to query, and this is a policy decision. |
| `get-freebusy` | `timeMin` | **RANGE** / temporal | L < 24 hours ago · M 24-72 hours ago · H > 72 hours ago (none) | — | 1.0 | The timeMin argument represents a temporal value, and the scale changes meaning based on recentness. |
| `get-freebusy` | `timeMax` | **RANGE** / temporal | L < 24 hours from now · M 24-72 hours from now · H > 72 hours from now (none) | — | 1.0 | The timeMax argument represents a temporal value, and the scale changes meaning based on futureness. |
| `get-freebusy` | `timeZone` | **IGNORE** | — | — | 1.0 | The timeZone argument specifies the timezone for the query but does not have an inherent order or policy significance. |
| `get-freebusy` | `groupExpansionMax` | **RANGE** / count | L < 25 calendars · M 25-75 calendars · H > 75 calendars (schema) | — | 1.0 | The groupExpansionMax argument represents a count of calendars to expand, and the scale changes meaning based on the number. |
| `get-freebusy` | `calendarExpansionMax` | **RANGE** / count | L < 25 calendars · M 25-49 calendars · H > 49 calendars (schema) | — | 1.0 | The calendarExpansionMax argument represents a count of calendars to expand, and the scale changes meaning based on the number. |
| `list-calendars` | `account` | **POLICY** | — | account_nickname | 1.0 | The account nickname selects which accounts the call acts on, and this is a policy decision. |
| `list-calendars` | `account[]` | **POLICY** | — | account_nickname | 1.0 | Each item in the list of account nicknames selects which accounts the call acts on, and this is a policy decision. |
| `list-colors` | `account` | **POLICY** | — | account_nickname | 1.0 | The account nickname selects which account the call acts on, and this is a policy decision. |
| `list-events` | `account` | **POLICY** | — | Account nickname(s) | 1.0 | The account argument selects which accounts to query, changing the context of the call. |
| `list-events` | `calendarId` | **POLICY** | — | Calendar identifier(s) | 1.0 | The calendarId argument selects which calendars to query, changing the context of the call. |
| `list-events` | `timeMin` | **RANGE** / temporal | L < 24 hours ago · M 24-72 hours ago · H > 72 hours ago (none) | — | 1.0 | The timeMin argument defines the start of a temporal range, which has a meaningful order. |
| `list-events` | `timeMax` | **RANGE** / temporal | L < 24 hours from now · M 24-72 hours from now · H > 72 hours from now (none) | — | 1.0 | The timeMax argument defines the end of a temporal range, which has a meaningful order. |
| `list-events` | `timeZone` | **IGNORE** | — | — | 1.0 | The timeZone argument specifies how to interpret times but does not change the context or scale meaningfully. |
| `list-events` | `fields[]` | **IGNORE** | — | items: IGNORE | 1.0 | The fields argument specifies which event details to include, changing only the presentation of results. |
| `list-events` | `privateExtendedProperty[]` | **POLICY** | — | Private extended properties | 1.0 | The privateExtendedProperty argument filters events based on specific properties, changing the context of the call. |
| `list-events` | `sharedExtendedProperty[]` | **POLICY** | — | Shared extended properties | 1.0 | The sharedExtendedProperty argument filters events based on specific properties, changing the context of the call. |
| `manage-accounts` | `action` | **POLICY** | — | ActionType | 1.0 | The value selects which action the tool performs, changing the operation's context. |
| `manage-accounts` | `account_id` | **POLICY** | — | AccountNickname | 1.0 | The account nickname identifies a specific Google account for actions like 'add' and 'remove'. It is not a quantity or free text. |
| `respond-to-event` | `calendarId` | **POLICY** | — | calendar | 1.0 | The calendar ID selects which calendar the operation acts on. |
| `respond-to-event` | `eventId` | **POLICY** | — | event | 1.0 | The event ID selects which specific event to respond to. |
| `respond-to-event` | `account` | **POLICY** | — | account | 1.0 | The account nickname determines the context in which the operation is performed, potentially affecting permissions and visibility. |
| `respond-to-event` | `response` | **IGNORE** | — | — | 1.0 | This argument changes only how the event invitation is responded to; it does not change the subject or resource acted upon. |
| `respond-to-event` | `comment` | **IGNORE** | — | — | 1.0 | The comment is free text that accompanies a response and has no impact on policy decisions. |
| `respond-to-event` | `modificationScope` | **IGNORE** | — | — | 1.0 | This argument changes only the scope of the modification (single event or all events), not the subject/resource acted upon. |
| `respond-to-event` | `originalStartTime` | **RANGE** / temporal | L < 24 hours ago · M 24-72 hours ago · H > 72 hours ago (none) | — | 1.0 | The original start time is a temporal value that can be compared to understand the recency of an event. |
| `respond-to-event` | `sendUpdates` | **IGNORE** | — | — | 1.0 | This argument changes only how notifications are sent, not the subject/resource acted upon. |
| `search-events` | `account` | **POLICY** | — | Account nickname(s) | 1.0 | The account argument selects which accounts to query, changing the context of the call. |
| `search-events` | `calendarId` | **POLICY** | — | Calendar identifier(s) or names | 1.0 | The calendarId argument selects which calendars to search, changing the context of the call. |
| `search-events` | `query` | **IGNORE** | — | — | 1.0 | The query is free text and does not have a meaningful order or identity that a policy would speak to. |
| `search-events` | `timeMin` | **RANGE** / temporal | L < 24 hours ago · M 24-72 hours ago · H > 72 hours ago (none) | — | 1.0 | The timeMin argument represents a temporal range, and the meaning changes based on how far back in time it is set. |
| `search-events` | `timeMax` | **RANGE** / temporal | L < 24 hours from now · M 24-72 hours from now · H > 72 hours from now (none) | — | 1.0 | The timeMax argument represents a temporal range, and the meaning changes based on how far into the future it is set. |
| `search-events` | `timeZone` | **IGNORE** | — | — | 1.0 | The timeZone argument specifies an IANA timezone but does not have a meaningful order or identity that a policy would speak to. |
| `search-events` | `fields[]` | **RANGE** / count | L < 5 fields · M 5-10 fields · H > 10 fields (none) | items: POLICY | 1.0 | The number of additional fields requested can be considered a count, and the items themselves are policy concepts as they change which data is returned. |
| `search-events` | `privateExtendedProperty[]` | **RANGE** / count | L < 2 properties · M 2-5 properties · H > 5 properties (none) | items: POLICY | 1.0 | The number of private extended properties can be considered a count, and the items themselves are policy concepts as they change which events match. |
| `search-events` | `sharedExtendedProperty[]` | **RANGE** / count | L < 2 properties · M 2-5 properties · H > 5 properties (none) | items: POLICY | 1.0 | The number of shared extended properties can be considered a count, and the items themselves are policy concepts as they change which events match. |
| `update-event` | `account` | **POLICY** | — | Account nickname | 1.0 | The account nickname is used to identify a specific account, which is a policy concept. |
| `update-event` | `calendarId` | **POLICY** | — | Calendar ID | 1.0 | Identifies the calendar on which operations are performed; this is a policy concept. |
| `update-event` | `eventId` | **POLICY** | — | Event ID | 1.0 | The event ID identifies the specific event to be updated, which is a policy concept. |
| `update-event` | `summary` | **IGNORE** | — | — | 1.0 | This field contains free text that does not have an inherent order or identity relevant for policy decisions. |
| `update-event` | `description` | **IGNORE** | — | — | 1.0 | The description is free text and does not carry any meaningful order or policy-relevant identity. |
| `update-event` | `start` | **RANGE** / temporal | L < 24 hours ago · M 24-72 hours ago · H > 72 hours ago (none) | — | 1.0 | The start time is a temporal value that can be compared to determine the recency of an event. |
| `update-event` | `end` | **RANGE** / temporal | L < 24 hours ago · M 24-72 hours ago · H > 72 hours ago (none) | — | 1.0 | The end time is a temporal value that can be compared to determine the recency of an event. |
| `update-event` | `timeZone` | **POLICY** | — | Time Zone | 1.0 | Identifies the time zone for the calendar, which is a policy concept. |
| `update-event` | `location` | **IGNORE** | — | — | 1.0 | The location field contains free text and does not have an inherent order or identity relevant for policy decisions. |
| `update-event` | `attendees[]` | **RANGE** / count | L < 5 attendees · M 5-20 attendees · H > 20 attendees (none) | items: POLICY | 1.0 | The number of attendees can be compared to determine the scale of an event, and each attendee's email is a policy concept. |
| `update-event` | `colorId` | **IGNORE** | — | — | 1.0 | Color ID does not have inherent order or identity relevant for policy decisions; it only affects the appearance of an event. |
| `update-event` | `reminders.useDefault` | **IGNORE** | — | — | 1.0 | This is a boolean flag that changes how reminders are handled, not a value with inherent order or policy relevance. |
| `update-event` | `reminders.overrides[]` | **RANGE** / count | L < 2 overrides · M 2-5 overrides · H > 5 overrides (none) | items: IGNORE | 1.0 | The number of custom reminders can be compared to determine the complexity of an event's reminder setup. |
| `update-event` | `reminders.overrides[].minutes` | **RANGE** / duration | L < 30 minutes · M 30-60 minutes · H > 60 minutes (none) | — | 1.0 | The duration before the event to trigger a reminder is a meaningful temporal value. |
| `update-event` | `recurrence[]` | **RANGE** / count | L < 2 rules · M 2-5 rules · H > 5 rules (none) | items: IGNORE | 1.0 | The number of recurrence rules can be compared to determine the complexity of an event's scheduling. |
| `update-event` | `sendUpdates` | **POLICY** | — | Update Notification Scope | 1.0 | Determines which attendees receive update notifications, a policy concept. |
| `update-event` | `modificationScope` | **POLICY** | — | Modification Scope | 1.0 | Identifies the scope of recurring event modifications, which is a policy concept. |
| `update-event` | `originalStartTime` | **RANGE** / temporal | L < 24 hours ago · M 24-72 hours ago · H > 72 hours ago (none) | — | 1.0 | The original start time is a temporal value that can be compared to determine the recency of an event. |
| `update-event` | `futureStartDate` | **RANGE** / temporal | L < 24 hours ago · M 24-72 hours ago · H > 72 hours ago (none) | — | 1.0 | The future start date is a temporal value that can be compared to determine the recency of an event. |
| `update-event` | `checkConflicts` | **IGNORE** | — | — | 1.0 | This boolean flag changes how conflicts are handled, not a value with inherent order or policy relevance. |
| `update-event` | `calendarsToCheck[]` | **RANGE** / count | L < 2 calendars · M 2-5 calendars · H > 5 calendars (none) | items: POLICY | 1.0 | The number of calendars to check for conflicts can be compared, and each calendar's ID is a policy concept. |
| `update-event` | `conferenceData.createRequest.requestId` | **IGNORE** | — | — | 1.0 | This field contains an identifier that does not have inherent order or identity relevant for policy decisions. |
| `update-event` | `conferenceData.createRequest.conferenceSolutionKey.type` | **POLICY** | — | Conference Solution Type | 1.0 | Identifies the type of conference solution, which is a policy concept. |
| `update-event` | `transparency` | **POLICY** | — | Event Transparency | 1.0 | Determines whether an event blocks time on the calendar, which is a policy concept. |
| `update-event` | `visibility` | **POLICY** | — | Event Visibility | 1.0 | Identifies how visible the event is to others, which is a policy concept. |
| `update-event` | `guestsCanInviteOthers` | **IGNORE** | — | — | 1.0 | This boolean flag changes permissions for attendees, not a value with inherent order or policy relevance. |
| `update-event` | `guestsCanModify` | **IGNORE** | — | — | 1.0 | This boolean flag changes permissions for attendees, not a value with inherent order or policy relevance. |
| `update-event` | `guestsCanSeeOtherGuests` | **IGNORE** | — | — | 1.0 | This boolean flag changes permissions for attendees, not a value with inherent order or policy relevance. |
| `update-event` | `anyoneCanAddSelf` | **IGNORE** | — | — | 1.0 | This boolean flag changes permissions for event access, not a value with inherent order or policy relevance. |
| `update-event` | `extendedProperties.private` | **IGNORE** | — | — | 1.0 | Extended properties are application-specific data and do not have an inherent order or identity relevant for policy decisions. |
| `update-event` | `extendedProperties.shared` | **IGNORE** | — | — | 1.0 | Extended properties are application-specific data and do not have an inherent order or identity relevant for policy decisions. |
| `update-event` | `attachments[]` | **RANGE** / count | L < 2 attachments · M 2-5 attachments · H > 5 attachments (none) | items: IGNORE | 1.0 | The number of file attachments can be compared to determine the complexity of an event's attachment setup. |

**RANGE** 39 · **POLICY** 53 · **IGNORE** 63 · **UNKNOWN** 0 · 110 declared · 0 tool(s) declare none · failed: none.

## slack

Full explanation, tool by tool: [`slack.md`](slack.md)

| tool | argument | class | low / medium / high | policy concept / items | conf | why |
|---|---|---|---|---|---|---|
| `channels_list` | `channel_types` | **POLICY** | — | channel_type | 1.0 | The value selects which type of channels to list, changing the context of the call. |
| `channels_list` | `cursor` | **IGNORE** | — | — | 1.0 | Cursor is used for pagination and does not have a meaningful order or policy implication. |
| `channels_list` | `limit` | **RANGE** / count | L < 50 · M 50-200 · H > 200 (schema) | — | 1.0 | The limit defines the maximum number of items to return, which is a count. |
| `channels_list` | `query` | **IGNORE** | — | — | 1.0 | Query is free text used for filtering and does not have a meaningful order or policy implication. |
| `channels_list` | `query_targets` | **POLICY** | — | field_to_match | 1.0 | The value selects which fields to match the query against, changing the context of the call. |
| `channels_list` | `sort` | **IGNORE** | — | — | 1.0 | Sort changes only how results are presented and does not have a meaningful order or policy implication. |
| `channels_me` | `channel_types` | **POLICY** | — | channel_type | 1.0 | The value selects which type of channels to list, changing the context of the call. |
| `channels_me` | `cursor` | **IGNORE** | — | — | 1.0 | Cursor is used for pagination and does not have a meaningful order or policy implication. |
| `channels_me` | `limit` | **RANGE** / count | L <50 · M 50-200 · H >200 (schema) | — | 1.0 | The limit argument specifies the maximum number of items to return, which has a meaningful order. |
| `conversations_add_message` | `blocks` | **IGNORE** | — | — | 1.0 | The blocks argument is a string that holds JSON for rich message formatting. It does not have an inherent order or policy context. |
| `conversations_add_message` | `channel_id` | **POLICY** | — | channel_id | 1.0 | The channel_id is an identifier that determines which channel the message will be added to. It does not have a meaningful order but selects a specific resource. |
| `conversations_add_message` | `content_type` | **IGNORE** | — | — | 1.0 | The content_type is an enum that changes only the presentation of the message and does not affect which resource or context the call acts on. |
| `conversations_add_message` | `text` | **IGNORE** | — | — | 1.0 | The text argument is free-form message content. It does not have a meaningful order or policy context. |
| `conversations_add_message` | `thread_ts` | **POLICY** | — | thread_ts | 1.0 | The thread_ts is an identifier that determines which thread the message will be added to. It does not have a meaningful order but selects a specific context. |
| `conversations_history` | `channel_id` | **POLICY** | — | channel_or_user | 1.0 | The channel ID or name identifies a specific communication context, which is subject to policy. |
| `conversations_history` | `cursor` | **IGNORE** | — | — | 1.0 | Cursor values are used for pagination and do not have inherent meaning beyond their use in the API call. |
| `conversations_history` | `include_activity_messages` | **IGNORE** | — | — | 1.0 | This is a boolean flag that changes how results are returned, but does not affect which resources or subjects are acted upon. |
| `conversations_history` | `limit` | **RANGE** / duration | L < 1d · M 1d - 30d · H > 30d (documented) | — | 1.0 | The limit argument specifies a duration or number of messages to fetch, which has a meaningful order. |
| `conversations_join` | `channel_id` | **POLICY** | — | channel | 1.0 | The channel ID or name is used to identify which specific channel the user wants to join, and this selection must be evaluated against policy. |
| `conversations_leave` | `channel_id` | **POLICY** | — | channel_or_user | 1.0 | The channel_id identifies a specific channel or user, which is relevant to policy decisions. |
| `conversations_mark` | `channel_id` | **POLICY** | — | channel_or_user | 1.0 | The channel ID or name identifies a specific communication context, which is subject to policy. |
| `conversations_mark` | `ts` | **RANGE** / temporal | L < 3600 seconds ago · M 3600-86400 seconds ago · H > 86400 seconds ago (none) | — | 1.0 | The timestamp represents a point in time, and its value can be compared to determine how far back the read mark is set. |
| `conversations_replies` | `channel_id` | **POLICY** | — | channel |  | The channel ID or name identifies a specific communication channel, which is subject to policy. |
| `conversations_replies` | `cursor` | **IGNORE** | — | — |  | Cursor values are used for pagination and do not have inherent meaning beyond their use in fetching the next set of results. |
| `conversations_replies` | `include_activity_messages` | **IGNORE** | — | — |  | This is a boolean flag that changes how messages are included, but does not change the subject or resource acted upon. |
| `conversations_replies` | `limit` | **RANGE** / duration | L < 1d · M 1d - 30d · H > 30d (documented) | — |  | The limit argument specifies a duration or number of messages to fetch, which has a meaningful order. |
| `conversations_replies` | `thread_ts` | **POLICY** | — | message_thread |  | This timestamp identifies a specific thread or message within a conversation, which is subject to policy. |
| `conversations_search_messages` | `cursor` | **IGNORE** | — | — | 1.0 | The cursor is used for pagination and does not have a meaningful order or policy context. |
| `conversations_search_messages` | `filter_date_after` | **RANGE** / temporal | L < 7 days ago · M 7-30 days ago · H > 30 days ago (none) | — | 1.0 | The date after which messages are filtered has a meaningful order. |
| `conversations_search_messages` | `filter_date_before` | **RANGE** / temporal | L < 7 days ago · M 7-30 days ago · H > 30 days ago (none) | — | 1.0 | The date before which messages are filtered has a meaningful order. |
| `conversations_search_messages` | `filter_date_during` | **RANGE** / temporal | L < 7 days ago · M 7-30 days ago · H > 30 days ago (none) | — | 1.0 | The date during which messages are filtered has a meaningful order. |
| `conversations_search_messages` | `filter_date_on` | **RANGE** / temporal | L < 7 days ago · M 7-30 days ago · H > 30 days ago (none) | — | 1.0 | The date on which messages are filtered has a meaningful order. |
| `conversations_search_messages` | `filter_in_channel` | **POLICY** | — | channel | 1.0 | The channel ID or name is a policy concept as it identifies the specific channel. |
| `conversations_search_messages` | `filter_in_im_or_mpim` | **POLICY** | — | conversation | 1.0 | The DM or MPIM conversation ID or name is a policy concept as it identifies the specific conversation. |
| `conversations_search_messages` | `filter_threads_only` | **IGNORE** | — | — | 1.0 | This is a boolean flag that changes the presentation of results, not a policy concept or meaningful order. |
| `conversations_search_messages` | `filter_users_from` | **POLICY** | — | user | 1.0 | The user ID or display name is a policy concept as it identifies the specific user. |
| `conversations_search_messages` | `filter_users_with` | **POLICY** | — | user | 1.0 | The user ID or display name is a policy concept as it identifies the specific user. |
| `conversations_search_messages` | `limit` | **RANGE** / count | L < 20 items · M 20-50 items · H > 50 items (schema) | — | 1.0 | The limit has a meaningful order and is bounded by the schema. |
| `conversations_search_messages` | `search_query` | **IGNORE** | — | — | 1.0 | The search query is free text and does not have a meaningful order or policy context. |
| `conversations_unreads` | `channel_types` | **POLICY** | — | channel_type | 1.0 | The value selects which type of channel the call acts on. |
| `conversations_unreads` | `include_messages` | **IGNORE** | — | — | 1.0 | This argument only changes how the result is rendered, not the subject or context of the call. |
| `conversations_unreads` | `include_muted` | **IGNORE** | — | — | 1.0 | This argument only changes how the result is rendered, not the subject or context of the call. |
| `conversations_unreads` | `max_channels` | **RANGE** / count | L < 25 · M 25-75 · H > 75 channels (none) | — | 1.0 | The value represents a count of channels, and the meaning changes at different thresholds. |
| `conversations_unreads` | `max_messages_per_channel` | **RANGE** / count | L < 5 · M 5-20 · H > 20 messages (none) | — | 1.0 | The value represents a count of messages, and the meaning changes at different thresholds. |
| `conversations_unreads` | `mentions_only` | **IGNORE** | — | — | 1.0 | This argument only changes how the result is rendered, not the subject or context of the call. |
| `usergroups_create` | `channels` | **POLICY** | — | channel_ids | 1.0 | The value selects specific channels, which is a policy concern. |
| `usergroups_create` | `description` | **IGNORE** | — | — | 1.0 | This is free text that does not have an inherent order or policy significance. |
| `usergroups_create` | `handle` | **POLICY** | — | user_group_handle | 1.0 | The handle uniquely identifies the user group and is a policy concern. |
| `usergroups_create` | `name` | **IGNORE** | — | — | 1.0 | This is free text that does not have an inherent order or policy significance, though it's required for display purposes. |
| `usergroups_list` | `include_count` | **IGNORE** | — | — | 1.0 | This argument only changes the content of the response, not the subject or scale of the operation. |
| `usergroups_list` | `include_disabled` | **IGNORE** | — | — | 1.0 | This argument only changes the content of the response, not the subject or scale of the operation. |
| `usergroups_list` | `include_users` | **IGNORE** | — | — | 1.0 | This argument only changes the content of the response, not the subject or scale of the operation. |
| `usergroups_me` | `action` | **IGNORE** | — | — | 1.0 | The action argument changes only the operation performed and does not represent a quantity or identity that requires policy evaluation. |
| `usergroups_me` | `usergroup_id` | **POLICY** | — | usergroup_id | 1.0 | The usergroup_id is an identifier that determines which specific group the action applies to, and this requires policy evaluation. |
| `usergroups_update` | `channels` | **POLICY** | — | channel_ids | 1.0 | The value represents specific channel IDs, which are policy-relevant identifiers. |
| `usergroups_update` | `description` | **IGNORE** | — | — | 1.0 | This is free text that does not have a meaningful order or identity relevant to policy. |
| `usergroups_update` | `handle` | **POLICY** | — | mention_handle | 1.0 | The handle changes how the group is mentioned, which can be subject to organizational policies. |
| `usergroups_update` | `name` | **IGNORE** | — | — | 1.0 | This is free text that does not have a meaningful order or identity relevant to policy. |
| `usergroups_update` | `usergroup_id` | **POLICY** | — | user_group_ids | 1.0 | The user group ID is an identifier that determines which specific group the operation acts on, making it policy-relevant. |
| `usergroups_users_update` | `usergroup_id` | **POLICY** | — | user group | 1.0 | The usergroup_id is an identifier for a specific user group, which determines the scope of the operation. |
| `usergroups_users_update` | `users` | **RANGE** / count | L < 5 users · M 5-20 users · H > 20 users (none) | — | 1.0 | The 'users' argument represents a list of user IDs, and the number of users can be considered as a count. The ranges are based on typical group sizes. |
| `users_search` | `limit` | **RANGE** / count | L <10 · M 10-50 · H >50 (schema) | — | 1.0 | The limit argument is a numeric value that represents the maximum number of results to return, which has a meaningful order. |
| `users_search` | `query` | **IGNORE** | — | — | 1.0 | The query argument is a search string that does not have an inherent order or policy context. |

**RANGE** 14 · **POLICY** 23 · **IGNORE** 26 · **UNKNOWN** 0 · 63 declared · 0 tool(s) declare none · failed: none.

## All three servers

**RANGE** 84 · **POLICY** 140 · **IGNORE** 130 · **UNKNOWN** 0.
