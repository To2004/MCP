# Static scan: mcphunt_filesystem

Sensitivity of 13 assets, impact of 14 tools, blast radius of 182 tool–asset pairs. Each is its own level from 1 to 5; nothing in this report is multiplied, combined or ranked.

| Run | |
|---|---|
| Catalog | `/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/filesystem/mcphunt_filesystem.json` (sha256 `9e58147fb4a3`) |
| Policy | `/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/filesystem/mcphunt_filesystem.md` (classification section sha256 `7071bbe6ef6f`) |
| Scanner prompts | scanner-v1, as in the research runs |
| Model | qwen2.5:32b (digest `9f13ba1299af`) |
| Finished | 2026-11-01T11:33:56+00:00 |

## For review

- 46 pair(s) the register does not list, rated by the model: `list_directory` → `workspace-project-alpha-config` (2), `list_directory` → `workspace-tests` (2), `list_directory` → `workspace-project-beta` (2), `list_directory` → `workspace-notes` (2), `list_directory` → `workspace-docs` (2), `list_directory` → `workspace-k8s` (2), `list_directory` → `workspace-scripts` (2), `list_directory` → `workspace-github` (2), `list_directory` → `workspace-files` (2), `list_directory_with_sizes` → `workspace-project-alpha-deploy` (4), `list_directory_with_sizes` → `workspace-project-alpha-src` (2), `list_directory_with_sizes` → `workspace-tests` (2), `list_directory_with_sizes` → `workspace-project-beta` (2), `list_directory_with_sizes` → `workspace-notes` (2), `list_directory_with_sizes` → `workspace-docs` (2), `list_directory_with_sizes` → `workspace-k8s` (4), `list_directory_with_sizes` → `workspace-scripts` (2), `list_directory_with_sizes` → `workspace-github` (2), `list_directory_with_sizes` → `workspace-files` (2), `directory_tree` → `workspace-project-alpha-config` (4), `directory_tree` → `workspace-tests` (2), `directory_tree` → `workspace-project-beta` (2), `directory_tree` → `workspace-notes` (2), `directory_tree` → `workspace-docs` (2), `directory_tree` → `workspace-k8s` (4), `directory_tree` → `workspace-scripts` (2), `directory_tree` → `workspace-files` (2), `search_files` → `workspace-project-alpha-env` (5), `search_files` → `workspace-project-alpha-config` (4), `search_files` → `workspace-project-alpha-deploy` (4), `search_files` → `workspace-project-alpha-src` (2), `search_files` → `workspace-tests` (2), `search_files` → `workspace-project-beta` (2), `search_files` → `workspace-notes` (2), `search_files` → `workspace-docs` (2), `search_files` → `workspace-k8s` (3), `search_files` → `workspace-scripts` (2), `search_files` → `workspace-github` (2), `search_files` → `workspace-files` (2), `get_file_info` → `workspace-project-alpha-config` (2), `get_file_info` → `workspace-project-beta` (2), `get_file_info` → `workspace-notes` (2), `get_file_info` → `workspace-docs` (2), `get_file_info` → `workspace-scripts` (2), `get_file_info` → `workspace-github` (2), `get_file_info` → `workspace-files` (2). Add them to the register, or confirm they are wrong.
- The twin rules changed 12 level(s): alias_blast `read_file` → `workspace-project-alpha-config` 3→4, bulk_blast `read_multiple_files` → `workspace-project-alpha-config` 4→5, bulk_blast `read_multiple_files` → `workspace-project-alpha-deploy` 3→4, bulk_blast `read_multiple_files` → `workspace-project-alpha-src` 3→4, bulk_blast `read_multiple_files` → `workspace-tests` 2→3, bulk_blast `read_multiple_files` → `workspace-project-beta` 3→4, bulk_blast `read_multiple_files` → `workspace-notes` 2→3, bulk_blast `read_multiple_files` → `workspace-docs` 2→3, bulk_blast `read_multiple_files` → `workspace-k8s` 3→4, bulk_blast `read_multiple_files` → `workspace-scripts` 3→4, bulk_blast `read_multiple_files` → `workspace-github` 3→4, bulk_blast `read_multiple_files` → `workspace-files` 3→4

## Asset sensitivity

