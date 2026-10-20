"""Development-only component tracing and punctuation-tokenization controls."""
from pathlib import Path
import sys,json,re,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from rank_bm25 import BM25Okapi
from src.chunk_retriever import ChunkRetriever,min_max_normalize
def main():
 out=ROOT/'experiments/bfp002-component-diagnosis-v1';out.mkdir(exist_ok=True)
 art=ROOT/'experiments/chapter3-table-repaired-development-v1'
 rt=ChunkRetriever.from_files(corpus_path=art/'corpus.json',bm25_path=art/'bm25_index.pkl',faiss_path=art/'faiss_index.bin',manifest_path=art/'pipeline_manifest.json')
 ids=[c['chunk_id'] for c in rt.chunks];targets=['DEV120-BFP-PDF0001-C019','DEV120-BFP-PDF0001-C020']
 token=lambda t:re.findall(r'\w+(?:[.\-]\w+)*',t.casefold())
 alt=BM25Okapi([token(c['text_content']) for c in rt.chunks])
 records=[json.loads(l) for l in (ROOT/'experiments/t07-development-abc-v1/B/interactions.jsonl').read_text(encoding='utf-8').splitlines()]
 queries={'archived_B':next(r['search_query'] for r in records if r['record_id']=='SCENARIO-BFP-002-taglish'),
 'preserve_FSIC_only':'How is the Fire Safety Inspection Fee (FSIF) calculated for an FSIC for Occupancy and what is the minimum monetary settlement?',
 'plain_payment_only':'How is the Fire Safety Inspection Fee (FSIF) calculated for an Occupancy and what is the minimum payment?',
 'faithful_translation_control':'How is the Fire Safety Inspection Fee (FSIF) calculated for FSIC for Occupancy and what is the minimum fee?'}
 results=[]
 for name,q in queries.items():
  sparse=np.asarray(rt.bm25.get_scores(q.lower().split()));emb=np.asarray(rt.embedder.encode([q],normalize_embeddings=True),dtype=np.float32);dist,ix=rt.index.search(emb,len(ids));dense=np.empty(len(ids));dense[ix[0]]=dist[0];terms=[t for t in rt.terms if t in q.lower()];boost=np.asarray([sum(t in x for t in terms) for x in rt.texts_lower]);regex=np.asarray(alt.get_scores(token(q)))
  columns={'bm25':sparse,'dense':dense,'dictionary':boost,'regex_bm25_probe':regex};fused=.75*min_max_normalize(sparse)+.25*min_max_normalize(dense);rfused=.75*min_max_normalize(regex)+.25*min_max_normalize(dense);columns.update(fusion=fused,regex_fusion_probe=rfused)
  ranks={key:{ids[int(idx)]:i for i,idx in enumerate(np.argsort(-v,kind='stable'),1)} for key,v in columns.items()}
  result={'query_variant':name,'query':q,'targets':[{ 'chunk_id':cid,'ranks':{key:value[cid] for key,value in ranks.items()},'raw_scores':{key:float(value[ids.index(cid)]) for key,value in columns.items()}} for cid in targets],'top5':[ids[int(i)] for i in np.argsort(-fused,kind='stable')[:5]],'matched_query_whitespace_tokens':{cid:sorted(set(q.lower().split())&set(rt.chunks[ids.index(cid)]['text_content'].lower().split())) for cid in targets}}
  results.append(result)
  print(name,[(t['chunk_id'],t['ranks']) for t in result['targets']],flush=True)
 write=lambda n,x:(out/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
 write('component_traces.json',results)
 write('protocol.json',{'held_out_accessed':False,'artifact_hashes':rt.artifact_hashes,'scope':'Counterfactual diagnostics, not tuned or promoted configurations','controls':'Query controls contain no reference-answer fees. Regex BM25 is an in-memory probe, not an index replacement.','corpus_changed':False,'app_defaults_changed':False})
if __name__=='__main__':main()
