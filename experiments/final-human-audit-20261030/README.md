# October 30 human-audit results

These are the files supplied through Christian's CLEAN package on 12 November 2026. They supersede the October 28-29 analysis in the active release tree; earlier evidence remains in the archive tag.

- `results/descriptive_scores.csv`: descriptive ratings by configuration and language.
- `results/reliability.csv`: ordinal Krippendorff's alpha and confidence intervals.
- `results/paired_comparisons.csv`: scenario-group paired comparisons with Holm correction.
- `results/analysis_results.json`: combined analysis; reproduced exactly from the supplied packets.
- `raw_packets/`: local private source exports, excluded from GitHub.

Module 1 contains 240 fidelity ratings (40 queries x two outputs x three raters). Module 2 contains 540 answer reviews (60 queries x three outputs x three raters), each with relevance and faithfulness. Total: 1,320 dimension scores. Do not describe these as 1,320 independent respondents.

In this supplied analysis, B and C score higher than A on Module 2 with significant Holm-adjusted paired contrasts. B versus C does not show a significant difference. Reliability point estimates are approximately .510 (fidelity), .771 (relevance), and .781 (faithfulness), all below the .80 target. Report those limitations alongside the comparisons.

This check establishes reproducibility of the calculations, not independent verification of human authorship, blinding or independence. The raw exports are retained unchanged. See `docs/cleanup/human_qa.json` and `docs/cleanup/RELEASE_NOTES.md` for validation and caveats.