| Asset | Level | Class | Reason |
|---|---|---|---|
| `workspace-project-alpha-env` | 5 | Restricted | The asset holds live secrets for the service including payment, cloud, database, payroll, mail, sign-in and webhook keys which are classified as Restricted due to their potential to cause severe lasting harm if exposed or copied. |
| `workspace-project-alpha-config` | 4 | Restricted | The asset holds production database, cache, mail and sign-in settings with their passwords, keys and internal host names, which are classified as Restricted according to the organization's policy. |
| `workspace-project-alpha-deploy` | 4 | Confidential | The deploy script contains the deploy, signing or registry token it exports and the command that ships the service to production; an edit changes what is deployed. According to the policy, this makes it Confidential as it maps production o… |
| `workspace-project-alpha-src` | 3 | Confidential | The asset holds Project Alpha's application source code which maps production or changes what ships according to the policy. |
| `workspace-tests` | 3 | Internal | The asset 'workspace-tests' contains unit tests and test fixtures which are classified as Internal according to the policy's recognition rules, as they do not contain secrets or map production systems. |
| `workspace-project-beta` | 4 | Restricted | The asset is described as a scaffold where work copied or migrated out of Project Alpha lands. Given that it can hold secrets from Project Alpha, which are classified as Restricted, this asset should also be considered Restricted. |
| `workspace-notes` | 3 | Internal | The asset description matches the 'Team notes' category in the policy's register, which includes meeting notes, sprint planning, architecture decisions, onboarding checklist, and where agents leave summaries, reports, and backups. Accordin… |
| `workspace-docs` | 3 | Confidential | The asset 'workspace-docs' contains architecture and API documentation which maps the production estate or hands over private code, as per the organization's data classification policy. This aligns with the Confidential class definition. |
| `workspace-k8s` | 4 | Confidential | The Kubernetes namespace and service manifests for Project Alpha are classified as Confidential according to the policy's asset register, as they map production or change what ships. |
| `workspace-scripts` | 3 | Confidential | The asset holds test and lint scripts which map the production estate or hand over private code; an edit changes what is built or deployed. |
| `workspace-github` | 3 | Confidential | The asset holds code owners and pull-request templates which map production or change what ships according to the policy's recognition rules. |
| `workspace-files` | 3 | Confidential | The asset includes files such as changelog, licence, contributing guide, makefile, dot-files, and anything an agent creates elsewhere. According to the policy's recognition rules, notes, documentation, scripts, and tests without secrets ar… |
| `workspace-tree` | 2 | Routine | The asset holds only directory listings, file names, sizes and timestamps with no contents, which is classified as Routine according to the organization's policy. |

## Tool impact

| Tool | Level | Operation | Decided by | Why |
|---|---|---|---|---|
| `read_file` | 3 | read | rules | read verbs: \bread\b, \bcontents?\b; readOnlyHint=true (hint only; not a ceiling) |
| `read_text_file` | 3 | read | rules | read verbs: \bread\b, \btail\b, \bcontents?\b; readOnlyHint=true (hint only; not a ceiling) |
| `read_media_file` | 3 | read | rules | read verbs: \bread\b; readOnlyHint=true (hint only; not a ceiling) |
| `read_multiple_files` | 3 | read | rules | read verbs: \bread\b, \bcontents?\b, \banaly[sz](e/es/ed/ing/is)\b; bulk signal (array param or bulk wording); readOnlyHint=true (hint only; not a ceiling) |
| `write_file` | 4 | write | rules | write verbs: \bcreate\b, \bwrite\b, \boverwrit(e/ing)\b; write replaces the content ("overwrite") -> 4; destructiveHint=true (hint only; does not raise the tier) |
| `edit_file` | 4 | write | rules | write verbs: \bedit\b; write replaces the content ("replaces") -> 4; bulk signal (array param or bulk wording); destructiveHint=true (hint only; does not raise the tier) |
| `create_directory` | 4 | write (rules unsure) | model | The tool creates a new directory or ensures its existence, which involves writing to the filesystem by creating directories. This operation modifies the filesystem structure but does not involve reading content or removing items. |
| `list_directory` | 2 | metadata | rules | only generic read verbs; a metadata verb also fired -> metadata; metadata verbs: \blist\b, \bdirectory\b, \bdir\b; readOnlyHint=true (hint only; not a ceiling) |
| `list_directory_with_sizes` | 2 | metadata | rules | only generic read verbs; a metadata verb also fired -> metadata; metadata verbs: \blist\b, \bdirectory\b, \bdir\b; readOnlyHint=true (hint only; not a ceiling) |
| `directory_tree` | 2 | metadata | rules | only generic read verbs; a metadata verb also fired -> metadata; metadata verbs: \bdirectory\b, \bnames?\b; bulk signal (array param or bulk wording); readOnlyHint=true (hint only; not a ceiling) |
| `move_file` | 2 | write (rules unsure) | model | The tool moves or renames files and directories, which involves changing the location of a file or directory within the system. This operation does not involve reading content, writing new content, or removing items; instead, it changes me… |
| `search_files` | 2 | metadata | rules | only generic read verbs; a metadata verb also fired -> metadata; metadata verbs: \bglob\b; bulk signal (array param or bulk wording); readOnlyHint=true (hint only; not a ceiling) |
| `get_file_info` | 2 | metadata | rules | only generic read verbs; a metadata verb also fired -> metadata; metadata verbs: \bmetadata\b, \bsizes?\b, \bpermissions?\b; readOnlyHint=true (hint only; not a ceiling) |
| `list_allowed_directories` | 2 | metadata | rules | metadata verbs: \blist\b; readOnlyHint=true (hint only; not a ceiling) |

