"""Deterministic tool-impact classification — the v4 "can we drop the LLM?" test.

Tool impact is meant to be a property of the ACTION ALONE: what one call does,
independent of the asset it touches or how valuable that asset is. If that is
true, the same 1-5 ladder the LLM applies should be derivable from the tool's own
declaration — its MCP annotations plus its description — with no model at all.

This module implements exactly the ladder in
``reports/experiments/v4/scoring-prompts.md`` as rules:

    1 NO EFFECT     liveness / session facts only
    2 METADATA      about-ness: names, ids, counts, listings; or consumption state
    3 CONTENT READ  returns the substance itself
    4 REVERSIBLE WRITE  create / append / scoped edit / move / membership change
    5 IRREVERSIBLE OR OPEN-WORLD  delete, full overwrite, execute, send outside

Evidence precedence, mirroring the prompt's own rules:

1. **MCP annotations first, but only as far as the spec licenses.** Per the MCP
   tool-annotation spec, ``destructiveHint`` and ``idempotentHint`` are only
   meaningful when ``readOnlyHint`` is false, and every field is a HINT — an
   untrusted server may misstate them. So annotations bound the tier
   (read-only ⇒ ≤ 3) but never by themselves push a tool to 5.
2. **Description verbs decide within that bound**, highest tier wins — the same
   "a tool spanning tiers takes the HIGHEST it reaches" rule the prompt states.
3. **Parameters describe, they do not decide.** A raw-query/command parameter, a
   send/notify parameter or an unconstrained path is recorded as a capability
   flag and nothing more. A parameter states what the caller COULD pass; what
   any given call DOES pass is a runtime fact.

What this module deliberately leaves to the DYNAMIC stage: whether a call
actually crosses the system boundary. ``openWorldHint`` is not read here and a
send/notify parameter does not raise the tier — both describe a possibility that
only a specific request can realise. A tool still reaches tier 5 when its own
declared ACTION is an outbound send (``send_message``, ``invite_user``), because
that is what the tool does on every call.

Every classification returns the evidence that set it, so a static score is as
auditable as a logged LLM answer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Verb/phrase evidence per tier. Order matters only for reporting; the score is
# the MAX tier whose evidence fires (the prompt's "highest tier it reaches").
# Phrases are matched against name + description, word-boundary anchored.
_TIER_PATTERNS: dict[int, tuple[str, ...]] = {
    # ---- 1 · NO EFFECT — the server talks about itself, not about the data ----
    1: (
        r"\bping\b",
        r"\bhealth(check)?\b",
        r"\bheartbeat\b",
        r"\bliveness\b",
        r"\breadiness\b",
        r"\becho\b",
        r"\bwhoami\b",
        r"\bcurrent[- ]time\b",
        r"\bserver time\b",
        r"\bnow\b",
        r"\bversion\b",
        r"\bcapabilit(y|ies)\b",
        r"\buptime\b",
        r"\bdiagnostics?\b",
        r"\bnoop\b",
        r"\bnop\b",
    ),
    # ---- 2 · METADATA — about-ness: what exists, how it is organised, its state
    # Reads that return names/shape, and writes that change only consumption
    # state or a label. Vocabulary spans: fs (stat, ls), db (describe, schema),
    # VCS (blame? no — that reads content), messaging (mark read, pin, mute).
    2: (
        # listing / enumerating
        r"\blist\b",
        r"\bls\b",
        r"\benumerate\b",
        r"\bindex\b",
        r"\bcatalog(ue)?\b",
        r"\bbrowse\b",
        r"\bdirectory\b",
        r"\bdir\b",
        r"\bglob\b",
        r"\bwalk\b",
        r"\bdiscover\b",
        r"\binventory\b",
        r"\bregistry\b",
        # shape / attributes
        r"\bmetadata\b",
        r"\bschema\b",
        r"\bdescribe\b",
        r"\bstat\b",
        r"\bsizes?\b",
        r"\bcounts?\b",
        r"\bnames?\b",
        r"\bids?\b",
        r"\btimestamps?\b",
        r"\bpermissions?\b",
        r"\battributes?\b",
        r"\bexists\b",
        r"\bcolumns?\b",
        r"\bfields?\b",
        r"\bkeys?\b",
        r"\bheaders?\b",
        r"\bstatus\b",
        r"\bfree.?busy\b",
        r"\bavailability\b",
        r"\bquotas?\b",
        r"\busage\b",
        # consumption state / labelling (a write, but only about-ness)
        r"\bmark (as )?(read|unread|seen)\b",
        r"\backnowledge\b",
        r"\bstar\b",
        r"\bunstar\b",
        r"\bpin\b",
        r"\bunpin\b",
        r"\bmute\b",
        r"\bunmute\b",
        r"\bflag\b",
        r"\bfollow\b",
        r"\bunfollow\b",
        r"\bwatch\b",
        r"\bunwatch\b",
        r"\brename\b",
        r"\breact(ion)?\b",
        r"\bemoji\b",
    ),
    # ---- 3 · CONTENT READ — the substance itself is disclosed ----------------
    # fs: read/cat/tail; db: select/query; VCS: blame/diff/show; mail: fetch.
    3: (
        r"\bread\b",
        r"\bcat\b",
        r"\btail\b",
        r"\bget\b",
        r"\bfetch\b",
        r"\bdownload\b",
        r"\bexport\b",
        r"\bdump\b",
        r"\bextract\b",
        r"\bsearch\b",
        r"\bquery\b",
        r"\bfind\b",
        r"\blookup\b",
        r"\bselect\b",
        r"\bgrep\b",
        r"\bscan\b",
        r"\bview\b",
        r"\bshow\b",
        r"\bdisplay\b",
        r"\bretrieve\b",
        r"\bopen\b",
        r"\bpreview\b",
        r"\binspect\b",
        r"\bcontents?\b",
        r"\bbody\b",
        r"\btext\b",
        r"\bpayload\b",
        r"\bhistor(y|ies)\b",
        r"\btranscripts?\b",
        r"\breplies\b",
        r"\bthread\b",
        r"\bdetails?\b",
        r"\bdiff\b",
        r"\bblame\b",
        r"\bsummar(y|ise|ize)\b",
        r"\banaly[sz](e|es|ed|ing|is)\b",
        r"\breport\b",
        r"\bcompare\b",
        r"\bcalculate\b",
        r"\bcompute\b",
        r"\bsimulat(e|ion)\b",
        r"\bbacktest\b",
        r"\bforecast\b",
        r"\bresearch\b",
        r"\bevaluate\b",
        r"\bscreen(er|ing)?\b",
    ),
    # ---- 4 · REVERSIBLE WRITE — state changes the system itself can undo -----
    # Same operation, different vocabularies: create/add/insert/new/make/mkdir,
    # update/edit/modify/patch/set/put/upsert, move/rename-to/relocate/mv,
    # membership: join/leave/grant/revoke/assign/invite (internal), lifecycle:
    # open/close/archive/restore/enable/disable/schedule.
    4: (
        # bring into existence
        r"\bcreate\b",
        r"\badd\b",
        r"\bnew\b",
        r"\bmake\b",
        r"\bmkdir\b",
        r"\binsert\b",
        r"\bappend\b",
        r"\bupload\b",
        r"\bimport\b",
        r"\bregister\b",
        r"\bprovision\b",
        r"\ballocate\b",
        r"\bdraft\b",
        r"\bgenerate\b",
        r"\bbuild\b",
        r"\bclone\b",
        r"\bduplicate\b",
        r"\bcopy\b",
        r"\bfork\b",
        r"\bbranch\b",
        r"\bsnapshot\b",
        r"\bstage\b",
        # a push APPENDS commits: the prior history is intact and `git revert`
        # undoes it from inside the system. `force-push` is the tier-5 twin.
        r"\bpush\b",
        r"\binit\b",
        r"\binitiali[sz]e\b",
        r"\binstall\b",
        r"\btrain\b",
        # browser automation acts on a live page: a click submits, a fill types
        # into someone's form. Navigating or screenshotting only reads.
        r"\bclick\b",
        r"\bfill\b",
        r"\btype into\b",
        # change in place
        r"\bupdate\b",
        r"\bedit\b",
        r"\bmodify\b",
        r"\bpatch\b",
        r"\bput\b",
        r"\bset\b",
        r"\bupsert\b",
        r"\bsave\b",
        r"\bstore\b",
        r"\bwrite\b",
        r"\bamend\b",
        r"\brevise\b",
        r"\badjust\b",
        r"\bconfigure\b",
        r"\brelabel\b",
        r"\btag\b",
        r"\blabel\b",
        r"\bannotate\b",
        # relocate
        r"\bmove\b",
        r"\bmv\b",
        r"\brelocate\b",
        r"\btransfer to\b",
        r"\bsync\b",
        r"\bmirror\b",
        # membership / access (recoverable both ways)
        r"\bjoin\b",
        r"\bleave\b",
        r"\bgrant\b",
        r"\brevoke\b",
        r"\bassign\b",
        r"\bunassign\b",
        r"\bmembership\b",
        r"\bsubscribe\b",
        r"\bunsubscribe\b",
        # the access grant, not the stock noun ("share float", "share price").
        # These words are name-scoped, and names are terse — `share_doc` has no
        # article — so a tool NAMED share_* counts on its own.
        r"\Ashare[sd]?\b",
        r"\bshare[sd]? (a|an|the|this|your|it|them|access|file|folder|doc|document|link)\b",
        r"\bshare[sd]?\b[^.]{0,30}\bwith\b",
        r"\bpermit\b",
        r"\bauthoriz?se\b",
        # in-system posting / response
        r"\bpost\b",
        r"\bcomment\b",
        r"\breply\b",
        r"\brespond\b",
        r"\brsvp\b",
        r"\baccept\b",
        r"\bdecline\b",
        r"\bvote\b",
        r"\bsubmit\b",
        # lifecycle (recoverable)
        r"\bopen\b",
        r"\bclose\b",
        r"\breopen\b",
        r"\barchive\b",
        r"\bunarchive\b",
        r"\brestore\b",
        r"\benable\b",
        r"\bdisable\b",
        r"\bactivate\b",
        r"\bdeactivate\b",
        r"\bpause\b",
        r"\bresume\b",
        r"\bschedule\b",
        r"\breschedule\b",
        r"\bmanage\b",
        r"\bapply\b",
        r"\bcommit\b",
        r"\bcheckout\b",
    ),
    # ---- 5 · IRREVERSIBLE, OR IT LEAVES THE SYSTEM ---------------------------
    5: (
        # destroy — fs (rm/unlink), db (drop/truncate), cache (flush/evict),
        # infra (terminate/decommission), generic (purge/wipe/erase)
        r"\bdelete\b",
        r"\bremove\b",
        r"\brm\b",
        r"\bunlink\b",
        r"\bdestroy\b",
        r"\bdrop\b",
        r"\bpurge\b",
        r"\bwipe\b",
        r"\berase\b",
        r"\btruncate\b",
        r"\bclear\b",
        r"\bflush\b",
        r"\bevict\b",
        r"\breset\b",
        # "empty" as a VERB only. As an adjective ("a children array which may
        # be empty", "returns an empty list") it is the commonest word in a
        # read tool's description — it fired tier 5 on `directory_tree`.
        r"\bempties\b",
        r"\bempty (the|all|a|an|this|out)\b",
        r"\bprune\b",
        r"\bdiscard\b",
        r"\bexpire\b",
        r"\binvalidate\b",
        r"\bterminate\b",
        r"\bkill\b",
        r"\bshutdown\b",
        r"\bdeprovision\b",
        r"\bdecommission\b",
        r"\buninstall\b",
        r"\bcancel\b",
        r"\bvoid\b",
        r"\brevert\b",
        r"\brollback\b",
        r"\bforce[- ]?push\b",
        # replace wholesale
        r"\boverwrit(e|ing)\b",
        r"\breplac(e|ing) (the )?(entire|whole|complete)\b",
        r"\bcompletely overwrite\b",
        # execute
        r"\bexecut(e|ing)\b",
        r"\beval(uate)?[- ]?(code|script|expression)\b",
        r"\brun (a )?(command|script|code|query|job)\b",
        r"\btrigger\b",
        r"\bdispatch\b",
        r"\binvoke\b",
        r"\beval(uate)?s?\b[^.]{0,20}\b(javascript|js|code|script|expression)\b",
        r"\bdeploy\b",
        # `get_latest_release` READS a release; only a tool named release_* ships one
        r"\Arelease[sd]?\b",
        r"\brelease[sd]? (a|an|the|this|to|version|build)\b",
        r"\bpublish\b",
        r"\bmerge\b",
        r"\brebase\b",
        # `push` itself is tier 4 (an append; the history survives and `revert`
        # undoes it). Only the history-REWRITING variant belongs here — it
        # discards commits, which no in-system control restores.
        r"\bforce[- ]?push(es|ed)?\b",
        r"\bpush --force\b",
        r"\bpush -f\b",
        # money
        r"\btransfer funds\b",
        r"\bpayments?\b",
        r"\bcharge\b",
        r"\brefund\b",
        r"\bpayout\b",
        r"\bwithdraw\b",
        r"\bsettle\b",
        r"\bplace (an )?order\b",
        # the EXECUTION, not the noun: "add an open trade to the journal" records
        # a trade, it does not place one.
        r"\b(execute|place|submit|enter|exit) (a |an |the )?trades?\b",
        r"\bbuy\b",
        r"\bsell\b",
        # leaves the system boundary
        r"\bsend\b",
        r"\bemail\b",
        r"\bsms\b",
        r"\bnotif(y|ies|ied|ying)\b",
        r"\bwebhook\b",
        r"\binvite\b",
        r"\bbroadcast\b",
        # needs its object: "walk-forward analysis" and "forward curve" are not sends
        r"\Aforwards?\b",
        r"\bforwards?\b[^.]{0,15}\b(message|email|mail|note|thread|conversation)\b",
        r"\bforward(s|ed|ing)? (a|an|the|this|your)\b",
        r"\bannounce\b",
    ),
}
_COMPILED = {t: tuple(re.compile(p, re.I) for p in pats) for t, pats in _TIER_PATTERNS.items()}

# AMBIGUOUS tokens: common English words that are a strong action verb in a tool
# NAME but an ordinary noun in prose. Matching these anywhere in a long
# description is the dominant false-positive source — "List all user groups …
# that notify all members" is not a notification tool, "Get list of commits of a
# branch" does not create a branch, "Search users by name, email …" does not send
# email. They are therefore matched against the tool NAME ONLY — the one place
# where such a word IS the action being named rather than described.
_AMBIGUOUS = frozenset(
    {
        # VCS / code
        "branch",
        "fork",
        "merge",
        "push",
        "rebase",
        "commit",
        "stage",
        "clone",
        "release",
        "deploy",
        "publish",
        "tag",
        "label",
        "checkout",
        # messaging / collaboration
        "email",
        "notif",
        "invite",
        "comment",
        "reply",
        "replies",
        "announce",
        "post",
        "share",
        "follow",
        "watch",
        "flag",
        "vote",
        "accept",
        "decline",
        # lifecycle / admin
        "manage",
        "trigger",
        "dispatch",
        "click",
        "fill",
        "train",
        "init",
        "install",
        "configure",
        "provision",
        "allocate",
        "register",
        "submit",
        "apply",
        "enable",
        "disable",
        "activate",
        "deactivate",
        "pause",
        "resume",
        "open",
        "close",
        "archive",
        "restore",
        "schedule",
        "permit",
        "member",
        "membership",
        "assign",
        "cancel",
        "subscribe",
        "kill",
        "reset",
        "clear",
        "run",
        "invoke",
        "make",
        "build",
        "new",
        "generate",
        # data movement
        "copy",
        "duplicate",
        "sync",
        "mirror",
        "import",
        "export",
        "snapshot",
        "save",
        "store",
        "set",
        "put",
        "add",
        "draft",
        # money
        "payment",
        "trade",
        "buy",
        "sell",
        "charge",
        "order",
        # words that are usually NOUNS describing the payload, not the action
        "index",
        "catalog",
        "directory",
        "history",
        "histories",
        "status",
        "external",
        "mark",
        "scan",
        "key",
        "field",
        "column",
        "header",
        "text",
        "body",
        "payload",
        "report",
        "compare",
        "evaluate",
        "screen",
        "usage",
        "quota",
        "attribute",
        "exists",
        "walk",
        "discover",
        "now",
        "select",
        "find",
        "show",
        "view",
    }
)


# NEGATION GUARD. Tool descriptions increasingly embed instructions to the MODEL
# ("NEVER add external information", "DO NOT delete anything", "without sending a
# notification"). Those are prohibitions, not capabilities, and a bare verb match
# turns a read-only SEC filings reader into a tier-4 writer. A verb preceded by a
# negator within a short window is therefore not evidence of a capability.
# A DDL keyword inside a QUOTED statement is being described, not performed:
# `describe_table` says "Returns the CREATE TABLE DDL" and scored tier 4. Guarded
# per occurrence, exactly like negation — so `create_table`, whose NAME carries
# the verb, still fires.
_QUOTED_STATEMENT = re.compile(
    r"\b(create|drop|alter|insert|update|delete|truncate)\s+"
    r"(table|index|view|column|schema|database)\b",
    re.I,
)


def _quoted_statement(text: str, position: int) -> bool:
    """True when this match sits inside a quoted DDL phrase in a read's prose."""
    window = text[max(0, position - 40) : position + 40]
    return bool(_QUOTED_STATEMENT.search(window)) and bool(
        re.search(r"\b(returns?|shows?|gets?|describ\w*)\b", window, re.I)
    )


