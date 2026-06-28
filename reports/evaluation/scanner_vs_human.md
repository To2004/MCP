# Scanner vs independent oracle panel

Graded against a PANEL of independent oracles in `presentations/heatmap_byhand/` (the human heatmap plus framework baselines: DREAD, CVSS v3, NIST SP 800-30/60, OWASP, MAESTRO, ChatGPT) — none of which is the scanner's own LLM. We report inter-rater agreement (how much the oracles disagree among themselves) and scanner-vs-consensus (the upper-median band across raters, robust to a maximalist outlier). Compared at worst-band per (filetype|table, tool); within-one-band counts adjacent bands.

**Overall (scanner vs consensus):** exact 25/71 (35%) · within-one-band 49/71 (69%)

### Filesystem oracle panel (10 raters)

- raters: human, chatgpt:plain, chatgpt:security, cvss_v3, dread, maestro_atfaa, nist_sp_800_30, nist_sp_800_60, owasp_aivss, owasp_risk_rating
- **inter-rater agreement** (mean pairwise over 4320 comparisons): exact 2174/4320 (50%) · within-one 3369/4320 (78%)
- this is the *legitimate-disagreement ceiling*: the raters themselves agree exactly only this often.

### Filesystem (scanner vs consensus, by filetype × tool)

- compared cells: **36** (scanner 54, consensus oracle 96; scanner-only 18, oracle-only 60)
- exact band agreement: **15/36 (42%)**
- within-one-band agreement: **23/36 (64%)**

| cell | scanner | consensus | 
| --- | --- | --- |
| `csv` × `create_dir` | low | high |
| `csv` × `list_dir` | medium | critical |
| `md` × `create_dir` | low | high |
| `md` × `edit_file` | high | critical |
| `md` × `list_dir` | low | high |
| `md` × `read_file` | low | critical |
| `md` × `write_file` | medium | critical |
| `pdf` × `create_dir` | low | high |
| `pdf` × `edit_file` | high | critical |
| `pdf` × `list_dir` | medium | critical |
| `pdf` × `move_file` | medium | critical |
| `pdf` × `read_file` | high | critical |
| `png` × `create_dir` | low | high |
| `png` × `list_dir` | high | critical |
| `png` × `read_file` | high | critical |
| `sql` × `create_dir` | low | high |
| `sql` × `list_dir` | medium | critical |
| `sql` × `read_file` | high | critical |
| `txt` × `create_dir` | low | high |
| `txt` × `list_dir` | high | critical |
| `txt` × `read_file` | high | critical |

### SQLite oracle panel (10 raters)

- raters: human, chatgpt:plain, chatgpt:security, cvss_v3, dread, maestro_atfaa, nist_sp_800_30, nist_sp_800_60, owasp_aivss, owasp_risk_rating
- **inter-rater agreement** (mean pairwise over 1739 comparisons): exact 734/1739 (42%) · within-one 1312/1739 (75%)
- this is the *legitimate-disagreement ceiling*: the raters themselves agree exactly only this often.

### SQLite (scanner vs consensus, by table × tool)

- compared cells: **35** (scanner 35, consensus oracle 42; scanner-only 0, oracle-only 7)
- exact band agreement: **10/35 (29%)**
- within-one-band agreement: **26/35 (74%)**

| cell | scanner | consensus | 
| --- | --- | --- |
| `api_keys` × `append_insight` | high | critical |
| `api_keys` × `describe_table` | medium | critical |
| `api_keys` × `list_tables` | low | critical |
| `api_keys` × `read_query` | high | critical |
| `datasets` × `append_insight` | medium | high |
| `datasets` × `describe_table` | medium | high |
| `datasets` × `write_query` | critical | high |
| `employees` × `append_insight` | medium | critical |
| `employees` × `describe_table` | medium | critical |
| `employees` × `list_tables` | medium | critical |
| `employees` × `read_query` | high | critical |
| `experiments` × `append_insight` | low | high |
| `experiments` × `describe_table` | medium | high |
| `experiments` × `list_tables` | medium | high |
| `experiments` × `read_query` | medium | high |
| `grants` × `append_insight` | medium | critical |
| `grants` × `describe_table` | low | critical |
| `grants` × `list_tables` | high | critical |
| `grants` × `read_query` | high | critical |
| `projects` × `describe_table` | low | high |
| `projects` × `read_query` | medium | high |
| `projects` × `write_query` | critical | high |
| `publications` × `describe_table` | low | medium |
| `publications` × `list_tables` | low | medium |
| `publications` × `read_query` | medium | high |
