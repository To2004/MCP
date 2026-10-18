# Tool Arguments: how each value is evaluated at run time

Run `run4` — prompt in `prompt-AS-RUN.md` beside this file.
Qwen2.5:32b, greedy, seed 0.

`RANGE` values are compared by magnitude; `POLICY` values are resolved
against the organisation's policy; `IGNORE` values this component does not
evaluate; `UNKNOWN` means the definition did not say enough.

## github

Full explanation, tool by tool: [`github.md`](github.md)

| tool | argument | class | low / medium / high | policy concept / items | conf | why |
|---|---|---|---|---|---|---|
| `add_issue_comment` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository the comment is added to, and this is a policy concern. |
| `add_issue_comment` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies which repository the comment is added to, and this is a policy concern. |
| `add_issue_comment` | `issue_number` | **RANGE** / count | — (none) | — | 1.0 | The issue number is a count and has no inherent policy implications. |
| `add_issue_comment` | `body` | **IGNORE** | — | — | 1.0 | The body of the comment is free text that does not have an order or identity relevant to policy. |
| `create_branch` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository (and thus, which entity) the operation acts on. |
| `create_branch` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies a particular repository within an owner's scope, thus it is policy-relevant. |
| `create_branch` | `branch` | **IGNORE** | — | — | 1.0 | Branch names are free text and do not have inherent order or policy implications beyond the context of the repository itself. |
| `create_branch` | `from_branch` | **IGNORE** | — | — | 1.0 | The source branch is a reference point for creating a new branch, but it does not change which entity or resource the operation acts on beyond the context of the repository. |
| `create_issue` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which GitHub user or organization the repository belongs to, and this is a policy concern. |
| `create_issue` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies which specific repository within an owner's account the issue should be created in, and this is a policy concern. |
| `create_issue` | `title` | **IGNORE** | — | — | 1.0 | The title of the issue is free text that does not have a meaningful order or identity that a policy would speak to. |
| `create_issue` | `body` | **IGNORE** | — | — | 1.0 | The body of the issue is free text and its content does not affect which resource or context the call acts on, only how it is presented. |
| `create_issue` | `assignees` | **RANGE** / count | — (unstated) | items: POLICY | 1.0 | The number of assignees can be counted, and each assignee is a policy concern as it determines which user(s) the issue will be assigned to. |
| `create_issue` | `milestone` | **RANGE** / other | — (unstated) | — | 1.0 | The milestone number does not have an inherent order or policy concern, but it is a numeric value that can be compared. |
| `create_issue` | `labels[].items` | **POLICY** | — | label | 1.0 | Labels are identifiers for categorizing issues and each label represents a specific category or context, which is a policy concern. |
| `create_or_update_file` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner argument refers to the entity (user or organization) that owns the repository, which is a policy concept. |
| `create_or_update_file` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo argument refers to the name of the repository, which is a policy concept as it identifies the specific resource. |
| `create_or_update_file` | `path` | **IGNORE** | — | — | 1.0 | The path argument specifies where in the repository the file should be created or updated. It does not have an inherent order and is not a policy concept. |
| `create_or_update_file` | `content` | **IGNORE** | — | — | 1.0 | The content of the file is free text that a person reads, which is typically classified as IGNORE. |
| `create_or_update_file` | `message` | **IGNORE** | — | — | 1.0 | Commit messages are free text and do not have an inherent order or policy significance. |
| `create_or_update_file` | `branch` | **POLICY** | — | repository_branch | 1.0 | The branch argument refers to the specific branch in which changes are made, which is a policy concept as it identifies the context of the operation. |
| `create_or_update_file` | `sha` | **POLICY** | — | file_sha | 1.0 | The sha argument refers to the specific version (SHA) of a file, which is a policy concept as it identifies the exact resource being updated. |
| `create_pull_request` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner argument refers to the entity (user or organization) that owns the repository, which is a policy concern. |
| `create_pull_request` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo argument refers to the specific repository name, which is a policy concern as it identifies the resource being acted upon. |
| `create_pull_request` | `title` | **IGNORE** | — | — | 1.0 | The title of the pull request is free text and does not have an inherent order or identity that would be subject to policy checks. |
| `create_pull_request` | `body` | **IGNORE** | — | — | 1.0 | The body/description of the pull request is free text and does not have an inherent order or identity that would be subject to policy checks. |
| `create_pull_request` | `head` | **POLICY** | — | branch_name | 1.0 | The head argument refers to the branch name where changes are implemented, which is a policy concern as it identifies the specific context of the operation. |
| `create_pull_request` | `base` | **POLICY** | — | branch_name | 1.0 | The base argument refers to the branch name into which changes are pulled, which is a policy concern as it identifies the specific context of the operation. |
| `create_pull_request` | `draft` | **IGNORE** | — | — | 1.0 | Whether the pull request is created as a draft does not have an inherent order or identity that would be subject to policy checks; it's more about presentation and operational state. |
| `create_pull_request` | `maintainer_can_modify` | **IGNORE** | — | — | 1.0 | Whether maintainers can modify the pull request is an operational switch rather than a value that would be subject to policy checks. |
| `create_pull_request_review` | `owner` | **POLICY** | — | repository_owner | 1.0 | The repository owner is a policy concept as it determines which repository the action is performed on. |
| `create_pull_request_review` | `repo` | **POLICY** | — | repository_name | 1.0 | The repository name is a policy concept as it determines which repository the action is performed on. |
| `create_pull_request_review` | `pull_number` | **RANGE** / count | — (unstated) | — | 1.0 | Pull request number is an identifier but can be considered a count in this context, as it represents the sequence of pull requests. |
| `create_pull_request_review` | `commit_id` | **POLICY** | — | commit_sha | 1.0 | The commit SHA is an identifier that determines which specific commit in a repository needs to be reviewed, making it a policy concept. |
| `create_pull_request_review` | `body` | **IGNORE** | — | — | 1.0 | The body text of the review is free-form text and does not have an inherent order or identity that would make it a policy concept. |
| `create_pull_request_review` | `event` | **POLICY** | — | review_action | 1.0 | The event determines the type of action to be performed on the pull request, which is a policy decision. |
| `create_pull_request_review` | `comments[].path` | **POLICY** | — | file_path | 1.0 | The relative path to the file being commented on determines which specific file in the repository is acted upon, making it a policy concept. |
| `create_pull_request_review` | `comments[].position` | **RANGE** / count | — (unstated) | — | 1.0 | The position in the diff where you want to add a review comment is an identifier but can be considered a count as it represents a specific location. |
| `create_pull_request_review` | `comments[].line` | **RANGE** / count | — (unstated) | — | 1.0 | The line number in the file where you want to add a review comment is an identifier but can be considered a count as it represents a specific location. |
| `create_pull_request_review` | `comments[].body` | **IGNORE** | — | — | 1.0 | The text of the review comment is free-form text and does not have an inherent order or identity that would make it a policy concept. |
| `create_repository` | `name` | **POLICY** | — | repository_name | 1.0 | The repository name is a unique identifier for the resource and must be evaluated against policy. |
| `create_repository` | `description` | **IGNORE** | — | — | 1.0 | The description is free text that does not affect the scope or identity of the resource. |
| `create_repository` | `private` | **IGNORE** | — | — | 1.0 | This boolean only changes how the repository is rendered (public vs private) and doesn't change which resource it acts on. |
| `create_repository` | `autoInit` | **IGNORE** | — | — | 1.0 | The auto initialization with README.md does not affect the scope or identity of the repository, only its initial content. |
| `fork_repository` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner argument specifies which entity owns the repository, and this is a policy concern. |
| `fork_repository` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo argument identifies the specific repository to be forked, which is a policy concern. |
| `fork_repository` | `organization` | **POLICY** | — | target_organization | 1.0 | The organization argument specifies where the repository should be forked to, and this is a policy concern. |
| `get_file_contents` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository is accessed, and this is a policy concern. |
| `get_file_contents` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies the exact repository to access, which is subject to policy. |
| `get_file_contents` | `path` | **POLICY** | — | file_or_directory_path | 1.0 | The path determines which file or directory content is accessed within the repository, and this can be subject to policy. |
| `get_file_contents` | `branch` | **POLICY** | — | repository_branch | 1.0 | The branch specifies which version of the file or directory content is accessed, and this can be subject to policy. |
| `get_issue` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which GitHub user or organization the repository belongs to, and this is a policy concern. |
| `get_issue` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies which specific repository within an owner's account the operation targets, and this is a policy concern. |
| `get_issue` | `issue_number` | **RANGE** / count | — (none) | — | 1.0 | The issue number is a count that identifies the specific issue within a repository. It has an order but does not inherently relate to policy. |
| `get_pull_request` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner argument specifies which repository owner (username or organization) the call acts on, and this is a policy concern. |
| `get_pull_request` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo argument specifies which repository name the call acts on, and this is a policy concern. |
| `get_pull_request` | `pull_number` | **RANGE** / count | — (none) | — | 1.0 | The pull_number argument is a number that represents the pull request number, which has an order but does not specify a policy concern. |
| `get_pull_request_comments` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner argument specifies which repository owner (username or organization) the call acts on, and this is a policy concern. |
| `get_pull_request_comments` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo argument specifies which repository name the call acts on, and this is a policy concern. |
| `get_pull_request_comments` | `pull_number` | **RANGE** / other | — (none) | — | 1.0 | The pull_number argument is a number that represents the pull request number, which has an order but does not fit into any specific subtype like count or duration. |
| `get_pull_request_files` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository's pull request files are being accessed, and this is a policy concern. |
| `get_pull_request_files` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies the exact repository within an owner's account, which is also a policy concern. |
| `get_pull_request_files` | `pull_number` | **RANGE** / other | — (none) | — | 1.0 | The pull request number is a numerical identifier but does not inherently imply an order or magnitude relevant to the tool's operation. |
| `get_pull_request_reviews` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner argument specifies which repository owner (username or organization) the call acts on, and this is a policy concern. |
| `get_pull_request_reviews` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo argument specifies which repository name the call acts on, and this is a policy concern. |
| `get_pull_request_reviews` | `pull_number` | **RANGE** / other | — (none) | — | 1.0 | The pull_number argument is a number that represents the pull request number, which has an order but does not fit into any specific subtype like count or duration. |
| `get_pull_request_status` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository the call acts on, and this is a policy concern. |
| `get_pull_request_status` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies which specific repository within an owner's scope the call acts on, and this is a policy concern. |
| `get_pull_request_status` | `pull_number` | **RANGE** / other | — (unstated) | — | 1.0 | The pull request number has a meaningful order (higher numbers are later requests), but it does not represent a quantity, duration or other common RANGE subtypes. |
| `list_commits` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which GitHub user or organization the repository belongs to, and this is a policy concern. |
| `list_commits` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies which specific repository within an owner's account the operation targets, and this is a policy concern. |
| `list_commits` | `sha` | **POLICY** | — | branch_or_commit_identifier | 1.0 | The SHA identifies which branch or specific commit to list commits for, and this is a policy concern. |
| `list_commits` | `page` | **RANGE** / count | — (none) | — | 1.0 | The page number is a count of which page of results to return, and it has a meaningful order. |
| `list_commits` | `perPage` | **RANGE** / count | — (none) | — | 1.0 | The perPage argument is a count of how many results to return per page, and it has a meaningful order. |
| `list_issues` | `owner` | **POLICY** | — | GitHub repository owner | 1.0 | The value identifies the GitHub user or organization owning the repository. |
| `list_issues` | `repo` | **POLICY** | — | GitHub repository name | 1.0 | The value identifies the specific repository within an owner's account. |
| `list_issues` | `direction` | **IGNORE** | — | — | 1.0 | This argument only changes how results are ordered, not which issues are retrieved. |
| `list_issues` | `labels[]` | **POLICY** | — | items: POLICY | 1.0 | Labels identify specific categories or tags for issues, which can be policy-relevant. |
| `list_issues` | `page` | **RANGE** / count | — (none) | — | 1.0 | The page number is a count of the result set pages. |
| `list_issues` | `per_page` | **RANGE** / count | — (none) | — | 1.0 | The number of items per page is a count. |
| `list_issues` | `since` | **RANGE** / temporal | — (none) | — | 1.0 | The value represents a date or timestamp, which is used to filter issues. |
| `list_issues` | `sort` | **IGNORE** | — | — | 1.0 | This argument only changes how results are ordered, not which issues are retrieved. |
| `list_issues` | `state` | **POLICY** | — | GitHub issue state | 1.0 | The value identifies the state of the issues (open, closed), which can be policy-relevant. |
| `list_pull_requests` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner argument specifies which repository owner (username or organization) the call acts on. |
| `list_pull_requests` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo argument specifies which repository name the call acts on. |
| `list_pull_requests` | `state` | **IGNORE** | — | — | 1.0 | The state argument changes only how results are filtered, not which specific resource or context is acted upon. |
| `list_pull_requests` | `head` | **POLICY** | — | branch_name_or_user | 1.0 | The head argument filters by a branch name or user, which can be considered as selecting a specific resource. |
| `list_pull_requests` | `base` | **POLICY** | — | branch_name | 1.0 | The base argument filters by a base branch name, which is a specific resource or context. |
| `list_pull_requests` | `sort` | **IGNORE** | — | — | 1.0 | The sort argument changes only how results are sorted, not the resources acted upon. |
| `list_pull_requests` | `direction` | **IGNORE** | — | — | 1.0 | The direction argument changes only how results are ordered, not which specific resource or context is acted upon. |
| `list_pull_requests` | `per_page` | **RANGE** / count | — (documented) | — | 1.0 | The per_page argument specifies the number of results per page, which is a count. |
| `list_pull_requests` | `page` | **RANGE** / count | — (none) | — | 1.0 | The page argument specifies the page number of the results, which is a count. |
| `merge_pull_request` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository (and thus, which entity or organization) the pull request belongs to. |
| `merge_pull_request` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies a particular repository within an owner's account, which is relevant for policy decisions. |
| `merge_pull_request` | `pull_number` | **RANGE** / other | — (none) | — | 1.0 | The pull request number is a unique identifier but can be considered as part of an ordered sequence. |
| `merge_pull_request` | `commit_title` | **IGNORE** | — | — | 1.0 | This argument specifies the title for the commit message, which does not affect policy or have any meaningful order. |
| `merge_pull_request` | `commit_message` | **IGNORE** | — | — | 1.0 | The extra detail to append to the automatic commit message is free text and does not influence policy decisions. |
| `merge_pull_request` | `merge_method` | **POLICY** | — | merge_strategy | 1.0 | The merge method can have significant implications for the repository's history and thus is subject to organizational policy. |
| `push_files` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner argument refers to the entity (user or organization) that owns the repository, which is a policy concern. |
| `push_files` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo argument refers to the specific repository name, which is a policy concern as it determines which repository will be acted upon. |
| `push_files` | `branch` | **POLICY** | — | repository_branch | 1.0 | The branch argument refers to the specific branch within a repository, which is a policy concern as it determines which branch will be acted upon. |
| `push_files` | `files` | **RANGE** / count | — (none) | items: IGNORE | 1.0 | The files argument is an array, and its length (number of files) can be compared. The content within each file does not have a meaningful order or policy significance. |
| `push_files` | `files[].path` | **IGNORE** | — | — | 1.0 | The path argument inside the files array is a string representing the file's path, which is operational and does not have a meaningful order or policy significance. |
| `push_files` | `files[].content` | **IGNORE** | — | — | 1.0 | The content argument inside the files array is free text that represents the file's contents, which is operational and does not have a meaningful order or policy significance. |
| `push_files` | `message` | **IGNORE** | — | — | 1.0 | The message argument is a string representing the commit message, which is free text that does not have a meaningful order or policy significance. |
| `search_code` | `q` | **IGNORE** | — | — | 1.0 | The query string is free text and does not have a meaningful order or policy context. |
| `search_code` | `order` | **IGNORE** | — | — | 1.0 | The order argument changes only the presentation of results and does not have a meaningful order or policy context. |
| `search_code` | `page` | **RANGE** / count | — (schema) | — | 1.0 | The page argument represents a count and has a minimum value defined in the schema. |
| `search_code` | `per_page` | **RANGE** / count | — (schema) | — | 1.0 | The per_page argument represents a count and has both minimum and maximum values defined in the schema. |
| `search_issues` | `q` | **IGNORE** | — | — | 1.0 | The query string is free text and does not have a meaningful order or policy context. |
| `search_issues` | `order` | **IGNORE** | — | — | 1.0 | The order argument changes only the presentation of results and does not affect which resources are acted upon. |
| `search_issues` | `page` | **RANGE** / count | — (schema) | — | 1.0 | The page argument represents a count of pages, which has a meaningful order. |
| `search_issues` | `per_page` | **RANGE** / count | — (schema) | — | 1.0 | The per_page argument represents a count of items per page, which has a meaningful order and defined bounds. |
| `search_issues` | `sort` | **IGNORE** | — | — | 1.0 | The sort argument changes only the presentation of results and does not affect which resources are acted upon. |
| `search_repositories` | `query` | **IGNORE** | — | — | 1.0 | The query is free text that a person reads and interprets, not a value with an inherent order or policy context. |
| `search_repositories` | `page` | **RANGE** / count | — (none) | — | 1.0 | The page number is a count that has an inherent order, indicating the sequence of pages. |
| `search_repositories` | `perPage` | **RANGE** / count | — (documented) | — | 1.0 | The number of results per page is a count with an upper bound, indicating the size of each result set. |
| `search_users` | `q` | **IGNORE** | — | — | 1.0 | The query string is free text and does not have a meaningful order or policy context. |
| `search_users` | `order` | **IGNORE** | — | — | 1.0 | The order argument changes only the presentation of results and does not affect which resources are acted upon. |
| `search_users` | `page` | **RANGE** / count | — (schema) | — | 1.0 | The page argument represents a count of pages, which has a meaningful order. |
| `search_users` | `per_page` | **RANGE** / count | — (schema) | — | 1.0 | The per_page argument represents a count of items per page, which has a meaningful order. |
| `search_users` | `sort` | **IGNORE** | — | — | 1.0 | The sort argument changes only the presentation of results and does not affect which resources are acted upon. |
| `update_issue` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies the entity that owns the repository, which is a policy concern. |
| `update_issue` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies the specific repository to act on, which is a policy concern. |
| `update_issue` | `issue_number` | **RANGE** / count | — (unstated) | — | 1.0 | Issue numbers are sequential and have an order, but they do not represent a quantity or duration. |
| `update_issue` | `title` | **IGNORE** | — | — | 1.0 | The title is free text that does not affect the policy context of the call. |
| `update_issue` | `body` | **IGNORE** | — | — | 1.0 | The body is free text and its content does not change the policy context or operational behavior. |
| `update_issue` | `assignees[]` | **RANGE** / count | — (unstated) | items: POLICY | 1.0 | The number of assignees is a count, and each assignee's identity is a policy concern. |
| `update_issue` | `milestone` | **RANGE** / count | — (unstated) | — | 1.0 | Milestone numbers are sequential and have an order but do not represent a quantity or duration. |
| `update_issue` | `labels[]` | **RANGE** / count | — (unstated) | items: POLICY | 1.0 | The number of labels is a count, and each label's identity can be a policy concern. |
| `update_issue` | `state` | **IGNORE** | — | — | 1.0 | State changes the presentation or status but does not change which resource or context the call acts on. |
| `update_pull_request_branch` | `owner` | **POLICY** | — | repository_owner | 1.0 | The owner identifies which repository (and thus, which entity or organization) the operation acts on. |
| `update_pull_request_branch` | `repo` | **POLICY** | — | repository_name | 1.0 | The repo name specifies which specific repository within an owner's scope is being acted upon, making it a policy concept. |
| `update_pull_request_branch` | `pull_number` | **RANGE** / other | — (none) | — | 1.0 | The pull number is a numerical identifier but does not inherently imply an order or quantity beyond its use as an index. |
| `update_pull_request_branch` | `expected_head_sha` | **IGNORE** | — | — | 1.0 | This value is expected to be copied from the current state of the pull request and does not represent a policy concept or have inherent ordering. |

