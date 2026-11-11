# Co-Member Guide: Cleaning the Repo Without Breaking Live Demos (While Matching the Final Manuscript PDF)

> **CRITICAL: Do NOT wipe or hard-reset your working demo branch to `1_CLEAN_REPOSITORY/` alone.**  
> `1_CLEAN_REPOSITORY/` isolates **only the core academic thesis/benchmark pipeline** required by the Final Manuscript PDF—it intentionally omits the post-study Citizen Website & Vercel demo layer (`app/website*.py`, `website/`, `config/website*.json`, Vercel build files) that you polished for live demos.  
>
> Instead of resetting blindly, use this guide as a checklist of **what NOT to compromise** (for both live demos and Final Manuscript reproduction) vs. **what IS safe to delete/prune** (~185 MB of dead logs, retry folders, and superseded October 28–29 drafts).

---

## 1. What Inside This `CLEAN/` Package Is For

1. **`1_CLEAN_REPOSITORY/`** — Reference snapshot of the stripped core thesis codebase, datasets, 1,032-chunk index, 30-group Dev experiments, and 70-group Held-Out Test experiments that match Chapters 3–4 of the **Final Manuscript PDF**.
2. **`2_CRITICAL_SYNC_FROM_DESKTOP_THESIS_FOLDER/`** — The finalized October 30 Double-Blind Human Expert Audit files (`FINAL HUMAN RATE`), automated statistical test script (`compute_m4_automated_stats.py`), and final figures (`Figures 3–11`) that lived in the Desktop thesis folder (`CS THESIS WRITING 2 - CS 4154`) and **must** replace the older October 28–29 human-analysis files in Git.

---

## 2. What NOT to Compromise for the Live Demos to Work

Keep these files **intact** in your working repository if you need either the **Citizen-Facing Website Demo** (`app.website` + Vercel frontend) or the **Local Chapter 3 UI Demo** (`app.main`) to run:

### A. Citizen Website & Vercel Demo Layer (`app.website:app`)
- **Backend modules (`app/`):**
  - `app/website.py` (Main FastAPI server, `/api/jobs` queue, CORS/CSP, `/sources/{id}.pdf`)
  - `app/website_intake.py` (Scope/missing-service intake checks & localized clarification options)
  - `app/website_language.py` (Dialect detection & response-language instruction loader)
  - `app/website_normalizer.py` (Explicit user option selection wrapper around `QueryNormalizer`)
  - `app/website_queue.py` (In-memory multi-visitor job queue: capacity 11 = 1 active + 10 waiting)
  - `app/website_scope.py` (Pre-generation coverage gate)
- **Website Configs (`config/`):**
  - `config/website_response_language_v4.json` *(Required by `app/website_language.py`; `v1`–`v3` are older iterations)*
  - `config/website_sources.json` *(Required by `scripts/build_citizen_vercel.cjs` and website source tests)*
- **Frontend & Deployment Assets:**
  - `website/` (Entire directory: `index.html`, `app.js`, `styles.css`, `motion.js`, `motion.css`, `mark.svg`, `runtime-config.js`, `THIRD_PARTY.md`, `vendor/`, plus `README.md`, `VERCEL_DEPLOYMENT.md`)
  - `vercel.json`, `package.json`, `.vercelignore`
  - `scripts/build_citizen_vercel.cjs` (Static Vercel Build Output v3 builder)
  - `scripts/start_citizen_website.ps1` and `scripts/stop_citizen_public_demo.ps1`
- **Demo Regression Tests (keep if running demo QA checks):**
  - `tests/test_citizen_website.py`, `tests/test_website_language.py`, `tests/test_website_queue.py`, `tests/test_website_grounding.py`, `tests/test_website_qa_contract.py`
  - `scripts/test_citizen_website_browser.cjs`, `scripts/test_website_motion.cjs`