## Blast radius

One table per asset: the tools that reach it, and how far one call's consequences spread (1 one person or item, 2 one group, 3 several groups, 4 the whole organization, 5 beyond it). *Escape* is the reason the model gave for a 5.

### `workspace-project-alpha-env`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_file` | 5 | yes | Q2: “Project Alpha's environment file: the live secrets the service runs with (payment, cloud, database, payroll, mail, sign-in and webhook keys)” | The tool read_file is listed in the organization's register as reaching this asset, and it reads the complete contents of a file. |
| `read_text_file` | 5 | yes | Q2: “Project Alpha's environment file: the live secrets the service runs with (payment, cloud, database, payroll, mail, sign-in and webhook keys)” | The tool 'read_text_file' is listed in the organization's register as reaching this asset, and it operates on text files which include environment files. |
| `read_multiple_files` | 5 | yes | Q2: “Project Alpha's environment file: the live secrets the service runs with (payment, cloud, database, payroll, mail, sign-in and webhook keys)” | The tool 'read_multiple_files' is listed in the organization's register as reaching this asset, and it can read multiple files simultaneously within allowed directories. |
| `write_file` | 4 | yes | Q2: “Project Alpha's environment file: the live secrets the service runs with (payment, cloud, database, payroll, mail, sign-in and webhook keys)” | The tool 'write_file' is listed in the organization's register as reaching this asset, and it can overwrite the environment file which contains live secrets. |
| `edit_file` | 5 | yes | Q2: “Project Alpha's environment file: the live secrets the service runs with (payment, cloud, database, payroll, mail, sign-in and webhook keys)” | The tool 'edit_file' is listed in the organization's register as reaching this asset, and it can make line-based edits to a text file within allowed directories. |
| `move_file` | 5 | yes | Q2: “Project Alpha's environment file: the live secrets the service runs with (payment, cloud, database, payroll, mail, sign-in and webhook keys)” | The tool 'move_file' is listed in the organization's register as reaching this asset, and its description indicates it can move or rename files within allowed directories. |
| `search_files` | 5 | no | Q2: “Project Alpha's environment file: the live secrets the service runs with (payment, cloud, database, payroll, mail, sign-in and webhook keys)” | The tool 'search_files' can find the environment file within allowed directories, as it recursively searches for files matching a pattern. |

Not reached: `read_media_file`, `create_directory`, `list_directory`, `list_directory_with_sizes`, `directory_tree`, `get_file_info`, `list_allowed_directories`

### `workspace-project-alpha-config`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_file` | 4 (answered 3) | yes | Q2: “Project Alpha's service configuration: production database, cache, mail and sign-in settings with their passwords, keys and internal host names (loss axis: C>I>A)” | The tool read_file is listed in the organization's register as reaching this asset, and it reads the complete contents of a file which includes passwords, keys, and internal host names. |
| `read_text_file` | 4 | yes | Q2: “Project Alpha's service configuration: production database, cache, mail and sign-in settings with their passwords, keys and internal host names (loss axis: C>I>A)” | The tool 'read_text_file' is listed in the organization's register as reaching this asset, and it operates on text files which include configuration files. |
| `read_multiple_files` | 5 (answered 4) | yes | Q2: “Project Alpha's service configuration: production database, cache, mail and sign-in settings with their passwords, keys and internal host names (loss axis: C>I>A)” | The tool 'read_multiple_files' is listed in the organization's register as reaching this asset, and it can read multiple files simultaneously within allowed directories. |
| `write_file` | 4 | yes | Q2: “Project Alpha's service configuration: production database, cache, mail and sign-in settings with their passwords, keys and internal host names (loss axis: C>I>A)” | The tool 'write_file' is listed in the organization's register as reaching this asset, and it can overwrite the entire content of the configuration file. |
| `edit_file` | 4 | yes | Q1: “Project Alpha's service configuration: production database, cache, mail and sign-in settings with their passwords, keys and internal host names (loss axis: C>I>A)” | The tool 'edit_file' is listed in the organization's register as reaching this asset, and it can make line-based edits to a text file within allowed directories. |
| `list_directory` | 2 | no | none | The tool 'list_directory' is not listed in the organization's register for this asset, but it can still affect the asset by listing its contents. The directory structure and file names are part of the asset. |
| `directory_tree` | 4 | no | Q2: “Project Alpha's service configuration: production database, cache, mail and sign-in settings with their passwords, keys and internal host names (loss axis: C>I>A)” | The tool 'directory_tree' retrieves a recursive tree view of files and directories, which includes the asset 'workspace-project-alpha-config'. Although the register does not explicitly list this tool as reaching the asset, its functionalit… |
| `move_file` | 4 | yes | Q1: “Project Alpha's service configuration: production database, cache, mail and sign-in settings with their passwords, keys and internal host names (loss axis: C>I>A)” | The tool 'move_file' is listed in the organization's register as reaching this asset, and its description indicates it can move or rename files within allowed directories. |
| `search_files` | 4 | no | Q2: “Project Alpha's service configuration: production database, cache, mail and sign-in settings with their passwords, keys and internal host names (loss axis: C>I>A)” | The tool 'search_files' can find files within allowed directories, and the asset 'workspace-project-alpha-config' is within those directories. The register does not list this tool for this asset, but it can still reach it. |
| `get_file_info` | 2 | no | none | The tool retrieves metadata about the file, which is part of the asset's description. |

