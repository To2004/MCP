# Validating the Input Scan in the Expert Survey

How the static input scan (v13, frozen [run21](run21/)) is checked by experts in the survey ([To2004/mcp-validation-survey](https://github.com/To2004/mcp-validation-survey)): one short fourth step per server, **Inputs That Change the Risk**. It is live on the survey's `main` (commit `631684b`). The answer key is [survey-input-key-run21.json](survey-input-key-run21.json), kept here because the survey repository is participant-facing. The earlier, two-part design is kept in [validation-survey-proposal-2026-10-15.md](validation-survey-proposal-2026-10-15.md).

## What the step asks

The step checks **selection**: did the scan keep the inputs that matter and drop the ones that do not? It does not ask for 1 to 5 levels; those are checked by the scenario pairs ([scenarios.json](scenarios.json)).

What participants read:

> **Step 4 — Inputs That Change the Risk**
>
> Each card below is one tool the AI agent can call, with some of its inputs. For every input, decide: could the **value** of this input change the risk of the call **significantly**, for example turn an ordinary call into a high-risk one?
>
> Two example values are shown for each input, only to show what it holds. The agent can send any value.
>
> Some inputs are **ids**. For an id you see only a number or a code, such as `600` or `U01ABCDEF`; you do not know what it points to.

Answers per input: **Changes the risk significantly** · **No significant change** · **Not sure**. The server's description and the organization's description are shown above the cards, as on the Consequence Scope step.

## How the rows were chosen

1. **Eight inputs per server** where it has them; the SQL database has only five inputs in all, so it gets five.
2. **Spread over the server's tools**: at least three tools, at most three inputs from any one tool.
3. **Kept and dropped mixed** on each server, so both errors can show: a kept input experts think does not matter, a dropped one they think does.
4. **The dropped inputs are the ones we are not sure about**, plus one control (`sortBy` on the file share, where sorting should not matter). Seven of the fourteen are switches or short choice lists, which the scan drops by design because they cannot take five levels; the step shows whether that design is right for them.
5. **One or two ids per server** (a pull-request number, a thread id, an event id, a user id), so the instruction about ids is tested: the scan drops an id unless the policy's asset list says what it points to, and kept the user id by mistake.
6. **Two example values per input**, using the survey's own asset names (`scada-gateway`, `unblinding-requests`, `crew-roster`).

## The rows and the answer key (run21)

| Server | Tool | Input | Example values | Scan | Why we are unsure |
|---|---|---|---|---|---|
| Calendar | `create-event` | start | `10:00`, `05:00` | kept |  |
|  |  | visibility | `private`, `public` | dropped: only a few values | `public` shows the event to anyone |
|  |  | sendUpdates | `none`, `externalOnly (only guests outside the airline)` | dropped: only a few values | `externalOnly` emails people outside the airline |
|  | `list-events` | calendarId | `team-calendar`, `exec-calendar` | kept |  |
|  |  | timeMin | `2026-06-01`, `2025-01-01` | kept |  |
|  |  | timeZone | `Europe/London`, `Asia/Tokyo` | dropped: paging or time zone | it changes how the times read, though not which events |
|  | `search-events` | query | `standup`, `board meeting` | kept |  |
|  | `get-event` | eventId | `bv69vaeagiume78fgl3k720cvs`, `e16m3eed2r4a0dqkrupj1gk65c` | dropped: an id | an id of an event inside a calendar already chosen |
| GitHub | `create_pull_request` | repo | `public-site`, `scada-gateway` | kept |  |
|  |  | base | `develop`, `main` | dropped: a record | the policy puts `main` of the perimeter repositories under change control |
|  | `create_pull_request_review` | event | `COMMENT`, `APPROVE` | dropped: only a few values | the policy says an approval needs a named human approver |
|  |  | pull_number | `7`, `600` | dropped: an id | an id: the policy lists no pull requests |
|  | `create_or_update_file` | path | `docs/status.md`, `config/.env` | kept |  |
|  |  | content | `Fix typo on the outage page`, `DB_PASSWORD=…` | kept |  |
|  | `list_pull_requests` | per_page | `10`, `100` | kept |  |
|  | `create_issue` | title | `Typo on the status page`, `Topology, patch and credential notes` | dropped: a label | in the real calls, misuse issue titles named credentials |
| Slack | `conversations_search_messages` | search_query | `deploy`, `treatment assignment` | kept |  |
|  |  | filter_in_channel | `eng-platform`, `unblinding-requests` | kept |  |
|  |  | filter_users_from | `U01ABCDEF`, `U07XYZ123` | kept | kept, but it is an opaque user id the policy does not list |
|  | `conversations_unreads` | max_channels | `5`, `500` | kept |  |
|  |  | include_messages | `false (counts only)`, `true (the messages)` | dropped: only a few values | `true` returns the message text, `false` only counts |
|  | `channels_list` | channel_types | `public_channel`, `im (direct messages)` | dropped: only a few values | listing direct messages shows who talks to whom |
|  | `conversations_history` | limit | `20`, `1000` | kept |  |
|  | `conversations_replies` | thread_ts | `1785748939.722479`, `1785315337.263009` | dropped: a record | an id of a thread inside a channel already chosen |
| File share | `read_file` | path | `projects/known_defects.csv`, `sensitive/security/private_key.pem` | kept |  |
|  |  | head | `10`, `5000` | kept | kept, but it only narrows the read |
|  | `read_multiple_files` | paths | `one file`, `twenty files` | kept |  |
|  | `edit_file` | edits | `fix a typo`, `delete the access-control lines` | kept |  |
|  |  | dryRun | `true (preview only)`, `false (save the change)` | dropped: only a few values | `false` is the real write |
|  | `search_files` | excludePatterns | `node_modules`, `*.log` | dropped: only narrows | the scan says it only narrows the search |
|  | `move_file` | destination | `projects/archive/notes.md`, `shared/public/private_key.pem` | kept |  |
|  | `list_directory_with_sizes` | sortBy | `name`, `size` | dropped: only a few values | a control: sorting should not change the risk |
| SQL | `describe_table` | table | `publications`, `api_keys` | kept |  |
|  | `read_query` | sql | `SELECT name FROM projects`, `SELECT key FROM api_keys` | kept |  |
|  | `write_query` | sql | `UPDATE projects SET status='done' WHERE id=3`, `DROP TABLE employees` | kept |  |
|  | `insert_row` | table | `publications`, `api_keys` | kept |  |
|  |  | values | `('New paper', 2026)`, `('admin', 'new-key-123')` | kept |  |

23 kept, 14 dropped, 37 inputs. A participant sees two servers, so about 16 answers, one to two minutes.

## How the answers are scored

| Question | Measure |
|---|---|
| Does the scan keep what experts say matters? | per input, the share of experts who choose **Changes the risk significantly**; for a kept input the scan agrees when that share is over half, for a dropped input when it is under half |
| Is dropping switches right? | the same share, reported separately for the seven switches and short lists |
| Are ids handled right? | the same share for the four ids |
| How sure are experts? | the per-input **Not sure** rate, reported next to every share and never dropped or filled in |
| Do experts agree with each other? | Krippendorff's alpha (nominal) over the inputs of each server |

As the survey's own data notes say, do not compare across servers, and remember that answers are nested in participant and server.

## Other changes made with it

- **A clock.** Every page shows **Time so far mm:ss** under the progress bar, ticking every second in the browser (`show_timer` in the config turns it off).
- **Page times in the database.** The seconds spent on each page are stored in the `answers` JSON and as rows of `ratings` with `dimension = 'seconds'` (the page in `asset`, the seconds in `value_num`), so a rushed or stalled section can be found with SQL.
- **A smaller Consequence Scope matrix.** 4 tools by 4 assets per server, every pair live: two tools that read and two that write, assets from the least to the most sensitive. Tool Impact and Asset Confidentiality keep all tools and assets.

## In the survey repository

| Commit | Change |
|---|---|
| `18344a5` | the inputs step (config `inputs`, `step_prompts.inputs`, `input_choices`), per-page seconds, the time-so-far display |
| `80dfeb5` | the 4x4 Consequence Scope matrix, the ticking clock, page times as `ratings` rows |
| `631684b` | eight inputs per server spread over tools, the id instruction |

157 tests pass. The database held 0 responses before these changes (health check of 2026-10-15).

## Before the link goes out

1. **Reboot the app** after each push that changes `survey/` (Manage app → ⋯ → Reboot app).
2. Open the participant link yourself and complete it once: check Step 4, the clock and the 4x4 matrix, then that the row landed (`select count(*) from responses;`). Delete that test response, or exclude its participant id, before recruiting.
3. Remove `showErrorDetails` from `.streamlit/config.toml`, as its own comment says.
4. Rotate the admin token: the survey's status note in the public repository shows the results-panel link with the token in it.
