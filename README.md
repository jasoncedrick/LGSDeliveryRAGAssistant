# LGSDeliveryRAGAssistant

This branch preserves the Chapter 3 development work through the T06 evaluation-harness checkpoint. It is a development snapshot, not a frozen final thesis evaluation.

## Start here

1. [T06 validation report](experiments/t06-validation-report-v1/T06_VALIDATION_REPORT.txt): completed work, results, and limitations.
2. [Conversation change guide](experiments/conversation-change-ledger-20261019-070107/START_HERE.txt): history of dictionary verification, source repairs, normalization, retrieval, and evaluation.
3. [Tracker-to-file map](experiments/conversation-change-ledger-20261019-070107/task_file_map.csv): which files support each task.
4. [File inventory](experiments/conversation-change-ledger-20261019-070107/file_inventory.csv): snapshot paths, roles, hashes, and provenance limitations. Git states in this inventory describe the pre-commit snapshot.

## Current development files

| Purpose | Location |
|---|---|
| Dictionary | `data/municipal_dictionary_v1.json` |
| Token windows and chunk retrieval | `src/token_windows.py`, `src/chunk_retriever.py` |
| Reviewed source-page repairs | `experiments/table-repairs-staged-v2/` |
| Rebuilt corpus and matching BM25/FAISS indices | `experiments/chapter3-table-repaired-development-v1/` |
| Offline normalization candidate | `config/normalization_intent_candidate.txt` |
| Candidate human reviews | `experiments/normalization-fidelity-suite-v3-intent-prompt/` |
| Corrected development references and K=3/K=5 scores | `experiments/t06-formal-development-validation-v3/` |
| Original 90-query answer archive | `experiments/t06-30group-development-batch-v1/` |
| Offline RAGAS results and judge traces | `experiments/t06-ragas-90query-development-v1/` |
| T06 checkpoint report | `experiments/t06-validation-report-v1/` |

Keep a corpus, its source pages, both indices, manifest, and provenance together. Do not mix artifacts from different versions.

## App versus offline evaluation

`app/pipeline.py` still defaults to `experiments/chapter3-step2-development`. The repaired corpus and reviewed normalization candidate were evaluated offline; this checkpoint does not promote them into app defaults. The normalization fidelity contract remains opt-in.

Start Uvicorn from the project directory where `app/` exists. Local inference requires a separately installed model/server. Model weights, the Python environment, and credentials are not bundled here. Use the archived runtime identities and protocols when reproducing evaluations; `requirements.txt` alone is not a complete environment lock.

The older `config/pipeline_manifest.json` has a historical `frozen` label and older metrics. It does not certify the repaired corpus or the new results. Inherited section-retrieval code and earlier experiments are historical; they are not the active Chapter 3 workflow.

## Methodology and task status

Chapter 3 requires 120-token source-linked chunks, 20-token overlap, chunk-level BM25/FAISS/dictionary fusion, and K=3 or K=5. Development uses 30 scenario groups / 90 language variants. Final held-out data remains isolated.

The main **Thesis Tracker** tab is authoritative. [Recorded methodology and tracker evidence](experiments/t06-formal-development-validation-v3/methodology_and_tracker.json) documents the source hashes and task definitions. The full manuscript/workbook copies are in the separate local backup, not newly published with this commit.

T06 harness engineering and development execution are demonstrated: 84 answers and six clarification outcomes; 81 complete RAGAS records and three partial judge failures. Answer generation/RAGAS used K=5. The 90-query retrieval scores are Hit@3 72.22%, MRR@3 0.5704; Hit@5 75.56%, MRR@5 0.5776. These are provisional development results, not final A/B/C results.

Next: inspect the three null judge metrics, finish remaining reference/source validation, and follow the documented tuning/freeze/expert-review requirements before final evaluation. See [remaining work](experiments/t06-validation-report-v1/remaining_work.json).

## Finding this checkpoint again

Branch: `thesis/t06-development-checkpoint-20261019`.

From a clean checkout, use `git switch thesis/t06-development-checkpoint-20261019`. Before switching branches in a working directory with edits, inspect `git status` and save those edits. This branch was created from local commit `bcd0ecdd0085c6f2b70d5615e2d80bcdb1912249`; it does not replace `main`.

The conversation backup ZIP is stored separately under `D:/thesis/conversation-backups/` on the original workstation. Absolute paths in older audit records describe that workstation; use this README's relative links when browsing GitHub.
