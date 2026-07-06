# Most influential MCP inputs

Which **input parameter values** move a call's risk the most. Ranked by
*swing* — how many bands the value alone can shift the call's risk (from
its smallest to its largest reachable band) — then by the top band it can
reach. `top trigger` is the value that trips that top band: the number,
list length, or unbounded query that makes the call as dangerous as the
input can make it (e.g. a money `amount ≥ N` once such a tool is scanned).
A ⭐ marks the input the scanner itself named as the tool's *most
influential* (`most_influential` in the rubric).

Scanned rubrics: 9 servers, 71 magnitude parameters, 0 flagged most-influential by the scanner.

## Top influential inputs

| rank | server | tool | input | swing | reaches | top trigger | why |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | calendar_cbg | create_event | `attendees` | low→critical (+3) | **critical** | items ≥ 20 | The number of attendees can indicate the scope and sensitivity of an e… |
| 2 | calendar_cbg | send_email_invite | `recipients` | low→critical (+3) | **critical** | items ≥ 50 | The number of recipients can indicate the potential reach and risk ass… |
| 3 | fs_corp_filesystem | read_multiple_files | `paths` | low→critical (+3) | **critical** | items ≥ 20 | The number of files being read can indicate the breadth of data access… |
| 4 | fs_corp_filesystem | edit_file | `edits` | low→critical (+3) | **critical** | items ≥ 20 | The number of edits can indicate the magnitude of changes to a file. |
| 5 | fs_corp_filesystem | search_files | `pattern` | low→critical (+3) | **critical** | unbounded (no LIMIT / no cap) | The pattern parameter can affect the breadth of the search. Without a … |
| 6 | fs_fintech_fs | read_multiple_files | `paths` | low→critical (+3) | **critical** | items ≥ 20 | The number of files being read can indicate the breadth of data access… |
| 7 | fs_fintech_fs | edit_file | `edits` | low→critical (+3) | **critical** | items ≥ 20 | The number of edits can indicate the magnitude of changes to a file. |
| 8 | fs_fintech_fs | search_files | `pattern` | low→critical (+3) | **critical** | unbounded (no LIMIT / no cap) | The pattern parameter can affect the breadth of the search. A more gen… |
| 9 | fs_law_firm_fs | read_multiple_files | `paths` | low→critical (+3) | **critical** | items ≥ 20 | The number of files being read can indicate the breadth of data access… |
| 10 | fs_law_firm_fs | edit_file | `edits` | low→critical (+3) | **critical** | items ≥ 20 | The number of edits can indicate the magnitude of changes to a file. |
| 11 | fs_law_firm_fs | search_files | `pattern` | low→critical (+3) | **critical** | unbounded (no LIMIT / no cap) | The pattern parameter can affect the breadth of the search. A more gen… |
| 12 | fs_media_studio_fs | read_multiple_files | `paths` | low→critical (+3) | **critical** | items ≥ 20 | The number of files being read can indicate the breadth of data access… |
| 13 | fs_media_studio_fs | edit_file | `edits` | low→critical (+3) | **critical** | items ≥ 20 | The number of edits can indicate the magnitude of changes to a file. |
| 14 | fs_media_studio_fs | search_files | `pattern` | low→critical (+3) | **critical** | unbounded (no LIMIT / no cap) | The pattern parameter can affect the breadth of the search. A more gen… |
| 15 | fs_medical_clinic_fs | read_multiple_files | `paths` | low→critical (+3) | **critical** | items ≥ 20 | The number of files being read can indicate the breadth of data access… |
| 16 | fs_medical_clinic_fs | edit_file | `edits` | low→critical (+3) | **critical** | items ≥ 20 | The number of edits can indicate the magnitude of changes to a file. |
| 17 | fs_medical_clinic_fs | search_files | `pattern` | low→critical (+3) | **critical** | unbounded (no LIMIT / no cap) | The pattern parameter can affect the breadth of the search. Without a … |
| 18 | sqlite_cbg_sqlite | read_query | `sql` | low→critical (+3) | **critical** | unbounded (no LIMIT / no cap) | The 'sql' parameter carries risk magnitude based on the LIMIT clause i… |
| 19 | sqlite_cbg_sqlite | write_query | `sql` | low→critical (+3) | **critical** | unbounded (no LIMIT / no cap) | The SQL query parameter can affect a large number of rows depending on… |
| 20 | sqlite_cbg_sqlite | insert_row | `values` | low→critical (+3) | **critical** | unbounded (no LIMIT / no cap) | The 'values' parameter carries the data to be inserted. Since it's an … |
| 21 | sqlite_devops_sqlite | read_query | `sql` | low→critical (+3) | **critical** | unbounded (no LIMIT / no cap) | The 'sql' parameter carries risk magnitude based on the LIMIT clause i… |
| 22 | sqlite_devops_sqlite | write_query | `sql` | low→critical (+3) | **critical** | unbounded (no LIMIT / no cap) | The SQL query parameter can affect a large number of rows depending on… |
| 23 | sqlite_devops_sqlite | insert_row | `values` | low→critical (+3) | **critical** | unbounded (no LIMIT / no cap) | The 'values' parameter carries the data to be inserted. Since it's an … |
| 24 | calendar_cbg | update_event | `attendees` | low→high (+2) | **high** | items ≥ 11 | The number of attendees can indicate the scope and sensitivity of an e… |
| 25 | calendar_cbg | update_event | `duration_min` | low→high (+2) | **high** | value ≥ 120 | The duration of an event can indicate its importance or the amount of … |

## By server

### calendar_cbg (4 magnitude inputs)

