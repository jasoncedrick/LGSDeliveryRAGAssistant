# Website regression review — 28 October 2026

**Do not promote this candidate to the live website.** Software checks pass, but observed unsupported claims and language failures remain. This branch preserves implementation work and its failed quality assessment. It does not certify all questions as correctly answered.

The original dry-run review is in `../website-dry-run-review-20261028/REVIEW.md`. The implementation and its methodology boundaries are described in `../../website/GROUNDING_REVISION.md`. Read `summary.json` for the completed run's counts and hashes and `case_statuses.csv` for all 200 dispositions. Raw outputs, normalizations, ranked chunks and exact generation contexts remain in the local QA archive; they are not public citizen logs.

## Completed checks

All 200 unique registered cases are present, without duplicate IDs or QA exceptions. The tested prompt and runtime hashes match the files in this branch. Thirty API/unit tests, 21 synthetic browser checks, 11 motion/accessibility checks and the static build passed. Thirteen registered runtime/artifact hashes and five source PDFs were preserved. The local archive is listed in `backup_receipt.json`.

| Disposition | Archived second run | Candidate |
| --- | ---: | ---: |
| ANSWERED (not an accuracy label) | 184 | 124 |
| Clarification required | 13 | 47 |
| No supported answer (coverage check) | 0 | 18 |
| Outside source scope | 0 | 7 |
| Capability limit | 0 | 4 |
| Generation incomplete | 3 | 0 |
| Total | 200 | 200 |

The candidate generated 124 answers and retrieved passages for 142 questions. Citation-format warnings fell from 16 to 4, and internal `DEV120`/`CHUNK` identifiers in answers fell from 34 to 0. These counts have different generation denominators and do not establish improved factual accuracy. All ten deliberately vague cases Q161–Q170 now request service details. Several substantive questions still receive unsupported answers or awkward/wrong-language text, so the quality gate remains failed.

## What changed

The website candidate adds localized intake/clarification, explicit dictionary-option selection, visible instructions to repeat service details for each question, and conservative checks for missing service/office evidence before generation. It also tests a shorter source-constrained generation prompt and removes internal chunk identifiers from the headers supplied to generation. The original selected passage text remains unchanged.

These are post-study website changes. The frozen thesis implementation/results, dictionary, corpus, indices, model, fusion weights, K=3 and 120/20 chunk construction were preserved. Pre-generation keyword checks are an operational addition, not a new thesis result or proof of factual support. No inline judge or regeneration chain was introduced.

## Concrete remaining failures

These are assistant-inspected counterexamples, not human rater scores or complete labels for the dataset.

| Case | Observed issue | Evidence and implication |
| --- | --- | --- |
| Q001 | English question receives Tagalog/Taglish despite `response_language: english`. | The answer begins “Kung iyong gusto mo…”; language-selection metadata does not establish output compliance. |
| Q003 | Generalizes a construction-stage fragment to a new-store application and invents an FSIC condition/sequence. | The selected BFP passages contain truncated matrix headings and a construction-related fragment. They do not establish the stated universal path for this question. |
| Q004 | Says a bakery is allowed simply because an area is commercial; classifies it as low hazard and prescribes extinguisher quantities. | S1/S2 are ownership/vehicle requirements; S3 lists low-hazard examples without identifying this bakery. None establishes the claimed zoning permission or the specific hazard classification. Labels include unprovided S16 and a mixed checklist number. |
| Q006 | Answers a first-time Business Bureau document question with awkward wording and unrelated treasury instructions. | It says “Lalaruan mo…” and directs the user to Counter 22 using a passage about a performance bond. The source is not a demonstrated document checklist for this request. |
| Q088 | Inspection question becomes business-renewal instructions. | Retrieved snippets cover renewal, blocked permits and tax termination, not whether this shop is subject to inspection. |
| Q134 | A modified fallback is recorded as ANSWERED. | The frozen status detector recognizes the exact fallback string; a paraphrased refusal is not a substantive answer just because the status says ANSWERED. |
| Q135 | Converts a request for a no-arrears certificate into a statement that no certificate is needed. | S3 is a truncated Real Property Tax Transfer Ownership with Certification checklist. It does not support this exemption. |
| Q136 | Answers a change-of-owner question with change-of-address and building-plan requirements. | Normalization preserves the owner-change request, but S1/S2 concern Change of Business Address and S3 concerns locational clearance. The answer combines these into a new procedure and invents “Special Permit Agreement” for SPA. |

The focused checks prevent the previously observed wrong-service answers for Q002, Q009, Q017, Q020, Q034, Q036, Q104 and Q133 by abstaining. That is a limited improvement in behavior, not successful retrieval or a correct substantive answer. The new scope checks do not cover every wording or test entailment. A passing keyword check can still lead to an unsupported answer.

## How to interpret the counts

- The input contains 200 distinct exploratory questions originally submitted twice. This candidate run evaluates those 200 once and reuses 13 focused records with identical input, prompt and runtime hashes.
- The baseline column comes from the second archived run. It is not a fresh baseline executed under a fully pinned matching environment.
- The candidate is tested directly through the pipeline. API/browser integration is tested separately with synthetic responses; this is not a 200-user load test.
- Statuses, citation-format checks, abstentions and execution times are operational observations. No overall factual accuracy, RAGAS improvement or thesis significance result is computed here.
- A question returning less text or an abstention is not automatically an improvement. Coverage and fluency still need evaluation.
- Source-label validity only checks labels. It does not mean the claim follows from that source. The additional unknown-label scan is also syntactic.

## Next engineering work

Use these saved traces to separate missing source context, normalization drift and generation overreach. For example, Q004 normalization retains the bakery/location request, but its top three passages do not answer permission for that location; the generator nevertheless supplies a permission and hazard classification. Q001 has adequate evidence for a narrow business-permit statement but violates the selected language.

The next candidate should address general behavior across languages and services, rather than hard-code answers to these examples. Preserve these failures as regression cases. Any retrieval/source-context change needs a separately versioned development experiment under the manuscript's chunk-level constraints. Do not modify the frozen results or describe website improvements as gains in the already completed study. No duplicate expert-rating assignment is needed to confirm the counterexamples above.

The live deployment remains on its earlier branch. This candidate has not been deployed, and the PC API has not been restarted onto it. Do not restart the backend from this review branch as if it were a promoted release.
