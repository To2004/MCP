# All static scans — scan-rules-v6 (judge-converged), 4 formats each

13 scans (3 real + 10 demo). Pipeline: blast 1-5; reach-is-a-count-not-a-consequence
(a tool's blast is fixed by its reach x asset structure, never raised by asset
importance); breadth limits (metadata ops don't expose contents; single items
aren't swept); relocation <= overwrite; concrete sensitivity anchors; judge off
(eval-only, fair). Validated by 6 judge iterations on corp+github (LLM-only,
framework-grounded, no leakage): per-primitive impact 92% / sensitivity 90% /
blast 76%; heatmap coherence github 85% / corp 87%; blast drift 6->1 / 2->1.
Bands are visualization only; the number (sensitivity*blast*impact) drives ranking.
