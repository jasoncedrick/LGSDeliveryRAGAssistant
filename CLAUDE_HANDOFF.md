# LGSDeliveryRAGAssistant: Claude Code handoff

> **Latest reference-display preference - 29 October 2026:** Citizen answers now show only quiet citation markers and a short source-name line (for example, Bureau of Fire Protection). No PDF buttons, page numbers, raw filenames or passage quotations appear below answers. The source library and full API/archive provenance remain available. This supersedes the earlier instruction to retain PDF/page links under answers; frozen research data and ratings are unchanged.

> **Paper / QA follow-up - 29 October 2026:** Read `outputs/final-qa-followup-20261029/README.md` and `PAPER_QA.md`. The current Chapters 4-5 draft and all scores remain unchanged and rechecked. Topic checks now retain each requested service; startup logs use the actual prompt version. The regression runner validates archives/resume records and never reloads a model for a completed run. `scripts/run_final_offline_qa.py` creates fresh logs and an isolated model-free server/build; 43 tests, 22 browser checks and 11 motion checks passed. Saved-output diagnostics identify refusal/status, citation and language issues without changing the 200 archived answers. No new generation, judge run, public-backend restart or deployment occurred. Factual answer quality remains NOT PASSED. Pushing is secondary to paper/code QA; keep frozen research and private collection artifacts preserved.

> **Team handoff - 29 October 2026:** Read `TEAM_START_HERE.md` first. Branch `handoff/human-results-chapters45-20261029` includes reverified human expert results and revised Chapters 4-5 in `outputs/team-handoff-20261029/`. All 780 records / 1,320 scores and aggregate calculations were reproduced exactly without score edits. The 15-page PDF adds human score distributions and language-specific discussion. Citizen source-passage quotations were removed from the display while reference/PDF links remain; expert packets and archived passages are unchanged. The inherited grounding candidate still fails answer-quality QA and was not deployed. Do not restart model evaluation or request duplicate expert ratings. Original drafts, private inputs and frozen outputs remain preserved.

> **Website grounding review branch - 28 October 2026:** `website/grounding-revision-20261028` contains the dry-run review and an unpromoted post-study website candidate. Read `outputs/website-grounding-qa-20261028/READ_THIS_FIRST.md`, its completed `summary.json`, and `website/GROUNDING_REVISION.md`. Software checks pass, but observed unsupported answers and output-language failures mean the answer-quality gate FAILED. Do not deploy or restart the PC backend onto this candidate merely because it was pushed. The original 200-question/two-run archive and new raw diagnostics are preserved locally; frozen T06/T07 inputs/results remain unchanged. This notice supersedes any inference that all website grounding problems have been repaired.

> **Citizen request queue - 28 October 2026:** The website now submits asynchronous jobs with private polling tickets and visible waiting position. Capacity is 11 outstanding questions, processed serially by the same registered pipeline. Read `website/VERCEL_DEPLOYMENT.md` and `website/QUEUE_QA.json`. Run only one backend process; queue/results are temporary memory and disappear on restart. No frozen inference settings or study artifacts were changed.

> **Vercel deployment branch - 28 October 2026:** `deploy/vercel-davaoragcitizencharter-20261028` is live at https://davaoragcitizencharter.com (www redirects). Read `website/VERCEL_DEPLOYMENT.md` and `website/VERCEL_QA.json` for current deployment status. Frontend and five source PDFs are static; AI remains on the PC through its tunnel. Preserve frozen results and private-file exclusions.

> **Website presentation update - 28 October 2026:** GSAP/Lenis assets are pinned locally under `website/vendor/`; React Bits reveal/edge-accent ideas are adapted for the buildless site. Read `website/THIRD_PARTY.md`. Larger text/touch controls, mobile form-first ordering, motion toggle, and OS reduced-motion support are implemented. These are presentation-only changes; no new inference/evaluation run or methodology change.

> **Citizen website - 28 October 2026:** The research/writing checkpoint was pushed to GitHub main as `020a5c0`. Website development is on `website/citizen-assistant-20261028`. Read `website/README.md` and `website/QA_REPORT.json`; run the new `app.website` entry point. It uses registered B retrieval/normalization and a separate post-study response-language prompt; read `website/LANGUAGE_REVISION.md`. The 29 registered source/input hashes remain preserved. Frozen T07 scores do not validate this new website prompt. The current temporary HTTPS address and process records are under ignored `tmp/citizen-website/`. The PC, Ollama, Uvicorn and tunnel must stay running. At that earlier checkpoint, always-on hosting and a purchased domain were not provisioned; the later Vercel deployment notice above supersedes domain status. The real smoke answer mixed services: connectivity passed, answer quality was not certified. Do not retune frozen experiments to fix the demonstration question. Editable manuscript/template integration remains deferred as instructed.

