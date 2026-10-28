# Chapters 1-3 revision package

Prepared 28 October 2026 against 20260923.pdf and the Thesis Tracker tab, with the researcher-approved two-module amendment. These are proposed replacement passages for the editable manuscript. The original PDF has not been overwritten. No editable Chapters 1-3 or department LaTeX template was located in the inspected project and usual document locations.

## Revision map

| Location in original PDF | Required revision | Basis |
| --- | --- | --- |
| Chapter 1 objectives, pages 7-8 | Preserve the three objectives; distinguish implementation from demonstrated improvement | Actual Chapter 4 findings |
| Chapter 1 scope, page 8 | Replace the 182 integrated barangays category with City Planning and Development Office in the evaluated five-category scope | Issued corpus and scenario allocation |
| Chapter 1 significance and claims | Express reduced congestion, better service and reduced misinformation as potential benefits, not measured results | No transaction, workload or citizen outcome data |
| Chapter 2 synthesis | Keep verified original literature and citations; distinguish the proposed dictionary mechanism from empirical proof | B-C differences do not demonstrate superiority |
| Chapter 3 framework, pages 24-25 | Retain normalization, retrieval, grounded generation and offline evaluation | Frozen architecture |
| Chapter 3 preprocessing, page 28 | State actual 120-token windows, 20-token overlap and source/table verification | Evaluated corpus and repair archive |
| Chapter 3 retrieval/generation, pages 29-31 | Report selected K=3 and actual registered weights/settings | Candidate registration and execution manifest |
| Chapter 3 evaluation, pages 32-34 | Separate development selection, held-out execution and later source-label reconciliation | Two crosswalk hashes and archived metrics |
| Section 3.2.9, page 35 | Replace A/B-only allocation with two-module amendment and actual limitations | Adviser mandate and issued triple packets |
| Analysis, page 36 | Describe separate ordinal alpha and exploratory scenario-paired comparisons | Analysis plan and numerical outputs |

## Chapter 1: proposed scope replacement

The evaluated prototype addresses charter-based service inquiries from five categories: the Business Bureau, City Treasurer's Office, Office of the City Building Official, Bureau of Fire Protection, and City Planning and Development Office. The benchmark contains English, Taglish and Bislish variants of the scenarios. The study evaluates information retrieval and generated guidance from the archived charter corpus. It does not cover every barangay transaction, conduct actual permit processing, or establish legal compliance of an applicant. The system is an informational research prototype rather than an official transaction service.

## Chapter 1: proposed contribution and significance wording

This study implements and evaluates a dictionary-assisted hybrid retrieval-augmented generation pipeline for code-switched local government inquiries. Its intended contribution is a reproducible method for preserving query intent, retrieving charter evidence and evaluating the resulting answers. Improvements in office workload, citizen satisfaction and transaction completion are possible future benefits, but they are not measured outcomes of this study. Whether query-specific dictionary injection improves the evaluated outcomes is an empirical question rather than an assumed result.

Retain the existing three research questions and objectives. Do not rewrite them after seeing results to imply that statistical superiority was guaranteed. Replace statements that the prototype eliminates misinformation with statements that it aims to reduce unsupported responses and that remaining errors are assessed.

## Chapter 2: targeted editorial changes

Keep the original verified references and theoretical discussion. In the synthesis, distinguish evidence for retrieval augmentation in the literature from evidence for this specific dictionary and corpus. Replace any prediction stated as a demonstrated result with a hypothesis or design rationale. Add a transition explaining that the three-configuration comparison tests the proposed components under shared generation conditions. Do not invent citations, publication details or a new literature review from the experiment results. A source-level bibliography check remains part of final manuscript integration.

## Chapter 3: preprocessing and pipeline replacement

The evaluated corpus comprises 1,082 chunks from 358 source pages. Source text and table representations retain document and page provenance. Table repairs are checked against rendered source pages and archived with earlier extractions. Text is divided into actual-token windows of 120 tokens with 20-token overlap; terminal windows may be shorter. Retrieval and fusion operate at chunk level. Source-table repair is distinct from section-based retrieval, which is not part of the evaluated method.

Configuration A retrieves using BM25 from the original query. Configuration B uses query-specific municipal dictionary injection during normalization followed by hybrid retrieval. Configuration C disables query-specific injection while retaining the other B components, including shared static lexical prompt guidance. This limits the ablation to the incremental query-specific injection mechanism. All configurations use the same registered generator and answer prompt.

Development selection considered the permitted retrieval cutoffs K=3 and K=5. The final registered candidate uses K=3, BM25 weight 0.75, dense weight 0.25 and dictionary retrieval-boost weight 0. Dictionary injection in B remains active despite the zero retrieval-boost weight. The registered Mistral generator uses temperature 0, top-p 0, context setting 8,192 and maximum prediction setting 1,536. Normalization uses temperature 0, top-p 0 and maximum prediction setting 150. RAGAS is an offline evaluator rather than a live response repair loop.

