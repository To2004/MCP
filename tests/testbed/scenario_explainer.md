# Attack Theory in Practice — A Lecture Using the MCP Filesystem Study

This document teaches you the fundamental attack theories used in offensive security research.
Each theory is explained first. Then I show you exactly how the MCP filesystem study is a
real, working example of that theory. The scenarios I ran are not random — every one maps to
a class of attack that has been used against real systems for decades.

---

## Lecture 1 — Reconnaissance and Information Gathering

### The Theory

Every serious attack begins with reconnaissance. You do not attack blindly.
You first study the target: how does it behave normally? What does it reveal about itself?
What can you learn without triggering any alarms?

There are two kinds of reconnaissance:

**Passive reconnaissance** — you observe without interacting directly with the target.
Reading documentation, looking up version numbers on public databases, reading source code
if it is open. The target never knows you are watching.

**Active reconnaissance** — you send inputs to the target and observe the responses.
This is riskier (it leaves traces) but reveals things passive recon cannot.

In practice, active reconnaissance focuses on:
- What does a normal, successful response look like?
- What does an error response look like, and what does it reveal?
- Does the system leak internal information in its error messages?

### The Key Principle: Error-Based Information Disclosure

Developers write error messages to help themselves debug. They put internal details in them:
file paths, stack traces, version strings, database names. That is useful for the developer
but it is a gift for an attacker.

**Classic real-world example:** Early PHP applications used to print the full server path in
errors: `Warning: include(/var/www/html/secret/config.php): failed to open stream`.
An attacker now knows the directory structure of the server.

SQL injection reconnaissance works similarly — forcing a database error that reveals
the table name or column name in the error message.

### How This Appears in the MCP Study (S1 and S2)

**Scenario 1 (Baseline Characterisation)** is pure reconnaissance.
I sent 13 completely legitimate requests before trying anything adversarial.
The goal: understand what a successful response looks like, how the output is structured,
what the [FILE] and [DIR] notation means, whether the server transforms content.

**Scenario 2 (Error Response Analysis)** exploited error-based information disclosure.
I sent paths that do not exist, paths outside the sandbox, and empty strings.
The server responded with:

```
Error: ENOENT: no such file or directory,
open '/tmp/mcp_sandbox/doesnotexist.txt'
```

That error message revealed that the server resolves paths internally to their absolute form
before throwing the error. This is a side-channel: I can now send *any* string and the error
will tell me what the server turned it into. I used this in every subsequent scenario to
verify my assumptions about how the server processes my inputs.

### The Lesson

Never skip reconnaissance. The information you gather in S1 and S2 directly enabled the
CVE discovery in S6. An attacker who jumps straight to exploitation without reconnaissance
will miss the structural details that make a targeted, precise attack possible.

---

## Lecture 2 — Path Traversal Attacks

### The Theory

A path traversal attack (also called directory traversal) is one of the oldest and most
well-understood file system vulnerabilities. It has appeared in CVE databases since the 1990s.

The core idea: a web server or file server is supposed to restrict access to a specific
directory. But an attacker crafts a path that uses `..` (parent directory) references to
climb *out* of the restricted directory and access files elsewhere on the system.

**The classic example:**

A web application serves files from `/var/www/html/files/`.
You request: `../../../../etc/passwd`
The server resolves this as: `/var/www/html/files/../../../../etc/passwd` = `/etc/passwd`
And you have read the system's password file.

This was used in the famous **Apache web server CVE-2021-41773** (exploited in the wild
within 24 hours of disclosure). It was also the basis of the **MS-IIS Unicode bypass**
in the year 2000, where encoding `..` as `..%c0%af` bypassed the path traversal filter.

### Why It Still Works

Because developers check inputs as strings rather than checking what the path actually
resolves to. They look for `..` in the raw input and block it — but there are hundreds
of ways to represent a parent-directory reference that do not look like `..`:

| Encoding | What it means |
|----------|---------------|
| `%2e%2e%2f` | `../` (URL-encoded) |
| `%252e%252e%252f` | `../` (double URL-encoded) |
| `..%c0%af` | `../` (overlong UTF-8, Apache bug) |
| `..%00/` | `../` (null byte to confuse the parser) |

