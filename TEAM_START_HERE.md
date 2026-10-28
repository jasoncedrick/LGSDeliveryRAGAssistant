# Human expert results and teammate handoff

**Christian: yes, the human-rating results are in this branch.** Start with the results brief below, then the revised Chapters 4 and 5. These are the paper's human-audit results; the website dry run is a separate engineering experiment.

Branch: `handoff/human-results-chapters45-20261029`. Prepared 29 October 2026.

1. [Human results for adviser review](outputs/team-handoff-20261029/HUMAN_RESULTS_FOR_ADVISER.md) — allocation, scores, agreement, comparisons and the conclusion supported by the data.
2. [Chapters 4 and 5 PDF](outputs/team-handoff-20261029/CHAPTERS_4_5_REVIEW.pdf) — 15-page revised review draft with eight tables and three figures.
3. [Editable Chapter 4](outputs/team-handoff-20261029/CHAPTER_4.md) and [Chapter 5](outputs/team-handoff-20261029/CHAPTER_5.md).
4. [Aggregate CSV tables](outputs/team-handoff-20261029/tables) and [original human analysis report](experiments/t10-t12-human-analysis-v1/T10_T12_REPORT.md).
5. [What changed and what remains unresolved](outputs/team-handoff-20261029/CHANGELOG.md) and [final QA](outputs/team-handoff-20261029/QA_REPORT.json).

## What is complete

- Human analysis: 240 Module 1 records and 540 Module 2 records, totaling 780 records and 1,320 dimension scores. No missing or imputed scores.
- Ordinal agreement: 0.9354 normalization fidelity, 0.9112 relevance, 0.8732 faithfulness.
- Seven scenario-paired comparisons: no significant system difference after Holm correction. Do not present high agreement as proof that the proposed system is superior or consistently correct.
- A 29 October replay from the preserved ratings exactly reproduced the descriptive statistics, reliability, comparisons and sensitivity results. Original scores were unchanged.
- Citizen website presentation: passage quotations removed from the response display; reference names, citation navigation and PDF/page links retained. Formal audit packets and retrieved evidence archives were not altered.

## What is still pending

The Chapters 4–5 deliverables are review drafts, not adviser-approved final chapters. Editable Chapters 1–3 integration and the official department template remain deferred as previously instructed. The latest versioned [Thesis Tracker workbook](outputs/manuscript-closeout-20261028/thesis_progress_tracker_updated.xlsx) marks T13/T14 draft work complete, T15 in progress and T16 not started. Use its **Thesis Tracker** tab. T17/T18 still require actual adviser approval and submission.

The inherited website grounding candidate **failed answer-quality QA**. It contains documented unsupported claims and language failures. This handoff does not repair or promote that candidate, and no production deployment or model/judge rerun was performed. The current live site remains a separate earlier release. See [the 200-question review](outputs/website-grounding-qa-20261028/READ_THIS_FIRST.md). Do not restart the public backend from this branch without a separate promotion decision.

## Get this branch

For a fresh teammate checkout:

```powershell
git clone --branch handoff/human-results-chapters45-20261029 --single-branch https://github.com/jasoncedrick/LGSDeliveryRAGAssistant.git
```

For an existing clone, first save or commit local work, then:

```powershell
git fetch origin
git switch --track origin/handoff/human-results-chapters45-20261029
```

The PDF, Markdown and aggregate CSVs can be reviewed without starting a model server. Numerical reproduction requires the researcher's private input snapshot and audit mapping, which are intentionally excluded from Git. Credentials, private audit keys and individual rating records are not part of this public handoff. Request a controlled transfer from the researcher if authorized to inspect those inputs; aggregate results and their verification receipts are included here.

## Website console and QA

The browser shows queue position and request progress. Server access logs show request/status activity, not a factual-correctness verdict. A running console does not mean an answer is supported.

The scoped software checks below use synthetic responses and no model calls. The browser checks need the local website/static server available and the configured Playwright/Chrome installation; the statistics/audit checks also need local private artifacts and analysis dependencies.

```powershell
D:\thesis\venv\Scripts\python.exe -m unittest tests.test_citizen_website tests.test_website_language tests.test_website_queue tests.test_website_grounding -v
node scripts/test_citizen_website_browser.cjs
node scripts/test_website_motion.cjs
```

No new expert scoring or duplicate manual review is needed to use the existing human-result tables. Adviser interpretation and manuscript approval remain human decisions.
