**We have built the research prototype, prepared and reviewed the development corpus and references, completed the development A/B/C comparison, investigated retrieval and evaluator failures, prepared expert-rater materials, and started the frozen held-out evaluation.**

**As of October 19, 2026, 9:13 p.m. Philippine time:** the final run had archived **31 of 630 planned generation outcomes**. It was still generating answers; the final execution report did not yet exist. Expert grading, agreement analysis, and final significance testing remain pending.

The timeline below distinguishes **planned tracker dates** from **verified execution evidence**. The clean repository contains one initial commit dated October 19; earlier work was imported into that snapshot, so its exact completion dates cannot all be reconstructed.

**1. September 4–10 — Planned dictionary and corpus-development period, T01–T02**

The tracker scheduled the municipal dictionary and document-processing engine during this period. The current project contains:

- A municipal dictionary with definitions, service tags, and ambiguity rules.
- Five supplied Citizens’ Charter PDFs covering Business Bureau, CTO, OCBO, CPDO, and BFP.
- A tokenizer-based corpus builder using **120-token windows and 20-token overlap**.
- BM25 and FAISS retrieval indices.

The repaired corpus’s validation record reports **358 source pages, 1,082 chunks, and matching 1,082-row BM25/FAISS indices**, using 384-dimensional embeddings.

One reporting correction is needed: the tracker describes **150 dictionary entries**, but the current file contains **167 entries**, including **20 ambiguity-flagged entries**. We should report the actual version used and reconcile the description.

Evidence: [dictionary](D:/thesis/LGSDeliveryRAGAssistant-clean/data/municipal_dictionary_v1.json), [corpus validation](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/chapter3-table-repaired-development-v1/validation.json).

**2. September 11–17 — Planned local model and rater-coordination period, T03–T04**

The project implemented local Mistral inference, query normalization, ambiguity handling, and a FastAPI/browser application. The application connects dictionary lookup, normalization, retrieval, and answer generation.

The tracker marks rater coordination complete, but **I have not verified transmitted letters, institutional approval, or three confirmed rater commitments from the files reviewed**. Those should be supported by your correspondence before being reported as completed.

Likewise, the evidence supports a local research prototype; it does not establish that a public deployment is complete.

Evidence: [project overview](D:/thesis/LGSDeliveryRAGAssistant-clean/README.md), [progress tracker](C:/Users/User/Downloads/thesis_progress_tracker.xlsx).

**3. September 18–24 — Planned benchmark and evaluation-development period, T05–T07**

The benchmark design expanded to **100 scenario groups and 300 language variants**:

| Partition | Scenario groups | Query variants |
|---|---:|---:|
| Development | 30 | 90 |
| Held-out test | 70 | 210 |
| Total | 100 | 300 |

The grouped split keeps related language variants together. The final preflight later verified 70 held-out groups, 210 queries, 14 groups per office, and no development/held-out group-ID overlap.

The evaluation harness was implemented to calculate Hit@K, MRR, and offline RAGAS metrics while preserving questions, references, retrieved passages, answers, failures, and judge traces.

**The tracker’s original “T07 Complete” label was ahead of the actual final-evaluation evidence.** Development completion and final held-out completion were subsequently separated.

**4. Before the October 19 clean snapshot — Source extraction and table repairs**

Source inspection found that preserving PDF text did not always preserve table relationships. Examples included separated fee labels and amounts, detached conditions, and unclear associations between procedural steps.

We inspected source pages, staged repairs, and rebuilt matching corpus/index artifacts. User interpretations were recorded separately from literal source wording.

This work improved the evidence base, but **it did not certify every source statement or resolve ambiguities in the official documents**.

Evidence: [source-fidelity review](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/chapter3-step3-source-review/source_fidelity_review.json).

**5. Before the clean snapshot — Normalization tests and first development evaluation**

A 24-case normalization test suite was created. Its automatic checks passed **22 of 24 cases**, while exact English preservation and semantic fidelity remained limitations.

An initial **90-query development batch** produced:

- **84 answers**
- **6 clarification outcomes**

Five development references were corrected and 26 claims were mapped to source evidence. Archived rankings were evaluated at K=3 and K=5, and the saved K=5 answers were scored with RAGAS.

The initial evaluation retained three partially scored records rather than replacing missing metrics with zero. This established that the harness worked and exposed further reference and evaluator problems.

Evidence: [initial T06 validation report](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/t06-validation-report-v1/T06_VALIDATION_REPORT.txt).

**6. October 19, 7:11 a.m. — Clean research checkpoint created**

Commit `633fbfd` created the clean Chapter 3 development and T06 evaluation snapshot.

It preserved the approved implementation and selected evidence while keeping the old project as a backup. The checkpoint recorded **41 passing tests across seven isolated test modules**.

This was a reproducible development checkpoint—not the final experimental freeze.

Evidence: [clean-branch validation](D:/thesis/LGSDeliveryRAGAssistant-clean/CLEAN_BRANCH_VALIDATION.json).

**7. October 19 — Remaining development references reviewed and consolidated**