### How This Appears in the MCP Study (S3 and S5)

**Scenario 3 (Path Resolution Behaviour)** tested whether the server normalises paths correctly.
I sent `/sandbox/subdir/deep/../` — this should resolve to `/sandbox/subdir/`.
It did. The server handles `..` properly.

**Scenario 5 (Near-Boundary Input Testing)** directly tested `../../sandbox/readme.txt`.
This was blocked. The server resolves it to a path outside the sandbox and denies it.

The classic traversal attack did not work here. But testing it was essential —
if it *had* worked, we would have stopped at S5 with a critical finding.
The fact that it did not work shaped the next line of investigation.

### The Lesson

Path traversal is the *obvious* attack against a filesystem server.
A well-hardened server will block it. But the absence of an obvious vulnerability
does not mean the server is secure — it means the obvious path is closed.
The interesting vulnerabilities are the non-obvious ones. S6 is exactly that.

---

## Lecture 3 — Input Validation and Injection Attacks

### The Theory

Injection attacks are the most consistently dangerous class of vulnerability.
They appear year after year at the top of the OWASP Top 10 because the root cause is
always the same: the application trusts input it should not trust, and processes it
in a context where it has meaning beyond its intended purpose.

The family includes:
- **SQL injection** — input is interpreted as SQL code
- **Command injection** — input is interpreted as a shell command
- **Path injection** — input is interpreted as a file path that escapes the intended boundary
- **Null byte injection** — a special character terminates string processing prematurely

### Null Byte Injection — A Specific Theory

This deserves special attention because it is subtle and historically significant.

In the C programming language, strings end with a null byte (`\x00`).
Many web servers and applications are written in C or call C libraries.
When you send a string like `/etc/passwd\x00.jpg`, the C layer sees it as `/etc/passwd`
(it stops reading at `\x00`), even though the higher-level application layer sees the
full string `/etc/passwd\x00.jpg`.

So a system that checks "does this file end in `.jpg`?" might say yes, but then
open `/etc/passwd` because the C library stopped at the null byte.

This was a critical technique against PHP applications through the 2000s.
PHP's `fopen()` and `include()` calls passed strings directly to C functions,
making this exploitable in countless web applications until PHP 5.3.4 (2010).

### Non-Standard Separator Attacks

