# `ollama_client.py` — the model transport

**112 lines.** One function does the work: `query_ollama(prompt)` posts to a local
Ollama server and returns parsed JSON, or `None`.

## Why it matters to the results

**Decoding is greedy and seeded** — `temperature=0`, fixed seed — so a given
registry produces the same table on a re-run. That is what makes the campaign's
arm-to-arm comparisons meaningful: a difference between two arms is attributable
to their inputs and prompts, not to sampling.

**It returns `None` rather than raising** on a transport failure or unparseable
output. The caller decides what that means, and in a strict scan
`pipeline.StaticScorer._ask()` converts it into `LLMUnavailableError`. So a scan
either gets the model's answer or fails loudly; it never quietly substitutes a
heuristic.

**JSON extraction is tolerant.** The prompts all end with "Output ONLY valid JSON,
no prose, no fences", but a local model sometimes wraps its answer in a fence or
adds a sentence. The client strips fences and locates the outermost JSON object
before parsing, which is why the stage code can assume a dict.

## The cost model this implies

Every scoring decision is its own request — no batching. For a v5r scan of
`github_helios`: 1 domain call + 9 impact hand-offs + 19 sensitivity calls +
26 × 19 = 494 blast calls ≈ 523 requests. Blast dominates, which is why the
preamble size (the policy text re-sent on every call) is the lever that matters,
and why cutting the domain stage from ten fields to three was worth doing.

The host comes from `OLLAMA_HOST`, set by `scripts/scan_v5.sbatch` to a
random-port server it starts on the reserved GPU.