The remaining **25 previously provisional groups** received source-review artifacts. Together with the five earlier corrections, all 30 development groups had review coverage.

The records include source passages, page references, claim mappings, before/after differences, and unresolved issues. Version 4 consolidated the references while preserving original generated answers, contexts, and rankings.

Important unresolved issues included CTO tax wording, OCBO mechanical-plan requirements, and some BFP context associations.

This was **source inspection and reference correction**, not independent expert certification. Changes in rescored retrieval metrics were identified as label changes, not improvements to the retriever.

Evidence: [source-review closeout](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/source-reference-review-remaining-batch-v1/READ_THIS_FIRST.txt), [V4 consolidation](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/t06-formal-development-validation-v4/READ_THIS_FIRST.txt).

**8. October 19 — Evaluator failures diagnosed and supplemental retries completed**

We inspected saved judge traces and addressed formatting/output-length failures through separately recorded evaluator retries.

For the reviewed single-system development batch, supplemental scoring eventually provided four finite metrics for all **84 answer-eligible records**. Six clarification outcomes remained excluded from answer scoring.

Original answers, references, contexts, failures, and score files were preserved. Supplemental values were explicitly distinguished from original results.

Later A/B/C faithfulness failures were also handled through documented supplemental retries.

**9. October 19 — Development grid and A/B/C comparison completed**

The historical grid evaluated **17 weight combinations at K=3 and K=5**, producing **34 conditions**.

Its selected development candidate was:

- BM25 weight: **0.75**
- Dense weight: **0.25**
- Dictionary retrieval-boost weight: **0**
- K: **3**

Near-tied objectives were documented; the selected candidate was not presented as meaningfully superior to numerical near-ties.

We then completed **270 development interactions**: the same 90 queries through each configuration.

| Configuration | Design | Development outcomes |
|---|---|---|
| A | Raw-query BM25 baseline | 90 answers |
| B | Dictionary-assisted normalization and hybrid retrieval | 83 answers, 6 clarifications, 1 incomplete generation |
| C | Query-specific dictionary injection disabled | 84 answers, 6 clarifications |

The consolidated **development-only** retrieval results were:

| Metric | A | B | C |
|---|---:|---:|---:|
| Hit@3 | 67.78% | 70.00% | 70.00% |
| MRR@3 | 0.4296 | 0.6167 | 0.6167 |

These are descriptive development results, not final test results or significance findings. Equal B/C aggregates also do not mean their per-query rankings were identical.

Evidence: [consolidated development metrics](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/t07-methodology-reconciliation-v1/master_metrics.csv).

**10. October 19, afternoon — Retrieval and normalization regressions investigated**

A BFP fee case showed that the required information existed in the corpus but ranked poorly. This distinguished a **retrieval-ranking problem** from missing source content.

We tested normalization revisions and punctuation-aware BM25 tokenization on development data.

The normalization revision was rejected for promotion because improvements in acronym retention did not translate into consistent retrieval improvements, and English-copy compliance worsened. Punctuation-aware retrieval showed promising diagnostics but was not adopted into the final candidate.

The review was recorded at approximately **5:32 p.m.**

Evidence: [normalization and sparse-retrieval review](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/normalization-sparse-development-regression-v1/REVIEW_RESULTS.txt).

**11. October 19, evening — Automated judge reliability investigated**

Further checks found that a judge could produce a valid-looking score while accepting an unsupported or irrelevant passage.

Several evaluator experiments were run and retained:

- A paired grid rescore attempted **1,560 unique query/context judgments**.
- **1,450** met its output/evidence contract.
- **110** remained invalid.
- None of its **68 conditions** had a complete objective suitable for selecting a winner.
- Structured-output and source-span evaluator candidates also failed their declared screening criteria and were not promoted.

A separate 60-item human usefulness-review packet was prepared. Its completion flag remains false. A later methodology reconciliation clarified that this was **optional evaluator auditing**, separate from the required three-expert answer-rating study.

Evidence: [paired-grid review](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/t07-paired-grid-results-review-v1/READ_THIS_FIRST.txt), [methodology reconciliation](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/t07-methodology-reconciliation-v1/READ_THIS_FIRST.txt).

**12. October 19 — T06 closed and expert-meeting materials prepared**

T06 was closed as **implementation complete with documented evaluator limitations**. Its closeout recorded 34 focused passing tests covering calculations, serialization, prompt contracts, adapters, and missing-score handling.

In parallel, we prepared:

- A mock rater handout.
- A separate facilitator guide.
- A five-page employee annotation meeting packet.

The planned expert audit remains **20 groups × 3 languages × 2 systems = 120 answers**, independently reviewed by three experts for **360 reviews**.

These materials support recruitment and orientation. They do not establish completed recruitment or formal ratings.

Evidence: [T06 closeout](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/t06-harness-closeout-v3/T06_STATUS.txt), [printable employee meeting packet](D:/thesis/LGSDeliveryRAGAssistant-clean/output/employee-annotation-meeting-v1/Davao_City_Employee_Annotation_Meeting_Packet.pdf).

**13. October 19, 8:55 p.m. — Final candidate registered before held-out preflight**