Different operating systems use different path separators.
Linux uses `/`. Windows uses `\`. If a Linux server does not reject backslashes,
an attacker might be able to use them as separators in unexpected ways:

```
/sandbox\../etc/passwd
```

Some servers treat `\` as a separator on Linux because the underlying C library
`realpath()` sometimes accepts it. This is a portability bug becoming a security bug.

### How This Appears in the MCP Study (S5)

Scenario 5 tested both of these directly:

**Windows backslash:** `/sandbox\readme.txt`
- Old version (v2025.3.28): treated `\` as a separator and returned the file.
- New version (v2025.7.29): rejected it.

This is a real patch for a real injection vulnerability. The old server's path-handling
code was accepting a non-standard separator, which could be used to construct bypass paths.

**Null byte:** `/sandbox/readme.txt\x00.png`
- Old version: returned the file content.
- New version: rejected it.

The null byte truncated the path at the application layer (the `.png` extension disappeared),
allowing the file to be read. This is a textbook null byte injection against a modern server —
the same class of bug that plagued PHP applications for two decades.

### The Lesson

Input validation failures are not exotic. They follow patterns that have been documented
for 30 years. When you are testing a system, run the known patterns first —
they exist in your test suite for a reason. Two of them (backslash and null byte) hit
in S5, confirming that even modern servers sometimes carry old vulnerabilities.

---

## Lecture 4 — Canonicalization and Normalization Attacks

### The Theory

Canonicalization is the process of converting something to its standard, unambiguous form.
A canonicalization attack exploits the gap between *how the system checks* a value
and *how the system uses* a value — specifically, when different representations of the
same thing are checked at different points in the processing pipeline.

The general principle:

```
Check happens here  →  input arrives  →  normalisation happens  →  use happens here
```

If the check uses the *raw* form but the system *uses* the normalised form, and the
raw-form check can be bypassed, you have a canonicalization vulnerability.

**Classic real-world example — IIS Unicode bug (MS00-078):**
Microsoft's IIS web server checked URLs for `../` to prevent traversal.
But it did not check for the Unicode overlong encoding of `/` (which is `%c0%af`).
So `..%c0%af` passed the check (no `../` found) but was decoded to `../` before use.
This allowed arbitrary file access on millions of Windows web servers in 2000.

**Another example — case sensitivity on Windows:**
Linux is case-sensitive. Windows is not. A check that looks for `ADMIN` in a URL
might be bypassed by requesting `admin` or `AdMiN` on a Windows server.

### The Specific Variant: Check Order

The MCP study revealed a subtle version of this. S3 confirmed:
the server normalises the path *before* checking the ACL.

This is actually the *safe* design. The dangerous design is the reverse:
check the raw string first, then normalise. That order creates a window where
a crafted raw string passes the check but normalises into something different.

However, S3 raised a new question: if normalisation happens before the ACL check,
what does that ACL check actually look like on the normalised string? S6 answered this.

### How This Appears in the MCP Study (S3 and S6)

**Scenario 3** established that normalisation precedes the check — a good design.
But it also established that I can observe the normalised form through error messages.

**Scenario 6** revealed that the ACL check itself was written incorrectly.
Even though normalisation happened first, the check after normalisation was:

```javascript
resolvedPath.startsWith(allowedRoot)
```

This is a canonicalization error at the semantic level. The path is fully canonical
(no dots, no double slashes) but the *comparison* does not account for the fact that
a path prefix is not the same as a path boundary.

The fix:

```javascript
resolvedPath.startsWith(allowedRoot + "/")
```

One character. This is the difference between vulnerable and safe.

### The Lesson

Canonicalization vulnerabilities are hard to find with automated tools because
they require understanding the system's *two-step* processing: what the check sees
versus what the execution sees. The MCP vulnerability is a pure canonicalization error —
the path is fully canonical, but the boundary check did not account for path semantics.

---

## Lecture 5 — Logic Flaws and Business Logic Attacks

### The Theory

Logic flaws are vulnerabilities in the *design* of a system's rules,
not in the implementation of its code. The code does exactly what it was written to do.
The problem is that what it was written to do is wrong.

These are the most dangerous class of vulnerability because:
1. **Automated scanners cannot find them.** A scanner looks for known bad patterns.
   A logic flaw does not match any pattern — it is unique to the system's design.
2. **Code review often misses them.** The code looks correct. Each line is fine.
   The flaw is in the relationship between lines, or in an assumption made silently.
3. **They require understanding the intended behaviour.** You have to know what the
   system is *supposed to do* before you can find where it fails to do that.

**Classic real-world example — password reset logic flaw:**
A system sends a password reset token by email. The token is tied to a user account.
The developer forgot to verify that the token matches the account being reset.
An attacker requests a reset for their own account, gets a valid token,
then uses that token to reset *someone else's* password.
Every line of code is syntactically correct. The logic is wrong.

**Another example — price manipulation:**
An e-commerce site charges `quantity × unit_price`. The developer forgot to validate
that quantity is positive. An attacker sets quantity to -1. The order total goes negative.
The store owes the attacker money.

### The Prefix Bypass as a Logic Flaw

The MCP vulnerability in S6 is a textbook logic flaw:

The developer's *intent*: "only allow paths that are inside the sandbox directory."

The developer's *implementation*: `path.startsWith(sandboxRoot)`

The flaw: a string-prefix match on a path is not the same as checking whether a path
is *inside* a directory. The intended semantic is containment. The implemented semantic
is string prefix. These are not equivalent when the target directory's name can be a
prefix of another directory's name.

```
Intended check:  Is /tmp/mcp_sandbox_escape/ INSIDE /tmp/mcp_sandbox/?  → NO
Implemented check: Does "/tmp/mcp_sandbox_escape/" START WITH "/tmp/mcp_sandbox"? → YES
```

The code is not buggy in any obvious way. The bug requires understanding the difference
between *string operations* and *filesystem semantics*.

### How This Appears in the MCP Study (S6)

Scenario 6 is the direct demonstration of this logic flaw.
After establishing in S1–S5 how the server behaves, I had enough understanding to
formulate the hypothesis: *if the check is a startsWith, then a sibling directory
whose name starts with the sandbox name will pass the check.*

I created `/tmp/mcp_sandbox_escape/` and requested a file from it.
The old server returned the file. Logic flaw confirmed.

The key insight is that this was *not* found by scanning for known patterns.
It was found by reasoning about the code's logic based on observations of behaviour.
This is why security researchers value manual analysis alongside automated tools.

### The Lesson

The most impactful vulnerabilities are often logic flaws, not injection bugs.
Finding them requires understanding the intended behaviour of the system well enough
to notice where the implementation diverges from the intent.
This is why the reconnaissance in S1–S5 was not optional — without it,
the hypothesis in S6 could not have been formed.

---

## Lecture 6 — Type Confusion and Schema Validation Failures

### The Theory

Strongly-typed languages (Java, Go, Rust) force you to declare what type a value is.
Weakly-typed languages (JavaScript, Python, PHP) allow implicit conversion between types.
This flexibility is convenient for developers but creates a class of vulnerability
where an attacker supplies a value of the *wrong type*, causing the system to behave
in unexpected or exploitable ways.

**Type juggling in PHP (classic):**
PHP's `==` operator does type coercion. The string `"0"` is considered equal to `false`.
The string `"0e12345"` is treated as a floating-point number in scientific notation (0).
So two different MD5 hashes that both start with `0e` can be treated as equal.
This broke authentication systems that compared password hashes with `==`.

**Type confusion in C/C++ (systems level):**
If a function receives a value it interprets as a pointer but the value was provided
by an attacker as an integer, the attacker can direct the program to dereference
any memory address they choose. This is a primitive for remote code execution.

**JSON type confusion (API level):**
An API expects `{ "admin": false }`. An attacker sends `{ "admin": "true" }` (a string,
not a boolean). The backend deserialises it and then checks `if (user.admin)` —
a non-empty string is truthy in JavaScript. The attacker is now admin.

### Schema Validation — The Defence

Modern systems use schema validation: before processing any input, validate that it
conforms to the expected shape. For an API endpoint that expects `{ "path": string }`,
the schema validator rejects any request where `path` is not a string before the
request ever reaches the business logic.

The gap between old and new versions in the MCP study is exactly this:
the old version tried to *use* wrong-typed inputs (running them through the filesystem code),
failing unpredictably; the new version *validated* them at the boundary first.

### How This Appears in the MCP Study (S7)

Scenario 7 sent wrong types as the `path` argument: integers, null, booleans, arrays, objects.

Both versions rejected all of them. The difference was *how*:

| Input | Old version behaviour | New version behaviour |
|-------|-----------------------|-----------------------|
| `path: 42` | Passed to handler, TypeError thrown internally | Schema validation error before handler |
| `path: null` | Converted to string `"null"`, ENOENT on `/mcp_sandbox/null` | Schema error, never reaches filesystem |
| `path: true` | Converted to `"true"`, ENOENT on `/mcp_sandbox/true` | Schema error |

The old version had no schema validation. It relied on the filesystem calls themselves
to eventually fail. The new version validated at the input boundary.

The reason this matters beyond correctness: the old version's error responses for wrong types
differ structurally from the new version's — different error fields, different wording.
This means an attacker can fingerprint which server version they are talking to
simply by sending `{ "path": 42 }` and reading the error shape.
That is useful reconnaissance for any attacker planning a more serious attack.

### The Lesson

Schema validation is not a luxury — it is a security boundary.
Always validate input at the point of entry, before it reaches any business logic.
The principle is called **input validation at system boundaries**: you trust nothing
that comes from outside the system until it has been verified to be the shape you expect.

---

## Lecture 7 — Patch Analysis and Exploit Variant Enumeration

### The Theory

When a vulnerability is discovered and patched, the security researcher's work is not over.
The next question is: **is the patch complete?**

A patch can fail in several ways:

1. **It fixes the symptom, not the cause.** The developer saw one specific exploit string
   and blacklisted it. Any variation of that string still works.

2. **It fixes one code path but not another.** The vulnerability was patched in
   `read_file` but not in `list_directory`. The attacker switches tools.

3. **It introduces a regression.** The fix breaks legitimate functionality —
   the cure is worse than the disease.

4. **It is correct but incomplete in scope.** The fix closes the specific variant
   that was reported but does not cover the general class of the vulnerability.

**Real-world example — HeartBleed (CVE-2014-0160):**
OpenSSL was patched quickly after HeartBleed was disclosed.
Security researchers then tested dozens of variations of the original proof-of-concept
to confirm the patch was complete and did not leave any bypass.
This is standard practice after any critical patch.

**Real-world example — Log4Shell (CVE-2021-44228):**
The initial patch for Log4Shell blocked the specific JNDI lookup string that was in
the proof-of-concept. Researchers found within days that alternative JNDI protocols
(`ldaps://`, `rmi://`, `dns://`) bypassed the initial filter.
A second patch was required, and then a third.

