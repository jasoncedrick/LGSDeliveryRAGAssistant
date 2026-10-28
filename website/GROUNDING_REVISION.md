# Website grounding candidate - 28 October 2026

Status: 200-case execution and software QA complete; answer-quality gate FAILED. This branch is not the production branch and was not deployed. Read GROUNDING_QA.json and outputs/website-grounding-qa-20261028/READ_THIS_FIRST.md. Passing software tests is not a factual-quality certification.

## References and preservation

The reference is D:/thesis/20260923.pdf, SHA256 628193ea55abc364c06dd3251a79126fa55ca2af2cb9d23e25cb584e7757f98a. Chapter 3 PDF25 describes grounded generation and offline evaluation, PDF29 describes dictionary ambiguity clarification, PDF30 describes chunk-level fusion, and PDF31 describes source-constrained generation, language matching and FastAPI. The selected tracker remains the Downloads workbook, Thesis Tracker tab, SHA256 74ae6a572885e54be360b13bd548e078e59c1a72d66c9180b52acbabcf6bf2ed. Its T06/T07 items concern the original harness and frozen A/B/C execution; this post-study website candidate is not a replacement result or a new completion claim for those tasks.

The original website release is preserved at commit 9d6b354. The frozen app/pipeline.py, src normalizer/retriever, dictionary, corpus, indices, model, weights 0.75/0.25/0, K=3 and 120-token/20-overlap construction are unchanged. Generation remains one Mistral call, temperature/top_p zero, 1536 maximum answer tokens and context 8192. Normalization remains capped at 150. No inline LLM judge, regeneration loop, section retrieval, appended source context or held-out benchmark tuning is introduced.

## Changes

- app/website_intake.py adds deterministic website intake messages for missing service information, unsupported product capabilities and selected outside-scope subjects. These are localized UI messages, not source-derived legal answers. This is an operational addition, distinct from the manuscript's dictionary-polysemy ambiguity test. Keyword coverage is incomplete and can over-clarify; it is not a validated intent classifier.
- app/website_normalizer.py allows a user to explicitly select exactly one of the existing dictionary's options by including it in the new full question. Only a per-request dictionary copy is changed. The original dictionary and translation prompt remain byte-preserved. No sense is inferred from previous chat or from a vague personal context. Multiple selected options remain ambiguous.
- Clarification option labels retain their original English technical wording; introductions/instructions match the chosen language. The browser offers buttons that fill the complete original question plus the selected option, requiring a new submission. A visible composer note says every question needs its service details. No conversational memory has been added.
- app/website_scope.py checks for explicitly named offices/topics and limited requested evidence types in the selected passages BEFORE generation. It neither changes ranking nor verifies a generated answer. Missing coverage returns the existing exact fallback. A matching keyword is only a necessary check, never proof of entailment. Relevant chunks lacking headings can be rejected, reducing answer coverage. This conservative pre-generation rule is a documented post-study addition, not the frozen T07 algorithm and not a RAGAS score.
- config/website_response_language_v4.json is a candidate generation prompt with compact answers, explicit condition/exemption instructions and two format examples. The original pipeline generator's request/settings/budget/error handling is reused without editing its source. A prior unsuccessful v3 prompt is retained. The candidate removes internal chunk IDs from generation headers, while retaining citation labels, source identity, page provenance and the EXACT selected passage text. Full internal IDs remain in private diagnostic records.
- The auto-language heuristic recognizes more explicit Cebuano and Tagalog clues. It remains a heuristic. A response_language label denotes the selection, not proof the model followed it or that the result is fluent. Citizen overrides remain available.

## QA and privacy

The synthetic suite covers ordinary API validation, source hashes, CORS, per-user queue isolation, language isolation, intake, source-scope checks, literal option preservation, actual dictionary option selection, no extra generation calls, and unchanged generator settings. Browser checks cover choice buttons, visible independent-question guidance, queue progress and retry behavior, mobile layout, source links and XSS-safe text rendering. Existing motion/accessibility checks remain applicable.

scripts/run_website_grounding_qa.py evaluates only the user-provided exploratory 200-question archive. It does not read thesis benchmark files. It archives normalized queries, injected terms, selected chunks/scores, exact generation context, raw outputs and elapsed time under ignored tmp/. These traces are obtained through an offline synthetic runner, not by turning on citizen logging. The public response still excludes internal diagnostics. No RAGAS judge is launched by this script.

The runner is resumable and refuses reuse across different input/prompt/runtime hashes. The final run reuses 13 already-completed cases only after matching those hashes. Raw results are not public accuracy labels; failures and abstentions stay in the archive. The original 400-submission archive is untouched. Its questions were authored for exploratory testing, and held-out membership is not certified; do not reuse this candidate as a claim about original held-out effectiveness.

For candidate identity, use the recorded prompt/runtime hashes and `website_prompt_version` in the result/profile. The legacy readiness log in app/website.py still says prompt v2; that static log label is stale for this candidate and is not provenance evidence. The direct regression runner records the actual v4 prompt hash.

CLI example (from the project root; the output must be under tmp):

```powershell
D:\thesis\venv\Scripts\python.exe -u scripts/run_website_grounding_qa.py --archive "C:\Users\User\.codex\.chatgpt-projects\g-p-6ac6a06fa534819186f2a4eae6c3c4e6\output\eboss-400-question-test-20261028.zip" --output tmp/grounding-v4-full --reuse tmp/grounding-v4-scope-focused
Get-Content tmp/grounding-v4-full/progress.log -Wait
```

Do not rerun completed cases merely to get a more favorable answer. For a different candidate, retain earlier traces and use a new output folder. The website backend and this offline runner do not coordinate their model locks across processes; run large regressions during a quiet maintenance period. The public site can be slower while the same PC model is being tested.

## Promotion rule

Do not deploy a candidate solely because HTTP responses, source links or software tests pass. The focused v3 candidate failed semantic review and was not promoted. The completed v4 run exposed unsupported answers and language regressions: 124 ANSWERED dispositions, 47 clarifications, 18 coverage abstentions, seven outside-scope replies and four capability-limit replies. These are operational outcomes, not correctness scores. A push preserves reviewable work; it is not an approval to describe all findings as fixed. No requests for duplicate human thesis ratings are needed to establish these observed failures.
