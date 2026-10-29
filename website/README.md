# Citizen website

This is the citizen-facing interface for the LGSDeliveryRAGAssistant research prototype. It includes a responsive chat, office-topic suggestions, compact source names, a source library and project information. Questions run through the real local RAG service; the UI contains no canned answers.

## Current review branch

The latest 29 October display revision uses a small source-name line under each answer, with quiet citation markers. It shows no PDF buttons, page numbers, raw filenames or passage quotations in the answer. The separate source library remains available. Retrieved context, source text in archived evaluations, and formal expert audit packets are unchanged. The lightweight reference frontend is live from commit 9069b3d. This checkout also contains an unpromoted Python grounding candidate: software checks pass, but factual and language quality failed. See [the team guide](../TEAM_START_HERE.md). Do not restart the public backend from this branch as a production upgrade.

## Run for local development only

From the clean project root, with the project's Python environment and cached model dependencies:

```powershell
Set-Location D:\thesis\LGSDeliveryRAGAssistant-clean
D:\thesis\venv\Scripts\python.exe -m uvicorn app.website:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Ollama must expose `eboss-mistral` or `eboss-mistral:latest` at `http://localhost:11434/api/generate`. The model digest must match the registered evaluation model. An existing model server can be reused; do not launch another batch evaluation. `OLLAMA_ENDPOINT` can point to a separately managed compatible Ollama server. Do not put credentials into committed files.

The site loads its retriever in the background. Its status distinguishes loading, ready, model offline and model mismatch. The page and source library remain usable while the model is unavailable. The source loader verifies the registered implementation/corpus/index hashes and the PDF hashes before accepting questions.

## Methodology alignment

- Uses the registered B configuration: query-specific dictionary injection, reviewed normalization prompt, chunk-level BM25/FAISS fusion 0.75/0.25 and dictionary retrieval boost 0, K=3.
- Uses `experiments/chapter3-table-repaired-development-v1/` with the original source-token 120/20 windows and matching indices. It does not rebuild or retune them.
- Preserves the frozen answer prompt on disk while the website adapter uses its separately versioned generation instruction; this is a post-study prompt change. Mistral generation settings remain: temperature 0, top-p 0, context 8192, maximum prediction 1536. Normalization remains capped at 150 tokens.
- Loads the reviewed prompt in an isolated normalizer module, without modifying the frozen normalizer source or its legacy global prompt.
- Keeps `app/main.py`, `app/pipeline.py`, frozen source code and evaluation records intact. This is a new opt-in `app.website` entry point; the historical app defaults remain unchanged.
- Clarification and incomplete output are shown explicitly. Citation labels identify the source names; they are not clickable or a guarantee of factual correctness. The offline RAGAS judge is not called by the website.
- Service-topic buttons change suggested questions only. They do not silently filter retrieval, inject office context or create a new routing method.
- Each request is independent; the UI does not inject conversational history into the registered prompt.

The model's installed digest is checked before queries (with a short readiness cache). Numerical reproducibility across runtimes is not guaranteed by the digest alone. Essential registered input changes fail readiness rather than silently changing the evaluated profile.

## Privacy and operational behavior

This entry point does not archive questions or answers to server history. The conversation lives in the open browser page and is cleared by New question or reload. Web-server or hosting infrastructure may retain access logs. Keep private citizen identifiers out of public demos.

Only five allowlisted charter PDFs are exposed. No filesystem path supplied by a visitor is used to choose a source file. Responses contain answer text and source evidence, not raw normalization diagnostics. The UI renders model text as text, not executable HTML. Up to eleven outstanding questions are accepted through the job queue and processed one at a time. The browser polls its private ticket for waiting, running and completion states. Source and model errors remain explicit.

See [the language revision record](LANGUAGE_REVISION.md) for the automatic language selection, manual override, test evidence, and limitations.

## Tests

The presentation layer also uses locally hosted GSAP/Lenis and React Bits-inspired adaptations. See [third-party notices and methodology boundaries](THIRD_PARTY.md). Motion can be switched off and respects the device reduced-motion setting. Chat scrolling remains native. Run `node scripts/test_website_motion.cjs` for targeted presentation checks; it makes no model calls.

```powershell
D:\thesis\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*website*.py" -v
node scripts/test_citizen_website_browser.cjs
```

Browser checks use synthetic fixtures and no model calls. They require a running website server and Playwright/Chrome. Set `AUDIT_PLAYWRIGHT_PATH`, `AUDIT_BROWSER` or `WEBSITE_TEST_URL` if the local paths differ. Test artifacts go to ignored `tmp/citizen-website/`.

## Going live and adding a domain

The FastAPI service, cached embedding model, paired indices and Ollama model must be reachable together. GitHub stores the code and evidence; GitHub Pages cannot run this Python/model backend. A domain supplies a stable address, not model hosting.

For a temporary demonstration, a managed HTTPS tunnel can expose this PC's website while the server, Ollama and PC remain running. Such a URL is temporary and is not an always-on deployment. For continuous citizen use, provision an appropriate persistent server/model endpoint, a managed service process, HTTPS and operational controls appropriate to expected traffic. Point the purchased domain at that deployment only after the hosting destination is selected. Do not expose Ollama's model-management API directly to the public internet.

The citizen frontend has been published on Vercel at `davaoragcitizencharter.com`, with the answer backend on the researcher's PC through a temporary Cloudflare Quick Tunnel. The domain does not keep the PC or model online. Local deployment records remain under ignored `tmp/`; check the deployed frontend's configured backend origin before using any older tunnel record. This is a temporary demonstration. The lightweight reference frontend is live; the Python backend remains on its earlier release. See [Cloudflare's Quick Tunnel documentation](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/) for the temporary-URL and availability limitations.

The current background demo writes startup/errors to `tmp/citizen-website/server-language-v2.log`, HTTP requests to `tmp/citizen-website/server-language-v2.out.log`, and tunnel progress to `tmp/citizen-website/tunnel.log`. Follow any of these with `Get-Content <path> -Wait`. For later foreground startup use `scripts/start_citizen_website.ps1`. To stop only the public tunnel, run `scripts/stop_citizen_public_demo.ps1`; it checks the recorded process identity before stopping it. Restarting a Quick Tunnel produces a different address.

Always-on hosting remains a separate selection. Do not describe the prototype as an official city service or as certified for unsupervised transactions. The first operational smoke request returned HTTP 200 with three citations in about 56 seconds, but its answer mixed services; the test verifies connectivity, not faithful answer quality. That outcome was retained instead of tuning the frozen pipeline to the smoke question.