### ⚠️ CRITICAL LOCK: Files That Must Remain Byte-for-Byte Unmodified (Fail-Closed Hash Checks!)
When `app/website.py` starts, `registered_profile()` reads `experiments/t07-final-evaluation-v1/candidate_registration.json` and **aborts startup (`ValueError`)** if any SHA-256 hash mismatches. Do **NOT** delete or edit:
1. `experiments/t07-final-evaluation-v1/candidate_registration.json`
2. `app/pipeline.py` *(Even changing its default `ARTIFACT_DIR` breaks the registered SHA-256 hash! Leave it untouched and set `EBOSS_ARTIFACT_DIR` as an env var only if running `app.main` against the repaired corpus.)*
3. `src/query_normalizer.py`, `src/chunk_retriever.py`, `src/token_windows.py`
4. `config/normalization_intent_candidate.txt`
5. `data/municipal_dictionary_v1.json`
6. All 7 files inside `experiments/chapter3-table-repaired-development-v1/` (`corpus.json`, `bm25_index.pkl`, `faiss_index.bin`, `index_provenance.json`, `pipeline_manifest.json`, `source_pages.json`, `validation.json`)
7. All 5 PDFs inside `data/raw_charters/` *(Also verified against `config/website_sources.json` during Vercel builds!)*

### B. Legacy Local Chapter 3 UI Demo (`app.main:app`)
- Keep `app/main.py`, `app/pipeline.py`, `app/__init__.py`, and `app/static/index.html`.
- Keep `experiments/chapter3-step2-development/` if you want `app.main` to boot with zero environment variables (`app/pipeline.py` defaults to it so its hash stays frozen). Alternatively, run with `$env:EBOSS_ARTIFACT_DIR="experiments/chapter3-table-repaired-development-v1"`.

---

## 3. What NOT to Compromise for Final Manuscript PDF Reproduction

In addition to the frozen code/hash files above, **never delete** any of these datasets, evaluation archives, or Desktop sync files:

1. **Benchmarks (`data/`):**
   - `data/benchmark_scenarios_dev.json` (30 groups / 90 queries — Tables 3 & 4)
   - `data/benchmark_scenarios_test.json` (70 held-out groups / 210 queries — Tables 3 & 4)
2. **Evaluated Experiment Folders (`experiments/`):**
   - `experiments/chapter3-table-repaired-development-v1/` (Official 1,032-chunk corpus & indices — Table 1)
   - `experiments/table-repairs-staged-v2/` (Cleaned `source_pages.json`)
   - `experiments/t06-formal-development-validation-v3/` & `v4/` (Verified Dev reference answers)
   - `experiments/t07-development-grid-v1/` & `t07-development-grid-format-retry-v2/` (Simplex grid search: $J=0.9408$ at $\alpha^*=0.75, \beta^*=0.25, \gamma^*=0.00, K^*=3$ — Table 8 & Figure 3)
   - `experiments/t07-development-abc-v1/` & `t07-development-abc-ragas-{a,b,c}-v1/` (30-group Dev A/B/C runs — Figure 4)
   - `experiments/t07-final-evaluation-v1/` & `t07-final-ragas-{a,b,c}-v1/` (70-group / 210-query Held-Out Test runs `A/B/C/interactions.jsonl`, `per_query_metrics.csv`, `master_metrics.csv`, `matched_metrics.csv` — Tables 9–12 & Figures 5–6)
3. **Finalized October 30 Sync (`2_CRITICAL_SYNC_FROM_DESKTOP_THESIS_FOLDER/`):**
   - `FINAL_HUMAN_RATE_RAW_PACKETS/` (`R01-M1`..`R03-M2`: 1,320 real human expert ratings)
   - `Final-Human-Rate-Results-20261030/` (Tables 13–15: `analysis_results.json`, `descriptive_scores.csv`, `reliability.csv`, `paired_comparisons.csv`)
   - `m4_automated_and_figures/` (`m4_automated_statistical_summary.json` + final Figures 3–11)
   - `portable_scripts/` (`run_final_human_rate_audit.py`, `compute_m4_automated_stats.py`, `generate_all_m4_figures.py` — updated to use relative `REPO_ROOT` paths so they work on any machine)
4. **Core Pipeline Scripts (`scripts/`) & Unit Tests (`tests/`):**
   - Keep the 16 pipeline/evaluation scripts and 17 unit tests present in `1_CLEAN_REPOSITORY/scripts/` and `1_CLEAN_REPOSITORY/tests/` (plus your website tests listed in Section 2).

---

## 4. What IS Safe to Clean / Delete (Zero Compromise to Demos or Manuscript)

You can safely delete or move to an external archive folder (`~185 MB` of bloat) without affecting either demo or any Final Manuscript PDF number:

### 🚨 A. Dangerous / Outdated Results (DELETE or NEVER USE!)
1. **`experiments/t10-t12-human-analysis-v1/`** and **`outputs/team-handoff-20261029/`** & **`outputs/manuscript-closeout-20261028/`**  
   *Why:* Contain superseded October 28–29 human evaluation tables (`M1 = 3.76`, `M2 Rel = 2.28`) and pre-reconciliation 177-query drafts. The Final Manuscript PDF uses October 30 results (`M1 = 4.69`, `M2 Rel = 2.84`, `M2 Faith = 3.03`, $\alpha \in [0.808, 0.875]$).
