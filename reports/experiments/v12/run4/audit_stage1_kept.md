# run4 stage 1: audit of the inputs it KEPT

## github: 122 kept

keep 76 · should drop 13 · borderline 21 · record id 12

| verdict | tool | input | votes | decided by | reason |
|---|---|---|---|---|---|
| drop | create_issue | `milestone` | nYn | vote | milestone number; organizational tag only |
| drop | create_issue | `labels` | nYn | vote | issue labels; organizational tags only |
| drop | create_issue | `labels[]` | nYn | vote | issue labels; organizational tags only |
| drop | create_or_update_file | `sha` | YYY | vote | blob SHA copied from an earlier read; only lets the overwrite go through |
| drop | create_pull_request | `draft` | nnn | check | draft or ready; same code, same reviewers |
| drop | create_repository | `description` | nnn | check | free-text label of a new repo; nothing is reached through it |
| drop | list_issues | `sort` | nnn | check | sort order (on the not-important list) |
| drop | search_code | `page` | nnn | check | page number (on the not-important list) |
| drop | search_issues | `sort` | nnn | check | sort order (on the not-important list) |
| drop | update_issue | `milestone` | nnY | vote | milestone number; organizational tag only |
| drop | update_issue | `labels` | YYY | vote | issue labels; organizational tags only |
| drop | update_issue | `labels[]` | YYY | vote | issue labels; organizational tags only |
| drop | update_pull_request_branch | `expected_head_sha` | nnn | check | SHA copied from an earlier read; a safety check |
| borderline | create_branch | `branch` | YnY | vote | names a new branch, which can be sensitive |
| borderline | create_issue | `assignees` | YYY | vote | widens who can see, join or change something |
| borderline | create_issue | `assignees[]` | YYY | vote | picks what the call touches |
| borderline | create_or_update_file | `message` | nnn | check | Commit messages can indicate sensitive changes, especially in regulated environments |
| borderline | create_pull_request | `title` | nnn | check | The title can indicate urgency or sensitivity of the pull request. |
| borderline | create_pull_request | `maintainer_can_modify` | nnn | check | This setting can affect control over changes and compliance with regulatory requirements. |
| borderline | create_repository | `name` | YYY | vote | picks what the call touches |
| borderline | get_file_contents | `branch` | Ynn | vote | changes what the operation does |
| borderline | list_issues | `labels` | YYY | vote | scopes or filters the call |
| borderline | list_issues | `labels[]` | YYY | vote | scopes or filters the call |
| borderline | list_issues | `since` | YYY | vote | sets when or for how long |
| borderline | list_issues | `state` | YYY | vote | scopes or filters the call |
| borderline | list_pull_requests | `state` | YYY | vote | changes what the operation does |
| borderline | list_pull_requests | `head` | YYY | vote | filters the call, leaving it out widens the call |
| borderline | list_pull_requests | `base` | YYY | vote | filters the call, leaving it out widens the call |
| borderline | merge_pull_request | `commit_title` | nYY | vote | content written or sent |
| borderline | merge_pull_request | `commit_message` | nYY | vote | content written or sent |
| borderline | merge_pull_request | `merge_method` | YYY | vote | changes what the operation does |
| borderline | push_files | `message` | nnn | check | Commit message can indicate changes to sensitive assets |
| borderline | update_issue | `assignees` | YYY | vote | widens who can see, join or change something |
| borderline | update_issue | `assignees[]` | YYY | vote | picks what the call touches |
| record-id | add_issue_comment | `issue_number` | YYY | vote | picks what the call touches |
| record-id | create_pull_request_review | `pull_number` | YYY | vote | changes which pull request is reviewed, affecting CIP change control |
| record-id | create_pull_request_review | `commit_id` | YnY | vote | picks what the call touches |
| record-id | get_issue | `issue_number` | YYY | vote | changes which specific issue is retrieved, potentially sensitive content |
| record-id | get_pull_request | `pull_number` | YYY | vote | changes which pull request is retrieved, impacting risk based on content and state of the specific PR |
| record-id | get_pull_request_comments | `pull_number` | YYY | vote | changes what the operation does |
| record-id | get_pull_request_files | `pull_number` | YYY | vote | changes what the operation does |
| record-id | get_pull_request_reviews | `pull_number` | YYY | vote | changes what the operation does |
| record-id | get_pull_request_status | `pull_number` | YYY | vote | changes which pull request's status is retrieved, impacting risk based on the PR content and scope |
| record-id | merge_pull_request | `pull_number` | YYn | vote | changes what the operation does |
| record-id | update_issue | `issue_number` | YYY | vote | picks what the call touches |
| record-id | update_pull_request_branch | `pull_number` | YYY | vote | changes what the operation does |
| keep | add_issue_comment | `owner` | YYY | vote | picks what the call touches |
| keep | add_issue_comment | `repo` | YYY | vote | picks what the call touches |
| keep | add_issue_comment | `body` | YYY | vote | content written or sent |
| keep | create_branch | `owner` | YYY | vote | picks what the call touches |
| keep | create_branch | `repo` | YYY | vote | picks what the call touches |
| keep | create_branch | `from_branch` | YYn | vote | picks what the call touches |
| keep | create_issue | `owner` | YYY | vote | picks what the call touches |
| keep | create_issue | `repo` | YYY | vote | picks what the call touches |
| keep | create_issue | `title` | YYY | vote | content written or sent |
| keep | create_issue | `body` | YYY | vote | content written or sent |
| keep | create_or_update_file | `owner` | YYY | vote | picks what the call touches |
| keep | create_or_update_file | `repo` | YYY | vote | picks what the call touches |
| keep | create_or_update_file | `path` | YYY | vote | picks where the data ends up |
| keep | create_or_update_file | `content` | YYY | vote | carries the content written or sent |
| keep | create_or_update_file | `branch` | YYY | vote | picks what the call touches |
| keep | create_pull_request | `owner` | YYY | vote | picks what the call touches |
| keep | create_pull_request | `repo` | YYY | vote | picks what the call touches |
| keep | create_pull_request | `body` | YYY | vote | content written or sent |
| keep | create_pull_request | `head` | YYY | vote | picks what the call touches |
| keep | create_pull_request | `base` | YYY | vote | picks what the call touches |
| keep | create_pull_request_review | `owner` | YYY | vote | picks what the call touches |
| keep | create_pull_request_review | `repo` | YYY | vote | picks what the call touches |
| keep | create_pull_request_review | `body` | YYY | vote | content written or sent in review |
| keep | create_pull_request_review | `event` | YYY | vote | changes what the operation does |
| keep | create_pull_request_review | `comments` | YY? | vote | content written or sent in comments |
| keep | create_repository | `private` | YYY | vote | widens who can see it |
| keep | fork_repository | `owner` | YYY | vote | picks what the call touches |
| keep | fork_repository | `repo` | YYY | vote | picks what the call touches |
| keep | fork_repository | `organization` | YYY | vote | appears in special-value rule and affects asset reach |
| keep | get_file_contents | `owner` | YYY | vote | picks what the call touches |
| keep | get_file_contents | `repo` | YYY | vote | picks what the call touches |
| keep | get_file_contents | `path` | YYY | vote | picks what the call touches and carries content written or sent |
| keep | get_issue | `owner` | YYY | vote | picks what the call touches |
| keep | get_issue | `repo` | YYY | vote | picks what the call touches |
| keep | get_pull_request | `owner` | YYY | vote | picks what the call touches |
| keep | get_pull_request | `repo` | YYY | vote | picks what the call touches |
| keep | get_pull_request_comments | `owner` | YYY | vote | picks what the call touches |
| keep | get_pull_request_comments | `repo` | YYY | vote | picks what the call touches |
| keep | get_pull_request_files | `owner` | YYY | vote | picks what the call touches |
| keep | get_pull_request_files | `repo` | YYY | vote | picks what the call touches |
| keep | get_pull_request_reviews | `owner` | YYY | vote | picks what the call touches |
| keep | get_pull_request_reviews | `repo` | YYY | vote | picks what the call touches |
| keep | get_pull_request_status | `owner` | YYY | vote | picks what the call touches |
| keep | get_pull_request_status | `repo` | YYY | vote | picks what the call touches |
| keep | list_commits | `owner` | YYY | vote | picks what the call touches |
| keep | list_commits | `repo` | YYY | vote | picks what the call touches |
| keep | list_commits | `perPage` | YYY | vote | sets how much is read |
| keep | list_issues | `owner` | YYY | vote | picks what the call touches |
| keep | list_issues | `repo` | YYY | vote | picks what the call touches |
| keep | list_issues | `per_page` | YYY | vote | sets how much is read |
| keep | list_pull_requests | `owner` | YYY | vote | picks what the call touches |
| keep | list_pull_requests | `repo` | YYY | vote | picks what the call touches |
| keep | list_pull_requests | `per_page` | YYY | vote | sets how much is read |
| keep | merge_pull_request | `owner` | YYY | vote | picks what the call touches |
| keep | merge_pull_request | `repo` | YYY | vote | picks what the call touches |
| keep | push_files | `owner` | YYY | vote | picks what the call touches |
| keep | push_files | `repo` | YYY | vote | picks what the call touches |
| keep | push_files | `branch` | YYY | vote | picks what the call touches |
| keep | push_files | `files` | YYY | vote | sets how much is written |
| keep | push_files | `files[].path` | YYY | vote | content sent to another party |
| keep | push_files | `files[].content` | YYY | vote | content sent to another party |
| keep | search_code | `q` | YYY | vote | changes what code is searched, potentially reaching sensitive repositories |
| keep | search_code | `per_page` | YYY | vote | sets how much is read in one call, potentially exposing more code |
| keep | search_issues | `q` | YYY | vote | content sent to another party |
| keep | search_issues | `per_page` | YYY | vote | sets how much is read |
| keep | search_repositories | `query` | YYY | vote | changes what repositories are searched |
| keep | search_repositories | `perPage` | YYY | vote | sets how much is read per page |
| keep | search_users | `q` | YYY | vote | content written or sent |
| keep | search_users | `per_page` | YYY | vote | sets how much is read |
| keep | update_issue | `owner` | YYY | vote | picks what the call touches |
| keep | update_issue | `repo` | YYY | vote | picks what the call touches |
| keep | update_issue | `title` | YYY | vote | content written or sent |
| keep | update_issue | `body` | YYY | vote | content written or sent |
| keep | update_issue | `state` | YYY | vote | changes what the operation does |
| keep | update_pull_request_branch | `owner` | YYY | vote | picks what the call touches |
| keep | update_pull_request_branch | `repo` | YYY | vote | picks what the call touches |

