# The static tool-impact rules — every rule, explained

Where they live: **`src/mcp_security/static_scoring/static_impact.py`** (906 lines).

**What this is.** A deterministic classifier that assigns a tool its 1–5 impact
tier from the tool's own declaration — name, description, parameters, MCP
annotation hints — with **no model call**. It exists to test whether the impact
stage needs an LLM at all.

**Threat model.** Misuse of legitimate tools during normal operation. The
declaration is taken at face value; this is *not* looking for a malicious or
poisoned server. (Tool-poisoning and rug-pull detection were removed for exactly
this reason.)

**Design principle.** Impact is a property of the **action**, not of the asset
and not of the asset's value. "How much does it touch" is blast radius; "how much
is it worth" is sensitivity. Both are scored elsewhere.

---

## The ladder it assigns

| Tier | Means | Test |
|---|---|---|
| **1** No effect | the server talks about itself, not the data | ping, health, version, current time, whoami |
| **2** Metadata | about-ness: what exists, how it's organised, its state | listings, names, sizes, schema, permissions; also mark-read / star / pin / mute / rename |
| **3** Content read | the substance itself is disclosed, nothing changes | read, get, download, export, search-returning-content, analysis over data |
| **4** Reversible write | state changes and the system can undo it | create, insert, edit, move, membership change, post-inside-the-system |
| **5** Irreversible or open-world | no path back **from inside the system** | delete, wipe, complete overwrite, execute code, move money, or an action that **is** an outbound send (email/invite/broadcast) |

Tier 5 is not only "destructive" — a sent email is as unrecallable as a deleted
row, so leaving the system sits at the same tier as destroying inside it.

---

## The rules, in execution order

### Rule 1 · Annotation ceiling
```python
ceiling = 3 if read_only is True else 5
```
A tool declaring `readOnlyHint: true` **cannot exceed tier 3**, no matter what
verbs appear in its text. Per the MCP spec, `destructiveHint` and
`idempotentHint` are only meaningful when `readOnlyHint` is false, and all four
are *hints* — so annotations **bound** the answer but never push a tool to 5 on
their own.

### Rule 2 · Verb evidence — highest tier wins
260 word-boundary patterns across the five tiers, drawn from multiple domain
vocabularies (filesystem `rm/unlink/mkdir`, database `select/drop/truncate/upsert`,
VCS `clone/fork/merge/push/rebase`, messaging `post/pin/mute/invite`, infra
`provision/terminate/decommission`, payments `charge/refund/payout/settle`).
The tier is the **maximum** that fires, capped by Rule 1.

**The scope sub-rule — the single most important detail.** Words that are a verb
in a tool *name* but a noun in prose are matched **against the name only**
(101 of them: branch, fork, push, email, notify, generate, build, open, report,
key, index, clear, run…). Separators are normalised first (`push_files` →
`push files`) so word boundaries work.

Why: matching verbs across whole descriptions produced these real failures —
- `usergroups_list` scored **tier 5** because its prose says groups *"notify all members"*
- `users_search` scored **tier 5** because "email" is one of its *search fields*
- `list_commits` scored **tier 4** because "branch" appears as a *noun*

**No-evidence fallback:** nothing matched → tier 3 (a tool that declares nothing
is assumed to read content, not assumed harmless), or 5 if `destructiveHint`.

### Rule 2b · Container listings
A listing of **containers** (calendars, directories, repositories, channels,
tables, accounts, buckets, databases, groups, workspaces) is a catalog → stays 2.
A listing of anything else hands back the items themselves → resolves up to 3.
Under-scoring is the costlier error, so ambiguity resolves upward.

### Rule 3 · Return-shape caps
What a **read** returns bounds it from above. Applies only when tier ≤ 3, so a
cap can never lower a mutation.
- **cap 1** (matched in the **name only**): current time, ping, health, version,
  capabilities, whoami — a tool is a liveness probe when it is *named* one.
- **cap 2** (name + first sentence): free/busy, availability, schema, "list of
  \<containers\>", "available X", colour palette, mark-as-read, "metadata about".

