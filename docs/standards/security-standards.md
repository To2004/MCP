# Security Standards

Since this is a security tooling project, our own code must follow strong
security practices.

## Secrets and Credentials

- **Never** commit secrets, API keys, tokens, or passwords
- Use environment variables or config files (gitignored) for sensitive values
- If a test needs credentials, use fixtures with dummy values
- Add sensitive file patterns to `.gitignore`

## Input Validation

- Validate all external input (user input, file contents, API responses)
- Use allowlists over denylists where possible
- Sanitize strings before using them in shell commands, queries, or file paths
- Never use `eval()`, `exec()`, or `os.system()` with untrusted input

## Subprocess Safety

When executing external commands:

```python
# Good — use a list, not a string
import subprocess
result = subprocess.run(["nmap", "-p", str(port), host], capture_output=True)

# Avoid — shell=True with user input is command injection
result = subprocess.run(f"nmap -p {port} {host}", shell=True)
```

## Dependency Management

- Minimize runtime dependencies — fewer deps = smaller attack surface
- Review new dependencies before adding them
- Use `uv` lock file to pin versions
- Periodically audit dependencies for known vulnerabilities

## File Operations

- Use `pathlib.Path` for path manipulation
- Validate file paths to prevent directory traversal
- Use `with` statements for file handles
- Set appropriate permissions on created files

## Error Messages

- Don't leak sensitive information in error messages
- Log sufficient detail for debugging without exposing internals
- Distinguish between user-facing messages and debug logs

## Code Review Focus Areas

When reviewing security-related code, pay extra attention to:
- Input handling and validation
- Subprocess calls
- File system operations
- Network operations
- Serialization/deserialization
- Authentication and authorization logic
