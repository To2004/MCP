# Filesystem MCP — Scoring Notes

**Variant:** ChatGPT (gpt-4o) — plain, no system prompt
**Generated:** 2026-05-25 07:24 UTC

## Tools

| Tool | Risk Level | Reasoning |
|---|---|---|
| read_file | High | Reading sensitive files can lead to data exposure. |
| write_file | Critical | Writing to files can alter critical data or introduce vulnerabilities. |
| edit_file | Critical | Editing files can modify sensitive information or system configurations. |
| create_dir | Medium | Creating directories can lead to unauthorized data storage. |
| list_dir | Medium | Listing directories can reveal the structure of sensitive data. |
| move_file | High | Moving files can result in data misplacement or unauthorized access. |
| search | High | Searching can expose sensitive information across files. |
| get_file_info | Medium | Accessing file metadata can reveal sensitive information. |

## File Types

| Filetype | Risk Level | Reasoning |
|---|---|---|
| .sys | Critical | System files are crucial for OS integrity and security. |
| .exe | Critical | Executable files can run malicious code if tampered with. |
| .bash | High | Bash scripts can automate harmful actions if altered. |
| .code | High | Source code files may contain proprietary or sensitive logic. |
| .sql | High | SQL files can contain sensitive database queries and data. |
| .xlsx | Medium | Excel files may contain sensitive business data. |
| .docx | Medium | Word documents can contain confidential information. |
| .pdf | Medium | PDFs can include sensitive reports or contracts. |
| .csv | Medium | CSV files can store large amounts of structured data. |
| .md | Low | Markdown files are typically used for documentation. |
| .png | Low | Image files generally contain non-sensitive visual data. |
| .txt | Low | Text files often contain non-sensitive information. |

## Folders

| Folder | Risk Level | Reasoning |
|---|---|---|
| Sensitive Docs | Critical | Contains highly sensitive documents. |
| Security Evidence | Critical | Holds evidence related to security incidents. |
| Source Code | High | Contains proprietary source code. |
| QA Test Plans | Medium | Includes test plans that may reveal system vulnerabilities. |
| Shared Proj Dir | Medium | Shared directories can contain collaborative work data. |
| Eval Data | Medium | Evaluation data may include sensitive analysis results. |
| Onboarding | Low | Contains general onboarding materials. |
| Public | Low | Public folder intended for non-sensitive information. |
