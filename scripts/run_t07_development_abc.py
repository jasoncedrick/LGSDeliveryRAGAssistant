"""Resumable paired DEVELOPMENT A/B/C generation; never reads held-out queries."""
import argparse, copy, csv, hashlib, json, os, sys
from pathlib import Path
from collections import Counter
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.query_normalizer import QueryNormalizer

class InjectionDisabledNormalizer(QueryNormalizer):
    """Only omit matched glossary entries; preserve the identical ambiguity scan."""
    def scan_query(self, raw_query):
        scanned=super().scan_query(raw_query)
        return {**scanned,'matched_entries':[]}

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

def sparse_retrieval(retriever, query, k):
    """A performs BM25 only; no embedding or dictionary scoring call."""
    import numpy as np
    scores=retriever.bm25.get_scores(query.lower().split())
    selected=np.argsort(-np.asarray(scores),kind='stable')[:k]
    citations=[];blocks=[]
    for rank,idx in enumerate(selected,1):
        c=retriever.chunks[int(idx)];label=f'S{rank}'
        citations.append({'citation':label,'chunk_id':c['chunk_id'],'file_source':c['file_source'],'source_page':c.get('source_page'),'pdf_relative_page':c.get('pdf_relative_page'),'text':c['text_content']})
        blocks.append(f"[{label}] {c['file_source']} | printed page {c.get('source_page')} | chunk {c['chunk_id']}\n{c['text_content']}")
    return {'status':'CONTEXT_READY','source_chunk_ids':[c['chunk_id'] for c in citations],'citations':citations,'context':'\n\n'.join(blocks)}

