"""
FastAPI backend for the eBOSS Dictionary-Assisted Hybrid RAG Assistant
(Thesis Sec 3.2.6: Deploy the Web Application).

Pipeline sequence per request: dictionary hashmap lookup and lexical
injection -> LLM-based query normalization -> hybrid BM25 and FAISS
retrieval with weighted fusion -> prompt construction with retrieved
context -> grounded LLM response generation. Indices and models are loaded
once at startup (see app/pipeline.py). Each interaction is archived
asynchronously via a BackgroundTask (does not add to response latency) to
experiments/web_interactions_log.jsonl, to support the offline RAGAS
benchmarking and human expert auditing suites described in Sec 3.2.6.

Run locally:
    uvicorn app.main:app --reload --port 8000
Then open http://localhost:8000 in a browser.

Deployment note (free-tier hosting, Sec 3.2.6): the FastAPI app itself
deploys fine to a free-tier host (Render, Railway, Fly.io, etc.) -- it's
lightweight. The actual Mistral 7B model via Ollama is the hard part: most
free web-hosting tiers don't have the RAM/compute to run a 7B model. The
OLLAMA_ENDPOINT env var below lets this backend point at Ollama running
anywhere (e.g. your own PC, tunneled with something like ngrok/Cloudflare
Tunnel) without touching the code -- worth deciding before you actually
deploy publicly.
"""

import json
import os
import time
import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.pipeline import Pipeline

ARCHIVE_PATH = "experiments/web_interactions_log.jsonl"

_state = {"pipeline": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[*] Loading pipeline (indices, embedder, normalizer)...")
    _state["pipeline"] = Pipeline()
    print("[+] Pipeline ready.")
    yield
    _state["pipeline"] = None


app = FastAPI(title="eBOSS Dictionary-Assisted Hybrid RAG Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    raw_query: str
    normalized_query: str
    normalization_status: str
    clarification_prompt: Optional[str] = None
    injected_terms: list
    retrieved_chunk_ids: list
    retrieved_chunks: list
    answer: str
    tokens_generated: int
    latency_seconds: float


def archive_interaction(record: dict):
    os.makedirs(os.path.dirname(ARCHIVE_PATH), exist_ok=True)
    record["archived_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    with open(ARCHIVE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


@app.post("/api/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest, background_tasks: BackgroundTasks):
    pipeline: Pipeline = _state["pipeline"]
    t0 = time.time()
    result = pipeline.handle_query(req.query)
    result["latency_seconds"] = round(time.time() - t0, 3)

    # Archive asynchronously -- runs after the response is sent, never adds
    # to citizen-facing latency (Sec 3.2.6).
    background_tasks.add_task(archive_interaction, dict(result))

    return result


@app.get("/health")
def health():
    return {"status": "ok", "pipeline_loaded": _state["pipeline"] is not None}


STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
