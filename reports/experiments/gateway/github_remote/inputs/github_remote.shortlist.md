# Input shortlist: github_remote

Kept **155 of 292** inputs across 48 tools (53%). 64 decision(s) flagged ⚑ for review (the votes disagreed).

| Run | |
|---|---|
| Catalog | `/home/ovadyat/MCP/reports/experiments/gateway/github_remote/github_remote.json` (sha256 `108315cf7888`) |
| Policy | `/home/ovadyat/MCP/reports/experiments/gateway/github_remote/github_helios_remote.md` (sha256 `0ec96105061c`) |
| Prompt | `run11` (sha256 `41802e7dd261`) |
| Model | qwen2.5:32b (digest `9f13ba1299af`) |
| Finished | 2026-10-14T10:16:12+00:00 |

Tools with no inputs: get_me

## add_comment_to_pending_review: kept 4 of 10

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `body` | carried | 3.0 | two_questions | 3/3 keep | A comment with sensitive information against a neutral one |
| `owner` | which | 4.0 | two_questions | 3/3 keep | A repository owner with sensitive code against a non-sensitive one |
| `path` | which | 4.0 | two_questions | 2/3 keep ⚑ | Sensitive file path against a non-sensitive one |
| `repo` | which | 4.0 | two_questions | 3/3 keep | Sensitive repository against a non-sensitive one |

Dropped: `line`, `pullNumber` ⚑, `side`, `startLine`, `startSide`, `subjectType`

## add_issue_comment: kept 3 of 6

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `body` | carried | 3.0 | two_questions | 3/3 keep | Sensitive content in the comment body can expose internal discussions. |
| `issue_number` | which | 4.0 | two_questions | 3/3 keep | Refers to sensitive issue threads or records within the repository. |
| `repo` | which | 4.0 | two_questions | 2/3 keep ⚑ | Refers to the repository containing sensitive issue threads or records. |

Dropped: `comment_id`, `owner`, `reaction`

## add_reply_to_pull_request_comment: kept 3 of 6

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `body` | carried | 3.0 | two_questions | 3/3 keep | A reply carrying sensitive data is riskier than a benign one |
| `owner` | which | 4.0 | two_questions | 3/3 keep | Sensitive repository owner against a non-sensitive one |
| `repo` | which | 4.0 | two_questions | 3/3 keep | Sensitive repository against a non-sensitive one |

Dropped: `commentId`, `pullNumber`, `reaction`

## assign_copilot_to_issue: kept 2 of 5

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 3.0 | two_questions | 1/1 keep | The owner decides which repository, and thus which asset, is affected. |
| `repo` | which | 3.0 | two_questions | 1/1 keep | The repo name together with the owner fully identifies the specific repository, an asset. |

Dropped: `base_ref`, `custom_instructions`, `issue_number` ⚑

## create_branch: kept 3 of 4

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `branch` | which | 3.0 | two_questions | 3/3 keep | A branch name can point to sensitive or non-sensitive code |
| `owner` | which | 4.0 | two_questions | 2/3 keep ⚑ | Different owners can have different levels of access and sensitivity |
| `repo` | which | 4.0 | two_questions | 3/3 keep | The repository itself may contain sensitive infrastructure or market bidding code |

Dropped: `from_branch` ⚑

## create_or_update_file: kept 5 of 8

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `branch` | which | 4.0 | two_questions | 3/3 keep | The branch can point to sensitive or less sensitive parts of the repository, affecting what is updated. |
| `content` | carried | 5.0 | two_questions | 3/3 keep | Content could contain highly sensitive information like credentials or critical system configurations. |
| `owner` | which | 4.0 | two_questions | 3/3 keep | Owner determines which repository (and thus, which assets) are affected by this operation. |
| `path` | which | 5.0 | two_questions | 3/3 keep | The path can point to sensitive files or directories within the repository. |
| `repo` | which | 4.0 | two_questions | 3/3 keep | Repo determines which repository (and thus, which assets) are affected by this operation. |

Dropped: `allow_symlink_write`, `message`, `sha`

## create_pull_request: kept 5 of 10

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `base` | which | 4.0 | two_questions | 3/3 keep | A pull request into a critical BES cyber system repository is riskier than one into a public site. |
| `draft` | action | 3.0 | two_questions | 3/3 keep | A draft pull request is less risky than a non-draft one that could be merged. |
| `maintainer_can_modify` | action | 3.0 | two_questions | 2/3 keep ⚑ | Allowing maintainers to modify a pull request can change its content and risk level. |
| `repo` | which | 4.0 | two_questions | 3/3 keep | A pull request into a critical BES cyber system repository is riskier than one into a public site. |
| `reviewers[]` | who | 3.0 | two_questions | 3/3 keep | Reviewers can influence the approval process and thus affect the asset's state. |