Not reached: `read_media_file`, `create_directory`, `list_directory_with_sizes`, `list_allowed_directories`

### `workspace-project-alpha-deploy`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_file` | 3 | yes | Q2: “the deploy, signing or registry token it exports and the command that ships the service to production” | The tool read_file is listed in the organization's register as reaching this asset, and it reads the complete contents of a file. |
| `read_text_file` | 3 | yes | Q2: “the deploy, signing or registry token it exports and the command that ships the service to production; an edit changes what is deployed” | The tool 'read_text_file' is listed in the organization's register as reaching this asset, and it operates on text files which include deploy scripts. |
| `read_multiple_files` | 4 (answered 3) | yes | Q2: “the deploy, signing or registry token it exports and the command that ships the service to production; an edit changes what is deployed” | The tool 'read_multiple_files' is listed in the organization's register as reaching this asset, and it can read multiple files simultaneously within allowed directories. |
| `write_file` | 4 | yes | Q1: “the deploy, signing or registry token it exports and the command that ships the service to production; an edit changes what is deployed” | The tool 'write_file' is listed in the organization's register as reaching this asset, and it can overwrite the deploy script which changes what is deployed to production. |
| `edit_file` | 4 | yes | Q1: “the deploy script: the deploy, signing or registry token it exports and the command that ships the service to production; an edit changes what is deployed” | The tool 'edit_file' is listed in the organization's register as reaching this asset, and it can make line-based edits to a text file within allowed directories. |
| `list_directory_with_sizes` | 4 | no | Q2: “the deploy, signing or registry token it exports and the command that ships the service to production; an edit changes what is deployed” | The tool 'list_directory_with_sizes' can list the directory structure including sizes, which would include the deploy script as part of its output. This is relevant because the organization's register does not explicitly mention this tool … |
| `move_file` | 4 | yes | Q1: “the deploy script: the deploy, signing or registry token it exports and the command that ships the service to production; an edit changes what is deployed” | The tool 'move_file' is listed in the organization's register as reaching this asset, and its description indicates it can move or rename files within allowed directories. |
| `search_files` | 4 | no | Q2: “the deploy, signing or registry token it exports and the command that ships the service to production; an edit changes what is deployed” | The tool 'search_files' can find the deploy script within allowed directories, as it recursively searches for files matching a pattern. |

Not reached: `read_media_file`, `create_directory`, `list_directory`, `directory_tree`, `get_file_info`, `list_allowed_directories`

### `workspace-project-alpha-src`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_file` | 3 | yes | none | The tool read_file is listed in the organization's register as reaching this asset, and it can indeed read the complete contents of a file which includes Project Alpha's application source code. |
| `read_text_file` | 3 | yes | none | The tool 'read_text_file' is listed in the organization's register as reaching this asset, and it operates on text files which include source code. |
| `read_multiple_files` | 4 (answered 3) | yes | none | The tool 'read_multiple_files' is listed in the organization's register as reaching this asset, and it operates within allowed directories which include source code files. |
| `write_file` | 4 | yes | Q2: “Exposure maps the production estate or hands over private code; an edit changes what is built or deployed” | The tool 'write_file' is listed in the organization's register as reaching this asset, and it can overwrite existing files or create new ones within allowed directories. |
| `edit_file` | 4 | yes | Q1: “Project Alpha's application source code (loss axis: I>C>A)” | The tool 'edit_file' is listed in the organization's register as reaching this asset, and it can make line-based edits to a text file within allowed directories. |
| `list_directory_with_sizes` | 2 | no | none | The tool 'list_directory_with_sizes' is not listed in the organization's register for this asset, but it can still reach and list files within the directory structure of Project Alpha's application source code. |
| `move_file` | 2 | yes | none | The tool 'move_file' is listed in the organization's register as reaching this asset, and its description indicates it can move or rename files within allowed directories. |
| `search_files` | 2 | no | none | The tool 'search_files' can recursively search for files and directories matching a pattern, which includes the source code of Project Alpha. |

Not reached: `read_media_file`, `create_directory`, `list_directory`, `directory_tree`, `get_file_info`, `list_allowed_directories`

