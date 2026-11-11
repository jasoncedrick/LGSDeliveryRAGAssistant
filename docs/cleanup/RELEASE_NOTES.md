# Christian-guided cleanup - 12 November 2026

Source: [shared CLEAN folder](https://drive.google.com/drive/folders/1O8b9MiLTgFECOEjSoYN-wVvBfvF6vm_u). The supplied guide is preserved verbatim as `CHRISTIAN_GUIDE.md`; its factual assertions are not automatically validated by copying it.

## Changes

- Removed 1,094 superseded tracked files (about 141 MiB) from the release tree, plus the obsolete historical README copy. Removed paths and hashes are recorded in `removed_files.json`. Full prior history remains at `archive/pre-clean-demo-20261112`; previous main is `archive/pre-clean-main-20261112`.
- Kept the core folders listed in Drive, registered runtime dependencies, source PDFs, benchmarks, website assets and deployment files. Supporting script imports required by the retained tests remain, even where the guide's short script list omitted them.
- Imported 66 supplied files: portable scripts, October 30 human results and raw packets, statistical summary and figures. Drive identifiers and local hashes are in `drive_imports.json`. Raw packets are private and gitignored; they are not published with the branch.
- Replaced stale landing-page and handoff instructions with current links. Historical paper drafts and October 28-29 results are no longer the active reference.
- Added 15 aligned English/Taglish/Bislish demo questions and three ambiguity prompts. They are practice material, not performance evidence or benchmark changes.

## Verified evidence

- 98 tests passed across 21 suites, run in separate processes. The combined attempt exposed an OpenMP library conflict; its log is retained. No unsafe OpenMP override was used.
- Registered corpus audit passed: 1,082 chunks, 120-token source windows, 20-token overlap, matching index rows and source hashes. All registered file hashes remain unchanged.
- Supplied human aggregate JSON reproduced exactly from six provided final exports: 780 output-review records / 1,320 dimension scores. The automated statistical summary also reproduced exactly from archived runs. No new model or RAGAS evaluation was launched.
- Human statistics dependency `krippendorff==0.8.2` was installed without changing its dependencies. Additional analysis dependencies are listed in `requirements-analysis.txt`.
- Human and automated reproduction scripts now require `--output-dir` and refuse nonempty output directories. This protects the imported originals; statistical computation is unchanged. The figure script remains the supplied portable version and has not overwritten supplied figures.

## Corrections and deliberate exceptions

1. The guide's **1,032 chunks** conflicts with the actual registered **1,082**. We retain the verified corpus and report the discrepancy; no corpus was rebuilt to fit the manuscript claim.
2. The guide's reliability claim **.808-.875** conflicts with the supplied tables, which reproduce as **.509656, .771219, .780854**. All three point estimates are below .80. These are the values to discuss with the adviser.
3. Website **v2** remains the operational demo adapter. The guide describes v4; v4 was an unapproved answer-quality candidate. Its modules/config remain available but it is not silently promoted. The obsolete v4-specific grounding test is archived with its version, not treated as a passing test of v2.
4. Exact numerical reproduction does not independently authenticate the raters' authorship or independence. No scores, provenance notes or outputs were altered to improve conclusions.
5. Frozen artifacts are preserved. Some historical reproduction manifests contain original-machine absolute paths; the current demo and imported portable analysis scripts are the supported entry points. Do not rerun historical held-out generation to resolve path differences.
6. Operational checks do not establish reliable live answers. Prior smoke failures remain in `demo/qa/live_smoke.json`: unsupported permit-validity inference, missed ambiguity and weak Bislish fidelity.

## Reproduce without overwriting originals

With the project environment and `requirements-analysis.txt` dependencies installed, and the private packets available locally:

```powershell
python scripts/run_final_human_rate_audit.py --output-dir tmp/human-check-new
python scripts/compute_m4_automated_stats.py --output-dir tmp/automated-check-new
python scripts/verify_chapter3_retrieval.py --artifacts experiments/chapter3-table-repaired-development-v1
```

Choose new output directories on each run. Results remain in the original imported folder until explicitly reviewed; never overwrite source exports.

Publishing this branch to main preserves Git ancestry. Archive tags retain old versions; no force push or historical branch deletion is required. A main push may trigger any existing hosting integration; successful Git publication alone is not verification of the public website or PC tunnel.