2. **Loose CSVs directly in `experiments/` root:** `grid_search_dev_results.csv`, `t07_master_results_test.csv`, `t07_summary_by_config.csv`, `t12_significance_results.csv`  
   *Why:* Left over from the obsolete 647-chunk Milestone 3 run (e.g., `t07_summary_by_config.csv` lists Hit@3 = `0.619` instead of `0.6810`).
3. **Obsolete index files in `data/` root:** `data/eboss_corpus_chunks_v1.json`, `data/bm25_index.pkl`, `data/faiss_index.bin`, `data/Master_Candidate_Terms.xlsx`, `data/compiledictionary.py`  
   *Why:* Early 647-chunk Milestone 1 prototype; replaced by `experiments/chapter3-table-repaired-development-v1/`.

### 🧹 B. Bloated Intermediate Logs, Scratch Folders & Retries (Safe to Delete)
- **Root clutter:** `do not push folder/`, `output/`, `outputs/`, `png/`, `scrape/`, `text_extraction steps/`, loose `.pdf`/`.png` chart copies in repo root, and old markdown handoff logs (`1 Progress Retrospective.md`, `CLAUDE_HANDOFF.md`, `TEAM_START_HERE.md`, `t03.md`, `t05_completion.md`, `t06-t07.md`, `new t06-t07.md`, `progress present.md`, `We-have-built-the-research-prototyp.md`). *(Only delete `CLAUDE_HANDOFF.md` / `TEAM_START_HERE.md` if your team no longer reads them—no code imports them.)*
- **`experiments/` intermediate diagnostics (~50 folders):**
  - `bfp002-*`, `context-precision-calibration-*`, `context-precision-source-span-validation-v4`, `failed-judge-retry-v2`, `punctuation-context-precision-*`, `normalization-sparse-development-regression-v1`
  - `source-reference-review-*`, `source-review-manual-checks-v1`
  - `t06-context-precision-v2-integration-smoke`, `t06-harness-closeout-*`, `t06-ragas-format-retry-*`, `t06-ragas-null-diagnosis-v1`, `t06-t07-*`
  - `t07-faithfulness-retry-*`, `t07-independent-judge-review-v1`, `t07-methodology-reconciliation-v1`, `t07-paired-grid-*`
  - `t08-t09-expert-audit-v1` (29 MB), `t08-t09-expert-audit-v2-triple` (30 MB), `t08-t12-rater-preparation`
  - `website-language-fidelity-v1`, `website-language-fidelity-v2`
- **One-off patch/diagnostic scripts in `scripts/`:** `diagnose_*`, `patch_*`, `retry_*`, `recover_*`, `finalize_team_handoff.py`, `prepare_team_chapters.py`, `build_team_chapter_pdf.py`, `create_employee_meeting_packet.py`, `package_manuscript_drafts.py`, `qa_team_handoff.py`.

---

## 5. How to Sync `2_CRITICAL_SYNC_FROM_DESKTOP_THESIS_FOLDER/` Into Your Working Repo

From your cleaned working repo (keep your demo files from Section 2 + core files from Section 3):

1. **Add Final Human Audit Packets & Results into `experiments/`:**
   - Create `experiments/final-human-audit-20261030/`
   - Copy `2_CRITICAL_SYNC_FROM_DESKTOP_THESIS_FOLDER/FINAL_HUMAN_RATE_RAW_PACKETS` $\rightarrow$ `experiments/final-human-audit-20261030/raw_packets`
   - Copy `2_CRITICAL_SYNC_FROM_DESKTOP_THESIS_FOLDER/Final-Human-Rate-Results-20261030` $\rightarrow$ `experiments/final-human-audit-20261030/results`
2. **Add Portable Statistical & Figure Scripts into `scripts/`:**
   - Copy all 3 scripts from `2_CRITICAL_SYNC_FROM_DESKTOP_THESIS_FOLDER/portable_scripts/` (`run_final_human_rate_audit.py`, `compute_m4_automated_stats.py`, `generate_all_m4_figures.py`) into `scripts/`.
