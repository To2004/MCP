# Dynamic Layer v4: How to Write It in the Paper

Notes for rewriting §4.3 (Dynamic Risk Adaptation) around the behaviour multiplier that the
gateway runs (`src/mcp_security/behaviour/engine.py`, design v4). The paper still describes the
older persona-based $D \cdot A \cdot N$ factor; this file holds the replacement text without
touching `main.tex` (Overleaf is its source of truth), as
[DYNAMIC-LAYER-V2-NOTES.md](DYNAMIC-LAYER-V2-NOTES.md) did for v2. The design itself, with every
number, is in
[`reports/experiments/dynamic_dimensions/DIMENSION_FORMULAS.md`](../reports/experiments/dynamic_dimensions/DIMENSION_FORMULAS.md).
Names updated on 2026-10-25: the third group is **Red Flags** (was Expected Conduct, earlier
Policy), and every dimension and mechanism has a short paper name (below).

## The story in one paragraph

The static score prices what a capability *can* do. It cannot tell an agent's routine call from
the same call made at an odd hour, at a runaway rate, from a new machine, or by a program the
agent never used. The Dynamic Scanner adds this evidence as a bounded multiplier
$M(c)\in[0.7,5]$, learned from the calling agent's own history and computed without reading the
call's arguments. Evidence comes in three groups: **Typical Cadence** (when and how often),
**Typical Footprint** (what and from where), both graded against the agent's own past, and **Red
Flags**, yes/no warning signs that hold for every agent. Every score is on one scale where $0.5$
is the edge of the agent's ordinary, and the top score alone sets $M$. Familiar behaviour lowers
the static risk by at most 30%; strange behaviour raises it up to five-fold, so
$R_{\mathrm{dynamic}}\in[0.7,25]$.

## The names

Use these names, and only these, in the text, the table, the figure and the evaluation.

**The three groups**

| Group | Question | Compared with | Scored as | Dimensions |
|---|---|---|---|---|
| **Typical Cadence** | *When and how often?* | the agent's own last 90 days | graded, 0–1 | call rate, write rate, breadth, repetition, session duration, hour of day |
| **Typical Footprint** | *What, and from where?* | the agent's own last 90 days | graded, 0–1 | tool, asset, network, client |
| **Red Flags** | *Is there a warning sign?* | one line for every agent (set by the organisation, or learned once from its traffic) | yes or no: raised → a set value | burst, sweep, oversized request, unsafe sequence, missing handshake |

How to say it: *"Two groups grade a call against the agent's own typical behaviour; red flags
are yes/no warning signs that hold for every agent. A dimension belongs to the group whose
question it answers."* The last sentence is why v4 moved "new network", "new client" and "new
tool" out of the flags: "is this new for him?" asks *what and from where*, so it is Footprint,
and a graded score can say what a yes/no check cannot: whether starting something new is
ordinary *for this agent* (a roaming phone user versus a desk-bound one).

**The fifteen dimensions**

| Group | Name | Measures | Score |
|---|---|---|---|
| Typical Cadence | Call rate | calls in the last hour | excess |
| | Write rate | writes in the last hour | excess |
| | Breadth | distinct assets in the last hour | excess |
| | Repetition | the same tool on the same asset within 10 minutes | excess |
| | Session duration | time since the session started | excess |
| | Hour of day | how often the agent acts near this time of day | rarity |
| Typical Footprint | Tool | the tool invoked | rarity |
| | Asset | the asset touched (with the first-access floor) | rarity |
| | Network | the caller's /16 address range | rarity |
| | Client | the client program (`clientInfo`, version dropped) | rarity |
| Red Flags | Burst | more calls in one minute than the limit | 0.9, habit discount |
| | Sweep | more distinct assets in one hour than the limit | 0.9, habit discount |
| | Oversized request | a request over the tool's limit | 0.9 |
| | Unsafe sequence | a write after reading a different sensitive asset; a write to a sensitive asset not read in 7 days; a merge without review | 0.9, habit discount |
| | Missing handshake | a tool call in a session that never sent `initialize` | 0.7 |

Two pairs are worth one sentence: burst backs up call rate, and sweep backs up breadth. The
Cadence dimension compares the agent with his own usual, so a busy or broad agent can stay
ordinary there; the flag still stops at the organisation's line.

**Mechanisms and symbols**