This is **variant enumeration**: take the confirmed exploit and generate systematic
mutations that test whether the fix addresses the class of attack or just one instance.

### How to Generate Good Variants

For a path-based vulnerability like the prefix bypass, useful mutations include:
- Trailing separator: `/sandbox_escape/` vs `/sandbox_escape`
- Duplicate separator: `/sandbox_escape//`
- Dot insertion: `/sandbox_escape/./file`
- Different suffix that still matches the prefix: `/sandbox_extra/`
- Same attack through a different tool: test both `read_file` and `list_directory`

Each mutation tests a specific assumption about how the patch was written.
If the fix is `startsWith(allowed + "/")`, all of these are blocked.
If the fix is `path !== "/tmp/mcp_sandbox_escape"`, most of these still work.

### How This Appears in the MCP Study (S8)

Scenario 8 ran 8 mutations of the prefix bypass confirmed in S6.
Every single one:
- Old version (v2025.3.28): leaked content
- New version (v2025.7.29): blocked with Access denied

This is the evidence that the patch is a real fix:
it addresses the class of attack (missing separator in prefix comparison),
not the one specific string found in the bug report.

If even one mutation had bypassed the new version, it would mean the patch was incomplete
and the developer would need to be informed.

### The Lesson

Testing a patch is as important as finding the original vulnerability.
An incomplete patch is dangerous precisely because it creates false confidence —
the developer thinks the problem is solved, defenders relax, and the remaining
bypass goes unnoticed until it is exploited.

