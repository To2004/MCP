# The nine tool-impact disagreements — what each one actually is

Static rules vs the LLM, across 74 tools on five servers. 65 agree. These nine do
not. For each: the declaration the classifier saw, why the rules landed where they
did, and **who is right**.

Verdict summary — the rules are wrong on 4, the model is wrong on 2, and 3 are
genuine judgement calls where the declaration does not settle it.

> **Status: 4 of the 4 rule bugs in the "metadata" family are FIXED** (Rule 3c
> and the `empty` fix in [STATIC_RULES.md](STATIC_RULES.md)). `directory_tree`,
> `search_files`, `search_repositories` and `list_commits` now score **2**.
> Agreement went 65/74 → 69/74. **`push_files` is also fixed** — `push` moved to
> tier 4 and `force-push` got its own tier-5 entry (Rule 8a) — taking agreement
> to **70/74 (95 %)**, with zero regressions on the 196-tool finance corpus.
>
> **`usergroups_me` is left at 5 by decision**, not by oversight: `remove` stays
> destructive everywhere rather than being taught a membership exception.

| tool | LLM | static | who is right | root cause |
|---|--:|--:|---|---|
| `usergroups_me` | 4 | **5** | **LLM** | `remove` matched as destroy; it is "remove yourself from a group" |
| `push_files` | 4 | **5** | **LLM** | plain `push` sits in tier 5 next to `force-push` |
| `directory_tree` | 2 | **3** | **LLM** | generic `get` verb; the return shape (names+types) isn't capped |
| `search_files` | 2 | **3** | **LLM** | `search` is tier 3 even when it returns *paths* |
| `search_repositories` | 2 | **3** | **LLM (weak)** | `search` doesn't get the container-noun treatment `list` gets |
| `get_pull_request_files` | **2** | 3 | **static** | GitHub returns the patch — that is content |
| `conversations_leave` | **5** | 4 | **static (weak)** | a private channel is not self-rejoinable |
| `list_commits` | 2 | 3 | toss-up | "get list of" — enumeration or content? |
| `search_users` | 2 | 3 | toss-up | GitHub profiles are public; Slack user search returns emails |

---

## The four the rules get wrong

### 1. `usergroups_me` — 5, should be 4
> *"Manage your own user group membership. Use action='join' with a usergroup_id
> to add yourself to a group. Use action='leave' with a usergroup_id to **remove**
> yourself."*

Evidence chain: `tier-5 verbs: \bremove\b`.

`leave` also fired at tier 4, but the max wins, so `remove` decided it. The word
is there — but it is **"remove yourself from a group"**, which is precisely the
tier-4 membership family, and the same description states the inverse operation
(`action='join'`) two sentences earlier. Nothing is destroyed; you can rejoin.

This is a **clear false positive**. `remove` is genuinely a destroy verb
(`remove_file`) and genuinely a membership verb (`remove_member`,
`remove yourself`). Tier 5 assumes the first reading unconditionally.

**Fix**: a membership-scoped exception, structurally identical to the existing
scoped-edit exception — when a tier-5 hit is `remove` and the object is a
membership (`remove yourself`, `remove a member/user`, `remove from a
group/channel/team`), drop to 4. Applies only to `remove`, only with that object.

### 2. `push_files` — 5, should be 4
> *"Push multiple files to a GitHub repository in a single commit"*

Evidence chain: `tier-5 verbs: \bpush\b`.

`push` sits in the tier-5 "execute / publish" family alongside `deploy`,
`release`, `publish`, `merge` and `force-push`. But a **plain push is additive**:
it appends commits, the previous history is intact, and `git revert` undoes it
from inside the system. That is the definition of tier 4.

What is genuinely irreversible is **`force-push`**, which rewrites history and
discards commits. Lumping the two together is the error — they are the textbook
example of a reversible and an irreversible version of the same operation.

**Fix**: move plain `\bpush\b` to tier 4; keep `force-push` / `push --force` /
`push -f` at tier 5. Note `deploy`, `release` and `publish` should stay at 5 —
those genuinely leave the system.

### 3 & 4. `directory_tree` and `search_files` — 3, should be 2
> `directory_tree`: *"Get a recursive tree view of files and directories as a JSON
> structure. Each entry includes 'name', 'type' (file/directory), and 'children'…"*
>
> `search_files`: *"Recursively search for files and directories matching a
> pattern… Returns full paths to all matching items."*

Evidence: `readOnlyHint=true -> ceiling 3; tier-3 verbs: \bget\b` and
`\bsearch\b`.

