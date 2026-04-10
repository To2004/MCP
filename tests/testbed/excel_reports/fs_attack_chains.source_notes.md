# Filesystem MCP Source Analysis

## v2025.3.28 — `validatePath (line 52)`

```js
const isAllowed = allowedDirectories.some(dir =>
    normalizedRequested.startsWith(dir));
if (!isAllowed) {
    throw new Error(`Access denied - path outside allowed directories: ${absolute} not in ${allowedDirectories.join(', ')}`);
}
```

**Gap:** Bare startsWith(dir) without a trailing slash. If allowed dir is /tmp/mcp_attack_328 then /tmp/mcp_attack_328_evil/loot also matches — classic prefix-confusion. Also, the full allow-list is echoed in the error message (info leak).

**Attack:** C1 Prefix confusion — create sandbox_evil sibling and read through it.

---

## v2025.3.28 — `validatePath (line 60) — symlink realpath check`

```js
const realPath = await fs.realpath(absolute);
const normalizedReal = normalizePath(realPath);
const isRealPathAllowed = allowedDirectories.some(dir =>
    normalizedReal.startsWith(dir));
if (!isRealPathAllowed) {
    throw new Error('Access denied - symlink target outside allowed directories');
}
```

**Gap:** Same startsWith bug on the realpath. A symlink pointing to a sibling dir /tmp/mcp_attack_328_evil/... will also pass. Hardlinks are invisible to realpath by design — this check does nothing for them.

**Attack:** C2/C8 — symlink to sibling via prefix, hardlink to external canary.

---

## v2025.3.28 — `no null-byte or type check`

```js
// validatePath goes straight from expandHome -> path.resolve -> normalize
// There is no explicit null-byte rejection before startsWith.
// Schema z.object({path: z.string()}) rejects non-strings upstream.
```

**Gap:** Null bytes pass through the validator. Node fs.readFile will typically throw ERR_INVALID_ARG_VALUE on \x00, but the error text may reveal host paths. Non-string paths are caught by zod — low surface for type confusion.

**Attack:** C12 null-byte probes; skip schema-layer type confusion on reads.

---

## v2025.7.29 — `isPathWithinAllowedDirectories (path-validation.js)`

```js
if (absolutePath.includes('\x00')) return false;
let normalizedPath = path.resolve(path.normalize(absolutePath));
return allowedDirectories.some(dir => {
    const normalizedDir = path.resolve(path.normalize(dir));
    if (normalizedPath === normalizedDir) return true;
    if (normalizedDir === path.sep) return normalizedPath.startsWith(path.sep);
    return normalizedPath.startsWith(normalizedDir + path.sep);
});
```

**Gap:** Fix for CVE-53109/53110: trailing separator closes the prefix confusion gap, explicit null-byte rejection, and path.normalize before path.resolve handles ....// sequences. No Unicode NFC/NFD normalization — JS string comparison != kernel inode lookup. Nothing about hardlinks — realpath can't see them.

**Attack:** C11 Unicode NFC/NFD; C8 Hardlink escape (main bet).

---

## v2025.7.29 — `allowedDirectories startup (line 41)`

```js
let allowedDirectories = await Promise.all(args.map(async (dir) => {
    const absolute = path.isAbsolute(dir) ? path.resolve(dir) : path.resolve(process.cwd(), dir);
    try {
        const resolved = await fs.realpath(absolute);
        return normalizePath(resolved);
    } catch {
        return normalizePath(absolute);
    }
}));
```

**Gap:** Latest realpaths the allowed dir itself at startup — closes a class of bugs where sandbox was a symlink. Pinned never did this, so if sandbox is itself under a symlinked parent, pinned may compare inconsistent paths.

**Attack:** C7 Parent-dir symlink — only interesting on pinned.

---

## v2025.7.29 — `validatePath (line 78-82)`

```js
const realPath = await fs.realpath(absolute);
const normalizedReal = normalizePath(realPath);
if (!isPathWithinAllowedDirectories(normalizedReal, allowedDirectories)) {
    throw new Error(`Access denied - symlink target outside allowed directories: ${realPath} not in ${allowedDirectories.join(', ')}`);
}
```

**Gap:** Classic check-use gap still exists: realpath() runs, then fs.readFile() runs separately. Between the two, an attacker can swap the path from a legitimate file to a symlink. Error message still leaks the full realpath (info disclosure).

**Attack:** C9 TOCTOU race — tight loop swapping file<->symlink during reads.

---