**RANGE** 34 · **POLICY** 61 · **IGNORE** 40 · **UNKNOWN** 0 · 130 declared · 0 tool(s) declare none · failed: none.

## calendar

Full explanation, tool by tool: [`calendar.md`](calendar.md)

| tool | argument | class | low / medium / high | policy concept / items | conf | why |
|---|---|---|---|---|---|---|
| `create-event` | `account` | **POLICY** | — | Account nickname (e.g., 'work') | 1.0 | The account nickname is used to identify a specific account, which is a policy concept. |
| `create-event` | `calendarId` | **POLICY** | — | Calendar ID | 1.0 | Identifies the calendar on which the event will be created; this is a resource identifier and thus a policy concept. |
| `create-event` | `eventId` | **POLICY** | — | Event ID | 1.0 | Identifies an individual event, which is a policy concept. |
| `create-event` | `summary` | **IGNORE** | — | — | 1.0 | The title of the event is free text and does not have any inherent order or policy implications. |
| `create-event` | `description` | **IGNORE** | — | — | 1.0 | Event description is free text and does not have any inherent order or policy implications. |
| `create-event` | `start` | **RANGE** / temporal | — (unstated) | — | 1.0 | The start time of the event has a meaningful temporal order. |
| `create-event` | `end` | **RANGE** / temporal | — (unstated) | — | 1.0 | The end time of the event has a meaningful temporal order. |
| `create-event` | `timeZone` | **POLICY** | — | Timezone | 1.0 | Identifies the timezone for the event, which is a policy concept as it affects how the event is scheduled. |
| `create-event` | `location` | **IGNORE** | — | — | 1.0 | The location of the event is free text and does not have any inherent order or policy implications. |
| `create-event` | `attendees[]` | **RANGE** / count | — (unstated) | items: POLICY | 1.0 | The list of attendees has a count that is meaningful, and each attendee's email is an identifier. |
| `create-event` | `colorId` | **POLICY** | — | Color ID for the event | 1.0 | Identifies the color of the event which can be a policy concept if it is used to categorize events. |
| `create-event` | `reminders.useDefault` | **IGNORE** | — | — | 1.0 | This boolean indicates whether default reminders should be used, which does not have any inherent order or policy implications. |
| `create-event` | `reminders.overrides[]` | **RANGE** / count | — (unstated) | items: IGNORE | 1.0 | The list of custom reminders has a count that is meaningful, but the individual items are configuration options. |
| `create-event` | `recurrence[]` | **RANGE** / count | — (unstated) | items: POLICY | 1.0 | The list of recurrence rules has a count that is meaningful, and each rule specifies how the event recurs. |
| `create-event` | `transparency` | **POLICY** | — | Event transparency | 1.0 | Identifies whether the event blocks time on the calendar, which is a policy concept. |
| `create-event` | `visibility` | **POLICY** | — | Event visibility | 1.0 | Identifies who can see the event, which is a policy concept. |
| `create-event` | `guestsCanInviteOthers` | **IGNORE** | — | — | 1.0 | This boolean indicates whether guests can invite others to the event, which does not have any inherent order or policy implications. |
| `create-event` | `guestsCanModify` | **IGNORE** | — | — | 1.0 | This boolean indicates whether guests can modify the event, which does not have any inherent order or policy implications. |
| `create-event` | `guestsCanSeeOtherGuests` | **IGNORE** | — | — | 1.0 | This boolean indicates whether guests can see other attendees, which does not have any inherent order or policy implications. |
| `create-event` | `anyoneCanAddSelf` | **IGNORE** | — | — | 1.0 | This boolean indicates whether anyone can add themselves to the event, which does not have any inherent order or policy implications. |
| `create-event` | `sendUpdates` | **POLICY** | — | Notification settings for event creation | 1.0 | Identifies who should receive notifications about the event, which is a policy concept. |
| `create-event` | `conferenceData.createRequest.requestId` | **POLICY** | — | Client-generated unique ID for conference request | 1.0 | Identifies a specific conference creation request, which is a policy concept. |
| `create-event` | `conferenceData.createRequest.conferenceSolutionKey.type` | **POLICY** | — | Conference solution type | 1.0 | Identifies the type of conference to create, which is a policy concept. |
| `create-event` | `extendedProperties.private` | **IGNORE** | — | items: POLICY | 1.0 | Extended properties are application-specific and do not have inherent order or policy implications, but the keys could be considered identifiers. |
| `create-event` | `extendedProperties.shared` | **IGNORE** | — | items: POLICY | 1.0 | Extended properties are application-specific and do not have inherent order or policy implications, but the keys could be considered identifiers. |
| `create-event` | `attachments[]` | **RANGE** / count | — (unstated) | items: POLICY | 1.0 | The list of attachments has a count that is meaningful, and each attachment's URL is an identifier. |
| `create-event` | `source.url` | **IGNORE** | — | — | 1.0 | URL of the source is free text and does not have any inherent order or policy implications. |
| `create-event` | `source.title` | **IGNORE** | — | — | 1.0 | Title of the source is free text and does not have any inherent order or policy implications. |
| `create-event` | `calendarsToCheck[]` | **RANGE** / count | — (unstated) | items: POLICY | 1.0 | The list of calendar IDs has a count that is meaningful, and each ID identifies a specific calendar. |
| `create-event` | `duplicateSimilarityThreshold` | **RANGE** / percentage | — (schema) | — | 1.0 | The threshold for duplicate detection is a percentage value with meaningful bounds. |
| `create-event` | `allowDuplicates` | **IGNORE** | — | — | 1.0 | This boolean indicates whether duplicates are allowed, which does not have any inherent order or policy implications. |
| `create-event` | `eventType` | **POLICY** | — | Event type | 1.0 | Identifies the type of event, which is a policy concept as it affects how the event behaves. |
| `create-event` | `focusTimeProperties.autoDeclineMode` | **POLICY** | — | Auto-decline mode for focus time events | 1.0 | Identifies how to handle conflicting meetings during focus time, which is a policy concept. |
| `create-event` | `focusTimeProperties.chatStatus` | **POLICY** | — | Chat status during focus time | 1.0 | Identifies the chat status during focus time, which is a policy concept. |
| `create-event` | `focusTimeProperties.declineMessage` | **IGNORE** | — | — | 1.0 | The message sent when declining invitations is free text and does not have any inherent order or policy implications. |
| `create-event` | `outOfOfficeProperties.autoDeclineMode` | **POLICY** | — | Auto-decline mode for out of office events | 1.0 | Identifies how to handle conflicting meetings during out of office time, which is a policy concept. |
| `create-event` | `outOfOfficeProperties.declineMessage` | **IGNORE** | — | — | 1.0 | The message sent when declining invitations is free text and does not have any inherent order or policy implications. |
| `create-event` | `workingLocationProperties.type` | **POLICY** | — | Working location type | 1.0 | Identifies the type of working location, which is a policy concept as it affects how the event behaves. |
| `create-event` | `workingLocationProperties.officeLocation.label` | **POLICY** | — | Office name shown in Calendar | 1.0 | Identifies the office location, which is a policy concept as it affects how the event behaves. |
| `create-event` | `workingLocationProperties.officeLocation.buildingId` | **POLICY** | — | Building identifier from organization's Resources | 1.0 | Identifies a specific building, which is a policy concept. |
| `create-event` | `workingLocationProperties.officeLocation.floorId` | **POLICY** | — | Floor identifier | 1.0 | Identifies a specific floor within the building, which is a policy concept. |
| `create-event` | `workingLocationProperties.officeLocation.floorSectionId` | **POLICY** | — | Floor section identifier | 1.0 | Identifies a specific floor section within the building, which is a policy concept. |
| `create-event` | `workingLocationProperties.officeLocation.deskId` | **POLICY** | — | Desk identifier | 1.0 | Identifies a specific desk within the building, which is a policy concept. |
| `create-event` | `workingLocationProperties.customLocation.label` | **POLICY** | — | Label for custom location | 1.0 | Identifies a specific custom location, which is a policy concept as it affects how the event behaves. |
| `create-events` | `account` | **POLICY** | — | user_account | 1.0 | Identifies the account for all events, which is a policy concern. |
| `create-events` | `calendarId` | **POLICY** | — | calendar_resource | 1.0 | Identifies the calendar resource where events are created, which is a policy concern. |
| `create-events` | `timeZone` | **IGNORE** | — | — | 1.0 | Specifies the timezone for all events but does not have an inherent order or identity that would be subject to policy. |
| `create-events` | `sendUpdates` | **IGNORE** | — | — | 1.0 | Determines how notifications are sent, which is a presentation detail rather than a policy concern. |
| `create-events` | `events[].summary` | **IGNORE** | — | — | 1.0 | The title of the event is free text and does not have an inherent order or identity that would be subject to policy. |
| `create-events` | `events[].start` | **RANGE** / temporal | — (unstated) | — | 1.0 | The start time of the event is a temporal value with an inherent order. |
| `create-events` | `events[].end` | **RANGE** / temporal | — (unstated) | — | 1.0 | The end time of the event is a temporal value with an inherent order. |
| `create-events` | `events[].calendarId` | **POLICY** | — | calendar_resource | 1.0 | Identifies the calendar resource where this specific event is created, which is a policy concern. |
| `create-events` | `events[].account` | **POLICY** | — | user_account | 1.0 | Identifies the account for this specific event, which is a policy concern. |
| `create-events` | `events[].timeZone` | **IGNORE** | — | — | 1.0 | Specifies the timezone for this specific event but does not have an inherent order or identity that would be subject to policy. |
| `create-events` | `events[].description` | **IGNORE** | — | — | 1.0 | The description of the event is free text and does not have an inherent order or identity that would be subject to policy. |
| `create-events` | `events[].location` | **POLICY** | — | event_location | 1.0 | Identifies the location of the event, which could be a policy concern depending on the organization's policies. |
| `create-events` | `events[].attendees[]` | **RANGE** / count | — (unstated) | items: POLICY | 1.0 | The list of attendees has a count that is meaningful, and each attendee's email is an identifier with policy implications. |
| `create-events` | `events[].colorId` | **IGNORE** | — | — | 1.0 | Color ID for the event is a presentation detail rather than a policy concern. |
| `create-events` | `events[].reminders.useDefault` | **IGNORE** | — | — | 1.0 | Determines whether to use default reminders, which is a preference setting and not a policy concern. |
| `create-events` | `events[].reminders.overrides[]` | **RANGE** / count | — (unstated) | items: IGNORE | 1.0 | The list of custom reminders has a count that is meaningful, but the individual reminder settings are not policy concerns. |
| `create-events` | `events[].recurrence[]` | **RANGE** / count | — (unstated) | items: IGNORE | 1.0 | The list of recurrence rules has a count that is meaningful, but the individual recurrence rules are not policy concerns. |
| `create-events` | `events[].transparency` | **POLICY** | — | event_transparency | 1.0 | Determines whether the event blocks time, which could be a policy concern depending on the organization's policies. |
| `create-events` | `events[].visibility` | **POLICY** | — | event_visibility | 1.0 | Determines the visibility of the event, which could be a policy concern depending on the organization's policies. |
| `create-events` | `events[].guestsCanInviteOthers` | **POLICY** | — | event_guest_permission | 1.0 | Determines whether attendees can invite others, which could be a policy concern depending on the organization's policies. |
| `create-events` | `events[].guestsCanModify` | **POLICY** | — | event_guest_permission | 1.0 | Determines whether attendees can modify the event, which could be a policy concern depending on the organization's policies. |
| `create-events` | `events[].guestsCanSeeOtherGuests` | **POLICY** | — | event_guest_permission | 1.0 | Determines whether attendees can see other attendees, which could be a policy concern depending on the organization's policies. |
| `create-events` | `events[].anyoneCanAddSelf` | **POLICY** | — | event_guest_permission | 1.0 | Determines whether anyone can add themselves, which could be a policy concern depending on the organization's policies. |
| `create-events` | `events[].sendUpdates` | **IGNORE** | — | — | 1.0 | Overrides the notification setting for this event, which is a preference setting and not a policy concern. |
| `create-events` | `events[].conferenceData.createRequest.requestId` | **IGNORE** | — | — | 1.0 | Client-generated unique ID for ensuring idempotency, which does not have an inherent order or identity that would be subject to policy. |
| `create-events` | `events[].conferenceData.createRequest.conferenceSolutionKey.type` | **IGNORE** | — | — | 1.0 | Conference solution type is a preference setting and not a policy concern. |
| `delete-event` | `account` | **POLICY** | — | Account nickname | 1.0 | The account nickname is used to identify a specific account, which is a policy concept. |
| `delete-event` | `calendarId` | **POLICY** | — | Calendar ID | 1.0 | The calendar ID identifies the specific calendar on which the operation acts, making it a policy concept. |
| `delete-event` | `eventId` | **POLICY** | — | Event ID | 1.0 | The event ID is used to identify the specific event to delete, which is a policy concept. |
| `delete-event` | `sendUpdates` | **IGNORE** | — | — | 1.0 | This argument only changes how notifications are sent and does not affect the core action of deleting an event. |
| `get-current-time` | `account` | **POLICY** | — | account_nickname | 1.0 | The account nickname is an identifier that selects which account the call acts on. |
| `get-current-time` | `timeZone` | **POLICY** | — | timezone | 1.0 | IANA timezone is a policy concept as it determines the context in which time is interpreted, and this can be subject to organizational policies. |
| `get-event` | `account` | **POLICY** | — | Account nickname | 1.0 | The account nickname is used to identify a specific account, which is a policy concept. |
| `get-event` | `calendarId` | **POLICY** | — | Calendar ID | 1.0 | The calendar ID identifies the specific calendar on which operations are performed, making it a policy concept. |
| `get-event` | `eventId` | **POLICY** | — | Event ID | 1.0 | The event ID is used to identify the specific event being retrieved, which is a policy concept. |
| `get-event` | `fields` | **RANGE** / count | — (none) | items: IGNORE | 1.0 | The length of the array can be compared, and its items are options that do not affect which resource is acted upon. |
| `get-freebusy` | `account` | **POLICY** | — | account_nickname | 1.0 | Account nickname(s) are identifiers that select which account to query. |
| `get-freebusy` | `calendars[].id` | **POLICY** | — | calendar_id | 1.0 | The ID of the calendar is an identifier that selects which calendar to query. |
| `get-freebusy` | `timeMin` | **RANGE** / temporal | — (none) | — | 1.0 | The start of the time range is a temporal value that has a meaningful order. |
| `get-freebusy` | `timeMax` | **RANGE** / temporal | — (none) | — | 1.0 | The end of the time range is a temporal value that has a meaningful order. |
| `get-freebusy` | `timeZone` | **IGNORE** | — | — | 1.0 | The timezone is a setting that changes how the result is interpreted, not which resource or context. |
| `get-freebusy` | `groupExpansionMax` | **RANGE** / count | — (schema) | — | 1.0 | The maximum number of calendars to expand per group is a count with meaningful bounds. |
| `get-freebusy` | `calendarExpansionMax` | **RANGE** / count | — (schema) | — | 1.0 | The maximum number of calendars to expand is a count with meaningful bounds. |
| `list-calendars` | `account` | **POLICY** | — | account_nickname | 1.0 | The account argument refers to specific accounts, which is a policy concept. |
| `list-colors` | `account` | **POLICY** | — | account_nickname | 1.0 | The account nickname is an identifier that selects which account the call acts on. |
| `list-events` | `account` | **POLICY** | — | account_nickname | 1.0 | The account nickname(s) determine which accounts the call acts on. |
| `list-events` | `calendarId` | **POLICY** | — | calendar_identifier | 1.0 | The calendar identifier(s) determine which calendars the call acts on. |
| `list-events` | `calendarId[]` | **POLICY** | — | calendar_identifier | 1.0 | The calendar identifier(s) determine which calendars the call acts on. |
| `list-events` | `timeMin` | **RANGE** / temporal | — (none) | — | 1.0 | The start of the time range is a temporal value. |
| `list-events` | `timeMax` | **RANGE** / temporal | — (none) | — | 1.0 | The end of the time range is a temporal value. |
| `list-events` | `timeZone` | **IGNORE** | — | — | 1.0 | The timezone is a configuration detail that does not change the identity or quantity of resources acted upon. |
| `list-events` | `fields[]` | **IGNORE** | — | — | 1.0 | The fields are configuration options that do not change the identity or quantity of resources acted upon. |
| `list-events` | `privateExtendedProperty[]` | **IGNORE** | — | — | 1.0 | The private extended properties are filters that do not change the identity or quantity of resources acted upon. |
| `list-events` | `sharedExtendedProperty[]` | **IGNORE** | — | — | 1.0 | The shared extended properties are filters that do not change the identity or quantity of resources acted upon. |
| `manage-accounts` | `action` | **IGNORE** | — | — | 1.0 | The action argument changes only the operation performed, not a specific resource or context. |
| `manage-accounts` | `account_id` | **POLICY** | — | Google account identifier | 1.0 | The account_id is a friendly name used to identify specific Google accounts, which changes the context of the operation. |
| `respond-to-event` | `calendarId` | **POLICY** | — | calendar | 1.0 | The calendar ID selects which calendar the operation acts on. |
| `respond-to-event` | `eventId` | **POLICY** | — | event | 1.0 | The event ID selects which specific event within a calendar is acted upon. |
| `respond-to-event` | `account` | **POLICY** | — | account | 1.0 | The account nickname determines the context in which the operation is performed, potentially affecting permissions and visibility. |
| `respond-to-event` | `response` | **IGNORE** | — | — | 1.0 | This argument changes only how the event invitation is responded to; it does not change WHICH subject or resource is acted upon. |
| `respond-to-event` | `comment` | **IGNORE** | — | — | 1.0 | The comment is free text that accompanies a response and does not affect which resources are acted on. |
| `respond-to-event` | `modificationScope` | **IGNORE** | — | — | 1.0 | This argument changes only the scope of the modification (e.g., this event or all events), but it doesn't change WHICH subject or resource is acted upon. |
| `respond-to-event` | `originalStartTime` | **RANGE** / temporal | — (unstated) | — | 1.0 | The original start time of the event instance has a meaningful order as it represents a point in time. |
| `respond-to-event` | `sendUpdates` | **IGNORE** | — | — | 1.0 | This argument changes only whether notifications are sent and to whom, but does not change WHICH subject or resource is acted upon. |
| `search-events` | `account` | **POLICY** | — | Account nickname(s) | 1.0 | The account argument selects which accounts the search acts on, making it a policy concept. |
| `search-events` | `calendarId` | **POLICY** | — | Calendar identifier(s) | 1.0 | The calendarId argument selects which calendars the search acts on, making it a policy concept. |
| `search-events` | `query` | **IGNORE** | — | — | 1.0 | The query argument is free text and changes only the search criteria, not which resource or context. |
| `search-events` | `timeMin` | **RANGE** / temporal | — (none) | — | 1.0 | The timeMin argument represents a temporal value, indicating the start of the search range. |
| `search-events` | `timeMax` | **RANGE** / temporal | — (none) | — | 1.0 | The timeMax argument represents a temporal value, indicating the end of the search range. |
| `search-events` | `timeZone` | **IGNORE** | — | — | 1.0 | The timeZone argument changes only the timezone context, not which resource or subject. |
| `search-events` | `fields[]` | **IGNORE** | — | items: IGNORE | 1.0 | The fields argument specifies additional fields to include in the response, which does not change the resource or context. |
| `search-events` | `privateExtendedProperty[]` | **IGNORE** | — | items: IGNORE | 1.0 | The privateExtendedProperty argument filters by extended properties, which does not change the resource or context. |
| `search-events` | `sharedExtendedProperty[]` | **IGNORE** | — | items: IGNORE | 1.0 | The sharedExtendedProperty argument filters by extended properties, which does not change the resource or context. |
| `update-event` | `account` | **POLICY** | — | Account nickname | 1.0 | The account nickname is used to identify a specific account, which is subject to policy. |
| `update-event` | `calendarId` | **POLICY** | — | Calendar ID | 1.0 | Identifies the calendar on which operations are performed; this is a resource identifier and thus subject to policy. |
| `update-event` | `eventId` | **POLICY** | — | Event ID | 1.0 | The event ID identifies the specific event being updated, which is a resource identifier and thus subject to policy. |
| `update-event` | `summary` | **IGNORE** | — | — | 1.0 | This is free text that does not have an inherent order or identity relevant for policy decisions. |
| `update-event` | `description` | **IGNORE** | — | — | 1.0 | Free text description, which does not affect the scope of action and thus is ignored in terms of policy relevance. |
| `update-event` | `start` | **RANGE** / temporal | — (unstated) | — | 1.0 | The start time has a meaningful order as it represents when the event starts, which is temporal data. |
| `update-event` | `end` | **RANGE** / temporal | — (unstated) | — | 1.0 | The end time has a meaningful order as it represents when the event ends, which is temporal data. |
| `update-event` | `timeZone` | **POLICY** | — | Time Zone | 1.0 | Identifies the time zone of the calendar, which can be subject to policy based on geographical or organizational rules. |
| `update-event` | `location` | **IGNORE** | — | — | 1.0 | Free text location description that does not have an inherent order or identity relevant for policy decisions. |
| `update-event` | `attendees[]` | **RANGE** / count | — (unstated) | items: POLICY | 1.0 | The list of attendees has a count that can be compared, and each attendee's email is an identifier subject to policy. |
| `update-event` | `colorId` | **IGNORE** | — | — | 1.0 | Color ID does not have inherent order or identity relevant for policy decisions; it affects only the presentation of events. |
| `update-event` | `reminders.useDefault` | **IGNORE** | — | — | 1.0 | Boolean flag that changes how reminders are set, but does not affect the scope or identity of resources involved. |
| `update-event` | `reminders.overrides[]` | **RANGE** / count | — (unstated) | items: IGNORE | 1.0 | The list of custom reminders has a count that can be compared, but the individual items are configuration settings. |
| `update-event` | `recurrence[]` | **RANGE** / count | — (unstated) | items: POLICY | 1.0 | The list of recurrence rules has a count that can be compared, and each rule is an identifier subject to policy. |
| `update-event` | `sendUpdates` | **IGNORE** | — | — | 1.0 | Enum value that changes how notifications are sent but does not affect the scope or identity of resources involved. |
| `update-event` | `modificationScope` | **POLICY** | — | Modification Scope | 1.0 | The modification scope determines which events in a recurring series are affected, and this can be subject to policy. |
| `update-event` | `originalStartTime` | **RANGE** / temporal | — (unstated) | — | 1.0 | Represents the original start time of an event, which is temporal data with a meaningful order. |
| `update-event` | `futureStartDate` | **RANGE** / temporal | — (unstated) | — | 1.0 | The future start date has a meaningful order as it represents when the event starts in the future, which is temporal data. |
| `update-event` | `checkConflicts` | **IGNORE** | — | — | 1.0 | Boolean flag that changes how conflicts are checked but does not affect the scope or identity of resources involved. |
| `update-event` | `calendarsToCheck[]` | **RANGE** / count | — (unstated) | items: POLICY | 1.0 | The list of calendars to check for conflicts has a count that can be compared, and each calendar ID is an identifier subject to policy. |
| `update-event` | `conferenceData.createRequest.requestId` | **IGNORE** | — | — | 1.0 | Client-generated unique ID used for idempotency; it does not affect the scope or identity of resources involved. |
| `update-event` | `conferenceData.createRequest.conferenceSolutionKey.type` | **POLICY** | — | Conference Solution Type | 1.0 | The conference solution type can be subject to policy based on the organization's approved solutions. |
| `update-event` | `transparency` | **POLICY** | — | Event Transparency | 1.0 | Whether an event blocks time is a property that can be subject to policy based on organizational rules. |
| `update-event` | `visibility` | **POLICY** | — | Event Visibility | 1.0 | The visibility of the event can be subject to policy based on privacy and access control policies. |
| `update-event` | `guestsCanInviteOthers` | **IGNORE** | — | — | 1.0 | Boolean flag that changes attendee permissions but does not affect the scope or identity of resources involved. |
| `update-event` | `guestsCanModify` | **IGNORE** | — | — | 1.0 | Boolean flag that changes attendee permissions but does not affect the scope or identity of resources involved. |
| `update-event` | `guestsCanSeeOtherGuests` | **IGNORE** | — | — | 1.0 | Boolean flag that changes attendee permissions but does not affect the scope or identity of resources involved. |
| `update-event` | `anyoneCanAddSelf` | **IGNORE** | — | — | 1.0 | Boolean flag that changes event access but does not affect the scope or identity of resources involved. |
| `update-event` | `extendedProperties.private` | **IGNORE** | — | — | 1.0 | Extended properties are application-specific data and do not have inherent order or identity relevant for policy decisions. |
| `update-event` | `extendedProperties.shared` | **IGNORE** | — | — | 1.0 | Shared extended properties are visible to all attendees but do not have inherent order or identity relevant for policy decisions. |
| `update-event` | `attachments[]` | **RANGE** / count | — (unstated) | items: IGNORE | 1.0 | The list of attachments has a count that can be compared, but the individual items are configuration settings. |