_NEGATOR = re.compile(
    r"\b(never|not|n't|don'?t|do not|does not|cannot|can'?t|avoid|without|"
    r"no need to|refrain from|must not|should not)\b[^.]{0,40}$",
    re.I,
)


def _negated(text: str, end_of_match_start: int) -> bool:
    """True when a negator appears just before the matched verb (same sentence)."""
    window = text[max(0, end_of_match_start - 60) : end_of_match_start]
    return bool(_NEGATOR.search(window))


def _is_ambiguous(pattern: str) -> bool:
    return any(tok in pattern for tok in _AMBIGUOUS)


def _first_sentence(text: str) -> str:
    """The description's first sentence — what the tool DOES, before the caveats."""
    return re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)[0] if text else ""


# Descriptions often SAY the operation is scoped/recoverable; that caps a
# would-be 5 back at 4 (the prompt's "scoped edit = 4, full overwrite = 5").
_SCOPED_EDIT = re.compile(
    r"\b(line[- ]based|partial|specific (lines|fields|parts)|diff|append(s|ing)? to|"
    r"leaves? the rest|selective)\b",
    re.I,
)
# An array-typed parameter (or an explicit bulk word) marks a bulk variant.
_BULK_WORDS = re.compile(r"\b(bulk|batch|multiple|several|many|in one call)\b", re.I)
# NOTE (v4): the "bulk form that drops a safety takes the higher tier" bump was
# REMOVED at the user's instruction. A bulk variant is still recorded (is_bulk)
# and the pipeline's deterministic bulk-twin pass still enforces
# impact(bulk) >= impact(singular), but dropping a safety no longer adds a tier.