Always enumerate variants. Test both tools. Test with and without trailing separators.
Test across different but related input classes.

---

## How the 8 Scenarios Map to Attack Theory

| Scenario | Attack Theory |
|----------|--------------|
| S1 Baseline Characterisation | Active reconnaissance — establishing the response envelope |
| S2 Error Response Analysis | Error-based information disclosure — side-channel through error messages |
| S3 Path Resolution Behaviour | Canonicalization analysis — where in the pipeline does normalisation occur? |
| S4 Malformed Input Handling | Input validation testing — fuzzing with syntactically invalid inputs |
| S5 Near-Boundary Input Testing | Known injection patterns — traversal, null byte, encoding, non-standard separators |
| S6 Semantic Boundary Violation | Logic flaw — string-prefix check does not enforce path containment |
| S7 Type Coercion Analysis | Type confusion — wrong-type inputs probe schema validation maturity |
| S8 Exploit Variant Enumeration | Patch analysis — systematic mutation to assess fix completeness |

---

## The One Principle That Ties All of This Together

Every scenario is an application of the same underlying principle:

> **A system's security is only as strong as the weakest assumption it makes about its inputs.**

S1–S4 map those assumptions explicitly.
S5 tests them against known failure modes.
S6 finds the one assumption that was wrong.
S7 and S8 characterise the boundaries of that wrong assumption.

The CVE was not found by luck or by running a scanner.
It was found by systematically building a model of the system's behaviour
and then reasoning about where the model could be exploited.
That process — reconnaissance, hypothesis, test, refine — is the scientific method
applied to security research.