Dropped: `body`, `head` ⚑, `owner` ⚑, `reviewers`, `title`

## create_pull_request_with_copilot: kept 4 of 5

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `base_ref` | which | 3.0 | two_questions | 3/3 keep | A critical branch against a non-critical one |
| `owner` | which | 4.0 | two_questions | 3/3 keep | An owner with sensitive repositories against one without |
| `problem_statement` | carried | 3.0 | two_questions | 3/3 keep | A statement that could lead to a critical change against a non-critical one |
| `repo` | which | 4.0 | two_questions | 3/3 keep | A sensitive repository against a non-sensitive one |

Dropped: `title`

## create_repository: kept 3 of 5

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `name` | which | 4.0 | two_questions | 3/3 keep | Naming a repository can expose BES Cyber System Information if sensitive names are used. |
| `organization` | which | 5.0 | two_questions | 3/3 keep | Creating the repository in an external organization exposes BES Cyber System Information outside the perimeter. |
| `private` | action | 4.0 | two_questions | 3/3 keep | Setting a repository to public can expose sensitive information compared to keeping it private. |

Dropped: `autoInit`, `description`

## delete_file: kept 3 of 5

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 4.0 | two_questions | 3/3 keep | Owner can be a sensitive repository owner, affecting the asset's sensitivity. |
| `path` | which | 5.0 | two_questions | 3/3 keep | Path to delete directly affects which file and potentially its sensitivity. |
| `repo` | which | 4.0 | two_questions | 3/3 keep | Repository name can be a sensitive repository, affecting the asset's sensitivity. |

Dropped: `branch` ⚑, `message`

## fork_repository: kept 1 of 3

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `organization` | who | 5.0 | two_questions | 3/3 keep | Forking to an external organization exposes BES Cyber System Information |

Dropped: `owner` ⚑, `repo` ⚑

## get_commit: kept 4 of 6

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `detail` | carried | 3.0 | two_questions | 2/3 keep ⚑ | full_patch exposes detailed diffs against none |
| `owner` | which | 4.0 | two_questions | 3/3 keep | sensitive repository owner against a public one |
| `perPage` | how_much | 3.0 | two_questions | 2/3 keep ⚑ | large page size against small one |
| `repo` | which | 4.0 | two_questions | 3/3 keep | sensitive repository name against a public one |

Dropped: `page`, `sha`

## get_copilot_job_status: kept 3 of 3

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `id` | which | 3.0 | two_questions | 3/3 keep | A job ID or pull request number can reveal different levels of sensitive information depending on the task. |
| `owner` | which | 4.0 | two_questions | 3/3 keep | The repository owner can be a critical asset, especially if it involves BES Cyber System Information. |
| `repo` | which | 4.0 | two_questions | 3/3 keep | The repository name can point to sensitive code or configuration files that are part of the control-room path. |

## get_file_contents: kept 3 of 7

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 4.0 | two_questions | 3/3 keep | Owner can be a sensitive repository owner like 'helios-grid-infra-config' |
| `path` | which | 5.0 | two_questions | 3/3 keep | Path can point to sensitive files or directories, including credential-shaped paths |
| `repo` | which | 4.0 | two_questions | 3/3 keep | Repo can be a sensitive repository like 'helios-grid-infra-config' |

Dropped: `fields`, `fields[]`, `ref`, `sha`

## get_label: kept 2 of 3

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 3.0 | two_questions | 3/3 keep | The owner decides which repository's label is accessed, affecting BES Cyber System Information. |
| `repo` | which | 3.0 | two_questions | 3/3 keep | The repo name decides which repository's label is accessed, affecting BES Cyber System Information. |

Dropped: `name`

## get_latest_release: kept 2 of 2

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 3.0 | two_questions | 3/3 keep | The owner decides which repository's latest release is fetched, affecting BES Cyber System Information. |
| `repo` | which | 3.0 | two_questions | 3/3 keep | The repo name decides which specific repository's latest release is fetched, impacting sensitive code and configuration. |