# "create_or_update_file" / "create or update": one call either makes a new item
# or replaces an existing one wholesale.
_CREATE_OR_OVERWRITE = re.compile(r"create[_ -]?or[_ -]?(update|overwrite|replace)", re.I)

# CAPS — evidence about WHAT A READ RETURNS, which bounds the tier from above.
# These apply ONLY when no write/destroy verb fired (a mutation's tier can never
# be capped by the shape of what it returns), so they cannot under-score an
# action. Without them a bare verb wins: "GET the current time" would score as a
# content read (3) purely because of the word "get".
# Container nouns — a listing of these is a catalog (metadata); a listing of
# anything else hands back the items themselves.
_CONTAINER_NOUN = re.compile(
    r"\b(calendars?|directories|director(y|ies)|folders?|repositor(y|ies)|channels?|"
    r"tables?|accounts?|buckets?|databases?|schemas?|colou?rs?|groups?|workspaces?)\b",
    re.I,
)

_CAP_MARKERS: tuple[tuple[int, re.Pattern[str]], ...] = (
    # cap 1: the answer is a server fact, not the data at all.
    (
        1,
        re.compile(
            r"\b(current (date|time)|server time|ping|health(check)?|heartbeat|"
            r"version|capabilit(y|ies)|who ?am ?i|"
            # pure arithmetic on no asset at all: a timezone conversion touches
            # nothing the server holds.
            r"convert.{0,12}time|time ?zone conversion)\b",
            re.I,
        ),
    ),
    # cap 2: the answer is about-ness — availability windows, names, schema.
    (
        2,
        re.compile(
            r"\b(free.?busy|availability|busy blocks|schema|"
            r"(list|names|ids) of (all )?(available )?"
            r"(calendars?|directories|folders|repositor(y|ies)|channels?|tables?|accounts?)|"
            r"available [a-z]+s\b|"
            r"colou?r (ids?|palette)|"
            r"mark (a )?(channel|dm|message|thread|conversation)?\s*(or dm )?as read|"
            r"marks? all messages as read|"
            r"metadata about|detailed metadata|"
            r"status|dashboard|connection state|"
            r"listing of all files and directories|"
            r"distinguish between files and directories)\b",
            re.I,
        ),
    ),
)