The executed prompt includes citation guidance. The original manuscript's wording concerning two complete format examples is not fully represented in the registered prompt; this implementation discrepancy is disclosed rather than repaired retrospectively in the frozen experiment. Report the runtime, model digest and package versions from the execution manifest and environment records. Do not copy proposed hardware or operating-system specifications as if they were verified execution measurements.

## Chapter 3: benchmark and label-version replacement

The development partition contains 30 scenario groups and 90 language-specific queries. The held-out partition contains 70 groups and 210 queries per configuration. All 630 planned outcomes were archived, including clarification and incomplete generation. Missing judge scores remain missing and matched descriptive comparisons identify the observed denominator for each metric.

The source-span crosswalk registered before inference yielded complete retrieval labels for 59 groups and 177 queries. A later reconciliation extended labels to 70 groups and 210 queries. Chapter 4 reports the original complete-label subset as the primary retrieval table and the later reconciled export separately. The crosswalk files and hashes are retained. The later mappings are not represented as if they had all been registered before inference. These label revisions do not constitute a new generation run.

## Section 3.2.9: proposed two-module audit replacement

Three auditors evaluate a fixed category-balanced subset of 20 scenario groups, four per category. The subset was selected after automated evaluation using a fixed ordering of group identifiers within categories rather than observed answer quality. This timing is disclosed; the sample was not registered before T07 outcomes. The researcher confirmed that formal scoring had not started when the two-module amendment was approved.

Module 1 evaluates normalized queries from B and C for 40 code-switched inputs: 20 Taglish and 20 Bislish. Each auditor scores both outputs against the statement, "This normalized query preserves the meaning, intent, and explicit details of the original query." The scale is 1 Strongly Disagree, 2 Disagree, 3 Neither Agree nor Disagree, 4 Agree and 5 Strongly Agree. This yields 80 ratings per auditor and 240 overall.

Module 2 evaluates A, B and C responses for all 60 queries, including English. Each auditor reviews 180 responses, yielding 540 response reviews and 1,080 dimension scores across three auditors. Answer Relevance and Factual Faithfulness retain the separate four-point rubric in Table 2. Together the modules yield 780 output reviews and 1,320 dimension scores. The two scales are never pooled.

Archived questions, outputs and retrieved passages are retained verbatim. System identities are masked and presentation orders randomized. The instrument specifies five sessions: Module 1 followed by four Module 2 blocks of 15 queries, with at least ten-minute breaks between sessions and after the first 20 Module 1 queries. These are protocol requirements; do not claim that actual session timings or break compliance were observed without collection records.

The actual packets contain shared opaque suffixes that permit linkage between 80 cross-module outputs. Content can also reveal similarities. Therefore, the implemented interface does not guarantee perfect blinding. Final exports require scores in the appropriate scale; unfinished drafts may remain blank. Scores are not generated, corrected or imputed during consolidation.

The supplied records are treated as independently assigned scores on the researcher's explicit confirmation. Conflicting preparation metadata in earlier files, the correction record and unchanged scores are preserved. Collection provenance is attributed to this confirmation rather than inferred from statistical agreement. Seven no-claim outputs remain in the primary analysis; a separate descriptive sensitivity analysis reports the effect of excluding them. The earlier automatic scoring convention is disclosed as a limitation rather than silently imposed on the analysis.

## Chapter 3: analysis replacement

Ordinal Krippendorff's alpha is calculated separately for Module 1 fidelity and the two Module 2 dimensions. The manuscript's 0.80 target concerns inter-rater agreement, not proof of system superiority. Percentile intervals use 2,000 category-stratified scenario-group bootstrap samples with associated languages, outputs and raters retained together. Inference is conditional on the three observed raters.

The comparison plan is exploratory: it was recorded before the current computation but after ratings and earlier summaries were available. Scores are averaged within each scenario and configuration across the applicable language variants and raters, yielding 20 paired scenario units. Two-sided exact signed-rank tests compare B-C fidelity and B-A, C-A and B-C for each answer dimension. Zero differences are omitted, tied absolute differences use midranks, and Holm adjustment covers all seven primary comparisons. Scenario-bootstrap mean-difference intervals are descriptive and unadjusted for multiplicity. Sign-test sensitivity results are reported separately. Nonsignificance is not interpreted as equivalence.

## Integration requirements

These passages must be merged into the editable manuscript using its actual subsection titles and citation style. Recheck Table 2 verbatim, chapter numbering, figure/table numbering, bibliography and cross-references after integration. Preserve the dated original PDF and amendment. T15 remains in progress until the replacement text is applied and checked in the editable source; preparing this package does not complete T16 formatting or T17 approval.
