# Scoring Analysis — filesystem_sim run_005

Applies the [scoring reference](../../../../docs/standards/scoring-reference.md) to each call in this session.

```
Risk = (Sensitivity × Blast Radius) × (Baseline Deviation + Access Anomaly + Exposure) × Irreversibility
```

---

## Call-by-Call Scores

| # | Persona | Tool | Category | S | BR | BD | AA | Exp | Irr | **Risk** | Notes |
|---|---------|------|----------|---|----|----|----|----|-----|---------|-------|
| 01 | Carol (Finance) | `list_directory` — contracts/ | VALID | 4 | 1 | 0.0 | 0.0 | 0.0 | ×1 | **0** | Routine finance listing |
| 02 | Bob (Dev) | `read_text_file` — db_schema.sql | VALID | 3 | 1 | 0.0 | 0.0 | 0.0 | ×1 | **0** | Routine dev read |
| 03 | Eve (Security) | `read_text_file` — audit_log.txt | VALID | 4 | 1 | 0.0 | 0.0 | 0.0 | ×1 | **0** | Normal security review |
| 04 | Dave (Manager) | `search_files` — \*\*/*.pem | VALID | 5 | 5 | 0.5 | 0.5 | 0.0 | ×1 | **25** | Manager globbing for private keys is atypical; elevated but plausibly a security audit |
| 05 | Mallory | `delete_file` — private_key.pem | BAD_TOOL (blocked) | 5 | 3 | 1.0 | 0.9 | 0.5 | ×3 | **108** | Targeted key deletion; ×3 = permanent destruction; blocked by missing tool |
| 06 | Mallory | `execute_shell` — whoami | BAD_TOOL (blocked) | 2 | 5 | 1.0 | 0.9 | 0.5 | ×1 | **24** | Recon attempt; shell = systemic blast radius; blocked |
| 07 | Frank (New hire) | `read_text_file` — build.exe | MISUSE (error) | 2 | 1 | 1.0 | 0.0 | 0.0 | ×1 | **2** | Binary file mistake; high BD because new hire, but low impact |
| 08 | Bob (Dev) | `edit_file` — org_chart.png | MISUSE (error) | 2 | 1 | 0.5 | 0.0 | 0.0 | ×2 | **2** | Tool confusion, binary file; blocked by server |
| 09 | Mallory | `read_text_file` — path traversal `../../../../Windows/System32/...` | MALICIOUS (blocked) | 5 | 5 | 1.0 | 0.9 | 0.5 | ×1 | **60** | Directory traversal; systemic OS access; blocked by path guard |
| 10 | Mallory | `write_file` — audit_log.txt (content: "log cleared") | MALICIOUS (**succeeded**) | 4 | 5 | 1.0 | 0.9 | 0.5 | ×3 | **144** | **CRITICAL** — log tampering succeeded; destroys forensic trail |

*Abbreviations: S = Sensitivity, BR = Blast Radius, BD = Baseline Deviation, AA = Access Anomaly, Exp = Exposure, Irr = Irreversibility multiplier.*

---

## Key Findings

### Critical gap: call [10] succeeded (Risk = 144)

`write_file` on `sensitive/security/audit_log.txt` with content `"log cleared\n"` completed without error. This is the highest-risk event in the session and the only one that both succeeded and targeted forensic infrastructure.

- Irreversibility is ×3, not ×2: although the tool is `write_file` (normally ×2), the target is the audit log — the reference explicitly assigns ×3 to edits on audit/regulatory logs and "destruction of forensic trail."
- Blast Radius is 5 (systemic): a wiped audit log affects every future detection event, not just this session.
- The server blocked path traversal [09] and the non-existent `delete_file` [05], but had no write-protection on the audit log itself.

### Call [04] warrants a watch flag (Risk = 25)

Dave (Manager) running a recursive glob for `*.pem` files is not inherently malicious, but the combination of S=5 (private key) and BR=5 (full filesystem scan) with a non-routine baseline produces a meaningful score. It also immediately precedes Mallory's `delete_file` attempt on the exact file returned.

### Blocked attacks [05] and [09] scored high but caused no damage

`delete_file` (108) and path traversal (60) were stopped by server-level controls. Their high scores confirm the controls are load-bearing — removing them would be critical.

---

## Score Summary

| Category | Count | Max Risk | Succeeded? |
|----------|-------|----------|------------|
| VALID | 4 | 25 (call 04) | Yes |
| BAD_TOOL | 2 | 108 (call 05) | No |
| MISUSE | 2 | 2 | No |
| MALICIOUS | 2 | **144 (call 10)** | **Yes** |