| Use | Means | Avoid, and why |
|---|---|---|
| **excess score** | "more than his usual", for counts and durations, Eq. (excess-score) | "z-score": it is not one, and it has no variance |
| **rarity score** | "rarer than his usual", for values (tool, asset, network, client, hour) | "novelty": it grades rarity, of which "never seen" is the extreme; "probability": it is not one |
| **habit discount** | a flag the agent raises often counts less | "rule rarity" (the earlier internal name) |
| **org discount** | something new for the agent that 3 or more other agents also started this week scores at most 0.5 | "peer group": nothing is grouped by role |
| **first-access floor** | a never-touched asset of sensitivity 4–5 scores at least 0.8–0.9 | "first look" (informal) |
| **warm-up** | the agent's first day: only the checks that need none of his past apply | |
| **behaviour multiplier** $M(c)$ | the dynamic layer's factor, $[0.7,5]$ | "likelihood" (it is not a probability) and $L(c)$ (taken by the old text) |
| **edge of ordinary** | $s=0.5$: twice his usual, or "every other day" | "threshold": nothing is cut at 0.5, $M$ is smooth through it |
| **top score** $s_1$, **runner-up** $s_2$ | the two largest scores of the call | |
| **reason** $d^*$ | the dimension that gave $s_1$, shown with every score | "root cause": it is the strongest evidence, not a diagnosis |
| **Red Flags**, a **red flag** is **raised** | the third group, and one of its checks | **"policy"** (the paper uses it for the classification policy on the static side); "Hard Limits" or "guardrails" (they suggest the call is blocked: a raised flag only raises $M$); "rule broken" |

## Notation and the full formula

Agent $a$, call $c$ on tool $t$ and asset $r$ (as in $R_{\mathrm{static}}(t,r)$). $H_a$ is the
agent's history over the last 90 days, up to the previous day; $A$ is his number of active days
in $H_a$; $\tau=2$ is the tolerance.

**Excess score (Typical Cadence counts and durations).** With $x_d(c)$ the current value (e.g.
calls in the last 60 minutes), $\mu_d$ its mean in $H_a$ and $u_d$ one unit:
$$ s_d(c)=\frac{x_d(c)+u_d}{x_d(c)+u_d+\tau(\mu_d+u_d)}. $$

**Rarity score (Typical Footprint, and hour of day).** For the value $v$ of dimension $d$ in
call $c$ (its tool, asset, network, client, or hour), with $n_d(w)$ the agent's past calls on
$w$:
$$ N_d(v)=\begin{cases}\sum_{w:\,n_d(w)\le n_d(v)} n_d(w) & n_d(v)>0\\ \nu_d & n_d(v)=0\end{cases}\qquad e_d(v)=\frac{N_d(v)+1}{A+1},\qquad s_d(c)=\frac{\kappa_d}{1+\tau\,e_d(v)}, $$
where $\nu_d$ is the number of new values of that kind the agent started after onboarding, and
$\kappa_d=0.9$ for tool, network and client ($1$ otherwise). $e_d$ reads "how many times a day he
does something this rare"; $N_d$ is an empirical tail count (the share of his past at least this
rare). Two adjustments: the **org discount**, a value he never used that at least three other
agents started in the last 7 days is an organisation-wide change, $s_d\leftarrow\min(s_d,0.5)$;
and the **first-access floor**, a first access to an asset of sensitivity $\sigma(r)\ge 4$ is
floored, $s_{\text{asset}}\leftarrow\max\big(s_{\text{asset}},\,0.9-0.1(5-\sigma(r))\big)$.

**Red Flags.** Flag $\phi$ takes part only when raised, with value $v_\phi=0.9$ ($0.7$ for the
missing handshake). For burst, sweep and unsafe sequence, the **habit discount**:
$s_\phi=v_\phi/\big(1+\tau k_\phi/(A+1)\big)$, with $k_\phi$ the days he raised $\phi$ in $H_a$.

**One shape.** Both graded scores are $x/(x+\tau)$: the excess score with
$x=(x_d+u)/(\mu_d+u)$, the rarity score with $x=1/e_d$ ("once every $x$ days"). This is the
saturating curve of BM25 term frequency. It is why the scores are comparable and why the maximum
below is meaningful.

### Top score and runner-up: s1 and s2

Let $\mathcal{D}(c)$ be the dimensions taking part in $c$ (graded dimensions once the agent has
a day of history; red flags when raised). Order their scores $s_{(1)}\ge s_{(2)}\ge\dots$ and
write
$$ s_1(c)=s_{(1)},\qquad s_2(c)=s_{(2)}\ (0\text{ if }|\mathcal{D}(c)|<2),\qquad d^*(c)=\arg\max_{d\in\mathcal{D}(c)} s_d(c). $$