## get_release_by_tag: kept 2 of 3

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 3.0 | two_questions | 3/3 keep | The owner decides which repository's release is fetched, affecting BES Cyber System Information. |
| `repo` | which | 3.0 | two_questions | 3/3 keep | The repo name decides which specific repository's release is fetched, impacting the control-room path code and configuration. |

Dropped: `tag`

## get_tag: kept 2 of 3

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 3.0 | two_questions | 3/3 keep | The owner decides which repository's tag is accessed, affecting BES Cyber System Information. |
| `repo` | which | 3.0 | two_questions | 3/3 keep | The repo name decides which specific repository's tag is accessed, impacting sensitive code and configuration. |

Dropped: `tag`

## get_team_members: kept 1 of 2

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `org` | which | 3.0 | two_questions | 3/3 keep | The most sensitive org against the least sensitive one |

Dropped: `team_slug` ⚑

## get_teams: kept 0 of 1

Dropped: `user`

## issue_read: kept 3 of 6

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `issue_number` | which | 3.0 | two_questions | 2/3 keep ⚑ | The issue number decides which specific issue is read, affecting the confidentiality of its content. |
| `method` | action | 4.0 | two_questions | 3/3 keep | Different methods can expose different parts of an issue thread, from comments to labels, impacting the scope and sensitivity of data exposed. |
| `perPage` | how_much | 3.0 | two_questions | 2/3 keep ⚑ | The number of items per page can affect the amount of sensitive information retrieved in a single call. |

Dropped: `owner`, `page`, `repo` ⚑

## issue_write: kept 9 of 23

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `assignees` | who | 3.0 | two_questions | 3/3 keep | Assigning to a sensitive team member vs. an ordinary user |
| `assignees[]` | who | 3.0 | two_questions | 3/3 keep | Assigning to a sensitive team member vs. an ordinary user |
| `body` | carried | 4.0 | two_questions | 3/3 keep | Sensitive data in the body vs. non-sensitive content |
| `issue_fields` | carried | 4.0 | two_questions | 3/3 keep | Sensitive field values vs. non-sensitive ones |
| `issue_fields[].field_name` | carried | 4.0 | two_questions | 2/3 keep ⚑ | Sensitive field names vs. non-sensitive ones |
| `issue_fields[].field_option_name` | carried | 4.0 | two_questions | 2/3 keep ⚑ | Sensitive options vs. non-sensitive ones |
| `issue_fields[].value` | carried | 4.0 | two_questions | 3/3 keep | Sensitive field values vs. non-sensitive ones |
| `repo` | which | 4.0 | two_questions | 2/3 keep ⚑ | Repository where issues are created or updated |
| `state` | action | 3.0 | two_questions | 3/3 keep | Closing vs. opening an issue |

Dropped: `duplicate_of`, `issue_fields[].delete` ⚑, `issue_number`, `labels` ⚑, `labels[]` ⚑, `method` ⚑, `milestone`, `owner` ⚑, `parent_issue_number` ⚑, `parent_owner` ⚑, `parent_repo` ⚑, `state_reason`, `title`, `type`

## list_branches: kept 2 of 4

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 3.0 | two_questions | 3/3 keep | The owner decides which repository's branches are listed, affecting sensitive BES Cyber System Information. |
| `repo` | which | 3.0 | two_questions | 3/3 keep | The repository name decides which repository's branches are listed, affecting sensitive BES Cyber System Information. |

Dropped: `page`, `perPage` ⚑

## list_commits: kept 5 of 11

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 3.0 | two_questions | 3/3 keep | Owner determines the repository, affecting different assets like BES Cyber System Information or market bidding engine. |
| `path` | which | 3.0 | two_questions | 2/3 keep ⚑ | File path can limit the scope of commits, affecting different parts of assets. |
| `repo` | which | 4.0 | two_questions | 3/3 keep | Repository name determines the specific asset being accessed, such as market bidding engine or SCADA gateway. |
| `since` | when | 3.0 | two_questions | 2/3 keep ⚑ | Date range can limit the commits affecting different parts of assets over time. |
| `until` | when | 3.0 | two_questions | 2/3 keep ⚑ | Date range can limit the commits affecting different parts of assets over time. |

Dropped: `author`, `fields`, `fields[]`, `page`, `perPage`, `sha`

## list_issue_fields: kept 2 of 2

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 3.0 | two_questions | 3/3 keep | Lists fields for a less sensitive owner against a more sensitive one |
| `repo` | which | 3.0 | two_questions | 3/3 keep | Lists fields for a less sensitive repository against a more sensitive one |