**RANGE** 32 · **POLICY** 61 · **IGNORE** 55 · **UNKNOWN** 0 · 110 declared · 0 tool(s) declare none · failed: none.

## slack

Full explanation, tool by tool: [`slack.md`](slack.md)

| tool | argument | class | low / medium / high | policy concept / items | conf | why |
|---|---|---|---|---|---|---|
| `channels_list` | `channel_types` | **POLICY** | — | channel_type | 1.0 | The value selects which type of channels to list, changing the context of the call. |
| `channels_list` | `cursor` | **IGNORE** | — | — | 1.0 | Cursor is used for pagination and does not affect the policy or represent a meaningful order. |
| `channels_list` | `limit` | **RANGE** / count | — (documented) | — | 1.0 | The limit represents the maximum number of items to return, which is a count. |
| `channels_list` | `query` | **IGNORE** | — | — | 1.0 | Query is used for filtering channels and does not affect policy or represent a meaningful order. |
| `channels_list` | `query_targets` | **POLICY** | — | field_to_match | 1.0 | The value selects which fields to match the query against, changing the context of the call. |
| `channels_list` | `sort` | **IGNORE** | — | — | 1.0 | Sort changes only how results are presented and does not affect policy or represent a meaningful order. |
| `channels_me` | `channel_types` | **POLICY** | — | channel_type | 1.0 | The value selects which type of channels to list, changing the context of the call. |
| `channels_me` | `cursor` | **IGNORE** | — | — | 1.0 | Cursor is used for pagination and does not affect the policy or represent a meaningful order. |
| `channels_me` | `limit` | **RANGE** / count | — (documented) | — | 1.0 | The limit argument represents a count of items to return, with documented bounds. |
| `conversations_add_message` | `blocks` | **IGNORE** | — | — | 1.0 | The blocks argument is used for rich message formatting and does not represent a quantity or policy concept. |
| `conversations_add_message` | `channel_id` | **POLICY** | — | channel_or_user | 1.0 | The channel_id identifies the specific channel or user to which the message is sent, and this identity must be checked against policy. |
| `conversations_add_message` | `content_type` | **IGNORE** | — | — | 1.0 | The content_type argument only changes how the message is rendered and does not represent a quantity or policy concept. |
| `conversations_add_message` | `text` | **IGNORE** | — | — | 1.0 | The text argument is free-form message content and does not represent a quantity or policy concept. |
| `conversations_add_message` | `thread_ts` | **IGNORE** | — | — | 1.0 | The thread_ts argument is a timestamp used to identify the parent message or thread, but it does not represent a quantity or policy concept. |
| `conversations_history` | `channel_id` | **POLICY** | — | channel_or_user | 1.0 | The channel_id identifies a specific channel or user, which is subject to policy. |
| `conversations_history` | `cursor` | **IGNORE** | — | — | 1.0 | Cursor is used for pagination and does not have an inherent order or identity that would be relevant to policy. |
| `conversations_history` | `include_activity_messages` | **IGNORE** | — | — | 1.0 | This argument changes the content of the response but does not affect which resource is accessed, so it's operational and not subject to policy. |
| `conversations_history` | `limit` | **RANGE** / duration | — (unstated) | — | 1.0 | The limit argument can specify a duration or number of messages, which has an inherent order (e.g., longer time periods or more messages). |
| `conversations_join` | `channel_id` | **POLICY** | — | channel | 1.0 | The channel ID or name is used to identify which specific channel the user wants to join, and this selection must be validated against organizational policies. |
| `conversations_leave` | `channel_id` | **POLICY** | — | channel_or_user_identifier | 1.0 | The channel_id is an identifier that determines which specific channel or user the action acts upon, and this requires policy validation. |
| `conversations_mark` | `channel_id` | **POLICY** | — | channel_or_user | 1.0 | The channel or user ID/name is a policy concept as it determines which specific communication context the operation acts on. |
| `conversations_mark` | `ts` | **RANGE** / temporal | — (none) | — | 1.0 | The timestamp is a temporal value that indicates up to which point messages are marked as read. It has a meaningful order. |
| `conversations_replies` | `channel_id` | **POLICY** | — | channel | 1.0 | The channel ID or name is used to identify which specific channel the call acts on. |
| `conversations_replies` | `cursor` | **IGNORE** | — | — | 1.0 | Cursor values are typically opaque tokens used for pagination and do not have a meaningful order or policy context. |
| `conversations_replies` | `include_activity_messages` | **IGNORE** | — | — | 1.0 | This is an operational switch that changes how the result is rendered, but does not affect which resources are acted upon. |
| `conversations_replies` | `limit` | **RANGE** / duration | — (none) | — | 1.0 | The limit can be specified as a duration or number of messages, indicating a quantity that has an order. |
| `conversations_replies` | `thread_ts` | **RANGE** / temporal | — (none) | — | 1.0 | The timestamp is a temporal value that has an order. |
| `conversations_search_messages` | `cursor` | **IGNORE** | — | — | 1.0 | The cursor is used for pagination and does not have a meaningful order or policy context. |
| `conversations_search_messages` | `filter_date_after` | **RANGE** / temporal | — (none) | — | 1.0 | The date after which messages are filtered has a meaningful order. |
| `conversations_search_messages` | `filter_date_before` | **RANGE** / temporal | — (none) | — | 1.0 | The date before which messages are filtered has a meaningful order. |
| `conversations_search_messages` | `filter_date_during` | **RANGE** / temporal | — (none) | — | 1.0 | The period during which messages are filtered has a meaningful order. |
| `conversations_search_messages` | `filter_date_on` | **RANGE** / temporal | — (none) | — | 1.0 | The date on which messages are filtered has a meaningful order. |
| `conversations_search_messages` | `filter_in_channel` | **POLICY** | — | channel_id_or_name | 1.0 | The channel ID or name is a policy concept as it identifies the specific channel. |
| `conversations_search_messages` | `filter_in_im_or_mpim` | **POLICY** | — | dm_or_mpim_id_or_name | 1.0 | The DM or MPIM ID or name is a policy concept as it identifies the specific conversation. |
| `conversations_search_messages` | `filter_threads_only` | **IGNORE** | — | — | 1.0 | This is a boolean flag that changes the result set but does not have an order or policy context. |
| `conversations_search_messages` | `filter_users_from` | **POLICY** | — | user_id_or_display_name | 1.0 | The user ID or display name is a policy concept as it identifies the specific user. |
| `conversations_search_messages` | `filter_users_with` | **POLICY** | — | user_id_or_display_name | 1.0 | The user ID or display name is a policy concept as it identifies the specific user. |
| `conversations_search_messages` | `limit` | **RANGE** / count | — (schema) | — | 1.0 | The limit has a meaningful order and is bounded by the schema. |
| `conversations_search_messages` | `search_query` | **IGNORE** | — | — | 1.0 | The search query is free text and does not have a meaningful order or policy context. |
| `conversations_unreads` | `channel_types` | **POLICY** | — | channel_type | 1.0 | The value selects which type of channels to act on, changing the context of the call. |
| `conversations_unreads` | `include_messages` | **IGNORE** | — | — | 1.0 | This argument changes only how the result is rendered (whether it includes messages or not). |
| `conversations_unreads` | `include_muted` | **IGNORE** | — | — | 1.0 | This argument changes only whether muted channels are included in results, which does not change the identity of the resources acted upon. |
| `conversations_unreads` | `max_channels` | **RANGE** / count | — (none) | — | 1.0 | The value represents a count of channels, which has a meaningful order. |
| `conversations_unreads` | `max_messages_per_channel` | **RANGE** / count | — (none) | — | 1.0 | The value represents a count of messages, which has a meaningful order. |
| `conversations_unreads` | `mentions_only` | **IGNORE** | — | — | 1.0 | This argument changes only whether to return channels with mentions or not, which does not change the identity of the resources acted upon. |
| `usergroups_create` | `channels` | **POLICY** | — | channel_ids | 1.0 | The value selects specific channels, which is a policy concern. |
| `usergroups_create` | `description` | **IGNORE** | — | — | 1.0 | This is free text that does not affect the scope or identity of the operation. |
| `usergroups_create` | `handle` | **POLICY** | — | user_group_handle | 1.0 | The handle uniquely identifies a user group and is used for mentions, which can be subject to policy. |
| `usergroups_create` | `name` | **IGNORE** | — | — | 1.0 | This is the display name of the user group, which does not affect the scope or identity of the operation in a way that would require policy evaluation. |
| `usergroups_list` | `include_count` | **IGNORE** | — | — | 1.0 | This is a boolean flag that only changes how the result is rendered, not which resources are acted upon. |
| `usergroups_list` | `include_disabled` | **IGNORE** | — | — | 1.0 | This is a boolean flag that only changes how the result is rendered, not which resources are acted upon. |
| `usergroups_list` | `include_users` | **IGNORE** | — | — | 1.0 | This is a boolean flag that only changes how the result is rendered, not which resources are acted upon. |
| `usergroups_me` | `action` | **IGNORE** | — | — | 1.0 | The action argument changes only the operation performed, not a quantity or policy entity. |
| `usergroups_me` | `usergroup_id` | **POLICY** | — | user group | 1.0 | The usergroup_id identifies a specific user group, which is a policy entity. |
| `usergroups_update` | `channels` | **POLICY** | — | channel_ids | 1.0 | The value represents specific channel IDs, which are policy-relevant identifiers. |
| `usergroups_update` | `description` | **IGNORE** | — | — | 1.0 | This is free text that does not have a meaningful order or identity relevant to policy. |
| `usergroups_update` | `handle` | **POLICY** | — | mention_handle | 1.0 | The handle changes how users mention the group, which is a specific identifier that matters for policy. |
| `usergroups_update` | `name` | **IGNORE** | — | — | 1.0 | This is free text that does not have a meaningful order or identity relevant to policy. |
| `usergroups_update` | `usergroup_id` | **POLICY** | — | user_group_ids | 1.0 | The user group ID is an identifier that matters for policy, as it specifies which specific group the operation acts on. |
| `usergroups_users_update` | `usergroup_id` | **POLICY** | — | user_group | 1.0 | The user group ID is an identifier that selects which specific user group the operation acts on. |
| `usergroups_users_update` | `users` | **RANGE** / count | — (unstated) | items: POLICY | 1.0 | The 'users' argument is a list of user IDs, which can be interpreted as the count of users to replace in the group. Each item within this list represents an individual user ID, making each item a policy concept. |
| `users_search` | `limit` | **RANGE** / count | — (documented) | — | 1.0 | The limit argument specifies a maximum number of results, which is a count. |
| `users_search` | `query` | **IGNORE** | — | — | 1.0 | The query argument is a search term that does not have an inherent order or policy context. |

**RANGE** 15 · **POLICY** 21 · **IGNORE** 27 · **UNKNOWN** 0 · 63 declared · 0 tool(s) declare none · failed: none.

## All three servers

**RANGE** 81 · **POLICY** 143 · **IGNORE** 122 · **UNKNOWN** 0.
