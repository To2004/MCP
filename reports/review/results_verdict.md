# Results-quality verdict — concern (quality: adequate)

*Reasoning:* The deterministic checks passed, indicating the pipeline is correctly implemented. However, the scanner's agreement with the consensus of independent oracles is only slightly better than chance for both filesystem and SQLite scans, which raises concerns about the reliability of the risk scores. The band distributions are not degenerate but show a wide range of risks, suggesting some variability in scoring.

*Evidence:* Overall scanner vs consensus agreement: exact 35%, within-one-band 69%; Filesystem exact band agreement: 42%, within-one-band 64%; SQLite exact band agreement: 29%, within-one-band 74%

## Top improvements
- Improve scanner accuracy by refining the scoring formula to align more closely with expert consensus
- Increase inter-rater agreement among oracles for a clearer benchmark
