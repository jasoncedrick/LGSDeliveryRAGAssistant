# Adviser demo - 12 November 2026

Use **D:\thesis\LGSDeliveryRAGAssistant-demo-20261112**, branch `demo/adviser-20261112`.
Read its `demo/DEMO_GUIDE.md` first.

```powershell
Set-Location D:\thesis\LGSDeliveryRAGAssistant-demo-20261112
powershell -NoProfile -ExecutionPolicy Bypass -File .\START_DEMO.ps1
```

Open http://127.0.0.1:8000. Keep Ollama and the server terminal running. One model request runs at a time.

## Repository map

- `LGSDeliveryRAGAssistant-demo-20261112`: active isolated demo.
- `LGSDeliveryRAGAssistant-clean`: research/development branch with unapproved experiments preserved. Do not launch that backend for this demo.
- `LGSDeliveryRAGAssistant-main`: historical provenance and abandoned experiments; preserve.
- `LGSDeliveryRAGAssistant-main-integration-20261020`: historical integration worktree; preserve.

No historical repositories, ratings or results were deleted. Untracked-file backups and exact inventories are in `conversation-backups/adviser-preparation-20261111`. Ignored/private files remain in their original locations and previous backups; these new ZIPs are not complete-machine backups. Keep backup archives private.

Operational checks pass; answer-quality limitations remain in the demo guide and QA evidence. No new remote push or public deployment was performed during this preparation.