Without this, *"**Get** the current time"* scores 3 purely because of the word
"get". The name-only scoping for cap 1 came from a real miss:
`get_user_portfolio_summary` scored **tier 1** because its description ended
*"…and stock analysis **capabilities**"*.

### Rule 3c · The object decides, when the verb does not
`get`, `search`, `fetch`, `retrieve`, `find`, `lookup`, `show`, `view`, `browse`
mean *"something comes back"* — they say nothing about **what**. When a tool
lands at tier 3 and its ONLY tier-3 evidence is one of these generic verbs, the
object is consulted, three ways:

1. **A stated return shape.** "Returns full paths…", "Each entry includes 'name',
   'type'…" → identifiers, not substance → **2**. Matched against the whole
   description (an explicit return statement is unambiguous wherever it sits),
   but the clause **stops at the first colon or newline** — otherwise a
   `Returns:` argument block leaks words like "type" and "count" from parameter
   names. A clause promising contents/body/text/values/records/rows/diff/patch
   never caps.
2. **A container object.** Searching or listing *containers* returns a catalog of
   names → **2**. Head-anchored: the container must be what the tool acts on —
   the tool name ends in it **and is plural** (`search_repositories` yes,
   `get_economic_calendar` no, that is a dataset named after a container), or it
   is the direct object of the opening verb. A container naming only the
   **scope** does not count: `search_code` "across GitHub repositories" stays 3.
3. **A name that is itself a listing.** `list_*`, `ls_*`, `enumerate_*`,
   `index_*` — the tool declares its return shape in its own name, so the "Get"
   in *"Get list of commits"* is just phrasing → **2**.

Why it was needed: `directory_tree`, `search_files`, `search_repositories` and
`list_commits` all fired *metadata* evidence (`directory`, `names`, `glob`,
`list`) and all scored 3 anyway, because the tier is the MAX and one generic verb
outranked it. None of them returns a byte of content.

Guard rails proved on the corpus: 4 tools moved 3 → 2 on the five servers (all
four now match the LLM), **0** of 196 finance tools moved, and
`get_key_metrics` / `get_insider_transactions` / `get_strategy_performance` —
which have incidental tier-2 words but genuinely return values — all stay 3.

### Rule 3b · Create-or-overwrite
`create_or_update` / "create or overwrite|replace" in one tool → **5**. One call
can either make a new item or replace an existing one wholesale.

### Rule 4 · Scoped-edit exception
A tier-5 that also says the edit is partial and reconstructable — *line-based,
partial, specific fields, diff, appends to, leaves the rest, selective* — drops
to **4**, unless a genuine delete/remove/purge verb also fired. The prior state
survives in the diff.

### Rule 5 · destructiveHint corroboration
If `destructiveHint: true`, the tool isn't read-only, the tier landed at 4, **and**
a tier-5 verb fired → **5**. Corroboration only; the hint alone never decides.

### Rule 6 · Bulk detection (flag only)
An array-typed parameter or bulk wording (bulk, batch, multiple, several, in one
call) sets `is_bulk`. **It does not change the tier** — the "+1 for dropping a
safety" rule was removed on request. Bulk-vs-singular dominance is enforced
separately, in the pipeline's bulk-twin pass.

### Rule 7 · Parameter signals — flags only, never a tier
Danger often lives in the **inputs**, not the verb. Nine signals, each recorded
as a capability flag. **None of them moves the tier.**

| Signal | Meaning |
|---|---|
| `raw-command` | a `cmd`/`script`/`code`/`exec` parameter |
| `raw-query` | a `sql`/`query`/`statement` parameter |
| `outbound` | `send_updates`/`notify`/`webhook`/`recipients`/`cc`/`bcc` |
| `path` | a filesystem path parameter |
| `recursive` | descends a subtree |
| `glob` | a pattern selects many items |
| `force` | a force/overwrite switch removing a safety |
| `unbounded` | caller controls result volume |
| `dry-run` | offers a preview → the real call is consequential |

Any `path`/`raw-query`/`raw-command` parameter with **no enum, pattern or format**
is additionally marked *unconstrained*.

