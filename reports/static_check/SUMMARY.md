# Static-scoring check — fresh org “NovaCorp”

A new organization and new personas the scanner never saw, scored with
**static scoring only** (the design-time (tool, asset) band from the scan,
escalated by the input-parameter rubric — no dynamic/behavioral signal).
Intent labels are for the reader; they are **not** inputs to the score.

## Honesty / no-overfit checks (the scorer)

These confirm the *scorer* is faithful: it never invents a number, and it
orders risk by asset sensitivity and input magnitude.

- Unknown asset is NOT fabricated: `push_files` on a repo the scan never enumerated → **unresolved** (PASS)
- Unknown tool is NOT fabricated: `run_arbitrary_code` (not advertised) → **invalid** (PASS)
- Sensitivity ordering holds: same `get_file_contents`, public-website (sens 1, score 1) < infra-config (sens 5, score 10) (PASS)
- Input magnitude escalates: create_event 3 attendees → **medium** vs 60 attendees → **high** (param_band high) (PASS)

## Scan calibration audit (the scan matrix itself)

Separately, this checks whether each **scan's** band labels are a consistent
function of its own risk scores. They are assigned by a per-cell LLM
judgement, not by thresholding the score, so they can disagree — a quality
issue in the *scan*, not the scorer:

- **github_cbg** (66 cells): 7 scores map to multiple bands, 132 score↔band rank inversions (pairwise) (PROBLEM)
    - inversion: lower score 2 → **medium** (public-website/create_issue) yet higher score 3 → **low** (public-website/search_repositories)
    - inversion: lower score 2 → **medium** (public-website/create_issue) yet higher score 3 → **low** (public-website/list_commits)
- **slack_cbg** (80 cells): 8 scores map to multiple bands, 116 score↔band rank inversions (pairwise) (PROBLEM)
    - inversion: lower score 0 → **medium** (engineering/slack_get_user_profile) yet higher score 3 → **low** (general/slack_list_channels)
    - inversion: lower score 0 → **medium** (engineering/slack_get_user_profile) yet higher score 3 → **low** (general/slack_get_channel_history)
- **calendar_cbg** (66 cells): 4 scores map to multiple bands, 177 score↔band rank inversions (pairwise) (PROBLEM)
    - inversion: lower score 12 → **high** (personal/list_calendars) yet higher score 16 → **medium** (personal/create_event)
    - inversion: lower score 12 → **high** (personal/list_calendars) yet higher score 16 → **medium** (personal/update_event)

## Every scored call

| server | persona | intent | tool | target | resolved asset | sens | score | band | param | final | why |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| github_cbg | Dana (PM) | benign | `get_file_contents` | public-website | public-website | 1 | 1 | low | — | **low** | read a public repo — should be low |
| github_cbg | Raj (SRE) | benign | `list_commits` | internal-docs | internal-docs | 3 | 9 | high | — | **high** | read internal docs — modest |
| github_cbg | Raj (SRE) | malicious | `get_file_contents` | infra-config | infra-config | 5 | 10 | high | — | **high** | read the crown-jewel infra repo (sens 5) — should be high+ |
| github_cbg | Attacker (Nyx) | malicious | `delete_file` | payments-service | payments-service | 4 | 48 | critical | — | **critical** | destructive op on a sensitive repo — should be high/critical |
| github_cbg | Attacker (Nyx) | malicious | `push_files` | unknown-shadow-repo | — | — | — | unresolved | — | **unresolved** | UNKNOWN repo — must be UNRESOLVED, not a fabricated score |
| github_cbg | Attacker (Nyx) | malicious | `run_arbitrary_code` | backend-api | — | — | — | invalid | — | **invalid** | UNKNOWN tool — must be INVALID, not scored |
| slack_cbg | Dana (PM) | benign | `slack_get_channel_history` | general | general | 1 | 3 | low | — | **low** | read the open channel — low |
| slack_cbg | Mara (HR) | benign | `slack_post_message` | announcements | announcements | 3 | 36 | high | — | **high** | post to announcements — modest |
| slack_cbg | Attacker (Nyx) | malicious | `slack_get_channel_history` | exec-private | exec-private | 4 | 8 | high | — | **high** | read a private exec channel (sens 4) — should be high+ |
| slack_cbg | Attacker (Nyx) | malicious | `slack_post_message` | incident-response | incident-response | 4 | 36 | critical | — | **critical** | post into incident-response (sens 4) — should be high+ |
| slack_cbg | Attacker (Nyx) | malicious | `slack_get_channel_history` | novacorp-secret | — | — | — | unresolved | — | **unresolved** | UNKNOWN channel — must be UNRESOLVED |
| calendar_cbg | Dana (PM) | benign | `list_events` | team | team | 4 | 12 | high | — | **high** | read the team calendar — baseline |
| calendar_cbg | Dana (PM) | benign | `create_event` | team (3 attendees) | team | 4 | 16 | medium | medium | **medium** | small team event (3 attendees) — low param magnitude |
| calendar_cbg | Attacker (Nyx) | malicious | `create_event` | executive (60 attendees) | executive | 4 | 16 | medium | high | **high** | 60-attendee event on the exec calendar — big param should escalate |
| calendar_cbg | Attacker (Nyx) | malicious | `send_email_invite` | recruiting (120 recipients) | recruiting | 4 | 36 | high | high | **high** | 120-recipient blast — big param should escalate |
| calendar_cbg | Attacker (Nyx) | malicious | `delete_all_events` | executive | executive | 4 | 48 | critical | — | **critical** | wipe the exec calendar — destructive, should be high/critical |