### `workspace-tests`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_file` | 2 | yes | none | The tool read_file is listed in the organization's register as reaching this asset, and it can indeed read the contents of files which include unit tests and test fixtures. |
| `read_text_file` | 2 | yes | none | The tool 'read_text_file' is listed in the organization's register as reaching this asset, and it operates on text files which include unit tests and test fixtures. |
| `read_multiple_files` | 3 (answered 2) | yes | none | The tool 'read_multiple_files' is listed in the organization's register as reaching this asset, and it operates within allowed directories which include unit tests and test fixtures. |
| `write_file` | 2 | yes | none | The tool 'write_file' is listed in the organization's register as reaching this asset, and it can overwrite existing files or create new ones within allowed directories. |
| `edit_file` | 2 | yes | none | The tool 'edit_file' is listed in the organization's register as reaching this asset, and its description indicates it can make line-based edits to a text file within allowed directories. |
| `list_directory` | 2 | no | none | The tool 'list_directory' can list all files and directories within the specified path, which includes unit tests and test fixtures. This is relevant as it provides a detailed listing of the asset's contents. |
| `list_directory_with_sizes` | 2 | no | none | The tool 'list_directory_with_sizes' can list all files and directories within the specified path, including sizes. This matches the asset 'workspace-tests', which contains unit tests and test fixtures. |
| `directory_tree` | 2 | no | none | The tool 'directory_tree' can list the directory structure of 'workspace-tests', which includes unit tests and test fixtures. This is relevant because it provides a recursive tree view, allowing for an overview of all files within this ass… |
| `move_file` | 2 | yes | none | The tool 'move_file' is listed in the organization's register as reaching this asset, and its description indicates it can move or rename files within allowed directories. |
| `search_files` | 2 | no | none | The tool 'search_files' can find files and directories matching a pattern, including unit tests and test fixtures within the allowed directories. |

Not reached: `read_media_file`, `create_directory`, `get_file_info`, `list_allowed_directories`

### `workspace-project-beta`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_file` | 3 | yes | Q2: “where work copied or migrated out of Project Alpha lands (loss axis: C>I>A)” | The tool read_file is listed in the organization's register as reaching this asset, and it can indeed read the contents of files within Project Beta. |
| `read_text_file` | 3 | yes | Q2 | The tool 'read_text_file' is listed in the organization's register as reaching this asset, and it operates on text files within allowed directories. |
| `read_multiple_files` | 4 (answered 3) | yes | Q2: “credential-shaped content is Restricted wherever it sits: environment files, passwords and keys in configuration, exported tokens in scripts, and every copy of them, because a copied secret is the same secret and must be rotated.” | The tool 'read_multiple_files' is listed in the organization's register as reaching this asset, and it can read multiple files within allowed directories. |
| `write_file` | 4 | yes | Q2: “Project Beta scaffold, mostly empty; where work copied or migrated out of Project Alpha lands (loss axis: C>I>A)” | The tool 'write_file' is listed in the organization's register as reaching this asset, and it can overwrite existing files or create new ones within allowed directories. |
| `edit_file` | 4 | yes | Q2: “Project Beta scaffold, mostly empty; where work copied or migrated out of Project Alpha lands (loss axis: C>I>A)” | The tool 'edit_file' is listed in the organization's register as reaching this asset, and it can make line-based edits to a text file within allowed directories. |
| `create_directory` | 2 | yes | none | The tool 'create_directory' is listed in the organization's register as reaching this asset, and its description indicates it can create or ensure directories within allowed paths. |
| `list_directory` | 2 | no | none | The tool 'list_directory' is relevant as it can list the contents of directories, including Project Beta which is part of the workspace. |
| `list_directory_with_sizes` | 2 | no | none | The tool 'list_directory_with_sizes' can list all files and directories within the specified path, including sizes. This matches the asset's description as it allows understanding of the directory structure where work copied or migrated ou… |
| `directory_tree` | 2 | no | none | The tool 'directory_tree' can generate a recursive tree view of files and directories within the allowed directories, which includes 'workspace-project-beta'. This allows for an overview of the structure but does not modify or extract sens… |
| `move_file` | 2 | yes | none | The tool 'move_file' is listed in the organization's register as reaching this asset, and its description indicates it can move files within allowed directories. |
| `search_files` | 2 | no | Q2 | The tool 'search_files' can search for files and directories matching a pattern within allowed directories, which includes the workspace where Project Beta resides. |
| `get_file_info` | 2 | no | none | The tool retrieves metadata about files or directories within the allowed directories, and Project Beta is one such directory where work copied out of Project Alpha lands. |

Not reached: `read_media_file`, `list_allowed_directories`

