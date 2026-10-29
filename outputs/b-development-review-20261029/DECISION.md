# Decision: retain experiments, do not promote yet

Completed: full B/C normalization traces; two isolated candidate changes; one source-checked dictionary entry with backup and exact diff; full 90-query retrieval comparisons at K=3 and K=5; 17-weight fusion diagnostics for both B/C (68 conditions); six guardrail tests and input/hash checks.

At unchanged weights, archived B Hit@3/MRR@3 = 0.7000/0.6167. Prompt candidate = 0.7222/0.5963. Prompt plus bayad correction = 0.7111/0.6056. These are mixed results, not a demonstrated overall improvement.

The grid's highest observed B Hit@5 is 0.8333 at weights 0.4/0.5/0.1, versus archived B 0.7111 at K=5. This is exploratory best-of-grid retrieval performance, not selected weights, a new final score, or evidence of answer-quality superiority. C also improves with different weights. The Chapter 3 selection objective remains macro context precision across 15 office-language cells.

Promotion and new answer generation are blocked by persistent semantic defects: purpose becomes location, selling becomes inspecting, tax questions acquire receipt assumptions, and conditions are weakened. The new glossary fixes some fee wording but does not solve the whole normalizer. No automatic literal checker certifies meaning.

Next engineering work: review the amilyar entry against its source context and test a narrowly defined candidate; investigate the purpose/action errors on development records without copying answer facts into normalization. Do not force ambiguity through retrieval or tune against known held-out outcomes. Changes to the shared generator must be applied fairly across A/B/C. When normalization clears review, run matched answer generation and offline evaluation; any new confirmatory superiority claim requires untouched scenario groups and new ratings.

No manual action is required to inspect these results. This does not claim all proposed improvement work is finished, that B is now stronger overall, or that new expert validation has occurred. Original study and live app remain unchanged.

Branch: development/b-dictionary-fidelity-20261029