> **Current status - 28 October 2026:** T10-T12 analysis is complete on researcher-confirmed independent-score provenance; no significant paired system differences after Holm correction. T13-T14 writing drafts are now complete for review in `outputs/manuscript-closeout-20261028/THESIS_RESULTS_REVIEW.pdf`. Read that folder's `READ_THIS_FIRST.md` and latest `thesis_progress_tracker_updated.xlsx`. T15 replacement text is prepared. The researcher explicitly deferred editable Chapters 1-3 integration and the department LaTeX template; do not ask repeatedly or mark T15/T16 complete. T17/T18 approval/submission remain external pending tasks. Earlier status paragraphs below are historical.


Prepared on **2026-10-22, Asia/Manila**. This is a continuation brief for the researcher's local project, not a verbatim conversation transcript. Read the actual referenced artifacts before making changes. The files, source PDFs, archived runs, and private audit records remain necessary; this Markdown does not embed or replace them.

## 1. Start here

The research project has progressed from dictionary/source extraction repair through development evaluation, frozen final A/B/C execution, and construction of an offline employee audit interface.

**Current work is T08/T09 handoff and preparation for T10 human auditing. Do not restart T06/T07 or launch another expensive model/judge run merely to resume this project.**

| Task | Current evidence-based status |
| --- | --- |
| T06: automated Hit/MRR/RAGAS harness | Implementation complete, with documented evaluator limitations. |
| T07: execute three architectures and export metrics | All 630 final outcomes archived and scoring attempts complete; some metrics remain missing. Completion is execution/export, not certification of every judgment or reference. |
| T08: blinded randomized A/B audit packets | Constructed and tested; post-T07 sample-selection timing is explicitly disclosed. |
| T09: scoring interface and four-point rubric | Implemented and tested, offline browser interface. |
| T10: three independent employee audits | No actual human ratings in the designated collection folder at this handoff. |
| T11: inter-rater reliability | Requires real T10 ratings. |
| T12: statistical comparison | Analysis plan and actual data required; do not promise significant results. |

Recommended first reads, in order:

1. `experiments/t08-t09-expert-audit-v1/READ_THIS_FIRST.txt`
2. `experiments/t08-t09-expert-audit-v1/FACILITATOR_PROTOCOL.txt`
3. `experiments/t08-t09-expert-audit-v1/QA_REPORT.json`
4. `experiments/t07-final-evaluation-v1/completion_assessment.json`
5. `experiments/t07-final-evaluation-v1/T07_EXECUTION_REPORT.txt`
6. `experiments/t07-final-evaluation-v1/candidate_registration.json` and `execution_manifest.json`
7. Authoritative manuscript and tracker below, particularly the parts relevant to the next proposed change.

**Status precedence:** the latest final evaluation artifacts supersede historical pending/running paragraphs. `t06-harness-closeout-v3/T06_STATUS.txt` contains old statements that T07 is still pending and nothing is frozen; those are historical, not the current state. Even `t07-final-evaluation-v1/READ_THIS_FIRST.txt` retains older preflight/running text beneath its latest completion notice. Likewise, some fields in `t06-t07-current-status/status.json` describe older experiments. Do not revive old blockers without checking the latest final assessment.

## 2. Workspace, Git, and transfer requirements

- Active project: **`D:\thesis\LGSDeliveryRAGAssistant-clean`**.
- Shell: Windows PowerShell.
- Python environment: **`D:\thesis\venv\Scripts\python.exe`**.
- Current local branch: **`main`**.
- Latest local commit: **`b99f87d`**, `Merge completed T06/T07 implementation and evaluation into main`.
- Remote: `https://github.com/jasoncedrick/LGSDeliveryRAGAssistant.git`.
- The T06/T07 merge was pushed successfully earlier. This handoff checked local state; it did not perform a fresh remote fetch.
- Old project: `D:\thesis\LGSDeliveryRAGAssistant-main`. Preserve it: certain sealed provenance inputs still point there.
- Integration worktree: `D:\thesis\LGSDeliveryRAGAssistant-main-integration-20261020`. It is not the active editing location.
- Local backups: `D:\thesis\conversation-backups`.