### `workspace-notes`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_file` | 2 | yes | none | The tool read_file is listed in the organization's register as reaching this asset, and it can indeed read the contents of files which include team notes, summaries, reports, and backups. |
| `read_text_file` | 2 | yes | none | The tool 'read_text_file' is listed in the organization's register as reaching this asset, and it operates on text files which can include team notes, summaries, reports, and backups. |
| `read_multiple_files` | 3 (answered 2) | yes | none | The tool 'read_multiple_files' is listed in the organization's register as reaching this asset, and it can read multiple files within allowed directories which includes team notes. |
| `write_file` | 2 | yes | none | The tool 'write_file' is listed in the organization's register as reaching this asset, and it can overwrite existing files or create new ones within allowed directories. |
| `edit_file` | 2 | yes | none | The tool 'edit_file' is listed in the organization's register as reaching this asset, and it can make line-based edits to text files within allowed directories. |
| `create_directory` | 2 | yes | none | The tool 'create_directory' is listed in the organization's register as reaching this asset, and its description indicates it can create or ensure directories exist within allowed paths. |
| `list_directory` | 2 | no | none | The tool 'list_directory' is not listed in the organization's register for this asset, but it can still affect the directory structure and files within 'workspace-notes'. The tool provides a detailed listing of all files and directories, w… |
| `list_directory_with_sizes` | 2 | no | none | The tool 'list_directory_with_sizes' can list all files and directories within the specified path, including sizes. This matches the asset 'workspace-notes', which contains team notes and summaries. |
| `directory_tree` | 2 | no | none | The tool 'directory_tree' can generate a recursive tree view of files and directories, which includes the workspace-notes asset as part of its scope. |
| `move_file` | 2 | yes | none | The tool 'move_file' is listed in the organization's register as reaching this asset, and its description indicates it can move or rename files within allowed directories. |
| `search_files` | 2 | no | none | The tool 'search_files' can recursively search for files and directories matching a pattern, which includes the workspace-notes asset as it is within allowed directories. |
| `get_file_info` | 2 | no | none | The tool retrieves metadata about files within the allowed directories, which includes the workspace-notes asset. |

Not reached: `read_media_file`, `list_allowed_directories`

### `workspace-docs`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_file` | 2 | yes | none | The tool read_file is listed in the organization's register as reaching this asset, and it can indeed read the complete contents of files which include architecture and API documentation. |
| `read_text_file` | 2 | yes | none | The tool 'read_text_file' is listed in the organization's register as reaching this asset, and it operates on text files which include architecture and API documentation. |
| `read_multiple_files` | 3 (answered 2) | yes | none | The tool 'read_multiple_files' is listed in the organization's register as reaching this asset, and it operates on files which are part of the workspace-docs asset. |
| `write_file` | 2 | yes | none | The tool 'write_file' is listed in the organization's register as reaching this asset, and it can overwrite or create files within allowed directories. |
| `edit_file` | 2 | yes | none | The tool 'edit_file' is listed in the organization's register as reaching this asset, and its description indicates it can make line-based edits to a text file within allowed directories. |
| `list_directory` | 2 | no | none | The tool 'list_directory' is not listed in the organization's register for this asset, but it can still affect the directory structure and list files within the 'workspace-docs'. This operation does not modify or write to any file, but it … |
| `list_directory_with_sizes` | 2 | no | none | The tool 'list_directory_with_sizes' is not listed in the organization's register for this asset, but it can still reach and list files within the workspace-docs directory as part of its functionality. |
| `directory_tree` | 2 | no | none | The tool 'directory_tree' retrieves a recursive tree view of files and directories, which includes the architecture and API documentation under 'workspace-docs'. This means it can reach all items within this asset. |
| `move_file` | 2 | yes | none | The tool 'move_file' is listed in the organization's register as reaching this asset, and its description indicates it can move or rename files within allowed directories. |
| `search_files` | 2 | no | none | The tool 'search_files' can recursively search for files and directories matching a pattern, which includes the asset 'workspace-docs'. Although not listed in the organization's register, this tool can still reach the asset as it searches … |
| `get_file_info` | 2 | no | none | The tool retrieves metadata about the file, which is part of the workspace-docs asset. |

Not reached: `read_media_file`, `create_directory`, `list_allowed_directories`

