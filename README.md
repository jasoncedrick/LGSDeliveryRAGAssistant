# LGSDeliveryRAGAssistant

Start with [the T06 closeout](experiments/t06-harness-closeout-v3/T06_STATUS.txt) and [the T07 execution report](experiments/t07-final-evaluation-v1/T07_EXECUTION_REPORT.txt).

This checkout contains the Chapter 3 implementation and archived T06/T07 evaluation evidence. T06 harness implementation and T07 A/B/C execution/CSV export are complete with the limitations recorded below. Evaluation completion does not certify every source label or automated judgment.

## Latest results

- [Final metrics](experiments/t07-final-evaluation-v1/master_metrics.csv), [matched comparisons](experiments/t07-final-evaluation-v1/matched_metrics.csv), and [per-query outcomes](experiments/t07-final-evaluation-v1/per_query_metrics.csv).
- All 630 held-out A/B/C outcomes and their scoring dispositions are archived.
- [Registered settings and provenance](experiments/t07-final-evaluation-v1/EXECUTION_GUIDE.txt): K=3, weights 0.75 BM25 / 0.25 dense / 0 dictionary boost, Mistral, 120-token chunks and 20-token overlap. The source-ID transfer addendum was registered after structural preflight and before inference.

Retrieval-label coverage is complete for 59/70 groups (177/210 queries) per architecture. The other 33 queries remain in the run with Hit/MRR missing. Judge failures, clarifications, incomplete answers and source-boundary transfer limitations are retained. Matched metric means use metric-specific shared eligible queries; they are descriptive and are not significance claims. Human employee auditing remains separate.

Final answers and evaluator traces are under `experiments/t07-final-evaluation-v1/` and `experiments/t07-final-ragas-{a,b,c}-v1/`. Rejected evaluator experiments remain historical evidence, not active replacements. The optional 60-control review form is not a prerequisite for using these archived results. Do not rerun or tune the frozen systems based on final-test outcomes.

## Where to work

Open `D:\thesis\LGSDeliveryRAGAssistant-clean` in VS Code on the original workstation. The clean-development and evaluation-checkpoint branches preserve earlier snapshots. The `main` integration retains existing repository history; older compatibility files are not instructions to substitute superseded evaluation methods.

| Purpose | Files |
|---|---|
| Application | `app/main.py`, `app/pipeline.py`, `app/static/index.html` |
| Normalization | `src/query_normalizer.py`, `config/normalization_intent_candidate.txt` |
| 120/20 token chunks and retrieval | `src/token_windows.py`, `src/chunk_retriever.py` |
| Dictionary and original PDFs | `data/municipal_dictionary_v1.json`, `data/raw_charters/` |
| Reviewed source staging | `experiments/table-repairs-staged-v2/source_pages.json` |
| Repaired corpus and matching indices | `experiments/chapter3-table-repaired-development-v1/` |
| Corrected reference answers and saved retrieval scores | `experiments/t06-formal-development-validation-v3/` |
| Original generated answers | `experiments/t06-30group-development-batch-v1/interactions.jsonl` |
| Offline RAGAS results and judge traces | `experiments/t06-ragas-90query-development-v1/` |
| T06 checkpoint and limitations | `experiments/t06-validation-report-v1/` |

## Compatibility boundaries

The app still defaults to `experiments/chapter3-step2-development/`. That older matched artifact set remains solely to preserve existing app behavior. The repaired corpus and reviewed prompt were evaluated offline; they have not been promoted automatically. `EBOSS_ARTIFACT_DIR` changes corpus selection only, not normalization prompt selection.

`build_chapter3_development.py` imports `INGESTION_CATALOG` from `scripts/ingest_eboss_corpus.py` and reads `config/pipeline_manifest.json`. Keep these dependencies; do not interpret the old manifest's frozen label as certification of the current results. Use the Chapter 3 builder, not the old ingester, for new artifacts.

## Running and evaluating

Install dependencies in a separate virtual environment, including the appropriate PyTorch build as noted in `requirements.txt`. Model weights and cached embeddings must be provisioned separately. Recorded package/model versions are in the RAGAS `runtime_identity.json`; requirements are not a complete platform lock.

Run commands from this project root:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
python -B scripts/verify_chapter3_retrieval.py --artifacts experiments/chapter3-table-repaired-development-v1
```

For a NEW development batch (requires the configured local model server), choose a fresh output name:

```powershell
python -B scripts/run_t06_chunk_development.py --output-name new-development-run --references experiments/t06-formal-development-validation-v3/development_groups.derived.json --prompt-file config/normalization_intent_candidate.txt
```

The runner now explicitly selects reference inputs, derives their metadata, and counts stopped queries with labels as zero Hit/MRR. Existing archived outputs were not regenerated or edited. No new model run was performed to prepare this branch.

## Methodology and limitations

Chapter 3 uses 120-token chunks, 20-token overlap, chunk-level scoring and K=3/K=5. The main Thesis Tracker tab defines T06 as harness engineering; T07 frozen configuration comparison is separate. [Recorded methodology and tracker evidence](experiments/t06-formal-development-validation-v3/methodology_and_tracker.json) preserves their source hashes.

The earlier 90-query K=5 development snapshot is historical. The reviewed v4 development references and later final K=3 A/B/C runs are linked above. Same-model judging, source-label transfer, BFP context separation and ambiguous source wording remain limitations; no claim of independent expert certification is made.

`publication_manifest.json` records the original clean snapshot; it is historical, not an inventory of every later evaluation file. Later experiment manifests and seals record their own inputs and outputs. Older audits can reference workstation paths or evidence retained in the backup. Model binaries and caches are provisioned separately. Compatibility inputs retained from earlier `main` history must be checked against the registered run hashes before reuse.

Next: diagnose the three null judge metrics and finish source/reference review before tuning, freezing and final evaluation. Preserve all failures and avoid changing held-out benchmarks.
