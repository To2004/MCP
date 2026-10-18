# Dynamic-layer design experiments

Scripts backing [docs/guides/dynamic-layer-experiments.md](../../docs/guides/dynamic-layer-experiments.md).
Run from the repo root with plain `python3` — no dependencies beyond the stdlib.

| script | what it answers |
|---|---|
| `bench.py` | Does the external gateway bundle load our artifacts, and how does it score the labelled live calls? |
| `design_check.py` | How much headroom does the band-floor rule leave, per band? |
| `likelihood_check.py` | Does a usage-share likelihood separate the labels, at which key granularity? |
| `sim.py` | Library: scores a call corpus with the proposed design, causally. |
| `livescale.py` | On warm corpora: does likelihood rank correctly inside a band, and what does moving the floor cost? |

`bench.py` expects the gateway bundle unpacked somewhere and its path edited at the
top; everything else runs against `reports/` and `logs/` as committed.