The clean snapshot had separate Git ancestry. Publication used a normal merge preserving old remote history, not a force push. The clean source commit was `d992537`; the merge retained old-main-only compatibility files. Do not assume every old file now present in main belongs to the active methodology.

### Uncommitted state at handoff

Before this handoff file was added, `git status --short` showed:

```text
 M .gitignore
?? audit_ui/
?? experiments/t08-t09-expert-audit-v1/
?? scripts/collect_expert_ratings.py
?? scripts/prepare_expert_audit.py
?? scripts/test_expert_audit_browser.cjs
?? tests/test_expert_audit.py
```

`CLAUDE_HANDOFF.md` is also new. **A fresh GitHub clone alone will not contain these uncommitted additions.** Open Claude Code in this existing local project, or transfer the entire current working project plus the required external references and private backups.

Two intentional Git exclusions were added:

```gitignore
experiments/t08-t09-expert-audit-v1/private/
experiments/t08-t09-expert-audit-v1/received-ratings/
```

`tmp/` is also ignored. Do not force-add private audit keys or real rater returns into a public commit. Preserve them separately when moving machines. Browser autosave is not a project file: any real browser-entered ratings must first be exported using Download backup.

Private backup:

```text
D:\thesis\conversation-backups\t08-t09-private-20261020-055324.zip
SHA256: 0e2d0d6c09012d1f902d8042bc3e88079740de2ffd00c6e91ebfa3204037e975
```

This contains the registered sample, answer key, original selected records, build provenance and release manifest. It is for the researcher/data custodian, not auditors.

## 3. Authoritative references and working preferences

The user's explicit project instruction is:

> always ground to the references before doing any changes to avoid violation of methodology.

Authoritative documents:

| Reference | Location / rule |
| --- | --- |
| Manuscript | `D:\thesis\20260923.pdf` |
| Manuscript SHA256 | `628193ea55abc364c06dd3251a79126fa55ca2af2cb9d23e25cb584e7757f98a` |
| Tracker | `C:\Users\User\Downloads\thesis_progress_tracker.xlsx` |
| Authoritative tracker tab | **Thesis Tracker**, explicitly selected by the user; not `Sheet1`. |
| Tracker recorded SHA256 | `74ae6a572885e54be360b13bd548e078e59c1a72d66c9180b52acbabcf6bf2ed` |
| Earlier reference extraction | `experiments/t06-formal-development-validation-v4/methodology_and_tracker.json` |
| Audit reference snapshot | `experiments/t08-t09-expert-audit-v1/methodology_snapshot.json` |

There is also a workbook at `D:\thesis\thesis_progress_tracker.xlsx`; do not assume it is byte-identical to the selected Downloads copy. Verify version/hash if switching paths. Tracker cells were not updated during T08/T09 construction. Historical workbook status labels are not proof of experimental completion.

Relevant manuscript PDF pages (PDF page numbers, not necessarily printed numbers):

- 24–25: conceptual framework, dictionary-assisted normalization, hybrid retrieval, grounded generation, offline evaluation.
- 28: source extraction/OCR and table verification; 120-token chunks, 20-token overlap.
- 29–31: normalization, ambiguity handling, chunk-level retrieval, generation/settings.
- 32–34: development tuning, A/B/C comparison, freezing and held-out separation.
- **35 / printed 30:** expert audit design and Table 2 four-point rubric.
- **36 / printed 31:** Krippendorff's alpha and environment/reproducibility.

User preferences established through the work:

- Proceed with authorized necessary work rather than repeatedly asking permission.
- Explain changes step by step and say exactly what genuinely needs manual checking.
- Provide CLI commands/progress for long jobs; don't silently launch another long run.
- Avoid repeated review templates for already reviewed issues and shifting completion criteria.
- Do not require reviewer names; anonymous rater codes are used.
- Preserve backups, original artifacts, old traces, and exact before/after evidence for source/dictionary repairs.
- Do not publish, email employees, change access permissions, or push unrelated changes just because this handoff exists. The current user request was to create this transfer document.

## 4. Methodology boundaries to preserve

