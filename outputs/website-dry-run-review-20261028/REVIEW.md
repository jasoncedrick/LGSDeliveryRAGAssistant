# Citizen website dry-run review - 28 October 2026

The archive is useful and internally consistent. It demonstrates working delivery and repeatable outputs, but it also contains serious answer-grounding defects. Do not describe the repeat run as 100% accurate or as evidence that citizen advice is ready for unrestricted reliance.

This is an assistant's post-study diagnostic review, not an independent employee audit, formal correctness annotation, RAGAS run, or replacement for T06/T07. No application code, prompts, dictionary, corpus, indices, frozen results, or human ratings were changed. No model calls or rerun of these questions were made during this inspection. The original ZIP remains unchanged.

## What was actually tested

- 200 distinct question IDs, each submitted twice: 400 sequential browser submissions.
- 150 office-specific questions (30 each for business, building, fire, planning and treasury), 10 mixed-service, 10 ambiguous, 10 outside-scope, and 20 conversational turns.
- Authored language labels: 67 English, 64 Taglish, 64 Bislish, five mixed. These are test-author labels, not verified linguistic annotations.
- Four five-turn conversations retained visible chat history. The archived request payload still sends only the current question and response-language preference.
- Both runs used the temporary Cloudflare address, not a controlled concurrency test of the later Vercel queue release.
- Run 1: 28 October, approximately 12:11-13:16 Asia/Manila; run 2: approximately 13:16-14:20. These precede the evening queue update.

## Independently recomputed results

| Observation | First run | Repeat |
| --- | ---: | ---: |
| Recorded submissions | 200 | 200 |
| HTTP 200 | 197 | 200 |
| Request failures | 3 | 0 |
| ANSWERED status | 181 | 184 |
| CLARIFICATION_REQUIRED | 13 | 13 |
| GENERATION_INCOMPLETE | 3 | 3 |
| Citation-label warnings | 16 | 16 |
| Answers exposing DEV120/CHUNK identifiers | 32 | 34 |
| Mean elapsed seconds | 18.36 | 18.43 |
| Median elapsed seconds | 18.36 | 18.22 |
| 95th percentile, nearest-rank, seconds | 25.49 | 24.20 |
| Maximum elapsed seconds | 50.50 | 49.71 |

Elapsed times include fast clarifications and failed attempts; they are not generation-only latency or multi-user queue latency. ANSWERED is an application disposition, not an accuracy label. Warnings and exposed identifiers can overlap and must not be added into an error rate.

Q092 and Q093 received HTTP 502, and Q094 received HTTP 503, during the first run. All three returned answers in the repeat. Among the other 197 paired HTTP-200 cases, answer text and returned citation arrays are identical. Repeating the run recovered availability for three cases; it did not fix the repeated semantic mistakes. This is observed repeatability, not proof that future inference is deterministic.

All 455 files listed in manifest-sha256.json matched their recorded lengths and SHA256 hashes. START-HERE.txt and the manifest itself are not listed in that manifest. Both JSON result arrays exactly match their JSONL records. Both runs contain 200 screenshots. All five first-run included PDFs match the current registered source PDF hashes. This verifies internal consistency, not independent authenticity of the test execution. The test's own UI report records 20 mobile checks per run with no overflow and no browser page errors; those are archived observations, not fresh browser checks by this review.

## Findings that matter first

1. **Unsupported exemptions and invented conditions.** Q036 says a home-based online seller needs no mayoral permit, but its three retrieved CPDO checklist passages establish no such exemption. Q133 ties fire-clearance need to whether an extinguisher exists; its cited passages concern maintenance and matrix headings. The rendered BFP charter separately lists hot-work clearance, explicitly conditional on being required. This review does not convert that into a universal requirement. The model must not invent an exemption or condition from incomplete evidence.
2. **Wrong office/service evidence.** Q104 explicitly names CPDO but answers five sets from OCBO. Rendered CPDO PDF pages 11 and 19 both state seven complete sets in the building locational-clearance checklist. Q017 confuses signing building plans with sign/billboard and demolition permits. Q173 gives City Treasurer book/receipt registration steps for SSS registration; none of its three passages supports that substitution.
3. **A correct condition can be present and still be lost.** In Q002, returned S2 already says the City Administrator signs for a housing project under the City. The answer broadens that to any non-NHA land. A retrieval-only repair cannot by itself fix this example.
4. **Missing retrieval becomes an unsupported claim of absence.** Q034 says there is no neighbors-consent mention for locational clearance; CPDO business-clearance PDF66 includes that undertaking. Q020 says no document is needed, while CTO PDF47 lists a tax-declaration photocopy for the unemployed/no-business row. Applicability still needs the user's correct service and circumstances.
5. **Clarification is inconsistent.** All ten test-authored ambiguous cases return ANSWERED. For example, Q162, “Ano requirements po?”, gets fire-extinguisher requirements; Q168's unspecified renewal becomes an employment-agency service. Conversely, several explicit personal questions trigger an individual/corporate or home-business/residential clarification. The current implementation's ambiguity branch is triggered by dictionary polysemy; it is not a general detector of every missing service detail. The branch returns the dictionary's literal clarification before answer-language generation. All 13 saved clarification prompts are English.
6. **Visible conversation is not conversational memory.** Q182 and Q183 lose the earlier coffee-shop context because that history is not in the payload. Making memory implicit would be a new inference design, not a cosmetic UI fix. A methodology-preserving immediate UX direction is to require a complete question, or explicitly ask which service a short follow-up refers to.
7. **Language quality and answer presentation remain weak.** Q133 and Q169 contain conspicuously repetitive/awkward Bislish; Q134 invents the expansion of UEESZ instead of the source's Urban Ecological Enhancement Sub-Zone. Internal chunk identifiers appear in 34 repeat answers, and Q067/Q071/Q083 are incomplete in both runs. A citation label matching a source does not prove the attached claim is supported.
8. **Capabilities need clear boundaries.** Q179 answers yes to sending permit payment “here” and directs the user to a special-permit portal without establishing the permit type. This chat cannot accept payment. Scope-limited responses must distinguish an external official process from an action this website can perform.