# A description that STATES what it returns settles the read/metadata question
# better than any verb does. "Returns full paths to all matching items" is
# about-ness however the tool got there, and `search`/`get` say nothing about it.
#
# Scope note: unlike the _CAP_MARKERS above this is matched against the WHOLE
# description, not the first sentence — an explicit return statement is
# unambiguous wherever an author put it.
# The clause stops at the first colon or newline: "Returns:\n  Dictionary
# containing ... form_type" is a parameter block, and matching inside it picked
# up "type"/"count" from argument names. Only running prose counts.
_RETURN_STATEMENT = re.compile(
    r"\b(?:returns?|each entry includes|entries include|output (?:is|includes)|"
    r"response (?:contains|includes))\b([^.:\n]{0,80})",
    re.I,
)
# Identifier-shaped returns: you learn WHICH things exist, not what is in them.
_RETURN_META = re.compile(
    r"\b(paths?|names?|ids?|identifiers?|urls?|uris?|keys?|"
    r"listings?|list of|tree|structure|hierarchy|counts?|sizes?|"
    r"timestamps?|types?|metadata|schema)\b",
    re.I,
)
# ...unless the same statement also promises the substance.
_RETURN_CONTENT = re.compile(
    r"\b(contents?|body|bodies|text|payloads?|values?|records?|rows?|"
    r"messages?|data|details?|snippets?|excerpts?|diffs?|patch(es)?)\b",
    re.I,
)
# A tier-3 verb that only means "something comes back" — the OBJECT decides the
# tier, not the verb. Contrast `read`/`download`/`export`/`contents`, which do
# state that the substance itself is returned.
_GENERIC_READ = frozenset(
    {
        r"\bget\b",
        r"\bsearch\b",
        r"\bfetch\b",
        r"\bretrieve\b",
        r"\bfind\b",
        r"\blookup\b",
        r"\bshow\b",
        r"\bview\b",
        r"\bbrowse\b",
    }
)


def _stated_return_is_metadata(description: str) -> str | None:
    """The matched 'Returns ...' clause when it promises identifiers, else None."""
    for match in _RETURN_STATEMENT.finditer(description):
        clause = match.group(1)
        if _RETURN_META.search(clause) and not _RETURN_CONTENT.search(clause):
            return clause.strip()
    return None


# --- Parameter signals ------------------------------------------------------
# From "Auditing MCP Servers for Over-Privileged Tool Capabilities" (arXiv
# 2603.21641): the dangerous property is often in the INPUTS, not the verb — a
# parameter taking a raw query/command, an unconstrained path, a recursion or
# force switch.
#
# These are recorded as CAPABILITY FLAGS ONLY — they never move the tier. A
# parameter says what the caller COULD pass, not what any call does pass; the
# actual argument is a runtime fact, so the dynamic stage prices it. Static
# impact stays a statement about the tool's declared action.
_PARAM_SIGNALS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    # NOTE: every pattern is FULL-NAME anchored. An unanchored alternation is a
    # silent disaster — "cc" matched inside "a(cc)ount" and turned every
    # calendar read into an outbound-messaging tool.
    (
        "raw-query",
        re.compile(r"\A(sql|statement|query|q|expression)\Z|_(sql|statement)\Z", re.I),
        "takes a raw query string — the caller composes the operation",
    ),
    (
        "raw-command",
        re.compile(
            r"\A(cmd|command|script|code|exec|shell|program)\Z|"
            r"_(cmd|command|script|code)\Z",
            re.I,
        ),
        "takes a command/script to execute",
    ),
    (
        "outbound",
        re.compile(
            r"\A(send_?updates?|sendUpdates|notify|notification|webhook|"
            r"recipients?|to|cc|bcc|to_?email|to_?address)\Z",
            re.I,
        ),
        "can emit a message outside the system",
    ),
    (
        "path",
        re.compile(
            r"\A(path|file|filepath|filename|dir|directory|"
            r"destination|source|src|dst)\Z|_(path|dir|file)\Z",
            re.I,
        ),
        "takes a filesystem path",
    ),
    (
        "recursive",
        re.compile(r"\A(recursive|recurse|deep|all_?files)\Z|include_?subdir", re.I),
        "can descend recursively — one call reaches a subtree",
    ),
    (
        "glob",
        re.compile(r"\A(glob|pattern|wildcard|regex|match|filter)\Z", re.I),
        "takes a pattern — one call can select many items",
    ),
    (
        "force",
        re.compile(
            r"\A(force|hard|permanent|skip_?confirm|no_?confirm|"
            r"overwrite|replace)\Z|_(force|permanent|overwrite)\Z",
            re.I,
        ),
        "has a force/overwrite switch that removes a safety",
    ),
    (
        "unbounded",
        re.compile(r"\A(limit|max_?results?|count|page_?size)\Z", re.I),
        "caller controls result volume",
    ),
    (
        "dry-run",
        re.compile(r"\A(dry_?run|preview|simulate)\Z", re.I),
        "offers a dry-run — the real call is consequential",
    ),
)


