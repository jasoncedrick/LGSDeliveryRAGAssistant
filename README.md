# LGSDeliveryRAGAssistant

Davao City Citizen Charter research assistant: English, Taglish and Bislish.

**Adviser demo: 12 November 2026.** This branch is `demo/adviser-20261112`.
It is an operational research prototype with documented answer-quality failures, not an official city service.

## Start here

| What you need | Where to open |
| --- | --- |
| Run and present the demo | [Demo guide](demo/DEMO_GUIDE.md) |
| Checks and known failures | [QA report](demo/qa/QA_REPORT.json), [live smoke responses](demo/qa/live_smoke.json) |
| Human-rating analysis archive | [T10-T12 report](experiments/t10-t12-human-analysis-v1/T10_T12_REPORT.md) |
| Automated A/B/C results | [T07 execution report](experiments/t07-final-evaluation-v1/T07_EXECUTION_REPORT.txt) |
| Paper and team handoff | [Team guide](TEAM_START_HERE.md) |
| Local repository map | [Repository map](demo/REPOSITORY_MAP.md) |
| Earlier implementation notes | [Historical README](demo/HISTORICAL_README.md) |

## Run on the prepared demo laptop

Open PowerShell in this checkout, with Ollama running:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\START_DEMO.ps1
```

Open http://127.0.0.1:8000. Keep the terminal open. One inference request runs at a time.
The launcher uses the existing `D:\thesis\venv` environment; a fresh clone on another machine requires dependencies and the registered model. The preflight checks model identity and research-file hashes. It does not certify answer correctness.

## What is current

- Registered chunk retrieval: 120 tokens, 20-token overlap, K=3, BM25 .75 / dense .25 / dictionary retrieval boost 0. Dictionary-assisted normalization remains enabled.
- Website runtime restored from the earlier operational `9d6b354` version, with the current lightweight reference display. Language adapter v2 is a post-study website change, not frozen T07 generation.
- QA: 20 unit tests, 22 browser checks, 11 motion/accessibility checks and static build passed. Three real requests completed; factual grounding, ambiguity handling and Bislish fidelity still have documented failures.
- Frozen evaluation outputs and previous experimental candidates remain archived. Experimental folders are not automatically active runtime settings.
- Human-rating archives and automated RAGAS scores are different evidence. The later final manuscript has figures that differ from earlier archived human-analysis tables; reconcile their provenance before presenting the newer figures as reproduced results.

## Repository hygiene

Use this branch for the adviser demo. Historical branches remain checkpoints; do not delete them or use every experiment as a current instruction. `main` remains the earlier published checkpoint until integration is reviewed.

Raw private ratings, audit keys, local credentials and machine backups are excluded from this demo update. Aggregate results and review documents remain available through the links above. No new model evaluation or public-domain deployment is performed by this repository cleanup.
