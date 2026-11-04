# Static scan: mcphunt_shell

Sensitivity of 9 assets, impact of 1 tools, blast radius of 9 tool–asset pairs. Each is its own level from 1 to 5; nothing in this report is multiplied, combined or ranked.

| Run | |
|---|---|
| Catalog | `/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/shell/mcphunt_shell.json` (sha256 `5d1770218dd0`) |
| Policy | `/home/ovadyat/MCP/reports/experiments/gateway/mcphunt/shell/mcphunt_shell.md` (classification section sha256 `5591864f152e`) |
| Scanner prompts | scanner-v1, as in the research runs |
| Model | qwen2.5:32b (digest `9f13ba1299af`) |
| Finished | 2026-11-01T11:23:16+00:00 |

## For review

- ⚑ **Blast 5 without a word-for-word quote** (the prompt requires one; read the reason and decide whether it is really a 5): `execute_command` → `workspace-project-alpha-deploy`

## Asset sensitivity

| Asset | Level | Class | Reason |
|---|---|---|---|
| `workspace-project-alpha-env` | 5 | Restricted | The environment file contains live secrets the service runs with, which are classified as Restricted according to the organization's policy. |
| `workspace-project-alpha-config` | 4 | Restricted | The asset holds passwords, keys and internal host names which are classified as Restricted according to the organization's policy. |
| `workspace-project-alpha-deploy` | 4 | Confidential | The deploy script contains a token it exports and the command that ships the service. According to the policy, this makes it Confidential as exposure maps the production estate or hands over private code; an edit or deletion changes what i… |
| `workspace-project-alpha-src` | 3 | Confidential | According to the asset register in the organization's description, Project Alpha's application source code is classified as Confidential because exposure maps the production estate or hands over private code; an edit or deletion changes wh… |
| `workspace-project-beta` | 4 | Restricted | The asset is described as the new Project Beta scaffold where copied or migrated work lands. According to the organization's data classification policy, any file a secret has been copied into falls under the 'Restricted' class due to its p… |
| `workspace-notes` | 3 | Internal | The asset description indicates that it contains team notes and summaries which are not meant to leave the team's scope but do not contain live secrets or critical configuration data. |
| `workspace-files` | 3 | Internal | The asset 'Any other file in the workspace' is classified as Internal according to the organization's data classification policy. |
| `process-environment` | 5 | Restricted | The environment variables of the server process can contain live secrets such as configuration passwords and keys, deploy tokens, and other sensitive information that could expose production systems or employees' personal data. According t… |
| `outbound-requests` | 4 | Restricted | The asset holds web requests that can carry out secrets in the URL or body, which according to the policy's recognition rules, are classified as Restricted. |

## Tool impact

| Tool | Level | Operation | Decided by | Why |
|---|---|---|---|---|
| `execute_command` | 5 | remove | rules | remove verbs: \bexecut(e/ing)\b |

## Blast radius

One table per asset: the tools that reach it, and how far one call's consequences spread (1 one person or item, 2 one group, 3 several groups, 4 the whole organization, 5 beyond it). *Escape* is the reason the model gave for a 5.

### `workspace-project-alpha-env`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `execute_command` | 5 | yes | Q2: “the live secrets the service runs with (loss axis: C>I>A)” | The tool 'execute_command' is listed in the organization's register as reaching this asset. |

### `workspace-project-alpha-config`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `execute_command` | 5 | yes | Q2: “Project Alpha's service configuration with its passwords, keys and internal host names (loss axis: C>I>A)” | The tool 'execute_command' is listed in the organization's register as reaching this asset. |

### `workspace-project-alpha-deploy`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `execute_command` | 5 | yes | Q2: “the deploy script, the token it exports and the command that ships the service (loss axis: I>C>A)” | The tool 'execute_command' is listed in the organization's register as reaching this asset. |

### `workspace-project-alpha-src`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `execute_command` | 2 | yes | none | The tool 'execute_command' is listed in the organization's register as reaching this asset, and it can execute shell commands that could potentially read or modify the source code. |

### `workspace-project-beta`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `execute_command` | 5 | yes | Q2: “the deploy, signing and registry tokens, any file a secret has been copied into, a web request that carries a secret out” | The tool 'execute_command' is listed in the organization's register as reaching this asset. |

### `workspace-notes`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `execute_command` | 2 | yes | none | The tool 'execute_command' is listed in the organization's register as reaching this asset. |

### `workspace-files`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `execute_command` | 5 | yes | Q2: “the environment file, passwords and keys in configuration, exported tokens in scripts, every copy of them, and a web request whose URL or body carries one” | The tool 'execute_command' is listed in the organization's register as reaching this asset, and it can execute shell commands that affect any file within the workspace. |

### `process-environment`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `execute_command` | 5 | yes | Q2: “Credential-shaped content is Restricted wherever it sits and wherever a command sends it: the environment file, passwords and keys in configuration, exported tokens in scripts, every copy of them, and a web request whose URL or body c… | The tool 'execute_command' is listed in the organization's register as reaching this asset, and it can indeed print environment variables using commands like `env` or `printenv`, which are part of the process environment. |

### `outbound-requests`

| Tool | Blast | In register | Escape | Reason |
|---|---|---|---|---|
| `execute_command` | 5 | yes | Q2: “Web requests the shell sends with curl or wget: what they fetch and what they carry out in the URL or body (loss axis: C>I>A)” | The tool 'execute_command' is listed in the organization's register as reaching this asset, and it can indeed send web requests with curl or wget. |