3. **Add Final Summary & Figures into `results/`:**
   - Copy `2_CRITICAL_SYNC_FROM_DESKTOP_THESIS_FOLDER/m4_automated_and_figures/` $\rightarrow$ `results/`.

*(Keep `FINAL_HUMAN_RATE_RAW_PACKETS` gitignored via `.gitignore` if your repository policy keeps raw human rater files private, while still keeping them locally when running `run_final_human_rate_audit.py`.)*

---

## 6. File-by-File Map to the Final Manuscript PDF

| Final Manuscript Section / Table / Figure | Exact Repository File Path |
| :--- | :--- |
| **Ch. 3 §3.2.1 & Table 1:** 1,032-Chunk Corpus (120-token window, 20-token overlap, 5 eBOSS offices) | `src/token_windows.py`<br>`data/raw_charters/*.pdf`<br>`experiments/chapter3-table-repaired-development-v1/{corpus.json,bm25_index.pkl,faiss_index.bin}` |
| **Ch. 3 §3.2.2 & Table 2:** 50-Entry (239-Expression) Municipal Dictionary | `data/municipal_dictionary_v1.json` |
| **Ch. 3 §3.2.3 & Tables 3–4:** 100 Scenario Groups (300 Queries: 30 Dev / 70 Held-Out Test) | `data/benchmark_scenarios_dev.json` (30 groups / 90 queries)<br>`data/benchmark_scenarios_test.json` (70 groups / 210 queries) |
| **Ch. 3 §3.2.4:** Two-Stage Query Normalizer & Polysemy Gatekeeper | `src/query_normalizer.py`, `config/normalization_intent_candidate.txt` |
| **Ch. 3 §3.2.5–3.2.6:** Tri-Signal Hybrid Retriever ($\alpha=0.75, \beta=0.25, \gamma=0.00, K=3$) | `src/chunk_retriever.py`, `config/pipeline_manifest.json` |
| **Ch. 4 §4.1, Table 8, & Figure 3:** 30-Group ($n=90$) Simplex Grid Search ($J=0.9408$) | `experiments/t07-development-grid-v1/context_precision_grid.json` |
| **Ch. 4 §4.1 & Figure 4:** 30-Group ($n=90$) Development A/B/C Comparison | `experiments/t07-development-abc-v1/comparison_metrics.csv` |
| **Ch. 4 §4.2, Tables 9–12, & Figures 5–6:** 70-Group ($n=210$) Held-Out Test Results & Stats | `experiments/t07-final-evaluation-v1/{A,B,C}/interactions.jsonl`<br>`experiments/t07-final-evaluation-v1/{per_query_metrics.csv,master_metrics.csv,matched_metrics.csv}`<br>`results/m4_automated_statistical_summary.json` |
| **Ch. 4 §4.3, Tables 13–15, Figures 7–11, & Appendix D:** 3-Rater Double-Blind Human Audit | `experiments/final-human-audit-20261030/raw_packets/R0{1,2,3}-M{1,2}/`<br>`experiments/final-human-audit-20261030/results/{descriptive_scores.csv,reliability.csv,paired_comparisons.csv,analysis_results.json}` |

---

## 7. Commands to Verify Manuscript Numbers AND Run the Polished Demos

### A. Reproduce Final Manuscript Results & Run Core Tests
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install krippendorff scipy matplotlib

# 1. Verify the 1,032-chunk Citizens' Charter corpus, BM25, and FAISS indices
python -B scripts/verify_chapter3_retrieval.py --artifacts experiments/chapter3-table-repaired-development-v1

# 2. Reproduce Human Expert Evaluation Tables (Tables 13, 14, 15)
python -B scripts/run_final_human_rate_audit.py

# 3. Reproduce Automated Held-Out Test Stats (Tables 9, 10, 11, 12)
python -B scripts/compute_m4_automated_stats.py

# 4. Regenerate Chapter 4 Publication Figures (PDF & 300-DPI PNG)
python -B scripts/generate_all_m4_figures.py

# 5. Core unit tests + website demo contract tests
python -m pytest tests/test_token_windows.py tests/test_chunk_retriever.py tests/test_normalization_fidelity.py
python -m unittest tests.test_citizen_website tests.test_website_language tests.test_website_queue -v
```

### B. Run the Polished Live Demos (Do NOT add `--workers`)
```powershell
# Citizen Website Demo (requires local Ollama running eboss-mistral with registered digest)
python -m uvicorn app.website:app --host 127.0.0.1 --port 8000

# Legacy Chapter 3 Development UI Demo (optional)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