1. Actual-token **120-token windows with 20-token overlap**. Do not switch to section retrieval or revive abandoned section-retrieval pilots.
2. Score at **chunk level**, using the registered BM25, FAISS and dictionary fusion procedure. Permitted studied cutoffs are **K=3 or K=5**; the final selected candidate uses K=3.
3. Preserve source wording, numbers, units, row relationships, conditions, blanks and page provenance. Verify source/table edits against rendered PDFs, not just flattened text.
4. Dictionary-assisted normalization must preserve intent, service, actor/direction and explicit qualifiers. Ambiguity clarification is distinct from low retrieval coverage or unsupported answer content.
5. Generation is grounded in retrieved context; RAGAS is **offline evaluation**, not a live judge/repair/regenerate chain.
6. The final generator remains the registered Mistral model. Qwen was discussed but was not adopted.
7. Development tuning and held-out evaluation must remain separate. The held-out results are now known: do not tune on them, change their references silently, or regenerate favorable answers for audit.
8. Null judge outputs, missing labels, clarification and incomplete generation are preserved and reported; they are not automatically zeros or successes.
9. Frozen files are identified by registered hashes, not by a file/folder name alone. Do not alter them casually for UI or audit work.
10. Do not claim statistical significance, perfect judge accuracy, universal source certification, or full dictionary benefit from the descriptive results.

## 5. Final T07 configuration and results

Source of truth: `experiments/t07-final-evaluation-v1/candidate_registration.json` and `execution_manifest.json`.

- Selected historical completed development grid candidate: weights **BM25 .75 / dense .25 / dictionary boost 0**, **K=3**.
- Existing whitespace BM25 tokenization; later punctuation candidates were not adopted.
- **A:** original query, BM25 retrieval, same generator/prompt.
- **B:** query-specific dictionary injection, normalization, hybrid retrieval.
- **C:** same as B with query-specific injection disabled. Static lexical prompt guidance remains, which limits the ablation's interpretation.
- Zero dictionary retrieval weight does not mean pre-translation dictionary injection is absent.
- Generator/model registration: `eboss-mistral`, served in the final run as local `eboss-mistral:latest`; Mistral 7B family, not an independent judge family.
- Model digest: `39d9f435aeed825a340db73dfba9e7ce346664aa00727c9066bb1f0352406a6f`.
- Generation: temperature 0, top_p 0, context 8192, max prediction 1536.
- Normalization: max prediction 150, temperature 0, top_p 0.
- Evaluator: registered legacy RAGAS 0.1.5 output contract, local Mistral judge, explicit failure/null policy.
- Registered generation prompt includes citation guidance; a discrepancy concerning the manuscript's wording about two complete format examples is disclosed, not silently repaired after the final run.

Final held-out size: **70 groups × 3 languages = 210 queries per architecture; 630 total outcomes.** Development set: 30 groups / 90 queries.

All final generation outcomes and scoring dispositions are archived. A has 209 answered + 1 incomplete; B has 204 answered + 5 clarification + 1 incomplete; C has 203 answered + 5 clarification + 2 incomplete.

Source-ID transfer resolved **77/87 legacy spans**, yielding complete retrieval labels for **59/70 groups / 177 of 210 queries**. Incomplete mappings remain missing, not retrieval misses. All queries were retained for the applicable generation/reference-based scoring stages. Original held-out references were not independently certified or rewritten.

Matched descriptive results from `matched_metrics.csv`:

| Metric | Shared query count | A | B | C |
| --- | ---: | ---: | ---: | ---: |
| Hit@3 | 177 | .559322 | .666667 | .666667 |
| MRR@3 | 177 | .358757 | .556497 | .550847 |
| Faithfulness | 188 | .748071 | .763610 | .759441 |
| Context precision | 202 | .848597 | .919142 | .917079 |
| Context recall | 202 | .843741 | .841472 | .844808 |
| Answer relevancy | 202 | .579449 | .582707 | .595568 |

These are shared complete cases per metric, with different denominators; they are not all-query effectiveness or significance tests. B/C improved retrieval over A in these observations, but B-versus-C differences do not establish a clear additional injection benefit. Known judge semantic/format errors remain limitations.

Important evidence paths:

```text
experiments/t07-final-evaluation-v1/
  completion_assessment.json
  T07_EXECUTION_REPORT.txt
  master_metrics.csv
  per_query_metrics.csv
  matched_metrics.csv
  candidate_registration.json
  registration_seal.json
  execution_manifest.json
  source_span_crosswalk.json
  source_alignment_coverage.csv
  A/interactions.jsonl
  B/interactions.jsonl
  C/interactions.jsonl
experiments/t07-final-ragas-a-v1/
experiments/t07-final-ragas-b-v1/
experiments/t07-final-ragas-c-v1/
```

The RAGAS folders retain scores and raw judge traces. `experiments/t07-methodology-reconciliation-v1/master_metrics.csv` is an earlier **development** artifact, not the final held-out table.

