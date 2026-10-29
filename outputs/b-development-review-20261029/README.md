# B development experiment: measured results

Post-study exploratory development only. Original held-out results and human ratings are unchanged.

| Configuration | Variant | K | Queries | With context | Hit@K | MRR@K |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| A | archived | 3 | 90 | 90 | 0.6778 | 0.4296 |
| A | archived | 5 | 90 | 90 | 0.7444 | 0.4452 |
| B | archived | 3 | 90 | 84 | 0.7000 | 0.6167 |
| B | archived | 5 | 90 | 84 | 0.7111 | 0.6194 |
| B | candidate | 3 | 90 | 84 | 0.7222 | 0.5963 |
| B | candidate | 5 | 90 | 84 | 0.7333 | 0.5991 |
| C | archived | 3 | 90 | 84 | 0.7000 | 0.6167 |
| C | archived | 5 | 90 | 84 | 0.7111 | 0.6194 |
| C | candidate | 3 | 90 | 84 | 0.6667 | 0.5926 |
| C | candidate | 5 | 90 | 84 | 0.6889 | 0.5976 |
| B | prompt + bayad gloss | 3 | 90 | 84 | 0.7111 | 0.6056 |
| B | prompt + bayad gloss | 5 | 90 | 84 | 0.7222 | 0.6078 |
| C | prompt + bayad gloss | 3 | 90 | 84 | 0.6667 | 0.5926 |
| C | prompt + bayad gloss | 5 | 90 | 84 | 0.6889 | 0.5976 |

## What changed

- New preservation-focused few-shot normalization prompt, applied identically to B and C. B still injects definitions; C does not.
- Separate one-entry dictionary candidate: bayad, “Monetary settlement of assessed regulatory fees” → “Fee or payment”. Original definition, governance tag, polysemy flag, and disambiguation settings remain archived. Only the definition changes in the candidate copy.
- Original corpus, indices, 120/20 token windows, K=3/5, generation prompt and runtime defaults are unchanged.
- Partial first prompt draft stopped because it lacked the existing examples. It is preserved and excluded from comparisons.

## Interpretation and gates

These are retrieval diagnostics, not new human ratings or proof of answer-quality superiority. All 90 queries are included; no-context outcomes remain in the denominator. No new retrieval weights have been selected.
Chapter 3 requires macro context precision across the 15 department/language cells for weight selection. Hit/MRR alone cannot promote a candidate. Positive and negative changes appear in query_deltas.csv.
The original held-out set has already been examined. A new confirmatory claim requires untouched scenario groups and, for revised answer-quality claims, new human ratings.

## Evidence

- experiments/b-fidelity-development-20261029-v2/: protocol, exact inputs/hashes, original versus revised queries, traces and full metrics.
- experiments/b-dictionary-bayad-development-20261029-v1/: dictionary backup, candidate, exact diff, rendered-source review, reuse provenance and full metrics.
- scripts/evaluate_b_fidelity_candidate.py; scripts/evaluate_b_dictionary_gloss.py: reproducible sequential runners.
- tests/test_b_fidelity_experiment.py: experiment guardrails.

No changes were deployed. No superiority or large improvement is guaranteed.
