# LGSDeliveryRAGAssistant

Davao City Citizen Charter research assistant for English, Taglish and Bislish.

This release follows Christian's CLEAN guide while preserving the working citizen website and registered thesis artifacts. Historical drafts and diagnostics are available at the Git tag `archive/pre-clean-demo-20261112`.

## Start here

| Purpose | Open |
| --- | --- |
| Present the assistant | [Demo guide](demo/DEMO_GUIDE.md) |
| English, Taglish, Bislish questions | [Demo queries](demo/DEMO_QUERIES.md) |
| Current October 30 human results | [Results guide](experiments/final-human-audit-20261030/README.md) |
| Automated statistical summary and figures | [Results](results/) |
| Cleanup, exceptions and QA | [Release notes](docs/cleanup/RELEASE_NOTES.md) |
| Frozen A/B/C evaluation | [Execution report](experiments/t07-final-evaluation-v1/T07_EXECUTION_REPORT.txt) |

## Run the demo

On the prepared laptop, open PowerShell in this repository with Ollama running:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\START_DEMO.ps1
```

Open http://127.0.0.1:8000. Keep the terminal open. Only one inference request runs at a time.
The launcher uses the existing `D:\thesis\venv` environment. Other machines need the Python requirements, cached embedding model and registered eboss-mistral model. A clone alone does not include model weights or private rater packets.

## Evidence and limitations

The registered runtime retains 120-token windows, 20-token overlap, chunk-level scoring and K=3. The corpus actually contains **1,082 chunks**; the supplied guide's 1,032 figure is not supported by the registered files. Website language adapter v2 is separate from frozen study generation. Live answers can still make unsupported claims or miss ambiguity; this is a research prototype, not an official city service.

The October 30 human aggregate tables and automated summary were reproduced exactly from the supplied packets and archived runs. This verifies calculations, not independent human authorship. Human reliability is .510/.771/.781, all below .80; do not repeat the conflicting reliability claim in the cleanup guide. See the results guide for descriptive and paired-comparison interpretation.

Raw rating packets remain private and ignored by Git. No frozen scores, references or model outputs were rewritten. No new model evaluation was run for cleanup.