The historical development candidate was registered and sealed before structural inspection of the held-out benchmark.

Registration recorded the corpus, indices, dictionary, prompts, code, model identity, settings, K, weights, and evaluator protocol.

The final candidate retained the historical whitespace BM25 implementation and legacy evaluator. Punctuation and rejected evaluator candidates were not adopted. Known judge errors and the remaining static lexical guidance in C were disclosed.

Evidence: [candidate registration](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/t07-final-evaluation-v1/candidate_registration.json).

**14. October 19, approximately 8:56–9:06 p.m. — Held-out source-ID incompatibility addressed**

Preflight found that the benchmark used old `CHUNK-…` relevance IDs while the rebuilt corpus used `DEV120-…` IDs.

A separate source-span crosswalk was created without rewriting benchmark questions or reference answers:

- **77 of 87 legacy spans transferred**
- **59 of 70 groups** received complete transferred relevance labels
- **11 groups / 33 query variants** retained unresolved labels

All queries remain in generation. Hit/MRR for incompletely mapped groups remain **null**, rather than being counted as retrieval failures.

The crosswalk transfers source spans across changed chunk boundaries; it is not new expert validation of every relevance label. Its limitations are recorded.

At **9:06 p.m.**, the execution manifest registered this evaluation-policy addendum before model outcomes. The addendum followed structural test access, which must be disclosed.

Evidence: [final execution guide](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/t07-final-evaluation-v1/EXECUTION_GUIDE.txt).

**15. October 19, approximately 9:08 p.m. onward — Final held-out evaluation launched**

The queued workflow plans:

1. Generate A/B/C outcomes for all 210 held-out queries: **630 outcomes**.
2. Export retrieval metrics with label-coverage denominators.
3. Run offline RAGAS for A, B, and C.
4. Export final comparison files and an execution report.

At **9:13 p.m.**, 31 outcomes were archived: A=11, B=10, C=10. The workflow was still in generation. Existing final-run CSVs were partial.

Evidence: [live generation progress](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/t07-final-evaluation-v1/generation_progress.json).

**What needs to be disclosed to the adviser**

The project has substantial implementation and evaluation evidence, but it should not be described as perfectly matching every manuscript detail:

- The manuscript specifies a **0.1-step weight grid**; the executed historical grid used **0.25 steps plus two additional candidates**.
- The registered answer prompt does not fully implement the manuscript’s description of **two complete output examples**.
- The dictionary has **167 entries**, while the tracker describes 150.
- Final retrieval-label coverage is **59/70 groups**, with conditional denominators.
- Automated judge errors, unresolved source ambiguities, and C’s retained static lexical guidance remain limitations.

These differences should be reconciled with the adviser and documented accurately. They should not be silently corrected through tuning after inspecting held-out outcomes. References: [September 23 manuscript](D:/thesis/20260923.pdf), [executed grid protocol](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/t07-development-grid-format-retry-v2/protocol.json).

**Current task status for reporting**

| Task | Evidence-supported status |
|---|---|
| T01–T03: Dictionary, corpus, local inference | Implemented; version and methodology differences need reconciliation |
| T04: Rater coordination | Tracker says complete; commitments/approval not verified in this review |
| T05: Benchmark | Development and held-out partitions established; relevance-transfer gaps documented |
| T06: Evaluation harness | Complete with evaluator limitations |
| T07: Architecture comparison | Development complete; final held-out execution running |
| T08–T09: Audit packets and scoring preparation | Mock and meeting materials prepared; formal package/interface still pending |
| T10: Expert grading | No completed formal ratings verified |
| T11–T12: Agreement and significance | Pending formal data and finalized analysis procedure |
| T13 onward: Results chapters and submission | Tracker lists these as not started; completion not established here |

You can tell your adviser:

> “We have completed the prototype, source-linked corpus and indices, development-reference review, automated evaluation harness, and development comparison of the three architectures. We also investigated retrieval and automated-judge failures and preserved the limitations. The final candidate is registered, and the held-out A/B/C evaluation is now running. Expert orientation materials are ready, while formal expert grading and statistical analysis remain pending. We need to reconcile several implementation details with the manuscript and report incomplete relevance-label coverage transparently before presenting final conclusions.”

**The earlier completed three-configuration results were developmental—not held-out.**

The file you have open, [master_metrics.csv](D:/thesis/LGSDeliveryRAGAssistant-clean/experiments/t07-methodology-reconciliation-v1/master_metrics.csv), contains:

| | Earlier completed comparison | Final held-out comparison |
|---|---|---|
| Scenario groups | 30 development groups | 70 held-out groups |
| Queries per configuration | 90 | 210 |
| Total A/B/C outcomes | 270 | 630 planned |
| Location | `t07-methodology-reconciliation-v1` | `t07-final-evaluation-v1` |
| Last verified status | Complete | Running |

The earlier **Hit@3 results of 67.78% for A and 70.00% for B/C** are development results.

For your adviser: **“We completed the developmental comparison of the three configurations. The separate frozen held-out evaluation was subsequently launched.”**