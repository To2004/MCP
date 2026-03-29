# Scripts — Automation Tools

This folder contains Python scripts used to organize the literature review and generate analysis documents.

## Files

| File | Description |
|------|-------------|
| `organize_papers.py` | Organizes PDF papers into category/score subfolders based on the Excel catalog data. Also generates the PDF/README.md index |
| `generate_reviews.py` | Reads the Excel catalog and paper PDFs to generate the datasets and benchmarks review documents in multiple formats (.md, .docx, .xlsx) |

## How to Use

Run scripts from the `Litereture_review/` root using `uv run`:

```bash
uv run python scripts/organize_papers.py
uv run python scripts/generate_reviews.py
```

## Related Folders

- [Excels/](../Excels/) — Input data for both scripts (paper catalog and comparison matrix)
- [PDF/](../PDF/) — Output target for `organize_papers.py`
- [reviews/](../reviews/) — Output target for `generate_reviews.py`