## list_issue_types: kept 2 of 2

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 3.0 | two_questions | 3/3 keep | The owner decides which organization's issue types are listed, affecting access to BES Cyber System Information. |
| `repo` | which | 3.0 | two_questions | 3/3 keep | The repo specifies the repository whose issue types are listed; if omitted, it defaults to org-level issue types, impacting access to sensitive repositories. |

## list_issues: kept 7 of 15

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `field_filters` | how_much | 3.0 | two_questions | 2/3 keep ⚑ | Filtering by custom field values can reduce the number of issues returned. |
| `fields` | how_much | 3.0 | two_questions | 3/3 keep | Selecting specific fields can reduce the amount of data returned per issue. |
| `labels` | how_much | 3.0 | two_questions | 2/3 keep ⚑ | Filtering by labels can reduce the number of issues returned. |
| `owner` | which | 4.0 | two_questions | 3/3 keep | Owner determines the repository from which issues are listed; different repositories can have different sensitivities. |
| `perPage` | how_much | 3.0 | two_questions | 2/3 keep ⚑ | Number of results per page affects how much data is returned in a single call. |
| `repo` | which | 4.0 | two_questions | 3/3 keep | Repository name determines the repository from which issues are listed; different repositories can have different sensitivities. |
| `state` | how_much | 3.0 | two_questions | 2/3 keep ⚑ | Filtering by state (open/closed) can significantly reduce or increase the number of issues returned. |

Dropped: `after`, `direction`, `field_filters[].field_name` ⚑, `field_filters[].value` ⚑, `fields[]` ⚑, `labels[]` ⚑, `orderBy`, `since` ⚑

## list_pull_requests: kept 6 of 11

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `base` | which | 3.0 | two_questions | 3/3 keep | Filtering by a sensitive base branch versus an insensitive one |
| `fields` | how_much | 3.0 | two_questions | 3/3 keep | Returning all fields versus only non-sensitive ones |
| `fields[]` | how_much | 3.0 | two_questions | 3/3 keep | Returning sensitive fields like 'body' versus non-sensitive ones |
| `head` | which | 3.0 | two_questions | 3/3 keep | Filtering by a sensitive head branch versus an insensitive one |
| `perPage` | how_much | 3.0 | two_questions | 3/3 keep | Returning a large number of results versus a small number |
| `state` | how_much | 3.0 | two_questions | 3/3 keep | Filtering by 'all' versus only 'open' or 'closed' |

Dropped: `direction`, `owner` ⚑, `page`, `repo` ⚑, `sort`

## list_releases: kept 3 of 6

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 4.0 | two_questions | 3/3 keep | Sensitive repository owner against a less critical one |
| `perPage` | how_much | 3.0 | two_questions | 2/3 keep ⚑ | A large page size can expose more data than a small one |
| `repo` | which | 4.0 | two_questions | 3/3 keep | Sensitive repository against a less critical one |

Dropped: `fields`, `fields[]`, `page`

## list_repository_collaborators: kept 3 of 5

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 4.0 | two_questions | 3/3 keep | The owner decides which repository's collaborators are listed, affecting sensitive BES Cyber System Information. |
| `perPage` | how_much | 3.0 | two_questions | 3/3 keep | The number of results per page affects how much data is retrieved in a single call. |
| `repo` | which | 4.0 | two_questions | 3/3 keep | The repository name decides which repository's collaborators are listed, affecting sensitive BES Cyber System Information. |

Dropped: `affiliation`, `page`

## list_tags: kept 3 of 4

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 3.0 | two_questions | 3/3 keep | The owner decides which repository's tags are listed, affecting BES Cyber System Information. |
| `perPage` | how_much | 3.0 | two_questions | 2/3 keep ⚑ | The number of results per page affects how much data is retrieved in one call, impacting BES Cyber System Information. |
| `repo` | which | 3.0 | two_questions | 3/3 keep | The repository name decides which repository's tags are listed, affecting BES Cyber System Information. |

Dropped: `page`

## merge_pull_request: kept 3 of 7

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `merge_method` | action | 4.0 | two_questions | 3/3 keep | Different merge methods can affect how changes are integrated into the repository. |
| `owner` | which | 4.5 | two_questions | 2/2 keep | Owner of the repository, which determines the scope and sensitivity of the asset being merged. |
| `repo` | which | 4.5 | two_questions | 2/2 keep | Repository name, which determines the scope and sensitivity of the asset being merged. |

Dropped: `commit_message`, `commit_title`, `expectedHeadSha`, `pullNumber`

