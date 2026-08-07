# `scan_v5.sbatch` — the job wrapper

**81 lines of bash.** Everything between "I have a policy document" and "the
driver can call a model".

## What it does, in order

1. **Reserves a GPU** — `--gres=gpu:rtx_4090:1`, 4 CPUs, 32 GB, 8 h wall clock.
2. **Picks the output directory from `MODE`** — `five_level_v2_v5r` writes to
   `five_level_v2_policy_v5r/`, anything else to the v5 folder. This is why the
   two arms can never overwrite each other by accident.
3. **Starts its own Ollama server** on a random port (`11600 + RANDOM % 300`) so
   several of these jobs can share a node without colliding, then polls
   `/api/tags` for up to 120 s and aborts if the model never comes up.
4. **Calls the driver** with `OLLAMA_HOST` pointed at that server.
5. **Prints a per-server summary** — score_max, sensitivity source, the
   static/LLM impact split, floored and capped cell counts, band distribution.
6. **Stops the server** and exits with the driver's return code.

## The environment that matters

```bash
OLLAMA_CONTEXT_LENGTH=16384   # the policy rides in every prompt
OLLAMA_FLASH_ATTENTION=1
OLLAMA_KV_CACHE_TYPE=q8_0
OLLAMA_KEEP_ALIVE=10m
```

16 K context is not generous — it has to hold the rubric, the org policy (up to
~900 words on github), the tool and asset JSON, and the sibling tool/asset lists.
That budget is the reason the domain-inference stage was cut from ten fields to
three: its output is re-serialized into the preamble of every later call.

## How this run was launched

```bash
sbatch --job-name=v5r2-github --export=ALL,MODE=five_level_v2_v5r \
       scripts/scan_v5.sbatch github_helios overwrite
```

Three jobs, one per server, in parallel — the scan is one HTTP request per scoring
decision, so wall clock is dominated by the blast stage (tools × assets) and
splitting by server is the only parallelism available.

Logs land in `reports/scan-v5-<jobname>-<jobid>.out` and the model's own log in
`reports/ollama-v5-<jobid>.log`.