## slack: 58 kept

keep 31 · should drop 10 · borderline 13 · record id 4

| verdict | tool | input | votes | decided by | reason |
|---|---|---|---|---|---|
| drop | channels_list | `query_targets` | YYY | vote | which fields the name filter matches |
| drop | channels_list | `sort` | nnn | check | sort order |
| drop | conversations_add_message | `content_type` | nnn | check | text or markdown rendering |
| drop | conversations_history | `include_activity_messages` | nnn | check | join and leave notices |
| drop | conversations_mark | `ts` | YYY | vote | read-marker position; routine metadata |
| drop | conversations_replies | `include_activity_messages` | nnn | check | join and leave notices |
| drop | conversations_search_messages | `filter_threads_only` | nnn | check | narrows to threads; never widens |
| drop | usergroups_create | `description` | nnn | check | free-text label |
| drop | usergroups_list | `include_count` | nnn | check | adds a member count |
| drop | usergroups_update | `description` | nnn | check | free-text label |
| borderline | channels_list | `query` | YYY | vote | filters the call, leaving it out widens the call |
| borderline | conversations_add_message | `thread_ts` | YYY | vote | changes what the operation does |
| borderline | conversations_search_messages | `filter_date_after` | YYY | vote | sets when or for how long |
| borderline | conversations_search_messages | `filter_date_before` | YYY | vote | sets when or for how long |
| borderline | conversations_search_messages | `filter_date_during` | YYY | vote | sets when or for how long |
| borderline | conversations_search_messages | `filter_date_on` | YYY | vote | sets when or for how long |
| borderline | conversations_unreads | `include_muted` | nYY | vote | widens who can see, join or change something |
| borderline | conversations_unreads | `mentions_only` | nYY | vote | scoping or filtering the call, when leaving it out widens the call |
| borderline | usergroups_create | `handle` | YYY | vote | content written or sent |
| borderline | usergroups_create | `name` | YYY | vote | content written or sent |
| borderline | usergroups_list | `include_disabled` | YYY | vote | widens who can see, join or change something |
| borderline | usergroups_update | `handle` | YYY | vote | changes how users mention the group, affecting visibility and access |
| borderline | usergroups_update | `name` | nnn | check | may indicate a change in access rights or roles that affects confidentiality |
| record-id | conversations_replies | `thread_ts` | YYY | vote | picks what the call touches |
| record-id | usergroups_me | `usergroup_id` | YYY | vote | picks what the call touches |
| record-id | usergroups_update | `usergroup_id` | YYY | vote | picks what the call touches |
| record-id | usergroups_users_update | `usergroup_id` | YYY | vote | picks what the call touches |
| keep | channels_list | `channel_types` | YYY | vote | picks what the call touches |
| keep | channels_list | `limit` | YYY | vote | sets how much is read |
| keep | channels_me | `channel_types` | YYY | vote | scoping or filtering the call |
| keep | channels_me | `limit` | YYY | vote | sets how much is read |
| keep | conversations_add_message | `blocks` | YYY | vote | content written or sent |
| keep | conversations_add_message | `channel_id` | YYY | vote | picks what the call touches |
| keep | conversations_add_message | `text` | YYY | vote | content written or sent |
| keep | conversations_history | `channel_id` | YYY | vote | picks what the call touches |
| keep | conversations_history | `limit` | YYY | vote | sets how much is read |
| keep | conversations_join | `channel_id` | YYY | vote | picks what the call touches |
| keep | conversations_leave | `channel_id` | YYY | vote | picks what the call touches |
| keep | conversations_mark | `channel_id` | YYY | vote | picks what the call touches |
| keep | conversations_replies | `channel_id` | YYY | vote | picks what the call touches |
| keep | conversations_replies | `limit` | YYY | vote | sets how much is read |
| keep | conversations_search_messages | `filter_in_channel` | YYY | vote | picks what the call touches |
| keep | conversations_search_messages | `filter_in_im_or_mpim` | YYY | vote | picks what the call touches |
| keep | conversations_search_messages | `filter_users_from` | YYY | vote | picks what the call touches |
| keep | conversations_search_messages | `filter_users_with` | YYY | vote | picks what the call touches |
| keep | conversations_search_messages | `limit` | YYY | vote | sets how much |
| keep | conversations_search_messages | `search_query` | YYY | vote | appears anywhere in the policy given below |
| keep | conversations_unreads | `channel_types` | YYY | vote | scoping or filtering the call |
| keep | conversations_unreads | `include_messages` | nnY | vote | determines whether to return actual messages or just a summary |
| keep | conversations_unreads | `max_channels` | YYY | vote | sets how much is read |
| keep | conversations_unreads | `max_messages_per_channel` | YYY | vote | sets how much is read |
| keep | usergroups_create | `channels` | YYY | vote | picks what the call touches |
| keep | usergroups_list | `include_users` | YYY | vote | changes what the operation does |
| keep | usergroups_me | `action` | YYY | vote | changes what the operation does |
| keep | usergroups_update | `channels` | YYY | vote | picks what the call touches |
| keep | usergroups_users_update | `users` | YYY | vote | changes who belongs to a user group, affecting access control and potentially sensitive information exposure |
| keep | users_search | `limit` | YYY | vote | sets how much is read |
| keep | users_search | `query` | YYY | vote | content written or sent can carry personal data |