## pull_request_read: kept 4 of 7

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `method` | action | 3.0 | two_questions | 3/3 keep | Different methods can retrieve different types of data from pull requests, affecting the sensitivity of the information retrieved. |
| `owner` | which | 4.0 | two_questions | 3/3 keep | Owner name decides which repository's pull request is accessed; some repositories may contain more sensitive data than others. |
| `perPage` | how_much | 3.0 | two_questions | 2/3 keep ⚑ | Controls the amount of data retrieved per page; a larger value can expose more sensitive information in one call. |
| `repo` | which | 4.0 | two_questions | 3/3 keep | Repository name decides which repository's pull request is accessed; some repositories may contain more sensitive data than others. |

Dropped: `after`, `page`, `pullNumber` ⚑

## pull_request_review_write: kept 4 of 8

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `body` | carried | 3.0 | two_questions | 3/3 keep | A body carrying sensitive data against a neutral comment |
| `event` | action | 4.0 | two_questions | 3/3 keep | "REQUEST_CHANGES" against "COMMENT" |
| `method` | action | 5.0 | two_questions | 3/3 keep | "delete_pending" against "create" |
| `repo` | which | 4.0 | two_questions | 2/3 keep ⚑ | Determines the repository, carrying BES Cyber System Information and CIP change-control gate |

Dropped: `commitID`, `owner` ⚑, `pullNumber` ⚑, `threadId` ⚑

## push_files: kept 6 of 7

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `branch` | which | 4.0 | two_questions | 3/3 keep | Pushing to a branch that affects the CIP security perimeter is riskier than pushing to a non-perimeter branch. |
| `files` | - | - | default | none answered | no vote answered this input; kept by default |
| `files[].content` | carried | 5.0 | two_questions | 3/3 keep | Sensitive content can be pushed, affecting the CIP security perimeter or market bidding strategy. |
| `files[].path` | which | 4.0 | two_questions | 3/3 keep | Paths that look credential-shaped are as weighty as the perimeter assets, and paths to sensitive files can affect the CIP security perimeter. |
| `owner` | which | 4.0 | two_questions | 3/3 keep | Owner can be a sensitive repository owner, affecting the CIP security perimeter or market bidding strategy. |
| `repo` | which | 4.0 | two_questions | 3/3 keep | Sensitive repositories like helios-grid-infra-config and helios-scada-gateway are under CIP change control, making the risk higher. |

Dropped: `message`

## request_copilot_review: kept 2 of 3

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 4.0 | two_questions | 3/3 keep | The owner can be a sensitive repository or a public one |
| `repo` | which | 4.0 | two_questions | 3/3 keep | The repository can be sensitive code or configuration, or less critical documentation |

Dropped: `pullNumber`

## run_secret_scanning: kept 1 of 3

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `files` | carried | 5.0 | two_questions | 3/3 keep | Sensitive files containing API keys or passwords against empty or harmless content |

Dropped: `owner`, `repo`

## search_code: kept 3 of 7

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `page` | none | 1.0 | policy | 0/3 keep | named by the policy for this tool; Pagination does not change the risk of accessing assets. |
| `perPage` | how_much | 4.0 | two_questions | 3/3 keep | A larger page size can expose more data from code search results. |
| `query` | which | 5.0 | two_questions | 3/3 keep | The query determines which repositories and files are searched, potentially exposing sensitive assets. |

Dropped: `fields`, `fields[]`, `order`, `sort`

## search_commits: kept 2 of 5

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `perPage` | how_much | 3.0 | two_questions | 2/3 keep ⚑ | A larger page size can expose more data at once compared to a smaller one. |
| `query` | carried | 5.0 | two_questions | 3/3 keep | The query can target sensitive repositories or commit messages, significantly changing the risk of the call. |

Dropped: `order`, `page`, `sort`

## search_issues: kept 6 of 9

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `fields` | how_much | 3.0 | two_questions | 3/3 keep | Reducing fields to only 'title' versus including sensitive 'body' |
| `fields[]` | how_much | 3.0 | two_questions | 3/3 keep | Reducing fields to only 'title' versus including sensitive 'body' |
| `owner` | which | 4.0 | two_questions | 3/3 keep | Searching in a sensitive repository versus a non-sensitive one |
| `perPage` | how_much | 3.0 | two_questions | 3/3 keep | Returning a large number of results versus a small number |
| `query` | carried | 4.0 | two_questions | 2/3 keep ⚑ | Sensitive query terms versus non-sensitive ones |
| `repo` | which | 4.0 | two_questions | 3/3 keep | Searching in a sensitive repository versus a non-sensitive one |

