#!/usr/bin/env python3
"""Convert risk_scoring_frameworks_survey.md to PDF via XeLaTeX."""

import re
import subprocess
import sys
from pathlib import Path

MD_FILE = Path(r"C:\Users\user\Documents\GitHub\MCP\Literature_review\risk_scoring_frameworks_survey.md")
OUT_DIR = Path(r"C:\Users\user\Documents\GitHub\MCP\Literature_review")

# Characters that must be escaped for LaTeX
_TEX_ESCAPE = {
    '\\': r'\textbackslash{}',
    '{': r'\{',
    '}': r'\}',
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '^': r'\^{}',
    '_': r'\_',
    '~': r'\textasciitilde{}',
    '<': r'\textless{}',
    '>': r'\textgreater{}',
}


def escape_tex(s: str) -> str:
    """Escape LaTeX special characters."""
    return ''.join(_TEX_ESCAPE.get(ch, ch) for ch in s)


def process_inline(text: str) -> str:
    """Convert inline markdown to LaTeX, escaping special chars correctly."""
    # 1. Extract and protect code spans (backticks)
    code_store: dict[str, str] = {}
    cc = [0]

    def save_code(m: re.Match) -> str:
        k = f'XCOD{cc[0]}X'
        code_store[k] = r'\texttt{' + escape_tex(m.group(1)) + '}'
        cc[0] += 1
        return k

    text = re.sub(r'`([^`]+)`', save_code, text)

    # 2. Extract bold+italic (***...***) before bold and italic individually
    bi_store: dict[str, str] = {}
    bic = [0]

    def save_bi(m: re.Match) -> str:
        k = f'XBI{bic[0]}X'
        bi_store[k] = r'\textbf{\textit{' + escape_tex(m.group(1)) + '}}'
        bic[0] += 1
        return k

    text = re.sub(r'\*\*\*(.+?)\*\*\*', save_bi, text)

    # 3. Extract bold (**...**)
    bold_store: dict[str, str] = {}
    bc = [0]

    def save_bold(m: re.Match) -> str:
        k = f'XBLD{bc[0]}X'
        bold_store[k] = r'\textbf{' + escape_tex(m.group(1)) + '}'
        bc[0] += 1
        return k

    text = re.sub(r'\*\*(.+?)\*\*', save_bold, text)

    # 4. Extract italic (*...*)
    ital_store: dict[str, str] = {}
    ic = [0]

    def save_ital(m: re.Match) -> str:
        k = f'XITL{ic[0]}X'
        ital_store[k] = r'\textit{' + escape_tex(m.group(1)) + '}'
        ic[0] += 1
        return k

    text = re.sub(r'\*(.+?)\*', save_ital, text)

    # 5. Escape remaining special characters
    text = escape_tex(text)

    # 6. Restore all stored spans (keys are alphanumeric only, safe to replace)
    for store in (bi_store, bold_store, ital_store, code_store):
        for k, v in store.items():
            text = text.replace(k, v)

    return text


def parse_table(lines: list[str]) -> str:
    """Convert markdown pipe table to a LaTeX longtable."""
    rows: list[list[str]] = []
    for line in lines:
        # Skip separator rows (|---|---|...)
        if re.match(r'^\s*\|[-:| ]+\|\s*$', line):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        rows.append(cells)

    if not rows:
        return ''

    ncols = len(rows[0])

    # Column widths tuned for 7-column table on A4 with 2cm margins (≈17cm text width)
    if ncols == 7:
        col_spec = (
            r'>{\raggedright\arraybackslash}p{2.8cm}'
            r'>{\raggedright\arraybackslash}p{2.0cm}'
            r'>{\centering\arraybackslash}p{0.6cm}'
            r'>{\raggedright\arraybackslash}p{1.4cm}'
            r'>{\raggedright\arraybackslash}p{4.2cm}'
            r'>{\centering\arraybackslash}p{1.4cm}'
            r'>{\raggedright\arraybackslash}p{1.8cm}'
        )
    else:
        col_spec = r'>{\raggedright\arraybackslash}p{2.5cm}' * ncols

    out: list[str] = []
    out.append(r'{\small')
    out.append(r'\begin{longtable}{' + col_spec + '}')
    out.append(r'\toprule')

    # Header
    header_cells = [r'\textbf{' + process_inline(h) + '}' for h in rows[0]]
    out.append(' & '.join(header_cells) + r' \\')
    out.append(r'\midrule')
    out.append(r'\endfirsthead')
    out.append(r'\toprule')
    out.append(' & '.join(header_cells) + r' \\')
    out.append(r'\midrule')
    out.append(r'\endhead')
    out.append(r'\midrule')
    out.append(r'\multicolumn{' + str(ncols) + r'}{r}{\textit{Continued on next page}} \\')
    out.append(r'\endfoot')
    out.append(r'\bottomrule')
    out.append(r'\endlastfoot')

    # Data rows
    for row in rows[1:]:
        # Pad or trim to ncols
        while len(row) < ncols:
            row.append('')
        cells = [process_inline(c) for c in row[:ncols]]
        out.append(' & '.join(cells) + r' \\')

    out.append(r'\end{longtable}')
    out.append(r'}')  # end \small
    return '\n'.join(out)


PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage{fontspec}
\usepackage[margin=2cm]{geometry}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{parskip}
\usepackage[hidelinks]{hyperref}
\usepackage{microtype}
\usepackage{xcolor}
\usepackage{sectsty}
\usepackage{setspace}
\definecolor{headcolor}{RGB}{0,70,127}
\sectionfont{\color{headcolor}\large\bfseries}
\setlength{\parskip}{6pt}
\setlength{\LTpre}{4pt}
\setlength{\LTpost}{4pt}
\setlength{\tabcolsep}{4pt}
\begin{document}
"""


def convert(md_text: str) -> str:
    """Convert a markdown string to a complete LaTeX document."""
    lines = md_text.split('\n')
    body: list[str] = [PREAMBLE]

    i = 0
    table_lines: list[str] = []
    in_table = False

    while i < len(lines):
        line = lines[i]

        # --- Table detection ---
        if re.match(r'^\s*\|', line):
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(line)
            i += 1
            continue
        elif in_table:
            body.append(parse_table(table_lines))
            body.append('')
            in_table = False
            table_lines = []
            # Re-process current line without incrementing
            continue

        # --- H1 (title) ---
        if re.match(r'^# (?!#)', line):
            title = process_inline(line[2:].strip())
            body.append(r'\begin{center}')
            body.append(r'{\LARGE\bfseries ' + title + r'}')
            body.append(r'\end{center}')
            body.append(r'\vspace{1em}')

        # --- H2 (section) ---
        elif line.startswith('## '):
            heading = process_inline(line[3:].strip())
            body.append(r'\section*{' + heading + '}')

        # --- Horizontal rule ---
        elif re.match(r'^-{3,}\s*$', line):
            body.append(r'\medskip\noindent\rule{\textwidth}{0.4pt}\medskip')

        # --- Blank line ---
        elif line.strip() == '':
            body.append('')

        # --- Normal paragraph line ---
        else:
            body.append(process_inline(line))

        i += 1

    # Flush any trailing table
    if in_table and table_lines:
        body.append(parse_table(table_lines))

    body.append(r'\end{document}')
    return '\n'.join(body)


def main() -> None:
    md_text = MD_FILE.read_text(encoding='utf-8')
    tex_text = convert(md_text)

    tex_file = OUT_DIR / 'risk_scoring_frameworks_survey.tex'
    tex_file.write_text(tex_text, encoding='utf-8')
    print(f"Wrote .tex: {tex_file}")

    # XeLaTeX needs to run from the output directory for auxiliary files
    for run in range(2):
        result = subprocess.run(
            ['xelatex', '-interaction=nonstopmode', str(tex_file)],
            cwd=str(OUT_DIR),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
        if result.returncode != 0:
            # Print last portion of log for diagnosis
            print(f"xelatex run {run + 1} FAILED (exit {result.returncode})")
            print("--- stdout (last 3000 chars) ---")
            print(result.stdout[-3000:])
            sys.exit(1)
        print(f"xelatex run {run + 1} OK")

    pdf = OUT_DIR / 'risk_scoring_frameworks_survey.pdf'
    if pdf.exists():
        print(f"\nPDF ready: {pdf}")
    else:
        print("ERROR: PDF file not found after compilation.")
        sys.exit(1)


if __name__ == '__main__':
    main()