def _tool_params(tool) -> dict:
    """The tool's parameter properties dict, whatever the ToolSpec calls it."""
    schema = getattr(tool, "input_schema", None) or getattr(tool, "parameters", None) or {}
    return schema.get("properties", {}) if isinstance(schema, dict) else {}


def _param_signals(tool) -> list[str]:
    """Capability flags implied by the tool's parameters.

    Descriptive only: a parameter never changes the impact tier. What the caller
    actually passes is a per-call fact, so the dynamic stage scores it.
    """
    props = _tool_params(tool)
    if not props:
        return []
    flags: list[str] = []
    for pname, spec in props.items():
        spec = spec if isinstance(spec, dict) else {}
        for key, pattern, why in _PARAM_SIGNALS:
            if not pattern.search(pname):
                continue
            note = f"{key}: `{pname}` {why}"
            # An unconstrained path/command parameter is the over-privilege case:
            # no enum, no pattern, no format to bound it.
            if key in ("path", "raw-command", "raw-query") and not (
                spec.get("enum") or spec.get("pattern") or spec.get("format")
            ):
                note += " (unconstrained: no enum/pattern/format)"
            if note not in flags:
                flags.append(note)
    return flags


@dataclass
class StaticImpact:
    """One deterministic impact decision, with everything that produced it.

    ``tool_impact`` is the 1-5 ladder. The other fields are SEPARATE risk axes,
    deliberately not folded into the tier:

    * ``capability_flags`` — over-privilege signals read from the PARAMETERS
      (raw SQL/command strings, unconstrained paths, recursion/globs, force
      switches). Following "Auditing MCP Servers for Over-Privileged Tool
      Capabilities", a tool can sit at a modest tier and still be dangerous
      because its inputs are unconstrained.

    THREAT MODEL: misuse during NORMAL operation. The tool declaration is taken
    at face value — we are not looking for a malicious or poisoned server, only
    for what a legitimate tool can do when an agent uses it wrongly.
    """

    tool_name: str
    tool_impact: int
    reasoning: str
    evidence: list[str] = field(default_factory=list)
    annotation_bound: int | None = None  # ceiling imposed by readOnlyHint, if any
    is_bulk: bool = False
    capability_flags: list[str] = field(default_factory=list)
    confidence: float = 0.5


def _matches(name: str, description: str) -> dict[int, list[str]]:
    """Tier -> the patterns that fired, with scope depending on ambiguity.

    Unambiguous action verbs (delete, create, overwrite, execute …) are matched
    across the whole declaration. Ambiguous noun/verb words (:data:`_AMBIGUOUS`)
    count ONLY in the tool name, so prose like "…groups that notify all members"
    cannot make a listing tool look like a notifier.
    """
    full = f"{re.sub(r'[_\-.]+', ' ', name)} {description}"
    # Ambiguous words count only where they ARE the action: the tool name.
    # Separators become spaces so word boundaries work ("push_files" -> "push files").
    narrow = re.sub(r"[_\-.]+", " ", name)
    hits: dict[int, list[str]] = {}
    for tier, pats in _COMPILED.items():
        found = []
        for pat in pats:
            scope = narrow if _is_ambiguous(pat.pattern) else full
            # A verb counts only if at least one occurrence is NOT negated.
            if any(
                not _negated(scope, m.start()) and not _quoted_statement(scope, m.start())
                for m in pat.finditer(scope)
            ):
                found.append(pat.pattern)
        if found:
            hits[tier] = found
    return hits


def _array_param(tool) -> bool:
    """True when any input parameter is array-typed (a bulk signal)."""
    schema = getattr(tool, "input_schema", None) or getattr(tool, "parameters", None) or {}
    props = schema.get("properties", {}) if isinstance(schema, dict) else {}
    return any(isinstance(spec, dict) and spec.get("type") == "array" for spec in props.values())


