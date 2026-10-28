# Vercel citizen website deployment

- Repository: `jasoncedrick/LGSDeliveryRAGAssistant`
- Deployment branch: `deploy/vercel-davaoragcitizencharter-20261028`
- Vercel team: `jason124rabanes-6549s-projects`
- Project: `davaoragcitizencharter`
- Requested domain: `davaoragcitizencharter.com` (Vercel registrar/DNS)

The initial production deployment is live at **https://davaoragcitizencharter.com**. `www.davaoragcitizencharter.com` redirects to it. The Vercel project tracks the deployment branch above for production; the repository's `main` branch remains unchanged. Public HTTP access does not require a Vercel login.

Vercel serves the static website and five hash-verified charter PDFs. It does not host Python, Ollama, embeddings, private research material or evaluation data. Browser requests for `/health`, `/api/jobs` and `/api/jobs/status` go directly to the configured PC backend. The older `/api/query` route remains available for compatibility. Source links stay on Vercel and remain readable when the PC is unavailable.

## Build and configuration

`vercel.json` selects Other/no framework, no dependency installation, and `node scripts/build_citizen_vercel.cjs`. The script emits Vercel Build Output API v3 under ignored `.vercel/output/`. `PUBLIC_RAG_API_ORIGIN` is required in Production and Preview. It is intentionally public and must contain only an HTTPS origin without a trailing slash. The build fails for absent/invalid origins or changed source PDFs.

The generated content security policy allows connections only to the website itself and that backend origin. No Vercel proxy or function is used for inference. The backend enables CORS for exact allowed website origins, with no cookies or wildcard permission. CORS controls browsers; it is not API authentication.

The initial backend is the existing temporary Cloudflare Quick Tunnel. It works while the PC, FastAPI, Ollama and tunnel remain running. Restarting that tunnel changes its address: update the Vercel environment value and redeploy. A permanent `api.davaoragcitizencharter.com` endpoint is not yet configured. Do not alter Vercel nameservers or claim the backend is permanently hosted. Long synchronous requests remain subject to tunnel/network timeouts.

Automatic startup of the PC services has not been configured as part of this deployment. The current backend logs are `tmp/citizen-website/server-vercel.log` and `server-vercel.out.log`; use `Get-Content <path> -Wait` in PowerShell to follow them. Keep Ollama, the website backend, and the existing tunnel running. After a PC reboot, start the backend with `scripts/start_citizen_website.ps1`, restart the tunnel, and update its public origin if the temporary address changed. Do not publish local `.env.local` or `.vercel` credentials/state.

Local entrypoint still works with same-origin `website/runtime-config.js`. Hosted builds replace that file, leaving retrieval/query content unchanged. `EBOSS_ALLOWED_ORIGINS` can override the backend list with comma-separated exact origins. Add a specific preview origin only when it needs real API access; arbitrary previews are not automatically allowed.

## Publication boundaries and methodology

The Git branch carries current public project code/evidence. `.gitignore` excludes credentials, Vercel state, private ratings, received returns, and temporary files. `.vercelignore` restricts uploaded build inputs further. The build publishes an explicit asset allowlist, source catalog and the five PDFs only.

Chapter 3 section 3.2.6 describes a FastAPI web application and loaded offline indices. This deployment preserves the existing pipeline, corpus, model settings and citations. Its split Vercel/PC hosting is an operational adaptation: it does not fulfill the original manuscript's fully cloud-hosted backend description. The existing post-study language prompt and known quality limitations remain documented separately. No frozen results are regenerated or relabeled.

## Verification

Run `python -m unittest discover -s tests -p "test_*website*.py" -v` for API/contract/CORS/source checks. Browser scripts `scripts/test_citizen_website_browser.cjs` and `scripts/test_website_motion.cjs` accept `WEBSITE_TEST_URL` and use synthetic responses. Deployment-specific evidence is recorded in `website/VERCEL_QA.json` after publication.

Production checks on 28 October 2026 confirmed unauthenticated page/source access, the www redirect, backend readiness and exact-origin CORS. The live question check reached the backend but received HTTP 429 because its single inference slot was occupied; a successful generated answer was not verified in this deployment check. The site keeps the question for retry. Fifteen API/unit tests, sixteen synthetic browser checks and eleven motion/accessibility checks passed. The startup send button now remains disabled until backend readiness is confirmed. These checks establish deployment behavior, not answer factuality.

## Multi-visitor queue ? 28 October 2026

The current website accepts up to 11 outstanding questions (one active plus ten waiting) and processes them in arrival order. It posts each question once to `/api/jobs`, then polls `/api/jobs/status` every two seconds using an unguessable ticket in the POST body. Visitors see the number of questions ahead and the running state. Brief polling failures retry the status lookup, never the question submission. A full queue returns 429 with a 60-second retry hint.

This is an operational scheduling change around the existing Chapter 3 FastAPI pipeline. It introduces no additional LLM call, live judge, prompt change, altered retrieval or model parallelism. The original synchronous route shares the same model lock. Use exactly one Uvicorn process: this queue is local memory, not shared across workers or machines. Do not add `--workers` to the launcher.

Waiting questions expire after five minutes. Completed/failed results remain in memory for up to ten minutes, with at most 100 terminal records retained (older ones can be removed earlier). Tickets are private bearer receipts, not user accounts; there is no result-list endpoint and ticket bodies are not included in Uvicorn access logs. No question/answer history is written to disk by the queue. Keep the browser page open: refresh loses its ticket, and a backend restart loses pending questions/results. There is no automatic resubmission or cancellation of model generation when a browser closes. The browser allows up to fifteen minutes for submission/polling, while individual model request limits are unchanged.

A queue increases simultaneous submission capacity; it does not increase tokens per second. Real simultaneous inference needs a separate hardware/throughput assessment. The temporary PC/tunnel availability limitations above still apply. Deployment restart may interrupt an existing question.