| tool | input | reaches | top trigger |
| --- | --- | --- | --- |
| create_event | `attendees` | critical | items ≥ 20 |
| send_email_invite | `recipients` | critical | items ≥ 50 |
| update_event | `attendees` | high | items ≥ 11 |
| update_event | `duration_min` | high | value ≥ 120 |

### fs_corp_filesystem (12 magnitude inputs)

| tool | input | reaches | top trigger |
| --- | --- | --- | --- |
| read_multiple_files | `paths` | critical | items ≥ 20 |
| edit_file | `edits` | critical | items ≥ 20 |
| search_files | `pattern` | critical | unbounded (no LIMIT / no cap) |
| read_file | `tail` | high | value ≥ 100 |
| read_file | `head` | high | value ≥ 100 |
| read_text_file | `head` | high | value ≥ 100 |
| read_text_file | `tail` | high | value ≥ 100 |
| write_file | `content` | high | value ≥ 5000 |
| directory_tree | `excludePatterns` | high | value ≥ 3 |
| search_files | `excludePatterns` | medium | items ≥ 5 |
| list_directory_with_sizes | `path` | low | top cutoff |
| directory_tree | `path` | low | top cutoff |

### fs_fintech_fs (12 magnitude inputs)

| tool | input | reaches | top trigger |
| --- | --- | --- | --- |
| read_multiple_files | `paths` | critical | items ≥ 20 |
| edit_file | `edits` | critical | items ≥ 20 |
| search_files | `pattern` | critical | unbounded (no LIMIT / no cap) |
| read_file | `tail` | high | value ≥ 100 |
| read_file | `head` | high | value ≥ 100 |
| read_text_file | `head` | high | value ≥ 100 |
| read_text_file | `tail` | high | value ≥ 100 |
| write_file | `content` | high | value ≥ 5000 |
| directory_tree | `excludePatterns` | high | value ≥ 3 |
| search_files | `excludePatterns` | medium | items ≥ 5 |
| list_directory_with_sizes | `path` | low | top cutoff |
| directory_tree | `path` | low | top cutoff |

### fs_law_firm_fs (12 magnitude inputs)

| tool | input | reaches | top trigger |
| --- | --- | --- | --- |
| read_multiple_files | `paths` | critical | items ≥ 20 |
| edit_file | `edits` | critical | items ≥ 20 |
| search_files | `pattern` | critical | unbounded (no LIMIT / no cap) |
| read_file | `tail` | high | value ≥ 100 |
| read_file | `head` | high | value ≥ 100 |
| read_text_file | `head` | high | value ≥ 100 |
| read_text_file | `tail` | high | value ≥ 100 |
| write_file | `content` | high | value ≥ 5000 |
| directory_tree | `excludePatterns` | high | value ≥ 3 |
| search_files | `excludePatterns` | medium | items ≥ 5 |
| list_directory_with_sizes | `path` | low | top cutoff |
| directory_tree | `path` | low | top cutoff |

### fs_media_studio_fs (12 magnitude inputs)

| tool | input | reaches | top trigger |
| --- | --- | --- | --- |
| read_multiple_files | `paths` | critical | items ≥ 20 |
| edit_file | `edits` | critical | items ≥ 20 |
| search_files | `pattern` | critical | unbounded (no LIMIT / no cap) |
| read_file | `tail` | high | value ≥ 100 |
| read_file | `head` | high | value ≥ 100 |
| read_text_file | `head` | high | value ≥ 100 |
| read_text_file | `tail` | high | value ≥ 100 |
| write_file | `content` | high | value ≥ 5000 |
| directory_tree | `excludePatterns` | high | value ≥ 3 |
| search_files | `excludePatterns` | medium | items ≥ 5 |
| list_directory_with_sizes | `path` | low | top cutoff |
| directory_tree | `path` | low | top cutoff |

### fs_medical_clinic_fs (12 magnitude inputs)

| tool | input | reaches | top trigger |
| --- | --- | --- | --- |
| read_multiple_files | `paths` | critical | items ≥ 20 |
| edit_file | `edits` | critical | items ≥ 20 |
| search_files | `pattern` | critical | unbounded (no LIMIT / no cap) |
| read_file | `tail` | high | value ≥ 100 |
| read_file | `head` | high | value ≥ 100 |
| read_text_file | `head` | high | value ≥ 100 |
| read_text_file | `tail` | high | value ≥ 100 |
| write_file | `content` | high | value ≥ 5000 |
| directory_tree | `excludePatterns` | high | value ≥ 3 |
| search_files | `excludePatterns` | medium | items ≥ 5 |
| list_directory_with_sizes | `path` | low | top cutoff |
| directory_tree | `path` | low | top cutoff |

### slack_cbg (1 magnitude inputs)

| tool | input | reaches | top trigger |
| --- | --- | --- | --- |
| slack_get_channel_history | `limit` | high | value ≥ 100 |

### sqlite_cbg_sqlite (3 magnitude inputs)

| tool | input | reaches | top trigger |
| --- | --- | --- | --- |
| read_query | `sql` | critical | unbounded (no LIMIT / no cap) |
| write_query | `sql` | critical | unbounded (no LIMIT / no cap) |
| insert_row | `values` | critical | unbounded (no LIMIT / no cap) |

### sqlite_devops_sqlite (3 magnitude inputs)

| tool | input | reaches | top trigger |
| --- | --- | --- | --- |
| read_query | `sql` | critical | unbounded (no LIMIT / no cap) |
| write_query | `sql` | critical | unbounded (no LIMIT / no cap) |
| insert_row | `values` | critical | unbounded (no LIMIT / no cap) |
