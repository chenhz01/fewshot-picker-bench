# Alignment Audit (Rules 85-100 / 16 items) — fewshot-picker-bench v0.1.1

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Safety/Ethics section | N/A | Not a security-research repo; no dual-use surface. Input validation fails closed (exit 2) on malformed JSONL |
| 2 | Privacy/dezero | PASS | No secrets/tokens/real names in any file; only contact line uses hcac4735@agent.qq.com (README License section); grep `(sk-\|ghp_\|api[_-]?key\s*=\s*['"][A-Za-z0-9])` → 0 hits |
| 3 | Copyright boundary | PASS | shotpick / TreePrompt-Code / fewshot-boost-results comparisons are structural restatements of their public descriptions, no >50-char copied text; MIT LICENSE present, "zhengming contributors" |
| 4 | Fact-check annotation | PASS | 68-check suite runtime "~3 s" marked [Measured] with repro `python self_test.py`; other timings marked ~; quality claims qualitative |
| 5 | Confidence grading | PASS | Opener determinism claim [High ≥80%] tied to the suite; MMR-suitability claim qualified for "tens-to-hundreds" pools; ≥2 explicit labels |
| 6 | PLAN B built-in | PASS | "Minimal Fallback (PLAN B)" section: grep keyword-count triage with zero setup |
| 7 | Timeout preset | PASS | Quickstart states "~3 min" total with ~1 min prepare / ~1 s pick / ~3 s suite markers |
| 8 | Rule-conflict arbitration | PASS | "Design Trade-offs" opens with priority order: determinism > explainability > zero-dependency > raw retrieval quality |
| 9 | Version changelog | PASS | CHANGELOG.md v0.1.0 + v0.1.1; v0.1.1 records documentation completion and suite re-verification |
| 10 | Exemption instruction | N/A | Session-level rule; static repo content not applicable |
| 11 | External-knowledge cutoff | PASS | why-not-X comparisons and equivalence claim dated "as of 2026-10-12" |
| 12 | Assumption explicitness | PASS | "[Core Assumptions]" section with 4 items |
| 13 | Logic-check trio | PASS | self_test.py three-tier suite (functional / error / extreme-edge); `python self_test.py` → `SUMMARY: PASS 68/68` |
| 14 | Socratic question | PASS | FAQ "When NOT to use this tool?" with 4 anti-use-cases (tiny pool, semantic matching, multilingual, fine-tuning curation) |
| 15 | Pareto improvement | PASS | v0.1.1 documentation round: README adds why-not-X anchors, PLAN B, trade-off ordering, and quality-report semantics absent from the bare module docstring — completeness improvement traceable in CHANGELOG |
| 16 | Ultimate fallback (≤60-word opener) | PASS | First paragraph = 57 words, contains what-it-is and "same input, same picks, every run" judgment sentence |

Second-order effects (rule 16 bonus): PASS — "Limits & Second-order Effects" covers pool freezing, λ metric-gaming, and structural-vs-task quality confusion.

Scan evidence: `grep -rEn "(sk-|ghp_|api[_-]?key\s*=\s*['\"][A-Za-z0-9])" .` → 0 hits; `grep -rn "hcac4735@agent.qq.com" README.md` → 1 hit.
