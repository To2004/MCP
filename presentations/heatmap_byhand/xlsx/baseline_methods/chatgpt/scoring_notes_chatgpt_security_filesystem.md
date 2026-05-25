# Filesystem MCP — Scoring Notes

**Variant:** ChatGPT (gpt-4o) — security analyst, NIST SP 800-30 + OWASP LLM Top 10
**Generated:** 2026-05-25 07:24 UTC

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| read_file | Critical | Unauthorized access to sensitive files can lead to data breaches. |
| write_file | Critical | Modifying files can introduce malicious code or corrupt data. |
| edit_file | Critical | Editing files can alter critical configurations or data integrity. |
| create_dir | High | Creating directories can be used to store unauthorized data. |
| list_dir | High | Listing directories can reveal sensitive file structures. |
| move_file | High | Moving files can disrupt file organization and access controls. |
| search | Medium | Searching can be used to locate sensitive information. |
| get_file_info | Medium | Accessing file metadata can reveal sensitive information. |

## File Types

| Filetype | Risk Level | Reasoning |
|---|---|---|
| .sys | Critical | System files are crucial for OS integrity and security. |
| .exe | Critical | Executable files can be used to run malicious code. |
| .bash | High | Bash scripts can automate harmful actions. |
| .code | High | Source code files can contain proprietary algorithms. |
| .sql | High | SQL files can contain sensitive database queries. |
| .xlsx | Medium | Spreadsheets can contain sensitive business data. |
| .docx | Medium | Documents can contain confidential information. |
| .pdf | Medium | PDFs can contain sensitive reports or contracts. |
| .csv | Medium | CSV files can contain large datasets of sensitive information. |
| .md | Low | Markdown files are typically used for documentation. |
| .png | Low | Image files generally pose low risk unless they contain sensitive information. |
| .txt | Low | Text files are often used for non-sensitive information. |

## Folders

| Folder | Risk Level | Reasoning |
|---|---|---|
| Sensitive Docs | Critical | Contains highly confidential documents. |
| Security Evidence | Critical | Contains evidence related to security incidents. |
| Source Code | High | Contains proprietary source code. |
| QA Test Plans | Medium | Contains test plans that could reveal system vulnerabilities. |
| Shared Proj Dir | Medium | Contains shared project files that may include sensitive data. |
| Eval Data | Medium | Contains evaluation data that could be sensitive. |
| Onboarding | Low | Contains onboarding materials with low sensitivity. |
| Public | Low | Contains publicly accessible information. |