Both descriptions **state their own return shape**, and in both cases it is
about-ness: names, types, children; full paths. Neither returns a byte of file
content. That is tier 2 by definition — and both descriptions say so explicitly.

The rules have machinery for exactly this (Rule 3's cap-2 markers, which already
carry *"listing of all files and directories"* and *"distinguish between files and
directories"*) — these two phrasings simply aren't in the list. The cap didn't
fail conceptually; its vocabulary is short.

**Fix**: add cap-2 markers for the shapes these state — `tree view of files and
directories`, `returns full paths`, `matching paths`, and the
`'name'…'type'…'children'` JSON-shape phrasing.

This is the safest fix of the four: caps only ever apply at tier ≤ 3, so no
mutation can be lowered by it.

---

## The two the model gets wrong

### 5. `get_pull_request_files` — LLM 2, static 3
> *"Get the list of files changed in a pull request"*

Reading the declaration alone, the model is right: "the list of files changed" is
an enumeration. But **GitHub's PR-files endpoint returns the `patch` field** — the
actual diff hunks, i.e. the changed source. The tool discloses content.

The rules land on 3 for the wrong reason (the generic verb `get`), but 3 is the
right answer. Worth noting as the one case where the rules' bias toward the
higher tier paid off.

### 6. `conversations_leave` — LLM 5, static 4
> *"Leave a channel, group conversation, or DM. Cannot leave the #general channel."*

The rules call this a reversible membership change (tier 4), and for a **public**
channel that is exactly right — rejoin whenever.

For a **private** channel or a group DM it is not. You cannot re-add yourself;
someone else must re-invite you. The capability is *gone* from the actor's side,
which is the ladder's own test for irreversibility. And the tool covers all three
cases in one call, so the ladder's "a tool spanning tiers takes the highest it
reaches" rule points at 5.

The model's answer is defensible and the rules' is defensible-but-optimistic. I'd
leave it: fixing it means teaching the rules that "leaving a private container is
one-way", which is a lot of specificity for one tool.

---

## The three genuine toss-ups

### 7. `list_commits` — *"Get list of commits of a branch"*
`list` fired at tier 2, `get` at tier 3, max wins. Commit *metadata* (sha, author,
date) is tier 2; commit *messages* are prose that routinely contains substance.
Both readings are honest. The deeper issue is that **`get` is a nearly contentless
verb** — "get file contents" is tier 3, "get list of names" is tier 2, and only
the object distinguishes them.

### 8. `search_users` — *"Search for users on GitHub"*
GitHub user search returns public profiles → metadata → 2. But the identical
phrasing on Slack (`users_search`) returns **email addresses**, which is PII
content → 3. Same words, different answer, and the tool declaration cannot tell
you which. This is precisely where the org profile — not the tool text — has to
carry the meaning.

I would **not** "fix" this one: making `users` a container noun would silently
lower Slack's user search too, which is the more sensitive of the two.

### 9. `search_repositories` — *"Search for GitHub repositories"*
The weakest of my "LLM is right" calls. `repositories` **is** already in the
rules' container-noun list, and Rule 2b uses that list to decide whether a
*listing* returns a catalog or its items. But 2b only fires on listing verbs;
`search` is hard-coded at tier 3, so it never consults the container check.

Searching for containers returns a catalog of container names — the same thing
`list_repositories` would return. The rules treat the two differently only because
of which verb was used.

**Fix**: let the container-noun check apply to `search` as well as `list`.
Moderate risk: `search_files` returns paths (fine, 2), but `search_messages` or
`search_code` return content and must stay 3 — the container-noun gate handles
that, since `messages` and `code` are not container nouns.

---

## What the pattern says

Seven of the nine cluster into two recurring problems, neither of them exotic:

1. **The generic verb problem** (`get`, `search`, `remove`, `push`). These words
   name an operation whose tier depends entirely on the object. The rules already
   solve this in two places — the ambiguous-word set (name-only scoping) and the
   container-noun check — but each solution is wired to one specific rule instead
   of being applied wherever the same verb appears.
2. **Reversible/irreversible twins** (`push` vs `force-push`, `remove yourself`
   vs `remove file`). The same verb names both a tier-4 and a tier-5 operation,
   and the tier-5 reading wins by default.

Both are addressable without new concepts — they reuse machinery that already
exists in the file. Applying the four fixes would take agreement from **65/74
(88 %) to 69/74 (93 %)**, with the remaining five being cases where the tool's own
declaration genuinely does not contain the answer.
