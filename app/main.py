"""Local web API for the Chapter 3 chunk RAG development pipeline.

Run from the project root: python -m uvicorn app.main:app --port 8000
Open http://127.0.0.1:8000. Startup loads the paired development indices once;
Ollama is called during normalization and answer generation.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.pipeline import Pipeline, ROOT

LOGGER = logging.getLogger(__name__)
_archive_lock = threading.Lock()
archive_value = Path(os.environ.get('EBOSS_ARCHIVE_PATH', 'experiments/chapter3_web_interactions.jsonl'))
ARCHIVE_PATH = archive_value if archive_value.is_absolute() else ROOT/archive_value
_state = {'pipeline': None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    LOGGER.info('Loading Chapter 3 chunk retrieval development pipeline')
    _state['pipeline'] = Pipeline()
    try:
        yield
    finally:
        _state['pipeline'] = None


app = FastAPI(title='Davao City eBOSS Assistant', lifespan=lifespan)


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class QueryResponse(BaseModel):
    status: str
    raw_query: str
    normalized_query: Optional[str] = None
    normalization_status: str
    clarification_prompt: Optional[str] = None
    injected_terms: list[str] = Field(default_factory=list)
    resolved_terms: list[dict[str, Any]] = Field(default_factory=list)
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    retrieved_chunks: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    ranked_chunks: list[dict[str, Any]] = Field(default_factory=list)
    retrieval_mode: str = 'chapter3_chunks'
    top_k: int
    retrieval_weights: dict[str, float] = Field(default_factory=dict)
    candidate_count: int = 0
    artifact_hashes: dict[str, str] = Field(default_factory=dict)
    pipeline_status: str = 'development_not_frozen'
    source_fidelity_status: str = 'NOT_REVIEWED'
    context_chars: int = 0
    corpus_sha256: Optional[str] = None
    retrieval_started: bool = False
    generation_started: bool = False
    answer: str
    tokens_generated: int = 0
    latency_seconds: float = 0.0
    experimental: bool = True
    error: Optional[dict[str, str]] = None


def archive_interaction(record: dict):
    record = dict(record)
    record['archived_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        line = json.dumps(record, ensure_ascii=False) + '\n'
        with _archive_lock:
            ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with ARCHIVE_PATH.open('a', encoding='utf-8') as handle:
                handle.write(line)
    except OSError:
        LOGGER.exception('Could not archive interaction')


@app.post('/api/query', response_model=QueryResponse)
def query_endpoint(req: QueryRequest, background_tasks: BackgroundTasks):
    if not req.query.strip():
        raise HTTPException(status_code=422, detail='Please enter a question.')
    pipeline = _state['pipeline']
    if pipeline is None:
        raise HTTPException(status_code=503, detail='The assistant is starting. Please try again shortly.')
    started = time.perf_counter()
    result = pipeline.handle_query(req.query)
    result['latency_seconds'] = round(time.perf_counter() - started, 3)
    background_tasks.add_task(archive_interaction, dict(result))
    return result


@app.get('/health')
def health():
    loaded = _state['pipeline'] is not None
    return {'status': 'ok' if loaded else 'starting', 'pipeline_loaded': loaded,
            'retrieval_mode': 'chapter3_chunks', 'pipeline_status': 'development_not_frozen',
            'top_k': getattr(_state['pipeline'], 'top_k', None),
            'source_fidelity_status': getattr(_state['pipeline'], 'source_fidelity_status', 'NOT_REVIEWED')}


STATIC_DIR = Path(__file__).resolve().parent/'static'
app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')


@app.get('/')
def index():
    return FileResponse(STATIC_DIR/'index.html')