$$ M(c)=\begin{cases}5^{\,2s_1(c)-1} & s_1(c)\ge 0.5\\[2pt] 0.7^{\,1-2s_1(c)} & s_1(c)<0.5\\[2pt] 1 & \mathcal{D}(c)=\emptyset\end{cases}\qquad\qquad R_{\mathrm{dynamic}}(c)=R_{\mathrm{static}}(t,r)\,M(c). $$

- The top score $s_1$ alone sets $M$; its reason $d^*$ is reported with every score.
- The runner-up $s_2$ never changes $M$ or the risk. It orders review: an agent-day is
  represented by its call with the largest $M$, and agent-days are ranked by $(M, s_2)$
  lexicographically. That is the only place where a second piece of evidence counts.

## Making the max a contribution

Reviewers will ask "why not a weighted sum, or a learned model?". Answer with properties, each
tied to something the paper already claims:

| Property of $M=g(s_1)$ | What it buys | Paper claim it supports |
|---|---|---|
| The top score's dimension is the reason | every score comes with one named cause and a runner-up | "interpretable risk scores" (contribution 2) |
| No dilution | ordinary dimensions cannot hide one strange one, however many are added | detection of single-signal misuse (a new client, a first access to payroll) |
| No double counting | correlated signals (a loop raises call rate, repetition and burst together) count once | low false alarms on ordinary traffic |
| Bounded independent of the number of dimensions | $M\in[0.7,5]$ with 15 or 30 dimensions; the alert line never moves | extensibility: a deployment adds a dimension without recalibration |
| Monotone | a stranger call never scores safer | soundness of gating on $R_{\mathrm{dynamic}}$ |
| Well-founded | all scores share one scale ($0.5$ = edge of ordinary), so the max compares like with like | the single shape $x/(x+\tau)$ |
| Exact attribution and cheap ablation | scores do not depend on each other, so removing a dimension changes $M$ only where it was $d^*$ | the ablation study (below) and the "what causes alerts" breakdown |

How to phrase it: *"We combine dimensions with the maximum rather than a sum or an average. The
maximum is the standard disjunction of fuzzy logic: a call is unusual if its cadence or its
footprint is unusual, or if it raises a red flag. In outlier-ensemble terms it is the
maximization combination, which keeps outliers visible to a single detector that averaging
would dilute \cite{aggarwal2015outlier,zimek2014ensembles}. Because every score is on the same
scale, the maximum is meaningful, and because it selects a single score, every multiplier
carries its own explanation."*

Then state the cost honestly and show it is handled: medium signals do not add up (two scores of
0.7 still give ×1.9). Summing them was tested ($s_1+0.3\,s_2(1-s_1)$): it caught more mass
cleanups but raised false alarms on ordinary agent-days. v4 therefore lets the runner-up act only
on the review ranking, where it breaks ties at no cost in false alarms. The ablation study
settles this point (see below).

## Missing handshake: a paragraph for the paper

*"Every MCP session starts with an `initialize` handshake in which the client names itself and
negotiates the protocol version and capabilities \cite{mcp2026spec}. The red flag
\emph{missing handshake} is raised when a tool call arrives in a session whose handshake the
gateway never observed for that caller, and only for agents that normally perform it (at least
half of their sessions). It is the one dimension that inspects the protocol rather than usage:
it asks whether the call came from the program the agent normally uses, which a script, a
replay, or a second program holding the same credentials would not. Because legitimate causes
exist (a session resumed after the gateway restarted, a stateless client), it carries a lower
value ($0.7$, ×1.9): alone it lifts a call above ordinary without crossing the alert line, and
combined with other evidence it becomes the call's runner-up and raises its place in review."*

## What to report in the evaluation

Lead with false alarms on mostly-ordinary traffic, then gray (risky, not malicious) episodes:
1. ordinary agent-days at ×3 or more, and their causes (the reason $d^*$ of the alerting call);
2. ordinary life and organisation-wide changes at ×3 (vacation, VPN change, client switch, new
   hire, tool release);
3. gray episodes caught at ×3, and on a daily review list of fixed size ranked by $(M, s_2)$.

