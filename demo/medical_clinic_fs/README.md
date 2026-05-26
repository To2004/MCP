# Medical Clinic Demo Filesystem

Small fake medical-clinic file tree served by the Anthropic filesystem MCP server.
Used as a target for benign, misuse, and malicious agent session traces.
All content is fictional — no real patients, staff, or credentials.

## Layout

| Folder | Sensitivity |
|--------|-------------|
| patients/ | HIGH — patient PHI |
| scans/ | HIGH — diagnostic images |
| billing/ | MEDIUM — invoices |
| policies/ | LOW — public notices |
| staff_directory.txt | LOW |

## Running the MCP server

```bash
npx -y @modelcontextprotocol/server-filesystem demo/medical_clinic_fs_work
```
