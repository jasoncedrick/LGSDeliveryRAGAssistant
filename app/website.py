"""Citizen website using B retrieval with a separate response-language revision.

Run: python -m uvicorn app.website:app --host 127.0.0.1 --port 8000
No query history is written to disk by this entry point.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path, PureWindowsPath
from urllib.parse import urlsplit, urlunsplit
from typing import Literal

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / 'website'
ARTIFACTS = ROOT / 'experiments/chapter3-table-repaired-development-v1'
REGISTRATION = ROOT / 'experiments/t07-final-evaluation-v1/candidate_registration.json'
LOGGER = logging.getLogger(__name__)
SOURCE_NAMES = {
    'business': ('Business Bureau', 'Business Bureau CGD_Citizen Charter 2026_VOL.I & II.pdf'),
    'treasury': ("City Treasurer's Office", "City Treasurer's CGD_Citizen Charter 2026_VOL.I & II-2.pdf"),
    'building': ('Office of the City Building Official', 'OCBD Pages from CGD_Citizen Charter 2026_VOL.I & II-2.pdf'),
    'fire': ('Bureau of Fire Protection', 'BFP-CITIZENS-CHARTER-2022.pdf'),
    'planning': ('City Planning and Development Office', 'City Planning CGD_Citizen Charter 2026_VOL.I & II-3.pdf'),
}


def registered_profile():
    """Fail closed if essential files differ from the registered implementation."""
    candidate = json.loads(REGISTRATION.read_text(encoding='utf-8'))
    prefixes = ('app\\pipeline.py', 'src\\query_normalizer.py', 'src\\chunk_retriever.py',
                'src\\token_windows.py', 'config\\normalization_intent_candidate.txt',
                'data\\municipal_dictionary_v1.json', 'experiments\\chapter3-table-repaired-development-v1\\')
    checked = {}
    for relative, expected in candidate['file_hashes'].items():
        if not relative.startswith(prefixes):
            continue
        path = ROOT.joinpath(*PureWindowsPath(relative).parts)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Registered runtime file differs: {relative}')
        checked[relative] = actual
    if len(checked) < 10 or candidate['k'] != 3 or candidate['weights_B_C'] != [.75, .25, 0.0]:
        raise ValueError('Unexpected registered website profile')
    # PDFs exposed to visitors must also match the evaluated source set.
    validation = json.loads((ARTIFACTS/'validation.json').read_text(encoding='utf-8'))
    expected_sources = {s['file_source']: s['sha256'] for s in validation['source_pdfs']}
    for _, filename in SOURCE_NAMES.values():
        if hashlib.sha256((ROOT/'data/raw_charters'/filename).read_bytes()).hexdigest() != expected_sources[filename]:
            raise ValueError('Source PDF differs from evaluated source')
    return candidate, checked


def create_pipeline():
    candidate, hashes = registered_profile()
    import numpy as np
    from app.website_language import WebsitePipeline, PROMPT, PROMPT_SHA256

    # Isolate the registered prompt per module instead of mutating the legacy
    # normalizer's global prompt in a multi-threaded web process.
    spec = importlib.util.spec_from_file_location('website_registered_normalizer', ROOT/'src/query_normalizer.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.BASELINE_SYSTEM_PROMPT = (ROOT/'config/normalization_intent_candidate.txt').read_text(encoding='utf-8')
    pipeline = WebsitePipeline(artifacts_dir=ARTIFACTS, corpus_path=ARTIFACTS/'corpus.json',
                        dictionary_path=ROOT/'data/municipal_dictionary_v1.json')
    if pipeline.model_name not in (candidate['model'], candidate['model']+':latest'):
        raise ValueError('Use the registered eboss-mistral model for this website profile')
    if pipeline.num_ctx != 8192 or pipeline.answer_tokens != 1536:
        raise ValueError('Generation settings differ from registration')
    import os
    if os.environ.get('EBOSS_TOP_K', '3') != '3':
        raise ValueError('This website profile requires K=3')
    pipeline.normalizer = module.QueryNormalizer(
        str(ROOT/'data/municipal_dictionary_v1.json'), ollama_api_url=pipeline.endpoint,
        model_name=pipeline.model_name, enable_context_rules=False, enable_fidelity_contract=False)
    pipeline.top_k = 3
    pipeline.retriever.weights = np.asarray(candidate['weights_B_C'], dtype=float)
    pipeline.website_profile = {'configuration': 'B', 'k': 3, 'weights': candidate['weights_B_C'],
                                'model_digest': candidate['model_digest'], 'checked_hashes': hashes,
                                'website_prompt_version':PROMPT['version'], 'language_prompt_sha256':PROMPT_SHA256}
    return pipeline


class Runtime:
    def __init__(self, factory=create_pipeline):
        self.factory = factory
        self.pipeline = None
        self.error = None
        self.query_lock = threading.Lock()
        self.model_lock = threading.Lock()
        self.model_cache = (0.0, None)

    def load(self):
        try:
            self.pipeline = self.factory()
            LOGGER.info('Citizen website ready: B retrieval, K=3, 120/20 windows; website language prompt v2')
        except Exception:
            self.error = 'The source service needs attention. Please contact the researcher.'
            LOGGER.exception('Website runtime could not load')

    def model_state(self):
        with self.model_lock:
            now = time.monotonic()
            if now-self.model_cache[0] < 10 and self.model_cache[1]:
                return self.model_cache[1]
            parts = urlsplit(self.pipeline.endpoint)
            tags = urlunsplit((parts.scheme, parts.netloc, '/api/tags', '', ''))
            try:
                response = requests.get(tags, timeout=2)
                response.raise_for_status()
                models = response.json()['models']
                expected = self.pipeline.website_profile['model_digest']
                name = self.pipeline.model_name
                model = next((m for m in models if m.get('name') in (name, name+':latest')), None)
                state = 'ready' if model and model.get('digest') == expected else 'model_mismatch'
            except (requests.RequestException, ValueError, KeyError, TypeError):
                state = 'model_offline'
            self.model_cache = (now, state)
            return state

    def health(self):
        if self.error:
            return {'status':'unavailable', 'message':self.error}
        if self.pipeline is None:
            return {'status':'starting', 'message':'Loading the charter sources. Please wait a moment.'}
        state = self.model_state()
        messages = {'ready':'Ready to help', 'model_offline':'The answer service is offline. You can still browse the charters.',
                    'model_mismatch':'The registered answer model is not available. You can still browse the charters.'}
        return {'status':state, 'message':messages[state]}


class CitizenQuestion(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    response_language: Literal['auto','english','taglish','bislish'] = 'auto'


def public_result(result):
    """Serve the answer and source evidence without exposing internal diagnostics."""
    citations=[]
    by_filename={v[1]:k for k,v in SOURCE_NAMES.items()}
    for c in result.get('citations',[]):
        source_id=by_filename.get(c.get('file_source'))
        page=c.get('pdf_relative_page')
        citations.append({k:c.get(k) for k in ['citation','file_source','source_page','pdf_relative_page','text']})
        citations[-1]['source_url']=(f'/sources/{source_id}.pdf'+(f'#page={page}' if isinstance(page,int) and page>0 else '')) if source_id else None
    return {'status':result['status'], 'answer':result.get('answer',''),
            'clarification_prompt':result.get('clarification_prompt'), 'citations':citations,
            'citation_labels_valid':result.get('diagnostics',{}).get('citation_labels_valid'),
            'response_language':result.get('diagnostics',{}).get('response_language'),
            'website_prompt_version':result.get('diagnostics',{}).get('website_prompt_version'),
            'latency_seconds':result.get('latency_seconds',0)}


def create_app(runtime=None, start_runtime=True, allowed_origins=None):
    runtime=runtime or Runtime()

    @asynccontextmanager
    async def lifespan(app):
        if start_runtime:
            threading.Thread(target=runtime.load, name='citizen-retriever-loader', daemon=True).start()
        yield

    app=FastAPI(title='eBOSS Citizen Assistant',lifespan=lifespan,docs_url=None,redoc_url=None)
    app.state.runtime=runtime
    if allowed_origins is None:
        allowed_origins=[s.strip() for s in os.environ.get('EBOSS_ALLOWED_ORIGINS',
            'https://davaoragcitizencharter.com,https://www.davaoragcitizencharter.com,https://davaoragcitizencharter.vercel.app').split(',') if s.strip()]
    if '*' in allowed_origins:
        raise ValueError('Specify exact citizen frontend origins; wildcard CORS is not supported')
    app.add_middleware(CORSMiddleware,allow_origins=allowed_origins,
                       allow_methods=['GET','POST'],allow_headers=['Content-Type'],
                       allow_credentials=False,expose_headers=['Retry-After'])

    @app.middleware('http')
    async def response_headers(request,call_next):
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self'"
        if request.url.path.startswith(('/api/','/health')):
            response.headers['Cache-Control']='no-store'
        return response

    @app.get('/health')
    def health():
        return runtime.health()

    @app.get('/api/sources')
    def sources():
        return [{'id':key,'office':office,'filename':filename,'url':f'/sources/{key}.pdf'}
                for key,(office,filename) in SOURCE_NAMES.items()]

    @app.get('/sources/{source_id}.pdf')
    def source_pdf(source_id:str):
        if source_id not in SOURCE_NAMES:
            raise HTTPException(404,'Source not found.')
        p=ROOT/'data/raw_charters'/SOURCE_NAMES[source_id][1]
        if not p.is_file():
            raise HTTPException(404,'Source file unavailable.')
        return FileResponse(p,media_type='application/pdf')

    @app.post('/api/query')
    def query(req:CitizenQuestion):
        question=req.query.strip()
        if not question:
            raise HTTPException(422,'Please enter a question.')
        state=runtime.health()
        if state['status']!='ready':
            raise HTTPException(503,state['message'])
        if not runtime.query_lock.acquire(blocking=False):
            raise HTTPException(429,'The assistant is helping someone else. Please try again shortly.',headers={'Retry-After':'15'})
        from app.website_language import REQUESTED_LANGUAGE
        language_token=REQUESTED_LANGUAGE.set(req.response_language)
        try:
            start=time.monotonic()
            result=runtime.pipeline.handle_query(question)
            result['latency_seconds']=round(time.monotonic()-start,2)
            return public_result(result)
        except Exception:
            LOGGER.exception('Citizen request failed')
            raise HTTPException(503,'The assistant could not complete this request. Please try again.')
        finally:
            REQUESTED_LANGUAGE.reset(language_token)
            runtime.query_lock.release()

    app.mount('/assets',StaticFiles(directory=STATIC),name='website_assets')

    @app.get('/')
    def index():
        return FileResponse(STATIC/'index.html')

    return app


app=create_app()