def main(args):
    import numpy as np
    import requests
    from app.pipeline import Pipeline,ANSWER_SYSTEM_PROMPT
    from src.development_retrieval_metrics import ranking_metrics
    grid=ROOT/'experiments/t07-development-grid-format-retry-v2'
    result=read(grid/'context_precision_grid.json')
    if result['selection_status']!='READY_FOR_COMPARISON_NOT_FROZEN':raise ValueError('Complete grid judging required first')
    best=result['best_complete_candidate'];weights=read(grid/'protocol.json')['weight_grid'][best['grid_id']];k=best['k']
    source=ROOT/'experiments/t06-formal-development-validation-v4/interactions.corrected_references.jsonl'
    groups=read(source.parent/'development_groups.derived.json')
    assert len(groups)==30 and all(g['split']=='development' for g in groups)
    records=lines(source);assert len(records)==90 and len({r['record_id'] for r in records})==90
    assert {r['question_group_id'] for r in records}=={g['group_id'] for g in groups}
    prompt=ROOT/'config/normalization_intent_candidate.txt';old=read(ROOT/'experiments/t06-30group-development-batch-v1/protocol.json')
    pipeline=Pipeline(artifacts_dir=ROOT/'experiments/chapter3-table-repaired-development-v1')
    assert pipeline.retriever.artifact_hashes==old['artifact_hashes']
    assert digest(prompt)==old['normalization_prompt_sha256']
    assert hashlib.sha256(ANSWER_SYSTEM_PROMPT.encode()).hexdigest()==old['answer_prompt_sha256']
    pipeline.retriever.weights=np.asarray(weights);c_normalizer=InjectionDisabledNormalizer(enable_context_rules=False)
    ranking_lookup={(r['configuration'],r['record_id']):r for r in lines(grid/'rankings.jsonl') if r['configuration']=='A' or r['grid_id']==best['grid_id']}
    for r in records:
        expected=ranking_lookup['A',r['record_id']]['rankings'][str(k)]
        assert sparse_retrieval(pipeline.retriever,r['question'],k)['source_chunk_ids']==expected
    if args.validate_only:
        print('PASS: development 30/90, artifact and prompt hashes, A raw-BM25 rankings, complete grid. K=',k,'weights=',weights);return
    out=ROOT/'experiments/t07-development-abc-v1';out.mkdir(exist_ok=True)
    tags=requests.get('http://localhost:11434/api/tags',timeout=10).json()
    model=[m for m in tags['models'] if m['name'] in ('eboss-mistral','eboss-mistral:latest')][0]
    protocol={'held_out_accessed':False,'freeze':False,'scope':'Paired development diagnostic comparison, not final T07 held-out comparison','k':k,'weights_B_C':weights,'selection_J':best['J'],'source_sha256':digest(source),'grid_result_sha256':digest(grid/'context_precision_grid.json'),'artifact_hashes':pipeline.retriever.artifact_hashes,'normalization_prompt_sha256':digest(prompt),'answer_prompt_sha256':old['answer_prompt_sha256'],'model_digest':model['digest'],'generation_settings':{'temperature':0,'top_p':0,'num_ctx':pipeline.num_ctx,'num_predict':pipeline.answer_tokens},'A':'Raw query BM25 only; no normalization or dictionary ambiguity gate','B':'Archived dictionary-injected normalization; selected fusion weights','C':'Fresh normalization, matched glossary entries omitted; identical ambiguity gate and retrieval boost','C_limitation':'Shared static lexical examples in the normalization prompt remain; ablation removes query-specific dictionary injection only.','retained_outcomes':'All 90 per configuration, including clarification and errors; no hidden retries','app_defaults_changed':False}
    if (out/'protocol.json').exists():assert read(out/'protocol.json')==protocol,'Cannot resume after configuration/input changes'
    else:write(out/'protocol.json',protocol)
    for config in 'ABC':
        folder=out/config;folder.mkdir(exist_ok=True);write(folder/'protocol.json',{**protocol,'configuration':config})
    completed={}
    for config in 'ABC':
        f=out/config/'interactions.jsonl';completed[config]=lines(f) if f.exists() else []
    done={(c,r['record_id']) for c,rs in completed.items() for r in rs}
    for original in records:
        for config in 'ABC':
            if (config,original['record_id']) in done:continue
            r={key:copy.deepcopy(original[key]) for key in ['record_id','question_id','question_group_id','language','question','pillar','reference_answer','reference_status','ground_truth_chunk_ids'] if key in original}
            r.update(configuration=config,k=k,citations=[],context='',answer='',status='PENDING',retrieved_rankings={},generation_started=False)
            try:
                if config=='A':
                    normalization={'status':'BYPASSED','normalized_query':r['question']};retrieved=sparse_retrieval(pipeline.retriever,r['question'],k)
                else:
                    if config=='B':normalization=copy.deepcopy(original['normalization'])
                    else:
                        with patch('src.query_normalizer.BASELINE_SYSTEM_PROMPT',prompt.read_text(encoding='utf-8')):normalization=c_normalizer.normalize(r['question'])
                    if normalization['status']=='FALLBACK_TRIGGERED':
                        r.update(status='CLARIFICATION_REQUIRED',answer=normalization.get('clarification_prompt') or '',clarification_prompt=normalization.get('clarification_prompt'));retrieved=None
                    elif normalization['status']!='SUCCESS' or not normalization.get('normalized_query'):
                        r.update(status='NORMALIZATION_ERROR');retrieved=None
                    else:
                        retrieved=pipeline.retriever.retrieve(normalization['normalized_query'],top_k=k)
                        if config=='B':assert retrieved['source_chunk_ids']==ranking_lookup['B',r['record_id']]['rankings'][str(k)]
                r['normalization']=normalization
                if retrieved:
                    r.update(search_query=normalization['normalized_query'],citations=retrieved['citations'],context=retrieved['context'],retrieved_rankings={str(k):retrieved['source_chunk_ids']})
                    r.update(pipeline._generate_answer(r['question'],retrieved))
            except Exception as exc:r.update(status='PIPELINE_ERROR',error=str(exc))
            r['ranking_metrics']=ranking_metrics(r['retrieved_rankings'].get(str(k),[]),r['ground_truth_chunk_ids'],k)
            with (out/config/'interactions.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(r,ensure_ascii=False)+'\n')
            completed[config].append(r)
            counts={c:len(rs) for c,rs in completed.items()};write(out/'progress.json',{'completed':sum(counts.values()),'total':270,'by_configuration':counts,'latest':{'configuration':config,'record_id':r['record_id'],'status':r['status']}})
            print(f"{sum(counts.values())}/270 {config} {r['record_id']} {r['status']}",flush=True)
    summary={}
    with (out/'retrieval_comparison.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['configuration','record_id','status','hit_at_k','mrr_at_k']);w.writeheader()
        for c,rs in completed.items():
            assert len(rs)==90
            summary[c]={'statuses':dict(Counter(r['status'] for r in rs)),'hit_at_k':sum(r['ranking_metrics']['hit_at_k'] for r in rs)/90,'mrr_at_k':sum(r['ranking_metrics']['mrr_at_k'] for r in rs)/90}
            for r in rs:w.writerow({'configuration':c,'record_id':r['record_id'],'status':r['status'],**{key:r['ranking_metrics'][key] for key in ['hit_at_k','mrr_at_k']}})
    write(out/'summary.json',{'held_out_accessed':False,'configurations':summary,'ragas_status':'Pending; generation and retrieval only','freeze':False})
    write(out/'hashes.json',{str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file() and p.name!='hashes.json'})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--validate-only',action='store_true');main(p.parse_args())