## calendar: 164 kept

keep 89 · should drop 43 · borderline 26 · record id 6

| verdict | tool | input | votes | decided by | reason |
|---|---|---|---|---|---|
| drop | create-event | `attendees[].optional` | YnY | vote | optional or required attendee |
| drop | create-event | `attendees[].responseStatus` | nnn | check | pre-set RSVP status |
| drop | create-event | `reminders.overrides` | YYY | vote | reminder timing |
| drop | create-event | `reminders.overrides[].minutes` | YYY | vote | reminder timing |
| drop | create-event | `transparency` | YYY | vote | busy or free display |
| drop | create-event | `conferenceData.createRequest.requestId` | nnn | check | client request id |
| drop | create-event | `attachments[].mimeType` | nnn | check | file type label |
| drop | create-event | `source.url` | nnn | check | back-link label |
| drop | create-event | `duplicateSimilarityThreshold` | nnn | check | duplicate-detection tuning |
| drop | create-event | `allowDuplicates` | YnY | vote | duplicate-detection switch |
| drop | create-event | `workingLocationProperties.type` | YYY | vote | working-location kind |
| drop | create-event | `workingLocationProperties.officeLocation.buildingId` | YYY | vote | desk-booking detail |
| drop | create-event | `workingLocationProperties.officeLocation.floorId` | YYY | vote | desk-booking detail |
| drop | create-event | `workingLocationProperties.officeLocation.floorSectionId` | YYY | vote | desk-booking detail |
| drop | create-event | `workingLocationProperties.officeLocation.deskId` | YYY | vote | desk-booking detail |
| drop | create-events | `events[].attendees[].optional` | YnY | vote | optional or required attendee |
| drop | create-events | `events[].attendees[].responseStatus` | nnn | check | pre-set RSVP status |
| drop | create-events | `events[].reminders.overrides` | YYY | vote | reminder timing |
| drop | create-events | `events[].reminders.overrides[].minutes` | YYY | vote | reminder timing |
| drop | create-events | `events[].transparency` | YYY | vote | busy or free display |
| drop | create-events | `events[].conferenceData.createRequest.requestId` | nnn | check | client request id |
| drop | get-current-time | `account` | nYn | vote | the clock is the same for every account |
| drop | get-current-time | `timeZone` | YnY | vote | display time zone of a read |
| drop | get-freebusy | `timeZone` | nnn | check | display time zone of a read |
| drop | list-colors | `account` | nYn | vote | the color palette is the same for every account |
| drop | list-events | `timeZone` | nnn | check | display time zone of a read |
| drop | list-events | `privateExtendedProperty` | YYY | vote | extended-property filter; only narrows inside the chosen calendar |
| drop | list-events | `privateExtendedProperty[]` | YYY | vote | extended-property filter; only narrows inside the chosen calendar |
| drop | list-events | `sharedExtendedProperty` | YYY | vote | extended-property filter; only narrows inside the chosen calendar |
| drop | list-events | `sharedExtendedProperty[]` | YYY | vote | extended-property filter; only narrows inside the chosen calendar |
| drop | search-events | `timeZone` | nnn | check | display time zone of a read |
| drop | search-events | `privateExtendedProperty` | YYY | vote | extended-property filter; only narrows inside the chosen calendar |
| drop | search-events | `privateExtendedProperty[]` | YYY | vote | extended-property filter; only narrows inside the chosen calendar |
| drop | search-events | `sharedExtendedProperty` | YYY | vote | extended-property filter; only narrows inside the chosen calendar |
| drop | search-events | `sharedExtendedProperty[]` | YYY | vote | extended-property filter; only narrows inside the chosen calendar |
| drop | update-event | `reminders.useDefault` | nnn | check | reminder setting |
| drop | update-event | `reminders.overrides` | YYY | vote | reminder timing |
| drop | update-event | `reminders.overrides[].method` | nnn | check | reminder channel |
| drop | update-event | `reminders.overrides[].minutes` | YYY | vote | reminder timing |
| drop | update-event | `checkConflicts` | nnn | check | warn about overlaps or not |
| drop | update-event | `transparency` | YYY | vote | busy or free display |
| drop | update-event | `attachments[].title` | nYn | vote | attachment label |
| drop | update-event | `attachments[].mimeType` | nnn | check | file type label |
| borderline | create-event | `timeZone` | nnn | check | timezone affects when the event occurs globally |
| borderline | create-event | `attendees[].comment` | YYY | vote | content sent to another party |
| borderline | create-event | `attendees[].additionalGuests` | YYY | vote | sets how much |
| borderline | create-event | `conferenceData.createRequest.conferenceSolutionKey.type` | YYY | vote | picks what the call touches (conference solution) |
| borderline | create-event | `calendarsToCheck` | YYY | vote | picks what the call touches (calendar IDs) |
| borderline | create-event | `calendarsToCheck[]` | YYY | vote | picks what the call touches (individual calendar ID) |
| borderline | create-event | `eventType` | YYY | vote | changes what the operation does (type of event) |
| borderline | create-event | `focusTimeProperties.autoDeclineMode` | YnY | vote | changes how the call handles conflicts |
| borderline | create-event | `focusTimeProperties.declineMessage` | YYY | vote | content sent when declining invitations |
| borderline | create-event | `outOfOfficeProperties.autoDeclineMode` | YnY | vote | changes how the call handles conflicts |
| borderline | create-event | `outOfOfficeProperties.declineMessage` | YYY | vote | content sent when declining invitations |
| borderline | create-events | `timeZone` | nnn | check | Timezone affects event timing and attendee availability |
| borderline | create-events | `events[].timeZone` | nnn | check | Timezone affects event timing and attendee availability |
| borderline | create-events | `events[].conferenceData.createRequest.conferenceSolutionKey.type` | YYY | vote | changes the conference solution type, affecting event setup and access |
| borderline | get-event | `fields` | nnn | check | Retrieving attendee lists can expose sensitive information about who is involved in the event. |
| borderline | get-event | `fields[]` | nnn | check | Retrieving specific fields such as attendees can expose sensitive information about who is involved in the event. |
| borderline | get-freebusy | `groupExpansionMax` | YYY | vote | sets how much |
| borderline | get-freebusy | `calendarExpansionMax` | YYY | vote | sets how much |
| borderline | list-events | `fields` | nnn | check | Including specific fields can expose sensitive attendee data. |
| borderline | list-events | `fields[]` | nnn | check | Extended properties may include confidential information that affects risk. |
| borderline | search-events | `fields` | nnY | vote | adds fields to the search, potentially revealing more sensitive information |
| borderline | search-events | `fields[]` | nnY | vote | specific fields can reveal additional sensitive details about events |
| borderline | update-event | `timeZone` | YYn | vote | sets when or for how long |
| borderline | update-event | `calendarsToCheck` | YYY | vote | picks what the call touches |
| borderline | update-event | `calendarsToCheck[]` | YYY | vote | picks what the call touches |
| borderline | update-event | `conferenceData.createRequest.conferenceSolutionKey.type` | YYY | vote | changes what the operation does |
| record-id | create-event | `attachments[].fileId` | YYY | vote | ID of the attached file in Google Drive, picks what the call touches |
| record-id | delete-event | `eventId` | YYY | vote | picks what the call touches |
| record-id | get-event | `eventId` | YYY | vote | picks what the call touches |
| record-id | respond-to-event | `eventId` | YYY | vote | picks what the call touches |
| record-id | update-event | `eventId` | YYY | vote | picks what the call touches |
| record-id | update-event | `attachments[].fileId` | YYY | vote | picks what the call touches |
| keep | create-event | `account` | YYY | vote | picks what the call touches |
| keep | create-event | `calendarId` | YYY | vote | picks what the call touches |
| keep | create-event | `summary` | YYY | vote | content sent to another party |
| keep | create-event | `description` | YYY | vote | content sent to another party |
| keep | create-event | `start` | YYY | vote | sets when or for how long |
| keep | create-event | `end` | YYY | vote | sets when or for how long |
| keep | create-event | `location` | YYY | vote | content sent to another party |
| keep | create-event | `attendees` | YYY | vote | picks what the call touches |
| keep | create-event | `attendees[].email` | YYY | vote | picks what the call touches |
| keep | create-event | `recurrence` | YYY | vote | sets when or for how long |
| keep | create-event | `recurrence[]` | YYY | vote | sets when or for how long |
| keep | create-event | `visibility` | YYY | vote | widens who can see, join or change something |
| keep | create-event | `guestsCanInviteOthers` | YYY | vote | widens who can see or join the event |
| keep | create-event | `guestsCanModify` | YYY | vote | changes what attendees can do with the event |
| keep | create-event | `guestsCanSeeOtherGuests` | YYY | vote | widens who can see other attendees |
| keep | create-event | `anyoneCanAddSelf` | YYY | vote | widens who can join the event |
| keep | create-event | `sendUpdates` | YYY | vote | sends something out or notifies people |
| keep | create-event | `attachments` | YYY | vote | carries content written or sent |
| keep | create-event | `attachments[].fileUrl` | YYY | vote | URL of the attached file, carries content |
| keep | create-events | `account` | YYY | vote | picks what the call touches |
| keep | create-events | `calendarId` | YYY | vote | picks what the call touches |
| keep | create-events | `sendUpdates` | YYY | vote | sends something out or notifies people |
| keep | create-events | `events` | YYY | vote | sets how much |
| keep | create-events | `events[].start` | YYY | vote | sets when or for how long |
| keep | create-events | `events[].end` | YYY | vote | sets when or for how long |
| keep | create-events | `events[].calendarId` | YYY | vote | picks what the call touches |
| keep | create-events | `events[].account` | YYY | vote | picks what the call touches |
| keep | create-events | `events[].description` | YYY | vote | content written or sent |
| keep | create-events | `events[].location` | YYY | vote | picks what the call touches |
| keep | create-events | `events[].attendees` | YYY | vote | sends something out or notifies people |
| keep | create-events | `events[].attendees[].email` | YYY | vote | picks what the call touches |
| keep | create-events | `events[].recurrence` | YYY | vote | sets when or for how long |
| keep | create-events | `events[].recurrence[]` | ??Y | vote | sets when or for how long |
| keep | create-events | `events[].visibility` | YYY | vote | widens who can see the event |
| keep | create-events | `events[].guestsCanInviteOthers` | YYY | vote | widens who can invite others to the event |
| keep | create-events | `events[].guestsCanModify` | YYY | vote | changes attendees' ability to modify the event |
| keep | create-events | `events[].guestsCanSeeOtherGuests` | YYY | vote | widens who can see other attendees |
| keep | create-events | `events[].anyoneCanAddSelf` | YYY | vote | widens who can add themselves to the event |
| keep | create-events | `events[].sendUpdates` | YYY | vote | sends notifications out |
| keep | delete-event | `account` | YYY | vote | picks what the call touches |
| keep | delete-event | `calendarId` | YYY | vote | picks what the call touches |
| keep | delete-event | `sendUpdates` | YYY | vote | sends something out or notifies people |
| keep | get-event | `account` | YYY | vote | picks what the call touches |
| keep | get-event | `calendarId` | YYY | vote | picks what the call touches |
| keep | get-freebusy | `account` | YYY | vote | picks what the call touches |
| keep | get-freebusy | `calendars` | YYY | vote | picks what the call touches |
| keep | get-freebusy | `calendars[].id` | YYY | vote | picks what the call touches |
| keep | get-freebusy | `timeMin` | YYY | vote | sets when or for how long |
| keep | get-freebusy | `timeMax` | YYY | vote | sets when or for how long |
| keep | list-calendars | `account` | YYY | vote | picks what the call touches |
| keep | list-events | `account` | YYY | vote | picks what the call touches |
| keep | list-events | `calendarId` | YYY | vote | picks what the call touches |
| keep | list-events | `timeMin` | YYY | vote | sets when or for how long |
| keep | list-events | `timeMax` | YYY | vote | sets when or for how long |
| keep | manage-accounts | `action` | YYY | vote | changes what the operation does |
| keep | manage-accounts | `account_id` | YYY | vote | picks what the call touches |
| keep | respond-to-event | `calendarId` | YYY | vote | picks what the call touches |
| keep | respond-to-event | `account` | nnn | check | Different accounts can have different permissions and visibility, affecting risk |
| keep | respond-to-event | `response` | YYY | vote | changes what the operation does |
| keep | respond-to-event | `comment` | YYY | vote | content sent to another party |
| keep | respond-to-event | `modificationScope` | YYY | vote | changes what the operation does |
| keep | respond-to-event | `sendUpdates` | YYY | vote | sends something out or notifies people |
| keep | search-events | `account` | YYY | vote | picks what the call touches |
| keep | search-events | `calendarId` | YYY | vote | picks what the call touches |
| keep | search-events | `query` | YYY | vote | content written or sent |
| keep | search-events | `timeMin` | YYY | vote | sets when or for how long |
| keep | search-events | `timeMax` | YYY | vote | sets when or for how long |
| keep | update-event | `account` | YYY | vote | picks what the call touches |
| keep | update-event | `calendarId` | YYY | vote | picks what the call touches |
| keep | update-event | `summary` | YYY | vote | content sent to another party |
| keep | update-event | `description` | YYY | vote | content sent to another party |
| keep | update-event | `start` | YYY | vote | sets when or for how long |
| keep | update-event | `end` | YYY | vote | sets when or for how long |
| keep | update-event | `location` | YYY | vote | content sent to another party |
| keep | update-event | `attendees` | YYY | vote | picks what the call touches |
| keep | update-event | `attendees[].email` | YYY | vote | appears anywhere in the policy given below |
| keep | update-event | `recurrence` | YYY | vote | changes what the operation does |
| keep | update-event | `recurrence[]` | YYY | vote | changes what the operation does |
| keep | update-event | `sendUpdates` | YYY | vote | sends something out or notifies people |
| keep | update-event | `modificationScope` | YYY | vote | changes what the operation does |
| keep | update-event | `originalStartTime` | Ynn | vote | sets when or for how long |
| keep | update-event | `futureStartDate` | YnY | vote | sets when or for how long |
| keep | update-event | `visibility` | YYY | vote | widens who can see it |
| keep | update-event | `guestsCanInviteOthers` | YYY | vote | widens who can join or change something |
| keep | update-event | `guestsCanModify` | YYY | vote | widens who can join or change something |
| keep | update-event | `guestsCanSeeOtherGuests` | YYY | vote | widens who can see it |
| keep | update-event | `anyoneCanAddSelf` | YYY | vote | widens who can join or change something |
| keep | update-event | `attachments` | YYY | vote | carries the content written or sent |
| keep | update-event | `attachments[].fileUrl` | YYY | vote | picks what the call touches |