def classify(tool) -> StaticImpact:
    """Assign tool impact 1-5 from the tool's own declaration — no LLM.

    ``tool`` is a :class:`~mcp_security.static_scoring.registry.ToolSpec` (or any
    object exposing ``name``, ``description`` and the annotation hints).
    """
    name = tool.name
    description = tool.description or ""
    text = f"{name} {description}"
    hits = _matches(name, description)

    read_only = getattr(tool, "read_only_hint", None)
    destructive = getattr(tool, "destructive_hint", None)
    idempotent = getattr(tool, "idempotent_hint", None)

    # 1. Annotation ceiling: a declared read-only tool cannot write or destroy.
    ceiling = 3 if read_only is True else 5
    evidence: list[str] = []
    if read_only is True:
        evidence.append("readOnlyHint=true -> ceiling 3")
    elif read_only is False:
        evidence.append("readOnlyHint=false")
    if destructive is True and read_only is not True:
        evidence.append("destructiveHint=true")

    # 2. Highest tier whose description evidence fires, inside the ceiling.
    tier = max((t for t in hits if t <= ceiling), default=None)
    if tier is None:
        # No verb matched: fall back to the annotations alone, else the safe
        # middle (a tool that declares nothing and says nothing is assumed to
        # read content rather than assumed harmless).
        tier = 3 if read_only is True else (5 if destructive is True else 3)
        evidence.append("no verb evidence -> annotation/default")
    else:
        evidence.append(f"tier-{tier} verbs: {', '.join(hits[tier][:3])}")

    # 2b. A listing of CONTAINERS is metadata (names of calendars, directories,
    #     repositories); a listing of anything else hands back the items
    #     themselves, which is a content read. Under-scoring is the costlier
    #     error, so an unqualified "list <domain object>" resolves upward to 3.
    if tier == 2 and hits.get(2) and not _CONTAINER_NOUN.search(text):
        listing = [p for p in hits[2] if any(v in p for v in ("list", "enumerate", "index"))]
        if listing and 3 not in hits:
            tier = 3
            evidence.append("lists non-container items -> content read (3)")

    # 3. Return-shape caps — READ-ONLY tiers only. A description that names what
    #    it returns (the clock, availability, a catalog of containers) bounds the
    #    tier from above; a mutation (>=4) is never capped this way.
    if tier <= 3:
        name_words = re.sub(r"[_\-.]+", " ", name)
        cap_scope = {
            # A liveness tool is NAMED one; "…and their capabilities" in prose is
            # not evidence that the tool is a ping.
            1: name_words,
            # What a read RETURNS is stated in the name or the opening sentence.
            2: f"{name_words} {_first_sentence(description)}",
        }
        for cap, pattern in _CAP_MARKERS:
            if pattern.search(cap_scope[cap]) and cap < tier:
                tier = cap
                evidence.append(f"return-shape marker -> capped at {cap}")
                break

    # 3c. THE OBJECT DECIDES, when the verb does not. `get` and `search` mean
    #     "something comes back"; they say nothing about WHAT. Two ways to learn
    #     the object, both requiring that no non-generic tier-3 verb fired (a
    #     `read`/`download`/`contents` verb states the substance itself):
    #       (i)  the description says what it returns, and it is identifiers;
    #       (ii) the thing being searched/listed IS a container, so the answer is
    #            a catalog of container names.
    #     Without this, `directory_tree` ("tree view … 'name', 'type'") and
    #     `search_files` ("Returns full paths") score 3 on the strength of the
    #     word "get" alone.
    if tier == 3 and hits.get(3) and set(hits[3]) <= _GENERIC_READ:
        stated = _stated_return_is_metadata(description)
        first = _first_sentence(description)
        # Head-anchored: the container has to be what the tool acts ON. Either
        # the tool NAME ends in it (`search_repositories`) or it is the direct
        # object of the opening verb ("Search for GitHub repositories"). A
        # container that merely names the SCOPE does not count.
        name_tail = re.sub(r"[_\-.]+", " ", name).split()
        tail_is_catalog = bool(
            name_tail
            and _CONTAINER_NOUN.fullmatch(name_tail[-1])
            and name_tail[-1].lower().endswith(("s", "ies"))
        )
        container_object = tail_is_catalog or bool(
            re.search(
                r"\b(search|list|get|browse|find|fetch|retrieve|show)\b"
                r"\s+(?:for\s+|all\s+|the\s+|your\s+|available\s+)*(?:\w+\s+)?"
                + _CONTAINER_NOUN.pattern,
                first,
                re.I,
            )
        )
        container_object = container_object and not _RETURN_CONTENT.search(first)
        # A tool NAMED `list_x` says what it returns in its own name; the `get`
        # in "Get list of commits" is then just how the list is phrased.
        named_listing = bool(re.match(r"(list|ls|enumerate|index)[_\-]", name, re.I))
        if stated:
            tier = 2
            evidence.append(f'generic verb; stated return is metadata ("{stated[:40]}") -> 2')
        elif container_object:
            tier = 2
            evidence.append("generic verb over a CONTAINER -> catalog of names (2)")
        elif named_listing:
            tier = 2
            evidence.append("named a listing; only a generic read verb above it -> 2")

    # 3b. "create OR update/overwrite" in one tool: the prompt's rule says a tool
    #     that can create-new OR fully-overwrite takes 5.
    if tier == 4 and _CREATE_OR_OVERWRITE.search(text):
        tier = 5
        evidence.append("create-or-overwrite in one tool -> 5")

    # 4. Scoped-edit exception: an explicitly partial/reconstructable edit is 4,
    #    not 5, unless a genuine delete verb also fired.
    if tier == 5 and _SCOPED_EDIT.search(text):
        delete_verbs = [p for p in hits.get(5, []) if "delet" in p or "remov" in p or "purge" in p]
        if not delete_verbs:
            tier = 4
            evidence.append("scoped/partial edit language -> capped at 4")

    # 5. destructiveHint corroborates a 5 when the description is ambiguous.
    if destructive is True and read_only is not True and tier == 4 and 5 in hits:
        tier = 5
        evidence.append("destructiveHint=true corroborates tier-5 verb")

    is_bulk = bool(_BULK_WORDS.search(text)) or _array_param(tool)
    if is_bulk:
        evidence.append("bulk signal (array param or bulk wording)")

    # 6. PARAMETER signals — over-privilege evidence from the inputs, recorded as
    #    capability flags. They do NOT move the tier: a parameter describes what
    #    the caller could pass, and the value actually passed is a runtime fact
    #    that the dynamic stage prices.
    capability_flags = _param_signals(tool)

    # NOTE: `openWorldHint` is deliberately NOT used here. Whether a call actually
    # leaves the system depends on the specific request (did it set sendUpdates?
    # was there an external recipient?), which is a RUNTIME fact — so boundary
    # crossing is scored by the dynamic stage, not by this design-time ladder.
    # The hint is still parsed onto ToolSpec so the dynamic scorer can consume it.
    if idempotent is False and tier >= 4:
        capability_flags.append("non-idempotent write: a retry repeats the effect")

    # Confidence: how much independent evidence agreed. A tier set by an explicit
    # verb AND corroborated by an annotation is trustworthy; a tier that fell
    # through to the default is not.
    confidence = 0.5
    if any(e.startswith("tier-") for e in evidence):
        confidence = 0.8
    if read_only is not None or destructive is not None:
        confidence = min(1.0, confidence + 0.15)
    if any("no verb evidence" in e for e in evidence):
        confidence = 0.35

    return StaticImpact(
        tool_name=name,
        tool_impact=tier,
        reasoning=(f"deterministic ladder: {'; '.join(evidence)}"),
        evidence=evidence,
        annotation_bound=ceiling if read_only is True else None,
        is_bulk=is_bulk,
        capability_flags=capability_flags,
        confidence=round(confidence, 2),
    )


def classify_all(tools) -> dict[str, StaticImpact]:
    return {t.name: classify(t) for t in tools}


