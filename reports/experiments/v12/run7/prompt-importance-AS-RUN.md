<!-- sha256: a79263f952b06259c2aa9a6748bc57d32642868e6ee4501bdd46fa96fd0c8d6e · source: docs/standards/tool-input-importance.md -->

# Tool Input Importance

The v12 stage 1 prompt. For one MCP tool, decide which of its inputs really drive the risk of a call, so that only those get run-time rules in stage 2. Most tools have a few inputs that decide almost everything (which repository, how much money, who receives it) and many that do not matter even at their most extreme value (a reminder time, a color, a label). Keep the first kind and drop the second.

## What you are given

You are analyzing one MCP tool. You get:

- the tool name and description;
- every declared input, with its description and schema facts (type, format, enum values, minimum, maximum, whether it is required, default);
- optionally, the organization's policy rows for this tool: a short org context, the normal workflow, the assets this tool can reach (with a description of why each matters), special-value rules and baseline rows. Any part may be empty.

Use the whole tool as context. The purpose of the tool and the sibling inputs decide what an input means.

## The test: compare the extremes

For each input, imagine two calls of this tool that are identical except for this input:

- one with the **safest** realistic value: the smallest amount, the shortest window, the least sensitive target, the most private setting;
- one with the **riskiest** realistic value: the largest amount, the longest window, the most sensitive target, an outside recipient, the most open setting.

Keep the input only if the riskiest call is **clearly** riskier than the safest one. Think of a five-step scale from safe (1) to critical (5), where an ordinary call is 3. Keep the input if the riskiest value could move the call at least two steps above the safest one: an ordinary call that becomes critical. If the difference is one step or less, or only matters in an unusual corner case, drop it.

- An amount of money: the riskiest value is a very large transfer. Clearly riskier: keep.
- A choice between black and white: both extremes give the same call: drop.
- A repository name: the riskiest value is the most sensitive repository, the safest a public one. Clearly riskier: keep.
- A page number: page 1 and page 500 return the same kind of data: drop.

For an input that names a target (a repository, a channel, a calendar, a person), the extremes are the most and the least sensitive target the call could name, not a number.

How sure you must be depends on the kind of input:

- an input of a kind listed under **Usually important** is kept unless you are sure that even its riskiest value leaves the call about as risky as its safest;
- an input of a kind listed under **Usually not important** is dropped unless the tool's description or the policy gives a specific reason it matters here;
- for any other input, apply the test as written.

## Usually important

These kinds of input usually pass the test:

1. **The target the call reads, writes or sends to**: the repository (with its owner), the file path or folder, the channel, the calendar, the database or table, the account selector that decides which linked account is used, the person whose messages or data are searched, a destination or recipient outside the organization.
2. **A quantity that can reach bulk**: an amount, a limit, a page size, a count, the number of items or recipients in a list.
3. **When the action itself happens, or how long a window it covers**: the start and end of an event, the start and the end of the window a read covers (both inputs), a recurrence that repeats a change or a change to every future occurrence.
4. **Who can see, join or change something**: public or private, visibility, guests can invite others, guests can modify, guests can see other guests, anyone can add themselves, including private channels or direct messages.
5. **Sending something out**: send updates, notify attendees, post, invite, publish.
6. **Turning one operation into a different, stronger one**: join or leave, approve, one event or all events, read or write.
7. **The main content written, sent or executed**: the file body, the message text, the issue or comment body, an executed query, a search query.
8. **A scope filter whose absence widens the call to the whole workspace or organization**: the channel filter on a workspace-wide search.
9. **An input the policy names** in a special-value rule or a baseline row, or that decides which listed asset is reached. These are always kept: the organization has said they matter.

## Usually not important

These kinds of input usually fail the test. Drop them unless the tool's description or the policy gives a specific reason they matter here:

- **a record id inside a target the call has already chosen**: an issue number, a pull request number, an event id, a comment id, a message timestamp, a commit to start from. The repository, calendar or channel already decides how sensitive the call is; which record inside it barely changes that, and no rule could tell a risky id from a safe one;
- **secondary text next to the main content**: a title, a commit message, a description, a display name, the name of a new object, a decline message, a comment on an RSVP. The exception: the policy says this text is sensitive (an event title on an executive calendar that discloses an unannounced decision);
- **pagination and ordering**: a page number, an offset, a cursor, a sort field, a sort direction;
- **presentation**: output format, rendering type, colors, icons, a time zone that only changes how times are displayed, which extra fields to return when they hold nothing beyond what the call already reaches;
- **bookkeeping**: client request ids, idempotency keys, a SHA copied from an earlier reply for a safety check, duplicate-detection settings, conflict-check switches;
- **organizational tags**: labels, milestones, categories, colors of events;
- **personal convenience**: reminders and their timing or channel, busy or free display, focus or working-location details such as a building, floor or desk;
- **narrowing filters inside a chosen target**: a label filter, a property filter, threads only, mentions only. They only make the call return less;
- **counts-only toggles**: include a member count, include activity notices.

## Rules

1. Describe every declared input exactly once, including nested ones, using a dotted path with `[]` for list items (`files[].path`). Describe none that the tool does not declare.
2. If an input is an array whose length is a count of targets or recipients, describe the array itself too.
3. A tool with many similar inputs, such as a list of events each carrying a start, an end and attendees, repeats the same kinds of input. Give every copy of the same kind the same answer, and the same answer a single-item tool of the same family would get.
4. Two inputs that only pick the target together (an owner and a repository name) are both important or both not.
5. `important` is `true` or `false`.
6. `reason` is one short sentence. For `true`, name the riskiest value and what it would touch. For `false`, say why even the riskiest value does not change the call much.
7. Never put a quotation mark inside any string value. Paraphrase instead of quoting.

## Examples

These show the reasoning only. Judge the real tool below from its own text.

| Tool and input | Important | Why |
|---|---|---|
| send_money `amount` | yes | a very large transfer is critical, a small one ordinary |
| send_money `recipient_account` | yes | an outside account is critical |
| send_money `currency` | no | the same transfer in another currency is about as risky |
| send_money `memo`, free text | no | secondary text next to the amount and recipient |
| set_theme `color`, black or white | no | both extremes give the same call |
| export_records `database_id` | yes | the most sensitive database is critical, a test one ordinary |
| export_records `limit`, 1 to 10000 | yes | ten thousand records at once is bulk |
| export_records `format`, csv or json | no | presentation |
| list_items `page`, integer | no | pagination |
| get_issue `issue_number` | no | the repository already decides how sensitive the call is |
| update_issue `labels` | no | organizational tags |
| create_event `reminder_minutes` | no | personal convenience |
| create_event `attendees[].email` | yes | an outside attendee receives an invitation from the organization |
| create_event `title`, policy says exec titles disclose decisions | yes | the policy names it |
| commit_file `message` | no | secondary text next to the file content |
| commit_file `content` | yes | a committed secret is critical |
| move_file `destination` | yes | a folder outside the protected area is critical |
| create_repo `private`, boolean | yes | a public copy of private code is critical |
| search `channel_filter`, optional | yes | leaving it out searches every channel |
| update_event `scope`, this event or all events | yes | changing every occurrence is far bigger than one |

## Output

Output ONLY valid JSON, no prose, no code fences:

```json
{"tool_name": "<name>", "arguments": [
  {"path": "<input path>",
   "important": true,
   "reason": "<one short sentence>"}
]}
```

Some large tools are given in more than one batch, each batch with only its own inputs but the full tool description. Describe only the inputs present below.

Tool: `{tool_json}`

Inputs: `{inputs_json}`

Policy for this tool (may be empty): `{policy_json}`