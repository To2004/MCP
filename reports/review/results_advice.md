# Results advisor

## Strengths
- High agreement in tool-impact assessments across all servers (97%)
- Complete coverage of tool calls with a high resolution rate to cells (87%)

## Weaknesses
- Low band agreement for 'cbg_sqlite' server (34%)
- Lack of ground truth data for '_params' scans complicates validation
- Inconsistent distribution of critical and high-risk bands across different servers

## Next steps (prioritised)
- **[high] Investigate discrepancies in cbg_sqlite band assessments** — To improve the overall accuracy of risk assessment
- **[medium] Develop a method to generate ground truth for '_params' scans** — For comprehensive validation and improvement of scanner performance
- **[medium] Analyze the distribution patterns of critical and high-risk bands across servers** — To identify common factors affecting risk assessment consistency

## Risks to validity
- Inaccurate band assessments in 'cbg_sqlite' may skew overall risk analysis
- Lack of ground truth for '_params' scans limits the scanner's validation scope
