# Behaviour golden files: changelog

One line per regeneration, newest last. Append only.

- 2026-10-26: recorded engine_v1-v4 and policy_v1-v4 on the pre-v5 engine (v5 Batch 0, INF-1 and INF-4 baseline).
- 2026-10-26: regenerated engine_v1-v4. Recorded on the pre-v5 engine (backup tree first on sys.path), not a change to v1-v4 output: the fixture gains resources/read and prompts/get requests, IPv6 and non-IP addresses and odd clients, and each file now also pins exact float digests (float.hex, with the platform), the final snapshot digest, and the verdicts after a snapshot/restore at day 15. The current engine gives the same exact digests.
