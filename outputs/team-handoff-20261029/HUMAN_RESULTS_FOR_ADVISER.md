# Human expert evaluation results

Prepared for Christian and the research team on 29 October 2026. The analysis of the supplied expert ratings is complete and has been reproduced from the preserved input snapshot. The main finding is **strong rater agreement without a statistically established system advantage**. Answer relevance remains a practical limitation.

## Evaluation allocation

The original manuscript's A/B-only allocation was amended on 26 October for two modules. The amended design retains the same 20 scenario groups, four per service category, and three raters.

| Module | Comparison | Allocation across three raters | Scale |
| --- | --- | --- | --- |
| 1 — normalized query fidelity | B versus C | 40 code-switched queries × 2 outputs × 3 raters = 240 ratings | Five-point agreement |
| 2 — final answers | A versus B versus C | 60 queries × 3 outputs × 3 raters = 540 answer reviews | Separate relevance and faithfulness scores, each 1–4 |

Module 2 supplies 1,080 dimension scores. Together, the two modules contain 780 output-review records and 1,320 scores. There are no missing scores, duplicate scores or imputed values in the validated input. These are repeated ratings of shared scenarios, not 780 independent scenarios.

## Descriptive human results

| Dimension | A mean | B mean | C mean | Median |
| --- | ---: | ---: | ---: | --- |
| M1 normalization fidelity, 1–5 | Not applicable | 3.7583 | 3.7667 | B and C: 4 |
| M2 relevance, 1–4 | 2.3222 | 2.2833 | 2.2778 | All: 2 |
| M2 faithfulness, 1–4 | 2.7167 | 2.7278 | 2.6222 | All: 3 |

Each M1 configuration has 120 ratings; each M2 configuration/dimension has 180. Keep the two scales separate. Score frequencies appear in [the distribution CSV](tables/human_score_distributions.csv); means alone do not capture the ordinal distribution.

For normalization, Taglish medians were 5 and Bislish medians were 3 in both B and C. The corresponding means were B 4.5333/C 4.5833 for Taglish and B 2.9833/C 2.9500 for Bislish. These are descriptive breakdowns, not additional significance tests.

For relevance, 60.0% of A ratings and 61.1% of both B and C ratings were 1 or 2. The rubric associates these categories with an irrelevant response or an answer that misses the primary procedural need. Thus, successful implementation and high agreement must not be described as consistently high answer quality.

## Agreement and paired comparisons

| Dimension | Ordinal alpha | 95% scenario-bootstrap interval |
| --- | ---: | --- |
| M1 fidelity | 0.9354 | [0.8945, 0.9641] |
| M2 relevance | 0.9112 | [0.8590, 0.9424] |
| M2 faithfulness | 0.8732 | [0.8011, 0.9229] |

All point estimates exceed the manuscript's 0.80 target. Alpha describes agreement, not model accuracy, superiority, or proof of independent collection.

The exploratory analysis averages ratings and languages within each scenario/configuration and compares **20 paired scenario units**. The seven comparisons are B–C fidelity and B–A, C–A and B–C for each Module 2 dimension. All Holm-adjusted p-values are **1.0000**. The data therefore do not establish a significant difference among the compared systems. This does not prove equivalence. Full effects, raw p-values and nonzero-pair counts are in [paired_comparisons.csv](tables/paired_comparisons.csv).

## Text suitable for the results discussion

The expert audit demonstrated consistent ordinal judgments across normalization fidelity, answer relevance and factual faithfulness, with Krippendorff's alpha values exceeding the specified 0.80 target. However, the paired comparisons did not establish significant differences among the evaluated configurations after correction for seven tests. The results therefore support the reproducibility of the collected judgments while identifying continuing limitations in procedural relevance and factual precision. The incremental human-rated benefit of query-specific dictionary injection was not established in this sample.

## Evidence and qualifications

- [Original analysis plan and results](../../experiments/t10-t12-human-analysis-v1/) and [29 October replay receipt](HUMAN_RESULTS_QA.json): all numerical sections reproduced exactly; aggregate CSV files are byte-identical; zero score edits and zero model calls.
- [Chapter 3 amendment](../../experiments/t08-t09-expert-audit-v2-triple/CHAPTER3_AMENDMENT.md): module allocation and different scales. It must be incorporated into the editable manuscript when integration resumes.
- Independence is attributed to the researcher's explicit confirmation. Earlier conflicting preparation metadata and the correction history remain preserved; this verification did not observe scoring sessions or independently certify auditor qualifications.
- The audit subset was selected after automated evaluation using a fixed group-ID rule. The comparison analysis is exploratory. The chapter draft preserves those timing and blinding limitations.
- The website's later 200-question dry run and unpromoted prompt candidate are separate from the human ratings used in the paper. Neither changed these scores or the archived study outputs.

The numerical tables are ready for manuscript review. Adviser approval, official-template integration and institutional submission are separate pending steps.