### Source-ID and corpus caveats

- Original held-out input: `D:\thesis\LGSDeliveryRAGAssistant-main\data\benchmark_scenarios_test.json`.
- Benchmark SHA256: `ec91a961df48ea165291a9e5e306de88b2668b42be927922e88f3255f6781054`.
- Exact legacy corpus used by the transfer: `D:\thesis\LGSDeliveryRAGAssistant-main\data\eboss_corpus_chunks_v1.json`.
- Legacy corpus SHA256: `1649d2dba95b8e03a57226364f7294d51d8f009af11c8509a74ecbd8cabba152`.
- **The same-named compatibility corpus inside the clean repo differs.** The T08 builder intentionally reads the old-project file matching the T07 provenance. Do not substitute by filename alone.
- Span transfer uses same-file/page source identity and protected numeric signatures, not answer-quality or retrieval-rank matching. Intersecting windows can broaden relevance at boundaries; that limitation is disclosed.
- The transfer addendum was recorded after structural preflight but before model outcomes. Do not misrepresent that timing.
- Final evaluated corpus/indices: `experiments/chapter3-table-repaired-development-v1/` (1082 chunks, 358 pages).
- Existing app defaults were **not automatically promoted** to the final evaluated corpus/settings; the historical default remains `experiments/chapter3-step2-development`. Check actual configuration before any app demonstration.

## 6. Completed source/normalization work and abandoned alternatives

The prior conversation covered:

1. Occupancy/locational dictionary inspection and patches, including DICT-OCBO-052 and DICT-OCBO-055. For a new dictionary task, inspect their current contents and actual source PDFs rather than infer exact definitions from this summary.
2. Source-table repairs for OCBO PDF pages 14–15, CTO PDF page 6, and separate BFP matrix/page reconstruction; retained before/after artifacts and reviewer notes.
3. New development corpus and matching indices, with source coverage, token overlap and index alignment checks.
4. Retrieval miss investigation separating wrong-service context from normalization fidelity problems.
5. Human-reviewed normalization fidelity suites v1, v2 and v3; actor/direction, unnecessary paraphrasing, intent and conversational clarification were discussed.
6. Corrected/versioned development references, 90-query comparisons, offline batch answer generation, RAGAS traces and T06 closeout.
7. Multiple evaluator experiments and methodology reconciliation; final A/B/C execution under the registered protocol.
8. Employee orientation material and the current offline audit packets/interface.

Useful history folders include `experiments/ocbo-page14-table-repair`, `ocbo-page15-table-repair`, `cto-page6-table-repair`, `bfp-matrix-review`, `table-repairs-staged-v1`, `normalization-fidelity-suite-v3-intent-prompt`, `t06-formal-development-validation-v4`, and `source-reference-review-remaining-batch-v1`. Some old selection/ledger artifacts reside in the older project. Preserve them; do not treat every historical candidate as active.

Specific source interpretations already discussed:

- BFP's condition ends at “if there is changes”; keep that exact source wording and distinguish the user's interpretation that it applies to changes in the specific document.
- CTO-002: printed “87% or 1%” remains ambiguous; quote it explicitly instead of inventing an intended rate.
- OCBO-001: the user distinguished mechanical permit form 6–7 signed/sealed sets and another five sets of plans. Preserve source wording and attributed interpretation; do not silently resolve questionable professional-title wording.
- CPDO-002: user's “both can do”/OR interpretation was not established solely by the cited page. Distinguish reviewer interpretation from authoritative source support.
- OCBO-005: fencing up to and including 1.80 m is PHP 3; above 1.80 m is PHP 4, preserving the source's units.
- BB accreditation: preserve PHP 100 for the first 10 units and PHP 10 “for every unit”; do not silently replace that with “each additional unit.”

Do not restart the old 60-control `t07-independent-judge-review-v1/human_review.json` as a mandatory user assignment. That duplicate review was withdrawn as a completion gate. It is distinct from the actual employee audit now being prepared.

Later v2/v3/v4 evaluator variants exposed semantic problems and were not all promoted. The paired 1560-attempt experiment had 1450 valid and 110 invalid judgments; it is not an active job or a new pending run. Do not retry nulls indefinitely until metrics look favorable.

A previous “577 > 512” tokenizer warning came from full-page tokenization used to reconstruct windows, not a 577-token transformer embedding input. Reviewed chunks were <=120 tokens, with <=122 including embedding special tokens. Do not truncate source pages or change frozen code merely to silence it.