The numbers are in
[DIMENSION_FORMULAS.md, Simulation (v4)](../reports/experiments/dynamic_dimensions/DIMENSION_FORMULAS.md#simulation-v4).
The traffic is synthetic and the detectors were designed after seeing what earlier versions
missed: present the drop in false alarms as the trustworthy number, the catch rates as
optimistic.

**Ablation study (planned, not done yet).** Leave one dimension out; leave one group out
(Typical Cadence, Typical Footprint, Red Flags); the combiner (max, mean, noisy-OR,
$s_1+0.3\,s_2(1-s_1)$); the review tie-break (random, $s_2$, number of dimensions past 0.5); the
three adjustments (habit discount, org discount, first-access floor); the warm-up. The dimension
and group arms need no rerun: log each call's scores once and recompute $M$ without the left-out
scores. That exactness is itself a consequence of the max, and worth one sentence in the paper.
The full plan:
[DIMENSION_FORMULAS.md, Future work](../reports/experiments/dynamic_dimensions/DIMENSION_FORMULAS.md#future-work-ablation-study).

## Paste-ready LaTeX for §4.3

```latex
\subsection{Dynamic Risk Adaptation}
\label{sec:dynamic}

The static score captures what a capability can do, but two invocations of the
same tool on the same asset need not present the same runtime situation. The
Dynamic Scanner adapts the static score with a bounded \emph{behaviour
multiplier} $M(c)\in[0.7,5]$ that compares invocation $c$ with the calling
agent's own history over the last 90 days, without reading its arguments:
\begin{equation}
R_{\mathrm{dynamic}}(c)=R_{\mathrm{static}}(t,r)\,M(c)\in[0.7,25].
\label{eq:dynamic-risk}
\end{equation}

\paragraph{Evidence.}
The evidence falls into three groups (Table~\ref{tab:dynamic-dimensions}), each
answering one question about the invocation. \emph{Typical Cadence} asks when
and how often the agent acts: its call rate, write rate and breadth (distinct
assets) in the last hour, the repetition of one call within ten minutes, the
session's duration, and the hour of day. \emph{Typical Footprint} asks what the
agent touches and from where: the tool, the asset, the network and the client.
Both groups are graded against the agent's own typical behavior.
\emph{Red Flags} are yes/no warning signs that hold for every agent: a
\emph{burst} of calls within one minute, a \emph{sweep} across more assets in an
hour than the organization's limit, an \emph{oversized request} for the tool, an
\emph{unsafe sequence} (a write after reading a different sensitive asset, a
write to a sensitive asset not read recently, a merge without review), and a
\emph{missing handshake} (a tool call in a session that never sent the
protocol's \texttt{initialize}). Their limits are set by the organization or
learned once from its traffic. A raised flag raises the score; it does not block
the invocation.

\paragraph{One scale.}
Every dimension $d$ yields a score $s_d(c)\in[0,1]$ in which $0.5$ marks the
edge of the agent's ordinary behavior. A count or duration $x$ is compared with
the agent's mean $\mu$ by the \emph{excess score}
\begin{equation}
s_d=\frac{x+u}{x+u+\tau(\mu+u)},
\label{eq:excess-score}
\end{equation}
with $u$ one unit and tolerance $\tau=2$, so that twice the usual gives exactly
$0.5$. A categorical value $v$ is scored by how often the agent does something
this rare, the \emph{rarity score}
\begin{equation}
e_d(v)=\frac{N_d(v)+1}{A+1},\qquad s_d=\frac{\kappa_d}{1+\tau\,e_d(v)},
\label{eq:rarity-score}
\end{equation}
where $N_d(v)$ counts the agent's past invocations on $v$ and on every value he
used at most as often (for a value never used, the number of new values he
started), $A$ is his number of active days, and $\kappa_d\le1$ caps the score.
Both scores are the saturating curve $x/(x+\tau)$. Two adjustments keep the
rarity score honest: a never-used value that at least three other agents also
started in the past week is an organization-wide change and scores at most
$0.5$ (the \emph{org discount}), and a first access to an asset of sensitivity
$\sigma\ge4$ scores at least $0.9-0.1(5-\sigma)$ (the \emph{first-access
floor}). A red flag takes part only when raised, with value $0.9$ ($0.7$ for a
missing handshake), reduced when the agent raises it habitually (the
\emph{habit discount}).

\paragraph{Combination.}
Let the \emph{top score} $s_1(c)$ and the \emph{runner-up} $s_2(c)$ be the two
largest scores among the dimensions that take part in $c$, and the
\emph{reason} $d^*(c)$ the dimension attaining $s_1(c)$. The multiplier depends
on the top score only:
\begin{equation}
M(c)=
\begin{cases}
5^{\,2s_1(c)-1}, & s_1(c)\ge0.5,\\
0.7^{\,1-2s_1(c)}, & s_1(c)<0.5,
\end{cases}
\label{eq:behaviour-multiplier}
\end{equation}
and $M(c)=1$ when no dimension takes part. Ordinary behavior ($s_1=0.5$)
leaves the static risk unchanged; familiar behavior lowers it by at most 30\%;
unusual behavior raises it up to five-fold. We use the maximum, the disjunction
of fuzzy logic and the maximization combination of outlier ensembles
\cite{aggarwal2015outlier,zimek2014ensembles}, for four reasons: a single
unusual dimension cannot be diluted by ordinary ones; correlated dimensions are
not counted twice; $M$ remains bounded however many dimensions are added; and
every score carries its explanation, the reason $d^*(c)$. Because all scores
share one scale, the maximum compares like with like. The runner-up $s_2(c)$
does not affect $M$; it orders invocations with equal $M$ for review.

\begin{table}[t]
\centering
\small
\setlength{\tabcolsep}{4pt}
\caption{The dynamic layer's dimensions. Typical Cadence and Typical Footprint
grade the invocation against the agent's own last 90 days; a red flag holds
for every agent and takes part only when raised.}
\label{tab:dynamic-dimensions}
\begin{tabular}{@{}llll@{}}
\toprule
Group & Dimension & Measures & Score \\
\midrule
Cadence   & Call rate         & calls in the last hour                 & excess \\
          & Write rate        & writes in the last hour                & excess \\
          & Breadth           & distinct assets in the last hour       & excess \\
          & Repetition        & same tool and asset, 10 min            & excess \\
          & Session duration  & time since the session started         & excess \\
          & Hour of day       & activity near this time of day         & rarity \\
\midrule
Footprint & Tool              & the tool invoked                       & rarity \\
          & Asset             & the asset touched                      & rarity$^{a}$ \\
          & Network           & the caller's /16 network               & rarity \\
          & Client            & the client program                     & rarity \\
\midrule
Red Flags & Burst             & calls per minute over the limit        & $0.9^{b}$ \\
          & Sweep             & assets per hour over the limit         & $0.9^{b}$ \\
          & Oversized request & request over the tool's limit          & $0.9$ \\
          & Unsafe sequence   & write or merge in unsafe order         & $0.9^{b}$ \\
          & Missing handshake & session without \texttt{initialize}    & $0.7$ \\
\bottomrule
\end{tabular}

\smallskip
{\footnotesize $^{a}$\,With the first-access floor. $^{b}$\,With the habit discount.}
\end{table}
```

Notes on the LaTeX:
- `eq:dynamic-risk` keeps its label, so the existing `\ref`s still resolve. `eq:runtime-factor`
  (the old $L=DAN$) is gone: in `main-restructured.tex` it is cited by §5.3's "Composition"
  paragraph (line ~952), and $L(c)$ appears in §4.3's closing paragraphs; both need rewriting.
  Note that §4.3's old text says familiar behaviour "does not reduce the static risk" (factors
  bounded below by 1); v4 deliberately allows a discount of up to 30% ($M\ge0.7$).
- The two score equations are labelled `eq:excess-score` and `eq:rarity-score` (new labels; no
  existing `\ref` uses them).
- The table uses `booktabs` (`\toprule`), which `acmart` already loads, and no other package.
  Compiled with `acmart` in `sigconf` mode, it fits one column with no overfull box; the text
  paragraph spells out what "unsafe order" covers.
- The figure `mcp_dynamic_scanner_architecture_updated.png` still shows $D$, $A$, $N$; it needs
  redrawing with the three groups (Typical Cadence, Typical Footprint, Red Flags) and the max.
- §5.3 (implementation, dynamic layer) should name `engine.py` and the gateway's per-caller state.
  The engine's keys differ from the paper names (`many_assets` is sweep, `protocol_skip` is
  missing handshake, ...): the mapping is in
  [DIMENSION_FORMULAS.md, Names](../reports/experiments/dynamic_dimensions/DIMENSION_FORMULAS.md#names).

## BibTeX for the new references

Both checked against the publisher's pages (DOIs resolve).

```bibtex
@article{aggarwal2015outlier,
  author  = {Aggarwal, Charu C. and Sathe, Saket},
  title   = {Theoretical Foundations and Algorithms for Outlier Ensembles},
  journal = {ACM SIGKDD Explorations Newsletter},
  volume  = {17},
  number  = {1},
  year    = {2015},
  doi     = {10.1145/2830544.2830549}
}

@article{zimek2014ensembles,
  author  = {Zimek, Arthur and Campello, Ricardo J. G. B. and Sander, J{\"o}rg},
  title   = {Ensembles for Unsupervised Outlier Detection: Challenges and Research Questions},
  journal = {ACM SIGKDD Explorations Newsletter},
  volume  = {15},
  number  = {1},
  pages   = {11--22},
  year    = {2014},
  doi     = {10.1145/2594473.2594476}
}
```

`\cite{mcp2026spec}` is already in `refs.bib` (the MCP specification).