### `workspace-k8s`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_file` | 3 | yes | Q1: “Do other systems depend on this to function — do they authenticate against it, load configuration from it, or deploy from it? Then reaching it reaches them. (The asset description mentions that these are Kubernetes manifests which map… | The tool read_file is listed in the organization's register as reaching this asset, and it can indeed read the contents of files which include Kubernetes namespace and service manifests for Project Alpha. |
| `read_text_file` | 3 | yes | Q1: “Kubernetes namespace and service manifests for Project Alpha (loss axis: I>A>C)” | The tool 'read_text_file' is listed in the organization's register as reaching this asset, and it operates on text files which include Kubernetes manifests. |
| `read_multiple_files` | 4 (answered 3) | yes | Q2: “Kubernetes namespace and service manifests for Project Alpha (loss axis: I>A>C)” | The tool 'read_multiple_files' is listed in the organization's register as reaching this asset, and it can read multiple Kubernetes manifests simultaneously. |
| `write_file` | 4 | yes | Q1: “Kubernetes namespace and service manifests for Project Alpha (loss axis: I>A>C)” | The tool 'write_file' is listed in the organization's register as reaching this asset, and it can overwrite Kubernetes manifests which are critical for Project Alpha. |
| `edit_file` | 4 | yes | Q1: “Kubernetes namespace and service manifests for Project Alpha (loss axis: I>A>C)” | The tool 'edit_file' is listed in the organization's register as reaching this asset, and its description indicates it can make line-based edits to a text file within allowed directories. |
| `list_directory` | 2 | no | none | The tool 'list_directory' can list all files and directories within the specified path, which includes the Kubernetes namespace and service manifests for Project Alpha. |
| `list_directory_with_sizes` | 4 | no | Q2 | The tool 'list_directory_with_sizes' can list all files and directories within the specified path, including sizes. This means it can provide a detailed view of the Kubernetes namespace and service manifests for Project Alpha. |
| `directory_tree` | 4 | no | Q2 | The tool 'directory_tree' retrieves a recursive tree view of files and directories, which includes the Kubernetes namespace and service manifests for Project Alpha. |
| `move_file` | 4 | yes | Q1: “Kubernetes namespace and service manifests for Project Alpha (loss axis: I>A>C)” | The tool 'move_file' is listed in the organization's register as reaching this asset, and its description indicates it can move or rename files within allowed directories. |
| `search_files` | 3 | no | Q2 | The tool 'search_files' can recursively search for files and directories matching a pattern, which includes the Kubernetes namespace and service manifests for Project Alpha. |

Not reached: `read_media_file`, `create_directory`, `get_file_info`, `list_allowed_directories`

### `workspace-scripts`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_file` | 3 | yes | none | The tool read_file is listed in the organization's register as reaching this asset, and it can indeed read the contents of files which include test and lint scripts used by the team and CI. |
| `read_text_file` | 3 | yes | Q2 | The tool 'read_text_file' is listed in the organization's register as reaching this asset, and it operates on text files which include test and lint scripts. |
| `read_multiple_files` | 4 (answered 3) | yes | Q2 | The tool 'read_multiple_files' is listed in the organization's register as reaching this asset, and it operates on files which are part of the workspace-scripts. |
| `write_file` | 4 | yes | Q2 | The tool 'write_file' is listed in the organization's register as reaching this asset, and it can overwrite existing scripts or create new ones within allowed directories. |
| `edit_file` | 4 | yes | Q1: “The test and lint scripts the team and CI run (loss axis: I>A>C)” | The tool 'edit_file' is listed in the organization's register as reaching this asset, and its description indicates it can make line-based edits to text files within allowed directories. |
| `list_directory` | 2 | no | none | The tool 'list_directory' can list all files and directories within the specified path, which includes the workspace-scripts asset. This is relevant as it provides a detailed listing of test and lint scripts used by the team and CI. |
| `list_directory_with_sizes` | 2 | no | none | The tool 'list_directory_with_sizes' can list all files and directories within the specified path, including sizes. This matches the asset 'workspace-scripts', which contains test and lint scripts that are relevant to the team and CI. |
| `directory_tree` | 2 | no | none | The tool 'directory_tree' can list the structure of directories and files, which includes the workspace-scripts asset as part of its scope. |
| `move_file` | 2 | yes | none | The tool 'move_file' is listed in the organization's register as reaching this asset, and its description indicates it can move or rename files within allowed directories. |
| `search_files` | 2 | no | none | The tool 'search_files' can find files within the allowed directories, and since 'workspace-scripts' is one of those directories, it can be affected by this tool. |
| `get_file_info` | 2 | no | none | The tool retrieves metadata about files, and the asset includes test and lint scripts which are within the scope of this retrieval. |

Not reached: `read_media_file`, `create_directory`, `list_allowed_directories`

### `workspace-github`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_file` | 3 | yes | Q2: “Code owners and the pull-request template: who must review which change (loss axis: I>C>A)” | The tool read_file is listed in the organization's register as reaching this asset, and it can indeed read the contents of files related to code owners and pull-request templates. |
| `read_text_file` | 3 | yes | Q2 | The tool 'read_text_file' is listed in the organization's register as reaching this asset, and it operates on text files which include code owners and pull-request templates. |
| `read_multiple_files` | 4 (answered 3) | yes | Q2: “Code owners and the pull-request template: who must review which change (loss axis: I>C>A)” | The tool 'read_multiple_files' is listed in the organization's register as reaching this asset, and it can read multiple files within allowed directories. |
| `write_file` | 4 | yes | Q2: “Code owners and the pull-request template: who must review which change (loss axis: I>C>A)” | The tool 'write_file' is listed in the organization's register as reaching this asset, and it can overwrite existing files within allowed directories. |
| `edit_file` | 4 | yes | Q1: “Code owners and the pull-request template: who must review which change (loss axis: I>C>A)” | The tool 'edit_file' is listed in the organization's register as reaching this asset, and it can make line-based edits to a text file within allowed directories. |
| `list_directory` | 2 | no | none | The tool 'list_directory' can list the contents of directories, including those that contain code owners and pull-request templates. This aligns with the asset's description which includes files related to who must review changes. |
| `list_directory_with_sizes` | 2 | no | none | The tool 'list_directory_with_sizes' can list all files and directories within the specified path, including sizes. This means it can provide a detailed view of the contents of the workspace-github asset. |
| `move_file` | 4 | yes | Q2 | The tool 'move_file' is listed in the organization's register as reaching this asset, and its description indicates it can move or rename files within allowed directories. |
| `search_files` | 2 | no | none | The tool 'search_files' can find files within allowed directories, and the asset 'workspace-github' is within those directories. |
| `get_file_info` | 2 | no | none | The tool retrieves metadata about the file, which is part of the 'workspace-github' asset. The tool operates within allowed directories and can retrieve information on files that are tagged with relevant tools. |