## 7. T08/T09 implementation details

Root: **`experiments/t08-t09-expert-audit-v1/`**.

| Path | Purpose |
| --- | --- |
| `public/R01/index.html`, `R02/index.html`, `R03/index.html` | Offline scoring interfaces, one assigned rater each. |
| `public/R01/packet.json` etc. | Blinded pair records; the HTML also embeds its packet. |
| `public/sources/` | Five byte-preserved source PDFs. |
| `distribution/R01-audit-packet.zip` etc. | Full offline packages to distribute separately. |
| `READ_THIS_FIRST.txt` | Researcher quick start and limitations. |
| `FACILITATOR_PROTOCOL.txt` | Blinding roles, orientation and special-case scoring policy. |
| `COLLECT_RATINGS.ps1` | Visible CLI validation/consolidation of three final JSON exports. |
| `QA_REPORT.json` | Recorded checks, counts and methodology limits. |
| `methodology_snapshot.json` | Manuscript/tracker excerpts and hashes. |
| `private/selection_registration.json` | Fixed sample and timing registration. Do not resample. |
| `private/answer_key.json` | Opaque response IDs to A/B mapping. Keep from raters. |
| `private/original_selected_records.json` | Full records, including original normalization/reference data. |
| `private/build_manifest.json`, `release_manifest.json` | Provenance and output hashes. |
| `private/backup_receipt.json` | External local backup path/hash. |
| `received-ratings/` | Real returned exports and validated outputs; empty at handoff. |

Implementation files:

```text
audit_ui/packet.html
scripts/prepare_expert_audit.py
scripts/collect_expert_ratings.py
scripts/test_expert_audit_browser.cjs
tests/test_expert_audit.py
```

Do not edit only a generated `index.html` and forget its source template, packet identity, manifests and distribution ZIP. Preserve versions if any formal ratings have started. The current builder refuses to overwrite the registered sample or existing public packet folder.

### Sample, blinding and disclosure

- 20 groups, four per category; 60 queries in English/Taglish/Bislish.
- A/B only: 120 unique responses. Each of three raters scores all 120.
- 360 response-review records, 720 separate ordinal scores for three completed reviews.
- Stable opaque answer IDs, separately randomized query order, 30 A-left / 30 B-left pairs per packet, side changes across raters.
- Original answer text and actual retrieved passages are preserved verbatim.
- Common source page links come from original source annotations, including unresolved chunk-transfer cases. They are starting points, **not certified complete reference answers**. Full PDFs allow adjacent-page/table checking.
- Expected reference answers and normalized-query diagnostics stay in private archives; they are withheld from the public rater view to reduce anchoring and pipeline identity clues.
- Configuration labels, scores, private key and seed are absent from distributed ZIPs. Content/style and public research archives can still allow inference; do not claim perfect blinding.
- A custodian who knows the key is not blind. A genuinely blinded facilitator must not access the key or compare with named archived outputs.

**Timing deviation:** no earlier registered 20-group audit selection was found. Selection was registered on 2026-10-20, after automated T07 results and before human ratings. It uses a fixed SHA256 ordering of group IDs within categories, not scores or answer quality. This is not preselection before T07. Preserve the disclosure and discuss it with the adviser before formal collection. Do not retroactively invent a preregistration or resample difficult cases.

The main tracker T10 title/allocation specifies three experts/360 records; one description says four while retaining 360. Follow the manuscript's three-full-rater allocation and document that inconsistency.

### Rubric and missingness

Two independent **1–4** dimensions: Answer Relevance and Factual Faithfulness. No five-point scale and no forced preference winner.

### Verification already performed

On 2026-10-20: eight focused automated tests and twelve browser checks passed; desktop/mobile screenshots were inspected. Checks included unchanged inputs, balanced selection/order, verbatim content, public metadata masking, valid PDF links, persistence/import/export and missing-score handling. All 426 page links per packet pointed within PDF bounds (86 distinct page links). Source PDF bytes matched frozen provenance.

On 2026-10-22, this handoff preparation rechecked **27 release-manifest files; none differed**. It did not rerun model evaluation or pretend old tests were newly executed.

Synthetic browser/collector test ratings exist only under ignored `tmp/expert-audit-browser/`; they are labeled synthetic and **must never be counted as employee evidence**.

## 8. Commands and practical continuation

Start Claude Code in the clean project, then use this as the initial instruction:

