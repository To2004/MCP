# v4static runs made BEFORE the classifier was hardened

These five scans used `static_impact.py` as it stood when they were submitted —
before the robustness pass that added parameter signals, `openWorldHint`,
tool-poisoning suspicions, description hashing, the negation guard, and the
missing verb families (insert / clear / flush / reset / share / archive …).

Kept for comparison. Current results are in `../five_level_v2_pure_v4static/`.
