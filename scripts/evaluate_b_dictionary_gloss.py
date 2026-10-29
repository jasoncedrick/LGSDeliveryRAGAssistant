"""One-entry development experiment; reuse only input-equivalent normalizations."""
import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_b_fidelity_candidate import PROMPT, fidelity_flags, read, lines, sha
from src.query_normalizer import QueryNormalizer

PARENT = ROOT / 'experiments/b-fidelity-development-20261029-v2'
OUT = ROOT / 'experiments/b-dictionary-bayad-development-20261029-v1'
ARCHIVE = ROOT / 'experiments/t07-development-abc-v1'
ART = ROOT / 'experiments/chapter3-table-repaired-development-v1'


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    p = argparse.ArgumentParser(); p.add_argument('--stage', choices=['normalize', 'retrieve'], required=True); args = p.parse_args()
    base = read(OUT / 'dictionary.before.json'); revised = read(OUT / 'dictionary.candidate.json')
    assert set(base) == set(revised)
    assert [k for k in base if base[k] != revised[k]] == ['bayad']
    assert {k:v for k,v in base['bayad'].items() if k != 'verified_english_definition'} == {k:v for k,v in revised['bayad'].items() if k != 'verified_english_definition'}
    source = lines(PARENT / 'candidate_normalizations.jsonl')
    parent = {(r['configuration'], r['record_id']): r for r in source}
    assert len(parent) == len(source) == 180
    records = {c: lines(ARCHIVE / c / 'interactions.jsonl') for c in 'BC'}
    groups = read(ROOT / 'experiments/t06-formal-development-validation-v4/development_groups.derived.json')
    assert len(groups) == 30 and all(g['split'] == 'development' for g in groups)
    for rs in records.values():
        assert len(rs) == 90 and len({r['record_id'] for r in rs}) == 90
        assert {r['question_group_id'] for r in rs} == {g['group_id'] for g in groups}
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), PARENT/'protocol.json', PARENT/'candidate_normalizations.jsonl', OUT/'dictionary.before.json', OUT/'dictionary.candidate.json', OUT/'source_review.json']}
    protocol = {'held_out_accessed': False, 'freeze': False, 'source_hashes': hashes,
        'scope': 'Single-entry lexical simplification, full 90-query development regression',
        'parent_prompt_unchanged': True, 'reuse': 'Reuse parent only when effective glossary plus ambiguity inputs are identical; C injection remains disabled',
        'dictionary_scope': 'Normalization only. Retrieval key set unchanged; no corpus/index change.',
        'weights': [.75,.25,0], 'k':[3,5], 'generation_changes': False,
        'selection': 'Hit/MRR are diagnostic; no promotion without context precision and answer-quality evidence',
        'maximum_workers':1}
    if (OUT/'protocol.json').exists():
        assert read(OUT/'protocol.json') == protocol
    else: write('protocol.json',protocol)
    old = QueryNormalizer(str(OUT/'dictionary.before.json'), enable_context_rules=False)
    new = QueryNormalizer(str(OUT/'dictionary.candidate.json'), enable_context_rules=False)
    path = OUT/'candidate_normalizations.jsonl'
    cached = lines(path) if path.exists() else []
    done = {(r['configuration'],r['record_id']):r for r in cached}; assert len(done)==len(cached)
    if args.stage == 'normalize':
        import requests
        model = next(m for m in requests.get('http://localhost:11434/api/tags',timeout=10).json()['models'] if m['name']=='eboss-mistral:latest')
        assert model['digest']==read(PARENT/'protocol.json')['model_digest']
        for c in 'BC':
            for r in records[c]:
                key=c,r['record_id']
                if key in done: continue
                q=r['question']; before=old.scan_query(q); after=new.scan_query(q)
                if c=='C':
                    before={**before,'matched_entries':[]};after={**after,'matched_entries':[]}
                same_input=before==after
                if same_input:
                    row={**parent[key],'reuse':'Exact effective normalization inputs unchanged','parent_cache_sha256':hashes[str((PARENT/'candidate_normalizations.jsonl').relative_to(ROOT))]}
                else:
                    literals=sorted(set(re.findall(r'\b[A-Z][A-Z0-9]{1,}\b|\d+(?:[.,]\d+)*',q)))
                    prompt=PROMPT+'\nCopy these explicitly supplied tokens unchanged: '+json.dumps(literals)+'\n'
                    try:
                        with patch('src.query_normalizer.BASELINE_SYSTEM_PROMPT',prompt): n=new.normalize(q)
                        row={'configuration':c,'record_id':r['record_id'],'normalization':n,'literal_flags':fidelity_flags(q,n['normalized_query']) if n.get('normalized_query') else [],'reuse':False}
                    except Exception as exc:
                        row={'configuration':c,'record_id':r['record_id'],'normalization':{'status':'ERROR'},'literal_flags':[],'reuse':False,'error':str(exc)}
                with path.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
                done[key]=row
                write('progress.json',{'completed':len(done),'total':180,'new_requests':sum(not r['reuse'] for r in done.values())})
                print(f"{len(done)}/180 {c} {r['record_id']} {'reused' if row['reuse'] else 'new'}",flush=True)
        return
    assert len(done)==180
    import numpy as np
    from src.chunk_retriever import ChunkRetriever
    from src.development_retrieval_metrics import ranking_metrics
    retriever=ChunkRetriever.from_files(corpus_path=ART/'corpus.json',bm25_path=ART/'bm25_index.pkl',faiss_path=ART/'faiss_index.bin',manifest_path=ART/'pipeline_manifest.json')
    retriever.weights=np.asarray([.75,.25,0])
    query_cache={};rows=[];traces=[]
    for c in 'BC':
        for r in records[c]:
            n=done[c,r['record_id']]['normalization'];q=n.get('normalized_query');result=None
            if n['status']=='SUCCESS' and q:
                if q not in query_cache:query_cache[q]=retriever.retrieve(q,top_k=5)
                result=query_cache[q]
            ids=result['source_chunk_ids'] if result else []
            traces.append({'configuration':c,'record_id':r['record_id'],'original_query':r['question'],'query':q,'normalization_status':n['status'],'top5':ids,'retrieved':result})
            for k in [3,5]:rows.append({'configuration':c,'record_id':r['record_id'],'pillar':r['pillar'],'language':r['language'],'k':k,'has_context':bool(ids),**ranking_metrics(ids,r['ground_truth_chunk_ids'],k)})
    summaries=[]
    for c in 'BC':
        for k in [3,5]:
            rs=[r for r in rows if r['configuration']==c and r['k']==k]
            summaries.append({'configuration':c,'k':k,'queries':len(rs),'with_context':sum(r['has_context'] for r in rs),'hit_at_k':sum(r['hit_at_k'] for r in rs)/90,'mrr_at_k':sum(r['mrr_at_k'] for r in rs)/90})
    write('retrieval_traces.json',traces);write('summary.json',{'results':summaries,'promoted':False,'context_precision':'not evaluated','answer_quality':'not evaluated'})
    for name,data in [('summary.csv',summaries),('per_query_metrics.csv',rows)]:
        with (OUT/name).open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    assert {str(p):sha(ROOT/p) for p in hashes}==hashes
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':main()
