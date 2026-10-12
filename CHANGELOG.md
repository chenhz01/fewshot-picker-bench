# Changelog

## v0.1.1 — 2026-10-12
- Documentation layer completed: README (Problem / How it works / Quickstart / why-not-X anchored on shotpick, TreePrompt-Code, fewshot-boost-results / Minimal Fallback / Trade-offs / Limits / FAQ), ALIGNMENT.md 16-item audit.
- Self-test re-verified green, no code changes needed this round: `python self_test.py` → `SUMMARY: PASS 68/68`.

## v0.1.0 — 2026-10-11
- Initial implementation: tokenizer with generic-stopword filter, TF-IDF corpus vectors + cosine relevance, deterministic MMR re-ranker (ties → lower index), quality self-report (Jaccard redundancy, query coverage with covered/missed profile, label diversity, mean relevance), JSONL loader with per-line validation, CLI (`--query`, `--k`, `--lambda`, `--json`, exit 2 on bad input).
- Self-test suite (functional / error / extreme-edge tiers).
