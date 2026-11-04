# Gateway golden files: changelog

One line per regeneration, newest last. Append only. A re-baseline must name E9, AI-3 or PS7.

- 2026-10-26: recorded github.jsonl and github_scored.csv on the pre-v5 gateway and engine (v5 Batch 0, INF-3 baseline).
- 2026-10-26: re-recorded github.jsonl on the pre-v5 gateway and engine (backup tree first on sys.path), through the app's lifespan, so the log now starts with gateway_started and ends with gateway_stopped (pre-v5 config_sha256). The other 336 lines equal the earlier recording except score_us and the hash chain. github_scored.csv is unchanged: not a re-baseline (no E9, AI-3 or PS7 change).