> Read CLAUDE_HANDOFF.md and the current T08/T09 handoff and QA report. Verify the local Git state and relevant manuscript/tracker references. Continue from the existing artifacts; preserve frozen T06/T07 results and the registered audit sample. Do not start a model run or duplicate review. First report the next concrete T10 preparation action and any real human input needed.

Read-only startup:

```powershell
Set-Location D:\thesis\LGSDeliveryRAGAssistant-clean
git status --short
git branch --show-current
git log -1 --oneline
Get-Content experiments/t08-t09-expert-audit-v1/READ_THIS_FIRST.txt
Get-Content experiments/t07-final-evaluation-v1/completion_assessment.json
```

No server is required to inspect or use the audit UI. Open `public/R01/index.html` in Edge/Chrome. For distribution, extract the entire assigned ZIP, keeping its rater folder and `sources` folder beside each other. Don't preview-enter scores into a real rater's browser session; use a separate profile for practice.

Run focused checks **if code has changed or a fresh validation is needed**, not as a reason to restart the study:

```powershell
D:\thesis\venv\Scripts\python.exe -m unittest discover -s tests -p test_expert_audit.py -v
node scripts/test_expert_audit_browser.cjs
```

The tests rely on local packet/private artifacts. The browser script uses the installed runtime Playwright package and Chrome; on another machine set `AUDIT_PLAYWRIGHT_PATH` and `AUDIT_BROWSER` to installed equivalents. Do not install or launch a model to run UI tests. Avoid mixing FAISS and RAGAS tests in one Python process; earlier checks used separate processes for library compatibility.

After actual T10 returns arrive:

1. Preserve original downloaded files.
2. Put selected final copies named `R01-final.json`, `R02-final.json`, `R03-final.json` in `experiments/t08-t09-expert-audit-v1/received-ratings/`.
3. Run:

```powershell
& .\experiments\t08-t09-expert-audit-v1\COLLECT_RATINGS.ps1
```

This creates a new `received-ratings/validated-v1/` containing blinded JSON, CSV and receipt. Existing output is not overwritten. If a legitimately revised collection is required, use the underlying collector with a new output directory and preserve earlier returns.

The collector validates exports and requires both 1?4 scores and does not unmask systems or calculate agreement. T11 then estimates **ordinal Krippendorff's alpha separately by dimension**, reporting missingness and the manuscript's >=.80 target without manipulating ratings to reach it. T12 needs a declared paired analysis that respects scenario/language/rater dependence; 360 reviews are not 360 independent scenario groups.

Do not run `prepare_expert_audit.py --register-only` again to choose new groups. Do not delete the public folder just to bypass overwrite protection. The sample and artifacts already exist.

For an unrelated future app startup task, run Uvicorn from the clean project root; running from `D:\thesis` caused `ModuleNotFoundError: No module named 'app'` previously. The audit UI itself does not use Uvicorn.

## 9. Employee materials and immediate next steps

Existing orientation resources:

- `experiments/t08-t12-rater-preparation/MOCK_RATER_HANDOUT.txt`: fictional English practice, not official Davao service advice or study ratings.
- `experiments/t08-t12-rater-preparation/FACILITATOR_GUIDE.txt`: useful practice guidance, but older development-status paragraphs are stale.
- `output/employee-annotation-meeting-v1/Davao_City_Employee_Annotation_Meeting_Packet.pdf`: previously created meeting packet.
- The meeting packet was previously uploaded with explicit authorization to Google Drive: `https://drive.google.com/file/d/148m7zbZnrj_69znMZ2UMeLbwHqdVCYHi/view`. Do not upload duplicates or send messages automatically.

Next actual tasks are to acknowledge the timing disclosure, arrange three qualified independent auditors, orient them using fictional practice, check PDFs open on their devices, distribute each assigned ZIP, and receive real ratings. The user can review the UI or request refinements before collection; changes must keep the research archive/version history intact.

Automated Chapter 4 findings can be drafted from existing T07 results while awaiting human ratings, with coverage and judge limitations stated. Human-audit conclusions, reliability values, and significance results cannot be fabricated or inferred from automated scores.

**The handoff is complete when the next assistant understands the current state and continues from these artifacts. It does not require restarting completed research work.**


Current scoring revision ? 2026-10-23
Both Answer Relevance and Factual Faithfulness require an integer 1?4 score for final submission, following Chapter 3 Table 2. Notes and flags record uncertainty. Drafts may contain unanswered dimensions; do not guess a score to complete a draft. Consult the facilitator when evidence is insufficient. No automatic conversion of old missing ratings is performed. Packet schema 2 / version t08-t09-v2-four-point rejects earlier-version imports. The original sample, questions, answers, passages, IDs and presentation order remain unchanged. Previous releases are retained in the local backup archive.


