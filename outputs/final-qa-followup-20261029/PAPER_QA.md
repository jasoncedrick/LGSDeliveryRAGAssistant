# Paper consistency review - 29 October 2026

The [Chapters 4-5 review draft](../team-handoff-20261029/CHAPTERS_4_5_REVIEW.pdf) remains the current paper draft. Its numerical tables and source files are checked by the new offline QA command. This review does not change expert scores, produce another evaluation, or declare adviser approval. Integration into editable Chapters 1-3 and the official template remains deferred as requested.

## Research questions and defensible conclusions

| Manuscript objective | Evidence in the current draft | Conclusion the evidence supports |
| --- | --- | --- |
| Implement an approach capturing charter identifiers and conversational intent (PDF pages 7-8) | Chapter 4.2: 1,082 chunks, 358 pages, 120/20 token windows, chunk-level retrieval and registered settings; Chapter 4.5: separate normalization audit | Implementation is demonstrated. Intent preservation is measured and imperfect, particularly in the descriptive Bislish scores. |
| Compare the proposed method with retrieval baselines | Chapter 4.4: original 177-query subset and separately labeled 210-query reconciliation; Chapter 4.8: seven scenario-paired human comparisons | B/C have descriptive retrieval gains over A. Dictionary-specific superiority and statistical human-rating superiority are not established. |
| Evaluate relevance and factual faithfulness | Chapters 4.3, 4.6-4.8: missing automated metrics, ordinal human distributions, agreement and comparisons | Strong inter-rater agreement coexists with substantial low-category ratings. It is not a factual-correctness certificate. |

The two-module totals remain 240 normalization ratings plus 540 answer reviews with two scores each: 780 review records and 1,320 scores. The 20 scenario groups are the paired analysis units; individual ratings are not independent citizen trials. The five-point and four-point scales remain separate. No new language significance test is inferred from Table 4.6.

The chapter language correctly distinguishes a nonsignificant result from equivalence. It also retains limitations concerning the post-outcome audit selection, shared static guidance in C, linked opaque IDs, missing judge outputs, later source-label reconciliation, and researcher-confirmed collection provenance.

## Remaining manuscript consistency edits

The existing [Chapters 1-3 revision package](../manuscript-closeout-20261028/CHAPTERS_1_TO_3_REVISION_PACKAGE.md) already provides replacement text for scope, audit allocation and analysis. These are integration items, not a request to repeat expert scoring.

| Original manuscript text | Required treatment when integration resumes |
| --- | --- |
| Chapter 1, PDF page 8: 182 integrated barangays in the five-category scope | Describe the evaluated five-source scope including CPDO, as the existing revision package specifies. Do not claim coverage of all barangay procedures. |
| Chapter 1, PDF page 8: reduced congestion and elimination of misleading advice | Keep these as intended future benefits. Neither staff workload nor actual citizen transaction outcomes were measured. |
| Chapter 3, PDF page 31: deterministic settings guarantee legally consistent outputs | Report the actual decoding settings without claiming that settings guarantee factual correctness or identical outputs across environments. |
| Chapter 3, PDF page 31: two format examples in the prompt | Preserve the disclosed discrepancy with the frozen generation prompt. Later website prompt examples do not retrospectively change the completed experiment. |
| Chapter 3, PDF page 31: cloud-hosted backend and asynchronous interaction archiving | Distinguish the archived research batch execution from the subsequent Vercel frontend plus PC-hosted demonstration. The citizen endpoint does not write question/answer history to disk. |
| Chapter 3, PDF page 35: A/B-only, 360 expert records | Integrate the approved two-module amendment: B/C normalization and A/B/C answers, including the different scales and 540 Module 2 reviews. |
| Chapter 3, PDF page 36: alpha >= .80 proves statistically significant consensus | Describe .80 as the manuscript's agreement target. It is not a p-value or evidence of superiority. |
| Chapter 3, PDF page 36: proposed Ubuntu/Python/runtime specifications | Use the archived execution environment and package versions for the corresponding run. Do not substitute this week's website QA environment for the frozen evaluation environment. |

## Copy-ready deployment distinction for integration

The final research evaluation was executed and archived under the registered configuration. A subsequent citizen-facing demonstration used a static frontend on Vercel and a FastAPI/model backend running on the researcher's PC through an HTTPS tunnel. The demonstration depends on the PC, model service and tunnel remaining available. Its response-language and intake revisions are post-study engineering changes and did not generate the automated or human results reported in Chapter 4. Research batch records retain the evaluation evidence; the citizen endpoint does not persist question-and-answer history. The demonstration therefore differs from the originally proposed fully cloud-hosted backend and must not be described as an always-on or officially certified city service.

## Tracker interpretation

The original Downloads workbook's **Thesis Tracker** tab was checked again. Its old T13-T16 status cells predate the completed drafting work; the versioned 28 October workbook records T13/T14 drafts complete, T15 in progress and T16 not started. Neither workbook is changed by this follow-up. A prepared draft is not adviser approval or a final formatted submission.

## Reference trail

- `D:/thesis/20260923.pdf`: PDF pages 7-8, 31, 35-36, read directly for this review.
- [Researcher-approved audit amendment](../../experiments/t08-t09-expert-audit-v2-triple/CHAPTER3_AMENDMENT.md).
- [Human analysis plan](../../experiments/t10-t12-human-analysis-v1/analysis_plan.json), results and preserved input manifest.
- [Current chapter source manifest](../team-handoff-20261029/source_manifest.json) and [versioned tracker](../manuscript-closeout-20261028/thesis_progress_tracker_updated.xlsx).
- [Citizen runtime](../../app/website.py) and [website deployment documentation](../../website/README.md).

The adviser still needs to review the interpretations and approve the integrated manuscript. No additional manual source or rating assignment is created here.
