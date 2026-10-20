"""Full development regression: isolate query fidelity and BM25 punctuation handling."""
from pathlib import Path
import sys,json,hashlib,re,copy,csv,pickle,os
from collections import Counter
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from rank_bm25 import BM25Okapi
from src.chunk_retriever import ChunkRetriever,min_max_normalize
from src.query_normalizer import QueryNormalizer,translation_errors
from scripts.run_t07_development_abc import InjectionDisabledNormalizer
from src.development_retrieval_metrics import ranking_metrics

def tokens(text):return re.findall(r'\w+(?:[.\-]\w+)*',text.casefold())
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 out=ROOT/'experiments/normalization-sparse-development-regression-v1';out.mkdir(exist_ok=True)
 source=ROOT/'experiments/t06-formal-development-validation-v4/interactions.corrected_references.jsonl';groups=read(source.parent/'development_groups.derived.json');assert len(groups)==30 and all(g['split']=='development' for g in groups)
 archived={c:lines(ROOT/f'experiments/t07-development-abc-v1/{c}/interactions.jsonl') for c in 'ABC'}
 ids={r['record_id'] for r in archived['B']};assert len(ids)==90 and all({r['record_id'] for r in rs}==ids for rs in archived.values())
 art=ROOT/'experiments/chapter3-table-repaired-development-v1';retriever=ChunkRetriever.from_files(corpus_path=art/'corpus.json',bm25_path=art/'bm25_index.pkl',faiss_path=art/'faiss_index.bin',manifest_path=art/'pipeline_manifest.json')
 assert retriever.artifact_hashes==read(ROOT/'experiments/t07-development-abc-v1/protocol.json')['artifact_hashes']
 base_prompt=(ROOT/'config/normalization_intent_candidate.txt').read_text(encoding='utf-8')
 extra='''\nFidelity checklist before emitting the question:\nCopy every supplied acronym exactly, even if its expanded name also appears. Keep each acronym attached to the service it qualifies. Do not omit one acronym because another is similar.\nUse ordinary English for the citizen's intent. Dictionary descriptions clarify word meaning; they are not phrases that must be copied verbatim. Preserve a simple request for a fee, payment, amount, quantity, or duration as that same simple request.\nDo not add answer facts, requirements, rates, conditions, or new service names.\n'''
 candidate_prompt=base_prompt+extra
 (out/'candidate_prompt.txt').write_text(candidate_prompt,encoding='utf-8')
 protocol={'held_out_accessed':False,'freeze':False,'scope':'Full 90-query development retrieval regression, no answer generation or new judge calls','artifact_hashes':retriever.artifact_hashes,'source_sha256':sha(source),'weights':[.75,.25,0],'k':[3,5],'sparse_candidate':'Same BM25 parameters; corpus and query both tokenized with Unicode word regex, retaining internal decimal/dash sequences. No synonym expansion.','candidate_prompt_sha256':hashlib.sha256(candidate_prompt.encode()).hexdigest(),'normalization_contract':'Record original outputs and fidelity errors; candidate validation errors stop retrieval and count as no-hit, not clarification.','factorial_comparison':['archived normalization / whitespace BM25','archived normalization / punctuation BM25','candidate normalization / whitespace BM25','candidate normalization / punctuation BM25'],'C_ablation':'Same prompt and ambiguity gate, no query-specific dictionary injection. Shared static prompt guidance retained.','selection_policy':'Hit/MRR diagnostics only. No weights selected, no candidate promoted without Context Precision objective and coverage review.','app_defaults_changed':False}
 if (out/'protocol.json').exists():assert read(out/'protocol.json')==protocol
 else:write(out/'protocol.json',protocol)
 bm=BM25Okapi([tokens(c['text_content']) for c in retriever.chunks])
 sparse_path=out/'bm25_punctuation_candidate.pkl'
 if not sparse_path.exists():
  with sparse_path.open('wb') as f:pickle.dump({'bm25':bm,'chunks':retriever.chunks,'tokenizer':'unicode-word-decimal-dash-v1'},f)
 normalizers={'B':QueryNormalizer(enable_context_rules=False),'C':InjectionDisabledNormalizer(enable_context_rules=False)}
 cachefile=out/'candidate_normalizations.jsonl';norms={(r['configuration'],r['record_id']):r for r in lines(cachefile)} if cachefile.exists() else {}
 for config in 'BC':
  for r in archived[config]:
   key=(config,r['record_id'])
   if key in norms:continue
   acronyms=sorted(set(re.findall(r'\b[A-Z][A-Z0-9]{1,}\b',r['question'])))
   prompt=candidate_prompt+'\nCopy these supplied tokens unchanged: '+(', '.join(acronyms) if acronyms else 'none')+'.'
   try:
    with patch('src.query_normalizer.BASELINE_SYSTEM_PROMPT',prompt):n=normalizers[config].normalize(r['question'])
    errors=translation_errors(r['question'],n.get('normalized_query') or '',{'done':n.get('diagnostics',{}).get('done'),'done_reason':n.get('diagnostics',{}).get('done_reason'),'eval_count':n.get('tokens_generated',0)}) if n['status']=='SUCCESS' else []
    item={'configuration':config,'record_id':r['record_id'],'normalization':n,'fidelity_errors':errors,'effective_status':'FIDELITY_ERROR' if errors else n['status']}
   except Exception as exc:item={'configuration':config,'record_id':r['record_id'],'normalization':{},'fidelity_errors':[],'effective_status':'NORMALIZATION_ERROR','error':str(exc)}
   with cachefile.open('a',encoding='utf-8') as f:f.write(json.dumps(item,ensure_ascii=False)+'\n')
   norms[key]=item
   write(out/'progress.json',{'processed':len(norms),'total':180,'latest':{'configuration':config,'record_id':r['record_id'],'status':item['effective_status']}})
   print(f'{len(norms)}/180 {config} {r["record_id"]} {item["effective_status"]}',flush=True)
 chunk_ids=[c['chunk_id'] for c in retriever.chunks];dense_cache={};allrows=[];details=[]
 def rank(q,mode,config):
  sparse=np.asarray((retriever.bm25.get_scores(q.lower().split()) if mode=='whitespace' else bm.get_scores(tokens(q))))
  if config=='A':score=sparse
  else:
   if q not in dense_cache:
    emb=np.asarray(retriever.embedder.encode([q],normalize_embeddings=True),dtype=np.float32);dist,idx=retriever.index.search(emb,len(chunk_ids));dense=np.empty(len(chunk_ids));dense[idx[0]]=dist[0];dense_cache[q]=dense
   score=.75*min_max_normalize(sparse)+.25*min_max_normalize(dense_cache[q])
  order=np.argsort(-score,kind='stable');return [chunk_ids[int(i)] for i in order[:5]],order
 for config in 'ABC':
  for r in archived[config]:
   versions=['archived'] if config=='A' else ['archived','candidate']
   for version in versions:
    if version=='candidate':n=norms[config,r['record_id']];status=n['effective_status'];q=n['normalization'].get('normalized_query');errors=n['fidelity_errors']
    else:
     n=r['normalization'];status='SUCCESS' if config=='A' else n['status'];q=r['question'] if config=='A' else n.get('normalized_query');errors=translation_errors(r['question'],q or '',{}) if status=='SUCCESS' else []
    for mode in ['whitespace','punctuation']:
     selected,order=rank(q,mode,config) if status=='SUCCESS' and q else ([],None)
     if version=='archived' and mode=='whitespace':assert selected[:3]==r['retrieved_rankings'].get('3',[]),(config,r['record_id'])
     for k in [3,5]:allrows.append({'configuration':config,'normalization':version,'sparse_tokenizer':mode,'record_id':r['record_id'],'pillar':r['pillar'],'language':r['language'],'status':status,'fidelity_error_count':len(errors),'k':k,**ranking_metrics(selected,r['ground_truth_chunk_ids'],k)})
     detail={'configuration':config,'normalization':version,'sparse_tokenizer':mode,'record_id':r['record_id'],'query':q,'status':status,'top5':selected,'fidelity_errors':errors}
     if r['record_id']=='SCENARIO-BFP-002-taglish' and order is not None:
      ranks={chunk_ids[int(idx)]:i for i,idx in enumerate(order,1)};detail['fee_chunk_ranks']={cid:ranks[cid] for cid in ['DEV120-BFP-PDF0001-C019','DEV120-BFP-PDF0001-C020']}
     details.append(detail)
 summaries=[]
 for config,version,mode,k in sorted({(r['configuration'],r['normalization'],r['sparse_tokenizer'],r['k']) for r in allrows}):
  rs=[r for r in allrows if (r['configuration'],r['normalization'],r['sparse_tokenizer'],r['k'])==(config,version,mode,k)];assert len(rs)==90
  summaries.append({'configuration':config,'normalization':version,'sparse_tokenizer':mode,'k':k,'queries':90,'hit_at_k':sum(r['hit_at_k'] for r in rs)/90,'mrr_at_k':sum(r['mrr_at_k'] for r in rs)/90,'statuses':dict(Counter(r['status'] for r in rs)),'queries_with_fidelity_errors':sum(bool(r['fidelity_error_count']) for r in rs)})
 for name,rs in [('per_query_metrics.csv',allrows),('summary.csv',[{**r,'statuses':json.dumps(r['statuses'])} for r in summaries])]:
  with (out/name).open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
 write(out/'summary.json',{'results':summaries,'held_out_accessed':False,'freeze':False,'original_rankings_reproduced':True,'ragas_context_precision_status':'Not scored for new rankings; no promotion or final selection justified yet'})
 (out/'rankings.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in details),encoding='utf-8')
 write(out/'hashes.json',{p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='hashes.json'})
 print('All 90 queries tested for each declared condition. No promotion.',flush=True)
if __name__=='__main__':main()
