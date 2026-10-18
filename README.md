# LGSDeliveryRAGAssistant - clean development branch

Start with [the T06 report](experiments/t06-validation-report-v1/T06_VALIDATION_REPORT.txt) and [remaining work](experiments/t06-validation-report-v1/remaining_work.json).

This branch contains only the approved current implementation, required compatibility inputs, and selected development evidence. It has independent Git history so abandoned files from the backup branch are not inherited. It is not a final corpus freeze or completed A/B/C thesis evaluation.

## Where to work

Open `D:\thesis\LGSDeliveryRAGAssistant-clean` in VS Code on the original workstation. Branch: `thesis/chapter3-clean-development-20261019`. The old working folder and checkpoint branch remain backups.

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

The saved 90-query development run has 84 answers and six clarifications; 81 full RAGAS records and three partial failures. Five reference groups were assistant source-reviewed; 25 retain provisional legacy semantics. Answer evaluation used K=5. Same-model judging, BFP context separation and ambiguous BB fee wording remain limitations.

The selected files have a new publication manifest (`publication_manifest.json`). Older audit files may reference historical evidence retained only in the backup; the reduced checkout does not pretend to reproduce every historical hash check. Source extraction history, superseded scripts, full backups, model binaries and held-out data are intentionally absent.

Next: diagnose the three null judge metrics and finish source/reference review before tuning, freezing and final evaluation. Preserve all failures and avoid changing held-out benchmarks.