# ---------------------------------------------------------------------------
# v5r — classification by OPERATION TYPE
# ---------------------------------------------------------------------------
#
# The rules above grew one special case per tool that scored wrong: a regex that
# matches only `create_or_update_file`, a return-shape cap written for
# `get-freebusy` and `list-colors`, a three-branch rule whose comment names
# `directory_tree` and `search_files`. Each fixed its example and none stated a
# principle. This rewrite replaces all of them with one question — **what
# operation is this?** — and four rules.
#
# Two things leave the ladder entirely:
#
# * **The annotation ceiling.** `readOnlyHint: true` no longer caps the tier. The
#   protocol's own guidance is that hints "are not guaranteed to faithfully
#   describe tool behavior" and a server "can claim readOnlyHint: true and delete
#   your files anyway", so a hint must not be the authority on a tool's own risk.
#   Annotations are recorded as evidence and, when they contradict the
#   description, the contradiction itself is recorded.
# * **Open-world.** Whether a call leaves the organization is a channel, not an
#   operation: "it is an email" says nothing about read / write / remove. Sending
#   creates a message, so by operation type it is a WRITE. Boundary crossing is
#   priced by the dynamic stage, which can see the actual recipient.

OP_NONE = "none"
OP_META = "metadata"
OP_READ = "read"
OP_WRITE = "write"
OP_REMOVE = "remove"

# Most consequential operation a declaration admits to wins.
_OP_PRECEDENCE = (OP_REMOVE, OP_WRITE, OP_READ, OP_META, OP_NONE)
_OP_TIER = {OP_NONE: 1, OP_META: 2, OP_READ: 3, OP_REMOVE: 5}

# The tier lists above are reused as operation vocabularies, with two corrections
# where the old tier said something about the CHANNEL or the DIRECTION of a
# change rather than about the operation itself.
_TIER_OP = {1: OP_NONE, 2: OP_META, 3: OP_READ, 4: OP_WRITE, 5: OP_REMOVE}

# Filed under tier 5 today, but they emit something — the operation is a write
# through an outbound channel.
_SEND_IS_WRITE = (
    "send",
    "email",
    "sms",
    "notif",
    "webhook",
    "invite",
    "broadcast",
    "forward",
    "announce",
    "publish",
    "release",
)
# Filed under tier 5 today, but they RESTORE a prior state rather than remove
# one; undoing is a write.
_UNDO_IS_WRITE = ("revert", "rollback", "cancel", "void", "restore")
# Filed under tier 5 today because of what they LEAD TO (merged code deploys),
# not because of what they do. Integrating a change is a write; the deployment
# that may follow is a different tool's operation.
_INTEGRATE_IS_WRITE = ("merge", "rebase", "commit", "checkout", "stage")
# Filed under tier 5 today and genuinely a full-item replacement, which the v5r
# ladder ranks as a write (tier 4) rather than a removal (tier 5).
_REPLACE_IS_WRITE = ("overwrit", "replac", "rewrit", "force[- ]?push", "push --force", "push -f")


def _operation_of(tier: int, pattern: str) -> str:
    """Which operation class a tier pattern belongs to under the v5r ladder."""
    if tier != 5:
        return _TIER_OP[tier]
    reclassified = _SEND_IS_WRITE + _UNDO_IS_WRITE + _INTEGRATE_IS_WRITE + _REPLACE_IS_WRITE
    if any(token in pattern for token in reclassified):
        return OP_WRITE
    return OP_REMOVE


# Vocabulary the tier lists state too rigidly to fire on real descriptions. The
# tier list has `mark (as )?read`, which misses "Mark a conversation as read" —
# the words between the verb and its object. Kept separate from _TIER_PATTERNS so
# the v4/v5 arms stay byte-reproducible.
_OP_EXTRA: dict[str, tuple[str, ...]] = {
    OP_META: (
        r"\bmarks?\b[^.]{0,40}\b(as )?(read|unread|seen)\b",
        r"\bunreads?\b",
    ),
}

_OP_COMPILED: dict[str, tuple[re.Pattern, ...]] = {}
for _tier, _pats in _TIER_PATTERNS.items():
    for _pat in _pats:
        _OP_COMPILED.setdefault(_operation_of(_tier, _pat), ())
        _OP_COMPILED[_operation_of(_tier, _pat)] += (re.compile(_pat, re.I),)
for _op, _extra in _OP_EXTRA.items():
    _OP_COMPILED[_op] += tuple(re.compile(p, re.I) for p in _extra)

# HOW MANY items a call reaches is not a tool-impact question — that is coverage,
# and blast radius scores it. So no breadth vocabulary is read here: not "all" or
# "every", not "bulk" / "batch" / "multiple", not a glob, a recursion switch or a
# scope selector. A bulk variant and its singular describe the same OPERATION.
#
# What DOES separate two writes is how much of one item the call authors. Two
# published standards draw that line in the same place:
#
#   * HTTP: PUT sends the complete representation and replaces the resource;
#     PATCH applies a partial modification and leaves unmentioned fields
#     untouched (RFC 5789 / RFC 9110).
#   * CVSS v4.0 integrity: VI:H is "a total loss of integrity ... the attacker is
#     able to modify any/all files"; VI:L is "modification of data is possible,
#     but ... the amount of modification is limited".
#
# So a write is a NORMAL write — the caller supplies what the item says — and that
# is tier 4. It drops to tier 3 only where the declaration states the amount
# written is bounded: a line appended, a comment added, named fields patched.
# Writing a text file is a 4; writing one sentence into it is a 3.
_FULL_REPLACEMENT = re.compile(
    r"\b(overwrit(e|es|ing)|replac(e|es|ing)|rewrit(e|es|ing)|truncat(e|es|ing)|"
    r"force[- ]?push|set the (entire|whole))\b",
    re.I,
)
# The bounded end — PATCH semantics: the rest of the item survives untouched.
_LIMITED_WRITE = re.compile(
    r"\b(append(s|ed|ing)?|adds? to|add (a|an|one) (comment|reply|note|reaction|"
    r"message|line|entry)|comments?|repl(y|ies)|react(ion)?|partial|"
    r"specific (lines|fields|parts)|line[- ]based|patch(es|ing)?|one field|"
    r"leaves? the rest|selective|insert into|a (line|sentence|note))\b",
    re.I,
)


# "query" belongs with get/fetch/search: it says something comes back, not what.
_GENERIC_READ_V5R = _GENERIC_READ | {r"\bquery\b"}


def _is_ambiguous_v5r(pattern: str) -> bool:
    """Whether a pattern may only be matched against the tool NAME.

    The ambiguity problem is that a single word can be an action in a name and an
    ordinary noun in prose ("…groups that notify all members"). A pattern that
    names the verb **and** its object cannot be misread that way, so a multi-word
    phrase is matched across the whole declaration even when one of its words is
    on the ambiguous list. This is why "Mark a channel or DM as read" is
    recognised as consumption state rather than as a content read.
    """
    if " " in pattern or "{0," in pattern:  # a phrase, not a bare word
        return False
    return _is_ambiguous(pattern)


