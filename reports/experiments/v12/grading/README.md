# Grading stage 1

Reference verdicts and a grader for the v12 stage 1 runs.

## Files

| File | What it is |
|---|---|
| `verdicts.json` | one verdict per input of the five catalogs: `keep`, `drop`, `record-id`, `borderline` or `debatable` |
| `grade_stage1.py` | compares a run's `<server>.importance.json` with the verdicts and lists every disagreement |
| `compare_end_to_end.py` | re-scores the 3,000 real labelled calls with each run's stage 2 rules and tabulates separation (AUC) against the tool-only baseline |

## Where the verdicts come from

- **github, slack, calendar (384 inputs)**: one annotator's judgments, first made on run4 (`run4/audit_stage1_kept.md` and the 40 inputs run4 dropped), then re-judged under the extremes test (keep an input only if its riskiest realistic value makes the call clearly riskier than its safest). The prompts were developed against these three servers, so scores here can be optimistic.
- **filesystem and sqlite (35 inputs)**: held out. No prompt was tuned on them, and their verdicts were written before any run on them was read.

These are not ground truth: `borderline` marks inputs where either answer is defensible, and a second, independent annotator would make the numbers stronger.

## Usage

```
python3 reports/experiments/v12/grading/grade_stage1.py run11
python3 reports/experiments/v12/grading/compare_end_to_end.py run4 run7 run9 run11
```