Dropped: `order`, `page`, `sort`

## search_pull_requests: kept 3 of 9

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 3.0 | two_questions | 3/3 keep | Different owners can have different levels of sensitivity. |
| `perPage` | how_much | 3.0 | two_questions | 3/3 keep | Larger page sizes can expose more data at once. |
| `repo` | which | 3.0 | two_questions | 3/3 keep | Different repositories can have different levels of sensitivity. |

Dropped: `fields`, `fields[]`, `order`, `page`, `query` ⚑, `sort`

## search_repositories: kept 2 of 6

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `perPage` | how_much | 3.0 | two_questions | 3/3 keep | A larger page size can expose more repository details at once |
| `query` | which | 4.0 | two_questions | 3/3 keep | The query can target sensitive repositories or metadata |

Dropped: `minimal_output`, `order`, `page`, `sort`

## search_users: kept 0 of 5

Dropped: `order`, `page`, `perPage`, `query` ⚑, `sort`

## sub_issue_write: kept 4 of 8

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `issue_number` | which | 3.0 | two_questions | 3/3 keep | Affects which parent issue is modified, impacting sensitive information within that issue. |
| `method` | action | 4.0 | two_questions | 3/3 keep | 'add' and 'remove' can significantly alter the structure of issues, while 'reprioritize' has less impact. |
| `replace_parent` | action | 4.0 | two_questions | 3/3 keep | When true, can significantly alter the structure of issues by replacing a sub-issue's parent. |
| `repo` | which | 3.0 | two_questions | 3/3 keep | Affects which repository is modified, impacting sensitive information within that repository. |

Dropped: `after_id`, `before_id`, `owner` ⚑, `sub_issue_id` ⚑

## ui_get: kept 3 of 3

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `method` | which | 3.0 | two_questions | 2/3 keep ⚑ | Fetching sensitive issue fields against fetching labels |
| `owner` | which | 4.0 | two_questions | 3/3 keep | Accessing a repository owner with BES Cyber System Information against one without |
| `repo` | which | 3.0 | two_questions | 3/3 keep | Fetching data from a sensitive repository against an ordinary one |

## update_issue_comment: kept 3 of 4

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `body` | carried | 3.0 | two_questions | 3/3 keep | Sensitive information in the comment body can expose sensitive data |
| `owner` | which | 4.0 | two_questions | 2/2 keep | Different repository owners can have different levels of sensitivity and access rights |
| `repo` | which | 4.0 | two_questions | 2/2 keep | Different repositories can contain sensitive information or code affecting BES Cyber Systems |

Dropped: `comment_id`

## update_pull_request: kept 7 of 11

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `base` | which | 3.0 | two_questions | 3/3 keep | Changing the base branch can affect which code is merged, impacting the asset. |
| `draft` | action | 3.0 | two_questions | 2/3 keep ⚑ | Marking a pull request as draft or ready for review changes the action taken on it, impacting its visibility and potential impact. |
| `owner` | which | 3.0 | two_questions | 2/3 keep ⚑ | The owner determines the repository, which can be sensitive in terms of its content or access levels. |
| `repo` | which | 4.0 | two_questions | 3/3 keep | The repository name decides which codebase is updated, impacting sensitive assets like BES Cyber Systems. |
| `reviewers` | who | 3.0 | two_questions | 1/1 keep | Reviewers can include sensitive stakeholders or external parties |
| `reviewers[]` | who | 3.0 | two_questions | 2/3 keep ⚑ | Adding reviewers can expose the pull request to more people, increasing risk. |
| `state` | action | 3.0 | two_questions | 3/3 keep | Changing a pull request's state from open to closed or vice versa significantly impacts its visibility and potential impact on assets. |

Dropped: `body`, `maintainer_can_modify` ⚑, `pullNumber`, `title`

## update_pull_request_branch: kept 2 of 4

| Input | Effect | Rank | Decided by | Votes | Reason |
|---|---|---|---|---|---|
| `owner` | which | 4.0 | two_questions | 3/3 keep | Affects which repository's pull request branch is updated, impacting sensitive BES Cyber System Information. |
| `repo` | which | 4.0 | two_questions | 3/3 keep | Affects which repository's pull request branch is updated, impacting sensitive BES Cyber System Information. |

Dropped: `expectedHeadSha`, `pullNumber`
