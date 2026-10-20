"""Prepare a declared simplex grid on archived development normalizations, no model calls."""
from pathlib import Path
import sys,json,hashlib,csv
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from src.chunk_retriever import ChunkRetriever,min_max_normalize
from src.development_retrieval_metrics import ranking_metrics

def main():
 out=ROOT/'experiments/t07-development-grid-v1'
 if out.exists():raise ValueError('Fresh output required')
 art=ROOT/'experiments/chapter3-table-repaired-development-v1';source=ROOT/'experiments/t06-formal-development-validation-v4/interactions.corrected_references.jsonl';records=[json.loads(l) for l in source.read_text(encoding='utf-8').splitlines()];old=json.loads((ROOT/'experiments/t06-30group-development-batch-v1/protocol.json').read_text(encoding='utf-8'))
 weights=[[a/4,b/4,(4-a-b)/4] for a in range(5) for b in range(5-a)]+[[.4,.6,0],[.4,.5,.1]]
 out.mkdir();write=lambda n,v:(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 write('protocol.json',{'held_out_accessed':False,'scope':'Development tuning preparation; not selected or frozen','weight_grid':weights,'grid_step':.25,'additional_candidates':[[.4,.6,0],[.4,.5,.1]],'k_values':[3,5],'selection_objective':'RAGAS context precision macro-average across all 15 office-language cells; Hit/MRR diagnostics are not selection objective.','selection_status':'PENDING_CONTEXT_PRECISION_JUDGING','candidate_pool':'all corpus chunks','normalization':'Reuse archived B normalization only after artifact/prompt hash verification. C requires new normalization without lexical injection.','stopped_query_policy':'Retain all 90 records; stopped queries have no contexts. Report coverage and conditional metric denominators, never silently omit.','configuration_A':'Raw citizen query, BM25 only, identical answer generator','configuration_B':'Dictionary-injected normalization and BM25/FAISS/dictionary fusion','configuration_C':'Same as B except glossary injection disabled; preserve ambiguity gate and dictionary retrieval boost.','tie_break':'Predeclared grid order, then K=3 before K=5 when objective exactly tied; no Hit/MRR tie-break','freeze':False})
 retriever=ChunkRetriever.from_files(corpus_path=art/'corpus.json',bm25_path=art/'bm25_index.pkl',faiss_path=art/'faiss_index.bin',manifest_path=art/'pipeline_manifest.json')
 assert all(retriever.artifact_hashes[n]==v for n,v in old['artifact_hashes'].items());prompt=ROOT/'config/normalization_intent_candidate.txt';assert hashlib.sha256(prompt.read_bytes()).hexdigest()==old['normalization_prompt_sha256']
 ids=[c['chunk_id'] for c in retriever.chunks];allr=[];stats=[];arrays={}
 for ix,r in enumerate(records):
  raw=np.asarray(retriever.bm25.get_scores(r['question'].lower().split()));aids=[ids[i] for i in np.argsort(-raw,kind='stable')[:5]]
  allr.append({'configuration':'A','record_id':r['record_id'],'query':r['question'],'rankings':{'3':aids[:3],'5':aids},'status':'RETRIEVED','weights':[1,0,0]})
  query=r.get('search_query');status=r['normalization']['status']
  if status=='SUCCESS' and query:
   sparse=np.asarray(retriever.bm25.get_scores(query.lower().split()),dtype=float);emb=np.asarray(retriever.embedder.encode([query],normalize_embeddings=True),dtype=np.float32);dist,ind=retriever.index.search(emb,len(ids));dense=np.empty(len(ids));dense[ind[0]]=dist[0];matched=[t for t in retriever.terms if t in query.lower()];boost=np.asarray([sum(t in text for t in matched) for text in retriever.texts_lower]);matrix=np.column_stack([min_max_normalize(x) for x in [sparse,dense,boost]]);arrays[r['record_id']]=matrix
   fixed=[ids[i] for i in np.argsort(-(matrix@np.array([.4,.6,0])),kind='stable')[:5]];assert fixed==r['retrieved_rankings']['5'],r['record_id']
  else:matrix=None
  for wi,w in enumerate(weights):
   selected=[ids[i] for i in np.argsort(-(matrix@np.asarray(w)),kind='stable')[:5]] if matrix is not None else []
   entry={'configuration':'B','grid_id':wi,'weights':w,'record_id':r['record_id'],'query':query,'status':status,'rankings':{'3':selected[:3],'5':selected}};allr.append(entry)
   for k in [3,5]:stats.append({'grid_id':wi,'weights':str(w),'record_id':r['record_id'],'pillar':r['pillar'],'language':r['language'],'k':k,**ranking_metrics(selected,r['ground_truth_chunk_ids'],k)})
  print(f'{ix+1}/90 prepared',flush=True)
 (out/'rankings.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in allr),encoding='utf-8');np.savez_compressed(out/'normalized_score_vectors.npz',**arrays);write('chunk_order.json',ids)
 with (out/'retrieval_diagnostics.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(stats[0]));w.writeheader();w.writerows(stats)
 write('validation.json',{'all_archived_B_K5_rankings_reproduced':True,'all_90_queries_retained':True,'grid_candidates':len(weights),'k_values':[3,5],'artifact_hashes':retriever.artifact_hashes,'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'context_precision_judged':False,'selected_weights':None})
 write('hashes.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()})
if __name__=='__main__':main()