The targeted case list in priority_cases.csv distinguishes rendered-page verification, returned-passage inspection and output-only findings. It is not an exhaustive list of all errors in the 200 questions. Unlisted cases have not been certified correct.

## Test data and interpretation cautions

Ten records have a disagreement between the authored language label and the response_language field, but these are not ten proven language failures. Q178 asks “Can you approve my business permit here?” in English while the manifest labels it Taglish. Q059 is also code-mixed in a way that needs linguistic judgment. The response_language field is a selected generation-language setting, not an independent measurement of the language actually produced. Neither that field nor HTTP 200 establishes fluency or correctness.

Run 1 spans two observed frontend-script hashes and an outage. The tester did not pin or inspect the backend revision/model configuration. Do not present this as a controlled A/B experiment, a before/after model improvement, or a 400-independent-question benchmark. The corpus PDF hashes do not establish the complete backend configuration. The archive also does not certify separation from the thesis held-out set.

The public response export contains the question, answer and three citations, but not the normalized query, injected terms, score components, or full ranking. Wrong-service retrieval is directly observable; whether normalization or ranking caused it is not established. Do not blame the dictionary, table repair or BM25 weight without tracing that stage. No Hit@K, MRR, answer-accuracy percentage or new RAGAS score can be honestly calculated from these records alone.

## Recommended next work

1. Preserve this archive as post-study website diagnostic evidence. Keep T06/T07, human ratings and the registered source/corpus/settings untouched.
2. Prioritize Q036, Q133 and Q179 for unsupported-claim/capability handling, then Q104, Q017, Q002 and the vague-query cases. Preserve original questions and answers as regression examples; do not edit old outputs to make them pass.
3. Before revising retrieval, capture normalized query, dictionary triggers and selected chunk scores in a private, explicitly enabled diagnostic path for synthetic tests. The archive is insufficient to attribute every service mismatch to a specific stage.
4. Implement any clarification/generation change as a separately versioned post-study candidate, grounded in Chapter 3 and compared against the current website across a fixed development regression set. Preserve 120/20, chunk-level scoring and K=3 or K=5. Do not add a live judge/rewrite loop or re-open held-out tuning.
5. Check source-supported claim behavior and native-language readability separately. No immediate manual action is needed to establish the concrete defects listed here. A formal all-question accuracy rate would require full claim-level annotation; fluent Bisaya review is needed before declaring the wording acceptable.

The current queue solves admission and waiting behavior. It cannot repair wrong-service evidence, invented requirements, missing context, or weak Bislish. Answer grounding should be the next development priority, rather than another unchanged 200-question rerun.

## Files in this review

- verified_metrics.json: reproducible counts, archive hash, integrity checks, language-label discrepancies and limitations.
- case_index.csv: all 200 paired records with operational flags; cases without targeted review are explicitly unscored.
- priority_cases.csv: 15 targeted findings/data issues and the specific verification scope.
- Original archive remains at the user-supplied path recorded in verified_metrics.json. It contains the HTML comparison report, raw outputs, source PDFs and screenshots.

## Source page checks

PDF page numbers below are file-relative, not printed page numbers. Reviewed original project PDFs are byte-identical to the corresponding archived references.

- [OCBO PDF](../../data/raw_charters/OCBD%20Pages%20from%20CGD_Citizen%20Charter%202026_VOL.I%20%26%20II-2.pdf): PDF6 visually inspected; PDF2 text inspected.
- [CPDO PDF](../../data/raw_charters/City%20Planning%20CGD_Citizen%20Charter%202026_VOL.I%20%26%20II-3.pdf): PDF11,19,46,66 visually inspected.
- [CTO PDF](../../data/raw_charters/City%20Treasurer%27s%20CGD_Citizen%20Charter%202026_VOL.I%20%26%20II-2.pdf): PDF47 visually inspected.
- [BFP PDF](../../data/raw_charters/BFP-CITIZENS-CHARTER-2022.pdf): PDF1 full-page layout and hot-work region inspected; the three Q133 retrieved snippets checked separately.

The archive's 18 first-run and three repeat-run source notes are useful pointers. Only the targeted checks described here were independently confirmed in this inspection; no blanket endorsement of all 21 notes or all 200 answers is made.
