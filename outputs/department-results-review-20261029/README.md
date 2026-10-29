# Results by department

Descriptive review, 29 October 2026. Existing archived scores only: no new model run, score changes or department-level significance tests.

Each department contributes four human-audit scenario groups. Module 2 has 12 queries and 36 ratings per configuration per dimension (three raters). Module 1 has eight code-switched queries and 24 ratings per configuration. These repeated ratings are not independent citizen samples.

## Human answer relevance (1-4)

| Department | A | B | C |
| --- | ---: | ---: | ---: |
| Business Bureau | 1.750 | 1.833 | 1.750 |
| Treasury (CTO) | 2.194 | 2.528 | 2.528 |
| Building (OCBO) | 2.667 | 2.528 | 2.528 |
| Fire Protection (BFP) | 2.472 | 2.389 | 2.472 |
| City Planning (CPDO) | 2.528 | 2.139 | 2.111 |

## Human factual faithfulness (1-4)

| Department | A | B | C |
| --- | ---: | ---: | ---: |
| Business Bureau | 2.333 | 2.278 | 2.278 |
| Treasury (CTO) | 3.611 | 2.722 | 2.472 |
| Building (OCBO) | 2.167 | 2.194 | 2.194 |
| Fire Protection (BFP) | 3.194 | 3.417 | 3.250 |
| City Planning (CPDO) | 2.278 | 3.028 | 2.917 |

## Human normalization fidelity (1-5)

| Department | B | C |
| --- | ---: | ---: |
| Business Bureau | 3.875 | 4.125 |
| Treasury (CTO) | 4.000 | 3.750 |
| Building (OCBO) | 4.000 | 3.875 |
| Fire Protection (BFP) | 3.958 | 3.958 |
| City Planning (CPDO) | 2.958 | 3.125 |

## Why the overall human means are close

The averages conceal opposing department-level differences. For faithfulness, B minus A is +0.750 in CPDO but -0.889 in CTO. For relevance, B minus A is -0.389 in CPDO but +0.333 in CTO. Every department contributes the same number of human ratings, so those opposing differences largely cancel. These are descriptive differences, not established departmental treatment effects.

Rater notes illustrate the different dimensions: in CTO-007 Taglish, R01 assigned A faithfulness 4 for a limited supported answer and B faithfulness 1 for a wrong core fee. In CPDO-016 Bislish, R01 assigned A faithfulness 1 for an invented acronym expansion and unrelated citation, and B faithfulness 4 while noting that B still omitted requested development types. These are specific recorded assessments, not a new source/legal ruling or a claim that every score is independently certified.

B and C produced identical answer text on 48/60 audited queries: BB 8/12, CTO 10/12, OCBO 11/12, BFP 10/12 and CPDO 9/12. A and B matched on only 2/60. This helps explain B/C similarity; A similarity mainly reflects comparable scores on different answers and offsetting wins.

## Automated Hit@3 (%)

| Department | Matched queries | A | B | C |
| --- | ---: | ---: | ---: | ---: |
| Business Bureau | 39 | 46.154 | 46.154 | 46.154 |
| Treasury (CTO) | 36 | 47.222 | 50.000 | 52.778 |
| Building (OCBO) | 42 | 57.143 | 71.429 | 69.048 |
| Fire Protection (BFP) | 21 | 61.905 | 85.714 | 85.714 |
| City Planning (CPDO) | 39 | 69.231 | 87.179 | 87.179 |

## Automated MRR@3

| Department | Matched queries | A | B | C |
| --- | ---: | ---: | ---: | ---: |
| Business Bureau | 39 | 0.261 | 0.385 | 0.368 |
| Treasury (CTO) | 36 | 0.343 | 0.454 | 0.477 |
| Building (OCBO) | 42 | 0.381 | 0.556 | 0.544 |
| Fire Protection (BFP) | 21 | 0.444 | 0.833 | 0.833 |
| City Planning (CPDO) | 39 | 0.402 | 0.675 | 0.658 |

## Automated answer relevancy

| Department | Matched queries | A | B | C |
| --- | ---: | ---: | ---: | ---: |
| Business Bureau | 42 | 0.650 | 0.615 | 0.607 |
| Treasury (CTO) | 38 | 0.519 | 0.495 | 0.541 |
| Building (OCBO) | 40 | 0.589 | 0.551 | 0.561 |
| Fire Protection (BFP) | 42 | 0.538 | 0.557 | 0.572 |
| City Planning (CPDO) | 40 | 0.596 | 0.691 | 0.694 |

## Automated faithfulness

| Department | Matched queries | A | B | C |
| --- | ---: | ---: | ---: | ---: |
| Business Bureau | 40 | 0.801 | 0.700 | 0.758 |
| Treasury (CTO) | 35 | 0.722 | 0.790 | 0.765 |
| Building (OCBO) | 36 | 0.822 | 0.794 | 0.776 |
| Fire Protection (BFP) | 40 | 0.675 | 0.795 | 0.752 |
| City Planning (CPDO) | 37 | 0.722 | 0.743 | 0.748 |

The retrieval tables above use the ORIGINAL 177-query complete-label subset; eligible department counts differ. The RAGAS tables use metric-specific shared observed queries across A/B/C. These full-test automated samples are larger than the human sample and the score scales are different. Do not infer a numerical calibration or correlation between these means.

The CSV also supplies the later reconciled 210-query retrieval version, context precision/recall, and automated values restricted to the 20 human-audit groups. Original-label gaps and judge failures still reduce the matched counts in that restricted subset.

## Files

- [Human scores, sums, medians and denominators](human_scores_by_department.csv)
- [Automated scores: both label versions and both sample scopes](automated_scores_by_department.csv)
- [Paired query win/tie counts](paired_query_counts.csv)
- [Identical archived answer counts](identical_answers.csv)
- [Verification and source hashes](verification.json)

All department totals reproduce the existing overall results. The analysis uses the preserved input ratings and answer key; it does not average A/B/C together or alter their scores. Qualifying or explaining a finding does not establish the independence of collection, which remains attributed to the researcher confirmation recorded in the original analysis.
