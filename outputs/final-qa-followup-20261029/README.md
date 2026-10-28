# Paper and final QA follow-up

Date: 29 October 2026. Continues the `handoff/human-results-chapters45-20261029` branch after commit `81f7a21`.

Start with [paper consistency review](PAPER_QA.md), then [fresh software/archive QA](software_archive_report.json) and [saved-answer diagnostics](archive_review.json). The previous [15-page Chapters 4-5 draft](../team-handoff-20261029/CHAPTERS_4_5_REVIEW.pdf) and all its numbers remain unchanged. The follow-up verifies them and supplies a deployment-methodology integration paragraph; it does not manufacture a new experimental result.

## Fixed and tested

- Coverage checks now retain every explicitly requested topic. Previously a later topic could replace the earlier topic's evidence when checking a sequence or checklist. Synthetic tests cover both query orders. This is a coverage predicate correction, not a source-entailment classifier or retriever change.
- Startup logs identify the loaded prompt version instead of always saying v2.
- The exploratory runner rejects duplicate/unknown records, changed queries or baselines, partial JSONL appends and incompatible candidate manifests. It verifies the model digest and registered artifacts, preserves exceptions, and resumes a completed archive without loading a model. A run with QA exceptions exits unsuccessfully rather than announcing a clean completion.
- Browser checks can write to a new output folder. Static-build QA can use an isolated directory under ignored `tmp/`, preserving the production build directory.
- Website documentation now describes the purchased domain, Vercel frontend and PC/tunnel backend accurately.

The final offline command runs real checks and records their current exit codes, test counts, source hashes and logs. It does not regenerate a previous QA report using hardcoded passing counts. The temporary QA server binds to loopback with model initialization disabled; it is stopped afterward. The existing public backend is not restarted.

## Saved-answer review

The 200 archived exploratory records match the original saved-results hash. Screening flags identify 22 refusal-like replies recorded as ANSWERED, three outputs containing unknown citation labels, two without a valid bracketed citation, and ten with possible language mismatch. Flags may overlap and are not validated correctness labels. No archived status or answer is rewritten.

Replaying the corrected topic predicate on the saved retrieved passages changes no disposition in this archive. The correction is supported by a new synthetic multi-topic regression; it cannot be claimed as an observed improvement on these 200 cases. The previously inspected unsupported claims and language problems remain unresolved. No new generation or judge run is warranted merely to repeat unchanged answers.

**The answer-quality gate remains NOT PASSED. Do not promote this review branch to production based on software tests.** Current citation, refusal and language diagnostics will help assess a future candidate, but they cannot establish that a cited claim follows from a source.

## Visible CLI

From the clean project, run the offline suite. It creates a new timestamped folder automatically, prints each stage, and returns a nonzero exit code if a check fails. This command needs the local private audit artifacts for archive/collector verification; a public clone alone does not include them.

```powershell
Set-Location D:\thesis\LGSDeliveryRAGAssistant-clean
D:\thesis\venv\Scripts\python.exe -u scripts/run_final_offline_qa.py
```

For a future changed model/prompt candidate, use the exploratory runner with a NEW output directory. It evaluates the supplied exploratory archive, not the thesis held-out benchmark. Preserve the completed v4 run. This is a command for a future engineering evaluation, not a currently running job:

```powershell
D:\thesis\venv\Scripts\python.exe -u scripts/run_website_grounding_qa.py --archive "C:\Users\User\.codex\.chatgpt-projects\g-p-6ac6a06fa534819186f2a4eae6c3c4e6\output\eboss-400-question-test-20261028.zip" --output tmp/website-next-candidate
```

The full model run can contend with citizen requests because it uses the PC model. The offline QA suite above makes no model calls. Finishing either execution does not certify factual quality or trigger deployment.

## Preservation

The frozen pipeline, dictionary, normalization prompt, 120/20 corpus and paired indices, K=3/weights, model settings, original ratings, previous chapters and original QA reports remain unchanged. This follow-up introduces no section retrieval, live LLM judge, regeneration chain, held-out retuning or new human-rating assignment. Original and versioned tracker workbooks remain unchanged. Adviser approval and official-template integration remain separate pending tasks.