## Current audit amendment - 2026-10-26 (supersedes earlier A/B-only handoff)

The researcher confirmed that formal scoring has not started and approved the Module 1 statement. The current local release is `experiments/t08-t09-expert-audit-v2-triple/`. Read its `READ_THIS_FIRST.txt`, `CHAPTER3_AMENDMENT.md`, and `QA_REPORT.json`. Module 1: 40 code-switched B/C comparisons, 80 five-point fidelity ratings per rater, 240 total. Module 2: 60 A/B/C triples, 180 answer reviews per rater, 540 total, with separate Table 2 relevance/faithfulness scores. Five sessions with mandatory breaks. Original sample and outputs are preserved; no model rerun. Original PDF/workbook have not been rewritten; the amendment supplies replacement text. Prior A/B archive hash discrepancies are documented in private/provenance.json: selected content is unchanged, retrieval-label metadata differs. Earlier release and Drive uploads are historical; new local ZIPs have not been uploaded. Use scripts/collect_triple_ratings.py separately for M1/M2; never pool scales. Private backup: D:\thesis\conversation-backups\t08-t09-triple-private-20261026.zip (SHA256 8f03276b4b65bf24b5a9afcdcba4e4c1a45cab501c40371a2d6003142b51f865).


Drive upload completed 2026-10-26: https://drive.google.com/drive/folders/1p5YI_AQuK1ysCm_GJpYpvMDZSzQiHj1R. See experiments/t08-t09-expert-audit-v2-triple/DRIVE_UPLOAD_RECEIPT.json for packet IDs and hashes. Supersedes earlier not-uploaded notices. Private answer keys remain local; no access permissions changed.


## Reviewer provenance correction - 2026-10-28

The researcher explicitly confirmed that all three experts independently chose their scores without seeing AI suggestions and that the six files contain their exact submitted scores. Earlier file metadata described AI-prepared assessments and was disputed by the researcher. Corrected copies are in `C:\Users\User\.codex\.chatgpt-projects\g-p-6ac6a06fa534819186f2a4eae6c3c4e6\output\reviewer-independent-assessments-corrected-20261028`. Attribution is recorded as independently scored, as confirmed by the researcher; this assistant did not observe the sessions. Originals are preserved at `C:\Users\User\.codex\.chatgpt-projects\g-p-6ac6a06fa534819186f2a4eae6c3c4e6\output\reviewer-personal-assessments`. See PROVENANCE_CORRECTION.json for prior statements and hashes. All 780 records and 1,320 scores are unchanged; no scores were imputed. These are custom-schema files; collector conversion and reliability analysis have not been performed.


## T10-T12 analysis closeout - 2026-10-28

All six corrected assessments validated against issued packets and CSV scores: 780 records, 1,320 scores, no missing or edited scores. Researcher confirmation of independent scoring remains the attribution basis; prior conflicting metadata and its correction are retained. Analysis artifacts are in `experiments/t10-t12-human-analysis-v1/`. Alpha was computed separately by dimension with category-stratified scenario bootstrap intervals. Seven exploratory scenario-paired signed-rank comparisons used Holm adjustment; none was significant. Do not claim equivalent performance or superiority. Raw inputs, mappings and aligned matrices are under ignored `private/`. Analysis uses no model calls and changes no frozen outputs. The updated workbook is a versioned copy; original Downloads workbook and a backup are preserved. No T10-T12 results have been uploaded to Drive in this step.


## Writing package and explicit deferral - 2026-10-28

Chapters 4-5, six result tables, three publication figures and Chapters 1-3 replacement passages are prepared in `outputs/manuscript-closeout-20261028/`. The PDF is a ReportLab review draft, not a department LaTeX compilation. The user answered the editable-manuscript/template question: "skip that part for me and just keep this in mind". Preserve that deferral. T13/T14 are complete as drafts; T15 source integration and T16 official compilation remain pending. Adviser-review and submission checklists are prepared, but no approval, ethics filing or portal upload occurred.

The manuscript draft discloses an original 177-query source-label subset separately from the later 210-query reconciliation. The original crosswalk hash matches the execution manifest; the current crosswalk matches its later seal. Drafting does not recertify the later mappings. No archived outcomes or scores were changed. The original manuscript and Downloads tracker remain preserved; use the latest versioned tracker copy in this output folder.
