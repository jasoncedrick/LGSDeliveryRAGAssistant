# Adviser demo: 12 November 2026

Use **D:\thesis\LGSDeliveryRAGAssistant-demo-20261112**, branch `demo/adviser-20261112`.
This is an isolated local demo checkout. Other repositories contain research history; do not delete them or launch competing servers.

## Start and recover

1. Plug in the laptop, open Ollama, and close other model/evaluation jobs. Keep sleep disabled during the presentation.
2. Open PowerShell and run:

```powershell
Set-Location D:\thesis\LGSDeliveryRAGAssistant-demo-20261112
powershell -NoProfile -ExecutionPolicy Bypass -File .\START_DEMO.ps1
```

3. Open **http://127.0.0.1:8000** in Chrome/Edge. Wait for readiness before asking.
4. Keep the terminal open. Expect tens of seconds per question; the first request may take longer. One model request runs at a time. Do not repeatedly resubmit.
5. Stop with Ctrl+C in the server terminal. Restart with the same command if needed. If the port is occupied, identify its terminal/process first; the launcher will not kill it or start a duplicate.

Read-only preflight: `powershell -NoProfile -ExecutionPolicy Bypass -File .\CHECK_DEMO.ps1`.
If Ollama is unavailable, open it and rerun preflight. If model/hash checks fail, preserve the error and investigate; do not bypass registration or download a substitute model.
If the network/domain fails, continue at localhost. This preparation does not update the public domain or create a tunnel. Model assets already exist on this PC, but a cold-start fully disconnected test has not been performed.

## Suggested 8-minute walkthrough

- 1 minute: explain the service-information problem and five source offices.
- 2 minutes: show the question field, language selector, compact references and source library. Explain each query is independent, not conversation memory.
- 2 minutes: submit an explicit service question in English, then Taglish. Allow time for the queue. These are demonstrations, not a new benchmark or proof of superiority.
- 2 minutes: discuss a recorded failure from `qa/live_smoke.json`: the Taglish excavation answer inferred a validity condition absent from its passages. The broad clearance question also assumed FSEC. Explain that source attribution alone does not establish factual support.
- 1 minute: discuss next work: improve ambiguity handling and evidence coverage in a separately versioned development study, with fair A/B/C evaluation.

Do not claim B beats A or C based on a successful live example. Do not present archived screenshots or responses as newly generated live results. If a response is wrong, show it honestly and explain the limitation.

## Configuration and reference basis

The demo retains the registered 120-token/20-overlap corpus and chunk-level retrieval. Registration: `experiments/t07-final-evaluation-v1/candidate_registration.json`; source coverage: `experiments/chapter3-table-repaired-development-v1/validation.json`. K=3, weights .75 BM25 / .25 dense / 0 dictionary retrieval boost. Dictionary injection remains in normalization.

Base checkout: `a64fd61`. Website runtime and language wrapper restored from `9d6b354`; newer lightweight UI retained. The newer unapproved development backend is not promoted. The website uses `website-response-language-v2`, a post-study language adapter; this is not an exact replay of frozen T07 generation. Frozen code, corpus, indices and evaluation records are not rewritten.

Original manuscript: `D:\thesis\20260923.pdf`, Chapter 3; reference snapshots and the documented audit amendment remain in experiments. The later 20261031 final draft contains human-rating figures that differ from the earlier archived human-analysis tables. Their provenance needs reconciliation before claiming the newer tables were reproduced. This demo does not settle that discrepancy or revise the paper.

## Readiness and known limits

Runtime and interface checks pass; answer quality has **not** passed a comprehensive acceptance test. The three live smoke requests completed, but two exposed substantive problems: unsupported validity inference and missed ambiguity (plus weak Bislish language fidelity and leaked chunk IDs). These are retained unchanged in QA evidence. Citation-label validity is a formatting check, not a support judgment.

The site is visibly a research prototype. It does not issue permits or provide official determinations. No extra model concurrency, new evaluation run, or fabricated ratings are introduced for this demo.