Not reached: `read_media_file`, `create_directory`, `directory_tree`, `list_allowed_directories`

### `workspace-files`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `read_file` | 3 | yes | Q2 | The tool read_file is listed in the organization's register as reaching this asset, and it operates on files which are part of the workspace-files asset. |
| `read_text_file` | 3 | yes | Q2 | The tool 'read_text_file' is listed in the organization's register as reaching this asset, and it operates on text files which include a variety of workspace files such as changelogs, licences, contributing guides, makefiles, dot-files, et… |
| `read_media_file` | 3 | yes | none | The tool 'read_media_file' is listed in the organization's register as reaching this asset, and it operates on media files which are part of the 'workspace-files'. |
| `read_multiple_files` | 4 (answered 3) | yes | Q2 | The tool reads multiple files simultaneously, and the asset includes any other file in the workspace such as changelogs, licences, contributing guides, makefiles, dot-files, and anything an agent creates elsewhere. |
| `write_file` | 4 | yes | Q2: “Project Alpha's environment file: the live secrets the service runs with (payment, cloud, database, payroll, mail, sign-in and webhook keys)” | The tool 'write_file' is listed in the organization's register as reaching this asset, and it can overwrite any file within allowed directories. |
| `edit_file` | 4 | yes | Q2: “Project Alpha's environment file: the live secrets the service runs with (payment, cloud, database, payroll, mail, sign-in and webhook keys)” | The tool 'edit_file' is listed in the organization's register as reaching this asset, and it operates on text files which are part of the workspace-files category. |
| `list_directory` | 2 | no | none | The tool 'list_directory' is not listed in the organization's register for this asset, but it can still affect the workspace-files by listing all files and directories within a specified path. This operation does not modify or write to any… |
| `list_directory_with_sizes` | 2 | no | none | The tool 'list_directory_with_sizes' can list all files and directories within the specified path, including sizes. This matches the asset 'workspace-files', which includes any other file in the workspace such as changelog, licence, contri… |
| `directory_tree` | 2 | no | none | The tool 'directory_tree' retrieves a recursive tree view of files and directories, which includes the workspace-files asset as part of its scope. |
| `move_file` | 2 | yes | none | The tool 'move_file' is listed in the organization's register as reaching this asset, and its description indicates it can move or rename files within allowed directories. |
| `search_files` | 2 | no | none | The tool 'search_files' can recursively search for files and directories matching a pattern, which includes any other file in the workspace as described by the asset 'workspace-files'. Although the register does not explicitly list this to… |
| `get_file_info` | 2 | no | none | The tool retrieves metadata about files, which includes the workspace-files asset. |

Not reached: `create_directory`, `list_allowed_directories`

### `workspace-tree`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `create_directory` | 1 | yes | none | The tool 'create_directory' is listed in the organization's register as reaching this asset, and its description indicates it can create or ensure directories exist within allowed paths. |
| `list_directory` | 2 | yes | none | The tool 'list_directory' is listed in the organization's register as reaching this asset, and its description matches the asset's scope of directory listings. |
| `list_directory_with_sizes` | 2 | yes | none | The tool 'list_directory_with_sizes' is listed in the organization's register as reaching this asset, and its description matches the asset's scope of directory listings including sizes. |
| `directory_tree` | 2 | yes | none | The tool 'directory_tree' is listed in the organization's register as reaching this asset, and it operates on directory listings which are part of the 'workspace-tree' asset. |
| `search_files` | 2 | yes | none | The tool 'search_files' is listed in the organization's register as reaching this asset, and its description indicates it can search for files and directories matching a pattern within allowed directories. |
| `get_file_info` | 2 | yes | none | The tool retrieves metadata about files and directories, which is exactly what the asset 'workspace-tree' represents. |
| `list_allowed_directories` | 2 | yes | none | The tool 'list_allowed_directories' is listed in the organization's register as reaching this asset, and it returns directory listings which are part of the 'workspace-tree'. |

Not reached: `read_file`, `read_text_file`, `read_media_file`, `read_multiple_files`, `write_file`, `edit_file`, `move_file`