def classify_by_operation(tool) -> StaticImpact:
    """Assign tool impact 1-5 by OPERATION TYPE — the v5r ladder, no LLM.

    Four rules, in order:

    1. **Which operation?** The most consequential class whose verbs fire, scoped
       by the same name-only discipline for ambiguous words that the tier
       classifier uses.
    2. **A generic read verb is not evidence of content.** ``get`` / ``fetch`` /
       ``search`` / ``find`` / ``show`` say that something comes back, not what.
       When the only read evidence is generic and a metadata verb also fired, the
       operation is metadata. (This one rule replaces the container-noun list,
       the return-shape caps and the three-branch "object decides" rule.)
    3. **A write is scoped until it claims breadth.** Scoped writes share tier 3
       with content reads — both touch one item's substance. A write becomes
       tier 4 when its text claims breadth or whole-item replacement, or its
       parameters admit a glob, recursion or an array of targets.
    4. **A liveness probe is one that is NAMED one.** Applied to the tool name
       only, so "…and their capabilities" in prose cannot make a read a ping.

    Annotations never bound the result; a hint that contradicts the description is
    recorded as evidence and ignored.
    """
    name = tool.name
    description = tool.description or ""
    name_words = re.sub(r"[_\-.]+", " ", name)
    full = f"{name_words} {description}"

    hits: dict[str, list[str]] = {}
    spans: dict[str, list[tuple[int, int, str]]] = {}
    for op, pats in _OP_COMPILED.items():
        for pat in pats:
            scope = name_words if _is_ambiguous_v5r(pat.pattern) else full
            for match in pat.finditer(scope):
                if _negated(scope, match.start()) or _quoted_statement(scope, match.start()):
                    continue
                hits.setdefault(op, [])
                if pat.pattern not in hits[op]:
                    hits[op].append(pat.pattern)
                spans.setdefault(op, []).append((match.start(), match.end(), scope))

    evidence: list[str] = []

    # LONGEST MATCH WINS. A match sitting inside a longer match from another
    # operation class is not independent evidence — "Mark a channel as read"
    # contains the word "read", but the phrase describes the operation and the
    # word inside it does not. Swallowed matches are dropped before precedence is
    # applied; a class left with no surviving span is not evidence at all. This
    # is ordinary lexical precedence, not a rule about any one tool.
    all_spans = [(lo, hi, scope) for op_spans in spans.values() for lo, hi, scope in op_spans]
    surviving: dict[str, list[tuple[int, int, str]]] = {}
    for op, op_spans in spans.items():
        kept = [
            (lo, hi, scope)
            for lo, hi, scope in op_spans
            if not any(
                s == scope and a <= lo and hi <= b and (b - a) > (hi - lo) for a, b, s in all_spans
            )
        ]
        if kept:
            surviving[op] = kept
    dropped = {op for op in spans if op not in surviving}
    for op in dropped:
        evidence.append(f"{op} match(es) sit inside a longer phrase -> not evidence")
    hits = {op: pats for op, pats in hits.items() if op in surviving}

    operation = next((op for op in _OP_PRECEDENCE if op in hits), None)

    # Rule 2 — a generic read verb says something comes back, not what.
    if operation == OP_READ and set(hits[OP_READ]) <= _GENERIC_READ_V5R and OP_META in hits:
        operation = OP_META
        evidence.append("only generic read verbs; a metadata verb also fired -> metadata")

    if operation is None:
        operation = OP_READ
        evidence.append("no verb evidence -> assumed a content read")
    else:
        evidence.append(f"{operation} verbs: {', '.join(hits[operation][:3])}")

    capability_flags = _param_signals(tool)
    is_bulk = bool(_BULK_WORDS.search(full)) or _array_param(tool)

    if operation == OP_WRITE:
        # How much of ONE item this call authors. Coverage across items is not
        # asked here — that is blast radius.
        if (full_rep := _FULL_REPLACEMENT.search(full)) is not None:
            tier = 4
            evidence.append(f'write replaces the content ("{full_rep.group(0)}") -> 4')
        elif (limited := _LIMITED_WRITE.search(full)) is not None:
            tier = 3
            evidence.append(f'the amount written is limited ("{limited.group(0)}") -> 3')
        else:
            # A write is a normal write unless it says it is bounded, so 4 is the
            # right prior — but "bounded or not" is exactly the fact this
            # declaration omitted, so the model decides.
            tier = 4
            evidence.append("write does not state a limit -> defaulted to 4 (unsure)")
    else:
        tier = _OP_TIER[operation]

    # Rule 4 — a liveness probe is one that is NAMED one.
    if tier <= 3:
        for cap, pattern in _CAP_MARKERS:
            if cap == 1 and pattern.search(name_words):
                tier = 1
                evidence.append("named a liveness probe -> 1")
                break

    if is_bulk:
        evidence.append("bulk signal (array param or bulk wording)")

    # Annotations: evidence only. A contradiction is reported, never enforced.
    read_only = getattr(tool, "read_only_hint", None)
    destructive = getattr(tool, "destructive_hint", None)
    if read_only is True:
        evidence.append(
            "readOnlyHint=true (hint only; not a ceiling)"
            + (f" — CONTRADICTED by a {operation} verb" if operation in (OP_WRITE, OP_REMOVE) else "")
        )
    if destructive is True:
        evidence.append("destructiveHint=true (hint only; does not raise the tier)")
    if getattr(tool, "idempotent_hint", None) is False and tier >= 3:
        capability_flags.append("non-idempotent write: a retry repeats the effect")

    # Confidence reports how the tier was REACHED, which is what v5's hand-off
    # rule keys on. Two branches are defaults rather than findings, and both hand
    # the tool to the model: no verb matched at all, and a write whose
    # declaration states neither breadth nor scope.
    defaulted = any(("no verb evidence" in e) or ("(unsure)" in e) for e in evidence)
    confidence = 0.35 if defaulted else 0.8

    return StaticImpact(
        tool_name=name,
        tool_impact=tier,
        reasoning=f"operation={operation}; " + "; ".join(evidence),
        evidence=evidence,
        annotation_bound=None,  # v5r imposes no annotation ceiling
        is_bulk=is_bulk,
        capability_flags=capability_flags,
        confidence=confidence,
    )


def classify_all_by_operation(tools) -> dict[str, StaticImpact]:
    return {t.name: classify_by_operation(t) for t in tools}
