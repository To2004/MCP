# AAMAS 2027 — Rules

Everything binding for a main-track submission, gathered 2026-07-30 from the
official conference site. Quotes are verbatim. Where AAMAS 2027 had not yet
published a detail, the AAMAS 2026 instructions are used and marked as such —
these carry over year to year, but re-check once AAMAS 2027 publishes its own.

The companion document is [`WRITING-GUIDE.md`](WRITING-GUIDE.md), which turns
these constraints into a length budget and a structure.

## Contents

- [1. Conference](#1-conference)
- [2. Length](#2-length)
- [3. Format](#3-format)
- [4. Anonymity](#4-anonymity)
- [5. Abstract registration](#5-abstract-registration)
- [6. Supplementary material](#6-supplementary-material)
- [7. Desk rejection](#7-desk-rejection)
- [8. Review criteria](#8-review-criteria)
- [9. Findings track](#9-findings-track)
- [10. Dual submission and prior publication](#10-dual-submission-and-prior-publication)
- [11. AI use policy](#11-ai-use-policy)
- [12. Attendance and publication](#12-attendance-and-publication)
- [13. What this means for our paper](#13-what-this-means-for-our-paper)

## 1. Conference

| | |
|---|---|
| Event | 26th International Conference on Autonomous Agents and Multiagent Systems |
| Dates | **3–7 May 2027** |
| Venue | JW Marriott Hotel, Hanoi, Vietnam |
| Paper deadline | **Early October 2026 (TBC)** |
| Abstract deadline | One week before the paper deadline |
| OpenReview accounts | Every author, two weeks before the abstract deadline |
| Submission system | OpenReview |
| Licence | CC-BY |

## 2. Length

> "at most **eight (8)** pages long, with any number of additional pages
> containing bibliographic references"

And from the reviewer guidelines, stated as a desk-reject trigger:

> "papers must be no more than 8 pages, **excluding references and appendices**"

So: **8 pages of body. References free. Appendices free** — but with a hard
catch, also from the reviewer guidelines:

> "papers are expected to be **self-contained** and should not rely on
> appendices or supplementary material for core contributions"

An appendix may hold extra tables, proofs, or reproduction detail. It may not
hold anything a reviewer must read to believe the claim. Treat the 8 pages as
the entire argument.

Extended abstracts are 2 pages plus references (AAMAS 2026) — a separate
acceptance outcome, not a separate submission.

## 3. Format

- **"The use of LaTeX is mandatory."**
- Use the official AAMAS template (ACM `acmart`, `sigconf`).
- **"Please do not modify the style files or any of the layout parameters."**
- **"Avoid excessive use of typesetting tricks to make everything fit into 8
  pages."**
- Submit PDF.

Practical reading of the last two: no shrunken `\baselineskip`, no negative
`\vspace` before headings, no `\small` on body text, no `\resizebox` on a table
to the point of illegibility. These are visible to an experienced reviewer and
are a formatting violation, which is a desk-reject category. **Cut words
instead.**

Two `acmart` traps we hit building this project — see `README.md`:

1. `\setcopyright{ifaamas}` only works with the patched `acmart.cls` inside the
   official AAMAS bundle, not stock `acmart`.
2. Do not add `\usepackage{amssymb}` — it clashes with `\Bbbk` from acmart's
   Libertine math setup.

## 4. Anonymity

Double-blind. From the AAMAS 2026 instructions:

- **"replace your name and affiliation on the first page with the paper
  tracking number"**
- **"do not include any acknowledgements in your submission"**
- Cite your own prior work in the third person: *"X et al. [42] showed…"*, not
  *"We showed…"*
- Supplementary material must also be anonymous.

For this paper specifically: the earlier v1–v4 arms of the framework, the BGU
group's `AgentGuardian`, `GenKubeSec`, and `KubeGuard`, and any repository URL
all need third-person phrasing or anonymised links.

In LaTeX:

```latex
\documentclass[sigconf, anonymous, review]{acmart}
\settopmatter{printacmref=false, printfolios=true}
```

`printfolios=true` gives reviewers page numbers.

## 5. Abstract registration

- Due **one week before** the paper deadline.
- **"around 100–300 words in plain text."**
- Keywords and additional metadata required at registration.
- **Placeholder abstracts are prohibited**, and abstracts cannot be
  significantly altered after the submission deadline.

Consequence: the abstract must be genuinely written a week early. It cannot be
the last thing drafted.

## 6. Supplementary material

- Optional, **single ZIP, ≤25 MB**.
- **"Do not use supplementary material to submit an extended or corrected
  version."**
- **"Any information that is essential for understanding or evaluating your
  paper must be included in the paper itself."**
- Reviewers consult it at their discretion — they are not required to.
- Must preserve anonymity.
- Should be released publicly after acceptance (Zenodo, GitHub, arXiv).

## 7. Desk rejection

A paper may be desk rejected if it:

- exceeds the page limit;
- is out of scope for the conference;
- **"contains severely insufficient technical content"**;
- violates formatting requirements;
- is not properly anonymised.

"Out of scope" is a live risk for us: AAMAS is an agents conference, not a
security conference. The framing must be about **agents acting on resources**
and the governance of that interaction — not about vulnerability management.
Note also: *"Papers may be moved to a different area based on fit but may be
desk rejected if deemed out of scope."*

## 8. Review criteria

Submissions are evaluated on:

> "originality, significance, soundness, reproducibility, clarity, relevance to
> the conference, quality of presentation, as well as understanding and
> appropriate referencing of the state of the art"

Reviewers must hold a PhD, or be a third-year-plus PhD student with at least
three peer-reviewed publications. AAMAS 2027 has not published a rating scale
or rubric; the Q&A page is the reviewers' further guidance.

Two of these criteria are unusually cheap to win and expensive to lose:

- **Reproducibility** — say exactly which model, which seed, which prompt, and
  where the artifacts are. We have all of it.
- **Referencing of the state of the art** — a 64-entry, verified bibliography
  covering MCP, agent safety, and classical risk scoring answers this directly.

## 9. Findings track

New for AAMAS 2027, modelled on ACL Findings.

- **No separate submission.** Every main-track paper is automatically
  considered, *"unless the authors opt out of this option in the submission
  form."*
- Findings papers are **"peer-reviewed, archival, and fully citable"**, CC-BY,
  same length and formatting as Proceedings papers.
- The split is by **strength of contribution**, not paper type. A *"surprising
  exploratory finding or a strong negative result"* can reach the Proceedings;
  a conventional contribution with limited scope or validation may land in
  Findings.

Decision for us: **do not opt out.** The work is real and archival either way,
and the honest reporting of where the derivation drifts is exactly the kind of
result the Findings description accommodates.

## 10. Dual submission and prior publication

- The paper may not be under review elsewhere at any point between submission
  and notification.
- No *"substantial overlap in contribution or text with work previously
  accepted for publication as a full paper in another archival forum."*
- **Workshop papers and arXiv preprints are allowed**, provided the preprint is
  not actively promoted during review.
- Previously rejected papers may be resubmitted.

Relevant to us: the BGU thesis proposal (`../thesis/`) is not an archival
publication, so it does not block submission. Text must not be reused verbatim
in a way that creates overlap with anything archival.

## 11. AI use policy

- **AI cannot be listed as an author or co-author.**
- Permitted for text polishing, code creation, and experimental design —
  **with detailed documentation of prompts and tools used**.
- AI-generated images only if AI is the paper's research topic.
- Authors are accountable for accuracy, plagiarism, and bias.

Note the documentation requirement is not a formality. Since our *method* is an
LLM pipeline, the prompt artifacts we already keep
(`scoring-prompts-AS-RUN.md`) serve both the method description and this policy.

## 12. Attendance and publication

- At least one author must register by the early deadline **with the intention
  of presenting**.
- Remote presentation only in exceptional circumstances.
- **Only in-person presentations are eligible for awards.**
- Accepted papers publish under CC-BY.

## 13. What this means for our paper

| Rule | Consequence here |
|---|---|
| 8 pages, self-contained | The whole argument — threat model, framework, evaluation over 3 servers — fits in 8 pages. Nothing load-bearing in an appendix. |
| Out-of-scope desk reject | Frame as **agent governance**, not vulnerability management. The protected resource and the acting agent are the subject. |
| Double-blind | v1–v4 arms and the group's own prior work cited in third person; repo links anonymised. |
| Abstract a week early, 100–300 words, no placeholders | The abstract is written *before* the paper is finished. Draft it once §5 numbers are pinned. |
| Reproducibility criterion | Name the local model, the seed, the prompt artifacts, and the held-out ground truth explicitly. |
| No typesetting tricks | Length is solved by cutting, per `WRITING-GUIDE.md`. |
| Findings auto-consideration | Do not opt out. |
| AI policy | Document the prompt pipeline as method *and* as disclosure. |

## Sources

- [Submission instructions](https://warwick.ac.uk/fac/sci/dcs/aamas2027/calls/instructions/)
- [Calls index](https://warwick.ac.uk/fac/sci/dcs/aamas2027/calls/)
- [Reviewer guidelines](https://warwick.ac.uk/fac/sci/dcs/aamas2027/calls/reviewer-guidelines/)
- [Findings](https://warwick.ac.uk/fac/sci/dcs/aamas2027/calls/findings/)
- [Conference site](https://warwick.ac.uk/fac/sci/dcs/aamas2027/)
- AAMAS 2026 (for details AAMAS 2027 has not yet published):
  [submission instructions](https://cyprusconferences.org/aamas2026/submission-instructions/),
  [main-track CFP](https://cyprusconferences.org/aamas2026/call-for-papers-main-track/)