**Why they only describe.** A parameter states what the caller *could* pass; what
a given call *does* pass is a runtime fact. `write_query` is tier 5 because its
description says "INSERT, UPDATE, DELETE", not because it has a `query`
parameter — the same parameter on `read_query` ("read-only SELECT") leaves it at
3. Pricing the argument itself is the **dynamic** stage's job.

One bug still shaped these patterns: they are **full-name anchored**. An
unanchored alternation made `cc` match inside `a(cc)ount`, turning every calendar
read into an outbound-messaging tool (tier-5 count across the corpus: 51 → 20).

### Rule 8 · ~~openWorldHint~~ — removed, moved to dynamic
`openWorldHint` is **not read by this module**. It used to promote a tier-4 write
to 5 ("a write that reaches outside is unrecallable"), which is why calendar's
`create-event`/`update-event`/`create-events` scored **5** here and **4** from
the LLM.

Removed because it is a *possibility*, not an action: whether a call actually
leaves the system depends on the request (was `sendUpdates` set? was there an
external recipient?). That is a runtime fact, so the **dynamic stage** prices it.
The hint is still parsed onto `ToolSpec` so the dynamic scorer can consume it.

A tool still reaches tier 5 when its declared **action** is an outbound send —
`send_message`, `invite_user` — because that is what it does on every call.

### Rule 8a · `push` is tier 4; only `force-push` is tier 5
`push` used to sit in the tier-5 publish family next to `deploy`/`release`.
A plain push **appends** commits — the prior history is intact and `git revert`
undoes it from inside the system, which is the tier-4 test. The genuinely
irreversible variant is `force-push`, which rewrites history and discards
commits, and it had **no entry of its own** — it scored 5 only because it
contains the substring "push".

Now: `\bpush\b` is tier 4, and `force-push` / `push --force` / `push -f` are
tier 5. `merge`, `rebase`, `deploy`, `release` and `publish` are unchanged.

### Rule 8b · "empty" is only destructive as a verb
`\bempty\b` sat in the tier-5 destroy family and matched *"a children array
which may be **empty**"* — an adjective. `directory_tree` fired **tier 5** on it
and was saved only by its `readOnlyHint`. Now only `empties` and
`empty the/all/a/an/this/out` count; `empty_trash` is still 5.

### Rule 9 · Negation guard (applied during Rule 2)
A verb preceded by *never / not / don't / cannot / avoid / without / must not*
within the same clause is a **prohibition, not a capability**.

Real case: `sec-edgar-mcp` scored six read-only tools as tier-4 writes because
their descriptions instruct the model — *"ONLY use data returned from SEC
records. **NEVER add** external information."* After the guard, all 21 tools
correctly score 3.

This matters generally: **MCP descriptions are increasingly written as prompts to
an agent rather than as API documentation**, so verb matching must be scoped.

### Rule 10 · Confidence
Not a tier rule — a self-report on evidence quality:
- **0.35** no verb matched (the tier is a default, not a finding)
- **0.8** an explicit tier verb fired
- **+0.15** an annotation corroborated

This is diagnostic machinery: filtering for low confidence is what exposed that
`insert`, `clear`, `flush` and `reset` were missing from the verb tables
entirely. Unclassified tools fell from 32 → 15 of 270 once they were added.

---

## What it does *not* do

- It does not look at the asset — impact is asset-independent by design.
- It does not detect malicious tools, poisoned descriptions or rug pulls (out of
  scope: misuse, not attack).
- It does not price boundary crossing from an *annotation* or a *parameter*
  (`openWorldHint`, `sendUpdates`) — only from the declared action. Whether a
  particular call actually reaches outside is a dynamic-stage judgement.
- It cannot infer **unstated** side effects. The LLM scored `respond-to-event` 5
  reasoning that an RSVP emails the organiser; the description never says so, so
  the rules say 4. That is the honest ceiling of reading a declaration.

## How well it works

Against the v3 LLM impacts: **83 % exact, 100 % within ±1** (69 tools).
Per server in a like-for-like run: sqlite **0/5** disagreements, fs 2/14,
slack 2/16, calendar 3/13 — and every disagreement is a judgement call of the
kind above, not an error.
